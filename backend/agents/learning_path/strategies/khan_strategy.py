"""Khan Academy search strategy for learning path recommendations.

This module provides integration with Khan Academy API to find educational
videos, exercises, and articles for personalized learning paths.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from ..models import KnowledgeLevel, LearningResource
from .resource_search import ResourceSearchStrategy

logger = logging.getLogger(__name__)


class KhanSearchStrategy(ResourceSearchStrategy):
    """Khan Academy API search strategy."""

    def __init__(self) -> None:
        """Initialize Khan Academy search strategy."""
        self.base_url = "https://www.khanacademy.org/api/v1"
        self.tr_base_url = "https://tr.khanacademy.org/api/v1"

    async def search(
        self,
        query: str,
        subject: str | None = None,
        difficulty_range: tuple[float, float] = (-4.0, 4.0),
        limit: int = 10,
    ) -> list[LearningResource]:
        """Search Khan Academy for educational content.

        Args:
            query: Search query string.
            subject: Optional subject filter.
            difficulty_range: Min and max difficulty values.
            limit: Maximum number of results to return.

        Returns:
            List of learning resources from Khan Academy.
        """
        try:
            # Try Turkish content first
            resources = await self._search_turkish(query, subject, limit)

            # Fallback to English if not enough results
            if len(resources) < limit // 2:
                english_resources = await self._search_english(
                    query, subject, limit - len(resources)
                )
                resources.extend(english_resources)

            # Filter by difficulty
            filtered = [
                r
                for r in resources
                if self._is_in_difficulty_range(r, difficulty_range)
            ]

            return filtered[:limit]

        except Exception as e:
            logger.warning(f"Khan Academy search failed: {e}")
            return []

    def get_platform_name(self) -> str:
        """Get platform identifier.

        Returns:
            Platform name string.
        """
        return "khan_academy"

    def normalize_result(self, raw_result: dict[str, Any]) -> LearningResource | None:
        """Convert Khan Academy API response to LearningResource.

        Args:
            raw_result: Raw API response data.

        Returns:
            Normalized LearningResource or None if conversion fails.
        """
        try:
            content_kind = raw_result.get("kind", "Video")

            # Determine resource type
            resource_type = self._map_content_kind(content_kind)

            # Calculate duration (Khan uses seconds)
            duration_seconds = raw_result.get(
                "duration", raw_result.get("video_seconds", 600)
            )
            duration_minutes = max(1, duration_seconds // 60)

            # Estimate difficulty
            difficulty = self._estimate_difficulty(raw_result)

            slug = raw_result.get("slug", raw_result.get("id", ""))

            # Map difficulty to KnowledgeLevel
            difficulty_level = self._map_difficulty_to_level(difficulty)

            return LearningResource(
                resource_id=f"khan-{slug}",
                title=raw_result.get("title", raw_result.get("translated_title", "")),
                description=raw_result.get(
                    "description", raw_result.get("translated_description", "")
                )[:500],
                url=self._build_url(raw_result),
                source="khan_academy",
                resource_type=resource_type,
                difficulty_level=difficulty_level,
                estimated_time=duration_minutes,
                language="tr" if raw_result.get("is_turkish", False) else "en",
                tags=self._extract_topics(raw_result),
                rating=None,
                metadata={
                    "kind": content_kind,
                    "ka_url": raw_result.get("ka_url", ""),
                    "thumbnail": raw_result.get(
                        "image_url", raw_result.get("thumbnail_url", "")
                    ),
                    "is_turkish": raw_result.get("is_turkish", False),
                    "difficulty_numeric": difficulty,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to normalize Khan result: {e}")
            return None

    def _map_content_kind(self, kind: str) -> str:
        """Map Khan content kinds to resource types.

        Args:
            kind: Khan Academy content kind.

        Returns:
            Normalized resource type.
        """
        mapping = {
            "Video": "video",
            "Exercise": "exercise",
            "Article": "article",
            "Topic": "topic",
            "Talkthrough": "video",
        }
        return mapping.get(kind, "video")

    async def _search_turkish(
        self, query: str, subject: str | None, limit: int
    ) -> list[LearningResource]:
        """Search Turkish Khan Academy.

        Args:
            query: Search query string.
            subject: Optional subject filter.
            limit: Maximum number of results.

        Returns:
            List of Turkish learning resources.
        """
        return await self._do_search(
            self.tr_base_url, query, subject, limit, is_turkish=True
        )

    async def _search_english(
        self, query: str, subject: str | None, limit: int
    ) -> list[LearningResource]:
        """Search English Khan Academy.

        Args:
            query: Search query string.
            subject: Optional subject filter.
            limit: Maximum number of results.

        Returns:
            List of English learning resources.
        """
        return await self._do_search(
            self.base_url, query, subject, limit, is_turkish=False
        )

    async def _do_search(
        self,
        base_url: str,
        query: str,
        subject: str | None,
        limit: int,
        is_turkish: bool,
    ) -> list[LearningResource]:
        """Execute search against Khan API.

        Args:
            base_url: API base URL.
            query: Search query string.
            subject: Optional subject filter.
            limit: Maximum number of results.
            is_turkish: Whether searching Turkish content.

        Returns:
            List of learning resources.
        """
        try:
            # Build search endpoint
            search_query = query
            if subject:
                search_query = f"{query} {subject}"

            params = {
                "q": search_query,
                "limit": limit,
            }

            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"{base_url}/search",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp,
            ):
                if resp.status != 200:
                    return []

                data = await resp.json()
                items = data if isinstance(data, list) else data.get("items", [])

                resources = []
                for item in items:
                    item["is_turkish"] = is_turkish
                    resource = self.normalize_result(item)
                    if resource:
                        resources.append(resource)

                return resources
        except Exception as e:
            logger.warning(f"Khan search failed ({base_url}): {e}")
            return []

    def _build_url(self, result: dict[str, Any]) -> str:
        """Build content URL.

        Args:
            result: Khan Academy API result.

        Returns:
            Full URL to content.
        """
        ka_url = result.get("ka_url", "")
        if ka_url:
            return ka_url

        slug = result.get("slug", result.get("id", ""))
        is_turkish = result.get("is_turkish", False)
        base = (
            "https://tr.khanacademy.org"
            if is_turkish
            else "https://www.khanacademy.org"
        )

        kind = result.get("kind", "video").lower()
        return f"{base}/{kind}/{slug}"

    def _estimate_difficulty(self, result: dict[str, Any]) -> float:
        """Estimate difficulty from mastery model and prerequisites.

        Args:
            result: Khan Academy API result.

        Returns:
            Difficulty value between -4.0 and 4.0.
        """
        # Check mastery model
        mastery = result.get("mastery_model", {})
        if mastery:
            level = mastery.get("level", 0)
            return (level - 2) * 1.5  # Map 0-4 to -3.0 to 3.0

        # Check prerequisites count
        prereqs = result.get("prerequisites", [])
        if len(prereqs) > 3:
            return 1.5  # Advanced
        if len(prereqs) > 1:
            return 0.0  # Intermediate
        return -1.0  # Beginner

    def _extract_topics(self, result: dict[str, Any]) -> list[str]:
        """Extract topics from Khan metadata.

        Args:
            result: Khan Academy API result.

        Returns:
            List of topic strings.
        """
        topics = []

        # Domain
        domain = result.get("domain_slug", "")
        if domain:
            topics.append(domain.replace("-", " ").title())

        # Subject
        subject = result.get("subject_slug", "")
        if subject:
            topics.append(subject.replace("-", " ").title())

        # Topic
        topic = result.get("topic_slug", "")
        if topic:
            topics.append(topic.replace("-", " ").title())

        return topics[:5]

    def _map_difficulty_to_level(self, difficulty: float) -> KnowledgeLevel:
        """Map numeric difficulty to KnowledgeLevel enum.

        Args:
            difficulty: Numeric difficulty (-4.0 to 4.0).

        Returns:
            Corresponding KnowledgeLevel.
        """
        if difficulty < -2.0:
            return KnowledgeLevel.BEGINNER
        if difficulty < -0.5:
            return KnowledgeLevel.ELEMENTARY
        if difficulty < 0.5:
            return KnowledgeLevel.INTERMEDIATE
        if difficulty < 2.0:
            return KnowledgeLevel.ADVANCED
        return KnowledgeLevel.EXPERT

    def _is_in_difficulty_range(
        self, resource: LearningResource, range_tuple: tuple[float, float]
    ) -> bool:
        """Check if resource difficulty is within range.

        Args:
            resource: Learning resource to check.
            range_tuple: Min and max difficulty values.

        Returns:
            True if resource is within difficulty range.
        """
        # Get numeric difficulty from metadata
        numeric_difficulty = (
            resource.metadata.get("difficulty_numeric", 0.0)
            if resource.metadata
            else 0.0
        )
        return range_tuple[0] <= numeric_difficulty <= range_tuple[1]
