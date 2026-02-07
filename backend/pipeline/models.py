"""
Pipeline Data Models
Soru üretim pipeline için veri modelleri

IRT Parametreleri (CLAUDE.md):
- difficulty: [-4.0, 4.0]
- discrimination: [0.2, 4.0]
- guessing: [0.0, 0.35]
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


class IRTParameters(BaseModel):
    """IRT (Item Response Theory) parametreleri"""

    difficulty: float = Field(
        ...,
        ge=-4.0,
        le=4.0,
        description="Zorluk parametresi b"
    )
    discrimination: float = Field(
        ...,
        ge=0.2,
        le=4.0,
        description="Ayırt edicilik parametresi a"
    )
    guessing: float = Field(
        ...,
        ge=0.0,
        le=0.35,
        description="Şans parametresi c"
    )

    def calculate_probability(self, theta: float = 0.0) -> float:
        """
        3 parametreli lojistik modelle başarı olasılığı hesapla

        P(theta) = c + (1-c) / (1 + exp(-a(theta-b)))

        Args:
            theta: Öğrenci yetenek seviyesi

        Returns:
            float: Başarı olasılığı (0-1)
        """
        import math
        exponent = -self.discrimination * (theta - self.difficulty)
        prob = self.guessing + (1 - self.guessing) / (1 + math.exp(exponent))
        return prob

    def is_in_zpd(self, theta: float = 0.0) -> bool:
        """
        ZPD (Zone of Proximal Development) kontrolü

        ZPD: %15-85 başarı olasılığı (CLAUDE.md)

        Args:
            theta: Öğrenci yetenek seviyesi

        Returns:
            bool: ZPD içinde mi
        """
        prob = self.calculate_probability(theta)
        return 0.15 <= prob <= 0.85


class QuestionOption(BaseModel):
    """Soru seçeneği"""

    label: Literal["A", "B", "C", "D"]
    text: str
    is_correct: bool = False
    plausibility_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Çeldirici akla yatkınlık skoru"
    )


class QualityScores(BaseModel):
    """Kalite skorları"""

    content_score: float = Field(default=0.0, ge=0.0, le=1.0)
    difficulty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    distractor_score: float = Field(default=0.0, ge=0.0, le=1.0)
    compliance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    language_score: float = Field(default=0.0, ge=0.0, le=1.0)

    def calculate_final_score(self) -> float:
        """
        Ağırlıklı ortalama hesapla

        Weights (design.md):
        - Content: 25%
        - Difficulty: 20%
        - Distractor: 20%
        - Compliance: 20%
        - Language: 15%

        Returns:
            float: Final skor (0-1)
        """
        weights = {
            "content": 0.25,
            "difficulty": 0.20,
            "distractor": 0.20,
            "compliance": 0.20,
            "language": 0.15
        }

        final = (
            self.content_score * weights["content"] +
            self.difficulty_score * weights["difficulty"] +
            self.distractor_score * weights["distractor"] +
            self.compliance_score * weights["compliance"] +
            self.language_score * weights["language"]
        )

        return round(final, 4)


class Question(BaseModel):
    """Tam soru modeli"""

    question_id: Optional[str] = None

    # Kazanım ve konu
    kazanim: str
    subject: str
    topic: str
    grade_level: int = Field(..., ge=9, le=12)
    target_difficulty: Literal["kolay", "orta", "zor"]

    # Soru içeriği
    question_text: str
    context: Optional[str] = None
    bloom_level: str
    question_type: str

    # Seçenekler
    options: List[QuestionOption] = Field(..., min_items=4, max_items=4)
    correct_answer: Literal["A", "B", "C", "D"]

    # IRT parametreleri
    irt_parameters: IRTParameters

    # Kalite skorları
    quality_scores: QualityScores
    final_score: float = Field(..., ge=0, le=1)
    status: Literal["approved", "review", "rejected"]

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pipeline_id: Optional[str] = None

    @validator("options")
    def validate_options(cls, v):
        """4 seçenek olmalı ve birisi doğru olmalı"""
        if len(v) != 4:
            raise ValueError("Tam olarak 4 seçenek olmalı")

        labels = [opt.label for opt in v]
        if sorted(labels) != ["A", "B", "C", "D"]:
            raise ValueError("Seçenekler A, B, C, D olmalı")

        correct_count = sum(1 for opt in v if opt.is_correct)
        if correct_count != 1:
            raise ValueError("Tam olarak 1 doğru cevap olmalı")

        return v


class PipelineResult(BaseModel):
    """Pipeline çalışma sonucu"""

    pipeline_id: str
    question: Question
    stage_results: List[Dict[str, Any]]
    final_score: float = Field(..., ge=0, le=1)
    decision: Literal["approved", "review", "rejected"]
    total_duration: float = Field(..., ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def from_pipeline_state(cls, state: "PipelineState", question: Question) -> "PipelineResult":
        """PipelineState'den oluştur"""
        return cls(
            pipeline_id=state.pipeline_id,
            question=question,
            stage_results=[r.dict() for r in state.stage_results],
            final_score=state.final_score or 0.0,
            decision=state.decision or "rejected",
            total_duration=state.total_duration
        )


class GenerationRequest(BaseModel):
    """Soru üretim isteği"""

    kazanim: str = Field(..., description="MEB kazanımı")
    subject: str = Field(..., description="Ders (matematik, fizik, vb.)")
    topic: str = Field(..., description="Konu")
    grade_level: int = Field(11, ge=9, le=12, description="Sınıf seviyesi")
    target_difficulty: Literal["kolay", "orta", "zor"] = Field(
        "orta",
        description="Hedef zorluk"
    )
    question_type: str = Field(
        "çoktan_seçmeli",
        description="Soru tipi"
    )
    correct_answer: Optional[str] = Field(
        None,
        description="Doğru cevap (opsiyonel)"
    )
    context: Optional[str] = Field(
        None,
        description="Ek bağlam"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "kazanim": "İkinci dereceden bir bilinmeyenli denklemleri çözer",
            "subject": "matematik",
            "topic": "İkinci Dereceden Denklemler",
            "grade_level": 10,
            "target_difficulty": "orta",
            "question_type": "çoktan_seçmeli"
        }
    })
