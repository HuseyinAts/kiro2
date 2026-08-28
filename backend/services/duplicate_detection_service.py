"""
Duplicate Detection Service - KIRO2 Soru Bankası

Spec REQ-5: Duplicate soru tespiti ve yönetimi.

Bu servis:
- REQ-5.1: Similarity search ile duplicate kontrol
- REQ-5.2: Similarity > 0.95 → duplicate olarak işaretleme
- REQ-5.3: Exact match (similarity = 1.0) engelleme
- REQ-5.4: Near-duplicate flagging
- REQ-5.5: Paraphrase detection (semantic similarity)
- REQ-5.6: Metadata merge

Author: KIRO2 Team
Date: 2026-01-15
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    import chromadb

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from core.chroma_client import create_chromadb_client
from core.config import EmbeddingConfig

logger = logging.getLogger(__name__)


class DuplicateStatus(str, Enum):
    """Duplicate tespit durumları."""

    UNIQUE = "unique"  # Benzeri yok
    NEAR_DUPLICATE = "near_duplicate"  # Yüksek benzerlik (0.90-0.95)
    DUPLICATE = "duplicate"  # Çok yüksek benzerlik (0.95-0.99)
    EXACT_MATCH = "exact_match"  # Tam eşleşme (>0.99)
    PARAPHRASE = "paraphrase"  # Semantik olarak aynı


@dataclass
class DuplicateCheckResult:
    """Duplicate kontrol sonucu."""

    status: DuplicateStatus
    is_duplicate: bool
    similarity_score: float
    similar_questions: list[dict] = field(default_factory=list)
    recommendation: str = ""
    can_add: bool = True
    merge_candidates: list[str] = field(default_factory=list)


@dataclass
class MergeResult:
    """Metadata merge sonucu."""

    success: bool
    merged_id: str
    merged_metadata: dict
    archived_ids: list[str] = field(default_factory=list)
    message: str = ""


class DuplicateDetectionService:
    """
    Soru bankasında duplicate tespit ve yönetim servisi.

    Spec REQ-5 implementasyonu.
    """

    # Benzerlik eşikleri
    EXACT_MATCH_THRESHOLD = 0.99
    DUPLICATE_THRESHOLD = 0.95
    NEAR_DUPLICATE_THRESHOLD = 0.90
    PARAPHRASE_THRESHOLD = 0.85

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = "kiro2_questions",
    ):
        """
        DuplicateDetectionService başlat.

        Args:
            persist_directory: ChromaDB persist dizini (embedded mod; env: CHROMADB_PERSIST_DIR)
            collection_name: Collection adı
        """
        import os

        self.persist_directory = persist_directory or os.getenv(
            "CHROMADB_PERSIST_DIR", "./vector_db"
        )
        self.collection_name = collection_name
        self._client: chromadb.Client | None = None
        self._collection = None
        self._embedding_model = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Servisi başlat."""
        if self._initialized:
            return True

        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available")
            return False

        try:
            self._client = create_chromadb_client(
                persist_directory=self.persist_directory,
            )

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )

            if EMBEDDINGS_AVAILABLE:
                model_name = EmbeddingConfig.get_model_name()
                self._embedding_model = SentenceTransformer(model_name)
                logger.info(f"Embedding model loaded: {model_name}")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    def _embed_text(self, text: str) -> list[float]:
        """Metin için embedding oluştur."""
        # 2026 Ultra Expert NLP Lens Fix: Normalize Turkish text before embedding
        from core.turkish_nlp_utils import normalize_tr

        text = normalize_tr(text)

        if self._embedding_model is None:
            # Fallback hash-based embedding (Turkish locale-safe & correct dimension)
            import hashlib
            import random

            from core.config import EmbeddingConfig

            dim = EmbeddingConfig.get_model_dimension()
            seed_int = int(hashlib.sha256(text.encode()).hexdigest(), 16)
            rng = random.Random(seed_int)
            return [rng.random() for _ in range(dim)]

        embedding = self._embedding_model.encode(text)
        return embedding.tolist()

    async def check_duplicate(
        self,
        content: str,
        check_paraphrase: bool = True,
        similarity_threshold: float | None = None,
    ) -> DuplicateCheckResult:
        """
        Soru içeriğinin duplicate olup olmadığını kontrol et.

        Spec REQ-5.1, REQ-5.2, REQ-5.3, REQ-5.4, REQ-5.5

        Args:
            content: Kontrol edilecek soru içeriği
            check_paraphrase: Paraphrase detection yap
            similarity_threshold: Özel benzerlik eşiği (varsayılan: DUPLICATE_THRESHOLD)

        Returns:
            DuplicateCheckResult
        """
        if not await self.initialize():
            return DuplicateCheckResult(
                status=DuplicateStatus.UNIQUE,
                is_duplicate=False,
                similarity_score=0.0,
                recommendation="ChromaDB initialization failed",
                can_add=False,
            )

        threshold = similarity_threshold or self.DUPLICATE_THRESHOLD

        try:
            # Embedding oluştur
            query_embedding = self._embed_text(content)

            # Benzer soruları ara
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=10,
                include=["documents", "metadatas", "distances"],
            )

            similar_questions = []
            max_similarity = 0.0
            merge_candidates = []

            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    distance = (
                        results["distances"][0][i] if results.get("distances") else 1.0
                    )
                    similarity = 1 - distance

                    max_similarity = max(max_similarity, similarity)

                    doc_id = results["ids"][0][i] if results.get("ids") else None
                    metadata = (
                        results["metadatas"][0][i] if results.get("metadatas") else {}
                    )

                    if similarity >= self.NEAR_DUPLICATE_THRESHOLD:
                        similar_questions.append(
                            {
                                "id": doc_id,
                                "content_preview": doc[:200] + "..."
                                if len(doc) > 200
                                else doc,
                                "similarity": round(similarity, 4),
                                "metadata": metadata,
                            }
                        )

                        if similarity >= self.DUPLICATE_THRESHOLD:
                            merge_candidates.append(doc_id)

            # Durum belirle
            status, recommendation, can_add = self._determine_status(
                max_similarity, check_paraphrase
            )

            return DuplicateCheckResult(
                status=status,
                is_duplicate=status
                in [DuplicateStatus.DUPLICATE, DuplicateStatus.EXACT_MATCH],
                similarity_score=round(max_similarity, 4),
                similar_questions=similar_questions,
                recommendation=recommendation,
                can_add=can_add,
                merge_candidates=merge_candidates,
            )

        except Exception as e:
            logger.error(f"Duplicate check failed: {e}", exc_info=True)
            return DuplicateCheckResult(
                status=DuplicateStatus.UNIQUE,
                is_duplicate=False,
                similarity_score=0.0,
                recommendation=f"Error: {e!s}",
                can_add=False,
            )

    def _determine_status(
        self, similarity: float, check_paraphrase: bool
    ) -> tuple[DuplicateStatus, str, bool]:
        """
        Benzerlik skoruna göre durum belirle.

        Returns:
            (status, recommendation, can_add)
        """
        if similarity >= self.EXACT_MATCH_THRESHOLD:
            # REQ-5.3: Exact match engelleme
            return (
                DuplicateStatus.EXACT_MATCH,
                "ENGELLENDI: Bu soru zaten veritabanında mevcut (exact match).",
                False,
            )

        if similarity >= self.DUPLICATE_THRESHOLD:
            # REQ-5.2: Duplicate olarak işaretle
            return (
                DuplicateStatus.DUPLICATE,
                "UYARI: Çok benzer soru tespit edildi. Manuel inceleme önerilir.",
                False,
            )

        if similarity >= self.NEAR_DUPLICATE_THRESHOLD:
            # REQ-5.4: Near-duplicate flagging
            return (
                DuplicateStatus.NEAR_DUPLICATE,
                "DİKKAT: Benzer soru bulundu. Ekleme mümkün ama kontrol önerilir.",
                True,
            )

        if check_paraphrase and similarity >= self.PARAPHRASE_THRESHOLD:
            # REQ-5.5: Paraphrase detection
            return (
                DuplicateStatus.PARAPHRASE,
                "BİLGİ: Semantik olarak benzer soru bulundu (paraphrase).",
                True,
            )

        return (DuplicateStatus.UNIQUE, "Benzersiz soru - ekleme güvenli.", True)

    async def add_with_duplicate_check(
        self,
        content: str,
        metadata: dict | None = None,
        question_id: str | None = None,
        force: bool = False,
    ) -> tuple[bool, str, DuplicateCheckResult]:
        """
        Duplicate kontrolü ile soru ekle.

        Args:
            content: Soru içeriği
            metadata: Soru metadata'sı
            question_id: Opsiyonel soru ID
            force: Duplicate olsa bile ekle (admin için)

        Returns:
            (success, question_id, duplicate_check_result)
        """
        # Önce duplicate kontrolü yap
        check_result = await self.check_duplicate(content)

        if not check_result.can_add and not force:
            return False, "", check_result

        if not await self.initialize():
            return False, "", check_result

        try:
            # ID oluştur
            if question_id is None:
                import uuid

                question_id = str(uuid.uuid4())

            # Embedding oluştur
            embedding = self._embed_text(content)

            # Metadata hazırla
            meta = metadata or {}
            meta["created_at"] = datetime.now().isoformat()
            meta["duplicate_check_similarity"] = check_result.similarity_score
            meta["duplicate_check_status"] = check_result.status.value

            # Ekle
            self._collection.add(
                ids=[question_id],
                documents=[content],
                metadatas=[meta],
                embeddings=[embedding],
            )

            logger.info(
                f"Question added: {question_id} (similarity: {check_result.similarity_score})"
            )
            return True, question_id, check_result

        except Exception as e:
            logger.error(f"Add failed: {e}", exc_info=True)
            check_result.recommendation = f"Ekleme hatası: {e!s}"
            return False, "", check_result

    async def merge_duplicates(
        self,
        primary_id: str,
        secondary_ids: list[str],
        merge_strategy: str = "keep_primary",
    ) -> MergeResult:
        """
        Duplicate soruları birleştir.

        Spec REQ-5.6: Metadata merge

        Args:
            primary_id: Ana soru ID'si (korunacak)
            secondary_ids: Birleştirilecek soru ID'leri
            merge_strategy: Birleştirme stratejisi
                - "keep_primary": Primary metadata'yı koru
                - "merge_all": Tüm metadata'ları birleştir
                - "keep_newest": En yeni metadata'yı koru

        Returns:
            MergeResult
        """
        if not await self.initialize():
            return MergeResult(
                success=False,
                merged_id="",
                merged_metadata={},
                message="ChromaDB initialization failed",
            )

        try:
            # Primary soruyu al
            primary = self._collection.get(
                ids=[primary_id], include=["documents", "metadatas"]
            )

            if not primary or not primary.get("documents"):
                return MergeResult(
                    success=False,
                    merged_id=primary_id,
                    merged_metadata={},
                    message=f"Primary question not found: {primary_id}",
                )

            primary_doc = primary["documents"][0]
            primary_meta = primary["metadatas"][0] if primary.get("metadatas") else {}

            # Secondary soruları al
            secondaries = self._collection.get(
                ids=secondary_ids, include=["documents", "metadatas"]
            )

            # Metadata birleştir
            merged_metadata = self._merge_metadata(
                primary_meta, secondaries.get("metadatas", []), merge_strategy
            )

            # Primary'yi güncelle
            self._collection.update(ids=[primary_id], metadatas=[merged_metadata])

            # Secondary'leri arşivle (sil)
            archived_ids = []
            for sec_id in secondary_ids:
                try:
                    self._collection.delete(ids=[sec_id])
                    archived_ids.append(sec_id)
                except Exception as e:
                    logger.warning(f"Could not archive {sec_id}: {e}")

            return MergeResult(
                success=True,
                merged_id=primary_id,
                merged_metadata=merged_metadata,
                archived_ids=archived_ids,
                message=f"Merged {len(archived_ids)} duplicates into {primary_id}",
            )

        except Exception as e:
            logger.error(f"Merge failed: {e}", exc_info=True)
            return MergeResult(
                success=False,
                merged_id=primary_id,
                merged_metadata={},
                message=f"Merge error: {e!s}",
            )

    def _merge_metadata(
        self, primary: dict, secondaries: list[dict], strategy: str
    ) -> dict:
        """
        Metadata birleştirme stratejisini uygula.

        Args:
            primary: Ana metadata
            secondaries: İkincil metadata listesi
            strategy: Birleştirme stratejisi

        Returns:
            Birleştirilmiş metadata
        """
        if strategy == "keep_primary":
            result = dict(primary)
            # Sadece eksik alanları ekle
            for sec in secondaries:
                for key, value in sec.items():
                    if key not in result and value:
                        result[key] = value
            return result

        if strategy == "merge_all":
            result = dict(primary)

            # Tags birleştir
            all_tags = set(primary.get("tags", []))
            for sec in secondaries:
                all_tags.update(sec.get("tags", []))
            if all_tags:
                result["tags"] = list(all_tags)

            # View count topla
            total_views = primary.get("view_count", 0)
            for sec in secondaries:
                total_views += sec.get("view_count", 0)
            result["view_count"] = total_views

            # Sources birleştir
            all_sources = set()
            if primary.get("source"):
                all_sources.add(primary["source"])
            for sec in secondaries:
                if sec.get("source"):
                    all_sources.add(sec["source"])
            if all_sources:
                result["sources"] = list(all_sources)

            return result

        if strategy == "keep_newest":
            # En yeni created_at'ı bul
            newest = primary
            newest_date = primary.get("created_at", "")

            for sec in secondaries:
                sec_date = sec.get("created_at", "")
                if sec_date > newest_date:
                    newest = sec
                    newest_date = sec_date

            result = dict(newest)
            result["merged_from"] = [primary.get("id")] + [
                s.get("id") for s in secondaries if s.get("id")
            ]
            return result

        # Default: keep_primary
        return dict(primary)

    async def get_duplicate_stats(self) -> dict:
        """
        Duplicate istatistiklerini döndür.

        Returns:
            İstatistik dictionary'si
        """
        if not await self.initialize():
            return {"error": "ChromaDB not available"}

        try:
            count = self._collection.count()

            # Sample al ve analiz et
            sample_size = min(100, count)
            if sample_size == 0:
                return {
                    "total_questions": 0,
                    "potential_duplicates": 0,
                    "duplicate_rate": 0.0,
                }

            sample = self._collection.peek(limit=sample_size)

            # Her soruyu kontrol et (basit analiz)
            duplicate_count = 0
            if sample and sample.get("metadatas"):
                for meta in sample["metadatas"]:
                    if meta.get("duplicate_check_status") in [
                        DuplicateStatus.DUPLICATE.value,
                        DuplicateStatus.EXACT_MATCH.value,
                    ]:
                        duplicate_count += 1

            return {
                "total_questions": count,
                "sample_size": sample_size,
                "potential_duplicates": duplicate_count,
                "duplicate_rate": round(duplicate_count / sample_size * 100, 2)
                if sample_size > 0
                else 0.0,
                "thresholds": {
                    "exact_match": self.EXACT_MATCH_THRESHOLD,
                    "duplicate": self.DUPLICATE_THRESHOLD,
                    "near_duplicate": self.NEAR_DUPLICATE_THRESHOLD,
                    "paraphrase": self.PARAPHRASE_THRESHOLD,
                },
            }

        except Exception as e:
            logger.error(f"Stats failed: {e}", exc_info=True)
            return {"error": str(e)}


# Singleton instance
_duplicate_service: DuplicateDetectionService | None = None


def get_duplicate_service(
    persist_directory: str = "./vector_db", collection_name: str = "kiro2_questions"
) -> DuplicateDetectionService:
    """
    Singleton DuplicateDetectionService instance döndür.

    Args:
        persist_directory: ChromaDB persist dizini
        collection_name: Collection adı

    Returns:
        DuplicateDetectionService instance
    """
    global _duplicate_service
    if _duplicate_service is None:
        _duplicate_service = DuplicateDetectionService(
            persist_directory=persist_directory, collection_name=collection_name
        )
    return _duplicate_service
