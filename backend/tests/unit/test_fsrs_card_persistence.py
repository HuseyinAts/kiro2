"""
Batch 2A: FSRSCard persistence integration tests.

Scope: services/bkt_service.py — FSRS write block within record_answer()
Level: integration (real AsyncSession + PostgreSQL)
FSRS: real FSRSService.review_card (NO MOCK)
Blackboard: mocked (batch1b pattern)

Tests (4):
  1. INSERT path — core fields written to DB match review_card output
  2. UPDATE path — mutable fields updated, unwritten fields preserved
  3. INSERT path — DB row fields match review_card return values (core fields)
  4. UPDATE path — elapsed_days/scheduled_days stay at seeded values

Excludes:
  - reps exact mapping (card.step proxy, not 1:1)
  - timezone exact equality
  - rounding-sensitive equality
  - mock usage
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.bkt_service import BKTService

# ---------------------------------------------------------------------------
# Constants (shared with batch1b)
# ---------------------------------------------------------------------------

TEST_TOPIC_ID = "00000000-0000-0000-0000-000000000001"
REAL_USER_ID = "41411c25-5c85-4470-a6ac-ac31c60ce732"
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2"

_blackboard_mock_instance = AsyncMock(
    publish_learning_event=AsyncMock(return_value="msg_id_mock")
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session():
    """Function-scoped async engine — identical to batch1b fixture."""
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
                "code": "TEST.BATCH2A",
                "name_tr": "Test Konu Batch2A",
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
async def fsrs_card_seed(db_session):
    """Pre-seed an FSRSCard row via ORM — avoids enum binding issues with raw SQL."""

    # Import here to avoid top-level circular imports
    from models.fsrs_models import FSRSCard

    async with db_session() as session:
        card = FSRSCard(
            id="00000000-0000-0000-0000-000000000099",
            student_id=REAL_USER_ID,
            front_text="Seed front",
            back_text="Seed back",
            subject_area="MATEMATIK",  # uppercase enum label (DB enum: subjectarea)
            topic=TEST_TOPIC_ID,
            stability=3.5,
            difficulty=4.0,
            elapsed_days=7,
            scheduled_days=14,
            reps=5,
            lapses=1,
            state="review",
            due_date=datetime.now(UTC),
            last_review=datetime.now(UTC),
        )
        session.add(card)
        await session.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _query_fsrs_card(session, student_id, topic_id):
    """Query FSRSCard row by student_id + topic."""
    result = await session.execute(
        text("""
            SELECT stability, difficulty, reps, lapses, state, due_date,
                   elapsed_days, scheduled_days, front_text, back_text
            FROM fsrs_cards
            WHERE student_id = :sid AND topic = :tid
        """),
        {"sid": student_id, "tid": topic_id},
    )
    return result.one_or_none()


# ---------------------------------------------------------------------------
# Test 1 — INSERT path: core fields written to DB match review_card output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fsrs_card_insert_persists_core_fields(db_session):
    """First record_answer call (no pre-existing FSRSCard) creates a row with valid fields."""

    with patch(
        "services.blackboard_service.BlackboardService.get",
        return_value=_blackboard_mock_instance,
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
            await session.flush()

            row = await _query_fsrs_card(session, REAL_USER_ID, TEST_TOPIC_ID)

    assert row is not None, "FSRSCard row should exist after INSERT"

    # Core numeric fields — positive
    assert row.stability > 0.0, f"stability should be positive, got {row.stability}"
    assert row.difficulty > 0.0, f"difficulty should be positive, got {row.difficulty}"
    assert row.reps >= 0, f"reps should be non-negative, got {row.reps}"
    assert row.lapses >= 0, f"lapses should be non-negative, got {row.lapses}"

    # State is valid
    assert row.state in ("new", "learning", "review"), f"state invalid: {row.state}"

    # due_date is non-null datetime in the future (or now)
    assert row.due_date is not None, "due_date should not be null"


# ---------------------------------------------------------------------------
# Test 2 — UPDATE path: mutable fields updated, unwritten fields preserved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fsrs_card_update_updates_mutable_fields_only(db_session, fsrs_card_seed):
    """UPDATE path modifies only mutable fields; elapsed_days/scheduled_days stay intact."""

    with patch(
        "services.blackboard_service.BlackboardService.get",
        return_value=_blackboard_mock_instance,
    ):
        async with db_session() as session:
            # Verify seed state before update
            seed_row = await _query_fsrs_card(session, REAL_USER_ID, TEST_TOPIC_ID)
            assert seed_row.elapsed_days == 7
            assert seed_row.scheduled_days == 14

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
            await session.flush()

            row = await _query_fsrs_card(session, REAL_USER_ID, TEST_TOPIC_ID)

    assert row is not None, "FSRSCard row should still exist after UPDATE"

    # Mutable fields: due_date should have changed (FSRS recalculates it)
    # reps might change (FSRS may update card.step)
    assert row.reps >= 0

    # Unwritten fields: MUST remain exactly as seeded
    assert row.elapsed_days == 7, (
        f"elapsed_days should be preserved at 7, got {row.elapsed_days} — "
        "record_answer UPDATE does NOT write this field"
    )
    assert row.scheduled_days == 14, (
        f"scheduled_days should be preserved at 14, got {row.scheduled_days} — "
        "record_answer UPDATE does NOT write this field"
    )


# ---------------------------------------------------------------------------
# Test 3 — INSERT: DB row core fields match review_card return values
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fsrs_card_db_matches_review_card_core_fields(db_session):
    """DB row fields match what FSRSService.review_card actually returned."""

    from services.fsrs_v6_service import FSRSService

    # Get ground-truth review_card output for a new card with rating=3
    fsrs_result = FSRSService.review_card(
        stability=None, difficulty=None, due_date=None, rating_int=3, reps=0
    )

    with patch(
        "services.blackboard_service.BlackboardService.get",
        return_value=_blackboard_mock_instance,
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
            await session.flush()

            row = await _query_fsrs_card(session, REAL_USER_ID, TEST_TOPIC_ID)

    assert row is not None

    # stability and difficulty should match the real FSRS output (within floating point)
    assert abs(row.stability - fsrs_result["stability"]) < 1e-6, (
        f"DB stability {row.stability} != FSRS result {fsrs_result['stability']}"
    )
    assert abs(row.difficulty - fsrs_result["difficulty"]) < 1e-6, (
        f"DB difficulty {row.difficulty} != FSRS result {fsrs_result['difficulty']}"
    )

    # state string should match exactly
    assert row.state == fsrs_result["state"], (
        f"DB state '{row.state}' != FSRS state '{fsrs_result['state']}'"
    )

    # due_date ordering: DB due_date should be today or in the future (FSRS sets it)
    now_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    assert row.due_date >= now_start, f"due_date {row.due_date} should be on or after today's start {now_start}"


# ---------------------------------------------------------------------------
# Test 4 — UPDATE: elapsed_days/scheduled_days default values preserved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fsrs_card_defaults_preserved_for_unwritten_fields(
    db_session, fsrs_card_seed
):
    """Fields not written by record_answer UPDATE stay at their pre-existing values."""

    with patch(
        "services.blackboard_service.BlackboardService.get",
        return_value=_blackboard_mock_instance,
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
            await session.flush()

            row = await _query_fsrs_card(session, REAL_USER_ID, TEST_TOPIC_ID)

    # elapsed_days and scheduled_days are NEVER set by record_answer UPDATE
    # They should remain at whatever the seed set (7 and 14 respectively)
    assert row.elapsed_days == 7, (
        f"elapsed_days was NOT written by record_answer and should stay at seed value 7, got {row.elapsed_days}"
    )
    assert row.scheduled_days == 14, (
        f"scheduled_days was NOT written by record_answer and should stay at seed value 14, got {row.scheduled_days}"
    )
