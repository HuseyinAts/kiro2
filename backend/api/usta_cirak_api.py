"""
Usta-Cirak API — Mentor-Mentee Sistemi (F6)
Endpoints: /api/v1/usta-cirak/*

- Usta/cirak ol
- Sistem eslestirmesi
- Oturum baslat/bitir
- Geri bildirim ver (preset)
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.usta_cirak import MentorFeedback, MentorPair, MentorSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/usta-cirak", tags=["Usta-Cirak"])

XP_SESSION_MENTOR = 20
XP_SESSION_MENTEE = 10
MAX_MENTEES_PER_MENTOR = 2

FEEDBACK_TAGS = [
    "helpful",
    "patient",
    "clear",
    "knowledgeable",
    "encouraging",
    "fast",
]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class MentorRequest(BaseModel):
    subject_area: str = Field(..., min_length=2, max_length=50)
    role: str = Field(..., pattern=r"^(mentor|mentee)$")


class SessionStart(BaseModel):
    question_bank_id: str | None = None
    topic: str | None = Field(None, max_length=100)


class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    tags: list[str] | None = None


# ---------------------------------------------------------------------------
# Match Endpoints
# ---------------------------------------------------------------------------


@router.post("/request", response_model=dict[str, Any])
async def request_match(
    body: MentorRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Usta veya cirak olarak eslestirme iste."""
    user_id = str(current_user.id)

    # Aktif pair kontrolu
    existing = await db.execute(
        select(func.count())
        .select_from(MentorPair)
        .where(
            MentorPair.status == "active",
            MentorPair.subject_area == body.subject_area,
            or_(
                MentorPair.mentor_id == user_id,
                MentorPair.mentee_id == user_id,
            ),
        )
    )
    active_count = existing.scalar() or 0

    if body.role == "mentor" and active_count >= MAX_MENTEES_PER_MENTOR:
        raise HTTPException(400, f"Maksimum {MAX_MENTEES_PER_MENTOR} cirak limiti.")
    if body.role == "mentee" and active_count >= 1:
        raise HTTPException(400, "Bu konuda zaten bir ustaniz var.")

    # Bekleyen karsi tarafi bul
    if body.role == "mentor":
        # Cirak arayan var mi?
        waiting = await db.execute(
            select(MentorPair).where(
                MentorPair.status == "waiting_mentor",
                MentorPair.subject_area == body.subject_area,
            )
        )
        match = waiting.scalar_one_or_none()
        if match:
            match.mentor_id = user_id
            match.status = "active"
            await db.commit()
            return {
                "success": True,
                "data": {"pair_id": match.id, "matched": True},
                "message": "Cirak eslesti!",
            }
        # Beklemeye al
        pair = MentorPair(
            mentor_id=user_id,
            mentee_id="",
            subject_area=body.subject_area,
            status="waiting_mentee",
        )
    else:
        # Usta arayan var mi?
        waiting = await db.execute(
            select(MentorPair).where(
                MentorPair.status == "waiting_mentee",
                MentorPair.subject_area == body.subject_area,
            )
        )
        match = waiting.scalar_one_or_none()
        if match:
            match.mentee_id = user_id
            match.status = "active"
            await db.commit()
            return {
                "success": True,
                "data": {"pair_id": match.id, "matched": True},
                "message": "Usta eslesti!",
            }
        # Beklemeye al
        pair = MentorPair(
            mentor_id="",
            mentee_id=user_id,
            subject_area=body.subject_area,
            status="waiting_mentor",
        )

    db.add(pair)
    await db.commit()

    return {
        "success": True,
        "data": {"pair_id": pair.id, "matched": False},
        "message": "Eslesme bekleniyor...",
    }


