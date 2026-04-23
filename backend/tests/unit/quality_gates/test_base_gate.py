"""
Unit Tests for BaseGate
=======================

Tests for the abstract base gate class and its utilities.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.quality_gates.gates.base import BaseGate, GateContext
from backend.core.quality_gates.models import (
    GateConfig,
    GateSeverity,
    GateStatus,
)

# =============================================================================
# Test Fixtures
# =============================================================================

class ConcreteGate(BaseGate):
    """Concrete implementation for testing."""

    def get_name(self) -> str:
        return "test_gate"

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name="test_gate",
            enabled=True,
            blocking=True,
            threshold=7.0,
            warning_threshold=8.5,
            timeout_seconds=60,
            max_retries=1,
            depends_on=[],
            tool_config={},
        )

    async def execute(self, context: GateContext):
        from datetime import datetime

        from backend.core.quality_gates.models import GateResult

        return GateResult(
            gate_name=self.get_name(),
            status=GateStatus.PASS,
            score=9.0,
            threshold=self.config.threshold,
            message="Test passed",
            issues=[],
            metrics=None,
            details={},
            execution_time_ms=100.0,
            blocking=self.config.blocking,
            retries=0,
            auto_fixed=False,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )


@pytest.fixture
def concrete_gate() -> ConcreteGate:
    """Create a concrete gate instance."""
    return ConcreteGate()


# =============================================================================
# Test Cases: Gate Configuration
# =============================================================================

class TestGateConfiguration:
    """Tests for gate configuration."""

    def test_get_name(self, concrete_gate: ConcreteGate):
        """Gate should return its name."""
        assert concrete_gate.get_name() == "test_gate"

    def test_get_default_config(self, concrete_gate: ConcreteGate):
        """Gate should return valid default config."""
        config = concrete_gate.get_default_config()

        assert config.name == "test_gate"
        assert config.enabled is True
        assert config.blocking is True
        assert config.threshold == 7.0
        assert config.warning_threshold == 8.5
        assert config.timeout_seconds == 60

    def test_config_is_accessible(self, concrete_gate: ConcreteGate):
        """Gate config should be accessible after initialization."""
        assert concrete_gate.config is not None
        assert concrete_gate.config.name == "test_gate"

    def test_get_dependencies_default(self, concrete_gate: ConcreteGate):
        """Default dependencies should be empty list."""
        deps = concrete_gate.get_dependencies()
        assert deps == []

    def test_is_blocking(self, concrete_gate: ConcreteGate):
        """is_blocking should return config.blocking value."""
        assert concrete_gate.is_blocking() is True


# =============================================================================
# Test Cases: Status Determination
# =============================================================================

class TestStatusDetermination:
    """Tests for status determination logic."""

    def test_determine_status_pass(self, concrete_gate: ConcreteGate):
        """Score >= warning_threshold should return PASS."""
        status = concrete_gate.determine_status(9.0)
        assert status == GateStatus.PASS

    def test_determine_status_pass_at_threshold(self, concrete_gate: ConcreteGate):
        """Score == warning_threshold should return PASS."""
        status = concrete_gate.determine_status(8.5)
        assert status == GateStatus.PASS

    def test_determine_status_warning(self, concrete_gate: ConcreteGate):
        """Score >= threshold but < warning should return WARNING."""
        status = concrete_gate.determine_status(7.5)
        assert status == GateStatus.WARNING

    def test_determine_status_warning_at_threshold(self, concrete_gate: ConcreteGate):
        """Score == threshold should return WARNING."""
        status = concrete_gate.determine_status(7.0)
        assert status == GateStatus.WARNING

    def test_determine_status_fail(self, concrete_gate: ConcreteGate):
        """Score < threshold should return FAIL."""
        status = concrete_gate.determine_status(6.9)
        assert status == GateStatus.FAIL

    def test_determine_status_zero(self, concrete_gate: ConcreteGate):
        """Score of 0 should return FAIL."""
        status = concrete_gate.determine_status(0.0)
        assert status == GateStatus.FAIL


# =============================================================================
# Test Cases: Score Calculation
# =============================================================================

class TestScoreCalculation:
    """Tests for weighted score calculation."""

    def test_calculate_score_single_metric(self, concrete_gate: ConcreteGate):
        """Calculate score with single metric."""
        metrics = {"quality": 8.0}
        weights = {"quality": 1.0}

        score = concrete_gate.calculate_score(metrics, weights)
        assert score == 8.0

    def test_calculate_score_multiple_metrics(self, concrete_gate: ConcreteGate):
        """Calculate weighted score with multiple metrics."""
        metrics = {"lint": 10.0, "type": 8.0, "complexity": 6.0}
        weights = {"lint": 0.4, "type": 0.3, "complexity": 0.3}

        score = concrete_gate.calculate_score(metrics, weights)
        # 10*0.4 + 8*0.3 + 6*0.3 = 4.0 + 2.4 + 1.8 = 8.2
        assert score == pytest.approx(8.2, rel=0.01)

    def test_calculate_score_empty_metrics(self, concrete_gate: ConcreteGate):
        """Empty metrics should return 0."""
        metrics = {}
        weights = {}

        score = concrete_gate.calculate_score(metrics, weights)
        assert score == 0.0

    def test_calculate_score_missing_weight(self, concrete_gate: ConcreteGate):
        """Missing weight should be treated as 0 but normalized."""
        metrics = {"lint": 10.0, "type": 8.0}
        weights = {"lint": 0.5}  # Missing 'type' weight

        score = concrete_gate.calculate_score(metrics, weights)
        # Only lint is counted: 10*0.5 = 5.0, normalized by total_weight (0.5) = 10.0
        assert score == pytest.approx(10.0, rel=0.01)


# =============================================================================
# Test Cases: Issue Creation
# =============================================================================

class TestIssueCreation:
    """Tests for issue creation helper."""

    def test_create_issue_basic(self, concrete_gate: ConcreteGate):
        """Create basic issue."""
        issue = concrete_gate.create_issue(
            file="src/main.py",
            rule="E001",
            message="Test error",
            severity=GateSeverity.MEDIUM,
        )

        assert issue.file == "src/main.py"
        assert issue.rule == "E001"
        assert issue.message == "Test error"
        assert issue.severity == GateSeverity.MEDIUM
        assert issue.line is None
        assert issue.suggestion is None

    def test_create_issue_with_line(self, concrete_gate: ConcreteGate):
        """Create issue with line number."""
        issue = concrete_gate.create_issue(
            file="src/main.py",
            line=42,
            rule="E001",
            message="Test error",
            severity=GateSeverity.HIGH,
        )

        assert issue.line == 42

    def test_create_issue_with_suggestion(self, concrete_gate: ConcreteGate):
        """Create issue with suggestion."""
        issue = concrete_gate.create_issue(
            file="src/main.py",
            rule="E001",
            message="Missing docstring",
            severity=GateSeverity.LOW,
            suggestion="Add a docstring to the function",
        )

        assert issue.suggestion == "Add a docstring to the function"

    def test_create_issue_all_severities(self, concrete_gate: ConcreteGate):
        """Test all severity levels."""
        for severity in GateSeverity:
            issue = concrete_gate.create_issue(
                file="test.py",
                rule="TEST",
                message="Test",
                severity=severity,
            )
            assert issue.severity == severity


# =============================================================================
# Test Cases: Command Execution
# =============================================================================

class TestCommandExecution:
    """Tests for command execution."""

    @pytest.mark.asyncio
    async def test_run_command_success(self, concrete_gate: ConcreteGate, tmp_path: Path):
        """Run command successfully."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"output", b""))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await concrete_gate.run_command(
                ["echo", "hello"],
                tmp_path,
            )

            assert result.return_code == 0
            assert "output" in result.stdout

    @pytest.mark.asyncio
    async def test_run_command_failure(self, concrete_gate: ConcreteGate, tmp_path: Path):
        """Run command that fails."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b"error"))
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            result = await concrete_gate.run_command(
                ["false"],
                tmp_path,
            )

            assert result.return_code == 1

    def test_run_command_sync_success(self, concrete_gate: ConcreteGate, tmp_path: Path):
        """Run sync command successfully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="output",
                stderr="",
            )

            result = concrete_gate.run_command_sync(
                ["echo", "hello"],
                tmp_path,
            )

            assert result.return_code == 0


