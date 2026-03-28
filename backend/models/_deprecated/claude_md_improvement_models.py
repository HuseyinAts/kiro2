"""
CLAUDE.md Self-Improvement Database Models.

Bu modül, feedback, pattern ve rule effectiveness
verilerini PostgreSQL'de saklamak için SQLAlchemy modelleri sağlar.

Spec: claude-md-self-improvement Phase 0.5
- PostgreSQL:5434 connection
- Redis:6379 cache support
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class FeedbackRecord(Base):
    """
    Agent task feedback kayıtları.

    Attributes:
        id: UUID primary key
        task_id: İlgili task ID
        rule_id: CLAUDE.md rule ID (optional)
        feedback_type: explicit, implicit, automatic
        outcome: success, failure, partial, timeout
        rating: Kullanıcı puanı (1-5)
        comment: Kullanıcı yorumu
        retry_count: Yeniden deneme sayısı
        edit_frequency: Düzenleme sıklığı
        execution_time: Çalışma süresi (saniye)
        test_passed: Test sonucu
        lint_passed: Lint sonucu
        type_check_passed: Type check sonucu
        session_id: Claude Code session ID
        agent_type: Agent türü
        context: Ek bağlam (JSON)
        created_at: Oluşturulma zamanı
    """

    __tablename__ = "claude_md_feedback_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(String(255), nullable=False, index=True)
    rule_id = Column(String(255), nullable=True, index=True)

    # Feedback türü
    feedback_type = Column(
        String(50),
        nullable=False,
        default="automatic",
    )

    # Sonuç
    outcome = Column(
        String(50),
        nullable=False,
        default="success",
    )

    # Explicit feedback
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)

    # Implicit feedback
    retry_count = Column(Integer, default=0)
    edit_frequency = Column(Integer, default=0)
    execution_time = Column(Float, default=0.0)

    # Automatic feedback (Boris Cherny verification)
    test_passed = Column(Boolean, nullable=True)
    lint_passed = Column(Boolean, nullable=True)
    type_check_passed = Column(Boolean, nullable=True)

    # Metadata
    session_id = Column(String(255), nullable=True)
    agent_type = Column(String(100), nullable=True)
    context = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_feedback_rule_created", "rule_id", "created_at"),
        Index("ix_feedback_type_outcome", "feedback_type", "outcome"),
    )


class RuleEffectiveness(Base):
    """
    CLAUDE.md rule effectiveness skorları.

    Attributes:
        id: UUID primary key
        rule_id: Unique rule identifier
        rule_text: Kural metni
        section: CLAUDE.md bölümü
        total_feedback: Toplam feedback sayısı
        success_count: Başarılı sonuç sayısı
        failure_count: Başarısız sonuç sayısı
        effectiveness_score: Etkinlik skoru (0-1)
        confidence: Güven aralığı
        explicit_score: Explicit feedback skoru
        implicit_score: Implicit feedback skoru
        window_days: Değerlendirme penceresi (gün)
        last_updated: Son güncelleme zamanı
        created_at: Oluşturulma zamanı
    """

    __tablename__ = "claude_md_rule_effectiveness"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id = Column(String(255), nullable=False, unique=True, index=True)
    rule_text = Column(Text, nullable=True)
    section = Column(String(255), nullable=True)

    # Metrikler
    total_feedback = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Hesaplanan skorlar
    effectiveness_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)

    # Ağırlıklı skorlar
    explicit_score = Column(Float, default=0.0)
    implicit_score = Column(Float, default=0.0)

    # Periyot
    window_days = Column(Integer, default=30)

    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def needs_improvement(self) -> bool:
        """Kuralın iyileştirme gerektirip gerektirmediğini kontrol et."""
        return self.effectiveness_score < 0.6


class ImprovementTrigger(Base):
    """
    İyileştirme tetikleyicileri.

    Attributes:
        id: UUID primary key
        rule_id: İyileştirilecek kural ID
        trigger_reason: Tetikleme nedeni
        current_score: Mevcut etkinlik skoru
        threshold: Tetikleme eşiği
        improvement_target: Hedef skor
        suggested_actions: Önerilen aksiyonlar (JSON)
        priority: Öncelik (1=en yüksek)
        triggered_at: Tetikleme zamanı
        processed: İşlendi mi
        processed_at: İşlenme zamanı
        approved: Onaylandı mı
        approved_by: Onaylayan
        applied: Uygulandı mı
        applied_at: Uygulama zamanı
    """

    __tablename__ = "claude_md_improvement_triggers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id = Column(String(255), nullable=False, index=True)
    trigger_reason = Column(Text, nullable=False)

    # Threshold bilgileri
    current_score = Column(Float, nullable=False)
    threshold = Column(Float, default=0.6)
    improvement_target = Column(Float, default=0.8)

    # Önerilen aksiyonlar
    suggested_actions = Column(JSON, default=list)
    priority = Column(Integer, default=1)

    # Durum
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)

    # Onay workflow
    approved = Column(Boolean, nullable=True)
    approved_by = Column(String(255), nullable=True)

    # Uygulama
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)

    # Index for pending triggers
    __table_args__ = (
        Index("ix_trigger_pending", "processed", "priority"),
    )


class PatternDetection(Base):
    """
    Tespit edilen pattern'ler.

    Attributes:
        id: UUID primary key
        pattern_type: error, success, anti
        description: Pattern açıklaması
        occurrence_count: Görülme sayısı
        confidence: Güven seviyesi (>= 0.95 gerekli)
        related_rules: İlişkili kural ID'leri (JSON)
        recommendation: Öneri
        detected_at: Tespit zamanı
        last_seen: Son görülme zamanı
        active: Aktif mi
    """

    __tablename__ = "claude_md_pattern_detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pattern_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # İstatistikler
    occurrence_count = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)

    # İlişkili kurallar
    related_rules = Column(JSON, default=list)
    recommendation = Column(Text, nullable=True)

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

    # Index for active patterns
    __table_args__ = (
        Index("ix_pattern_active_type", "active", "pattern_type"),
    )


class RuleVersion(Base):
    """
    CLAUDE.md rule versiyonları (Git-like tracking).

    Attributes:
        id: UUID primary key
        rule_id: Kural ID
        version: Semantic version (major.minor.patch)
        rule_text: Kural metni
        change_reason: Değişiklik nedeni
        previous_version_id: Önceki versiyon ID
        effectiveness_before: Değişiklik öncesi etkinlik
        effectiveness_after: Değişiklik sonrası etkinlik
        created_by: Oluşturan (agent/user)
        created_at: Oluşturulma zamanı
        is_current: Güncel versiyon mu
    """

    __tablename__ = "claude_md_rule_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    rule_text = Column(Text, nullable=False)
    change_reason = Column(Text, nullable=True)

    # Version tracking
    previous_version_id = Column(UUID(as_uuid=True), nullable=True)

    # Etkinlik karşılaştırma
    effectiveness_before = Column(Float, nullable=True)
    effectiveness_after = Column(Float, nullable=True)

    # Metadata
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_current = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("rule_id", "version", name="uq_rule_version"),
        Index("ix_rule_current", "rule_id", "is_current"),
    )


class AuditLog(Base):
    """
    Self-improvement audit log (who, what, when, why).

    Spec: REQ-8.5 - Audit logging

    Attributes:
        id: UUID primary key
        action: Yapılan aksiyon
        entity_type: feedback, rule, trigger, pattern
        entity_id: İlgili entity ID
        actor: Yapan (agent/user)
        reason: Neden
        details: Detaylar (JSON)
        created_at: Oluşturulma zamanı
    """

    __tablename__ = "claude_md_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(255), nullable=True)
    actor = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_action_time", "action", "created_at"),
    )
