"""
Hook Manager - Orchestrates reward hacking detection.

Daisy Stanton Standards - Exit Code Management
Boris Cherny Standards - Verification Feedback Loops
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from .base_detector import BaseDetector

# Import all detectors
from .detectors import (
    AssertTrueDetector,
    CICDBypassDetector,
    CoverageManipulationDetector,
    EchoSuccessDetector,
    EmptyExceptionDetector,
    HardcodedTestDataDetector,
    MockAbuseDetector,
    PlaceholderDetector,
)
from .models.detection_result import (
    DetectionResult,
    DetectorConfig,
    GlobalConfig,
    HookResult,
)
from .models.enums import ExitCode, SeverityLevel


class HookManager:
    """
    Orchestrates reward hacking detection across multiple detectors.

    Runs all registered detectors in parallel and aggregates results.
    """

    # All available detector classes
    DETECTOR_CLASSES: list[type[BaseDetector]] = [
        AssertTrueDetector,
        EchoSuccessDetector,
        PlaceholderDetector,
        CoverageManipulationDetector,
        MockAbuseDetector,
        EmptyExceptionDetector,
        HardcodedTestDataDetector,
        CICDBypassDetector,
    ]

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.py', '.sh', '.yml', '.yaml', '.js', '.ts', '.tsx'}

    def __init__(self, config: GlobalConfig | None = None):
        """
        Initialize HookManager with optional configuration.

        Args:
            config: Optional global configuration
        """
        self.config = config or GlobalConfig()
        self.detectors: list[BaseDetector] = []
        self._register_detectors()

    def _register_detectors(self) -> None:
        """Register all detector instances."""
        self.detectors = []

        for detector_cls in self.DETECTOR_CLASSES:
            # Get detector-specific config if available
            detector_name = detector_cls.__name__
            detector_config = self.config.detectors.get(
                detector_name,
                DetectorConfig()
            )

            try:
                detector = detector_cls(config=detector_config)
                self.detectors.append(detector)
            except Exception as e:
                # Log but don't fail - other detectors can still work
                print(f"Warning: Failed to initialize {detector_name}: {e}")

    async def run_hooks(self, file_paths: list[str]) -> HookResult:
        """
        Run all detectors on given files.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            HookResult with aggregated results
        """
        if not self.config.enabled:
            return HookResult(
                exit_code=ExitCode.SUCCESS,
                summary="Reward hacking detection disabled"
            )

        start_time = time.perf_counter()
        all_results: list[DetectionResult] = []
        files_analyzed = 0

        # Filter to supported files
        valid_files = [
            f for f in file_paths
            if self._should_analyze(f)
        ][:self.config.max_files]

        # Process each file
        for file_path in valid_files:
            try:
                content = self._read_file(file_path)
                if content is None:
                    continue

                files_analyzed += 1

                # Run all detectors concurrently on this file
                results = await self._run_detectors(file_path, content)
                all_results.extend(results)

            except Exception as e:
                # Don't fail the entire run for one file
                print(f"Warning: Error analyzing {file_path}: {e}")

        # Calculate execution time
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Aggregate results
        return self._aggregate_results(
            all_results,
            execution_time_ms,
            files_analyzed
        )

    async def _run_detectors(
        self,
        file_path: str,
        content: str
    ) -> list[DetectionResult]:
        """
        Run all enabled detectors on a single file.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult objects
        """
        results: list[DetectionResult] = []

        # Create tasks for all detectors
        tasks = []
        for detector in self.detectors:
            if detector.is_enabled():
                task = self._run_detector_with_timeout(
                    detector, file_path, content
                )
                tasks.append(task)

        # Run all detectors concurrently
        if tasks:
            detector_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in detector_results:
                if isinstance(result, Exception):
                    # Log but don't fail
                    continue
                if result:
                    results.extend(result)

        return results

    async def _run_detector_with_timeout(
        self,
        detector: BaseDetector,
        file_path: str,
        content: str
    ) -> list[DetectionResult]:
        """
        Run a single detector with timeout.

        Args:
            detector: Detector instance
            file_path: Path to file
            content: File content

        Returns:
            List of DetectionResult objects
        """
        try:
            return await asyncio.wait_for(
                detector.detect(file_path, content),
                timeout=self.config.timeout_seconds
            )
        except TimeoutError:
            print(f"Warning: {detector.name} timed out on {file_path}")
            return []
        except Exception as e:
            print(f"Warning: {detector.name} failed on {file_path}: {e}")
            return []

    def _should_analyze(self, file_path: str) -> bool:
        """
        Check if file should be analyzed.

        Args:
            file_path: Path to check

        Returns:
            True if file should be analyzed
        """
        path = Path(file_path)
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _read_file(self, file_path: str) -> str | None:
        """
        Read file content safely.

        Args:
            file_path: Path to file

        Returns:
            File content or None if error
        """
        try:
            return Path(file_path).read_text(encoding='utf-8')
        except Exception:
            return None

    def _aggregate_results(
        self,
        results: list[DetectionResult],
        execution_time_ms: float,
        files_analyzed: int
    ) -> HookResult:
        """
        Aggregate detection results into HookResult.

        Args:
            results: List of all detection results
            execution_time_ms: Total execution time
            files_analyzed: Number of files analyzed

        Returns:
            HookResult with aggregated data
        """
        # Count by severity
        critical_count = sum(1 for r in results if r.severity == SeverityLevel.CRITICAL)
        warning_count = sum(1 for r in results if r.severity == SeverityLevel.WARNING)
        info_count = sum(1 for r in results if r.severity == SeverityLevel.INFO)

        # Determine exit code
        if critical_count > 0 or (warning_count > 0 and self.config.fail_on_warning):
            exit_code = ExitCode.BLOCKING_ERROR
        elif warning_count > 0:
            exit_code = ExitCode.WARNING
        else:
            exit_code = ExitCode.SUCCESS

        # Generate summary
        summary = self._generate_summary(results, critical_count, warning_count, info_count)

        return HookResult(
            exit_code=exit_code,
            total_detections=len(results),
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            results=results,
            summary=summary,
            execution_time_ms=execution_time_ms,
            files_analyzed=files_analyzed
        )

    def _generate_summary(
        self,
        results: list[DetectionResult],
        critical_count: int,
        warning_count: int,
        info_count: int
    ) -> str:
        """
        Generate human-readable summary.

        Args:
            results: All detection results
            critical_count: Number of critical issues
            warning_count: Number of warnings
            info_count: Number of info items

        Returns:
            Human-readable summary string
        """
        if not results:
            return "✅ No reward hacking patterns detected"

        lines = []

        if critical_count > 0:
            lines.append(f"❌ REWARD HACKING DETECTED - {critical_count} critical issue(s)")
        elif warning_count > 0:
            lines.append(f"⚠️ Warnings found - {warning_count} issue(s)")
        else:
            lines.append(f"ℹ️ Info items found - {info_count} item(s)")

        lines.append("")

        # Group by file
        by_file: dict[str, list[DetectionResult]] = {}
        for result in results:
            if result.file_path not in by_file:
                by_file[result.file_path] = []
            by_file[result.file_path].append(result)

        # Format each file's results
        for file_path, file_results in by_file.items():
            lines.append(f"📄 {file_path}")
            for result in file_results:
                severity_icon = {
                    SeverityLevel.CRITICAL: "🔴",
                    SeverityLevel.WARNING: "🟡",
                    SeverityLevel.INFO: "🔵",
                }.get(result.severity, "⚪")

                lines.append(f"  {severity_icon} Line {result.line_number}: {result.message}")
                lines.append(f"     Code: {result.code_snippet[:60]}...")
                lines.append(f"     Fix: {result.remediation[:60]}...")
            lines.append("")

        return "\n".join(lines)

    def get_detector_names(self) -> list[str]:
        """Get names of all registered detectors."""
        return [d.name for d in self.detectors]

    def enable_detector(self, name: str) -> bool:
        """Enable a specific detector by name."""
        for detector in self.detectors:
            if detector.name == name:
                detector.config.enabled = True
                return True
        return False

    def disable_detector(self, name: str) -> bool:
        """Disable a specific detector by name."""
        for detector in self.detectors:
            if detector.name == name:
                detector.config.enabled = False
                return True
        return False


async def run_reward_hacking_detection(
    file_paths: list[str],
    config: GlobalConfig | None = None
) -> HookResult:
    """
    Convenience function to run reward hacking detection.

    Args:
        file_paths: List of file paths to analyze
        config: Optional configuration

    Returns:
        HookResult with detection results
    """
    manager = HookManager(config=config)
    return await manager.run_hooks(file_paths)
