"""
WP-02: Authenticated Stub Guardrail Tests

Detects the "authenticated stub" anti-pattern:
  - Endpoint requires auth (Depends(get_current_user))
  - But returns fake/pending/hardcoded response instead of real data

Target family: Authenticated stubs that return "not yet implemented" or
fake success with no meaningful side effect.

Coverage: 7 endpoints identified in Phase 2-3 audit.
  - PWA Sync: POST /api/v1/sync/exam-sessions, /sync/study-notes, /sync/progress
  - PWA Push: POST /api/v1/push/subscribe
  - Users:  GET /api/v1/users/export-data, DELETE /api/v1/users/delete-account
  - Questions: POST /api/v1/questions/download

NOT coverage: Public ingest endpoints (telemetry, web-vitals) — those are WP-01.

Standards:
- Uses FastAPI TestClient (sync, no async hangs)
- Uses auth_headers fixture for JWT authentication
- NEVER use assert True (reward hacking prevention)
"""

import pytest
from fastapi.testclient import TestClient

from main import app

STUB_PATTERNS = [
    "stub",
    "not yet implemented",
    "not implemented",
    "coming soon",
]


def _is_stub_response(data: dict) -> tuple[bool, str]:
    """Detect stub response patterns. Returns (is_stub, reason)."""
    # Check top-level message
    msg = data.get("message", "").lower()
    for p in STUB_PATTERNS:
        if p in msg:
            return True, f"message contains '{p}': {msg!r}"

    # Check nested data.message
    inner = data.get("data", {})
    if isinstance(inner, dict):
        inner_msg = inner.get("message", "").lower()
        for p in STUB_PATTERNS:
            if p in inner_msg:
                return True, f"data.message contains '{p}': {inner_msg!r}"

    # Check pending flags with no real action
    if isinstance(inner, dict):
        if inner.get("synced") == 0 and inner.get("pending") == 0:
            # Could be real "nothing to sync" or could be fake zero
            pass  # Handled below
        # Detect fake pending without real data
        if inner.get("export_status") == "pending":
            return True, "export_status is 'pending' — no real export"
        if inner.get("deletion_status") == "pending":
            return True, "deletion_status is 'pending' — no real deletion"
        if inner.get("subscribed") is False:
            return True, "subscribed is False — push not implemented"

    return False, ""


@pytest.mark.guardrail
class TestAuthenticatedStubGuardrails:
    """
    Guardrail tests that FAIL when authenticated endpoints return stub responses.

    These tests assert that authenticated endpoints return MEANINGFUL data,
    not hardcoded fake success with no side effect.
    """

    def test_sync_exam_sessions_not_stub(self, auth_headers):
        """
        GR-04: POST /api/pwa-sync-api/exam-sessions must not return stub.
        Authenticated but returns {"synced": 0, "pending": 0} + "stub" message.
        """
        with TestClient(app) as client:
            response = client.post(
                "/api/pwa-sync-api/exam-sessions",
                headers=auth_headers,
                json={},
            )

            # Accept 200 (stub currently returns 200) or 201/202 (real impl)
            assert response.status_code < 500, f"Server error: {response.status_code}"

            data = response.json()
            is_stub, reason = _is_stub_response(data)

            assert not is_stub, (
                f"POST /api/pwa-sync-api/exam-sessions is an authenticated STUB: {reason}. "
                f"Auth works but no real sync happens. Response: {data}"
            )

    def test_sync_study_notes_not_stub(self, auth_headers):
        """
        GR-05: POST /api/pwa-sync-api/study-notes must not return stub.
        Authenticated but returns {"synced": 0, "pending": 0} + "stub" message.
        """
        with TestClient(app) as client:
            response = client.post(
                "/api/pwa-sync-api/study-notes",
                headers=auth_headers,
                json={},
            )

        assert response.status_code < 500, f"Server error: {response.status_code}"

        data = response.json()
        is_stub, reason = _is_stub_response(data)

        assert not is_stub, (
            f"POST /api/v1/sync/study-notes is an authenticated STUB: {reason}. "
            f"Response: {data}"
        )

    def test_sync_progress_not_stub(self, auth_headers):
        """
        GR-06: POST /api/pwa-sync-api/progress must not return stub.
        Authenticated but returns {"synced": 0, "pending": 0} + "stub" message.
        """
        with TestClient(app) as client:
            response = client.post(
                "/api/pwa-sync-api/progress",
                headers=auth_headers,
                json={},
            )

        assert response.status_code < 500, f"Server error: {response.status_code}"

        data = response.json()
        is_stub, reason = _is_stub_response(data)

        assert not is_stub, (
            f"POST /api/v1/sync/progress is an authenticated STUB: {reason}. "
            f"Response: {data}"
        )

    def test_push_subscribe_not_stub(self, auth_headers):
        """
        GR-07: POST /api/v1/push/subscribe must not return stub.
        Authenticated but returns {"subscribed": False} + "stub" message.
        """
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/push/subscribe",
                headers=auth_headers,
                json={"endpoint": "https://test.example.com/push", "keys": {}},
            )

        assert response.status_code < 500, f"Server error: {response.status_code}"

        data = response.json()
        is_stub, reason = _is_stub_response(data)

        assert not is_stub, (
            f"POST /api/v1/push/subscribe is an authenticated STUB: {reason}. "
            f"Response: {data}"
        )

    def test_export_user_data_not_stub(self, auth_headers):
        """
        GR-08: GET /api/v1/users/export-data must not return stub.
        Authenticated but returns {"export_status": "pending"} + "stub" message.
        """
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/users/export-data",
                headers=auth_headers,
            )

        assert response.status_code < 500, f"Server error: {response.status_code}"

        data = response.json()
        is_stub, reason = _is_stub_response(data)

        assert not is_stub, (
            f"GET /api/v1/users/export-data is an authenticated STUB: {reason}. "
            f"Response: {data}"
        )

    def test_delete_account_not_stub(self, auth_headers):
        """
        GR-09: DELETE /api/v1/users/delete-account must not return stub.
        Authenticated but returns {"deletion_status": "pending"} + "stub" message.
        """
        with TestClient(app) as client:
            response = client.delete(
                "/api/v1/users/delete-account",
                headers=auth_headers,
            )

        assert response.status_code < 500, f"Server error: {response.status_code}"

        data = response.json()
        is_stub, reason = _is_stub_response(data)

        assert not is_stub, (
            f"DELETE /api/v1/users/delete-account is an authenticated STUB: {reason}. "
            f"Response: {data}"
        )

    def test_download_questions_not_stub(self, auth_headers):
        """
        GR-10: POST /api/v1/questions/download must not return stub.
        Authenticated but returns {"questions": [], "total": 0} + "stub" message.
        """
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/questions/download",
                headers=auth_headers,
                json={"subject": "matematik", "count": 10},
            )

        assert response.status_code < 500, f"Server error: {response.status_code}"

        data = response.json()
        is_stub, reason = _is_stub_response(data)

        assert not is_stub, (
            f"POST /api/v1/questions/download is an authenticated STUB: {reason}. "
            f"Response: {data}"
        )
