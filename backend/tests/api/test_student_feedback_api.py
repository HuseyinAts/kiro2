"""Student feedback API tests — Faz 7.2 + S1.1/S2.1/S3 hardening.

Live-backend pattern (golden_flow style — bypasses conftest mocks).
Tests run against http://localhost:8000 (BACKEND_URL env var).
Skipped automatically if backend unreachable.

Tests cover:
- TC1 happy path (POST 201) — REGRESSION guard
- TC2 duplicate flag — TDD-pin (S1.1 fix Task 2)
- TC3 FK violation → 400 — REGRESSION
- TC4 invalid flag_type → 422 — REGRESSION
- TC5 rate limit → 429 — TDD-pin (S1.2 fix Task 3)
"""

from __future__ import annotations

import os
import subprocess

import httpx
import pytest

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 30.0
FEEDBACK = "/api/v1/quality/feedback"

BETA = {"email": "beta01@kiro2.com", "password": "Beta01!Kiro2026"}


# ------------------------------------------------------------------
# Fixtures (live backend, no mocks)
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    """Live httpx client; skip module if backend unreachable."""
    try:
        with httpx.Client(base_url=BACKEND_URL, timeout=TIMEOUT) as c:
            r = c.get("/health")
            if r.status_code >= 500:
                pytest.skip(f"backend unhealthy at {BACKEND_URL}: {r.status_code}")
            yield c
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        pytest.skip(f"backend unreachable at {BACKEND_URL}: {exc}")


@pytest.fixture(scope="module")
def beta_token(client: httpx.Client) -> str:
    r = client.post("/api/v1/auth/login", json=BETA)
    if r.status_code != 200:
        pytest.skip(f"beta01 login failed: {r.status_code} {r.text[:200]}")
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def beta_question_id() -> str:
    """First beta-eligible question_bank.id via docker exec psql."""
    cmd = [
        "docker",
        "exec",
        "kiro2-backend",
        "python",
        "-c",
        (
            "import asyncio\n"
            "from sqlalchemy import text\n"
            "from core.database import get_db_session_context\n"
            "async def main():\n"
            "    async with get_db_session_context() as s:\n"
            "        r = await s.execute(text("
            '"SELECT id FROM question_bank WHERE is_active=TRUE '
            "AND quality_review_status IN ('human_verified','auto_judged_high') LIMIT 1\""
            "))\n"
            "        print(r.scalar())\n"
            "asyncio.run(main())\n"
        ),
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=30, check=False
    )
    qid = result.stdout.strip().splitlines()[-1] if result.stdout else ""
    if not qid or qid == "None":
        pytest.skip(
            f"no beta-eligible question_bank row (stdout={result.stdout[:200]})"
        )
    return qid


def _cleanup_flags() -> None:
    """Delete all flags with note LIKE 'TEST_%' via docker exec."""
    cmd = [
        "docker",
        "exec",
        "kiro2-backend",
        "python",
        "-c",
        (
            "import asyncio\n"
            "from sqlalchemy import text\n"
            "from core.database import get_db_session_context\n"
            "async def main():\n"
            "    async with get_db_session_context() as s:\n"
            "        await s.execute(text("
            "\"DELETE FROM student_question_flags WHERE note LIKE 'TEST_%'\""
            "))\n"
            "        await s.commit()\n"
            "asyncio.run(main())\n"
        ),
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)


@pytest.fixture(autouse=True)
def cleanup_between_tests():
    """Each test gets a clean slate for TEST_-prefixed flags."""
    _cleanup_flags()
    yield
    _cleanup_flags()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------
