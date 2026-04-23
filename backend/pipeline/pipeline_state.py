"""
Pipeline State Management
Redis ile pipeline durum yönetimi
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    """Pipeline durumları"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageResult(BaseModel):
    """Aşama sonucu"""
    stage_name: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    duration: float = Field(ge=0.0, description="Süre (saniye)")
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    retry_count: int = Field(default=0, ge=0)
    completed_at: datetime | None = None


class PipelineState(BaseModel):
    """Pipeline durumu"""

    pipeline_id: str
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: str | None = None
    stage_results: list[StageResult] = Field(default_factory=list)

    # Input/Output
    initial_input: dict[str, Any] = Field(default_factory=dict)
    current_data: dict[str, Any] = Field(default_factory=dict)
    final_output: dict[str, Any] | None = None

    # Skorlar
    final_score: float | None = Field(default=None, ge=0.0, le=1.0)
    decision: str | None = None  # approved, review, rejected

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_duration: float = Field(default=0.0, ge=0.0)

    # Metadata
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    def add_stage_result(self, result: StageResult) -> None:
        """Aşama sonucu ekle"""
        self.stage_results.append(result)

    def get_stage_result(self, stage_name: str) -> StageResult | None:
        """Aşama sonucunu getir"""
        for result in self.stage_results:
            if result.stage_name == stage_name:
                return result
        return None

    def get_completed_stages(self) -> list[str]:
        """Tamamlanan aşamaları getir"""
        return [r.stage_name for r in self.stage_results if r.passed]

    def get_failed_stages(self) -> list[str]:
        """Başarısız aşamaları getir"""
        return [r.stage_name for r in self.stage_results if not r.passed]

    def calculate_progress(self, total_stages: int = 6) -> float:
        """İlerleme yüzdesini hesapla"""
        if total_stages == 0:
            return 0.0
        return len(self.stage_results) / total_stages

    def to_summary(self) -> dict[str, Any]:
        """Özet bilgi döndür"""
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status,
            "current_stage": self.current_stage,
            "progress": self.calculate_progress(),
            "stages_completed": len(self.stage_results),
            "final_score": self.final_score,
            "decision": self.decision,
            "total_duration": self.total_duration,
            "errors": [
                {"stage": r.stage_name, "errors": r.errors}
                for r in self.stage_results
                if r.errors
            ]
        }
