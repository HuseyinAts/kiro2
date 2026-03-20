"""
Task 100: Video Analytics API Routes

REST API endpoints for video watch tracking, notes, and bookmarks
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import AuthenticatedUser, get_current_user
from services.video_analytics_service import VideoAnalyticsService

router = APIRouter(prefix="/api/v1/video-analytics", tags=["video-analytics"])


# ============================================================
# Request/Response Models
# ============================================================


class StartSessionRequest(BaseModel):
    video_id: str = Field(..., description="Video ID")
    video_source: str = Field(..., description="Video source (youtube, eba, khan)")
    video_duration: int = Field(..., description="Video duration in seconds", gt=0)


class UpdateProgressRequest(BaseModel):
    current_position: int = Field(
        ..., description="Current video position in seconds", ge=0
    )
    playback_speed: float = Field(1.0, description="Playback speed", gt=0)


class SeekRequest(BaseModel):
    from_position: int = Field(..., ge=0)
    to_position: int = Field(..., ge=0)


class CreateNoteRequest(BaseModel):
    video_id: str
    video_source: str
    content: str = Field(..., min_length=1)
    timestamp: int = Field(..., ge=0)
    session_id: UUID | None = None
    is_important: bool = False
    tags: list[str] = []
    video_caption: str | None = None


class UpdateNoteRequest(BaseModel):
    content: str | None = None
    is_important: bool | None = None
    tags: list[str] | None = None


class CreateBookmarkRequest(BaseModel):
    video_id: str
    video_source: str
    timestamp: int = Field(..., ge=0)
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    session_id: UUID | None = None
    bookmark_type: str = "manual"
    is_public: bool = False


class UpdateBookmarkRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    is_public: bool | None = None


# ============================================================
# Task 100.1: Watch Session Endpoints
# ============================================================


@router.post("/sessions/start", response_model=dict)
async def start_watch_session(
    request: StartSessionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new watch session

    Creates a new session for tracking watch progress
    """
    user_id = UUID(current_user.user_id)
    service = VideoAnalyticsService(db)

    session = await service.start_watch_session(
        user_id=user_id,
        video_id=request.video_id,
        video_source=request.video_source,
        video_duration=request.video_duration,
    )

    return {
        "session_id": str(session.id),
        "video_id": session.video_id,
        "started_at": session.started_at.isoformat(),
    }


