"""Guard result model for loop protection."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GuardStatus(str, Enum):
    """Guard check status."""

    OK = "OK"
    WARNING = "WARNING"
    STOP = "STOP"


class GuardResult(BaseModel):
    """Result of a guard check."""

    guard_name: str = Field(..., description="Name of the guard")
    status: GuardStatus = Field(..., description="Guard status")
    message: str = Field(..., description="Human-readable message")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed information"
    )
    should_stop: bool = Field(..., description="Whether execution should stop")

    model_config = {"frozen": False}
