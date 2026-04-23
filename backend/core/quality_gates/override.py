"""
Quality Gates Override Workflow
===============================

Allows approved exceptions for gate failures with:
- Request/approval workflow
- Audit trail logging
- Expiration support
- Justification requirements

For temporary exceptions when business needs override quality gates.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .models import OverrideApproval, OverrideRequest

logger = logging.getLogger(__name__)


class OverrideManager:
    """
    Manages gate override requests and approvals.

    Provides:
    - Request submission
    - Approval workflow
    - Audit trail
    - Expiration handling
    """

    def __init__(self, storage_path: Path | None = None):
        """
        Initialize override manager.

        Args:
            storage_path: Path to store override data (JSON file)
        """
        self.storage_path = storage_path or Path(".quality-gates-overrides.json")
        self._overrides: dict[str, OverrideApproval] = {}
        self._pending_requests: dict[str, OverrideRequest] = {}
        self._load()

    def _load(self) -> None:
        """Load overrides from storage."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path) as f:
                data = json.load(f)

            for gate_name, override_data in data.get("overrides", {}).items():
                request = OverrideRequest(**override_data["request"])
                approval = OverrideApproval(
                    request=request,
                    approved=override_data["approved"],
                    approver=override_data["approver"],
                    comments=override_data.get("comments"),
                    approved_at=datetime.fromisoformat(override_data["approved_at"]),
                )
                self._overrides[gate_name] = approval

            for gate_name, request_data in data.get("pending", {}).items():
                self._pending_requests[gate_name] = OverrideRequest(**request_data)

        except Exception as e:
            logger.warning(f"Failed to load overrides: {e}")

    def _save(self) -> None:
        """Save overrides to storage."""
        data = {
            "overrides": {},
            "pending": {},
        }

        for gate_name, approval in self._overrides.items():
            data["overrides"][gate_name] = {
                "request": {
                    "gate_name": approval.request.gate_name,
                    "reason": approval.request.reason,
                    "requestor": approval.request.requestor,
                    "ticket_id": approval.request.ticket_id,
                    "expires_at": approval.request.expires_at.isoformat() if approval.request.expires_at else None,
                },
                "approved": approval.approved,
                "approver": approval.approver,
                "comments": approval.comments,
                "approved_at": approval.approved_at.isoformat(),
            }

        for gate_name, request in self._pending_requests.items():
            data["pending"][gate_name] = {
                "gate_name": request.gate_name,
                "reason": request.reason,
                "requestor": request.requestor,
                "ticket_id": request.ticket_id,
                "expires_at": request.expires_at.isoformat() if request.expires_at else None,
            }

        try:
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save overrides: {e}")

    def submit_request(
        self,
        gate_name: str,
        reason: str,
        requestor: str,
        ticket_id: str | None = None,
        expires_in_days: int = 7,
    ) -> OverrideRequest:
        """
        Submit an override request.

        Args:
            gate_name: Gate to override
            reason: Justification (min 20 chars)
            requestor: Who is requesting
            ticket_id: Related issue/ticket
            expires_in_days: How long override should last

        Returns:
            OverrideRequest object
        """
        if len(reason) < 20:
            raise ValueError("Override reason must be at least 20 characters")

        expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

        request = OverrideRequest(
            gate_name=gate_name,
            reason=reason,
            requestor=requestor,
            ticket_id=ticket_id,
            expires_at=expires_at,
        )

        self._pending_requests[gate_name] = request
        self._save()

        logger.info(
            f"Override request submitted for {gate_name} by {requestor}",
            extra={
                "gate_name": gate_name,
                "requestor": requestor,
                "ticket_id": ticket_id,
            },
        )

        return request

    def approve(
        self,
        gate_name: str,
        approver: str,
        comments: str | None = None,
    ) -> OverrideApproval:
        """
        Approve a pending override request.

        Args:
            gate_name: Gate to approve
            approver: Who is approving
            comments: Optional comments

        Returns:
            OverrideApproval object
        """
        if gate_name not in self._pending_requests:
            raise ValueError(f"No pending request for gate {gate_name}")

        request = self._pending_requests.pop(gate_name)

        approval = OverrideApproval(
            request=request,
            approved=True,
            approver=approver,
            comments=comments,
        )

        self._overrides[gate_name] = approval
        self._save()

        logger.info(
            f"Override approved for {gate_name} by {approver}",
            extra={
                "gate_name": gate_name,
                "approver": approver,
                "requestor": request.requestor,
            },
        )

        return approval

    def deny(
        self,
        gate_name: str,
        approver: str,
        comments: str | None = None,
    ) -> OverrideApproval:
        """
        Deny a pending override request.

        Args:
            gate_name: Gate to deny
            approver: Who is denying
            comments: Reason for denial

        Returns:
            OverrideApproval object (with approved=False)
        """
        if gate_name not in self._pending_requests:
            raise ValueError(f"No pending request for gate {gate_name}")

        request = self._pending_requests.pop(gate_name)

        denial = OverrideApproval(
            request=request,
            approved=False,
            approver=approver,
            comments=comments,
        )

        self._save()

        logger.info(
            f"Override denied for {gate_name} by {approver}",
            extra={
                "gate_name": gate_name,
                "approver": approver,
                "requestor": request.requestor,
            },
        )

        return denial

    def revoke(self, gate_name: str) -> None:
        """Revoke an existing override."""
        if gate_name in self._overrides:
            approval = self._overrides.pop(gate_name)
            self._save()

            logger.info(
                f"Override revoked for {gate_name}",
                extra={
                    "gate_name": gate_name,
                    "original_requestor": approval.request.requestor,
                },
            )

    def get_override(self, gate_name: str) -> OverrideApproval | None:
        """Get active override for a gate."""
        approval = self._overrides.get(gate_name)

        if approval:
            # Check expiration
            if approval.request.expires_at and approval.request.expires_at < datetime.now(UTC):
                logger.info(f"Override for {gate_name} has expired")
                self.revoke(gate_name)
                return None

        return approval

    def get_pending_request(self, gate_name: str) -> OverrideRequest | None:
        """Get pending request for a gate."""
        return self._pending_requests.get(gate_name)

    def list_overrides(self) -> list[OverrideApproval]:
        """List all active overrides."""
        # Clean up expired overrides
        expired = []
        for gate_name, approval in self._overrides.items():
            if approval.request.expires_at and approval.request.expires_at < datetime.now(UTC):
                expired.append(gate_name)

        for gate_name in expired:
            self.revoke(gate_name)

        return list(self._overrides.values())

    def list_pending_requests(self) -> list[OverrideRequest]:
        """List all pending requests."""
        return list(self._pending_requests.values())

    def is_overridden(self, gate_name: str) -> bool:
        """Check if a gate has an active override."""
        return self.get_override(gate_name) is not None

    def get_audit_log(self) -> list[dict]:
        """Get audit log of all override activity."""
        # In a real system, this would query a database
        # For now, return current state
        log = []

        for approval in self._overrides.values():
            log.append({
                "type": "approved",
                "gate_name": approval.request.gate_name,
                "requestor": approval.request.requestor,
                "approver": approval.approver,
                "reason": approval.request.reason,
                "timestamp": approval.approved_at.isoformat(),
            })

        for request in self._pending_requests.values():
            log.append({
                "type": "pending",
                "gate_name": request.gate_name,
                "requestor": request.requestor,
                "reason": request.reason,
                "ticket_id": request.ticket_id,
            })

        return sorted(log, key=lambda x: x.get("timestamp", ""), reverse=True)
