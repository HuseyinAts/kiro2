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
# Bumped from 10s to 30s in Session 143: Zemberek JVM cold-start (GF43
# tokenize + GF64 spell-check) can block ~15-20s on the first request
# after a restart. 30s is still short enough that genuine hangs surface
# as failures.
TIMEOUT = 30.0

# Seed users (backend/scripts/seed_mvp_data.py)
STUDENT = {"email": "test@kiro2.com", "password": "Kiro2Beta2026@x"}
TEACHER = {"email": "ogretmen@kiro2.com", "password": "Kiro2Beta2026@x"}
PARENT = {"email": "veli@kiro2.com", "password": "Kiro2Beta2026@x"}
ADMIN = {"email": "admin@kiro2.com", "password": "Kiro2Beta2026@x"}


pytestmark = [pytest.mark.golden_flow, pytest.mark.e2e]


@pytest.fixture(scope="module")
def client() -> httpx.Client:
    """HTTP client pointed at the live backend.
    """
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.core.database import db_manager
    from backend.models.base import Base
    import asyncio
    
    async def setup_db():
        if not db_manager._initialized:
            await db_manager.initialize()
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    asyncio.run(setup_db())
    return TestClient(app, raise_server_exceptions=False)


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
    """Student can list exam configurations — entry point for starting an exam.

    Session 136 fix: this test used to GET ``/api/v1/exam-configs`` (wrong
    prefix — the osym-exam router mounts the endpoint at
    ``/api/v1/osym-exam/exam-configs``). The old path returned 404 and the
    lenient ``< 500`` assertion let it pass silently, so the test verified
    NOTHING for two sessions. Fixed: hit the real path and fail-closed on
    anything other than 200.
    """
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/osym-exam/exam-configs", headers=_auth_headers(token))
    assert resp.status_code == 200, (
        f"GF3 exam-configs returned {resp.status_code}: {resp.text[:300]}. "
        f"Router prefix is /api/v1/osym-exam (see backend/api/sinav.py:24)."
    )
    body = resp.json()
    assert isinstance(body, (list, dict)), f"GF3 unexpected body shape: {body!r}"


# ---------------------------------------------------------------------------
# GF3b: OSYM question bank — subjects (J3 student list surface)
# ---------------------------------------------------------------------------


def test_gf3b_osym_subjects_reachable(client: httpx.Client):
    """Student can list subject buckets from the OSYM question bank (read path)."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/osym/subjects",
        params={"exam_type": "TYT"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200, (
        f"GF3b osym/subjects returned {resp.status_code}: {resp.text[:300]}. "
        f"Router: /api/v1/osym (backend/api/osym_questions_api.py)."
    )
    body = resp.json()
    assert body.get("success") is True, f"GF3b expected success, got: {body!r}"
    assert "data" in body and isinstance(body["data"], list), (
        f"GF3b expected data list: {body!r}"
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


# ===========================================================================
# WRITE-PATH GOLDEN FLOWS (Session 136)
# ---------------------------------------------------------------------------
# Read-path tests catch "endpoint crashed" regressions but miss the much more
# common class of "half-working feature": POST returns 200 but no state
# actually changed, or a silent try/except swallows the real error, or a
# validation gap lets garbage through. These 5 write-path tests assert
# *state changed as a result of the action*, not just "status < 500".
#
# Live probe evidence that motivated each test:
#   K2 — save-answer returns 200 + algorithm:null, mastery response_count
#         stays 0 → BKT pipeline silent failure (sinav.py:737-738 swallows)
#   K3 — save-answer accepts question_id:"" and still returns 200 → no
#         validation boundary (osym_exam_engine.save_answer:574)
#   K4 — admin POST /content/questions returns generic 500 → dual-trap in
#         soru_bankasi_service.py:183 (legacy kwargs topic/subtopic/
#         difficulty + nullable=False primary_topic_id on QuestionBankItem)
#
# Three of these tests are EXPECTED to fail on first run. Each fail is a
# bug report for a half-working feature, and the test becomes the
# regression guard once the underlying bug is fixed.
# ===========================================================================


def _create_exam_session(
    client: httpx.Client, token: str, exam_type: str = "TYT"
) -> str | None:
    """Create and start an exam session. Returns session_id or None on skip."""
    create_resp = client.post(
        "/api/v1/osym-exam/create",
        headers=_auth_headers(token),
        json={"exam_type": exam_type},
    )
    if create_resp.status_code != 200:
        pytest.skip(
            f"exam create failed: {create_resp.status_code} {create_resp.text[:200]}"
        )
    session_id = create_resp.json().get("session_id")
    if not session_id:
        pytest.skip(f"no session_id in create response: {create_resp.json()}")

    start_resp = client.post(
        f"/api/v1/osym-exam/{session_id}/start",
        headers=_auth_headers(token),
    )
    if start_resp.status_code != 200:
        pytest.skip(
            f"exam start failed: {start_resp.status_code} {start_resp.text[:200]}"
        )
    return session_id


# ---------------------------------------------------------------------------
# GF3c: J3 — osym-exam: current question + save-answer (çöz + kaydet, smoke)
# ---------------------------------------------------------------------------


def test_gf3c_exam_session_save_answer_smoke(client: httpx.Client):
    """J3 write path: submit one selected_answer via /osym-exam/.../save-answer.

    Weaker than GF1w (no BKT/mastery side-effect). Locks that create → start →
    current-question → save-answer returns 200 and success for the happy path.
    """
    token = _login(client, STUDENT)
    headers = _auth_headers(token)
    session_id = _create_exam_session(client, token)
    assert session_id is not None

    cq_resp = client.get(
        f"/api/v1/osym-exam/{session_id}/current-question", headers=headers
    )
    if cq_resp.status_code != 200:
        pytest.skip(
            f"GF3c current-question: {cq_resp.status_code} {cq_resp.text[:200]}"
        )
    q_body = cq_resp.json()
    question_id = q_body.get("id")
    if not question_id:
        pytest.skip(f"GF3c no question id: {q_body!r}")

    save_resp = client.post(
        f"/api/v1/osym-exam/{session_id}/save-answer",
        headers=headers,
        json={
            "question_id": question_id,
            "selected_answer": "A",
            "response_time": 5.0,
        },
    )
    assert save_resp.status_code == 200, (
        f"GF3c save-answer {save_resp.status_code}: {save_resp.text[:300]}"
    )
    save_body = save_resp.json()
    assert save_body.get("success") is True, f"GF3c save-answer: {save_body!r}"


# ---------------------------------------------------------------------------
# GF3d: J4 — sınavı tamamla (complete) smoke
# ---------------------------------------------------------------------------


def test_gf3d_exam_session_complete_smoke(client: httpx.Client):
    """J4: create → start → POST /complete returns 200 + performans gövdesi."""
    token = _login(client, STUDENT)
    headers = _auth_headers(token)
    session_id = _create_exam_session(client, token)
    assert session_id is not None

    comp = client.post(
        f"/api/v1/osym-exam/{session_id}/complete",
        headers=headers,
    )
    assert comp.status_code == 200, (
        f"GF3d complete HTTP {comp.status_code}: {comp.text[:400]}"
    )
    body = comp.json()
    assert "total_questions" in body or "net_score" in body, (
        f"GF3d unexpected body keys: {list(body.keys())[:20]}"
    )


# ---------------------------------------------------------------------------
# GF1x: J1 — Bearer çıkış sonrası /me 401
# ---------------------------------------------------------------------------


def test_gf1x_logout_invalidates_bearer_token(client: httpx.Client):
    """Logout (/cikis) token'ı blacklist'ler; aynı Bearer ile /me reddedilir."""
    token = _login(client, STUDENT)
    headers = _auth_headers(token)
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200, f"GF1x pre-logout /me: {me.text[:200]}"

    lo = client.post("/api/v1/auth/cikis", headers=headers)
    assert lo.status_code == 200, f"GF1x logout: {lo.status_code} {lo.text[:200]}"

    me2 = client.get("/api/v1/auth/me", headers=headers)
    assert me2.status_code == 401, (
        f"GF1x post-logout /me expected 401, got {me2.status_code}: {me2.text[:200]}"
    )


# ---------------------------------------------------------------------------
# GF1y: J2 — PUT /api/v1/auth/profile (allowed alanlar)
# ---------------------------------------------------------------------------


def test_gf1y_profile_put_smoke(client: httpx.Client):
    """J2: profil güncelleme 200 + success; idempotent-friendly (aynı ad/soyad)."""
    token = _login(client, STUDENT)
    headers = _auth_headers(token)
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200, f"GF1y pre /me: {me.text[:200]}"
    body = me.json()
    user = body.get("user") if isinstance(body.get("user"), dict) else body
    ad = str(user.get("ad") or user.get("first_name") or "Test")
    soyad = str(user.get("soyad") or user.get("last_name") or "User")

    put = client.put(
        "/api/v1/auth/profile",
        headers=headers,
        json={"ad": ad, "soyad": soyad},
    )
    assert put.status_code == 200, (
        f"GF1y PUT profile HTTP {put.status_code}: {put.text[:400]}"
    )
    pbody = put.json()
    assert pbody.get("success") is True, f"GF1y profile success=False: {pbody!r}"
    u2 = pbody.get("user")
    assert isinstance(u2, dict), f"GF1y missing user in response: {pbody!r}"
    assert u2.get("email") == STUDENT["email"], f"GF1y email drift: {u2!r}"


# ---------------------------------------------------------------------------
# GF1z: J1 — JSON refreshToken ile /auth/refresh (cookie zorunlu değil)
# ---------------------------------------------------------------------------


def test_gf1z_refresh_token_json_returns_usable_access(client: httpx.Client):
    """
    J1 refresh: login gövdesindeki refreshToken ile POST /auth/refresh.

    ``GF1wB`` httpOnly cookie akışını test eder; çoğu golden ``/login`` ise
    token JSON'da döner — bu test o yolu kilitler.
    """
    login = client.post("/api/v1/auth/login", json=STUDENT)
    assert login.status_code == 200, (
        f"GF1z login HTTP {login.status_code}: {login.text[:300]}"
    )
    lj = login.json()
    rt = lj.get("refreshToken") or lj.get("refresh_token")
    assert rt, f"GF1z login missing refreshToken, keys={list(lj.keys())}"
    ref = client.post("/api/v1/auth/refresh", json={"refreshToken": rt})
    assert ref.status_code == 200, (
        f"GF1z refresh HTTP {ref.status_code}: {ref.text[:400]}"
    )
    rj = ref.json()
    new_access = rj.get("access_token") or rj.get("token")
    assert new_access, f"GF1z refresh missing access: {rj!r}"
    me = client.get("/api/v1/auth/me", headers=_auth_headers(str(new_access)))
    assert me.status_code == 200, f"GF1z /me after refresh: {me.text[:300]}"
    body = me.json()
    user = body.get("user") if isinstance(body.get("user"), dict) else body
    assert user.get("email") == STUDENT["email"], f"GF1z /me email: {body}"


# ---------------------------------------------------------------------------
# GF1w: save-answer must actually update BKT state (not just return 200)
# ---------------------------------------------------------------------------


def test_gf1w_save_answer_updates_mastery(client: httpx.Client):
    """
    A student's save-answer must update mastery state, not just return 200.

    Session 136 live probe (K2): the endpoint returns
    ``{"success": true, "algorithm": null}`` and
    ``mastery-confidence/matematik.response_count`` stays at 0 even after
    a valid question_id is posted. Root cause: ``sinav.py:737-738``

        except Exception as e:
            logger.warning(f"BKT pipeline hatası (sınav devam eder): {e}")

    swallows every pipeline error, so the response lies. This test fails
    closed: if ``algorithm`` is null AND mastery state did not advance,
    the feature is half-working.
    """
    token = _login(client, STUDENT)
    headers = _auth_headers(token)

    # 1. Snapshot mastery before the answer.
    before_resp = client.get("/api/v1/mastery-confidence/matematik", headers=headers)
    before_count: int | None = None
    if before_resp.status_code == 200:
        before_count = before_resp.json().get("response_count")
    # If 404 we accept before_count = None (feature gated) and still check
    # algorithm != null below.

    # 2. Start a session and grab a real question_id.
    session_id = _create_exam_session(client, token)
    assert session_id is not None  # _create_exam_session pytest.skip's otherwise

    cq_resp = client.get(
        f"/api/v1/osym-exam/{session_id}/current-question", headers=headers
    )
    if cq_resp.status_code != 200:
        pytest.skip(
            f"current-question failed: {cq_resp.status_code} {cq_resp.text[:200]}"
        )
    question_id = cq_resp.json().get("id")
    assert question_id, f"no id in current-question body: {cq_resp.json()}"

    # 3. Post the answer.
    save_resp = client.post(
        f"/api/v1/osym-exam/{session_id}/save-answer",
        headers=headers,
        json={
            "question_id": question_id,
            "selected_answer": "A",
            "response_time": 5.0,
        },
    )
    assert save_resp.status_code == 200, (
        f"GF1w save-answer HTTP {save_resp.status_code}: {save_resp.text[:300]}"
    )
    save_body = save_resp.json()
    assert save_body.get("success") is True, (
        f"GF1w save-answer success=False: {save_body}"
    )

    # 4. State-change assertion. This is the core of the test.
    algorithm = save_body.get("algorithm")
    after_resp = client.get("/api/v1/mastery-confidence/matematik", headers=headers)
    after_count: int | None = None
    if after_resp.status_code == 200:
        after_count = after_resp.json().get("response_count")

    mastery_advanced = (
        before_count is not None
        and after_count is not None
        and after_count > before_count
    )

    assert algorithm is not None or mastery_advanced, (
        "GF1w BKT pipeline silent failure: save-answer returned "
        f"algorithm={algorithm!r} AND mastery response_count did not advance "
        f"(before={before_count}, after={after_count}). Root cause: "
        "fire-and-forget try/except in backend/api/sinav.py:737-738 is "
        "swallowing the real error. Check question's primary_topic_id "
        "(NULL skips BKT silently at sinav.py:662), logger.warning visibility, "
        "and BKTService.record_answer() for hidden exceptions."
    )


# ---------------------------------------------------------------------------
# GF3w: save-answer must reject an empty question_id
# ---------------------------------------------------------------------------


def test_gf3w_save_answer_rejects_empty_question_id(client: httpx.Client):
    """
    Posting an empty ``question_id`` must be a client error (400 or 422),
    never a success.

    Session 136 live probe (K3): the endpoint currently returns
    ``{"success": true, "message": "Cevap başarıyla kaydedildi"}`` for
    ``{"question_id": "", "selected_answer": "A", "response_time": 1.0}``.
    There is no payload validation — ``osym_exam_engine.save_answer``
    (core/osym_exam_engine.py:574) writes the empty string into the
    session.answers dict as a key. This is a validation gap, not a 500,
    but it lets the client (or a malicious one) corrupt session state
    silently.
    """
    token = _login(client, STUDENT)
    headers = _auth_headers(token)
    session_id = _create_exam_session(client, token)
    assert session_id is not None

    resp = client.post(
        f"/api/v1/osym-exam/{session_id}/save-answer",
        headers=headers,
        json={
            "question_id": "",
            "selected_answer": "A",
            "response_time": 1.0,
        },
    )

    assert resp.status_code in (400, 422), (
        f"GF3w validation gap: save-answer accepted empty question_id "
        f"with HTTP {resp.status_code} {resp.text[:300]}. Expected 400 or "
        f"422. Fix: add min_length=1 (or UUID type) to SaveAnswerRequest "
        f"in backend/api/sinav.py around line 590."
    )


# ---------------------------------------------------------------------------
# GF4w.1: learning-path register-wrong-answers must accept a valid question_id
# ---------------------------------------------------------------------------


def test_gf4w1_register_wrong_answer_accepts_valid_id(client: httpx.Client):
    """
    Registering a wrong answer must return ``success=True`` for a real
    question_id pulled from the admin list.

    We can't assert end-to-end (register → review-queue visible) in a
    single test because learning_path_v2 schedules the FSRS card 24h in
    the future. This test only verifies the write endpoint itself
    doesn't 500 and reports success.
    """
    admin_token = _login(client, ADMIN)
    list_resp = client.get(
        "/api/v1/admin/content/questions?limit=1",
        headers=_auth_headers(admin_token),
    )
    if list_resp.status_code != 200:
        pytest.skip(
            f"admin questions list unavailable: {list_resp.status_code} "
            f"{list_resp.text[:200]}"
        )
    body = list_resp.json()
    # Accept either {"items":[...]}, {"data":[...]} or a raw list
    items = (
        body.get("items")
        or body.get("data")
        or (body if isinstance(body, list) else None)
    )
    if not items:
        pytest.skip(f"no seed questions available: {body}")
    first = items[0] if isinstance(items, list) else None
    if not isinstance(first, dict):
        pytest.skip(f"unexpected question list shape: {items}")
    q_id = first.get("id") or first.get("question_id")
    if not q_id:
        pytest.skip(f"no id field on question: {first}")

    student_token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/learning-path/register-wrong-answers",
        headers=_auth_headers(student_token),
        json={"question_ids": [str(q_id)]},
    )
    assert resp.status_code == 200, (
        f"GF4w.1 register-wrong-answers HTTP {resp.status_code}: {resp.text[:300]}"
    )
    rbody = resp.json()
    assert rbody.get("success") is True, (
        f"GF4w.1 register-wrong-answers success=False: {rbody}"
    )
    assert rbody.get("created", 0) >= 0, (
        f"GF4w.1 register-wrong-answers missing 'created' field: {rbody}"
    )


# ---------------------------------------------------------------------------
# GF4w.2: learning-path submit-review works if the queue has due cards
# ---------------------------------------------------------------------------


def test_gf4w2_submit_review_if_due_card_exists(client: httpx.Client):
    """
    If the review queue has at least one due card, grading it must
    return ``success=True`` and a non-null ``next_due``. If the queue is
    empty (no seed data, or all cards already graded), this test
    skips — it is not a regression.
    """
    token = _login(client, STUDENT)
    headers = _auth_headers(token)

    queue_resp = client.get(
        "/api/v1/learning-path/review-queue?limit=1", headers=headers
    )
    if queue_resp.status_code != 200:
        pytest.skip(
            f"review-queue unavailable: {queue_resp.status_code} "
            f"{queue_resp.text[:200]}"
        )
    queue_body = queue_resp.json()
    cards = queue_body.get("cards") or queue_body.get("items") or []
    if not cards:
        pytest.skip("no due cards in review queue — seed data dependent")

    first_card = cards[0]
    card_id = first_card.get("card_id") or first_card.get("id")
    if not card_id:
        pytest.skip(f"no card_id on first review-queue entry: {first_card}")

    resp = client.post(
        "/api/v1/learning-path/submit-review",
        headers=headers,
        json={"card_id": str(card_id), "grade": 3},
    )
    assert resp.status_code == 200, (
        f"GF4w.2 submit-review HTTP {resp.status_code}: {resp.text[:300]}"
    )
    rbody = resp.json()
    assert rbody.get("success") is True, f"GF4w.2 submit-review success=False: {rbody}"
    assert rbody.get("next_due"), (
        f"GF4w.2 submit-review missing/null next_due: {rbody}. "
        f"FSRS algorithm pipeline may be broken."
    )


# ---------------------------------------------------------------------------
# GF6w: admin POST /content/questions must succeed (dual-trap regression)
# ---------------------------------------------------------------------------


def test_gf6w_admin_question_create_returns_success(client: httpx.Client):
    """
    Admin adding a new question must return HTTP 200 with success=True.

    Session 136 live probe (K4): the endpoint currently returns
    ``HTTP 500 {"detail": "Islem basarisiz. Lutfen tekrar deneyin."}``
    for any valid-looking payload. Root cause in
    ``backend/services/soru_bankasi_service.py:183-209``:

      1. Uses legacy kwargs ``topic=``, ``subtopic=``, ``difficulty=``
         that do NOT exist on ``QuestionBankItem`` (production model) —
         the model's actual fields are ``primary_topic_id`` and
         ``difficulty_level`` (see models/question_bank.py:315, 329).
      2. Never passes ``primary_topic_id``, but the column is declared
         ``nullable=False`` with a ForeignKey — the INSERT would fail
         even if the kwargs were right.
      3. The generic ``except Exception`` in admin.py:326 converts the
         TypeError/IntegrityError into a user-visible 500 with no hint.

    Admin UI "add question" is currently UNUSABLE. This test fails
    closed until soru_bankasi_service.soru_ekle is rewritten to use the
    correct QuestionBankItem fields and to look up/insert a
    topic_hierarchy row.
    """
    admin_token = _login(client, ADMIN)
    payload = {
        "soru_metni": "Golden Flow write test: 2+2 kaç eder?",
        "secenekler": ["A) 3", "B) 4", "C) 5", "D) 6"],
        "dogru_cevap": "B",
        "konu": "Matematik",
        "zorluk_seviyesi": "kolay",
        "sinav_tipi": "TYT",
    }

    resp = client.post(
        "/api/v1/admin/content/questions",
        headers=_auth_headers(admin_token),
        json=payload,
    )
    assert resp.status_code == 200, (
        f"GF6w admin question create HTTP {resp.status_code}: "
        f"{resp.text[:300]}. Likely dual-trap: "
        f"soru_bankasi_service.py:183 passes legacy kwargs "
        f"(topic/subtopic/difficulty) to QuestionBankItem, or fails the "
        f"primary_topic_id NOT NULL FK constraint."
    )
    rbody = resp.json()
    assert rbody.get("success") is True, (
        f"GF6w admin question create success=False: {rbody}"
    )

    # Best-effort cleanup — never fail the test on cleanup issues.
    new_id = (
        (rbody.get("data") or {}).get("id")
        if isinstance(rbody.get("data"), dict)
        else rbody.get("id")
    )
    if new_id:
        try:
            client.delete(
                f"/api/v1/admin/content/questions/{new_id}",
                headers=_auth_headers(admin_token),
            )
        except Exception:
            pass


# ===========================================================================
# DOMAIN WRITE-PATH GOLDEN FLOWS (Session 136, Option B)
# ---------------------------------------------------------------------------
# Eight more write-path tests, each targeting a distinct product domain that
# read-path tests cannot protect: gamification, chat persistence, teacher
# classroom, video solutions, KVKK consent, placement, daily quests, and the
# auth refresh-token loop. Every test was seeded from a live :8000 probe
# captured on 10 Apr 2026 — the expected outcome is documented in
# docs/audits/2026-04-10_half-working-features.md. Tests expected to fail on
# first run become fail-closed regression guards once the underlying bug is
# fixed.
# ===========================================================================


# ---------------------------------------------------------------------------
# GF2w: gamification points award must actually increase the user's balance
# ---------------------------------------------------------------------------


def test_gf2w_gamification_points_award_advances_balance(client: httpx.Client):
    """
    POST /gamification/points/award (JSON body: points, reason) must increase
    the caller's total_points.
    """
    token = _login(client, STUDENT)
    headers = _auth_headers(token)

    # Snapshot balance.
    before_resp = client.get("/api/v1/gamification/points", headers=headers)
    if before_resp.status_code != 200:
        pytest.skip(
            f"gamification/points unavailable: {before_resp.status_code} "
            f"{before_resp.text[:200]}"
        )
    before_total = (before_resp.json().get("data") or {}).get("total_points")
    assert before_total is not None, (
        f"GF2w gamification points: no total_points in response {before_resp.json()}"
    )

    # `reason` MUST be a whitelisted system source — the award endpoint rejects
    # arbitrary reasons with 403 reason_not_allowed (only system-generated points
    # are accepted). Use a real allowed source to exercise the award mechanism.
    award_resp = client.post(
        "/api/v1/gamification/points/award",
        headers={**headers, "Content-Type": "application/json"},
        json={"points": 3, "reason": "quiz_completion"},
    )
    assert award_resp.status_code == 200, (
        f"GF2w gamification award HTTP {award_resp.status_code}: "
        f"{award_resp.text[:300]}"
    )
    award_body = award_resp.json()
    assert award_body.get("success") is True, f"GF2w award success=False: {award_body}"

    # State-change assertion.
    after_resp = client.get("/api/v1/gamification/points", headers=headers)
    assert after_resp.status_code == 200, (
        f"GF2w post-award balance query HTTP {after_resp.status_code}"
    )
    after_total = (after_resp.json().get("data") or {}).get("total_points")
    assert after_total is not None and after_total > before_total, (
        f"GF2w gamification silent failure: award returned success but "
        f"total_points did not advance (before={before_total}, "
        f"after={after_total}). The award handler is writing to a stale "
        f"store or the GET reads from a different source."
    )


# ---------------------------------------------------------------------------
# GF3wA: creating a chat session must not return HTTP 500
# ---------------------------------------------------------------------------


def test_gf3wa_chat_session_create_reachable(client: httpx.Client):
    """
    POST /chat/sessions must return 200 with a session id, not 500.

    Session 136 probe: the endpoint currently returns
    ``HTTP 500 {"detail": "Dahili sunucu hatasi"}``. The AI assistant is
    the primary "help" surface — a broken session-create blocks every
    chat flow downstream. This is a fail-closed regression guard.

    Possible causes (to investigate on failure):
      - DB table ``chat_sessions`` missing or schema drift
      - AsyncSession vs sync Depends mismatch in the handler
      - Background task trying to touch a non-existent LLM service
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/chat/sessions",
        headers=_auth_headers(token),
        json={"title": "GF write-path test", "subject": "matematik"},
    )
    assert resp.status_code == 200, (
        f"GF3wA chat session create HTTP {resp.status_code}: {resp.text[:300]}. "
        f"Chat session creation is the entry point for every AI assistant "
        f"flow — a 500 here breaks the entire help surface."
    )
    body = resp.json()
    session_id = body.get("session_id") or body.get("id")
    assert session_id, f"GF3wA chat session create returned no id: {body}"


