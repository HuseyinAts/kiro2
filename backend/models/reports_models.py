"""
SQLAlchemy ORM Report Models
database.py'den ayrıştırıldı (2026-01-10)
ParentReport, ParentApproval, StudentGrade, ClassReport

NOTE: StudentGoal and Notification were moved to their canonical files:
- StudentGoal -> student_goal.py
- Notification -> notification.py
"""

import uuid
from uuid6 import uuid7
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    JSON,
    Boolean,
    Date,
    DateTime,
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

if TYPE_CHECKING:
    from .user_models import User


class ParentReport(Base):
    """Weekly reports sent to parents about student performance"""

    __tablename__ = "parent_reports"
    __table_args__ = (
        Index("idx_parent_report_parent", "parent_user_id", "created_at"),
        Index("idx_parent_report_student", "student_user_id"),
        Index("idx_parent_report_period", "report_period"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    parent_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Report period
    report_period: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="e.g., 2025-W47"
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Statistics
    total_study_minutes: Mapped[int] = mapped_column(Integer, default=0)
    completed_exams_count: Mapped[int] = mapped_column(Integer, default=0)
    average_success_rate: Mapped[float] = mapped_column(
        Float, default=0.0, comment="0-100"
    )

    # Performance arrays
    strong_subjects: Mapped[list[str]] = mapped_column(JSON, default=list, deferred=True)
    weak_subjects: Mapped[list[str]] = mapped_column(JSON, default=list, deferred=True)
    weekly_progress_description: Mapped[str | None] = mapped_column(Text, deferred=True)

    # Recommendations
    parent_recommendations: Mapped[list[str]] = mapped_column(JSON, default=list, deferred=True)
    support_areas: Mapped[list[str]] = mapped_column(JSON, default=list, deferred=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships (dual FK - both point to User)
    parent: Mapped["User"] = relationship("User", foreign_keys=[parent_user_id], lazy="selectin")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_user_id], lazy="selectin")


class ParentApproval(Base):
    """Parent approval requests from students"""

    __tablename__ = "parent_approvals"
    __table_args__ = (
        Index("idx_approval_parent_status", "parent_user_id", "status"),
        Index("idx_approval_student", "student_user_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    student_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    parent_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Request details
    request_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="ekstra_ders_izni, sinav_kayit, ozel_egitim",
    )
    request_description: Mapped[str] = mapped_column(Text, nullable=False, deferred=True)
    status: Mapped[str] = mapped_column(
        String(20), default="beklemede", comment="beklemede, onaylandi, reddedildi"
    )

    # Response
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    parent_note: Mapped[str | None] = mapped_column(Text, deferred=True)

    # Relationships (dual FK - both point to User)
    student: Mapped["User"] = relationship("User", foreign_keys=[student_user_id], lazy="selectin")
    parent: Mapped["User"] = relationship("User", foreign_keys=[parent_user_id], lazy="selectin")


class StudentGrade(Base):
    """Teacher-assigned grades for students"""

    __tablename__ = "student_grades"
    __table_args__ = (
        Index("idx_grade_student_subject", "student_user_id", "subject"),
        Index("idx_grade_teacher", "teacher_user_id"),
        Index("idx_grade_academic_year", "academic_year", "semester"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    teacher_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Grade details
    subject: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Matematik, Türkçe, etc."
    )
    grade_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="yazili, sözlü, proje, performans"
    )
    grade_value: Mapped[float] = mapped_column(
        Float, nullable=False, comment="0-100 or other scale"
    )
    max_grade: Mapped[float] = mapped_column(Float, default=100.0)
    weight: Mapped[float] = mapped_column(
        Float, default=1.0, comment="Weight in final grade calculation"
    )
    notes: Mapped[str | None] = mapped_column(Text, deferred=True)

    # Academic period
    graded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    academic_year: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="2024-2025"
    )
    semester: Mapped[int] = mapped_column(Integer, nullable=False, comment="1 or 2")

    # Relationships (dual FK - both point to User)
    teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_user_id], lazy="selectin")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_user_id], lazy="selectin")


class ClassReport(Base):
    """Teacher reports for class performance"""

    __tablename__ = "class_reports"
    __table_args__ = (
        Index("idx_class_report_teacher", "teacher_user_id", "created_at"),
        Index("idx_class_report_period", "report_period"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    teacher_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Class info
    class_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="12-A, 11-B, etc."
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    report_period: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="2025-W47, 2025-Q1, etc."
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Class statistics
    total_students: Mapped[int] = mapped_column(Integer, default=0)
    average_grade: Mapped[float] = mapped_column(Float, default=0.0)
    passing_students: Mapped[int] = mapped_column(Integer, default=0)
    failing_students: Mapped[int] = mapped_column(Integer, default=0)

    # Performance distribution
    grade_distribution: Mapped[dict | None] = mapped_column(
        JSON, comment='{"90-100": 5, "80-90": 10, ...}'
    , deferred=True)
    top_students: Mapped[list[str]] = mapped_column(JSON, default=list, deferred=True)
    struggling_students: Mapped[list[str]] = mapped_column(JSON, default=list, deferred=True)

    # Recommendations
    teacher_notes: Mapped[str | None] = mapped_column(Text, deferred=True)
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list, deferred=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    teacher: Mapped["User"] = relationship("User", lazy="selectin")
