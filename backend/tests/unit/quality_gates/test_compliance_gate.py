"""
Unit Tests for ComplianceGate
=============================

Tests for GDPR, KVKK, and audit log compliance.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

from backend.core.quality_gates.models import GateStatus, GateSeverity
from backend.core.quality_gates.gates.compliance import ComplianceGate
from backend.core.quality_gates.gates.base import GateContext


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def gate() -> ComplianceGate:
    """Create ComplianceGate instance."""
    return ComplianceGate()


@pytest.fixture
def context(tmp_path: Path, gate: ComplianceGate) -> GateContext:
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

    def test_get_name(self, gate: ComplianceGate):
        """Gate name should be 'compliance'."""
        assert gate.get_name() == "compliance"

    def test_default_config_blocking(self, gate: ComplianceGate):
        """Compliance should be blocking by default."""
        config = gate.get_default_config()

        assert config.blocking is True

    def test_dependencies(self, gate: ComplianceGate):
        """Should depend on earlier gates."""
        deps = gate.get_dependencies()

        assert len(deps) > 0


# =============================================================================
# Test Cases: Execution with Mocks
# =============================================================================

class TestExecutionWithMocks:
    """Tests for gate execution with mocked checks."""

    @pytest.mark.asyncio
    async def test_execute_all_pass(self, gate: ComplianceGate, context: GateContext):
        """Execute with full compliance."""
        with patch.object(gate, "_check_pii_handling", new_callable=AsyncMock) as mock_pii, \
             patch.object(gate, "_check_audit_logging", new_callable=AsyncMock) as mock_audit, \
             patch.object(gate, "_check_consent_management", new_callable=AsyncMock) as mock_consent, \
             patch.object(gate, "_check_data_retention", new_callable=AsyncMock) as mock_retention, \
             patch.object(gate, "_check_gdpr_compliance", new_callable=AsyncMock) as mock_gdpr, \
             patch.object(gate, "_check_kvkk_compliance", new_callable=AsyncMock) as mock_kvkk:

            mock_pii.return_value = {"score": 9.0, "issues": [], "encrypted": True, "pii_count": 10}
            mock_audit.return_value = {"score": 9.0, "issues": []}
            mock_consent.return_value = {"score": 9.0, "issues": []}
            mock_retention.return_value = {"score": 10.0, "issues": []}
            mock_gdpr.return_value = {"score": 8.0, "issues": []}
            mock_kvkk.return_value = {"score": 8.0, "issues": []}

            result = await gate.execute(context)

            assert result.status in [GateStatus.PASS, GateStatus.WARNING]

    @pytest.mark.asyncio
    async def test_execute_gdpr_violation(self, gate: ComplianceGate, context: GateContext):
        """Execute with GDPR violation."""
        with patch.object(gate, "_check_pii_handling", new_callable=AsyncMock) as mock_pii, \
             patch.object(gate, "_check_audit_logging", new_callable=AsyncMock) as mock_audit, \
             patch.object(gate, "_check_consent_management", new_callable=AsyncMock) as mock_consent, \
             patch.object(gate, "_check_data_retention", new_callable=AsyncMock) as mock_retention, \
             patch.object(gate, "_check_gdpr_compliance", new_callable=AsyncMock) as mock_gdpr, \
             patch.object(gate, "_check_kvkk_compliance", new_callable=AsyncMock) as mock_kvkk:

            mock_pii.return_value = {"score": 9.0, "issues": [], "encrypted": True, "pii_count": 5}
            mock_audit.return_value = {"score": 9.0, "issues": []}
            mock_consent.return_value = {"score": 9.0, "issues": []}
            mock_retention.return_value = {"score": 10.0, "issues": []}
            mock_gdpr.return_value = {
                "score": 4.0,
                "issues": [
                    gate.create_issue(
                        file=".",
                        rule="GDPR_RIGHT_TO_ERASURE",
                        message="GDPR right to erasure not implemented",
                        severity=GateSeverity.MEDIUM,
                    ),
                ],
            }
            mock_kvkk.return_value = {"score": 8.0, "issues": []}

            result = await gate.execute(context)

            assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_execute_kvkk_violation(self, gate: ComplianceGate, context: GateContext):
        """Execute with KVKK violation."""
        with patch.object(gate, "_check_pii_handling", new_callable=AsyncMock) as mock_pii, \
             patch.object(gate, "_check_audit_logging", new_callable=AsyncMock) as mock_audit, \
             patch.object(gate, "_check_consent_management", new_callable=AsyncMock) as mock_consent, \
             patch.object(gate, "_check_data_retention", new_callable=AsyncMock) as mock_retention, \
             patch.object(gate, "_check_gdpr_compliance", new_callable=AsyncMock) as mock_gdpr, \
             patch.object(gate, "_check_kvkk_compliance", new_callable=AsyncMock) as mock_kvkk:

            mock_pii.return_value = {"score": 9.0, "issues": [], "encrypted": True, "pii_count": 5}
            mock_audit.return_value = {"score": 9.0, "issues": []}
            mock_consent.return_value = {"score": 9.0, "issues": []}
            mock_retention.return_value = {"score": 10.0, "issues": []}
            mock_gdpr.return_value = {"score": 8.0, "issues": []}
            mock_kvkk.return_value = {
                "score": 5.5,
                "issues": [
                    gate.create_issue(
                        file=".",
                        rule="KVKK_AYDINLATMA_METNI",
                        message="KVKK requirement 'aydinlatma_metni' not found",
                        severity=GateSeverity.MEDIUM,
                    ),
                ],
            }

            result = await gate.execute(context)

            assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_execute_exposed_pii(self, gate: ComplianceGate, context: GateContext):
        """Execute with exposed PII."""
        with patch.object(gate, "_check_pii_handling", new_callable=AsyncMock) as mock_pii, \
             patch.object(gate, "_check_audit_logging", new_callable=AsyncMock) as mock_audit, \
             patch.object(gate, "_check_consent_management", new_callable=AsyncMock) as mock_consent, \
             patch.object(gate, "_check_data_retention", new_callable=AsyncMock) as mock_retention, \
             patch.object(gate, "_check_gdpr_compliance", new_callable=AsyncMock) as mock_gdpr, \
             patch.object(gate, "_check_kvkk_compliance", new_callable=AsyncMock) as mock_kvkk:

            mock_pii.return_value = {
                "score": 2.0,
                "encrypted": False,
                "pii_count": 5,
                "issues": [
                    gate.create_issue(
                        file="models/user.py",
                        rule="PII_UNENCRYPTED",
                        message="PII field 'tc_kimlik' may not be encrypted",
                        severity=GateSeverity.HIGH,
                    ),
                ],
            }
            mock_audit.return_value = {"score": 9.0, "issues": []}
            mock_consent.return_value = {"score": 9.0, "issues": []}
            mock_retention.return_value = {"score": 10.0, "issues": []}
            mock_gdpr.return_value = {"score": 8.0, "issues": []}
            mock_kvkk.return_value = {"score": 8.0, "issues": []}

            result = await gate.execute(context)

            assert any("pii" in str(i.rule).lower() or "encrypt" in str(i.message).lower()
                      for i in result.issues)


# =============================================================================
# Test Cases: Real Checks
# =============================================================================

class TestRealChecks:
    """Tests with actual file analysis."""

    @pytest.mark.asyncio
    async def test_check_pii_handling(self, gate: ComplianceGate, tmp_path: Path):
        """Check PII handling."""
        # Create models directory
        (tmp_path / "models").mkdir()
        (tmp_path / "models" / "user.py").write_text('''
class User:
    email: str
    tc_kimlik: str
    password_hash: str  # encrypted
''')

        result = await gate._check_pii_handling(tmp_path, encryption_required=True)

        assert "score" in result
        assert "pii_count" in result

    @pytest.mark.asyncio
    async def test_check_audit_logging_found(self, gate: ComplianceGate, tmp_path: Path):
        """Check audit logging when present."""
        (tmp_path / "audit_log.py").write_text('''
class AuditLog:
    user_id: int
    action: str
    timestamp: datetime
    resource: str
''')

        result = await gate._check_audit_logging(tmp_path)

        assert result["score"] > 5.0

    @pytest.mark.asyncio
    async def test_check_audit_logging_missing(self, gate: ComplianceGate, tmp_path: Path):
        """Check audit logging when absent."""
        (tmp_path / "main.py").write_text("print('hello')")

        result = await gate._check_audit_logging(tmp_path)

        assert result["score"] < 10.0
        assert len(result["issues"]) > 0

    @pytest.mark.asyncio
    async def test_check_gdpr_compliance(self, gate: ComplianceGate, tmp_path: Path):
        """Check GDPR compliance."""
        (tmp_path / "user_service.py").write_text('''
def export_data(user_id):
    """Export user data for GDPR compliance."""
    pass

def delete_user(user_id):
    """Delete user data - right to erasure."""
    pass

def data_portability(user_id):
    """Support data portability."""
    pass
''')

        result = await gate._check_gdpr_compliance(tmp_path)

        assert "score" in result

    @pytest.mark.asyncio
    async def test_check_kvkk_compliance(self, gate: ComplianceGate, tmp_path: Path):
        """Check KVKK compliance."""
        (tmp_path / "kvkk.py").write_text('''
# KVKK uyumluluk
aydinlatma_metni = "..."
acik_riza_required = True
veri_sorumlusu = "..."
''')

        result = await gate._check_kvkk_compliance(tmp_path)

        assert "score" in result


# =============================================================================
# Test Cases: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_directory(self, gate: ComplianceGate, tmp_path: Path):
        """Handle empty directory."""
        result = await gate._check_pii_handling(tmp_path, encryption_required=True)

        # Should not crash
        assert "score" in result

    @pytest.mark.asyncio
    async def test_unreadable_files(self, gate: ComplianceGate, tmp_path: Path):
        """Handle unreadable files gracefully."""
        # Create a binary file
        (tmp_path / "binary.py").write_bytes(b'\x00\x01\x02\x03')

        result = await gate._check_audit_logging(tmp_path)

        # Should not crash
        assert "score" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
