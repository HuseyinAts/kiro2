"""TDD RED kaniti + regresyon bekcisi — #485 / Y2 "B-placement" izi.

Iki AYRI kusur sinifi, ikisi de ULASILABILIR ve ikisi de yeni ogrencinin ILK
temas noktasini (seviye tespiti) olduruyor:

A) ``app/services/placement_service.py`` — HAM SQL, split ONCESI semayi
   varsayiyor. Canli olcum (18 Agu 2026, port 5434 / kiro2):

       _get_candidates()  -> UndefinedColumnError: column "question_text" does not exist
       answer() :419      -> UndefinedColumnError: column "irt_discrimination" does not exist
       app/api/placement.py:130 -> UndefinedColumnError: column "correct_answer" does not exist

   Uclarin hicbiri ``ProgrammingError``i yakalamiyor (yalniz ``ValueError``
   -> 422/409 dallari var), dolayisiyla POST /api/v1/placement/start ve
   POST /api/v1/placement/{id}/answer **kosulsuz 500**.

B) ``services/placement_assessment_service.py`` — ORM SINIF DUZEYI erisim.
   ``QuestionBankItem.difficulty_level`` / ``.subject_area`` artik devredici
   (models/question_bank.py:545-587) ve sinif duzeyinde KASITLI
   ``AttributeError`` atiyor -> sorgu HIC KURULAMIYOR:

       AttributeError: QuestionBankItem.difficulty_level sinif duzeyinde
       kullanilamaz: bu alan artik statistics iliskisinde. Sorguda JOIN kullanin.

   ``load_assessment_items`` icinde try/except YOK -> POST /api/v1/assessment/start
   500 (API'deki ``if "error" in result -> 503`` dalina hic ulasilmaz).

Testler GERCEK Postgres'e karsi kosar (mock DB DEGIL). S228'de olculdu ki
``AsyncMock`` DB'li 50 test bu kusur sinifini YAPISAL OLARAK goremiyor: mock
sema kaymasini da devredici ``AttributeError``ini de uretmez.

OLCUM NOTU — deger esitligi bu tabloda AYIRT EDICI DEGIL
--------------------------------------------------------
``question_statistics``ta ``(irt_discrimination, irt_difficulty, irt_guessing)``
**tek bir kombinasyon** tasiyor: ``(1.0, 0.0, 0.25)`` — ve bu, ``answer()``in
satir bulunamadiginda kullandigi geri-donus degerleriyle BIREBIR AYNI. Yani
"item_params DB degerine esit" seklindeki bir assert, sorguyu tamamen SILEN bir
"fix"te de gecerdi (vakum test). Bu yuzden o iddia SQL metni uzerinden
(``question_statistics`` tablosuna gidiliyor mu) civilenir; davranissal ayrimi
ise ``correct_answer`` cozumu tasir (dogru harf -> theta > 0, yanlis harf ->
theta < 0).
"""

from __future__ import annotations

import os
import sys
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32-chars")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-chars")

from core.dependencies import AuthenticatedUser, get_current_user  # noqa: E402
from models.enums_db import UserRole  # noqa: E402

# `live_db` fixture'i tests/integration/conftest.py'de; DSN kaynak koda
# GOMULMEZ (parola git'e girmesin), env veya backend/.env'den cozulur ve
# postgres olmayan DSN REDDEDILIR (sessizce sqlite'a dusmez).
pytestmark = pytest.mark.asyncio

SUBJECT = "MATEMATIK"
STUDENT_ID = "student-1"

# `_get_candidates` kalite kapisini `quality_review_status` ile birlikte
# uyguluyor; fix bu iki filtreyi de TASIMAK zorunda (kaldirmak sizinti olur —
# olcum: kapisiz havuz 110.858 / kapili 27.073).
ACCEPTED_QUALITY_STATUS = {"human_verified", "auto_judged_high"}


# ---------------------------------------------------------------------------
# Yardimcilar
# ---------------------------------------------------------------------------


