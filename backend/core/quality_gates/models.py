"""
Quality Gates Data Models
=========================

Pydantic models for quality gate pipeline.
Designed for extensibility and validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GateStatus(str, Enum):
    """Gate execution status."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    ERROR = "error"


class GateSeverity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class GateIssue(BaseModel):
    """Single issue found by a gate."""

    file: str = Field(..., description="File path where issue found")
    line: Optional[int] = Field(None, description="Line number")
    column: Optional[int] = Field(None, description="Column number")
    rule: str = Field(..., description="Rule/check identifier")
    message: str = Field(..., description="Issue description")
    severity: GateSeverity = Field(GateSeverity.MEDIUM, description="Severity level")
    suggestion: Optional[str] = Field(None, description="Fix suggestion")

    model_config = ConfigDict(frozen=True)


class GateMetrics(BaseModel):
    """Metrics collected by a gate."""

    # Code quality metrics
    lint_score: Optional[float] = Field(None, ge=0, le=10)
    type_coverage: Optional[float] = Field(None, ge=0, le=100)
    complexity_avg: Optional[float] = Field(None, ge=0)
    complexity_max: Optional[int] = Field(None, ge=0)
    docstring_coverage: Optional[float] = Field(None, ge=0, le=100)
    duplication_percent: Optional[float] = Field(None, ge=0, le=100)

    # Test coverage metrics
    line_coverage: Optional[float] = Field(None, ge=0, le=100)
    branch_coverage: Optional[float] = Field(None, ge=0, le=100)
    function_coverage: Optional[float] = Field(None, ge=0, le=100)
    new_code_coverage: Optional[float] = Field(None, ge=0, le=100)

    # Performance metrics
    p50_ms: Optional[float] = Field(None, ge=0)
    p95_ms: Optional[float] = Field(None, ge=0)
    p99_ms: Optional[float] = Field(None, ge=0)
    throughput_rps: Optional[float] = Field(None, ge=0)
    memory_mb: Optional[float] = Field(None, ge=0)
    memory_leak_detected: Optional[bool] = Field(None)
    n_plus_one_count: Optional[int] = Field(None, ge=0)

    # Architecture metrics
    circular_deps_count: Optional[int] = Field(None, ge=0)
    layer_violations_count: Optional[int] = Field(None, ge=0)
    coupling_score: Optional[float] = Field(None, ge=0, le=1)
    cohesion_score: Optional[float] = Field(None, ge=0, le=1)

    # Security metrics
    critical_vulns: Optional[int] = Field(None, ge=0)
    high_vulns: Optional[int] = Field(None, ge=0)
    medium_vulns: Optional[int] = Field(None, ge=0)
    low_vulns: Optional[int] = Field(None, ge=0)
    secrets_found: Optional[int] = Field(None, ge=0)

    # Compliance metrics
    gdpr_compliant: Optional[bool] = Field(None)
    kvkk_compliant: Optional[bool] = Field(None)
    audit_logs_complete: Optional[bool] = Field(None)
    pii_encrypted: Optional[bool] = Field(None)


class GateResult(BaseModel):
    """Result from a single gate execution."""

    gate_name: str = Field(..., description="Gate identifier")
    status: GateStatus = Field(..., description="Execution status")
    score: float = Field(..., ge=0, le=10, description="Quality score (0-10)")
    threshold: float = Field(..., ge=0, le=10, description="Pass threshold")
    message: str = Field(..., description="Result summary message")

    # Detailed data
    issues: list[GateIssue] = Field(default_factory=list, description="Issues found")
    metrics: Optional[GateMetrics] = Field(None, description="Collected metrics")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")

    # Execution info
    execution_time_ms: float = Field(..., ge=0, description="Execution duration")
    blocking: bool = Field(True, description="Is this a blocking gate?")
    retries: int = Field(0, ge=0, description="Number of retries")
    auto_fixed: bool = Field(False, description="Was auto-fix applied?")

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)

    @property
    def passed(self) -> bool:
        """Check if gate passed."""
        return self.status in (GateStatus.PASS, GateStatus.WARNING)

    @property
    def critical_issues(self) -> list[GateIssue]:
        """Get critical severity issues."""
        return [i for i in self.issues if i.severity == GateSeverity.CRITICAL]

    model_config = ConfigDict(frozen=False)


