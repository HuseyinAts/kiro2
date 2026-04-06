"""
PWA Sync & Push API — endpoints for frontend backgroundSyncService.ts and sw.ts

Frontend calls:
  POST /api/v1/sync/exam-sessions   — implemented (Sprint 1E)
  POST /api/v1/sync/study-notes    — stub
  POST /api/v1/sync/progress       — stub
  POST /api/v1/push/subscribe      — stub
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import AuthenticatedUser, get_current_user, get_db
from models.exam_db import ExamSession, StudentAnswer

logger = logging.getLogger(__name__)

# Two routers: one for /sync, one for /push
sync_router = APIRouter(prefix="/api/v1/sync", tags=["PWA Sync"])
push_router = APIRouter(prefix="/api/v1/push", tags=["PWA Push"])


# --- Request Schemas ---


class OfflineExamSession(BaseModel):
    """Payload from backgroundSyncService.ts:syncExamSessions()."""

    session_id: str = Field(..., description="Offline exam session UUID")
    questions: list[str] = Field(default_factory=list, description="Question IDs")
    answers: dict[str, int] = Field(
        default_factory=dict, description="questionId -> selected answer (1-5)"
    )
    start_time: str = Field(..., description="ISO-8601 start timestamp")
    end_time: str | None = Field(None, description="ISO-8601 end timestamp")
    score: float | None = Field(None, description="Score 0-100")
    completed: bool = Field(False, description="Whether session was completed")


class PushSubscriptionPayload(BaseModel):
    endpoint: str
    keys: dict[str, str] = Field(default_factory=dict)


# --- Stub Endpoints (study-notes, progress, push/subscribe) ---


@push_router.post("/subscribe")
async def push_subscribe(
    subscription: PushSubscriptionPayload,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Register push notification subscription — stub endpoint.
    Frontend: backgroundSyncService.ts
    """
    return {
        "success": True,
        "data": {"subscribed": False},
        "message": "Push subscription stub — not yet implemented",
    }


@sync_router.post("/study-notes")
async def sync_study_notes(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Sync offline study notes — stub endpoint.
    Frontend: backgroundSyncService.ts
    """
    return {
        "success": True,
        "data": {"synced": 0, "pending": 0},
        "message": "Study notes sync stub — not yet implemented",
    }


@sync_router.post("/progress")
async def sync_progress(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Sync offline progress data — stub endpoint.
    Frontend: backgroundSyncService.ts / sw.ts
    """
    return {
        "success": True,
        "data": {"synced": 0, "pending": 0},
        "message": "Progress sync stub — not yet implemented",
    }


# --- Implemented: sync/exam-sessions ---


def _parse_dt(iso_str: str | None) -> datetime | None:
    if iso_str is None:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(UTC)


@sync_router.post("/exam-sessions")
async def sync_exam_sessions(
    session: OfflineExamSession,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Sync offline exam session from PWA to PostgreSQL.

    Upserts ExamSession + bulk upserts StudentAnswer records.
    Frontend only checks HTTP status — response body is informational.
    """
    student_id = str(current_user.id)

    # Upsert exam session
    session_values = {
        "id": session.session_id,
        "student_id": student_id,
        "status": "completed" if session.completed else "in_progress",
        "started_at": _parse_dt(session.start_time),
        "completed_at": _parse_dt(session.end_time),
        "total_questions": len(session.questions),
        "time_spent_seconds": 0,
        "total_correct": 0,
        "total_wrong": 0,
        "total_empty": 0,
        "raw_score": session.score or 0.0,
        "updated_at": datetime.now(UTC),
    }

    stmt = pg_insert(ExamSession).values(**session_values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={k: v for k, v in session_values.items() if v is not None and k != "id"},
    )
    await db.execute(stmt)

    # Bulk upsert student answers
    synced = 0
    for qid in session.questions:
        selected = session.answers.get(qid)  # 1-5 or None
        answer_char = chr(64 + selected) if selected is not None else None  # 1->A, etc.
        answer_values = {
            "id": str(uuid.uuid4()),
            "exam_session_id": session.session_id,
            "question_id": qid,
            "selected_answer": answer_char,
            "is_correct": None,
            "response_time_seconds": 0.0,
        }
        ans_stmt = pg_insert(StudentAnswer).values(**answer_values)
        ans_stmt = ans_stmt.on_conflict_do_update(
            index_elements=["exam_session_id", "question_id"],
            set_={
                k: v
                for k, v in answer_values.items()
                if v is not None and k not in ("id", "exam_session_id", "question_id")
            },
        )
        await db.execute(ans_stmt)
        synced += 1

    await db.commit()

    return {
        "success": True,
        "data": {"synced": synced, "pending": 0},
        "message": f"Exam session {session.session_id} synced",
    }


# Expose combined router AFTER all route decorators
# so include_router captures the actual routes (not an empty snapshot)
router = APIRouter()
router.include_router(sync_router)
router.include_router(push_router)
