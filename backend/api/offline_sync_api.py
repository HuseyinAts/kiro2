"""
Offline Sync API — F10 PWA Offline Mode

Endpoints for PWA offline mode: download study packages for offline use and
upload results that were recorded while the device had no connectivity.

Endpoints:
  GET  /api/v1/offline/sync-package   — Download offline study package
  POST /api/v1/offline/sync-results   — Upload offline study results
  GET  /api/v1/offline/sync-status    — Check last sync time and pending items
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/offline", tags=["Offline Sync"])
logger = get_logger("offline_sync_api")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class OfflineQuestion(BaseModel):
    """Minimal question payload for offline study."""

    id: str
    text: str
    options: dict
    correct_answer: str
    subject: str
    topic: str
    difficulty: str


class FSRSDueCard(BaseModel):
    """Minimal FSRS card payload for offline review."""

    card_id: str
    question_id: str
    due_at: str
    interval: int
    ease_factor: float


class SyncPackageResponse(BaseModel):
    """Response payload for GET /sync-package."""

    package_id: str
    created_at: str
    questions: list[OfflineQuestion]
    fsrs_due_cards: list[FSRSDueCard]
    total_questions: int
    estimated_study_time_minutes: int


class OfflineResult(BaseModel):
    """A single answer recorded offline."""

    question_id: str = Field(..., description="UUID of the answered question")
    selected_answer: str = Field(..., min_length=1, max_length=1, description="A-E")
    is_correct: bool
    time_seconds: float = Field(default=0.0, ge=0.0)
    answered_at: str = Field(..., description="ISO-8601 timestamp")


class SyncResultsRequest(BaseModel):
    """Request body for POST /sync-results."""

    package_id: str = Field(..., description="package_id from the sync package")
    results: list[OfflineResult] = Field(..., min_length=1, max_length=500)
    completed_at: str = Field(..., description="ISO-8601 timestamp when study ended")


class SyncResultsResponse(BaseModel):
    """Response payload for POST /sync-results."""

    synced_count: int
    failed_count: int
    next_sync_recommended_at: str


class SyncStatusResponse(BaseModel):
    """Response payload for GET /sync-status."""

    last_sync_at: Optional[str]
    pending_results_count: int
    offline_package_version: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/sync-package",
    response_model=SyncPackageResponse,
    summary="Çevrimdışı çalışma paketi indir",
    description=(
        "Öğrencinin tekrar etmesi gereken FSRS kartlarını ve zayıf konulardan "
        "rastgele soruları içeren çevrimdışı çalışma paketi döner."
    ),
)
async def get_sync_package(
    subject: Optional[str] = Query(
        default=None, description="Ders filtresi (ör. MATEMATIK)"
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maksimum soru sayısı"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SyncPackageResponse:
    """Download an offline study package for the authenticated student.

    Combines FSRS due cards and random questions from weak topics into a
    single JSON payload suitable for storing in the browser's IndexedDB.

    Args:
        subject: Optional subject filter (uppercase, e.g. "MATEMATIK").
        limit: Maximum number of questions to include.
        current_user: The authenticated student.

    Returns:
        A sync package with questions and FSRS due cards.

    Raises:
        HTTPException: 500 on database error.
    """
    from services.offline_sync_service import build_sync_package

    try:
        async with get_db_session_context() as db:
            package = await build_sync_package(
                db=db,
                student_id=current_user.id,
                subject=subject.upper() if subject else None,
                limit=limit,
            )

        logger.info(
            "Offline sync package created",
            extra_data={
                "user": current_user.id,
                "question_count": package["total_questions"],
                "subject": subject,
            },
        )
        return SyncPackageResponse(**package)

    except Exception as e:
        logger.error(
            f"Sync package oluşturma hatası: {e}",
            extra_data={"user": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Çevrimdışı çalışma paketi oluşturulurken hata oluştu",
        )


@router.post(
    "/sync-results",
    response_model=SyncResultsResponse,
    status_code=status.HTTP_200_OK,
    summary="Çevrimdışı çalışma sonuçlarını yükle",
    description=(
        "Cihaz çevrimdışıyken kaydedilen cevapları sunucuya gönderir. "
        "Her cevap için FSRS zamanlaması güncellenir ve "
        "student_answers'a kayıt eklenir."
    ),
)
async def sync_results(
    request: SyncResultsRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SyncResultsResponse:
    """Upload offline study results to the server.

    Processes each recorded answer: updates FSRS card scheduling and inserts
    a record into student_answers. Results that fail processing (e.g. unknown
    question ID) are counted in failed_count rather than aborting the whole batch.

    Args:
        request: Package ID, list of offline results, and completion timestamp.
        current_user: The authenticated student.

    Returns:
        Counts of synced / failed records and the recommended next sync time.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.offline_sync_service import process_sync_results

    try:
        async with get_db_session_context() as db:
            outcome = await process_sync_results(
                db=db,
                student_id=current_user.id,
                package_id=request.package_id,
                results=[r.model_dump() for r in request.results],
                completed_at=request.completed_at,
            )

        logger.info(
            "Offline results synced",
            extra_data={
                "user": current_user.id,
                "synced": outcome["synced_count"],
                "failed": outcome["failed_count"],
            },
        )
        return SyncResultsResponse(**outcome)

    except Exception as e:
        logger.error(
            f"Sync results işleme hatası: {e}",
            extra_data={"user": current_user.id, "package_id": request.package_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Çevrimdışı sonuçlar işlenirken hata oluştu",
        )


@router.get(
    "/sync-status",
    response_model=SyncStatusResponse,
    summary="Senkronizasyon durumunu kontrol et",
    description="Son senkronizasyon zamanını ve bekleyen öğe sayısını döner.",
)
async def get_sync_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SyncStatusResponse:
    """Return the student's current offline sync status.

    Reports when the last successful sync occurred and how many FSRS cards
    are currently due (an approximation of pending offline work).

    Args:
        current_user: The authenticated student.

    Returns:
        Sync status including last sync time and pending count.

    Raises:
        HTTPException: 500 on database error.
    """
    from services.offline_sync_service import get_sync_status

    try:
        async with get_db_session_context() as db:
            status_data = await get_sync_status(db=db, student_id=current_user.id)

        return SyncStatusResponse(**status_data)

    except Exception as e:
        logger.error(
            f"Sync status sorgulama hatası: {e}",
            extra_data={"user": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Senkronizasyon durumu alınırken hata oluştu",
        )
