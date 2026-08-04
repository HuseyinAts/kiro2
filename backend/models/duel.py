"""
Duel Models

DuelSession, DuelMatch ve DuelRating modelleri — ogrenciler arasi soru duelolari.
"""

import uuid
from uuid6 import uuid7
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class DuelSession(Base):
    """Iki ogrenci arasindaki duel oturumu."""

    __tablename__ = "duel_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    player1_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    player2_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, default=5)
    time_per_question_sec: Mapped[int] = mapped_column(Integer, default=15)
    status: Mapped[str] = mapped_column(String(20), default="waiting")
    player1_score: Mapped[int] = mapped_column(Integer, default=0)
    player2_score: Mapped[int] = mapped_column(Integer, default=0)
    winner_id: Mapped[str | None] = mapped_column(String, nullable=True)
    player1_elo_change: Mapped[float] = mapped_column(Float, default=0.0)
    player2_elo_change: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<DuelSession id={self.id} p1={self.player1_id}"
            f" p2={self.player2_id} status={self.status}>"
        )


class DuelMatch(Base):
    """Duel oturumu icindeki tek bir soru eslesmesi."""

    __tablename__ = "duel_matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("duel_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False)
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    player1_answer: Mapped[str | None] = mapped_column(String(1), nullable=True)
    player1_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    player1_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    player2_answer: Mapped[str | None] = mapped_column(String(1), nullable=True)
    player2_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    player2_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<DuelMatch id={self.id} session={self.session_id}"
            f" q={self.question_order}>"
        )


class DuelRating(Base):
    """Ogrencinin duel ELO puani ve istatistikleri."""

    __tablename__ = "duel_ratings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    student_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    elo_rating: Mapped[float] = mapped_column(Float, default=1200.0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    peak_rating: Mapped[float] = mapped_column(Float, default=1200.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<DuelRating id={self.id} student={self.student_id} elo={self.elo_rating}>"
        )
