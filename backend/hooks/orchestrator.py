"""
PostToolUse Hook Orchestrator - REQ-8.1 to REQ-8.6

Orchestrates all quality hooks with parallel execution.
Boris Cherny Standards - %200-300 quality improvement.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import List, Optional

from .models import (
    QualityCheckResult,
    HookConfig,
    AggregatedResult,
    ExitCode,
)
from .base import BaseHook
from .ruff_hook import RuffHook
from .mypy_hook import MypyHook
from .pytest_hook import PytestHook
from .black_hook import BlackHook
from .isort_hook import IsortHook
from .docstring_hook import DocstringHook
from .reward_hacking_hook import RewardHackingHook

try:
    from ..utils.file_watcher import FileWatcher, get_changed_python_files
except ImportError:
    # Fallback for standalone execution
    import subprocess
    from pathlib import Path

    class FileWatcher:
        def __init__(self, repo_root=None):
            self.repo_root = repo_root or Path.cwd()

        def get_changed_python_files(self, staged_only=False, include_untracked=True):
            try:
                result = subprocess.run(
                    ["git", "diff", "--name-only", "HEAD"],
                    capture_output=True, text=True, cwd=self.repo_root
                )
                return [f for f in result.stdout.strip().split("\n") if f.endswith(".py")]
            except Exception:
                return []

    def get_changed_python_files(repo_root=None):
        return FileWatcher(repo_root).get_changed_python_files()


class PostToolUseOrchestrator:
    """
    Main orchestrator for PostToolUse hooks.

    REQ-8.1: Check only changed files
    REQ-8.3: Run hooks in parallel
    REQ-8.4: Log execution time for each hook
    REQ-8.5: Timeout 30s per hook
    REQ-8.6: Warn if hook is slow (> 10s)
    """

    def __init__(
        self,
        config: Optional[HookConfig] = None,
        enable_pytest: bool = True,
        enable_docstring: bool = True,
        enable_reward_hacking: bool = True
    ):
        """
        Initialize orchestrator.

        Args:
            config: Hook configuration
            enable_pytest: Enable pytest hook (can be slow)
            enable_docstring: Enable docstring validation
            enable_reward_hacking: Enable reward hacking detection
        """
        self.config = config or HookConfig()
        self.enable_pytest = enable_pytest
        self.enable_docstring = enable_docstring
        self.enable_reward_hacking = enable_reward_hacking

        # Initialize hooks
        self.ruff_hook = RuffHook(self.config)
        self.mypy_hook = MypyHook(self.config)
        self.pytest_hook = PytestHook(self.config) if enable_pytest else None
        self.black_hook = BlackHook(self.config)
        self.isort_hook = IsortHook(self.config)
        self.docstring_hook = DocstringHook(self.config) if enable_docstring else None
        self.reward_hacking_hook = RewardHackingHook(self.config) if enable_reward_hacking else None

        # File watcher for changed files
        self.file_watcher = FileWatcher()

    async def run_all_checks(
        self,
        files: Optional[List[str]] = None
    ) -> AggregatedResult:
        """
        Run all quality checks in parallel.

        Args:
            files: Optional list of files to check.
                   If None, uses git to find changed files.

        Returns:
            AggregatedResult with all check results
        """
        start_time = time.perf_counter()

        # Get files to check
        if files is None:
            files = self.file_watcher.get_changed_python_files()

        if not files:
            return AggregatedResult(
                total_checks=0,
                exit_code=ExitCode.SUCCESS
            )

        # Build list of hooks to run
        hooks: List[BaseHook] = [
            self.ruff_hook,
            self.mypy_hook,
            self.black_hook,
            self.isort_hook,
        ]

        if self.pytest_hook:
            hooks.append(self.pytest_hook)

        if self.docstring_hook:
            hooks.append(self.docstring_hook)

        if self.reward_hacking_hook:
            hooks.append(self.reward_hacking_hook)

        # Run all hooks in parallel
        tasks = [
            hook.run_with_timeout(files)
            for hook in hooks
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        aggregated = AggregatedResult()

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Hook raised an exception
                error_result = QualityCheckResult(
                    tool=hooks[i].name,
                    passed=False,
                    exit_code=ExitCode.BLOCKING_ERROR,
                    errors=[f"Hook error: {str(result)}"],
                    warnings=[],
                    execution_time=0.0,
                    files_checked=len(files)
                )
                aggregated.add_result(error_result)
            else:
                aggregated.add_result(result)

        aggregated.total_execution_time = time.perf_counter() - start_time

        return aggregated

    async def run_quick_checks(
        self,
        files: Optional[List[str]] = None
    ) -> AggregatedResult:
        """
        Run only fast checks (ruff, black, isort).

        Args:
            files: Files to check

        Returns:
            AggregatedResult
        """
        if files is None:
            files = self.file_watcher.get_changed_python_files()

        if not files:
            return AggregatedResult(exit_code=ExitCode.SUCCESS)

        tasks = [
            self.ruff_hook.run_with_timeout(files),
            self.black_hook.run_with_timeout(files),
            self.isort_hook.run_with_timeout(files),
        ]

        results = await asyncio.gather(*tasks)

        aggregated = AggregatedResult()
        for result in results:
            aggregated.add_result(result)

        return aggregated

    def format_results(self, results: AggregatedResult) -> str:
        """Format results for display."""
        lines: List[str] = []

        lines.append("=" * 60)
        lines.append("  VERIFICATION FEEDBACK LOOP - PostToolUse Hook")
        lines.append("  Boris Cherny: 'Kaliteyi %200-300 artiran dogrulama'")
        lines.append("=" * 60)
        lines.append("")

        for result in results.results:
            status = "[OK]" if result.passed else "[FAIL]"
            lines.append(f"{status} {result.tool}: {result.execution_time:.2f}s")

            if result.errors:
                for error in result.errors[:5]:  # Limit errors shown
                    lines.append(f"    ERROR: {error}")
                if len(result.errors) > 5:
                    lines.append(f"    ... and {len(result.errors) - 5} more errors")

            if result.warnings:
                for warning in result.warnings[:3]:
                    lines.append(f"    WARN: {warning}")

            if result.auto_fixed > 0:
                lines.append(f"    Auto-fixed: {result.auto_fixed} issues")

        lines.append("")
        lines.append("=" * 60)
        lines.append("  SUMMARY")
        lines.append("=" * 60)
        lines.append(f"  Passed: {results.passed_checks}/{results.total_checks}")
        lines.append(f"  Errors: {results.total_errors}")
        lines.append(f"  Warnings: {results.total_warnings}")
        lines.append(f"  Auto-fixed: {results.total_auto_fixed}")
        lines.append(f"  Total time: {results.total_execution_time:.2f}s")
        lines.append("")

        if results.all_passed:
            lines.append("[SUCCESS] All verification checks passed!")
        else:
            lines.append("[FAILED] Verification failed - fix issues above")
            lines.append(f"Exit code: {results.exit_code}")

        return "\n".join(lines)


async def run_orchestrator(
    files: Optional[List[str]] = None,
    quick: bool = False
) -> int:
    """
    Main entry point for running the orchestrator.

    Args:
        files: Files to check (None = use git diff)
        quick: Run only quick checks

    Returns:
        Exit code (0 = success, 2 = blocking error)
    """
    orchestrator = PostToolUseOrchestrator()

    if quick:
        results = await orchestrator.run_quick_checks(files)
    else:
        results = await orchestrator.run_all_checks(files)

    # Print results
    print(orchestrator.format_results(results))

    return results.exit_code


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Python Code Quality Hooks Orchestrator"
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="Files to check (default: git changed files)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only quick checks (ruff, black, isort)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a test check on backend/main.py"
    )

    args = parser.parse_args()

    if args.test:
        files = ["backend/main.py"]
    else:
        files = args.files

    exit_code = asyncio.run(run_orchestrator(files, args.quick))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
