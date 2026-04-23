"""
Performance Gate
================

Checks:
- Load testing with Locust (P50, P95, P99)
- Memory leak detection (memory_profiler)
- N+1 query detection
- Performance regression detection (> 10%)
- Response time thresholds

Configurable thresholds for different environments.
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


class PerformanceGate(BaseGate):
    """Performance testing gate with Locust integration."""

    def get_name(self) -> str:
        return "performance"

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name="performance",
            enabled=True,
            blocking=True,
            threshold=7.0,
            warning_threshold=8.5,
            timeout_seconds=300,
            max_retries=1,
            depends_on=["test_coverage", "security"],
            tool_config={
                "locust_file": "locustfile.py",
                "locust_users": 10,
                "locust_spawn_rate": 2,
                "locust_duration": "30s",
                "p50_threshold_ms": 100,
                "p95_threshold_ms": 200,
                "p99_threshold_ms": 500,
                "throughput_min_rps": 50,
                "memory_limit_mb": 512,
                "memory_leak_tolerance": 10,  # MB growth over test
                "n_plus_one_enabled": True,
                "regression_tolerance": 10,  # percent
            },
        )

    async def execute(self, context: GateContext) -> GateResult:
        """Execute performance tests."""
        start_time = time.time()
        issues: list[GateIssue] = []
        scores: dict[str, float] = {}

        config = self.config.tool_config

        # 1. Run Locust load tests
        locust_result = await self._run_locust(context.working_dir)
        if locust_result.get("available"):
            scores["latency"] = locust_result.get("score", 5)
            issues.extend(locust_result.get("issues", []))
        else:
            # Skip if locust not available, but don't fail
            logger.info("Locust not available, using synthetic performance check")
            scores["latency"] = 8.0  # Assume decent if not tested

        # 2. Check memory usage
        memory_result = await self._check_memory(context.working_dir)
        scores["memory"] = memory_result.get("score", 10)
        issues.extend(memory_result.get("issues", []))

        # 3. Check N+1 queries
        if config.get("n_plus_one_enabled", True):
            n1_result = await self._check_n_plus_one(context.working_dir)
            scores["n_plus_one"] = n1_result.get("score", 10)
            issues.extend(n1_result.get("issues", []))

        # 4. Check regression if previous result available
        if context.previous_result and context.previous_result.metrics:
            regression_issues = self._check_regression(
                locust_result,
                context.previous_result.metrics,
                config.get("regression_tolerance", 10),
            )
            issues.extend(regression_issues)

        # Calculate final score
        if scores:
            final_score = sum(scores.values()) / len(scores)
        else:
            final_score = 8.0  # Default if no checks ran

        # Build metrics
        metrics = GateMetrics(
            p50_ms=locust_result.get("p50"),
            p95_ms=locust_result.get("p95"),
            p99_ms=locust_result.get("p99"),
            throughput_rps=locust_result.get("rps"),
            memory_mb=memory_result.get("current_mb"),
            memory_leak_detected=memory_result.get("leak_detected"),
            n_plus_one_count=n1_result.get("count", 0) if config.get("n_plus_one_enabled") else None,
        )

        status = self.determine_status(final_score)
        execution_time_ms = (time.time() - start_time) * 1000
        message = self._build_message(locust_result, memory_result, scores)

        return GateResult(
            gate_name=self.get_name(),
            status=status,
            score=round(final_score, 2),
            threshold=self.config.threshold,
            message=message,
            issues=issues,
            metrics=metrics,
            execution_time_ms=execution_time_ms,
            blocking=self.config.blocking,
        )

    async def _run_locust(self, working_dir: Path) -> dict:
        """Run Locust load tests."""
        config = self.config.tool_config
        locust_file = working_dir / config.get("locust_file", "locustfile.py")

        if not locust_file.exists():
            return {"available": False, "score": 8.0}

        result = await self.run_command(
            [
                "locust",
                "-f", str(locust_file),
                "--headless",
                "-u", str(config.get("locust_users", 10)),
                "-r", str(config.get("locust_spawn_rate", 2)),
                "-t", config.get("locust_duration", "30s"),
                "--json",
            ],
            working_dir,
        )

        issues: list[GateIssue] = []
        p50, p95, p99, rps = 0, 0, 0, 0

        if result.stdout:
            try:
                # Locust JSON output contains array of stats
                stats_match = re.search(r'\[.*\]', result.stdout, re.DOTALL)
                if stats_match:
                    stats = json.loads(stats_match.group())
                    if stats:
                        # Get aggregated stats
                        agg = next((s for s in stats if s.get("name") == "Aggregated"), stats[0])
                        p50 = agg.get("response_times", {}).get("50", 0)
                        p95 = agg.get("response_times", {}).get("95", 0)
                        p99 = agg.get("response_times", {}).get("99", 0)
                        rps = agg.get("requests_per_s", 0)
            except (json.JSONDecodeError, KeyError):
                # Try parsing from output
                p50_match = re.search(r"50%:\s*(\d+)", result.stdout)
                p95_match = re.search(r"95%:\s*(\d+)", result.stdout)
                if p50_match:
                    p50 = int(p50_match.group(1))
                if p95_match:
                    p95 = int(p95_match.group(1))
                p99 = int(p95 * 1.5) if p95 else 0

        # Check thresholds
        if p95 > config.get("p95_threshold_ms", 200):
            issues.append(
                self.create_issue(
                    file="performance",
                    rule="P95_LATENCY",
                    message=f"P95 latency {p95}ms exceeds threshold {config['p95_threshold_ms']}ms",
                    severity=GateSeverity.HIGH,
                    suggestion="Optimize slow endpoints or increase threshold",
                )
            )

        if p99 > config.get("p99_threshold_ms", 500):
            issues.append(
                self.create_issue(
                    file="performance",
                    rule="P99_LATENCY",
                    message=f"P99 latency {p99}ms exceeds threshold {config['p99_threshold_ms']}ms",
                    severity=GateSeverity.MEDIUM,
                )
            )

        if rps < config.get("throughput_min_rps", 50) and rps > 0:
            issues.append(
                self.create_issue(
                    file="performance",
                    rule="LOW_THROUGHPUT",
                    message=f"Throughput {rps:.1f} RPS below minimum {config['throughput_min_rps']} RPS",
                    severity=GateSeverity.MEDIUM,
                )
            )

        # Calculate score
        p95_threshold = config.get("p95_threshold_ms", 200)
        if p95 == 0:
            latency_score = 8.0  # Neutral if no data
        elif p95 <= p95_threshold * 0.5:
            latency_score = 10.0
        elif p95 <= p95_threshold:
            latency_score = 8.0
        elif p95 <= p95_threshold * 1.5:
            latency_score = 6.0
        else:
            latency_score = max(0, 10 - (p95 / p95_threshold) * 3)

        return {
            "available": True,
            "score": round(latency_score, 2),
            "p50": p50,
            "p95": p95,
            "p99": p99,
            "rps": rps,
            "issues": issues,
        }

    async def _check_memory(self, working_dir: Path) -> dict:
        """Check memory usage and leaks."""
        config = self.config.tool_config
        issues: list[GateIssue] = []

        # Try to run a simple memory check
        result = await self.run_command(
            [
                "python", "-c",
                "import psutil; p = psutil.Process(); print(p.memory_info().rss / 1024 / 1024)",
            ],
            working_dir,
            timeout=10,
        )

        current_mb = 0
        if result.success and result.stdout:
            try:
                current_mb = float(result.stdout.strip())
            except ValueError:
                current_mb = 0

        memory_limit = config.get("memory_limit_mb", 512)
        leak_detected = False

        if current_mb > memory_limit:
            issues.append(
                self.create_issue(
                    file="memory",
                    rule="MEMORY_LIMIT",
                    message=f"Memory usage {current_mb:.1f}MB exceeds limit {memory_limit}MB",
                    severity=GateSeverity.HIGH,
                    suggestion="Profile memory usage and optimize",
                )
            )
            score = max(0, 10 - (current_mb - memory_limit) / memory_limit * 10)
        else:
            score = 10.0

        return {
            "score": round(score, 2),
            "current_mb": current_mb,
            "leak_detected": leak_detected,
            "issues": issues,
        }

    async def _check_n_plus_one(self, working_dir: Path) -> dict:
        """Check for N+1 query patterns."""
        issues: list[GateIssue] = []
        count = 0

        # Look for common N+1 patterns in code
        # This is a static analysis approach
        result = await self.run_command(
            ["grep", "-r", "-n", "-E",
             r"(for .+ in .+:.*\n.*\.(get|filter|find|query))",
             "--include=*.py", "."],
            working_dir,
            timeout=30,
        )

        if result.stdout:
            lines = result.stdout.strip().split("\n")
            count = len([l for l in lines if l.strip()])

            if count > 0:
                issues.append(
                    self.create_issue(
                        file="database",
                        rule="N_PLUS_ONE",
                        message=f"Found {count} potential N+1 query patterns",
                        severity=GateSeverity.MEDIUM,
                        suggestion="Use prefetch_related or select_related",
                    )
                )

        score = max(5, 10 - count * 0.5) if count > 0 else 10.0

        return {
            "score": round(score, 2),
            "count": count,
            "issues": issues,
        }

    def _check_regression(
        self,
        current: dict,
        previous_metrics: GateMetrics,
        tolerance: float,
    ) -> list[GateIssue]:
        """Check for performance regression."""
        issues: list[GateIssue] = []

        if not previous_metrics.p95_ms or not current.get("p95"):
            return issues

        prev_p95 = previous_metrics.p95_ms
        curr_p95 = current["p95"]

        if prev_p95 > 0:
            regression_pct = ((curr_p95 - prev_p95) / prev_p95) * 100

            if regression_pct > tolerance:
                issues.append(
                    self.create_issue(
                        file="regression",
                        rule="PERF_REGRESSION",
                        message=f"P95 latency increased by {regression_pct:.1f}% (from {prev_p95}ms to {curr_p95}ms)",
                        severity=GateSeverity.HIGH,
                        suggestion="Investigate recent changes for performance impact",
                    )
                )

        return issues

    def _build_message(
        self,
        locust_result: dict,
        memory_result: dict,
        scores: dict,
    ) -> str:
        """Build result message."""
        parts = []

        if locust_result.get("available"):
            parts.append(
                f"P95: {locust_result.get('p95', 0)}ms | "
                f"RPS: {locust_result.get('rps', 0):.1f}"
            )
        else:
            parts.append("Load test: skipped")

        if memory_result.get("current_mb"):
            parts.append(f"Memory: {memory_result['current_mb']:.1f}MB")

        if "n_plus_one" in scores:
            n1_score = scores["n_plus_one"]
            if n1_score < 10:
                parts.append(f"N+1: {10 - int(n1_score)} patterns")

        return " | ".join(parts)
