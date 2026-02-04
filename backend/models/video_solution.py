"""
Video Çözüm Sistemi Modelleri
Teknofest 2025 Eğitim Eylemci Platformu

Task 72: Video Çözüm Sistemi
- 72.1: Video yükleme (Upload interface, format validation, compression)
- 72.2: Video streaming (HLS/DASH, adaptive bitrate, CDN)
- 72.3: Video transkript (Auto-generated, manual editing, searchable)
- 72.4: Video arama (Transcript-based, topic filtering, timestamp navigation)

Requirements: REQ-14.1, REQ-14.2, REQ-14.3, REQ-14.4, REQ-14.5, REQ-14.6
"""

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


# ============================================================================
# TASK 72.1: Video Format and Status Enums
# ============================================================================


class VideoFormat(enum.Enum):
    """Desteklenen video formatları"""

    MP4 = "mp4"
    WEBM = "webm"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"


class VideoQuality(enum.Enum):
    """Video kalite seviyeleri"""

    SD_360P = "360p"
    SD_480P = "480p"
    HD_720P = "720p"
    HD_1080P = "1080p"
    UHD_4K = "4k"


class VideoProcessingStatus(enum.Enum):
    """Video işleme durumu"""

    PENDING = "pending"  # Yüklendi, işleme bekliyor
    VALIDATING = "validating"  # Format validasyonu yapılıyor
    COMPRESSING = "compressing"  # Sıkıştırma yapılıyor
    TRANSCODING = "transcoding"  # Format dönüşümü yapılıyor
    GENERATING_THUMBNAILS = "generating_thumbnails"  # Thumbnail oluşturuluyor
    GENERATING_TRANSCRIPT = "generating_transcript"  # Transkript oluşturuluyor
    READY = "ready"  # Hazır
    FAILED = "failed"  # Hata oluştu
    ARCHIVED = "archived"  # Arşivlendi


class TranscriptStatus(enum.Enum):
    """Transkript durumu"""

    NOT_GENERATED = "not_generated"
    GENERATING = "generating"
    AUTO_GENERATED = "auto_generated"
    MANUALLY_EDITED = "manually_edited"
    VERIFIED = "verified"


# ============================================================================
# TASK 72.1 & 72.2: Video Solution Model
# ============================================================================


class VideoSolution(Base):
    """
    Soru çözüm videoları
    REQ-14.1, REQ-14.2, REQ-14.3
    """

    __tablename__ = "video_solutions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # ========================================================================
    # İlişkiler
    # ========================================================================
    question_id: Mapped[str] = mapped_column(
        String, ForeignKey("question_bank.id", ondelete="CASCADE"), nullable=False
    )
    uploaded_by: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # ========================================================================
    # TASK 72.1: Video Upload Information
    # ========================================================================
    # Orijinal video bilgileri
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_format: Mapped[VideoFormat] = mapped_column(
        Enum(VideoFormat), nullable=False
    )
    original_size_bytes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Byte cinsinden
    original_duration_seconds: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # REQ-14.2

    # Video URL'leri
    original_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    cdn_url: Mapped[Optional[str]] = mapped_column(String(1000))  # CDN URL

    # Format validation sonuçları
    is_format_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_errors: Mapped[Optional[dict]] = mapped_column(JSON)

    # Compression bilgileri
    compressed_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    compression_ratio: Mapped[Optional[float]] = mapped_column(
        Float
    )  # Orijinal/Sıkıştırılmış

    # ========================================================================
    # TASK 72.2: Streaming Configuration
    # ========================================================================
    # HLS/DASH streaming URL'leri
    hls_playlist_url: Mapped[Optional[str]] = mapped_column(String(1000))
    dash_manifest_url: Mapped[Optional[str]] = mapped_column(String(1000))

    # Adaptive bitrate variants
    available_qualities: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # {quality: url} mapping

    # Streaming istatistikleri
    total_views: Mapped[int] = mapped_column(Integer, default=0)  # REQ-14.4
    total_watch_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    average_completion_rate: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # 0-1 arası

    # ========================================================================
    # TASK 72.3: Video Thumbnail
    # ========================================================================
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000))  # REQ-14.3
    thumbnail_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # ========================================================================
    # Video Metadata
    # ========================================================================
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Video içerik bilgileri
    solution_method: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # Hızlı çözüm, klasik çözüm, vb.
    difficulty_level: Mapped[Optional[str]] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(10), default="tr")

    # Eğitmen bilgileri
    instructor_name: Mapped[Optional[str]] = mapped_column(String(200))
    instructor_title: Mapped[Optional[str]] = mapped_column(String(200))

    # ========================================================================
    # Processing Status
    # ========================================================================
    processing_status: Mapped[VideoProcessingStatus] = mapped_column(
        Enum(VideoProcessingStatus),
        nullable=False,
        default=VideoProcessingStatus.PENDING,
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text)

    # ========================================================================
    # Quality and Moderation
    # ========================================================================
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100 arası
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    moderation_notes: Mapped[Optional[str]] = mapped_column(Text)

    # ========================================================================
    # Accessibility
    # ========================================================================
    has_subtitles: Mapped[bool] = mapped_column(Boolean, default=False)
    has_transcript: Mapped[bool] = mapped_column(Boolean, default=False)
    has_audio_description: Mapped[bool] = mapped_column(Boolean, default=False)

    # ========================================================================
    # System Fields
    # ========================================================================
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ========================================================================
    # Relationships
    # ========================================================================
    transcripts: Mapped[List["VideoTranscript"]] = relationship(
        "VideoTranscript", back_populates="video"
    )
    analytics: Mapped[List["VideoAnalytics"]] = relationship(
        "VideoAnalytics", back_populates="video"
    )

    # ========================================================================
    # Indexes and Constraints
    # ========================================================================
    __table_args__ = (
        CheckConstraint("original_size_bytes > 0", name="check_video_size"),
        CheckConstraint("original_duration_seconds > 0", name="check_video_duration"),
        CheckConstraint(
            "quality_score >= 0.0 AND quality_score <= 100.0",
            name="check_quality_score",
        ),
        CheckConstraint(
            "average_completion_rate >= 0.0 AND average_completion_rate <= 1.0",
            name="check_completion_rate",
        ),
        Index("idx_video_question", "question_id"),
        Index("idx_video_uploader", "uploaded_by"),
        Index("idx_video_status", "processing_status"),
        Index("idx_video_approved", "is_approved"),
        Index("idx_video_active", "is_active"),
        Index("idx_video_created", "created_at"),
    )


