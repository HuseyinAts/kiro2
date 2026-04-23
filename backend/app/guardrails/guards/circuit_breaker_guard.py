"""Circuit breaker guard - prevents cascade failures."""
import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

from ..models import GuardResult, GuardStatus
from .base_guard import BaseGuard

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"      # Normal operation, allowing requests
    OPEN = "OPEN"          # Blocking requests due to failures
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreakerGuard(BaseGuard):
    """Circuit breaker pattern to prevent cascade failures.

    State transitions:
    - CLOSED -> OPEN: After failure_threshold consecutive failures
    - OPEN -> HALF_OPEN: After timeout period expires
    - HALF_OPEN -> CLOSED: After successful calls
    - HALF_OPEN -> OPEN: On failure during half-open state

    Configuration:
        failure_threshold: Number of failures before opening (default: 5)
        timeout: Seconds before transitioning to half-open (default: 60)
        half_open_max_calls: Successful calls needed to close (default: 3)
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize Circuit Breaker guard.

        Args:
            config: Configuration with failure_threshold, timeout, half_open_max_calls
        """
        super().__init__(config)
        self.failure_threshold: int = config.get("failure_threshold", 5)
        self.timeout: float = config.get("timeout", 60)
        self.half_open_max_calls: int = config.get("half_open_max_calls", 3)

        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.last_failure_time: float | None = None
        self.half_open_calls: int = 0

        # Event callbacks
        self._state_change_callbacks: list[Callable[[CircuitState, CircuitState], None]] = []

    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Check circuit breaker state and update based on operation result.

        Args:
            context: Execution context containing:
                - last_operation_failed: Whether the last operation failed

        Returns:
            GuardResult with STOP if circuit is open, OK otherwise
        """
        self._increment_check_count()
        current_time = time.time()

        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (current_time - self.last_failure_time >= self.timeout):
                self._transition_state(CircuitState.HALF_OPEN)
                self.half_open_calls = 0
            else:
                time_until_retry = self.timeout - (current_time - (self.last_failure_time or current_time))
                return self._create_result(
                    status=GuardStatus.STOP,
                    message="Circuit breaker is OPEN, blocking execution",
                    details={
                        "state": self.state.value,
                        "failure_count": self.failure_count,
                        "time_until_retry": round(max(0, time_until_retry), 1),
                    },
                    should_stop=True
                )

        # Process operation result
        operation_failed = context.get("last_operation_failed", False)

        if operation_failed:
            return await self._handle_failure(current_time)
        return await self._handle_success()

    async def _handle_failure(self, current_time: float) -> GuardResult:
        """Handle a failed operation.

        Args:
            current_time: Current timestamp

        Returns:
            GuardResult indicating circuit state
        """
        self.failure_count += 1
        self.last_failure_time = current_time
        self.success_count = 0  # Reset success count on failure

        details = {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "threshold": self.failure_threshold,
        }

        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state, reopen circuit
            self._transition_state(CircuitState.OPEN)
            result = self._create_result(
                status=GuardStatus.STOP,
                message="Circuit breaker reopened due to failure in HALF_OPEN state",
                details=details,
                should_stop=True
            )
            self._log_check(result)
            return result

        if self.failure_count >= self.failure_threshold:
            # Threshold reached, open circuit
            self._transition_state(CircuitState.OPEN)
            result = self._create_result(
                status=GuardStatus.STOP,
                message=f"Circuit breaker opened after {self.failure_count} failures",
                details=details,
                should_stop=True
            )
            self._log_check(result)
            return result

        # Not enough failures yet
        return self._create_result(
            status=GuardStatus.WARNING,
            message=f"Failure recorded: {self.failure_count}/{self.failure_threshold}",
            details=details,
            should_stop=False
        )

    async def _handle_success(self) -> GuardResult:
        """Handle a successful operation.

        Returns:
            GuardResult indicating circuit state
        """
        self.success_count += 1

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                # Enough successes, close circuit
                self._transition_state(CircuitState.CLOSED)
                self.failure_count = 0
                return self._create_result(
                    status=GuardStatus.OK,
                    message="Circuit breaker closed after successful recovery",
                    details={"state": self.state.value, "success_count": self.success_count},
                    should_stop=False
                )

        return self._create_result(
            status=GuardStatus.OK,
            message=f"Circuit breaker state: {self.state.value}",
            details={
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
            },
            should_stop=False
        )

    def _transition_state(self, new_state: CircuitState) -> None:
        """Transition to a new state and emit event.

        Args:
            new_state: The new circuit state
        """
        old_state = self.state
        self.state = new_state
        logger.info(f"Circuit breaker state transition: {old_state.value} -> {new_state.value}")

        # Emit state change events
        for callback in self._state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self._check_count = 0
        logger.debug(f"Circuit breaker reset (threshold: {self.failure_threshold})")

    def register_state_change_callback(
        self,
        callback: Callable[[CircuitState, CircuitState], None]
    ) -> None:
        """Register a callback to be called on state changes.

        Args:
            callback: Function taking (old_state, new_state)
        """
        self._state_change_callbacks.append(callback)

    def force_open(self, reason: str = "Manual override") -> None:
        """Force circuit breaker to open state.

        Args:
            reason: Reason for forcing open
        """
        logger.warning(f"Circuit breaker forced open: {reason}")
        self._transition_state(CircuitState.OPEN)
        self.last_failure_time = time.time()

    def force_close(self) -> None:
        """Force circuit breaker to closed state."""
        logger.info("Circuit breaker forced closed")
        self._transition_state(CircuitState.CLOSED)
        self.failure_count = 0
