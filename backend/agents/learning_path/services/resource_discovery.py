"""
Resource Discovery Service
Teknofest 2025 - Eğitim Eylemci Projesi

Unified service for discovering learning resources across multiple platforms.
Aggregates results from YouTube, Khan Academy, OER Commons, and RAG search,
providing deduplication, ranking, and fallback mechanisms.

Features:
- Multi-strategy parallel search
- Result deduplication
- Intelligent ranking
- Platform diversity
- Fallback mechanisms
"""

from __future__ import annotations

import logging
import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..models import LearningResource, KnowledgeLevel
    from ..strategies.resource_search import (
        ResourceSearchStrategy,
    )

from ..config import get_learning_path_config

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryRequest:
    """Request for resource discovery.

    Attributes:
        query: Search query string
        subject: Subject filter (e.g., "matematik")
        difficulty_range: IRT difficulty range (min, max)
        target_level: Target knowledge level
        limit: Maximum number of results to return
        preferred_platforms: List of preferred platforms
        include_videos: Include video resources
        include_documents: Include document resources
        include_exercises: Include exercise resources
    """

    query: str
    subject: Optional[str] = None
    difficulty_range: tuple[float, float] = (-4.0, 4.0)
    target_level: Optional[KnowledgeLevel] = None
    limit: int = 20
    preferred_platforms: list[str] = field(default_factory=list)
    include_videos: bool = True
    include_documents: bool = True
    include_exercises: bool = True

    def __post_init__(self) -> None:
        """Validate request after initialization."""
        if not self.query or not self.query.strip():
            raise ValueError("query cannot be empty")
        if self.limit < 1:
            raise ValueError("limit must be at least 1")
        if self.difficulty_range[0] > self.difficulty_range[1]:
            raise ValueError("invalid difficulty_range: min > max")


@dataclass
class DiscoveryResult:
    """Result of resource discovery.

    Attributes:
        resources: List of discovered resources (ranked)
        total_found: Total number of resources before limiting
        sources_searched: List of platforms searched
        errors: Dict of platform to error message
    """

    resources: list[LearningResource]
    total_found: int
    sources_searched: list[str]
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def by_platform(self) -> dict[str, list[LearningResource]]:
        """Group resources by platform.

        Returns:
            Dictionary mapping platform name to resources
        """
        grouped: dict[str, list[LearningResource]] = {}
        for resource in self.resources:
            platform = resource.source
            if platform not in grouped:
                grouped[platform] = []
            grouped[platform].append(resource)
        return grouped

    @property
    def success_rate(self) -> float:
        """Calculate success rate (sources without errors).

        Returns:
            Success rate as percentage (0.0-100.0)
        """
        if not self.sources_searched:
            return 0.0
        success_count = len(self.sources_searched) - len(self.errors)
        return (success_count / len(self.sources_searched)) * 100


