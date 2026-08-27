"""K1 — "cevabi temizle" DB'ye islenmeli, sessizce yutulmamali.

----------------------------------------------------------------------------
KUSUR (olculdu, tahmin degil)
----------------------------------------------------------------------------
`frontend/src/store/examStore.ts:411-413`::

    clearAnswer: async (questionId: string) => {
      await get().saveAnswer(questionId, '', 0);
    }

Yani "cevabi temizle" HTTP'de bos dizge (`""`) olarak gelir. `api/sinav.py:91`
`selected_answer: str | None` — desen dogrulamasi YOK, `""` sema kapisindan
gecer ve motora ulasir.

`core/osym_exam_engine.py:716-718`::

    normalized_answer = (
        selected_answer.strip().upper() if selected_answer else selected_answer
    )

`""` falsy oldugu icin `else` dali onu **aynen** gecirir; `None`'a CEVIRMEZ.
Postgres kisiti bunu reddeder (canli olcum, 27 Agu 2026)::

    SELECT ''::varchar IS NULL
        OR (''::varchar)::text = ANY ((ARRAY['A','B','C','D','E']::varchar[])::text[]);
    -> f          # NULL icin ayni ifade -> t

    check_selected_answer
      CHECK (selected_answer IS NULL OR selected_answer IN ('A','B','C','D','E'))

Hata `_db_worker` icindeki ciplak `except Exception: logger.error(...)`
(:708-709) tarafindan yutulur, uc HTTP 200 doner. Uretim dalinda (`TESTING`
set degilken) satirlar `execute(stmt, batch)` ile TOPLU yazildigi icin
(:686 `while len(batch) < 1000`) TEK gecersiz oge, o batch'teki **1000'e
kadar** cevabi birlikte dusurur. Ogrenci ve sistem hicbir hata gormez.

----------------------------------------------------------------------------
NEDEN CANLI POSTGRES (mock DEGIL)
----------------------------------------------------------------------------
Kusurun tamami bir **DB kisitinda** yasiyor. `student_answers` uzerindeki
`check_selected_answer` mock'lu bir oturumda YAPISAL OLARAK degerlendirilemez;
sahte oturum `""` degerini mutlu mesut kabul eder ve test kirik kodda da
YESIL kalir (`tests/fast/test_osym_exam_engine_split.py` bu yuzden bu kusuru
goremez: orada INSERT yalnizca *kurulur*, hic CALISTIRILMAZ).

----------------------------------------------------------------------------
NEDEN `core.database.get_db_session_context` YENIDEN YONLENDIRILIYOR
----------------------------------------------------------------------------
Iki olculmus sebep:

  1. `tests/conftest.py:100` kosum ortaminda
     `os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"` yapiyor.
     Yonlendirme olmadan motor SQLite'a bakar, kisit hic degerlendirilmez ve
     test YANLIS-YESIL olur.
  2. `save_answer` (:668) `from core.database import get_db_session_context`
     satirini fonksiyon GOVDESINDE calistirir. Python `from X import Y`'yi
     yerel bagladigi icin `core.osym_exam_engine` modul-duzeyi yamasi bu
     fonksiyon icin ETKISIZDIR — yama `core.database` uzerinde olmali.
     (Ayni olcum `tests/fast/test_osym_exam_engine_split.py:181-184`.)

Bu bir davranis stub'i DEGIL, bir baglanti yonlendirmesidir: SQL, ORM
modelleri, kisitlar ve satirlar gercektir. Alet her kosumda dogrulanir
(`_dialect_postgres_mi`), sessizce SQLite'a dusulemez.

----------------------------------------------------------------------------
NEDEN HICBIR SEY KALICI YAZILMIYOR
----------------------------------------------------------------------------
Tum is TEK bir `AsyncConnection` uzerinde acilan DIS transaction icinde
kosar; motorun kendi `commit()` cagrisi `join_transaction_mode=
"create_savepoint"` sayesinde yalnizca savepoint'i serbest birakir. Teardown
dis transaction'i ROLLBACK eder. Uretim tablolarina tek satir kalmaz ve
hicbir `DELETE`/`UPDATE` calistirilmaz.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from tests.integration.conftest import canli_dsn_cozumle

# Ilk (gercek) cevap. Kontrol kolu bunun KORUNDUGUNU civiler.
ILK_CEVAP = "B"

# Frontend `clearAnswer` tam olarak bunu gonderir (examStore.ts:412).
TEMIZLE = ""

OGRENCI_SQL = text(
    "SELECT id, organization_id FROM student_profiles ORDER BY id LIMIT 1"
)

SORU_SQL = text(
    "SELECT qb.id FROM question_bank qb "
    "JOIN question_content qc ON qc.id = qb.id "
    "WHERE qb.is_active IS TRUE "
    "ORDER BY qb.id LIMIT 1"
)

OTURUM_INSERT_SQL = text(
    """
    INSERT INTO exam_sessions
        (id, organization_id, student_id, exam_type, exam_name,
         total_questions, duration_minutes, status, current_question_index,
         time_spent_seconds, total_correct, total_wrong, total_empty,
         raw_score, estimated_ability, ability_confidence)
    VALUES
        (:sid, :org, :ogr, CAST('TYT' AS examtype), 'K1 cevap temizleme TDD',
         1, 40, 'in_progress', 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)
    """
)

SATIR_SQL = text(
    # LEFT JOIN BILEREK: satirin VARLIGI yalnizca `student_answers`a bagli
    # kalmali. INNER JOIN olsaydi `question_content` eksikliginde satir
    # "hic yazilmamis" gibi gorunur ve ustteki testler YANLIS sebeple duserdi.
    "SELECT sa.selected_answer, sa.answer_changes, sa.is_correct, "
    "       qc.correct_answer "
    "FROM student_answers sa "
    "LEFT JOIN question_content qc ON qc.id = sa.question_id "
    "WHERE sa.exam_session_id = :sid AND sa.question_id = :qid"
)


def _dialect_postgres_mi(oturum: AsyncSession) -> bool:
    """Olcum aletini dogrula: gercekten Postgres'e mi bagliyiz?"""
    return oturum.get_bind().dialect.name == "postgresql"


