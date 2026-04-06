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


def _is_dead_route(response) -> tuple[bool, str]:
    """
    Detect dead/unregistered routes.
    Returns (is_dead, reason).
    A route is dead if it returns 404 or 405 — meaning the endpoint
    was never registered in the FastAPI app, regardless of whether
    stub code exists in the source file.
    """
    if response.status_code == 404:
        return True, "404 Not Found — endpoint not registered in app.routes"
    if response.status_code == 405:
        return True, "405 Method Not Allowed — endpoint exists but method not allowed"
    return False, ""


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
        GR-04: POST /api/v1/sync/exam-sessions must not return stub.

        Checks in order:
        1. Route is registered (not 404/405) — FAIL if dead route
        2. Response is not a stub pattern — FAIL if stub
        3. Non-5xx status — PASS only if both above pass
        """
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/sync/exam-sessions",
                headers=auth_headers,
                json={},
            )

            # Step 1: Dead route check
            is_dead, dead_reason = _is_dead_route(response)
            assert not is_dead, (
                f"POST /api/v1/sync/exam-sessions is a DEAD ROUTE: {dead_reason}. "
                f"Route not registered in app.routes. Response: {response.json()}"
            )

            # Step 2: Stub check (only if route exists)
            assert response.status_code < 500, f"Server error: {response.status_code}"
            data = response.json()
            is_stub, reason = _is_stub_response(data)

            assert not is_stub, (
                f"POST /api/v1/sync/exam-sessions is an authenticated STUB: {reason}. "
                f"Auth works but no real sync happens. Response: {data}"
            )

    def test_sync_study_notes_not_stub(self, auth_headers):
        """
        GR-05: POST /api/v1/sync/study-notes must not return stub.
        """
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/sync/study-notes",
                headers=auth_headers,
                json={},
            )

            is_dead, dead_reason = _is_dead_route(response)
            assert not is_dead, (
                f"POST /api/v1/sync/study-notes is a DEAD ROUTE: {dead_reason}. "
                f"Response: {response.json()}"
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
        GR-06: POST /api/v1/sync/progress must not return stub.
        """
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/sync/progress",
                headers=auth_headers,
                json={},
            )

            is_dead, dead_reason = _is_dead_route(response)
            assert not is_dead, (
                f"POST /api/v1/sync/progress is a DEAD ROUTE: {dead_reason}. "
                f"Response: {response.json()}"
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
        """
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/push/subscribe",
                headers=auth_headers,
                json={"endpoint": "https://test.example.com/push", "keys": {}},
            )

            is_dead, dead_reason = _is_dead_route(response)
            assert not is_dead, (
                f"POST /api/v1/push/subscribe is a DEAD ROUTE: {dead_reason}. "
                f"Response: {response.json()}"
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
