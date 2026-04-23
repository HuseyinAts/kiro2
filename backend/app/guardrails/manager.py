"""Guardrail Manager - orchestrates all loop protection guards."""
import asyncio
import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .exceptions import GuardrailError
from .guards import (
    BaseGuard,
    CircuitBreakerGuard,
    DeadlockDetectionGuard,
    EmergencyStopGuard,
    MaxTurnsGuard,
    ProgressMonitorGuard,
    RecursionDepthGuard,
    ResourceLimitGuard,
    TimeoutGuard,
)
from .models import GuardConfig, GuardResult, GuardStatus, TerminationReport

logger = logging.getLogger(__name__)


class GuardrailManager:
    """Orchestrates all loop guardrails for comprehensive protection.

    This manager coordinates multiple guard types to prevent:
    - Infinite loops (maxTurns)
    - Long-running operations (timeout)
    - Cascade failures (circuit breaker)
    - Stack overflow (recursion depth)
    - Stalled progress (progress monitor)
    - Resource exhaustion (resource limits)
    - Deadlocks (deadlock detection)
    - Critical failures (emergency stop)

    Usage:
        manager = GuardrailManager(config)
        manager.start_execution()

        while not done:
            result = await manager.check_all_guards(context)
            if result["should_stop"]:
                break
            # ... do work ...

        report = manager.generate_report()
    """

    def __init__(self, config: GuardConfig | dict[str, Any] | None = None):
        """Initialize Guardrail Manager.

        Args:
            config: Guard configuration (GuardConfig or dict)
        """
        if config is None:
            self.config = GuardConfig()
        elif isinstance(config, dict):
            self.config = GuardConfig(**config)
        else:
            self.config = config

        self.guards: list[BaseGuard] = []
        self.start_time: float | None = None
        self.iteration_count: int = 0
        self._warnings: list[str] = []
        self._partial_result: Any = None

        self._register_guards()
        logger.info(f"GuardrailManager initialized with {len(self.guards)} guards")

    def _register_guards(self) -> None:
        """Register all enabled guards."""
        enabled = self.config.enabled_guards

        guard_mapping = {
            "MaxTurns": (MaxTurnsGuard, {
                "max_turns": self.config.max_turns,
                "warning_threshold": self.config.warning_threshold,
            }),
            "Timeout": (TimeoutGuard, {
                "timeout_seconds": self.config.timeout_seconds,
                "warning_threshold": self.config.warning_threshold,
            }),
            "CircuitBreaker": (CircuitBreakerGuard, {
                "failure_threshold": self.config.failure_threshold,
                "timeout": self.config.circuit_timeout,
                "half_open_max_calls": self.config.half_open_max_calls,
            }),
            "RecursionDepth": (RecursionDepthGuard, {
                "recursion_limit": self.config.recursion_limit,
            }),
            "ProgressMonitor": (ProgressMonitorGuard, {
                "stall_threshold": self.config.stall_threshold_iterations,
                "progress_callback_interval": self.config.progress_update_interval,
            }),
            "ResourceLimit": (ResourceLimitGuard, {
                "memory_limit_mb": self.config.memory_limit_mb,
                "cpu_limit_percent": self.config.cpu_limit_percent,
                "disk_min_free_mb": self.config.disk_min_free_mb,
            }),
            "DeadlockDetection": (DeadlockDetectionGuard, {
                "deadlock_timeout": self.config.deadlock_timeout,
            }),
            "EmergencyStop": (EmergencyStopGuard, {
                "graceful_timeout": self.config.graceful_shutdown_timeout,
            }),
        }

        for guard_name, (guard_class, guard_config) in guard_mapping.items():
            if guard_name in enabled:
                try:
                    guard = guard_class(guard_config)
                    self.guards.append(guard)
                    logger.debug(f"Registered guard: {guard_name}")
                except Exception as e:
                    logger.error(f"Failed to register guard {guard_name}: {e}")

    async def check_all_guards(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Check all guards in parallel.

        Args:
            context: Execution context with guard-specific data

        Returns:
            Aggregated guard results with should_stop flag
        """
        context = context or {}
        self.iteration_count += 1

        # Add elapsed time to context
        if self.start_time:
            context["elapsed_time"] = time.time() - self.start_time
        context["iteration"] = self.iteration_count

        # Check all guards in parallel
        tasks = []
        for guard in self.guards:
            if guard.enabled:
                tasks.append(self._check_guard_safe(guard, context))

        results: list[GuardResult] = await asyncio.gather(*tasks)

        # Aggregate results
        should_stop = any(r.should_stop for r in results)
        warnings = [r for r in results if r.status == GuardStatus.WARNING]
        stops = [r for r in results if r.status == GuardStatus.STOP]

        # Record warnings
        for warning in warnings:
            self._warnings.append(warning.message)

        aggregated = {
            "should_stop": should_stop,
            "iteration": self.iteration_count,
            "guard_results": [r.model_dump() for r in results],
            "warnings": [r.model_dump() for r in warnings],
            "stops": [r.model_dump() for r in stops],
            "summary": self._generate_summary(results),
        }

        if should_stop and stops:
            logger.warning(f"Loop stopping: {stops[0].message}")

        return aggregated

    async def _check_guard_safe(
        self,
        guard: BaseGuard,
        context: dict[str, Any]
    ) -> GuardResult:
        """Safely check a guard, catching any exceptions.

        Args:
            guard: Guard to check
            context: Execution context

        Returns:
            GuardResult, or error result if exception occurs
        """
        try:
            return await guard.check(context)
        except Exception as e:
            logger.exception(f"Guard {guard.name} check failed: {e}")
            return GuardResult(
                guard_name=guard.name,
                status=GuardStatus.WARNING,
                message=f"Guard check error: {e!s}",
                details={"error": str(e)},
                should_stop=False
            )

    def start_execution(self, agent_type: str | None = None) -> None:
        """Start execution timer and reset all guards.

        Args:
            agent_type: Optional agent type for config overrides
        """
        self.start_time = time.time()
        self.iteration_count = 0
        self._warnings = []
        self._partial_result = None

        # Apply agent-specific config if provided
        if agent_type:
            self.config = self.config.get_config_for_agent(agent_type)
            self._register_guards()  # Re-register with new config

        # Reset all guards
        for guard in self.guards:
            guard.reset()

        logger.info(f"Execution started with {len(self.guards)} guards")

    def stop_execution(self, partial_result: Any = None) -> TerminationReport:
        """Stop execution and generate termination report.

        Args:
            partial_result: Partial result to include in report

        Returns:
            TerminationReport with execution summary
        """
        self._partial_result = partial_result
        return self.generate_report()

    def _generate_summary(self, results: list[GuardResult]) -> str:
        """Generate human-readable summary.

        Args:
            results: List of guard results

        Returns:
            Summary string
        """
        stops = [r for r in results if r.status == GuardStatus.STOP]
        if stops:
            return f"Loop stopped: {stops[0].message}"

        warnings = [r for r in results if r.status == GuardStatus.WARNING]
        if warnings:
            return f"Warnings: {', '.join(w.message for w in warnings[:3])}"

        return "All guardrails OK"

    def generate_report(
        self,
        completed_normally: bool = False
    ) -> TerminationReport:
        """Generate a termination report.

        Args:
            completed_normally: Whether loop completed normally

        Returns:
            TerminationReport with full execution details
        """
        elapsed = time.time() - self.start_time if self.start_time else 0

        # Get final guard results
        final_results = []
        terminated_by = "completion" if completed_normally else "unknown"

        for guard in self.guards:
            if hasattr(guard, "_create_result"):
                # Get last known state
                result = guard._create_result(
                    status=GuardStatus.OK,
                    message="Final state",
                    details={"check_count": guard.check_count}
                )
                final_results.append(result)

                # Determine termination cause
                if hasattr(guard, "_stop_triggered") and guard._stop_triggered:
                    terminated_by = guard.name
                elif hasattr(guard, "current_turn") and guard.current_turn > guard.max_turns:
                    terminated_by = "MaxTurns"
                elif hasattr(guard, "elapsed_time") and guard.elapsed_time >= guard.timeout_seconds:
                    terminated_by = "Timeout"

        # Get resource usage if available
        resource_usage = {}
        for guard in self.guards:
            if isinstance(guard, ResourceLimitGuard):
                resource_usage = guard.get_resource_report()
                break

        return TerminationReport(
            reason=f"Loop terminated by {terminated_by}",
            terminated_by=terminated_by,
            total_iterations=self.iteration_count,
            elapsed_time_seconds=elapsed,
            guard_results=final_results,
            partial_result=self._partial_result,
            completed_normally=completed_normally,
            resource_usage=resource_usage,
            warnings_issued=self._warnings,
        )

    def get_guard(self, guard_name: str) -> BaseGuard | None:
        """Get a specific guard by name.

        Args:
            guard_name: Name of the guard

        Returns:
            Guard instance or None
        """
        for guard in self.guards:
            if guard.name == guard_name:
                return guard
        return None

    def enable_guard(self, guard_name: str) -> bool:
        """Enable a specific guard.

        Args:
            guard_name: Name of the guard to enable

        Returns:
            True if guard was found and enabled
        """
        guard = self.get_guard(guard_name)
        if guard:
            guard.enabled = True
            return True
        return False

    def disable_guard(self, guard_name: str) -> bool:
        """Disable a specific guard.

        Args:
            guard_name: Name of the guard to disable

        Returns:
            True if guard was found and disabled
        """
        guard = self.get_guard(guard_name)
        if guard:
            guard.enabled = False
            return True
        return False

    def trigger_emergency_stop(self, reason: str) -> None:
        """Trigger emergency stop.

        Args:
            reason: Reason for emergency stop
        """
        guard = self.get_guard("EmergencyStop")
        if guard and isinstance(guard, EmergencyStopGuard):
            guard.trigger(reason)
        else:
            logger.error("Emergency stop guard not found")

    @classmethod
    def from_yaml(cls, path: str | Path) -> "GuardrailManager":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML config file

        Returns:
            GuardrailManager instance
        """
        import yaml
        with open(path) as f:
            config_dict = yaml.safe_load(f)
        return cls(config_dict)

    @classmethod
    def from_json(cls, path: str | Path) -> "GuardrailManager":
        """Load configuration from JSON file.

        Args:
            path: Path to JSON config file

        Returns:
            GuardrailManager instance
        """
        with open(path) as f:
            config_dict = json.load(f)
        return cls(config_dict)

    def to_dict(self) -> dict[str, Any]:
        """Export current configuration to dictionary.

        Returns:
            Configuration dictionary
        """
        return self.config.model_dump()


# Decorator for protecting async functions with guardrails
def with_guardrails(
    config: GuardConfig | dict[str, Any] | None = None,
    on_stop: Callable | None = None
):
    """Decorator to protect async functions with guardrails.

    Args:
        config: Guard configuration
        on_stop: Callback when guards stop execution

    Usage:
        @with_guardrails({"max_turns": 50, "timeout_seconds": 60})
        async def my_loop_function():
            while True:
                yield some_result  # Must be a generator

    Returns:
        Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = GuardrailManager(config)
            manager.start_execution()

            results = []
            try:
                async for item in func(*args, **kwargs):
                    results.append(item)

                    check_result = await manager.check_all_guards()
                    if check_result["should_stop"]:
                        if on_stop:
                            on_stop(check_result, results)
                        break

                return results
            except Exception as e:
                logger.exception(f"Guardrailed function error: {e}")
                raise GuardrailError(str(e)) from e
            finally:
                report = manager.generate_report()
                logger.info(f"Guardrail report: {report.to_log_dict()}")

        return wrapper
    return decorator
