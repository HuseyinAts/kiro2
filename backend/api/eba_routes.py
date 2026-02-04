"""
Task 97: EBA TV API Routes
REST endpoints for EBA TV integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, UUID4
from datetime import datetime

# PHASE 1 FIX: Corrected import paths (removed 'backend.' prefix)
from core.database import get_db
from models.database import User
from services.eba_tv_client import (
    EBASubject,
    EBAGradeLevel,
    EBACatalogFilter,
    get_eba_client,
)
from services.eba_catalog_sync import EBACatalogSyncService
from services.eba_watch_tracking import EBAWatchTrackingService, WatchAnalytics
from core.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/eba", tags=["EBA TV Integration"])


# ============================================
# Request/Response Models
# ============================================


class EBAVideoResponse(BaseModel):
    """Video response model"""

    video_id: str
    title: str
    description: Optional[str]
    duration_seconds: int
    thumbnail_url: Optional[str]
    video_url: str
    subject: str
    grade_level: str
    topic: Optional[str]
    keywords: List[str]
    quality: str
    view_count: int


class WatchSessionStartRequest(BaseModel):
    """Start watch session request"""

    eba_video_id: str


class WatchProgressRequest(BaseModel):
    """Update watch progress request"""

    session_id: UUID4
    current_time: int  # seconds
    video_duration: int


class WatchHistoryResponse(BaseModel):
    """Watch history item"""

    session_id: str
    video_id: str
    video_title: str
    video_duration: int
    last_position: int
    watch_percentage: float
    completed: bool
    last_watched: Optional[str]
    thumbnail_url: Optional[str]


class SyncStatsResponse(BaseModel):
    """Catalog sync statistics"""

    total_fetched: int
    new_videos: int
    updated_videos: int
    errors: int


# ============================================
# Task 97.2: Video Catalog Endpoints
# ============================================


@router.get("/videos", response_model=List[EBAVideoResponse])
async def get_eba_videos(
    subject: Optional[EBASubject] = None,
    grade_level: Optional[EBAGradeLevel] = None,
    topic: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 97.2: Get EBA video catalog

    Filters:
    - subject: matematik, fizik, kimya, etc.
    - grade_level: ortaokul_8, lise_11, etc.
    - topic: Konu adı
    - search: Arama terimi (başlık/açıklama)

    Returns paginated video list
    """
    from sqlalchemy import select, and_, or_
    from models.eba_video import EBAVideo

    # Build query
    filters = []

    if subject:
        filters.append(EBAVideo.subject == subject.value)

    if grade_level:
        filters.append(EBAVideo.grade_level == grade_level.value)

    if topic:
        filters.append(EBAVideo.topic.ilike(f"%{topic}%"))

    if search:
        filters.append(
            or_(
                EBAVideo.title.ilike(f"%{search}%"),
                EBAVideo.description.ilike(f"%{search}%"),
            )
        )

    stmt = select(EBAVideo)

    if filters:
        stmt = stmt.where(and_(*filters))

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    # Order by view count (most popular first)
    stmt = stmt.order_by(EBAVideo.view_count.desc())

    result = await db.execute(stmt)
    videos = result.scalars().all()

    return [
        EBAVideoResponse(
            video_id=v.eba_video_id,
            title=v.title,
            description=v.description,
            duration_seconds=v.duration_seconds,
            thumbnail_url=v.thumbnail_url,
            video_url=v.video_url,
            subject=v.subject,
            grade_level=v.grade_level,
            topic=v.topic,
            keywords=v.keywords or [],
            quality=v.quality,
            view_count=v.view_count,
        )
        for v in videos
    ]


