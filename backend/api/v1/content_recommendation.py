"""
Content Recommendation API - KIRO2 Egitim Platformu

Spec REQ-4: Kisisellestirilmis icerik oneri API'si.

Endpoints:
- POST /api/v1/recommendations/ - Kullanici icin oneri getir
- POST /api/v1/recommendations/interaction - Etkilesim kaydet
- GET /api/v1/recommendations/ctr-stats - CTR istatistikleri (REQ-4.6)
- GET /api/v1/recommendations/user/{user_id}/profile - Kullanici profil

Author: KIRO2 Team
Date: 2026-01-19
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    from services.content_recommendation_service import (
        UserInteraction,
        InteractionType,
        get_recommendation_service,
    )
    RECOMMENDATION_AVAILABLE = True
except (ImportError, OSError, Exception) as e:
    RECOMMENDATION_AVAILABLE = False
    UserInteraction = None
    InteractionType = None
    get_recommendation_service = None
    logger.warning(f"content_recommendation_service not available: {e}")

router = APIRouter(
    prefix="/api/v1/recommendations",
    tags=["recommendations", "chromadb"],
    responses={404: {"description": "Not found"}},
)


# ============================================================================
# Pydantic Models
# ============================================================================


class RecommendationRequest(BaseModel):
    """Oneri istegi."""
    user_id: str = Field(..., description="Kullanici ID'si", min_length=1)
    limit: int = Field(default=10, ge=1, le=100, description="Maksimum oneri sayisi")
    subject_filter: Optional[str] = Field(default=None, description="Konu filtresi")
    ensure_diversity: bool = Field(default=True, description="Cesitlilik sagla (REQ-4.5)")


class ContentRecommendation(BaseModel):
    """Tek bir oneri."""
    content_id: str
    content_preview: str
    score: float
    metadata: dict
    recommendation_type: str


class RecommendationResponse(BaseModel):
    """Oneri yaniti."""
    user_id: str
    recommendations: list[ContentRecommendation]
    is_cold_start: bool
    strategy_used: str
    diversity_score: float
    generated_at: datetime


class InteractionRequest(BaseModel):
    """Etkilesim kayit istegi."""
    user_id: str = Field(..., description="Kullanici ID'si", min_length=1)
    content_id: str = Field(..., description="Icerik ID'si", min_length=1)
    interaction_type: str = Field(
        ...,
        description="Etkilesim tipi: view, like, complete, bookmark, share, skip, dislike"
    )
    duration_seconds: int = Field(default=0, ge=0, description="Etkilesim suresi (saniye)")
    metadata: dict = Field(default_factory=dict, description="Ek metadata")


class InteractionResponse(BaseModel):
    """Etkilesim kayit yaniti."""
    success: bool
    message: str
    user_id: str
    content_id: str
    interaction_type: str
    recorded_at: datetime


class CTRStats(BaseModel):
    """CTR istatistikleri (REQ-4.6)."""
    total_content: int
    average_ctr: float
    top_performing: list[dict]
    bottom_performing: list[dict]
    improvement_vs_baseline: Optional[float] = Field(
        default=None,
        description="Baseline'a gore iyilesme yuzdesi (hedef: %300)"
    )


class UserProfileResponse(BaseModel):
    """Kullanici profil yaniti."""
    user_id: str
    interaction_count: int
    is_cold_start: bool
    preferred_subjects: list[str]
    last_updated: Optional[datetime]
    embedding_dimension: int


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/",
    response_model=RecommendationResponse,
    summary="Icerik onerileri getir",
    description="""
    Kullanici icin kisisellestirilmis icerik onerileri getirir.

    Spec REQ-4.3, REQ-4.4, REQ-4.5:
    - Hybrid filtering (collaborative + content-based)
    - Cold-start fallback (popularity-based)
    - Diversity sampling
    """
)
async def get_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """Kullanici icin icerik onerileri getir."""
    if not RECOMMENDATION_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation service not available"
        )

    try:
        service = get_recommendation_service()

        result = await service.get_recommendations(
            user_id=request.user_id,
            limit=request.limit,
            subject_filter=request.subject_filter,
            ensure_diversity=request.ensure_diversity,
        )

        # Convert to response format
        recommendations = [
            ContentRecommendation(
                content_id=rec.content_id,
                content_preview=rec.content_preview,
                score=rec.score,
                metadata=rec.metadata,
                recommendation_type=rec.recommendation_type,
            )
            for rec in result.recommendations
        ]

        return RecommendationResponse(
            user_id=result.user_id,
            recommendations=recommendations,
            is_cold_start=result.is_cold_start,
            strategy_used=result.strategy_used,
            diversity_score=result.diversity_score,
            generated_at=result.generated_at,
        )

    except Exception as e:
        logger.error(f"Recommendations failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post(
    "/interaction",
    response_model=InteractionResponse,
    summary="Etkilesim kaydet",
    description="""
    Kullanici etkilesimini kaydeder.

    Etkilesim tipleri:
    - view: Goruntulenme
    - like: Begeni
    - complete: Tamamlama
    - bookmark: Yer imi
    - share: Paylasim
    - skip: Atlama
    - dislike: Begenmeme
    """
)
async def record_interaction(request: InteractionRequest) -> InteractionResponse:
    """Kullanici etkilesimini kaydet."""
    if not RECOMMENDATION_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation service not available"
        )

    try:
        # Validate interaction type
        try:
            interaction_type = InteractionType(request.interaction_type)
        except ValueError:
            valid_types = [t.value for t in InteractionType]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Gecersiz etkilesim tipi. Gecerli tipler: {valid_types}"
            )

        service = get_recommendation_service()

        interaction = UserInteraction(
            user_id=request.user_id,
            content_id=request.content_id,
            interaction_type=interaction_type,
            duration_seconds=request.duration_seconds,
            metadata=request.metadata,
        )

        success = await service.record_interaction(interaction)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Etkilesim kaydedilemedi"
            )

        return InteractionResponse(
            success=True,
            message="Etkilesim basariyla kaydedildi",
            user_id=request.user_id,
            content_id=request.content_id,
            interaction_type=request.interaction_type,
            recorded_at=datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interaction recording failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/ctr-stats",
    response_model=CTRStats,
    summary="CTR istatistikleri getir",
    description="""
    Click-through rate (CTR) istatistiklerini getirir.

    Spec REQ-4.6: CTR tracking.
    Hedef: %300 iyilesme.
    """
)
async def get_ctr_stats(
    baseline_ctr: float = Query(
        default=2.0,
        ge=0.0,
        le=100.0,
        description="Baseline CTR yuzdesi (karsilastirma icin)"
    )
) -> CTRStats:
    """CTR istatistiklerini getir (REQ-4.6)."""
    try:
        service = get_recommendation_service()
        report = await service.get_ctr_report()

        # Calculate improvement vs baseline
        improvement = None
        if report["average_ctr"] > 0 and baseline_ctr > 0:
            improvement = round(
                ((report["average_ctr"] - baseline_ctr) / baseline_ctr) * 100,
                2
            )

        return CTRStats(
            total_content=report["total_content"],
            average_ctr=report["average_ctr"],
            top_performing=report["top_performing"],
            bottom_performing=report["bottom_performing"],
            improvement_vs_baseline=improvement,
        )

    except Exception as e:
        logger.error(f"CTR stats failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/user/{user_id}/profile",
    response_model=UserProfileResponse,
    summary="Kullanici profili getir",
    description="Kullanici profil embedding bilgilerini getirir."
)
async def get_user_profile(user_id: str) -> UserProfileResponse:
    """Kullanici profilini getir."""
    try:
        service = get_recommendation_service()

        # Update and get profile
        profile = await service._update_user_profile(user_id)

        return UserProfileResponse(
            user_id=profile.user_id,
            interaction_count=profile.interaction_count,
            is_cold_start=profile.is_cold_start,
            preferred_subjects=profile.preferred_subjects,
            last_updated=profile.last_updated,
            embedding_dimension=len(profile.embedding),
        )

    except Exception as e:
        logger.error(f"User profile failed for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get(
    "/health",
    summary="Oneri servisi saglik kontrolu"
)
async def health_check() -> dict:
    """Oneri servisinin saglik durumunu kontrol et."""
    try:
        service = get_recommendation_service()
        initialized = await service.initialize()

        return {
            "status": "healthy" if initialized else "degraded",
            "service": "content_recommendation",
            "chromadb_available": initialized,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "content_recommendation",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
