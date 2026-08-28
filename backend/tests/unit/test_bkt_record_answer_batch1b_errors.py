"""
Batch 1B-b: BKTService.record_answer() error swallowing / fallback tests.

Scope: services/bkt_service.py — record_answer() error paths
Level: service-level (no API, no dependency_overrides)
DB:   real AsyncSession + PostgreSQL (function-scoped engine)

Tests (6):
  1. BKTState read fail  — OperationalError on SELECT → fallback p_L=0.10, errors["bkt"]
  2. IRT fail            — eap_theta raises ValueError → theta=0.0/se=1.0, errors["irt"]
  3. StudentAbility upsert fail — IntegrityError → errors["irt"], NOT errors["student_ability"]
  4. FSRS fail           — review_card raises RuntimeError → fsrs_next_review=None, errors["fsrs"]
  5. BKT read fail — no BKTState row written on read failure
  6. All-4-fail         — all 4 error paths fire simultaneously → all 4 errors populated

Excludes: ZPDHistory error, Blackboard publish, happy-path, API layer,
         dependency_overrides, Batch 2 FSRS write tests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.bkt_service import BKTService

# ---------------------------------------------------------------------------
# Constants (shared with batch1b)
# ---------------------------------------------------------------------------

TEST_TOPIC_ID = "00000000-0000-0000-0000-000000000001"
REAL_USER_ID = "41411c25-5c85-4470-a6ac-ac31c60ce732"
DB_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5434/kiro2"

_FSRS_MOCK_RETURN = {
    "stability": 1.0,
    "difficulty": 0.5,
    "due_date": datetime.now(UTC),
    "state": "new",
    "reps": 1,
    "lapses": 0,
}

_blackboard_mock_instance = AsyncMock(
    publish_learning_event=AsyncMock(return_value="msg_id_mock")
)


# ---------------------------------------------------------------------------
# Fixtures (shared db_session + seed from batch1b)
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session():
    """Function-scoped async engine — identical to batch1b."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(DB_URL, echo=False, pool_size=5, max_overflow=10)
    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        for table in ["bkt_states", "student_abilities", "zpd_history", "fsrs_cards"]:
            await session.execute(
                text(f"DELETE FROM {table} WHERE student_id = :sid"),
                {"sid": REAL_USER_ID},
            )
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
                "email": f"{REAL_USER_ID}@test.batch1b_err.com",
                "username": f"user_err_{REAL_USER_ID[:8]}",
            },
        )
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
                "code": "TEST.BATCH1B-ERR",
                "name_tr": "Test Konu Batch1B-Err",
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
    """Pre-seed BKTState row so read-fail test has a row to fail on reading."""
    async with db_session() as session:
        await session.execute(
            text("""
                INSERT INTO bkt_states (student_id, topic_id, organization_id, p_learn, p_transit, p_guess,
                                        p_slip, attempt_count, mastery_status, last_attempt)
                VALUES (:student_id, :topic_id, 'org_legacy_default', :p_learn, :p_transit, :p_guess,
                        :p_slip, :attempt_count, :mastery_status, :last_attempt)
                ON CONFLICT (student_id, topic_id) DO UPDATE SET p_learn = EXCLUDED.p_learn
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
# Test 1 — BKTState read fail → fallback p_L=0.10, errors["bkt"]
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_bkt_read_fails_uses_default_p_L(
    db_session, bkt_state_seed
):
    """BKTState SELECT raises OperationalError → p_learn defaults to params.p_T=0.10."""

    async def bkt_read_fail_execute(self, clause, *args, **kwargs):
        """Raise OperationalError only on BKTState SELECT statements."""
        compiled = str(clause.compile())
        if "bkt_states" in compiled.lower() and "student_id" in compiled.lower():
            from sqlalchemy.exc import OperationalError

            raise OperationalError("BKT read failed", None, None)
        # All other statements pass through
        return await AsyncSession.execute(self, clause, *args, **kwargs)

    with (
        patch.object(AsyncSession, "execute", bkt_read_fail_execute),
        patch(
            "services.fsrs_v6_service.FSRSService.review_card",
            return_value=_FSRS_MOCK_RETURN,
        ),
        patch(
            "services.blackboard_service.BlackboardService.get",
            return_value=_blackboard_mock_instance,
        ),
    ):
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

    # Fallback: p_L defaults to params["p_T"]=0.10, then update(0.10, correct=True)
    assert result["new_p_L"] > 0.10, (
        f"new_p_L should exceed default 0.10, got {result['new_p_L']}"
    )
    assert result["errors"]["bkt"] is not None, "errors['bkt'] should be populated"
    assert isinstance(result["errors"]["bkt"], str), (
        f"errors['bkt'] should be str, got {type(result['errors']['bkt'])}"
    )
    # Bridge method still applies (no answered_questions)
    assert result["irt_method"] == "bridge"
    # ZPD computed normally — FRUSTRATION (p_L=0.10 < LOWER=0.40) or ZPD_ACTIVE
    assert result["zpd_zone"] in ("FRUSTRATION", "ZPD_ACTIVE", "MASTERED")
    assert "theta_after" in result
    await db_session().close()


# ---------------------------------------------------------------------------
# Test 2 — IRT fail → theta=0.0/se=1.0, errors["irt"]
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_irt_fails_uses_zero_theta(db_session):
    """IRTService3PL.eap_theta raises ValueError → theta_after=0.0, theta_se=1.0."""

    with (
        patch(
            "services.fsrs_v6_service.FSRSService.review_card",
            return_value=_FSRS_MOCK_RETURN,
        ),
        patch(
            "services.blackboard_service.BlackboardService.get",
            return_value=_blackboard_mock_instance,
        ),
        patch(
            "services.irt_service_3pl.IRTService3PL.eap_theta",
            side_effect=ValueError("IRT explosion"),
        ),
    ):
        async with db_session() as session:
            result = await BKTService.record_answer(
                student_id=REAL_USER_ID,
                topic_id=TEST_TOPIC_ID,
                subject_slug="matematik",
                correct=True,
                rating=3,
                db=session,
                answered_questions=[{"irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2}],
                responses=[True],
            )

    # Fallback defaults are set before the try block
    assert result["theta_after"] == 0.0, (
        f"theta_after should be 0.0 fallback, got {result['theta_after']}"
    )
    assert result["theta_se"] == 1.0, (
        f"theta_se should be 1.0 fallback, got {result['theta_se']}"
    )
    assert result["errors"]["irt"] is not None, "errors['irt'] should be populated"
    assert "IRT explosion" in result["errors"]["irt"]
    # IRT method still determined by answered_questions presence
    assert result["irt_method"] == "eap"
    # BKT update still happened
    assert result["new_p_L"] > 0.0
    await db_session().close()


# ---------------------------------------------------------------------------
# Test 3 — StudentAbility upsert fail → errors["irt"], NOT errors["student_ability"]
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_student_ability_upsert_fails_continues(db_session):
    """StudentAbility upsert raises IntegrityError → errors['irt'] (NOT 'student_ability')."""

    async def student_ability_fail_execute(self, clause, *args, **kwargs):
        compiled = str(clause.compile())
        if "student_abilities" in compiled.lower():
            from sqlalchemy.exc import IntegrityError

            raise IntegrityError("StudentAbility constraint violation", None, None)
        return await AsyncSession.execute(self, clause, *args, **kwargs)

    with (
        patch.object(AsyncSession, "execute", student_ability_fail_execute),
        patch(
            "services.fsrs_v6_service.FSRSService.review_card",
            return_value=_FSRS_MOCK_RETURN,
        ),
        patch(
            "services.blackboard_service.BlackboardService.get",
            return_value=_blackboard_mock_instance,
        ),
    ):
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

    # StudentAbility upsert fail → errors["irt"] (line 335: if errors["irt"] is None)
    assert result["errors"]["irt"] is not None, (
        "errors['irt'] should be populated on StudentAbility fail"
    )
    # NO separate errors["student_ability"] key
    assert "student_ability" not in result["errors"], (
        "errors has no 'student_ability' key"
    )
    # Bridge theta still computed
    assert result["theta_after"] != 0.0 or result["theta_se"] != 1.0, (
        "theta should still be computed via bridge"
    )
    assert result["irt_method"] == "bridge"
    assert result["new_p_L"] > 0.0
    await db_session().close()


# ---------------------------------------------------------------------------
# Test 4 — FSRS fail → fsrs_next_review=None, errors["fsrs"]
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_fsrs_fails_sets_next_review_to_none(db_session):
    """FSRSService.review_card raises RuntimeError → fsrs_next_review=None, errors['fsrs']."""

    with (
        patch(
            "services.blackboard_service.BlackboardService.get",
            return_value=_blackboard_mock_instance,
        ),
        patch(
            "services.fsrs_v6_service.FSRSService.review_card",
            side_effect=RuntimeError("FSRS explosion"),
        ),
    ):
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

    # fsrs_next_review defaults to None before the try block (line 340)
    assert result["fsrs_next_review"] is None, (
        f"fsrs_next_review should be None on FSRS fail, got {result['fsrs_next_review']}"
    )
    assert result["errors"]["fsrs"] is not None, "errors['fsrs'] should be populated"
    assert "FSRS explosion" in result["errors"]["fsrs"]
    # Other computations still happened
    assert result["new_p_L"] > 0.0
    assert result["irt_method"] == "bridge"
    assert result["theta_after"] != 0.0 or result["theta_se"] != 1.0
    await db_session().close()


# ---------------------------------------------------------------------------
# Test 5 — BKT read fail → no BKTState row written (only write failure would create)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_bkt_read_fail_writes_no_bkt_state_row(
    db_session, bkt_state_seed
):
    """On BKT read failure, no BKTState row should be INSERTed or modified."""

    async def bkt_read_fail_execute(self, clause, *args, **kwargs):
        compiled = str(clause.compile())
        if "bkt_states" in compiled.lower() and "student_id" in compiled.lower():
            from sqlalchemy.exc import OperationalError

            raise OperationalError("BKT read failed", None, None)
        return await AsyncSession.execute(self, clause, *args, **kwargs)

    with (
        patch.object(AsyncSession, "execute", bkt_read_fail_execute),
        patch(
            "services.fsrs_v6_service.FSRSService.review_card",
            return_value=_FSRS_MOCK_RETURN,
        ),
        patch(
            "services.blackboard_service.BlackboardService.get",
            return_value=_blackboard_mock_instance,
        ),
    ):
        async with db_session() as session:
            await BKTService.record_answer(
                student_id=REAL_USER_ID,
                topic_id=TEST_TOPIC_ID,
                subject_slug="matematik",
                correct=True,
                rating=3,
                db=session,
                answered_questions=None,
                responses=None,
            )
            await session.rollback()

    # Verify: original seeded row is still there (read failure → no write)
    async with db_session() as session:
        row = await session.execute(
            text(
                "SELECT p_learn, attempt_count FROM bkt_states WHERE student_id=:sid AND topic_id=:tid"
            ),
            {"sid": REAL_USER_ID, "tid": TEST_TOPIC_ID},
        )
        db_row = row.one_or_none()
        assert db_row is not None, (
            "Original BKTState row should remain after read failure"
        )
        assert float(db_row.p_learn) == 0.3, (
            f"p_learn should be original 0.3, not updated: got {db_row.p_learn}"
        )
        assert db_row.attempt_count == 2, (
            f"attempt_count should be original 2, got {db_row.attempt_count}"
        )


# ---------------------------------------------------------------------------
# Test 6 — All 4 fail simultaneously → all 4 errors populated, return dict complete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_answer_all_4_fail_collects_all_errors(db_session, bkt_state_seed):
    """All 4 error paths fire together → bkt+irt+fsrs all populated, 12 keys intact."""

    async def multi_error_execute(self, clause, *args, **kwargs):
        compiled = str(clause.compile())
        if "bkt_states" in compiled.lower():
            from sqlalchemy.exc import OperationalError

            raise OperationalError("BKT read failed", None, None)
        if "student_abilities" in compiled.lower():
            from sqlalchemy.exc import IntegrityError

            raise IntegrityError("StudentAbility violated", None, None)
        return await AsyncSession.execute(self, clause, *args, **kwargs)

    with (
        patch.object(AsyncSession, "execute", multi_error_execute),
        patch(
            "services.blackboard_service.BlackboardService.get",
            return_value=_blackboard_mock_instance,
        ),
        patch(
            "services.irt_service_3pl.IRTService3PL.eap_theta",
            side_effect=ValueError("IRT explosion"),
        ),
        patch(
            "services.fsrs_v6_service.FSRSService.review_card",
            side_effect=RuntimeError("FSRS explosion"),
        ),
    ):
        async with db_session() as session:
            result = await BKTService.record_answer(
                student_id=REAL_USER_ID,
                topic_id=TEST_TOPIC_ID,
                subject_slug="matematik",
                correct=True,
                rating=3,
                db=session,
                answered_questions=[{"irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2}],
                responses=[True],
            )

    # All 3 algorithm errors captured
    assert result["errors"]["bkt"] is not None, "errors['bkt'] should be populated"
    assert result["errors"]["irt"] is not None, "errors['irt'] should be populated"
    assert result["errors"]["fsrs"] is not None, "errors['fsrs'] should be populated"

    # Fallback values applied
    assert result["theta_after"] == 0.0
    assert result["theta_se"] == 1.0
    assert result["fsrs_next_review"] is None

    # All 12 return keys present
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
    assert set(result.keys()) == EXPECTED_KEYS, (
        f"Missing/extra keys: {set(result.keys()) ^ EXPECTED_KEYS}"
    )

    # errors dict has correct 4 keys
    assert set(result["errors"].keys()) == {"bkt", "irt", "fsrs", "zpd"}
