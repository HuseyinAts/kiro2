"""
Base Gate Abstract Class
========================

Foundation for all quality gates.
Implements common functionality and interface.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..models import (
    GateConfig,
    GateIssue,
    GateMetrics,
    GateResult,
    GateSeverity,
    GateStatus,
)


logger = logging.getLogger(__name__)


@dataclass
class GateContext:
    """Context for gate execution."""

    working_dir: Path
    config: GateConfig
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    changed_files: list[str] = field(default_factory=list)
    previous_result: Optional[GateResult] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    """Result from running a shell command."""

    success: bool
    stdout: str
    stderr: str
    return_code: int
    duration_ms: float


class BaseGate(ABC):
    """
    Abstract base class for quality gates.

    Subclasses must implement:
    - execute(): Main gate logic
    - get_name(): Gate identifier
    - get_default_config(): Default configuration
    """

    def __init__(self, config: Optional[GateConfig] = None):
        """Initialize gate with configuration."""
        self.config = config or self.get_default_config()

    @abstractmethod
    def get_name(self) -> str:
        """Return gate identifier."""
        ...

    @abstractmethod
    def get_default_config(self) -> GateConfig:
        """Return default configuration for this gate."""
        ...

    @abstractmethod
    async def execute(self, context: GateContext) -> GateResult:
        """
        Execute the gate checks.

        Args:
            context: Execution context with working dir, config, etc.

        Returns:
            GateResult with status, score, issues, and metrics.
        """
        ...

    def get_dependencies(self) -> list[str]:
        """Return list of gate names this gate depends on."""
        return self.config.depends_on

    def is_blocking(self) -> bool:
        """Return whether this gate blocks the pipeline on failure."""
        return self.config.blocking

    async def run(self, context: GateContext) -> GateResult:
        """
        Run gate with timeout and retry handling.

        This is the main entry point - calls execute() internally.
        """
        start_time = time.time()
        retries = 0
        last_error: Optional[str] = None

        while retries <= self.config.max_retries:
            try:
                result = await asyncio.wait_for(
                    self.execute(context),
                    timeout=self.config.timeout_seconds,
                )
                result.retries = retries
                result.execution_time_ms = (time.time() - start_time) * 1000
                result.completed_at = datetime.now(timezone.utc)
                return result

            except asyncio.TimeoutError:
                logger.warning(
                    f"Gate {self.get_name()} timed out after {self.config.timeout_seconds}s"
                )
                return self._timeout_result(start_time)

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Gate {self.get_name()} attempt {retries + 1} failed: {e}"
                )
                retries += 1

                if retries <= self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay_seconds)

        # All retries exhausted
        return self._error_result(start_time, last_error or "Unknown error", retries)

    async def run_command(
        self,
        command: list[str],
        working_dir: Path,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """
        Run shell command asynchronously.

        Args:
            command: Command and arguments as list
            working_dir: Working directory
            timeout: Timeout in seconds (defaults to gate timeout)

        Returns:
            CommandResult with stdout, stderr, return code
        """
        timeout = timeout or self.config.timeout_seconds
        start = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            return CommandResult(
                success=process.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                return_code=process.returncode or 0,
                duration_ms=(time.time() - start) * 1000,
            )

        except asyncio.TimeoutError:
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                return_code=-1,
                duration_ms=timeout * 1000,
            )
        except FileNotFoundError as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Command not found: {e}",
                return_code=-1,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                duration_ms=(time.time() - start) * 1000,
            )

    def run_command_sync(
        self,
        command: list[str],
        working_dir: Path,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """
        Run shell command synchronously.

        For cases where async is not needed.
        """
        timeout = timeout or self.config.timeout_seconds
        start = time.time()

        try:
            result = subprocess.run(
                command,
                cwd=working_dir,
                capture_output=True,
                timeout=timeout,
                text=True,
            )

            return CommandResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                duration_ms=(time.time() - start) * 1000,
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                return_code=-1,
                duration_ms=timeout * 1000,
            )
        except FileNotFoundError as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Command not found: {e}",
                return_code=-1,
                duration_ms=(time.time() - start) * 1000,
            )

    def calculate_score(
        self,
        metrics: dict[str, float],
        weights: dict[str, float],
    ) -> float:
        """
        Calculate weighted score from multiple metrics.

        Args:
            metrics: Dict of metric_name -> value (0-10 scale)
            weights: Dict of metric_name -> weight (should sum to 1.0)

        Returns:
            Weighted average score (0-10)
        """
        total_weight = sum(weights.get(k, 0) for k in metrics.keys())
        if total_weight == 0:
            return 0.0

        score = sum(
            metrics[k] * weights.get(k, 0)
            for k in metrics.keys()
        )
        return round(score / total_weight, 2)

    def determine_status(self, score: float) -> GateStatus:
        """Determine gate status from score."""
        if score >= self.config.warning_threshold:
            return GateStatus.PASS
        elif score >= self.config.threshold:
            return GateStatus.WARNING
        else:
            return GateStatus.FAIL

    def create_issue(
        self,
        file: str,
        rule: str,
        message: str,
        line: Optional[int] = None,
        severity: GateSeverity = GateSeverity.MEDIUM,
        suggestion: Optional[str] = None,
    ) -> GateIssue:
        """Helper to create a GateIssue."""
        return GateIssue(
            file=file,
            line=line,
            rule=rule,
            message=message,
            severity=severity,
            suggestion=suggestion,
        )

    def _timeout_result(self, start_time: float) -> GateResult:
        """Create result for timeout."""
        return GateResult(
            gate_name=self.get_name(),
            status=GateStatus.TIMEOUT,
            score=0.0,
            threshold=self.config.threshold,
            message=f"Gate timed out after {self.config.timeout_seconds}s",
            execution_time_ms=(time.time() - start_time) * 1000,
            blocking=self.config.blocking,
            completed_at=datetime.now(timezone.utc),
        )

    def _error_result(
        self,
        start_time: float,
        error: str,
        retries: int,
    ) -> GateResult:
        """Create result for error."""
        return GateResult(
            gate_name=self.get_name(),
            status=GateStatus.ERROR,
            score=0.0,
            threshold=self.config.threshold,
            message=f"Gate failed with error: {error}",
            execution_time_ms=(time.time() - start_time) * 1000,
            blocking=self.config.blocking,
            retries=retries,
            completed_at=datetime.now(timezone.utc),
        )

    def _success_result(
        self,
        score: float,
        message: str,
        execution_time_ms: float,
        issues: Optional[list[GateIssue]] = None,
        metrics: Optional[GateMetrics] = None,
    ) -> GateResult:
        """Helper to create successful result."""
        status = self.determine_status(score)
        return GateResult(
            gate_name=self.get_name(),
            status=status,
            score=score,
            threshold=self.config.threshold,
            message=message,
            issues=issues or [],
            metrics=metrics,
            execution_time_ms=execution_time_ms,
            blocking=self.config.blocking,
            completed_at=datetime.now(timezone.utc),
        )