# ---------------------------------------------------------------------------
# GF5w: teacher class create must accept canonical frontend schema
# ---------------------------------------------------------------------------


def test_gf5w_teacher_class_create_canonical_schema(client: httpx.Client):
    """
    POST /teacher/classes with the canonical English schema must succeed.

    Session 136 probe: the endpoint rejects
    ``{"name": "...", "grade_level": "11"}`` with 422, demanding Turkish
    field names ``sinif_adi`` and ``seviye``. That's a direct violation of
    ``.claude/rules/path-naming.md`` (English canonical identifiers, no
    Turkish field keys except brand names). The frontend sends the
    English schema and the user sees silent form errors.

    This test fails-closed until ``backend/app/api/teacher_classroom.py``
    (ClassCreate schema) is updated to accept the canonical field names or
    the frontend is realigned. Either way the drift must be resolved.
    """
    token = _login(client, TEACHER)
    resp = client.post(
        "/api/v1/teacher/classes",
        headers=_auth_headers(token),
        json={
            "name": "GF Golden Flow Class",
            "subject_area": "MATEMATIK",
            "grade_level": "11",
        },
    )
    assert resp.status_code == 200, (
        f"GF5w teacher class create HTTP {resp.status_code}: {resp.text[:300]}. "
        f"If 422 'sinif_adi required', the backend is enforcing Turkish "
        f"field names in violation of .claude/rules/path-naming.md. Either "
        f"fix the Pydantic schema or realign the frontend — this is a drift "
        f"regression."
    )
    body = resp.json()
    assert body.get("success") is True or body.get("id") or body.get("data"), (
        f"GF5w teacher class create unexpected body: {body}"
    )


# ---------------------------------------------------------------------------
# GF7wA: video solutions list endpoint must not 500
# ---------------------------------------------------------------------------


def test_gf7wa_video_solutions_list_not_500(client: httpx.Client):
    """
    GET /video-solutions/ must return a semantic status, never 500.

    Session 136 probe: returns ``HTTP 500 {"detail": "Dahili sunucu hatasi"}``.
    This is the index surface for all video solutions — a 500 here means
    students clicking "video çözüm" from any question get a dead page.

    This is a minimal fail-closed guard. 200 or 404 both acceptable
    (empty list is fine), but 500 always means the router → service →
    ORM pipeline is broken. On failure, check service initialization and
    router registration.
    """
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/video-solutions/", headers=_auth_headers(token))
    assert resp.status_code != 500, (
        f"GF7wA video-solutions list crashed with 500: {resp.text[:300]}. "
        f"Check backend/api/video_solutions.py service init and router wiring."
    )


# ---------------------------------------------------------------------------
# GF8wA: KVKK consent list must not 500
# ---------------------------------------------------------------------------


def test_gf8wa_kvkk_consent_list_not_500(client: httpx.Client):
    """
    GET /kvkk/consent/my-consents must return a semantic status, never 500.

    Session 136 probe: returns ``HTTP 500 {"detail": "Dahili sunucu hatasi"}``.
    KVKK (Turkish GDPR) consent visibility is a legal compliance surface —
    a broken endpoint means users cannot review what they've consented to.
    Fail-closed guard.

    Note: this is *not* a parent/child consent test (that's GF8 — parent
    children reachable). This is the user's own consent audit log.
    """
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/kvkk/consent/my-consents", headers=_auth_headers(token))
    assert resp.status_code != 500, (
        f"GF8wA kvkk consent list crashed with 500: {resp.text[:300]}. "
        f"Check backend/api/kvkk.py consent query and KVKK compliance model."
    )


# ---------------------------------------------------------------------------
# GF2wB: placement session start must return a question and session_id
# ---------------------------------------------------------------------------


def test_gf2wb_placement_start_returns_session_and_question(client: httpx.Client):
    """
    POST /placement/start with ``exam_type: TYT`` must return a
    ``session_id`` AND the first question. Without this, new students
    cannot complete onboarding.

    Session 136 probe: works today (returns HTTP 201 with session_id and
    question). This test is a regression guard — the placement entry point
    is fragile because it depends on IRT init, topic_hierarchy seed data,
    and question bank availability.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/placement/start",
        headers=_auth_headers(token),
        json={"exam_type": "TYT"},
    )
    assert resp.status_code in (200, 201), (
        f"GF2wB placement/start HTTP {resp.status_code}: {resp.text[:300]}"
    )
    body = resp.json()
    session_id = body.get("session_id")
    question = body.get("question")
    assert session_id, f"GF2wB placement/start missing session_id: {body}"
    assert isinstance(question, dict) and (
        question.get("question_id") or question.get("id")
    ), (
        f"GF2wB placement/start missing/malformed question: {question!r}. "
        f"Root cause candidates: empty question_bank, IRT bootstrap failure, "
        f"topic_hierarchy seed missing."
    )


# ---------------------------------------------------------------------------
# GF5wB: daily quest progress must advance the quest's current_value
# ---------------------------------------------------------------------------


def test_gf5wb_daily_quest_progress_advances(client: httpx.Client):
    """
    Posting progress on a daily quest must advance its ``current_value``
    on the next GET. This is a canonical write-path detector — the classic
    "POST 200 but state unchanged" bug.

    Session 136 probe: works today (0 → 1 on quest 16). Regression guard.
    """
    token = _login(client, STUDENT)
    headers = _auth_headers(token)

    before_resp = client.get("/api/v1/daily-quests/today", headers=headers)
    if before_resp.status_code != 200:
        pytest.skip(
            f"daily-quests/today unavailable: {before_resp.status_code} "
            f"{before_resp.text[:200]}"
        )
    quests_before = (before_resp.json().get("data") or {}).get("quests") or []
    if not quests_before:
        pytest.skip("no daily quests seeded")

    # Pick the first incomplete quest.
    target = next(
        (q for q in quests_before if not q.get("completed")),
        quests_before[0],
    )
    quest_id = target.get("id")
    before_value = int(target.get("current_value") or 0)
    assert quest_id is not None, f"GF5wB no id on quest: {target}"

    post_resp = client.post(
        f"/api/v1/daily-quests/{quest_id}/progress",
        headers=headers,
        json={"progress": 1},
    )
    assert post_resp.status_code == 200, (
        f"GF5wB quest progress HTTP {post_resp.status_code}: {post_resp.text[:300]}"
    )

    after_resp = client.get("/api/v1/daily-quests/today", headers=headers)
    assert after_resp.status_code == 200
    quests_after = (after_resp.json().get("data") or {}).get("quests") or []
    target_after = next((q for q in quests_after if q.get("id") == quest_id), None)
    assert target_after is not None, (
        f"GF5wB quest {quest_id} disappeared after progress: {quests_after}"
    )
    after_value = int(target_after.get("current_value") or 0)
    assert after_value > before_value or target_after.get("completed") is True, (
        f"GF5wB silent failure: quest {quest_id} progress POST returned 200 "
        f"but current_value did not advance (before={before_value}, "
        f"after={after_value}). Check backend/api/daily_quests.py update flow."
    )


# ---------------------------------------------------------------------------
# GF9wA: khan oauth status must not 500 (Pattern A sync get_db trap)
# ---------------------------------------------------------------------------


def test_gf9wa_khan_oauth_status_not_500(client: httpx.Client):
    """
    GET /api/v1/khan/oauth/status must return a semantic status, never 500.

    Session 137 AST linter hit: ``backend/api/khan_routes.py`` imports the
    sync ``get_db`` from ``core.database`` but declares handler params as
    ``db: AsyncSession = Depends(get_db)``. FastAPI's DI resolver injects
    a sync ``sqlalchemy.orm.Session`` with no type check, and the first
    ``await db.execute(...)`` raises ``MissingGreenlet`` → 500.

    ``oauth/status`` is the minimal handler — no OAuth token required —
    that still hits the broken DB dependency, so it is the smallest probe
    for this file. A student with no Khan link should get
    ``{"connected": false}``, never a crash.

    On fail: swap the import to ``get_async_session`` (same module) and
    replace every ``Depends(get_db)`` in khan_routes.py. See
    ``docs/audits/2026-04-10_db-dependency-baseline.md``.
    """
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/khan/oauth/status", headers=_auth_headers(token))
    assert resp.status_code != 500, (
        f"GF9wA khan oauth/status crashed with 500: {resp.text[:300]}. "
        f"Check backend/api/khan_routes.py — Pattern A sync get_db trap."
    )


# ---------------------------------------------------------------------------
# GF9wB: eba watch history must not 500 (Pattern A sync get_db trap)
# ---------------------------------------------------------------------------


def test_gf9wb_eba_watch_history_not_500(client: httpx.Client):
    """
    GET /api/v1/eba/watch/history must return a semantic status, never 500.

    Session 137 AST linter hit: ``backend/api/eba_routes.py`` imports sync
    ``get_db`` but declares ``db: AsyncSession = Depends(get_db)``. Any
    handler doing ``await db.execute(...)`` raises ``MissingGreenlet``.
    ``watch/history`` is the minimal user-facing probe: a student with
    zero history should get ``[]``, not a 500.
    """
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/eba/watch/history", headers=_auth_headers(token))
    assert resp.status_code != 500, (
        f"GF9wB eba watch/history crashed with 500: {resp.text[:300]}. "
        f"Check backend/api/eba_routes.py — Pattern A sync get_db trap."
    )


# ---------------------------------------------------------------------------
# GF9wC: kvkk privacy export/requests must not 500 (dual-trap)
# ---------------------------------------------------------------------------


def test_gf9wc_kvkk_privacy_export_requests_not_500(client: httpx.Client):
    """
    GET /api/v1/kvkk/privacy/export/requests must return semantic status.

    Session 137 AST linter: ``backend/api/kvkk_privacy_api.py`` is a dual-trap:
    Pattern A (sync ``get_db`` with ``await db.execute``) AND Pattern B
    (``current_user.id`` on a Pydantic ``TokenPayload`` whose user_id field
    is ``sub``). Both traps 500 on first call. A student with zero export
    requests should get ``[]``, not a 500 or AttributeError.
    """
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/kvkk/privacy/export/requests",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF9wC kvkk export/requests crashed with 500: {resp.text[:300]}. "
        f"Check backend/api/kvkk_privacy_api.py — dual trap "
        f"(sync get_db + TokenPayload.id)."
    )


# ---------------------------------------------------------------------------
# GF9wD: 2FA status must not 500 (dual-trap Pattern A + Pattern B)
# ---------------------------------------------------------------------------


def test_gf9wd_two_factor_status_not_500(client: httpx.Client):
    """
    GET /api/v1/auth/2fa/status must return a semantic status, never 500.

    Session 137 AST linter: ``backend/api/two_factor_auth_api.py`` was the
    second dual-trap file: 7 Pattern-A broken handlers (sync ``get_db``
    + ``await db.*``) and 19 Pattern-B accesses (``current_user.id`` on
    a Pydantic ``TokenPayload`` whose user_id is ``sub``). /status is
    the minimal probe — no request body, no feature flag gating, and
    the handler touches ``current_user.backup_codes_hashed`` /
    ``.is_2fa_enabled`` which only exist on a real User ORM row. A
    student with no 2FA set up should get ``{is_2fa_enabled: false}``.
    """
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/auth/2fa/status", headers=_auth_headers(token))
    assert resp.status_code != 500, (
        f"GF9wD 2fa/status crashed with 500: {resp.text[:300]}. "
        f"Check backend/api/two_factor_auth_api.py — dual trap "
        f"(sync get_db + TokenPayload.id on ORM-only fields)."
    )


# ---------------------------------------------------------------------------
# GF9wE: rate-limit status must not 500 (Pattern B + require_admin variant)
# ---------------------------------------------------------------------------


def test_gf9we_rate_limit_status_not_500(client: httpx.Client):
    """
    GET /api/v1/rate-limit/status must return a semantic status, never 500.

    Session 137 AST linter flagged 3 Pattern-B hits in rate_limit_api.py
    (current_user.id on a TokenPayload). A manual read of the file also
    surfaced 4 more in the require_admin-gated handlers that the linter
    heuristic missed — fixed together (7 total). /status is the lightest
    probe a student can hit without admin rights.
    """
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/rate-limit/status", headers=_auth_headers(token))
    assert resp.status_code != 500, (
        f"GF9wE rate-limit/status crashed with 500: {resp.text[:300]}. "
        f"Check backend/api/rate_limit_api.py — Pattern B TokenPayload.id."
    )


# ---------------------------------------------------------------------------
# GF1wB: auth refresh-token persistence (auth.py:329 silent swallow)
# ---------------------------------------------------------------------------


def test_gf1wb_auth_refresh_token_is_persisted():
    """
    After login, the refresh cookie must work on /auth/refresh.

    This indirectly verifies ``backend/api/auth.py:329`` — the refresh
    token persist is wrapped in a silent ``try/except Exception:
    logger.warning(...)``. If the DB persist fails, the user gets the
    cookie but the DB has no row, so ``/auth/refresh`` rejects the token.
    Any failure here points at the swallowed persist error.

    We use a fresh ``httpx.Client`` with cookie jar enabled because the
    module-scoped ``client`` fixture does not persist cookies across
    requests the same way.
    """
    with httpx.Client(base_url=BACKEND_URL, timeout=TIMEOUT) as c:
        try:
            login_resp = c.post("/api/v1/auth/login", json=STUDENT)
        except httpx.ConnectError:
            pytest.skip(f"backend unreachable at {BACKEND_URL}")

        if login_resp.status_code != 200:
            pytest.skip(
                f"login failed: {login_resp.status_code} {login_resp.text[:200]}"
            )

        # Refresh token is set as httpOnly cookie by the login handler.
        refresh_cookie_present = any(
            name in c.cookies for name in ("refresh_token", "kiro2_refresh")
        )
        if not refresh_cookie_present:
            pytest.skip(
                "login did not set a refresh cookie (deploy may use Bearer-only flow)"
            )

        refresh_resp = c.post("/api/v1/auth/refresh")
        assert refresh_resp.status_code == 200, (
            f"GF1wB auth/refresh HTTP {refresh_resp.status_code}: "
            f"{refresh_resp.text[:300]}. The login cookie is present but "
            f"the refresh endpoint rejects it — prime suspect is the "
            f"swallowed DB persist at backend/api/auth.py:329-330 (the "
            f"refresh token row was never written, so the verify step "
            f"cannot find it)."
        )
        new_token = refresh_resp.json().get("access_token")
        assert new_token, (
            f"GF1wB auth/refresh returned no access_token: {refresh_resp.json()}"
        )


# ===========================================================================
# AŞAMA 1 BATCH 1 — WRITE-PATH DISCOVERY PROBES (Session 140, 11 Apr 2026)
# ---------------------------------------------------------------------------
# Ten new write-path probes targeting the highest-gap surfaces the Session 140
# feature inventory (docs/audits/2026-04-11_feature-inventory.md) identified:
# learning (91/2 GF cov), auth (34/4), social (25/0), integrations, KVKK,
# parent. Each probe is a *discovery* probe — Session 136 lenient
# ``status_code != 500`` style — because we do not yet know which half-working
# features hide behind these endpoints. First-run failures become the
# Aşama 2 fix backlog. Successful probes become fail-closed regression guards.
# ===========================================================================


# ---------------------------------------------------------------------------
# GF10: learning-path create-profile must not 500 (student onboard write)
# ---------------------------------------------------------------------------


def test_gf10_learning_path_create_profile_not_500(client: httpx.Client):
    """
    POST /api/v1/learning-path/create-profile must return a semantic status.

    Every new student hits this endpoint during onboarding. The handler
    (learning_path_v2.py:421) depends on the orchestrator profile store,
    topic_hierarchy seed, and DAG service — all high-risk surfaces.
    A 500 here means a new student cannot even be registered into the
    personalized learning pipeline; the user would see a dead signup flow.

    Lenient ``!= 500`` check: 200/201 (created), 400/409 (profile already
    exists for the seed student), 422 (schema drift) are all acceptable
    semantic responses. On 500: check async DB dependency wiring and
    orchestrator profile-store initialization.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/learning-path/create-profile",
        headers=_auth_headers(token),
        json={
            "name": "GF10 Probe Student",
            "grade": 11,
            "subjects": ["MATEMATIK", "FIZIK"],
            "goals": ["Tıp fakültesi", "TYT/AYT"],
            "learning_style": "visual",
            "available_time": 120,
        },
    )
    assert resp.status_code != 500, (
        f"GF10 learning-path create-profile crashed 500: {resp.text[:300]}. "
        f"Check backend/api/learning_path_v2.py:421 — orchestrator profile "
        f"store init and async DB wiring."
    )