# =============================================================================
# Test Cases: Gate Execution
# =============================================================================

class TestGateExecution:
    """Tests for gate execution."""

    @pytest.mark.asyncio
    async def test_execute_returns_result(
        self, concrete_gate: ConcreteGate, gate_context: GateContext
    ):
        """Execute should return a GateResult."""
        result = await concrete_gate.execute(gate_context)

        assert result.gate_name == "test_gate"
        assert result.status == GateStatus.PASS
        assert result.score == 9.0

    @pytest.mark.asyncio
    async def test_run_wraps_execute(
        self, concrete_gate: ConcreteGate, gate_context: GateContext
    ):
        """Run should wrap execute with timeout handling."""
        result = await concrete_gate.run(gate_context)

        assert result.gate_name == "test_gate"
        assert result.status in list(GateStatus)


# =============================================================================
# Test Cases: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_score_boundary_values(self, concrete_gate: ConcreteGate):
        """Test score at boundary values."""
        # Exactly at threshold
        assert concrete_gate.determine_status(7.0) == GateStatus.WARNING

        # Just below threshold
        assert concrete_gate.determine_status(6.999) == GateStatus.FAIL

        # Exactly at warning threshold
        assert concrete_gate.determine_status(8.5) == GateStatus.PASS

        # Just below warning threshold
        assert concrete_gate.determine_status(8.499) == GateStatus.WARNING

    def test_score_extreme_values(self, concrete_gate: ConcreteGate):
        """Test extreme score values."""
        assert concrete_gate.determine_status(10.0) == GateStatus.PASS
        assert concrete_gate.determine_status(0.0) == GateStatus.FAIL
        assert concrete_gate.determine_status(-1.0) == GateStatus.FAIL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