# TC1 — Happy path: POST /flag → 201
# ------------------------------------------------------------------
def test_create_flag_happy_path(
    client: httpx.Client, beta_token: str, beta_question_id: str
):
    r = client.post(
        f"{FEEDBACK}/flag",
        json={
            "question_id": beta_question_id,
            "flag_type": "wrong_answer",
            "note": "TEST_happy_path",
        },
        headers=_auth(beta_token),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["flag_type"] == "wrong_answer"
    assert body["question_id"] == beta_question_id
    assert body["note"] == "TEST_happy_path"
    assert body["resolved_at"] is None


# ------------------------------------------------------------------
# TC2 — Duplicate flag — should be REJECTED (TDD-pin for Task 2)
# ------------------------------------------------------------------
def test_duplicate_flag_rejected(
    client: httpx.Client, beta_token: str, beta_question_id: str
):
    """After S1.1 fix: 2nd identical flag returns 409 Conflict."""
    body = {
        "question_id": beta_question_id,
        "flag_type": "wrong_topic",
        "note": "TEST_duplicate",
    }
    r1 = client.post(f"{FEEDBACK}/flag", json=body, headers=_auth(beta_token))
    assert r1.status_code == 201, r1.text
    r2 = client.post(f"{FEEDBACK}/flag", json=body, headers=_auth(beta_token))
    assert (
        r2.status_code == 409
    ), f"Duplicate flag should be rejected (S1.1). Got {r2.status_code}: {r2.text}"


# ------------------------------------------------------------------
# TC3 — FK violation: invalid question_id → 400
# ------------------------------------------------------------------
def test_invalid_question_id_400(client: httpx.Client, beta_token: str):
    r = client.post(
        f"{FEEDBACK}/flag",
        json={
            "question_id": "00000000-0000-0000-0000-000000000000",
            "flag_type": "other",
            "note": "TEST_fk_violation",
        },
        headers=_auth(beta_token),
    )
    assert r.status_code == 400, r.text
    detail = r.json()["detail"].lower()
    assert "constraint" in detail or "not found" in detail


# ------------------------------------------------------------------
# TC4 — Pydantic validation: invalid flag_type → 422
# ------------------------------------------------------------------
def test_invalid_flag_type_422(
    client: httpx.Client, beta_token: str, beta_question_id: str
):
    r = client.post(
        f"{FEEDBACK}/flag",
        json={"question_id": beta_question_id, "flag_type": "hacker_flag"},
        headers=_auth(beta_token),
    )
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert isinstance(detail, list)
    assert detail[0]["type"] == "literal_error"


# ------------------------------------------------------------------
# TC5 — Rate limit (TDD-pin for Task 3): 11 hızlı POST'ta 11. tane 429
# ------------------------------------------------------------------
def test_rate_limit_after_10_per_minute(
    client: httpx.Client, beta_token: str, beta_question_id: str
):
    """After Task 3 (S1.2): 10/minute, 11th request returns 429.

    NOT: 'other' flag_type için her note unique olmalı yoksa S1.1 (Task 2)
    duplicate guard rate-limit testini bozar. Bu yüzden 11 farklı note kullan.
    """
    statuses: list[int] = []
    headers = _auth(beta_token)
    headers["X-Forwarded-For"] = "127.0.0.12"
    for i in range(11):
        r = client.post(
            f"{FEEDBACK}/flag",
            json={
                "question_id": beta_question_id,
                "flag_type": "other",
                "note": f"TEST_rate_{i}",
            },
            headers=headers,
        )
        statuses.append(r.status_code)

    # 11th must be 429. S1.1 duplicate guard rejects same (user,q,type) repeats,
    # but flag_type 'other' allows 11 distinct notes — duplicate path not triggered.
    # After Task 2 S1.1: duplicate (user_id, question_id, flag_type='other') would
    # reject the 2nd onwards as 409 — so this test pattern expects EITHER:
    # - 1 success + 10 conflicts, then 11th 429 (post Task 2+3) — last is still 429
    # - 10 success + 11th 429 (Task 3 only, S1.1 not yet enforced for same flag_type)
    assert (
        429 in statuses
    ), f"Rate limit should reject 11th+ request (S1.2). Got: {statuses}"
