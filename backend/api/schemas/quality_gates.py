"""
Quality Gates API Schemas
=========================

Pydantic request/response schemas for Quality Gates API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class GateStatusEnum(str, Enum):
    """Gate execution status for API responses."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    ERROR = "error"


class GateSeverityEnum(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ==================== REQUEST SCHEMAS ====================


class RunPipelineRequest(BaseModel):
    """Request to run quality gates pipeline."""

    working_dir: str | None = Field(
        None,
        description="Working directory path. Uses current dir if not specified.",
    )
    gates: list[str] | None = Field(
        None,
        description="Specific gates to run. Runs all if not specified.",
    )
    parallel: bool = Field(
        True,
        description="Run independent gates in parallel.",
    )
    fail_fast: bool = Field(
        False,
        description="Stop on first blocking failure.",
    )
    timeout_seconds: int = Field(
        600,
        gt=0,
        le=1800,
        description="Pipeline timeout in seconds (max 30 min).",
    )
    format: list[str] = Field(
        default=["json"],
        description="Report formats: json, console, html",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "gates": ["code_quality", "test_coverage", "security"],
            "parallel": True,
            "fail_fast": False,
            "timeout_seconds": 300,
            "format": ["json", "console"],
        }
    })


class OverrideRequestSchema(BaseModel):
    """Request to override a gate failure."""

    gate_name: str = Field(
        ...,
        description="Gate identifier to override.",
    )
    reason: str = Field(
        ...,
        min_length=20,
        description="Justification for override (min 20 chars).",
    )
    ticket_id: str | None = Field(
        None,
        description="Related ticket/issue ID.",
    )
    expires_hours: int | None = Field(
        24,
        gt=0,
        le=168,
        description="Override expiration in hours (max 7 days).",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "gate_name": "test_coverage",
            "reason": "Emergency hotfix for production critical bug. Tests will be added in follow-up PR.",
            "ticket_id": "KIRO-1234",
            "expires_hours": 24,
        }
    })


class ApproveOverrideRequest(BaseModel):
    """Request to approve an override."""

    override_id: str = Field(..., description="Override request ID to approve.")
    comments: str | None = Field(None, description="Approver comments.")


# ==================== RESPONSE SCHEMAS ====================


class GateIssueResponse(BaseModel):
    """Single issue found by a gate."""

    file: str
    line: int | None = None
    column: int | None = None
    rule: str
    message: str
    severity: GateSeverityEnum
    suggestion: str | None = None


class GateMetricsResponse(BaseModel):
    """Metrics collected by a gate."""

    # Code quality metrics
    lint_score: float | None = None
    type_coverage: float | None = None
    complexity_avg: float | None = None
    docstring_coverage: float | None = None
    duplication_percent: float | None = None

    # Test coverage metrics
    line_coverage: float | None = None
    branch_coverage: float | None = None
    function_coverage: float | None = None

    # Performance metrics
    p50_ms: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None

    # Security metrics
    critical_vulns: int | None = None
    high_vulns: int | None = None
    secrets_found: int | None = None

    # Architecture metrics
    circular_deps_count: int | None = None
    coupling_score: float | None = None
    cohesion_score: float | None = None


class GateResultResponse(BaseModel):
    """Result from a single gate execution."""

    gate_name: str
    status: GateStatusEnum
    score: float = Field(ge=0, le=10)
    threshold: float = Field(ge=0, le=10)
    message: str
    issues_count: int
    issues: list[GateIssueResponse] = Field(default_factory=list)
    metrics: GateMetricsResponse | None = None
    execution_time_ms: float
    blocking: bool
    passed: bool


class PipelineResultResponse(BaseModel):
    """Response for pipeline run."""

    run_id: str = Field(..., description="Unique run identifier.")
    pipeline_name: str
    status: GateStatusEnum
    total_score: float = Field(ge=0, le=10)
    passed_gates: int
    failed_gates: int
    skipped_gates: int
    gates: list[GateResultResponse]
    total_execution_time_ms: float
    parallel_execution_used: bool
    commit_hash: str | None = None
    branch: str | None = None
    triggered_by: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    passed: bool


class GateConfigResponse(BaseModel):
    """Configuration for a gate."""

    name: str
    enabled: bool
    blocking: bool
    threshold: float
    warning_threshold: float
    timeout_seconds: int
    depends_on: list[str]


class PipelineStatusResponse(BaseModel):
    """Pipeline status and configuration."""

    pipeline_name: str
    enabled: bool
    parallel_execution: bool
    fail_fast: bool
    timeout_seconds: int
    gates: list[GateConfigResponse]
    available_gates: list[str]
    total_gates: int


class OverrideResponse(BaseModel):
    """Response for override request."""

    override_id: str
    gate_name: str
    reason: str
    requestor: str
    ticket_id: str | None = None
    status: str  # pending, approved, denied, expired
    expires_at: datetime | None = None
    created_at: datetime


class OverrideApprovalResponse(BaseModel):
    """Response for override approval."""

    override_id: str
    approved: bool
    approver: str
    comments: str | None = None
    approved_at: datetime


class RunHistoryResponse(BaseModel):
    """Pipeline run history item."""

    run_id: str
    status: GateStatusEnum
    total_score: float
    passed_gates: int
    failed_gates: int
    execution_time_ms: float
    commit_hash: str | None = None
    branch: str | None = None
    triggered_by: str | None = None
    started_at: datetime
    completed_at: datetime | None = None


class PipelineHistoryResponse(BaseModel):
    """Pipeline run history list."""

    total: int
    page: int
    page_size: int
    runs: list[RunHistoryResponse]


# ==================== ERROR RESPONSES ====================


class QualityGatesErrorResponse(BaseModel):
    """Error response for quality gates API."""

    error: str
    detail: str | None = None
    gate_name: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