class ResourceDiscoveryService:
    """Unified service for discovering learning resources across multiple platforms.

    Aggregates results from YouTube, Khan Academy, OER Commons, and RAG search,
    providing deduplication, ranking, and fallback mechanisms.

    Example:
        >>> from backend.agents.learning_path.strategies.youtube_strategy import YouTubeSearchStrategy
        >>> service = ResourceDiscoveryService()
        >>> service.add_strategy(YouTubeSearchStrategy(api_key="..."))
        >>> request = DiscoveryRequest(query="türev", subject="matematik", limit=10)
        >>> result = await service.discover(request)
        >>> print(f"Found {len(result.resources)} resources from {len(result.sources_searched)} platforms")
    """

    def __init__(
        self,
        strategies: Optional[list[ResourceSearchStrategy]] = None,
        youtube_api_key: Optional[str] = None,
    ) -> None:
        """Initialize ResourceDiscoveryService.

        Args:
            strategies: Optional list of search strategies. If not provided,
                       default strategies will be initialized.
            youtube_api_key: Optional YouTube API key for YouTube strategy.
        """
        self.config = get_learning_path_config()

        # Initialize strategies
        if strategies is not None:
            self.strategies = strategies
        else:
            self.strategies = self._initialize_default_strategies(youtube_api_key)

        # Strategy priority (lower = higher priority)
        self.strategy_priority = {
            "youtube": 1,
            "khan_academy": 2,
            "rag": 3,
            "oer_commons": 4,
        }

        logger.info(
            f"ResourceDiscoveryService initialized with {len(self.strategies)} strategies"
        )

    def _initialize_default_strategies(
        self, youtube_api_key: Optional[str] = None
    ) -> list[ResourceSearchStrategy]:
        """Initialize default search strategies.

        Args:
            youtube_api_key: Optional YouTube API key

        Returns:
            List of initialized strategies
        """
        strategies: list[ResourceSearchStrategy] = []

        # YouTube strategy
        api_key = youtube_api_key or self.config.YOUTUBE_API_KEY
        if api_key:
            try:
                from ..strategies.youtube_strategy import (
                    YouTubeSearchStrategy,
                )

                strategies.append(YouTubeSearchStrategy(api_key=api_key))
                logger.debug("Initialized YouTube strategy")
            except Exception as e:
                logger.warning(f"Failed to initialize YouTube strategy: {e}")

        # Khan Academy strategy
        try:
            from ..strategies.khan_strategy import (
                KhanSearchStrategy,
            )

            strategies.append(KhanSearchStrategy())
            logger.debug("Initialized Khan Academy strategy")
        except Exception as e:
            logger.warning(f"Failed to initialize Khan Academy strategy: {e}")

        # OER Commons strategy
        try:
            from ..strategies.oer_strategy import (
                OERSearchStrategy,
            )

            strategies.append(OERSearchStrategy())
            logger.debug("Initialized OER Commons strategy")
        except Exception as e:
            logger.warning(f"Failed to initialize OER strategy: {e}")

        # RAG Search strategy
        try:
            from ..strategies.rag_strategy import (
                RAGSearchStrategy,
            )

            strategies.append(RAGSearchStrategy())
            logger.debug("Initialized RAG strategy")
        except Exception as e:
            logger.warning(f"Failed to initialize RAG strategy: {e}")

        return strategies

    async def discover(self, request: DiscoveryRequest) -> DiscoveryResult:
        """Discover learning resources across all platforms.

        Args:
            request: Discovery request with query and filters

        Returns:
            DiscoveryResult with aggregated and ranked resources

        Example:
            >>> request = DiscoveryRequest(query="türev kavramı", limit=10)
            >>> result = await service.discover(request)
            >>> print(f"Found {len(result.resources)} resources")
        """
        logger.info(f"Discovering resources for query: {request.query}")

        # Filter strategies by platform preference
        active_strategies = self._filter_strategies(request)

        if not active_strategies:
            logger.warning("No active strategies available")
            return DiscoveryResult(resources=[], total_found=0, sources_searched=[])

        # Search all strategies in parallel
        all_resources: list[LearningResource] = []
        errors: dict[str, str] = {}
        sources_searched: list[str] = []

        # Create search tasks
        tasks = []
        for strategy in active_strategies:
            platform = strategy.get_platform_name()
            sources_searched.append(platform)
            tasks.append(self._search_with_strategy(strategy, request))

        # Wait for all searches to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for strategy, result in zip(active_strategies, results):
            platform = strategy.get_platform_name()

            if isinstance(result, Exception):
                logger.warning(f"Strategy {platform} failed: {result}")
                errors[platform] = str(result)
            elif isinstance(result, list):
                logger.debug(f"Strategy {platform} returned {len(result)} resources")
                all_resources.extend(result)
            else:
                logger.warning(
                    f"Strategy {platform} returned unexpected type: {type(result)}"
                )

        # Deduplicate
        unique_resources = self._deduplicate(all_resources)

        # Rank resources
        ranked_resources = self._rank_resources(unique_resources, request)

        # Limit results
        final_resources = ranked_resources[: request.limit]

        logger.info(
            f"Discovery complete: {len(final_resources)} resources from {len(sources_searched)} sources"
        )

        return DiscoveryResult(
            resources=final_resources,
            total_found=len(unique_resources),
            sources_searched=sources_searched,
            errors=errors,
        )

    async def _search_with_strategy(
        self, strategy: ResourceSearchStrategy, request: DiscoveryRequest
    ) -> list[LearningResource]:
        """Execute search with a single strategy.

        Args:
            strategy: Search strategy to use
            request: Discovery request

        Returns:
            List of resources from this strategy

        Raises:
            Exception: Any exception from the strategy
        """
        try:
            return await strategy.search(
                query=request.query,
                subject=request.subject,
                difficulty_range=request.difficulty_range,
                limit=request.limit,
            )
        except Exception as e:
            logger.warning(f"Strategy search failed: {e}")
            raise

    def _filter_strategies(
        self, request: DiscoveryRequest
    ) -> list[ResourceSearchStrategy]:
        """Filter strategies based on request preferences.

        Args:
            request: Discovery request with platform preferences

        Returns:
            List of active strategies
        """
        if not request.preferred_platforms:
            return self.strategies

        return [
            s
            for s in self.strategies
            if s.get_platform_name() in request.preferred_platforms
        ]

    def _deduplicate(
        self, resources: list[LearningResource]
    ) -> list[LearningResource]:
        """Remove duplicate resources based on URL and title similarity.

        Args:
            resources: List of resources to deduplicate

        Returns:
            List of unique resources
        """
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        unique: list[LearningResource] = []

        for resource in resources:
            # Check URL
            url = resource.url
            if url and url in seen_urls:
                continue

            # Check title similarity (normalized)
            title = resource.title
            title_normalized = title.lower().strip()
            if title_normalized and title_normalized in seen_titles:
                continue

            # Add to unique
            unique.append(resource)
            if url:
                seen_urls.add(url)
            if title_normalized:
                seen_titles.add(title_normalized)

        logger.debug(
            f"Deduplication: {len(resources)} -> {len(unique)} resources "
            f"({len(resources) - len(unique)} duplicates removed)"
        )

        return unique

    def _rank_resources(
        self, resources: list[LearningResource], request: DiscoveryRequest
    ) -> list[LearningResource]:
        """Rank resources by relevance and diversity.

        Args:
            resources: List of resources to rank
            request: Original discovery request

        Returns:
            Sorted list of resources (best first)
        """

        def score_resource(resource: LearningResource) -> float:
            """Calculate relevance score for a resource."""
            score = 0.0

            # Platform priority (higher for lower priority number)
            platform = resource.source
            priority = self.strategy_priority.get(platform.lower(), 5)
            score += (5 - priority) * 10

            # Difficulty match (if target level provided)
            if request.target_level:
                resource_diff = self._level_to_difficulty(resource.difficulty_level)
                target_diff = self._level_to_difficulty(request.target_level)
                diff_distance = abs(resource_diff - target_diff)
                score += max(0, 20 - diff_distance * 5)  # Up to 20 points

            # Duration preference (shorter is better for videos)
            duration = resource.estimated_time
            if duration > 0:
                if duration <= 15:
                    score += 10
                elif duration <= 30:
                    score += 5

            # Quality indicators
            if resource.rating and resource.rating >= 4.0:
                score += 10

            # Language match (prefer Turkish for Turkish queries)
            if resource.language == "tr":
                score += 5

            return score

        return sorted(resources, key=score_resource, reverse=True)

    def _level_to_difficulty(self, level: KnowledgeLevel) -> float:
        """Convert KnowledgeLevel to IRT difficulty.

        Args:
            level: Knowledge level enum

        Returns:
            IRT difficulty value
        """
        from ..models import KnowledgeLevel

        mapping = {
            KnowledgeLevel.BEGINNER: -3.0,
            KnowledgeLevel.ELEMENTARY: -1.5,
            KnowledgeLevel.INTERMEDIATE: 0.0,
            KnowledgeLevel.ADVANCED: 1.5,
            KnowledgeLevel.EXPERT: 3.0,
        }
        return mapping.get(level, 0.0)

    async def find_similar(
        self, resource: LearningResource, limit: int = 5
    ) -> list[LearningResource]:
        """Find resources similar to a given resource.

        Args:
            resource: Reference resource
            limit: Maximum number of similar resources to return

        Returns:
            List of similar resources

        Example:
            >>> similar = await service.find_similar(resource, limit=5)
            >>> print(f"Found {len(similar)} similar resources")
        """
        # Use title as search query
        query = resource.title
        if not query:
            return []

        # Search with limited platforms
        request = DiscoveryRequest(
            query=query,
            limit=limit * 2,  # Get extra to filter out the original
        )

        result = await self.discover(request)

        # Filter out the original resource
        original_url = resource.url
        similar = [r for r in result.resources if r.url != original_url]

        return similar[:limit]

    def add_strategy(self, strategy: ResourceSearchStrategy) -> None:
        """Add a new search strategy.

        Args:
            strategy: Search strategy to add
        """
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.get_platform_name()}")

    def remove_strategy(self, platform: str) -> bool:
        """Remove a strategy by platform name.

        Args:
            platform: Platform name to remove

        Returns:
            True if strategy was removed, False if not found
        """
        for i, strategy in enumerate(self.strategies):
            if strategy.get_platform_name() == platform:
                self.strategies.pop(i)
                logger.info(f"Removed strategy: {platform}")
                return True
        return False

    def get_available_platforms(self) -> list[str]:
        """Get list of available platforms.

        Returns:
            List of platform names
        """
        return [s.get_platform_name() for s in self.strategies]
