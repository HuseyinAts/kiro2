"""OER Commons search strategy for learning path recommendations.

This module provides integration with OER Commons API to find free educational
resources (documents, videos, interactive content) for personalized learning paths.

OER Commons (https://www.oercommons.org/) provides open educational resources
with various licenses (CC-BY, CC-BY-SA, Public Domain).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import logging
import aiohttp

from agents.learning_path.strategies.resource_search import ResourceSearchStrategy
from agents.learning_path.models import LearningResource, KnowledgeLevel
from agents.learning_path.config import get_learning_path_config

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class OERSearchStrategy(ResourceSearchStrategy):
    """OER Commons API search strategy for open educational resources."""

    def __init__(self) -> None:
        """Initialize OER Commons search strategy."""
        self.config = get_learning_path_config()
        self.base_url = "https://www.oercommons.org/api/v1"

    async def search(
        self,
        query: str,
        subject: Optional[str] = None,
        difficulty_range: tuple[float, float] = (-4.0, 4.0),
        limit: int = 10,
    ) -> list[LearningResource]:
        """Search OER Commons for educational resources.

        Args:
            query: Search query string.
            subject: Optional subject filter (e.g., "matematik", "fizik").
            difficulty_range: Min and max IRT difficulty values.
            limit: Maximum number of results to return.

        Returns:
            List of learning resources from OER Commons.
        """
        try:
            # Validate query
            self.validate_query(query)

            # Search with subject filter (get extra for filtering)
            results = await self._search_oer(query, subject, limit * 2)

            # Convert and filter
            resources = []
            for result in results:
                resource = self.normalize_result(result)
                if resource and self._is_in_difficulty_range(resource, difficulty_range):
                    resources.append(resource)

            return resources[:limit]

        except Exception as e:
            logger.warning(f"OER search failed: {e}")
            return []

    def get_platform_name(self) -> str:
        """Get platform identifier.

        Returns:
            Platform name string.
        """
        return "oer_commons"

    def normalize_result(self, raw_result: dict[str, Any]) -> Optional[LearningResource]:
        """Convert OER Commons API response to LearningResource.

        Args:
            raw_result: Raw API response data.

        Returns:
            Normalized LearningResource or None if conversion fails.
        """
        try:
            # Determine resource type
            media_type = raw_result.get("media_type", "document")
            resource_type = self._map_media_type(media_type)

            # Estimate duration
            duration = self._estimate_duration(raw_result, resource_type)

            # Estimate difficulty from grade level
            difficulty = self._estimate_difficulty(raw_result)
            difficulty_level = self._map_difficulty_to_level(difficulty)

            # Generate resource ID
            resource_id = raw_result.get("id", raw_result.get("url", "").split("/")[-1])

            # Extract language
            language = raw_result.get("language", "en")

            return LearningResource(
                resource_id=f"oer-{resource_id}",
                title=raw_result.get("title", "")[:200],
                description=raw_result.get("abstract", raw_result.get("description", ""))[:500],
                url=raw_result.get("url", raw_result.get("link", "")),
                source="oer_commons",
                resource_type=resource_type,
                difficulty_level=difficulty_level,
                estimated_time=duration,
                language=language,
                tags=self._extract_topics(raw_result),
                rating=self._extract_rating(raw_result),
                metadata={
                    "license": raw_result.get("license", ""),
                    "author": raw_result.get("author", raw_result.get("creator", "")),
                    "grade_level": raw_result.get("grade_level", []),
                    "media_type": media_type,
                    "difficulty_irt": difficulty,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to normalize OER result: {e}")
            return None

    def _map_media_type(self, media_type: str) -> str:
        """Map OER media types to resource types.

        Args:
            media_type: OER Commons media type.

        Returns:
            Normalized resource type.
        """
        mapping = {
            "video": "video",
            "audio": "audio",
            "interactive": "interactive",
            "document": "document",
            "image": "image",
            "simulation": "interactive",
            "assessment": "exercise",
            "lesson_plan": "document",
            "module": "course",
            "text": "document",
            "activity": "interactive",
        }
        return mapping.get(media_type.lower(), "document")

    async def _search_oer(
        self,
        query: str,
        subject: Optional[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute search against OER Commons API.

        Args:
            query: Search query string.
            subject: Optional subject filter.
            limit: Maximum number of results.

        Returns:
            List of raw API results.
        """
        try:
            params = {
                "q": query,
                "limit": limit,
                "format": "json",
            }

            # Add subject filter
            if subject:
                subject_mapping = {
                    "matematik": "mathematics",
                    "fizik": "physics",
                    "kimya": "chemistry",
                    "biyoloji": "biology",
                    "türkçe": "language-arts",
                    "edebiyat": "literature",
                    "tarih": "history",
                    "coğrafya": "geography",
                    "felsefe": "philosophy",
                }
                oer_subject = subject_mapping.get(subject.lower(), subject)
                params["subject"] = oer_subject

            # Prefer open licenses
            params["license"] = "cc-by,cc-by-sa,public-domain"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.config.SEARCH_TIMEOUT),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"OER API returned status {resp.status}")
                        return []

                    data = await resp.json()
                    return data.get("results", data.get("items", []))

        except aiohttp.ClientError as e:
            logger.warning(f"OER API request failed: {e}")
            return []
        except Exception as e:
            logger.warning(f"Unexpected error in OER search: {e}")
            return []

    def _estimate_duration(self, result: dict[str, Any], resource_type: str) -> int:
        """Estimate reading/viewing duration in minutes.

        Args:
            result: OER API result.
            resource_type: Normalized resource type.

        Returns:
            Estimated duration in minutes.
        """
        # If duration provided (in seconds or minutes)
        if "duration" in result:
            duration = result["duration"]
            # Assume seconds if > 1000
            if duration > 1000:
                return max(1, duration // 60)
            # Assume minutes otherwise
            return max(1, int(duration))

        # Estimate based on type
        duration_estimates = {
            "video": 15,
            "audio": 20,
            "interactive": 30,
            "document": 20,
            "exercise": 15,
            "course": 60,
            "image": 5,
            "article": 10,
        }

        base = duration_estimates.get(resource_type, 15)

        # Adjust for content length if available
        word_count = result.get("word_count", 0)
        if word_count > 0:
            # Assume 200 words per minute reading speed
            estimated = word_count // 200
            return max(base, estimated)

        return base

    def _estimate_difficulty(self, result: dict[str, Any]) -> float:
        """Estimate IRT difficulty from grade level.

        Args:
            result: OER API result.

        Returns:
            IRT difficulty value between -4.0 and 4.0.
        """
        grade_levels = result.get("grade_level", [])

        if not grade_levels:
            return 0.0  # Default to intermediate

        # Map grade levels to IRT difficulty
        # K-5 = -3 to -1, 6-8 = -1 to 0, 9-12 = 0 to 2, Higher Ed = 2 to 4
        grade_mapping = {
            "K": -3.0,
            "1": -2.5,
            "2": -2.0,
            "3": -1.5,
            "4": -1.0,
            "5": -0.5,
            "6": 0.0,
            "7": 0.5,
            "8": 1.0,
            "9": 1.5,
            "10": 2.0,
            "11": 2.5,
            "12": 3.0,
            "Higher Education": 3.5,
            "Professional": 4.0,
        }

        difficulties = []
        for grade in grade_levels:
            grade_str = str(grade).strip()
            if grade_str in grade_mapping:
                difficulties.append(grade_mapping[grade_str])

        if difficulties:
            return sum(difficulties) / len(difficulties)
        return 0.0

    def _map_difficulty_to_level(self, difficulty: float) -> KnowledgeLevel:
        """Map IRT difficulty to KnowledgeLevel enum.

        Args:
            difficulty: IRT difficulty value.

        Returns:
            KnowledgeLevel enum value.
        """
        if difficulty < -2.0:
            return KnowledgeLevel.BEGINNER
        elif difficulty < -0.5:
            return KnowledgeLevel.ELEMENTARY
        elif difficulty < 1.0:
            return KnowledgeLevel.INTERMEDIATE
        elif difficulty < 2.5:
            return KnowledgeLevel.ADVANCED
        else:
            return KnowledgeLevel.EXPERT

    def _extract_topics(self, result: dict[str, Any]) -> list[str]:
        """Extract topics from OER metadata.

        Args:
            result: OER API result.

        Returns:
            List of topic strings (max 5).
        """
        topics = []

        # Subject areas
        subjects = result.get("subjects", result.get("subject_areas", []))
        if isinstance(subjects, list):
            topics.extend([str(s).title() for s in subjects[:3]])
        elif isinstance(subjects, str):
            topics.append(subjects.title())

        # Keywords
        keywords = result.get("keywords", result.get("tags", []))
        if isinstance(keywords, list):
            topics.extend([str(k).title() for k in keywords[:2]])

        return [t for t in topics if t][:5]

    def _extract_rating(self, result: dict[str, Any]) -> Optional[float]:
        """Extract rating from OER metadata.

        Args:
            result: OER API result.

        Returns:
            Rating value (0.0-5.0) or None.
        """
        rating = result.get("rating", result.get("avg_rating"))
        if rating is not None:
            try:
                rating_float = float(rating)
                # Normalize to 0.0-5.0 range
                if rating_float > 5.0:
                    rating_float = rating_float / 2.0  # Assume 0-10 scale
                return min(5.0, max(0.0, rating_float))
            except (ValueError, TypeError):
                return None
        return None

    def _is_in_difficulty_range(
        self, resource: LearningResource, range_tuple: tuple[float, float]
    ) -> bool:
        """Check if resource difficulty is within IRT range.

        Args:
            resource: Learning resource to check.
            range_tuple: Min and max IRT difficulty values.

        Returns:
            True if resource is within difficulty range.
        """
        # Get IRT difficulty from metadata
        irt_difficulty = resource.metadata.get("difficulty_irt", 0.0) if resource.metadata else 0.0
        return range_tuple[0] <= irt_difficulty <= range_tuple[1]
