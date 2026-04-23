"""
Pytest Auto-Run Hook - REQ-3.1 to REQ-3.6

Automatically runs related tests when code changes.
Exit code 2 for test failures.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseHook
from .models import (
    ExitCode,
    HookConfig,
    QualityCheckResult,
    TestResult,
)


class PytestHook(BaseHook):
    """
    Pytest auto-run hook.

    REQ-3.1: Find related test file for changed code
    REQ-3.2: Run pytest -x --tb=short
    REQ-3.3: Stop at first failure, show traceback
    REQ-3.4: Warn if no test found
    REQ-3.5: Exit code 2 if test fails
    REQ-3.6: Show green success message if all pass
    """

    name = "pytest"

    # Pattern to detect test failures
    FAILURE_PATTERN = re.compile(
        r"FAILED\s+(.+?)::([\w_]+)"
    )

    # Pattern to detect test errors
    ERROR_PATTERN = re.compile(
        r"ERROR\s+(.+?)::([\w_]+)"
    )

    async def run(self, files: list[str]) -> QualityCheckResult:
        """
        Run pytest on related test files.

        Args:
            files: List of changed file paths

        Returns:
            QualityCheckResult with test results
        """
        self._start_timer()

        python_files = self._filter_python_files(files)
        if not python_files:
            return self._create_success_result(0, self._stop_timer())

        # Find related test files
        test_files = self._find_related_tests(python_files)

        if not test_files:
            execution_time = self._stop_timer()
            return QualityCheckResult(
                tool=self.name,
                passed=True,
                exit_code=ExitCode.SUCCESS,
                errors=[],
                warnings=["No related test files found. Consider writing tests."],
                execution_time=execution_time,
                files_checked=len(python_files)
            )

        # Build pytest command
        cmd = [
            "pytest",
            "-x",           # Stop at first failure
            "--tb=short",   # Short traceback
            "-q",           # Quiet output
        ]
        cmd.extend(test_files)

        # Run pytest
        return_code, stdout, stderr = await self._run_command(cmd)
        execution_time = self._stop_timer()

        # Parse results
        output = stdout + stderr
        failures = self._parse_failures(output)
        errors = self._parse_errors(output)

        # Build result
        all_issues = failures + errors

        if all_issues or return_code != 0:
            error_messages = [
                f"{f.test_name}: {f.error_message or 'Test failed'}"
                for f in all_issues
            ]

            # Include traceback if available
            traceback = self._extract_traceback(output)
            if traceback:
                error_messages.append(f"Traceback:\n{traceback}")

            return QualityCheckResult(
                tool=self.name,
                passed=False,
                exit_code=ExitCode.BLOCKING_ERROR,
                errors=error_messages if error_messages else ["Test(s) failed"],
                warnings=[],
                execution_time=execution_time,
                files_checked=len(test_files)
            )

        # All tests passed
        return self._create_success_result(
            files_checked=len(test_files),
            execution_time=execution_time,
            warnings=[]
        )

    def _find_related_tests(self, files: list[str]) -> list[str]:
        """
        Find test files related to source files.

        Maps source files to test files using common patterns:
        - module.py -> test_module.py
        - module.py -> module_test.py
        - src/module.py -> tests/test_module.py
        """
        test_files: set[str] = set()

        for file_path in files:
            path = Path(file_path)

            # Skip if already a test file
            if path.name.startswith("test_") or path.name.endswith("_test.py"):
                test_files.add(str(path))
                continue

            # Skip non-Python files
            if not path.suffix == ".py":
                continue

            # Try different test file patterns
            candidates = self._get_test_candidates(path)
            for candidate in candidates:
                if candidate.exists():
                    test_files.add(str(candidate))

        return list(test_files)

    def _get_test_candidates(self, source_path: Path) -> list[Path]:
        """Get possible test file locations for a source file."""
        stem = source_path.stem
        parent = source_path.parent
        candidates: list[Path] = []

        # Same directory patterns
        candidates.append(parent / f"test_{stem}.py")
        candidates.append(parent / f"{stem}_test.py")

        # tests/ subdirectory
        candidates.append(parent / "tests" / f"test_{stem}.py")
        candidates.append(parent / "tests" / f"{stem}_test.py")

        # tests/ at project root (relative to backend/)
        if "backend" in str(parent):
            backend_idx = str(parent).find("backend")
            backend_root = Path(str(parent)[:backend_idx + 7])
            relative = source_path.relative_to(backend_root)
            test_path = backend_root / "tests" / relative.parent / f"test_{stem}.py"
            candidates.append(test_path)

        # __tests__ directory (Jest-style)
        candidates.append(parent / "__tests__" / f"test_{stem}.py")

        return candidates

    def _parse_failures(self, output: str) -> list[TestResult]:
        """Parse test failures from pytest output."""
        results: list[TestResult] = []

        for match in self.FAILURE_PATTERN.finditer(output):
            file_path, test_name = match.groups()
            results.append(TestResult(
                test_name=f"{file_path}::{test_name}",
                passed=False,
                error_message="Test assertion failed"
            ))

        return results

    def _parse_errors(self, output: str) -> list[TestResult]:
        """Parse test errors from pytest output."""
        results: list[TestResult] = []

        for match in self.ERROR_PATTERN.finditer(output):
            file_path, test_name = match.groups()
            results.append(TestResult(
                test_name=f"{file_path}::{test_name}",
                passed=False,
                error_message="Test error (exception raised)"
            ))

        return results

    def _extract_traceback(self, output: str) -> str | None:
        """Extract traceback from pytest output."""
        # Look for short traceback
        tb_start = output.find("=== FAILURES ===")
        if tb_start == -1:
            tb_start = output.find("=== ERRORS ===")

        if tb_start != -1:
            tb_end = output.find("=== short test summary", tb_start)
            if tb_end == -1:
                tb_end = len(output)
            return output[tb_start:tb_end].strip()[:1000]  # Limit size

        return None


async def run_pytest(
    files: list[str],
    config: HookConfig | None = None
) -> QualityCheckResult:
    """
    Convenience function to run pytest.

    Args:
        files: Files to find tests for
        config: Optional hook configuration

    Returns:
        QualityCheckResult
    """
    hook = PytestHook(config)
    return await hook.run_with_timeout(files)
