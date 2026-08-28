"""
Batch 1B-a: BKTService.record_answer() happy-path execution tests.

Scope: services/bkt_service.py — record_answer() method
Level: service-level (no API, no dependency_overrides)
DB:    real AsyncSession + PostgreSQL (function-scoped engine)
Happy-path only — error swallowing paths excluded.

Mocks:
  - FSRSService.review_card()      — patched directly
  - BlackboardService.publish_learning_event() — patched via get().publish_learning_event chain

Tests (7):
  1. first-answer INSERT   — BKTState row does not exist yet
  2. existing-state UPDATE — BKTState row exists, p_L increases on correct
  3. answered_questions    — irt_method = "eap"
  4. no answered_questions  — irt_method = "bridge" + formula verification
  5. return dict           — all 12 keys present
  6. BKTState persistence  — flush → same-session SELECT → commit → fresh requery
  7. StudentAbility upsert  — flush → same-session SELECT → commit → fresh requery
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.bkt_service import BKTService

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEST_TOPIC_ID = "00000000-0000-0000-0000-000000000001"
# Real user in DB — satisfies FK constraints on REAL_USER_ID
REAL_USER_ID = "41411c25-5c85-4470-a6ac-ac31c60ce732"
DB_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5434/kiro2"

# FSRS mock return
_FSRS_MOCK_RETURN = {
    "stability": 1.0,
    "difficulty": 0.5,
    "due_date": datetime.now(UTC),
    "state": "new",
    "reps": 1,
    "lapses": 0,
}

# Blackboard mock: patch at source import location, not at bkt_service module
# BlackboardService.get() is called inside record_answer (line 439 of bkt_service.py)
# so we patch BlackboardService.get to return our mock
_blackboard_mock_instance = AsyncMock(
    publish_learning_event=AsyncMock(return_value="msg_id_mock")
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session():
    """Function-scoped async engine — no dependency_overrides.

    Creates a fresh engine per test to avoid connection-reuse conflicts.
    Yields an AsyncSession; on exit the engine is disposed.
    """
    engine = create_async_engine(
        DB_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Clean up any leftover test data for this user before each test
    async with session_maker() as session:
        for table in ["bkt_states", "student_abilities", "zpd_history", "fsrs_cards"]:
            await session.execute(
                text(f"DELETE FROM {table} WHERE student_id = :sid"),
                {"sid": REAL_USER_ID},
            )
        await session.commit()

    async with session_maker() as session:
        # Ensure org_legacy_default exists in organizations table
        await session.execute(
            text("""
                INSERT INTO organizations (id, name, created_at, updated_at)
                VALUES ('org_legacy_default', 'Legacy Default Org', now(), now())
                ON CONFLICT (id) DO NOTHING
            """)
        )
        # Ensure REAL_USER_ID seed user exists (FK for BKTState.student_id)
        await session.execute(
            text("""
                INSERT INTO users (id, email, username, first_name, last_name, password_hash, role, organization_id, is_active, created_at, updated_at)
                VALUES (:id, :email, :username, 'Test', 'User', 'hashed_pwd', 'STUDENT', 'org_legacy_default', true, now(), now())
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": REAL_USER_ID,
                "email": f"{REAL_USER_ID}@test.batch1b.com",
                "username": f"user_{REAL_USER_ID[:8]}",
            },
        )
        # Ensure topic_hierarchy seed row exists (FK for BKTState.topic_id)
        await session.execute(
            text("""
                INSERT INTO topic_hierarchy
                    (id, level, code, name_tr, osym_relevance, osym_frequency,
                     total_questions, average_difficulty, is_active, created_at, updated_at)
                VALUES
                    (:id, :level, :code, :name_tr, :osym_relevance, :osym_frequency,
                     :total_questions, :average_difficulty, :is_active, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": TEST_TOPIC_ID,
                "level": 1,
                "code": "TEST.BATCH1B",
                "name_tr": "Test Konu Batch1B",
                "osym_relevance": 0.0,
                "osym_frequency": 0,
                "total_questions": 0,
                "average_difficulty": 0.0,
                "is_active": True,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        )
        await session.commit()

    yield session_maker

    engine.dispose()


@pytest.fixture
async def bkt_state_seed(db_session):
    """Pre-seed an existing BKTState row (p_L=0.3, attempt_count=2) for UPDATE test.

    Uses REAL_USER_ID which exists in the users table (satisfies FK).
    Cleanup is done by db_session autouse.
    """
    async with db_session() as session:
        await session.execute(
            text("""
                INSERT INTO bkt_states (student_id, topic_id, organization_id, p_learn, p_transit, p_guess,
                                       p_slip, attempt_count, mastery_status, last_attempt)
                VALUES (:student_id, :topic_id, 'org_legacy_default', :p_learn, :p_transit, :p_guess,
                        :p_slip, :attempt_count, :mastery_status, :last_attempt)
                ON CONFLICT (student_id, topic_id) DO UPDATE
                SET p_learn = EXCLUDED.p_learn,
                    attempt_count = EXCLUDED.attempt_count
            """),
            {
                "student_id": REAL_USER_ID,
                "topic_id": TEST_TOPIC_ID,
                "p_learn": 0.3,
                "p_transit": 0.10,
                "p_guess": 0.20,
                "p_slip": 0.10,
                "attempt_count": 2,
                "mastery_status": "learning",
                "last_attempt": datetime.now(UTC),
            },
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _fresh_session(db_session):
    """Return a new session from the same session_maker (for requery after commit)."""
    return db_session()


# ---------------------------------------------------------------------------
# Test 1 — first-answer path: BKTState INSERT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_first_answer_inserts_bkt_state(db_session):
    """First answer for a student+topic creates a new BKTState row with attempt_count=1."""
    async with db_session() as session:
        result = await BKTService.record_answer(
            student_id=REAL_USER_ID,
            topic_id=TEST_TOPIC_ID,
            subject_slug="matematik",
            correct=True,
            rating=3,
            db=session,
            answered_questions=None,
            responses=None,
        )

        assert result["new_p_L"] > 0.0, (
            f"new_p_L should be positive, got {result['new_p_L']}"
        )
        assert "errors" in result
        assert result["errors"]["bkt"] is None

        # Flush to make INSERT visible within this transaction
        await session.flush()

        # Same-session SELECT to verify INSERT happened
        row = await session.execute(
            select(text("p_learn, attempt_count, mastery_status"))
            .select_from(text("bkt_states"))
            .where(text("student_id = :sid AND topic_id = :tid")),
            {"sid": REAL_USER_ID, "tid": TEST_TOPIC_ID},
        )
        db_row = row.one_or_none()
        assert db_row is not None, "BKTState row should have been INSERTed"
        assert db_row.attempt_count == 1, (
            f"attempt_count should be 1, got {db_row.attempt_count}"
        )
        assert 0.0 <= db_row.p_learn <= 0.999, f"p_learn out of range: {db_row.p_learn}"

        await session.rollback()


# ---------------------------------------------------------------------------
# Test 2 — existing-state path: BKTState UPDATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_existing_state_updates_bkt_state(
    db_session, bkt_state_seed
):
    """Correct answer on existing BKTState increments attempt_count and increases p_L.

    bkt_state_seed pre-creates a BKTState row (p_L=0.3, attempt_count=2)
    using REAL_USER_ID.
    """
    # bkt_state_seed uses REAL_USER_ID directly

    async with db_session() as session:
        # Get initial p_L before the call
        initial = await session.execute(
            select(text("p_learn, attempt_count"))
            .select_from(text("bkt_states"))
            .where(text("student_id = :sid AND topic_id = :tid")),
            {"sid": REAL_USER_ID, "tid": TEST_TOPIC_ID},
        )
        init_row = initial.one()
        init_p_learn = init_row.p_learn
        init_attempts = init_row.attempt_count

        result = await BKTService.record_answer(
            student_id=REAL_USER_ID,
            topic_id=TEST_TOPIC_ID,
            subject_slug="matematik",
            correct=True,
            rating=3,
            db=session,
            answered_questions=None,
            responses=None,
        )

        await session.flush()

        updated = await session.execute(
            select(text("p_learn, attempt_count"))
            .select_from(text("bkt_states"))
            .where(text("student_id = :sid AND topic_id = :tid")),
            {"sid": REAL_USER_ID, "tid": TEST_TOPIC_ID},
        )
        upd_row = updated.one()

        assert upd_row.attempt_count == init_attempts + 1, (
            f"attempt_count should be {init_attempts + 1}, got {upd_row.attempt_count}"
        )
        assert upd_row.p_learn > init_p_learn, (
            f"p_learn should increase on correct: {upd_row.p_learn} <= {init_p_learn}"
        )

        await session.rollback()


# ---------------------------------------------------------------------------
# Test 3 — answered_questions path: irt_method = "eap"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_with_answered_questions_uses_eap(db_session):
    """When answered_questions is non-empty, irt_method should be 'eap'."""
    items = [
        {"irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2},
        {"irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2},
        {"irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2},
    ]
    responses = [True, False, True]

    async with db_session() as session:
        result = await BKTService.record_answer(
            student_id=REAL_USER_ID,
            topic_id=TEST_TOPIC_ID,
            subject_slug="matematik",
            correct=True,
            rating=3,
            db=session,
            answered_questions=items,
            responses=responses,
        )

        assert result["irt_method"] == "eap", (
            f"irt_method should be 'eap', got {result['irt_method']}"
        )
        assert isinstance(result["theta_after"], float), (
            f"theta_after should be float, got {type(result['theta_after'])}"
        )
        assert result["theta_se"] > 0.0, (
            f"theta_se should be positive, got {result['theta_se']}"
        )

        await session.rollback()


# ---------------------------------------------------------------------------
# Test 4 — no answered_questions: irt_method = "bridge" + formula
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_without_answered_questions_uses_bridge(db_session):
    """When answered_questions is empty, irt_method='bridge' and theta = (p_L-0.5)*8.0."""
    async with db_session() as session:
        result = await BKTService.record_answer(
            student_id=REAL_USER_ID,
            topic_id=TEST_TOPIC_ID,
            subject_slug="matematik",
            correct=True,
            rating=3,
            db=session,
            answered_questions=None,
            responses=None,
        )

        assert result["irt_method"] == "bridge", (
            f"irt_method should be 'bridge', got {result['irt_method']}"
        )

        # S179 fix (B-P0-33): DM-05 replaced the linear bridge formula
        # (theta = (clamped - 0.5) * 8.0) with logit (math.log(clamped /
        # (1 - clamped))). The old assert was stale and silently passed
        # only because the test never ran in CI (skipif elsewhere).
        # clamped = max(0.05, min(0.95, p_L))
        import math

        new_p_L = result["new_p_L"]
        clamped = max(0.05, min(0.95, new_p_L))
        expected_theta = math.log(clamped / (1.0 - clamped))
        assert abs(result["theta_after"] - expected_theta) < 0.01, (
            f"theta_after={result['theta_after']} != expected {expected_theta} "
            f"(logit bridge since DM-05)"
        )

        # SE: max(0.3, 1.0 - p_L) — formula unchanged in DM-05
        expected_se = max(0.3, 1.0 - new_p_L)
        assert abs(result["theta_se"] - expected_se) < 0.01, (
            f"theta_se={result['theta_se']} != expected {expected_se}"
        )

        await session.rollback()


# ---------------------------------------------------------------------------
# Test 5 — return dict: all 12 keys present
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_returns_all_12_keys(db_session):
    """record_answer() return dict must contain all 12 documented keys."""
    EXPECTED_KEYS = {
        "new_p_L",
        "theta_after",
        "theta_se",
        "irt_method",
        "fsrs_next_review",
        "zpd_zone",
        "scaffold_level",
        "hints_available",
        "bilge_mode",
        "unlock_3d",
        "recommended_difficulty",
        "errors",
    }

    async with db_session() as session:
        result = await BKTService.record_answer(
            student_id=REAL_USER_ID,
            topic_id=TEST_TOPIC_ID,
            subject_slug="matematik",
            correct=True,
            rating=3,
            db=session,
            answered_questions=None,
            responses=None,
        )

        assert isinstance(result, dict), f"result should be dict, got {type(result)}"
        missing = EXPECTED_KEYS - result.keys()
        assert not missing, f"Missing keys in return dict: {missing}"
        extra = result.keys() - EXPECTED_KEYS
        assert not extra, f"Unexpected extra keys in return dict: {extra}"

        # errors must be a dict with these 4 keys
        assert isinstance(result["errors"], dict), "errors should be dict"
        assert set(result["errors"].keys()) == {"bkt", "irt", "fsrs", "zpd"}

        await session.rollback()


# ---------------------------------------------------------------------------
# Test 6 — BKTState persistence: flush → same-session SELECT → commit → fresh requery
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_bkt_state_persisted_to_db(db_session):
    """BKTState changes survive commit and a fresh session requery."""
    async with db_session() as session:
        result = await BKTService.record_answer(
            student_id=REAL_USER_ID,
            topic_id=TEST_TOPIC_ID,
            subject_slug="matematik",
            correct=True,
            rating=3,
            db=session,
            answered_questions=None,
            responses=None,
        )
        await session.flush()

        # Same-session verification (before commit)
        same_row = await session.execute(
            select(text("p_learn, attempt_count, mastery_status"))
            .select_from(text("bkt_states"))
            .where(text("student_id = :sid AND topic_id = :tid")),
            {"sid": REAL_USER_ID, "tid": TEST_TOPIC_ID},
        )
        ss_r = same_row.one_or_none()
        assert ss_r is not None, "BKTState should exist after flush"
        assert float(ss_r.p_learn) == result["new_p_L"], (
            f"p_learn mismatch after flush: db={ss_r.p_learn} result={result['new_p_L']}"
        )

        await session.commit()

    # Fresh session requery — proves persistence survived the transaction
    fresh_engine = create_async_engine(DB_URL, echo=False)
    fresh_maker = async_sessionmaker(
        fresh_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with fresh_maker() as fresh_session:
        fresh_row = await fresh_session.execute(
            select(text("p_learn, attempt_count"))
            .select_from(text("bkt_states"))
            .where(text("student_id = :sid AND topic_id = :tid")),
            {"sid": REAL_USER_ID, "tid": TEST_TOPIC_ID},
        )
        fr = fresh_row.one_or_none()
        assert fr is not None, "BKTState row missing after fresh-session requery"
        assert float(fr.p_learn) == result["new_p_L"], (
            f"p_learn mismatch after commit+requery: db={fr.p_learn} result={result['new_p_L']}"
        )
    await fresh_engine.dispose()


# ---------------------------------------------------------------------------
# Test 7 — StudentAbility upsert persistence: flush → same-session SELECT → commit → fresh requery
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_student_ability_upserted_to_db(db_session):
    """StudentAbility (subject_id=1 for matematik) is upserted and survives commit."""
    SUBJECT_ID_MATEMATIK = (
        1  # maps to "matematik" in _SUBJECT_ID_MAP at bkt_service.py:298
    )

    async with db_session() as session:
        result = await BKTService.record_answer(
            student_id=REAL_USER_ID,
            topic_id=TEST_TOPIC_ID,
            subject_slug="matematik",
            correct=True,
            rating=3,
            db=session,
            answered_questions=None,
            responses=None,
        )
        await session.flush()

        # Same-session verification
        sa_row = await session.execute(
            select(text("theta, theta_se"))
            .select_from(text("student_abilities"))
            .where(text("student_id = :sid AND subject_id = :subid")),
            {"sid": REAL_USER_ID, "subid": SUBJECT_ID_MATEMATIK},
        )
        ss_r = sa_row.one_or_none()
        assert ss_r is not None, "StudentAbility row should exist after flush"
        assert abs(float(ss_r.theta) - result["theta_after"]) < 0.001, (
            f"theta mismatch after flush: db={ss_r.theta} result={result['theta_after']}"
        )

        await session.commit()

    # Fresh session requery
    fresh_engine = create_async_engine(DB_URL, echo=False)
    fresh_maker = async_sessionmaker(
        fresh_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with fresh_maker() as fresh_session:
        fresh_row = await fresh_session.execute(
            select(text("theta, theta_se"))
            .select_from(text("student_abilities"))
            .where(text("student_id = :sid AND subject_id = :subid")),
            {"sid": REAL_USER_ID, "subid": SUBJECT_ID_MATEMATIK},
        )
        fr = fresh_row.one_or_none()
        assert fr is not None, "StudentAbility row missing after fresh-session requery"
        assert abs(float(fr.theta) - result["theta_after"]) < 0.001, (
            f"theta mismatch after commit+requery: db={fr.theta} result={result['theta_after']}"
        )
    await fresh_engine.dispose()


# ---------------------------------------------------------------------------
# Global mock patches — apply to every test in this module
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_fsrs_and_blackboard():
    """Patch FSRSService.review_card and BlackboardService.publish_learning_event for all tests.

    FSRSService is imported inside record_answer at:
      services.bkt_service:345 — from services.fsrs_v6_service import FSRSService
    Patch target: services.fsrs_v6_service.FSRSService.review_card

    BlackboardService is imported inside record_answer at:
      services.bkt_service:437 — from services.blackboard_service import BlackboardService
    The call is: await BlackboardService.get().publish_learning_event(...)
    Patch target: services.blackboard_service.BlackboardService.get
    """
    with (
        patch(
            "services.fsrs_v6_service.FSRSService.review_card",
            return_value=_FSRS_MOCK_RETURN,
        ),
        patch(
            "services.blackboard_service.BlackboardService.get",
            return_value=_blackboard_mock_instance,
        ),
    ):
        yield
