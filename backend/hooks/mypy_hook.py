"""
Mypy Type Checking Hook - REQ-2.1 to REQ-2.6

Static type checking with strict mode support.
Exit code 2 for any type errors.
"""

from __future__ import annotations

import re
from typing import List, Optional

from .base import BaseHook
from .models import (
    QualityCheckResult,
    HookConfig,
    ExitCode,
    TypeErrorInfo,
)


class MypyHook(BaseHook):
    """
    Mypy type checking hook.

    REQ-2.1: Run mypy --ignore-missing-imports
    REQ-2.2: Show error message, line number, expected/actual type
    REQ-2.3: Warn on missing type hints
    REQ-2.4: Detect incompatible return types
    REQ-2.5: Exit code 2 if type errors > 0
    REQ-2.6: Support --strict mode
    """

    name = "mypy"

    # Pattern to parse mypy output: file:line: error: message [code]
    ERROR_PATTERN = re.compile(
        r"^(.+?):(\d+)(?::(\d+))?\s*:\s*(error|warning|note):\s*(.+?)(?:\s*\[([^\]]+)\])?$"
    )

    # Pattern for type mismatch - mypy format: (got "X", expected "Y")
    TYPE_MISMATCH_PATTERN = re.compile(
        r'got\s+"([^"]+)".*expected\s+"([^"]+)"'
    )

    async def run(self, files: List[str]) -> QualityCheckResult:
        """
        Run mypy type checking on files.

        Args:
            files: List of file paths to check

        Returns:
            QualityCheckResult with type checking results
        """
        self._start_timer()

        python_files = self._filter_python_files(files)
        if not python_files:
            return self._create_success_result(0, self._stop_timer())

        # Build command
        cmd = ["mypy", "--ignore-missing-imports"]

        if self.config.strict_mode:
            cmd.append("--strict")

        cmd.extend([
            "--no-error-summary",
            "--show-error-codes",
            "--show-column-numbers",
        ])
        cmd.extend(python_files)

        # Run mypy
        return_code, stdout, stderr = await self._run_command(cmd)
        execution_time = self._stop_timer()

        # Parse output
        type_errors = self._parse_output(stdout + stderr)
        errors = [e for e in type_errors if "error" in e.message.lower() or e.error_code]
        warnings = []

        # Check for missing type hints
        missing_hints = self._find_missing_hints(stdout + stderr)
        if missing_hints:
            warnings.extend(missing_hints)

        # Build result
        if errors:
            error_messages = [
                self._format_error(e) for e in errors
            ]
            return QualityCheckResult(
                tool=self.name,
                passed=False,
                exit_code=ExitCode.BLOCKING_ERROR,
                errors=error_messages,
                warnings=warnings,
                execution_time=execution_time,
                files_checked=len(python_files)
            )

        return self._create_success_result(
            files_checked=len(python_files),
            execution_time=execution_time,
            warnings=warnings
        )

    def _parse_output(self, output: str) -> List[TypeErrorInfo]:
        """Parse mypy output into TypeErrorInfo objects."""
        errors: List[TypeErrorInfo] = []

        for line in output.strip().split("\n"):
            match = self.ERROR_PATTERN.match(line.strip())
            if match:
                file_path, line_num, col, level, message, error_code = match.groups()

                if level == "error":
                    # Try to extract expected/actual types
                    expected, actual = self._extract_types(message)

                    errors.append(TypeErrorInfo(
                        file=file_path,
                        line=int(line_num),
                        column=int(col) if col else None,
                        message=message,
                        error_code=error_code,
                        expected_type=expected,
                        actual_type=actual
                    ))

        return errors

    def _extract_types(self, message: str) -> tuple[Optional[str], Optional[str]]:
        """Extract expected and actual types from error message.

        Returns:
            Tuple of (expected_type, actual_type) or (None, None)
        """
        match = self.TYPE_MISMATCH_PATTERN.search(message)
        if match:
            # Pattern captures: got="actual", expected="expected"
            # group(1) = actual, group(2) = expected
            actual, expected = match.group(1), match.group(2)
            return expected, actual
        return None, None

    def _find_missing_hints(self, output: str) -> List[str]:
        """Find warnings about missing type hints."""
        warnings: List[str] = []

        patterns = [
            r"Function is missing a type annotation",
            r"Function is missing a return type annotation",
            r"has no type annotation for",
        ]

        for line in output.split("\n"):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    warnings.append(f"Missing type hint: {line.strip()}")
                    break

        return warnings

    def _format_error(self, error: TypeErrorInfo) -> str:
        """Format error for display."""
        base = f"{error.file}:{error.line}"
        if error.column:
            base += f":{error.column}"

        msg = f"{base}: {error.message}"

        if error.error_code:
            msg += f" [{error.error_code}]"

        if error.expected_type and error.actual_type:
            msg += f" (expected: {error.expected_type}, got: {error.actual_type})"

        return msg


async def run_mypy(
    files: List[str],
    config: Optional[HookConfig] = None
) -> QualityCheckResult:
    """
    Convenience function to run mypy type checking.

    Args:
        files: Files to check
        config: Optional hook configuration

    Returns:
        QualityCheckResult
    """
    hook = MypyHook(config)
    return await hook.run_with_timeout(files)
