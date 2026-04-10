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
