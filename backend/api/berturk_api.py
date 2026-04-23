"""
BERTurk API Endpoints
Duygu analizi, motivasyon tespiti ve intent detection API'leri
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

try:
    from core.berturk_service import berturk_service
except (ImportError, TypeError):
    berturk_service = None

from core.dependencies import AuthenticatedUser, UserRole, get_current_user

_STAFF_CAN_TARGET_STUDENT = frozenset(
    {UserRole.TEACHER, UserRole.ADMIN, UserRole.SUPER_ADMIN}
)
_BERTURK_ADMIN_ROLES = frozenset({UserRole.ADMIN, UserRole.SUPER_ADMIN})

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/berturk", tags=["BERTurk NLP"])


def _require_berturk_service() -> None:
    """Fail fast with 503 if the optional BERTurk transformer service is
    unavailable. The module-level `berturk_service` falls back to ``None`` when
    the heavy `transformers` dependency or model weights are missing; calling
    any method on it would crash the handler with a generic 500 that hides the
    real cause. See GF22 in golden-flows.md.
    """
    if berturk_service is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "BERTurk NLP servisi su anda kullanilamiyor "
                "(model veya bagimliliklar yuklu degil)."
            ),
        )


# Request Models
class SentimentAnalysisRequest(BaseModel):
    """Duygu analizi isteği"""

    text: str = Field(
        ..., description="Analiz edilecek metin", min_length=1, max_length=5000
    )
    include_emotions: bool = Field(
        True, description="Detaylı duygu skorları dahil edilsin mi"
    )
    educational_context: bool = Field(
        True, description="Eğitim bağlamı analizi yapılsın mı"
    )


class MotivationAssessmentRequest(BaseModel):
    """Motivasyon değerlendirme isteği"""

    student_id: str = Field(..., description="Öğrenci ID'si")
    recent_texts: list[str] = Field(
        ...,
        description="Son metinler (sohbet, yorumlar, vs.)",
        min_items=1,
        max_items=50,
    )
    time_window_hours: int = Field(
        24, description="Değerlendirme zaman penceresi (saat)", ge=1, le=168
    )


class IntentDetectionRequest(BaseModel):
    """Niyet tespit isteği"""

    text: str = Field(
        ..., description="Analiz edilecek metin", min_length=1, max_length=2000
    )


class ContextualMeaningRequest(BaseModel):
    """Bağlamsal anlam çıkarma isteği"""

    text: str = Field(
        ..., description="Analiz edilecek metin", min_length=1, max_length=5000
    )


class BatchAnalysisRequest(BaseModel):
    """Toplu analiz isteği"""

    texts: list[str] = Field(
        ..., description="Analiz edilecek metinler", min_items=1, max_items=100
    )
    analysis_type: str = Field(
        ..., description="Analiz tipi: sentiment, intent, contextual"
    )
    include_emotions: bool = Field(
        True, description="Duygu analizi için detaylı skorlar"
    )
    educational_context: bool = Field(True, description="Eğitim bağlamı analizi")


# Response Models
class SentimentAnalysisResponse(BaseModel):
    """Duygu analizi yanıtı"""

    success: bool
    data: dict[str, Any] | None = None
    message: str
    processing_time_ms: float | None = None


class MotivationAssessmentResponse(BaseModel):
    """Motivasyon değerlendirme yanıtı"""

    success: bool
    data: dict[str, Any] | None = None
    message: str
    processing_time_ms: float | None = None


class IntentDetectionResponse(BaseModel):
    """Niyet tespit yanıtı"""

    success: bool
    data: dict[str, Any] | None = None
    message: str
    processing_time_ms: float | None = None


class ContextualMeaningResponse(BaseModel):
    """Bağlamsal anlam yanıtı"""

    success: bool
    data: dict[str, Any] | None = None
    message: str
    processing_time_ms: float | None = None


class BatchAnalysisResponse(BaseModel):
    """Toplu analiz yanıtı"""

    success: bool
    data: dict[str, Any] | None = None
    message: str
    total_processed: int
    processing_time_ms: float | None = None


class PerformanceStatsResponse(BaseModel):
    """Performans istatistikleri yanıtı"""

    success: bool
    data: dict[str, Any] | None = None
    message: str


@router.post("/sentiment/analyze", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Metinin duygu analizini yap

    - **text**: Analiz edilecek metin (1-5000 karakter)
    - **include_emotions**: Detaylı duygu skorları (joy, sadness, anger, fear, surprise, disgust)
    - **educational_context**: Eğitim bağlamı skorları (motivation, frustration, engagement, confusion, confidence, anxiety)

    Returns:
    - Sentiment (positive/negative/neutral)
    - Confidence score
    - Detailed emotion scores (opsiyonel)
    - Educational context scores (opsiyonel)
    """
    _require_berturk_service()
    try:
        start_time = datetime.now()

        # BERTurk servisi ile duygu analizi
        result = await berturk_service.analyze_sentiment(
            text=request.text,
            include_emotions=request.include_emotions,
            educational_context=request.educational_context,
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return SentimentAnalysisResponse(
            success=True,
            data={
                "text": result.text,
                "sentiment": result.sentiment,
                "confidence": result.confidence,
                "emotion_scores": result.emotion_scores,
                "educational_context": result.educational_context,
                "timestamp": result.timestamp.isoformat(),
            },
            message="Duygu analizi başarıyla tamamlandı",
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Duygu analizi API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/motivation/assess", response_model=MotivationAssessmentResponse)
async def assess_student_motivation(
    request: MotivationAssessmentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Öğrenci motivasyon durumunu değerlendir

    - **student_id**: Öğrenci ID'si
    - **recent_texts**: Son metinler (1-50 adet)
    - **time_window_hours**: Değerlendirme zaman penceresi (1-168 saat)

    Returns:
    - Motivation level (0.0-1.0)
    - Engagement score (0.0-1.0)
    - Frustration level (0.0-1.0)
    - Confidence level (0.0-1.0)
    - Learning enthusiasm (0.0-1.0)
    - Support needed (boolean)
    - Recommendations (list)
    """
    _require_berturk_service()
    try:
        start_time = datetime.now()

        if current_user.role not in _STAFF_CAN_TARGET_STUDENT and str(
            current_user.id
        ) != str(request.student_id):
            raise HTTPException(
                status_code=403,
                detail="Bu öğrencinin motivasyon verilerine erişim yetkiniz yok",
            )

        # Motivasyon değerlendirmesi
        result = await berturk_service.assess_student_motivation(
            student_id=request.student_id,
            recent_texts=request.recent_texts,
            time_window_hours=request.time_window_hours,
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return MotivationAssessmentResponse(
            success=True,
            data={
                "student_id": result.student_id,
                "motivation_level": result.motivation_level,
                "engagement_score": result.engagement_score,
                "frustration_level": result.frustration_level,
                "confidence_level": result.confidence_level,
                "learning_enthusiasm": result.learning_enthusiasm,
                "support_needed": result.support_needed,
                "recommendations": result.recommendations,
                "analysis_timestamp": result.analysis_timestamp.isoformat(),
            },
            message="Motivasyon değerlendirmesi başarıyla tamamlandı",
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Motivasyon değerlendirme API hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/intent/detect", response_model=IntentDetectionResponse)
async def detect_intent(
    request: IntentDetectionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Metindeki niyeti tespit et

    - **text**: Analiz edilecek metin (1-2000 karakter)

    Returns:
    - Intent (question, help_request, complaint, compliment, confusion, technical_issue)
    - Confidence score
    - Extracted entities
    - Context category (academic, technical, emotional, social)
    - Urgency level (low, medium, high, critical)
    """
    _require_berturk_service()
    try:
        start_time = datetime.now()

        # Intent tespiti
        result = await berturk_service.detect_intent(request.text)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return IntentDetectionResponse(
            success=True,
            data={
                "text": result.text,
                "intent": result.intent,
                "confidence": result.confidence,
                "entities": result.entities,
                "context_category": result.context_category,
                "urgency_level": result.urgency_level,
            },
            message="Niyet tespiti başarıyla tamamlandı",
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Intent tespit API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/contextual/extract", response_model=ContextualMeaningResponse)
async def extract_contextual_meaning(
    request: ContextualMeaningRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Bağlamsal anlam çıkarma

    - **text**: Analiz edilecek metin (1-5000 karakter)

    Returns:
    - Main topic
    - Subtopics
    - Difficulty level (0.0-1.0)
    - Academic domain (mathematics, science, language, social_studies, general)
    - Key concepts
    - Semantic similarity score
    """
    _require_berturk_service()
    try:
        start_time = datetime.now()

        # Bağlamsal anlam çıkarma
        result = await berturk_service.extract_contextual_meaning(request.text)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return ContextualMeaningResponse(
            success=True,
            data={
                "text": result.text,
                "main_topic": result.main_topic,
                "subtopics": result.subtopics,
                "difficulty_level": result.difficulty_level,
                "academic_domain": result.academic_domain,
                "key_concepts": result.key_concepts,
                "semantic_similarity_score": result.semantic_similarity_score,
            },
            message="Bağlamsal anlam çıkarma başarıyla tamamlandı",
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bağlamsal anlam çıkarma API hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/batch/analyze", response_model=BatchAnalysisResponse)
async def batch_analysis(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Toplu metin analizi

    - **texts**: Analiz edilecek metinler (1-100 adet)
    - **analysis_type**: Analiz tipi (sentiment, intent, contextual)
    - **include_emotions**: Duygu analizi için detaylı skorlar
    - **educational_context**: Eğitim bağlamı analizi

    Returns:
    - Batch analysis results
    - Processing statistics
    """
    _require_berturk_service()
    try:
        start_time = datetime.now()

        if len(request.texts) > 100:
            raise HTTPException(
                status_code=400, detail="Maksimum 100 metin analiz edilebilir"
            )

        results = []

        for i, text in enumerate(request.texts):
            try:
                if request.analysis_type == "sentiment":
                    result = await berturk_service.analyze_sentiment(
                        text=text,
                        include_emotions=request.include_emotions,
                        educational_context=request.educational_context,
                    )
                    results.append(
                        {
                            "index": i,
                            "text": text,
                            "result": {
                                "sentiment": result.sentiment,
                                "confidence": result.confidence,
                                "emotion_scores": result.emotion_scores,
                                "educational_context": result.educational_context,
                            },
                        }
                    )

                elif request.analysis_type == "intent":
                    result = await berturk_service.detect_intent(text)
                    results.append(
                        {
                            "index": i,
                            "text": text,
                            "result": {
                                "intent": result.intent,
                                "confidence": result.confidence,
                                "entities": result.entities,
                                "context_category": result.context_category,
                                "urgency_level": result.urgency_level,
                            },
                        }
                    )

                elif request.analysis_type == "contextual":
                    result = await berturk_service.extract_contextual_meaning(text)
                    results.append(
                        {
                            "index": i,
                            "text": text,
                            "result": {
                                "main_topic": result.main_topic,
                                "subtopics": result.subtopics,
                                "difficulty_level": result.difficulty_level,
                                "academic_domain": result.academic_domain,
                                "key_concepts": result.key_concepts,
                            },
                        }
                    )

                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Geçersiz analiz tipi. Kullanılabilir: sentiment, intent, contextual",
                    )

            except Exception as e:
                logger.error(f"Toplu analiz - metin {i} hatası: {e}")
                results.append({"index": i, "text": text, "error": "Analiz basarisiz"})

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return BatchAnalysisResponse(
            success=True,
            data={
                "results": results,
                "analysis_type": request.analysis_type,
                "total_texts": len(request.texts),
                "successful_analyses": len([r for r in results if "error" not in r]),
                "failed_analyses": len([r for r in results if "error" in r]),
            },
            message="Toplu analiz başarıyla tamamlandı",
            total_processed=len(request.texts),
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Toplu analiz API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/performance/stats", response_model=PerformanceStatsResponse)
async def get_performance_stats(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    BERTurk servisi performans istatistiklerini getir

    Sadece admin kullanıcıları erişebilir.

    Returns:
    - Total analyses count
    - Cache hit rate
    - Average inference time
    - Error count
    - Cache size
    """
    _require_berturk_service()
    try:
        if current_user.role not in _BERTURK_ADMIN_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Performans istatistiklerine sadece admin kullanıcıları erişebilir",
            )

        stats = await berturk_service.get_performance_stats()

        return PerformanceStatsResponse(
            success=True,
            data=stats,
            message="Performans istatistikleri başarıyla getirildi",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performans istatistikleri API hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/cache/clear")
async def clear_cache(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    BERTurk servisi cache'ini temizle

    Sadece admin kullanıcıları erişebilir.
    """
    _require_berturk_service()
    try:
        if current_user.role not in _BERTURK_ADMIN_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Cache temizleme işlemine sadece admin kullanıcıları erişebilir",
            )

        await berturk_service.clear_cache()

        return {"success": True, "message": "BERTurk cache başarıyla temizlendi"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache temizleme API hatası: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/health")
async def health_check():
    """
    BERTurk servisi sağlık kontrolü
    """
    if berturk_service is None:
        return {
            "success": False,
            "message": "BERTurk servisi bagimliliklari yuklu degil",
            "status": "unavailable",
            "test_analysis_completed": False,
        }
    try:
        # Basit sağlık kontrolü
        test_result = await berturk_service.analyze_sentiment(
            "Test mesajı", include_emotions=False, educational_context=False
        )

        return {
            "success": True,
            "message": "BERTurk servisi çalışıyor",
            "status": "healthy",
            "test_analysis_completed": test_result.sentiment is not None,
        }

    except Exception as e:
        logger.error(f"BERTurk sağlık kontrolü hatası: {e}")
        return {
            "success": False,
            "message": "BERTurk servisi saglik kontrolu basarisiz",
            "status": "unhealthy",
        }
