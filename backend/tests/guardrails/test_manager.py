"""Unit tests for GuardrailManager."""
import asyncio

import pytest

from app.guardrails import GuardConfig, GuardrailManager


class TestGuardrailManager:
    """Tests for GuardrailManager."""

    @pytest.fixture
    def manager(self) -> GuardrailManager:
        """Create GuardrailManager with test config."""
        config = GuardConfig(
            max_turns=10,
            timeout_seconds=5,
            failure_threshold=3,
            memory_limit_mb=2048,
            enabled_guards=["MaxTurns", "Timeout", "CircuitBreaker"],
        )
        return GuardrailManager(config)

    @pytest.mark.asyncio
    async def test_initialization(self, manager: GuardrailManager) -> None:
        """Test manager initializes with configured guards."""
        assert len(manager.guards) == 3
        guard_names = [g.name for g in manager.guards]
        assert "MaxTurns" in guard_names
        assert "Timeout" in guard_names
        assert "CircuitBreaker" in guard_names

    @pytest.mark.asyncio
    async def test_start_execution(self, manager: GuardrailManager) -> None:
        """Test start_execution initializes state."""
        manager.start_execution()

        assert manager.start_time is not None
        assert manager.iteration_count == 0

        for guard in manager.guards:
            assert guard.check_count == 0

    @pytest.mark.asyncio
    async def test_check_all_guards_returns_aggregated_result(
        self, manager: GuardrailManager
    ) -> None:
        """Test check_all_guards returns aggregated results."""
        manager.start_execution()

        result = await manager.check_all_guards()

        assert "should_stop" in result
        assert "guard_results" in result
        assert "summary" in result
        assert len(result["guard_results"]) == 3

    @pytest.mark.asyncio
    async def test_stops_when_max_turns_exceeded(self, manager: GuardrailManager) -> None:
        """Test manager stops when maxTurns exceeded."""
        manager.start_execution()

        # Run until limit
        for _ in range(10):
            result = await manager.check_all_guards()
            if result["should_stop"]:
                break

        # 11th check should stop
        result = await manager.check_all_guards()
        assert result["should_stop"] is True
        assert any("MaxTurns" in str(s) for s in result["stops"])

    @pytest.mark.asyncio
    async def test_stops_when_timeout_exceeded(self) -> None:
        """Test manager stops when timeout exceeded."""
        config = GuardConfig(
            max_turns=1000,
            timeout_seconds=0.5,
            enabled_guards=["Timeout"],
        )
        manager = GuardrailManager(config)
        manager.start_execution()

        # Run until timeout
        stopped = False
        for _ in range(100):
            result = await manager.check_all_guards()
            if result["should_stop"]:
                stopped = True
                break
            await asyncio.sleep(0.1)

        assert stopped is True

    @pytest.mark.asyncio
    async def test_generate_report(self, manager: GuardrailManager) -> None:
        """Test report generation."""
        manager.start_execution()

        # Run some iterations
        for _ in range(5):
            await manager.check_all_guards()

        report = manager.generate_report()

        assert report.total_iterations == 5
        assert report.elapsed_time_seconds > 0
        assert report.terminated_by is not None

    @pytest.mark.asyncio
    async def test_enable_disable_guard(self, manager: GuardrailManager) -> None:
        """Test enabling and disabling guards."""
        manager.start_execution()

        # Disable MaxTurns
        assert manager.disable_guard("MaxTurns") is True
        max_turns_guard = manager.get_guard("MaxTurns")
        assert max_turns_guard is not None
        assert max_turns_guard.enabled is False

        # Enable again
        assert manager.enable_guard("MaxTurns") is True
        assert max_turns_guard.enabled is True

        # Try to disable non-existent guard
        assert manager.disable_guard("NonExistent") is False

    @pytest.mark.asyncio
    async def test_emergency_stop(self, manager: GuardrailManager) -> None:
        """Test emergency stop functionality."""
        config = GuardConfig(enabled_guards=["EmergencyStop"])
        manager = GuardrailManager(config)
        manager.start_execution()

        # Trigger emergency stop
        manager.trigger_emergency_stop("Test reason")

        # Check should stop
        result = await manager.check_all_guards()
        assert result["should_stop"] is True

    @pytest.mark.asyncio
    async def test_iteration_counter(self, manager: GuardrailManager) -> None:
        """Test iteration counter increments."""
        manager.start_execution()
        assert manager.iteration_count == 0

        for i in range(5):
            await manager.check_all_guards()
            assert manager.iteration_count == i + 1

    @pytest.mark.asyncio
    async def test_warnings_are_recorded(self, manager: GuardrailManager) -> None:
        """Test warnings are recorded in _warnings list."""
        config = GuardConfig(
            max_turns=10,
            enabled_guards=["MaxTurns"],
        )
        manager = GuardrailManager(config)
        manager.start_execution()

        # Run to warning threshold (80% = 8)
        for _ in range(9):
            await manager.check_all_guards()

        # Should have recorded warnings
        assert len(manager._warnings) > 0


class TestGuardrailManagerConfig:
    """Tests for GuardrailManager configuration."""

    @pytest.mark.asyncio
    async def test_default_config(self) -> None:
        """Test manager works with default config."""
        manager = GuardrailManager()

        assert manager.config.max_turns == 100
        assert manager.config.timeout_seconds == 300
        assert len(manager.guards) == 8  # All guards enabled by default

    @pytest.mark.asyncio
    async def test_dict_config(self) -> None:
        """Test manager accepts dict config."""
        manager = GuardrailManager({
            "max_turns": 50,
            "timeout_seconds": 60,
        })

        assert manager.config.max_turns == 50
        assert manager.config.timeout_seconds == 60

    @pytest.mark.asyncio
    async def test_agent_type_override(self) -> None:
        """Test agent-type-specific config overrides."""
        config = GuardConfig(
            max_turns=100,
            agent_type_overrides={
                "fast_agent": {"max_turns": 20},
            }
        )
        manager = GuardrailManager(config)

        # Start with fast_agent type
        manager.start_execution(agent_type="fast_agent")

        assert manager.config.max_turns == 20

    @pytest.mark.asyncio
    async def test_partial_guard_list(self) -> None:
        """Test manager works with partial guard list."""
        config = GuardConfig(
            enabled_guards=["MaxTurns", "Timeout"],
        )
        manager = GuardrailManager(config)

        assert len(manager.guards) == 2

    @pytest.mark.asyncio
    async def test_to_dict(self) -> None:
        """Test config export to dict."""
        config = GuardConfig(max_turns=50, timeout_seconds=60)
        manager = GuardrailManager(config)

        config_dict = manager.to_dict()
        assert config_dict["max_turns"] == 50
        assert config_dict["timeout_seconds"] == 60


class TestGuardrailManagerWithCircuitBreaker:
    """Tests for GuardrailManager with circuit breaker."""

    @pytest.fixture
    def manager(self) -> GuardrailManager:
        """Create manager with circuit breaker config."""
        config = GuardConfig(
            max_turns=100,
            failure_threshold=2,
            enabled_guards=["CircuitBreaker"],
        )
        return GuardrailManager(config)

    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self, manager: GuardrailManager) -> None:
        """Test circuit breaker opens after failures."""
        manager.start_execution()

        # First failure
        await manager.check_all_guards({"last_operation_failed": True})

        # Second failure - should open circuit
        result = await manager.check_all_guards({"last_operation_failed": True})
        assert result["should_stop"] is True