@router.post("/sessions/{session_id}/progress", response_model=dict)
async def update_watch_progress(
    session_id: UUID, request: UpdateProgressRequest, db: AsyncSession = Depends(get_db)
):
    """
    Update watch progress

    Called periodically (e.g., every 10 seconds) to track progress
    """
    service = VideoAnalyticsService(db)

    try:
        session = await service.update_watch_progress(
            session_id=session_id,
            current_position=request.current_position,
            playback_speed=request.playback_speed,
        )

        return {
            "session_id": str(session.id),
            "completion_percentage": session.completion_percentage,
            "is_completed": session.is_completed,
            "last_position": session.last_position,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sessions/{session_id}/pause")
async def record_pause(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Record a pause event"""
    service = VideoAnalyticsService(db)
    await service.record_pause(session_id)
    return {"status": "ok"}


@router.post("/sessions/{session_id}/seek")
async def record_seek(
    session_id: UUID, request: SeekRequest, db: AsyncSession = Depends(get_db)
):
    """Record a seek event"""
    service = VideoAnalyticsService(db)
    await service.record_seek(
        session_id=session_id,
        from_position=request.from_position,
        to_position=request.to_position,
    )
    return {"status": "ok"}


@router.post("/sessions/{session_id}/end", response_model=dict)
async def end_watch_session(
    session_id: UUID,
    final_position: int = Query(..., ge=0),
    db: AsyncSession = Depends(get_db),
):
    """End a watch session"""
    service = VideoAnalyticsService(db)

    try:
        session = await service.end_watch_session(session_id, final_position)

        return {
            "session_id": str(session.id),
            "completion_percentage": session.completion_percentage,
            "is_completed": session.is_completed,
            "watch_duration": session.watch_duration,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/videos/{video_id}/engagement")
async def get_video_engagement(
    video_id: str, video_source: str = Query(...), db: AsyncSession = Depends(get_db)
):
    """
    Get engagement metrics for a video

    Returns average completion, drop-off points, etc.
    """
    service = VideoAnalyticsService(db)
    metrics = await service.get_video_engagement_metrics(video_id, video_source)
    return metrics


# ============================================================
# Task 100.2: Milestone Endpoints
# ============================================================


@router.get("/milestones", response_model=list[dict])
async def get_user_milestones(
    video_id: str | None = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's completion milestones

    Returns all milestones achieved by the user
    """
    user_id = UUID(current_user.user_id)
    service = VideoAnalyticsService(db)
    milestones = await service.get_user_milestones(user_id, video_id)

    return [
        {
            "id": str(m.id),
            "video_id": m.video_id,
            "video_source": m.video_source,
            "milestone_percentage": m.milestone_percentage,
            "achieved_at": m.achieved_at.isoformat(),
            "badge_awarded": m.badge_awarded,
        }
        for m in milestones
    ]


# ============================================================
# Task 100.3: Notes Endpoints
# ============================================================


@router.post("/notes", response_model=dict)
async def create_note(
    request: CreateNoteRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a timestamped note

    Create a note at a specific video timestamp
    """
    user_id = UUID(current_user.user_id)
    service = VideoAnalyticsService(db)

    note = await service.create_note(
        user_id=user_id,
        video_id=request.video_id,
        video_source=request.video_source,
        content=request.content,
        timestamp=request.timestamp,
        session_id=request.session_id,
        is_important=request.is_important,
        tags=request.tags,
        video_caption=request.video_caption,
    )

    return {
        "id": str(note.id),
        "video_id": note.video_id,
        "timestamp": note.timestamp,
        "content": note.content,
        "created_at": note.created_at.isoformat(),
    }


@router.put("/notes/{note_id}", response_model=dict)
async def update_note(
    note_id: UUID, request: UpdateNoteRequest, db: AsyncSession = Depends(get_db)
):
    """Update a note"""
    service = VideoAnalyticsService(db)

    try:
        note = await service.update_note(
            note_id=note_id,
            content=request.content,
            is_important=request.is_important,
            tags=request.tags,
        )

        return {
            "id": str(note.id),
            "content": note.content,
            "is_important": note.is_important,
            "tags": note.tags,
            "updated_at": note.updated_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/notes/{note_id}")
async def delete_note(note_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a note"""
    service = VideoAnalyticsService(db)
    await service.delete_note(note_id)
    return {"status": "deleted"}


@router.get("/notes", response_model=list[dict])
async def get_video_notes(
    video_id: str = Query(...),
    video_source: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all notes for a video

    Returns notes ordered by timestamp
    """
    user_id = UUID(current_user.user_id)
    service = VideoAnalyticsService(db)
    notes = await service.get_video_notes(user_id, video_id, video_source)

    return [
        {
            "id": str(n.id),
            "video_id": n.video_id,
            "timestamp": n.timestamp,
            "content": n.content,
            "is_important": n.is_important,
            "tags": n.tags,
            "video_caption": n.video_caption,
            "created_at": n.created_at.isoformat(),
            "updated_at": n.updated_at.isoformat(),
        }
        for n in notes
    ]


@router.get("/notes/search", response_model=list[dict])
async def search_notes(
    query: str = Query(..., min_length=1),
    video_id: str | None = Query(None),
    tags: list[str] | None = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search user's notes

    Full-text search in note content
    """
    user_id = UUID(current_user.user_id)
    service = VideoAnalyticsService(db)
    notes = await service.search_notes(user_id, query, video_id, tags)

    return [
        {
            "id": str(n.id),
            "video_id": n.video_id,
            "video_source": n.video_source,
            "timestamp": n.timestamp,
            "content": n.content,
            "is_important": n.is_important,
            "tags": n.tags,
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ]


# ============================================================
# Task 100.4: Bookmark Endpoints
# ============================================================


@router.post("/bookmarks", response_model=dict)
async def create_bookmark(
    request: CreateBookmarkRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a bookmark

    Create a bookmark at a specific video timestamp
    """
    user_id = UUID(current_user.user_id)
    service = VideoAnalyticsService(db)

    bookmark = await service.create_bookmark(
        user_id=user_id,
        video_id=request.video_id,
        video_source=request.video_source,
        timestamp=request.timestamp,
        title=request.title,
        description=request.description,
        session_id=request.session_id,
        bookmark_type=request.bookmark_type,
        is_public=request.is_public,
    )

    return {
        "id": str(bookmark.id),
        "video_id": bookmark.video_id,
        "timestamp": bookmark.timestamp,
        "title": bookmark.title,
        "created_at": bookmark.created_at.isoformat(),
    }


@router.put("/bookmarks/{bookmark_id}", response_model=dict)
async def update_bookmark(
    bookmark_id: UUID,
    request: UpdateBookmarkRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a bookmark"""
    service = VideoAnalyticsService(db)

    try:
        bookmark = await service.update_bookmark(
            bookmark_id=bookmark_id,
            title=request.title,
            description=request.description,
            is_public=request.is_public,
        )

        return {
            "id": str(bookmark.id),
            "title": bookmark.title,
            "description": bookmark.description,
            "is_public": bookmark.is_public,
            "updated_at": bookmark.updated_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a bookmark"""
    service = VideoAnalyticsService(db)
    await service.delete_bookmark(bookmark_id)
    return {"status": "deleted"}


@router.get("/bookmarks", response_model=list[dict])
async def get_video_bookmarks(
    video_id: str = Query(...),
    video_source: str = Query(...),
    include_public: bool = Query(
        False, description="Include public bookmarks from other users"
    ),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get bookmarks for a video

    Returns bookmarks ordered by timestamp
    """
    user_id = UUID(current_user.user_id)
    service = VideoAnalyticsService(db)
    bookmarks = await service.get_video_bookmarks(
        user_id, video_id, video_source, include_public
    )

    return [
        {
            "id": str(b.id),
            "user_id": str(b.user_id),
            "video_id": b.video_id,
            "timestamp": b.timestamp,
            "title": b.title,
            "description": b.description,
            "bookmark_type": b.bookmark_type,
            "is_public": b.is_public,
            "share_count": b.share_count,
            "created_at": b.created_at.isoformat(),
        }
        for b in bookmarks
    ]


@router.post("/bookmarks/{bookmark_id}/share")
async def share_bookmark(bookmark_id: UUID, db: AsyncSession = Depends(get_db)):
    """Increment share count for a bookmark"""
    service = VideoAnalyticsService(db)
    await service.increment_bookmark_share(bookmark_id)
    return {"status": "shared"}


# ============================================================
# Analytics Summary Endpoints
# ============================================================


@router.get("/summary/daily", response_model=dict)
async def get_daily_summary(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily analytics summary"""
    user_id = UUID(current_user.user_id)
    service = VideoAnalyticsService(db)

    try:
        target_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    summary = await service.generate_daily_summary(user_id, target_date)

    return {
        "user_id": str(summary.user_id),
        "period_type": summary.period_type,
        "period_start": summary.period_start.isoformat(),
        "period_end": summary.period_end.isoformat(),
        "total_videos_watched": summary.total_videos_watched,
        "total_watch_time": summary.total_watch_time,
        "total_videos_completed": summary.total_videos_completed,
        "average_completion_rate": summary.average_completion_rate,
        "total_notes": summary.total_notes,
        "total_bookmarks": summary.total_bookmarks,
        "average_playback_speed": summary.average_playback_speed,
        "source_breakdown": summary.source_breakdown,
        "subject_breakdown": summary.subject_breakdown,
    }
