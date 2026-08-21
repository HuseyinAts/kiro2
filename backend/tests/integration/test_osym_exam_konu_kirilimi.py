"""Konu (topic) bazli kirilim — CANLI Postgres'e karsi TDD RED testleri.

B3 tasarimi: docs/superpowers/specs/2026-08-21-b3-konu-kirilimi-design.md
Kabul kriteri: bir sinav oturumu icin konu kirilimi DERS degil KONU bazinda
donmeli (>= 3 farkli `topic_code`), ve donen konu adedi DB'den sayilan
konu adediyle ESIT olmali (yanlis-pozitif / yanlis-sifir tuzagi).

----------------------------------------------------------------------------
NEDEN AYRI DOSYA (olculdu — tahmin degil)
----------------------------------------------------------------------------
Bu testler `tests/integration/test_osym_exam_engine.py` icine YAZILAMAZ.
O dosya :17-24'te modul duzeyinde
`with patch.dict("sys.modules", {"models.database": MagicMock(),
"core.database": MagicMock(), ...})` blogu ACIP motoru o blogun ICINDE import
ediyor. Iki olculmus sonuc:

  1) Blok icinde import edilen motorun DB kapisi mock'tur:
         IN BLOCK get_db_session_context: <class 'unittest.mock.MagicMock'>
     Yani o dosyadaki `OSYMExamEngine` sembolu MagicMock'lu bir modul
     globals()'ina baglidir ve canli Postgres'e ASLA gidemez.

  2) `patch.dict` cikista sozlugu eski haline dondurur; blok ICINDE
     sys.modules'a eklenen her modul SILINIR:
         AFTER BLOCK: <class 'function'>   e2 is e -> False
     Yani ayni surecte motor bir kez daha (temiz) import edilir; iki farkli
     modul nesnesi dolasir.

Ayrica o dosyanin 26 testi :55 ve :844'teki `@pytest.mark.skipif(True, ...)`
ile KOSULSUZ skip — Postgres ayakta olsa bile 26/26 skip kalir, yani bekci
degildir.

----------------------------------------------------------------------------
NEDEN `get_db_session_context` YENIDEN YONLENDIRILIYOR (mock DEGIL)
----------------------------------------------------------------------------
`tests/conftest.py:100` kosum ortaminda
`os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"` yapiyor.
Bu yuzden pytest icinde `core.database.db_manager` SQLite'a bakar ve motorun
canli Postgres verisini gormesi IMKANSIZ olur — bu da testi YANLIS sebeple
kirmiziya dusururdu (yanlis-RED).

Cozum: motorun modul-global `get_db_session_context` adi, ayni DSN'e
(`tests/integration/conftest.py::canli_dsn_cozumle`) bagli GERCEK bir
AsyncSession uretecine yonlendirilir. Bu bir davranis stub'i DEGIL, bir
baglanti yonlendirmesidir: SQL, ORM modelleri ve satirlar gercektir.
Aletin kendisi de olculur: `_dialect_postgres_mi` her kosumda dogrular,
sessizce SQLite'a dusulemez.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tests.integration.conftest import canli_dsn_cozumle

# Tasarim kabul kriteri: >= 3 farkli konu kodu (A1 hedefi >= 5).
BEKLENEN_ASGARI_KONU = 3

# Oturum, TEK bir ders altinda birden cok konu tasir. Bu bilerek secildi:
# bugunku kod `subject_area` ile grupladigi icin TEK kova doner; konu bazina
# gecince kova sayisi konu sayisina cikar. Boylece RED sinyali ders/konu
# ayrimini dogrudan olcer.
DERS = "MATEMATIK"

# konu_no=1 -> 5 soru, konu_no=2 -> 4, ... konu_no=5 -> 1  (toplam 15)
# Farkli sayilar siralama testini anlamli kilar; 1 soruluk kova ise
# "az soruluk kova gizlenmez" kuralini civiler.
KONU_SAYISI = 5
BEKLENEN_TOPLAM_SORU = KONU_SAYISI * (KONU_SAYISI + 1) // 2  # 15

# Kapidan (mv_safe_for_beta) deterministik soru secimi.
# Siralama th.code + qb.id ile sabit -> tekrarlanabilir.
SECIM_SQL = text(
    """
    WITH aday AS (
        SELECT qb.id                                                   AS question_id,
               th.code                                                 AS topic_code,
               th.name_tr                                              AS topic_name,
               row_number() OVER (PARTITION BY th.code ORDER BY qb.id)  AS satir_no,
               dense_rank() OVER (ORDER BY th.code)                     AS konu_no
        FROM mv_safe_for_beta m
        JOIN question_bank     qb ON qb.id = m.id
        JOIN topic_hierarchy   th ON th.id = qb.primary_topic_id
        JOIN question_metadata qm ON qm.id = qb.id
        WHERE qm.subject_area = :ders
    )
    SELECT question_id, topic_code, topic_name, konu_no
    FROM aday
    WHERE konu_no <= :konu_sayisi
      AND satir_no <= (:konu_sayisi + 1 - konu_no)
    ORDER BY konu_no, satir_no
    """
)

# Karsi-olcum: API'nin dondurdugu konu adedi bununla ESIT olmali.
DB_KONU_SAYIM_SQL = text(
    """
    SELECT count(DISTINCT th.code) AS konu_adedi,
           count(*)                AS soru_adedi
    FROM exam_questions eq
    JOIN question_bank    qb ON qb.id = eq.question_id
    LEFT JOIN topic_hierarchy th ON th.id = qb.primary_topic_id
    WHERE eq.exam_session_id = :sid
    """
)

NULL_KONU_SAYIM_SQL = text(
    "SELECT count(*) FROM question_bank WHERE primary_topic_id IS NULL"
)


def _dialect_postgres_mi(session: AsyncSession) -> bool:
    """Olcum aletini dogrula: gercekten Postgres'e mi bagliyiz?"""
    return session.get_bind().dialect.name == "postgresql"


