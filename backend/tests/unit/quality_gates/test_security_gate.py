"""
Unit Tests for SecurityGate
===========================

Tests for Bandit, Safety, and secret detection.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.core.quality_gates.models import GateStatus, GateSeverity
from backend.core.quality_gates.gates.security import SecurityGate
from backend.core.quality_gates.gates.base import GateContext


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def gate() -> SecurityGate:
    """Create SecurityGate instance."""
    return SecurityGate()


@pytest.fixture
def context(tmp_path: Path, gate: SecurityGate) -> GateContext:
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

    def test_get_name(self, gate: SecurityGate):
        """Gate name should be 'security'."""
        assert gate.get_name() == "security"

    def test_default_config_blocking(self, gate: SecurityGate):
        """Security should be blocking by default."""
        config = gate.get_default_config()

        assert config.blocking is True

    def test_depends_on_code_quality(self, gate: SecurityGate):
        """Should depend on code_quality."""
        deps = gate.get_dependencies()

        assert "code_quality" in deps

    def test_default_config_has_tool_config(self, gate: SecurityGate):
        """Should have tool configuration."""
        config = gate.get_default_config()

        assert "bandit_enabled" in config.tool_config
        assert "safety_enabled" in config.tool_config
        assert "secrets_enabled" in config.tool_config


# =============================================================================
# Test Cases: Execution with Mocks
# =============================================================================

class TestExecutionWithMocks:
    """Tests for gate execution with mocked commands."""

    @pytest.mark.asyncio
    async def test_execute_all_pass(self, gate: SecurityGate, context: GateContext):
        """Execute with all security checks passing."""
        with patch.object(gate, "_run_bandit", new_callable=AsyncMock) as mock_bandit, \
             patch.object(gate, "_run_safety", new_callable=AsyncMock) as mock_safety, \
             patch.object(gate, "_run_secrets_scan", new_callable=AsyncMock) as mock_secrets:

            mock_bandit.return_value = {
                "score": 10.0,
                "issues": [],
                "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }
            mock_safety.return_value = {
                "score": 10.0,
                "issues": [],
                "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }
            mock_secrets.return_value = {"secrets_found": 0, "issues": []}

            result = await gate.execute(context)

            assert result.status in [GateStatus.PASS, GateStatus.WARNING]

    @pytest.mark.asyncio
    async def test_execute_with_critical_vulnerability(
        self, gate: SecurityGate, context: GateContext
    ):
        """Execute with critical vulnerability should fail."""
        with patch.object(gate, "_run_bandit", new_callable=AsyncMock) as mock_bandit, \
             patch.object(gate, "_run_safety", new_callable=AsyncMock) as mock_safety, \
             patch.object(gate, "_run_secrets_scan", new_callable=AsyncMock) as mock_secrets:

            mock_bandit.return_value = {
                "score": 5.0,
                "issues": [
                    gate.create_issue(
                        file="main.py",
                        line=10,
                        rule="B101",
                        message="Use of exec detected",
                        severity=GateSeverity.CRITICAL,
                    ),
                ],
                "counts": {"critical": 1, "high": 0, "medium": 0, "low": 0},
            }
            mock_safety.return_value = {
                "score": 10.0,
                "issues": [],
                "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }
            mock_secrets.return_value = {"secrets_found": 0, "issues": []}

            result = await gate.execute(context)

            # Critical vulnerability should cause failure
            assert result.status == GateStatus.FAIL

    @pytest.mark.asyncio
    async def test_execute_with_secret_exposure(
        self, gate: SecurityGate, context: GateContext
    ):
        """Execute with exposed secret should fail."""
        with patch.object(gate, "_run_bandit", new_callable=AsyncMock) as mock_bandit, \
             patch.object(gate, "_run_safety", new_callable=AsyncMock) as mock_safety, \
             patch.object(gate, "_run_secrets_scan", new_callable=AsyncMock) as mock_secrets:

            mock_bandit.return_value = {
                "score": 10.0,
                "issues": [],
                "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }
            mock_safety.return_value = {
                "score": 10.0,
                "issues": [],
                "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }
            mock_secrets.return_value = {
                "secrets_found": 1,
                "issues": [
                    gate.create_issue(
                        file="config.py",
                        line=5,
                        rule="SECRET_EXPOSED",
                        message="Possible API key detected",
                        severity=GateSeverity.CRITICAL,
                    ),
                ],
            }

            result = await gate.execute(context)

            # Exposed secrets should cause failure
            assert result.status == GateStatus.FAIL
            assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_execute_with_vulnerable_dependency(
        self, gate: SecurityGate, context: GateContext
    ):
        """Execute with vulnerable dependency."""
        with patch.object(gate, "_run_bandit", new_callable=AsyncMock) as mock_bandit, \
             patch.object(gate, "_run_safety", new_callable=AsyncMock) as mock_safety, \
             patch.object(gate, "_run_secrets_scan", new_callable=AsyncMock) as mock_secrets:

            mock_bandit.return_value = {
                "score": 10.0,
                "issues": [],
                "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }
            mock_safety.return_value = {
                "score": 5.0,
                "issues": [
                    gate.create_issue(
                        file="requirements.txt",
                        rule="CVE-2021-1234",
                        message="requests: Vulnerable to XSS",
                        severity=GateSeverity.HIGH,
                    ),
                ],
                "counts": {"critical": 0, "high": 1, "medium": 0, "low": 0},
            }
            mock_secrets.return_value = {"secrets_found": 0, "issues": []}

            result = await gate.execute(context)

            assert result.score < 10.0
            assert len(result.issues) > 0


# =============================================================================
# Test Cases: Severity Mapping
# =============================================================================

class TestSeverityMapping:
    """Tests for severity mapping."""

    def test_map_severity_critical(self, gate: SecurityGate):
        """Map critical severity."""
        severity = gate._map_severity("critical")

        assert severity == GateSeverity.CRITICAL

    def test_map_severity_high(self, gate: SecurityGate):
        """Map high severity."""
        severity = gate._map_severity("high")

        assert severity == GateSeverity.HIGH

    def test_map_severity_medium(self, gate: SecurityGate):
        """Map medium severity."""
        severity = gate._map_severity("medium")

        assert severity == GateSeverity.MEDIUM

    def test_map_severity_low(self, gate: SecurityGate):
        """Map low severity."""
        severity = gate._map_severity("low")

        assert severity == GateSeverity.LOW

    def test_map_severity_info(self, gate: SecurityGate):
        """Map info severity."""
        severity = gate._map_severity("info")

        assert severity == GateSeverity.INFO

    def test_map_severity_unknown_defaults_to_medium(self, gate: SecurityGate):
        """Unknown severity should default to medium."""
        severity = gate._map_severity("unknown")

        assert severity == GateSeverity.MEDIUM


# =============================================================================
# Test Cases: Blocking Behavior
# =============================================================================

class TestBlockingBehavior:
    """Tests for blocking behavior."""

    def test_critical_vulnerability_blocks(self, gate: SecurityGate):
        """Critical vulnerability should block pipeline."""
        assert gate.is_blocking() is True

    def test_block_on_critical_config(self, gate: SecurityGate):
        """Block on critical should be configurable."""
        config = gate.get_default_config()

        assert config.tool_config.get("block_on_critical", True) is True

    @pytest.mark.asyncio
    async def test_high_severity_fails_gate(self, gate: SecurityGate, context: GateContext):
        """High severity issues should reduce score."""
        with patch.object(gate, "_run_bandit", new_callable=AsyncMock) as mock_bandit, \
             patch.object(gate, "_run_safety", new_callable=AsyncMock) as mock_safety, \
             patch.object(gate, "_run_secrets_scan", new_callable=AsyncMock) as mock_secrets:

            mock_bandit.return_value = {
                "score": 4.0,  # Low score due to high severity
                "issues": [
                    gate.create_issue(
                        file="main.py",
                        rule="B101",
                        message="Security issue",
                        severity=GateSeverity.HIGH,
                    ),
                ],
                "counts": {"critical": 0, "high": 3, "medium": 0, "low": 0},
            }
            mock_safety.return_value = {
                "score": 10.0,
                "issues": [],
                "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }
            mock_secrets.return_value = {"secrets_found": 0, "issues": []}

            result = await gate.execute(context)

            # Multiple high severity issues should lower score
            assert result.score < 10.0


# =============================================================================
# Test Cases: Message Building
# =============================================================================

class TestMessageBuilding:
    """Tests for message building."""

    def test_build_message_no_vulnerabilities(self, gate: SecurityGate):
        """Message for no vulnerabilities."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        scores = {"bandit": 10.0, "safety": 10.0}

        message = gate._build_message(counts, scores)

        assert "No vulnerabilities" in message

    def test_build_message_with_critical(self, gate: SecurityGate):
        """Message should include critical count."""
        counts = {"critical": 2, "high": 0, "medium": 0, "low": 0}
        scores = {"bandit": 5.0}

        message = gate._build_message(counts, scores)

        assert "Critical: 2" in message

    def test_build_message_with_tool_scores(self, gate: SecurityGate):
        """Message should include tool scores."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        scores = {"bandit": 9.5, "safety": 8.0}

        message = gate._build_message(counts, scores)

        assert "bandit" in message
        assert "safety" in message


# =============================================================================
# Test Cases: Guess Severity
# =============================================================================

class TestGuessSeverity:
    """Tests for severity guessing from description."""

    def test_guess_severity_rce(self, gate: SecurityGate):
        """RCE should be critical."""
        severity = gate._guess_severity("Remote Code Execution vulnerability")

        assert severity == "critical"

    def test_guess_severity_sql_injection(self, gate: SecurityGate):
        """SQL injection should be critical."""
        severity = gate._guess_severity("SQL injection possible")

        assert severity == "critical"

    def test_guess_severity_dos(self, gate: SecurityGate):
        """DoS should be medium."""
        severity = gate._guess_severity("Denial of Service vulnerability")

        assert severity == "medium"

    def test_guess_severity_generic(self, gate: SecurityGate):
        """Generic description should be low."""
        severity = gate._guess_severity("Some generic security issue")

        assert severity == "low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
