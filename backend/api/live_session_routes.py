"""
Task 108: Live Q&A Sessions API Routes

API endpoints for video conferences, screen sharing, whiteboard, and recording.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import AuthenticatedUser, get_current_user
from models.live_session import (
    PlatformType,
    ScreenShareType,
    SessionStatus,
    SessionType,
    WhiteboardToolType,
)
from services.video_conference_service import VideoConferenceService
from services.whiteboard_service import WhiteboardService

router = APIRouter(prefix="/api/v1/live-sessions", tags=["live-sessions"])


# ============================================================
# Session Access Helpers
# ============================================================


async def _verify_host_only(
    session_id: UUID,
    current_user: AuthenticatedUser,
    db: AsyncSession,
) -> None:
    """Verify current user is the session host. Raises 403/404."""
    result = await db.execute(
        text("SELECT host_id FROM live_sessions WHERE id = :sid"),
        {"sid": str(session_id)},
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(row.host_id) != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Only session host can perform this action"
        )


async def _verify_session_participant(
    session_id: UUID,
    current_user: AuthenticatedUser,
    db: AsyncSession,
) -> None:
    """Verify current user is host or participant. Raises 403/404."""
    result = await db.execute(
        text("SELECT host_id FROM live_sessions WHERE id = :sid"),
        {"sid": str(session_id)},
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(row.host_id) == current_user.user_id:
        return  # Host always has access
    part = await db.execute(
        text(
            "SELECT 1 FROM live_session_participants "
            "WHERE session_id = :sid AND user_id = :uid"
        ),
        {"sid": str(session_id), "uid": current_user.user_id},
    )
    if not part.first():
        raise HTTPException(status_code=403, detail="Not a session participant")


# ============================================================
# Request/Response Models
# ============================================================


class SessionCreateRequest(BaseModel):
    title: str
    description: str
    scheduled_start: datetime
    scheduled_end: datetime
    session_type: SessionType
    platform: PlatformType = PlatformType.ZOOM
    subject: str | None = None
    topics: list[str] | None = None
    max_participants: int = 50
    auto_record: bool = False
    require_password: bool = True
    teacher_id: UUID | None = None


class ScreenShareRequest(BaseModel):
    share_type: ScreenShareType
    window_title: str | None = None
    application_name: str | None = None


class ChatMessageRequest(BaseModel):
    message: str
    recipient_id: UUID | None = None


class WhiteboardCreateRequest(BaseModel):
    name: str = "Whiteboard"
    background_color: str = "#FFFFFF"
    grid_enabled: bool = True


class StrokeRequest(BaseModel):
    tool_type: WhiteboardToolType
    page_number: int
    path_data: list[dict[str, float]] | None = None
    shape_type: str | None = None
    shape_data: dict[str, Any] | None = None
    text_content: str | None = None
    color: str = "#000000"
    width: float = 2.0
    opacity: float = 1.0
    font_size: int = 16
    font_family: str = "Arial"


class EquationRequest(BaseModel):
    page_number: int
    x: float
    y: float
    latex_code: str
    font_size: int = 20
    color: str = "#000000"


# ============================================================
# Task 108.1: Video Conference & Session Management
# ============================================================


@router.post("")
async def create_session(
    request: SessionCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new live session with video conference integration"""
    host_id = UUID(current_user.user_id)
    service = VideoConferenceService(db)

    session = await service.create_session(
        host_id=host_id,
        title=request.title,
        description=request.description,
        scheduled_start=request.scheduled_start,
        scheduled_end=request.scheduled_end,
        session_type=request.session_type,
        platform=request.platform,
        subject=request.subject,
        topics=request.topics,
        max_participants=request.max_participants,
        auto_record=request.auto_record,
        require_password=request.require_password,
        teacher_id=request.teacher_id,
    )

    return {
        "id": str(session.id),
        "meeting_url": session.meeting_url,
        "meeting_id": session.meeting_id,
        "meeting_password": session.meeting_password,
        "platform": session.platform,
        "scheduled_start": session.scheduled_start.isoformat(),
        "scheduled_end": session.scheduled_end.isoformat(),
    }


