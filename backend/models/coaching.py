"""
Coaching Models

CoachingEvent ve StudentEngagementSignal modelleri — AI koçluk ve etkileşim sinyalleri.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from uuid6 import uuid7

from .base import Base


class CoachingEvent(Base):
    """AI koç tarafindan olusturulan ogrenci motivasyon/uyari olaylari."""

    __tablename__ = "coaching_events"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid7())
    )
    organization_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, deferred=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False, deferred=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    shown_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    clicked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
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
        String, primary_key=True, default=lambda: str(uuid7())
    )
    organization_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
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
