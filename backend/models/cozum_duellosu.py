"""
Cozum Duellosu (Solution Duel) Models — F2 Social Feature

Tablolar:
- solution_duels: Cozum duellosu eslesmesi
- solution_duel_submissions: Katilimci cozum gonderimi
- solution_duel_votes: Topluluk oyu (hangi cozum daha iyi)

Kurallar:
- Ayni soru uzerinde 2 kisi yarisir
- Her ikisi de cozum gonderir (zamanli)
- Topluluk oylama ile kazanan belirlenir
- Sistem eslestirmeli (benzer theta/seviye)
- Chat yok, sadece cozum gonderimi
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

# ---------------------------------------------------------------------------
# Table 1: solution_duels
# ---------------------------------------------------------------------------


class SolutionDuel(Base):
    """Cozum duellosu — 2 kisi ayni soruyu cozer, topluluk oylar."""

    __tablename__ = "solution_duels"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Soru
    question_bank_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject_area: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Katilimcilar
    challenger_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    opponent_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    # Durum
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="waiting", index=True
    )  # waiting, active, voting, completed, cancelled
    # Zaman limitleri
    solve_time_seconds: Mapped[int] = mapped_column(Integer, default=300)  # 5dk
    voting_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Sonuc
    winner_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # XP
    winner_xp: Mapped[int] = mapped_column(Integer, default=30)
    loser_xp: Mapped[int] = mapped_column(Integer, default=10)
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
# Table 2: solution_duel_submissions
# ---------------------------------------------------------------------------


class SolutionDuelSubmission(Base):
    """Duello katilimcisinin cozum gonderimi."""

    __tablename__ = "solution_duel_submissions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    duel_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    # Cozum
    body: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Oylama
    vote_count: Mapped[int] = mapped_column(Integer, default=0)
    # Moderasyon
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Table 3: solution_duel_votes
# ---------------------------------------------------------------------------


class SolutionDuelVote(Base):
    """Topluluk oyu — duel basina kisi basina 1."""

    __tablename__ = "solution_duel_votes"
    __table_args__ = (UniqueConstraint("duel_id", "voter_id", name="uq_duel_vote"),)

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    duel_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    voter_id: Mapped[str] = mapped_column(String, nullable=False)
    voted_for_id: Mapped[str] = mapped_column(String, nullable=False)  # submission_id
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
