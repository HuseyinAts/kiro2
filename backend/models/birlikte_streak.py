"""
Birlikte Streak Models — F5 Social Feature

Tablolar:
- streak_pairs: Streak ortakligi (2 kisilik)
- streak_daily_log: Gunluk streak logu

Kurallar:
- Sistem eslestirmeli (kullanici secimi yok)
- Her iki kisi de gunluk gorev tamamlarsa streak devam eder
- 7-gun bonusu, 30-gun bonusu
- Ortaklik max 1 aktif (ayni anda baska ortak yok)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

# ---------------------------------------------------------------------------
# Table 1: streak_pairs
# ---------------------------------------------------------------------------


class StreakPair(Base):
    """Streak ortakligi — sistem tarafindan eslestirilir."""

    __tablename__ = "streak_pairs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_a_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    student_b_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Durum
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )  # active, broken, completed
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0)
    # XP
    total_xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    # Zaman
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    broken_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ---------------------------------------------------------------------------
# Table 2: streak_daily_log
# ---------------------------------------------------------------------------


class StreakDailyLog(Base):
    """Gunluk streak kaydı — her kullanici icin o gun gorev tamamladi mi."""

    __tablename__ = "streak_daily_log"

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
    pair_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
