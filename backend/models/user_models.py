"""
SQLAlchemy ORM User Models
database.py'den ayrıştırıldı (2026-01-10)
"""

import uuid
from uuid6 import uuid7
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String,
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .enums_db import LearningStyle, UserRole

if TYPE_CHECKING:
    from .analytics_db import LearningAnalytics
    from .content_db import ClassRoom
    from .exam_db import ExamSession
    from .fsrs_models import (
        FSRSCard,
        FSRSReview,
        FSRSSchedule,
        FSRSStudentProfile,
        FSRSStudySession,
        FSRSSubjectStats,
    )
    from .gamification_db import (
        ManipulativeActivity,
        ManipulativeProgress,
        WeeklyProgress,
    )
    from .learning_path_models import LearningPathStudentProfile


class User(Base):
    """Kullanıcı modeli - öğrenci, öğretmen, veli"""

    __tablename__ = "users"
    __table_args__ = (
        # Single-column indexes
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
        Index("idx_user_role", "role"),
        Index("idx_user_created_at", "created_at"),
        # Compound indexes for common query patterns
        Index("idx_user_email_role", "email", "role"),  # Login + role check
        Index("idx_user_created_active", "created_at", "is_active"),  # User listing
        Index("idx_user_role_active", "role", "is_active"),  # Active users by role
        Index(
            "idx_user_premium_expires", "is_premium", "premium_expires_at"
        ),  # Premium check
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    # Faz 0 multi-tenancy: kurum bağı (Step 2 retrofit)
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Sprint 4: Two-Factor Authentication (2FA) fields
    secret_2fa: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="TOTP secret key for 2FA"
    )
    is_2fa_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="2FA enabled status"
    )
    backup_codes_hashed: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="Hashed backup codes for 2FA recovery"
    , deferred=True)

    # Sprint 6: Premium/Tier fields for rate limiting
    is_premium: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Premium subscription status"
    )
    premium_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Premium subscription expiry"
    )

    # Profile information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.STUDENT
    )

    # Contact information
    phone: Mapped[str | None] = mapped_column(String(20))
    birth_date: Mapped[date | None] = mapped_column(Date)

    # Gamification fields (Task 91)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    last_level_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # System fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # DB'de mevcut kolonlar — Alembic dışı migration ile eklendi
    elo_rating: Mapped[int] = mapped_column(Integer, default=1000)
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile", back_populates="user", uselist=False
    )
    teacher_profile: Mapped[Optional["TeacherProfile"]] = relationship(
        "TeacherProfile", back_populates="user", uselist=False
    )
    parent_profile: Mapped[Optional["ParentProfile"]] = relationship(
        "ParentProfile", back_populates="user", uselist=False
    )

    # Gamification relationships (Task 91, P2.2)
    badges: Mapped[list["UserBadge"]] = relationship("UserBadge", back_populates="user")
    achievements: Mapped[list["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user"
    )
    point_transactions: Mapped[list["PointTransaction"]] = relationship(
        "models.point_transaction.PointTransaction", back_populates="user"
    )

    # FSRS relationships
    fsrs_cards: Mapped[list["FSRSCard"]] = relationship(
        "FSRSCard", back_populates="student"
    )
    fsrs_schedules: Mapped[list["FSRSSchedule"]] = relationship(
        "FSRSSchedule", back_populates="student"
    )
    fsrs_reviews: Mapped[list["FSRSReview"]] = relationship(
        "FSRSReview", back_populates="student"
    )
    fsrs_profile: Mapped[Optional["FSRSStudentProfile"]] = relationship(
        "FSRSStudentProfile", back_populates="student", uselist=False
    )
    fsrs_study_sessions: Mapped[list["FSRSStudySession"]] = relationship(
        "FSRSStudySession", back_populates="student"
    )
    fsrs_subject_stats: Mapped[list["FSRSSubjectStats"]] = relationship(
        "FSRSSubjectStats", back_populates="student"
    )

    # Manipulatives relationships (Task 87.9)
    manipulative_progress: Mapped[list["ManipulativeProgress"]] = relationship(
        "ManipulativeProgress", back_populates="user"
    )
    manipulative_activities: Mapped[list["ManipulativeActivity"]] = relationship(
        "ManipulativeActivity", back_populates="user"
    )
    weekly_progress: Mapped[list["WeeklyProgress"]] = relationship(
        "WeeklyProgress", back_populates="user"
    )


class StudentProfile(Base):
    """
    Öğrenci profil modeli (User tablosu ile ilişkili).

    NOTE: For learning path specific operations, consider using
    LearningPathStudentProfile from backend.models.learning_path_models.

    This model is kept for general user profile data tied to User table.
    """

    __tablename__ = "student_profiles"
    __table_args__ = (
        CheckConstraint(
            "grade_level >= 9 AND grade_level <= 12", name="check_grade_level"
        ),
        CheckConstraint(
            "current_level >= 0.0 AND current_level <= 10.0", name="check_current_level"
        ),
        Index("idx_student_grade_level", "grade_level"),
        Index("idx_student_learning_style", "learning_style"),
        Index("idx_student_grade_style", "grade_level", "learning_style"),
        Index("idx_student_user_grade", "user_id", "grade_level"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Faz 0 multi-tenancy: kurum bağı (Step 2 retrofit)
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )

    # Academic information
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 9, 10, 11, 12
    school_name: Mapped[str | None] = mapped_column(String(200))
    target_university: Mapped[str | None] = mapped_column(String(200))
    target_department: Mapped[str | None] = mapped_column(String(200))
    hedef_sinav: Mapped[str | None] = mapped_column(String(20))
    veli_onay: Mapped[bool] = mapped_column(Boolean, default=True)
    # KVKK Faz 1: reşit olmayan öğrenci için veli iletişim e-postası (capture-only)
    veli_email: Mapped[str | None] = mapped_column(String(255))

    # Learning preferences
    learning_style: Mapped[LearningStyle | None] = mapped_column(Enum(LearningStyle))
    study_hours_per_day: Mapped[int | None] = mapped_column(Integer)
    preferred_study_time: Mapped[str | None] = mapped_column(String(50))

    # Performance tracking
    current_level: Mapped[float] = mapped_column(Float, default=0.0)
    total_study_hours: Mapped[int] = mapped_column(Integer, default=0)
    total_questions_solved: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)

    # Devrimsel özellikler
    vark_profile: Mapped[dict | None] = mapped_column(JSON, deferred=True)
    zpd_range: Mapped[dict | None] = mapped_column(JSON, deferred=True)
    irt_ability: Mapped[float] = mapped_column(Float, default=0.0)
    fsrs_parameters: Mapped[dict | None] = mapped_column(JSON, deferred=True)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="student_profile"
    )
    exam_sessions: Mapped[list["ExamSession"]] = relationship(
        "ExamSession", back_populates="student"
    )
    learning_analytics: Mapped[list["LearningAnalytics"]] = relationship(
        "LearningAnalytics", back_populates="student"
    )

    def to_canonical(self) -> "LearningPathStudentProfile":
        """
        Convert to canonical LearningPathStudentProfile for learning path operations.

        Returns:
            New LearningPathStudentProfile instance
        """
        from .learning_path_models import LearningPathStudentProfile

        return LearningPathStudentProfile.from_legacy_profile(self)


class TeacherProfile(Base):
    """Öğretmen profil modeli"""

    __tablename__ = "teacher_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Faz 0 multi-tenancy: kurum bağı (Step 2 retrofit)
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )

    # Professional information
    school_name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject_areas: Mapped[dict | None] = mapped_column(JSON, deferred=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    education_level: Mapped[str | None] = mapped_column(String(100))

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="teacher_profile")
    classes: Mapped[list["ClassRoom"]] = relationship(
        "ClassRoom", back_populates="teacher"
    )


class ParentProfile(Base):
    """Veli profil modeli"""

    __tablename__ = "parent_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Faz 0 multi-tenancy: kurum bağı (Step 2 retrofit)
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )

    # Children information (JSON array of student IDs)
    children_ids: Mapped[dict | None] = mapped_column(JSON, deferred=True)

    # Notification preferences
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    sms_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    weekly_reports: Mapped[bool] = mapped_column(Boolean, default=True)

    # System fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="parent_profile")


# Import gamification models at the end to avoid circular imports
from .organization import Organization, OrgMembership  # noqa: E402, F401
from .point_transaction import PointTransaction  # noqa: E402
from .user_achievement import UserAchievement  # noqa: E402
from .user_badge import UserBadge  # noqa: E402
