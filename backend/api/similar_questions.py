"""
Benzer Soru Önerisi API Endpoint'leri

Task 75: Benzer Soru Önerisi
Requirements: REQ-13.7
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field

try:
    from core.dependencies import get_current_user
    from services.similar_question_service import (
        SimilarQuestionService,
        SimilarQuestionResult,
        get_similar_question_service,
    )
except ImportError:
    from core.dependencies import get_current_user
    from services.similar_question_service import (
        SimilarQuestionService,
        SimilarQuestionResult,
        get_similar_question_service,
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/similar-questions", tags=["similar-questions"])


# Request/Response modelleri
class GenerateEmbeddingRequest(BaseModel):
    """Embedding oluşturma isteği"""

    question_id: str = Field(..., description="Soru ID")
    text: str = Field(..., description="Soru metni")
    subject: str = Field(..., description="Ders")
    topic: str = Field(..., description="Konu")
    difficulty: float = Field(..., ge=0, le=10, description="Zorluk seviyesi")
    exam_type: str = Field(..., description="Sınav türü")


class BatchEmbeddingRequest(BaseModel):
    """Toplu embedding isteği"""

    questions: List[Dict[str, Any]] = Field(..., description="Soru listesi")


class SimilarQuestionResponse(BaseModel):
    """Benzer soru yanıtı"""

    question_id: str
    text: str
    similarity_score: float
    subject: str
    topic: str
    difficulty: float
    exam_type: str
    match_reason: str


class SimilarQuestionsListResponse(BaseModel):
    """Benzer sorular listesi yanıtı"""

    success: bool
    total: int
    query_question_id: str
    results: List[SimilarQuestionResponse]
    filters_applied: Dict[str, Any]


class ServiceStatsResponse(BaseModel):
    """Servis istatistikleri yanıtı"""

    total_embeddings: int
    has_similarity_matrix: bool
    cache_dir: str
    berturk_cache_size: int
    topics: Optional[Dict[str, int]] = None
    difficulty_stats: Optional[Dict[str, float]] = None
    similarity_matrix_shape: Optional[List[int]] = None


# ========== Embedding Yönetimi Endpoint'leri ==========


@router.post("/embeddings/generate")
async def generate_embedding(
    request: GenerateEmbeddingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Tek bir soru için embedding oluştur

    Task 75.1: Question vectorization
    """
    try:
        embedding = service.generate_question_embedding(
            question_id=request.question_id,
            text=request.text,
            subject=request.subject,
            topic=request.topic,
            difficulty=request.difficulty,
            exam_type=request.exam_type,
        )

        return {
            "success": True,
            "message": "Embedding oluşturuldu",
            "question_id": embedding.question_id,
            "embedding_dimension": len(embedding.embedding),
        }

    except Exception as e:
        logger.error(f"Embedding oluşturma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding hatası: {str(e)}")


