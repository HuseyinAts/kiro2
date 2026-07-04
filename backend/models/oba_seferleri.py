"""
Oba Seferleri (Team Challenges) Models — F3 Social Feature

Tablolar:
- oba_challenges: Haftalik takim gorevi
- oba_challenge_progress: Bireysel katki logu

Kurallar:
- Oba (guild) 5-15 kisi
- Haftalik hedef: toplam X soru coz, Y XP kazan
- Bireysel katki otomatik sayilir (soru cozme, CAT, FSRS)
- Chat yok, sadece ilerleme cizgisi
- Tamamlaninca tum oba uyelerine bonus XP
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

# ---------------------------------------------------------------------------
# Table 1: oba_challenges
# ---------------------------------------------------------------------------


class ObaChallenge(Base):
    """Haftalik oba (takim) gorevi."""

    __tablename__ = "oba_challenges"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    oba_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Gorev tanimı
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    challenge_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="solve_questions"
    )  # solve_questions, earn_xp, streak_days, review_cards
    # Hedefler
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    current_value: Mapped[int] = mapped_column(Integer, default=0)
    # Odul
    bonus_xp_per_member: Mapped[int] = mapped_column(Integer, default=50)
    # Durum
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )  # active, completed, expired
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    # Zaman
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Table 2: oba_challenge_progress
# ---------------------------------------------------------------------------


class ObaChallengeProgress(Base):
    """Bireysel katki logu — otomatik guncellenir."""

    __tablename__ = "oba_challenge_progress"

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
    challenge_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Katki
    contribution: Mapped[int] = mapped_column(Integer, default=0)
    contribution_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    # XP
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