# ============================================================================
# TASK 72.3: Video Transcript Model
# ============================================================================


class VideoTranscript(Base):
    """
    Video transkriptleri
    REQ-14.1, REQ-14.2
    """

    __tablename__ = "video_transcripts"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    video_id: Mapped[str] = mapped_column(
        String, ForeignKey("video_solutions.id", ondelete="CASCADE"), nullable=False
    )

    # ========================================================================
    # Transcript Content
    # ========================================================================
    language: Mapped[str] = mapped_column(String(10), default="tr")

    # Tam transkript metni (searchable)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Zaman damgalı transkript (JSON format)
    # [{"start": 0.0, "end": 5.2, "text": "Merhaba..."}, ...]
    timestamped_segments: Mapped[dict] = mapped_column(JSON, nullable=False)

    # ========================================================================
    # Generation Information
    # ========================================================================
    transcript_status: Mapped[TranscriptStatus] = mapped_column(
        Enum(TranscriptStatus), nullable=False, default=TranscriptStatus.NOT_GENERATED
    )

    # Auto-generation bilgileri
    auto_generated_by: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # Whisper, Google Speech, vb.
    auto_generation_confidence: Mapped[Optional[float]] = mapped_column(
        Float
    )  # 0-1 arası
    auto_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Manual editing bilgileri
    manually_edited_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL")
    )
    manually_edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    edit_count: Mapped[int] = mapped_column(Integer, default=0)

    # Verification bilgileri
    verified_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL")
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ========================================================================
    # Search and Analysis
    # ========================================================================
    # Anahtar kelimeler (otomatik çıkarılmış)
    keywords: Mapped[Optional[list]] = mapped_column(JSON)

    # Konu etiketleri
    topics: Mapped[Optional[list]] = mapped_column(JSON)

    # Matematik formülleri (LaTeX format)
    math_formulas: Mapped[Optional[list]] = mapped_column(JSON)

    # ========================================================================
    # Quality Metrics
    # ========================================================================
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    average_words_per_minute: Mapped[float] = mapped_column(Float, default=0.0)
    readability_score: Mapped[float] = mapped_column(Float, default=0.0)

    # ========================================================================
    # System Fields
    # ========================================================================
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ========================================================================
    # Relationships
    # ========================================================================
    video: Mapped["VideoSolution"] = relationship(
        "VideoSolution", back_populates="transcripts"
    )

    # ========================================================================
    # Indexes and Constraints
    # ========================================================================
    __table_args__ = (
        CheckConstraint("word_count >= 0", name="check_word_count"),
        CheckConstraint("average_words_per_minute >= 0", name="check_wpm"),
        CheckConstraint(
            "readability_score >= 0.0 AND readability_score <= 100.0",
            name="check_readability",
        ),
        Index("idx_transcript_video", "video_id"),
        Index("idx_transcript_language", "language"),
        Index("idx_transcript_status", "transcript_status"),
        Index("idx_transcript_active", "is_active"),
        # Full-text search index (PostgreSQL specific)
        # Index('idx_transcript_fulltext', 'full_text', postgresql_using='gin'),
    )


