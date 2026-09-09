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
from tests.pg_sync import async_pg_dsn

# ---------------------------------------------------------------------------
# Constants (shared with batch1b)
# ---------------------------------------------------------------------------

# Kimlikler DOSYAYA OZEL (9 Eyl 2026): test_bkt_record_answer_batch1b*.py ve
# test_fsrs_card_persistence.py ayni REAL_USER_ID / TEST_TOPIC_ID'yi
# paylasiyordu ve her dosyanin db_session fixture'i o kullanicinin
# fsrs_cards/bkt_states satirlarini SILIYORDU. xdist (--dist=loadscope) uc
# dosyayi ayri worker'lara dagitinca silme baska dosyanin testinin ortasina
# dusuyordu -- CI'da rastgele 'stability 1.0 != 2.3065', 'scheduled_days
# tohum degerinde kalmis' (job 102477252081; ayni test yerelde ve baska
# kosumlarda yesil). Ayri kimlik = ayri satirlar = yaris yok.
TEST_TOPIC_ID = "00000000-0000-0000-0000-000000000002"
REAL_USER_ID = "41411c25-5c85-4470-a6ac-ac31c60ce734"
# DSN artik SABIT DEGIL: gerekce ve olcum tests/pg_sync.py::async_pg_dsn
# docstring'inde (parola git'te + veritabani adi CI'da `kiro2_test`).

