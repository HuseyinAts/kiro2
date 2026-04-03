"""
Duplicate Detection API - KIRO2 Soru Bankasi

Spec REQ-5: Duplicate soru tespiti ve yonetimi API'si.

Endpoints:
- POST /api/v1/duplicates/check - Duplicate kontrol
- POST /api/v1/duplicates/add-with-check - Duplicate kontrolu ile ekleme
- POST /api/v1/duplicates/merge - Duplicate birlestirme
- GET /api/v1/duplicates/stats - Istatistikler
- GET /api/v1/duplicates/pending-review - Manuel inceleme bekleyenler (REQ-5.4)
- POST /api/v1/duplicates/review/{question_id} - Inceleme sonucu kaydet

Author: KIRO2 Team
Date: 2026-01-19
"""

import logging
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    from services.duplicate_detection_service import (
        DuplicateStatus,
        get_duplicate_service,
    )

    DUPLICATE_AVAILABLE = True
except (ImportError, OSError, Exception) as e:
    DUPLICATE_AVAILABLE = False
    DuplicateStatus = None
    get_duplicate_service = None
    logger.warning(f"duplicate_detection_service not available: {e}")

try:
    from services.pending_review_service import (
        ReviewStatus as ServiceReviewStatus,
    )
    from services.pending_review_service import (
        get_pending_review_service,
    )

    REVIEW_AVAILABLE = True
except (ImportError, OSError, Exception) as e:
    REVIEW_AVAILABLE = False
    get_pending_review_service = None
    ServiceReviewStatus = None
    logger.warning(f"pending_review_service not available: {e}")

router = APIRouter(
    prefix="/api/v1/duplicates",
    tags=["duplicates", "chromadb"],
    responses={404: {"description": "Not found"}},
)


class ReviewDecision(str, Enum):
    """Manuel inceleme kararlari."""

    APPROVE_ADD = "approve_add"  # Eklemeyi onayla
    REJECT_DUPLICATE = "reject_duplicate"  # Duplicate olarak reddet
    MERGE_WITH = "merge_with"  # Mevcut soru ile birlestir


# ============================================================================
# Pydantic Models
# ============================================================================


class DuplicateCheckRequest(BaseModel):
    """Duplicate kontrol istegi."""

    content: str = Field(
        ..., description="Kontrol edilecek soru icerigi", min_length=10
    )
    subject: str | None = Field(default=None, description="Konu filtresi")
    check_paraphrase: bool = Field(default=True, description="Paraphrase detection yap")
    similarity_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Ozel benzerlik esigi (varsayilan: 0.95)",
    )


class SimilarQuestion(BaseModel):
    """Benzer soru."""

    id: str
    content_preview: str
    similarity: float
    metadata: dict


class DuplicateCheckResponse(BaseModel):
    """Duplicate kontrol yaniti."""

    status: str
    is_duplicate: bool
    similarity_score: float
    similar_questions: list[SimilarQuestion]
    recommendation: str
    can_add: bool
    requires_manual_review: bool = Field(
        default=False, description="Manuel inceleme gerekiyor mu (REQ-5.4)"
    )
    merge_candidates: list[str]


class AddWithCheckRequest(BaseModel):
    """Duplicate kontrolu ile ekleme istegi."""

    content: str = Field(..., description="Soru icerigi", min_length=10)
    metadata: dict = Field(default_factory=dict, description="Soru metadata'si")
    question_id: str | None = Field(default=None, description="Opsiyonel soru ID")
    force: bool = Field(
        default=False, description="Duplicate olsa bile ekle (admin icin)"
    )


class AddWithCheckResponse(BaseModel):
    """Duplicate kontrolu ile ekleme yaniti."""

    success: bool
    question_id: str
    duplicate_check: DuplicateCheckResponse
    message: str


class MergeRequest(BaseModel):
    """Duplicate birlestirme istegi."""

    primary_id: str = Field(..., description="Ana soru ID'si (korunacak)")
    secondary_ids: list[str] = Field(
        ..., description="Birlestirilecek soru ID'leri", min_length=1
    )
    merge_strategy: str = Field(
        default="keep_primary",
        description="Birlestirme stratejisi: keep_primary, merge_all, keep_newest",
    )


