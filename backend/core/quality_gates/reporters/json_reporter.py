"""
JSON Reporter
=============

Machine-readable JSON output for CI/CD integration.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..models import GateResult, PipelineResult


class JsonReporter:
    """
    JSON reporter for quality gate results.

    Features:
    - Full pipeline result serialization
    - Metadata inclusion (timestamp, commit, branch)
    - Configurable output (file or stream)
    - Pretty or compact formatting
    """

    def __init__(
        self,
        output_path: Path | None = None,
        pretty: bool = True,
        include_details: bool = True,
    ):
        """
        Initialize JSON reporter.

        Args:
            output_path: Path to write JSON file (None for stdout)
            pretty: Use indented formatting
            include_details: Include full issue details
        """
        self.output_path = output_path
        self.pretty = pretty
        self.include_details = include_details

    def report(self, result: PipelineResult) -> str:
        """
        Generate JSON report.

        Args:
            result: Pipeline result to report

        Returns:
            JSON string
        """
        data = self._serialize_result(result)
        json_str = json.dumps(
            data,
            indent=2 if self.pretty else None,
            default=self._json_serializer,
        )

        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self.output_path.write_text(json_str, encoding="utf-8")

        return json_str

    def _serialize_result(self, result: PipelineResult) -> dict[str, Any]:
        """Serialize pipeline result to dict."""
        return {
            "pipeline": {
                "name": result.pipeline_name,
                "status": result.status.value,
                "total_score": result.total_score,
                "passed_gates": result.passed_gates,
                "failed_gates": result.failed_gates,
                "skipped_gates": result.skipped_gates,
                "parallel_execution": result.parallel_execution_used,
            },
            "execution": {
                "total_time_ms": result.total_execution_time_ms,
                "started_at": result.started_at.isoformat() if result.started_at else None,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            },
            "context": {
                "commit_hash": result.commit_hash,
                "branch": result.branch,
                "triggered_by": result.triggered_by,
            },
            "gates": [self._serialize_gate(g) for g in result.gates],
            "override": {
                "overridden": result.overridden,
                "reason": result.override_reason,
                "approver": result.override_approver,
            } if result.overridden else None,
            "metadata": {
                "report_generated_at": datetime.now(UTC).isoformat(),
                "reporter_version": "1.0.0",
            },
        }

    def _serialize_gate(self, gate: GateResult) -> dict[str, Any]:
        """Serialize gate result to dict."""
        data = {
            "name": gate.gate_name,
            "status": gate.status.value,
            "score": gate.score,
            "threshold": gate.threshold,
            "message": gate.message,
            "execution_time_ms": gate.execution_time_ms,
            "blocking": gate.blocking,
            "retries": gate.retries,
            "auto_fixed": gate.auto_fixed,
        }

        if self.include_details:
            data["issues"] = [
                {
                    "file": issue.file,
                    "line": issue.line,
                    "column": issue.column,
                    "rule": issue.rule,
                    "message": issue.message,
                    "severity": issue.severity.value,
                    "suggestion": issue.suggestion,
                }
                for issue in gate.issues
            ]

            if gate.metrics:
                data["metrics"] = {
                    k: v
                    for k, v in gate.metrics.model_dump().items()
                    if v is not None
                }

            data["details"] = gate.details

        return data

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "value"):  # Enum
            return obj.value
        if hasattr(obj, "model_dump"):  # Pydantic model
            return obj.model_dump()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class JsonSummaryReporter(JsonReporter):
    """
    Compact JSON reporter with summary only.

    Useful for dashboards and quick status checks.
    """

    def __init__(self, output_path: Path | None = None):
        super().__init__(output_path, pretty=True, include_details=False)

    def _serialize_result(self, result: PipelineResult) -> dict[str, Any]:
        """Serialize to compact summary."""
        return {
            "status": result.status.value,
            "score": result.total_score,
            "passed": result.passed_gates,
            "failed": result.failed_gates,
            "skipped": result.skipped_gates,
            "duration_ms": result.total_execution_time_ms,
            "commit": result.commit_hash,
            "branch": result.branch,
            "timestamp": datetime.now(UTC).isoformat(),
            "gates": {
                g.gate_name: {
                    "status": g.status.value,
                    "score": g.score,
                }
                for g in result.gates
            },
        }
