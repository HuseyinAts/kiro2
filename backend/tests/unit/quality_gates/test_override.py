"""
Unit Tests for OverrideManager
==============================

Tests for override request and approval workflow.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from backend.core.quality_gates.models import OverrideRequest
from backend.core.quality_gates.override import OverrideManager

# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def override_manager(tmp_path: Path) -> OverrideManager:
    """Create override manager instance."""
    return OverrideManager(storage_path=tmp_path / "overrides.json")


@pytest.fixture
def sample_request() -> dict:
    """Create sample override request data."""
    return {
        "gate_name": "security",
        "reason": "False positive - third-party library pattern detected incorrectly",
        "requestor": "dev@kiro2.com",
        "ticket_id": "KIRO-1234",
        "expires_in_days": 7,
    }


# =============================================================================
# Test Cases: Request Submission
# =============================================================================

class TestRequestSubmission:
    """Tests for override request submission."""

    def test_submit_request(self, override_manager: OverrideManager, sample_request: dict):
        """Submit override request."""
        request = override_manager.submit_request(**sample_request)

        assert request.gate_name == "security"
        assert request.reason == sample_request["reason"]
        assert request.requestor == sample_request["requestor"]

    def test_submit_request_returns_override_request(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Request should be an OverrideRequest instance."""
        request = override_manager.submit_request(**sample_request)

        assert isinstance(request, OverrideRequest)

    def test_submit_request_sets_expiry(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Request should have expiration date."""
        request = override_manager.submit_request(**sample_request)

        assert request.expires_at is not None

    def test_submit_request_calculates_expiry(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Expiry should be calculated from expires_in_days."""
        request = override_manager.submit_request(**sample_request)

        # Expiry should be approximately 7 days from now
        expected_expiry = datetime.now(UTC) + timedelta(days=7)
        diff = abs((request.expires_at - expected_expiry).total_seconds())
        assert diff < 60  # Within 60 seconds

    def test_submit_request_adds_to_pending(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Request should be added to pending list."""
        override_manager.submit_request(**sample_request)

        pending = override_manager.list_pending_requests()
        assert len(pending) == 1
        assert pending[0].gate_name == "security"

    def test_submit_request_short_reason_rejected(
        self, override_manager: OverrideManager
    ):
        """Reason shorter than 20 chars should be rejected."""
        with pytest.raises(ValueError, match="at least 20 characters"):
            override_manager.submit_request(
                gate_name="security",
                reason="Too short",  # Less than 20 chars
                requestor="dev@kiro2.com",
            )


# =============================================================================
# Test Cases: Request Approval
# =============================================================================

class TestRequestApproval:
    """Tests for override request approval."""

    def test_approve_request(self, override_manager: OverrideManager, sample_request: dict):
        """Approve pending request."""
        override_manager.submit_request(**sample_request)

        approval = override_manager.approve(
            gate_name="security",
            approver="admin@kiro2.com",
            comments="Verified as false positive",
        )

        assert approval is not None
        assert approval.approved is True
        assert approval.approver == "admin@kiro2.com"

    def test_approve_removes_from_pending(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Approval should remove from pending."""
        override_manager.submit_request(**sample_request)
        override_manager.approve(
            gate_name="security",
            approver="admin@kiro2.com",
        )

        pending = override_manager.list_pending_requests()
        assert len(pending) == 0

    def test_approve_adds_to_overrides(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Approval should add to active overrides."""
        override_manager.submit_request(**sample_request)
        override_manager.approve(
            gate_name="security",
            approver="admin@kiro2.com",
        )

        overrides = override_manager.list_overrides()
        assert len(overrides) == 1

    def test_approve_nonexistent_request_raises(self, override_manager: OverrideManager):
        """Approving nonexistent request should raise ValueError."""
        with pytest.raises(ValueError, match="No pending request"):
            override_manager.approve(
                gate_name="nonexistent",
                approver="admin@kiro2.com",
            )

    def test_deny_request(self, override_manager: OverrideManager, sample_request: dict):
        """Deny pending request."""
        override_manager.submit_request(**sample_request)

        denial = override_manager.deny(
            gate_name="security",
            approver="admin@kiro2.com",
            comments="Not a valid false positive",
        )

        assert denial.approved is False

    def test_deny_removes_from_pending(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Denial should remove from pending."""
        override_manager.submit_request(**sample_request)
        override_manager.deny(
            gate_name="security",
            approver="admin@kiro2.com",
        )

        pending = override_manager.list_pending_requests()
        assert len(pending) == 0


# =============================================================================
# Test Cases: Request Retrieval
# =============================================================================

class TestRequestRetrieval:
    """Tests for request retrieval."""

    def test_get_pending_request(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Get pending request by gate name."""
        override_manager.submit_request(**sample_request)

        request = override_manager.get_pending_request("security")

        assert request is not None
        assert request.gate_name == "security"

    def test_get_nonexistent_pending_request(self, override_manager: OverrideManager):
        """Get nonexistent pending request returns None."""
        request = override_manager.get_pending_request("nonexistent")

        assert request is None

    def test_get_override(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Get active override by gate name."""
        override_manager.submit_request(**sample_request)
        override_manager.approve(
            gate_name="security",
            approver="admin@kiro2.com",
        )

        approval = override_manager.get_override("security")

        assert approval is not None
        assert approval.request.gate_name == "security"

    def test_list_pending_requests(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """List all pending requests."""
        override_manager.submit_request(**sample_request)
        sample_request["gate_name"] = "code_quality"
        override_manager.submit_request(**sample_request)

        pending = override_manager.list_pending_requests()

        assert len(pending) == 2

    def test_list_overrides(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """List all active overrides."""
        override_manager.submit_request(**sample_request)
        override_manager.approve(gate_name="security", approver="admin@kiro2.com")

        overrides = override_manager.list_overrides()

        assert len(overrides) == 1
        assert overrides[0].request.gate_name == "security"


# =============================================================================
# Test Cases: Override Check
# =============================================================================

class TestOverrideCheck:
    """Tests for checking if gate is overridden."""

    def test_is_overridden_true(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Approved override should return True."""
        override_manager.submit_request(**sample_request)
        override_manager.approve(gate_name="security", approver="admin@kiro2.com")

        result = override_manager.is_overridden("security")

        assert result is True

    def test_is_overridden_false_pending(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Pending override should return False."""
        override_manager.submit_request(**sample_request)

        result = override_manager.is_overridden("security")

        assert result is False

    def test_is_overridden_false_no_request(self, override_manager: OverrideManager):
        """No request should return False."""
        result = override_manager.is_overridden("security")

        assert result is False

    def test_revoke_override(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Revoke an active override."""
        override_manager.submit_request(**sample_request)
        override_manager.approve(gate_name="security", approver="admin@kiro2.com")

        override_manager.revoke("security")

        assert override_manager.is_overridden("security") is False


# =============================================================================
# Test Cases: Audit Trail
# =============================================================================

class TestAuditTrail:
    """Tests for audit trail logging."""

    def test_get_audit_log_empty(self, override_manager: OverrideManager):
        """Empty audit log."""
        log = override_manager.get_audit_log()

        assert isinstance(log, list)

    def test_get_audit_log_with_approved(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Audit log includes approved overrides."""
        override_manager.submit_request(**sample_request)
        override_manager.approve(gate_name="security", approver="admin@kiro2.com")

        log = override_manager.get_audit_log()

        assert len(log) >= 1
        types = [entry["type"] for entry in log]
        assert "approved" in types

    def test_get_audit_log_with_pending(
        self, override_manager: OverrideManager, sample_request: dict
    ):
        """Audit log includes pending requests."""
        override_manager.submit_request(**sample_request)

        log = override_manager.get_audit_log()

        assert len(log) >= 1
        types = [entry["type"] for entry in log]
        assert "pending" in types


# =============================================================================
# Test Cases: Persistence
# =============================================================================

class TestPersistence:
    """Tests for data persistence."""

    def test_save_and_load(self, tmp_path: Path, sample_request: dict):
        """Data should persist across instances."""
        storage_path = tmp_path / "overrides.json"

        # Create manager and submit request
        manager1 = OverrideManager(storage_path=storage_path)
        manager1.submit_request(**sample_request)
        manager1.approve(gate_name="security", approver="admin@kiro2.com")

        # Create new manager with same storage
        manager2 = OverrideManager(storage_path=storage_path)
        override = manager2.get_override("security")

        assert override is not None
        assert override.request.gate_name == "security"

    def test_load_from_nonexistent_file(self, tmp_path: Path):
        """Loading from nonexistent file should not fail."""
        storage_path = tmp_path / "nonexistent.json"
        manager = OverrideManager(storage_path=storage_path)

        # Should work without errors
        assert manager.list_overrides() == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
