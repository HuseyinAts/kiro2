"""
Proactive Coaching Models — F6
AI coaching events, engagement signals, and suggestion tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class CoachingEvent(Base):
    """A coaching suggestion shown to (or dismissed by) a student."""

    __tablename__ = "coaching_events"
    __table_args__ = (
        Index("idx_coaching_student", "student_id"),
        Index("idx_coaching_event_type", "event_type"),
        Index("idx_coaching_shown", "student_id", "shown_at"),
        Index("idx_coaching_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    # weakness_alert, burnout_warning, streak_encouragement, topic_recommendation
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # what triggered the suggestion
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # higher = more important
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Interaction tracking
    shown_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StudentEngagementSignal(Base):
    """Behavioral signal recorded for a student (session_duration, post_error_pause, etc.)."""

    __tablename__ = "student_engagement_signals"
    __table_args__ = (
        Index("idx_engagement_student", "student_id"),
        Index("idx_engagement_type_recorded", "student_id", "signal_type", "recorded_at"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    # session_duration, post_error_pause, answer_speed_trend, daily_login
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