class _FakePipeline:
    """`redis.pipeline()` — hset/expire SENKRON cagriliyor, execute await'li."""

    def __init__(self, parent: _FakeRedis) -> None:
        self._parent = parent
        self._ops: list[tuple] = []

    def hset(self, key: str, mapping: dict | None = None):
        self._ops.append(("hset", key, mapping or {}))
        return self

    def expire(self, key: str, ttl: int):
        self._ops.append(("expire", key, ttl))
        return self

    async def execute(self) -> list:
        for op in self._ops:
            if op[0] == "hset":
                bucket = self._parent.hashes.setdefault(op[1], {})
                for k, v in op[2].items():
                    bucket[str(k).encode()] = str(v).encode()
        self._ops.clear()
        return []


class _FakeRedis:
    """Sureç-ici Redis ikamesi.

    DB DEGIL — test edilen kusur Postgres semasinda; Redis yalniz oturum
    durumunu tasiyor. Deterministik olsun diye gercek Redis yerine bu kullanilir.
    """

    def __init__(self) -> None:
        self.hashes: dict[str, dict[bytes, bytes]] = {}
        self.strings: dict[str, bytes] = {}

    async def hgetall(self, key: str) -> dict[bytes, bytes]:
        return dict(self.hashes.get(key, {}))

    def pipeline(self) -> _FakePipeline:
        return _FakePipeline(self)

    async def setex(self, key: str, ttl: int, value) -> bool:
        self.strings[key] = str(value).encode()
        return True

    async def expire(self, key: str, ttl: int) -> bool:
        return True


class _SqlSpySession:
    """`live_db`yi SARMALAR — mock degil, passthrough kaydedici.

    Her `execute` GERCEK Postgres'e gider; yalnizca SQL metni biriktirilir.
    """

    def __init__(self, inner: AsyncSession) -> None:
        self._inner = inner
        self.sqls: list[str] = []

    async def execute(self, statement, params=None, **kw):
        self.sqls.append(str(statement))
        if params is None:
            return await self._inner.execute(statement, **kw)
        return await self._inner.execute(statement, params, **kw)

    def __getattr__(self, name):
        return getattr(self._inner, name)


async def _gate_uyeleri(db: AsyncSession, ids: list[str]) -> set[str]:
    """Verilen id'lerin kalite kapisi (mv_safe_for_beta) icinde olanlari."""
    stmt = text("SELECT id::text FROM mv_safe_for_beta WHERE id::text IN :ids")
    stmt = stmt.bindparams(bindparam("ids", expanding=True))
    rows = await db.execute(stmt, {"ids": ids})
    return {r[0] for r in rows}


async def _statuslar(db: AsyncSession, ids: list[str]) -> set[str]:
    stmt = text(
        "SELECT DISTINCT quality_review_status FROM question_statistics "
        "WHERE id::text IN :ids"
    )
    stmt = stmt.bindparams(bindparam("ids", expanding=True))
    rows = await db.execute(stmt, {"ids": ids})
    return {r[0] for r in rows}


async def _ornek_soru(db: AsyncSession) -> tuple[str, str]:
    """(question_id, correct_answer) — kapidan gecen gercek bir MATEMATIK sorusu."""
    rows = await db.execute(
        text(
            "SELECT qb.id::text, qc.correct_answer "
            "FROM question_bank qb "
            "JOIN question_content qc ON qc.id = qb.id "
            "JOIN question_metadata qm ON qm.id = qb.id "
            "WHERE upper(qm.subject_area) = :subj "
            "  AND qb.is_active = TRUE "
            "  AND qc.correct_answer IS NOT NULL "
            "  AND qb.id IN (SELECT id FROM mv_safe_for_beta) "
            "ORDER BY qb.id LIMIT 1"
        ),
        {"subj": SUBJECT},
    )
    row = rows.fetchone()
    if row is None:
        pytest.skip(f"{SUBJECT} icin kapidan gecen soru yok — veri onkosulu")
    return row[0], (row[1] or "A").strip().upper()[0]


def _yanlis_harf(dogru: str) -> str:
    return next(h for h in "ABCDE" if h != dogru)


# ---------------------------------------------------------------------------
# Fixture'lar
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_redis() -> _FakeRedis:
    return _FakeRedis()


@pytest.fixture
def placement_svc(live_db: AsyncSession, fake_redis: _FakeRedis):
    from app.services.placement_service import PlacementTestService

    return PlacementTestService(db=live_db, redis=fake_redis)


