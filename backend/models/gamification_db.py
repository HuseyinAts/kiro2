"""
SQLAlchemy ORM Gamification Models (Manipulatives)
database.py'den ayrıştırıldı (2026-01-10)
Task 87.9: REQ-51.101-51.105
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    pass


class ManipulativeProgress(Base):
    """Manipulative usage progress tracking"""

    __tablename__ = "manipulative_progress"
    __table_args__ = (
        Index("idx_manip_progress_user", "user_id"),
        Index("idx_manip_progress_type", "manipulative_type"),
        Index("idx_manip_progress_user_type", "user_id", "manipulative_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    manipulative_type = Column(String(50), nullable=False)
    activity_type = Column(String(50))

    # Progress metrics
    operation_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    total_duration_seconds = Column(Integer, default=0)
    avg_duration_seconds = Column(Float, default=0.0)
    mastery_level = Column(Float, default=0.0)

    # Activity details
    activity_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="manipulative_progress")


class ManipulativeActivity(Base):
    """Individual manipulative activity log"""

    __tablename__ = "manipulative_activities"
    __table_args__ = (
        Index("idx_manip_activity_user", "user_id"),
        Index("idx_manip_activity_created", "created_at"),
        Index("idx_manip_activity_user_created", "user_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    manipulative_type = Column(String(50), nullable=False)
    activity_type = Column(String(50))

    # Activity metrics
    duration_seconds = Column(Integer)
    completed = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)

    # Activity details
    details = Column(JSON)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="manipulative_activities")


class WeeklyProgress(Base):
    """Weekly progress tracking"""

    __tablename__ = "weekly_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "year", "week_number", name="uq_weekly_progress"),
        Index("idx_weekly_progress_user", "user_id"),
        Index("idx_weekly_progress_year_week", "year", "week_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Week info
    year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)

    # Metrics
    total_activities = Column(Integer, default=0)
    total_time_seconds = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)

    # Daily breakdown
    daily_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="weekly_progress")
