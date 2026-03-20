"""
Manipulatives database models
REQ-51.101-51.105: Progress tracking, badges, achievements
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


class ManipulativeProgress(Base):
    """Manipulative usage progress tracking"""

    __tablename__ = "manipulative_progress"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    manipulative_type = Column(
        String(50), nullable=False
    )  # virtualBlocks, geogebra, geometry, tangram
    activity_type = Column(String(50))  # add, subtract, geometry, algebra, etc.

    # Progress metrics
    operation_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    total_duration_seconds = Column(Integer, default=0)
    avg_duration_seconds = Column(Float, default=0.0)
    mastery_level = Column(Float, default=0.0)  # 0-100

    # Activity details
    activity_data = Column(JSON)  # Additional metadata

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="manipulative_progress")


class ManipulativeActivity(Base):
    """Individual manipulative activity log"""

    __tablename__ = "manipulative_activities"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    manipulative_type = Column(String(50), nullable=False)
    activity_type = Column(String(50))

    # Activity metrics
    duration_seconds = Column(Integer)
    completed = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)

    # Activity details
    details = Column(JSON)  # Specific activity data

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="manipulative_activities")


class UserBadge(Base):
    """User earned badges"""

    __tablename__ = "user_badges"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    badge_id = Column(String(100), nullable=False)  # first-block, math-explorer, etc.

    # Badge info
    name = Column(String(200), nullable=False)
    description = Column(Text)
    icon = Column(String(10))  # Emoji

    # Progress
    earned = Column(Boolean, default=False)
    earned_date = Column(DateTime)
    progress_current = Column(Integer, default=0)
    progress_target = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="badges")


class WeeklyProgress(Base):
    """Weekly progress tracking"""

    __tablename__ = "weekly_progress"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Week info
    year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)  # 1-52

    # Metrics
    total_activities = Column(Integer, default=0)
    total_time_seconds = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)

    # Daily breakdown
    daily_data = Column(JSON)  # {day: {activities: X, time: Y}}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="weekly_progress")