@router.get("/{session_id}")
async def get_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get session details"""
    await _verify_session_participant(session_id, current_user, db)
    service = VideoConferenceService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": str(session.id),
        "title": session.title,
        "description": session.description,
        "status": session.status,
        "platform": session.platform,
        "meeting_url": session.meeting_url,
        "meeting_password": session.meeting_password,
        "scheduled_start": session.scheduled_start.isoformat(),
        "scheduled_end": session.scheduled_end.isoformat(),
        "current_participants": session.current_participants,
        "max_participants": session.max_participants,
        "is_recorded": session.is_recorded,
    }


@router.post("/{session_id}/start")
async def start_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start session (host only)"""
    await _verify_host_only(session_id, current_user, db)
    service = VideoConferenceService(db)
    session = await service.start_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session started", "status": session.status}


@router.post("/{session_id}/end")
async def end_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """End session (host only)"""
    await _verify_host_only(session_id, current_user, db)
    service = VideoConferenceService(db)
    session = await service.end_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session ended", "status": session.status}


@router.post("/{session_id}/join")
async def join_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join session as participant"""
    user_id = UUID(current_user.user_id)
    service = VideoConferenceService(db)
    participant = await service.join_session(session_id, user_id)

    return {"message": "Joined session", "participant_id": str(participant.id)}


@router.post("/{session_id}/leave")
async def leave_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave session"""
    user_id = UUID(current_user.user_id)
    service = VideoConferenceService(db)
    await service.leave_session(session_id, user_id)

    return {"message": "Left session"}


# ============================================================
# Task 108.2: Screen Sharing
# ============================================================


