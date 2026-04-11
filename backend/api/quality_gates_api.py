"""
Quality Gates API Endpoints
===========================

REST API endpoints for running and managing quality gates pipeline.

Endpoints:
- POST /api/quality-gates/run          - Trigger pipeline
- GET  /api/quality-gates/status       - Get gate configurations
- GET  /api/quality-gates/results/{id} - Get specific run results
- POST /api/quality-gates/override     - Request override
- GET  /api/quality-gates/history      - Get run history
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from api.schemas.quality_gates import (
    ApproveOverrideRequest,
    GateConfigResponse,
    GateIssueResponse,
    GateMetricsResponse,
    GateResultResponse,
    GateSeverityEnum,
    GateStatusEnum,
    OverrideRequestSchema,
    OverrideResponse,
    PipelineHistoryResponse,
    PipelineResultResponse,
    PipelineStatusResponse,
    QualityGatesErrorResponse,
    RunHistoryResponse,
    RunPipelineRequest,
)
from core.dependencies import (
    AuthenticatedUser,
    get_current_user,  # fixed: was auth_dependencies (no blacklist)
)
from core.structured_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/quality-gates", tags=["quality-gates"])

# In-memory storage for results (will be replaced with database)
_pipeline_results: dict[str, dict[str, Any]] = {}
_override_requests: dict[str, dict[str, Any]] = {}


def _convert_gate_status(status_value: str) -> GateStatusEnum:
    """Convert internal status to API enum."""
    mapping = {
        "pass": GateStatusEnum.PASS,
        "warning": GateStatusEnum.WARNING,
        "fail": GateStatusEnum.FAIL,
        "skipped": GateStatusEnum.SKIPPED,
        "timeout": GateStatusEnum.TIMEOUT,
        "error": GateStatusEnum.ERROR,
    }
    return mapping.get(status_value.lower(), GateStatusEnum.ERROR)


def _convert_severity(severity_value: str) -> GateSeverityEnum:
    """Convert internal severity to API enum."""
    mapping = {
        "critical": GateSeverityEnum.CRITICAL,
        "high": GateSeverityEnum.HIGH,
        "medium": GateSeverityEnum.MEDIUM,
        "low": GateSeverityEnum.LOW,
        "info": GateSeverityEnum.INFO,
    }
    return mapping.get(severity_value.lower(), GateSeverityEnum.MEDIUM)


@router.post(
    "/run",
    response_model=PipelineResultResponse,
    responses={
        500: {"model": QualityGatesErrorResponse},
    },
)
async def run_quality_gates(
    request: RunPipelineRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PipelineResultResponse:
    """
    Run quality gates pipeline.

    Triggers execution of configured quality gates on the codebase.
    Returns results with scores, issues, and metrics for each gate.
    """
    logger.info(
        "quality_gates_run_requested",
        user=current_user.email or "unknown",
        gates=request.gates,
        parallel=request.parallel,
    )

    try:
        from core.quality_gates.models import PipelineConfig
        from core.quality_gates.orchestrator import QualityGatesOrchestrator

        # Determine working directory
        working_dir = Path(request.working_dir) if request.working_dir else Path.cwd()

        if not working_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Working directory does not exist",
            )

        # Create pipeline config
        config = PipelineConfig(
            name="quality-gates",
            enabled=True,
            parallel_execution=request.parallel,
            fail_fast=request.fail_fast,
            timeout_seconds=request.timeout_seconds,
            report_formats=request.format,
        )

        # Create orchestrator
        orchestrator = QualityGatesOrchestrator(
            working_dir=working_dir,
            config=config,
        )

        # Run pipeline
        result = await orchestrator.run(gates=request.gates)

        # Generate run ID
        run_id = str(uuid.uuid4())

        # Convert gate results
        gate_responses = []
        for gate in result.gates:
            issues = [
                GateIssueResponse(
                    file=issue.file,
                    line=issue.line,
                    column=issue.column,
                    rule=issue.rule,
                    message=issue.message,
                    severity=_convert_severity(issue.severity.value),
                    suggestion=issue.suggestion,
                )
                for issue in gate.issues
            ]

            metrics = None
            if gate.metrics:
                metrics = GateMetricsResponse(
                    lint_score=gate.metrics.lint_score,
                    type_coverage=gate.metrics.type_coverage,
                    complexity_avg=gate.metrics.complexity_avg,
                    docstring_coverage=gate.metrics.docstring_coverage,
                    duplication_percent=gate.metrics.duplication_percent,
                    line_coverage=gate.metrics.line_coverage,
                    branch_coverage=gate.metrics.branch_coverage,
                    function_coverage=gate.metrics.function_coverage,
                    p50_ms=gate.metrics.p50_ms,
                    p95_ms=gate.metrics.p95_ms,
                    p99_ms=gate.metrics.p99_ms,
                    critical_vulns=gate.metrics.critical_vulns,
                    high_vulns=gate.metrics.high_vulns,
                    secrets_found=gate.metrics.secrets_found,
                    circular_deps_count=gate.metrics.circular_deps_count,
                    coupling_score=gate.metrics.coupling_score,
                    cohesion_score=gate.metrics.cohesion_score,
                )

            gate_responses.append(
                GateResultResponse(
                    gate_name=gate.gate_name,
                    status=_convert_gate_status(gate.status.value),
                    score=gate.score,
                    threshold=gate.threshold,
                    message=gate.message,
                    issues_count=len(gate.issues),
                    issues=issues,
                    metrics=metrics,
                    execution_time_ms=gate.execution_time_ms,
                    blocking=gate.blocking,
                    passed=gate.passed,
                )
            )

        # Build response
        response = PipelineResultResponse(
            run_id=run_id,
            pipeline_name=result.pipeline_name,
            status=_convert_gate_status(result.status.value),
            total_score=result.total_score,
            passed_gates=result.passed_gates,
            failed_gates=result.failed_gates,
            skipped_gates=result.skipped_gates,
            gates=gate_responses,
            total_execution_time_ms=result.total_execution_time_ms,
            parallel_execution_used=result.parallel_execution_used,
            commit_hash=result.commit_hash,
            branch=result.branch,
            triggered_by=current_user.email,
            started_at=result.started_at,
            completed_at=result.completed_at,
            passed=result.passed,
        )

        # Store result for later retrieval
        _pipeline_results[run_id] = response.model_dump()

        logger.info(
            "quality_gates_run_completed",
            run_id=run_id,
            status=response.status.value,
            total_score=response.total_score,
            passed_gates=response.passed_gates,
            failed_gates=response.failed_gates,
        )

        return response

    except ImportError as e:
        logger.error("quality_gates_import_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("quality_gates_run_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PipelineStatusResponse:
    """
    Get pipeline status and gate configurations.

    Returns current configuration for all quality gates including
    thresholds, timeouts, and dependencies.
    """
    try:
        from core.quality_gates.dependency_graph import DEFAULT_GATE_DEPENDENCIES
        from core.quality_gates.orchestrator import QualityGatesOrchestrator

        # Create orchestrator with default config to get gate info
        orchestrator = QualityGatesOrchestrator(working_dir=Path.cwd())

        # Get gate configurations
        gate_configs = []
        available_gates = []

        for gate_name, gate in orchestrator._gates.items():
            available_gates.append(gate_name)
            config = gate._config

            gate_configs.append(
                GateConfigResponse(
                    name=gate_name,
                    enabled=config.enabled if config else True,
                    blocking=config.blocking if config else True,
                    threshold=config.threshold if config else 7.0,
                    warning_threshold=config.warning_threshold if config else 8.0,
                    timeout_seconds=config.timeout_seconds if config else 120,
                    depends_on=DEFAULT_GATE_DEPENDENCIES.get(gate_name, []),
                )
            )

        return PipelineStatusResponse(
            pipeline_name=orchestrator.config.name,
            enabled=orchestrator.config.enabled,
            parallel_execution=orchestrator.config.parallel_execution,
            fail_fast=orchestrator.config.fail_fast,
            timeout_seconds=orchestrator.config.timeout_seconds,
            gates=gate_configs,
            available_gates=available_gates,
            total_gates=len(available_gates),
        )

    except ImportError as e:
        logger.error("quality_gates_import_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_pipeline_status_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/results/{run_id}", response_model=PipelineResultResponse)
async def get_run_results(
    run_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PipelineResultResponse:
    """
    Get results for a specific pipeline run.

    Returns full results including all gate scores, issues, and metrics.
    """
    if run_id not in _pipeline_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run not found: {run_id}",
        )

    result_data = _pipeline_results[run_id]
    return PipelineResultResponse(**result_data)


@router.get("/history", response_model=PipelineHistoryResponse)
async def get_run_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PipelineHistoryResponse:
    """
    Get pipeline run history.

    Returns paginated list of previous pipeline runs.
    """
    # Get all results sorted by started_at (newest first)
    all_results = list(_pipeline_results.values())
    all_results.sort(key=lambda x: x.get("started_at", ""), reverse=True)

    # Paginate
    total = len(all_results)
    start = (page - 1) * page_size
    end = start + page_size
    page_results = all_results[start:end]

    runs = [
        RunHistoryResponse(
            run_id=r["run_id"],
            status=GateStatusEnum(r["status"]),
            total_score=r["total_score"],
            passed_gates=r["passed_gates"],
            failed_gates=r["failed_gates"],
            execution_time_ms=r["total_execution_time_ms"],
            commit_hash=r.get("commit_hash"),
            branch=r.get("branch"),
            triggered_by=r.get("triggered_by"),
            started_at=r["started_at"],
            completed_at=r.get("completed_at"),
        )
        for r in page_results
    ]

    return PipelineHistoryResponse(
        total=total,
        page=page,
        page_size=page_size,
        runs=runs,
    )


@router.post("/override", response_model=OverrideResponse)
async def request_override(
    request: OverrideRequestSchema,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> OverrideResponse:
    """
    Request override for a failed gate.

    Creates an override request that requires approval before
    the gate failure can be bypassed.
    """
    logger.info(
        "override_requested",
        user=current_user.email,
        gate=request.gate_name,
        reason=request.reason[:50],  # Log first 50 chars
    )

    override_id = str(uuid.uuid4())
    expires_at = None
    if request.expires_hours:
        expires_at = datetime.now(UTC) + timedelta(hours=request.expires_hours)

    override_data = {
        "override_id": override_id,
        "gate_name": request.gate_name,
        "reason": request.reason,
        "requestor": current_user.email or "unknown",
        "ticket_id": request.ticket_id,
        "status": "pending",
        "expires_at": expires_at,
        "created_at": datetime.now(UTC),
    }

    _override_requests[override_id] = override_data

    return OverrideResponse(**override_data)


@router.get("/overrides", response_model=list[OverrideResponse])
async def list_overrides(
    status_filter: str | None = Query(None, description="Filter by status"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[OverrideResponse]:
    """
    List override requests.

    Returns all override requests, optionally filtered by status.
    """
    overrides = list(_override_requests.values())

    if status_filter:
        overrides = [o for o in overrides if o["status"] == status_filter]

    return [OverrideResponse(**o) for o in overrides]


@router.post("/overrides/{override_id}/approve")
async def approve_override(
    override_id: str,
    request: ApproveOverrideRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Approve or deny an override request.

    Requires admin role to approve overrides.
    """
    if override_id not in _override_requests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Override not found: {override_id}",
        )

    # Check if user has admin role
    user_role = current_user.role.value
    if user_role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can approve overrides",
        )

    override = _override_requests[override_id]
    override["status"] = "approved"
    override["approver"] = current_user.email
    override["approved_at"] = datetime.now(UTC)
    override["comments"] = request.comments

    logger.info(
        "override_approved",
        override_id=override_id,
        approver=current_user.email,
        gate=override["gate_name"],
    )

    return {
        "override_id": override_id,
        "approved": True,
        "approver": current_user.email,
        "approved_at": override["approved_at"].isoformat(),
        "comments": request.comments,
    }


@router.delete("/overrides/{override_id}")
async def delete_override(
    override_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, str]:
    """
    Delete/cancel an override request.

    Only the requestor or an admin can delete an override.
    """
    if override_id not in _override_requests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Override not found: {override_id}",
        )

    override = _override_requests[override_id]
    user_email = current_user.email
    user_role = current_user.role.value

    # Check permissions
    if override["requestor"] != user_email and user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requestor or an admin can delete this override",
        )

    del _override_requests[override_id]

    return {"message": f"Override {override_id} deleted successfully"}
