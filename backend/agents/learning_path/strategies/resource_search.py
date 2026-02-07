"""
ResourceSearchStrategy Interface for Learning Path Agent
Teknofest 2025 - Eğitim Eylemci Projesi

This module defines the abstract base class for resource search strategies.
Each strategy represents a different platform (YouTube, Khan Academy, Wikipedia, etc.)
and provides a unified interface for searching and normalizing learning resources.

Usage:
    class YouTubeSearchStrategy(ResourceSearchStrategy):
        async def search(self, query: str, **filters) -> List[LearningResource]:
            # Implementation specific to YouTube
            pass

        def get_platform_name(self) -> str:
            return "YouTube"

        def normalize_result(self, raw_result: Dict[str, Any]) -> LearningResource:
            # Convert YouTube API response to LearningResource
            pass
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from backend.agents.learning_path.models import LearningResource


class ResourceSearchStrategy(ABC):
    """
    Abstract base class for resource search strategies.

    Each concrete implementation represents a specific learning resource platform
    (e.g., YouTube, Khan Academy, Wikipedia, OER Commons) and provides:
    1. Search functionality with platform-specific filters
    2. Platform identification
    3. Result normalization to LearningResource format
    4. Optional priority for multi-platform searches

    Attributes:
        None (stateless by default, but subclasses may add state)
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        **filters: Any
    ) -> List[LearningResource]:
        """
        Search for learning resources on the platform.

        Args:
            query: Search query string (e.g., "matematik türev")
            **filters: Platform-specific filters:
                - max_results (int): Maximum number of results to return
                - language (str): Content language (e.g., "tr", "en")
                - difficulty (str): Difficulty level filter
                - duration_min (int): Minimum duration in minutes
                - duration_max (int): Maximum duration in minutes
                - rating_min (float): Minimum rating threshold
                - resource_type (str): Type filter (video, article, etc.)

        Returns:
            List of normalized LearningResource objects

        Raises:
            ValueError: If query is empty or invalid
            ConnectionError: If platform API is unreachable
            RuntimeError: If search fails for other reasons

        Example:
            >>> strategy = YouTubeSearchStrategy()
            >>> resources = await strategy.search(
            ...     "matematik türev",
            ...     max_results=10,
            ...     language="tr",
            ...     duration_max=20
            ... )
            >>> len(resources)
            10
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the platform name for this strategy.

        Returns:
            Platform name (e.g., "YouTube", "Khan Academy", "Wikipedia")

        Example:
            >>> strategy = YouTubeSearchStrategy()
            >>> strategy.get_platform_name()
            'YouTube'
        """
        pass

    @abstractmethod
    def normalize_result(self, raw_result: Dict[str, Any]) -> LearningResource:
        """
        Normalize a platform-specific result to LearningResource format.

        This method converts the raw API response from the platform into
        a standardized LearningResource object that can be used by the
        learning path agent.

        Args:
            raw_result: Platform-specific result dictionary containing:
                - Required fields: id, title, url
                - Optional fields: description, duration, rating, etc.

        Returns:
            Normalized LearningResource object

        Raises:
            ValueError: If required fields are missing or invalid
            KeyError: If expected fields are not in raw_result

        Example:
            >>> raw = {
            ...     "id": "abc123",
            ...     "title": "Türev Kavramı",
            ...     "url": "https://youtube.com/watch?v=abc123",
            ...     "duration": 900,  # seconds
            ...     "views": 10000
            ... }
            >>> resource = strategy.normalize_result(raw)
            >>> resource.title
            'Türev Kavramı'
            >>> resource.estimated_time
            15
        """
        pass

    def get_priority(self) -> int:
        """
        Get the priority of this strategy for multi-platform searches.

        Lower numbers indicate higher priority. When multiple platforms
        are searched simultaneously, higher-priority strategies are
        consulted first for resource selection.

        Returns:
            Priority value (default: 0 for equal priority)
            Negative values: Higher priority (checked first)
            Positive values: Lower priority (checked later)

        Example:
            >>> youtube_strategy.get_priority()
            -1  # YouTube has higher priority
            >>> wikipedia_strategy.get_priority()
            0  # Wikipedia has default priority
            >>> generic_strategy.get_priority()
            1  # Generic has lower priority
        """
        return 0  # Default priority (equal with others)

    def validate_query(self, query: str) -> None:
        """
        Validate search query before processing.

        Args:
            query: Search query string

        Raises:
            ValueError: If query is invalid (empty, too short, etc.)

        Note:
            This is a helper method provided for subclasses.
            Override if custom validation logic is needed.
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        if len(query.strip()) < 2:
            raise ValueError("Search query too short (minimum 2 characters)")

    def apply_common_filters(
        self,
        results: List[LearningResource],
        **filters: Any
    ) -> List[LearningResource]:
        """
        Apply common filters to search results.

        This helper method provides standard filtering logic that can be
        reused across different strategy implementations.

        Args:
            results: List of LearningResource objects to filter
            **filters: Filter criteria:
                - max_results (int): Maximum number of results
                - language (str): Filter by language
                - difficulty (str): Filter by difficulty level
                - rating_min (float): Minimum rating threshold
                - duration_min (int): Minimum duration in minutes
                - duration_max (int): Maximum duration in minutes

        Returns:
            Filtered list of LearningResource objects

        Example:
            >>> filtered = strategy.apply_common_filters(
            ...     all_results,
            ...     max_results=5,
            ...     language="tr",
            ...     rating_min=3.5
            ... )
        """
        filtered = results

        # Language filter
        if "language" in filters:
            language = filters["language"]
            filtered = [r for r in filtered if r.language == language]

        # Rating filter
        if "rating_min" in filters:
            rating_min = filters["rating_min"]
            filtered = [
                r for r in filtered
                if r.rating is not None and r.rating >= rating_min
            ]

        # Duration filters
        if "duration_min" in filters:
            duration_min = filters["duration_min"]
            filtered = [r for r in filtered if r.estimated_time >= duration_min]

        if "duration_max" in filters:
            duration_max = filters["duration_max"]
            filtered = [r for r in filtered if r.estimated_time <= duration_max]

        # Difficulty filter
        if "difficulty" in filters:
            from backend.agents.learning_path.models import KnowledgeLevel
            difficulty = filters["difficulty"]
            if isinstance(difficulty, str):
                difficulty_level = KnowledgeLevel(difficulty)
                filtered = [
                    r for r in filtered
                    if r.difficulty_level == difficulty_level
                ]

        # Max results limit
        if "max_results" in filters:
            max_results = filters["max_results"]
            filtered = filtered[:max_results]

        return filtered