@pytest_asyncio.fixture
async def canli_maker():
    """Canli Postgres'e bagli async_sessionmaker.

    Postgres yoksa SKIP eder — sqlite'a DUSMEZ (conftest'teki ayni disiplin).
    """
    dsn = canli_dsn_cozumle()
    if not dsn:
        pytest.skip(
            "Canli DSN cozulemedi — KIRO2_TEST_DSN / KVKK_VERIFY_DSN / "
            "backend/.env icindeki DATABASE_URL gerekli"
        )

    engine = create_async_engine(dsn)
    try:
        async with engine.connect():
            pass
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"Canli Postgres ulasilamiyor: {type(exc).__name__}: {exc}")

    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        yield maker
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def konu_kirilimi_oturumu(canli_maker, monkeypatch):
    """Gercek bir exam_session + 15 exam_questions + 15 student_answers kurar.

    Sorular TEK ders (`MATEMATIK`) altinda 5 FARKLI `primary_topic_id`
    tasir. Kurulum COMMIT edilir (motor ayri bir baglanti kullanir),
    teardown'da satirlar silinir.
    """
    import core.osym_exam_engine as motor_modulu

    session_id = f"pytest-konu-{uuid.uuid4()}"

    async with canli_maker() as db:
        assert _dialect_postgres_mi(db), (
            "Olcum aleti arizali: canli_maker Postgres'e bagli DEGIL "
            f"(dialect={db.get_bind().dialect.name}). SQLite'a dusuldu."
        )

        ogrenci = (
            await db.execute(
                text(
                    "SELECT id, organization_id FROM student_profiles "
                    "ORDER BY id LIMIT 1"
                )
            )
        ).first()
        if ogrenci is None:
            pytest.skip("student_profiles bos — exam_sessions FK'si karsilanamiyor")

        secim = (
            (await db.execute(SECIM_SQL, {"ders": DERS, "konu_sayisi": KONU_SAYISI}))
            .mappings()
            .all()
        )
        beklenen_kodlar: dict[str, int] = {}
        for satir in secim:
            beklenen_kodlar[satir["topic_code"]] = (
                beklenen_kodlar.get(satir["topic_code"], 0) + 1
            )

        if len(beklenen_kodlar) < KONU_SAYISI or len(secim) != BEKLENEN_TOPLAM_SORU:
            pytest.skip(
                f"Kapidan {DERS} dersinde {KONU_SAYISI} konu x kademeli soru "
                f"secilemedi (konu={len(beklenen_kodlar)}, soru={len(secim)}). "
                "mv_safe_for_beta icerigi degismis olabilir."
            )

        await db.execute(
            text(
                """
                INSERT INTO exam_sessions
                    (id, organization_id, student_id, exam_type, exam_name,
                     total_questions, duration_minutes, status,
                     current_question_index, time_spent_seconds,
                     total_correct, total_wrong, total_empty, raw_score,
                     estimated_ability, ability_confidence)
                VALUES
                    (:sid, :org, :ogr, CAST('TYT' AS examtype),
                     'B3 konu kirilimi TDD RED',
                     :toplam, 40, 'completed', 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)
                """
            ),
            {
                "sid": session_id,
                "org": ogrenci.organization_id,
                "ogr": ogrenci.id,
                "toplam": len(secim),
            },
        )

        for sira, satir in enumerate(secim, start=1):
            await db.execute(
                text(
                    "INSERT INTO exam_questions "
                    "(id, exam_session_id, question_id, question_order) "
                    "VALUES (gen_random_uuid()::text, :sid, :qid, :sira)"
                ),
                {"sid": session_id, "qid": satir["question_id"], "sira": sira},
            )

        # Cift sirali sorular DOGRU, tek sirali sorular YANLIS cevaplanir.
        await db.execute(
            text(
                """
                INSERT INTO student_answers
                    (id, exam_session_id, question_id, selected_answer,
                     is_correct, response_time_seconds, answer_changes,
                     time_to_first_answer)
                SELECT gen_random_uuid()::text,
                       eq.exam_session_id,
                       eq.question_id,
                       CASE WHEN eq.question_order % 2 = 0
                            THEN qc.correct_answer
                            ELSE CASE WHEN qc.correct_answer = 'A'
                                      THEN 'B' ELSE 'A' END
                       END,
                       (eq.question_order % 2 = 0),
                       12.0, 0, 12.0
                FROM exam_questions eq
                JOIN question_content qc ON qc.id = eq.question_id
                WHERE eq.exam_session_id = :sid
                """
            ),
            {"sid": session_id},
        )
        await db.commit()

    # Motorun DB kapisini canli Postgres'e yonlendir (bkz. modul docstring).
    @asynccontextmanager
    async def _canli_kapi():
        async with canli_maker() as oturum:
            yield oturum

    monkeypatch.setattr(motor_modulu, "get_db_session_context", _canli_kapi)

    async with canli_maker() as db:
        olcum = (
            (await db.execute(DB_KONU_SAYIM_SQL, {"sid": session_id})).mappings().one()
        )
        null_konulu_soru = (await db.execute(NULL_KONU_SAYIM_SQL)).scalar_one()

    try:
        yield {
            "session_id": session_id,
            "beklenen_kodlar": beklenen_kodlar,
            "db_konu_sayisi": olcum["konu_adedi"],
            "db_soru_sayisi": olcum["soru_adedi"],
            "null_konulu_soru": null_konulu_soru,
        }
    finally:
        async with canli_maker() as db:
            for tablo, kolon in (
                ("student_answers", "exam_session_id"),
                ("exam_questions", "exam_session_id"),
                ("exam_sessions", "id"),
            ):
                await db.execute(
                    text(f"DELETE FROM {tablo} WHERE {kolon} = :sid"),  # noqa: S608
                    {"sid": session_id},
                )
            await db.commit()


