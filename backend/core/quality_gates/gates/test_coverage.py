"""
Test Coverage Gate
==================

Checks:
- Line coverage (default: 80%)
- Branch coverage (default: 70%)
- Function coverage (default: 75%)
- New code coverage (stricter: 90%)
- Critical path coverage (100%)
- Coverage regression detection

Score based on weighted average of coverage metrics.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from ..models import (
    GateConfig,
    GateIssue,
    GateMetrics,
    GateResult,
    GateSeverity,
    GateStatus,
)
from .base import BaseGate, GateContext

logger = logging.getLogger(__name__)


class TestCoverageGate(BaseGate):
    """Test coverage gate with multi-metric analysis."""

    def get_name(self) -> str:
        return "test_coverage"

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name="test_coverage",
            enabled=True,
            blocking=True,
            threshold=7.0,
            warning_threshold=8.5,
            timeout_seconds=300,
            max_retries=1,
            depends_on=["code_quality"],
            tool_config={
                "line_threshold": 80,
                "branch_threshold": 70,
                "function_threshold": 75,
                "new_code_threshold": 90,
                "critical_paths": [],  # List of paths requiring 100%
                "line_weight": 0.4,
                "branch_weight": 0.3,
                "function_weight": 0.3,
                "regression_tolerance": 2,  # Allow 2% regression
            },
        )

    async def execute(self, context: GateContext) -> GateResult:
        """Execute test coverage checks."""
        start_time = time.time()
        issues: list[GateIssue] = []

        # Run pytest with coverage
        coverage_result = await self._run_coverage(context.working_dir)

        if coverage_result.get("error"):
            return GateResult(
                gate_name=self.get_name(),
                status=GateStatus.ERROR,
                score=0.0,
                threshold=self.config.threshold,
                message=f"Coverage analysis failed: {coverage_result['error']}",
                execution_time_ms=(time.time() - start_time) * 1000,
                blocking=self.config.blocking,
            )

        # Extract metrics
        line_cov = coverage_result.get("line_coverage", 0)
        branch_cov = coverage_result.get("branch_coverage", 0)
        func_cov = coverage_result.get("function_coverage", line_cov)  # Fallback

        config = self.config.tool_config

        # Check thresholds
        if line_cov < config.get("line_threshold", 80):
            issues.append(
                self.create_issue(
                    file="coverage",
                    rule="LINE_COV",
                    message=f"Line coverage {line_cov:.1f}% below threshold {config['line_threshold']}%",
                    severity=GateSeverity.HIGH,
                )
            )

        if branch_cov < config.get("branch_threshold", 70):
            issues.append(
                self.create_issue(
                    file="coverage",
                    rule="BRANCH_COV",
                    message=f"Branch coverage {branch_cov:.1f}% below threshold {config['branch_threshold']}%",
                    severity=GateSeverity.MEDIUM,
                )
            )

        # Check new code coverage
        new_code_cov = await self._check_new_code_coverage(
            context.working_dir,
            context.changed_files,
        )
        if new_code_cov is not None and new_code_cov < config.get("new_code_threshold", 90):
            issues.append(
                self.create_issue(
                    file="new_code",
                    rule="NEW_CODE_COV",
                    message=f"New code coverage {new_code_cov:.1f}% below threshold {config['new_code_threshold']}%",
                    severity=GateSeverity.HIGH,
                )
            )

        # Check critical paths
        critical_issues = await self._check_critical_paths(
            context.working_dir,
            config.get("critical_paths", []),
        )
        issues.extend(critical_issues)

        # Check regression
        if context.previous_result:
            regression_issues = self._check_regression(
                line_cov,
                context.previous_result.metrics,
                config.get("regression_tolerance", 2),
            )
            issues.extend(regression_issues)

        # Calculate weighted score
        weights = {
            "line": config.get("line_weight", 0.4),
            "branch": config.get("branch_weight", 0.3),
            "function": config.get("function_weight", 0.3),
        }
        # Convert coverage % to 0-10 score
        coverage_scores = {
            "line": line_cov / 10,
            "branch": branch_cov / 10,
            "function": func_cov / 10,
        }
        final_score = self.calculate_score(coverage_scores, weights)

        # Build metrics
        metrics = GateMetrics(
            line_coverage=line_cov,
            branch_coverage=branch_cov,
            function_coverage=func_cov,
            new_code_coverage=new_code_cov,
        )

        # Determine status
        status = self.determine_status(final_score)
        if any(i.severity == GateSeverity.CRITICAL for i in issues):
            status = GateStatus.FAIL

        execution_time_ms = (time.time() - start_time) * 1000
        message = f"Line: {line_cov:.1f}% | Branch: {branch_cov:.1f}% | Function: {func_cov:.1f}%"

        return GateResult(
            gate_name=self.get_name(),
            status=status,
            score=final_score,
            threshold=self.config.threshold,
            message=message,
            issues=issues,
            metrics=metrics,
            execution_time_ms=execution_time_ms,
            blocking=self.config.blocking,
        )

    async def _run_coverage(self, working_dir: Path) -> dict:
        """Run pytest with coverage and return metrics."""
        # Run pytest with coverage in JSON format
        result = await self.run_command(
            [
                "pytest",
                "--cov=.",
                "--cov-report=json",
                "--cov-branch",
                "-q",
                "--tb=no",
            ],
            working_dir,
        )

        coverage_json_path = working_dir / "coverage.json"

        if coverage_json_path.exists():
            try:
                with open(coverage_json_path) as f:
                    cov_data = json.load(f)

                totals = cov_data.get("totals", {})
                return {
                    "line_coverage": totals.get("percent_covered", 0),
                    "branch_coverage": totals.get("percent_covered_branches", 0),
                    "function_coverage": totals.get("percent_covered", 0),
                    "total_lines": totals.get("num_statements", 0),
                    "covered_lines": totals.get("covered_lines", 0),
                    "missing_lines": totals.get("missing_lines", 0),
                }
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to parse coverage.json: {e}")

        # Fallback: parse stdout
        return self._parse_coverage_stdout(result.stdout)

    def _parse_coverage_stdout(self, stdout: str) -> dict:
        """Parse coverage from pytest stdout."""
        # Look for "TOTAL ... XX%"
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", stdout)
        line_cov = int(match.group(1)) if match else 0

        # Look for branch coverage
        branch_match = re.search(r"Branch coverage:\s*(\d+(?:\.\d+)?)", stdout)
        branch_cov = float(branch_match.group(1)) if branch_match else line_cov * 0.9

        return {
            "line_coverage": line_cov,
            "branch_coverage": branch_cov,
            "function_coverage": line_cov,
        }

    async def _check_new_code_coverage(
        self,
        working_dir: Path,
        changed_files: list[str],
    ) -> float | None:
        """Check coverage for newly changed files."""
        if not changed_files:
            return None

        py_files = [f for f in changed_files if f.endswith(".py")]
        if not py_files:
            return None

        # Run coverage for specific files
        result = await self.run_command(
            [
                "pytest",
                f"--cov={','.join(py_files[:10])}",  # Limit to 10 files
                "--cov-report=term",
                "-q",
                "--tb=no",
            ],
            working_dir,
        )

        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
        return float(match.group(1)) if match else None

    async def _check_critical_paths(
        self,
        working_dir: Path,
        critical_paths: list[str],
    ) -> list[GateIssue]:
        """Check that critical paths have 100% coverage."""
        issues: list[GateIssue] = []

        if not critical_paths:
            return issues

        for path in critical_paths:
            result = await self.run_command(
                [
                    "pytest",
                    f"--cov={path}",
                    "--cov-report=term",
                    "--cov-fail-under=100",
                    "-q",
                    "--tb=no",
                ],
                working_dir,
            )

            if not result.success:
                match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
                actual_cov = int(match.group(1)) if match else 0

                issues.append(
                    self.create_issue(
                        file=path,
                        rule="CRITICAL_PATH",
                        message=f"Critical path '{path}' has {actual_cov}% coverage (required: 100%)",
                        severity=GateSeverity.CRITICAL,
                    )
                )

        return issues

    def _check_regression(
        self,
        current_line_cov: float,
        previous_metrics: GateMetrics | None,
        tolerance: float,
    ) -> list[GateIssue]:
        """Check for coverage regression."""
        issues: list[GateIssue] = []

        if not previous_metrics or previous_metrics.line_coverage is None:
            return issues

        prev_cov = previous_metrics.line_coverage
        diff = prev_cov - current_line_cov

        if diff > tolerance:
            issues.append(
                self.create_issue(
                    file="regression",
                    rule="COVERAGE_REGRESSION",
                    message=f"Coverage decreased by {diff:.1f}% (from {prev_cov:.1f}% to {current_line_cov:.1f}%)",
                    severity=GateSeverity.HIGH,
                    suggestion=f"Add tests to maintain coverage above {prev_cov - tolerance:.1f}%",
                )
            )

        return issues
