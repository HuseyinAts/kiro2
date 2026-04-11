"""
Video Cache Model
SQLAlchemy model for video_cache table
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class VideoCache(Base):
    """
    Video cache model for storing YouTube video recommendations

    Optimized for fast lookup with composite and individual indexes
    """

    __tablename__ = "video_cache"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Video identification
    video_id = Column(String(100), nullable=False, unique=True, index=True)

    # Video metadata
    title = Column(Text, nullable=False)
    description = Column(Text)
    channel_name = Column(String(255), nullable=False)
    channel_id = Column(String(100), nullable=False)
    thumbnail_url = Column(Text)
    duration = Column(Integer, nullable=False)  # in seconds

    # Classification
    subject = Column(String(50), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False, index=True)
    exam_type = Column(String(20), nullable=False, index=True)
    language = Column(String(10), nullable=False, default="tr", index=True)

    # Quality metrics
    quality_score = Column(Float, nullable=False, default=0.0, index=True)
    relevance_score = Column(Float, nullable=False, default=0.0, index=True)
    language_score = Column(Float, nullable=False, default=0.0)
    difficulty_match = Column(Float, nullable=False, default=0.0)

    # Engagement metrics
    view_count = Column(BigInteger, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)

    # Additional metadata (JSON)
    # Note: Using 'video_metadata' to avoid conflict with SQLAlchemy's metadata attribute
    video_metadata = Column("metadata", JSONB)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow, index=True)

    # Cache management
    access_count = Column(Integer, default=0, index=True)
    cache_ttl = Column(Integer, default=3600)  # TTL in seconds (1 hour default)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "quality_score >= 0 AND quality_score <= 10", name="check_quality_score"
        ),
        CheckConstraint(
            "relevance_score >= 0 AND relevance_score <= 1",
            name="check_relevance_score",
        ),
        CheckConstraint(
            "language_score >= 0 AND language_score <= 1", name="check_language_score"
        ),
        CheckConstraint(
            "difficulty_match >= 0 AND difficulty_match <= 1",
            name="check_difficulty_match",
        ),
        CheckConstraint(
            "difficulty IN ('başlangıç', 'kolay', 'orta', 'zor', 'ileri')",
            name="check_difficulty",
        ),
        CheckConstraint(
            "exam_type IN ('TYT', 'AYT', 'LGS', 'YKS')", name="check_exam_type"
        ),
        CheckConstraint(
            "language IN ('tr', 'en', 'ar', 'other')", name="check_language"
        ),
        # Composite index for common video search queries
        Index(
            "idx_video_search_composite",
            "subject",
            "difficulty",
            "exam_type",
            "language",
            "quality_score",
            postgresql_ops={"quality_score": "DESC"},
        ),
        # Composite index for cache management (LRU eviction)
        Index(
            "idx_video_cache_management",
            "last_accessed",
            "access_count",
            postgresql_ops={"last_accessed": "DESC", "access_count": "DESC"},
        ),
        # Composite index for subject + quality
        Index(
            "idx_video_subject_quality",
            "subject",
            "quality_score",
            postgresql_ops={"quality_score": "DESC"},
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<VideoCache(id={self.id}, video_id={self.video_id}, "
            f"subject={self.subject}, quality_score={self.quality_score})>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "channel_name": self.channel_name,
            "channel_id": self.channel_id,
            "thumbnail_url": self.thumbnail_url,
            "duration": self.duration,
            "subject": self.subject,
            "difficulty": self.difficulty,
            "exam_type": self.exam_type,
            "language": self.language,
            "quality_score": self.quality_score,
            "relevance_score": self.relevance_score,
            "language_score": self.language_score,
            "difficulty_match": self.difficulty_match,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "metadata": self.video_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_updated": self.last_updated.isoformat()
            if self.last_updated
            else None,
            "last_accessed": self.last_accessed.isoformat()
            if self.last_accessed
            else None,
            "access_count": self.access_count,
            "cache_ttl": self.cache_ttl,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoCache":
        """Create model from dictionary"""
        # Remove fields that shouldn't be set directly
        data = data.copy()
        data.pop("id", None)
        data.pop("created_at", None)
        data.pop("last_updated", None)

        return cls(**data)

    def update_access(self) -> None:
        """Update access tracking"""
        self.last_accessed = datetime.now(UTC)
        self.access_count += 1

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if not self.last_updated or not self.cache_ttl:
            return False

        elapsed = (datetime.now(UTC) - self.last_updated).total_seconds()
        return elapsed > self.cache_ttl

    def calculate_overall_score(self) -> float:
        """
        Calculate overall score based on multiple factors

        Weighted average:
        - Quality score: 40%
        - Relevance score: 30%
        - Language score: 20%
        - Difficulty match: 10%
        """
        # Normalize quality_score to 0-1 range
        normalized_quality = self.quality_score / 10.0

        overall = (
            normalized_quality * 0.4
            + self.relevance_score * 0.3
            + self.language_score * 0.2
            + self.difficulty_match * 0.1
        )

        return round(overall, 3)
