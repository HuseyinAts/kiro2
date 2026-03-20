"""
SQLAlchemy ORM Exam Models
database.py'den ayrıştırıldı (2026-01-10)
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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

from .base import Base
from .enums_db import ExamType

if TYPE_CHECKING:
    from .user_models import StudentProfile
    from .question_bank import QuestionBankItem


class ExamSession(Base):
    """Sınav oturumu modeli"""

    __tablename__ = "exam_sessions"
    __table_args__ = (
        Index("idx_exam_session_student", "student_id"),
        Index("idx_exam_session_type", "exam_type"),
        Index("idx_exam_session_status", "status"),
        Index("idx_exam_session_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Exam information
    exam_type: Mapped[ExamType] = mapped_column(Enum(ExamType), nullable=False)
    exam_name: Mapped[str] = mapped_column(String(200), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Session status
    status: Mapped[str] = mapped_column(String(50), default="not_started")
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Results
    total_correct: Mapped[int] = mapped_column(Integer, default=0)
    total_wrong: Mapped[int] = mapped_column(Integer, default=0)
    total_empty: Mapped[int] = mapped_column(Integer, default=0)
    raw_score: Mapped[float] = mapped_column(Float, default=0.0)
    scaled_score: Mapped[Optional[float]] = mapped_column(Float)
    percentile: Mapped[Optional[float]] = mapped_column(Float)

    # IRT Analysis
    estimated_ability: Mapped[float] = mapped_column(Float, default=0.0)
    ability_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile", back_populates="exam_sessions"
    )
    exam_questions: Mapped[List["ExamQuestion"]] = relationship(
        "ExamQuestion", back_populates="exam_session"
    )
    student_answers: Mapped[List["StudentAnswer"]] = relationship(
        "StudentAnswer", back_populates="exam_session"
    )


class ExamQuestion(Base):
    """Sınav-soru ilişki modeli"""

    __tablename__ = "exam_questions"
    __table_args__ = (
        UniqueConstraint(
            "exam_session_id", "question_order", name="uq_exam_question_order"
        ),
        Index("idx_exam_question_session", "exam_session_id"),
        Index("idx_exam_question_order", "question_order"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    exam_session_id: Mapped[str] = mapped_column(
        String, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False)

    question_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    exam_session: Mapped["ExamSession"] = relationship(
        "ExamSession", back_populates="exam_questions"
    )
    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", foreign_keys=[question_id],
        primaryjoin="ExamQuestion.question_id == QuestionBankItem.id",
        lazy="select",
    )


class StudentAnswer(Base):
    """Öğrenci cevap modeli"""

    __tablename__ = "student_answers"
    __table_args__ = (
        UniqueConstraint("exam_session_id", "question_id", name="uq_student_answer"),
        CheckConstraint(
            "selected_answer IS NULL OR selected_answer IN ('A', 'B', 'C', 'D', 'E')",
            name="check_selected_answer",
        ),
        Index("idx_student_answer_session", "exam_session_id"),
        Index("idx_student_answer_question", "question_id"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    exam_session_id: Mapped[str] = mapped_column(
        String, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False)

    # Answer information
    selected_answer: Mapped[Optional[str]] = mapped_column(String(1))
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    response_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # Behavioral data
    answer_changes: Mapped[int] = mapped_column(Integer, default=0)
    time_to_first_answer: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_level: Mapped[Optional[float]] = mapped_column(Float)

    # System fields
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    exam_session: Mapped["ExamSession"] = relationship(
        "ExamSession", back_populates="student_answers"
    )
    question: Mapped["QuestionBankItem"] = relationship(
        "QuestionBankItem", foreign_keys=[question_id],
        primaryjoin="StudentAnswer.question_id == QuestionBankItem.id",
        lazy="select",
    )