@router.post("/embeddings/batch")
async def generate_batch_embeddings(
    request: BatchEmbeddingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Toplu soru embedding'leri oluştur

    Task 75.1: Semantic embeddings (batch)
    """
    try:
        embeddings = service.generate_batch_embeddings(request.questions)

        return {
            "success": True,
            "message": f"{len(embeddings)} embedding oluşturuldu",
            "total": len(embeddings),
        }

    except Exception as e:
        logger.error(f"Toplu embedding hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Toplu embedding hatası: {str(e)}")


@router.post("/embeddings/build-matrix")
async def build_similarity_matrix(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Similarity matrix oluştur

    Task 75.1: Similarity matrix

    Admin only - tüm sorular için similarity matrix hesaplar
    """
    try:
        # Admin kontrolü
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")

        matrix = service.build_similarity_matrix()

        return {
            "success": True,
            "message": "Similarity matrix oluşturuldu",
            "matrix_shape": list(matrix.shape) if matrix.size > 0 else [0, 0],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similarity matrix hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Matrix hatası: {str(e)}")


# ========== Benzer Soru Önerisi Endpoint'leri ==========


@router.get("/{question_id}", response_model=SimilarQuestionsListResponse)
async def get_similar_questions(
    question_id: str = Path(..., description="Soru ID"),
    k: int = Query(default=10, ge=1, le=50, description="Öneri sayısı"),
    similarity_threshold: float = Query(
        default=0.6, ge=0.0, le=1.0, description="Minimum benzerlik"
    ),
    same_topic_only: bool = Query(default=True, description="Sadece aynı konu"),
    difficulty_range: Optional[float] = Query(
        default=None, ge=0.0, le=5.0, description="Zorluk aralığı"
    ),
    student_performance: Optional[float] = Query(
        default=None, ge=0.0, le=1.0, description="Öğrenci performansı"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Benzer soru önerileri getir

    Combines all tasks:
    - Task 75.1: Question embeddings
    - Task 75.2: Semantic similarity
    - Task 75.3: Topic filtering
    - Task 75.4: Difficulty filtering

    Args:
        question_id: Query soru ID
        k: Öneri sayısı
        similarity_threshold: Minimum benzerlik eşiği (0-1)
        same_topic_only: Sadece aynı konudan öner
        difficulty_range: Zorluk aralığı (±)
        student_performance: Öğrenci performansı (0-1, adaptif filtreleme için)
    """
    try:
        results = service.get_similar_questions(
            question_id=question_id,
            k=k,
            similarity_threshold=similarity_threshold,
            same_topic_only=same_topic_only,
            difficulty_range=difficulty_range,
            student_performance=student_performance,
        )

        # Response'a çevir
        response_results = [
            SimilarQuestionResponse(
                question_id=r.question_id,
                text=r.text,
                similarity_score=r.similarity_score,
                subject=r.subject,
                topic=r.topic,
                difficulty=r.difficulty,
                exam_type=r.exam_type,
                match_reason=r.match_reason,
            )
            for r in results
        ]

        return SimilarQuestionsListResponse(
            success=True,
            total=len(response_results),
            query_question_id=question_id,
            results=response_results,
            filters_applied={
                "similarity_threshold": similarity_threshold,
                "same_topic_only": same_topic_only,
                "difficulty_range": difficulty_range,
                "student_performance": student_performance,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Benzer soru önerisi hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Öneri hatası: {str(e)}")


@router.get("/{question_id}/cross-topic")
async def get_cross_topic_suggestions(
    question_id: str = Path(..., description="Soru ID"),
    k: int = Query(default=5, ge=1, le=20, description="Öneri sayısı"),
    similarity_threshold: float = Query(
        default=0.6, ge=0.0, le=1.0, description="Minimum benzerlik"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Çapraz konu önerileri getir

    Task 75.3: Cross-topic suggestions

    Farklı konulardan ama semantik olarak benzer soruları önerir
    """
    try:
        results = service.get_cross_topic_suggestions(
            question_id=question_id, k=k, similarity_threshold=similarity_threshold
        )

        response_results = [
            SimilarQuestionResponse(
                question_id=r.question_id,
                text=r.text,
                similarity_score=r.similarity_score,
                subject=r.subject,
                topic=r.topic,
                difficulty=r.difficulty,
                exam_type=r.exam_type,
                match_reason=r.match_reason,
            )
            for r in results
        ]

        return {
            "success": True,
            "total": len(response_results),
            "query_question_id": question_id,
            "results": response_results,
            "note": "Farklı konulardan ama semantik olarak benzer sorular",
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Çapraz konu önerisi hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Öneri hatası: {str(e)}")


@router.get("/{question_id}/progressive")
async def get_progressive_difficulty_suggestions(
    question_id: str = Path(..., description="Soru ID"),
    k: int = Query(default=5, ge=1, le=20, description="Öneri sayısı"),
    difficulty_increment: float = Query(
        default=0.5, ge=0.0, le=3.0, description="Zorluk artışı"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Giderek zorlaşan soru önerileri

    Task 75.4: Progressive difficulty

    Benzer ama giderek daha zor soruları önerir
    """
    try:
        results = service.get_progressive_difficulty_suggestions(
            question_id=question_id, k=k, difficulty_increment=difficulty_increment
        )

        response_results = [
            SimilarQuestionResponse(
                question_id=r.question_id,
                text=r.text,
                similarity_score=r.similarity_score,
                subject=r.subject,
                topic=r.topic,
                difficulty=r.difficulty,
                exam_type=r.exam_type,
                match_reason=r.match_reason,
            )
            for r in results
        ]

        return {
            "success": True,
            "total": len(response_results),
            "query_question_id": question_id,
            "results": response_results,
            "difficulty_increment": difficulty_increment,
            "note": "Giderek zorlaşan benzer sorular",
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Progressive difficulty hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Öneri hatası: {str(e)}")


@router.get("/{question_id}/adaptive")
async def get_adaptive_suggestions(
    question_id: str = Path(..., description="Soru ID"),
    student_performance: float = Query(
        ..., ge=0.0, le=1.0, description="Öğrenci performansı"
    ),
    k: int = Query(default=5, ge=1, le=20, description="Öneri sayısı"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Öğrenci performansına göre adaptif öneriler

    Task 75.4: Adaptive suggestions

    Öğrenci başarı oranına göre zorluk seviyesini ayarlar:
    - Yüksek performans (≥0.8): Daha zor sorular
    - Orta performans (0.6-0.8): Benzer zorluk
    - Düşük performans (<0.6): Daha kolay sorular
    """
    try:
        results = service.get_adaptive_suggestions(
            question_id=question_id, student_performance=student_performance, k=k
        )

        response_results = [
            SimilarQuestionResponse(
                question_id=r.question_id,
                text=r.text,
                similarity_score=r.similarity_score,
                subject=r.subject,
                topic=r.topic,
                difficulty=r.difficulty,
                exam_type=r.exam_type,
                match_reason=r.match_reason,
            )
            for r in results
        ]

        # Performans kategorisi
        if student_performance >= 0.8:
            performance_category = "Yüksek"
            adjustment = "Daha zor sorular önerildi"
        elif student_performance >= 0.6:
            performance_category = "Orta"
            adjustment = "Benzer zorlukta sorular önerildi"
        else:
            performance_category = "Düşük"
            adjustment = "Daha kolay sorular önerildi"

        return {
            "success": True,
            "total": len(response_results),
            "query_question_id": question_id,
            "results": response_results,
            "student_performance": student_performance,
            "performance_category": performance_category,
            "adjustment": adjustment,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Adaptif öneri hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Öneri hatası: {str(e)}")


# ========== Yönetim Endpoint'leri ==========


@router.get("/stats", response_model=ServiceStatsResponse)
async def get_service_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Servis istatistiklerini getir

    Embedding sayısı, cache durumu, konu dağılımı vb.
    """
    try:
        stats = service.get_stats()

        return ServiceStatsResponse(
            total_embeddings=stats["total_embeddings"],
            has_similarity_matrix=stats["has_similarity_matrix"],
            cache_dir=stats["cache_dir"],
            berturk_cache_size=stats["berturk_cache_size"],
            topics=stats.get("topics"),
            difficulty_stats=stats.get("difficulty_stats"),
            similarity_matrix_shape=list(stats["similarity_matrix_shape"])
            if "similarity_matrix_shape" in stats
            else None,
        )

    except Exception as e:
        logger.error(f"İstatistik hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"İstatistik hatası: {str(e)}")


@router.post("/cache/save")
async def save_cache(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Embedding cache'ini diske kaydet

    Admin only
    """
    try:
        # Admin kontrolü
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")

        service.save_embeddings_to_disk()

        return {
            "success": True,
            "message": "Cache kaydedildi",
            "total_embeddings": len(service.question_embeddings),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache kaydetme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cache hatası: {str(e)}")


@router.post("/cache/load")
async def load_cache(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: SimilarQuestionService = Depends(get_similar_question_service),
):
    """
    Embedding cache'ini diskten yükle

    Admin only
    """
    try:
        # Admin kontrolü
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")

        success = service.load_embeddings_from_disk()

        if not success:
            raise HTTPException(status_code=404, detail="Cache dosyası bulunamadı")

        return {
            "success": True,
            "message": "Cache yüklendi",
            "total_embeddings": len(service.question_embeddings),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache yükleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cache hatası: {str(e)}")
