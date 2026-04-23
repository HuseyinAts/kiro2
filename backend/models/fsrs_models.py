"""
SQLAlchemy ORM FSRS (Spaced Repetition System) Models
database.py'den ayrıştırıldı (2026-01-10)
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .enums_db import SubjectArea

if TYPE_CHECKING:
    from .user_models import User


class FSRSCard(Base):
    """FSRS flashcard modeli"""

    __tablename__ = "fsrs_cards"
    __table_args__ = (
        Index("idx_fsrs_card_student", "student_id"),
        Index("idx_fsrs_card_due", "due_date"),
        Index("idx_fsrs_card_subject", "subject_area"),
        Index("idx_fsrs_card_state", "state"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Kart içeriği
    front_text: Mapped[str] = mapped_column(Text, nullable=False)
    back_text: Mapped[str] = mapped_column(Text, nullable=False)
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)

    # FSRS parametreleri
    stability: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    elapsed_days: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_days: Mapped[int] = mapped_column(Integer, default=0)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)

    # Durum
    state: Mapped[str] = mapped_column(String(20), default="new")
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_review: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Türk öğrenci özel faktörleri
    cultural_factors: Mapped[dict | None] = mapped_column(JSON)

    # Sistem alanları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_cards")
    reviews: Mapped[list["FSRSReview"]] = relationship(
        "FSRSReview", back_populates="card"
    )


class FSRSReview(Base):
    """FSRS review kayıtları"""

    __tablename__ = "fsrs_reviews"
    __table_args__ = (
        CheckConstraint("grade >= 1 AND grade <= 4", name="check_fsrs_grade"),
        Index("idx_fsrs_review_card", "card_id"),
        Index("idx_fsrs_review_student", "student_id"),
        Index("idx_fsrs_review_date", "review_date"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    card_id: Mapped[str] = mapped_column(
        String, ForeignKey("fsrs_cards.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Review bilgileri
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    review_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    response_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # FSRS hesaplamaları
    old_stability: Mapped[float] = mapped_column(Float, default=0.0)
    new_stability: Mapped[float] = mapped_column(Float, default=0.0)
    old_difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    new_difficulty: Mapped[float] = mapped_column(Float, default=0.0)

    # Kültürel faktör etkisi
    cultural_adjustment: Mapped[float] = mapped_column(Float, default=1.0)

    # İlişkiler
    card: Mapped["FSRSCard"] = relationship("FSRSCard", back_populates="reviews")
    student: Mapped["User"] = relationship("User", back_populates="fsrs_reviews")


class FSRSSchedule(Base):
    """FSRS zamanlama tablosu"""

    __tablename__ = "fsrs_schedules"
    __table_args__ = (
        UniqueConstraint("student_id", "schedule_date", name="uq_fsrs_schedule"),
        Index("idx_fsrs_schedule_student", "student_id"),
        Index("idx_fsrs_schedule_date", "schedule_date"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Zamanlama bilgileri
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_cards_due: Mapped[int] = mapped_column(Integer, default=0)
    new_cards: Mapped[int] = mapped_column(Integer, default=0)
    review_cards: Mapped[int] = mapped_column(Integer, default=0)

    # Performans metrikleri
    cards_studied: Mapped[int] = mapped_column(Integer, default=0)
    study_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    retention_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Türk öğrenci adaptasyonu
    cultural_period: Mapped[str | None] = mapped_column(String(50))
    adjustment_factor: Mapped[float] = mapped_column(Float, default=1.0)

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_schedules")


class FSRSStudentProfile(Base):
    """FSRS öğrenci profili"""

    __tablename__ = "fsrs_student_profiles"
    __table_args__ = (Index("idx_fsrs_profile_student", "student_id"),)

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # FSRS parametreleri (17 parametre)
    fsrs_parameters: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Türk öğrenci özel parametreleri
    cultural_parameters: Mapped[dict] = mapped_column(JSON, nullable=False)

    # İstatistikler
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    average_retention: Mapped[float] = mapped_column(Float, default=0.0)
    study_streak_days: Mapped[int] = mapped_column(Integer, default=0)

    # Sistem alanları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_profile")


class FSRSStudySession(Base):
    """FSRS çalışma oturumları"""

    __tablename__ = "fsrs_study_sessions"
    __table_args__ = (
        Index("idx_fsrs_session_student", "student_id"),
        Index("idx_fsrs_session_date", "session_date"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Oturum bilgileri
    session_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    cards_reviewed: Mapped[int] = mapped_column(Integer, default=0)

    # Performans
    correct_reviews: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)

    # Kültürel bağlam
    cultural_context: Mapped[dict | None] = mapped_column(JSON)

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_study_sessions")


class FSRSSubjectStats(Base):
    """FSRS konu bazlı istatistikler"""

    __tablename__ = "fsrs_subject_stats"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_area", name="uq_fsrs_subject_stats"),
        Index("idx_fsrs_stats_student", "student_id"),
        Index("idx_fsrs_stats_subject", "subject_area"),
    )

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject_area: Mapped[SubjectArea] = mapped_column(Enum(SubjectArea), nullable=False)

    # İstatistikler
    total_cards: Mapped[int] = mapped_column(Integer, default=0)
    mature_cards: Mapped[int] = mapped_column(Integer, default=0)
    average_stability: Mapped[float] = mapped_column(Float, default=0.0)
    average_difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    retention_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Zaman damgaları
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    student: Mapped["User"] = relationship("User", back_populates="fsrs_subject_stats")
