"""
Usta-Cirak (Mentor-Mentee) Models — F6 Social Feature

Tablolar:
- mentor_pairs: Usta-cirak eslesmesi
- mentor_sessions: Birlikte calisma oturumu
- mentor_feedback: Oturum sonrasi geri bildirim (preset secenekler)

Kurallar:
- Usta: subject_area'da theta >= 1.0 (IRT yeterliligi)
- Sistem eslestirmeli, kullanici secimi YOK
- Chat yok, sadece preset mesaj sablonlari
- Max 2 aktif cirak / usta
- Oturum max 30dk
"""

from __future__ import annotations

import uuid
from uuid6 import uuid7
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

# ---------------------------------------------------------------------------
# Table 1: mentor_pairs
# ---------------------------------------------------------------------------


class MentorPair(Base):
    """Usta-cirak eslesmesi."""

    __tablename__ = "mentor_pairs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    mentor_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    mentee_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject_area: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Durum
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )  # active, completed, cancelled
    # Istatistikler
    session_count: Mapped[int] = mapped_column(Integer, default=0)
    total_xp_mentor: Mapped[int] = mapped_column(Integer, default=0)
    total_xp_mentee: Mapped[int] = mapped_column(Integer, default=0)
    # Zaman
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ---------------------------------------------------------------------------
# Table 2: mentor_sessions
# ---------------------------------------------------------------------------


class MentorSession(Base):
    """Usta-cirak birlikte calisma oturumu."""

    __tablename__ = "mentor_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    pair_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Hangi soru/konu uzerinde
    question_bank_id: Mapped[str | None] = mapped_column(String, nullable=True)
    topic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Durum
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, completed, cancelled
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # XP
    mentor_xp: Mapped[int] = mapped_column(Integer, default=0)
    mentee_xp: Mapped[int] = mapped_column(Integer, default=0)
    # Zaman
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ---------------------------------------------------------------------------
# Table 3: mentor_feedback
# ---------------------------------------------------------------------------


class MentorFeedback(Base):
    """Oturum sonrasi geri bildirim — preset secenekler."""

    __tablename__ = "mentor_feedback"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    session_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    giver_id: Mapped[str] = mapped_column(String, nullable=False)
    receiver_id: Mapped[str] = mapped_column(String, nullable=False)
    # Preset secenekler (1-5 yildiz + etiketler)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    tags: Mapped[str | None] = mapped_column(
        Text, nullable=True
    , deferred=True)  # comma-separated: "helpful,patient,clear"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
