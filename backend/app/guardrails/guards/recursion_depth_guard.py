"""Recursion depth guard - prevents stack overflow."""
import logging
import sys
import traceback
from typing import Any

from .base_guard import BaseGuard
from ..models import GuardResult, GuardStatus

logger = logging.getLogger(__name__)


class RecursionDepthGuard(BaseGuard):
    """Prevents stack overflow by tracking and limiting recursion depth.

    Configuration:
        recursion_limit: Maximum recursion depth (default: 1000)
        warning_threshold: Percentage at which to warn (default: 0.7)
        suggest_iteration: Suggest converting to iteration (default: True)
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize Recursion Depth guard.

        Args:
            config: Configuration with recursion_limit
        """
        super().__init__(config)
        self.recursion_limit: int = config.get("recursion_limit", 1000)
        self.warning_threshold: float = config.get("warning_threshold", 0.7)
        self.suggest_iteration: bool = config.get("suggest_iteration", True)
        self.current_depth: int = 0
        self.max_depth_reached: int = 0
        self._call_stack: list[str] = []

        # Set Python's recursion limit
        try:
            sys.setrecursionlimit(self.recursion_limit + 100)  # Add buffer
        except (ValueError, RecursionError) as e:
            logger.warning(f"Could not set recursion limit: {e}")

    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Check if recursion depth exceeded.

        Args:
            context: Execution context containing:
                - recursion_depth: Current recursion depth
                - call_name: Name of current recursive call (optional)
                - entering: True if entering recursion, False if exiting

        Returns:
            GuardResult with STOP if exceeded, WARNING if approaching, OK otherwise
        """
        self._increment_check_count()

        # Get depth from context or calculate from stack
        if "recursion_depth" in context:
            self.current_depth = context["recursion_depth"]
        elif context.get("entering", True):
            self.current_depth += 1
            call_name = context.get("call_name", f"call_{self.current_depth}")
            self._call_stack.append(call_name)
        else:
            self.current_depth = max(0, self.current_depth - 1)
            if self._call_stack:
                self._call_stack.pop()

        # Track maximum depth
        self.max_depth_reached = max(self.max_depth_reached, self.current_depth)

        details = {
            "current_depth": self.current_depth,
            "max_depth_reached": self.max_depth_reached,
            "recursion_limit": self.recursion_limit,
            "percentage": round(self.current_depth / self.recursion_limit * 100, 1) if self.recursion_limit > 0 else 0,
        }

        # Check if exceeded
        if self.current_depth > self.recursion_limit:
            # Log call stack trace
            stack_trace = self._get_call_stack_trace()
            details["stack_trace"] = stack_trace[-10:]  # Last 10 calls

            message = f"Recursion depth exceeded: {self.current_depth}/{self.recursion_limit}"
            if self.suggest_iteration:
                message += " - Consider converting to iteration"

            result = self._create_result(
                status=GuardStatus.STOP,
                message=message,
                details=details,
                should_stop=True
            )
            logger.warning(f"Recursion limit exceeded at depth {self.current_depth}")
            self._log_check(result)
            return result

        # Check warning threshold
        warning_limit = int(self.recursion_limit * self.warning_threshold)
        if self.current_depth >= warning_limit:
            remaining = self.recursion_limit - self.current_depth
            details["remaining_depth"] = remaining

            message = f"Approaching recursion limit: {self.current_depth}/{self.recursion_limit}"
            if self.suggest_iteration:
                message += " - Consider optimizing with iteration"

            result = self._create_result(
                status=GuardStatus.WARNING,
                message=message,
                details=details,
                should_stop=False
            )
            self._log_check(result)
            return result

        # Normal operation
        result = self._create_result(
            status=GuardStatus.OK,
            message=f"Recursion depth: {self.current_depth}/{self.recursion_limit}",
            details=details,
            should_stop=False
        )
        return result

    def reset(self) -> None:
        """Reset depth counter for new execution."""
        self.current_depth = 0
        self.max_depth_reached = 0
        self._call_stack = []
        self._check_count = 0
        logger.debug(f"Recursion depth guard reset (limit: {self.recursion_limit})")

    def enter_recursion(self, call_name: str | None = None) -> int:
        """Mark entering a recursive call.

        Args:
            call_name: Optional name for the call

        Returns:
            Current depth after entering
        """
        self.current_depth += 1
        self._call_stack.append(call_name or f"call_{self.current_depth}")
        return self.current_depth

    def exit_recursion(self) -> int:
        """Mark exiting a recursive call.

        Returns:
            Current depth after exiting
        """
        self.current_depth = max(0, self.current_depth - 1)
        if self._call_stack:
            self._call_stack.pop()
        return self.current_depth

    def _get_call_stack_trace(self) -> list[str]:
        """Get current call stack trace.

        Returns:
            List of call names in the stack
        """
        if self._call_stack:
            return self._call_stack.copy()

        # Fallback to Python's traceback
        try:
            stack = traceback.extract_stack()
            return [f"{frame.filename}:{frame.lineno} {frame.name}" for frame in stack[-20:]]
        except Exception:
            return []

    @property
    def remaining_depth(self) -> int:
        """Get remaining recursion depth before limit."""
        return max(0, self.recursion_limit - self.current_depth)

    @staticmethod
    def convert_to_iteration(func: callable) -> callable:
        """Decorator suggestion for converting tail recursion to iteration.

        This is a helper to guide developers on converting recursive functions.
        """
        logger.info(
            f"Consider converting {func.__name__} to iteration using a stack-based approach"
        )
        return func
