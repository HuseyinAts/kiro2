"""
Unit Tests for PerformanceGate
==============================

Tests for load testing, memory profiling, and N+1 detection.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.core.quality_gates.models import GateStatus, GateSeverity
from backend.core.quality_gates.gates.performance import PerformanceGate
from backend.core.quality_gates.gates.base import GateContext


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def gate() -> PerformanceGate:
    """Create PerformanceGate instance."""
    return PerformanceGate()


@pytest.fixture
def context(tmp_path: Path, gate: PerformanceGate) -> GateContext:
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

    def test_get_name(self, gate: PerformanceGate):
        """Gate name should be 'performance'."""
        assert gate.get_name() == "performance"

    def test_default_config_blocking(self, gate: PerformanceGate):
        """Performance should be blocking by default."""
        config = gate.get_default_config()

        assert config.blocking is True

    def test_default_response_thresholds(self, gate: PerformanceGate):
        """Default response time thresholds should be set."""
        config = gate.get_default_config()
        tool_config = config.tool_config

        assert tool_config.get("p95_threshold_ms", 200) <= 500
        assert tool_config.get("p99_threshold_ms", 500) <= 1000

    def test_dependencies(self, gate: PerformanceGate):
        """Should depend on earlier gates."""
        deps = gate.get_dependencies()

        assert len(deps) > 0


# =============================================================================
# Test Cases: Execution with Mocks
# =============================================================================

class TestExecutionWithMocks:
    """Tests for gate execution with mocked commands."""

    @pytest.mark.asyncio
    async def test_execute_all_pass(self, gate: PerformanceGate, context: GateContext):
        """Execute with good performance."""
        with patch.object(gate, "_run_locust", new_callable=AsyncMock) as mock_load, \
             patch.object(gate, "_check_memory", new_callable=AsyncMock) as mock_memory, \
             patch.object(gate, "_check_n_plus_one", new_callable=AsyncMock) as mock_n1:

            # Use actual key names from implementation
            mock_load.return_value = {
                "available": True,
                "score": 10.0,
                "p50": 50,
                "p95": 100,
                "p99": 200,
                "rps": 1000,
                "issues": [],
            }
            mock_memory.return_value = {
                "score": 10.0,
                "current_mb": 256,
                "leak_detected": False,
                "issues": [],
            }
            mock_n1.return_value = {
                "score": 10.0,
                "count": 0,
                "issues": [],
            }

            result = await gate.execute(context)

            assert result.status in [GateStatus.PASS, GateStatus.WARNING]

    @pytest.mark.asyncio
    async def test_execute_slow_response(self, gate: PerformanceGate, context: GateContext):
        """Execute with slow response times."""
        with patch.object(gate, "_run_locust", new_callable=AsyncMock) as mock_load, \
             patch.object(gate, "_check_memory", new_callable=AsyncMock) as mock_memory, \
             patch.object(gate, "_check_n_plus_one", new_callable=AsyncMock) as mock_n1:

            # Must include "available": True for issues to be collected
            mock_load.return_value = {
                "available": True,
                "score": 5.0,
                "p50": 300,
                "p95": 800,  # Above threshold
                "p99": 1500,  # Above threshold
                "rps": 200,
                "issues": [
                    gate.create_issue(
                        file="performance",
                        rule="P95_LATENCY",
                        message="P95 latency 800ms exceeds threshold",
                        severity=GateSeverity.HIGH,
                    ),
                ],
            }
            mock_memory.return_value = {
                "score": 10.0,
                "current_mb": 256,
                "leak_detected": False,
                "issues": [],
            }
            mock_n1.return_value = {
                "score": 10.0,
                "count": 0,
                "issues": [],
            }

            result = await gate.execute(context)

            assert result.score < 10.0
            assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_execute_locust_unavailable(self, gate: PerformanceGate, context: GateContext):
        """Execute when locust is not available."""
        with patch.object(gate, "_run_locust", new_callable=AsyncMock) as mock_load, \
             patch.object(gate, "_check_memory", new_callable=AsyncMock) as mock_memory, \
             patch.object(gate, "_check_n_plus_one", new_callable=AsyncMock) as mock_n1:

            # When available is False, issues are not collected from locust
            mock_load.return_value = {
                "available": False,
                "score": 8.0,
            }
            mock_memory.return_value = {
                "score": 10.0,
                "current_mb": 256,
                "leak_detected": False,
                "issues": [],
            }
            mock_n1.return_value = {
                "score": 10.0,
                "count": 0,
                "issues": [],
            }

            result = await gate.execute(context)

            # Should still pass but with default latency score
            assert result.status in [GateStatus.PASS, GateStatus.WARNING]

    @pytest.mark.asyncio
    async def test_execute_memory_leak(self, gate: PerformanceGate, context: GateContext):
        """Execute with memory leak detected."""
        with patch.object(gate, "_run_locust", new_callable=AsyncMock) as mock_load, \
             patch.object(gate, "_check_memory", new_callable=AsyncMock) as mock_memory, \
             patch.object(gate, "_check_n_plus_one", new_callable=AsyncMock) as mock_n1:

            mock_load.return_value = {
                "available": True,
                "score": 10.0,
                "p50": 50,
                "p95": 100,
                "p99": 200,
                "rps": 1000,
                "issues": [],
            }
            mock_memory.return_value = {
                "score": 3.0,
                "current_mb": 1024,  # High memory
                "leak_detected": True,
                "issues": [
                    gate.create_issue(
                        file="memory",
                        rule="MEMORY_LIMIT",
                        message="Memory usage 1024MB exceeds limit",
                        severity=GateSeverity.HIGH,
                    ),
                ],
            }
            mock_n1.return_value = {
                "score": 10.0,
                "count": 0,
                "issues": [],
            }

            result = await gate.execute(context)

            assert any("memory" in str(i.message).lower()
                      for i in result.issues)

    @pytest.mark.asyncio
    async def test_execute_n_plus_one(self, gate: PerformanceGate, context: GateContext):
        """Execute with N+1 query problem."""
        with patch.object(gate, "_run_locust", new_callable=AsyncMock) as mock_load, \
             patch.object(gate, "_check_memory", new_callable=AsyncMock) as mock_memory, \
             patch.object(gate, "_check_n_plus_one", new_callable=AsyncMock) as mock_n1:

            mock_load.return_value = {
                "available": True,
                "score": 10.0,
                "p50": 50,
                "p95": 100,
                "p99": 200,
                "rps": 1000,
                "issues": [],
            }
            mock_memory.return_value = {
                "score": 10.0,
                "current_mb": 256,
                "leak_detected": False,
                "issues": [],
            }
            mock_n1.return_value = {
                "score": 5.0,
                "count": 3,
                "issues": [
                    gate.create_issue(
                        file="database",
                        rule="N_PLUS_ONE",
                        message="Found 3 potential N+1 query patterns",
                        severity=GateSeverity.MEDIUM,
                    ),
                ],
            }

            result = await gate.execute(context)

            assert any("n+1" in str(i.message).lower() or "query" in str(i.message).lower()
                      for i in result.issues)


# =============================================================================
# Test Cases: Status Determination
# =============================================================================

class TestStatusDetermination:
    """Tests for status determination."""

    def test_status_pass(self, gate: PerformanceGate):
        """High score gives PASS status."""
        status = gate.determine_status(9.0)

        assert status == GateStatus.PASS

    def test_status_warning(self, gate: PerformanceGate):
        """Medium score gives WARNING status."""
        status = gate.determine_status(7.5)

        assert status == GateStatus.WARNING

    def test_status_fail(self, gate: PerformanceGate):
        """Low score gives FAIL status."""
        status = gate.determine_status(5.0)

        assert status == GateStatus.FAIL


# =============================================================================
# Test Cases: Issue Severity
# =============================================================================

class TestIssueSeverity:
    """Tests for issue severity mapping."""

    def test_memory_leak_critical(self, gate: PerformanceGate):
        """Memory leak should be critical."""
        issue = gate.create_issue(
            file="",
            rule="MEMORY_LEAK",
            message="Memory leak detected",
            severity=GateSeverity.CRITICAL,
        )

        assert issue.severity == GateSeverity.CRITICAL

    def test_slow_response_high(self, gate: PerformanceGate):
        """Slow response should be high severity."""
        issue = gate.create_issue(
            file="",
            rule="SLOW_RESPONSE",
            message="P99 response time > 1000ms",
            severity=GateSeverity.HIGH,
        )

        assert issue.severity == GateSeverity.HIGH


# =============================================================================
# Test Cases: Real Check Methods
# =============================================================================

class TestRealMethods:
    """Tests for real internal methods."""

    @pytest.mark.asyncio
    async def test_check_memory_returns_dict(self, gate: PerformanceGate, tmp_path: Path):
        """_check_memory should return a dict with expected keys."""
        result = await gate._check_memory(tmp_path)

        assert isinstance(result, dict)
        assert "score" in result
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_check_n_plus_one_returns_dict(self, gate: PerformanceGate, tmp_path: Path):
        """_check_n_plus_one should return a dict with expected keys."""
        result = await gate._check_n_plus_one(tmp_path)

        assert isinstance(result, dict)
        assert "score" in result
        assert "issues" in result


# =============================================================================
# Test Cases: Message Building
# =============================================================================

class TestMessageBuilding:
    """Tests for message building."""

    def test_build_message_with_locust(self, gate: PerformanceGate):
        """Message with locust available."""
        locust_result = {"available": True, "p95": 150, "rps": 500}
        memory_result = {"current_mb": 200}
        scores = {"latency": 9.0, "memory": 10.0}

        message = gate._build_message(locust_result, memory_result, scores)

        assert "P95" in message
        assert "RPS" in message

    def test_build_message_without_locust(self, gate: PerformanceGate):
        """Message without locust."""
        locust_result = {"available": False}
        memory_result = {"current_mb": 200}
        scores = {"memory": 10.0}

        message = gate._build_message(locust_result, memory_result, scores)

        assert "skipped" in message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
