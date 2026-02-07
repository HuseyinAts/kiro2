"""
Quality Gates Pipeline Orchestrator
====================================

Coordinates execution of all 8 quality gates with:
- Dependency-aware execution order
- Parallel execution for independent gates
- Timeout handling per gate
- Result aggregation
- Override workflow support

Boris Cherny verification standards.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Type

from .dependency_graph import DependencyGraph, build_gate_graph
from .models import (
    GateResult,
    GateStatus,
    OverrideApproval,
    OverrideRequest,
    PipelineConfig,
    PipelineResult,
)
from .gates.base import BaseGate, GateContext


logger = logging.getLogger(__name__)


class QualityGatesOrchestrator:
    """
    Orchestrates quality gate pipeline execution.

    Features:
    - Dependency-aware execution ordering
    - Parallel execution at each dependency level
    - Fail-fast mode (optional)
    - Override workflow for approved exceptions
    - Comprehensive result aggregation
    """

    def __init__(
        self,
        working_dir: Path,
        config: Optional[PipelineConfig] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            working_dir: Project root directory
            config: Pipeline configuration (uses defaults if not provided)
        """
        self.working_dir = working_dir
        self.config = config or self._default_config()
        self._gates: dict[str, BaseGate] = {}
        self._overrides: dict[str, OverrideApproval] = {}
        self._setup_gates()

    def _default_config(self) -> PipelineConfig:
        """Create default pipeline configuration."""
        return PipelineConfig(
            name="quality-gates",
            enabled=True,
            parallel_execution=True,
            fail_fast=False,
            timeout_seconds=600,
        )

    def _setup_gates(self) -> None:
        """Initialize all gates with their configurations."""
        from .gates import (
            CodeQualityGate,
            TestCoverageGate,
            SecurityGate,
            PerformanceGate,
            ArchitectureGate,
            DocumentationGate,
            ComplianceGate,
        )

        gate_classes: dict[str, Type[BaseGate]] = {
            "code_quality": CodeQualityGate,
            "test_coverage": TestCoverageGate,
            "security": SecurityGate,
            "performance": PerformanceGate,
            "architecture": ArchitectureGate,
            "documentation": DocumentationGate,
            "compliance": ComplianceGate,
        }

        for name, gate_class in gate_classes.items():
            gate_config = self.config.gates.get(name)
            gate = gate_class(gate_config)
            self._gates[name] = gate

    def register_gate(self, name: str, gate: BaseGate) -> None:
        """Register a custom gate."""
        self._gates[name] = gate

    def enable_gate(self, name: str) -> None:
        """Enable a gate."""
        if name in self._gates:
            self._gates[name].config = self._gates[name].config.model_copy(
                update={"enabled": True}
            )

    def disable_gate(self, name: str) -> None:
        """Disable a gate."""
        if name in self._gates:
            self._gates[name].config = self._gates[name].config.model_copy(
                update={"enabled": False}
            )

    async def run(
        self,
        commit_hash: Optional[str] = None,
        branch: Optional[str] = None,
        changed_files: Optional[list[str]] = None,
        triggered_by: Optional[str] = None,
    ) -> PipelineResult:
        """
        Run the complete quality gates pipeline.

        Args:
            commit_hash: Git commit hash
            branch: Git branch name
            changed_files: List of changed files (for targeted checks)
            triggered_by: Who/what triggered the pipeline

        Returns:
            PipelineResult with all gate results
        """
        start_time = time.time()
        started_at = datetime.now(timezone.utc)

        # Get git info if not provided
        if not commit_hash:
            commit_hash = self._get_git_commit()
        if not branch:
            branch = self._get_git_branch()
        if not changed_files:
            changed_files = self._get_changed_files()

        # Build dependency graph
        graph = self._build_dependency_graph()
        execution_levels = graph.get_execution_levels()

        gate_results: list[GateResult] = []
        failed_gates: set[str] = set()
        skipped_gates: set[str] = set()

        # Execute gates level by level
        for level in execution_levels:
            # Filter enabled gates that aren't skipped
            gates_to_run = [
                name for name in level.gates
                if name in self._gates
                and self._gates[name].config.enabled
                and name not in skipped_gates
            ]

            # Check dependencies for failures
            for gate_name in gates_to_run[:]:
                deps = self._gates[gate_name].get_dependencies()
                if any(d in failed_gates for d in deps):
                    skipped_gates.add(gate_name)
                    gates_to_run.remove(gate_name)
                    gate_results.append(self._skipped_result(gate_name))

            if not gates_to_run:
                continue

            # Run gates (parallel or sequential)
            if self.config.parallel_execution and len(gates_to_run) > 1:
                level_results = await self._run_parallel(
                    gates_to_run,
                    commit_hash,
                    branch,
                    changed_files,
                )
            else:
                level_results = await self._run_sequential(
                    gates_to_run,
                    commit_hash,
                    branch,
                    changed_files,
                )

            gate_results.extend(level_results)

            # Track failures
            for result in level_results:
                if not result.passed and result.blocking:
                    failed_gates.add(result.gate_name)

                    if self.config.fail_fast:
                        # Skip remaining gates
                        remaining = set(self._gates.keys()) - set(
                            r.gate_name for r in gate_results
                        )
                        for name in remaining:
                            skipped_gates.add(name)
                            gate_results.append(self._skipped_result(name))
                        break

            if self.config.fail_fast and failed_gates:
                break

        # Calculate final status and score
        total_execution_time = (time.time() - start_time) * 1000
        overall_status, total_score = self._calculate_overall_status(gate_results)

        passed = sum(1 for r in gate_results if r.passed)
        failed = sum(1 for r in gate_results if not r.passed and r.status != GateStatus.SKIPPED)
        skipped = sum(1 for r in gate_results if r.status == GateStatus.SKIPPED)

        return PipelineResult(
            pipeline_name=self.config.name,
            status=overall_status,
            gates=gate_results,
            total_score=total_score,
            passed_gates=passed,
            failed_gates=failed,
            skipped_gates=skipped,
            total_execution_time_ms=total_execution_time,
            parallel_execution_used=self.config.parallel_execution,
            commit_hash=commit_hash,
            branch=branch,
            triggered_by=triggered_by,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    async def _run_parallel(
        self,
        gate_names: list[str],
        commit_hash: Optional[str],
        branch: Optional[str],
        changed_files: list[str],
    ) -> list[GateResult]:
        """Run gates in parallel."""
        tasks = []

        for name in gate_names:
            context = GateContext(
                working_dir=self.working_dir,
                config=self._gates[name].config,
                commit_hash=commit_hash,
                branch=branch,
                changed_files=changed_files,
            )
            tasks.append(self._run_gate_with_timeout(name, context))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        final_results: list[GateResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(self._error_result(gate_names[i], str(result)))
            else:
                final_results.append(result)

        return final_results

    async def _run_sequential(
        self,
        gate_names: list[str],
        commit_hash: Optional[str],
        branch: Optional[str],
        changed_files: list[str],
    ) -> list[GateResult]:
        """Run gates sequentially."""
        results: list[GateResult] = []

        for name in gate_names:
            context = GateContext(
                working_dir=self.working_dir,
                config=self._gates[name].config,
                commit_hash=commit_hash,
                branch=branch,
                changed_files=changed_files,
            )
            result = await self._run_gate_with_timeout(name, context)
            results.append(result)

        return results

    async def _run_gate_with_timeout(
        self,
        gate_name: str,
        context: GateContext,
    ) -> GateResult:
        """Run a single gate with timeout."""
        gate = self._gates[gate_name]

        try:
            result = await asyncio.wait_for(
                gate.run(context),
                timeout=self.config.timeout_seconds,
            )

            # Check for override
            if not result.passed and gate_name in self._overrides:
                override = self._overrides[gate_name]
                if override.approved:
                    logger.info(f"Gate {gate_name} failure overridden by {override.approver}")
                    result.status = GateStatus.WARNING
                    result.details["overridden"] = True
                    result.details["override_reason"] = override.request.reason

            return result

        except asyncio.TimeoutError:
            return GateResult(
                gate_name=gate_name,
                status=GateStatus.TIMEOUT,
                score=0.0,
                threshold=gate.config.threshold,
                message=f"Gate timed out after {self.config.timeout_seconds}s",
                execution_time_ms=self.config.timeout_seconds * 1000,
                blocking=gate.config.blocking,
            )
        except Exception as e:
            logger.exception(f"Gate {gate_name} failed with exception")
            return self._error_result(gate_name, str(e))

    def _build_dependency_graph(self) -> DependencyGraph:
        """Build dependency graph from gate configurations."""
        gate_configs = {}

        for name, gate in self._gates.items():
            if gate.config.enabled:
                gate_configs[name] = {
                    "depends_on": gate.get_dependencies(),
                }

        return build_gate_graph(gate_configs)

    def _calculate_overall_status(
        self,
        results: list[GateResult],
    ) -> tuple[GateStatus, float]:
        """Calculate overall pipeline status and score."""
        if not results:
            return GateStatus.SKIPPED, 0.0

        # Check for blocking failures
        blocking_failures = [r for r in results if not r.passed and r.blocking]
        if blocking_failures:
            return GateStatus.FAIL, 0.0

        # Calculate weighted average score
        total_score = sum(r.score for r in results if r.status != GateStatus.SKIPPED)
        count = sum(1 for r in results if r.status != GateStatus.SKIPPED)
        avg_score = total_score / count if count > 0 else 0.0

        # Determine status from score
        if avg_score >= 8.0:
            status = GateStatus.PASS
        elif avg_score >= 6.0:
            status = GateStatus.WARNING
        else:
            status = GateStatus.FAIL

        return status, round(avg_score, 2)

    def _skipped_result(self, gate_name: str) -> GateResult:
        """Create a skipped result."""
        gate = self._gates.get(gate_name)
        return GateResult(
            gate_name=gate_name,
            status=GateStatus.SKIPPED,
            score=0.0,
            threshold=gate.config.threshold if gate else 7.0,
            message="Skipped due to dependency failure",
            execution_time_ms=0,
            blocking=gate.config.blocking if gate else True,
        )

    def _error_result(self, gate_name: str, error: str) -> GateResult:
        """Create an error result."""
        gate = self._gates.get(gate_name)
        return GateResult(
            gate_name=gate_name,
            status=GateStatus.ERROR,
            score=0.0,
            threshold=gate.config.threshold if gate else 7.0,
            message=f"Gate error: {error}",
            execution_time_ms=0,
            blocking=gate.config.blocking if gate else True,
        )

    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _get_git_branch(self) -> Optional[str]:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _get_changed_files(self) -> list[str]:
        """Get list of changed files."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")
        except Exception:
            pass
        return []

    # Override workflow methods

    def request_override(self, request: OverrideRequest) -> None:
        """Submit an override request for a failed gate."""
        logger.info(f"Override requested for gate {request.gate_name} by {request.requestor}")
        # In a real system, this would notify approvers

    def approve_override(self, approval: OverrideApproval) -> None:
        """Approve an override request."""
        if approval.approved:
            self._overrides[approval.request.gate_name] = approval
            logger.info(f"Override approved for {approval.request.gate_name} by {approval.approver}")

    def revoke_override(self, gate_name: str) -> None:
        """Revoke an existing override."""
        if gate_name in self._overrides:
            del self._overrides[gate_name]
            logger.info(f"Override revoked for {gate_name}")

    def get_override(self, gate_name: str) -> Optional[OverrideApproval]:
        """Get override status for a gate."""
        return self._overrides.get(gate_name)


# Convenience function
async def run_quality_gates(
    working_dir: Optional[Path] = None,
    config: Optional[PipelineConfig] = None,
) -> PipelineResult:
    """
    Run quality gates pipeline.

    Args:
        working_dir: Project directory (defaults to cwd)
        config: Pipeline configuration

    Returns:
        PipelineResult with all gate results
    """
    working_dir = working_dir or Path.cwd()
    orchestrator = QualityGatesOrchestrator(working_dir, config)
    return await orchestrator.run()
