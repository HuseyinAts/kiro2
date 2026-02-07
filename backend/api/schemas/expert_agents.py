"""
Expert Agents API Schemas
Pydantic models for konu-bazli subagent system
REQ-1 to REQ-8
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DomainTypeEnum(str, Enum):
    """Domain types for expert agents"""

    MATEMATIK = "matematik"
    FIZIK = "fizik"
    TURKCE = "turkce"
    SOSYAL = "sosyal"
    BIYOLOJI = "biyoloji"
    YABANCI_DIL = "yabanci_dil"


# ==================== Request Models ====================


class QuestionRequest(BaseModel):
    """
    POST /api/v1/ask-question request body

    Attributes:
        question_text: Soru metni (Turkish)
        student_id: Ogrenci ID (opsiyonel)
        preferred_domain: Tercih edilen domain (opsiyonel, auto-detect)
        include_visualizations: Grafik/diyagram istek
        include_step_by_step: Adim adim cozum istek
    """

    question_text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Soru metni (minimum 10 karakter)",
        examples=["2x + 3 = 7 denklemini cozunuz."],
    )
    student_id: Optional[str] = Field(
        None, description="Ogrenci ID (performans takibi icin)"
    )
    preferred_domain: Optional[DomainTypeEnum] = Field(
        None, description="Tercih edilen domain (bos birakilirsa auto-detect)"
    )
    include_visualizations: bool = Field(
        True, description="Grafik/diyagram olustur"
    )
    include_step_by_step: bool = Field(
        True, description="Adim adim cozum goster"
    )
    exam_type: Optional[str] = Field(
        None,
        description="Sinav tipi (TYT, AYT-SAY, AYT-EA, AYT-SOZ, YDT)",
        examples=["TYT", "AYT-SAY"],
    )

    @field_validator("question_text")
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Soru metni bos olamaz")
        return v.strip()


class DomainClassificationRequest(BaseModel):
    """Request for domain classification only"""

    question_text: str = Field(..., min_length=10, max_length=5000)


# ==================== Response Models ====================


class DomainClassification(BaseModel):
    """
    Soru siniflandirma sonucu

    Attributes:
        primary_domain: Ana domain
        primary_confidence: Ana domain guven skoru [0, 1]
        secondary_domain: Ikincil domain (multi-domain sorular)
        secondary_confidence: Ikincil guven skoru
        is_multi_domain: Birden fazla domain gerektirir mi?
    """

    primary_domain: DomainTypeEnum
    primary_confidence: float = Field(..., ge=0.0, le=1.0)
    secondary_domain: Optional[DomainTypeEnum] = None
    secondary_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_multi_domain: bool = False


class Visualization(BaseModel):
    """Gorsel/grafik bilgisi"""

    type: str = Field(..., description="Gorsel tipi (graph, diagram, table)")
    title: str = Field("", description="Gorsel basligi")
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Gorsel verisi (plotly, matplotlib JSON)"
    )
    base64_image: Optional[str] = Field(None, description="Base64 encoded image")


class AgentResponse(BaseModel):
    """
    Tek agent'in yaniti

    Attributes:
        domain: Yaniti ureten agent
        content: Yanit icerigi
        confidence: Guven skoru [0, 1]
        tools_used: Kullanilan araclar
        step_by_step_solution: Adim adim cozum
        latex_expressions: LaTeX ifadeleri
        visualizations: Olusturulan gorseller
        references: Kaynaklar
        response_time_ms: Yanit suresi
        tokens_used: Kullanilan token
    """

    domain: DomainTypeEnum
    content: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    tools_used: List[str] = Field(default_factory=list)
    step_by_step_solution: List[str] = Field(default_factory=list)
    latex_expressions: List[str] = Field(default_factory=list)
    visualizations: List[Visualization] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    response_time_ms: float = Field(0.0, ge=0.0)
    tokens_used: int = Field(0, ge=0)


class QuestionResponse(BaseModel):
    """
    POST /api/v1/ask-question response

    Attributes:
        success: Islem basarili mi?
        classification: Soru siniflandirmasi
        responses: Agent yanitlari (multi-domain icin birden fazla)
        synthesized_response: Birlestirilmis yanit
        specialization_score: Uzmanlik skoru
        total_response_time_ms: Toplam islem suresi
        metadata: Ek bilgiler
    """

    success: bool
    classification: DomainClassification
    responses: List[AgentResponse]
    synthesized_response: str = Field("", description="Birlestirilmis final yanit")
    specialization_score: float = Field(0.0, ge=0.0, le=1.0)
    total_response_time_ms: float = Field(0.0, ge=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


# ==================== Performance & Metrics Models ====================


class SpecializationScore(BaseModel):
    """
    Agent uzmanlik skoru (REQ-8.1, REQ-8.2)

    Formula: 0.4*relevance + 0.3*accuracy + 0.2*completeness + 0.1*satisfaction
    """

    domain: DomainTypeEnum
    domain_relevance: float = Field(..., ge=0.0, le=1.0, description="Domain uyumu (40%)")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Dogruluk (30%)")
    completeness: float = Field(..., ge=0.0, le=1.0, description="Tamlık (20%)")
    user_satisfaction: float = Field(..., ge=0.0, le=1.0, description="Memnuniyet (10%)")
    total_score: float = Field(..., ge=0.0, le=1.0, description="Toplam skor")
    calculated_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def calculate(
        cls,
        domain: DomainTypeEnum,
        relevance: float,
        accuracy: float,
        completeness: float,
        satisfaction: float,
    ) -> "SpecializationScore":
        """
        Uzmanlik skorunu hesapla (REQ-8.2)

        Weights:
        - Domain Relevance: 40%
        - Accuracy: 30%
        - Completeness: 20%
        - User Satisfaction: 10%
        """
        total = (
            relevance * 0.40
            + accuracy * 0.30
            + completeness * 0.20
            + satisfaction * 0.10
        )

        return cls(
            domain=domain,
            domain_relevance=relevance,
            accuracy=accuracy,
            completeness=completeness,
            user_satisfaction=satisfaction,
            total_score=total,
        )


class AgentPerformance(BaseModel):
    """
    GET /api/v1/agents/{agent_name}/performance response

    Agent performans metrikleri
    """

    agent_id: str
    domain: DomainTypeEnum
    specialization_areas: List[str]
    total_questions_answered: int = 0
    successful_answers: int = 0
    failed_answers: int = 0
    average_response_time_ms: float = 0.0
    average_confidence: float = Field(0.0, ge=0.0, le=1.0)
    current_specialization_score: Optional[SpecializationScore] = None
    context_usage: Dict[str, Any] = Field(default_factory=dict)
    tools_available: List[str] = Field(default_factory=list)
    last_activity: Optional[datetime] = None


class AllAgentsScores(BaseModel):
    """
    GET /api/v1/agents/specialization-scores response

    Tum agent'larin uzmanlik skorlari
    """

    scores: List[SpecializationScore]
    average_score: float = Field(0.0, ge=0.0, le=1.0)
    best_performing_domain: Optional[DomainTypeEnum] = None
    needs_retraining: List[DomainTypeEnum] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)


# ==================== Context Models ====================


class ContextStatus(BaseModel):
    """Agent context durumu (REQ-7.2)"""

    domain: DomainTypeEnum
    current_tokens: int = Field(..., ge=0)
    max_tokens: int = Field(200_000, ge=0)
    remaining_tokens: int = Field(..., ge=0)
    usage_percentage: float = Field(..., ge=0.0, le=100.0)
    conversation_history_length: int = Field(0, ge=0)
    last_updated: datetime


# ==================== Blackboard Models ====================


class BlackboardMessage(BaseModel):
    """Blackboard mesaj yapisi (REQ-7.3)"""

    message_id: str
    source_agent: DomainTypeEnum
    target_agent: Optional[DomainTypeEnum] = None  # None = broadcast
    message_type: str
    content: Dict[str, Any]
    priority: int = Field(0, ge=0, le=2)
    ttl_seconds: int = Field(3600, ge=0)  # 1 hour default
    timestamp: datetime = Field(default_factory=datetime.now)


class SharedContext(BaseModel):
    """Agent'lar arasi paylasilan context (REQ-7.5)"""

    context_id: str
    source_agent: DomainTypeEnum
    data: Dict[str, Any]
    ttl_seconds: int = Field(600, ge=0)  # 10 minutes for shared context
    created_at: datetime = Field(default_factory=datetime.now)
