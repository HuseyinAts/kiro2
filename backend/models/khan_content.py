"""
Task 98: Khan Academy Database Models
Content catalog, progress tracking, and certificates
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from .database import Base


class KhanContent(Base):
    """
    Task 98.2: Khan Academy Content Model

    Stores Turkish content from Khan Academy
    """

    __tablename__ = "khan_contents"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    # Khan Academy IDs
    khan_content_id = Column(String(100), unique=True, nullable=False, index=True)

    # Content metadata
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(
        String(20), nullable=False, index=True
    )  # video, exercise, article

    # Classification
    subject = Column(String(50), nullable=False, index=True)  # math, science, etc.
    topic = Column(String(200), nullable=True)

    # Video specific
    video_url = Column(String(1000), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    thumbnail_url = Column(String(1000), nullable=True)

    # Exercise specific
    exercise_url = Column(String(1000), nullable=True)
    problem_count = Column(Integer, nullable=True)

    # Language
    language = Column(String(5), default="tr", index=True)  # tr = Turkish

    # Metadata
    difficulty_level = Column(
        String(20), nullable=True
    )  # beginner, intermediate, advanced
    last_synced_at = Column(DateTime(timezone=True), default=datetime.now)
    created_at = Column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    user_progress = relationship("KhanUserProgress", back_populates="content")

    def __repr__(self):
        return f"<KhanContent {self.khan_content_id}: {self.title}>"


class KhanUserProgress(Base):
    """
    Task 98.3: Khan Academy User Progress Model

    Tracks user progress with bidirectional sync
    """

    __tablename__ = "khan_user_progress"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    khan_user_id = Column(
        String(100), nullable=True, index=True
    )  # Khan Academy user ID
    khan_content_id = Column(
        String, ForeignKey("khan_contents.id"), nullable=False, index=True
    )

    # Content type
    content_type = Column(String(20), nullable=False)  # video, exercise

    # Progress timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed = Column(DateTime(timezone=True), nullable=True)

    # Video progress
    video_seconds_watched = Column(Integer, default=0)
    video_completed = Column(Boolean, default=False)

    # Exercise progress
    problems_attempted = Column(Integer, default=0)
    problems_correct = Column(Integer, default=0)
    proficiency_level = Column(String(20), nullable=True)  # practicing, mastered, etc.

    # Gamification
    energy_points = Column(Integer, default=0)  # Khan Academy points
    badges_earned = Column(ARRAY(String), default=list)  # Badge names

    # Sync metadata
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    sync_conflict = Column(Boolean, default=False)  # True if merge conflict detected
    created_at = Column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    content = relationship("KhanContent", back_populates="user_progress")
    user = relationship("User")

    def __repr__(self):
        return f"<KhanUserProgress user={self.user_id} content={self.khan_content_id} progress={self.proficiency_level}>"


class KhanCertificate(Base):
    """
    Task 98.4: Khan Academy Certificate/Badge Model

    Stores user's earned badges and certificates
    """

    __tablename__ = "khan_certificates"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    khan_user_id = Column(String(100), nullable=True, index=True)

    # Badge details
    badge_id = Column(String(100), nullable=False, unique=True)
    badge_name = Column(String(200), nullable=False)
    badge_category = Column(
        String(50), nullable=False, index=True
    )  # mastery, challenge, etc.
    description = Column(Text, nullable=True)
    icon_url = Column(String(1000), nullable=True)

    # Verification
    verification_url = Column(String(1000), nullable=True)
    earned_at = Column(DateTime(timezone=True), nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    last_synced_at = Column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<KhanCertificate user={self.user_id} badge={self.badge_name}>"


class KhanOAuthToken(Base):
    """
    Task 98.1: Khan Academy OAuth Token Storage

    Stores OAuth tokens for Khan Academy API access
    """

    __tablename__ = "khan_oauth_tokens"

    id = Column(String, primary_key=True, default=uuid.uuid4)

    # User association
    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    khan_user_id = Column(String(100), nullable=True)  # Khan Academy user ID

    # OAuth tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(20), default="Bearer")

    # Token expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)
    issued_at = Column(DateTime(timezone=True), default=datetime.now)

    # Scopes
    scopes = Column(
        ARRAY(String), default=list
    )  # ["user:read", "progress:read", "badges:read"]

    # Status
    is_active = Column(Boolean, default=True)
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<KhanOAuthToken user={self.user_id} expires={self.expires_at}>"
