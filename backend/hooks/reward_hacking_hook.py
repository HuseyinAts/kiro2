"""
Reward Hacking Hook - PostToolUseOrchestrator Integration.

Wraps HookManager for orchestrator compatibility.
Boris Cherny Standards - Verification Feedback Loops
Daisy Stanton Standards - Exit Code Management
"""

from __future__ import annotations

from typing import List, Optional

from .base import BaseHook
from .models import QualityCheckResult, HookConfig, ExitCode
from .reward_hacking.hook_manager import HookManager


class RewardHackingHook(BaseHook):
    """
    Reward hacking detection hook for PostToolUseOrchestrator.

    Detects reward hacking patterns:
    - assert True / self.assertTrue(True)
    - echo Success / print("Success")
    - pass # placeholder / # TODO:
    - # pragma: no cover
    - Mock abuse (> 80% mocking)
    - except: pass
    - Hardcoded test data
    - CI/CD bypass attempts
    """

    name = "reward_hacking"

    def __init__(self, config: Optional[HookConfig] = None):
        """
        Initialize RewardHackingHook.

        Args:
            config: Optional hook configuration
        """
        super().__init__(config)
        self.manager = HookManager()

    async def run(self, files: List[str]) -> QualityCheckResult:
        """
        Run reward hacking detection on files.

        Args:
            files: List of file paths to check

        Returns:
            QualityCheckResult with detection results
        """
        self._start_timer()

        # Filter to supported file types
        supported_files = [
            f for f in files
            if any(f.endswith(ext) for ext in ['.py', '.sh', '.yml', '.yaml', '.js', '.ts', '.tsx'])
        ]

        if not supported_files:
            return self._create_success_result(
                files_checked=0,
                execution_time=self._stop_timer()
            )

        # Run detection via HookManager
        result = await self.manager.run_hooks(supported_files)

        execution_time = self._stop_timer()

        # Convert HookResult → QualityCheckResult
        # Note: Pydantic uses use_enum_values=True, so enums are already strings
        errors: List[str] = []
        warnings: List[str] = []

        for detection in result.results:
            # pattern_type is already a string due to use_enum_values=True
            pattern_type = detection.pattern_type
            message = f"{detection.file_path}:{detection.line_number}: [{pattern_type}] {detection.message}"

            # severity is also a string value
            if detection.severity == "CRITICAL":
                errors.append(message)
            elif detection.severity == "WARNING":
                warnings.append(message)

        # Map exit codes (Daisy Stanton standards)
        # Exit code is also converted to int due to use_enum_values=True
        exit_code = ExitCode.SUCCESS
        if result.exit_code == 2:  # BLOCKING_ERROR
            exit_code = ExitCode.BLOCKING_ERROR

        passed = result.critical_count == 0

        return QualityCheckResult(
            tool=self.name,
            passed=passed,
            exit_code=exit_code,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            files_checked=result.files_analyzed
        )
