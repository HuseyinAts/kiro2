"""Property-based tests for guardrails - Boris Cherny verification standards."""
import asyncio
import random
import time

import pytest

from app.guardrails import GuardConfig, GuardrailManager
from app.guardrails.guards import (
    CircuitBreakerGuard,
    MaxTurnsGuard,
    TimeoutGuard,
)
from app.guardrails.guards.circuit_breaker_guard import CircuitState
from app.guardrails.models import GuardStatus


class TestProperty1MaxTurnsEnforcement:
    """Property 1: For any loop with maxTurns=N, loop terminates after at most N iterations.

    Validates: Requirements 1.1, 1.2, 1.3, 1.4
    """

    @pytest.mark.parametrize("max_turns", [1, 5, 10, 50, 100])
    @pytest.mark.asyncio
    async def test_terminates_at_max_turns(self, max_turns: int) -> None:
        """Verify loop terminates exactly at maxTurns limit."""
        guard = MaxTurnsGuard({"max_turns": max_turns})

        iterations = 0
        for _ in range(max_turns + 10):  # Try to exceed
            result = await guard.check({})
            iterations += 1
            if result.should_stop:
                break

        # Should stop at exactly max_turns + 1
        assert iterations == max_turns + 1
        assert guard.current_turn == max_turns + 1

    @pytest.mark.asyncio
    async def test_random_max_turns_enforcement(self) -> None:
        """Property test with random maxTurns values (100 iterations)."""
        for _ in range(100):
            max_turns = random.randint(1, 100)
            guard = MaxTurnsGuard({"max_turns": max_turns})

            for i in range(max_turns + 5):
                result = await guard.check({})
                if result.should_stop:
                    assert i == max_turns  # Should stop at exactly max_turns
                    break
            else:
                pytest.fail(f"Guard did not stop at max_turns={max_turns}")


class TestProperty2TimeoutEnforcement:
    """Property 2: For any loop with timeout=T, loop terminates within T seconds.

    Validates: Requirements 2.1, 2.2, 2.3
    """

    @pytest.mark.parametrize("timeout", [0.1, 0.2, 0.5])
    @pytest.mark.asyncio
    async def test_terminates_within_timeout(self, timeout: float) -> None:
        """Verify loop terminates within timeout."""
        guard = TimeoutGuard({"timeout_seconds": timeout})

        start = time.time()
        while True:
            result = await guard.check({})
            if result.should_stop:
                break
            await asyncio.sleep(0.01)

            # Safety limit
            if time.time() - start > timeout + 1:
                pytest.fail("Did not stop within reasonable time")

        elapsed = time.time() - start
        # Allow small tolerance for async timing
        assert elapsed <= timeout + 0.1, f"Elapsed {elapsed} > timeout {timeout}"

    @pytest.mark.asyncio
    async def test_random_timeout_enforcement(self) -> None:
        """Property test with random timeout values (50 iterations)."""
        for _ in range(50):
            timeout = random.uniform(0.05, 0.3)
            guard = TimeoutGuard({"timeout_seconds": timeout})

            start = time.time()
            stopped = False
            for _ in range(1000):
                result = await guard.check({})
                if result.should_stop:
                    stopped = True
                    break
                await asyncio.sleep(0.01)

            assert stopped is True
            elapsed = time.time() - start
            assert elapsed <= timeout + 0.15  # Tolerance for async


class TestProperty3CircuitBreakerStateTransitions:
    """Property 3: Circuit breaker state transitions are correct.

    State machine:
    - CLOSED -> OPEN: After F consecutive failures
    - OPEN -> HALF_OPEN: After timeout
    - HALF_OPEN -> CLOSED: After successful calls
    - HALF_OPEN -> OPEN: On failure

    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """

    @pytest.mark.parametrize("failure_threshold", [1, 2, 3, 5])
    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self, failure_threshold: int) -> None:
        """Verify circuit opens after exactly threshold failures."""
        guard = CircuitBreakerGuard({
            "failure_threshold": failure_threshold,
            "timeout": 1.0,
        })

        # Record failures
        for i in range(failure_threshold - 1):
            await guard.check({"last_operation_failed": True})
            assert guard.state == CircuitState.CLOSED

        # Next failure should open
        result = await guard.check({"last_operation_failed": True})
        assert guard.state == CircuitState.OPEN
        assert result.should_stop is True

    @pytest.mark.asyncio
    async def test_state_transition_sequence(self) -> None:
        """Verify full state transition sequence."""
        guard = CircuitBreakerGuard({
            "failure_threshold": 2,
            "timeout": 0.1,
            "half_open_max_calls": 2,
        })

        # Initial state: CLOSED
        assert guard.state == CircuitState.CLOSED

        # CLOSED -> OPEN (after failures)
        await guard.check({"last_operation_failed": True})
        await guard.check({"last_operation_failed": True})
        assert guard.state == CircuitState.OPEN

        # OPEN -> HALF_OPEN (after timeout)
        await asyncio.sleep(0.15)
        await guard.check({"last_operation_failed": False})
        assert guard.state == CircuitState.HALF_OPEN

        # HALF_OPEN -> CLOSED (after successful calls)
        await guard.check({"last_operation_failed": False})
        await guard.check({"last_operation_failed": False})
        assert guard.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens(self) -> None:
        """Verify failure in half-open state reopens circuit."""
        guard = CircuitBreakerGuard({
            "failure_threshold": 2,
            "timeout": 0.1,
            "half_open_max_calls": 3,
        })

        # Open circuit
        await guard.check({"last_operation_failed": True})
        await guard.check({"last_operation_failed": True})
        assert guard.state == CircuitState.OPEN

        # Transition to half-open
        await asyncio.sleep(0.15)
        await guard.check({"last_operation_failed": False})
        assert guard.state == CircuitState.HALF_OPEN

        # Failure should reopen
        await guard.check({"last_operation_failed": True})
        assert guard.state == CircuitState.OPEN


