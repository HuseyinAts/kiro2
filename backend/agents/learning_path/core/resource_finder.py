"""
Resource Finding and Ranking Module
Teknofest 2025 - Eğitim Eylemci Projesi

Extracted from LearningPathAgent (lines 728-1108, 1597-1818)

This module handles:
- Learning resource discovery
- Multi-source search (YouTube, Khan Academy, OER)
- Resource ranking and filtering
- Learning style matching
- Difficulty-based filtering

Responsibilities:
- Search resources across multiple platforms
- Rank resources by relevance and quality
- Filter by learning style preferences
- Match difficulty to student level
"""

import hashlib
import logging
from typing import Any

from cachetools import TTLCache

from services.subject_relevance_scorer import normalize_tr

from ..models import KnowledgeLevel, LearningResource, LearningStyle
from ..utils.duration_parser import parse_iso8601_duration

logger = logging.getLogger(__name__)


class ResourceFinder:
    """
    Resource Finder - Discovers and ranks learning resources

    This class searches multiple platforms for learning resources
    and ranks them based on relevance, quality, and student preferences.

    Uses dependency injection for external services.
    """

    def __init__(
        self,
        youtube_service=None,
        khan_service=None,
        oer_service=None,
        resource_ranker=None,
        rag_service=None,
    ):
        """
        Initialize ResourceFinder with injected dependencies

        Args:
            youtube_service: YouTube API service (optional)
            khan_service: Khan Academy API service (optional)
            oer_service: OER service (optional)
            resource_ranker: Resource ranking service (optional)
            rag_service: RAG service for semantic search (optional)
        """
        self.youtube = youtube_service
        self.khan = khan_service
        self.oer = oer_service
        self.ranker = resource_ranker
        self.rag = rag_service

        # Cache for search results with TTL to prevent memory leak
        # Max 500 search results, 15 minute TTL
        self.resource_cache: TTLCache = TTLCache(maxsize=500, ttl=900)

        logger.info("ResourceFinder initialized with TTLCache (maxsize=500, ttl=900s)")

    async def search_resources(
        self,
        topic: str,
        subjects: list[str] | None = None,
        difficulty: KnowledgeLevel | None = None,
        learning_style: LearningStyle | None = None,
        count: int = 10,
        language: str = "tr",
    ) -> list[LearningResource]:
        """
        Search for learning resources across multiple platforms

        Main method that orchestrates search across all available platforms.

        Args:
            topic: Search topic/query
            subjects: Related subjects (optional)
            difficulty: Difficulty level filter (optional)
            learning_style: Learning style preference (optional)
            count: Maximum number of resources to return
            language: Content language (default: "tr")

        Returns:
            List of LearningResource objects, ranked by relevance

        Example:
            >>> finder = ResourceFinder(youtube_service, khan_service)
            >>> resources = await finder.search_resources(
            ...     "Türev",
            ...     subjects=["Matematik"],
            ...     difficulty=KnowledgeLevel.INTERMEDIATE,
            ...     count=10
            ... )
        """
        # Validation
        if not topic or not isinstance(topic, str):
            raise ValueError("topic must be a non-empty string")
        if count < 1 or count > 50:
            raise ValueError("count must be between 1 and 50")

        try:
            logger.info(
                f"Searching resources: topic='{topic}', difficulty={difficulty}, "
                f"style={learning_style}, count={count}"
            )

            # Check cache first
            cache_key = self._generate_cache_key(
                topic, subjects, difficulty, learning_style, language
            )
            if cache_key in self.resource_cache:
                logger.info(f"Returning cached results for: {cache_key}")
                cached_resources = self.resource_cache[cache_key]
                return cached_resources[:count]

            # Collect resources from all sources
            all_resources = []

            # 1. YouTube search
            if self.youtube:
                youtube_resources = await self._search_youtube(topic, language, count)
                all_resources.extend(youtube_resources)

            # 2. Khan Academy search
            if self.khan:
                khan_resources = await self._search_khan_academy(topic, subjects)
                all_resources.extend(khan_resources)

            # 3. OER search
            if self.oer:
                oer_resources = await self._search_oer(topic, subjects)
                all_resources.extend(oer_resources)

            # 4. RAG search (if available) - with subject and difficulty filtering
            if self.rag:
                difficulty_range = (
                    self._get_difficulty_range(difficulty) if difficulty else None
                )
                rag_resources = await self._search_rag(
                    query=topic,
                    subject=subjects[0] if subjects else None,
                    difficulty_range=difficulty_range,
                    count=count,
                )
                all_resources.extend(rag_resources)

            logger.info(f"Found {len(all_resources)} resources from all sources")

            # Filter by difficulty if specified
            if difficulty:
                all_resources = self._filter_by_difficulty(all_resources, difficulty)

            # Filter by learning style if specified
            if learning_style:
                all_resources = self._filter_by_style(all_resources, learning_style)

            # Rank resources
            ranked_resources = await self._rank_resources(
                all_resources, topic, learning_style
            )

            # Cache results
            self.resource_cache[cache_key] = ranked_resources

            # Return top N
            result = ranked_resources[:count]

            logger.info(f"Returning {len(result)} ranked resources")
            return result

        except Exception as e:
            logger.error(f"Search resources error: {e!s}")
            raise

    async def search_by_topic(
        self, topic: str, count: int = 5
    ) -> list[LearningResource]:
        """
        Simple topic search without filters

        Args:
            topic: Search topic
            count: Maximum results

        Returns:
            List of resources
        """
        return await self.search_resources(topic, count=count)

    async def search_by_difficulty(
        self, topic: str, difficulty: KnowledgeLevel, count: int = 10
    ) -> list[LearningResource]:
        """
        Search resources filtered by difficulty level

        Args:
            topic: Search topic
            difficulty: Difficulty level
            count: Maximum results

        Returns:
            List of resources matching difficulty
        """
        return await self.search_resources(topic, difficulty=difficulty, count=count)

    async def search_by_style(
        self, topic: str, learning_style: LearningStyle, count: int = 10
    ) -> list[LearningResource]:
        """
        Search resources filtered by learning style

        Args:
            topic: Search topic
            learning_style: Preferred learning style
            count: Maximum results

        Returns:
            List of resources matching learning style
        """
        return await self.search_resources(
            topic, learning_style=learning_style, count=count
        )

    def get_style_recommendations(
        self, resources: list[LearningResource], learning_style: LearningStyle
    ) -> list[dict[str, Any]]:
        """
        Get recommendations based on learning style

        Args:
            resources: List of resources
            learning_style: Preferred learning style

        Returns:
            List of recommendations with match scores
        """
        recommendations = []

        for resource in resources:
            match_score = self._calculate_style_match_score(
                resource.resource_type, learning_style
            )

            recommendations.append(
                {
                    "resource": resource,
                    "match_score": match_score,
                    "match_description": self._get_style_match_description(match_score),
                }
            )

        # Sort by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)

        return recommendations

    # Private methods for external service integrations

    async def _search_youtube(
        self, query: str, language: str, max_results: int
    ) -> list[LearningResource]:
        """Search YouTube for videos"""
        try:
            videos = await self.youtube.search(
                query=query, max_results=min(max_results, 10), language=language
            )

            resources = []
            for video in videos:
                resource = LearningResource(
                    resource_id=f"yt_{video.get('id', '')}",
                    title=video.get("title", ""),
                    source="YouTube",
                    url=video.get("url", ""),
                    resource_type="video",
                    difficulty_level=KnowledgeLevel.INTERMEDIATE,  # Default
                    estimated_time=self._parse_youtube_duration(video.get("duration")),
                    language=language,
                    description=video.get("description", "")[:500],
                    tags=[query],
                    rating=video.get("rating"),
                    metadata={
                        "views": video.get("views", 0),
                        "likes": video.get("likes", 0),
                        "channel": video.get("channel", ""),
                        "published_at": video.get("published_at", ""),
                    },
                )
                resources.append(resource)

            logger.info(f"YouTube search returned {len(resources)} videos")
            return resources

        except Exception as e:
            logger.error(f"YouTube search error: {e!s}")
            return []

    async def _search_khan_academy(
        self, topic: str, subjects: list[str] | None
    ) -> list[LearningResource]:
        """Search Khan Academy for resources"""
        try:
            results = await self.khan.search(query=topic, subjects=subjects)

            resources = []
            for item in results:
                resource = LearningResource(
                    resource_id=f"khan_{item.get('id', '')}",
                    title=item.get("title", ""),
                    source="Khan Academy",
                    url=item.get("url", ""),
                    resource_type=item.get("type", "course"),
                    difficulty_level=self._parse_khan_difficulty(
                        item.get("difficulty")
                    ),
                    estimated_time=item.get("duration", 30),
                    language="tr" if item.get("language") == "turkish" else "en",
                    description=item.get("description", ""),
                    tags=subjects or [topic],
                    rating=item.get("rating"),
                    metadata=item.get("metadata", {}),
                )
                resources.append(resource)

            logger.info(f"Khan Academy search returned {len(resources)} resources")
            return resources

        except Exception as e:
            logger.error(f"Khan Academy search error: {e!s}")
            return []

    async def _search_oer(
        self, topic: str, subjects: list[str] | None
    ) -> list[LearningResource]:
        """Search Open Educational Resources"""
        try:
            results = await self.oer.search(query=topic, subjects=subjects)

            resources = []
            for item in results:
                resource = LearningResource(
                    resource_id=f"oer_{item.resource_id}",
                    title=item.title,
                    source="OER",
                    url=item.url,
                    resource_type=item.resource_type,
                    difficulty_level=item.difficulty_level,
                    estimated_time=item.estimated_time,
                    language=item.language,
                    description=item.description,
                    tags=item.tags,
                    rating=item.rating,
                    metadata=item.metadata,
                )
                resources.append(resource)

            logger.info(f"OER search returned {len(resources)} resources")
            return resources

        except Exception as e:
            logger.error(f"OER search error: {e!s}")
            return []

    async def _search_rag(
        self,
        query: str,
        subject: str | None = None,
        difficulty_range: tuple | None = None,
        count: int = 10,
    ) -> list[LearningResource]:
        """
        Search using RAG service for semantic matching.

        Args:
            query: Search query string
            subject: Subject filter (e.g., 'matematik', 'fizik')
            difficulty_range: IRT difficulty range tuple (min, max), e.g., (-2.0, 0.5)
            count: Maximum number of results to return

        Returns:
            List of LearningResource objects from RAG search
        """
        try:
            if not self.rag or not hasattr(self.rag, "search"):
                logger.debug("RAG service not available or no search method")
                return []

            # Build search kwargs based on what the RAG service supports
            search_kwargs: dict[str, Any] = {
                "query": query,
                "limit": count,
            }

            # Add optional filters if provided and service supports them
            if subject:
                search_kwargs["subject"] = subject
            if difficulty_range:
                search_kwargs["difficulty_range"] = difficulty_range

            resources = await self.rag.search(**search_kwargs)
            logger.info(
                f"RAG search returned {len(resources)} resources for "
                f"query='{query}', subject={subject}, count={count}"
            )
            return resources

        except TypeError as te:
            # Fallback if RAG service doesn't support all params
            logger.warning(f"RAG search param error, trying simple search: {te}")
            try:
                resources = await self.rag.search(query=query, limit=count)
                return resources
            except Exception as e2:
                logger.error(f"RAG simple search also failed: {e2}")
                return []

        except Exception as e:
            logger.error(f"RAG search error: {e!s}")
            return []

    def _get_difficulty_range(self, difficulty: KnowledgeLevel) -> tuple:
        """
        Map KnowledgeLevel to IRT difficulty range.

        IRT difficulty scale: -4.0 (easiest) to +4.0 (hardest)

        Args:
            difficulty: KnowledgeLevel enum value

        Returns:
            Tuple of (min_difficulty, max_difficulty)
        """
        ranges = {
            KnowledgeLevel.BEGINNER: (-4.0, -2.0),
            KnowledgeLevel.ELEMENTARY: (-2.0, -0.5),
            KnowledgeLevel.INTERMEDIATE: (-0.5, 0.5),
            KnowledgeLevel.ADVANCED: (0.5, 2.0),
            KnowledgeLevel.EXPERT: (2.0, 4.0),
        }
        return ranges.get(difficulty, (-4.0, 4.0))

    # Filtering methods

    def _filter_by_difficulty(
        self, resources: list[LearningResource], target_difficulty: KnowledgeLevel
    ) -> list[LearningResource]:
        """Filter resources by difficulty level with tolerance"""
        # Allow resources one level above or below
        difficulty_order = [
            KnowledgeLevel.BEGINNER,
            KnowledgeLevel.ELEMENTARY,
            KnowledgeLevel.INTERMEDIATE,
            KnowledgeLevel.ADVANCED,
            KnowledgeLevel.EXPERT,
        ]

        target_index = difficulty_order.index(target_difficulty)
        allowed_range = range(
            max(0, target_index - 1), min(len(difficulty_order), target_index + 2)
        )

        filtered = [
            r
            for r in resources
            if difficulty_order.index(r.difficulty_level) in allowed_range
        ]

        logger.info(f"Filtered by difficulty: {len(resources)} → {len(filtered)}")
        return filtered

    def _filter_by_style(
        self, resources: list[LearningResource], learning_style: LearningStyle
    ) -> list[LearningResource]:
        """Filter resources by learning style preference"""
        if learning_style == LearningStyle.MIXED:
            return resources  # Mixed learners can use any type

        filtered = [r for r in resources if r.matches_style(learning_style)]

        # If too few results, include some other types
        if len(filtered) < 3:
            filtered = resources

        logger.info(f"Filtered by style: {len(resources)} → {len(filtered)}")
        return filtered

    # Ranking methods

    async def _rank_resources(
        self,
        resources: list[LearningResource],
        query: str,
        learning_style: LearningStyle | None = None,
    ) -> list[LearningResource]:
        """Rank resources by relevance and quality"""
        if not resources:
            return []

        if self.ranker:
            # Use unified resource ranker if available
            try:
                ranked = await self.ranker.rank_resources(
                    resources=resources,
                    query=query,
                    preferences={
                        "learning_style": learning_style.value
                        if learning_style
                        else None
                    },
                )
                return ranked
            except Exception as e:
                logger.warning(f"Ranker failed, using simple ranking: {e!s}")

        # Simple ranking fallback
        scored_resources = []
        for resource in resources:
            score = self._calculate_simple_score(resource, query, learning_style)
            scored_resources.append((resource, score))

        # Sort by score descending
        scored_resources.sort(key=lambda x: x[1], reverse=True)

        return [r for r, _ in scored_resources]

    def _calculate_simple_score(
        self,
        resource: LearningResource,
        query: str,
        learning_style: LearningStyle | None,
    ) -> float:
        """Calculate simple relevance score"""
        score = 0.0

        # Title relevance (40%) — Turkish casefold for İ/I

        if normalize_tr(query) in normalize_tr(resource.title):
            score += 0.4

        # Description relevance (20%)
        if normalize_tr(query) in normalize_tr(resource.description):
            score += 0.2

        # Learning style match (20%)
        if learning_style and resource.matches_style(learning_style):
            score += 0.2

        # Quality indicators (20%)
        if resource.rating:
            score += (resource.rating / 5.0) * 0.2

        return score

    # Utility methods

    def _calculate_style_match_score(
        self, content_type: str, learning_style: LearningStyle
    ) -> float:
        """Calculate how well content type matches learning style"""
        style_scores = {
            LearningStyle.VISUAL: {
                "video": 1.0,
                "infographic": 0.9,
                "diagram": 0.8,
                "article": 0.3,
                "audio": 0.1,
            },
            LearningStyle.AUDITORY: {
                "audio": 1.0,
                "podcast": 1.0,
                "video": 0.7,
                "article": 0.3,
            },
            LearningStyle.READING: {
                "article": 1.0,
                "book": 1.0,
                "text": 0.9,
                "video": 0.4,
            },
            LearningStyle.KINESTHETIC: {
                "practice": 1.0,
                "quiz": 0.9,
                "interactive": 0.9,
                "video": 0.5,
            },
        }

        if learning_style == LearningStyle.MIXED:
            return 0.7  # Mixed learners have moderate match with all types

        scores = style_scores.get(learning_style, {})
        return scores.get(content_type.lower(), 0.5)  # Default 0.5

    def _get_style_match_description(self, score: float) -> str:
        """Get human-readable description of match score"""
        if score >= 0.8:
            return "Mükemmel uyum"
        if score >= 0.6:
            return "İyi uyum"
        if score >= 0.4:
            return "Orta uyum"
        return "Düşük uyum"

    def _parse_youtube_duration(self, duration: str | None) -> int:
        """Parse YouTube duration string to minutes using ISO 8601 parser"""
        return parse_iso8601_duration(duration, default=10)

    def _parse_khan_difficulty(self, difficulty: str | None) -> KnowledgeLevel:
        """Parse Khan Academy difficulty to KnowledgeLevel"""
        difficulty_mapping = {
            "beginner": KnowledgeLevel.BEGINNER,
            "easy": KnowledgeLevel.ELEMENTARY,
            "medium": KnowledgeLevel.INTERMEDIATE,
            "hard": KnowledgeLevel.ADVANCED,
            "expert": KnowledgeLevel.EXPERT,
        }

        if not difficulty:
            return KnowledgeLevel.INTERMEDIATE

        return difficulty_mapping.get(difficulty.lower(), KnowledgeLevel.INTERMEDIATE)

    def _generate_cache_key(
        self,
        topic: str,
        subjects: list[str] | None,
        difficulty: KnowledgeLevel | None,
        learning_style: LearningStyle | None,
        language: str,
    ) -> str:
        """Generate cache key using hash to avoid collision."""

        key_parts = [
            topic,
            str(subjects or []),
            difficulty.value if difficulty else "none",
            learning_style.value if learning_style else "none",
            language,
        ]
        digest = hashlib.md5("\x00".join(key_parts).encode()).hexdigest()
        return f"rf:{digest}"
