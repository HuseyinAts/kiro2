"""
RAG Search Strategy for Learning Path Agent
Teknofest 2025 - Eğitim Eylemci Projesi

This module wraps the RAGSearchService into the Strategy pattern.
Provides semantic search capabilities using ChromaDB via MCP server.

Features:
- Strategy pattern compliance
- Lazy initialization of RAG service
- LearningResource normalization
- Similar resource search
- Resource indexing support
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .resource_search import ResourceSearchStrategy
from ..core.rag_search import RAGSearchService
from ..config import get_learning_path_config
from ..models import LearningResource, KnowledgeLevel

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RAGSearchStrategy(ResourceSearchStrategy):
    """
    RAG-based search strategy using ChromaDB semantic search.

    This strategy wraps RAGSearchService to provide Strategy pattern compliance.
    It uses semantic search over the ChromaDB vector database to find relevant
    learning resources based on query embeddings.

    Features:
        - Semantic search via ChromaDB MCP server
        - Lazy initialization for performance
        - Metadata filtering (subject, difficulty)
        - Similar resource discovery
        - Resource indexing support

    Example:
        >>> strategy = RAGSearchStrategy()
        >>> resources = await strategy.search(
        ...     query="trigonometri",
        ...     subject="matematik",
        ...     difficulty_range=(-2.0, 0.0),
        ...     limit=10
        ... )
    """

    def __init__(self, rag_service: Optional[RAGSearchService] = None):
        """
        Initialize RAG search strategy.

        Args:
            rag_service: Optional RAGSearchService instance (for testing/mocking)
        """
        self.config = get_learning_path_config()
        self._rag_service = rag_service

    @property
    def rag_service(self) -> RAGSearchService:
        """
        Lazy initialization of RAG service.

        Returns:
            RAGSearchService instance

        Note:
            Service is only initialized when first accessed,
            improving startup performance.
        """
        if self._rag_service is None:
            self._rag_service = RAGSearchService()
        return self._rag_service

    async def search(
        self,
        query: str,
        subject: Optional[str] = None,
        difficulty_range: tuple = (-4.0, 4.0),
        limit: int = 10,
        **filters: Any
    ) -> List[LearningResource]:
        """
        Search RAG database for learning resources.

        Delegates to RAGSearchService for ChromaDB semantic search.
        Validates query and applies difficulty range filtering.

        Args:
            query: Search query string (Turkish)
            subject: Optional subject filter (e.g., "matematik", "fizik")
            difficulty_range: (min, max) IRT difficulty range
            limit: Maximum number of results
            **filters: Additional filters (for interface compliance)

        Returns:
            List of LearningResource objects

        Raises:
            ValueError: If query is invalid

        Example:
            >>> resources = await strategy.search(
            ...     "türev kavramı",
            ...     subject="matematik",
            ...     difficulty_range=(-1.0, 1.0),
            ...     limit=5
            ... )
        """
        try:
            # Validate query
            self.validate_query(query)

            # Extract difficulty range with validation
            diff_min, diff_max = difficulty_range
            if diff_min > diff_max:
                logger.warning(f"Invalid difficulty range: {difficulty_range}, swapping")
                diff_min, diff_max = diff_max, diff_min

            # Delegate to RAGSearchService
            resources = await self.rag_service.search(
                query=query,
                subject=subject,
                difficulty_range=(diff_min, diff_max),
                limit=limit,
            )

            logger.debug(
                f"RAG search returned {len(resources)} resources for query: {query}"
            )
            return resources

        except ValueError as e:
            logger.error(f"Invalid query for RAG search: {e}")
            raise
        except Exception as e:
            logger.warning(f"RAG search strategy failed: {e}")
            return []

    def get_platform_name(self) -> str:
        """
        Get the platform name for this strategy.

        Returns:
            Platform name ("rag")
        """
        return "rag"

    def normalize_result(
        self, raw_result: Dict[str, Any]
    ) -> Optional[LearningResource]:
        """
        Convert RAG result to LearningResource.

        Note: RAGSearchService already returns LearningResource objects,
        so this is mainly for interface compliance and edge cases where
        raw dict results need to be converted.

        Args:
            raw_result: Raw ChromaDB result or dict

        Returns:
            LearningResource or None if conversion fails

        Example:
            >>> raw = {
            ...     "id": "question_123",
            ...     "title": "Trigonometri Sorusu",
            ...     "content": "Soru metni...",
            ...     "difficulty": -0.5
            ... }
            >>> resource = strategy.normalize_result(raw)
        """
        try:
            # If already a LearningResource, return as-is
            if isinstance(raw_result, LearningResource):
                return raw_result

            # If dict, convert
            resource_id = raw_result.get("id", "")
            title = raw_result.get("title", "Soru")
            content = raw_result.get("content", raw_result.get("description", ""))
            difficulty = float(raw_result.get("difficulty", 0.0))
            topics = raw_result.get("topics", [])

            # Generate description (first 500 chars)
            description = content[:500] if content else ""

            # Generate URL (must not be empty per LearningResource validation)
            url = (
                raw_result.get("url")
                or f"/questions/{resource_id}"
                if resource_id
                else "/questions/unknown"
            )

            # Map IRT difficulty to KnowledgeLevel
            difficulty_level = self._map_difficulty_to_level(difficulty)

            return LearningResource(
                resource_id=resource_id or f"rag_{hash(content)}",
                title=title,
                source="rag",
                url=url,
                resource_type=raw_result.get("resource_type", "question"),
                difficulty_level=difficulty_level,
                estimated_time=raw_result.get(
                    "duration", self.config.DEFAULT_VIDEO_DURATION
                ),
                language=raw_result.get("language", "tr"),
                description=description,
                tags=topics if isinstance(topics, list) else [],
                rating=raw_result.get("rating"),
                metadata=raw_result.get("metadata", {}),
            )

        except Exception as e:
            logger.warning(f"Failed to normalize RAG result: {e}")
            return None

    async def search_similar(
        self, resource_id: str, limit: int = 5
    ) -> List[LearningResource]:
        """
        Find similar resources based on a reference resource.

        This is a RAG-specific feature that leverages embedding similarity
        in the ChromaDB vector database.

        Args:
            resource_id: Reference resource ID
            limit: Maximum number of similar resources

        Returns:
            List of similar LearningResource objects

        Example:
            >>> similar = await strategy.search_similar("question_123", limit=5)
        """
        try:
            # Check if RAG service supports similar search
            if hasattr(self.rag_service, "find_similar"):
                return await self.rag_service.find_similar(resource_id, limit)

            logger.debug("Similar search not supported by RAG service")
            return []

        except Exception as e:
            logger.warning(f"Similar search failed: {e}")
            return []

    async def add_resource(self, resource: LearningResource) -> bool:
        """
        Add a resource to the RAG database.

        Useful for indexing new content into the ChromaDB vector database.

        Args:
            resource: LearningResource to index

        Returns:
            True if successful, False otherwise

        Example:
            >>> resource = LearningResource(...)
            >>> success = await strategy.add_resource(resource)
        """
        try:
            # Check if RAG service supports adding resources
            if hasattr(self.rag_service, "add_resource"):
                return await self.rag_service.add_resource(resource)

            logger.debug("Add resource not supported by RAG service")
            return False

        except Exception as e:
            logger.warning(f"Failed to add resource to RAG: {e}")
            return False

    def _map_difficulty_to_level(self, irt_difficulty: float) -> KnowledgeLevel:
        """
        Map IRT difficulty (-4.0 to 4.0) to KnowledgeLevel.

        Mapping:
            - difficulty < -2.0 → BEGINNER
            - difficulty <= -0.5 → ELEMENTARY
            - difficulty < 0.5  → INTERMEDIATE
            - difficulty < 2.0  → ADVANCED
            - difficulty >= 2.0 → EXPERT

        Args:
            irt_difficulty: IRT difficulty parameter

        Returns:
            Corresponding KnowledgeLevel

        Example:
            >>> strategy._map_difficulty_to_level(-2.5)
            KnowledgeLevel.BEGINNER
            >>> strategy._map_difficulty_to_level(0.0)
            KnowledgeLevel.INTERMEDIATE
        """
        if irt_difficulty < -2.0:
            return KnowledgeLevel.BEGINNER
        if irt_difficulty <= -0.5:
            return KnowledgeLevel.ELEMENTARY
        if irt_difficulty < 0.5:
            return KnowledgeLevel.INTERMEDIATE
        if irt_difficulty < 2.0:
            return KnowledgeLevel.ADVANCED
        return KnowledgeLevel.EXPERT

    def get_priority(self) -> int:
        """
        Get the priority of this strategy for multi-platform searches.

        RAG search has higher priority (negative value) because it provides
        semantic search capabilities over our own curated content.

        Returns:
            Priority value (-1 for higher priority)
        """
        return -1  # Higher priority than generic searches
