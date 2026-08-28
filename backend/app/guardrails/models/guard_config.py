"""Guard configuration model."""

from typing import Any

from pydantic import BaseModel, Field


class GuardConfig(BaseModel):
    """Configuration for guardrail system."""

    # maxTurns config
    max_turns: int = Field(default=100, ge=1, description="Maximum iterations")

    # Timeout config
    timeout_seconds: float = Field(
        default=300.0, ge=0.1, description="Timeout in seconds"
    )
    warning_threshold: float = Field(
        default=0.8, ge=0.1, le=1.0, description="Warning threshold percentage"
    )

    # Circuit breaker config
    failure_threshold: int = Field(
        default=5, ge=1, description="Circuit breaker failure threshold"
    )
    circuit_timeout: float = Field(
        default=60.0, ge=0.1, description="Circuit breaker timeout seconds"
    )
    half_open_max_calls: int = Field(
        default=3, ge=1, description="Max calls in half-open state"
    )

    # Recursion config
    recursion_limit: int = Field(
        default=1000, ge=100, description="Maximum recursion depth"
    )

    # Resource limits
    memory_limit_mb: int = Field(default=1024, ge=64, description="Memory limit in MB")
    cpu_limit_percent: float = Field(
        default=80.0, ge=10.0, le=100.0, description="CPU usage limit percentage"
    )
    disk_min_free_mb: int = Field(
        default=100, ge=10, description="Minimum free disk space in MB"
    )

    # Progress monitoring
    stall_threshold_iterations: int = Field(
        default=10, ge=1, description="Iterations without progress before stall warning"
    )
    progress_update_interval: float = Field(
        default=1.0, ge=0.1, description="Progress update interval in seconds"
    )

    # Deadlock detection
    deadlock_timeout: float = Field(
        default=30.0, ge=1.0, description="Deadlock detection timeout"
    )

    # Emergency stop
    graceful_shutdown_timeout: float = Field(
        default=5.0, ge=1.0, description="Graceful shutdown timeout"
    )

    # Guard enable/disable
    enabled_guards: list[str] = Field(
        default_factory=lambda: [
            "MaxTurns",
            "Timeout",
            "CircuitBreaker",
            "RecursionDepth",
            "ProgressMonitor",
            "ResourceLimit",
            "DeadlockDetection",
            "EmergencyStop",
        ],
        description="List of enabled guards",
    )

    # Per-agent type overrides
    agent_type_overrides: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Per-agent type configuration overrides"
    )

    model_config = {"frozen": False}

    def get_config_for_agent(self, agent_type: str) -> "GuardConfig":
        """Get configuration with agent-specific overrides applied."""
        if agent_type not in self.agent_type_overrides:
            return self

        overrides = self.agent_type_overrides[agent_type]
        return self.model_copy(update=overrides)
