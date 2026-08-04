"""
SQLAlchemy ORM Content Models
database.py'den ayrıştırıldı (2026-01-10)
"""

import uuid
from uuid6 import uuid7
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .enums_db import ExamType, QuestionDifficulty, SubjectArea

if TYPE_CHECKING:
    from .user_models import TeacherProfile


# DEPRECATED: `Question` class has been removed to fix the Dual Table Trap.
# Please import `QuestionBankItem` from `models.question_bank` instead.


# Legacy alias for compatibility
EgitimIcerigi = "EducationalContent"


class EducationalContent(Base):
    """Eğitim içeriği modeli"""

    __tablename__ = "educational_contents"
    __table_args__ = (
        Index("idx_content_subject", "subject_area"),
        Index("idx_content_topic", "topic"),
        Index("idx_content_grade", "grade_level"),
        Index("idx_content_difficulty", "difficulty_level"),
        Index("idx_content_score", "educational_score"),
        Index("idx_content_platform", "source_platform"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Content information
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, deferred=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Source information
    source_platform: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(200))

    # Classification
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    subtopic: Mapped[str | None] = mapped_column(String(200))
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)

    # Quality metrics
    difficulty_level: Mapped[QuestionDifficulty] = mapped_column(
        Enum(QuestionDifficulty), nullable=False
    )
    educational_score: Mapped[float] = mapped_column(Float, default=0.0)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)

    # Accessibility features
    has_subtitles: Mapped[bool] = mapped_column(Boolean, default=False)
    has_transcript: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(10), default="tr")

    # Engagement metrics
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class ClassRoom(Base):
    """Sınıf modeli"""

    __tablename__ = "classrooms"
    __table_args__ = (
        CheckConstraint(
            "grade_level >= 9 AND grade_level <= 12", name="check_class_grade_level"
        ),
        Index("idx_classroom_teacher", "teacher_id"),
        Index("idx_classroom_grade", "grade_level"),
        Index("idx_classroom_subject", "subject_area"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    teacher_id: Mapped[str] = mapped_column(String, ForeignKey("teacher_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Class information
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)
    school_year: Mapped[str] = mapped_column(String(20), nullable=False)

    # Student list (JSON array of student IDs)
    student_ids: Mapped[dict | None] = mapped_column(JSON, deferred=True)

    # Class settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    max_students: Mapped[int] = mapped_column(Integer, default=40)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    teacher: Mapped["TeacherProfile"] = relationship(
        "TeacherProfile", back_populates="classes"
    , lazy="selectin")