@pytest_asyncio.fixture
async def placement_client(
    live_db: AsyncSession, fake_redis: _FakeRedis
) -> AsyncGenerator[AsyncClient, None]:
    from app.api.placement import router as placement_router
    from app.core.deps import get_db as placement_get_db
    from app.core.deps import get_redis as placement_get_redis

    app = FastAPI()
    app.include_router(placement_router)

    async def _override_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            id=STUDENT_ID,
            username="student",
            role=UserRole.STUDENT,
            email="student@test.com",
        )

    async def _override_db():
        yield live_db

    async def _override_redis():
        return fake_redis

    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[placement_get_db] = _override_db
    app.dependency_overrides[placement_get_redis] = _override_redis

    # raise_app_exceptions=False: yakalanmamis ProgrammingError'i 500'e cevirir,
    # boylece "uc kosulsuz 500 donuyor" iddiasi HTTP katmaninda olculebilir.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def assessment_client(
    live_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> AsyncGenerator[AsyncClient, None]:
    from api import placement_assessment_api as mod

    class _Ctx:
        async def __aenter__(self):
            return live_db

        async def __aexit__(self, *exc):
            return False

    # Handler `async with get_db_session_context()` ile KENDI oturumunu aciyor;
    # canli oturumu oraya baglamak icin modul-duzeyi adi degistiriyoruz.
    monkeypatch.setattr(mod, "get_db_session_context", lambda: _Ctx(), raising=True)

    app = FastAPI()
    app.include_router(mod.router)

    async def _override_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            id=STUDENT_ID,
            username="student",
            role=UserRole.STUDENT,
            email="student@test.com",
        )

    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# A) app/services/placement_service.py — ham SQL
# ---------------------------------------------------------------------------


async def test_get_candidates_canli_semaya_karsi_kurulur(placement_svc):
    """_get_candidates() UndefinedColumn ile patlamamali (kok RED)."""
    rows = await placement_svc._get_candidates(SUBJECT, 0.0)
    assert isinstance(rows, list)
    assert rows, "kapidan gecen MATEMATIK havuzu bos gorunuyor"


async def test_get_candidates_row_takma_adlarini_korur(placement_svc):
    """`a`/`b`/`c` takma adlari select_placement_question'in SOZLESMESI."""
    rows = await placement_svc._get_candidates(SUBJECT, 0.0)
    beklenen = {
        "question_id",
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "a",
        "b",
        "c",
        "subject_id",
        "topic_id",
    }
    eksik = beklenen - set(rows[0].keys())
    assert not eksik, f"row'dan dusen alanlar: {sorted(eksik)}"


async def test_get_candidates_irt_parametreleri_sayisal(placement_svc):
    """a/b/c None olamaz — select_placement_question float() ile okuyor."""
    rows = await placement_svc._get_candidates(SUBJECT, 0.0)
    for r in rows[:20]:
        assert r["a"] is not None and r["b"] is not None and r["c"] is not None, r
        float(r["a"]), float(r["b"]), float(r["c"])


async def test_get_candidates_soru_metni_ve_secenekler_dolu(placement_svc):
    """question_text/option_a..d gercekten question_content'ten gelmeli."""
    rows = await placement_svc._get_candidates(SUBJECT, 0.0)
    for r in rows[:20]:
        assert (r["question_text"] or "").strip(), f"bos soru metni: {r['question_id']}"
        assert (r["option_a"] or "").strip(), f"bos secenek A: {r['question_id']}"


async def test_get_candidates_ders_filtresi_uygulanir(placement_svc):
    """subject_area filtresi question_metadata'ya gocerken DUSMEMELI."""
    rows = await placement_svc._get_candidates(SUBJECT, 0.0)
    dersler = {(r["subject_id"] or "").upper() for r in rows}
    assert dersler == {SUBJECT}, f"karisan dersler: {sorted(dersler)}"


async def test_get_candidates_kalite_kapisini_korur(
    placement_svc, live_db: AsyncSession
):
    """safe_for_beta_sql kapisi kaldirilirsa havuz 27.073 -> 110.858 sizar."""
    rows = await placement_svc._get_candidates(SUBJECT, 0.0)
    ids = [r["question_id"] for r in rows]
    icerdekiler = await _gate_uyeleri(live_db, ids)
    disarda = set(ids) - icerdekiler
    assert (
        not disarda
    ), f"kapi disindan {len(disarda)} soru sizdi: {sorted(disarda)[:5]}"