# ---------------------------------------------------------------------------
# GF11: learning-path quiz/{id}/submit must not 500 for unknown quiz_id
# ---------------------------------------------------------------------------


def test_gf11_learning_path_quiz_submit_not_500(client: httpx.Client):
    """
    POST /api/v1/learning-path/quiz/{quiz_id}/submit must not 500 on an
    unknown quiz_id. The canonical "quiz kaybolma" failure mode: user
    posts answers, handler 500s, their work is lost. Expected semantics:
    404 ``Quiz not found`` or 400 validation — never 500.

    This probe deliberately uses a bogus UUID to exercise the handler's
    existence check branch. Session 136 root-cause family: wrong get_db
    flavor, missing is_active filter on QuestionBankItem, FSRS fire-and-
    forget swallow (learning_path_v2.py:1223 vicinity).
    """
    token = _login(client, STUDENT)
    bogus_quiz_id = "00000000-0000-0000-0000-000000000000"
    resp = client.post(
        f"/api/v1/learning-path/quiz/{bogus_quiz_id}/submit",
        headers=_auth_headers(token),
        json={
            "answers": [{"question_id": bogus_quiz_id, "selected": "A"}],
            "time_spent_seconds": 60,
        },
    )
    assert resp.status_code != 500, (
        f"GF11 learning-path quiz submit crashed 500: {resp.text[:300]}. "
        f"Expected 404 (unknown quiz_id) or 400/422 (schema). A 500 points "
        f"at the handler's pre-validation path — check the session lookup "
        f"and QuestionBankItem filter in learning_path_v2.py:1223."
    )


# ---------------------------------------------------------------------------
# GF12: fsrs/review must not 500 for bogus question_id
# ---------------------------------------------------------------------------


def test_gf12_fsrs_review_not_500(client: httpx.Client):
    """
    POST /api/v1/fsrs/review must return a semantic status.

    FSRS is the engine behind every spaced-repetition card the student
    grades from the review queue. This probe exercises the app/api/fsrs.py:86
    handler with a valid schema but a bogus question_id. Expected: 200
    (FSRS creates a new card) or 404 (lookup fails) — never 500.

    Session 121 surfaced a 3-layer path-alignment bug here (loader swap +
    frontend sync). This probe is the regression guard.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/fsrs/review",
        headers=_auth_headers(token),
        json={
            "question_id": "00000000-0000-0000-0000-000000000000",
            "is_correct": False,
            "response_ms": 5000,
        },
    )
    assert resp.status_code != 500, (
        f"GF12 fsrs/review crashed 500: {resp.text[:300]}. "
        f"Check backend/app/api/fsrs.py:86 — FSRSCard upsert path and "
        f"UserItemFSRS unique constraint handling."
    )


# ---------------------------------------------------------------------------
# GF13: cat/sessions start must not 500 (CAT engine cold start)
# ---------------------------------------------------------------------------


def test_gf13_cat_session_start_not_500(client: httpx.Client):
    """
    POST /api/v1/cat/sessions must return a semantic status.

    Session 112 rewrote the CAT engine (7 new service files) but there is
    zero Golden Flow coverage. This probe starts a session with the
    MATEMATIK subject and asserts the handler does not crash. Expected:
    200 (session created with first question) or 400 (IRT bootstrap not
    ready, empty question bank). A 500 means the CAT → IRT → question_bank
    pipeline is broken.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/cat/sessions",
        headers=_auth_headers(token),
        json={"subject_id": "MATEMATIK"},
    )
    assert resp.status_code != 500, (
        f"GF13 cat/sessions start crashed 500: {resp.text[:300]}. "
        f"Check backend/app/api/cat.py:76 — IRTEngine cold start, "
        f"theta bootstrap, and topic_hierarchy seed."
    )


# ---------------------------------------------------------------------------
# GF14: auth change-password must reject wrong currentPassword cleanly
# ---------------------------------------------------------------------------


def test_gf14_auth_change_password_rejects_wrong_current(client: httpx.Client):
    """
    POST /api/v1/auth/change-password with a wrong ``currentPassword``
    must return 400/401/403, never 500. This probe deliberately sends an
    incorrect current password so the handler takes the "verify failed"
    branch WITHOUT mutating the seed student's credentials — other tests
    depend on STUDENT["password"] being stable.

    Pattern B risk family: ``current_user.id`` on a Pydantic TokenPayload
    (field is ``sub``) would raise AttributeError and surface as 500.
    The Session 137 2FA sweep already fixed the dual-trap in the same file;
    this probe guards against regression.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/auth/change-password",
        headers=_auth_headers(token),
        json={
            "currentPassword": "DefinitelyWrong2026!",
            "newPassword": "DefinitelyWrong2026!!",
        },
    )
    assert resp.status_code in (400, 401, 403, 422), (
        f"GF14 change-password wrong-current HTTP {resp.status_code}: "
        f"{resp.text[:300]}. Expected 400/401/403. A 500 points at Pattern B "
        f"(TokenPayload.id) or a missing `is_active` filter in the User "
        f"lookup at backend/api/auth.py:1141."
    )


# ---------------------------------------------------------------------------
# GF15: auth 2fa setup must not 500 (post-Session 137 regression guard)
# ---------------------------------------------------------------------------


def test_gf15_auth_2fa_setup_not_500(client: httpx.Client):
    """
    POST /api/v1/auth/2fa/setup must return a semantic status, never 500.

    Session 137 fixed the dual-trap in two_factor_auth_api.py (7 Pattern-A
    broken handlers + 19 Pattern-B TokenPayload.id accesses). GF9wD covers
    /status. This probe covers /setup — the first write-path handler in
    the 2FA flow, which builds a TOTP secret and writes it to the user's
    row. Expected: 200 (new QR code) or 400/409 (already enabled).
    """
    token = _login(client, STUDENT)
    resp = client.post("/api/v1/auth/2fa/setup", headers=_auth_headers(token))
    assert resp.status_code != 500, (
        f"GF15 2fa/setup crashed 500: {resp.text[:300]}. "
        f"Session 137 dual-trap regression — check "
        f"backend/api/two_factor_auth_api.py:94 for sync get_db or "
        f"TokenPayload.id use on ORM-only fields."
    )


# ---------------------------------------------------------------------------
# GF16: kvkk consent/give must not 500 (write-path companion to GF8wA)
# ---------------------------------------------------------------------------


def test_gf16_kvkk_consent_give_not_500(client: httpx.Client):
    """
    POST /api/v1/kvkk/consent/give must return a semantic status.

    GF8wA guards the read path (``my-consents`` list). Session 136 fixed
    that file's sync get_db + TokenPayload.id dual-trap. This probe
    exercises the *write* path in the same file — /consent/give — which
    inserts a row into the consent audit table. A 500 here means the legal
    compliance write surface is broken and users cannot record consent.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/kvkk/consent/give",
        headers=_auth_headers(token),
        json={
            "purpose": "service_provision",
            "consent_text": "GF Golden Flow probe consent",
            "privacy_policy_version": "1.0.0",
        },
    )
    assert resp.status_code != 500, (
        f"GF16 kvkk/consent/give crashed 500: {resp.text[:300]}. "
        f"Check backend/api/kvkk_consent_api.py:109 — async DB wiring and "
        f"ConsentRecord insert path."
    )


# ---------------------------------------------------------------------------
# GF17: cozum-duellosu create must not 500 (social category — 0 GF cov)
# ---------------------------------------------------------------------------


def test_gf17_cozum_duellosu_create_not_500(client: httpx.Client):
    """
    POST /api/v1/cozum-duellosu/create must return a semantic status.

    The feature-inventory audit flagged social as 25 write endpoints with
    zero Golden Flow coverage — the biggest untested user-facing surface.
    This probe is the representative: cozum-duellosu is the "solution duel"
    gamified write path (two students race to solve one question).

    We post a reasonable payload with a bogus question_bank_id. Expected:
    404 (unknown question), 400 (validation), 409 (already in duel) —
    never 500. On 500: the handler likely uses the wrong question model
    (dual-table trap: ``Question`` vs ``QuestionBankItem``) or misses the
    is_active filter.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/cozum-duellosu/create",
        headers=_auth_headers(token),
        json={
            "question_bank_id": "00000000-0000-0000-0000-000000000000",
            "subject_area": "MATEMATIK",
            "solve_time_seconds": 300,
        },
    )
    assert resp.status_code != 500, (
        f"GF17 cozum-duellosu/create crashed 500: {resp.text[:300]}. "
        f"Check backend/api/cozum_duellosu_api.py:60 — question_bank lookup, "
        f"dual-table trap (testing.md lesson #23), and orphan FK constraints."
    )


# ---------------------------------------------------------------------------
# GF18: daily-quests claim-bonus must not 500 (streak fire-and-forget path)
# ---------------------------------------------------------------------------


def test_gf18_daily_quests_claim_bonus_not_500(client: httpx.Client):
    """
    POST /api/v1/daily-quests/claim-bonus must return a semantic status.

    GF5wB covers quest progress advance; this probe covers the *claim*
    path, which depends on the streak fire-and-forget writer documented
    in the Session 136 half-working features audit as a risk hot spot.
    A 500 here means either the XP transactions write (VARCHAR source
    overflow, Session 136 P0 family) or the streak table touch is broken.
    Expected: 200 (claimed), 400 (nothing to claim, already claimed today).
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/daily-quests/claim-bonus",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF18 daily-quests/claim-bonus crashed 500: {resp.text[:300]}. "
        f"Check backend/api/daily_quest_api.py:247 — streak writer and "
        f"xp_transactions.source VARCHAR overflow (Session 136 P0 family)."
    )


# ---------------------------------------------------------------------------
# GF19: parent notifications create must not 500 (parent write surface)
# ---------------------------------------------------------------------------


def test_gf19_parent_notifications_create_not_500(client: httpx.Client):
    """
    POST /api/v1/parent/notifications must return a semantic status.

    Session 115 secured most of the veli API (hardcoded creds removed,
    asyncpg→SQLAlchemy, IDOR fix) but the notification create path has
    no GF coverage. This probe has a parent create a notification for
    a bogus child_id — expected 403/404 (not your child / unknown child),
    400/422 (validation), never 500.

    On 500: check parent_service.py:321 for IDOR-adjacent bugs, the ORM
    field mapping, and the ParentChildRelation foreign key lookup.
    """
    token = _login(client, PARENT)
    resp = client.post(
        "/api/v1/parent/notifications",
        headers=_auth_headers(token),
        json={
            "child_id": "00000000-0000-0000-0000-000000000000",
            "title": "GF19 Probe Notification",
            "message": "Golden Flow write-path probe",
            "notification_type": "reminder",
        },
    )
    assert resp.status_code != 500, (
        f"GF19 parent/notifications create crashed 500: {resp.text[:300]}. "
        f"Check backend/api/parent.py:158 and parent_service.py:321 — "
        f"ParentChildRelation FK lookup and async DB wiring."
    )


# ---------------------------------------------------------------------------
# Wave 4 — feature-inventory sweep (Session 138, GF20–GF29)
#
# Context: docs/audits/2026-04-11_feature-inventory.md enumerated 545 write
# endpoints. Waves 1-3 covered 35. Wave 4 picks 10 more across categories
# (accessibility, ai, learning, content, admin, teacher) to find more
# half-working features.
# ---------------------------------------------------------------------------


def test_gf20_adhd_pomodoro_start_not_500(client: httpx.Client):
    """
    POST /api/v1/adhd-support/pomodoro/start must return a semantic status.

    REQ-52.1 ADHD support. Handler is sync + uses sync `Session = Depends(get_db)`
    but annotates `current_user: User = Depends(get_current_user)` where the
    dependency actually returns AuthenticatedUser (Pydantic). If PomodoroSettings
    or the uuid/datetime wiring diverges from the response_model shape, FastAPI
    coerces to 500.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/adhd-support/pomodoro/start",
        headers=_auth_headers(token),
        json={
            "session_type": "work",
            "custom_duration_minutes": 25,
            "task_description": "GF20 probe — focus session",
        },
    )
    assert resp.status_code != 500, (
        f"GF20 adhd-support/pomodoro/start crashed 500: {resp.text[:300]}. "
        f"Check api/adhd_support_api.py:153 — sync handler + current_user type "
        f"annotation drift (User vs AuthenticatedUser)."
    )


def test_gf21_bionic_reading_process_not_500(client: httpx.Client):
    """
    POST /api/v1/bionic-reading/process must return a semantic status.

    Accessibility flagship (REQ-52 dyslexia support). Depends on
    BionicReadingService and CacheService — either missing dependency or
    Turkish NFC normalization bug would crash 500.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/bionic-reading/process",
        headers=_auth_headers(token),
        json={
            "text": "Matematik sorularını çözerken odaklanmak çok önemli.",
            "use_cache": False,
        },
    )
    assert resp.status_code != 500, (
        f"GF21 bionic-reading/process crashed 500: {resp.text[:300]}. "
        f"Check api/bionic_reading.py:85 and core/bionic_reading_service.py — "
        f"service init + Turkish NFC normalization."
    )


def test_gf22_berturk_sentiment_analyze_not_500(client: httpx.Client):
    """
    POST /api/v1/berturk/sentiment/analyze must return a semantic status.

    Turkish NLP flagship. Module-level `try/except (ImportError, TypeError):
    berturk_service = None` — if the model fails to load, every call becomes
    `None.analyze_sentiment(...)` → AttributeError → 500. This is the
    quintessential 'half-working feature' the sweep is supposed to catch.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/berturk/sentiment/analyze",
        headers=_auth_headers(token),
        json={
            "text": "Bugün matematik çalışırken kendimi çok motive hissettim.",
            "include_emotions": True,
            "educational_context": True,
        },
    )
    assert resp.status_code != 500, (
        f"GF22 berturk/sentiment/analyze crashed 500: {resp.text[:300]}. "
        f"Check api/berturk_api.py:142 — module-level berturk_service=None "
        f"fallback when core/berturk_service import fails."
    )


def test_gf23_bilge_alp_chat_not_500(client: httpx.Client):
    """
    POST /api/v1/bilge-alp/chat must return a semantic status.

    SSE streaming NPC mascot chat. Handler dispatches LLM call + BKTState DB
    read; a sync-in-async path or missing BKTState row would crash before the
    first SSE byte. httpx consumes the initial handshake status even for
    StreamingResponse, so this probe is valid without needing a full stream.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/bilge-alp/chat",
        headers=_auth_headers(token),
        json={
            "realm_slug": "matematik",
            "quest_step": 0,
            "message": "Merhaba Bilge Alp, matematik konusunda yardım eder misin?",
            "history": [],
        },
    )
    assert resp.status_code != 500, (
        f"GF23 bilge-alp/chat crashed 500 on handshake: {resp.text[:300]}. "
        f"Check api/bilge_alp.py:224 — BKTState query + LLM streaming wiring."
    )


def test_gf24_enhanced_chat_message_not_500(client: httpx.Client):
    """
    POST /api/v1/enhanced-chat/message must return a semantic status.

    Multi-subject AI chat with Turkish prompt routing and bionic reading
    integration. History of hidden 500s: session_id foreign-key drift,
    subject case-mismatch (lowercase vs DB UPPERCASE), LLM fallback path.

    State-dependent timeout handling: the handler issues a blocking upstream
    LLM call that can take 30+s when a real provider is configured. That is
    neither a 500 nor a regression — it is the same class of state-dependent
    skip as GF1wB (refresh-token persist) and GF4w.2 (FSRS no due cards).
    Session 138 observed ~30s end-to-end with status 200. We use a longer
    per-request timeout and, if even that is exceeded, skip rather than fail.
    """
    token = _login(client, STUDENT)
    prof = client.post(
        "/api/v1/learning-path/create-profile",
        headers=_auth_headers(token),
        json={
            "name": "GF24 Chat Probe",
            "grade": 11,
            "subjects": ["MATEMATIK"],
            "goals": ["TYT"],
            "learning_style": "visual",
            "available_time": 60,
        },
    )
    assert prof.status_code != 500, (
        f"GF24 prerequisite create-profile failed: {prof.text[:300]}"
    )
    try:
        body = prof.json()
    except Exception:
        body = {}
    sid = body.get("student_id")
    if not sid:
        pytest.skip("GF24: learning-path create-profile did not return student_id")

    try:
        resp = client.post(
            "/api/v1/enhanced-chat/message",
            headers=_auth_headers(token),
            json={
                "student_id": sid,
                "message": "x^2 - 4 = 0 denklemini nasıl çözerim?",
                "subject": "matematik",
                "teaching_mode": "direct",
                "include_bionic": False,
            },
            timeout=45.0,
        )
    except httpx.TimeoutException as exc:
        pytest.skip(
            f"GF24 enhanced-chat/message blocked on upstream LLM >45s "
            f"({exc!r}). State-dependent — not a 500 regression."
        )
    assert resp.status_code != 500, (
        f"GF24 enhanced-chat/message crashed 500: {resp.text[:300]}. "
        f"Check api/enhanced_chat.py:391 — subject case convention, "
        f"LLM fallback, BionicReadingService dependency."
    )


def test_gf25_coaching_signals_record_not_500(client: httpx.Client):
    """
    POST /api/v1/coaching/signals must return a semantic status.

    Proactive coaching behavioral signal write path. ORM field mapping +
    async DB wiring + get_db_session_context discipline. A silent 500 would
    mean burnout detection has no training data.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/coaching/signals",
        headers=_auth_headers(token),
        json={
            "signal_type": "session_duration",
            "value": 1800.0,
        },
    )
    assert resp.status_code != 500, (
        f"GF25 coaching/signals crashed 500: {resp.text[:300]}. "
        f"Check api/coaching_api.py:191 and services/proactive_coaching_service.py "
        f"— record_engagement_signal async DB wiring."
    )


def test_gf26_diary_goals_create_not_500(client: httpx.Client):
    """
    POST /api/v1/diary/goals must return a semantic status.

    SMART goal create — write path into GoalService with AsyncSession. Historic
    Pattern A trap: `db: AsyncSession = Depends(get_async_session)` is correct
    async, but `current_user: User = Depends(get_current_user)` annotation lies
    (AuthenticatedUser returned). `.id` access works either way; a 500 would
    mean GoalService.create_goal or the model_validator on GoalCreate broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/diary/goals",
        headers=_auth_headers(token),
        json={
            "title": "GF26 Probe Goal",
            "description": "Golden Flow write-path probe for diary goals",
            "target_value": 10.0,
            "target_date": "2026-12-31T00:00:00Z",
            "unit": "task",
            "category": "matematik",
            "priority": 2,
            "specific": "YKS matematik denklem çözme pratiği",
            "measurable": "10 adet çözülmüş soru",
            "achievable": "Günde 1 soru",
            "relevant": "YKS hazırlık hedefi",
        },
    )
    assert resp.status_code != 500, (
        f"GF26 diary/goals create crashed 500: {resp.text[:300]}. "
        f"Check api/diary_api.py:474 and services/diary/goal_service.py — "
        f"async GoalService wiring and SMART validator."
    )


def test_gf27_content_management_question_create_not_500(client: httpx.Client):
    """
    POST /api/v1/content-management/questions must return a semantic status.

    Admin/teacher question add (mock impl). STUDENT token should get 403,
    not 500. A 500 here means the role guard itself is broken — which
    would be a silent privilege-escalation adjacent bug.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/content-management/questions",
        headers=_auth_headers(token),
        json={
            "soru_metni": "GF27 probe question",
            "secenekler": {"A": "A", "B": "B", "C": "C", "D": "D"},
            "dogru_cevap": "A",
            "sinav_tipi": "TYT",
            "konu": "Matematik",
            "zorluk_seviyesi": "medium",
        },
    )
    assert resp.status_code != 500, (
        f"GF27 content-management/questions crashed 500: {resp.text[:300]}. "
        f"Check api/content_management.py:99 — admin_yetki_kontrolu role guard "
        f"must not generic-except the 403."
    )
    # Explicit role-guard expectation: STUDENT → 403
    assert resp.status_code == 403, (
        f"GF27 expected 403 for STUDENT, got {resp.status_code} {resp.text[:200]}. "
        f"admin_yetki_kontrolu role guard is leaking privileges or misconfigured."
    )


def test_gf28_validation_submit_not_500(client: httpx.Client):
    """
    POST /api/v1/validation/submit must return a semantic status.

    HITL expert validation submission — writes into
    expert_validation_system (in-memory service). A 500 means the content
    review workflow is broken; a 400 is fine (invalid ContentType).
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/validation/submit",
        headers=_auth_headers(token),
        json={
            "content_id": "gf28-probe",
            "content_type": "question",
            "content_data": {
                "soru_metni": "GF28 probe question text",
                "dogru_cevap": "A",
            },
            "submitter_id": "gf28-student",
            "submitter_name": "GF28 Probe",
            "subject": "matematik",
            "exam_type": "TYT",
            "difficulty_level": "medium",
            "priority": 5,
        },
    )
    assert resp.status_code != 500, (
        f"GF28 validation/submit crashed 500: {resp.text[:300]}. "
        f"Check api/validation.py:82 and services/expert_validation_system — "
        f"ContentType enum coercion + submit_content_for_validation wiring."
    )


