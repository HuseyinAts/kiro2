"""
Unit Tests for QualityGatesOrchestrator
=======================================

Tests for pipeline orchestration, parallel execution, and result aggregation.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from core.quality_gates.models import (
    GateConfig,
    GateResult,
    GateStatus,
    PipelineConfig,
    PipelineResult,
)
from core.quality_gates.orchestrator import (
    QualityGatesOrchestrator,
    run_quality_gates,
)
from core.quality_gates.gates.base import BaseGate, GateContext


# =============================================================================
# Mock Gate for Testing
# =============================================================================

class MockGate(BaseGate):
    """Mock gate for testing."""

    def __init__(
        self,
        name: str = "mock_gate",
        result_status: GateStatus = GateStatus.PASS,
        score: float = 9.0,
        blocking: bool = True,
        deps: list[str] | None = None,
    ):
        self._name = name
        self._result_status = result_status
        self._score = score
        self._blocking = blocking
        self._deps = deps or []
        super().__init__()

    def get_name(self) -> str:
        return self._name

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name=self._name,
            enabled=True,
            blocking=self._blocking,
            threshold=7.0,
            warning_threshold=8.5,
            timeout_seconds=60,
            max_retries=1,
            depends_on=self._deps,
            tool_config={},
        )

    def get_dependencies(self) -> list[str]:
        return self._deps

    async def execute(self, context: GateContext) -> GateResult:
        return GateResult(
            gate_name=self._name,
            status=self._result_status,
            score=self._score,
            threshold=7.0,
            message=f"{self._name} result",
            issues=[],
            metrics=None,
            details={},
            execution_time_ms=100.0,
            blocking=self._blocking,
            retries=0,
            auto_fixed=False,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def orchestrator(tmp_path: Path) -> QualityGatesOrchestrator:
    """Create orchestrator instance."""
    return QualityGatesOrchestrator(tmp_path)


@pytest.fixture
def mock_orchestrator(tmp_path: Path) -> QualityGatesOrchestrator:
    """Create orchestrator with mock gates."""
    orch = QualityGatesOrchestrator(tmp_path)

    # Replace gates with mocks
    orch._gates = {
        "gate_a": MockGate("gate_a", GateStatus.PASS),
        "gate_b": MockGate("gate_b", GateStatus.PASS),
    }

    return orch


# =============================================================================
# Test Cases: Initialization
# =============================================================================

class TestInitialization:
    """Tests for orchestrator initialization."""

    def test_init_with_path(self, tmp_path: Path):
        """Initialize orchestrator with working directory."""
        orch = QualityGatesOrchestrator(tmp_path)

        assert orch.working_dir == tmp_path

    def test_init_with_config(self, tmp_path: Path):
        """Initialize with custom config."""
        config = PipelineConfig(
            name="custom-pipeline",
            parallel_execution=False,
            fail_fast=True,
        )
        orch = QualityGatesOrchestrator(tmp_path, config)

        assert orch.config.name == "custom-pipeline"
        assert orch.config.fail_fast is True

    def test_gates_registered(self, orchestrator: QualityGatesOrchestrator):
        """Default gates should be registered."""
        gates = list(orchestrator._gates.keys())

        # Should have default gates
        assert len(gates) > 0
        assert "code_quality" in gates


# =============================================================================
# Test Cases: Gate Management
# =============================================================================

class TestGateManagement:
    """Tests for gate management."""

    def test_get_gate_names(self, mock_orchestrator: QualityGatesOrchestrator):
        """Get list of gate names."""
        names = list(mock_orchestrator._gates.keys())

        assert "gate_a" in names
        assert "gate_b" in names

    def test_get_gate(self, mock_orchestrator: QualityGatesOrchestrator):
        """Get gate by name."""
        gate = mock_orchestrator._gates.get("gate_a")

        assert gate is not None
        assert gate.get_name() == "gate_a"

    def test_get_nonexistent_gate(self, mock_orchestrator: QualityGatesOrchestrator):
        """Get nonexistent gate returns None."""
        gate = mock_orchestrator._gates.get("nonexistent")

        assert gate is None

    def test_register_gate(self, mock_orchestrator: QualityGatesOrchestrator):
        """Register a new gate."""
        new_gate = MockGate("new_gate")
        mock_orchestrator.register_gate("new_gate", new_gate)

        assert "new_gate" in mock_orchestrator._gates

    def test_enable_gate(self, orchestrator: QualityGatesOrchestrator):
        """Enable a gate."""
        orchestrator.disable_gate("code_quality")
        orchestrator.enable_gate("code_quality")

        assert orchestrator._gates["code_quality"].config.enabled is True

    def test_disable_gate(self, orchestrator: QualityGatesOrchestrator):
        """Disable a gate."""
        orchestrator.disable_gate("code_quality")

        assert orchestrator._gates["code_quality"].config.enabled is False


# =============================================================================
# Test Cases: Pipeline Execution
# =============================================================================

class TestPipelineExecution:
    """Tests for pipeline execution."""

    @pytest.mark.asyncio
    async def test_run_all_gates(self, mock_orchestrator: QualityGatesOrchestrator):
        """Run all gates."""
        result = await mock_orchestrator.run()

        assert isinstance(result, PipelineResult)
        assert len(result.gates) == 2
        assert result.status == GateStatus.PASS

    @pytest.mark.asyncio
    async def test_run_with_blocking_failure(self, tmp_path: Path):
        """Pipeline fails when blocking gate fails."""
        orch = QualityGatesOrchestrator(tmp_path)
        orch._gates = {
            "failing_gate": MockGate("failing_gate", GateStatus.FAIL, score=5.0),
        }

        result = await orch.run()

        assert result.status == GateStatus.FAIL
        assert result.failed_gates == 1

    @pytest.mark.asyncio
    async def test_run_parallel_execution(self, tmp_path: Path):
        """Gates execute in parallel when possible."""
        config = PipelineConfig(parallel_execution=True)
        orch = QualityGatesOrchestrator(tmp_path, config)

        orch._gates = {
            "gate_a": MockGate("gate_a"),
            "gate_b": MockGate("gate_b"),
            "gate_c": MockGate("gate_c"),
        }

        result = await orch.run()

        # All gates should run
        assert len(result.gates) == 3


# =============================================================================
# Test Cases: Result Aggregation
# =============================================================================

class TestResultAggregation:
    """Tests for result aggregation."""

    @pytest.mark.asyncio
    async def test_total_score_calculation(self, mock_orchestrator: QualityGatesOrchestrator):
        """Total score is average of gate scores."""
        result = await mock_orchestrator.run()

        # Both gates return 9.0, so average is 9.0
        assert result.total_score == pytest.approx(9.0, rel=0.1)

    @pytest.mark.asyncio
    async def test_passed_gates_count(self, mock_orchestrator: QualityGatesOrchestrator):
        """Count passed gates correctly."""
        result = await mock_orchestrator.run()

        assert result.passed_gates == 2
        assert result.failed_gates == 0

    @pytest.mark.asyncio
    async def test_execution_time_sum(self, mock_orchestrator: QualityGatesOrchestrator):
        """Total execution time is tracked."""
        result = await mock_orchestrator.run()

        assert result.total_execution_time_ms >= 0


# =============================================================================
# Test Cases: Fail Fast Mode
# =============================================================================

class TestFailFastMode:
    """Tests for fail-fast mode."""

    @pytest.mark.asyncio
    async def test_fail_fast_stops_on_failure(self, tmp_path: Path):
        """Fail-fast stops after first blocking failure."""
        config = PipelineConfig(fail_fast=True, parallel_execution=False)
        orch = QualityGatesOrchestrator(tmp_path, config)

        # gate_a fails, gate_b depends on gate_a
        orch._gates = {
            "gate_a": MockGate("gate_a", GateStatus.FAIL, score=5.0, blocking=True),
            "gate_b": MockGate("gate_b", GateStatus.PASS, deps=["gate_a"]),
        }

        result = await orch.run()

        # Pipeline should fail
        assert result.status == GateStatus.FAIL

    @pytest.mark.asyncio
    async def test_no_fail_fast_continues(self, tmp_path: Path):
        """Without fail-fast, continues after failure."""
        config = PipelineConfig(fail_fast=False)
        orch = QualityGatesOrchestrator(tmp_path, config)

        orch._gates = {
            "gate_a": MockGate("gate_a", GateStatus.FAIL, score=5.0, blocking=False),
            "gate_b": MockGate("gate_b", GateStatus.PASS),
        }

        result = await orch.run()

        # Both gates should run
        assert len(result.gates) == 2


# =============================================================================
# Test Cases: Convenience Function
# =============================================================================

class TestConvenienceFunction:
    """Tests for run_quality_gates function."""

    @pytest.mark.asyncio
    async def test_run_quality_gates_function(self, tmp_path: Path):
        """Test convenience function."""
        with patch.object(QualityGatesOrchestrator, "run") as mock_run:
            mock_run.return_value = PipelineResult(
                pipeline_name="test",
                status=GateStatus.PASS,
                gates=[],
                total_score=10.0,
                passed_gates=0,
                failed_gates=0,
                skipped_gates=0,
                total_execution_time_ms=100.0,
            )

            result = await run_quality_gates(tmp_path)

            assert result.status == GateStatus.PASS


# =============================================================================
# Test Cases: Error Handling
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_gate_exception_handled(self, tmp_path: Path):
        """Gate exceptions are handled gracefully."""
        orch = QualityGatesOrchestrator(tmp_path)

        # Create gate that raises exception
        class FailingGate(MockGate):
            async def execute(self, context):
                raise RuntimeError("Test error")

        orch._gates = {"failing": FailingGate("failing")}

        result = await orch.run()

        # Should not crash, gate should be ERROR
        assert len(result.gates) == 1
        assert result.gates[0].status in [GateStatus.ERROR, GateStatus.FAIL]


# =============================================================================
# Test Cases: Git Context
# =============================================================================

class TestGitContext:
    """Tests for git context extraction."""

    def test_get_git_commit(self, orchestrator: QualityGatesOrchestrator):
        """Get current git commit hash."""
        # Call the method (may return None in tmp_path which is not a git repo)
        commit = orchestrator._get_git_commit()

        # Should return commit hash or None
        assert commit is None or isinstance(commit, str)

    def test_get_git_branch(self, orchestrator: QualityGatesOrchestrator):
        """Get current git branch."""
        branch = orchestrator._get_git_branch()

        assert branch is None or isinstance(branch, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