async def _performansi_getir(session_id: str):
    from core.osym_exam_engine import OSYMExamEngine

    return await OSYMExamEngine().get_subject_performance(session_id)


def _bos_liste_uyarisi(session_id: str, db_soru_sayisi: int) -> str:
    return (
        "Motor BOS liste dondu. get_subject_performance icindeki ciplak "
        "`except Exception` (core/osym_exam_engine.py:1432) gercek hatayi "
        "yutup `return []` yapiyor olabilir — bu YANLIS-RED uretir. "
        f"session_id={session_id}, DB'deki exam_questions={db_soru_sayisi}"
    )


async def test_konu_kirilimi_ders_degil_konu_bazinda_doner(konu_kirilimi_oturumu):
    """Konu kirilimi DERS degil KONU bazinda donmeli (>= 3 farkli topic_code).

    BUGUN KIRMIZI: motor `subject_area` ile grupluyor -> tek kova.
    """
    veri = konu_kirilimi_oturumu
    perf = await _performansi_getir(veri["session_id"])

    assert perf, _bos_liste_uyarisi(veri["session_id"], veri["db_soru_sayisi"])

    donen_kodlar = {getattr(p, "topic_code", None) for p in perf}
    donen_kodlar.discard(None)

    assert len(donen_kodlar) >= BEKLENEN_ASGARI_KONU, (
        f"Konu kirilimi DERS bazinda kalmis. Donen kova sayisi={len(perf)}, "
        f"kovalarin `subject` degerleri={[p.subject for p in perf]}, "
        f"cozulen topic_code kumesi={sorted(donen_kodlar)}. "
        f"DB'de bu oturumda {veri['db_konu_sayisi']} farkli konu var "
        f"(beklenen kodlar={sorted(veri['beklenen_kodlar'])}). "
        f"Kovalarda `topic_code` alani var mi? "
        f"{[hasattr(p, 'topic_code') for p in perf]}"
    )

    # KARSI-OLCUM: ">= 3" tek basina yanlis-pozitif verebilir (fazla kova
    # uretmek de kusurdur). Donen adet DB'den sayilanla ESIT olmali.
    assert len(donen_kodlar) == veri["db_konu_sayisi"], (
        f"API {len(donen_kodlar)} konu donduruyor ama DB'de "
        f"{veri['db_konu_sayisi']} farkli konu var. "
        f"API kodlari={sorted(donen_kodlar)}, "
        f"DB kodlari={sorted(veri['beklenen_kodlar'])}"
    )


