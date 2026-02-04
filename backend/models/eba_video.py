"""
Task 97: EBA TV Database Models
Video catalog and watch tracking models
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
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models.database import Base


class EBAVideo(Base):
    """
    Task 97.2: EBA Video Catalog Model

    Stores EBA TV video metadata synced from MEB API
    """

    __tablename__ = "eba_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # EBA specific IDs
    eba_video_id = Column(String(100), unique=True, nullable=False, index=True)
    meb_content_id = Column(String(100), nullable=True)  # MEB content ID

    # Video metadata
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=False)
    thumbnail_url = Column(String(1000), nullable=True)
    video_url = Column(String(1000), nullable=False)

    # Classification (Task 97.3: Subject-based filtering)
    subject = Column(String(50), nullable=False, index=True)  # matematik, fizik, etc.
    grade_level = Column(
        String(20), nullable=False, index=True
    )  # ortaokul_8, lise_11, etc.
    topic = Column(String(200), nullable=True)  # "Sayılar ve İşlemler"
    subtopics = Column(
        ARRAY(String), nullable=True
    )  # ["Kareköklü Sayılar", "Karekök Alma"]
    keywords = Column(ARRAY(String), nullable=True)  # For search

    # Curriculum alignment
    kazanim_codes = Column(ARRAY(String), nullable=True)  # ["8.1.2.1", "8.1.2.2"]
    curriculum_aligned = Column(Boolean, default=True)

    # Video properties
    quality = Column(String(10), default="720p")  # 360p, 480p, 720p, 1080p
    has_turkish_subtitle = Column(Boolean, default=True)

    # Analytics from EBA
    view_count = Column(Integer, default=0)  # From EBA API
    publish_date = Column(DateTime(timezone=True), nullable=True)

    # Sync metadata
    last_synced_at = Column(DateTime(timezone=True), default=datetime.now)
    created_at = Column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    watch_sessions = relationship("EBAVideoWatch", back_populates="video")

    def __repr__(self):
        return f"<EBAVideo {self.eba_video_id}: {self.title}>"


class EBAVideoWatch(Base):
    """
    Task 97.4: Watch Progress Tracking Model

    Tracks user video watch sessions
    - Resume functionality (kaldığın yerden devam et)
    - Completion tracking
    - Analytics data
    """

    __tablename__ = "eba_video_watches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    eba_video_id = Column(
        UUID(as_uuid=True), ForeignKey("eba_videos.id"), nullable=False, index=True
    )

    # Watch session info
    session_start = Column(DateTime(timezone=True), default=datetime.now)
    session_end = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Progress tracking
    last_position = Column(Integer, default=0)  # Last watched position in seconds
    watch_percentage = Column(Float, default=0.0)  # Percentage of video watched
    completed = Column(Boolean, default=False)  # True if watched >= 90%
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Analytics
    total_watch_time = Column(Integer, default=0)  # Total time spent watching (seconds)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    video = relationship("EBAVideo", back_populates="watch_sessions")
    user = relationship("User")

    def __repr__(self):
        return f"<EBAVideoWatch user={self.user_id} video={self.eba_video_id} progress={self.watch_percentage:.1f}%>"


class EBASubjectTaxonomy(Base):
    """
    Task 97.3: Subject Taxonomy Model

    Stores subject -> topic hierarchy from EBA
    """

    __tablename__ = "eba_subject_taxonomy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    subject = Column(String(50), nullable=False, index=True)
    topic = Column(String(200), nullable=False)
    subtopics = Column(ARRAY(String), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    def __repr__(self):
        return f"<EBASubjectTaxonomy {self.subject} -> {self.topic}>"