_blackboard_mock_instance = AsyncMock(
    publish_learning_event=AsyncMock(return_value="msg_id_mock")
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session():
    """Function-scoped async engine — identical to batch1b fixture."""
    engine = create_async_engine(
        async_pg_dsn(host="localhost"), echo=False, pool_size=5, max_overflow=10
    )
    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        for table in ["bkt_states", "student_abilities", "zpd_history", "fsrs_cards"]:
            # S608: tablo adi sabit listeden; bind edilemez (bkz. batch1b).
            await session.execute(
                text(f"DELETE FROM {table} WHERE student_id = :sid"),  # noqa: S608
                {"sid": REAL_USER_ID},
            )
        # Kullanici satiri BU dosyada kurulur (9 Eyl 2026). Onceden yoktu:
        # fsrs_cards.student_id FK'si batch1b dosyasinin ayni kullaniciyi
        # daha once eklemis olmasina gizlice bagliydi (alfabetik sira). Ayri
        # kimlikle o bagimlilik da kalkiyor. Org satiri da ayni sebeple burada
        # (users.organization_id FK; kolon listesi batch1b'deki olcumden).
        await session.execute(
            text("""
                INSERT INTO organizations (id, name, org_type, status,
                                           kvkk_role, license_seats,
                                           created_at, updated_at)
                VALUES ('org_legacy_default', 'Legacy Default Org',
                        'ozel_okul', 'trial', 'controller', 0,
                        now(), now())
                ON CONFLICT (id) DO NOTHING
            """)
        )
        await session.execute(
            text("""
                INSERT INTO users (id, email, username, first_name, last_name,
                                   password_hash, role, organization_id,
                                   is_active, is_verified, is_2fa_enabled,
                                   is_premium, is_parent, total_xp, level,
                                   elo_rating, created_at, updated_at)
                VALUES (:id, :email, :username, 'Test', 'User', 'hashed_pwd',
                        'STUDENT', 'org_legacy_default',
                        true, true, false, false, false, 0, 1, 1200,
                        now(), now())
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": REAL_USER_ID,
                "email": f"{REAL_USER_ID}@test.fsrs_persist.com",
                "username": f"user_fsrs_{REAL_USER_ID[:8]}",
            },
        )
        # ON CONFLICT DO NOTHING (kisitsiz): id VEYA code (UNIQUE) catisirsa
        # satir zaten var demektir; eski `(id)` biciminde code catismasi
        # UniqueViolation atiyordu (yerel DB'de olculdu).
        await session.execute(
            text("""
                INSERT INTO topic_hierarchy
                    (id, level, code, name_tr, osym_relevance, osym_frequency,
                     total_questions, average_difficulty, is_active, created_at, updated_at)
                VALUES
                    (:id, :level, :code, :name_tr, :osym_relevance, :osym_frequency,
                     :total_questions, :average_difficulty, :is_active, :created_at, :updated_at)
                ON CONFLICT DO NOTHING
            """),
            {
                "id": TEST_TOPIC_ID,
                "level": 1,
                "code": "TEST.FSRS-PERSIST",
                "name_tr": "Test Konu Batch2A",
                "osym_relevance": 0.0,
                "osym_frequency": 0,
                "total_questions": 0,
                "average_difficulty": 0.0,
                # is_active=False (9 Eyl 2026): bu satir yalnizca FK icin var.
                # CI Backend Tests paylasilan kiro2_test DB'sine yazar ve silinmez;
                # aktif birakilinca tests/db/test_mufredat_agaci_saglik.py bekcisi
                # "uretim agacinda aktif test artigi" diye duser (#222 CI olcumu).
                # Olculdu: 17/17 test satir pasifken de gecer (yerel DB'de 0005
                # bu satiri zaten pasife almisti).
                "is_active": False,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        )
        await session.commit()

    yield session_maker
    # `AsyncEngine.dispose()` COROUTINE dondurur; `await` olmadan cagri
    # hicbir sey yapmiyordu -- havuz kapanmiyor, baglantilar siziyordu.
    # mypy bunu `[unused-coroutine]` ile isaretledi (CI mypy kapisi).
    await engine.dispose()


@pytest.fixture
async def fsrs_card_seed(db_session):
    """Pre-seed an FSRSCard row via ORM — avoids enum binding issues with raw SQL."""

    # Import here to avoid top-level circular imports
    from models.fsrs_models import FSRSCard

    async with db_session() as session:
        card = FSRSCard(
            # Kart id'si de dosyaya ozel: eski 0099 baska kullanicinin (732)
            # artigi olarak DB'de kalinca fsrs_cards_pkey catisiyordu (olculdu).
            id="00000000-0000-0000-0000-000000000734",
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
    """UPDATE yolu FSRS zamanlama alanlarini da yazar.

    9 Eyl 2026 -- DAVRANIS DEGISTI. Bu test onceden "elapsed_days ve
    scheduled_days record_answer tarafindan HIC yazilmaz" diyordu; yani bir
    kusuru beklenen davranis olarak sabitliyordu. Canli olcum o kusurun
    sonucunu gosterdi: fsrs_cards tablosundaki 107 satirin 106'sinda
    scheduled_days=0 -- tekrar araligi hicbir zaman kaydedilmemis.
    services/bkt_service.py artik iki alani da yaziyor; test de yeni,
    dogru davranisi sabitliyor.
    """

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

    # Zamanlama alanlari ARTIK yaziliyor -- tohum degerinde kalmamali.
    assert row.elapsed_days != 7, (
        "elapsed_days tohum degerinde (7) kalmis; record_answer bu alani "
        "yazmali. Bu tam olarak 9 Eyl 2026'da duzeltilen kusur."
    )
    assert row.elapsed_days == 0, (
        "Tohumun last_review'i az once ayarlandi, dolayisiyla iki tekrar "
        f"arasindaki gercek gecen sure 0 gun olmali. Donen: {row.elapsed_days}"
    )
    assert row.scheduled_days != 14, (
        "scheduled_days tohum degerinde (14) kalmis; record_answer bu alani "
        "FSRS'in hesapladigi araliktan yazmali."
    )
    assert row.scheduled_days >= 0

    # Ic tutarlilik: kaydedilen aralik, kaydedilen bitis tarihiyle uyusmali.
    gercek_aralik = (row.due_date - datetime.now(UTC)).days
    assert abs(row.scheduled_days - gercek_aralik) <= 1, (
        f"scheduled_days={row.scheduled_days} ile due_date'ten hesaplanan "
        f"aralik={gercek_aralik} uyusmuyor"
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
    assert (
        abs(row.stability - fsrs_result["stability"]) < 1e-6
    ), f"DB stability {row.stability} != FSRS result {fsrs_result['stability']}"
    assert (
        abs(row.difficulty - fsrs_result["difficulty"]) < 1e-6
    ), f"DB difficulty {row.difficulty} != FSRS result {fsrs_result['difficulty']}"

    # state string should match exactly
    assert (
        row.state == fsrs_result["state"]
    ), f"DB state '{row.state}' != FSRS state '{fsrs_result['state']}'"

    # due_date ordering: DB due_date should be today or in the future (FSRS sets it)
    now_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    assert (
        row.due_date >= now_start
    ), f"due_date {row.due_date} should be on or after today's start {now_start}"


# ---------------------------------------------------------------------------
# Test 4 — UPDATE: zamanlama alanlari yaziliyor mu (regresyon bekcisi)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fsrs_zamanlama_alanlari_yaziliyor(db_session, fsrs_card_seed):
    """record_answer, elapsed_days ve scheduled_days'i YAZMALI.

    Bu test eskiden `test_fsrs_card_defaults_preserved_for_unwritten_fields`
    adiyla TAM TERSINI iddia ediyordu: "bu alanlar record_answer tarafindan
    ASLA yazilmaz, tohum degerinde kalir". Yani bir kusuru sozlesme haline
    getirmisti.

    Kusurun canli sonucu (9 Eyl 2026, fsrs_cards, 107 satir):
        scheduled_days = 0 olan satir : 106
    Tekrar araligi hicbir kartta kaydedilmemis; aralikli tekrar sistemi
    araligi saklamiyordu. services/bkt_service.py duzeltildi ve bu test
    artik duzeltmenin geri gitmemesini bekliyor.
    """

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

    # Tohum degerleri: elapsed_days=7, scheduled_days=14.
    # Ikisi de record_answer tarafindan UZERINE YAZILMALI.
    assert row.elapsed_days != 7, (
        "REGRESYON: elapsed_days tohum degerinde kalmis. record_answer bu "
        "alani yazmiyor -- 9 Eyl 2026'da duzeltilen kusur geri gelmis."
    )
    assert row.scheduled_days != 14, (
        "REGRESYON: scheduled_days tohum degerinde kalmis. Canli tabloda bu "
        "kusur 107 kartin 106'sinda scheduled_days=0 olarak gorunuyordu."
    )
    assert row.scheduled_days >= 0
    assert row.elapsed_days >= 0
