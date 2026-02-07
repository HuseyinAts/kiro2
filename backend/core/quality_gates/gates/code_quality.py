"""
Code Quality Gate
=================

Checks:
- Linting (ruff) - score 0-10
- Type checking (mypy) - score 0-10
- Complexity analysis (radon) - score 0-10
- Docstring coverage - warning if < 80%
- Code duplication - suggestion if > 5%

Weighted score: lint 40%, type 30%, complexity 30%
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
)
from .base import BaseGate, GateContext


logger = logging.getLogger(__name__)


class CodeQualityGate(BaseGate):
    """Code quality gate with lint, type check, and complexity analysis."""

    def get_name(self) -> str:
        return "code_quality"

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name="code_quality",
            enabled=True,
            blocking=True,
            threshold=7.0,
            warning_threshold=8.5,
            timeout_seconds=120,
            max_retries=2,
            depends_on=[],
            tool_config={
                "lint_weight": 0.4,
                "type_weight": 0.3,
                "complexity_weight": 0.3,
                "max_complexity": 10,
                "min_docstring_coverage": 80,
                "max_duplication_percent": 5,
            },
        )

    async def execute(self, context: GateContext) -> GateResult:
        """Execute code quality checks."""
        start_time = time.time()
        issues: list[GateIssue] = []
        scores: dict[str, float] = {}

        # 1. Run ruff linting
        lint_result = await self._run_lint(context.working_dir)
        scores["lint"] = lint_result["score"]
        issues.extend(lint_result["issues"])

        # 2. Run mypy type checking
        type_result = await self._run_type_check(context.working_dir)
        scores["type"] = type_result["score"]
        issues.extend(type_result["issues"])

        # 3. Run radon complexity
        complexity_result = await self._run_complexity(context.working_dir)
        scores["complexity"] = complexity_result["score"]
        issues.extend(complexity_result["issues"])

        # 4. Check docstring coverage (warning only)
        docstring_result = await self._check_docstrings(context.working_dir)

        # 5. Check code duplication (suggestion only)
        duplication_result = await self._check_duplication(context.working_dir)

        # Calculate weighted score
        config = self.config.tool_config
        weights = {
            "lint": config.get("lint_weight", 0.4),
            "type": config.get("type_weight", 0.3),
            "complexity": config.get("complexity_weight", 0.3),
        }
        final_score = self.calculate_score(scores, weights)

        # Build metrics
        metrics = GateMetrics(
            lint_score=scores.get("lint"),
            type_coverage=type_result.get("coverage"),
            complexity_avg=complexity_result.get("avg_complexity"),
            complexity_max=complexity_result.get("max_complexity"),
            docstring_coverage=docstring_result.get("coverage"),
            duplication_percent=duplication_result.get("percent"),
        )

        # Build message
        status = self.determine_status(final_score)
        message = self._build_message(scores, docstring_result, duplication_result)

        execution_time_ms = (time.time() - start_time) * 1000

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

    async def _run_lint(self, working_dir: Path) -> dict:
        """Run ruff linting."""
        result = await self.run_command(
            ["ruff", "check", ".", "--format", "json", "--output-format", "json"],
            working_dir,
        )

        issues: list[GateIssue] = []
        error_count = 0

        if result.stdout:
            try:
                lint_output = json.loads(result.stdout)
                error_count = len(lint_output)

                for item in lint_output[:50]:  # Limit to 50 issues
                    severity = self._map_lint_severity(item.get("code", ""))
                    issues.append(
                        self.create_issue(
                            file=item.get("filename", "unknown"),
                            line=item.get("location", {}).get("row"),
                            rule=item.get("code", "unknown"),
                            message=item.get("message", ""),
                            severity=severity,
                            suggestion=item.get("fix", {}).get("message"),
                        )
                    )
            except json.JSONDecodeError:
                # Fallback: count lines
                error_count = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

        # Score: 10 for 0 errors, decreasing
        score = max(0, 10 - (error_count * 0.5))
        score = min(10, score)

        return {
            "score": round(score, 2),
            "issues": issues,
            "error_count": error_count,
        }

    async def _run_type_check(self, working_dir: Path) -> dict:
        """Run mypy type checking."""
        result = await self.run_command(
            ["mypy", ".", "--ignore-missing-imports", "--no-error-summary"],
            working_dir,
        )

        issues: list[GateIssue] = []
        error_count = 0

        if result.stdout:
            lines = result.stdout.strip().split("\n")
            error_pattern = re.compile(r"(.+):(\d+): error: (.+)")

            for line in lines:
                match = error_pattern.match(line)
                if match:
                    error_count += 1
                    if error_count <= 50:
                        issues.append(
                            self.create_issue(
                                file=match.group(1),
                                line=int(match.group(2)),
                                rule="mypy",
                                message=match.group(3),
                                severity=GateSeverity.MEDIUM,
                            )
                        )

        # Score: 10 for 0 errors, decreasing
        score = max(0, 10 - (error_count * 0.3))
        score = min(10, score)

        # Estimate type coverage from success
        coverage = 100 if error_count == 0 else max(0, 100 - (error_count * 2))

        return {
            "score": round(score, 2),
            "issues": issues,
            "error_count": error_count,
            "coverage": coverage,
        }

    async def _run_complexity(self, working_dir: Path) -> dict:
        """Run radon complexity analysis."""
        result = await self.run_command(
            ["radon", "cc", ".", "-a", "-s", "--json"],
            working_dir,
        )

        issues: list[GateIssue] = []
        complexities: list[int] = []

        if result.stdout:
            try:
                complexity_data = json.loads(result.stdout)
                max_allowed = self.config.tool_config.get("max_complexity", 10)

                for filepath, functions in complexity_data.items():
                    for func in functions:
                        complexity = func.get("complexity", 0)
                        complexities.append(complexity)

                        if complexity > max_allowed:
                            issues.append(
                                self.create_issue(
                                    file=filepath,
                                    line=func.get("lineno"),
                                    rule="CC",
                                    message=f"Function '{func.get('name')}' has complexity {complexity} (max: {max_allowed})",
                                    severity=GateSeverity.MEDIUM if complexity <= 15 else GateSeverity.HIGH,
                                    suggestion="Consider refactoring to reduce complexity",
                                )
                            )
            except json.JSONDecodeError:
                pass

        # Calculate averages
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0

        # Score: based on average complexity (1-5 is good, >10 is bad)
        if avg_complexity <= 3:
            score = 10
        elif avg_complexity <= 5:
            score = 9
        elif avg_complexity <= 7:
            score = 8
        elif avg_complexity <= 10:
            score = 7
        elif avg_complexity <= 15:
            score = 5
        else:
            score = max(0, 10 - (avg_complexity - 10) * 0.5)

        return {
            "score": round(score, 2),
            "issues": issues,
            "avg_complexity": round(avg_complexity, 2),
            "max_complexity": max_complexity,
        }

    async def _check_docstrings(self, working_dir: Path) -> dict:
        """Check docstring coverage (warning only)."""
        result = await self.run_command(
            ["radon", "mi", ".", "-s", "--json"],
            working_dir,
        )

        total_items = 0
        documented = 0

        if result.stdout:
            try:
                mi_data = json.loads(result.stdout)
                for filepath, grade in mi_data.items():
                    total_items += 1
                    # A or B grade typically means documented
                    if grade in ("A", "B"):
                        documented += 1
            except json.JSONDecodeError:
                pass

        coverage = (documented / total_items * 100) if total_items > 0 else 0

        return {
            "coverage": round(coverage, 2),
            "total": total_items,
            "documented": documented,
        }

    async def _check_duplication(self, working_dir: Path) -> dict:
        """Check code duplication (suggestion only)."""
        # Try jscpd if available
        result = await self.run_command(
            ["jscpd", ".", "--min-lines", "5", "--reporters", "json", "--silent"],
            working_dir,
            timeout=60,
        )

        percent = 0.0

        if result.success and result.stdout:
            try:
                dup_data = json.loads(result.stdout)
                percent = dup_data.get("statistics", {}).get("total", {}).get("percentage", 0)
            except json.JSONDecodeError:
                pass

        return {
            "percent": round(percent, 2),
        }

    def _map_lint_severity(self, code: str) -> GateSeverity:
        """Map lint code to severity."""
        if code.startswith("E"):
            return GateSeverity.HIGH
        elif code.startswith("W"):
            return GateSeverity.MEDIUM
        elif code.startswith("F"):
            return GateSeverity.CRITICAL
        elif code.startswith("C"):
            return GateSeverity.LOW
        return GateSeverity.MEDIUM

    def _build_message(
        self,
        scores: dict[str, float],
        docstring_result: dict,
        duplication_result: dict,
    ) -> str:
        """Build result message."""
        parts = [
            f"Lint: {scores.get('lint', 0):.1f}/10",
            f"Type: {scores.get('type', 0):.1f}/10",
            f"Complexity: {scores.get('complexity', 0):.1f}/10",
        ]

        min_docstring = self.config.tool_config.get("min_docstring_coverage", 80)
        if docstring_result.get("coverage", 100) < min_docstring:
            parts.append(f"Docstring coverage: {docstring_result['coverage']:.1f}% (warning)")

        max_dup = self.config.tool_config.get("max_duplication_percent", 5)
        if duplication_result.get("percent", 0) > max_dup:
            parts.append(f"Duplication: {duplication_result['percent']:.1f}% (suggestion)")

        return " | ".join(parts)
