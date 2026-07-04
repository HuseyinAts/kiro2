"""
Pomodoro Odalari (Study Rooms) Models — F4 Social Feature

Tablolar:
- pomodoro_rooms: Calisma odalari (2-4 kisi, konu bazli)
- pomodoro_participants: Oda katilimcilari
- pomodoro_sessions: Bireysel pomodoro oturumlari

Kurallar:
- Oda max 4 kisi
- Sistem eslestirmeli (kullanici secimi yok)
- Chat yok, sadece durum gostergeleri (calisiyorum/molada/bitti)
- 25dk calisma + 5dk mola dogusu
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

# ---------------------------------------------------------------------------
# Table 1: pomodoro_rooms
# ---------------------------------------------------------------------------


class PomodoroRoom(Base):
    """Konu bazli calisma odasi — max 4 kisi."""

    __tablename__ = "pomodoro_rooms"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subject_area: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    topic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Oda durumu
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="waiting", index=True
    )  # waiting, active, completed
    max_participants: Mapped[int] = mapped_column(Integer, default=4)
    current_participants: Mapped[int] = mapped_column(Integer, default=0)
    # Pomodoro ayarlari
    work_minutes: Mapped[int] = mapped_column(Integer, default=25)
    break_minutes: Mapped[int] = mapped_column(Integer, default=5)
    total_rounds: Mapped[int] = mapped_column(Integer, default=4)
    current_round: Mapped[int] = mapped_column(Integer, default=0)
    # Zaman
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Table 2: pomodoro_participants
# ---------------------------------------------------------------------------


class PomodoroParticipant(Base):
    """Oda katilimcisi."""

    __tablename__ = "pomodoro_participants"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    room_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Durum
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="joined"
    )  # joined, working, on_break, left, completed
    rounds_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_work_minutes: Mapped[int] = mapped_column(Integer, default=0)
    # XP
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
