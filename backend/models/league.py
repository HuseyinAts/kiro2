"""
League System Models — F2
5-tier league: BRONZE -> SILVER -> GOLD -> PLATINUM -> CHAMPION
Weekly XP-based ranking with promotion/demotion.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

# Tier constants (UPPERCASE)
LEAGUE_TIERS = ["BRONZE", "SILVER", "GOLD", "PLATINUM", "CHAMPION"]
DEFAULT_TIER = "BRONZE"


class LeagueMembership(Base):
    """Current league standing for a student in the active week."""

    __tablename__ = "league_memberships"
    __table_args__ = (
        Index("idx_league_membership_student", "student_id"),
        Index("idx_league_membership_tier_week", "league_tier", "week_start"),
        Index("idx_league_membership_xp_rank", "league_tier", "week_start", "weekly_xp"),
        UniqueConstraint("student_id", "week_start", name="uq_league_membership_student_week"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    league_tier: Mapped[str] = mapped_column(String(20), nullable=False, default=DEFAULT_TIER)
    weekly_xp: Mapped[int] = mapped_column(Integer, default=0)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # computed periodically

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LeagueHistory(Base):
    """Historical league results per student per week."""

    __tablename__ = "league_history"
    __table_args__ = (
        Index("idx_league_history_student", "student_id"),
        Index("idx_league_history_week", "week_start"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    from_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    to_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    final_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    final_xp: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