@pytest_asyncio.fixture
async def sinav_ortami(monkeypatch):
    """Canli Postgres'te gecici bir sinav oturumu + motoru ona baglar.

    Doner: ``(engine, session_id, question_id, satiri_oku)``.
    ``satiri_oku()`` motorla AYNI baglantidan `student_answers` satirini okur.
    """
    import core.database
    from core.osym_exam_engine import ExamSessionData, ExamStatus, OSYMExamEngine
    from models.database import ExamType

    dsn = canli_dsn_cozumle()
    if not dsn:
        pytest.skip(
            "Canli DSN cozulemedi — KIRO2_TEST_DSN / KVKK_VERIFY_DSN / "
            "backend/.env icindeki DATABASE_URL gerekli"
        )

    db_engine = create_async_engine(dsn)
    try:
        baglanti = await db_engine.connect()
    except Exception as exc:  # pragma: no cover - ortam yoklugu
        await db_engine.dispose()
        pytest.skip(f"Canli Postgres ulasilamiyor: {type(exc).__name__}: {exc}")

    dis_trans = await baglanti.begin()

    def _oturum_ac() -> AsyncSession:
        # `create_savepoint`: motorun `commit()` cagrisi yalnizca savepoint'i
        # serbest birakir; dis transaction ACIK kalir ve teardown'da geri alinir.
        return AsyncSession(
            bind=baglanti,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

    try:
        async with _oturum_ac() as kurulum:
            assert _dialect_postgres_mi(kurulum), (
                "Olcum aleti arizali: Postgres'e bagli DEGIL "
                f"(dialect={kurulum.get_bind().dialect.name}). SQLite'a dusuldu."
            )

            ogrenci = (await kurulum.execute(OGRENCI_SQL)).first()
            if ogrenci is None:
                pytest.skip("student_profiles bos — exam_sessions FK'si karsilanamiyor")

            question_id = (await kurulum.execute(SORU_SQL)).scalar_one_or_none()
            if question_id is None:
                pytest.skip(
                    "is_active question_bank + question_content satiri yok — "
                    "student_answers FK'si karsilanamiyor"
                )

            session_id = f"pytest-k1-{uuid.uuid4()}"
            await kurulum.execute(
                OTURUM_INSERT_SQL,
                {"sid": session_id, "org": ogrenci.organization_id, "ogr": ogrenci.id},
            )
            await kurulum.commit()

        # Motorun DB kapisini bu baglantiya yonlendir (bkz. modul docstring).
        @asynccontextmanager
        async def _canli_kapi():
            async with _oturum_ac() as oturum:
                yield oturum

        monkeypatch.setattr(core.database, "get_db_session_context", _canli_kapi)

        # INSERT'in senkron ve gozlenebilir olmasinin TEK sebebi bu env.
        # Kok conftest zaten set ediyor; burada ACIKCA sabitlenir ki kok
        # conftest degisirse test sessizce olcumsuz kalmasin.
        monkeypatch.setenv("TESTING", "true")

        engine = OSYMExamEngine()
        engine.active_sessions[session_id] = ExamSessionData(
            session_id=session_id,
            student_id=str(ogrenci.id),
            exam_config=engine.exam_configs[ExamType.TYT],
            status=ExamStatus.IN_PROGRESS,
            questions=[question_id],
            answers={},
        )

        async def satiri_oku():
            async with _oturum_ac() as oturum:
                return (
                    (
                        await oturum.execute(
                            SATIR_SQL, {"sid": session_id, "qid": question_id}
                        )
                    )
                    .mappings()
                    .one_or_none()
                )

        yield engine, session_id, question_id, satiri_oku
    finally:
        await dis_trans.rollback()
        await baglanti.close()
        await db_engine.dispose()


async def test_alet_gercek_cevap_gercekten_db_ye_yaziliyor(sinav_ortami):
    """ALET DOGRULAMASI + KONTROL KOLU — ikisi ayni assert'te.

    ALET: bu test DUSERSE kapatilacak bir sey yok demektir; kosum hattinin
    kendisi (yonlendirme / TESTING env / FK'lar) bozuktur ve K1 hakkindaki
    KIRMIZI sinyal YANLIS-KIRMIZI olurdu.

    KONTROL KOLU: fix'in ASIRIYA kacmadigini civiler. `normalized_answer`'i
    kosulsuz `None` yapan bir "fix" (veya `save_answer`'i erken `return`
    ettiren her sey) K1 testlerini gecer ama BU testi oldurur — cunku gercek
    bir cevap artik DB'ye yazilmiyor olurdu.
    """
    engine, session_id, _question_id, satiri_oku = sinav_ortami

    await engine.save_answer(session_id, _question_id, ILK_CEVAP)

    satir = await satiri_oku()
    assert satir is not None, (
        "student_answers'a HICBIR satir yazilmadi. Kusur K1 DEGIL, kosum "
        "hattidir: TESTING env'i 'true' mu, `core.database."
        "get_db_session_context` yonlendirmesi tutuyor mu, FK'lar saglandi mi?"
    )
    assert satir["selected_answer"] == ILK_CEVAP, (
        f"Gercek cevap korunmali. Beklenen {ILK_CEVAP!r}, "
        f"DB'de {satir['selected_answer']!r}. Bu deger None ise 'fix' asiriya "
        "kacmis ve her cevabi siliyor demektir."
    )


async def test_bos_dizge_cevabi_db_de_temizler(sinav_ortami):
    """KIRMIZI: `""` gonderilince satir `NULL` olmali, `B` kalmamali.

    Bugun `normalized_answer` `""` uretiyor, `check_selected_answer` INSERT'i
    reddediyor, hata :708/:823 tarafindan yutuluyor ve satir `B` olarak
    KALIYOR — ogrenci "temizledim" saniyor.
    """
    engine, session_id, question_id, satiri_oku = sinav_ortami

    await engine.save_answer(session_id, question_id, ILK_CEVAP)
    onceki = await satiri_oku()
    assert onceki is not None and onceki["selected_answer"] == ILK_CEVAP, (
        f"On kosul saglanmadi: ilk cevap DB'de {onceki!r}. "
        "Bu testin KIRMIZI'si K1'i olcmuyor olabilir."
    )

    await engine.save_answer(session_id, question_id, TEMIZLE)

    sonraki = await satiri_oku()
    assert sonraki is not None, "Satir tamamen kayboldu — beklenen davranis bu degil"
    assert sonraki["selected_answer"] is None, (
        "Ogrenci cevabi temizledi ama DB'de "
        f"{sonraki['selected_answer']!r} duruyor. Bos dizge `None`'a "
        "cevrilmiyor; `check_selected_answer` INSERT'i reddediyor ve hata "
        "sessizce yutuluyor (osym_exam_engine.py:716-718)."
    )


async def test_bos_dizge_upsert_i_gercekten_calistirir(sinav_ortami):
    """KIRMIZI: temizleme bir UPSERT'tir — `answer_changes` ARTMALI.

    `selected_answer IS NULL` tek basina yanlis-pozitif verebilir: satir hic
    yazilmamis olsa da (veya `is_correct` gibi baska bir sebeple NULL kalsa
    da) o assert gecebilirdi. `answer_changes` yalnizca `on_conflict_do_update`
    dali KOSTUGUNDA artar (:765) — yani bu assert "UPSERT gercekten
    calisti mi" sorusunu olcer, "deger ne oldu" sorusunu degil.
    """
    engine, session_id, question_id, satiri_oku = sinav_ortami

    await engine.save_answer(session_id, question_id, ILK_CEVAP)
    onceki = await satiri_oku()
    assert onceki is not None, "On kosul saglanmadi: ilk cevap DB'ye yazilmadi"
    assert onceki["answer_changes"] == 0, (
        f"Ilk INSERT'te answer_changes 0 olmali, {onceki['answer_changes']} "
        "bulundu — sayac beklenmedik bir yerden artiyor"
    )

    await engine.save_answer(session_id, question_id, TEMIZLE)

    sonraki = await satiri_oku()
    assert sonraki is not None, "Satir tamamen kayboldu"
    assert sonraki["answer_changes"] == onceki["answer_changes"] + 1, (
        "Temizleme UPSERT'i hic kosmadi: answer_changes "
        f"{onceki['answer_changes']} -> {sonraki['answer_changes']}. "
        "INSERT kisit ihlaliyle dustu ve hata yutuldu."
    )


async def test_is_correct_cevapla_birlikte_hareket_eder(sinav_ortami):
    """`is_correct` her yazimda YENIDEN hesaplanmali: notla, temizle, yeniden notla.

    NEDEN VAR (S255 -- veri olcumunden dogdu)
    -----------------------------------------
    `student_answers`ta ALTI fosil satir olculdu (27 Agu 2026): biri yanlis
    notlu (`answer_changes > 0`, K2 oncesi uretim UPSERT'i `is_correct`i
    guncellemiyordu), besi "cevap temizlenmis ama not duruyor". Ureticinin
    duzeldigi canli olculdu ve satirlar geriye donuk duzeltildi -- ama
    ureticiyi koruyan BIR DAVRANIS testi yoktu.

    Var olan bekci `test_save_answer_upsert_parity.py` UPSERT'in SQL SEKLINI
    civiliyor (`is_correct: stmt.excluded.is_correct`). Bu YETMEZ: notu
    URETEN blok (`save_answer` icindeki `question_content.correct_answer`
    sorgusu) bozulsa `is_correct` her yazimda sessizce NULL olurdu ve sekil
    testi YESIL kalirdi -- `except Exception: logger.debug(...)` onu yutuyor.
    Yani sozlesme dogru, URETIM olu olabilir. Bu test o boslugu kapatir.

    UC GECIS de olculur, cunku fosillerin IKI ayri sinifi vardi:
      notla -> temizle (NULL olmali)  ·  yanlisa degis (yeniden notlanmali)
    """
    engine, session_id, question_id, satiri_oku = sinav_ortami

    await engine.save_answer(session_id, question_id, ILK_CEVAP)
    satir = await satiri_oku()
    assert satir is not None, "On kosul: ilk cevap DB'ye yazilmadi"

    dogru = satir["correct_answer"]
    # ALET DOGRULAMASI: dogru cevap yoksa asagidaki assert'ler VAKUMDA gecerdi.
    assert dogru, (
        "Secilen sorunun `question_content.correct_answer` degeri bos -- "
        "bu test hicbir sey olcemez. Fikstur baska bir soru secmeli."
    )
    dogru_harf = str(dogru).strip().upper()

    assert satir["is_correct"] is (dogru_harf == ILK_CEVAP), (
        f"Ilk yazimda not yanlis: cevap={ILK_CEVAP!r} dogru={dogru_harf!r} "
        f"is_correct={satir['is_correct']!r}. `is_correct` HIC hesaplanmiyorsa "
        "(None) notlama blogu sessizce dusuyordur (save_answer icindeki "
        "`except Exception: logger.debug`)."
    )

    # 2) TEMIZLE -> not da silinmeli (5 fosil satirin sinifi)
    await engine.save_answer(session_id, question_id, TEMIZLE)
    temiz = await satiri_oku()
    assert temiz is not None, "Satir tamamen kayboldu"
    assert temiz["is_correct"] is None, (
        "Cevap temizlendi ama not DURUYOR: "
        f"is_correct={temiz['is_correct']!r}. Ogrencinin cevabi yokken "
        "'dogru/yanlis' demek analitigi ve mastery'yi kirletir."
    )

    # 3) DOGRU cevaba gec -> True
    await engine.save_answer(session_id, question_id, dogru_harf)
    d = await satiri_oku()
    assert d is not None and d["is_correct"] is True, (
        f"Dogru cevap {dogru_harf!r} yazildi ama is_correct="
        f"{d['is_correct'] if d else None!r}"
    )

    # 4) YANLIS cevaba gec -> False (1 fosil satirin sinifi: cakismada
    #    not yeniden hesaplanmiyordu)
    yanlis_harf = "A" if dogru_harf != "A" else "B"
    await engine.save_answer(session_id, question_id, yanlis_harf)
    y = await satiri_oku()
    assert y is not None and y["is_correct"] is False, (
        f"Cevap {dogru_harf!r} -> {yanlis_harf!r} degisti ama is_correct="
        f"{y['is_correct'] if y else None!r}. Cakisma dalinda not YENIDEN "
        "hesaplanmiyor (K2'nin sinifi geri gelmis olabilir)."
    )
