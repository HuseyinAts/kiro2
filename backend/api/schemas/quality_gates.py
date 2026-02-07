"""
Quality Gates API Schemas
=========================

Pydantic request/response schemas for Quality Gates API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

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

    working_dir: Optional[str] = Field(
        None,
        description="Working directory path. Uses current dir if not specified.",
    )
    gates: Optional[list[str]] = Field(
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
    ticket_id: Optional[str] = Field(
        None,
        description="Related ticket/issue ID.",
    )
    expires_hours: Optional[int] = Field(
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
    comments: Optional[str] = Field(None, description="Approver comments.")


# ==================== RESPONSE SCHEMAS ====================


class GateIssueResponse(BaseModel):
    """Single issue found by a gate."""

    file: str
    line: Optional[int] = None
    column: Optional[int] = None
    rule: str
    message: str
    severity: GateSeverityEnum
    suggestion: Optional[str] = None


class GateMetricsResponse(BaseModel):
    """Metrics collected by a gate."""

    # Code quality metrics
    lint_score: Optional[float] = None
    type_coverage: Optional[float] = None
    complexity_avg: Optional[float] = None
    docstring_coverage: Optional[float] = None
    duplication_percent: Optional[float] = None

    # Test coverage metrics
    line_coverage: Optional[float] = None
    branch_coverage: Optional[float] = None
    function_coverage: Optional[float] = None

    # Performance metrics
    p50_ms: Optional[float] = None
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None

    # Security metrics
    critical_vulns: Optional[int] = None
    high_vulns: Optional[int] = None
    secrets_found: Optional[int] = None

    # Architecture metrics
    circular_deps_count: Optional[int] = None
    coupling_score: Optional[float] = None
    cohesion_score: Optional[float] = None


class GateResultResponse(BaseModel):
    """Result from a single gate execution."""

    gate_name: str
    status: GateStatusEnum
    score: float = Field(ge=0, le=10)
    threshold: float = Field(ge=0, le=10)
    message: str
    issues_count: int
    issues: list[GateIssueResponse] = Field(default_factory=list)
    metrics: Optional[GateMetricsResponse] = None
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
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    triggered_by: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
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
    ticket_id: Optional[str] = None
    status: str  # pending, approved, denied, expired
    expires_at: Optional[datetime] = None
    created_at: datetime


class OverrideApprovalResponse(BaseModel):
    """Response for override approval."""

    override_id: str
    approved: bool
    approver: str
    comments: Optional[str] = None
    approved_at: datetime


class RunHistoryResponse(BaseModel):
    """Pipeline run history item."""

    run_id: str
    status: GateStatusEnum
    total_score: float
    passed_gates: int
    failed_gates: int
    execution_time_ms: float
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    triggered_by: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


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
    detail: Optional[str] = None
    gate_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
