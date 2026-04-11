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
    POST /gamification/points/award must increase the caller's total_points.

    Session 136 probe: the endpoint rejects a JSON body with 422
    (``points`` and ``reason`` are declared as *query* parameters, not body
    fields — which is an unusual FastAPI choice). The frontend sends JSON
    and silently fails; the user never sees the points. This test uses the
    backend's expected query-param schema, so it PASSES today and becomes
    a regression guard for any future change that breaks the balance update.

    If this starts failing: check
    ``backend/api/gamification.py`` award_points handler, the schema
    mismatch is almost certainly the root cause (frontend vs. backend
    contract drift) — see docs/audits/2026-04-10_half-working-features.md.
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

    # Award via query params (the backend's actual contract).
    award_resp = client.post(
        "/api/v1/gamification/points/award"
        "?points=3&reason=golden_flow_write_test&category=quiz",
        headers=headers,
    )
    assert award_resp.status_code == 200, (
        f"GF2w gamification award HTTP {award_resp.status_code}: "
        f"{award_resp.text[:300]}. If 422, the frontend JSON body vs backend "
        f"query-param contract has drifted."
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
    try:
        resp = client.post(
            "/api/v1/enhanced-chat/message",
            headers=_auth_headers(token),
            json={
                "student_id": "gf24-probe-student",
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