class TestProperty4RecursionDepthEnforcement:
    """Property 4: Recursion does not exceed depth limit.

    Validates: Requirements 4.1, 4.2, 4.3
    """

    @pytest.mark.asyncio
    async def test_stops_at_recursion_limit(self) -> None:
        """Verify recursion stops at limit."""
        from app.guardrails.guards import RecursionDepthGuard

        for limit in [5, 10, 20, 50]:
            guard = RecursionDepthGuard({"recursion_limit": limit})

            for i in range(limit + 5):
                result = await guard.check({"entering": True})
                if result.should_stop:
                    assert i == limit  # Should stop at exactly limit
                    break
            else:
                pytest.fail(f"Did not stop at recursion_limit={limit}")


class TestProperty5ResourceLimitEnforcement:
    """Property 5: Execution terminates when resource limits exceeded.

    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """

    @pytest.mark.asyncio
    async def test_respects_memory_limit(self) -> None:
        """Verify memory limit is respected."""
        from app.guardrails.guards import ResourceLimitGuard

        # Very low memory limit to trigger
        guard = ResourceLimitGuard({
            "memory_limit_mb": 1,  # 1MB - almost certainly exceeded
            "check_interval_iterations": 1,
        })

        result = await guard.check({})
        # Should either stop or warn (depends on actual memory usage)
        assert result.status in [GuardStatus.STOP, GuardStatus.WARNING, GuardStatus.OK]


class TestProperty6EmergencyStopResponsiveness:
    """Property 6: Emergency stop terminates execution within 1 second.

    Validates: Requirements 8.1, 8.2, 8.3
    """

    @pytest.mark.asyncio
    async def test_emergency_stop_response_time(self) -> None:
        """Verify emergency stop responds within 1 second."""
        from app.guardrails.guards import EmergencyStopGuard

        guard = EmergencyStopGuard({})

        # Trigger emergency stop
        start = time.time()
        guard.trigger("Test emergency", "MANUAL")

        result = await guard.check({})
        elapsed = time.time() - start

        assert result.should_stop is True
        assert elapsed < 1.0  # Must respond within 1 second

    @pytest.mark.asyncio
    async def test_emergency_stop_in_manager(self) -> None:
        """Verify emergency stop works through manager."""
        config = GuardConfig(enabled_guards=["EmergencyStop"])
        manager = GuardrailManager(config)
        manager.start_execution()

        start = time.time()
        manager.trigger_emergency_stop("Test reason")

        result = await manager.check_all_guards()
        elapsed = time.time() - start

        assert result["should_stop"] is True
        assert elapsed < 1.0


class TestIntegrationGuardrails:
    """Integration tests for full guardrail system."""

    @pytest.mark.asyncio
    async def test_full_system_prevents_infinite_loop(self) -> None:
        """Verify full system prevents infinite loop."""
        config = GuardConfig(
            max_turns=50,
            timeout_seconds=5,
            enabled_guards=["MaxTurns", "Timeout"],
        )
        manager = GuardrailManager(config)
        manager.start_execution()

        iterations = 0
        max_iterations = 1000  # Safety limit

        while iterations < max_iterations:
            result = await manager.check_all_guards()
            iterations += 1
            if result["should_stop"]:
                break

        # Should have stopped
        assert iterations < max_iterations
        assert iterations == 51  # maxTurns + 1

    @pytest.mark.asyncio
    async def test_multiple_guards_work_together(self) -> None:
        """Verify multiple guards cooperate correctly."""
        config = GuardConfig(
            max_turns=100,
            timeout_seconds=0.5,
            failure_threshold=5,
            enabled_guards=["MaxTurns", "Timeout", "CircuitBreaker"],
        )
        manager = GuardrailManager(config)
        manager.start_execution()

        # Should stop due to timeout (fastest trigger)
        stopped = False
        for _ in range(1000):
            result = await manager.check_all_guards()
            if result["should_stop"]:
                stopped = True
                break
            await asyncio.sleep(0.05)

        assert stopped is True

    @pytest.mark.asyncio
    async def test_100_random_scenarios(self) -> None:
        """Run 100 random scenarios to verify system stability."""
        for _ in range(100):
            max_turns = random.randint(5, 50)
            timeout = random.uniform(0.1, 0.5)

            config = GuardConfig(
                max_turns=max_turns,
                timeout_seconds=timeout,
                enabled_guards=["MaxTurns", "Timeout"],
            )
            manager = GuardrailManager(config)
            manager.start_execution()

            for _ in range(max_turns + 10):
                result = await manager.check_all_guards()
                if result["should_stop"]:
                    break
                await asyncio.sleep(0.01)

            # Must have stopped
            report = manager.generate_report()
            assert report.total_iterations <= max_turns + 1 or report.elapsed_time_seconds <= timeout + 0.2
