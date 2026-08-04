"""
Task 100: Video Analytics Models

Models for video watch tracking, notes, and bookmarks
"""

import uuid
from uuid6 import uuid7
from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from .database import Base


class VideoWatchSession(Base):
    """
    Task 100.1: Video watch session tracking

    Tracks individual watch sessions for analytics
    """

    __tablename__ = "video_watch_sessions"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    # Session info
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    video_id = Column(String(100), nullable=False, index=True)
    video_source = Column(String(20), nullable=False)  # youtube, eba, khan, vimeo

    # Watch metrics
    watch_duration = Column(Integer, default=0)  # Total seconds watched
    video_duration = Column(Integer, nullable=False)  # Total video length
    completion_percentage = Column(Float, default=0.0)  # 0-100

    # Progress tracking
    last_position = Column(Integer, default=0)  # Last watched position (seconds)
    watched_segments = Column(JSONB, default=list)  # [{start: 0, end: 120}, ...]

    # Engagement metrics
    pause_count = Column(Integer, default=0)
    seek_count = Column(Integer, default=0)  # Forward/backward seeks
    playback_speed = Column(Float, default=1.0)

    # Drop-off analysis
    dropped_at = Column(Integer, nullable=True)  # Position where user stopped (seconds)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Session timestamps
    started_at = Column(DateTime(timezone=True), default=datetime.now, index=True)
    last_updated = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user = relationship("User", lazy="selectin")
    notes = relationship(
        "VideoNote", back_populates="session", cascade="all, delete-orphan"
    , lazy="selectin")
    bookmarks = relationship(
        "VideoBookmark", back_populates="session", cascade="all, delete-orphan"
    , lazy="selectin")

    def __repr__(self):
        return f"<VideoWatchSession {self.id}: {self.video_id} - {self.completion_percentage}%>"


class VideoCompletionMilestone(Base):
    """
    Task 100.2: Completion milestone tracking

    Tracks milestone achievements (25%, 50%, 75%, 100%)
    """

    __tablename__ = "video_completion_milestones"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    # User and video
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    video_id = Column(String(100), nullable=False, index=True)
    video_source = Column(String(20), nullable=False)

    # Milestone info
    milestone_percentage = Column(Integer, nullable=False)  # 25, 50, 75, 100
    achieved_at = Column(DateTime(timezone=True), default=datetime.now)

    # Badge awarded
    badge_awarded = Column(Boolean, default=False)
    badge_id = Column(String, ForeignKey("user_badges.id"), nullable=True)

    # Relationships
    user = relationship("User", lazy="selectin")

    __table_args__ = (
        Index(
            "idx_user_video_milestone",
            "user_id",
            "video_id",
            "milestone_percentage",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<VideoCompletionMilestone {self.user_id}: {self.video_id} - {self.milestone_percentage}%>"


class VideoNote(Base):
    """
    Task 100.3: Timestamped video notes

    Notes taken during video playback with timestamps
    """

    __tablename__ = "video_notes"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    # User and video
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    video_id = Column(String(100), nullable=False, index=True)
    video_source = Column(String(20), nullable=False)

    # Session reference
    session_id = Column(
        String, ForeignKey("video_watch_sessions.id"), nullable=True
    )

    # Note content
    content = Column(Text, nullable=False)
    timestamp = Column(
        Integer, nullable=False
    )  # Video position when note was taken (seconds)

    # Note metadata
    is_important = Column(Boolean, default=False)  # Starred/important note
    tags = Column(ARRAY(String), default=list)

    # Note context (optional: video caption at that moment)
    video_caption = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now, index=True)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user = relationship("User", lazy="selectin")
    session = relationship("VideoWatchSession", back_populates="notes", lazy="selectin")

    def __repr__(self):
        return f"<VideoNote {self.id}: {self.video_id}@{self.timestamp}s>"


class VideoBookmark(Base):
    """
    Task 100.4: Video timestamp bookmarks

    Bookmarks for key moments in videos
    """

    __tablename__ = "video_bookmarks"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    # User and video
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    video_id = Column(String(100), nullable=False, index=True)
    video_source = Column(String(20), nullable=False)

    # Session reference
    session_id = Column(
        String, ForeignKey("video_watch_sessions.id"), nullable=True
    )

    # Bookmark info
    timestamp = Column(Integer, nullable=False)  # Video position (seconds)
    title = Column(String(200), nullable=False)  # User-given title
    description = Column(Text, nullable=True)

    # Bookmark type
    bookmark_type = Column(
        String(20), default="manual"
    )  # manual, key_moment, auto_generated

    # Sharing
    is_public = Column(Boolean, default=False)
    share_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now, index=True)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user = relationship("User", lazy="selectin")
    session = relationship("VideoWatchSession", back_populates="bookmarks", lazy="selectin")

    def __repr__(self):
        return f"<VideoBookmark {self.id}: {self.title}@{self.timestamp}s>"


class VideoAnalyticsSummary(Base):
    """
    Aggregated analytics for a user's video watching

    Daily/weekly/monthly summaries
    """

    __tablename__ = "video_analytics_summary"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    # User and period
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    period_type = Column(String(10), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Watch metrics
    total_videos_watched = Column(Integer, default=0)
    total_watch_time = Column(Integer, default=0)  # seconds
    total_videos_completed = Column(Integer, default=0)
    average_completion_rate = Column(Float, default=0.0)

    # Engagement metrics
    total_notes = Column(Integer, default=0)
    total_bookmarks = Column(Integer, default=0)
    average_playback_speed = Column(Float, default=1.0)

    # Source breakdown
    source_breakdown = Column(JSONB, default=dict)  # {youtube: 10, eba: 5, khan: 3}

    # Subject breakdown (if available)
    subject_breakdown = Column(JSONB, default=dict)  # {matematik: 5, fizik: 3}

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("idx_user_period", "user_id", "period_type", "period_start", unique=True),
    )

    def __repr__(self):
        return f"<VideoAnalyticsSummary {self.user_id}: {self.period_type} {self.period_start}>"
