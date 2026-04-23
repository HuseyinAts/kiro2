"""
AI Agent Yanıt Doğrulama Sistemi - Base Validator

Bu modül, AI agent'ların (LearningPathAgent, StudyBuddyAgent, ExamAgent)
ürettiği yanıtların doğrulanması için temel sınıfları ve modelleri içerir.

Boris Cherny verification feedback loops prensibi uygulanmaktadır.

Requirements:
- REQ-1.1 - REQ-8.6 (verification-ai-agent-yanit spec)
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class AgentType(str, Enum):
    """AI Agent tipleri"""
    LEARNING_PATH = "learning_path"
    STUDY_BUDDY = "study_buddy"
    EXAM = "exam"


class ValidationAction(str, Enum):
    """Doğrulama sonucu aksiyonları"""
    APPROVE = "approve"   # Score >= 0.8
    REVIEW = "review"     # 0.5 <= Score < 0.8
    REJECT = "reject"     # Score < 0.5


class ValidationResult(BaseModel):
    """
    Doğrulama sonucu modeli.

    Her validator bu modeli döndürür.
    Score 0-1 aralığında olmalıdır.
    """
    is_valid: bool = Field(
        description="Doğrulama geçti mi (kritik hata yok)"
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Doğrulama skoru (0-1 arası)"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Kritik hatalar listesi"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Uyarılar listesi"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="İyileştirme önerileri"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Ek metadata (validator ismi, istatistikler vb.)"
    )

    @field_validator('score')
    @classmethod
    def validate_score_bounds(cls, v: float) -> float:
        """Score değerini 0-1 aralığında tut"""
        return max(0.0, min(1.0, v))


class AgentResponse(BaseModel):
    """
    AI Agent yanıt modeli.

    Doğrulanacak agent yanıtının yapısı.
    """
    agent_type: Literal["learning_path", "study_buddy", "exam"] = Field(
        description="Agent tipi"
    )
    response_id: str = Field(
        description="Yanıt unique ID'si"
    )
    user_id: str = Field(
        description="Kullanıcı ID'si"
    )
    query: str = Field(
        description="Kullanıcı sorusu/isteği"
    )
    response_text: str = Field(
        description="Agent'ın metin yanıtı"
    )
    response_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent'a özgü yapılandırılmış veri"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Yanıt zamanı"
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Ek bağlam bilgisi (öğrenci seviyesi, sınıf vb.)"
    )


class ValidationReport(BaseModel):
    """
    Tam doğrulama raporu modeli.

    Tüm validator sonuçlarının birleştirilmiş hali.
    """
    response_id: str = Field(
        description="Doğrulanan yanıt ID'si"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Toplam güven skoru (0-1)"
    )
    action: ValidationAction = Field(
        description="Önerilen aksiyon"
    )
    validation_results: dict[str, dict[str, Any]] = Field(
        description="Her validator'ın detaylı sonuçları"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Tüm hatalar"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Tüm uyarılar"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Tüm öneriler"
    )
    duration_seconds: float = Field(
        ge=0.0,
        description="Toplam doğrulama süresi (saniye)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Rapor oluşturma zamanı"
    )

    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_bounds(cls, v: float) -> float:
        """Confidence değerini 0-1 aralığında tut"""
        return max(0.0, min(1.0, v))


class BaseResponseValidator(ABC):
    """
    AI yanıt doğrulayıcı abstract base class.

    Tüm validator'lar bu sınıftan türetilmelidir.

    Attributes:
        weight: Bu validator'ın toplam skordaki ağırlığı (0-1)
        name: Validator ismi (logging için)
    """

    def __init__(self, weight: float = 0.3):
        """
        Args:
            weight: Validator ağırlığı (default: 0.3)
        """
        if not 0.0 <= weight <= 1.0:
            raise ValueError(f"Weight must be between 0 and 1, got {weight}")
        self.weight = weight
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        """Validator ismi"""
        return self._name

    @abstractmethod
    async def validate(self, response: AgentResponse) -> ValidationResult:
        """
        AI yanıtını doğrula.

        Args:
            response: Doğrulanacak agent yanıtı

        Returns:
            ValidationResult: Doğrulama sonucu

        Raises:
            ValidationError: Doğrulama işlemi başarısız olursa
        """

    @abstractmethod
    def get_validator_name(self) -> str:
        """
        Validator ismini döndür.

        Returns:
            str: Validator ismi (örn: "LearningPathValidator")
        """

    def _create_success_result(
        self,
        score: float = 1.0,
        warnings: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Başarılı doğrulama sonucu oluştur.

        Args:
            score: Başarı skoru (default: 1.0)
            warnings: Opsiyonel uyarılar
            metadata: Opsiyonel metadata

        Returns:
            ValidationResult: Başarılı sonuç
        """
        return ValidationResult(
            is_valid=True,
            score=score,
            errors=[],
            warnings=warnings or [],
            suggestions=[],
            metadata={
                "validator": self.name,
                **(metadata or {})
            }
        )

    def _create_failure_result(
        self,
        errors: list[str],
        score: float = 0.0,
        warnings: list[str] | None = None,
        suggestions: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Başarısız doğrulama sonucu oluştur.

        Args:
            errors: Hata mesajları
            score: Hata skoru (default: 0.0)
            warnings: Opsiyonel uyarılar
            suggestions: Opsiyonel düzeltme önerileri
            metadata: Opsiyonel metadata

        Returns:
            ValidationResult: Başarısız sonuç
        """
        return ValidationResult(
            is_valid=False,
            score=score,
            errors=errors,
            warnings=warnings or [],
            suggestions=suggestions or [],
            metadata={
                "validator": self.name,
                **(metadata or {})
            }
        )


class ValidationError(Exception):
    """Doğrulama işlemi hatası"""

    def __init__(self, message: str, validator_name: str = "Unknown"):
        self.message = message
        self.validator_name = validator_name
        super().__init__(f"[{validator_name}] {message}")


class ValidationTimeoutError(ValidationError):
    """Doğrulama zaman aşımı hatası"""


class ExternalAPIError(ValidationError):
    """Harici API hatası (Wikipedia, MEB vb.)"""


class AgentTypeError(ValidationError):
    """Bilinmeyen agent tipi hatası"""


class HistoryNotFoundError(ValidationError):
    """Yanıt geçmişi bulunamadı hatası"""
