"""
SQLAlchemy ORM EBA TV Content Models
database.py'den ayrıştırıldı (2026-01-10)
"""

import uuid
from uuid6 import uuid7
from datetime import date, datetime

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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .enums_db import (
    EBAContentCategory,
    EBAGradeLevel,
    EBAVideoQuality,
    QuestionDifficulty,
)


class EBAVideo(Base):
    """EBA TV video modeli"""

    __tablename__ = "eba_videos"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes >= 1 AND duration_minutes <= 180",
            name="check_eba_duration",
        ),
        CheckConstraint(
            "quality_score >= 0.0 AND quality_score <= 10.0",
            name="check_eba_quality_score",
        ),
        Index("idx_eba_video_category", "category"),
        Index("idx_eba_video_grade", "grade_level"),
        Index("idx_eba_video_difficulty", "difficulty_level"),
        Index("idx_eba_video_quality", "quality_score"),
        Index("idx_eba_video_moderation", "moderation_status"),
        Index("idx_eba_video_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Video bilgileri
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, deferred=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Kategorilendirme
    category: Mapped[EBAContentCategory] = mapped_column(
        Enum(EBAContentCategory), nullable=False
    )
    grade_level: Mapped[EBAGradeLevel] = mapped_column(
        Enum(EBAGradeLevel), nullable=False
    )
    subject_topics: Mapped[dict | None] = mapped_column(JSON, deferred=True)
    difficulty_level: Mapped[QuestionDifficulty] = mapped_column(
        Enum(QuestionDifficulty), nullable=False
    )

    # URL ve medya
    video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    transcript: Mapped[str | None] = mapped_column(Text, deferred=True)

    # Kalite ve değerlendirme
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_category: Mapped[EBAVideoQuality] = mapped_column(
        Enum(EBAVideoQuality), default=EBAVideoQuality.MEDIUM
    )
    curriculum_alignment: Mapped[dict | None] = mapped_column(JSON, deferred=True)

    # Erişilebilirlik
    accessibility_features: Mapped[dict | None] = mapped_column(JSON, deferred=True)
    has_subtitles: Mapped[bool] = mapped_column(Boolean, default=False)
    has_transcript: Mapped[bool] = mapped_column(Boolean, default=False)

    # İstatistikler
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0)

    # Kalite analizi detayları
    duration_score: Mapped[float] = mapped_column(Float, default=0.0)
    title_clarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    description_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    curriculum_alignment_score: Mapped[float] = mapped_column(Float, default=0.0)
    accessibility_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Moderasyon
    moderation_status: Mapped[str] = mapped_column(String(50), default="pending")
    moderated_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE")
    )
    moderation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    moderation_notes: Mapped[str | None] = mapped_column(Text, deferred=True)

    # Sistem alanları
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    usage_analytics: Mapped[list["EBAVideoUsage"]] = relationship(
        "EBAVideoUsage", back_populates="video"
    , lazy="selectin")
    recommendations: Mapped[list["EBAVideoRecommendation"]] = relationship(
        "EBAVideoRecommendation", back_populates="video"
    , lazy="selectin")