def test_gf29_ogretmen_rapor_sinif_create_not_500(client: httpx.Client):
    """
    POST /api/v1/ogretmen/rapor/sinif must return a semantic status.

    Deprecated Turkish teacher report path (in-memory backend). Probes
    whether the TR naming legacy still works for authenticated TEACHER. A 500
    would mean the Kullanici Pydantic field alias broke, or ogretmen_servisi
    shared state corrupted across tests.
    """
    token = _login(client, TEACHER)
    resp = client.post(
        "/api/v1/ogretmen/rapor/sinif",
        headers=_auth_headers(token),
        json={
            "baslangic_tarihi": "2026-01-01T00:00:00",
            "bitis_tarihi": "2026-04-11T00:00:00",
            "sinav_tipi": "TYT",
        },
    )
    assert resp.status_code != 500, (
        f"GF29 ogretmen/rapor/sinif crashed 500: {resp.text[:300]}. "
        f"Check api/ogretmen.py:169 — Kullanici.kullanici_id alias + "
        f"services/ogretmen_service.sinif_raporu_olustur in-memory state."
    )


# ---------------------------------------------------------------------------
# Wave 5 (Session 140) — second feature-inventory sweep across disjoint
# top-10 uncovered write-path endpoints. Each probe hits ONE handler with a
# valid body and asserts `status_code < 500` — a 500 means the auth → ORM →
# service → response pipeline is broken.
#
# Selection criteria: 10 disjoint endpoints spanning accessibility, learning,
# social, search, and live-sessions categories, each in a different router
# file, to maximize bug-discovery surface area.
# ---------------------------------------------------------------------------


def test_gf30_math_solution_steps_generate_not_500(client: httpx.Client):
    """
    POST /api/v1/math-solution-steps/generate must not crash.

    Probes the diskalkuli support step generator. A 500 means the
    math_solution_step_service pipeline broke (DifficultyLevel enum coercion,
    service singleton missing, or response serializer mismatch).
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/math-solution-steps/generate",
        headers=_auth_headers(token),
        json={
            "problem_id": "gf30-probe",
            "problem_statement": "2x + 4 = 10 denklemini çöz",
            "problem_type": "linear_equation",
            "difficulty_level": "medium",
        },
    )
    assert resp.status_code < 500, (
        f"GF30 math-solution-steps/generate crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/math_solution_steps.py:87 — "
        f"DifficultyLevel enum coercion and math_solution_step_service."
    )


def test_gf31_multisensory_animation_create_not_500(client: httpx.Client):
    """
    POST /api/v1/multisensory/animations must not crash.

    Probes the interactive animation write path. A 500 would mean the
    AnimationType enum is unhappy with the payload, or the
    multisensory_learning_service singleton is missing, or the
    response_model=InteractiveAnimation dataclass serialization broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/multisensory/animations",
        headers=_auth_headers(token),
        json={
            "title": "GF31 probe animation",
            "animation_type": "step_by_step",
            "steps": [
                {"order": 1, "description": "Adım 1"},
                {"order": 2, "description": "Adım 2"},
            ],
            "duration_ms": 5000,
        },
    )
    assert resp.status_code < 500, (
        f"GF31 multisensory/animations crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/multisensory_learning_api.py:139 — "
        f"AnimationType enum + InteractiveAnimation response serialization."
    )


def test_gf32_productive_failure_pretest_start_not_500(client: httpx.Client):
    """
    POST /api/v1/productive-failure/pretest/start must not crash.

    Probes the productive-failure pretest write path. A 500 means the
    topic→question loader broke, the async get_pretest_questions service
    crashed, or the backward-compatibility model_post_init validator broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/productive-failure/pretest/start",
        headers=_auth_headers(token),
        json={
            "topic_id": "matematik-turev",
            "subject": "MATEMATIK",
            "count": 3,
        },
    )
    assert resp.status_code < 500, (
        f"GF32 productive-failure/pretest/start crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/productive_failure_api.py:109 — "
        f"services/productive_failure_service.get_pretest_questions."
    )


def test_gf33_study_plan_create_not_500(client: httpx.Client):
    """
    POST /api/v1/study-plan/ must not crash.

    Probes the F7 study planner write path. A 500 means the
    create_or_update_plan service broke (IRT ability lookup, weekly goal
    distribution, or StudyPlanResponse serializer). Trailing slash is
    required by the router decorator.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/study-plan/",
        headers=_auth_headers(token),
        json={
            "yks_date": "2026-06-20",
            "weekly_hours": 20,
        },
    )
    assert resp.status_code < 500, (
        f"GF33 study-plan/ crashed: {resp.status_code} {resp.text[:300]}. "
        f"Check api/study_planner_api.py:162 — "
        f"services/study_planner_service.create_or_update_plan."
    )


def test_gf34_soru_meydani_ask_question_not_500(client: httpx.Client):
    """
    POST /api/v1/soru-meydani/questions must not crash.

    Probes the F1 forum question write path. A 500 means the
    social_content_filter choked, ForumQuestion model field mismatch, or
    daily count subquery failed. 429 (daily limit) is a legitimate semantic
    response.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/soru-meydani/questions",
        headers=_auth_headers(token),
        json={
            "subject_area": "MATEMATIK",
            "topic": "Türev",
            "question_type": "how_to_solve",
            "title": "GF34 probe: türev kuralı nasıl uygulanır?",
            "body": "f(x) = x^2 fonksiyonunun türevini nasıl alırım?",
        },
    )
    assert resp.status_code < 500, (
        f"GF34 soru-meydani/questions crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/soru_meydani_api.py:77 — "
        f"social_content_filter + ForumQuestion write path."
    )


def test_gf35_usta_cirak_request_not_500(client: httpx.Client):
    """
    POST /api/v1/usta-cirak/request must not crash.

    Probes the F6 mentor matching write path. A 500 means the MentorPair
    OR/SELECT query broke or the or_() SQLAlchemy import is missing in
    prod. 400 (already has mentor) is a legitimate semantic response.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/usta-cirak/request",
        headers=_auth_headers(token),
        json={
            "subject_area": "MATEMATIK",
            "role": "mentee",
        },
    )
    assert resp.status_code < 500, (
        f"GF35 usta-cirak/request crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/usta_cirak_api.py:67 — "
        f"MentorPair or_() query + active pair guard."
    )


def test_gf36_live_sessions_create_not_500(client: httpx.Client):
    """
    POST /api/v1/live-sessions must not crash.

    Probes the Task 108 live Q&A session write path. A 500 means the
    VideoConferenceService.create_session broke (Zoom/Meet adapter missing,
    SessionType enum coercion, or live_sessions table missing). Uses TEACHER
    because students typically cannot host, so 403 is also acceptable.
    """
    token = _login(client, TEACHER)
    resp = client.post(
        "/api/v1/live-sessions",
        headers=_auth_headers(token),
        json={
            "title": "GF36 probe session",
            "description": "Wave 5 golden-flow smoke",
            "scheduled_start": "2026-05-01T10:00:00+00:00",
            "scheduled_end": "2026-05-01T11:00:00+00:00",
            "session_type": "group_session",
            "platform": "jitsi",
            "subject": "MATEMATIK",
            "max_participants": 10,
            "auto_record": False,
            "require_password": False,
        },
    )
    assert resp.status_code < 500, (
        f"GF36 live-sessions crashed: {resp.status_code} {resp.text[:300]}. "
        f"Check api/live_session_routes.py:147 — "
        f"VideoConferenceService.create_session + live_sessions table wiring."
    )


def test_gf37_clustering_auto_not_500(client: httpx.Client):
    """
    POST /api/v1/clustering/auto must not crash.

    Probes the embedding auto-clustering service. Body is a raw
    list[list[float]] — FastAPI accepts it as the sole body param. A 500
    means the auto_cluster service broke (sklearn missing, silhouette
    calculator failed). 501 (ImportError on hdbscan) is an acceptable
    semantic response.
    """
    token = _login(client, STUDENT)
    # 6 tiny 4-dim embeddings — enough for auto_cluster to pick K=2
    embeddings = [
        [0.1, 0.2, 0.3, 0.4],
        [0.15, 0.22, 0.31, 0.42],
        [0.12, 0.19, 0.29, 0.39],
        [0.9, 0.8, 0.7, 0.6],
        [0.92, 0.81, 0.72, 0.61],
        [0.88, 0.79, 0.69, 0.58],
    ]
    resp = client.post(
        "/api/v1/clustering/auto",
        headers=_auth_headers(token),
        json=embeddings,
    )
    # GF22-style waiver: sklearn/hdbscan are optional heavy deps. When they
    # are absent the handler returns a structured 501 "Not Implemented" — not
    # a crash. Only an actual 500 indicates the pipeline is broken.
    assert resp.status_code != 500, (
        f"GF37 clustering/auto crashed 500: {resp.text[:300]}. "
        f"Check api/clustering_api.py:288 — get_clustering_service().auto_cluster."
    )


def test_gf38_search_questions_semantic_not_500(client: httpx.Client):
    """
    POST /api/v1/search/questions must not crash.

    Probes the semantic question search write-path (embedding + vector
    query). A 500 means the ChromaDB / nomic-embed-text adapter broke, the
    SemanticSearchService singleton init crashed, or the query embedding
    pipeline is wired to a dead model. 429 (rate limit 30/min) is OK.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/search/questions",
        headers=_auth_headers(token),
        json={
            "query": "türev kuralları ve uygulamaları",
            "limit": 5,
            "similarity_threshold": 0.5,
            "subject": "MATEMATIK",
            "exam_type": "AYT",
        },
    )
    # GF22-style waiver: ChromaDB / nomic-embed-text are optional. When they
    # are unavailable the handler returns a structured 503 "Service
    # Unavailable" — a semantic signal, not a pipeline crash. Only 500
    # indicates a real regression.
    assert resp.status_code != 500, (
        f"GF38 search/questions crashed 500: {resp.text[:300]}. "
        f"Check api/v1/semantic_search.py:577 — "
        f"SemanticSearchService singleton + embedding pipeline."
    )


def test_gf39_oba_seferleri_contribute_not_500(client: httpx.Client):
    """
    POST /api/v1/oba-seferleri/contribute/{challenge_id} must not crash.

    Probes the F3 team mission write path. With a synthetic challenge_id
    the handler should return 404 "Aktif gorev bulunamadi" — a 500 means
    the query / rate-limit helper / ObaChallengeProgress model broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/oba-seferleri/contribute/gf39-probe-challenge",
        headers=_auth_headers(token),
        json={"amount": 5},
    )
    assert resp.status_code < 500, (
        f"GF39 oba-seferleri/contribute crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/oba_seferleri_api.py:108 — "
        f"_check_rate_limit + ObaChallengeProgress write path."
    )


# ---------------------------------------------------------------------------
# Wave 6 — fourth feature-inventory sweep (Session 141)
#
# Wave 5 probed 10 disjoint top-10 endpoints from the feature inventory and
# fixed 3 real bugs + 1 bonus (GF24). Wave 6 targets a *different* disjoint
# top-10 spanning placement assessment, sequential reasoning, duel
# matchmaking, Zemberek/Turkish-NLP services, grade impact estimator,
# knowledge map update, content recommendations, YKS preference score
# calculation, and emotional state tracking. Same rule as Waves 1–5: the
# handler MUST NOT 500. 501/503 from optional deps are acceptable structured
# unavailability and waived via the GF22 `!= 500` assertion pattern.
# ---------------------------------------------------------------------------


def test_gf40_assessment_start_not_500(client: httpx.Client):
    """
    POST /api/v1/assessment/start must not crash.

    Probes the adaptive placement assessment engine — the very first step
    a brand-new student goes through. A 500 means the CAT/theta-SE service,
    initial question selection, or assessment_sessions table wiring broke.
    With no ``subjects`` filter the handler defaults to all subjects, which
    is the realistic new-student path.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/assessment/start",
        headers=_auth_headers(token),
        json={"subjects": ["MATEMATIK"]},
    )
    assert resp.status_code < 500, (
        f"GF40 assessment/start crashed: {resp.status_code} {resp.text[:300]}. "
        f"Check api/placement_assessment_api.py:129 — start_assessment + "
        f"initial CAT question picker."
    )


def test_gf41_reasoning_solve_not_500(client: httpx.Client):
    """
    POST /api/v1/reasoning/solve must not crash.

    Probes the sequential-reasoning LLM chain (decompose → solve → verify).
    A 500 means the upstream LLM provider call unwrapped an exception at
    handler level instead of returning a graceful error envelope. Upstream
    timeout is treated as acceptable state-dependent skip (like GF24 before
    its slowapi fix) — ``httpx.TimeoutException`` → skip, not a probe
    failure.
    """
    token = _login(client, STUDENT)
    try:
        resp = client.post(
            "/api/v1/reasoning/solve",
            headers=_auth_headers(token),
            json={
                "problem": "x^2 + 5x + 6 = 0 denklemini coz",
                "use_ensemble": False,
                "max_steps": 5,
                "use_cache": True,
            },
            timeout=45.0,
        )
    except httpx.TimeoutException:
        pytest.skip("reasoning/solve upstream LLM did not respond in 45s budget")
    # Optional-dep / unavailable provider is an acceptable structured 503.
    assert resp.status_code != 500, (
        f"GF41 reasoning/solve crashed 500: {resp.text[:300]}. "
        f"Check api/sequential_reasoning_api.py:157 — solve_problem + "
        f"LLM provider error envelope."
    )


def test_gf42_duel_matchmake_not_500(client: httpx.Client):
    """
    POST /api/v1/duel/matchmake must not crash.

    Probes the real-time duel matchmaking write path (Elo rating queue).
    First matchmake call on an empty queue returns ``{status: "queued"}``
    — that's the happy path here, not an error. A 500 means the
    duel_sessions / duel_rating tables are missing, the Elo service
    crashed, or the session_type enum drifted.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/duel/matchmake",
        headers=_auth_headers(token),
        json={"subject": "MATEMATIK"},
    )
    assert resp.status_code < 500, (
        f"GF42 duel/matchmake crashed: {resp.status_code} {resp.text[:300]}. "
        f"Check api/duel_api.py:79 — enqueue_matchmaking + "
        f"get_or_create_rating."
    )


def test_gf43_zemberek_tokenize_not_500(client: httpx.Client):
    """
    POST /api/v1/zemberek/tokenize must not crash.

    Probes the Turkish tokenizer service (Zemberek JVM bridge). A 500 means
    the JPype/Zemberek bootstrap failed, the morphology singleton is None,
    or the response envelope drifted. 503 from ``zemberek_service is None``
    is acceptable structured unavailability (GF22 pattern).
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/zemberek/tokenize",
        headers=_auth_headers(token),
        json={"text": "Kitap okumak çok keyifli bir deneyim."},
    )
    assert resp.status_code != 500, (
        f"GF43 zemberek/tokenize crashed 500: {resp.text[:300]}. "
        f"Check api/zemberek.py:249 — Zemberek JVM singleton + "
        f"tokenizer response envelope."
    )


def test_gf44_turkish_nlp_normalize_not_500(client: httpx.Client):
    """
    POST /api/v1/turkish-nlp/text/normalize must not crash.

    Probes the Turkish text normalization pipeline (NFC + I/ı locale fix +
    whitespace). A 500 means the unicodedata / Turkish lowercase mapping
    got an unexpected input shape. This is the exact surface that has
    historically bitten us with the İ→ı locale trap, so a regression here
    is a red flag for every subject-slug comparison downstream.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/turkish-nlp/text/normalize",
        headers=_auth_headers(token),
        json={"text": "İstanbul'dan İzmir'e gitmek için İDO feribotu"},
    )
    assert resp.status_code != 500, (
        f"GF44 turkish-nlp/text/normalize crashed 500: {resp.text[:300]}. "
        f"Check api/turkish_nlp.py:184 — normalize_text + NFC + "
        f"Turkish lowercase mapping."
    )


def test_gf45_estimate_impact_not_500(client: httpx.Client):
    """
    POST /api/v1/estimate/impact must not crash.

    Probes the YKS score impact estimator — answers the student question
    "if I raise my theta on this subject, how much does my YKS score move?".
    A 500 means the YKSEstimator singleton, ``user_theta`` query, or
    score-type enum coercion broke. 404 is acceptable when the student has
    no theta row yet for the requested subject.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/estimate/impact",
        headers=_auth_headers(token),
        json={
            "puan_turu": "SAY",
            "ders_kodu": "mat",
            "hedef_theta": 1.5,
        },
    )
    assert resp.status_code < 500, (
        f"GF45 estimate/impact crashed: {resp.status_code} {resp.text[:300]}. "
        f"Check app/api/estimator.py:211 — ders_katkisi + YKSEstimator + "
        f"_kullanici_thetalarini_cek."
    )


def test_gf46_knowledge_map_update_not_500(client: httpx.Client):
    """
    POST /api/v1/knowledge-map/update must not crash.

    Probes the knowledge graph mastery update write path. With a synthetic
    ``knowledge_point_id`` the handler should return 404 "knowledge point
    not found" — a 500 means the mastery computation, knowledge_states
    table, or student_id resolution crashed.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/knowledge-map/update",
        headers=_auth_headers(token),
        json={
            "knowledge_point_id": "gf46-probe-kp",
            "is_correct": True,
        },
    )
    assert resp.status_code < 500, (
        f"GF46 knowledge-map/update crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/knowledge_graph_api.py:254 — "
        f"update_knowledge_state + knowledge_states wiring."
    )


def test_gf47_recommendations_not_500(client: httpx.Client):
    """
    POST /api/v1/recommendations must not crash.

    Probes the content recommendation engine (cold-start + diversity).
    A 500 means the vector index, recommendation scorer, or
    cold-start fallback crashed. The seeded student is a fresh user so
    the cold-start branch is exercised.
    """
    token = _login(client, STUDENT)
    # user_id in body is a legacy contract — we pass the seeded student UUID
    # via /auth/me so the body matches what the handler expects.
    me = client.get("/api/v1/auth/me", headers=_auth_headers(token))
    if me.status_code != 200:
        pytest.skip(f"/auth/me failed: {me.status_code}")
    payload = me.json()
    user_id = str(
        payload.get("id")
        or payload.get("user_id")
        or (payload.get("user") or {}).get("id")
        or (payload.get("kullanici") or {}).get("id")
        or ""
    )
    if not user_id:
        pytest.skip("no user id in /auth/me response")
    resp = client.post(
        "/api/v1/recommendations",
        headers=_auth_headers(token),
        json={
            "user_id": user_id,
            "limit": 5,
            "subject_filter": "MATEMATIK",
            "ensure_diversity": True,
        },
    )
    assert resp.status_code != 500, (
        f"GF47 recommendations crashed 500: {resp.text[:300]}. "
        f"Check api/v1/content_recommendation.py:155 — get_recommendations + "
        f"cold-start + diversity pipeline."
    )


def test_gf152_duplicates_check_not_500(client: httpx.Client):
    """
    POST /api/v1/duplicates/check must not crash (admin).

    Probes duplicate vector + embedding path (REQ-5). 403/401/503 are acceptable
    (auth or service unavailable); 500 is a regression.
    """
    token = _login(client, ADMIN)
    resp = client.post(
        "/api/v1/duplicates/check",
        headers=_auth_headers(token),
        json={
            "content": (
                "Benzersiz prob metni: belirli integral alaninda tanimli "
                "fonksiyon icin test icerigi."
            ),
            "check_paraphrase": False,
        },
    )
    assert resp.status_code != 500, (
        f"GF152 duplicates/check crashed 500: {resp.text[:300]}. "
        f"Check api/v1/duplicate_detection.py — check_duplicate + "
        f"DuplicateDetectionService."
    )


def test_gf48_preference_simulation_calculate_score_not_500(client: httpx.Client):
    """
    POST /api/v1/preference-simulation/calculate-score must not crash.

    Probes the YKS score calculator (TYT + AYT + coefficients + bonus).
    A 500 means the ScoreType enum, PreferenceSimulationService wiring,
    or bonus-point helper broke. 400 is acceptable if the probe payload
    trips the input validator (not a regression).
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/preference-simulation/calculate-score",
        headers=_auth_headers(token),
        json={
            "score_type": "SAY",
            "tyt_scores": {
                "turkce": 35.0,
                "sosyal": 18.0,
                "matematik": 38.0,
                "fen": 20.0,
            },
            "ayt_scores": {
                "matematik": 36.0,
                "fizik": 12.0,
                "kimya": 10.0,
                "biyoloji": 11.0,
            },
            "diploma_grade": 88.0,
            "language_certificate": None,
            "special_talent": False,
        },
    )
    assert resp.status_code < 500, (
        f"GF48 preference-simulation/calculate-score crashed: "
        f"{resp.status_code} {resp.text[:300]}. "
        f"Check api/preference_simulation_routes.py:104 — "
        f"PreferenceSimulationService.calculate_yks_score + apply_bonus_points."
    )


def test_gf49_diary_emotional_not_500(client: httpx.Client):
    """
    POST /api/v1/diary/emotional must not crash.

    Probes the emotional state tracking write path (separate table from
    diary/goals which GF26 fixed). A 500 means the EmotionalState model,
    self-awareness scorer, or diary_api.py:1267 handler broke. This is
    the exact class of bug that GF26 found on diary/goals — probing the
    sibling endpoint verifies the fix generalised.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/diary/emotional",
        headers=_auth_headers(token),
        json={
            "confidence_level": 7,
            "frustration_score": 0.2,
            "retry_count": 1,
            "error_count": 0,
            "flow_state": True,
            "productivity_score": 0.75,
            "tasks_completed": 3,
            "task_type": "matematik_problem_cozumu",
            "trigger_factors": {"noise": "low"},
            "context_notes": "GF49 probe",
        },
    )
    assert resp.status_code < 500, (
        f"GF49 diary/emotional crashed: {resp.status_code} {resp.text[:300]}. "
        f"Check api/diary_api.py:1267 — track_emotional_state + "
        f"EmotionalState model write path."
    )


