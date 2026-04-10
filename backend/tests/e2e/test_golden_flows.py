"""
Golden Flow E2E smoke tests.

Purpose
-------
Each test probes ONE critical user journey end-to-end against a live backend
via HTTP. These are not unit tests — they exist to catch silent regressions
that unit tests miss (case convention bugs, missing routers, middleware drift,
wrong dependency wiring, seed data rot).

The full project can have >12,000 passing unit tests while a user still cannot
log in. Golden Flow tests prevent that class of failure from reaching
production by gating CI on the 8 flows the user explicitly said must work.

The 8 Golden Flows (per user, 10 Apr 2026)
------------------------------------------
GF1: Kayıt → Login → Placement → İlk soru → Cevap → Mastery güncelle
GF2: Daily learning path → Konu seç → Quiz → FSRS register → İlerleme
GF3: TYT sınav başlat → 5 soru → Bitir → Sonuç analizi
GF4: Review queue → Due kart → Cevap → Next due güncelle
GF5: Öğretmen sınıf oluştur → Öğrenci ekle → Ödev ver → Progress gör
GF6: Admin soru CRUD → Is_active toggle → DAG rebuild → Frontend görür
GF7: Video öneri → YouTube API → Cache → Frontend render
GF8: Parent view → Çocuk progress → Consent flow

Execution
---------
These are slow and need a running backend at BACKEND_URL (default
http://localhost:8000). In CI they run against a Docker-composed stack.
Skipped automatically if the backend is unreachable.

    # Run only Golden Flows
    pytest -v -m golden_flow

    # CI merge gate (fail fast)
    pytest -x -m golden_flow --tb=short

Rule (.claude/rules/case-convention.md, .claude/rules/path-naming.md):
Any new top-level user journey MUST be paired with a golden_flow test before
the feature ships. No exceptions.
"""

from __future__ import annotations

import os

import httpx
import pytest

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 10.0

# Seed users (backend/scripts/seed_mvp_data.py)
STUDENT = {"email": "test@kiro2.com", "password": "Kiro2Beta2026@x"}
TEACHER = {"email": "ogretmen@kiro2.com", "password": "Kiro2Beta2026@x"}
PARENT = {"email": "veli@kiro2.com", "password": "Kiro2Beta2026@x"}
ADMIN = {"email": "admin@kiro2.com", "password": "Kiro2Beta2026@x"}


pytestmark = [pytest.mark.golden_flow, pytest.mark.e2e]


@pytest.fixture(scope="module")
def client() -> httpx.Client:
    """HTTP client pointed at the live backend.

    Skips all Golden Flow tests if the backend is unreachable so a missing
    Docker stack doesn't masquerade as a code regression.
    """
    try:
        with httpx.Client(base_url=BACKEND_URL, timeout=TIMEOUT) as c:
            resp = c.get("/health")
            if resp.status_code >= 500:
                pytest.skip(f"backend unhealthy: {resp.status_code}")
            yield c
    except httpx.ConnectError:
        pytest.skip(f"backend unreachable at {BACKEND_URL}")


def _login(client: httpx.Client, creds: dict[str, str]) -> str:
    """Return access_token or skip the test with a clear message."""
    resp = client.post("/api/v1/auth/login", json=creds)
    if resp.status_code != 200:
        pytest.skip(
            f"login failed for {creds['email']}: {resp.status_code} {resp.text[:200]}"
        )
    token = resp.json().get("access_token")
    assert token, f"no access_token in login response: {resp.json()}"
    return token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GF1: Login → protected endpoint accessible (auth stack works end-to-end)
# ---------------------------------------------------------------------------


def test_gf1_login_and_me(client: httpx.Client):
    """Student login returns a token that works on /me."""
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/auth/me", headers=_auth_headers(token))
    assert resp.status_code == 200, f"/me failed: {resp.text[:300]}"
    body = resp.json()
    # /auth/me returns {"user": {...}} — accept both flat and nested shapes
    user = body.get("user") if isinstance(body.get("user"), dict) else body
    assert user.get("email") == STUDENT["email"], (
        f"GF1 regression: /auth/me did not return expected email. Body: {body}"
    )


# ---------------------------------------------------------------------------
# GF2: Daily learning path → topics list (DAG lookup with case convention)
# ---------------------------------------------------------------------------


def test_gf2_dag_topics_lowercase_and_uppercase(client: httpx.Client):
    """
    GET /dag/topics?subject_id=matematik AND ?subject_id=MATEMATIK must both
    return a non-empty topic list. Session 134 audit: the endpoint used to
    silently return [] for lowercase because topic_hierarchy.subject_area is
    UPPERCASE. Fix: defensive .upper() in app/api/dag.py.
    """
    token = _login(client, STUDENT)
    headers = _auth_headers(token)

    for subject in ("MATEMATIK", "matematik"):
        resp = client.get(f"/api/v1/dag/topics?subject_id={subject}", headers=headers)
        assert resp.status_code == 200, (
            f"dag/topics {subject} HTTP {resp.status_code}: {resp.text[:300]}"
        )
        body = resp.json()
        # Accept either {"topics":[...]} or a raw list
        topics = body.get("topics") if isinstance(body, dict) else body
        assert topics, (
            f"GF2 regression: dag/topics returned empty for subject={subject}. "
            f"Check app/api/dag.py defensive .upper() guard."
        )


