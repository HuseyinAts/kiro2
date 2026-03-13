"""
League Models

LeagueMembership ve LeagueHistory modelleri — haftalik lig sistemi.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class LeagueMembership(Base):
    """Ogrencinin mevcut haftaki lig uyeligi."""

    __tablename__ = "league_memberships"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    league_tier: Mapped[str] = mapped_column(String(20), default="BRONZE")
    weekly_xp: Mapped[int] = mapped_column(Integer, default=0)
    week_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<LeagueMembership id={self.id} student={self.student_id}"
            f" tier={self.league_tier}>"
        )


class LeagueHistory(Base):
    """Gecmis haftalara ait lig sonuclari."""

    __tablename__ = "league_history"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    week_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    from_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    to_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    final_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    final_xp: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<LeagueHistory id={self.id} student={self.student_id}"
            f" week={self.week_start}>"
        )
