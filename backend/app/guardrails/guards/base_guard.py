"""Abstract base class for loop guardrails."""
import logging
from abc import ABC, abstractmethod
from typing import Any

from ..models import GuardResult, GuardStatus

logger = logging.getLogger(__name__)


class BaseGuard(ABC):
    """Abstract base class for loop guardrails.

    All guards must implement:
    - check(): Check if guard condition is violated
    - reset(): Reset guard state for new execution
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize guard with configuration.

        Args:
            config: Guard-specific configuration dictionary
        """
        self.config = config
        self.name = self.__class__.__name__.replace("Guard", "")
        self._enabled = config.get("enabled", True)
        self._check_count = 0
        logger.debug(f"Initialized {self.name} guard with config: {config}")

    @abstractmethod
    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Check if guard condition is violated.

        Args:
            context: Execution context containing:
                - iteration: Current iteration number
                - elapsed_time: Elapsed time in seconds
                - last_operation_failed: Whether last operation failed
                - progress: Progress percentage (0-100)
                - Additional guard-specific data

        Returns:
            GuardResult with status and details
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset guard state for new execution.

        Called at the start of each new loop execution.
        """

    @property
    def enabled(self) -> bool:
        """Whether this guard is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable this guard."""
        self._enabled = value
        logger.info(f"{self.name} guard {'enabled' if value else 'disabled'}")

    @property
    def check_count(self) -> int:
        """Number of times this guard has been checked."""
        return self._check_count

    def _increment_check_count(self) -> None:
        """Increment the check counter."""
        self._check_count += 1

    def _create_result(
        self,
        status: GuardStatus,
        message: str,
        details: dict[str, Any] | None = None,
        should_stop: bool | None = None
    ) -> GuardResult:
        """Create a guard result with standard fields.

        Args:
            status: Guard status
            message: Human-readable message
            details: Additional details
            should_stop: Whether to stop execution (defaults based on status)

        Returns:
            GuardResult instance
        """
        if should_stop is None:
            should_stop = status == GuardStatus.STOP

        return GuardResult(
            guard_name=self.name,
            status=status,
            message=message,
            details=details or {},
            should_stop=should_stop
        )

    def _log_check(self, result: GuardResult) -> None:
        """Log guard check result.

        Args:
            result: Guard check result
        """
        if result.status == GuardStatus.STOP:
            logger.warning(f"{self.name} guard STOP: {result.message}")
        elif result.status == GuardStatus.WARNING:
            logger.warning(f"{self.name} guard WARNING: {result.message}")
        else:
            logger.debug(f"{self.name} guard OK: {result.message}")
