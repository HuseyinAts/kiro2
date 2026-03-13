"""
Coaching Models

CoachingEvent ve StudentEngagementSignal modelleri — AI koçluk ve etkileşim sinyalleri.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class CoachingEvent(Base):
    """AI koç tarafindan olusturulan ogrenci motivasyon/uyari olaylari."""

    __tablename__ = "coaching_events"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    shown_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    clicked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<CoachingEvent id={self.id} student={self.student_id}"
            f" type={self.event_type}>"
        )


class StudentEngagementSignal(Base):
    """Ogrencinin platform etkileşim sinyalleri (seans suresi, aktivite skoru vb.)."""

    __tablename__ = "student_engagement_signals"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<StudentEngagementSignal id={self.id} student={self.student_id}"
            f" type={self.signal_type} value={self.value}>"
        )
