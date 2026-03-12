"""
1v1 Düello Models — F1
DB tables: duel_sessions, duel_matches, duel_ratings

Real-time competitive quiz duels between students with ELO rating.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class DuelSession(Base):
    """A 1v1 duel session between two players."""

    __tablename__ = "duel_sessions"
    __table_args__ = (
        Index("idx_duel_player1", "player1_id"),
        Index("idx_duel_player2", "player2_id"),
        Index("idx_duel_status", "status"),
        Index("idx_duel_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    player1_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    player2_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id"), nullable=True
    )

    # Game config
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, default=5)
    time_per_question_sec: Mapped[int] = mapped_column(Integer, default=15)

    # Status: waiting, active, completed, cancelled, expired
    status: Mapped[str] = mapped_column(String(20), default="waiting")

    # Scores
    player1_score: Mapped[int] = mapped_column(Integer, default=0)
    player2_score: Mapped[int] = mapped_column(Integer, default=0)
    winner_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # ELO changes
    player1_elo_change: Mapped[float] = mapped_column(Float, default=0.0)
    player2_elo_change: Mapped[float] = mapped_column(Float, default=0.0)

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DuelMatch(Base):
    """A single question round within a duel session."""

    __tablename__ = "duel_matches"
    __table_args__ = (
        Index("idx_duel_match_session", "session_id"),
        Index("idx_duel_match_order", "session_id", "question_order"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("duel_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False)
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Player 1 response
    player1_answer: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    player1_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    player1_correct: Mapped[Optional[bool]] = mapped_column(nullable=True)

    # Player 2 response
    player2_answer: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    player2_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    player2_correct: Mapped[Optional[bool]] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DuelRating(Base):
    """ELO rating for a student in duels."""

    __tablename__ = "duel_ratings"
    __table_args__ = (
        Index("idx_duel_rating_student", "student_id", unique=True),
        Index("idx_duel_rating_elo", "elo_rating"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, unique=True
    )
    elo_rating: Mapped[float] = mapped_column(Float, default=1200.0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    peak_rating: Mapped[float] = mapped_column(Float, default=1200.0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