class GateConfig(BaseModel):
    """Configuration for a gate."""

    name: str = Field(..., description="Gate identifier")
    enabled: bool = Field(True, description="Is gate enabled?")
    blocking: bool = Field(True, description="Block pipeline on failure?")

    # Thresholds
    threshold: float = Field(7.0, ge=0, le=10, description="Pass threshold")
    warning_threshold: float = Field(8.0, ge=0, le=10, description="Warning threshold")

    # Execution settings
    timeout_seconds: int = Field(120, gt=0, description="Execution timeout")
    max_retries: int = Field(3, ge=0, description="Max retry attempts")
    retry_delay_seconds: int = Field(5, ge=0, description="Delay between retries")

    # Dependencies
    depends_on: list[str] = Field(default_factory=list, description="Gate dependencies")

    # Tool-specific settings
    tool_config: dict[str, Any] = Field(default_factory=dict, description="Tool configuration")

    @field_validator("warning_threshold")
    @classmethod
    def warning_must_be_higher(cls, v: float, info) -> float:
        """Warning threshold must be >= pass threshold."""
        threshold = info.data.get("threshold", 7.0)
        if v < threshold:
            raise ValueError("warning_threshold must be >= threshold")
        return v

    model_config = ConfigDict(frozen=True)


class PipelineConfig(BaseModel):
    """Pipeline configuration."""

    name: str = Field("quality-gates", description="Pipeline name")
    enabled: bool = Field(True, description="Is pipeline enabled?")

    # Execution settings
    parallel_execution: bool = Field(True, description="Run independent gates in parallel")
    fail_fast: bool = Field(False, description="Stop on first blocking failure")
    timeout_seconds: int = Field(600, gt=0, description="Total pipeline timeout")

    # Gate configurations
    gates: dict[str, GateConfig] = Field(default_factory=dict, description="Gate configs")

    # Reporting
    report_formats: list[str] = Field(
        default=["console", "json"],
        description="Report output formats",
    )
    report_path: str = Field("./reports/quality-gates", description="Report output path")

    # Override settings
    allow_override: bool = Field(True, description="Allow gate overrides")
    override_approvers: list[str] = Field(default_factory=list, description="Override approvers")


class PipelineResult(BaseModel):
    """Result from full pipeline execution."""

    pipeline_name: str = Field(..., description="Pipeline name")
    status: GateStatus = Field(..., description="Overall status")

    # Gate results
    gates: list[GateResult] = Field(default_factory=list, description="Gate results")

    # Aggregated metrics
    total_score: float = Field(..., ge=0, le=10, description="Weighted average score")
    passed_gates: int = Field(0, ge=0, description="Number of passed gates")
    failed_gates: int = Field(0, ge=0, description="Number of failed gates")
    skipped_gates: int = Field(0, ge=0, description="Number of skipped gates")

    # Execution info
    total_execution_time_ms: float = Field(..., ge=0, description="Total execution time")
    parallel_execution_used: bool = Field(False, description="Was parallel execution used?")

    # Context
    commit_hash: Optional[str] = Field(None, description="Git commit hash")
    branch: Optional[str] = Field(None, description="Git branch")
    triggered_by: Optional[str] = Field(None, description="Who triggered the pipeline")

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)

    # Override info
    overridden: bool = Field(False, description="Was result overridden?")
    override_reason: Optional[str] = Field(None, description="Override justification")
    override_approver: Optional[str] = Field(None, description="Who approved override")

    @property
    def passed(self) -> bool:
        """Check if pipeline passed."""
        return self.status in (GateStatus.PASS, GateStatus.WARNING)

    @property
    def blocking_failures(self) -> list[GateResult]:
        """Get blocking gate failures."""
        return [g for g in self.gates if not g.passed and g.blocking]

    def get_gate(self, name: str) -> Optional[GateResult]:
        """Get result for specific gate."""
        for gate in self.gates:
            if gate.gate_name == name:
                return gate
        return None

    model_config = ConfigDict(frozen=False)


class OverrideRequest(BaseModel):
    """Request to override gate failure."""

    gate_name: str = Field(..., description="Gate to override")
    reason: str = Field(..., min_length=20, description="Justification (min 20 chars)")
    requestor: str = Field(..., description="Who is requesting")
    ticket_id: Optional[str] = Field(None, description="Related ticket/issue")
    expires_at: Optional[datetime] = Field(None, description="Override expiration")

    model_config = ConfigDict(frozen=True)


class OverrideApproval(BaseModel):
    """Approval for override request."""

    request: OverrideRequest = Field(..., description="Original request")
    approved: bool = Field(..., description="Was it approved?")
    approver: str = Field(..., description="Who approved/denied")
    comments: Optional[str] = Field(None, description="Approver comments")
    approved_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)