async def test_get_candidates_quality_review_status_filtresini_korur(
    placement_svc, live_db: AsyncSession
):
    """quality_review_status question_statistics'e gocerken DUSMEMELI."""
    rows = await placement_svc._get_candidates(SUBJECT, 0.0)
    ids = [r["question_id"] for r in rows]
    statuslar = await _statuslar(live_db, ids)
    assert statuslar <= ACCEPTED_QUALITY_STATUS, f"kabul disi status: {statuslar}"


async def test_get_candidates_ciktisi_soru_secicisini_besler(placement_svc):
    """Gercek tuketici: select_placement_question(state, candidates)."""
    from app.services.placement_service import (
        PlacementState,
        select_placement_question,
    )

    rows = await placement_svc._get_candidates(SUBJECT, 0.0)
    state = PlacementState(
        session_id=str(uuid.uuid4()),
        user_id=STUDENT_ID,
        subject_id=SUBJECT,
        started_at=datetime.now(UTC).isoformat(),
    )
    secilen = select_placement_question(state, rows)
    assert secilen is not None
    assert (secilen.get("question_text") or "").strip()


async def test_start_ilk_soruyu_metniyle_dondurur(placement_svc):
    """svc.start() -> stem + 4 secenek dolu (ValueError 'soru bulunamadi' DEGIL)."""
    sonuc = await placement_svc.start(
        user_id=STUDENT_ID, subject_id=SUBJECT, school_type="default"
    )
    soru = sonuc["question"]
    assert soru["question_id"]
    assert soru["stem"].strip(), "stem bos — question_text JOIN'i eksik"
    assert all(soru["options"][h].strip() for h in ("A", "B", "C", "D")), soru[
        "options"
    ]


async def test_answer_irt_parametrelerini_question_statistics_ten_okur(
    live_db: AsyncSession, fake_redis: _FakeRedis
):
    """answer() :419 sorgusu question_statistics'e gitmeli.

    Deger esitligi burada AYIRT EDICI DEGIL (DB'de a/b/c == 1.0/0.0/0.25 ve
    bu, satir bulunamadigindaki geri-donus degerinin AYNISI) — bu yuzden
    iddia SQL metni uzerinden civilenir.
    """
    from app.services.placement_service import PlacementState, PlacementTestService

    qid, _ = await _ornek_soru(live_db)
    spy = _SqlSpySession(live_db)
    svc = PlacementTestService(db=spy, redis=fake_redis)

    sid = str(uuid.uuid4())
    await svc._write(
        PlacementState(
            session_id=sid,
            user_id=STUDENT_ID,
            subject_id=SUBJECT,
            started_at=datetime.now(UTC).isoformat(),
        )
    )

    await svc.answer(sid, qid, True)

    irt_sorgulari = [s for s in spy.sqls if "irt_discrimination" in s]
    assert irt_sorgulari, "irt_discrimination okuyan sorgu hic kosmadi"
    assert any("question_statistics" in s for s in irt_sorgulari), (
        "irt_* hala question_bank'tan okunuyor: " + irt_sorgulari[0][:200]
    )


# ---------------------------------------------------------------------------
# A2) app/api/placement.py — uc katmani (correct_answer :130 dahil)
# ---------------------------------------------------------------------------