class EBAVideoUsage(Base):
    """EBA video kullanım istatistikleri"""

    __tablename__ = "eba_video_usage"
    __table_args__ = (
        CheckConstraint(
            "completion_percentage >= 0.0 AND completion_percentage <= 100.0",
            name="check_eba_completion",
        ),
        CheckConstraint(
            "user_rating IS NULL OR (user_rating >= 1.0 AND user_rating <= 5.0)",
            name="check_eba_rating",
        ),
        Index("idx_eba_usage_video", "video_id"),
        Index("idx_eba_usage_student", "student_id"),
        Index("idx_eba_usage_started", "started_at"),
        UniqueConstraint(
            "video_id", "student_id", "started_at", name="uq_eba_video_usage"
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    video_id: Mapped[str] = mapped_column(String, ForeignKey("eba_videos.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(String, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Kullanım bilgileri
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    watch_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Etkileşim
    paused_count: Mapped[int] = mapped_column(Integer, default=0)
    rewound_count: Mapped[int] = mapped_column(Integer, default=0)
    fast_forwarded_count: Mapped[int] = mapped_column(Integer, default=0)

    # Değerlendirme
    user_rating: Mapped[float | None] = mapped_column(Float)
    user_feedback: Mapped[str | None] = mapped_column(Text, deferred=True)

    # Öğrenme etkisi
    pre_knowledge_score: Mapped[float | None] = mapped_column(Float)
    post_knowledge_score: Mapped[float | None] = mapped_column(Float)
    learning_effectiveness: Mapped[float | None] = mapped_column(Float)

    # İlişkiler
    video: Mapped["EBAVideo"] = relationship(
        "EBAVideo", back_populates="usage_analytics"
    , lazy="selectin")


class EBAVideoRecommendation(Base):
    """EBA video önerileri"""

    __tablename__ = "eba_video_recommendations"
    __table_args__ = (
        CheckConstraint(
            "recommendation_score >= 0.0 AND recommendation_score <= 10.0",
            name="check_eba_rec_score",
        ),
        Index("idx_eba_rec_video", "video_id"),
        Index("idx_eba_rec_student", "student_id"),
        Index("idx_eba_rec_score", "recommendation_score"),
        Index("idx_eba_rec_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))
    organization_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        server_default="org_legacy_default",
        index=True,
    )
    video_id: Mapped[str] = mapped_column(String, ForeignKey("eba_videos.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(String, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # Öneri bilgileri
    recommendation_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation_reason: Mapped[str] = mapped_column(String(200), nullable=False)
    recommendation_category: Mapped[str] = mapped_column(String(100), nullable=False)

    # Kişiselleştirme faktörleri
    learning_style_match: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_appropriateness: Mapped[float] = mapped_column(Float, default=0.0)
    curriculum_relevance: Mapped[float] = mapped_column(Float, default=0.0)

    # Durum takibi
    shown_to_student: Mapped[bool] = mapped_column(Boolean, default=False)
    clicked_by_student: Mapped[bool] = mapped_column(Boolean, default=False)
    watched_by_student: Mapped[bool] = mapped_column(Boolean, default=False)

    # Zaman damgaları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    shown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # İlişkiler
    video: Mapped["EBAVideo"] = relationship(
        "EBAVideo", back_populates="recommendations"
    , lazy="selectin")


class EBAContentCollection(Base):
    """EBA içerik koleksiyonları"""

    __tablename__ = "eba_content_collections"
    __table_args__ = (
        Index("idx_eba_collection_category", "category"),
        Index("idx_eba_collection_grade", "grade_level"),
        Index("idx_eba_collection_featured", "is_featured"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Koleksiyon bilgileri
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, deferred=True)
    category: Mapped[EBAContentCategory] = mapped_column(
        Enum(EBAContentCategory), nullable=False
    )
    grade_level: Mapped[EBAGradeLevel] = mapped_column(
        Enum(EBAGradeLevel), nullable=False
    )

    # Video listesi (JSON array of video IDs)
    video_ids: Mapped[dict | None] = mapped_column(JSON, deferred=True)

    # İstatistikler
    total_videos: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    average_quality_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Durum
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)

    # Sistem alanları
    created_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EBAContentAnalytics(Base):
    """EBA içerik analitikleri"""

    __tablename__ = "eba_content_analytics"
    __table_args__ = (
        UniqueConstraint(
            "analysis_date", "category", "grade_level", name="uq_eba_analytics"
        ),
        Index("idx_eba_analytics_date", "analysis_date"),
        Index("idx_eba_analytics_category", "category"),
        Index("idx_eba_analytics_grade", "grade_level"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Analiz dönemi
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[EBAContentCategory] = mapped_column(
        Enum(EBAContentCategory), nullable=False
    )
    grade_level: Mapped[EBAGradeLevel] = mapped_column(
        Enum(EBAGradeLevel), nullable=False
    )

    # Kullanım metrikleri
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    unique_viewers: Mapped[int] = mapped_column(Integer, default=0)
    total_watch_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    average_completion_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Kalite metrikleri
    average_user_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_ratings: Mapped[int] = mapped_column(Integer, default=0)
    average_learning_effectiveness: Mapped[float] = mapped_column(Float, default=0.0)

    # Popülerlik metrikleri
    trending_score: Mapped[float] = mapped_column(Float, default=0.0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Sistem alanları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
