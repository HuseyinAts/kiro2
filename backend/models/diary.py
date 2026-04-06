"""
Claude Diary Plugin - Database Models

Agent gunluk tutma ve reflection sistemi icin veritabani modelleri.
REQ-1 ile REQ-8 arasindaki gereksinimleri destekler.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    Text,
    Date,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from .database import Base


# ============================================================
# Enumerations
# ============================================================


class InsightCategory(str, Enum):
    """Insight kategorileri (REQ-2.6)"""
    TECHNICAL = "technical"
    PROCESS = "process"
    COMMUNICATION = "communication"


class GoalStatus(str, Enum):
    """Hedef durumlari (REQ-6)"""
    ACTIVE = "active"
    COMPLETED = "completed"
    AT_RISK = "at_risk"
    CANCELLED = "cancelled"


class ReflectionDepth(str, Enum):
    """Yansitma derinligi (REQ-3.6)"""
    SURFACE = "surface"
    MODERATE = "moderate"
    DEEP = "deep"


class ExportFormat(str, Enum):
    """Export formatlari (REQ-8.1)"""
    MARKDOWN = "markdown"
    PDF = "pdf"
    JSON = "json"


# ============================================================
# REQ-1: Daily Summary - DiaryEntry Model
# ============================================================


class DiaryEntry(Base):
    """
    Gunluk kaydi modeli (REQ-1)

    Gunluk aktivite ozetlerini saklar:
    - Task agregasyonu (success/failure count)
    - Key learnings (onemli ogrenimler)
    - Highlights (one cikan tasklar)
    - Challenges (karsilasilan zorluklar)
    """

    __tablename__ = "diary_entries"

    id = Column(String, primary_key=True, default=uuid4)
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Tarih (benzersiz - gun basina tek kayit)
    date = Column(Date, nullable=False, index=True)

    # Task istatistikleri (REQ-1.1, REQ-1.2)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    total_tasks = Column(Integer, default=0)
    total_duration_minutes = Column(Integer, default=0)

    # Icerik (REQ-1.2, REQ-1.3, REQ-1.4)
    highlights = Column(JSONB, default=list)  # List[str] - One cikan tasklar
    learnings = Column(JSONB, default=list)   # List[str] - Key learnings (top 3)
    challenges = Column(JSONB, default=list)  # List[str] - Karsilasilan zorluklar

    # Ham task verileri
    tasks_data = Column(JSONB, default=list)  # Tum task detaylari

    # Markdown ozet (REQ-1.5)
    markdown_content = Column(Text)

    # Dosya yolu (REQ-1.6)
    file_path = Column(String(512))  # .kiro/diary/YYYY-MM-DD.md

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    insights = relationship(
        "Insight",
        back_populates="diary_entry",
        cascade="all, delete-orphan"
    )
    reflections = relationship(
        "Reflection",
        back_populates="diary_entry",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_diary_entries_user", "user_id"),
        Index("idx_diary_entries_date", "date"),
        Index("idx_diary_entries_user_date", "user_id", "date", unique=True),
    )

    @property
    def success_rate(self) -> float:
        """Basari orani hesapla"""
        if self.total_tasks == 0:
            return 0.0
        return (self.success_count / self.total_tasks) * 100


# ============================================================
# REQ-2: Insight Extraction - Insight Model
# ============================================================


class Insight(Base):
    """
    Icgoru modeli (REQ-2)

    Pattern detection ve insight generation:
    - Recurring success factors (REQ-2.1)
    - Failure root causes (REQ-2.2)
    - Correlations (REQ-2.3)
    - Confidence scoring >= 0.8 (REQ-2.4)
    - Actionable recommendations (REQ-2.5)
    - Categorization (REQ-2.6)
    """

    __tablename__ = "insights"

    id = Column(String, primary_key=True, default=uuid4)
    diary_entry_id = Column(
        String,
        ForeignKey("diary_entries.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Kategori (REQ-2.6)
    category = Column(
        SQLEnum(InsightCategory),
        nullable=False,
        default=InsightCategory.TECHNICAL
    )

    # Pattern ve analiz (REQ-2.1, REQ-2.2, REQ-2.3)
    pattern = Column(Text, nullable=False)  # Tespit edilen pattern
    root_cause = Column(Text)  # Root cause (failure icin)
    correlation = Column(Text)  # Cause-effect iliskisi

    # Confidence scoring (REQ-2.4) - Minimum 0.8
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    evidence_count = Column(Integer, default=1)  # Kanit sayisi

    # Recommendation (REQ-2.5)
    recommendation = Column(Text, nullable=False)
    priority = Column(Integer, default=1)  # 1=yuksek, 2=orta, 3=dusuk

    # Metadata
    evidence_data = Column(JSONB, default=list)  # Kanit detaylari
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    diary_entry = relationship("DiaryEntry", back_populates="insights")

    # Indexes
    __table_args__ = (
        Index("idx_insights_diary_entry", "diary_entry_id"),
        Index("idx_insights_user", "user_id"),
        Index("idx_insights_category", "category"),
        Index("idx_insights_confidence", "confidence"),
    )


# ============================================================
# REQ-3: Reflection Prompts - Reflection Model
# ============================================================


class Reflection(Base):
    """
    Yansitma modeli (REQ-3)

    Guided reflection questions ve responses:
    - "What went well?" (REQ-3.2)
    - "What could improve?" (REQ-3.3)
    - "What did I learn?" (REQ-3.4)
    - "What will I do differently?" (REQ-3.5)
    - Depth measurement (REQ-3.6)
    """

    __tablename__ = "reflections"

    id = Column(String, primary_key=True, default=uuid4)
    diary_entry_id = Column(
        String,
        ForeignKey("diary_entries.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Reflection sorulari ve yanitlari
    what_went_well = Column(Text)       # REQ-3.2
    what_could_improve = Column(Text)   # REQ-3.3
    what_did_i_learn = Column(Text)     # REQ-3.4
    what_will_i_do_differently = Column(Text)  # REQ-3.5

    # Additional notes
    additional_notes = Column(Text)

    # Depth measurement (REQ-3.6)
    depth = Column(
        SQLEnum(ReflectionDepth),
        default=ReflectionDepth.SURFACE
    )
    depth_score = Column(Float, default=0.0)  # 0.0 - 1.0

    # Analysis
    extracted_learnings = Column(JSONB, default=list)
    action_items = Column(JSONB, default=list)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    diary_entry = relationship("DiaryEntry", back_populates="reflections")

    # Indexes
    __table_args__ = (
        Index("idx_reflections_diary_entry", "diary_entry_id"),
        Index("idx_reflections_user", "user_id"),
        Index("idx_reflections_depth", "depth"),
    )


# ============================================================
# REQ-4: Learning Journal - LearningEntry Model
# ============================================================


class LearningEntry(Base):
    """
    Ogrenme gunlugu modeli (REQ-4)

    Knowledge tracking:
    - Knowledge entry creation (REQ-4.1)
    - Categorization with tags (REQ-4.2)
    - Concept linking (REQ-4.3)
    - Spaced repetition (REQ-4.4)
    - Gap detection (REQ-4.5)
    """

    __tablename__ = "learning_entries"

    id = Column(String, primary_key=True, default=uuid4)
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Content (REQ-4.1)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)  # Kisa ozet

    # Tags (REQ-4.2) - domain, skill, tool
    tags = Column(ARRAY(String), default=list)
    domain = Column(String(100))  # e.g., "backend", "frontend", "devops"
    skill_type = Column(String(100))  # e.g., "python", "react", "sql"

    # Related concepts (REQ-4.3) - Knowledge graph edges
    related_concepts = Column(ARRAY(String), default=list)
    concept_links = Column(JSONB, default=list)  # [{concept_id, relationship_type}]

    # Spaced repetition (REQ-4.4)
    next_review = Column(DateTime(timezone=True))
    review_count = Column(Integer, default=0)
    last_review = Column(DateTime(timezone=True))
    retention_score = Column(Float, default=0.0)  # 0.0 - 1.0
    ease_factor = Column(Float, default=2.5)  # FSRS ease factor
    interval_days = Column(Integer, default=1)  # Current interval

    # Importance and mastery
    importance = Column(Integer, default=1)  # 1-5
    mastery_level = Column(Float, default=0.0)  # 0.0 - 1.0

    # Source
    source_type = Column(String(50))  # "task", "research", "course", "book"
    source_reference = Column(String(512))

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Indexes
    __table_args__ = (
        Index("idx_learning_entries_user", "user_id"),
        Index("idx_learning_entries_next_review", "next_review"),
        Index("idx_learning_entries_domain", "domain"),
        Index("idx_learning_entries_tags", "tags", postgresql_using="gin"),
    )


# ============================================================
# REQ-5: Emotional State Tracking - EmotionalState Model
# ============================================================


class EmotionalState(Base):
    """
    Duygusal durum modeli (REQ-5)

    Agent state awareness:
    - Confidence level (REQ-5.1)
    - Frustration detection (REQ-5.2)
    - Flow state identification (REQ-5.3)
    - Emotional pattern analysis (REQ-5.4)
    - Self-awareness scoring (REQ-5.6)
    """

    __tablename__ = "emotional_states"

    id = Column(String, primary_key=True, default=uuid4)
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Confidence level (REQ-5.1) - 1 to 10
    confidence_level = Column(Integer, nullable=False)  # 1-10

    # Frustration metrics (REQ-5.2)
    frustration_score = Column(Float, default=0.0)  # 0.0 - 1.0
    retry_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)

    # Flow state (REQ-5.3)
    flow_state = Column(Boolean, default=False)
    productivity_score = Column(Float, default=0.0)  # 0.0 - 1.0
    tasks_completed = Column(Integer, default=0)

    # Trigger factors (REQ-5.4)
    trigger_factors = Column(JSONB, default=dict)
    task_type = Column(String(100))  # Task type that triggered this state

    # Self-awareness (REQ-5.6)
    self_awareness_score = Column(Float, default=0.0)  # 0.0 - 100.0
    predicted_state = Column(String(50))  # What was predicted
    actual_state = Column(String(50))  # What actually happened

    # Context
    context_notes = Column(Text)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Indexes
    __table_args__ = (
        Index("idx_emotional_states_user", "user_id"),
        Index("idx_emotional_states_timestamp", "timestamp"),
        Index("idx_emotional_states_flow", "flow_state"),
        Index("idx_emotional_states_confidence", "confidence_level"),
    )


# ============================================================
# REQ-6: Goal Tracking - Goal Model
# ============================================================


class Goal(Base):
    """
    Hedef modeli (REQ-6)

    Goal tracking:
    - SMART validation (REQ-6.1)
    - Progress tracking (REQ-6.2)
    - Milestone celebration (REQ-6.3)
    - Risk detection (REQ-6.4)
    - Goal adjustment (REQ-6.5)
    - Retrospective (REQ-6.6)
    """

    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=uuid4)
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Goal info (REQ-6.1 - SMART)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # SMART criteria
    specific = Column(Text)  # What exactly?
    measurable = Column(Text)  # How to measure?
    achievable = Column(Text)  # Is it realistic?
    relevant = Column(Text)  # Why does it matter?
    time_bound = Column(DateTime(timezone=True))  # Deadline

    # Progress (REQ-6.2)
    progress = Column(Integer, default=0)  # 0-100
    current_value = Column(Float, default=0.0)
    target_value = Column(Float, nullable=False)
    unit = Column(String(50))  # e.g., "tasks", "hours", "points"

    # Status
    status = Column(
        SQLEnum(GoalStatus),
        default=GoalStatus.ACTIVE
    )

    # Milestones (REQ-6.3)
    milestones = Column(JSONB, default=list)  # [{percentage, title, achieved, achieved_at}]
    milestone_celebrations = Column(JSONB, default=list)

    # Risk detection (REQ-6.4)
    is_at_risk = Column(Boolean, default=False)
    risk_factors = Column(JSONB, default=list)
    predicted_completion = Column(DateTime(timezone=True))
    velocity = Column(Float, default=0.0)  # Progress per day

    # Adjustments (REQ-6.5)
    adjustments = Column(JSONB, default=list)  # [{date, reason, old_value, new_value}]

    # Retrospective (REQ-6.6)
    lessons_learned = Column(JSONB, default=list)
    success_factors = Column(JSONB, default=list)
    challenges_faced = Column(JSONB, default=list)

    # Dates
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    target_date = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    # Metadata
    category = Column(String(100))  # e.g., "learning", "productivity", "health"
    priority = Column(Integer, default=2)  # 1=high, 2=medium, 3=low
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Indexes
    __table_args__ = (
        Index("idx_goals_user", "user_id"),
        Index("idx_goals_status", "status"),
        Index("idx_goals_target_date", "target_date"),
        Index("idx_goals_at_risk", "is_at_risk"),
    )

    @property
    def days_remaining(self) -> int:
        """Kalan gun sayisi"""
        if self.target_date is None:
            return 0
        delta = self.target_date - datetime.now(self.target_date.tzinfo)
        return max(0, delta.days)

    @property
    def is_overdue(self) -> bool:
        """Gecikme durumu"""
        if self.target_date is None:
            return False
        return datetime.now(self.target_date.tzinfo) > self.target_date


# ============================================================
# REQ-7: Peer Comparison - PeerComparison Model
# ============================================================


class PeerComparison(Base):
    """
    Akran karsilastirma modeli (REQ-7)

    Anonymized peer comparison:
    - Percentile calculation (REQ-7.2)
    - Strength areas (REQ-7.3)
    - Improvement areas (REQ-7.4)
    - Differential privacy (REQ-7.6)
    """

    __tablename__ = "peer_comparisons"

    id = Column(String, primary_key=True, default=uuid4)
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Comparison period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Percentiles (REQ-7.2)
    success_rate_percentile = Column(Float)  # 0-100
    speed_percentile = Column(Float)  # 0-100
    quality_percentile = Column(Float)  # 0-100
    overall_percentile = Column(Float)  # 0-100

    # Strengths (REQ-7.3) - Top 25%
    strengths = Column(JSONB, default=list)  # [{skill, percentile}]

    # Improvements (REQ-7.4) - Bottom 25%
    improvements = Column(JSONB, default=list)  # [{skill, percentile, recommendation}]

    # Best practices (REQ-7.5)
    best_practices = Column(JSONB, default=list)

    # Privacy (REQ-7.6)
    is_anonymized = Column(Boolean, default=True)
    noise_added = Column(Boolean, default=True)  # Differential privacy
    k_anonymity = Column(Integer, default=5)  # k >= 5

    # Peer group info (anonymized)
    peer_group_size = Column(Integer)
    peer_group_avg_success_rate = Column(Float)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_peer_comparisons_user", "user_id"),
        Index("idx_peer_comparisons_period", "period_start", "period_end"),
    )


# ============================================================
# REQ-8: Export and Sharing - DiaryExport Model
# ============================================================


class DiaryExport(Base):
    """
    Diary export modeli (REQ-8)

    Export and sharing:
    - Multi-format support (REQ-8.1)
    - Date range filtering (REQ-8.2)
    - Privacy redaction (REQ-8.3)
    - Sharing links (REQ-8.4)
    - Encrypted backup (REQ-8.6)
    """

    __tablename__ = "diary_exports"

    id = Column(String, primary_key=True, default=uuid4)
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Export info
    format = Column(SQLEnum(ExportFormat), nullable=False)

    # Date range (REQ-8.2)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)

    # File info
    file_path = Column(String(512))
    file_size = Column(Integer)  # bytes

    # Privacy (REQ-8.3)
    privacy_filter_applied = Column(Boolean, default=False)
    redacted_fields = Column(JSONB, default=list)

    # Sharing (REQ-8.4)
    share_token = Column(String(64), unique=True, index=True)
    share_url = Column(String(512))
    share_expires_at = Column(DateTime(timezone=True))
    share_access_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)

    # Backup (REQ-8.6)
    is_backup = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)
    encryption_algorithm = Column(String(50))  # e.g., "AES-256"

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_diary_exports_user", "user_id"),
        Index("idx_diary_exports_share_token", "share_token"),
        Index("idx_diary_exports_created", "created_at"),
    )
