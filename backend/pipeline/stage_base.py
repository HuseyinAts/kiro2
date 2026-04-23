"""
Pipeline Stage Base Classes
Tüm pipeline aşamaları için temel sınıflar

Boris Cherny Standards:
- Type hints zorunlu
- Async I/O
- Pydantic validation
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class StageInput(BaseModel):
    """Pipeline aşaması için input modeli"""

    question_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Soru verileri"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Pipeline metadata"
    )
    previous_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Önceki aşamaların skorları"
    )

    class Config:
        extra = "allow"


class StageOutput(BaseModel):
    """Pipeline aşaması için output modeli"""

    question_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Güncellenmiş soru verileri"
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Aşama skoru (0-1)"
    )
    passed: bool = Field(
        default=False,
        description="Aşama başarılı mı"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Hata mesajları"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Uyarı mesajları"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="İyileştirme önerileri"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Aşama metadata"
    )
    execution_time: float = Field(
        default=0.0,
        description="Çalışma süresi (saniye)"
    )

    class Config:
        extra = "allow"


class BasePipelineStage(ABC):
    """
    Tüm pipeline aşamaları için abstract base class

    Her aşama bu sınıfı extend eder:
    - ContentGeneratorAgent
    - DifficultyAgent
    - DistractorAgent
    - ComplianceAgent
    - LanguageQAAgent
    - QualityGateAgent
    """

    def __init__(
        self,
        stage_name: str,
        llm_client: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        """
        Pipeline aşaması başlat

        Args:
            stage_name: Aşama adı
            llm_client: LLM client (Qwen3-8B)
            config: Aşama konfigürasyonu
        """
        self.stage_name = stage_name
        self.llm = llm_client
        self.config = config or {}
        self._initialized_at = datetime.now(UTC)

    @abstractmethod
    async def process(self, input_data: StageInput) -> StageOutput:
        """
        Ana işlem metodu - her aşama kendi implementasyonunu yapar

        Args:
            input_data: Aşama girişi

        Returns:
            StageOutput: Aşama çıkışı
        """

    @abstractmethod
    def get_stage_weight(self) -> float:
        """
        Final skorda bu aşamanın ağırlığını döndür

        Returns:
            float: Ağırlık (0-1 arası)

        Weights:
        - Content: 0.25 (25%)
        - Difficulty: 0.20 (20%)
        - Distractor: 0.20 (20%)
        - Compliance: 0.20 (20%)
        - Language: 0.15 (15%)
        """

    def get_stage_info(self) -> dict[str, Any]:
        """Aşama bilgilerini döndür"""
        return {
            "stage_name": self.stage_name,
            "weight": self.get_stage_weight(),
            "initialized_at": self._initialized_at.isoformat(),
            "config": self.config
        }

    async def validate_input(self, input_data: StageInput) -> bool:
        """
        Input validasyonu - alt sınıflar override edebilir

        Args:
            input_data: Doğrulanacak input

        Returns:
            bool: Geçerli mi
        """
        return True

    async def pre_process(self, input_data: StageInput) -> StageInput:
        """
        Ön işleme - alt sınıflar override edebilir

        Args:
            input_data: İşlenecek input

        Returns:
            StageInput: İşlenmiş input
        """
        return input_data

    async def post_process(self, output: StageOutput) -> StageOutput:
        """
        Son işleme - alt sınıflar override edebilir

        Args:
            output: İşlenecek output

        Returns:
            StageOutput: İşlenmiş output
        """
        return output