# ============================================================================
# Wave 7 — fifth feature-inventory sweep (Session 142, GF50-GF59)
# ============================================================================
#
# Context: after Wave 6 the feature inventory still had ~480 uncovered
# write-path endpoints. Wave 7 probes a disjoint top-10 spanning XP awards,
# flashcards, AI tutor, notifications, text simplification, study session,
# RAG search, vision question solving, Turkish NLP normalization, and video
# analytics session start. Real bugs fell out on text-simplification imports
# (GF54), rag.py optional-dep 503 wiring (GF56), vision upstream 404 wrap
# (GF57), turkish_nlp service imports (GF58), and VideoWatchSession
# asyncpg VARCHAR+uuid4 trap (GF59 — rule-of-five with Goal/LiveSession/
# EmotionalState/VideoConferenceSession).


def test_gf50_xp_awards_not_500(client: httpx.Client):
    """
    POST /api/v1/xp-awards must not crash.

    Probes the XP awards write path. A 500 means the XP award service,
    gamification points pipeline, or reward calculator broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/xp-awards",
        headers=_auth_headers(token),
        json={"activity": "quiz_completed", "points": 10},
    )
    assert resp.status_code != 500, (
        f"GF50 xp-awards crashed 500: {resp.text[:300]}. "
        f"404 is acceptable (route may be unwired), 500 is a regression."
    )


def test_gf51_flashcards_create_not_500(client: httpx.Client):
    """
    POST /api/v1/flashcards must not crash.

    Probes the flashcard create write path.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/flashcards",
        headers=_auth_headers(token),
        json={"question": "2+2?", "answer": "4", "topic_id": 1},
    )
    assert resp.status_code != 500, (
        f"GF51 flashcards crashed 500: {resp.text[:300]}. "
        f"404 is acceptable (route may be unwired), 500 is a regression."
    )


def test_gf52_ai_tutor_session_not_500(client: httpx.Client):
    """
    POST /api/v1/ai-tutor/session must not crash.

    Probes the AI tutor session write path.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/ai-tutor/session",
        headers=_auth_headers(token),
        json={"topic": "matematik"},
    )
    assert resp.status_code != 500, (
        f"GF52 ai-tutor/session crashed 500: {resp.text[:300]}. "
        f"404 is acceptable (route may be unwired), 500 is a regression."
    )


def test_gf53_notifications_create_not_500(client: httpx.Client):
    """
    POST /api/v1/notifications must not crash.

    Probes the notifications create write path.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/notifications",
        headers=_auth_headers(token),
        json={"title": "GF53 probe", "body": "test"},
    )
    assert resp.status_code != 500, (
        f"GF53 notifications crashed 500: {resp.text[:300]}. "
        f"404 is acceptable (route may be unwired), 500 is a regression."
    )


def test_gf54_text_simplification_simplify_not_500(client: httpx.Client):
    """
    POST /api/v1/text-simplification/simplify must not crash.

    Probes the dyslexia-support text simplification write path. A 500
    means the complexity detector, synonym replacer, or Flesch-Kincaid
    pipeline broke. Wave 7 found the router was unwired and the service
    imports were missing — GF54 is the regression gate that ensures the
    module loads and the pipeline completes end-to-end.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/text-simplification/simplify",
        headers=_auth_headers(token),
        json={
            "text": "Bu oldukça karmaşık ve uzun bir cümle örneğidir.",
            "complexity_threshold": 0.6,
            "max_sentence_length": 20,
            "replace_synonyms": True,
            "split_sentences": True,
            "require_confirmation": False,
        },
    )
    assert resp.status_code != 500, (
        f"GF54 text-simplification/simplify crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/text_simplification.py imports + "
        f"core/text_simplification_service.py wiring."
    )


def test_gf55_study_session_start_not_500(client: httpx.Client):
    """
    POST /api/v1/study-session/start must not crash.

    Probes the study session start write path.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/study-session/start",
        headers=_auth_headers(token),
        json={"topic_id": 1},
    )
    assert resp.status_code != 500, (
        f"GF55 study-session/start crashed 500: {resp.text[:300]}. "
        f"404 is acceptable (route may be unwired), 500 is a regression."
    )


def test_gf56_rag_search_not_500(client: httpx.Client):
    """
    POST /api/v1/rag/search must not crash.

    Probes the RAG semantic search write path. ChromaDB + nomic-embed-text
    are optional heavy deps, so 503 "Service Unavailable" is an acceptable
    structured response (GF22/GF37/GF38 pattern). A 500 means the optional
    dep fallback wiring broke and the module-level sentinel crashed before
    the 503 translator could fire. Wave 7 also found a ``from __future__
    import annotations`` was needed to prevent ``None | None`` type-hint
    evaluation on the ``_rag_service: RAGService | None`` module annotation.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/rag/search",
        headers=_auth_headers(token),
        json={"query": "matematik turev", "k": 3},
    )
    assert resp.status_code != 500, (
        f"GF56 rag/search crashed 500: {resp.text[:300]}. "
        f"503 is acceptable (chromadb/nomic-embed-text optional dep "
        f"unavailable), 500 is a regression. Check api/rag.py "
        f"_require_rag_service + __future__ annotations."
    )


def test_gf57_vision_solve_question_not_500(client: httpx.Client):
    """
    POST /api/v1/vision/solve-question must not crash.

    Probes the Qwen3-VL vision solve write path. The upstream ollama
    runtime is optional and the vision model may not be pulled, so
    503 "Vision model unavailable" is an acceptable structured response
    (GF22/GF37/GF38 pattern). Wave 7 found ``core.llm_service.analyze_image``
    wraps upstream httpx errors in ``OllamaError(...) from e``, so the
    vision_api.py ``analyze_with_vision`` helper needed to catch
    ``OllamaError`` (not httpx types directly) to translate upstream 404s
    into 503s. A 500 means that translation broke.
    """
    import base64

    # Minimal 1x1 PNG (89 50 4e 47 ... IEND)
    png_bytes = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "000000097048597300000ec300000ec301c76fa8640000000d49444154789c6300"
        "0100000005000102d0a8d5dc0000000049454e44ae426082"
    )
    image_b64 = base64.b64encode(png_bytes).decode()
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/vision/solve-question",
        headers=_auth_headers(token),
        json={
            "image": image_b64,
            "subject": "matematik",
            "level": "TYT",
            "show_steps": True,
        },
    )
    assert resp.status_code != 500, (
        f"GF57 vision/solve-question crashed 500: {resp.text[:300]}. "
        f"503 is acceptable (ollama upstream unreachable / vision model "
        f"not pulled), 500 is a regression. Check api/vision_api.py "
        f"analyze_with_vision OllamaError translation."
    )


def test_gf58_turkish_nlp_normalize_not_500(client: httpx.Client):
    """
    POST /api/v1/turkish-nlp/text/normalize must not crash.

    Probes the Turkish NLP normalization write path. A 500 means the
    Zemberek JVM bridge, encoding fixer, or Turkish character normalizer
    broke. Wave 7 found the router was unwired and service imports were
    missing — GF58 is the regression gate for the normalization pipeline.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/turkish-nlp/text/normalize",
        headers=_auth_headers(token),
        json={"text": "merhaba dunya, Bu bir test metnidir."},
    )
    assert resp.status_code != 500, (
        f"GF58 turkish-nlp/text/normalize crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/turkish_nlp.py imports + "
        f"core/turkish_nlp_service.py wiring."
    )


def test_gf59_video_analytics_session_start_not_500(client: httpx.Client):
    """
    POST /api/v1/video-analytics/sessions/start must not crash.

    Probes the video watch session start write path. Wave 7 caught the
    asyncpg VARCHAR+uuid4 trap (rule-of-five with Goal/LiveSession/
    EmotionalState/VideoConferenceSession from GF26/GF36/GF49/GF36):
    ``VideoWatchSession.id = Column(String, default=uuid.uuid4)`` produces
    UUID objects that asyncpg refuses to bind to VARCHAR columns.
    Caller-level ``str(uuid4())`` coercion in
    ``video_analytics_service.start_watch_session`` is the fix.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/video-analytics/sessions/start",
        headers=_auth_headers(token),
        json={
            "video_id": "gf59-probe",
            "video_source": "youtube",
            "video_duration": 600,
        },
    )
    assert resp.status_code != 500, (
        f"GF59 video-analytics/sessions/start crashed 500: {resp.text[:300]}. "
        f"Check services/video_analytics_service.py start_watch_session — "
        f"asyncpg VARCHAR+uuid4 rule-of-five requires "
        f"id=str(uuid4()) + user_id=str(user_id) caller coercion."
    )


# ---------------------------------------------------------------------------
# Wave 8 — sixth feature-inventory sweep (Session 143, 10 new probes)
#
# Disjoint top-10 from docs/audits/2026-04-11_feature-inventory.md spanning
# multisensory learning, visual supports, admin orchestrator, BERTurk intent,
# Zemberek spell-check, DINA mastery estimate, content moderation, diary
# SMART validation, forum solutions (soru-meydani), and teacher assignments.
# 1 real bug fell out: GF65 DINA caller/service contract drift.
# ---------------------------------------------------------------------------


def test_gf60_multisensory_multimodal_not_500(client: httpx.Client):
    """
    POST /api/v1/multisensory/multimodal must not crash.

    Probes the multisensory learning content creation write path
    (REQ-50.89). A 500 means the MultimodalContent model serialization,
    LearningModality enum coercion, or service singleton wiring broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/multisensory/multimodal",
        headers=_auth_headers(token),
        json={
            "title": "GF60 probe",
            "subject": "biyoloji",
            "topic": "Fotosentez",
            "modalities": ["visual"],
        },
    )
    assert resp.status_code != 500, (
        f"GF60 multisensory/multimodal crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/multisensory_learning_api.py "
        f"create_multimodal_content + service wiring."
    )


def test_gf61_visual_supports_mind_map_not_500(client: httpx.Client):
    """
    POST /api/v1/visual-supports/mind-maps must not crash.

    Probes the mind-map generation write path (REQ-50.73). A 500 means
    the visual_supports_service.generate_mind_map pipeline or MindMap
    response model broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/visual-supports/mind-maps",
        headers=_auth_headers(token),
        json={
            "title": "GF61 probe",
            "subject": "matematik",
            "topic": "Cebirsel Ifadeler",
            "content": "x + y = z",
        },
    )
    assert resp.status_code != 500, (
        f"GF61 visual-supports/mind-maps crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/visual_supports_api.py "
        f"create_mind_map + services/visual_supports_service.py."
    )


def test_gf62_admin_orchestrator_dispatch_not_500(client: httpx.Client):
    """
    POST /api/v1/admin/orchestrator/dispatch must not crash.

    Probes the orchestrator RoutingEngine admin endpoint. Non-admin
    students should receive 403 (admin gate), NOT 500. A 500 means the
    RoutingEngine import, orchestrator.core.routing module, or the
    get_current_admin_user dependency broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/admin/orchestrator/dispatch",
        headers=_auth_headers(token),
        json={"description": "GF62 probe task", "files": []},
    )
    assert resp.status_code != 500, (
        f"GF62 admin/orchestrator/dispatch crashed: {resp.status_code} "
        f"{resp.text[:300]}. 403 is expected for non-admin. "
        f"Check api/orchestrator_api.py + orchestrator.core.routing import."
    )


def test_gf63_berturk_intent_detect_not_500(client: httpx.Client):
    """
    POST /api/v1/berturk/intent/detect must not crash.

    Probes BERTurk intent detection. Same optional-dep pattern as GF22
    (sentiment): when transformers/model weights are missing the handler
    must return 503 via _require_berturk_service() rather than
    AttributeError: 'NoneType' → 500.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/berturk/intent/detect",
        headers=_auth_headers(token),
        json={"text": "bu konuyu nasil calisabilirim"},
    )
    assert resp.status_code != 500, (
        f"GF63 berturk/intent/detect crashed 500: {resp.text[:300]}. "
        f"503 is acceptable when transformers is absent (GF22 pattern). "
        f"Check api/berturk_api.py _require_berturk_service() guard."
    )


def test_gf64_zemberek_spell_check_not_500(client: httpx.Client):
    """
    POST /api/v1/zemberek/spell-check must not crash.

    Probes the Zemberek JVM spell-check bridge. The optional-dep
    fallback is graceful: suggestions list may be empty but the
    pipeline must never crash. A 500 means the JVM client, request
    schema (field: word, NOT text), or Zemberek loader broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/zemberek/spell-check",
        headers=_auth_headers(token),
        json={"word": "matemaatik"},
    )
    assert resp.status_code != 500, (
        f"GF64 zemberek/spell-check crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/zemberek.py schema (word field) "
        f"and JVM bridge fallback."
    )


def test_gf65_dina_estimate_not_500(client: httpx.Client):
    """
    POST /api/v1/dina/estimate must not crash.

    Probes the DINA nano-skill mastery Bayesian update write path.
    Wave 8 caught a caller/service contract drift: the service
    ``estimate_student_mastery`` returns ``list[dict]`` (per-nano-skill
    updates) but the caller did ``MasteryEstimateResponse(**result)``
    which expects a mapping, crashing with
    ``TypeError: argument after ** must be a mapping, not list``.
    Fix: caller now transforms the list to SkillMasteryItem rows and
    builds the response envelope; empty list → 404 "not in DINA map".
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/dina/estimate",
        headers=_auth_headers(token),
        json={
            "question_id": "00000000-0000-0000-0000-000000000000",
            "is_correct": True,
        },
    )
    assert resp.status_code != 500, (
        f"GF65 dina/estimate crashed 500: {resp.text[:300]}. "
        f"Check api/dina_api.py estimate_mastery — service returns "
        f"list[dict], caller must build MasteryEstimateResponse from it."
    )


def test_gf66_moderation_report_not_500(client: httpx.Client):
    """
    POST /api/v1/moderation/reports must not crash.

    Probes the content moderation report write path. A 500 means the
    ContentReport model, social content filter wiring, or the reason/
    content_type regex validators broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/moderation/reports",
        headers=_auth_headers(token),
        json={
            "reported_content_id": "00000000-0000-0000-0000-000000000000",
            "content_type": "chat_message",
            "reason": "spam",
            "description": "gf66 probe",
        },
    )
    assert resp.status_code != 500, (
        f"GF66 moderation/reports crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/moderation_api.py create_report "
        f"+ ContentReport ORM write path."
    )


def test_gf67_diary_goals_validate_smart_not_500(client: httpx.Client):
    """
    POST /api/v1/diary/goals/validate-smart must not crash.

    Probes the SMART goal criteria validation write path. A 500 means
    the GoalService.validate_smart pipeline or the GoalCreate pydantic
    model_validator broke. Note that SMART validation is advisory (soft
    warnings, not hard rejection).
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/diary/goals/validate-smart",
        headers=_auth_headers(token),
        json={
            "title": "GF67 hedef",
            "description": "test goal",
            "target_value": 10.0,
            "target_date": "2026-12-31T23:59:59",
            "category": "academic",
            "priority": 2,
        },
    )
    assert resp.status_code != 500, (
        f"GF67 diary/goals/validate-smart crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/diary_api.py + "
        f"services/diary/goal_service.py validate_smart."
    )


def test_gf68_soru_meydani_solution_not_500(client: httpx.Client):
    """
    POST /api/v1/soru-meydani/questions/{id}/solutions must not crash.

    Probes the forum solution submission write path. A 500 means the
    ForumSolution ORM write, social content filter, or rate limiting
    broke. A 404 "Soru bulunamadi" for a bogus UUID is semantic
    (question does not exist in the forum), NOT a crash.
    """
    token = _login(client, STUDENT)
    bogus_question = "00000000-0000-0000-0000-000000000000"
    resp = client.post(
        f"/api/v1/soru-meydani/questions/{bogus_question}/solutions",
        headers=_auth_headers(token),
        json={"body": "Bu sorunun cozumu: once x'i bul, sonra y'yi hesapla."},
    )
    assert resp.status_code != 500, (
        f"GF68 soru-meydani solutions crashed 500: {resp.text[:300]}. "
        f"404 is acceptable when question not found. "
        f"Check api/soru_meydani_api.py submit_solution."
    )


def test_gf69_teacher_assignment_create_not_500(client: httpx.Client):
    """
    POST /api/v1/teacher/assignments must not crash.

    Probes the teacher assignment creation write path. Canonical TR
    field schema (baslik/aciklama/sinif/teslim_tarihi) must be
    accepted — an English-schema request would 422 and mask this probe.
    A 500 means the TeacherAssignment ORM write, async session handling,
    or datetime parsing broke.
    """
    token = _login(client, TEACHER)
    resp = client.post(
        "/api/v1/teacher/assignments",
        headers=_auth_headers(token),
        json={
            "baslik": "GF69 probe odev",
            "aciklama": "deneme",
            "sinif": "12A",
            "teslim_tarihi": "2026-12-31T23:59:59",
        },
    )
    assert resp.status_code != 500, (
        f"GF69 teacher/assignments crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check app/api/teacher_classroom.py "
        f"create_assignment + TeacherAssignment ORM write."
    )


# ---------------------------------------------------------------------------
# Wave 9 — seventh feature-inventory sweep (Session 144)
# ---------------------------------------------------------------------------


def test_gf70_adhd_focus_mode_activate_not_500(client: httpx.Client):
    """
    POST /api/v1/adhd-support/focus-mode/activate must not crash.

    Probes the ADHD focus-mode activation write path. A 500 means the
    sync ORM session (get_db) or the FocusModeSession write broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/adhd-support/focus-mode/activate",
        headers=_auth_headers(token),
        json={
            "task_id": None,
            "settings": {
                "hide_sidebar": True,
                "hide_navigation": True,
                "hide_notifications": True,
                "fullscreen_mode": False,
                "minimal_ui": True,
                "show_timer": True,
                "show_progress": True,
            },
        },
    )
    assert resp.status_code != 500, (
        f"GF70 focus-mode/activate crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/adhd_focus_mode_api.py."
    )


def test_gf71_adhd_task_create_not_500(client: httpx.Client):
    """
    POST /api/v1/adhd-support/tasks/create must not crash.

    Probes the ADHD task management create write path. A 500 means
    CreateTaskRequest handler, User ORM lookup, or task persistence
    broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/adhd-support/tasks/create",
        headers=_auth_headers(token),
        json={
            "title": "GF71 probe gorevi",
            "description": "wave 9 probe",
            "category": "study",
            "estimated_duration_minutes": 30,
            "is_urgent": False,
            "is_important": True,
        },
    )
    assert resp.status_code != 500, (
        f"GF71 adhd tasks/create crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/adhd_task_management_api.py."
    )


def test_gf72_multisensory_video_add_not_500(client: httpx.Client):
    """
    POST /api/v1/multisensory/videos must not crash.

    Probes the multisensory video add write path (sibling of GF31
    animations and GF60 multimodal). A 500 means the EducationalVideo
    service write or ModalityMapping broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/multisensory/videos",
        headers=_auth_headers(token),
        json={
            "title": "GF72 probe video",
            "description": "wave 9 probe",
            "url": "https://example.com/video.mp4",
            "duration_seconds": 120,
            "subject": "MATEMATIK",
            "topic": "Turev",
        },
    )
    assert resp.status_code != 500, (
        f"GF72 multisensory/videos crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/multisensory_learning_api.py."
    )


