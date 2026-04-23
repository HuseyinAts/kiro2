"""
Black Formatting Hook - REQ-5.1 to REQ-5.6

Automatic code formatting with Black.
Always exit 0 (formatting is non-blocking).
"""

from __future__ import annotations

import re

from .base import BaseHook
from .models import (
    ExitCode,
    HookConfig,
    QualityCheckResult,
)


class BlackHook(BaseHook):
    """
    Black formatting hook.

    REQ-5.1: Run black formatter on Python files
    REQ-5.2: Use line length 88 (Black default)
    REQ-5.3: Auto-save formatted files
    REQ-5.4: Ensure compatibility with Ruff
    REQ-5.5: Support check-only mode
    REQ-5.6: Show "Formatted X files" message
    """

    name = "black"

    async def run(self, files: list[str]) -> QualityCheckResult:
        """
        Run black formatting on files.

        Args:
            files: List of file paths to format

        Returns:
            QualityCheckResult with formatting results
        """
        self._start_timer()

        python_files = self._filter_python_files(files)
        if not python_files:
            return self._create_success_result(0, self._stop_timer())

        # Build command
        cmd = ["black"]

        # Line length
        cmd.extend(["--line-length", str(self.config.line_length)])

        # Check only mode
        if self.config.check_only:
            cmd.append("--check")
            cmd.append("--diff")
        else:
            cmd.append("--quiet")

        cmd.extend(python_files)

        # Run black
        return_code, stdout, stderr = await self._run_command(cmd)
        execution_time = self._stop_timer()

        # Count formatted files
        formatted_count = self._count_formatted(stdout + stderr, python_files)

        # In check mode, non-zero return means files need formatting
        if self.config.check_only and return_code != 0:
            needs_formatting = self._find_unformatted(stdout + stderr)
            return QualityCheckResult(
                tool=self.name,
                passed=False,
                exit_code=ExitCode.BLOCKING_ERROR,
                errors=[f"Files need formatting: {', '.join(needs_formatting)}"],
                warnings=[],
                execution_time=execution_time,
                files_checked=len(python_files)
            )

        # Success - report formatted files
        message = f"Formatted {formatted_count} file(s)" if formatted_count else "All files already formatted"

        return QualityCheckResult(
            tool=self.name,
            passed=True,
            exit_code=ExitCode.SUCCESS,
            errors=[],
            warnings=[message] if formatted_count > 0 else [],
            execution_time=execution_time,
            files_checked=len(python_files),
            auto_fixed=formatted_count
        )

    def _count_formatted(self, output: str, files: list[str]) -> int:
        """Count number of files that were formatted."""
        # Black reports "reformatted X files" or individual file names
        match = re.search(r"reformatted\s+(\d+)\s+file", output)
        if match:
            return int(match.group(1))

        # Count individual "reformatted" mentions
        count = output.lower().count("reformatted")
        return count

    def _find_unformatted(self, output: str) -> list[str]:
        """Find files that need formatting (in check mode)."""
        unformatted: list[str] = []

        # Black check mode shows "would reformat X"
        pattern = re.compile(r"would reformat\s+(.+?)$", re.MULTILINE)
        for match in pattern.finditer(output):
            unformatted.append(match.group(1).strip())

        return unformatted


async def run_black(
    files: list[str],
    config: HookConfig | None = None
) -> QualityCheckResult:
    """
    Convenience function to run black formatting.

    Args:
        files: Files to format
        config: Optional hook configuration

    Returns:
        QualityCheckResult
    """
    hook = BlackHook(config)
    return await hook.run_with_timeout(files)