@router.post("/{session_id}/screen-share/start")
async def start_screen_share(
    session_id: UUID,
    request: ScreenShareRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start screen sharing (participants)"""
    await _verify_session_participant(session_id, current_user, db)
    user_id = UUID(current_user.user_id)
    service = VideoConferenceService(db)

    screen_share = await service.start_screen_share(
        session_id=session_id,
        user_id=user_id,
        share_type=request.share_type,
        window_title=request.window_title,
        application_name=request.application_name,
    )

    return {"message": "Screen share started", "screen_share_id": str(screen_share.id)}


@router.post("/screen-share/{screen_share_id}/stop")
async def stop_screen_share(
    screen_share_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop screen sharing"""
    service = VideoConferenceService(db)
    screen_share = await service.end_screen_share(screen_share_id)

    if not screen_share:
        raise HTTPException(status_code=404, detail="Screen share not found")

    return {"message": "Screen share stopped"}


# ============================================================
# Task 108.3: Whiteboard
# ============================================================


@router.post("/{session_id}/whiteboard")
async def create_whiteboard(
    session_id: UUID,
    request: WhiteboardCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create whiteboard for session (host only)"""
    await _verify_host_only(session_id, current_user, db)
    service = WhiteboardService(db)

    whiteboard = await service.create_whiteboard(
        session_id=session_id,
        name=request.name,
        background_color=request.background_color,
        grid_enabled=request.grid_enabled,
    )

    return {
        "id": str(whiteboard.id),
        "name": whiteboard.name,
        "page_count": whiteboard.page_count,
    }


@router.get("/whiteboard/{whiteboard_id}")
async def get_whiteboard(
    whiteboard_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get whiteboard details"""
    service = WhiteboardService(db)
    whiteboard = await service.get_whiteboard(whiteboard_id)

    if not whiteboard:
        raise HTTPException(status_code=404, detail="Whiteboard not found")

    return {
        "id": str(whiteboard.id),
        "name": whiteboard.name,
        "page_count": whiteboard.page_count,
        "current_page": whiteboard.current_page,
        "background_color": whiteboard.background_color,
        "grid_enabled": whiteboard.grid_enabled,
    }


@router.post("/whiteboard/{whiteboard_id}/stroke")
async def add_stroke(
    whiteboard_id: UUID,
    request: StrokeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add drawing stroke to whiteboard"""
    user_id = UUID(current_user.user_id)
    service = WhiteboardService(db)

    stroke = await service.add_stroke(
        whiteboard_id=whiteboard_id,
        user_id=user_id,
        tool_type=request.tool_type,
        page_number=request.page_number,
        path_data=request.path_data,
        shape_type=request.shape_type,
        shape_data=request.shape_data,
        text_content=request.text_content,
        color=request.color,
        width=request.width,
        opacity=request.opacity,
        font_size=request.font_size,
        font_family=request.font_family,
    )

    return {"stroke_id": str(stroke.id), "message": "Stroke added"}


@router.post("/whiteboard/{whiteboard_id}/equation")
async def add_equation(
    whiteboard_id: UUID,
    request: EquationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add math equation to whiteboard"""
    user_id = UUID(current_user.user_id)
    service = WhiteboardService(db)

    equation = await service.add_equation(
        whiteboard_id=whiteboard_id,
        user_id=user_id,
        page_number=request.page_number,
        x=request.x,
        y=request.y,
        latex_code=request.latex_code,
        font_size=request.font_size,
        color=request.color,
    )

    return {
        "equation_id": str(equation.id),
        "rendered_svg": equation.rendered_svg,
        "message": "Equation added",
    }


@router.get("/whiteboard/{whiteboard_id}/page/{page_number}")
async def get_page_content(
    whiteboard_id: UUID,
    page_number: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete page content (strokes + equations)"""
    service = WhiteboardService(db)
    content = await service.get_page_content(whiteboard_id, page_number)

    return content


@router.post("/whiteboard/{whiteboard_id}/page")
async def add_page(
    whiteboard_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add new page to whiteboard"""
    service = WhiteboardService(db)
    whiteboard = await service.add_page(whiteboard_id)

    if not whiteboard:
        raise HTTPException(status_code=404, detail="Whiteboard not found")

    return {
        "page_count": whiteboard.page_count,
        "current_page": whiteboard.current_page,
    }


@router.delete("/whiteboard/stroke/{stroke_id}")
async def delete_stroke(
    stroke_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete stroke"""
    service = WhiteboardService(db)
    success = await service.delete_stroke(stroke_id)

    if not success:
        raise HTTPException(status_code=404, detail="Stroke not found")

    return {"message": "Stroke deleted"}


# ============================================================
# Task 108.4: Recording
# ============================================================


@router.post("/{session_id}/recording/start")
async def start_recording(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    title: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Start session recording (host only)"""
    await _verify_host_only(session_id, current_user, db)
    service = VideoConferenceService(db)

    recording = await service.start_recording(session_id, title)

    return {"recording_id": str(recording.id), "message": "Recording started"}


@router.post("/recording/{recording_id}/stop")
async def stop_recording(
    recording_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop recording"""
    service = VideoConferenceService(db)
    recording = await service.stop_recording(recording_id)

    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    return {"message": "Recording stopped", "status": recording.status}


@router.get("/{session_id}/recordings")
async def get_session_recordings(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all recordings for session"""
    await _verify_session_participant(session_id, current_user, db)
    service = VideoConferenceService(db)
    recordings = await service.get_session_recordings(session_id)

    return {
        "recordings": [
            {
                "id": str(rec.id),
                "title": rec.title,
                "duration_seconds": rec.duration_seconds,
                "file_url": rec.file_url,
                "thumbnail_url": rec.thumbnail_url,
                "status": rec.status,
                "view_count": rec.view_count,
            }
            for rec in recordings
        ]
    }


# ============================================================
# Chat
# ============================================================


@router.post("/{session_id}/chat")
async def send_chat_message(
    session_id: UUID,
    request: ChatMessageRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send chat message"""
    await _verify_session_participant(session_id, current_user, db)
    user_id = UUID(current_user.user_id)
    service = VideoConferenceService(db)

    message = await service.send_chat_message(
        session_id=session_id,
        user_id=user_id,
        message=request.message,
        recipient_id=request.recipient_id,
    )

    return {"message_id": str(message.id), "created_at": message.created_at.isoformat()}


@router.get("/{session_id}/chat")
async def get_session_chat(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get chat messages"""
    await _verify_session_participant(session_id, current_user, db)
    service = VideoConferenceService(db)
    messages = await service.get_session_chat(session_id, limit)

    return {
        "messages": [
            {
                "id": str(msg.id),
                "user_id": str(msg.user_id),
                "message": msg.message,
                "is_private": msg.is_private,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]
    }


# ============================================================
# User Sessions
# ============================================================


@router.get("/my-sessions")
async def get_my_sessions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    status: SessionStatus | None = None,
    upcoming_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get user's sessions"""
    user_id = UUID(current_user.user_id)
    service = VideoConferenceService(db)
    sessions = await service.get_user_sessions(user_id, status, upcoming_only)

    return {
        "sessions": [
            {
                "id": str(s.id),
                "title": s.title,
                "status": s.status,
                "scheduled_start": s.scheduled_start.isoformat(),
                "scheduled_end": s.scheduled_end.isoformat(),
                "meeting_url": s.meeting_url,
            }
            for s in sessions
        ]
    }
