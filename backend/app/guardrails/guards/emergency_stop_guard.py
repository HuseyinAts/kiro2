"""Emergency stop guard - provides emergency termination capability."""
import asyncio
import logging
import signal
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from ..models import GuardResult, GuardStatus
from .base_guard import BaseGuard

logger = logging.getLogger(__name__)


class EmergencyStopGuard(BaseGuard):
    """Provides emergency stop mechanism for critical situations.

    Configuration:
        graceful_timeout: Seconds to wait for graceful shutdown (default: 5.0)
        enable_signal_handlers: Enable SIGTERM/SIGINT handlers (default: True)
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize Emergency Stop guard.

        Args:
            config: Configuration with emergency stop settings
        """
        super().__init__(config)
        self.graceful_timeout: float = config.get("graceful_timeout", 5.0)
        self.enable_signal_handlers: bool = config.get("enable_signal_handlers", True)

        self._stop_triggered: bool = False
        self._stop_reason: str | None = None
        self._stop_time: float | None = None
        self._stop_signal: str | None = None
        self._lock = threading.Lock()

        # Callbacks
        self._pre_stop_callbacks: list[Callable[[], None]] = []
        self._post_stop_callbacks: list[Callable[[str], None]] = []

        # State for recovery
        self._saved_state: dict[str, Any] | None = None

        # Incident log
        self._incidents: list[dict[str, Any]] = []

        # Register signal handlers if enabled
        if self.enable_signal_handlers:
            self._register_signal_handlers()

    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Check if emergency stop has been triggered.

        Args:
            context: Execution context

        Returns:
            GuardResult with STOP if triggered, OK otherwise
        """
        self._increment_check_count()

        with self._lock:
            if self._stop_triggered:
                details = {
                    "reason": self._stop_reason,
                    "signal": self._stop_signal,
                    "time": self._stop_time,
                    "elapsed_since_trigger": time.time() - self._stop_time if self._stop_time else 0,
                }

                result = self._create_result(
                    status=GuardStatus.STOP,
                    message=f"Emergency stop triggered: {self._stop_reason}",
                    details=details,
                    should_stop=True
                )
                self._log_check(result)
                return result

        # Normal operation
        return self._create_result(
            status=GuardStatus.OK,
            message="Emergency stop not triggered",
            details={"checks": self._check_count},
            should_stop=False
        )

    def reset(self) -> None:
        """Reset emergency stop for new execution."""
        with self._lock:
            self._stop_triggered = False
            self._stop_reason = None
            self._stop_time = None
            self._stop_signal = None
        self._check_count = 0
        logger.debug("Emergency stop guard reset")

    def trigger(self, reason: str, signal_type: str = "MANUAL") -> None:
        """Trigger emergency stop.

        Args:
            reason: Reason for emergency stop
            signal_type: Type of signal (SIGTERM, SIGINT, MANUAL)
        """
        with self._lock:
            if self._stop_triggered:
                logger.warning(f"Emergency stop already triggered, ignoring: {reason}")
                return

            self._stop_triggered = True
            self._stop_reason = reason
            self._stop_time = time.time()
            self._stop_signal = signal_type

            # Log incident
            self._log_incident(reason, signal_type)

        logger.critical(f"EMERGENCY STOP triggered: {reason} ({signal_type})")

        # Execute pre-stop callbacks
        self._execute_pre_stop_callbacks()

    async def graceful_shutdown(
        self,
        running_tasks: list[asyncio.Task] | None = None
    ) -> bool:
        """Attempt graceful shutdown of running tasks.

        Args:
            running_tasks: List of tasks to cancel

        Returns:
            True if graceful shutdown succeeded, False otherwise
        """
        logger.info(f"Starting graceful shutdown (timeout: {self.graceful_timeout}s)")

        if not running_tasks:
            return True

        # Cancel all tasks
        for task in running_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        try:
            await asyncio.wait_for(
                asyncio.gather(*running_tasks, return_exceptions=True),
                timeout=self.graceful_timeout
            )
            logger.info("Graceful shutdown completed successfully")
            return True
        except TimeoutError:
            logger.warning("Graceful shutdown timed out, forcing termination")
            return False

    async def force_kill(self, process_id: int | None = None) -> None:
        """Force kill process if graceful shutdown fails.

        Args:
            process_id: Process ID to kill (default: current process)
        """
        import os
        import signal as sig

        pid = process_id or os.getpid()
        logger.warning(f"Force killing process {pid}")

        try:
            os.kill(pid, sig.SIGKILL)
        except Exception as e:
            logger.error(f"Failed to kill process: {e}")

    def save_state(self, state: dict[str, Any]) -> None:
        """Save state for potential recovery.

        Args:
            state: State dictionary to save
        """
        self._saved_state = {
            "timestamp": datetime.now(UTC).isoformat(),
            "data": state,
        }
        logger.info("State saved for recovery")

    def restore_state(self) -> dict[str, Any] | None:
        """Restore previously saved state.

        Returns:
            Saved state or None if no state saved
        """
        if self._saved_state:
            logger.info(f"Restoring state from {self._saved_state['timestamp']}")
            return self._saved_state["data"]
        return None

    def register_pre_stop_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to run before stop.

        Args:
            callback: Function to call before stop
        """
        self._pre_stop_callbacks.append(callback)

    def register_post_stop_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback to run after stop.

        Args:
            callback: Function taking stop reason
        """
        self._post_stop_callbacks.append(callback)

    def _register_signal_handlers(self) -> None:
        """Register OS signal handlers for graceful shutdown."""
        def signal_handler(signum: int, frame: Any) -> None:
            sig_name = signal.Signals(signum).name
            self.trigger(f"Received {sig_name}", sig_name)

        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            logger.debug("Signal handlers registered for SIGTERM and SIGINT")
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")

    def _execute_pre_stop_callbacks(self) -> None:
        """Execute all pre-stop callbacks."""
        for callback in self._pre_stop_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Pre-stop callback error: {e}")

    def _execute_post_stop_callbacks(self, reason: str) -> None:
        """Execute all post-stop callbacks.

        Args:
            reason: Stop reason to pass to callbacks
        """
        for callback in self._post_stop_callbacks:
            try:
                callback(reason)
            except Exception as e:
                logger.error(f"Post-stop callback error: {e}")

    def _log_incident(self, reason: str, signal_type: str) -> None:
        """Log an emergency stop incident.

        Args:
            reason: Reason for stop
            signal_type: Signal type that triggered stop
        """
        incident = {
            "timestamp": datetime.now(UTC).isoformat(),
            "reason": reason,
            "signal": signal_type,
            "check_count": self._check_count,
        }
        self._incidents.append(incident)
        logger.info(f"Incident logged: {incident}")

    def generate_post_mortem(self) -> dict[str, Any]:
        """Generate a post-mortem report.

        Returns:
            Dictionary with incident details and analysis
        """
        return {
            "stop_triggered": self._stop_triggered,
            "reason": self._stop_reason,
            "signal": self._stop_signal,
            "stop_time": datetime.fromtimestamp(self._stop_time).isoformat() if self._stop_time else None,
            "total_checks": self._check_count,
            "incidents": self._incidents,
            "saved_state_available": self._saved_state is not None,
            "analysis": {
                "root_cause": self._stop_reason or "Unknown",
                "recovery_possible": self._saved_state is not None,
                "recommended_action": "Review logs and saved state for debugging",
            }
        }

    @property
    def is_triggered(self) -> bool:
        """Check if emergency stop is triggered."""
        with self._lock:
            return self._stop_triggered
