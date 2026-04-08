"""Debug stub detection"""

import sys

sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from main import app

STUB_PATTERNS = [
    "stub",
    "not yet implemented",
    "not implemented",
    "coming soon",
]


def _is_stub_response(data: dict):
    msg = data.get("message", "").lower()
    for p in STUB_PATTERNS:
        if p in msg:
            return True, f"message contains '{p}': {msg!r}"

    inner = data.get("data", {})
    if isinstance(inner, dict):
        inner_msg = inner.get("message", "").lower()
        for p in STUB_PATTERNS:
            if p in inner_msg:
                return True, f"data.message contains '{p}': {inner_msg!r}"

        if inner.get("export_status") == "pending":
            return True, "export_status is 'pending' — no real export"
        if inner.get("deletion_status") == "pending":
            return True, "deletion_status is 'pending' — no real deletion"
        if inner.get("subscribed") is False:
            return True, "subscribed is False — push not implemented"

    return False, ""


# Monkeypatch JWT
import core.dependencies

core.dependencies.JWT_SECRET = "test-secret-for-unit-tests-only"
core.dependencies.JWT_ALGORITHM = "HS256"

from datetime import UTC, datetime, timedelta

import pyjwt

payload = {
    "sub": "1",
    "username": "test",
    "role": "student",
    "email": "test@example.com",
    "permissions": [],
    "exp": datetime.now(UTC) + timedelta(hours=1),
}
token = pyjwt.encode(
    payload, core.dependencies.JWT_SECRET, algorithm=core.dependencies.JWT_ALGORITHM
)
headers = {"Authorization": f"Bearer {token}"}

with TestClient(app) as client:
    # PWA sync endpoints
    for path in [
        "/api/v1/sync/exam-sessions",
        "/api/v1/sync/progress",
        "/api/v1/push/subscribe",
    ]:
        r = client.post(path, headers=headers, json={})
        print(f"\nPOST {path}")
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.json()}")
        is_stub, reason = _is_stub_response(r.json())
        print(f"  is_stub: {is_stub}, reason: {reason}")

    # Users endpoints
    r = client.get("/api/v1/users/export-data", headers=headers)
    print("\nGET /api/v1/users/export-data")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    is_stub, reason = _is_stub_response(r.json())
    print(f"  is_stub: {is_stub}, reason: {reason}")
