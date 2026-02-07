"""Custom exceptions for guardrail system."""
from typing import Any


class GuardrailError(Exception):
    """Base exception for guardrail violations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.details = details or {}


class MaxTurnsExceeded(GuardrailError):
    """Raised when maximum iterations are exceeded."""

    def __init__(self, current_turn: int, max_turns: int):
        super().__init__(
            f"Maximum iterations exceeded: {current_turn}/{max_turns}",
            {"current_turn": current_turn, "max_turns": max_turns}
        )
        self.current_turn = current_turn
        self.max_turns = max_turns


class TimeoutExceeded(GuardrailError):
    """Raised when execution timeout is exceeded."""

    def __init__(self, elapsed_time: float, timeout: float):
        super().__init__(
            f"Timeout exceeded: {elapsed_time:.2f}s/{timeout}s",
            {"elapsed_time": elapsed_time, "timeout": timeout}
        )
        self.elapsed_time = elapsed_time
        self.timeout = timeout


class CircuitBreakerOpen(GuardrailError):
    """Raised when circuit breaker is open."""

    def __init__(self, failure_count: int, time_until_retry: float):
        super().__init__(
            f"Circuit breaker is OPEN after {failure_count} failures. Retry in {time_until_retry:.1f}s",
            {"failure_count": failure_count, "time_until_retry": time_until_retry}
        )
        self.failure_count = failure_count
        self.time_until_retry = time_until_retry


class RecursionLimitExceeded(GuardrailError):
    """Raised when recursion depth limit is exceeded."""

    def __init__(self, current_depth: int, max_depth: int):
        super().__init__(
            f"Recursion depth exceeded: {current_depth}/{max_depth}",
            {"current_depth": current_depth, "max_depth": max_depth}
        )
        self.current_depth = current_depth
        self.max_depth = max_depth


class ResourceLimitExceeded(GuardrailError):
    """Raised when resource limits are exceeded."""

    def __init__(self, resource_type: str, current_value: float, limit_value: float):
        super().__init__(
            f"{resource_type} limit exceeded: {current_value:.2f}/{limit_value:.2f}",
            {"resource_type": resource_type, "current_value": current_value, "limit_value": limit_value}
        )
        self.resource_type = resource_type
        self.current_value = current_value
        self.limit_value = limit_value


class DeadlockDetected(GuardrailError):
    """Raised when a deadlock is detected."""

    def __init__(self, involved_locks: list[str]):
        super().__init__(
            f"Deadlock detected involving locks: {', '.join(involved_locks)}",
            {"involved_locks": involved_locks}
        )
        self.involved_locks = involved_locks


class EmergencyStopTriggered(GuardrailError):
    """Raised when emergency stop is triggered."""

    def __init__(self, reason: str, signal_type: str = "SIGTERM"):
        super().__init__(
            f"Emergency stop triggered: {reason}",
            {"reason": reason, "signal_type": signal_type}
        )
        self.reason = reason
        self.signal_type = signal_type


class StallDetected(GuardrailError):
    """Raised when progress stall is detected."""

    def __init__(self, iterations_without_progress: int, threshold: int):
        super().__init__(
            f"Progress stall detected: {iterations_without_progress} iterations without progress (threshold: {threshold})",
            {"iterations_without_progress": iterations_without_progress, "threshold": threshold}
        )
        self.iterations_without_progress = iterations_without_progress
        self.threshold = threshold
