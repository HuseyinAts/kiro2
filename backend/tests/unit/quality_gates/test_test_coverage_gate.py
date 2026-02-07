"""
Unit Tests for TestCoverageGate
===============================

Tests for line, branch, and function coverage analysis.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.core.quality_gates.models import GateStatus, GateSeverity, GateMetrics
from backend.core.quality_gates.gates.test_coverage import TestCoverageGate
from backend.core.quality_gates.gates.base import GateContext


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def gate() -> TestCoverageGate:
    """Create TestCoverageGate instance."""
    return TestCoverageGate()


@pytest.fixture
def context(tmp_path: Path, gate: TestCoverageGate) -> GateContext:
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

    def test_get_name(self, gate: TestCoverageGate):
        """Gate name should be 'test_coverage'."""
        assert gate.get_name() == "test_coverage"

    def test_default_config_blocking(self, gate: TestCoverageGate):
        """Test coverage should be blocking by default."""
        config = gate.get_default_config()

        assert config.blocking is True

    def test_depends_on_code_quality(self, gate: TestCoverageGate):
        """Should depend on code_quality."""
        deps = gate.get_dependencies()

        assert "code_quality" in deps

    def test_default_thresholds(self, gate: TestCoverageGate):
        """Default thresholds should be reasonable."""
        config = gate.get_default_config()
        tool_config = config.tool_config

        # Line coverage threshold
        assert tool_config.get("line_threshold", 80) >= 60
        # Branch coverage threshold
        assert tool_config.get("branch_threshold", 70) >= 50

    def test_default_weights(self, gate: TestCoverageGate):
        """Default weights should sum to 1.0."""
        config = gate.get_default_config()
        tool_config = config.tool_config

        line_weight = tool_config.get("line_weight", 0.4)
        branch_weight = tool_config.get("branch_weight", 0.3)
        func_weight = tool_config.get("function_weight", 0.3)

        assert abs((line_weight + branch_weight + func_weight) - 1.0) < 0.01


# =============================================================================
# Test Cases: Execution with Mocks
# =============================================================================

class TestExecutionWithMocks:
    """Tests for gate execution with mocked commands."""

    @pytest.mark.asyncio
    async def test_execute_all_pass(self, gate: TestCoverageGate, context: GateContext):
        """Execute with good coverage."""
        with patch.object(gate, "_run_coverage", new_callable=AsyncMock) as mock_coverage, \
             patch.object(gate, "_check_new_code_coverage", new_callable=AsyncMock) as mock_new, \
             patch.object(gate, "_check_critical_paths", new_callable=AsyncMock) as mock_critical:

            mock_coverage.return_value = {
                "line_coverage": 85.0,
                "branch_coverage": 75.0,
                "function_coverage": 90.0,
            }
            mock_new.return_value = 95.0  # Good new code coverage
            mock_critical.return_value = []  # No critical path issues

            result = await gate.execute(context)

            assert result.status in [GateStatus.PASS, GateStatus.WARNING]
            assert result.score >= gate.config.threshold

    @pytest.mark.asyncio
    async def test_execute_low_coverage(self, gate: TestCoverageGate, context: GateContext):
        """Execute with low coverage should fail."""
        with patch.object(gate, "_run_coverage", new_callable=AsyncMock) as mock_coverage, \
             patch.object(gate, "_check_new_code_coverage", new_callable=AsyncMock) as mock_new, \
             patch.object(gate, "_check_critical_paths", new_callable=AsyncMock) as mock_critical:

            mock_coverage.return_value = {
                "line_coverage": 50.0,
                "branch_coverage": 40.0,
                "function_coverage": 60.0,
            }
            mock_new.return_value = None
            mock_critical.return_value = []

            result = await gate.execute(context)

            assert result.score < gate.config.threshold

    @pytest.mark.asyncio
    async def test_execute_coverage_error(self, gate: TestCoverageGate, context: GateContext):
        """Execute with coverage error."""
        with patch.object(gate, "_run_coverage", new_callable=AsyncMock) as mock_coverage:
            mock_coverage.return_value = {
                "error": "pytest not found",
            }

            result = await gate.execute(context)

            assert result.status == GateStatus.ERROR


# =============================================================================
# Test Cases: Score Calculation
# =============================================================================

class TestScoreCalculation:
    """Tests for score calculation using BaseGate.calculate_score()."""

    def test_calculate_score_perfect_coverage(self, gate: TestCoverageGate):
        """Perfect coverage gives max score."""
        # Using the base gate's calculate_score method
        scores = {
            "line": 100.0 / 10,  # 10.0
            "branch": 100.0 / 10,  # 10.0
            "function": 100.0 / 10,  # 10.0
        }
        weights = {
            "line": 0.4,
            "branch": 0.3,
            "function": 0.3,
        }

        score = gate.calculate_score(scores, weights)

        assert score == 10.0

    def test_calculate_score_good_coverage(self, gate: TestCoverageGate):
        """Good coverage gives high score."""
        scores = {
            "line": 85.0 / 10,  # 8.5
            "branch": 75.0 / 10,  # 7.5
            "function": 90.0 / 10,  # 9.0
        }
        weights = {
            "line": 0.4,
            "branch": 0.3,
            "function": 0.3,
        }

        score = gate.calculate_score(scores, weights)

        assert score >= 8.0

    def test_calculate_score_low_coverage(self, gate: TestCoverageGate):
        """Low coverage gives low score."""
        scores = {
            "line": 50.0 / 10,  # 5.0
            "branch": 40.0 / 10,  # 4.0
            "function": 60.0 / 10,  # 6.0
        }
        weights = {
            "line": 0.4,
            "branch": 0.3,
            "function": 0.3,
        }

        score = gate.calculate_score(scores, weights)

        assert score < 6.0

    def test_calculate_score_zero_coverage(self, gate: TestCoverageGate):
        """Zero coverage gives minimum score."""
        scores = {
            "line": 0.0,
            "branch": 0.0,
            "function": 0.0,
        }
        weights = {
            "line": 0.4,
            "branch": 0.3,
            "function": 0.3,
        }

        score = gate.calculate_score(scores, weights)

        assert score == 0.0

    def test_line_coverage_weight(self, gate: TestCoverageGate):
        """Line coverage should have significant weight."""
        # High line coverage, low others
        scores1 = {"line": 10.0, "branch": 5.0, "function": 5.0}
        # Low line coverage, high others
        scores2 = {"line": 5.0, "branch": 10.0, "function": 10.0}
        weights = {"line": 0.4, "branch": 0.3, "function": 0.3}

        score1 = gate.calculate_score(scores1, weights)
        score2 = gate.calculate_score(scores2, weights)

        # Scores should be different due to weighting
        assert abs(score1 - score2) > 0.5


# =============================================================================
# Test Cases: Regression Detection
# =============================================================================

class TestRegressionDetection:
    """Tests for coverage regression detection using _check_regression."""

    def test_check_regression_detects_drop(self, gate: TestCoverageGate):
        """Detect coverage regression when drop exceeds tolerance."""
        current = 80.0
        previous_metrics = GateMetrics(line_coverage=90.0)
        tolerance = 2.0  # 2% tolerance

        issues = gate._check_regression(current, previous_metrics, tolerance)

        # 10% drop > 2% tolerance, should have issue
        assert len(issues) > 0
        # Message format: "Coverage decreased by..."
        assert any("decreased" in str(i.message).lower() or "coverage" in str(i.message).lower()
                  for i in issues)

    def test_check_regression_no_issues_on_improvement(self, gate: TestCoverageGate):
        """No regression when coverage improves."""
        current = 90.0
        previous_metrics = GateMetrics(line_coverage=80.0)
        tolerance = 2.0

        issues = gate._check_regression(current, previous_metrics, tolerance)

        assert len(issues) == 0

    def test_check_regression_no_issues_same_coverage(self, gate: TestCoverageGate):
        """No regression when coverage stays same."""
        current = 80.0
        previous_metrics = GateMetrics(line_coverage=80.0)
        tolerance = 2.0

        issues = gate._check_regression(current, previous_metrics, tolerance)

        assert len(issues) == 0

    def test_check_regression_within_tolerance(self, gate: TestCoverageGate):
        """Small drops within tolerance should not trigger regression."""
        current = 89.0
        previous_metrics = GateMetrics(line_coverage=90.0)
        tolerance = 2.0  # 1% drop is within 2% tolerance

        issues = gate._check_regression(current, previous_metrics, tolerance)

        assert len(issues) == 0

    def test_check_regression_no_previous_metrics(self, gate: TestCoverageGate):
        """No regression issues when no previous metrics."""
        current = 80.0
        tolerance = 2.0

        issues = gate._check_regression(current, None, tolerance)

        assert len(issues) == 0

    def test_check_regression_no_previous_line_coverage(self, gate: TestCoverageGate):
        """No regression issues when previous metrics lack line_coverage."""
        current = 80.0
        previous_metrics = GateMetrics()  # No line_coverage set
        tolerance = 2.0

        issues = gate._check_regression(current, previous_metrics, tolerance)

        assert len(issues) == 0


# =============================================================================
# Test Cases: Issue Creation
# =============================================================================

class TestIssueCreation:
    """Tests for issue creation."""

    def test_create_uncovered_line_issue(self, gate: TestCoverageGate):
        """Create issue for uncovered line."""
        issue = gate.create_issue(
            file="main.py",
            line=10,
            rule="COVERAGE",
            message="Line not covered by tests",
            severity=GateSeverity.LOW,
        )

        assert issue.file == "main.py"
        assert issue.line == 10

    def test_create_regression_issue(self, gate: TestCoverageGate):
        """Create issue for coverage regression."""
        issue = gate.create_issue(
            file="",
            rule="COVERAGE_REGRESSION",
            message="Coverage dropped from 90% to 80%",
            severity=GateSeverity.HIGH,
        )

        assert "dropped" in issue.message.lower()


# =============================================================================
# Test Cases: New Code Coverage
# =============================================================================

class TestNewCodeCoverage:
    """Tests for new code coverage (stricter threshold)."""

    @pytest.mark.asyncio
    async def test_new_code_stricter_threshold(
        self, gate: TestCoverageGate, context: GateContext
    ):
        """New code should have stricter coverage requirements."""
        context.changed_files = ["new_module.py"]

        with patch.object(gate, "_run_coverage", new_callable=AsyncMock) as mock_coverage, \
             patch.object(gate, "_check_new_code_coverage", new_callable=AsyncMock) as mock_new, \
             patch.object(gate, "_check_critical_paths", new_callable=AsyncMock) as mock_critical:

            mock_coverage.return_value = {
                "line_coverage": 85.0,  # Overall good
                "branch_coverage": 75.0,
                "function_coverage": 90.0,
            }
            mock_new.return_value = 70.0  # New code below 90% threshold
            mock_critical.return_value = []

            result = await gate.execute(context)

            # Should flag low new code coverage
            assert result.score < 10.0 or len(result.issues) > 0


# =============================================================================
# Test Cases: Parse Coverage Output
# =============================================================================

class TestParseCoverageOutput:
    """Tests for parsing coverage from stdout."""

    def test_parse_coverage_stdout_with_total(self, gate: TestCoverageGate):
        """Parse coverage from stdout with TOTAL line."""
        stdout = "TOTAL  100  20  80%"

        result = gate._parse_coverage_stdout(stdout)

        assert result["line_coverage"] == 80

    def test_parse_coverage_stdout_no_total(self, gate: TestCoverageGate):
        """Parse coverage when no TOTAL line present."""
        stdout = "some other output"

        result = gate._parse_coverage_stdout(stdout)

        assert result["line_coverage"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