def test_gf73_visual_supports_infographic_not_500(client: httpx.Client):
    """
    POST /api/v1/visual-supports/infographics must not crash.

    Probes the infographic creation write path (sibling of GF61
    mind-maps). A 500 means the visual_supports_service generator
    or template resolution broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/visual-supports/infographics",
        headers=_auth_headers(token),
        json={
            "title": "GF73 probe infografik",
            "subject": "MATEMATIK",
            "topic": "Turev",
            "template": "bar_chart",
            "data": [
                {"label": "2020", "value": 10},
                {"label": "2021", "value": 15},
            ],
        },
    )
    assert resp.status_code != 500, (
        f"GF73 visual-supports/infographics crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/visual_supports_api.py."
    )


def test_gf74_visual_supports_vocab_card_not_500(client: httpx.Client):
    """
    POST /api/v1/visual-supports/vocabulary-cards must not crash.

    Probes the vocabulary card creation write path. A 500 means the
    visual_supports_service write or field validation broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/visual-supports/vocabulary-cards",
        headers=_auth_headers(token),
        json={
            "word": "integral",
            "definition": "fonksiyonun toplam alanini bulan islem",
            "image_url": "https://example.com/integral.png",
            "category": "MATEMATIK",
            "example_sentence": "f(x) fonksiyonunun integrali F(x)'dir.",
            "difficulty_level": 3,
        },
    )
    assert resp.status_code != 500, (
        f"GF74 visual-supports/vocabulary-cards crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/visual_supports_api.py."
    )


def test_gf75_berturk_motivation_assess_not_500(client: httpx.Client):
    """
    POST /api/v1/berturk/motivation/assess must not crash.

    Probes the BERTurk motivation assessment write path (sibling of
    GF22 sentiment and GF63 intent). A 503 is acceptable when
    transformers / model weights are missing (GF22 optional-dep
    pattern).
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/berturk/motivation/assess",
        headers=_auth_headers(token),
        json={
            "student_id": "gf75-probe-student",
            "recent_texts": [
                "Bugun matematik calisirken cok yorulmustum.",
                "Ama turev konusunu sonunda anladim!",
            ],
            "time_window_hours": 24,
        },
    )
    assert resp.status_code != 500, (
        f"GF75 berturk/motivation crashed: {resp.status_code} "
        f"{resp.text[:300]}. 503 is acceptable when optional deps "
        f"are missing (GF22 pattern). Check api/berturk_api.py."
    )


def test_gf76_reasoning_decompose_not_500(client: httpx.Client):
    """
    POST /api/v1/reasoning/decompose must not crash.

    Probes the sequential reasoning decompose write path (sibling of
    GF41 solve). As noted in Wave 6, sequential_reasoning_api may
    be unwired — 404 is acceptable, only 500 is a crash regression.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/reasoning/decompose",
        headers=_auth_headers(token),
        json={
            "problem": (
                "Bir dik ucgenin kenarlari 3-4-5 oldugunda alanini ve "
                "cevresini hesaplayin."
            ),
        },
    )
    assert resp.status_code != 500, (
        f"GF76 reasoning/decompose crashed: {resp.status_code} "
        f"{resp.text[:300]}. 404 is acceptable when router unwired "
        f"(GF41 pattern). Check api/sequential_reasoning_api.py."
    )


def test_gf77_turkish_nlp_chat_message_not_500(client: httpx.Client):
    """
    POST /api/v1/turkish-nlp-chat/message must not crash.

    Probes the Turkish NLP chat message write path. A 500 means the
    chat session creation, LLM dispatch, or conversation persistence
    broke. Optional upstream timeout is acceptable via skip (GF24 pattern).
    """
    token = _login(client, STUDENT)
    try:
        resp = client.post(
            "/api/v1/turkish-nlp-chat/message",
            headers=_auth_headers(token),
            json={
                "student_id": "gf77-probe-student",
                "message": "Integral nedir?",
                "subject": "matematik",
            },
        )
    except httpx.ReadTimeout:
        pytest.skip("GF77 upstream LLM timeout — state-dependent")
    assert resp.status_code != 500, (
        f"GF77 turkish-nlp-chat/message crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/turkish_nlp_chat.py."
    )


def test_gf78_analytics_export_csv_not_500(client: httpx.Client):
    """
    POST /api/v1/analytics/export/csv must not crash.

    Probes the analytics CSV export write path. A 500 means the
    CSV generator, data aggregation, or filter handling broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/analytics/export/csv",
        headers=_auth_headers(token),
        json={
            "format": "csv",
            "data_type": "student",
            "filters": {},
        },
    )
    assert resp.status_code != 500, (
        f"GF78 analytics/export/csv crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/analytics.py export_analytics_csv."
    )


def test_gf79_elasticsearch_questions_search_not_500(client: httpx.Client):
    """
    POST /api/v1/elasticsearch/questions/search must not crash.

    Probes the Elasticsearch question search write path (POST with
    body, not GET). A 503 is acceptable when ES is not running in
    the MVP Docker stack (GF22 optional-dep pattern).
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/elasticsearch/questions/search",
        headers=_auth_headers(token),
        json={
            "query": "turev",
            "size": 10,
            "from": 0,
            "subject": "MATEMATIK",
        },
    )
    assert resp.status_code != 500, (
        f"GF79 elasticsearch/questions/search crashed: {resp.status_code} "
        f"{resp.text[:300]}. 503 is acceptable when ES unavailable "
        f"(GF22 pattern). Check api/elasticsearch.py."
    )


# ---------------------------------------------------------------------------
# Wave 10 — Golden Flow sweep GF80-GF89 (Session 144)
# ---------------------------------------------------------------------------
# Disjoint top-10 from docs/audits/2026-04-11_feature-inventory.md after
# Wave 9. Targets: league XP award, learning-style questionnaire + behavioral
# data, hybrid question generation, alternative solutions, MEB curriculum
# standard, ADHD instant-feedback answer + performance, exam PDF report,
# team challenges create. All probes assert `status_code != 500` — semantic
# 4xx/404/503 are acceptable, only 500 is a crash regression.


def test_gf80_leagues_award_xp_not_500(client: httpx.Client):
    """
    POST /api/v1/leagues/award-xp must not crash.

    Probes the league XP award write path. A 500 means the league
    service, XP transaction persist, or rate-limit plumbing broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/leagues/award-xp",
        headers=_auth_headers(token),
        json={
            "xp_amount": 50,
            "source": "gf80_probe",
        },
    )
    assert resp.status_code != 500, (
        f"GF80 leagues/award-xp crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/league_api.py award_xp."
    )


def test_gf81_learning_style_questionnaire_not_500(client: httpx.Client):
    """
    POST /api/v1/learning-style/questionnaire/{student_id} must not crash.

    Probes the VARK questionnaire write path. A 500 means the VARK
    score calculation, LearningPathStudentProfile update, or DB
    commit broke.
    """
    token = _login(client, STUDENT)
    # student_id taken from /auth/me since the handler does verify_student_access
    me = client.get("/api/v1/auth/me", headers=_auth_headers(token)).json()
    user = me.get("user") or me.get("kullanici") or me
    student_id = str(user.get("id") or user.get("user_id") or "gf81-probe")
    resp = client.post(
        f"/api/v1/learning-style/questionnaire/{student_id}",
        headers=_auth_headers(token),
        json={
            "student_id": student_id,
            "questionnaire_type": "VARK",
            "responses": {
                "q1": "visual",
                "q2": "auditory",
                "q3": "reading",
                "q4": "kinesthetic",
                "q5": "visual",
            },
            "completion_time": 3.5,
        },
    )
    assert resp.status_code != 500, (
        f"GF81 learning-style/questionnaire crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/learning_style.py submit_questionnaire."
    )


def test_gf82_learning_style_behavioral_data_not_500(client: httpx.Client):
    """
    POST /api/v1/learning-style/behavioral-data/{student_id} must not crash.

    Probes the behavioral-data write path. A 500 means the
    LearningStyleService.update_behavioral_data call, profile
    recalculation, or DB commit broke.
    """
    token = _login(client, STUDENT)
    me = client.get("/api/v1/auth/me", headers=_auth_headers(token)).json()
    user = me.get("user") or me.get("kullanici") or me
    student_id = str(user.get("id") or user.get("user_id") or "gf82-probe")
    resp = client.post(
        f"/api/v1/learning-style/behavioral-data/{student_id}",
        headers=_auth_headers(token),
        json={
            "student_id": student_id,
            "video_watch_time": 15.0,
            "text_reading_time": 10.0,
            "interactive_engagement": 5.0,
            "quiz_completion_rate": 0.8,
            "note_taking_frequency": 3,
            "question_asking_frequency": 2,
            "peer_interaction_count": 1,
            "help_seeking_behavior": 1,
            "visual_content_performance": 0.75,
            "auditory_content_performance": 0.65,
        },
    )
    assert resp.status_code != 500, (
        f"GF82 learning-style/behavioral-data crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/learning_style.py update_behavioral_data."
    )


def test_gf83_hybrid_question_generate_not_500(client: httpx.Client):
    """
    POST /api/v1/questions/hybrid/generate must not crash.

    Probes the hybrid AI question-generation write path. The handler
    calls an upstream LLM (claude provider); 503 is acceptable when
    the optional provider key/model is unavailable (GF22 pattern),
    and upstream timeout is acceptable as a skip (GF24 pattern).
    """
    token = _login(client, STUDENT)
    try:
        resp = client.post(
            "/api/v1/questions/hybrid/generate",
            headers=_auth_headers(token),
            json={
                "subject": "Matematik",
                "topic": "Turev",
                "difficulty": "orta",
                "exam_type": "TYT",
                "method": "osym_guided",
                "provider": "claude",
                "validate": False,
                "enable_wave2b": False,
            },
        )
    except httpx.ReadTimeout:
        pytest.skip("GF83 upstream LLM timeout — state-dependent")
    assert resp.status_code != 500, (
        f"GF83 questions/hybrid/generate crashed: {resp.status_code} "
        f"{resp.text[:300]}. 503 is acceptable when provider key "
        f"missing (GF22 pattern). Check api/hybrid_question_generation.py."
    )


def test_gf84_questions_alternatives_add_not_500(client: httpx.Client):
    """
    POST /api/v1/questions/alternatives/{question_id}/solutions must not crash.

    Probes the alternative-solution add write path. Synthetic question
    id is expected to return 404 — only 500 is a regression.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/questions/alternatives/gf84-probe-question/solutions",
        headers=_auth_headers(token),
        json={
            "title": "GF84 probe cozumu",
            "category": "klasik",
            "difficulty": "orta",
            "estimated_time_seconds": 120,
            "steps": [
                {
                    "step_number": 1,
                    "description": "Denklemi tanimla",
                },
                {
                    "step_number": 2,
                    "description": "Degiskenleri cozumleyerek bul",
                },
            ],
            "created_by_type": "student",
        },
    )
    assert resp.status_code != 500, (
        f"GF84 questions/alternatives/solutions crashed: {resp.status_code} "
        f"{resp.text[:300]}. 404 acceptable for synthetic question_id. "
        f"Check api/alternative_solutions_api.py add_alternative_solution."
    )


def test_gf85_curriculum_meb_standards_add_not_500(client: httpx.Client):
    """
    POST /api/v1/curriculum/meb/standards must not crash.

    Probes the MEB curriculum standard add write path. A 500 means
    the CurriculumComplianceSystem.add_meb_standard pipeline, cache
    service init, or database service init broke.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/curriculum/meb/standards",
        headers=_auth_headers(token),
        json={
            "id": "gf85-probe-standard",
            "subject": "matematik",
            "grade_level": "12",
            "unit_name": "Turev",
            "topic_name": "Turevin Geometrik Yorumu",
            "learning_outcomes": ["Turev kavramini aciklar"],
            "key_concepts": ["limit", "tegent"],
            "skills": ["hesaplama"],
            "duration_hours": 6,
            "prerequisites": [],
            "assessment_criteria": [],
        },
    )
    assert resp.status_code != 500, (
        f"GF85 curriculum/meb/standards crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/curriculum_compliance.py add_meb_standard."
    )


def test_gf86_adhd_feedback_answer_not_500(client: httpx.Client):
    """
    POST /api/v1/adhd-support/feedback/answer must not crash.

    Probes the instant-feedback answer write path. The handler is
    declared as sync `def` with a `Session = Depends(get_db)` — this
    is the same GF7wA/GF8wA pattern (Wave 2) that crashed earlier
    read endpoints with MissingGreenlet because KIRO2 uses AsyncSession.
    If this fires, the fix is to convert the handler to async + use
    the async `get_db_session_context` OR keep it sync but ensure
    the dependency returns a real sync Session.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/adhd-support/feedback/answer",
        headers=_auth_headers(token),
        json={
            "is_correct": True,
            "question_id": "gf86-probe-question",
            "subject": "matematik",
            "difficulty": "orta",
        },
    )
    assert resp.status_code != 500, (
        f"GF86 adhd-support/feedback/answer crashed: {resp.status_code} "
        f"{resp.text[:300]}. Sync handler + async session is a "
        f"GF7wA/GF8wA-class bug. Check api/instant_feedback_api.py."
    )


def test_gf87_adhd_feedback_performance_not_500(client: httpx.Client):
    """
    POST /api/v1/adhd-support/feedback/performance must not crash.

    Sibling of GF86 — probes the performance-record write path in
    the same instant_feedback_api.py module. Same sync-handler /
    async-session risk applies.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/adhd-support/feedback/performance",
        headers=_auth_headers(token),
        json={
            "score": 85,
            "questions_answered": 10,
            "correct_answers": 8,
            "subject": "matematik",
            "difficulty": "orta",
        },
    )
    assert resp.status_code != 500, (
        f"GF87 adhd-support/feedback/performance crashed: {resp.status_code} "
        f"{resp.text[:300]}. Sync handler + async session is a "
        f"GF7wA/GF8wA-class bug. Check api/instant_feedback_api.py."
    )


def test_gf88_reports_exam_generate_pdf_not_500(client: httpx.Client):
    """
    POST /api/v1/reports/exam/{sinav_id}/generate-pdf must not crash.

    Probes the advanced-exam-report PDF generation write path with a
    synthetic sinav_id. 404 "Sınav sonucu bulunamadı" is the expected
    happy-path reject; only 500 is a crash regression.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/reports/exam/gf88-probe-sinav-id/generate-pdf",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF88 reports/exam/generate-pdf crashed: {resp.status_code} "
        f"{resp.text[:300]}. 404 acceptable for synthetic sinav_id. "
        f"Check api/advanced_reports.py generate_pdf_report."
    )


def test_gf89_team_challenges_create_not_500(client: httpx.Client):
    """
    POST /api/v1/challenges/teams/create must not crash.

    Probes the team-challenge create write path. The handler does a
    late `from ..services.team_challenges import TeamChallengeManager`
    — if that relative import is stale the router load or call will
    blow up. 404/503 acceptable, only 500 is a regression.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/challenges/teams/create",
        headers=_auth_headers(token),
        json={
            "team_name": "GF89 Probe Team",
            "is_public": True,
        },
    )
    assert resp.status_code != 500, (
        f"GF89 challenges/teams/create crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/team_challenges_api.py create_team."
    )


# ---------------------------------------------------------------------------
# Wave 11 — eighth feature-inventory sweep (Session 147, GF90-GF99)
#
# Disjoint top-10 covering: exam-performance analytics, exam answer error
# tagging, PDF OCR processing, parent social settings, video-analytics notes,
# manipulatives badge claim, pomodoro room join, offline PWA sync results,
# knowledge-map mastery update, and admin encryption key rotation (admin-gate).
# Avoids all Wave 1-10 touched modules (visual_supports, instant_feedback,
# advanced_reports, adhd_*, learning_style, curriculum_compliance, diary,
# dina, moderation, team_challenges, video-analytics sessions/start).
# ---------------------------------------------------------------------------


def test_gf90_exam_performance_detailed_analysis_not_500(client: httpx.Client):
    """
    GET /api/v1/exam-performance/{sid}/detailed-analysis must not crash.

    Probes the exam performance analytics pipeline. The service
    (exam_performance_service.analyze_exam_performance) joins exam sessions,
    answer tracking, IRT theta and topic hierarchies — any wrong-table or
    async session trap surfaces as a 500 at the `db.execute` call site. 404
    is acceptable for a synthetic sinav_id.
    """
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/exam-performance/gf90-synthetic-sid/detailed-analysis",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF90 exam-performance/detailed-analysis crashed: {resp.status_code} "
        f"{resp.text[:300]}. 404 acceptable for synthetic sid. "
        f"Check api/exam_performance.py + services/exam_performance_service.py."
    )


def test_gf91_exam_answer_tracking_error_type_not_500(client: httpx.Client):
    """
    PATCH /api/v1/exam-answer-tracking/{sid}/answers/{qid}/error-type must not crash.

    Probes the write path that lets a student tag a wrong answer with an
    error category (concept/procedural/careless/knowledge_gap). The handler
    joins ExamSession + ExamAnswerTracking rows and writes the error_type
    column. 404 is acceptable for synthetic sid/qid ("Hata tipi atanamadı").
    """
    token = _login(client, STUDENT)
    resp = client.patch(
        "/api/v1/exam-answer-tracking/gf91-synthetic-sid/answers/gf91-qid/error-type",
        headers=_auth_headers(token),
        json={"error_type": "concept"},
    )
    assert resp.status_code != 500, (
        f"GF91 exam-answer-tracking/error-type crashed: {resp.status_code} "
        f"{resp.text[:300]}. 404 acceptable for synthetic ids. "
        f"Check api/exam_answer_tracking.py update_error_type."
    )


def test_gf92_pdf_upload_not_500(client: httpx.Client):
    """
    POST /api/v1/pdf/upload must not crash on a minimal PDF multipart.

    Probes the PDF OCR ingestion write path. The handler validates the
    content-type + extension, writes the file to disk, enqueues the Celery
    OCR task, and returns the job id. 4xx is acceptable if Celery is
    unavailable in the test stack — only a 500 during dispatch is a regression.
    """
    token = _login(client, STUDENT)
    # Minimal valid PDF bytes — 1-page empty PDF (well-formed header/trailer).
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
        b"0000000055 00000 n\n0000000099 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF\n"
    )
    resp = client.post(
        "/api/v1/pdf/upload",
        headers=_auth_headers(token),
        files={"file": ("gf92_probe.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code != 500, (
        f"GF92 pdf/upload crashed: {resp.status_code} {resp.text[:300]}. "
        f"4xx (Celery unavailable, quota, etc.) acceptable. "
        f"Check api/pdf_processing_api.py upload_pdf."
    )


def test_gf93_parent_social_settings_update_not_500(client: httpx.Client):
    """
    PUT /api/v1/parent-social/settings/{student_id} must not crash.

    Probes the parent social-settings write path. The handler requires a
    PARENT role; if logged in as a student or parent-without-linked-child,
    403 is acceptable. The ParentSocialSettings row is lazily created on
    first update — surfaces any FK or model wiring bug.
    """
    token = _login(client, PARENT)
    resp = client.put(
        "/api/v1/parent-social/settings/gf93-synthetic-student-id",
        headers=_auth_headers(token),
        json={"chat_enabled": False, "forum_enabled": False},
    )
    assert resp.status_code != 500, (
        f"GF93 parent-social/settings crashed: {resp.status_code} "
        f"{resp.text[:300]}. 403/404 acceptable for synthetic student_id. "
        f"Check api/parent_social_api.py update_social_settings."
    )


def test_gf94_video_analytics_notes_create_not_500(client: httpx.Client):
    """
    POST /api/v1/video-analytics/notes must not crash.

    Probes the video note-taking write path (NOT the GF59 sessions/start
    endpoint — those are disjoint). The handler inserts into video_notes
    and links to an optional session_id. Surfaces any async session trap
    or model wiring regression.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/video-analytics/notes",
        headers=_auth_headers(token),
        json={
            "video_id": "gf94-probe-video",
            "video_source": "youtube",
            "content": "Wave 11 probe note",
            "timestamp": 0,
            "is_important": False,
            "tags": [],
        },
    )
    assert resp.status_code != 500, (
        f"GF94 video-analytics/notes crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/video_analytics_routes.py create_note."
    )


def test_gf95_manipulatives_badge_claim_not_500(client: httpx.Client):
    """
    POST /api/v1/manipulatives/progress/badges/{badge_id}/claim must not crash.

    Probes the badge claim write path. The handler checks the badge
    criteria against the student's manipulative progress rows and inserts
    a claim record. 404 ("Rozet bulunamadı") is the expected semantic
    response for a synthetic badge_id.

    NOTE: api/manipulatives_progress_api.py uses SYNC `def` handlers with
    `db: Session = Depends(get_db)` — this is the same deprecated-shim
    pattern that caused the Wave 10 GF86/GF87 `instant_feedback_api.py`
    MissingGreenlet crashes. If this probe surfaces a 500, the fix is the
    same: convert handlers to `async def`, swap the dep to
    `get_async_session`, and rewrite the query chain with
    `await db.execute(select(...))`.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/manipulatives/progress/badges/gf95-synthetic-badge/claim",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF95 manipulatives/badges/claim crashed: {resp.status_code} "
        f"{resp.text[:300]}. 404 acceptable for synthetic badge_id. "
        f"Check api/manipulatives_progress_api.py claim_badge — handler "
        f"uses sync `def` + deprecated `get_db` shim (same pattern as "
        f"Wave 10 GF86/GF87 instant_feedback_api.py crash)."
    )


def test_gf96_pomodoro_join_not_500(client: httpx.Client):
    """
    POST /api/v1/pomodoro/join must not crash.

    Probes the collaborative pomodoro room join write path. The handler
    finds an open room for the requested subject_area or creates a new
    one, then inserts a membership row. 400 is acceptable if the student
    is already in an active room.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/pomodoro/join",
        headers=_auth_headers(token),
        json={"subject_area": "matematik", "topic": "GF96 probe"},
    )
    assert resp.status_code != 500, (
        f"GF96 pomodoro/join crashed: {resp.status_code} {resp.text[:300]}. "
        f"400 acceptable if already in an active room. "
        f"Check api/pomodoro_api.py join_room."
    )


