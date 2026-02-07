"""
Pipeline Stage Base Classes
Tüm pipeline aşamaları için temel sınıflar

Boris Cherny Standards:
- Type hints zorunlu
- Async I/O
- Pydantic validation
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StageInput(BaseModel):
    """Pipeline aşaması için input modeli"""

    question_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Soru verileri"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pipeline metadata"
    )
    previous_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Önceki aşamaların skorları"
    )

    class Config:
        extra = "allow"


class StageOutput(BaseModel):
    """Pipeline aşaması için output modeli"""

    question_data: Dict[str, Any] = Field(
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
    errors: List[str] = Field(
        default_factory=list,
        description="Hata mesajları"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Uyarı mesajları"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="İyileştirme önerileri"
    )
    metadata: Dict[str, Any] = Field(
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
        llm_client: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
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
        self._initialized_at = datetime.now(timezone.utc)

    @abstractmethod
    async def process(self, input_data: StageInput) -> StageOutput:
        """
        Ana işlem metodu - her aşama kendi implementasyonunu yapar

        Args:
            input_data: Aşama girişi

        Returns:
            StageOutput: Aşama çıkışı
        """
        pass

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
        pass

    def get_stage_info(self) -> Dict[str, Any]:
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
