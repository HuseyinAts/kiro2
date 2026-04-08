"""
WP-02: Authenticated Stub Guardrail Tests

Detects the "authenticated stub" anti-pattern:
  - Endpoint requires auth (Depends(get_current_user))
  - But returns fake/pending/hardcoded response instead of real data

Target family: Authenticated stubs that return "not yet implemented" or
fake success with no meaningful side effect.

Intentional deferred stubs (DECISION=DEFER) are exempted from failure:
  - POST /api/v1/push/subscribe — push infrastructure not in Sprint 1 scope

NOT coverage: Public ingest endpoints (telemetry, web-vitals) — those are WP-01.

Standards:
- Uses FastAPI TestClient (sync, no async hangs)
- Uses auth_headers fixture for JWT authentication
- NEVER use assert True (reward hacking prevention)
"""

from datetime import datetime

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from main import app

# Module-level engine/session maker created per test function (avoids loop conflicts)
_test_engine = None
_test_session_maker = None


@pytest_asyncio.fixture
async def db_session():
    """Function-scoped DB session — creates fresh engine per test to avoid loop conflicts."""
    global _test_engine, _test_session_maker

    import uuid

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    # Create a fresh engine for THIS test function (function-scoped event loop)
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2",
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    # Override get_db to use our engine
    from core.dependencies import get_db

    async def _override_get_db():
        async with session_maker() as sess:
            yield sess

    app.dependency_overrides[get_db] = _override_get_db

    # Check if seeding needed (use production data — already has 77K questions)
    async with session_maker() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM question_bank"))
        count = result.scalar() or 0
        if count == 0:
            # Seed minimal test data if DB is empty
            topic_id = "00000000-0000-0000-0000-000000000001"
            now = datetime.now().isoformat()
            await session.execute(
                text(
                    "INSERT INTO topic_hierarchy (id, level, code, name_tr, is_active, created_at, updated_at) "
                    "VALUES (:id, :level, :code, :name_tr, :is_active, :created_at, :updated_at)"
                ),
                {
                    "id": topic_id,
                    "level": 1,
                    "code": "TEST.MAT",
                    "name_tr": "Test Matematik Konusu",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            seed_questions = [
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "2x + 4 = 10 denkleminin cozumu nedir?",
                    "option_a": "x = 2",
                    "option_b": "x = 3",
                    "option_c": "x = 4",
                    "option_d": "x = 5",
                    "option_e": "x = 6",
                    "correct_answer": "B",
                    "exam_type": "TYT",
                    "subject_area": "MATEMATIK",
                    "difficulty_level": "easy",
                    "primary_topic_id": topic_id,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "Bir ucgenin ic acilari toplami kac derecedir?",
                    "option_a": "90",
                    "option_b": "180",
                    "option_c": "270",
                    "option_d": "360",
                    "option_e": "45",
                    "correct_answer": "B",
                    "exam_type": "TYT",
                    "subject_area": "MATEMATIK",
                    "difficulty_level": "medium",
                    "primary_topic_id": topic_id,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "log2(3x - 1) = 5 denkleminin cozum kumesi nedir?",
                    "option_a": "{11}",
                    "option_b": "{10}",
                    "option_c": "{9}",
                    "option_d": "{8}",
                    "option_e": "{7}",
                    "correct_answer": "A",
                    "exam_type": "TYT",
                    "subject_area": "MATEMATIK",
                    "difficulty_level": "hard",
                    "primary_topic_id": topic_id,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "3 carpi 4 isleminin sonucu kactir?",
                    "option_a": "10",
                    "option_b": "11",
                    "option_c": "12",
                    "option_d": "13",
                    "option_e": "14",
                    "correct_answer": "C",
                    "exam_type": "TYT",
                    "subject_area": "MATEMATIK",
                    "difficulty_level": "easy",
                    "primary_topic_id": topic_id,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "Bir dikdortgenin alani 24 cm2 ve kenar orani 3:2 ise cevresi kac cm'dir?",
                    "option_a": "20",
                    "option_b": "24",
                    "option_c": "28",
                    "option_d": "32",
                    "option_e": "36",
                    "correct_answer": "A",
                    "exam_type": "TYT",
                    "subject_area": "MATEMATIK",
                    "difficulty_level": "medium",
                    "primary_topic_id": topic_id,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                },
            ]
            for q in seed_questions:
                cols = ", ".join(q.keys())
                placeholders = ", ".join([f":{k}" for k in q.keys()])
                await session.execute(
                    text(f"INSERT INTO question_bank ({cols}) VALUES ({placeholders})"),
                    q,
                )
            await session.commit()

    # Provide session to test
    async with session_maker() as session:
        yield session

    # Cleanup
    await engine.dispose()


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


def _is_stub_response(data: dict | list) -> tuple[bool, str]:
    """Detect stub response patterns. Returns (is_stub, reason)."""
    # Direct array response = real implementation (not a stub wrapper)
    if isinstance(data, list):
        return False, ""
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


# Deferred intentional stubs — documented gaps, NOT bugs
INTENTIONAL_DEFERRED_STUBS = {
    "POST /api/v1/push/subscribe": "Phase 3 decision: push infrastructure not in Sprint 1 scope",
}


def _assert_intentional_deferred_stub(
    data: dict, endpoint: str, is_stub: bool, reason: str
) -> None:
    """
    Assert that stub behavior for a deferred endpoint is intentional.
    If is_stub=True and endpoint is NOT in INTENTIONAL_DEFERRED_STUBS, fail.
    If is_stub=False, pass silently.
    If is_stub=True and endpoint IS in INTENTIONAL_DEFERRED_STUBS, pass with no assertion.
    """
    if not is_stub:
        return
    if endpoint in INTENTIONAL_DEFERRED_STUBS:
        return  # Expected deferred stub — no assertion failure
    # Unexpected stub — fail the test
    assert not is_stub, (
        f"{endpoint} is an authenticated STUB: {reason}. Response: {data}"
    )


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
        GR-07: POST /api/v1/push/subscribe — intentionally deferred stub.
        Endpoint remains but is exempted from stub-failure because DECISION=DEFER.
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

            # DEFERRED STUB: push/subscribe is intentionally a stub (DECISION = DEFER).
            # Not a bug — known gap documented in Phase 3 audit.
            # This guardrail skips the stub check for intentional deferred endpoints.
            is_stub, reason = _is_stub_response(data)
            _assert_intentional_deferred_stub(
                data, "POST /api/v1/push/subscribe", is_stub, reason
            )

    async def test_export_user_data_not_stub_async(self, db_session):
        """
        GR-10: GET /api/v1/users/export-data must not return stub.
        Uses direct function call with real DB session (TestClient can't resolve async get_db).
        """

        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        current_user = AuthenticatedUser(
            id=1, username="testuser", role=UserRole.STUDENT, email="test@example.com"
        )

        from api.enhanced_user_management_api import export_user_data

        response = await export_user_data(
            current_user=current_user,
            db=db_session,
        )

        import json

        data = json.loads(response.body)
        is_stub, reason = _is_stub_response(data)
        assert not is_stub, (
            f"GET /api/v1/users/export-data is an authenticated STUB: {reason}. "
            f"Response: {data}"
        )
        # Verify it's a real export payload with actual user data
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        assert "user" in data, f"No 'user' section in export: {data.keys()}"
        assert data.get("user", {}).get("id") == "1", "User ID mismatch"


@pytest.mark.guardrail
class TestQuestionsDownloadContract:
    """
    Contract verification: POST /api/v1/questions/download vs OfflineQuestion interface.

    OfflineQuestion interface (offlineStorageService.ts):
      id: string
      text: string
      options: string[]          // MUST have exactly 5 elements
      correct: number             // 0-4
      subject: string             // lowercase
      difficulty: 'easy'|'medium'|'hard'
      explanation?: string
      downloadedAt: string        // ISO timestamp

    Contract rules verified:
      - top-level response is a LIST (no wrapper keys)
      - len(response) <= requested_count
      - each item has all required fields
      - options.length == 5
      - every option is a non-null, non-empty string
      - correct is integer in [0, 4]
      - subject is lowercase string
      - difficulty is in {'easy', 'medium', 'hard'}
      - downloadedAt is parseable ISO-8601
    """

    async def _call_download(self, db, subject="matematik", count=5):
        """Helper: call the download_questions endpoint function directly."""
        from unittest.mock import AsyncMock

        from core.dependencies import AuthenticatedUser
        from models.enums_db import UserRole

        # Create mock request with JSON body
        mock_request = AsyncMock()
        mock_request.json = AsyncMock(return_value={"subject": subject, "count": count})

        # Create mock authenticated user
        current_user = AuthenticatedUser(
            id=1,
            username="testuser",
            role=UserRole.STUDENT,
            email="test@example.com",
        )

        # Import and call the endpoint function directly
        from api.question_crud_api import download_questions

        return await download_questions(
            request=mock_request,
            current_user=current_user,
            db=db,
        )

    async def test_download_returns_direct_list_no_wrapper(self, db_session):
        """Response must be a direct array, not {success, data, ...}."""
        response = await self._call_download(db_session, count=5)
        # Endpoint returns JSONResponse — body is already serialized
        import json

        data = json.loads(response.body)
        assert isinstance(data, list), (
            f"Response must be a direct list, got type: {type(data).__name__}. "
            f"Response: {data}"
        )

    async def test_download_length_within_count(self, db_session):
        """len(response) must be <= requested count."""
        import json

        response = await self._call_download(db_session, count=10)
        data = json.loads(response.body)
        assert isinstance(data, list)
        assert len(data) <= 10, (
            f"Response length {len(data)} exceeds requested count 10"
        )

    async def test_download_all_required_fields_present(self, db_session):
        """Every item must have id, text, options, correct, subject, difficulty, downloadedAt."""
        import json

        REQUIRED = {
            "id",
            "text",
            "options",
            "correct",
            "subject",
            "difficulty",
            "downloadedAt",
        }
        response = await self._call_download(db_session, count=5)
        data = json.loads(response.body)
        assert isinstance(data, list) and len(data) > 0, (
            "Need at least 1 question to verify fields"
        )
        for i, item in enumerate(data):
            missing = REQUIRED - set(item.keys())
            assert not missing, (
                f"Item {i} missing required fields: {missing}. Item: {item}"
            )

    async def test_download_options_exactly_5_elements(self, db_session):
        """options must be a list of exactly 5 elements."""
        import json

        response = await self._call_download(db_session, count=5)
        data = json.loads(response.body)
        assert isinstance(data, list) and len(data) > 0
        for i, item in enumerate(data):
            opts = item.get("options")
            assert isinstance(opts, list) and len(opts) == 5, (
                f"Item {i}: options must have exactly 5 elements, got {opts}"
            )

    async def test_download_options_all_non_null_strings(self, db_session):
        """Every option in options[] must be a non-null, non-empty string."""
        import json

        response = await self._call_download(db_session, count=5)
        data = json.loads(response.body)
        assert isinstance(data, list) and len(data) > 0
        for i, item in enumerate(data):
            for j, opt in enumerate(item.get("options", [])):
                assert isinstance(opt, str) and opt.strip(), (
                    f"Item {i}, option {j}: must be non-null non-empty string, got {opt!r}"
                )

    async def test_download_correct_range(self, db_session):
        """correct must be integer in [0, 4]."""
        import json

        response = await self._call_download(db_session, count=5)
        data = json.loads(response.body)
        assert isinstance(data, list) and len(data) > 0
        for i, item in enumerate(data):
            c = item.get("correct")
            assert isinstance(c, int) and 0 <= c <= 4, (
                f"Item {i}: correct must be int in [0,4], got {c!r}"
            )

    async def test_download_subject_lowercase(self, db_session):
        """subject must be a lowercase string."""
        import json

        response = await self._call_download(db_session, count=5)
        data = json.loads(response.body)
        assert isinstance(data, list) and len(data) > 0
        for i, item in enumerate(data):
            subj = item.get("subject")
            assert isinstance(subj, str) and subj == subj.lower(), (
                f"Item {i}: subject must be lowercase string, got {subj!r}"
            )

    async def test_download_difficulty_valid_values(self, db_session):
        """difficulty must be in {'easy', 'medium', 'hard'}."""
        import json

        VALID = {"easy", "medium", "hard"}
        response = await self._call_download(db_session, count=5)
        data = json.loads(response.body)
        assert isinstance(data, list) and len(data) > 0
        for i, item in enumerate(data):
            diff = item.get("difficulty")
            assert diff in VALID, (
                f"Item {i}: difficulty must be in {VALID}, got {diff!r}"
            )

    async def test_download_timestamp_iso_parseable(self, db_session):
        """downloadedAt must be a parseable ISO-8601 string."""
        import json

        response = await self._call_download(db_session, count=5)
        data = json.loads(response.body)
        assert isinstance(data, list) and len(data) > 0
        for i, item in enumerate(data):
            ts = item.get("downloadedAt")
            assert isinstance(ts, str) and len(ts) > 0
            try:
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                pytest.fail(f"Item {i}: downloadedAt not ISO parseable: {ts!r}")

    async def test_download_no_wrapper_keys(self, db_session):
        """top-level response must not contain wrapper keys."""
        import json

        FORBIDDEN = {"success", "data", "questions", "total", "message", "error"}
        response = await self._call_download(db_session, count=5)
        data = json.loads(response.body)
        assert isinstance(data, list)
        # Only check first item for forbidden keys (whole list can't have them)
        if data:
            assert not (set(data[0].keys()) & FORBIDDEN), (
                f"Item contains wrapper keys: {set(data[0].keys()) & FORBIDDEN}"
            )

    async def test_download_questions_not_stub(self, db_session):
        """
        GR-10: POST /api/v1/questions/download must not return stub.
        Uses direct function call to avoid TestClient event-loop conflict.
        """
        import json

        response = await self._call_download(db_session, count=10)
        data = json.loads(response.body)

        is_stub, reason = _is_stub_response(data)

        assert not is_stub, (
            f"POST /api/v1/questions/download is an authenticated STUB: {reason}. "
            f"Response: {data}"
        )