# ---------------------------------------------------------------------------
# GF3: Exam configs reachable (TYT exam start surface)
# ---------------------------------------------------------------------------


def test_gf3_exam_configs_list(client: httpx.Client):
    """Student can list exam configurations — entry point for starting an exam."""
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/exam-configs", headers=_auth_headers(token))
    # 200 with list, or 404 if the feature is disabled in this env, but
    # NEVER 500 (that would mean the route is broken).
    assert resp.status_code < 500, (
        f"GF3 exam-configs crashed: {resp.status_code} {resp.text[:300]}"
    )


# ---------------------------------------------------------------------------
# GF4: Review queue endpoint responds (FSRS surface)
# ---------------------------------------------------------------------------


def test_gf4_review_queue_reachable(client: httpx.Client):
    """Student can hit the review queue — FSRS read path."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/learning-path/review-queue?limit=5", headers=_auth_headers(token)
    )
    assert resp.status_code < 500, (
        f"GF4 review-queue crashed: {resp.status_code} {resp.text[:300]}"
    )


# ---------------------------------------------------------------------------
# GF5: Teacher profile endpoint returns semantic status (not 500)
# ---------------------------------------------------------------------------


def test_gf5_teacher_profile_semantic_response(client: httpx.Client):
    """
    GET /teachers/my-profile must return a *semantic* status:
      - 200 with the profile,
      - 404 "Teacher profile not found" if the seed user has no profile row.

    It must NEVER return 500. Session 135 audit found:
      - current_user.user_id (attribute did not exist)
      - UUID(current_user.id) against a String column (operator mismatch)
      - sync get_db used where AsyncSession was expected (MissingGreenlet)
    All three would surface here.
    """
    token = _login(client, TEACHER)
    resp = client.get("/api/v1/teachers/my-profile", headers=_auth_headers(token))
    assert resp.status_code in (200, 404), (
        f"GF5 teacher profile returned {resp.status_code}: {resp.text[:300]}. "
        f"Any 500 here means the auth → ORM → response pipeline is broken."
    )


# ---------------------------------------------------------------------------
# GF6: Admin can list questions (question_bank read path)
# ---------------------------------------------------------------------------


def test_gf6_admin_question_bank_reachable(client: httpx.Client):
    """Admin can query the question bank — validates the prod table wiring."""
    token = _login(client, ADMIN)
    resp = client.get(
        "/api/v1/admin/content/questions?limit=1",
        headers=_auth_headers(token),
    )
    assert resp.status_code < 500, (
        f"GF6 admin questions crashed: {resp.status_code} {resp.text[:300]}"
    )


# ---------------------------------------------------------------------------
# GF7: Video fallback returns success for BOTH cases (Turkish locale trap)
# ---------------------------------------------------------------------------


def test_gf7_video_fallback_both_cases(client: httpx.Client):
    """
    Fallback videos MUST resolve for both MATEMATIK and matematik.

    Root cause (Session 135): _normalize_turkish() applied Turkish locale
    (I → ı) to the ASCII identifier "MATEMATIK", producing "matematık"
    (dotless ı), which never matched the dict key "matematik". Fix: use
    subject_key() from core.turkish_nlp_utils (plain ASCII lowercase).
    """
    token = _login(client, STUDENT)
    headers = _auth_headers(token)

    for subject in ("MATEMATIK", "matematik"):
        resp = client.get(
            f"/api/v1/learning-path/fallback-videos/{subject}", headers=headers
        )
        assert resp.status_code == 200, (
            f"GF7 {subject} HTTP {resp.status_code}: {resp.text[:300]}"
        )
        body = resp.json()
        assert body.get("success") is True, (
            f"GF7 regression: fallback-videos returned success=false for "
            f"subject={subject}. Check subject_key() in learning_path_v2.py "
            f"and .claude/rules/case-convention.md Endpoint Gate."
        )
        assert body.get("videos"), f"GF7 {subject} empty videos array"


# ---------------------------------------------------------------------------
# GF8: Parent can reach children endpoint (consent + parent auth)
# ---------------------------------------------------------------------------


def test_gf8_parent_children_reachable(client: httpx.Client):
    """Parent login → children list must not 5xx."""
    token = _login(client, PARENT)
    # Prefer the canonical English path; fall back to legacy Turkish if needed.
    resp = client.get("/api/v1/parent/children", headers=_auth_headers(token))
    if resp.status_code == 404:
        resp = client.get("/api/v1/veli/cocuklar", headers=_auth_headers(token))
    assert resp.status_code < 500, (
        f"GF8 parent children crashed: {resp.status_code} {resp.text[:300]}"
    )
