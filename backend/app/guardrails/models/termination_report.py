"""Termination report model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .guard_result import GuardResult


class TerminationReport(BaseModel):
    """Report generated when loop terminates."""

    reason: str = Field(..., description="Termination reason")
    terminated_by: str = Field(..., description="Guard that caused termination")
    total_iterations: int = Field(..., description="Total iterations completed")
    elapsed_time_seconds: float = Field(..., description="Total elapsed time")
    guard_results: list[GuardResult] = Field(..., description="Final guard results")
    partial_result: Any = Field(None, description="Partial result if stopped early")
    completed_normally: bool = Field(
        default=False, description="Whether loop completed normally"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Termination timestamp"
    )

    resource_usage: dict[str, Any] = Field(
        default_factory=dict, description="Resource usage statistics"
    )

    warnings_issued: list[str] = Field(
        default_factory=list, description="Warnings issued during execution"
    )

    model_config = {"frozen": False}

    def to_log_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for logging."""
        return {
            "reason": self.reason,
            "terminated_by": self.terminated_by,
            "iterations": self.total_iterations,
            "elapsed_seconds": round(self.elapsed_time_seconds, 2),
            "completed_normally": self.completed_normally,
            "warnings_count": len(self.warnings_issued),
            "resource_usage": self.resource_usage,
        }
