"""
Base class for all quality check hooks.

Boris Cherny Standards - Verification Feedback Loops
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from .models import QualityCheckResult, HookConfig, ExitCode


class BaseHook(ABC):
    """Abstract base class for quality check hooks."""

    name: str = "base"

    def __init__(self, config: Optional[HookConfig] = None):
        """Initialize hook with optional config."""
        self.config = config or HookConfig()
        self._start_time: float = 0.0

    @abstractmethod
    async def run(self, files: List[str]) -> QualityCheckResult:
        """
        Run the quality check on given files.

        Args:
            files: List of file paths to check

        Returns:
            QualityCheckResult with check results
        """
        pass

    async def run_with_timeout(self, files: List[str]) -> QualityCheckResult:
        """
        Run hook with timeout enforcement.

        Args:
            files: List of file paths to check

        Returns:
            QualityCheckResult with check results
        """
        try:
            result = await asyncio.wait_for(
                self.run(files),
                timeout=self.config.timeout
            )

            # Warn if slow (> 10 seconds)
            if result.execution_time > 10.0:
                result.warnings.append(
                    f"Performance warning: {self.name} took "
                    f"{result.execution_time:.2f}s (> 10s threshold)"
                )

            return result

        except asyncio.TimeoutError:
            return QualityCheckResult(
                tool=self.name,
                passed=False,
                exit_code=ExitCode.BLOCKING_ERROR,
                errors=[f"Hook timed out after {self.config.timeout}s"],
                warnings=[],
                execution_time=self.config.timeout,
                files_checked=len(files)
            )

    def _start_timer(self) -> None:
        """Start execution timer."""
        self._start_time = time.perf_counter()

    def _stop_timer(self) -> float:
        """Stop timer and return elapsed time."""
        return time.perf_counter() - self._start_time

    async def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None
    ) -> tuple[int, str, str]:
        """
        Run a command asynchronously.

        Args:
            cmd: Command and arguments
            cwd: Working directory

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await process.communicate()
            return (
                process.returncode or 0,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace")
            )
        except FileNotFoundError:
            return (1, "", f"Command not found: {cmd[0]}")
        except Exception as e:
            return (1, "", str(e))

    def _run_command_sync(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None
    ) -> tuple[int, str, str]:
        """
        Run a command synchronously.

        Args:
            cmd: Command and arguments
            cwd: Working directory

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=self.config.timeout
            )
            return (result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return (1, "", f"Command timed out after {self.config.timeout}s")
        except FileNotFoundError:
            return (1, "", f"Command not found: {cmd[0]}")
        except Exception as e:
            return (1, "", str(e))

    def _filter_python_files(self, files: List[str]) -> List[str]:
        """Filter only Python files from list."""
        return [f for f in files if f.endswith(".py")]

    def _create_success_result(
        self,
        files_checked: int,
        execution_time: float,
        auto_fixed: int = 0,
        warnings: Optional[List[str]] = None
    ) -> QualityCheckResult:
        """Create a success result."""
        return QualityCheckResult(
            tool=self.name,
            passed=True,
            exit_code=ExitCode.SUCCESS,
            errors=[],
            warnings=warnings or [],
            execution_time=execution_time,
            files_checked=files_checked,
            auto_fixed=auto_fixed
        )

    def _create_error_result(
        self,
        errors: List[str],
        files_checked: int,
        execution_time: float,
        warnings: Optional[List[str]] = None
    ) -> QualityCheckResult:
        """Create an error result."""
        return QualityCheckResult(
            tool=self.name,
            passed=False,
            exit_code=ExitCode.BLOCKING_ERROR,
            errors=errors,
            warnings=warnings or [],
            execution_time=execution_time,
            files_checked=files_checked
        )
