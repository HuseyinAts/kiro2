"""Timeout guard - enforces maximum execution time."""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from ..models import GuardResult, GuardStatus
from .base_guard import BaseGuard

logger = logging.getLogger(__name__)


class TimeoutGuard(BaseGuard):
    """Enforces maximum execution time to prevent long-running operations.

    Configuration:
        timeout_seconds: Maximum execution time in seconds (default: 300)
        warning_threshold: Percentage at which to issue warning (default: 0.8)
        graceful_shutdown: Enable graceful shutdown on timeout (default: True)
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize Timeout guard.

        Args:
            config: Configuration with timeout_seconds and warning_threshold
        """
        super().__init__(config)
        self.timeout_seconds: float = config.get("timeout_seconds", 300)
        self.warning_threshold: float = config.get("warning_threshold", 0.8)
        self.graceful_shutdown: bool = config.get("graceful_shutdown", True)
        self.start_time: float | None = None
        self._warning_issued: bool = False
        # `callable` bir FONKSIYON, tip DEGIL (mypy: valid-type). Dogru tip
        # `collections.abc.Callable`.
        self._cleanup_callbacks: list[Callable[..., Any]] = []

    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Check if execution timeout exceeded.

        Args:
            context: Execution context (may contain elapsed_time)

        Returns:
            GuardResult with STOP if exceeded, WARNING if approaching, OK otherwise
        """
        self._increment_check_count()

        # Initialize start time on first check
        if self.start_time is None:
            self.start_time = time.time()

        elapsed = context.get("elapsed_time", time.time() - self.start_time)
        remaining = max(0, self.timeout_seconds - elapsed)

        details = {
            "elapsed_seconds": round(elapsed, 2),
            "timeout_seconds": self.timeout_seconds,
            "remaining_seconds": round(remaining, 2),
            "percentage": round(elapsed / self.timeout_seconds * 100, 1)
            if self.timeout_seconds > 0
            else 0,
        }

        # Check if exceeded
        if elapsed >= self.timeout_seconds:
            result = self._create_result(
                status=GuardStatus.STOP,
                message=f"Timeout exceeded: {elapsed:.2f}s/{self.timeout_seconds}s",
                details=details,
                should_stop=True,
            )
            logger.warning(
                f"Timeout exceeded: {elapsed:.2f}s >= {self.timeout_seconds}s"
            )

            # Trigger graceful shutdown if enabled
            if self.graceful_shutdown:
                await self._graceful_shutdown()

            self._log_check(result)
            return result

        # Check warning threshold
        warning_time = self.timeout_seconds * self.warning_threshold
        if elapsed >= warning_time and not self._warning_issued:
            self._warning_issued = True
            result = self._create_result(
                status=GuardStatus.WARNING,
                message=f"Approaching timeout: {elapsed:.2f}s/{self.timeout_seconds}s ({remaining:.1f}s remaining)",
                details=details,
                should_stop=False,
            )
            self._log_check(result)
            return result

        # Normal operation
        return self._create_result(
            status=GuardStatus.OK,
            message=f"Time elapsed: {elapsed:.2f}s/{self.timeout_seconds}s",
            details=details,
            should_stop=False,
        )

    def reset(self) -> None:
        """Reset timer for new execution."""
        self.start_time = None
        self._warning_issued = False
        self._check_count = 0
        logger.debug(f"Timeout guard reset (limit: {self.timeout_seconds}s)")

    def register_cleanup_callback(self, callback: Callable[..., Any]) -> None:
        """Register a callback to run during graceful shutdown.

        Args:
            callback: Async callable to run during shutdown
        """
        self._cleanup_callbacks.append(callback)

    async def _graceful_shutdown(self) -> None:
        """Execute graceful shutdown procedures."""
        logger.info("Starting graceful shutdown...")
        for callback in self._cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Cleanup callback error: {e}")
        logger.info("Graceful shutdown complete")

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since start."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    @property
    def remaining_time(self) -> float:
        """Get remaining time before timeout."""
        return max(0, self.timeout_seconds - self.elapsed_time)

    def get_eta(self, current_progress: float, total: float) -> float | None:
        """Estimate time to completion based on current progress.

        Args:
            current_progress: Current progress value
            total: Total progress value

        Returns:
            Estimated seconds to completion, or None if cannot estimate
        """
        if current_progress <= 0 or self.elapsed_time <= 0:
            return None

        progress_rate = current_progress / self.elapsed_time
        remaining_progress = total - current_progress

        if progress_rate > 0:
            return remaining_progress / progress_rate
        return None
