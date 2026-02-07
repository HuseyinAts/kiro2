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
    Float,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base

# Re-export EBAVideo from canonical source (models/eba_models.py)
# to avoid duplicate class registration in SQLAlchemy mapper registry.
# The comprehensive EBAVideo model lives in eba_models.py.
from .eba_models import EBAVideo  # noqa: F401


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
    video = relationship("EBAVideo")
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