@router.get("/pairs", response_model=dict[str, Any])
async def get_my_pairs(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Aktif usta-cirak eslesmelerini gor."""
    user_id = str(current_user.id)

    result = await db.execute(
        select(MentorPair).where(
            MentorPair.status == "active",
            or_(
                MentorPair.mentor_id == user_id,
                MentorPair.mentee_id == user_id,
            ),
        )
    )
    pairs = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": p.id,
                "mentor_id": p.mentor_id,
                "mentee_id": p.mentee_id,
                "subject_area": p.subject_area,
                "session_count": p.session_count,
                "my_role": "mentor" if p.mentor_id == user_id else "mentee",
            }
            for p in pairs
        ],
    }


# ---------------------------------------------------------------------------
# Session Endpoints
# ---------------------------------------------------------------------------


@router.post("/pairs/{pair_id}/session", response_model=dict[str, Any])
async def start_session(
    pair_id: str,
    body: SessionStart,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Birlikte calisma oturumu baslat."""
    user_id = str(current_user.id)

    await _get_active_pair(pair_id, user_id, db)

    session = MentorSession(
        pair_id=pair_id,
        question_bank_id=body.question_bank_id,
        topic=body.topic,
    )
    db.add(session)
    await db.commit()

    return {
        "success": True,
        "data": {"session_id": session.id},
        "message": "Oturum basladi!",
    }


@router.post("/sessions/{session_id}/end", response_model=dict[str, Any])
async def end_session(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Oturumu bitir ve XP dagit."""
    user_id = str(current_user.id)
    from datetime import UTC, datetime

    result = await db.execute(
        select(MentorSession).where(
            MentorSession.id == session_id,
            MentorSession.status == "active",
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Aktif oturum bulunamadi.")

    # Pair kontrolu
    pair = await _get_active_pair(session.pair_id, user_id, db)

    now = datetime.now(UTC)
    session.status = "completed"
    session.ended_at = now
    if session.started_at:
        session.duration_minutes = int((now - session.started_at).total_seconds() / 60)

    # XP dagit
    session.mentor_xp = XP_SESSION_MENTOR
    session.mentee_xp = XP_SESSION_MENTEE
    pair.session_count = (pair.session_count or 0) + 1
    pair.total_xp_mentor = (pair.total_xp_mentor or 0) + XP_SESSION_MENTOR
    pair.total_xp_mentee = (pair.total_xp_mentee or 0) + XP_SESSION_MENTEE

    await db.commit()

    return {
        "success": True,
        "data": {
            "duration_minutes": session.duration_minutes,
            "mentor_xp": XP_SESSION_MENTOR,
            "mentee_xp": XP_SESSION_MENTEE,
        },
        "message": "Oturum bitti! XP kazanildi.",
    }


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------


@router.post("/sessions/{session_id}/feedback", response_model=dict[str, Any])
async def submit_feedback(
    session_id: str,
    body: FeedbackCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Oturum sonrasi geri bildirim ver (preset secenekler)."""
    user_id = str(current_user.id)

    result = await db.execute(
        select(MentorSession).where(
            MentorSession.id == session_id,
            MentorSession.status == "completed",
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Tamamlanmis oturum bulunamadi.")

    # Pair'den karsi tarafi bul
    pair_result = await db.execute(
        select(MentorPair).where(MentorPair.id == session.pair_id)
    )
    pair = pair_result.scalar_one_or_none()
    if not pair:
        raise HTTPException(404, "Eslestirme bulunamadi.")

    receiver_id = pair.mentee_id if pair.mentor_id == user_id else pair.mentor_id
    if user_id not in (pair.mentor_id, pair.mentee_id):
        raise HTTPException(403, "Bu oturumun katilimcisi degilsiniz.")

    # Tag validasyonu
    valid_tags = []
    if body.tags:
        valid_tags = [t for t in body.tags if t in FEEDBACK_TAGS]

    feedback = MentorFeedback(
        session_id=session_id,
        giver_id=user_id,
        receiver_id=receiver_id,
        rating=body.rating,
        tags=",".join(valid_tags) if valid_tags else None,
    )
    db.add(feedback)
    await db.commit()

    return {
        "success": True,
        "message": "Geri bildiriminiz kaydedildi.",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_active_pair(pair_id: str, user_id: str, db: AsyncSession) -> MentorPair:
    result = await db.execute(
        select(MentorPair).where(
            MentorPair.id == pair_id,
            MentorPair.status == "active",
        )
    )
    pair = result.scalar_one_or_none()
    if not pair:
        raise HTTPException(404, "Aktif eslestirme bulunamadi.")
    if user_id not in (pair.mentor_id, pair.mentee_id):
        raise HTTPException(403, "Bu eslestirmenin katilimcisi degilsiniz.")
    return pair
