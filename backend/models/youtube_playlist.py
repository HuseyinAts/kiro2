"""
Task 99.2: YouTube Playlist Models
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Float,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models.database import Base


# Association table for playlist-video many-to-many
playlist_videos = Table(
    "playlist_videos",
    Base.metadata,
    Column(
        "playlist_id",
        UUID(as_uuid=True),
        ForeignKey("youtube_playlists.id"),
        primary_key=True,
    ),
    Column("video_id", String(20), primary_key=True),
    Column("position", Integer, default=0),
    Column("added_at", DateTime(timezone=True), default=datetime.now),
)


class YouTubePlaylist(Base):
    """
    Task 99.2: YouTube Playlist Model

    Custom playlists created by teachers/students
    """

    __tablename__ = "youtube_playlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Playlist metadata
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # YouTube playlist ID (if synced to YouTube)
    youtube_playlist_id = Column(String(50), nullable=True, unique=True)

    # Creator
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Stats
    video_count = Column(Integer, default=0)
    total_duration = Column(Integer, default=0)  # seconds

    # Visibility
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)  # Featured by admin

    # Tags/categories
    tags = Column(ARRAY(String), default=list)
    subject = Column(String(50), nullable=True, index=True)
    grade_level = Column(String(20), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    creator = relationship("User")

    def __repr__(self):
        return f"<YouTubePlaylist {self.id}: {self.title}>"


class YouTubeVideoQuality(Base):
    """
    Task 99.4: YouTube Video Quality Assessment

    Stores quality scores for videos
    """

    __tablename__ = "youtube_video_quality"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Video ID
    video_id = Column(String(20), unique=True, nullable=False, index=True)

    # Quality scores (0-100)
    educational_score = Column(Float, default=0)
    content_appropriateness = Column(Float, default=0)
    quality_score = Column(Float, default=0)
    engagement_score = Column(Float, default=0)
    overall_score = Column(Float, default=0, index=True)

    # Boolean flags
    has_captions = Column(Boolean, default=False)
    is_hd = Column(Boolean, default=False)
    duration_appropriate = Column(Boolean, default=False)

    # Detailed metrics
    channel_credibility = Column(Float, default=0)
    view_to_like_ratio = Column(Float, default=0)

    # Timestamps
    assessed_at = Column(DateTime(timezone=True), default=datetime.now)
    last_updated = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    def __repr__(self):
        return f"<YouTubeVideoQuality {self.video_id}: {self.overall_score}>"