@router.get("/videos/{eba_video_id}", response_model=EBAVideoResponse)
async def get_eba_video_details(eba_video_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get specific EBA video details
    """
    from sqlalchemy import select
    from models.eba_video import EBAVideo

    stmt = select(EBAVideo).where(EBAVideo.eba_video_id == eba_video_id)
    result = await db.execute(stmt)
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return EBAVideoResponse(
        video_id=video.eba_video_id,
        title=video.title,
        description=video.description,
        duration_seconds=video.duration_seconds,
        thumbnail_url=video.thumbnail_url,
        video_url=video.video_url,
        subject=video.subject,
        grade_level=video.grade_level,
        topic=video.topic,
        keywords=video.keywords or [],
        quality=video.quality,
        view_count=video.view_count,
    )


# ============================================
# Task 97.3: Subject Filtering Endpoints
# ============================================


@router.get("/taxonomy/subjects", response_model=Dict[str, List[str]])
async def get_subjects_taxonomy(
    use_mock: bool = Query(False, description="Use mock EBA client")
):
    """
    Task 97.3: Get subject taxonomy

    Returns subject -> topics hierarchy
    Example: { "matematik": ["Sayılar", "Geometri", ...], ... }
    """
    eba_client = get_eba_client(use_mock=use_mock)

    try:
        taxonomy = await eba_client.get_subjects_taxonomy()
        return taxonomy

    except Exception as e:
        logger.error(f"Failed to fetch taxonomy: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch taxonomy")

    finally:
        await eba_client.close()


@router.get("/curriculum/{grade_level}/{subject}")
async def get_curriculum_alignment(
    grade_level: EBAGradeLevel, subject: EBASubject, use_mock: bool = Query(False)
):
    """
    Task 97.3: Get curriculum alignment

    Returns kazanım codes and video mappings
    """
    eba_client = get_eba_client(use_mock=use_mock)

    try:
        alignment = await eba_client.get_curriculum_alignment(grade_level, subject)
        return alignment

    except Exception as e:
        logger.error(f"Failed to fetch curriculum alignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alignment")

    finally:
        await eba_client.close()


@router.get("/videos/by-kazanim/{kazanim_code}", response_model=List[EBAVideoResponse])
async def get_videos_by_kazanim(kazanim_code: str, db: AsyncSession = Depends(get_db)):
    """
    Task 97.3: Get videos by curriculum kazanım code

    Example: kazanim_code = "8.1.2.1"
    """
    from sqlalchemy import select
    from models.eba_video import EBAVideo

    # Search for videos containing this kazanim code
    stmt = select(EBAVideo).where(EBAVideo.kazanim_codes.contains([kazanim_code]))

    result = await db.execute(stmt)
    videos = result.scalars().all()

    return [
        EBAVideoResponse(
            video_id=v.eba_video_id,
            title=v.title,
            description=v.description,
            duration_seconds=v.duration_seconds,
            thumbnail_url=v.thumbnail_url,
            video_url=v.video_url,
            subject=v.subject,
            grade_level=v.grade_level,
            topic=v.topic,
            keywords=v.keywords or [],
            quality=v.quality,
            view_count=v.view_count,
        )
        for v in videos
    ]


# ============================================
# Task 97.4: Watch Tracking Endpoints
# ============================================


@router.post("/watch/start")
async def start_watch_session(
    request: WatchSessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 97.4: Start watching a video

    Returns session_id and resume_position (if previously watched)
    """
    tracking_service = EBAWatchTrackingService(db)

    try:
        session_id = await tracking_service.start_watch_session(
            user_id=current_user.id, eba_video_id=request.eba_video_id
        )

        # Get resume position
        resume_position = await tracking_service.get_resume_position(
            user_id=current_user.id, eba_video_id=request.eba_video_id
        )

        return {
            "session_id": str(session_id),
            "resume_position": resume_position or 0,
            "message": "Kaldığın yerden devam et"
            if resume_position
            else "Yeni izleme başladı",
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start watch session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start session")


@router.post("/watch/progress")
async def update_watch_progress(
    request: WatchProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 97.4: Update watch progress

    Called periodically during video playback (every 10-30 seconds)
    """
    tracking_service = EBAWatchTrackingService(db)

    try:
        result = await tracking_service.update_watch_progress(
            session_id=request.session_id,
            current_time=request.current_time,
            video_duration=request.video_duration,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to update progress")


@router.post("/watch/end/{session_id}")
async def end_watch_session(
    session_id: UUID4,
    final_time: int = Query(..., description="Final position in seconds"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 97.4: End watch session

    Called when user closes video or navigates away
    """
    tracking_service = EBAWatchTrackingService(db)

    try:
        result = await tracking_service.end_watch_session(
            session_id=session_id, final_time=final_time
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(status_code=500, detail="Failed to end session")


@router.get("/watch/history", response_model=List[WatchHistoryResponse])
async def get_watch_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 97.4: Get user's watch history

    Returns recently watched videos
    """
    tracking_service = EBAWatchTrackingService(db)

    try:
        history = await tracking_service.get_user_watch_history(
            user_id=current_user.id, limit=limit
        )

        return [WatchHistoryResponse(**item) for item in history]

    except Exception as e:
        logger.error(f"Failed to fetch watch history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@router.get("/watch/analytics", response_model=WatchAnalytics)
async def get_user_analytics(
    since_days: Optional[int] = Query(
        None, description="Last X days (null = all time)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 97.4: Get user watch analytics

    - Total watch time
    - Completed videos count
    - Completion rate
    - Average watch percentage
    """
    tracking_service = EBAWatchTrackingService(db)

    try:
        analytics = await tracking_service.get_user_analytics(
            user_id=current_user.id, since_days=since_days
        )

        return analytics

    except Exception as e:
        logger.error(f"Failed to fetch analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


@router.get("/videos/{eba_video_id}/analytics")
async def get_video_analytics(eba_video_id: str, db: AsyncSession = Depends(get_db)):
    """
    Task 97.4: Get video analytics (all users)

    - Total viewers
    - Completion rate
    - Drop-off analysis
    """
    tracking_service = EBAWatchTrackingService(db)

    try:
        analytics = await tracking_service.get_video_analytics(eba_video_id)
        return analytics

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch video analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


@router.get("/popular", response_model=List[EBAVideoResponse])
async def get_popular_videos(
    subject: Optional[EBASubject] = None,
    grade_level: Optional[EBAGradeLevel] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Task 97.4: Get popular videos (most watched)
    """
    tracking_service = EBAWatchTrackingService(db)

    try:
        popular = await tracking_service.get_popular_videos(
            subject=subject.value if subject else None,
            grade_level=grade_level.value if grade_level else None,
            limit=limit,
        )

        return [
            EBAVideoResponse(
                video_id=v["video_id"],
                title=v["title"],
                description=None,
                duration_seconds=v["duration"],
                thumbnail_url=v["thumbnail_url"],
                video_url="",  # Not included in popular response
                subject=v["subject"],
                grade_level=v["grade_level"],
                topic=None,
                keywords=[],
                quality="720p",
                view_count=v["watch_count"],
            )
            for v in popular
        ]

    except Exception as e:
        logger.error(f"Failed to fetch popular videos: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch popular videos")


# ============================================
# Admin Endpoints (Catalog Sync)
# ============================================


@router.post("/admin/sync/full", response_model=SyncStatsResponse)
async def trigger_full_catalog_sync(
    subjects: Optional[List[EBASubject]] = None,
    grade_levels: Optional[List[EBAGradeLevel]] = None,
    use_mock: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin: Trigger full EBA catalog sync

    WARNING: This can take several minutes!
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    sync_service = EBACatalogSyncService(db, use_mock=use_mock)

    try:
        logger.info(f"[ADMIN] Starting full catalog sync (user: {current_user.email})")

        stats = await sync_service.sync_full_catalog(
            subjects=subjects, grade_levels=grade_levels
        )

        return SyncStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Catalog sync failed: {e}")
        raise HTTPException(status_code=500, detail="Sync failed")

    finally:
        await sync_service.close()


@router.post("/admin/sync/incremental", response_model=SyncStatsResponse)
async def trigger_incremental_sync(
    since_hours: int = Query(24, ge=1, le=168),
    use_mock: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin: Trigger incremental catalog sync

    Syncs only recent videos (last X hours)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    sync_service = EBACatalogSyncService(db, use_mock=use_mock)

    try:
        logger.info(f"[ADMIN] Starting incremental sync (since_hours={since_hours})")

        stats = await sync_service.sync_incremental(since_hours=since_hours)

        return SyncStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Incremental sync failed: {e}")
        raise HTTPException(status_code=500, detail="Sync failed")

    finally:
        await sync_service.close()


@router.get("/admin/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Admin: Get catalog sync status
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    sync_service = EBACatalogSyncService(db)

    try:
        status = await sync_service.get_sync_status()
        return status

    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")

    finally:
        await sync_service.close()


logger.info("[OK] [EBA TV] EBA TV entegrasyon API'si yüklendi (Task 97)")
