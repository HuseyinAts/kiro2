"""Progress monitor guard - detects stalls and tracks progress."""

import inspect
import logging
import time
from collections.abc import Callable
from typing import Any

from ..models import GuardResult, GuardStatus
from .base_guard import BaseGuard

logger = logging.getLogger(__name__)


class ProgressMonitorGuard(BaseGuard):
    """Monitors progress and detects stalls in long-running operations.

    Configuration:
        stall_threshold: Iterations without progress before warning (default: 10)
        progress_callback_interval: Seconds between callbacks (default: 1.0)
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize Progress Monitor guard.

        Args:
            config: Configuration with stall_threshold
        """
        super().__init__(config)
        self.stall_threshold: int = config.get("stall_threshold", 10)
        self.callback_interval: float = config.get("progress_callback_interval", 1.0)

        self.last_progress: float = 0.0
        self.iterations_without_progress: int = 0
        self.total_progress_updates: int = 0
        self.start_time: float | None = None
        self.last_callback_time: float = 0.0

        # Progress history for ETA calculation
        self._progress_history: list[tuple[float, float]] = []  # (timestamp, progress)
        # Donus tipi `None` DEGIL `Any`: `_fire_callbacks` async callback'leri
        # de kabul ediyor (`inspect.isawaitable(result)` -> `await result`).
        # `None` yazildiginda mypy o dali `Never`e daraltip `await`i hata
        # sayiyordu -- yani annotation kodun GERCEK sozlesmesini anlatmiyordu.
        self._progress_callbacks: list[Callable[[float, float | None], Any]] = []

    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Check progress and detect stalls.

        Args:
            context: Execution context containing:
                - progress: Current progress (0-100)
                - total: Total work units (optional)
                - completed: Completed work units (optional)

        Returns:
            GuardResult with WARNING if stalled, OK otherwise
        """
        self._increment_check_count()
        current_time = time.time()

        if self.start_time is None:
            self.start_time = current_time

        # Get progress from context
        progress = context.get("progress", 0.0)
        if "completed" in context and "total" in context:
            total = context["total"]
            completed = context["completed"]
            if total > 0:
                progress = (completed / total) * 100

        # Record progress
        self._progress_history.append((current_time, progress))
        # Keep only last 100 records
        if len(self._progress_history) > 100:
            self._progress_history = self._progress_history[-100:]

        # Calculate ETA
        eta = self._calculate_eta(progress)

        # Check for stall
        if progress <= self.last_progress:
            self.iterations_without_progress += 1
        else:
            self.iterations_without_progress = 0
            self.total_progress_updates += 1

        self.last_progress = progress

        details = {
            "progress_percent": round(progress, 2),
            "iterations_without_progress": self.iterations_without_progress,
            "stall_threshold": self.stall_threshold,
            "eta_seconds": round(eta, 1) if eta else None,
            "elapsed_seconds": round(current_time - self.start_time, 2),
        }

        # Fire callbacks if interval passed
        if current_time - self.last_callback_time >= self.callback_interval:
            self.last_callback_time = current_time
            await self._fire_callbacks(progress, eta)

        # Check for stall
        if self.iterations_without_progress >= self.stall_threshold:
            result = self._create_result(
                status=GuardStatus.WARNING,
                message=f"Progress stall detected: {self.iterations_without_progress} iterations without progress",
                details=details,
                should_stop=False,  # Warning only, don't stop
            )
            self._log_check(result)
            return result

        # Check for completion
        if progress >= 100:
            elapsed = current_time - self.start_time
            details["total_time_seconds"] = round(elapsed, 2)
            return self._create_result(
                status=GuardStatus.OK,
                message=f"Progress complete (100%) in {elapsed:.2f}s",
                details=details,
                should_stop=False,
            )

        # Normal operation
        return self._create_result(
            status=GuardStatus.OK,
            message=f"Progress: {progress:.1f}%"
            + (f" (ETA: {eta:.1f}s)" if eta else ""),
            details=details,
            should_stop=False,
        )

    def reset(self) -> None:
        """Reset progress monitor for new execution."""
        self.last_progress = 0.0
        self.iterations_without_progress = 0
        self.total_progress_updates = 0
        self.start_time = None
        self.last_callback_time = 0.0
        self._progress_history = []
        self._check_count = 0
        logger.debug(
            f"Progress monitor reset (stall threshold: {self.stall_threshold})"
        )

    def _calculate_eta(self, current_progress: float) -> float | None:
        """Calculate estimated time to completion.

        Args:
            current_progress: Current progress percentage

        Returns:
            Estimated seconds to completion, or None
        """
        if (
            len(self._progress_history) < 2
            or current_progress <= 0
            or current_progress >= 100
        ):
            return None

        # Use recent progress rate
        recent_start = self._progress_history[max(0, len(self._progress_history) - 10)]
        recent_end = self._progress_history[-1]

        time_diff = recent_end[0] - recent_start[0]
        progress_diff = recent_end[1] - recent_start[1]

        if time_diff <= 0 or progress_diff <= 0:
            return None

        progress_rate = progress_diff / time_diff  # % per second
        remaining_progress = 100 - current_progress

        if progress_rate > 0:
            return remaining_progress / progress_rate
        return None

    def register_progress_callback(
        self, callback: Callable[[float, float | None], Any]
    ) -> None:
        """Register a callback for progress updates.

        Args:
            callback: Function taking (progress_percent, eta_seconds)
        """
        self._progress_callbacks.append(callback)

    async def _fire_callbacks(self, progress: float, eta: float | None) -> None:
        """Fire all registered progress callbacks.

        Args:
            progress: Current progress percentage
            eta: Estimated time to completion
        """
        for callback in self._progress_callbacks:
            try:
                result = callback(progress, eta)
                # `inspect.isawaitable` mypy'da tip DARALTIR; `hasattr` ile
                # yapilan ayni kontrol daraltmadigi icin mypy `await result`i
                # `"None" has no attribute "__await__"` diye isaretliyordu.
                # Davranis ayni: senkron callback'ler await EDILMEZ.
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def get_progress_report(self) -> dict[str, Any]:
        """Generate a progress summary report.

        Returns:
            Dictionary with progress statistics
        """
        current_time = time.time()
        elapsed = current_time - self.start_time if self.start_time else 0

        return {
            "current_progress": self.last_progress,
            "elapsed_seconds": round(elapsed, 2),
            "total_updates": self.total_progress_updates,
            "stalls_detected": self.iterations_without_progress >= self.stall_threshold,
            "eta_seconds": self._calculate_eta(self.last_progress),
            "average_progress_rate": (
                self.last_progress / elapsed if elapsed > 0 else 0
            ),
        }

    def cancel(self) -> dict[str, Any]:
        """Cancel progress monitoring and return final report.

        Returns:
            Final progress report
        """
        report = self.get_progress_report()
        report["cancelled"] = True
        logger.info(f"Progress monitoring cancelled at {self.last_progress:.1f}%")
        return report