async def test_konu_kirilimi_soru_sayisi_azalan_siralanir(konu_kirilimi_oturumu):
    """Kovalar `total_questions` AZALAN sirali donmeli.

    Siralama iddiasi ancak 2+ kova varken bir iddiadir; tek kovada
    kendiliginden gecer (S238: bos kumede bekciler XPASS verdi). Bu yuzden
    once alt sinir assert edilir.
    """
    veri = konu_kirilimi_oturumu
    perf = await _performansi_getir(veri["session_id"])

    assert perf, _bos_liste_uyarisi(veri["session_id"], veri["db_soru_sayisi"])

    assert len(perf) >= 2, (
        "Siralama iddiasi olculemez: tek kova donuyor. "
        f"kova sayisi={len(perf)}, DB konu sayisi={veri['db_konu_sayisi']}"
    )

    sayilar = [p.total_questions for p in perf]
    assert sayilar == sorted(
        sayilar, reverse=True
    ), f"Kovalar total_questions'a gore azalan sirali degil: {sayilar}"


async def test_konu_kirilimi_toplamlari_korunur(konu_kirilimi_oturumu):
    """INVARYANT: kova toplamlari == oturumun toplam soru sayisi.

    Gruplama anahtari degisirken soru kaybedilmedigini civiler.
    Bu test bugun de GECEBILIR — asil RED sinyali 1. testten gelir.
    """
    veri = konu_kirilimi_oturumu
    perf = await _performansi_getir(veri["session_id"])

    assert perf, _bos_liste_uyarisi(veri["session_id"], veri["db_soru_sayisi"])

    toplam = sum(p.total_questions for p in perf)
    assert toplam == veri["db_soru_sayisi"], (
        f"Kova toplamlari {toplam}, oturumun soru sayisi "
        f"{veri['db_soru_sayisi']}. Gruplama sirasinda soru kayboldu/coklandi. "
        f"kova dagilimi={[(p.subject, p.total_questions) for p in perf]}"
    )
    assert (
        toplam == BEKLENEN_TOPLAM_SORU
    ), f"Fikstur {BEKLENEN_TOPLAM_SORU} soru kurmustu, toplam {toplam}"


async def test_konu_atanmamis_soru_gorunur_kovada_toplanir(konu_kirilimi_oturumu):
    """`primary_topic_id` NULL olan soru "Konu atanmamis" kovasinda gorunur.

    Tasarim: sessiz varsayilan YOK, ders adina DUSULMEZ.

    Skip kosulu CALISMA ANINDA olculur (sabit `@pytest.mark.skip` DEGIL):
    NULL-konulu bir `question_bank` satiri olustugu gun test kendiliginden
    kosar. 21 Agu 2026 olcumu: 0 / 3922.
    """
    veri = konu_kirilimi_oturumu

    if veri["null_konulu_soru"] == 0:
        pytest.skip(
            "primary_topic_id IS NULL olan question_bank satiri YOK "
            f"(olculdu: {veri['null_konulu_soru']} satir). NULL kova iddiasi "
            "bu veritabaninda uretilemiyor; sentetik satir INSERT etmek "
            "uretim icerik tablosuna yazmak olurdu. Bu dal GREEN fazinda "
            "test kapsami DISINDA kalir — bosluk bilerek gorunur birakildi."
        )

    perf = await _performansi_getir(veri["session_id"])
    assert perf, _bos_liste_uyarisi(veri["session_id"], veri["db_soru_sayisi"])

    atanmamis = [p for p in perf if getattr(p, "topic_code", None) is None]
    assert atanmamis, (
        "Konusu atanmamis soru var ama gorunur kova yok. "
        f"kovalar={[(p.subject, getattr(p, 'topic_code', '<alan-yok>')) for p in perf]}"
    )
    assert all(p.topic_name == "Konu atanmamis" for p in atanmamis), (
        "Konusu atanmamis kovanin adi 'Konu atanmamis' olmali (ders adina "
        f"dusulmemeli). Bulunan={[p.topic_name for p in atanmamis]}"
    )