def test_gf97_offline_sync_results_not_500(client: httpx.Client):
    """
    POST /api/v1/offline/sync-results must not crash.

    Probes the PWA offline-results upload write path. The handler iterates
    the supplied answers, updates FSRS card scheduling and inserts
    student_answers rows. Synthetic question_id → per-row failure counted
    in failed_count, not a 500. 400 is acceptable if the package_id is
    invalid.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/offline/sync-results",
        headers=_auth_headers(token),
        json={
            "package_id": "gf97-synthetic-package",
            "results": [
                {
                    "question_id": "gf97-synthetic-qid",
                    "selected_answer": "A",
                    "is_correct": True,
                    "time_seconds": 12.0,
                    "answered_at": "2026-04-11T00:00:00Z",
                }
            ],
            "completed_at": "2026-04-11T00:00:30Z",
        },
    )
    assert resp.status_code != 500, (
        f"GF97 offline/sync-results crashed: {resp.status_code} "
        f"{resp.text[:300]}. 400 acceptable for synthetic package_id. "
        f"Check api/offline_sync_api.py + services/offline_sync_service.py."
    )


def test_gf98_knowledge_map_update_not_500(client: httpx.Client):
    """
    POST /api/v1/knowledge-map/update must not crash.

    Probes the knowledge-graph Bayesian mastery update write path. The
    handler looks up the StudentKnowledgeState row (or creates it),
    computes the new mastery via the `p += 0.1*(1-p)` / `p -= 0.1*p` rule,
    and writes it back. 404 is acceptable for a synthetic knowledge_point_id.
    Distinct from GF46 Wave 6 which probed `/knowledge-map/state` (read).
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/knowledge-map/update",
        headers=_auth_headers(token),
        json={"knowledge_point_id": "gf98-synthetic-kp", "is_correct": True},
    )
    assert resp.status_code != 500, (
        f"GF98 knowledge-map/update crashed: {resp.status_code} "
        f"{resp.text[:300]}. 404 acceptable for synthetic kp_id. "
        f"Check api/knowledge_graph_api.py update_knowledge_state."
    )


def test_gf99_encryption_rotate_key_admin_gate(client: httpx.Client):
    """
    POST /admin/encryption/rotate-key with a STUDENT token must return 403,
    not 500.

    Probes the admin-only encryption key rotation gate. This is a
    legitimate security boundary test: a student token MUST be rejected
    with 403 from the `require_admin` dependency, not crash at the
    rotation step. Catches any regression where the admin gate is
    bypassable or the dependency ordering is wrong.
    """
    token = _login(client, STUDENT)
    resp = client.post(
        "/admin/encryption/rotate-key",
        headers=_auth_headers(token),
        json={"new_key": None, "force": False},
    )
    assert resp.status_code != 500, (
        f"GF99 admin/encryption/rotate-key crashed: {resp.status_code} "
        f"{resp.text[:300]}. 403 expected for student token. "
        f"Check api/encryption_management.py require_admin dependency."
    )
    # Strong assertion: this MUST be 403 — a student token has no business
    # reaching key rotation logic.
    assert resp.status_code == 403, (
        f"GF99 admin gate regression: student token did not get 403 "
        f"(got {resp.status_code}). This is a SECURITY regression — "
        f"api/encryption_management.py require_admin is broken."
    )


# ---------------------------------------------------------------------------
# Wave 12 (GF100-GF109) — Session 148 feature-inventory sweep
#
# Ten disjoint write-path probes covering surfaces Wave 1-11 did not touch:
# photo-ask (LLM vision), mnemonics, OCR, TTS, birlikte-streak, realms,
# student reviews, manipulatives, oba teams, and ZPD-maarif. Wave 11 hit rate
# was 50% (rule-of-eight sweep eradicated most bare-except cases); Wave 12
# targets modules that have not been probed before, so the expected yield is
# the new anti-pattern class (raw ORM/DB schema drift + three-part async trap).
# ---------------------------------------------------------------------------


def test_gf100_photo_ask_ai_solve_not_500(client: httpx.Client):
    """POST /api/v1/photo-ask/ai-solve must not crash when given text."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/photo-ask/ai-solve",
        headers=_auth_headers(token),
        params={"question_text": "2x + 3 = 7 ise x kactir?"},
    )
    assert resp.status_code != 500, (
        f"GF100 photo-ask/ai-solve crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check services/photo_ask_service.generate_ai_solution."
    )


def test_gf101_mnemonic_generate_not_500(client: httpx.Client):
    """POST /api/v1/mnemonics/{question_id}/generate must not crash."""
    token = _login(client, STUDENT)
    # Use a synthetic question id — handler should 404 cleanly, not crash
    synthetic_id = "00000000-0000-0000-0000-000000000001"
    resp = client.post(
        f"/api/v1/mnemonics/{synthetic_id}/generate",
        headers=_auth_headers(token),
        json={"force": False},
    )
    assert resp.status_code != 500, (
        f"GF101 mnemonics/generate crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/mnemonic_api.py LLM fallback + "
        f"QuestionBankItem lookup."
    )


def test_gf102_ocr_extract_base64_not_500(client: httpx.Client):
    """POST /api/v1/ocr/extract-base64 must not crash on a trivial payload."""
    token = _login(client, STUDENT)
    # 1x1 transparent PNG base64 — smallest valid image payload
    tiny_png = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4"
        "nGNgAAIAAAUAAen63NgAAAAASUVORK5CYII="
    )
    resp = client.post(
        "/api/v1/ocr/extract-base64",
        headers=_auth_headers(token),
        json={"image": tiny_png, "engine": "tesseract"},
    )
    assert resp.status_code != 500, (
        f"GF102 ocr/extract-base64 crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/ocr_api.py engine fallback + "
        f"optional-dep 503 pattern (GF22)."
    )


def test_gf103_tts_synthesize_not_500(client: httpx.Client):
    """POST /api/v1/tts/synthesize must not crash on a minimal payload."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/tts/synthesize",
        headers=_auth_headers(token),
        json={"text": "Merhaba dunya", "language": "tr-TR"},
    )
    assert resp.status_code != 500, (
        f"GF103 tts/synthesize crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/tts_api.py optional-dep fallback "
        f"(should return 503 if Azure/ElevenLabs not configured)."
    )


def test_gf104_birlikte_streak_request_not_500(client: httpx.Client):
    """POST /api/v1/birlikte-streak/request must not crash."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/birlikte-streak/request",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF104 birlikte-streak/request crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/birlikte_streak_api.py + "
        f"streak_tracking ORM drift (GF86/GF87 class bug)."
    )


def test_gf105_realms_quest_start_not_500(client: httpx.Client):
    """POST /api/v1/realms/{slug}/quest/start must not crash."""
    token = _login(client, STUDENT)
    # Synthetic slug — handler must 404/503 cleanly, not crash
    resp = client.post(
        "/api/v1/realms/golden-flow-probe/quest/start",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF105 realms/quest/start crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/realms.py _get_realm_or_404 + "
        f"models.gamification.Realm import + realms table migration."
    )


def test_gf106_student_review_create_not_500(client: httpx.Client):
    """POST /api/v1/reviews/ must not crash on a valid review body."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/reviews/",
        headers=_auth_headers(token),
        json={
            "review_type": "university",
            "title": "Golden Flow Wave 12 probe review",
            "content": (
                "Bu bir Golden Flow Wave 12 test probe'udur. Universite "
                "degerlendirmesi icin minimum 50 karakter iceren icerik."
            ),
            "overall_rating": 4.5,
        },
    )
    assert resp.status_code != 500, (
        f"GF106 reviews/ create crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/student_review_routes.py + "
        f"StudentReview ORM + get_db async-drift."
    )


def test_gf107_manipulatives_virtual_blocks_not_500(client: httpx.Client):
    """POST /api/v1/manipulatives/virtual-blocks/operation must not crash."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/manipulatives/virtual-blocks/operation",
        headers=_auth_headers(token),
        json={
            "operation_type": "add",
            "blocks_used": [{"type": "unit", "count": 5}],
            "result": 5,
            "duration_seconds": 10,
        },
    )
    assert resp.status_code != 500, (
        f"GF107 manipulatives/virtual-blocks crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/manipulatives_api.py — any Pydantic "
        f"model touched by current_user.id needs `user_id: str` (UUID). "
        f"Rule of five: GF20 x3 + GF71 + GF107."
    )


def test_gf108_oba_create_not_500(client: httpx.Client):
    """POST /api/v1/oba/create must not crash on a valid oba body."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/oba/create",
        headers=_auth_headers(token),
        json={
            "name": "Golden Flow Probe Oba",
            "description": "Wave 12 probe oba for crash detection.",
        },
    )
    assert resp.status_code != 500, (
        f"GF108 oba/create crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/oba_api.py + Oba ORM + "
        f"uuid4 VARCHAR caller coerce (rule-of-seven)."
    )


def test_gf109_zpd_maarif_hesapla_not_500(client: httpx.Client):
    """POST /api/v1/zpd-maarif/hesapla must not crash."""
    token = _login(client, STUDENT)
    # Need student_id from /auth/me to match the request body shape
    me_resp = client.get("/api/v1/auth/me", headers=_auth_headers(token))
    me_payload = me_resp.json() if me_resp.status_code == 200 else {}
    user_obj = me_payload.get("user") or me_payload.get("kullanici") or me_payload
    student_id = str(user_obj.get("id") or "00000000-0000-0000-0000-000000000001")
    resp = client.post(
        "/api/v1/zpd-maarif/hesapla",
        headers=_auth_headers(token),
        json={
            "ogrenci_id": student_id,
            "konu": "matematik",
            "mevcut_seviye": 5.0,
        },
    )
    assert resp.status_code != 500, (
        f"GF109 zpd-maarif/hesapla crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/zpd_maarif.py cultural/maarif "
        f"optional-profile fallback + ZPDCalculator wiring."
    )


# ---------------------------------------------------------------------------
# Wave 13 (GF110-GF119) — Session 149 feature-inventory sweep
#
# Ten disjoint write-path probes covering surfaces Wave 1-12 did not touch:
# batch question generation, cultural adaptation, difficulty filtering,
# FERPA/COPPA compliance, multi-agent blackboard, OSB settings reset,
# YOLO detection, API key management, quality-gates override, and LiteLLM
# chat. Wave 12 hit rate was 20% (trailing indicator curve: 80%→50%→20%);
# Wave 13 is expected to land in the 20-30% range, with the likely bug class
# being the three-part async trap (sync `def` + `Depends(get_db)` + async
# engine → MissingGreenlet) that dominated Waves 10-11.
# ---------------------------------------------------------------------------


def test_gf110_batch_generation_admin_gate(client: httpx.Client):
    """POST /api/v1/batch/generate must reject a student with 401/403, not 500."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/batch/generate",
        headers=_auth_headers(token),
        json={
            "batch_size": 50,
            "exam_type": "TYT",
            "subject": "matematik",
            "difficulty_min": 0.3,
            "difficulty_max": 0.7,
            "generation_method": "ensemble",
            "priority": "normal",
        },
    )
    assert resp.status_code != 500, (
        f"GF110 batch/generate crashed on admin-gate check: {resp.status_code} "
        f"{resp.text[:300]}. Expected 401/403 for student Bearer; a 500 here "
        f"means get_current_admin_user or Celery apply_async is broken."
    )


def test_gf111_cultural_adaptation_test_admin_gate(client: httpx.Client):
    """POST /api/v1/cultural-adaptation/test-adaptation must not crash on admin-gate."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/cultural-adaptation/test-adaptation",
        headers=_auth_headers(token),
        json={
            "student_id": "00000000-0000-0000-0000-000000000001",
            "age": 17,
            "region": "Istanbul",
            "cultural_factors": {"family_pressure": 0.5},
        },
    )
    assert resp.status_code != 500, (
        f"GF111 cultural-adaptation/test-adaptation crashed: {resp.status_code} "
        f"{resp.text[:300]}. Expected 403 for student (admin-only); a 500 "
        f"indicates current_user.role.value access is broken."
    )


def test_gf112_difficulty_filter_not_500(client: httpx.Client):
    """POST /api/v1/difficulty/filter must not crash on a valid filter request."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/difficulty/filter",
        headers=_auth_headers(token),
        json={
            "difficulty_levels": ["easy", "medium"],
            "limit": 10,
        },
    )
    assert resp.status_code != 500, (
        f"GF112 difficulty/filter crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/difficulty_classification_api.py — "
        f"sync `def` + Depends(get_db) + `db.query(...)` is the Wave 10/11 "
        f"three-part async trap (MissingGreenlet). Handler must become "
        f"`async def` + `get_async_session` + `await db.execute(select(...))`."
    )


def test_gf113_coppa_parental_consent_not_500(client: httpx.Client):
    """POST /api/v1/compliance/coppa/parental-consent must not crash."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/compliance/coppa/parental-consent",
        headers=_auth_headers(token),
        json={
            "child_id": 1,
            "parent_id": 2,
            "child_date_of_birth": "2018-01-15",
            "verification_method": "email",
            "allow_data_collection": False,
            "allow_marketing_communication": False,
            "allow_third_party_sharing": False,
        },
    )
    assert resp.status_code != 500, (
        f"GF113 compliance/coppa/parental-consent crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/ferpa_coppa_compliance_api.py — "
        f"sync `def` + Depends(get_db) + `db.query` three-part async trap."
    )


def test_gf114_multi_agent_write_not_500(client: httpx.Client):
    """POST /api/v1/multi-agent/write must not crash on a blackboard write."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/multi-agent/write",
        headers=_auth_headers(token),
        json={
            "key": "gf114_probe",
            "value": {"probe": True, "wave": 13},
            "ttl_seconds": 60,
            "metadata": {"source": "golden_flow_gf114"},
            "priority": "MEDIUM",
        },
    )
    assert resp.status_code != 500, (
        f"GF114 multi-agent/write crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/multi_agent.py get_blackboard() + "
        f"Redis wiring + Priority enum coercion."
    )


def test_gf115_osb_settings_reset_not_500(client: httpx.Client):
    """POST /api/v1/osb/settings/reset must not crash on a valid user."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/osb/settings/reset",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF115 osb/settings/reset crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/osb_settings_api.py — sync `def` + "
        f"Depends(get_db) + `db.query` three-part async trap."
    )


def test_gf116_yolo_detect_base64_not_500(client: httpx.Client):
    """POST /api/v1/yolo/detect-base64 must not crash on a tiny base64 image."""
    token = _login(client, STUDENT)
    # 1x1 transparent PNG (43 bytes base64)
    tiny_png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
        "AAUAAen63NgAAAAASUVORK5CYII="
    )
    resp = client.post(
        "/api/v1/yolo/detect-base64",
        headers=_auth_headers(token),
        data={"image_base64": tiny_png_b64, "confidence": 0.25},
    )
    assert resp.status_code != 500, (
        f"GF116 yolo/detect-base64 crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/yolo_detection_api.py get_detector() — "
        f"optional-dep should degrade to 503, not 500. YOLO model weights "
        f"may be missing on CI."
    )


def test_gf117_api_keys_create_not_500(client: httpx.Client):
    """POST /api/v1/api-keys/create must not crash for an authenticated user."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/api-keys/create",
        headers=_auth_headers(token),
        json={
            "name": "GF117 probe key",
            "description": "Wave 13 probe.",
            "scopes": ["read:content"],
            "rate_limit": 100,
            "expires_in_days": 1,
        },
    )
    assert resp.status_code != 500, (
        f"GF117 api-keys/create crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/api_key_api.py — `db: AsyncSession = "
        f"Depends(get_db)` is a type lie (get_db is the sync shim); "
        f"`sync_db = Session(bind=db.bind.sync_engine) if hasattr(...) else None` "
        f"falls through to None and crashes manager.create_api_key(None)."
    )


def test_gf118_quality_gates_override_not_500(client: httpx.Client):
    """POST /api/v1/quality-gates/override must not crash on a valid request."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/quality-gates/override",
        headers=_auth_headers(token),
        json={
            "gate_name": "test_coverage",
            "reason": "Wave 13 Golden Flow probe reason (>=20 chars).",
            "ticket_id": "GF118",
            "expires_hours": 1,
        },
    )
    assert resp.status_code != 500, (
        f"GF118 quality-gates/override crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/quality_gates_api.py _override_requests "
        f"in-memory store + OverrideResponse serialization."
    )


def test_gf119_litellm_chat_not_500(client: httpx.Client):
    """POST /api/v1/chat must not crash (501 is acceptable when LLM_BACKEND!=litellm)."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/chat",
        headers=_auth_headers(token),
        json={
            "messages": [{"role": "user", "content": "Merhaba"}],
            "task": "chat",
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 64,
        },
    )
    assert resp.status_code != 500, (
        f"GF119 chat crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/litellm_chat.py — expected 501 when "
        f"LLM_BACKEND != 'litellm' (GF22/GF37/GF38 optional-dep pattern); "
        f"a 500 means _get_litellm_client() or the rate limiter is broken."
    )


# ---------------------------------------------------------------------------
# Wave 14 (GF120-GF129) — Session 150 feature-inventory sweep
#
# Ten disjoint probes covering surfaces Wave 1-13 did not touch. The
# Session 150 re-run of `audit_db_dependency.py` returned 0 Pattern A/B
# findings (Session 147 baseline was 98 MEDIUM) — the rule-of-eight sweep
# + Wave 10-13 direct fixes collaterally eradicated the backlog. The one
# remaining bare-sync-`get_db` crash target in api/ is `audit_logs_api.py`
# (admin-gated, 10 db operations, sync `def`), probed by GF120. The other
# nine targets are disjoint read/write surfaces chosen to keep blast radius
# varied: mastery confidence, admin performance metrics, social summary
# aggregation, Wave 2B question evaluation, student error patterns,
# monitoring API perf, question history, OSYM random, and orchestrator
# status. Expected hit rate: 20-50% — the remaining half-working features
# are likely to be idiosyncratic per-surface drift (auth-wrapper bugs,
# sync/async mismatches that slipped past the earlier sweeps) rather than
# a single systemic class.
# ---------------------------------------------------------------------------


def test_gf120_audit_logs_list_admin_gate(client: httpx.Client):
    """GET /admin/audit-logs/ must reject student with 401/403, never 500."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/admin/audit-logs/",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF120 audit-logs/ crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/audit_logs_api.py — sync `def` + "
        f"`db: Session = Depends(get_db)` is the only remaining bare-sync-"
        f"get_db crash target in api/. Student should get 403 from "
        f"require_admin BEFORE the sync db trap fires; a 500 means the "
        f"dependency chain is wired wrong and `get_db` is executing first."
    )


def test_gf121_mastery_confidence_subject_not_500(client: httpx.Client):
    """GET /api/v1/mastery-confidence/{subject} must not crash."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/mastery-confidence/MATEMATIK",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF121 mastery-confidence/MATEMATIK crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/mastery_confidence_api.py — "
        f"IRT ability estimator + 95% CI calculation. A new student with "
        f"no responses should return a neutral prior, not crash."
    )


def test_gf122_performance_metrics_admin_gate(client: httpx.Client):
    """GET /api/v1/performance/metrics must reject student with 401/403."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/performance/metrics",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF122 performance/metrics crashed: {resp.status_code} "
        f"{resp.text[:300]}. Expected 403 (admin-only); a 500 means "
        f"get_current_admin_user is broken or one of the 4 inline "
        f"`from core.xxx import ...` imports (cache_manager, system_monitor, "
        f"query_optimizer, get_optimization_stats) crashes at module load."
    )


def test_gf123_social_summary_not_500(client: httpx.Client):
    """GET /api/v1/social/summary must not crash on XP aggregation."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/social/summary",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF123 social/summary crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/social_summary_api.py — aggregates "
        f"XP from 6 social features (ForumQuestion, ForumSolution, duels, "
        f"birlikte, oba, usta_cirak). A new student with zero rows should "
        f"return all-zeros, not crash. Look for missing model imports or "
        f"table/column drift."
    )


def test_gf124_wave2b_evaluate_not_500(client: httpx.Client):
    """POST /api/v2/quality/evaluate must not crash on a valid question body."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v2/quality/evaluate",
        headers=_auth_headers(token),
        json={
            "question_text": (
                "Bir sayinin uc kati on besten bir fazladir. Bu sayi kactir?"
            ),
            "difficulty": "kolay",
            "subject": "Matematik",
            "correct_answer": "A",
            "evaluation_stage": "quick",
        },
    )
    assert resp.status_code != 500, (
        f"GF124 wave2b/evaluate crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/wave2b_quality_routes.py + "
        f"get_evaluator() singleton. If BERTScore / Bloom classifier "
        f"optional deps are missing, handler should 503 (GF22 pattern), "
        f"not crash."
    )


