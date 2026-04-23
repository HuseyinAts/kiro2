"""
isort Import Sorting Hook - REQ-6.1 to REQ-6.6

Automatic import sorting with Black compatibility.
"""

from __future__ import annotations

import re

from .base import BaseHook
from .models import (
    ExitCode,
    HookConfig,
    QualityCheckResult,
)


class IsortHook(BaseHook):
    """
    isort import sorting hook.

    REQ-6.1: Run isort on Python files
    REQ-6.2: Sort stdlib -> third-party -> local
    REQ-6.3: Use --profile black for compatibility
    REQ-6.4: Separate groups with blank lines
    REQ-6.5: Warn on unused imports (don't remove)
    REQ-6.6: Auto-save sorted files
    """

    name = "isort"

    async def run(self, files: list[str]) -> QualityCheckResult:
        """
        Run isort on files.

        Args:
            files: List of file paths to sort

        Returns:
            QualityCheckResult with sorting results
        """
        self._start_timer()

        python_files = self._filter_python_files(files)
        if not python_files:
            return self._create_success_result(0, self._stop_timer())

        # Build command
        cmd = [
            "isort",
            "--profile", "black",  # Black compatibility
            "--line-length", str(self.config.line_length),
        ]

        # Check only mode
        if self.config.check_only:
            cmd.append("--check-only")
            cmd.append("--diff")

        cmd.extend(python_files)

        # Run isort
        return_code, stdout, stderr = await self._run_command(cmd)
        execution_time = self._stop_timer()

        # Parse results
        output = stdout + stderr
        sorted_count = self._count_sorted(output)
        warnings = self._find_unused_imports(output)

        # Check mode failure
        if self.config.check_only and return_code != 0:
            needs_sorting = self._find_unsorted(output)
            return QualityCheckResult(
                tool=self.name,
                passed=False,
                exit_code=ExitCode.BLOCKING_ERROR,
                errors=[f"Files need import sorting: {', '.join(needs_sorting)}"],
                warnings=warnings,
                execution_time=execution_time,
                files_checked=len(python_files)
            )

        # Success
        return QualityCheckResult(
            tool=self.name,
            passed=True,
            exit_code=ExitCode.SUCCESS,
            errors=[],
            warnings=warnings,
            execution_time=execution_time,
            files_checked=len(python_files),
            auto_fixed=sorted_count
        )

    def _count_sorted(self, output: str) -> int:
        """Count files that were sorted."""
        # isort reports "Fixing X" for each file
        count = output.lower().count("fixing")
        if count == 0:
            # Alternative format "Sorted X imports"
            match = re.search(r"sorted\s+(\d+)", output.lower())
            if match:
                count = int(match.group(1))
        return count

    def _find_unsorted(self, output: str) -> list[str]:
        """Find files that need sorting."""
        unsorted: list[str] = []

        # isort check shows files that would be modified
        pattern = re.compile(r"would\s+(?:fix|sort)\s+(.+?)$", re.MULTILINE | re.IGNORECASE)
        for match in pattern.finditer(output):
            unsorted.append(match.group(1).strip())

        # Also check for "ERROR:" lines
        for line in output.split("\n"):
            if "ERROR:" in line or "would be sorted" in line.lower():
                # Extract filename
                parts = line.split()
                for part in parts:
                    if part.endswith(".py"):
                        unsorted.append(part)
                        break

        return list(set(unsorted))

    def _find_unused_imports(self, output: str) -> list[str]:
        """Find warnings about unused imports."""
        warnings: list[str] = []

        # Check for unused import mentions
        pattern = re.compile(
            r"(?:unused|unreferenced)\s+import[:\s]+([^\n]+)",
            re.IGNORECASE
        )
        for match in pattern.finditer(output):
            warnings.append(f"Unused import (not removed): {match.group(1).strip()}")

        return warnings


async def run_isort(
    files: list[str],
    config: HookConfig | None = None
) -> QualityCheckResult:
    """
    Convenience function to run isort.

    Args:
        files: Files to sort
        config: Optional hook configuration

    Returns:
        QualityCheckResult
    """
    hook = IsortHook(config)
    return await hook.run_with_timeout(files)
