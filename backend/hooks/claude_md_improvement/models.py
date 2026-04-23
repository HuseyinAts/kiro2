"""
CLAUDE.md Self-Improvement için Pydantic modelleri.

Boris Cherny Standards - Verification Feedback Loops
Daisy Stanton Standards - Exit Code 2 Mekanizması
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class FeedbackType(str, Enum):
    """Feedback türleri."""

    EXPLICIT = "explicit"  # User rating (1-5) + comment
    IMPLICIT = "implicit"  # Retry count, edit frequency
    AUTOMATIC = "automatic"  # Hook-based (test pass/fail)


class OutcomeType(str, Enum):
    """Task sonuç türleri."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


class FeedbackRecord(BaseModel):
    """Tek bir feedback kaydı."""

    id: UUID = Field(default_factory=uuid4)
    task_id: str = Field(..., description="İlgili task ID'si")
    rule_id: str | None = Field(None, description="CLAUDE.md rule ID'si")
    feedback_type: FeedbackType = Field(..., description="Feedback türü")
    outcome: OutcomeType = Field(..., description="Task sonucu")

    # Explicit feedback alanları
    rating: int | None = Field(
        None, ge=1, le=5, description="Kullanıcı puanı (1-5)"
    )
    comment: str | None = Field(None, description="Kullanıcı yorumu")

    # Implicit feedback alanları
    retry_count: int = Field(default=0, description="Yeniden deneme sayısı")
    edit_frequency: int = Field(default=0, description="Düzenleme sıklığı")
    execution_time: float = Field(default=0.0, description="Çalışma süresi (s)")

    # Automatic feedback alanları
    test_passed: bool | None = Field(None, description="Test sonucu")
    lint_passed: bool | None = Field(None, description="Lint sonucu")
    type_check_passed: bool | None = Field(None, description="Type check sonucu")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: str | None = Field(None, description="Claude Code session ID")
    agent_type: str | None = Field(None, description="Agent türü")
    context: dict[str, Any] = Field(default_factory=dict, description="Ek bağlam")

    # Pydantic v2 automatically serializes datetime and UUID
    model_config = ConfigDict()


class RuleEffectiveness(BaseModel):
    """Bir CLAUDE.md kuralının etkinlik skoru."""

    rule_id: str = Field(..., description="Kural ID'si")
    rule_text: str = Field(..., description="Kural metni")
    section: str = Field(..., description="CLAUDE.md bölümü")

    # Metrikler
    total_feedback: int = Field(default=0, description="Toplam feedback sayısı")
    success_count: int = Field(default=0, description="Başarılı sonuç sayısı")
    failure_count: int = Field(default=0, description="Başarısız sonuç sayısı")

    # Hesaplanan skorlar
    effectiveness_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Etkinlik skoru (0-1)"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Güven aralığı"
    )

    # Ağırlıklı skorlar
    explicit_score: float = Field(default=0.0, description="Explicit feedback skoru")
    implicit_score: float = Field(default=0.0, description="Implicit feedback skoru")

    # Periyot
    window_days: int = Field(default=30, description="Değerlendirme penceresi (gün)")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def calculate_effectiveness(self) -> float:
        """
        Etkinlik skorunu hesapla.

        Returns:
            0-1 arası etkinlik skoru
        """
        if self.total_feedback == 0:
            return 0.5  # Varsayılan nötr skor

        # Ağırlıklı ortalama: explicit %70, implicit %30
        weighted_score = (self.explicit_score * 0.7) + (self.implicit_score * 0.3)

        # Başarı oranı
        success_rate = (
            self.success_count / self.total_feedback if self.total_feedback > 0 else 0.5
        )

        # Kombine skor
        self.effectiveness_score = (weighted_score + success_rate) / 2
        return self.effectiveness_score

    @property
    def needs_improvement(self) -> bool:
        """Kuralın iyileştirme gerektirip gerektirmediğini kontrol et."""
        return self.effectiveness_score < 0.6


class ImprovementTrigger(BaseModel):
    """İyileştirme tetikleyici."""

    trigger_id: UUID = Field(default_factory=uuid4)
    rule_id: str = Field(..., description="İyileştirilecek kural ID'si")
    trigger_reason: str = Field(..., description="Tetikleme nedeni")

    # Threshold bilgileri
    current_score: float = Field(..., description="Mevcut etkinlik skoru")
    threshold: float = Field(default=0.6, description="Tetikleme eşiği")
    improvement_target: float = Field(default=0.8, description="Hedef skor")

    # Önerilen aksiyonlar
    suggested_actions: list[str] = Field(
        default_factory=list, description="Önerilen aksiyonlar"
    )
    priority: int = Field(default=1, ge=1, le=5, description="Öncelik (1=en yüksek)")

    # Durum
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = Field(default=False)
    processed_at: datetime | None = None

    # Pydantic v2 automatically serializes datetime and UUID
    model_config = ConfigDict()


class PatternInfo(BaseModel):
    """Tespit edilen pattern bilgisi."""

    pattern_id: UUID = Field(default_factory=uuid4)
    pattern_type: str = Field(..., description="Pattern türü (error, success, anti)")
    description: str = Field(..., description="Pattern açıklaması")

    # İstatistikler
    occurrence_count: int = Field(default=0, description="Görülme sayısı")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Güven seviyesi (>= 0.95 gerekli)"
    )

    # İlişkili kurallar
    related_rules: list[str] = Field(
        default_factory=list, description="İlişkili kural ID'leri"
    )
    recommendation: str | None = Field(None, description="Öneri")

    detected_at: datetime = Field(default_factory=datetime.utcnow)


class ExitCodeResult(BaseModel):
    """Exit code sonucu (Daisy Stanton standards)."""

    exit_code: int = Field(..., description="Exit code (0=success, 2=blocking)")
    message: str = Field(..., description="Sonuç mesajı")
    blocking: bool = Field(default=False, description="Claude'a geri beslenir mi")
    details: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def success(cls, message: str = "İşlem başarılı") -> ExitCodeResult:
        """Başarılı sonuç oluştur."""
        return cls(exit_code=0, message=message, blocking=False)

    @classmethod
    def blocking_error(
        cls, message: str, details: dict[str, Any] | None = None
    ) -> ExitCodeResult:
        """Blocking hata oluştur (Exit Code 2)."""
        return cls(
            exit_code=2,
            message=message,
            blocking=True,
            details=details or {},
        )
