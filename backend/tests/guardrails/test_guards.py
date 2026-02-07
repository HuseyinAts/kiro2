"""Unit tests for individual guards."""
import asyncio

import pytest

from app.guardrails.guards import (
    MaxTurnsGuard,
    TimeoutGuard,
    CircuitBreakerGuard,
    RecursionDepthGuard,
    ProgressMonitorGuard,
)
from app.guardrails.guards.circuit_breaker_guard import CircuitState
from app.guardrails.models import GuardStatus


class TestMaxTurnsGuard:
    """Tests for MaxTurnsGuard."""

    @pytest.fixture
    def guard(self) -> MaxTurnsGuard:
        """Create MaxTurnsGuard with test config."""
        return MaxTurnsGuard({"max_turns": 10, "warning_threshold": 0.8})

    @pytest.mark.asyncio
    async def test_ok_within_limit(self, guard: MaxTurnsGuard) -> None:
        """Test guard returns OK within limit."""
        for i in range(5):
            result = await guard.check({})
            assert result.status == GuardStatus.OK
            assert result.should_stop is False
            assert result.details["current_turn"] == i + 1

    @pytest.mark.asyncio
    async def test_warning_at_threshold(self, guard: MaxTurnsGuard) -> None:
        """Test guard returns WARNING at 80% threshold."""
        # Run to 80% (8 of 10)
        for _ in range(7):
            await guard.check({})

        # 8th iteration should warn
        result = await guard.check({})
        assert result.status == GuardStatus.WARNING
        assert result.should_stop is False
        assert "Approaching" in result.message

    @pytest.mark.asyncio
    async def test_stop_when_exceeded(self, guard: MaxTurnsGuard) -> None:
        """Test guard returns STOP when limit exceeded."""
        # Run past limit
        for _ in range(10):
            await guard.check({})

        # 11th iteration should stop
        result = await guard.check({})
        assert result.status == GuardStatus.STOP
        assert result.should_stop is True
        assert "exceeded" in result.message.lower()

    @pytest.mark.asyncio
    async def test_reset(self, guard: MaxTurnsGuard) -> None:
        """Test guard reset clears counter."""
        for _ in range(5):
            await guard.check({})

        assert guard.current_turn == 5

        guard.reset()
        assert guard.current_turn == 0

        result = await guard.check({})
        assert result.details["current_turn"] == 1


class TestTimeoutGuard:
    """Tests for TimeoutGuard."""

    @pytest.fixture
    def guard(self) -> TimeoutGuard:
        """Create TimeoutGuard with test config."""
        return TimeoutGuard({"timeout_seconds": 1.0, "warning_threshold": 0.8})

    @pytest.mark.asyncio
    async def test_ok_within_timeout(self, guard: TimeoutGuard) -> None:
        """Test guard returns OK within timeout."""
        result = await guard.check({})
        assert result.status == GuardStatus.OK
        assert result.should_stop is False

    @pytest.mark.asyncio
    async def test_warning_at_threshold(self, guard: TimeoutGuard) -> None:
        """Test guard returns WARNING at 80% of timeout."""
        await guard.check({})  # Initialize timer

        # Wait until past warning threshold
        await asyncio.sleep(0.85)

        result = await guard.check({})
        assert result.status == GuardStatus.WARNING
        assert result.should_stop is False

    @pytest.mark.asyncio
    async def test_stop_when_exceeded(self, guard: TimeoutGuard) -> None:
        """Test guard returns STOP when timeout exceeded."""
        await guard.check({})  # Initialize timer

        # Wait past timeout
        await asyncio.sleep(1.1)

        result = await guard.check({})
        assert result.status == GuardStatus.STOP
        assert result.should_stop is True

    @pytest.mark.asyncio
    async def test_reset(self, guard: TimeoutGuard) -> None:
        """Test guard reset clears timer."""
        await guard.check({})
        await asyncio.sleep(0.5)

        guard.reset()
        assert guard.start_time is None

        result = await guard.check({})
        assert result.status == GuardStatus.OK