# ============================================================================
# TASK 72.4: Video Analytics Model
# ============================================================================


class VideoAnalytics(Base):
    """
    Video izleme analitiği
    REQ-14.4, REQ-14.5
    """

    __tablename__ = "video_analytics"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    video_id: Mapped[str] = mapped_column(
        String, ForeignKey("video_solutions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )

    # ========================================================================
    # Viewing Session
    # ========================================================================
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # İzleme bilgileri
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    watch_duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    completion_percentage: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # 0-100 arası

    # Kullanıcı etkileşimi
    paused_count: Mapped[int] = mapped_column(Integer, default=0)
    seeked_count: Mapped[int] = mapped_column(Integer, default=0)
    playback_speed: Mapped[float] = mapped_column(
        Float, default=1.0
    )  # 0.5x, 1x, 1.5x, 2x

    # Kalite seçimi
    selected_quality: Mapped[Optional[str]] = mapped_column(String(20))
    quality_changes: Mapped[int] = mapped_column(Integer, default=0)

    # ========================================================================
    # Device and Network
    # ========================================================================
    device_type: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # mobile, tablet, desktop
    browser: Mapped[Optional[str]] = mapped_column(String(100))
    os: Mapped[Optional[str]] = mapped_column(String(100))

    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    country: Mapped[Optional[str]] = mapped_column(String(2))  # ISO country code

    # Network quality
    average_bandwidth_mbps: Mapped[Optional[float]] = mapped_column(Float)
    buffering_count: Mapped[int] = mapped_column(Integer, default=0)
    buffering_duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # ========================================================================
    # Engagement Metrics
    # ========================================================================
    # Kullanıcı video hakkında ne yaptı
    liked: Mapped[bool] = mapped_column(Boolean, default=False)
    bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)
    shared: Mapped[bool] = mapped_column(Boolean, default=False)
    reported: Mapped[bool] = mapped_column(Boolean, default=False)

    # Faydalı buldu mu
    helpful_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 arası

    # ========================================================================
    # System Fields
    # ========================================================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ========================================================================
    # Relationships
    # ========================================================================
    video: Mapped["VideoSolution"] = relationship(
        "VideoSolution", back_populates="analytics"
    )

    # ========================================================================
    # Indexes and Constraints
    # ========================================================================
    __table_args__ = (
        CheckConstraint("watch_duration_seconds >= 0", name="check_watch_duration"),
        CheckConstraint(
            "completion_percentage >= 0.0 AND completion_percentage <= 100.0",
            name="check_completion",
        ),
        CheckConstraint("playback_speed > 0", name="check_playback_speed"),
        CheckConstraint(
            "helpful_rating IS NULL OR (helpful_rating >= 1 AND helpful_rating <= 5)",
            name="check_rating",
        ),
        Index("idx_analytics_video", "video_id"),
        Index("idx_analytics_user", "user_id"),
        Index("idx_analytics_session", "session_id"),
        Index("idx_analytics_created", "created_at"),
        Index("idx_analytics_completion", "completion_percentage"),
    )


# ============================================================================
# Helper Functions
# ============================================================================


def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
    """
    Sıkıştırma oranını hesapla

    Args:
        original_size: Orijinal dosya boyutu (bytes)
        compressed_size: Sıkıştırılmış dosya boyutu (bytes)

    Returns:
        float: Sıkıştırma oranı (örn: 2.5 = %60 küçültme)
    """
    if compressed_size == 0:
        return 0.0
    return original_size / compressed_size


def format_duration(seconds: float) -> str:
    """
    Saniyeyi HH:MM:SS formatına çevir

    Args:
        seconds: Saniye cinsinden süre

    Returns:
        str: Formatlanmış süre
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def is_valid_video_format(filename: str) -> tuple[bool, Optional[VideoFormat]]:
    """
    Dosya adından video formatını kontrol et

    Args:
        filename: Dosya adı

    Returns:
        tuple: (geçerli mi, format enum)
    """
    extension = filename.lower().split(".")[-1]

    format_map = {
        "mp4": VideoFormat.MP4,
        "webm": VideoFormat.WEBM,
        "avi": VideoFormat.AVI,
        "mov": VideoFormat.MOV,
        "mkv": VideoFormat.MKV,
    }

    video_format = format_map.get(extension)
    return (video_format is not None, video_format)
