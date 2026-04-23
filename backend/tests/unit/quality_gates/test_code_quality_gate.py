"""
Unit Tests for CodeQualityGate
==============================

Tests for linting, type checking, and complexity analysis.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.core.quality_gates.gates.base import GateContext
from backend.core.quality_gates.gates.code_quality import CodeQualityGate
from backend.core.quality_gates.models import GateSeverity, GateStatus

# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def gate() -> CodeQualityGate:
    """Create CodeQualityGate instance."""
    return CodeQualityGate()


@pytest.fixture
def context(tmp_path: Path, gate: CodeQualityGate) -> GateContext:
    """Create gate context."""
    return GateContext(
        working_dir=tmp_path,
        config=gate.get_default_config(),
        commit_hash="abc123",
        branch="main",
        changed_files=[],
        previous_result=None,
        extra={},
    )


# =============================================================================
# Test Cases: Configuration
# =============================================================================

class TestConfiguration:
    """Tests for gate configuration."""

    def test_get_name(self, gate: CodeQualityGate):
        """Gate name should be 'code_quality'."""
        assert gate.get_name() == "code_quality"

    def test_default_config_threshold(self, gate: CodeQualityGate):
        """Default threshold should be set."""
        config = gate.get_default_config()

        assert config.threshold > 0
        assert config.threshold <= 10

    def test_default_config_blocking(self, gate: CodeQualityGate):
        """Code quality should be blocking by default."""
        config = gate.get_default_config()

        assert config.blocking is True

    def test_default_config_timeout(self, gate: CodeQualityGate):
        """Should have reasonable timeout."""
        config = gate.get_default_config()

        assert config.timeout_seconds >= 60

    def test_no_dependencies(self, gate: CodeQualityGate):
        """Code quality has no dependencies."""
        deps = gate.get_dependencies()

        assert deps == []


# =============================================================================
# Test Cases: Execution with Mocks
# =============================================================================

class TestExecutionWithMocks:
    """Tests for gate execution with mocked commands."""

    @pytest.mark.asyncio
    async def test_execute_all_pass(self, gate: CodeQualityGate, context: GateContext):
        """Execute with all checks passing."""
        with patch.object(gate, "_run_lint", new_callable=AsyncMock) as mock_lint, \
             patch.object(gate, "_run_type_check", new_callable=AsyncMock) as mock_type, \
             patch.object(gate, "_run_complexity", new_callable=AsyncMock) as mock_complexity, \
             patch.object(gate, "_check_docstrings", new_callable=AsyncMock) as mock_docs, \
             patch.object(gate, "_check_duplication", new_callable=AsyncMock) as mock_dup:

            mock_lint.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_type.return_value = {"score": 10.0, "issues": [], "coverage": 95.0}
            mock_complexity.return_value = {
                "score": 10.0,
                "issues": [],
                "avg_complexity": 3.0,
                "max_complexity": 5,
            }
            mock_docs.return_value = {"coverage": 85.0}
            mock_dup.return_value = {"percent": 2.0}

            result = await gate.execute(context)

            assert result.status in [GateStatus.PASS, GateStatus.WARNING]
            assert result.score >= gate.config.threshold

    @pytest.mark.asyncio
    async def test_execute_with_lint_errors(self, gate: CodeQualityGate, context: GateContext):
        """Execute with lint errors."""
        with patch.object(gate, "_run_lint", new_callable=AsyncMock) as mock_lint, \
             patch.object(gate, "_run_type_check", new_callable=AsyncMock) as mock_type, \
             patch.object(gate, "_run_complexity", new_callable=AsyncMock) as mock_complexity, \
             patch.object(gate, "_check_docstrings", new_callable=AsyncMock) as mock_docs, \
             patch.object(gate, "_check_duplication", new_callable=AsyncMock) as mock_dup:

            mock_lint.return_value = {
                "score": 5.0,
                "issues": [
                    gate.create_issue(
                        file="main.py",
                        line=1,
                        rule="E001",
                        message="Error",
                        severity=GateSeverity.HIGH,
                    ),
                ],
                "count": 10,
            }
            mock_type.return_value = {"score": 10.0, "issues": [], "coverage": 95.0}
            mock_complexity.return_value = {
                "score": 10.0, "issues": [], "avg_complexity": 3.0, "max_complexity": 5
            }
            mock_docs.return_value = {"coverage": 85.0}
            mock_dup.return_value = {"percent": 2.0}

            result = await gate.execute(context)

            assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_execute_with_type_errors(self, gate: CodeQualityGate, context: GateContext):
        """Execute with type errors."""
        with patch.object(gate, "_run_lint", new_callable=AsyncMock) as mock_lint, \
             patch.object(gate, "_run_type_check", new_callable=AsyncMock) as mock_type, \
             patch.object(gate, "_run_complexity", new_callable=AsyncMock) as mock_complexity, \
             patch.object(gate, "_check_docstrings", new_callable=AsyncMock) as mock_docs, \
             patch.object(gate, "_check_duplication", new_callable=AsyncMock) as mock_dup:

            mock_lint.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_type.return_value = {
                "score": 4.0,
                "issues": [
                    gate.create_issue(
                        file="main.py",
                        line=10,
                        rule="TYPE_ERROR",
                        message="Type error",
                        severity=GateSeverity.MEDIUM,
                    ),
                ],
                "coverage": 60.0,
            }
            mock_complexity.return_value = {
                "score": 10.0, "issues": [], "avg_complexity": 3.0, "max_complexity": 5
            }
            mock_docs.return_value = {"coverage": 85.0}
            mock_dup.return_value = {"percent": 2.0}

            result = await gate.execute(context)

            # Score should be reduced
            assert result.score < 10.0

    @pytest.mark.asyncio
    async def test_execute_with_high_complexity(self, gate: CodeQualityGate, context: GateContext):
        """Execute with high complexity."""
        with patch.object(gate, "_run_lint", new_callable=AsyncMock) as mock_lint, \
             patch.object(gate, "_run_type_check", new_callable=AsyncMock) as mock_type, \
             patch.object(gate, "_run_complexity", new_callable=AsyncMock) as mock_complexity, \
             patch.object(gate, "_check_docstrings", new_callable=AsyncMock) as mock_docs, \
             patch.object(gate, "_check_duplication", new_callable=AsyncMock) as mock_dup:

            mock_lint.return_value = {"score": 10.0, "issues": [], "count": 0}
            mock_type.return_value = {"score": 10.0, "issues": [], "coverage": 95.0}
            mock_complexity.return_value = {
                "score": 3.0,  # Low score due to high complexity
                "issues": [
                    gate.create_issue(
                        file="main.py",
                        rule="C901",
                        message="Function too complex",
                        severity=GateSeverity.MEDIUM,
                    ),
                ],
                "avg_complexity": 25.0,
                "max_complexity": 30,
            }
            mock_docs.return_value = {"coverage": 85.0}
            mock_dup.return_value = {"percent": 2.0}

            result = await gate.execute(context)

            # Score should be reduced due to complexity
            assert result.score < 10.0


# =============================================================================
# Test Cases: Status Determination
# =============================================================================

class TestStatusDetermination:
    """Tests for status determination."""

    def test_status_pass(self, gate: CodeQualityGate):
        """High score gives PASS status."""
        status = gate.determine_status(9.0)

        assert status == GateStatus.PASS

    def test_status_warning(self, gate: CodeQualityGate):
        """Medium score gives WARNING status."""
        status = gate.determine_status(7.5)

        assert status == GateStatus.WARNING

    def test_status_fail(self, gate: CodeQualityGate):
        """Low score gives FAIL status."""
        status = gate.determine_status(5.0)

        assert status == GateStatus.FAIL


# =============================================================================
# Test Cases: Issue Creation
# =============================================================================

class TestIssueCreation:
    """Tests for issue creation."""

    def test_create_lint_issue(self, gate: CodeQualityGate):
        """Create lint issue."""
        issue = gate.create_issue(
            file="main.py",
            line=10,
            rule="E001",
            message="Line too long",
            severity=GateSeverity.LOW,
        )

        assert issue.file == "main.py"
        assert issue.line == 10
        assert issue.rule == "E001"

    def test_create_type_issue(self, gate: CodeQualityGate):
        """Create type error issue."""
        issue = gate.create_issue(
            file="main.py",
            line=20,
            rule="TYPE_ERROR",
            message="Incompatible types",
            severity=GateSeverity.MEDIUM,
            suggestion="Add type annotation",
        )

        assert issue.severity == GateSeverity.MEDIUM
        assert issue.suggestion is not None


# =============================================================================
# Test Cases: Weighted Score
# =============================================================================

class TestWeightedScore:
    """Tests for weighted score calculation."""

    def test_weights_config(self, gate: CodeQualityGate):
        """Weights should be in config."""
        config = gate.get_default_config()

        lint_weight = config.tool_config.get("lint_weight", 0)
        type_weight = config.tool_config.get("type_weight", 0)
        complexity_weight = config.tool_config.get("complexity_weight", 0)

        assert lint_weight > 0
        assert type_weight > 0
        assert complexity_weight > 0

    def test_weights_sum_to_one(self, gate: CodeQualityGate):
        """Weights should sum to 1.0."""
        config = gate.get_default_config()

        lint_weight = config.tool_config.get("lint_weight", 0)
        type_weight = config.tool_config.get("type_weight", 0)
        complexity_weight = config.tool_config.get("complexity_weight", 0)

        total = lint_weight + type_weight + complexity_weight
        assert abs(total - 1.0) < 0.01

    def test_lint_has_significant_weight(self, gate: CodeQualityGate):
        """Lint should have significant weight."""
        config = gate.get_default_config()
        lint_weight = config.tool_config.get("lint_weight", 0)

        assert lint_weight >= 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