class TestCircuitBreakerGuard:
    """Tests for CircuitBreakerGuard."""

    @pytest.fixture
    def guard(self) -> CircuitBreakerGuard:
        """Create CircuitBreakerGuard with test config."""
        return CircuitBreakerGuard({
            "failure_threshold": 3,
            "timeout": 0.5,
            "half_open_max_calls": 2
        })

    @pytest.mark.asyncio
    async def test_closed_state_on_success(self, guard: CircuitBreakerGuard) -> None:
        """Test circuit stays closed on success."""
        result = await guard.check({"last_operation_failed": False})
        assert guard.state == CircuitState.CLOSED
        assert result.status == GuardStatus.OK

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self, guard: CircuitBreakerGuard) -> None:
        """Test circuit opens after threshold failures."""
        # Record failures
        for _ in range(2):
            await guard.check({"last_operation_failed": True})
            assert guard.state == CircuitState.CLOSED

        # Third failure should open circuit
        result = await guard.check({"last_operation_failed": True})
        assert guard.state == CircuitState.OPEN
        assert result.status == GuardStatus.STOP

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, guard: CircuitBreakerGuard) -> None:
        """Test circuit transitions to half-open after timeout."""
        # Open circuit
        for _ in range(3):
            await guard.check({"last_operation_failed": True})
        assert guard.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.6)

        # Should transition to half-open
        await guard.check({"last_operation_failed": False})
        assert guard.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_successful_half_open(self, guard: CircuitBreakerGuard) -> None:
        """Test circuit closes after successful half-open calls."""
        # Open circuit
        for _ in range(3):
            await guard.check({"last_operation_failed": True})

        # Wait for timeout
        await asyncio.sleep(0.6)

        # Successful calls in half-open
        await guard.check({"last_operation_failed": False})  # Transition to half-open
        await guard.check({"last_operation_failed": False})  # First success
        await guard.check({"last_operation_failed": False})  # Second success - should close

        assert guard.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_half_open_failure(self, guard: CircuitBreakerGuard) -> None:
        """Test circuit reopens on failure in half-open state."""
        # Open circuit
        for _ in range(3):
            await guard.check({"last_operation_failed": True})

        # Wait for timeout
        await asyncio.sleep(0.6)

        # Transition to half-open
        await guard.check({"last_operation_failed": False})
        assert guard.state == CircuitState.HALF_OPEN

        # Failure in half-open
        result = await guard.check({"last_operation_failed": True})
        assert guard.state == CircuitState.OPEN
        assert result.status == GuardStatus.STOP


class TestRecursionDepthGuard:
    """Tests for RecursionDepthGuard."""

    @pytest.fixture
    def guard(self) -> RecursionDepthGuard:
        """Create RecursionDepthGuard with test config."""
        return RecursionDepthGuard({"recursion_limit": 10, "warning_threshold": 0.7})

    @pytest.mark.asyncio
    async def test_ok_within_limit(self, guard: RecursionDepthGuard) -> None:
        """Test guard returns OK within limit."""
        for _ in range(5):
            result = await guard.check({"entering": True})
            assert result.status == GuardStatus.OK

    @pytest.mark.asyncio
    async def test_warning_at_threshold(self, guard: RecursionDepthGuard) -> None:
        """Test guard returns WARNING at threshold."""
        for _ in range(6):
            await guard.check({"entering": True})

        # 7th call should warn (70% of 10)
        result = await guard.check({"entering": True})
        assert result.status == GuardStatus.WARNING

    @pytest.mark.asyncio
    async def test_stop_when_exceeded(self, guard: RecursionDepthGuard) -> None:
        """Test guard returns STOP when limit exceeded."""
        for _ in range(10):
            await guard.check({"entering": True})

        # 11th call should stop
        result = await guard.check({"entering": True})
        assert result.status == GuardStatus.STOP
        assert result.should_stop is True

    @pytest.mark.asyncio
    async def test_depth_tracking(self, guard: RecursionDepthGuard) -> None:
        """Test depth increments and decrements correctly."""
        await guard.check({"entering": True})
        assert guard.current_depth == 1

        await guard.check({"entering": True})
        assert guard.current_depth == 2

        await guard.check({"entering": False})
        assert guard.current_depth == 1


class TestProgressMonitorGuard:
    """Tests for ProgressMonitorGuard."""

    @pytest.fixture
    def guard(self) -> ProgressMonitorGuard:
        """Create ProgressMonitorGuard with test config."""
        return ProgressMonitorGuard({"stall_threshold": 3})

    @pytest.mark.asyncio
    async def test_ok_with_progress(self, guard: ProgressMonitorGuard) -> None:
        """Test guard returns OK when progress is made."""
        for i in range(5):
            result = await guard.check({"progress": i * 20})
            assert result.status == GuardStatus.OK

    @pytest.mark.asyncio
    async def test_warning_on_stall(self, guard: ProgressMonitorGuard) -> None:
        """Test guard returns WARNING when stalled."""
        # Set initial progress
        await guard.check({"progress": 50})

        # No progress for 3 iterations
        for _ in range(2):
            await guard.check({"progress": 50})

        # Should warn on stall
        result = await guard.check({"progress": 50})
        assert result.status == GuardStatus.WARNING
        assert "stall" in result.message.lower()

    @pytest.mark.asyncio
    async def test_eta_calculation(self, guard: ProgressMonitorGuard) -> None:
        """Test ETA calculation."""
        # Start
        await guard.check({"progress": 0})
        await asyncio.sleep(0.1)

        # Progress
        await guard.check({"progress": 50})
        result = await guard.check({"progress": 50})

        # ETA should be calculated if there's history
        if guard._progress_history:
            eta = guard._calculate_eta(50)
            # ETA should be positive or None
            assert eta is None or eta >= 0
