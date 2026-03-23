"""
ChromaDB Collection Manager - KIRO2 YKS Platform
Manages separate collections for questions, content, and concepts with HNSW indexing.

Spec: REQ-2 Collection Management
- 3 separate collections with metadata schemas
- HNSW indexing (M=16, efConstruction=200)
- Cascade delete support
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)


class CollectionType(str, Enum):
    """Supported collection types"""
    QUESTIONS = "questions"
    CONTENT = "content"
    CONCEPTS = "concepts"


@dataclass
class CollectionSchema:
    """Schema definition for a collection"""
    name: str
    required_metadata: list[str]
    optional_metadata: list[str] = field(default_factory=list)
    description: str = ""


# Collection schemas as defined in spec
COLLECTION_SCHEMAS: dict[CollectionType, CollectionSchema] = {
    CollectionType.QUESTIONS: CollectionSchema(
        name="kiro2_questions",
        required_metadata=["subject", "difficulty", "exam_type"],
        optional_metadata=["learning_outcome", "source", "created_at", "question_id"],
        description="YKS/TYT/AYT questions with IRT parameters"
    ),
    CollectionType.CONTENT: CollectionSchema(
        name="kiro2_content",
        required_metadata=["topic", "source"],
        optional_metadata=["created_at", "content_type", "grade_level", "subject"],
        description="Educational content and learning materials"
    ),
    CollectionType.CONCEPTS: CollectionSchema(
        name="kiro2_concepts",
        required_metadata=["domain", "level"],
        optional_metadata=["prerequisites", "related_concepts", "curriculum_code"],
        description="Curriculum concepts for clustering and mapping"
    )
}


@dataclass
class HNSWConfig:
    """HNSW index configuration as per spec"""
    M: int = 16  # Number of connections per layer
    ef_construction: int = 200  # Construction time accuracy
    ef_search: int = 100  # Search time accuracy

    def to_dict(self) -> dict[str, Any]:
        return {
            "hnsw:M": self.M,
            "hnsw:construction_ef": self.ef_construction,
            "hnsw:search_ef": self.ef_search,
        }


@dataclass
class CollectionStats:
    """Statistics for a collection"""
    name: str
    count: int
    metadata_keys: list[str]
    created_at: datetime | None = None


class ChromaDBCollectionManager:
    """
    Manages ChromaDB collections for KIRO2 platform.

    Features:
    - 3 separate collections (questions, content, concepts)
    - HNSW indexing with optimized parameters
    - Metadata validation
    - Batch operations
    - Cascade delete support
    """

    def __init__(
        self,
        persist_directory: str | None = None,
        hnsw_config: HNSWConfig | None = None,
    ):
        """
        Initialize collection manager.

        Args:
            persist_directory: Directory for persistent storage
            hnsw_config: HNSW index configuration
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb package not installed. Run: pip install chromadb")

        self.persist_directory = persist_directory or os.getenv(
            "CHROMADB_PERSIST_DIR", "./chromadb_data"
        )
        self.hnsw_config = hnsw_config or HNSWConfig()
        self._client: chromadb.Client | None = None
        self._collections: dict[CollectionType, Any] = {}

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize ChromaDB client with persistence."""
        try:
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False,
            )
            self._client = chromadb.Client(settings)
            logger.info(f"ChromaDB client initialized at {self.persist_directory}")
        except Exception as e:
            # Fallback for newer chromadb versions
            logger.warning(f"Legacy settings failed, trying new API: {e}")
            self._client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info(f"ChromaDB PersistentClient initialized at {self.persist_directory}")

    def get_or_create_collection(
        self,
        collection_type: CollectionType,
        custom_hnsw_config: HNSWConfig | None = None,
    ) -> Any:
        """
        Get or create a collection with proper schema and indexing.

        Args:
            collection_type: Type of collection to create
            custom_hnsw_config: Optional custom HNSW configuration

        Returns:
            ChromaDB collection instance
        """
        if collection_type in self._collections:
            return self._collections[collection_type]

        schema = COLLECTION_SCHEMAS[collection_type]
        hnsw = custom_hnsw_config or self.hnsw_config

        try:
            collection = self._client.get_or_create_collection(
                name=schema.name,
                metadata={
                    **hnsw.to_dict(),
                    "description": schema.description,
                    "required_fields": ",".join(schema.required_metadata),
                }
            )
            self._collections[collection_type] = collection
            logger.info(f"Collection '{schema.name}' ready with {collection.count()} documents")
            return collection
        except Exception as e:
            logger.error(f"Failed to create collection {schema.name}: {e}")
            raise

    def validate_metadata(
        self,
        collection_type: CollectionType,
        metadata: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        Validate metadata against collection schema.

        Args:
            collection_type: Type of collection
            metadata: Metadata to validate

        Returns:
            Tuple of (is_valid, list of missing fields)
        """
        schema = COLLECTION_SCHEMAS[collection_type]
        missing = [
            field for field in schema.required_metadata
            if field not in metadata or metadata[field] is None
        ]
        return len(missing) == 0, missing

    def add_documents(
        self,
        collection_type: CollectionType,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Add documents with embeddings to a collection.

        Args:
            collection_type: Target collection
            documents: Document texts
            embeddings: Pre-computed embeddings
            metadatas: Metadata for each document
            ids: Optional document IDs (auto-generated if not provided)

        Returns:
            Result with count and any validation errors
        """
        if len(documents) != len(embeddings) != len(metadatas):
            raise ValueError("Documents, embeddings, and metadatas must have same length")

        # Validate all metadata
        validation_errors = []
        for i, meta in enumerate(metadatas):
            is_valid, missing = self.validate_metadata(collection_type, meta)
            if not is_valid:
                validation_errors.append({
                    "index": i,
                    "missing_fields": missing,
                })

        if validation_errors:
            logger.warning(f"Metadata validation warnings: {len(validation_errors)} documents")

        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        # Add to collection
        collection = self.get_or_create_collection(collection_type)

        try:
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"Added {len(documents)} documents to {collection_type.value}")
            return {
                "success": True,
                "count": len(documents),
                "collection": collection_type.value,
                "validation_warnings": validation_errors,
            }
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def search(
        self,
        collection_type: CollectionType,
        query_embedding: list[float],
        k: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Search collection by embedding similarity.

        Args:
            collection_type: Collection to search
            query_embedding: Query vector
            k: Number of results
            where: Metadata filter
            where_document: Document content filter

        Returns:
            Search results with documents, distances, and metadata
        """
        collection = self.get_or_create_collection(collection_type)

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"],
            )

            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
            }
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def delete_documents(
        self,
        collection_type: CollectionType,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> int:
        """
        Delete documents from collection.

        Args:
            collection_type: Collection to delete from
            ids: Specific document IDs to delete
            where: Metadata filter for deletion

        Returns:
            Number of deleted documents
        """
        collection = self.get_or_create_collection(collection_type)

        # Get count before deletion
        count_before = collection.count()

        try:
            if ids:
                collection.delete(ids=ids)
            elif where:
                collection.delete(where=where)
            else:
                raise ValueError("Must provide either ids or where filter")

            count_after = collection.count()
            deleted = count_before - count_after
            logger.info(f"Deleted {deleted} documents from {collection_type.value}")
            return deleted
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise

    def delete_collection(
        self,
        collection_type: CollectionType,
        cascade: bool = False,
    ) -> bool:
        """
        Delete entire collection.

        Args:
            collection_type: Collection to delete
            cascade: If True, also delete related data in other collections

        Returns:
            True if successful
        """
        schema = COLLECTION_SCHEMAS[collection_type]

        try:
            self._client.delete_collection(name=schema.name)
            if collection_type in self._collections:
                del self._collections[collection_type]
            logger.info(f"Deleted collection {schema.name}")

            # Cascade delete related data if requested
            if cascade and collection_type == CollectionType.QUESTIONS:
                # Questions might have related concepts
                self._cascade_delete_related(collection_type)

            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise

    def _cascade_delete_related(self, source_type: CollectionType) -> None:
        """
        Handle cascade deletion of related data.

        Spec REQ-2.6: Cascade delete implementasyonu.

        İlişki haritası:
        - QUESTIONS → CONCEPTS (soru silinince ilişkili concept referansları temizlenir)
        - CONTENT → CONCEPTS (içerik silinince ilişkili concept referansları temizlenir)
        - CONCEPTS → (bağımsız, cascade yok)

        Args:
            source_type: Silinen collection tipi
        """
        logger.info(f"Cascade delete triggered from {source_type.value}")

        # İlişki haritası: hangi collection'dan hangi collection'lara cascade yapılacak
        relationships: dict[CollectionType, list[CollectionType]] = {
            CollectionType.QUESTIONS: [CollectionType.CONCEPTS],
            CollectionType.CONTENT: [CollectionType.CONCEPTS],
            CollectionType.CONCEPTS: [],  # Concepts bağımsız
        }

        related_types = relationships.get(source_type, [])
        if not related_types:
            logger.debug(f"No cascade relationships for {source_type.value}")
            return

        for related_type in related_types:
            try:
                self._cleanup_orphaned_references(source_type, related_type)
            except Exception as e:
                logger.warning(
                    f"Cascade cleanup failed from {source_type.value} to {related_type.value}: {e}"
                )

    def _cleanup_orphaned_references(
        self,
        source_type: CollectionType,
        target_type: CollectionType
    ) -> int:
        """
        Kaynak collection silindiğinde hedef collection'daki referansları temizle.

        Args:
            source_type: Silinen kaynak collection
            target_type: Temizlenecek hedef collection

        Returns:
            Temizlenen referans sayısı
        """
        try:
            target_collection = self.get_or_create_collection(target_type)

            # Hedef collection'daki tüm dökümanları al
            # (büyük collection'larda batch işlem gerekebilir)
            sample = target_collection.peek(limit=1000)

            if not sample or not sample.get("ids"):
                return 0

            # source_type referansı içeren dökümanları bul
            source_ref_key = f"{source_type.value}_id"
            source_refs_key = f"{source_type.value}_ids"

            docs_to_update = []
            for i, doc_id in enumerate(sample["ids"]):
                if not sample.get("metadatas"):
                    continue

                metadata = sample["metadatas"][i]

                # Referans içeriyor mu kontrol et
                if source_ref_key in metadata or source_refs_key in metadata:
                    # Referansı temizle
                    updated_metadata = dict(metadata)
                    updated_metadata.pop(source_ref_key, None)
                    updated_metadata.pop(source_refs_key, None)
                    updated_metadata["orphaned_from"] = source_type.value
                    updated_metadata["orphaned_at"] = __import__("datetime").datetime.now().isoformat()

                    docs_to_update.append((doc_id, updated_metadata))

            # Batch güncelle
            if docs_to_update:
                for doc_id, new_metadata in docs_to_update:
                    try:
                        target_collection.update(
                            ids=[doc_id],
                            metadatas=[new_metadata]
                        )
                    except Exception as e:
                        logger.warning(f"Could not update {doc_id}: {e}")

            cleaned_count = len(docs_to_update)
            if cleaned_count > 0:
                logger.info(
                    f"Cleaned {cleaned_count} orphaned references "
                    f"from {source_type.value} in {target_type.value}"
                )

            return cleaned_count

        except Exception as e:
            logger.error(f"Reference cleanup failed: {e}")
            return 0

    def get_collection_stats(
        self,
        collection_type: CollectionType | None = None,
    ) -> list[CollectionStats]:
        """
        Get statistics for collection(s).

        Args:
            collection_type: Specific collection or None for all

        Returns:
            List of collection statistics
        """
        stats = []
        types_to_check = [collection_type] if collection_type else list(CollectionType)

        for ct in types_to_check:
            try:
                collection = self.get_or_create_collection(ct)
                # Get sample to infer metadata keys
                sample = collection.peek(limit=1)
                metadata_keys = list(sample["metadatas"][0].keys()) if sample["metadatas"] else []

                stats.append(CollectionStats(
                    name=ct.value,
                    count=collection.count(),
                    metadata_keys=metadata_keys,
                ))
            except Exception as e:
                logger.warning(f"Could not get stats for {ct.value}: {e}")

        return stats

    def update_document(
        self,
        collection_type: CollectionType,
        doc_id: str,
        document: str | None = None,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Update a document in collection.

        Args:
            collection_type: Collection containing the document
            doc_id: Document ID to update
            document: New document text (optional)
            embedding: New embedding (optional)
            metadata: New metadata (optional, merged with existing)

        Returns:
            True if successful
        """
        collection = self.get_or_create_collection(collection_type)

        try:
            update_kwargs: dict[str, Any] = {"ids": [doc_id]}

            if document is not None:
                update_kwargs["documents"] = [document]
            if embedding is not None:
                update_kwargs["embeddings"] = [embedding]
            if metadata is not None:
                update_kwargs["metadatas"] = [metadata]

            collection.update(**update_kwargs)
            logger.info(f"Updated document {doc_id} in {collection_type.value}")
            return True
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise


# Singleton instance for global access
_collection_manager: ChromaDBCollectionManager | None = None


def get_collection_manager() -> ChromaDBCollectionManager:
    """Get or create the global collection manager instance."""
    global _collection_manager
    if _collection_manager is None:
        _collection_manager = ChromaDBCollectionManager()
    return _collection_manager
