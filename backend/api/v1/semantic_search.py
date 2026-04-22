"""
Semantic Search API - KIRO2 YKS Platform

Spec REQ-3: Semantic Question Search
- REQ-3.1: Query embedding oluşturma
- REQ-3.2: Top-k nearest neighbors (k=10)
- REQ-3.3: Similarity threshold (> 0.7)
- REQ-3.4: Metadata filtering (konu, zorluk, kazanım)
- REQ-3.5: MMR diversity (lambda=0.5)
- REQ-3.6: Hybrid ranking (similarity + recency + popularity)

Author: KIRO2 Team
Date: 2026-01-18
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import Response

from core.auth_dependencies import AuthenticationDependency
from core.ddos_protection import limiter

get_current_user = AuthenticationDependency(required=True)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    np = None  # type: ignore[assignment, misc]
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available for semantic search")


def _coerce_embedding_list(raw: object) -> list[float] | None:
    """Chroma 0.5+ bazen numpy ndarray döndürür; `if arr` boolean hatası verir."""
    if raw is None:
        return None
    if NUMPY_AVAILABLE and np is not None and isinstance(raw, np.ndarray):
        return np.asarray(raw, dtype=np.float64).reshape(-1).tolist()
    if isinstance(raw, (list, tuple)):
        return [float(x) for x in raw]
    return None

try:
    import chromadb

    CHROMADB_AVAILABLE = True
except (ImportError, TypeError, OSError, Exception) as e:
    CHROMADB_AVAILABLE = False
    chromadb = None
    logger.warning(f"chromadb not available for semantic search: {e}")

try:
    from services.embedding_service import get_embedding_service

    EMBEDDING_AVAILABLE = True
except (ImportError, TypeError):
    EMBEDDING_AVAILABLE = False
    get_embedding_service = None
    logger.warning("embedding_service not available")

router = APIRouter(prefix="/api/v1/search", tags=["Semantic Search"])


# ============================================================================
# Pydantic Models
# ============================================================================


class SearchRequest(BaseModel):
    """Arama isteği."""

    query: str = Field(..., min_length=3, max_length=1000, description="Arama sorgusu")
    limit: int = Field(default=10, ge=1, le=100, description="Maksimum sonuç sayısı")
    similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum benzerlik eşiği"
    )
    subject: str | None = Field(default=None, description="Ders filtresi")
    difficulty_min: float | None = Field(
        default=None, ge=-4.0, le=4.0, description="Minimum zorluk"
    )
    difficulty_max: float | None = Field(
        default=None, ge=-4.0, le=4.0, description="Maksimum zorluk"
    )
    exam_type: str | None = Field(default=None, description="Sınav tipi (TYT, AYT)")
    learning_outcome: str | None = Field(default=None, description="Kazanım filtresi")
    use_mmr: bool = Field(default=False, description="MMR diversity kullan")
    mmr_lambda: float = Field(
        default=0.5, ge=0.0, le=1.0, description="MMR lambda (0=diversity, 1=relevance)"
    )
    use_hybrid_ranking: bool = Field(default=False, description="Hybrid ranking kullan")


class SearchResult(BaseModel):
    """Arama sonucu."""

    id: str
    content: str
    similarity: float
    metadata: dict
    hybrid_score: float | None = None
    score_breakdown: dict | None = None


class SearchResponse(BaseModel):
    """Arama response'u."""

    query: str
    results: list[SearchResult]
    total_found: int
    filters_applied: dict
    ranking_info: dict
    latency_ms: float


class SimilarRequest(BaseModel):
    """Benzer soru isteği."""

    question_id: str = Field(..., description="Kaynak soru ID'si")
    limit: int = Field(default=5, ge=1, le=50)
    exclude_same_subject: bool = Field(default=False)


class SimilarResponse(BaseModel):
    """Benzer soru response'u."""

    source_id: str
    source_preview: str
    similar_questions: list[SearchResult]
    total_found: int


# ============================================================================
# ChromaDB Service
# ============================================================================


