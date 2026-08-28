"""
SQLAlchemy ORM Analytics Models
database.py'den ayrıştırıldı (2026-01-10)
"""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from uuid6 import uuid7

from .base import Base
from .enums_db import SubjectArea

if TYPE_CHECKING:
    from .user_models import StudentProfile


class LearningAnalytics(Base):
    """Öğrenme analitiği modeli"""

    __tablename__ = "learning_analytics"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "date", "subject_area", name="uq_learning_analytics"
        ),
        Index("idx_learning_analytics_student", "student_id"),
        Index("idx_learning_analytics_date", "date"),
        Index("idx_learning_analytics_subject", "subject_area"),
    )

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
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Analytics data
    date: Mapped[date] = mapped_column(Date, nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)

    # Performance metrics
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    questions_correct: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)
    study_time_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Learning progress
    skill_level: Mapped[float] = mapped_column(Float, default=0.0)
    improvement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_preference: Mapped[float] = mapped_column(Float, default=0.0)

    # Devrimsel özellik metrikleri
    zpd_utilization: Mapped[float] = mapped_column(Float, default=0.0)
    fsrs_retention_rate: Mapped[float] = mapped_column(Float, default=0.0)
    morphology_awareness: Mapped[float] = mapped_column(Float, default=0.0)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile", back_populates="learning_analytics"
    )
