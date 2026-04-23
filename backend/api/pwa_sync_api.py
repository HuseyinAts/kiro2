"""
PWA Sync & Push API — endpoints for frontend backgroundSyncService.ts and sw.ts

Public JSON paths (``sync_router`` / ``push_router``); there is no ``/api/pwa-sync-api`` API.

Frontend calls:
  GET  /api/v1/sync/health          — liveness + DB ping (no auth)
  GET  /api/v1/push/health         — push router liveness (no auth, no DB)
  POST /api/v1/sync/exam-sessions   — implemented (Sprint 1E)
  POST /api/v1/sync/progress       — implemented (Sprint 1G)
  POST /api/v1/push/subscribe      — stub
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user, get_db
from models.exam_db import ExamSession, StudentAnswer

logger = logging.getLogger(__name__)

# Two routers: one for /sync, one for /push
sync_router = APIRouter(prefix="/api/v1/sync", tags=["PWA Sync"])
push_router = APIRouter(prefix="/api/v1/push", tags=["PWA Push"])


@sync_router.get("/health", tags=["health"])
async def pwa_sync_health() -> dict[str, str | bool]:
    """Liveness: ``SELECT 1`` — auth yok."""
    try:
        async with get_db_session_context() as db:
            await db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "service": "pwa_sync",
            "database": True,
        }
    except Exception as e:
        logger.warning(f"PWA sync health DB ping failed: {e!s}")
        return {
            "status": "degraded",
            "service": "pwa_sync",
            "database": False,
        }


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


class OfflineProgressPayload(BaseModel):
    """Payload from backgroundSyncService.ts:syncProgress() and sw.ts:syncUserProgress()."""

    userId: str = Field(..., description="User ID")
    subject: str = Field(..., description="Subject area")
    totalQuestions: int = Field(..., description="Total questions attempted")
    correctAnswers: int = Field(..., description="Number of correct answers")
    studyTime: int = Field(..., description="Study time in minutes")
    lastActivity: str = Field(..., description="ISO-8601 last activity timestamp")


class PushSubscriptionPayload(BaseModel):
    """Payload for push notification subscription."""

    endpoint: str
    keys: dict[str, str] = Field(default_factory=dict)


@push_router.get("/health", tags=["health"])
async def pwa_push_health() -> dict[str, str | bool]:
    """Push API rotası açık; auth yok, DB sorgusu yok (subscribe stub)."""
    return {
        "status": "ok",
        "service": "pwa_push",
        "subscribe_implemented": False,
    }


# --- Stub Endpoints (study-notes, push/subscribe) ---


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


@sync_router.post("/progress")
async def sync_progress(
    progress: OfflineProgressPayload,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Sync offline progress data to learning_progress_daily.

    Upserts into learning_progress_daily using (user_id, log_date, subject, activity_type) unique key.
    Frontend only checks HTTP status — response body is informational.
    """
    if str(progress.userId).strip() != str(current_user.id).strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="userId must match authenticated user",
        )

    student_id = str(current_user.id)

    # Determine log_date from lastActivity (date part only)
    try:
        last_dt = datetime.fromisoformat(progress.lastActivity.replace("Z", "+00:00"))
        log_date = last_dt.date()
    except ValueError:
        log_date = datetime.now(UTC).date()

    # Map subject from frontend convention to canonical form
    # Frontend sends lowercase ("matematik", "turkce") — normalize to DB uppercase
    subject_map = {
        "matematik": "MATEMATIK",
        "turkce": "TURKCE",
        "fen": "FEN",
        "sosyal": "SOSYAL",
        "fizik": "FIZIK",
        "kimya": "KIMYA",
        "biyoloji": "BIYOLOJI",
        "tarih": "TARIH",
        "cografya": "COGRAFIYA",
        "geometri": "GEOMETRI",
        "edebiyat": "EDEBIYAT",
    }
    db_subject = subject_map.get(progress.subject.lower(), progress.subject.upper())

    progress_values = {
        "user_id": student_id,
        "log_date": log_date,
        "subject": db_subject,
        "minutes_spent": progress.studyTime,
        "questions_done": progress.totalQuestions,
        "correct_count": progress.correctAnswers,
        "activity_type": "practice",
    }

    # Upsert using raw SQL — learning_progress_daily has no ORM model (raw SQL migration)
    upsert_sql = text("""
        INSERT INTO learning_progress_daily
            (user_id, log_date, subject, minutes_spent, questions_done, correct_count, activity_type)
        VALUES
            (:user_id, :log_date, :subject, :minutes_spent, :questions_done, :correct_count, :activity_type)
        ON CONFLICT ON CONSTRAINT learning_progress_daily_user_id_log_date_subject_activity_t_key
        DO UPDATE SET
            minutes_spent = EXCLUDED.minutes_spent,
            questions_done = EXCLUDED.questions_done,
            correct_count = EXCLUDED.correct_count
    """)
    await db.execute(upsert_sql, progress_values)
    await db.commit()

    return {
        "success": True,
        "data": {"synced": 1, "pending": 0},
        "message": f"Progress synced for {db_subject} on {log_date}",
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

    existing_owner = (
        await db.execute(
            select(ExamSession.student_id).where(ExamSession.id == session.session_id)
        )
    ).scalar_one_or_none()
    if existing_owner is not None and str(existing_owner) != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Exam session belongs to another user",
        )

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
        set_={
            k: v
            for k, v in session_values.items()
            if v is not None and k not in ("id", "student_id")
        },
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