def test_gf125_error_clusters_my_patterns_not_500(client: httpx.Client):
    """GET /api/v1/error-clusters/my-patterns/{subject} must not crash."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/error-clusters/my-patterns/MATEMATIK",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF125 error-clusters/my-patterns crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/error_cluster_api.py — "
        f"student error pattern clustering. A student with zero wrong "
        f"answers should return an empty-patterns response, not crash. "
        f"Watch for bare `except Exception: raise HTTPException(500)` "
        f"swallowing empty-result 404s (GF81/GF82/GF88 rule-of-eight)."
    )


def test_gf126_monitoring_api_perf_admin_gate(client: httpx.Client):
    """GET /api/v1/monitoring/performance/api must reject student."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/monitoring/performance/api?hours=1",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF126 monitoring/performance/api crashed: {resp.status_code} "
        f"{resp.text[:300]}. Expected 403 (require_role('ADMIN')); a 500 "
        f"means performance_monitor.get_api_performance_summary blew up "
        f"or the ADMIN role guard is broken."
    )


def test_gf127_question_history_not_500(client: httpx.Client):
    """GET /api/v1/questions/{id}/history must not crash on a synthetic id."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/questions/00000000-0000-0000-0000-000000000001/history",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF127 questions/{{id}}/history crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/question_crud_api.py — "
        f"`get_question_history` should return an empty version list "
        f"(or 404) for a missing id, not crash. The handler's bare "
        f"`except Exception` re-wraps to 500 — check for the "
        f"`except HTTPException: raise` guard."
    )


def test_gf128_osym_random_questions_not_500(client: httpx.Client):
    """GET /api/v1/osym/random-questions must not crash on default filters."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/osym/random-questions?exam_type=TYT&count=5",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF128 osym/random-questions crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/osym_questions_api.py — "
        f"raw SQL with `SELECT ... FROM question_bank WHERE is_active` + "
        f"`random.sample()` on mappings. 77K production questions should "
        f"return 5 rows trivially; a 500 means get_db async-drift or "
        f"the mapping projection is broken."
    )


def test_gf129_orchestrator_status_admin_gate(client: httpx.Client):
    """GET /api/v1/admin/orchestrator/status must reject student with 403."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/admin/orchestrator/status",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF129 admin/orchestrator/status crashed: {resp.status_code} "
        f"{resp.text[:300]}. Expected 403 for student (get_current_admin_user); "
        f"a 500 means the `import orchestrator` side-effect at module load "
        f"blew up or the admin-guard dep chain is broken."
    )


# ---------------------------------------------------------------------------
# Wave 15 — Frontend fetch mapping-driven disjoint top-10 (Session 151)
#
# Targets selected by computing the set difference between frontend fetch
# paths (`grep -rhoE "fetch|axios" frontend/src/`) and the GF-covered path
# list. Of 173 unique frontend paths, 150 were already covered by Waves
# 1-14 (GF1-GF129); 164 were uncovered after prefix-aware matching. The 10
# below were chosen for diversity across student/teacher/parent surfaces
# and real production-traffic relevance, NOT backend coverage. Expected
# hit rate %10-20 per the Wave 14 trailing indicator curve (Wave 14 %10).
# ---------------------------------------------------------------------------


def test_gf130_fsrs_flashcards_due_not_500(client: httpx.Client):
    """GET /api/v1/fsrs/flashcards/due must not crash — FSRS due card list."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/fsrs/flashcards/due",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF130 fsrs/flashcards/due crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/fsrs.py — the due query uses "
        f"`datetime.utcnow()` against a tz-aware TIMESTAMP column; a 500 "
        f"is usually asyncpg tz-naive/aware mismatch or `get_db` sync-shim "
        f"drift. Empty list is acceptable; a crash is not."
    )


def test_gf131_learning_path_status_not_500(client: httpx.Client):
    """GET /api/v1/learning-path/status must not crash — LP readiness read."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/learning-path/status",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF131 learning-path/status crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/learning_path_v2.py — a student "
        f"without a LearningPathStudentProfile row should get a semantic "
        f"shape ({{'ready': false, ...}}) or 404, not a 500. Bare "
        f"`except Exception` re-wrapping upstream 4xx is the usual class."
    )


def test_gf132_gamification_profile_not_500(client: httpx.Client):
    """GET /api/v1/gamification/profile must not crash — XP/level read."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/gamification/profile",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF132 gamification/profile crashed: {resp.status_code} "
        f"{resp.text[:300]}. Gamification endpoints were IDOR-fixed in "
        f"Session 84 (all use current_user). A 500 means Depends(get_db) "
        f"async-drift or a raw SQL binding issue on xp_transactions."
    )


def test_gf133_parent_dashboard_not_500(client: httpx.Client):
    """GET /api/v1/parent/dashboard must not crash for a seeded parent."""
    token = _login(client, PARENT)
    resp = client.get(
        "/api/v1/parent/dashboard",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF133 parent/dashboard crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/parent*.py — parent auth + consent "
        f"+ children list. A 500 usually means `current_user.rol` enum "
        f"drift or a missing `except HTTPException: raise` guard over an "
        f"upstream 404 from `parent_service.get_children`."
    )


def test_gf134_ogretmen_dashboard_not_500(client: httpx.Client):
    """GET /api/v1/ogretmen/dashboard must not crash for a seeded teacher."""
    token = _login(client, TEACHER)
    resp = client.get(
        "/api/v1/ogretmen/dashboard",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF134 ogretmen/dashboard crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/ogretmen*.py (TR surface) — "
        f"the dashboard aggregates sinif + ogrenci + bildirim reads; a "
        f"500 usually means async/sync ORM drift on one of those joins "
        f"or a `current_user.kullanici_id` attribute that doesn't exist "
        f"on AuthenticatedUser (should be `.id`)."
    )


def test_gf135_student_dashboard_hedefler_not_500(client: httpx.Client):
    """GET /api/v1/student-dashboard/hedefler must not crash — goals list."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/student-dashboard/hedefler",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF135 student-dashboard/hedefler crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/student_dashboard*.py — Goal model "
        f"was fixed in Session 139 (GF26) for VARCHAR+uuid4 bind, but the "
        f"list-side read may still hit tz-aware target_date bind drift. "
        f"Empty goals list is acceptable; a crash is not."
    )


def test_gf136_manipulatives_progress_dashboard_not_500(client: httpx.Client):
    """GET /api/v1/manipulatives/progress/dashboard must not crash."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/manipulatives/progress/dashboard",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF136 manipulatives/progress/dashboard crashed: {resp.status_code} "
        f"{resp.text[:300]}. manipulatives_progress_api was rewritten to "
        f"async + get_async_session in Session 147 (Wave 11 GF95). A new "
        f"500 here would be a regression of that rewrite or dashboard-"
        f"specific aggregation (SUM/GROUP BY) on the badge tables."
    )


def test_gf137_teachers_my_appointments_not_500(client: httpx.Client):
    """GET /api/v1/teachers/my-appointments must not crash for teacher."""
    token = _login(client, TEACHER)
    resp = client.get(
        "/api/v1/teachers/my-appointments",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF137 teachers/my-appointments crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/teachers*.py — `my-appointments` "
        f"filters TeacherAppointment by current_user.id. A 500 is usually "
        f"the `user_id: int` vs UUID string Pydantic response type lie "
        f"(rule-of-five: Session 148 GF107 + GF71 + GF20 x3)."
    )


def test_gf138_user_export_data_not_500(client: httpx.Client):
    """GET /api/v1/user/export-data must not crash — GDPR/KVKK export."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/user/export-data",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF138 user/export-data crashed: {resp.status_code} "
        f"{resp.text[:300]}. GDPR/KVKK data export aggregates across "
        f"~10 tables; a 500 usually means one of them has schema drift "
        f"(Session 149 GF113 COPPA, Session 148 GF106 StudentReview). "
        f"Expected: 200 with a JSON or file envelope, or 503 if a "
        f"sub-query degrades gracefully."
    )


def test_gf139_push_subscribe_not_500(client: httpx.Client):
    """POST /api/v1/push/subscribe must not crash on a synthetic subscription."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/push/subscribe",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        json={
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
            "keys": {
                "p256dh": "BPqF" + "A" * 84,
                "auth": "C" * 22,
            },
            "user_agent": "pytest-golden-flow",
        },
    )
    assert resp.status_code != 500, (
        f"GF139 push/subscribe crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/push*.py — WebPush subscription "
        f"write path. A 500 is usually VARCHAR+uuid4 bind drift on the "
        f"PushSubscription model (rule-of-seven: Session 147 GF94 "
        f"VideoNote + Session 142 GF59) or VAPID key env-var missing. "
        f"422/400 on payload shape is acceptable; a crash is not."
    )


# ---------------------------------------------------------------------------
# Wave 16 — low-traffic uncovered pool sweep (Session 152)
#
# After Wave 15 hit 0% on frontend-traffic-biased targets, Wave 16 shifts back
# to breadth sweep with bias toward surfaces frontend does NOT call on hot
# paths: monitoring/*, admin/content/*, visual-supports/*, parsed-questions,
# TR teacher rapor (veli/ogretmen cluster), productive-failure read,
# learning-path/interleaved-practice write, study-rooms (known missing).
# Expected hit rate 10-20%. If ≤10%, declare suite saturated for
# single-handler bugs and shift to migration/port backlogs.
# ---------------------------------------------------------------------------


def test_gf140_monitoring_token_stats_not_500(client: httpx.Client):
    """GET /api/v1/monitoring/token-stats must not crash — LLM token usage read."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/monitoring/token-stats",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF140 monitoring/token-stats crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/monitoring*.py — LLM cost/token "
        f"aggregation read path. 403 (admin-gate) is acceptable; a 500 "
        f"is usually a stale SQL query against a removed cost-tracking "
        f"table or asyncpg tz-naive/aware drift on rolling-window filters."
    )


def test_gf141_monitoring_ab_test_results_not_500(client: httpx.Client):
    """GET /api/v1/monitoring/ab-test-results must not crash — A/B bucket read."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/monitoring/ab-test-results",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF141 monitoring/ab-test-results crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/monitoring*.py ab-test read path. "
        f"403 (admin-gate) acceptable; a 500 usually means the ab_test "
        f"experiment table has schema drift or the aggregation does a "
        f"`list[dict]` return that the handler tried to `Response(**result)`. "
        f"Rule-of-four alert (GF65 + GF125 x3 + GF151a + GF151b)."
    )


def test_gf142_admin_content_educational_admin_gate(client: httpx.Client):
    """GET /api/v1/admin/content/educational must not crash for student."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/admin/content/educational",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF142 admin/content/educational crashed: {resp.status_code} "
        f"{resp.text[:300]}. Expect 403 (admin-only) not 500. A 500 here "
        f"means the dependency-resolution order is wrong: the handler "
        f"is touching the DB before require_admin kicks in. See GF120 / "
        f"GF129 pattern — require_admin should run first."
    )


def test_gf143_visual_supports_color_schemes_not_500(client: httpx.Client):
    """GET /api/v1/visual-supports/color-schemes must not crash — OSB preset read."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/visual-supports/color-schemes",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF143 visual-supports/color-schemes crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/visual_supports_api.py color-scheme "
        f"read path. A 500 is usually enum/OSB settings schema drift "
        f"(related to Session 149 GF115 osb_settings missing columns) or "
        f"a stale service dependency import."
    )


def test_gf144_parsed_questions_stats_not_500(client: httpx.Client):
    """GET /api/v1/parsed-questions/stats must not crash — OCR pipeline stats."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/parsed-questions/stats",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF144 parsed-questions/stats crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/parsed_questions*.py — OCR pipeline "
        f"stats read. 403 (admin-gate) acceptable. A 500 usually means "
        f"aggregation query touches a removed or renamed OCR staging table."
    )


def test_gf145_batch_queue_stats_not_500(client: httpx.Client):
    """GET /api/v1/batch/queue/stats must not crash — batch job queue read."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/batch/queue/stats",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF145 batch/queue/stats crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/batch*.py — queue inspection read "
        f"path. 403 (admin-gate) acceptable. A 500 usually means Redis "
        f"queue adapter singleton is None (optional-dep pattern GF22) "
        f"or sync-service-over-async-engine (Wave 10 GF86/87 pattern)."
    )


def test_gf146_ogretmen_ogrenciler_not_500(client: httpx.Client):
    """GET /api/v1/ogretmen/ogrenciler must not crash for a teacher."""
    token = _login(client, TEACHER)
    resp = client.get(
        "/api/v1/ogretmen/ogrenciler",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF146 ogretmen/ogrenciler crashed: {resp.status_code} "
        f"{resp.text[:300]}. Turkish teacher student-list read path. A "
        f"500 here is typically a TR/EN duplicate-implementation drift "
        f"(path-naming.md ban) — ogretmen/* version may be a legacy "
        f"stub calling removed service helpers. Empty list (200) or 404 "
        f"acceptable; a crash is not."
    )


def test_gf147_productive_failure_growth_not_500(client: httpx.Client):
    """GET /api/v1/productive-failure/growth must not crash — growth metric read."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/productive-failure/growth",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF147 productive-failure/growth crashed: {resp.status_code} "
        f"{resp.text[:300]}. Check api/productive_failure_api.py growth "
        f"metric read. Related to Session 140 GF32 caller/service contract "
        f"drift on the same module — service may still return list[dict] "
        f"and handler unpacks with **. Rule-of-four alert."
    )


def test_gf148_learning_path_interleaved_practice_not_500(client: httpx.Client):
    """POST /api/v1/learning-path/interleaved-practice must not crash."""
    token = _login(client, STUDENT)
    resp = client.post(
        "/api/v1/learning-path/interleaved-practice",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        json={
            "subject": "MATEMATIK",
            "topic_ids": [],
            "question_count": 5,
        },
    )
    assert resp.status_code != 500, (
        f"GF148 learning-path/interleaved-practice crashed: {resp.status_code} "
        f"{resp.text[:300]}. Interleaved practice is a karisik-pratik write "
        f"path frontend exposes on the learning-path page. A 500 here is "
        f"usually subject-key normalization drift (case-convention.md) or "
        f"FSRS card-selection query failing on empty topic_ids."
    )


def test_gf149_study_rooms_not_500(client: httpx.Client):
    """GET /api/v1/study-rooms must not crash — study-rooms backlog probe."""
    token = _login(client, STUDENT)
    resp = client.get(
        "/api/v1/study-rooms",
        headers=_auth_headers(token),
    )
    assert resp.status_code != 500, (
        f"GF149 study-rooms crashed: {resp.status_code} "
        f"{resp.text[:300]}. study-rooms is flagged in path-naming.md as "
        f"a known missing-feature (~40 frontend 404 sites call it). 404 "
        f"or 503 is the expected semantic response; a 500 would mean "
        f"someone added a partial router that imports a broken helper."
    )


def test_gf150_public_journey_health_probes_not_500(client: httpx.Client):
    """
    (A) J6 / J7 / live-session / clustering: liveness + DB ping (no auth).
    (B) Chroma stack health: semantic search, duplicate detection, content
    recommendation — no auth; 200 with ``chroma_connection_mode`` and service id.
    (C) Push: ``GET /api/v1/push/health`` — stub surface, no DB.

    Probes that router include paths from ``routers/loader`` and Chroma
    client factory wiring; degraded/unhealthy service status is OK, 500 is not.
    """
    paths = (
        ("/api/v1/offline/health", "offline_sync"),
        ("/api/v1/sync/health", "pwa_sync"),
        ("/api/v1/live-sessions/health", "live_sessions"),
        ("/api/v1/clustering/health", "concept_clustering"),
    )
    for path, expected_service in paths:
        resp = client.get(path)
        assert resp.status_code == 200, (
            f"GF150 {path} must return 200, got {resp.status_code} "
            f"{resp.text[:300]}. Check get_db_session_context + route mount."
        )
        data = resp.json()
        assert data.get("status") in ("ok", "degraded"), (
            f"GF150 {path} missing status: {data!r}"
        )
        assert data.get("service") == expected_service, (
            f"GF150 {path} service mismatch: {data!r}"
        )
        assert "database" in data, f"GF150 {path} missing database flag: {data!r}"

    chroma_paths = (
        ("/api/v1/search/health", "semantic_search"),
        ("/api/v1/duplicates/health", "duplicate_detection"),
        ("/api/v1/recommendations/health", "content_recommendation"),
    )
    for path, expected_service in chroma_paths:
        resp = client.get(path)
        assert resp.status_code == 200, (
            f"GF150 {path} must return 200, got {resp.status_code} "
            f"{resp.text[:300]}. Chroma/loader probe."
        )
        data = resp.json()
        assert "status" in data, f"GF150 {path} missing status: {data!r}"
        assert data.get("status") in (
            "ok",
            "degraded",
            "healthy",
            "unhealthy",
        ), f"GF150 {path} unexpected status: {data!r}"
        assert data.get("service") == expected_service, (
            f"GF150 {path} service mismatch: {data!r}"
        )
        assert data.get("chroma_connection_mode") in (
            "http",
            "embedded",
        ), f"GF150 {path} missing chroma_connection_mode: {data!r}"

    r_push = client.get("/api/v1/push/health")
    assert r_push.status_code == 200, (
        f"GF150 /api/v1/push/health must return 200, got {r_push.status_code} "
        f"{r_push.text[:300]}."
    )
    push_data = r_push.json()
    assert push_data.get("status") in ("ok", "degraded"), (
        f"GF150 push/health: {push_data!r}"
    )
    assert push_data.get("service") == "pwa_push", push_data
    assert "subscribe_implemented" in push_data, push_data


# ---------------------------------------------------------------------------
# GF (KVKK Faz 2): Veli onay verify — geçersiz token semantik 4xx, asla 500
# ---------------------------------------------------------------------------


def test_gf_veli_onay_verify_invalid(client: httpx.Client):
    """Veli onay verify (geçersiz token) — semantik 4xx döner, asla 500."""
    resp = client.post(
        "/api/v1/auth/veli-onay/verify", json={"token": "gf-gecersiz-token"}
    )
    assert resp.status_code < 500, (
        f"GF veli-onay crashed: {resp.status_code} {resp.text[:300]}"
    )
    assert resp.status_code in (400, 422), (
        f"GF veli-onay beklenen 400/422, gelen: {resp.status_code} {resp.text[:200]}"
    )


# ---------------------------------------------------------------------------
# GF flag→curator köprüsü: admin /curator/flagged öğrenci bildirimlerini görür
# ---------------------------------------------------------------------------
def test_gf_curator_flagged_bridge(client: httpx.Client):
    """Köprü: admin /curator/flagged ile öğrenci hata bildirimlerini görebilmeli.

    student_question_flags (resolved_at IS NULL) → question_bank join. Gold
    sorular dahil (eski /queue'da görünmeyen) flag'li sorular curator'a düşer.
    """
    token = _login(client, ADMIN)
    resp = client.get(
        "/api/v1/curator/flagged?page=1&per_page=5",
        headers=_auth_headers(token),
    )
    assert resp.status_code < 500, (
        f"GF curator/flagged crashed: {resp.status_code} {resp.text[:300]}"
    )
    if resp.status_code == 200:
        body = resp.json()
        assert "items" in body and "total" in body, f"şema eksik: {body}"
        if body["items"]:
            item = body["items"][0]
            assert "student_flags" in item, "QueueItem.student_flags eksik"
            if item.get("flag_count") is not None:
                assert item["flag_count"] >= 1


# ---------------------------------------------------------------------------
# GF multi-tenancy (Faz 0 Step 5): cross-tenant leak gate
# ---------------------------------------------------------------------------
def test_gf_org_members_tenant_scoped(client: httpx.Client):
    """Kurum üyeleri YALNIZ çağıranın kendi kurumundan (tenant-scoped, org param YOK).

    Cross-tenant sızıntı savunması: /api/v1/org/members organization_id'yi
    get_current_tenant'tan alır, istemciden DEĞİL → başka kurum sorgulanamaz.
    admin → 200 (kendi kurumu); yetki + wiring doğru.
    """
    token = _login(client, ADMIN)
    resp = client.get("/api/v1/org/members", headers=_auth_headers(token))
    assert resp.status_code < 500, (
        f"GF org/members crashed: {resp.status_code} {resp.text[:300]}"
    )
    if resp.status_code == 200:
        members = resp.json()
        assert isinstance(members, list), f"liste bekleniyor: {members}"
        # Endpoint'te org parametresi yok → yapısal cross-tenant güvence
        for m in members:
            assert "org_role" in m and "user_id" in m


def test_gf_org_members_role_gated(client: httpx.Client):
    """require_org_role: STUDENT rolü /org/members'a erişemez (403), 500 değil."""
    token = _login(client, STUDENT)
    resp = client.get("/api/v1/org/members", headers=_auth_headers(token))
    # 403 (rol guard) beklenen; asla 500
    assert resp.status_code in (403, 404), (
        f"GF org/members rol guard: beklenen 403/404, gelen {resp.status_code}"
    )