class SemanticSearchService:
    """
    Semantic search servisi.

    Spec REQ-3 implementasyonu.
    """

    def __init__(
        self,
        persist_directory: str = "./vector_db",
        collection_name: str = "kiro2_questions",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client: chromadb.Client | None = None
        self._collection = None
        self._embedding_service = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Servisi başlat."""
        if self._initialized:
            return True

        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available")
            return False

        try:
            from core.chroma_client import create_chromadb_client

            self._client = create_chromadb_client(
                persist_directory=self.persist_directory,
            )

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )

            self._embedding_service = get_embedding_service()
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Semantic arama yap.

        Spec REQ-3.1 - REQ-3.6

        Args:
            request: Arama parametreleri

        Returns:
            SearchResponse
        """
        import time

        start_time = time.time()

        if not await self.initialize():
            raise HTTPException(status_code=503, detail="Search service unavailable")

        try:
            # REQ-3.1: Query embedding oluştur
            query_embedding = self._embedding_service.embed(request.query)

            # Build where clause
            where_clause = self._build_where_clause(request)

            # REQ-3.2: Top-k search (fazla al, sonra filtrele)
            fetch_limit = (
                request.limit * 3
                if (request.use_mmr or request.use_hybrid_ranking)
                else request.limit
            )

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=fetch_limit,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances", "embeddings"],
            )

            # Process results
            search_results = self._process_results(
                results,
                request.similarity_threshold,
                request.difficulty_min,
                request.difficulty_max,
            )

            # REQ-3.5: MMR diversity
            if request.use_mmr and len(search_results) > request.limit:
                search_results = self._apply_mmr(
                    query_embedding, search_results, request.mmr_lambda, request.limit
                )

            # REQ-3.6: Hybrid ranking
            if request.use_hybrid_ranking:
                search_results = self._apply_hybrid_ranking(search_results)

            # Limit
            search_results = search_results[: request.limit]

            latency_ms = (time.time() - start_time) * 1000

            return SearchResponse(
                query=request.query,
                results=search_results,
                total_found=len(search_results),
                filters_applied={
                    "subject": request.subject,
                    "exam_type": request.exam_type,
                    "difficulty_range": [
                        request.difficulty_min,
                        request.difficulty_max,
                    ],
                    "learning_outcome": request.learning_outcome,
                    "similarity_threshold": request.similarity_threshold,
                },
                ranking_info={
                    "mmr_enabled": request.use_mmr,
                    "mmr_lambda": request.mmr_lambda if request.use_mmr else None,
                    "hybrid_ranking_enabled": request.use_hybrid_ranking,
                },
                latency_ms=round(latency_ms, 2),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )

    def _build_where_clause(self, request: SearchRequest) -> dict | None:
        """Where clause oluştur."""
        conditions = []

        if request.subject:
            conditions.append({"subject": request.subject})
        if request.exam_type:
            conditions.append({"exam_type": request.exam_type})
        if request.learning_outcome:
            conditions.append({"learning_outcome": request.learning_outcome})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def _process_results(
        self,
        results: dict,
        similarity_threshold: float,
        difficulty_min: float | None,
        difficulty_max: float | None,
    ) -> list[SearchResult]:
        """Sonuçları işle ve filtrele."""
        search_results = []

        if not results or not results.get("ids"):
            return search_results

        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results.get("distances") else 1.0
            similarity = 1 - distance

            # REQ-3.3: Similarity threshold
            if similarity < similarity_threshold:
                continue

            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            document = results["documents"][0][i] if results.get("documents") else ""

            # Difficulty filter
            difficulty = metadata.get("difficulty", 0.0)
            if difficulty_min is not None and difficulty < difficulty_min:
                continue
            if difficulty_max is not None and difficulty > difficulty_max:
                continue

            # Embedding'i sakla (MMR için); Chroma ndarray → list
            embedding = None
            emb_outer = results.get("embeddings")
            if emb_outer is not None and len(emb_outer) > 0:
                row = emb_outer[0]
                if row is not None and i < len(row):
                    embedding = _coerce_embedding_list(row[i])

            search_results.append(
                SearchResult(
                    id=doc_id,
                    content=document,
                    similarity=round(similarity, 4),
                    metadata={**metadata, "_embedding": embedding},
                )
            )

        return search_results

    def _apply_mmr(
        self,
        query_embedding: list[float],
        results: list[SearchResult],
        lambda_param: float,
        top_k: int,
    ) -> list[SearchResult]:
        """
        MMR (Maximal Marginal Relevance) uygula.

        Spec REQ-3.5: Diversity sağlamak için MMR.
        MMR = λ * Sim(d, q) - (1-λ) * max(Sim(d, d_selected))
        """
        if not results or not NUMPY_AVAILABLE:
            return results

        def cosine_sim(a: list[float], b: list[float]) -> float:
            a_arr = np.array(a)
            b_arr = np.array(b)
            norm_a = np.linalg.norm(a_arr)
            norm_b = np.linalg.norm(b_arr)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))

        selected: list[SearchResult] = []
        remaining = list(results)

        while len(selected) < top_k and remaining:
            mmr_scores = []

            for result in remaining:
                embedding = result.metadata.get("_embedding")
                if embedding is None:
                    relevance = result.similarity
                else:
                    relevance = cosine_sim(query_embedding, embedding)

                # Max similarity to already selected
                if selected:
                    max_sim = (
                        max(
                            cosine_sim(
                                embedding
                                if embedding is not None
                                else [],
                                s.metadata.get("_embedding") or [],
                            )
                            for s in selected
                            if s.metadata.get("_embedding") is not None
                        )
                        if embedding is not None
                        else 0.0
                    )
                else:
                    max_sim = 0.0

                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
                mmr_scores.append((result, mmr_score))

            # En yüksek MMR skorlu sonucu seç
            best_result, _ = max(mmr_scores, key=lambda x: x[1])
            selected.append(best_result)
            remaining.remove(best_result)

        # Embedding'leri temizle
        for r in selected:
            r.metadata.pop("_embedding", None)

        return selected

    def _apply_hybrid_ranking(
        self, results: list[SearchResult], weights: dict | None = None
    ) -> list[SearchResult]:
        """
        Hybrid ranking uygula.

        Spec REQ-3.6: similarity + recency + popularity
        """
        if not results:
            return results

        if weights is None:
            weights = {"similarity": 0.6, "recency": 0.2, "popularity": 0.2}

        now = datetime.now()
        max_views = max((r.metadata.get("view_count", 1) for r in results), default=1)

        for result in results:
            # 1. Similarity (zaten normalize)
            similarity = result.similarity

            # 2. Recency score
            created_at_str = result.metadata.get("created_at")
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(
                        created_at_str.replace("Z", "+00:00")
                    )
                    days_old = (now - created_at.replace(tzinfo=None)).days
                    recency = max(0.0, 1.0 - (days_old / 365))
                except (ValueError, TypeError):
                    recency = 0.5
            else:
                recency = 0.5

            # 3. Popularity score
            view_count = result.metadata.get("view_count", 0)
            popularity = view_count / max_views if max_views > 0 else 0.0

            # Hybrid score
            hybrid_score = (
                weights["similarity"] * similarity
                + weights["recency"] * recency
                + weights["popularity"] * popularity
            )

            result.hybrid_score = round(hybrid_score, 4)
            result.score_breakdown = {
                "similarity": round(similarity, 4),
                "recency": round(recency, 4),
                "popularity": round(popularity, 4),
            }

        # Hybrid score'a göre sırala
        results.sort(key=lambda x: x.hybrid_score or 0, reverse=True)

        # Embedding'leri temizle
        for r in results:
            r.metadata.pop("_embedding", None)

        return results

    async def find_similar(self, request: SimilarRequest) -> SimilarResponse:
        """
        Belirli bir soruya benzer soruları bul.

        Args:
            request: Benzer soru isteği

        Returns:
            SimilarResponse
        """
        if not await self.initialize():
            raise HTTPException(status_code=503, detail="Search service unavailable")

        try:
            # Kaynak soruyu al
            source = self._collection.get(
                ids=[request.question_id],
                include=["documents", "metadatas", "embeddings"],
            )

            if not source or not source.get("documents"):
                raise HTTPException(
                    status_code=404, detail=f"Question {request.question_id} not found"
                )

            source_doc = source["documents"][0]
            source_meta = source["metadatas"][0] if source.get("metadatas") else {}
            source_embedding: list[float] | None = None
            if source.get("embeddings") is not None and len(source["embeddings"]) > 0:
                e0 = source["embeddings"][0]
                if e0 is not None:
                    if NUMPY_AVAILABLE and np is not None and isinstance(
                        e0, np.ndarray
                    ):
                        e0 = e0.reshape(-1)
                    source_embedding = _coerce_embedding_list(e0)

            # Embedding yoksa oluştur
            if source_embedding is None:
                source_embedding = self._embedding_service.embed(source_doc)

            # Where clause
            where_clause = None
            if request.exclude_same_subject and source_meta.get("subject"):
                where_clause = {"subject": {"$ne": source_meta["subject"]}}

            # Benzer soruları ara
            results = self._collection.query(
                query_embeddings=[source_embedding],
                n_results=request.limit + 1,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            # Sonuçları işle (kaynak hariç)
            similar = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"][0]):
                    if doc_id == request.question_id:
                        continue

                    distance = (
                        results["distances"][0][i] if results.get("distances") else 1.0
                    )
                    similarity = 1 - distance

                    similar.append(
                        SearchResult(
                            id=doc_id,
                            content=results["documents"][0][i]
                            if results.get("documents")
                            else "",
                            similarity=round(similarity, 4),
                            metadata=results["metadatas"][0][i]
                            if results.get("metadatas")
                            else {},
                        )
                    )

            return SimilarResponse(
                source_id=request.question_id,
                source_preview=source_doc[:200] + "..."
                if len(source_doc) > 200
                else source_doc,
                similar_questions=similar[: request.limit],
                total_found=len(similar[: request.limit]),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Find similar failed: {e}")
            raise HTTPException(
                status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
            )


# ============================================================================
# Service Instance
# ============================================================================

_search_service: SemanticSearchService | None = None


def get_search_service() -> SemanticSearchService:
    """Singleton search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = SemanticSearchService()
    return _search_service


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/questions", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_questions(
    request: Request,
    response: Response,
    payload: SearchRequest,
    _current_user=Depends(get_current_user),
):
    """
    Soru bankasında semantic arama yap.

    Spec REQ-3: Semantic Question Search

    - Query embedding oluşturur
    - Top-k benzer soruları bulur
    - Metadata filtreleri uygular
    - MMR diversity ve hybrid ranking destekler
    """
    service = get_search_service()
    return await service.search(payload)


@router.post("/content", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_content(
    request: Request,
    response: Response,
    payload: SearchRequest,
    _current_user=Depends(get_current_user),
):
    """
    Eğitim içeriklerinde semantic arama yap.

    Questions ile aynı mantık, farklı collection.
    """
    # Content collection için service
    import os

    service = SemanticSearchService(
        persist_directory=os.getenv("CHROMADB_PERSIST_DIR", "./vector_db"),
        collection_name="kiro2_content",
    )
    return await service.search(payload)


@router.post("/similar", response_model=SimilarResponse)
@limiter.limit("30/minute")
async def find_similar_questions(
    request: Request,
    response: Response,
    payload: SimilarRequest,
    _current_user=Depends(get_current_user),
):
    """
    Belirli bir soruya benzer soruları bul.

    Args:
        payload: Kaynak soru ID ve parametreler

    Returns:
        Benzer sorular listesi
    """
    service = get_search_service()
    return await service.find_similar(payload)


@router.get("/health")
async def search_health():
    """Search service sağlık kontrolü."""
    from core.chroma_client import chromadb_connection_mode

    service = get_search_service()
    initialized = await service.initialize()

    collection_count = 0
    if initialized and service._collection:
        try:
            collection_count = service._collection.count()
        except Exception:
            pass

    return {
        "status": "healthy" if initialized else "unhealthy",
        "service": "semantic_search",
        "chromadb_available": CHROMADB_AVAILABLE,
        "chroma_connection_mode": chromadb_connection_mode(),
        "collection_name": service.collection_name,
        "document_count": collection_count,
    }