async def test_start_ucu_500_dondurmez(placement_client: AsyncClient):
    resp = await placement_client.post(
        "/api/v1/placement/start",
        json={"subject_id": SUBJECT, "school_type": "default"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["question"]["stem"].strip()


async def test_answer_ucu_dogru_harfte_theta_yukseltir(
    placement_client: AsyncClient, live_db: AsyncSession, fake_redis: _FakeRedis
):
    """correct_answer question_content'ten cozulmeli (api/placement.py:130).

    Davranissal ayrim: tek dogru yanit -> EAP theta prior (0.0) UZERINE cikar.
    """
    from app.services.placement_service import PlacementState, PlacementTestService

    qid, dogru = await _ornek_soru(live_db)
    sid = str(uuid.uuid4())
    await PlacementTestService(db=live_db, redis=fake_redis)._write(
        PlacementState(
            session_id=sid,
            user_id=STUDENT_ID,
            subject_id=SUBJECT,
            started_at=datetime.now(UTC).isoformat(),
        )
    )

    resp = await placement_client.post(
        f"/api/v1/placement/{sid}/answer",
        json={"question_id": qid, "answer": dogru},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    theta = body["result"]["theta"] if body["is_complete"] else body["theta"]
    assert theta > 0.0, f"dogru yanit theta'yi yukseltmedi: {theta}"


async def test_answer_ucu_yanlis_harfte_theta_dusurur(
    placement_client: AsyncClient, live_db: AsyncSession, fake_redis: _FakeRedis
):
    """Ikiz test: `is_correct` sabitlenirse (hep True) bu test duser."""
    from app.services.placement_service import PlacementState, PlacementTestService

    qid, dogru = await _ornek_soru(live_db)
    sid = str(uuid.uuid4())
    await PlacementTestService(db=live_db, redis=fake_redis)._write(
        PlacementState(
            session_id=sid,
            user_id=STUDENT_ID,
            subject_id=SUBJECT,
            started_at=datetime.now(UTC).isoformat(),
        )
    )

    resp = await placement_client.post(
        f"/api/v1/placement/{sid}/answer",
        json={"question_id": qid, "answer": _yanlis_harf(dogru)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    theta = body["result"]["theta"] if body["is_complete"] else body["theta"]
    assert theta < 0.0, f"yanlis yanit theta'yi dusurmedi: {theta}"


# ---------------------------------------------------------------------------
# B) services/placement_assessment_service.py — ORM sinif duzeyi
# ---------------------------------------------------------------------------


async def test_load_assessment_items_sorgusu_kurulur(live_db: AsyncSession):
    """select() KURULURKEN AttributeError atmamali (kok RED)."""
    from services.placement_assessment_service import load_assessment_items

    items = await load_assessment_items(db=live_db, subjects=[SUBJECT])
    assert isinstance(items, list)


async def test_load_assessment_items_bos_donmez(live_db: AsyncSession):
    """Sessiz yutma bekcisi.

    Item kurulumu `except Exception: continue` icinde; JOIN'e cevrilip
    eager-load unutulursa ornek-duzeyi `MissingGreenlet` yutulur ve havuz
    SESSIZCE bosalir -> uc 503 "Yeterli soru bulunamadi" doner.
    """
    from services.placement_assessment_service import load_assessment_items

    items = await load_assessment_items(db=live_db, subjects=[SUBJECT])
    assert items, "havuz bos — split alanlari ornek duzeyinde okunamiyor olabilir"


async def test_load_assessment_items_ders_filtresi_uygulanir(live_db: AsyncSession):
    """subject_area hem WHERE'de hem IRTItem.subject'te dogru gelmeli."""
    from services.placement_assessment_service import load_assessment_items

    items = await load_assessment_items(db=live_db, subjects=[SUBJECT])
    dersler = {(i.subject or "").upper() for i in items}
    assert dersler == {SUBJECT}, f"karisan/bos ders etiketi: {sorted(dersler)}"


async def test_load_assessment_items_kalite_kapisini_korur(live_db: AsyncSession):
    from services.placement_assessment_service import load_assessment_items

    items = await load_assessment_items(db=live_db, subjects=[SUBJECT])
    ids = [i.item_id for i in items]
    disarda = set(ids) - await _gate_uyeleri(live_db, ids)
    assert not disarda, f"kapi disindan {len(disarda)} soru sizdi"


async def test_start_assessment_error_dondurmez(live_db: AsyncSession):
    """API'nin 503 dali icin `error` anahtari — burada OLMAMALI."""
    from services.placement_assessment_service import start_assessment

    sonuc = await start_assessment(
        db=live_db, student_id=STUDENT_ID, subjects=[SUBJECT]
    )
    assert "error" not in sonuc, sonuc
    assert sonuc["question_id"]
    assert (sonuc["subject"] or "").upper() == SUBJECT


async def test_assessment_start_ucu_500_dondurmez(assessment_client: AsyncClient):
    resp = await assessment_client.post("/api/v1/assessment/start", json={})
    assert resp.status_code == 200, resp.text
    assert resp.json()["question_id"]