class MergeResponse(BaseModel):
    """Duplicate birlestirme yaniti."""

    success: bool
    merged_id: str
    merged_metadata: dict
    archived_ids: list[str]
    message: str


class DuplicateStats(BaseModel):
    """Duplicate istatistikleri."""

    total_questions: int
    sample_size: int
    potential_duplicates: int
    duplicate_rate: float
    thresholds: dict
    pending_review_count: int


class PendingReviewItem(BaseModel):
    """Manuel inceleme bekleyen oge (REQ-5.4)."""

    question_id: str
    content_preview: str
    similarity_score: float
    similar_to_id: str
    similar_to_preview: str
    flagged_at: datetime
    status: str


class ReviewRequest(BaseModel):
    """Inceleme sonucu kayit istegi (REQ-5.4)."""

    decision: ReviewDecision
    merge_with_id: str | None = Field(
        default=None, description="MERGE_WITH karari icin hedef soru ID"
    )
    reviewer_notes: str = Field(default="", description="Inceleme notlari")


class ReviewResponse(BaseModel):
    """Inceleme sonucu yaniti."""

    success: bool
    question_id: str
    decision: str
    message: str
    processed_at: datetime


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/check",
    response_model=DuplicateCheckResponse,
    summary="Duplicate kontrol",
    description="""
    Soru iceriginin duplicate olup olmadigini kontrol eder.

    Spec REQ-5.1, REQ-5.2, REQ-5.3, REQ-5.4, REQ-5.5:
    - Similarity search ile duplicate kontrol
    - >= 0.95 benzerlik = duplicate
    - >= 0.99 benzerlik = exact match (engellenir)
    - 0.90-0.95 arasi = near-duplicate (uyari)
    - Paraphrase detection
    """,
)
async def check_duplicate(
    request: DuplicateCheckRequest, _admin=Depends(get_current_admin_user)
) -> DuplicateCheckResponse:
    """Soru iceriginin duplicate olup olmadigini kontrol et."""
    if not DUPLICATE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Duplicate detection service not available",
        )

    try:
        service = get_duplicate_service()

        result = await service.check_duplicate(
            content=request.content,
            check_paraphrase=request.check_paraphrase,
            similarity_threshold=request.similarity_threshold,
        )

        # Near-duplicate veya duplicate ise manual review flag'i set et (REQ-5.4)
        requires_manual_review = result.status in [
            DuplicateStatus.NEAR_DUPLICATE,
            DuplicateStatus.DUPLICATE,
        ]

        similar_questions = [
            SimilarQuestion(
                id=sq["id"],
                content_preview=sq["content_preview"],
                similarity=sq["similarity"],
                metadata=sq["metadata"],
            )
            for sq in result.similar_questions
        ]

        return DuplicateCheckResponse(
            status=result.status.value,
            is_duplicate=result.is_duplicate,
            similarity_score=result.similarity_score,
            similar_questions=similar_questions,
            recommendation=result.recommendation,
            can_add=result.can_add,
            requires_manual_review=requires_manual_review,
            merge_candidates=result.merge_candidates,
        )

    except Exception as e:
        logger.error(f"Duplicate check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post(
    "/add-with-check",
    response_model=AddWithCheckResponse,
    summary="Duplicate kontrolu ile ekleme",
    description="Soru eklenmeden once duplicate kontrolu yapar.",
)
async def add_with_duplicate_check(
    request: AddWithCheckRequest,
    _admin=Depends(get_current_admin_user),
) -> AddWithCheckResponse:
    """Duplicate kontrolu ile soru ekle."""
    try:
        service = get_duplicate_service()

        success, question_id, check_result = await service.add_with_duplicate_check(
            content=request.content,
            metadata=request.metadata,
            question_id=request.question_id,
            force=request.force,
        )

        # Near-duplicate ise pending review'a ekle (REQ-5.4)
        if check_result.status == DuplicateStatus.NEAR_DUPLICATE and success:
            if check_result.similar_questions:
                review_service = get_pending_review_service()
                content_preview = (
                    request.content[:200] + "..."
                    if len(request.content) > 200
                    else request.content
                )
                review_service.add_for_review(
                    question_id=question_id,
                    content_preview=content_preview,
                    similarity_score=check_result.similarity_score,
                    similar_to_id=check_result.similar_questions[0]["id"],
                    similar_to_preview=check_result.similar_questions[0][
                        "content_preview"
                    ],
                )

        similar_questions = [
            SimilarQuestion(
                id=sq["id"],
                content_preview=sq["content_preview"],
                similarity=sq["similarity"],
                metadata=sq["metadata"],
            )
            for sq in check_result.similar_questions
        ]

        duplicate_check = DuplicateCheckResponse(
            status=check_result.status.value,
            is_duplicate=check_result.is_duplicate,
            similarity_score=check_result.similarity_score,
            similar_questions=similar_questions,
            recommendation=check_result.recommendation,
            can_add=check_result.can_add,
            requires_manual_review=check_result.status
            == DuplicateStatus.NEAR_DUPLICATE,
            merge_candidates=check_result.merge_candidates,
        )

        message = "Soru basariyla eklendi" if success else check_result.recommendation

        return AddWithCheckResponse(
            success=success,
            question_id=question_id,
            duplicate_check=duplicate_check,
            message=message,
        )

    except Exception as e:
        logger.error(f"Add with check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post(
    "/merge",
    response_model=MergeResponse,
    summary="Duplicate birlestirme",
    description="""
    Duplicate sorulari birlestirir.

    Spec REQ-5.6: Metadata merge.

    Stratejiler:
    - keep_primary: Ana soru metadata'sini koru
    - merge_all: Tum metadata'lari birlestir
    - keep_newest: En yeni metadata'yi koru
    """,
)
async def merge_duplicates(
    request: MergeRequest, _admin=Depends(get_current_admin_user)
) -> MergeResponse:
    """Duplicate sorulari birlestir."""
    try:
        service = get_duplicate_service()

        result = await service.merge_duplicates(
            primary_id=request.primary_id,
            secondary_ids=request.secondary_ids,
            merge_strategy=request.merge_strategy,
        )

        return MergeResponse(
            success=result.success,
            merged_id=result.merged_id,
            merged_metadata=result.merged_metadata,
            archived_ids=result.archived_ids,
            message=result.message,
        )

    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/stats",
    response_model=DuplicateStats,
    summary="Duplicate istatistikleri",
    description="Duplicate tespit istatistiklerini getirir.",
)
async def get_duplicate_stats(_admin=Depends(get_current_admin_user)) -> DuplicateStats:
    """Duplicate istatistiklerini getir."""
    try:
        service = get_duplicate_service()
        stats = await service.get_duplicate_stats()

        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=stats["error"]
            )

        review_service = get_pending_review_service()
        return DuplicateStats(
            total_questions=stats.get("total_questions", 0),
            sample_size=stats.get("sample_size", 0),
            potential_duplicates=stats.get("potential_duplicates", 0),
            duplicate_rate=stats.get("duplicate_rate", 0.0),
            thresholds=stats.get("thresholds", {}),
            pending_review_count=review_service.get_pending_count(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stats failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/pending-review",
    response_model=list[PendingReviewItem],
    summary="Manuel inceleme bekleyenler",
    description="""
    Manuel inceleme bekleyen sorulari listeler.

    Spec REQ-5.4: Near-duplicate flagging ve manual review suggestion.
    """,
)
async def get_pending_reviews(
    limit: int = Query(default=20, ge=1, le=100, description="Maksimum sonuc sayisi"),
    status_filter: str | None = Query(
        default="pending", description="Durum filtresi: pending, reviewed, all"
    ),
    _admin=Depends(get_current_admin_user),
) -> list[PendingReviewItem]:
    """Manuel inceleme bekleyen sorulari getir (REQ-5.4)."""
    try:
        review_service = get_pending_review_service()

        # Map status filter to service ReviewStatus
        service_status = None
        if status_filter == "pending":
            service_status = ServiceReviewStatus.PENDING
        elif status_filter == "reviewed":
            # "reviewed" covers approved, rejected, merged
            service_status = None  # Will filter manually

        # Get items from service
        service_items = review_service.list_pending(
            limit=limit, status_filter=service_status
        )

        # Filter for "reviewed" if needed
        if status_filter == "reviewed":
            service_items = [
                item
                for item in service_items
                if item.status != ServiceReviewStatus.PENDING
            ]

        # Convert to API response model
        items = [
            PendingReviewItem(
                question_id=item.question_id,
                content_preview=item.content_preview,
                similarity_score=item.similarity_score,
                similar_to_id=item.similar_to_id,
                similar_to_preview=item.similar_to_preview,
                flagged_at=item.flagged_at,
                status=item.status.value,
            )
            for item in service_items
        ]

        return items[:limit]

    except Exception as e:
        logger.error(f"Pending reviews failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post(
    "/review/{question_id}",
    response_model=ReviewResponse,
    summary="Inceleme sonucu kaydet",
    description="""
    Manuel inceleme sonucunu kaydeder.

    Spec REQ-5.4: Manual review suggestion.

    Kararlar:
    - approve_add: Eklemeyi onayla (soru kalir)
    - reject_duplicate: Duplicate olarak reddet (soru silinir)
    - merge_with: Mevcut soru ile birlestir
    """,
)
async def submit_review(
    question_id: str, request: ReviewRequest, _admin=Depends(get_current_admin_user)
) -> ReviewResponse:
    """Inceleme sonucunu kaydet (REQ-5.4)."""
    try:
        review_service = get_pending_review_service()

        # Pending review'da var mi kontrol et
        if not review_service.exists(question_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inceleme bekleyen soru bulunamadi: {question_id}",
            )

        duplicate_service = get_duplicate_service()
        message = ""
        new_status: ServiceReviewStatus

        if request.decision == ReviewDecision.APPROVE_ADD:
            # Onaylandı
            new_status = ServiceReviewStatus.APPROVED
            message = "Soru onaylandi, soru bankasinda kalacak."

        elif request.decision == ReviewDecision.REJECT_DUPLICATE:
            # Reddedildi - soruyu sil
            new_status = ServiceReviewStatus.REJECTED
            try:
                if duplicate_service._collection:
                    duplicate_service._collection.delete(ids=[question_id])
                message = "Soru duplicate olarak reddedildi ve silindi."
            except Exception as e:
                logger.warning(f"Could not delete question {question_id}: {e}")
                logger.error(f"Soru silinemedi: {e}")
                message = "Soru reddedildi ama silinemedi"

        elif request.decision == ReviewDecision.MERGE_WITH:
            # Birleştir
            if not request.merge_with_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="MERGE_WITH karari icin merge_with_id gerekli",
                )

            merge_result = await duplicate_service.merge_duplicates(
                primary_id=request.merge_with_id,
                secondary_ids=[question_id],
                merge_strategy="merge_all",
            )

            if merge_result.success:
                new_status = ServiceReviewStatus.MERGED
                message = f"Soru {request.merge_with_id} ile birlestirildi."
            else:
                new_status = ServiceReviewStatus.PENDING
                message = f"Birlestirme basarisiz: {merge_result.message}"
        else:
            new_status = ServiceReviewStatus.PENDING
            message = "Bilinmeyen karar tipi"

        # Update status via service
        review_service.update_status(
            question_id=question_id,
            status=new_status,
            reviewer_notes=request.reviewer_notes,
        )

        return ReviewResponse(
            success=True,
            question_id=question_id,
            decision=request.decision.value,
            message=message,
            processed_at=datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/health", summary="Duplicate servis saglik kontrolu")
async def health_check() -> dict:
    """Duplicate servisinin saglik durumunu kontrol et."""
    try:
        duplicate_service = get_duplicate_service()
        review_service = get_pending_review_service()
        initialized = await duplicate_service.initialize()

        return {
            "status": "healthy" if initialized else "degraded",
            "service": "duplicate_detection",
            "chromadb_available": initialized,
            "pending_review_count": review_service.get_pending_count(),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "duplicate_detection",
            "error": "Internal error",
            "timestamp": datetime.now().isoformat(),
        }
