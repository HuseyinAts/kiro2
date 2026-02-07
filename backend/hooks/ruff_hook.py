"""
Ruff Linting Hook - REQ-1.1 to REQ-1.6

Automatic linting with auto-fix capability.
Exit code 2 for critical errors (E, F).
"""

from __future__ import annotations

import re
from typing import List, Optional

from .base import BaseHook
from .models import (
    QualityCheckResult,
    HookConfig,
    ExitCode,
    LintError,
    ErrorCategory,
)


class RuffHook(BaseHook):
    """
    Ruff linting hook.

    REQ-1.1: Run ruff check on Python files
    REQ-1.2: Categorize errors (E, W, F)
    REQ-1.3: Auto-fix when possible
    REQ-1.4: Show detailed error messages with line numbers
    REQ-1.5: Exit code 2 for critical errors (E, F)
    REQ-1.6: Exit code 0 for warnings only
    """

    name = "ruff"

    # Pattern to parse ruff output: file:line:col: CODE message
    ERROR_PATTERN = re.compile(
        r"^(.+?):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$"
    )

    async def run(self, files: List[str]) -> QualityCheckResult:
        """
        Run ruff linting on files.

        Args:
            files: List of file paths to check

        Returns:
            QualityCheckResult with linting results
        """
        self._start_timer()

        python_files = self._filter_python_files(files)
        if not python_files:
            return self._create_success_result(0, self._stop_timer())

        # Build command
        cmd = ["ruff", "check"]
        if self.config.auto_fix:
            cmd.append("--fix")
        cmd.extend(["--select", "E,F,W"])  # Error, Fatal, Warning
        cmd.extend(python_files)

        # Run ruff
        return_code, stdout, stderr = await self._run_command(cmd)
        execution_time = self._stop_timer()

        # Parse output
        lint_errors = self._parse_output(stdout + stderr)

        # Categorize errors
        critical_errors = [e for e in lint_errors if e.is_critical]
        warnings = [e for e in lint_errors if not e.is_critical]

        # Count auto-fixed issues (from --fix output)
        auto_fixed = self._count_auto_fixed(stdout + stderr)

        # Build result
        if critical_errors:
            error_messages = [
                f"{e.file}:{e.line}:{e.column}: [{e.code}] {e.message}"
                for e in critical_errors
            ]
            warning_messages = [
                f"{e.file}:{e.line}:{e.column}: [{e.code}] {e.message}"
                for e in warnings
            ]
            return QualityCheckResult(
                tool=self.name,
                passed=False,
                exit_code=ExitCode.BLOCKING_ERROR,
                errors=error_messages,
                warnings=warning_messages,
                execution_time=execution_time,
                files_checked=len(python_files),
                auto_fixed=auto_fixed
            )

        # Only warnings - exit 0 but show warnings
        warning_messages = [
            f"{e.file}:{e.line}:{e.column}: [{e.code}] {e.message}"
            for e in warnings
        ]
        return self._create_success_result(
            files_checked=len(python_files),
            execution_time=execution_time,
            auto_fixed=auto_fixed,
            warnings=warning_messages
        )

    def _parse_output(self, output: str) -> List[LintError]:
        """Parse ruff output into LintError objects."""
        errors: List[LintError] = []

        for line in output.strip().split("\n"):
            match = self.ERROR_PATTERN.match(line.strip())
            if match:
                file_path, line_num, col, code, message = match.groups()
                category = self._get_category(code)
                errors.append(LintError(
                    file=file_path,
                    line=int(line_num),
                    column=int(col),
                    code=code,
                    message=message,
                    category=category,
                    fixable=self._is_fixable(code)
                ))

        return errors

    def _get_category(self, code: str) -> ErrorCategory:
        """Get error category from code."""
        if code.startswith("E"):
            return ErrorCategory.ERROR
        elif code.startswith("F"):
            return ErrorCategory.FATAL
        elif code.startswith("W"):
            return ErrorCategory.WARNING
        return ErrorCategory.INFO

    def _is_fixable(self, code: str) -> bool:
        """Check if error code is auto-fixable."""
        # Common fixable codes
        fixable_prefixes = ["E1", "E2", "E3", "W2", "W3", "F401"]
        return any(code.startswith(p) for p in fixable_prefixes)

    def _count_auto_fixed(self, output: str) -> int:
        """Count auto-fixed issues from ruff output."""
        # Ruff reports "Found X errors (Y fixed, Z remaining)"
        match = re.search(r"(\d+)\s+fixed", output)
        if match:
            return int(match.group(1))
        return 0


async def run_ruff(
    files: List[str],
    config: Optional[HookConfig] = None
) -> QualityCheckResult:
    """
    Convenience function to run ruff linting.

    Args:
        files: Files to check
        config: Optional hook configuration

    Returns:
        QualityCheckResult
    """
    hook = RuffHook(config)
    return await hook.run_with_timeout(files)
