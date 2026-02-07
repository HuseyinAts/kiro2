"""MaxTurns guard - enforces maximum iteration limit."""
import logging
from typing import Any

from .base_guard import BaseGuard
from ..models import GuardResult, GuardStatus

logger = logging.getLogger(__name__)


class MaxTurnsGuard(BaseGuard):
    """Enforces maximum iteration limit to prevent infinite loops.

    Configuration:
        max_turns: Maximum number of iterations (default: 100)
        warning_threshold: Percentage at which to issue warning (default: 0.8)
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize MaxTurns guard.

        Args:
            config: Configuration with max_turns and warning_threshold
        """
        super().__init__(config)
        self.max_turns: int = config.get("max_turns", 100)
        self.warning_threshold: float = config.get("warning_threshold", 0.8)
        self.current_turn: int = 0

    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Check if maximum iterations exceeded.

        Args:
            context: Execution context (not used for this guard)

        Returns:
            GuardResult with STOP if exceeded, WARNING if approaching, OK otherwise
        """
        self._increment_check_count()
        self.current_turn += 1

        details = {
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "percentage": round(self.current_turn / self.max_turns * 100, 1),
        }

        # Check if exceeded
        if self.current_turn > self.max_turns:
            result = self._create_result(
                status=GuardStatus.STOP,
                message=f"Maximum iterations exceeded: {self.current_turn}/{self.max_turns}",
                details=details,
                should_stop=True
            )
            logger.warning(
                f"MaxTurns exceeded: iteration {self.current_turn} > limit {self.max_turns}"
            )
            self._log_check(result)
            return result

        # Check warning threshold
        warning_limit = int(self.max_turns * self.warning_threshold)
        if self.current_turn >= warning_limit:
            remaining = self.max_turns - self.current_turn
            details["remaining_iterations"] = remaining
            result = self._create_result(
                status=GuardStatus.WARNING,
                message=f"Approaching iteration limit: {self.current_turn}/{self.max_turns} ({remaining} remaining)",
                details=details,
                should_stop=False
            )
            self._log_check(result)
            return result

        # Normal operation
        result = self._create_result(
            status=GuardStatus.OK,
            message=f"Iteration {self.current_turn}/{self.max_turns}",
            details=details,
            should_stop=False
        )
        return result

    def reset(self) -> None:
        """Reset turn counter for new execution."""
        self.current_turn = 0
        self._check_count = 0
        logger.debug(f"MaxTurns guard reset (limit: {self.max_turns})")

    @property
    def remaining_turns(self) -> int:
        """Get remaining turns before limit."""
        return max(0, self.max_turns - self.current_turn)

    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage of max turns."""
        return (self.current_turn / self.max_turns) * 100 if self.max_turns > 0 else 0
