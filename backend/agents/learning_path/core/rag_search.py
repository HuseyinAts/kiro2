"""
RAG Search Service for Learning Path Agent
Teknofest 2025 - Eğitim Eylemci Projesi

This module provides RAG-based resource search using ChromaDB.
Converts ChromaDB semantic search results to LearningResource objects.

Features:
- ChromaDB integration with EmbeddingService
- Turkish text normalization
- Metadata filtering (subject, difficulty)
- Fallback to empty results on error
- LearningResource conversion
"""

from __future__ import annotations

import logging
from typing import Any

from ..config import get_learning_path_config
from ..models import KnowledgeLevel, LearningResource

logger = logging.getLogger(__name__)

# Lazy import flags
_SERVICES_AVAILABLE = False
_SERVICES_CHECKED = False


def _check_services() -> bool:
    """Check if required services are available."""
    global _SERVICES_AVAILABLE, _SERVICES_CHECKED
    if _SERVICES_CHECKED:
        return _SERVICES_AVAILABLE

    _SERVICES_CHECKED = True
    try:
        from services.embedding_service import EmbeddingService  # noqa: F401
        from services.chromadb_collection_manager import ChromaDBCollectionManager  # noqa: F401
        _SERVICES_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"RAG services not available: {e}")
        _SERVICES_AVAILABLE = False

    return _SERVICES_AVAILABLE


