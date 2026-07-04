"""
SQLAlchemy ORM Content Models
database.py'den ayrıştırıldı (2026-01-10)
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
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


class Question(Base):
    """Soru modeli"""

    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(
            "correct_answer IN ('A', 'B', 'C', 'D', 'E')", name="check_correct_answer"
        ),
        CheckConstraint(
            "irt_difficulty >= -3.0 AND irt_difficulty <= 3.0",
            name="check_irt_difficulty",
        ),
        CheckConstraint(
            "irt_discrimination >= 0.1 AND irt_discrimination <= 3.0",
            name="check_irt_discrimination",
        ),
        CheckConstraint(
            "irt_guessing >= 0.0 AND irt_guessing <= 1.0", name="check_irt_guessing"
        ),
        CheckConstraint(
            "irt_upper_asymptote >= 0.85 AND irt_upper_asymptote <= 1.0",
            name="check_irt_upper_asymptote",
        ),
        Index("idx_question_exam_type", "exam_type"),
        Index("idx_question_subject", "subject_area"),
        Index("idx_question_topic", "topic"),
        Index("idx_question_difficulty", "difficulty"),
        Index("idx_question_irt_difficulty", "irt_difficulty"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Question content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_image_url: Mapped[str | None] = mapped_column(String(500))

    # Answer options
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    option_e: Mapped[str | None] = mapped_column(Text)

    correct_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)

    # Classification - use values_callable for correct lowercase enum mapping
    exam_type: Mapped[ExamType] = mapped_column(
        Enum(
            ExamType,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
            create_constraint=False,
        ),
        nullable=False,
    )
    subject_area: Mapped[SubjectArea] = mapped_column(
        Enum(
            SubjectArea,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
            create_constraint=False,
        ),
        nullable=False,
    )
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    subtopic: Mapped[str | None] = mapped_column(String(200))

    # Difficulty and IRT parameters
    difficulty: Mapped[QuestionDifficulty] = mapped_column(
        Enum(
            QuestionDifficulty,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
            create_constraint=False,
        ),
        nullable=False,
    )
    irt_difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    irt_discrimination: Mapped[float] = mapped_column(Float, default=1.0)
    irt_guessing: Mapped[float] = mapped_column(Float, default=0.25)
    irt_upper_asymptote: Mapped[float] = mapped_column(Float, default=1.0)

    # IRT calibration metadata
    irt_calibrated: Mapped[bool] = mapped_column(Boolean, default=False)
    irt_sample_size: Mapped[int] = mapped_column(Integer, default=0)

    # Source information
    source_book: Mapped[str | None] = mapped_column(String(300))
    source_page: Mapped[int | None] = mapped_column(Integer)

    # Turkish morphology analysis
    morphology_complexity: Mapped[float] = mapped_column(Float, default=0.0)
    readability_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Statistics
    times_asked: Mapped[int] = mapped_column(Integer, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)

    # System fields
    created_by: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column("aktif", Boolean, default=True)

    # Visual content support
    visual_content: Mapped[dict | None] = mapped_column(JSON)

    # Note: exam_questions and student_answers relationships moved to QuestionBankItem
    # (ExamQuestion/StudentAnswer now reference question_bank table)


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

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Content information
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


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

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    teacher_id: Mapped[str] = mapped_column(
        String, ForeignKey("teacher_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Class information
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)
    school_year: Mapped[str] = mapped_column(String(20), nullable=False)

    # Student list (JSON array of student IDs)
    student_ids: Mapped[dict | None] = mapped_column(JSON)

    # Class settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    )
