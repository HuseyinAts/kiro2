"""
Pomodoro Odalari API — Birlikte Calisma (F4)
Endpoints: /api/v1/pomodoro/*

- Odaya katil (sistem eslestirmeli)
- Oda durumu gor
- Durum guncelle (working/on_break)
- Oturumu bitir
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.pomodoro import PomodoroParticipant, PomodoroRoom

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pomodoro", tags=["Pomodoro Rooms"])

XP_PER_ROUND = 5
XP_COMPLETION_BONUS = 15


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class JoinRoomRequest(BaseModel):
    subject_area: str = Field(..., min_length=2, max_length=50)
    topic: str | None = Field(None, max_length=100)


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(working|on_break|left)$")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/join", response_model=dict[str, Any])
async def join_room(
    body: JoinRoomRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Bir pomodoro odasina katil. Uygun oda yoksa yeni olustur."""
    user_id = str(current_user.id)

    # Aktif oda kontrolu — kullanici zaten bir odada mi?
    active_check = await db.execute(
        select(PomodoroParticipant).where(
            PomodoroParticipant.student_id == user_id,
            PomodoroParticipant.status.in_(["joined", "working", "on_break"]),
        )
    )
    if active_check.scalar_one_or_none():
        raise HTTPException(400, "Zaten aktif bir odadasiniz.")

    # Uygun oda bul (ayni konu, bos yer var)
    room_result = await db.execute(
        select(PomodoroRoom).where(
            PomodoroRoom.subject_area == body.subject_area,
            PomodoroRoom.status == "waiting",
            PomodoroRoom.current_participants < PomodoroRoom.max_participants,
        )
    )
    room = room_result.scalar_one_or_none()

    if not room:
        # Yeni oda olustur
        room = PomodoroRoom(
            subject_area=body.subject_area,
            topic=body.topic,
        )
        db.add(room)
        await db.flush()

    # Katilimci ekle
    participant = PomodoroParticipant(
        room_id=room.id,
        student_id=user_id,
    )
    db.add(participant)
    room.current_participants = (room.current_participants or 0) + 1

    # 2+ kisi olunca odayi aktif et
    if room.current_participants >= 2 and room.status == "waiting":
        from datetime import UTC, datetime

        room.status = "active"
        room.started_at = datetime.now(UTC)
        room.current_round = 1

    await db.commit()

    return {
        "success": True,
        "data": {
            "room_id": room.id,
            "subject_area": room.subject_area,
            "status": room.status,
            "participants": room.current_participants,
            "work_minutes": room.work_minutes,
            "break_minutes": room.break_minutes,
        },
        "message": "Odaya katildiniz!",
    }


@router.get("/room/{room_id}", response_model=dict[str, Any])
async def get_room_status(
    room_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Oda durumunu ve katilimcilari gor."""
    result = await db.execute(select(PomodoroRoom).where(PomodoroRoom.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Oda bulunamadi.")

    # Katilimcilari getir
    p_result = await db.execute(
        select(PomodoroParticipant).where(
            PomodoroParticipant.room_id == room_id,
            PomodoroParticipant.status != "left",
        )
    )
    participants = p_result.scalars().all()

    return {
        "success": True,
        "data": {
            "room": {
                "id": room.id,
                "subject_area": room.subject_area,
                "topic": room.topic,
                "status": room.status,
                "current_round": room.current_round,
                "total_rounds": room.total_rounds,
                "work_minutes": room.work_minutes,
                "break_minutes": room.break_minutes,
                "started_at": room.started_at.isoformat() if room.started_at else None,
            },
            "participants": [
                {
                    "student_id": p.student_id,
                    "status": p.status,
                    "rounds_completed": p.rounds_completed,
                }
                for p in participants
            ],
        },
    }


@router.post("/room/{room_id}/status", response_model=dict[str, Any])
async def update_participant_status(
    room_id: str,
    body: StatusUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Katilimci durumunu guncelle (working/on_break/left)."""
    user_id = str(current_user.id)

    result = await db.execute(
        select(PomodoroParticipant).where(
            PomodoroParticipant.room_id == room_id,
            PomodoroParticipant.student_id == user_id,
            PomodoroParticipant.status != "left",
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(404, "Bu odada katilimci degilsiniz.")

    participant.status = body.status

    if body.status == "left":
        from datetime import UTC, datetime

        participant.left_at = datetime.now(UTC)
        # Oda katilimci sayisini dusur
        room_result = await db.execute(
            select(PomodoroRoom).where(PomodoroRoom.id == room_id)
        )
        room = room_result.scalar_one_or_none()
        if room:
            room.current_participants = max(0, (room.current_participants or 1) - 1)
            if room.current_participants == 0:
                room.status = "completed"
                room.ended_at = datetime.now(UTC)

    await db.commit()

    return {
        "success": True,
        "message": f"Durumunuz: {body.status}",
    }


@router.post("/room/{room_id}/complete-round", response_model=dict[str, Any])
async def complete_round(
    room_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Bir pomodoro turunu tamamla. XP kazan."""
    user_id = str(current_user.id)

    result = await db.execute(
        select(PomodoroParticipant).where(
            PomodoroParticipant.room_id == room_id,
            PomodoroParticipant.student_id == user_id,
            PomodoroParticipant.status.in_(["joined", "working"]),
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(404, "Bu odada aktif katilimci degilsiniz.")

    participant.rounds_completed = (participant.rounds_completed or 0) + 1
    participant.total_work_minutes = (participant.total_work_minutes or 0) + 25
    participant.xp_earned = (participant.xp_earned or 0) + XP_PER_ROUND

    # Tum turlari tamamladi mi?
    room_result = await db.execute(
        select(PomodoroRoom).where(PomodoroRoom.id == room_id)
    )
    room = room_result.scalar_one_or_none()

    bonus = 0
    if room and participant.rounds_completed >= room.total_rounds:
        participant.status = "completed"
        bonus = XP_COMPLETION_BONUS
        participant.xp_earned += bonus

    await db.commit()

    return {
        "success": True,
        "data": {
            "rounds_completed": participant.rounds_completed,
            "xp_earned": XP_PER_ROUND + bonus,
            "total_xp": participant.xp_earned,
        },
        "message": "Tur tamamlandi!"
        if not bonus
        else f"Tebrikler! Tum turlar bitti! +{bonus} bonus XP",
    }