class RAGSearchService:
    """
    RAG-based resource search using ChromaDB.

    This service searches the ChromaDB vector database for learning resources
    using semantic search, then converts results to LearningResource objects.

    Integrates with:
    - EmbeddingService: Generates embeddings for query text
    - ChromaDBCollectionManager: Searches vector database
    """

    def __init__(
        self,
        chromadb_client: Any | None = None,
        embedding_service: Any | None = None,
        collection_manager: Any | None = None,
    ):
        """
        Initialize RAG search service.

        Args:
            chromadb_client: Optional ChromaDB client (for testing/mocking)
            embedding_service: Optional EmbeddingService instance
            collection_manager: Optional ChromaDBCollectionManager instance
        """
        self.config = get_learning_path_config()
        self.client = chromadb_client
        self._embedding_service = embedding_service
        self._collection_manager = collection_manager
        self._initialized = False

    def _lazy_init(self) -> bool:
        """Lazily initialize services on first use."""
        if self._initialized:
            return self._embedding_service is not None and self._collection_manager is not None

        self._initialized = True

        if not _check_services():
            logger.info("RAG services not available, search will return empty results")
            return False

        try:
            # Import services
            from services.embedding_service import EmbeddingService
            from services.chromadb_collection_manager import (
                ChromaDBCollectionManager,
                CollectionType,
            )

            # Initialize embedding service if not provided
            if self._embedding_service is None:
                self._embedding_service = EmbeddingService()
                logger.info("EmbeddingService initialized for RAG search")

            # Initialize collection manager if not provided
            if self._collection_manager is None:
                self._collection_manager = ChromaDBCollectionManager()
                logger.info("ChromaDBCollectionManager initialized for RAG search")

            # Store collection type for questions
            self._questions_collection = CollectionType.QUESTIONS

            return True

        except Exception as e:
            logger.warning(f"Failed to initialize RAG services: {e}")
            self._embedding_service = None
            self._collection_manager = None
            return False

    async def search(
        self,
        query: str,
        subject: str | None = None,
        difficulty_range: tuple[float, float] = (-4.0, 4.0),
        limit: int = 10,
    ) -> list[LearningResource]:
        """
        Search RAG database for learning resources.

        Args:
            query: Search query (Turkish)
            subject: Subject filter (e.g., "matematik", "fizik")
            difficulty_range: (min, max) IRT difficulty range
            limit: Maximum number of results

        Returns:
            List of LearningResource objects

        Example:
            >>> rag = RAGSearchService()
            >>> resources = await rag.search(
            ...     query="trigonometri",
            ...     subject="matematik",
            ...     difficulty_range=(-2.0, 0.0),
            ...     limit=5
            ... )
        """
        try:
            # Search ChromaDB
            results = await self._search_chromadb(
                query=query,
                subject=subject,
                difficulty_min=difficulty_range[0],
                difficulty_max=difficulty_range[1],
                limit=limit,
            )

            # Convert to LearningResource
            resources: list[LearningResource] = []
            for result in results:
                resource = self._convert_to_learning_resource(result)
                if resource:
                    resources.append(resource)

            logger.info(
                f"RAG search returned {len(resources)} resources for query: {query}"
            )
            return resources

        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            return []

    async def _search_chromadb(
        self,
        query: str,
        subject: str | None,
        difficulty_min: float,
        difficulty_max: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        """
        Execute ChromaDB semantic search.

        Uses EmbeddingService to convert query to vector, then searches
        ChromaDB collection with optional metadata filters.

        Args:
            query: Search query
            subject: Optional subject filter
            difficulty_min: Minimum IRT difficulty
            difficulty_max: Maximum IRT difficulty
            limit: Maximum results

        Returns:
            List of raw ChromaDB results
        """
        # Lazy initialize services
        if not self._lazy_init():
            logger.debug("RAG services not initialized, returning empty results")
            return []

        try:
            logger.debug(
                f"ChromaDB search: query={query}, subject={subject}, "
                f"difficulty=[{difficulty_min}, {difficulty_max}], limit={limit}"
            )

            # Generate embedding for query
            embedding = self._embedding_service.embed(query)
            if embedding is None:
                logger.warning("Failed to generate embedding for query")
                return []

            # Build metadata filter
            where_filter: dict[str, Any] | None = None
            if subject or (difficulty_min > -4.0 or difficulty_max < 4.0):
                where_filter = {}
                if subject:
                    where_filter["subject"] = subject
                # Note: ChromaDB doesn't support range queries natively
                # We'll filter by difficulty after retrieval

            # Search ChromaDB
            results = self._collection_manager.search(
                collection_type=self._questions_collection,
                query_embedding=embedding,
                k=limit * 2,  # Get extra results for post-filtering
                where=where_filter,
            )

            # Convert results to expected format
            formatted_results: list[dict[str, Any]] = []
            for i, doc_id in enumerate(results.get("ids", [])):
                metadata = results.get("metadatas", [])[i] if results.get("metadatas") else {}
                document = results.get("documents", [])[i] if results.get("documents") else ""
                distance = results.get("distances", [])[i] if results.get("distances") else 0.0

                # Filter by difficulty range
                difficulty = metadata.get("difficulty", 0.0)
                if not (difficulty_min <= difficulty <= difficulty_max):
                    continue

                formatted_results.append({
                    "id": doc_id,
                    "title": metadata.get("title", "Soru"),
                    "content": document,
                    "subject": metadata.get("subject", ""),
                    "difficulty": difficulty,
                    "topics": metadata.get("topics", []),
                    "metadata": metadata,
                    "score": 1.0 - distance,  # Convert distance to similarity score
                })

                # Stop when we have enough results
                if len(formatted_results) >= limit:
                    break

            logger.info(f"ChromaDB search returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.warning(f"ChromaDB search failed: {e}")
            return []

    def _convert_to_learning_resource(
        self, rag_result: dict[str, Any]
    ) -> LearningResource | None:
        """
        Convert ChromaDB result to LearningResource.

        Expected ChromaDB result format:
        {
            "id": "question_123",
            "title": "Trigonometri Sorusu",
            "content": "Soru metni...",
            "subject": "matematik",
            "difficulty": -0.5,
            "topics": ["trigonometri", "açılar"],
            "metadata": {
                "exam_type": "TYT",
                "year": 2023,
                ...
            }
        }

        Args:
            rag_result: Raw ChromaDB result

        Returns:
            LearningResource or None if conversion fails
        """
        try:
            # Extract basic fields
            resource_id = rag_result.get("id", "")
            title = rag_result.get("title", "Soru")
            content = rag_result.get("content", "")
            difficulty = rag_result.get("difficulty", 0.0)
            topics = rag_result.get("topics", [])

            # Generate description (first 200 chars of content)
            description = content[:200] if content else ""

            # Generate URL (placeholder - could link to question detail page)
            # Must not be empty per LearningResource validation
            url = f"/questions/{resource_id}" if resource_id else "/questions/unknown"

            # Determine difficulty level from IRT difficulty
            difficulty_level = self._map_difficulty_to_level(difficulty)

            # Create LearningResource
            return LearningResource(
                resource_id=resource_id or f"rag_{hash(content)}",
                title=title,
                source="rag",
                url=url,
                resource_type="question",
                difficulty_level=difficulty_level,
                estimated_time=self.config.DEFAULT_VIDEO_DURATION,
                language="tr",
                description=description,
                tags=topics if isinstance(topics, list) else [],
                rating=None,
                metadata=rag_result.get("metadata", {}),
            )

        except Exception as e:
            logger.warning(f"Failed to convert RAG result to LearningResource: {e}")
            return None

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
