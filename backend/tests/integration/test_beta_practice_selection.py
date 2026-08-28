"""Beta pratik soru seçimi testleri.

Beta pratik modu, kör-çözüm doğrulamasından geçmiş (pipeline_metadata.
verified_provisional == 'true') ~2,734 çekirdek soruyu kullanır. Standart ÖSYM
soru-seçim base_filters'ı (uzunluk>=50, passage regex, geometri-görsel şartı
vb.) bu mod için UYGULANMAZ — gate, o sezgisel proxy'lerden daha güçlü bir
kalite kanıtı sağlar (öğrenci-eşdeğeri kör çözüm).

Mock kullanılmaz: beta havuzu yalnızca prod DB'de (port 5434) bulunduğu için
testler gerçek DB'ye karşı çalışır; DB ulaşılamazsa skip eder (repo deseni).
"""

import pytest

from core.osym_exam_engine import OSYMExamConfig, OSYMExamEngine
from tests.integration.conftest import canli_dsn_cozumle


@pytest.fixture
async def canli_db_baglantisi(override_database_manager):
    """Uretim kodunun kullandigi ``get_db_session_context()``'i CANLI PG'ye baglar.

    NEDEN VAR (iki katman, ikisi de olculdu):

    1. ``tests/conftest.py:100`` kosum ortaminda ``DATABASE_URL``'i
       ``sqlite+aiosqlite:///:memory:`` yapiyor.
    2. ``tests/conftest.py:148`` ``override_database_manager`` AUTOUSE ve
       FONKSIYON kapsamli: her testten once ``db_manager.engine``'i paylasilan
       sqlite motoruna cevirir.

    Sonuc: ``_select_beta_questions`` testte BOS bir in-memory sqlite'a
    baglaniyor, havuz 0 cikiyor ve bu dosyadaki testler "DB yok" gerekcesiyle
    SESSIZCE skip ediyordu (olcum: 3 skipped). Bu fixture ``override_database_
    manager``'i ACIKCA talep eder -> pytest onu ONCE kurar, biz SONRA
    ezeriz; teardown sirasi da tersine isler.

    Kanonik cozucu ``canli_dsn_cozumle()`` postgres olmayan DSN'i reddeder,
    yani sqlite'a sessizce DUSULMEZ.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.ext.asyncio import create_async_engine as _motor_yap

    dsn = canli_dsn_cozumle()
    if not dsn:
        pytest.skip(
            "Canli DSN cozulemedi — KIRO2_TEST_DSN / KVKK_VERIFY_DSN / "
            "backend/.env gerekli"
        )

    from core.database import db_manager

    canli_motor = _motor_yap(dsn)
    onceki = (db_manager.engine, db_manager.async_session_maker)
    db_manager.engine = canli_motor
    db_manager.async_session_maker = async_sessionmaker(
        canli_motor, class_=AsyncSession, expire_on_commit=False
    )
    db_manager._initialized = True
    try:
        yield dsn
    finally:
        db_manager.engine, db_manager.async_session_maker = onceki
        await canli_motor.dispose()


async def _kapi_id_kumesi(dsn: str) -> set[str]:
    """Kalite kapisinin (``mv_safe_for_beta``) id kumesi — BAGIMSIZ olcum.

    Uretim kod yolundan (``get_db_session_context``) degil, dogrudan kendi
    engine'i uzerinden okur; boylece kapi iddiasi ayni aletle olculmez.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(dsn)
    try:
        async with engine.connect() as conn:
            sonuc = await conn.execute(text("SELECT id FROM mv_safe_for_beta"))
            return {satir[0] for satir in sonuc}
    finally:
        await engine.dispose()


async def _exam_type_kumesi(dsn: str, ids: set[str]) -> set[str]:
    """Verilen id'lerin ``question_metadata.exam_type`` degerleri."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(dsn)
    try:
        async with engine.connect() as conn:
            sonuc = await conn.execute(
                text(
                    "SELECT DISTINCT exam_type FROM question_metadata "
                    "WHERE id = ANY(:ids)"
                ),
                {"ids": list(ids)},
            )
            return {satir[0] for satir in sonuc}
    finally:
        await engine.dispose()


async def _beklenen_havuz_boyutu(dsn: str, exam_type: str) -> int:
    """Kapidan gecen + istenen sinav tipindeki beta havuzunun CANLI boyutu.

    KONTROL KOLU: fix'in asiriya kacmadigini civiler. ``return []`` veya
    fazla-daraltan bir "duzeltme" ust iki testi de gecerdi; bu sayi gecmez.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(dsn)
    try:
        async with engine.connect() as conn:
            sonuc = await conn.execute(
                text(
                    "SELECT count(*) FROM question_bank qb "
                    "JOIN question_metadata qm ON qm.id = qb.id "
                    "WHERE qb.is_active = true "
                    "AND qm.pipeline_metadata->>'verified_provisional' = 'true' "
                    "AND qm.exam_type = :et "
                    "AND qb.id IN (SELECT id FROM mv_safe_for_beta)"
                ),
                {"et": exam_type},
            )
            return sonuc.scalar() or 0
    finally:
        await engine.dispose()


async def _beta_pool_available() -> bool:
    """Gerçek DB erişilebilir ve beta havuzu dolu mu?"""
    try:
        from sqlalchemy import func, select

        from core.database import get_db_session_context
        from models.question_bank import QuestionBankItem as Question
        from models.question_bank import QuestionMetadata

        async with get_db_session_context() as db_session:
            result = await db_session.execute(
                # #485: pipeline_metadata artik QuestionMetadata'da. Eskiden burada
                # Question.pipeline_metadata yaziyordu -> strangler devredicisi SINIF
                # duzeyinde AttributeError atiyor, asagidaki `except Exception` onu
                # yutuyor ve fixture "DB yok" sanip 3 testi de SESSIZCE skip ediyordu.
                select(func.count())
                .select_from(Question)
                .join(QuestionMetadata, QuestionMetadata.id == Question.id)
                .where(
                    Question.is_active.is_(True),
                    QuestionMetadata.pipeline_metadata.op("->>")("verified_provisional")
                    == "true",
                )
            )
            return (result.scalar() or 0) >= 20
    except Exception:
        return False


async def _beta_clean_olmayanlar(dsn: str, ids: set[str]) -> set[str]:
    """``verified_provisional`` != true olan id'ler.

    ONCEDEN ``_is_beta_clean(question)`` vardi ve ``question.pipeline_metadata``
    okuyordu. #485 sonrasi bu alan ``metadata_info`` iliskisine devrediliyor;
    ``_select_beta_questions`` nesneleri session KAPANDIKTAN sonra donduruyor ->
    ``DetachedInstanceError``. Olcum artik ORM tembel-yuklemesine degil bagimsiz
    SQL'e dayaniyor (JSON true / string "true" ikisi de kabul).
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(dsn)
    try:
        async with engine.connect() as conn:
            sonuc = await conn.execute(
                text(
                    "SELECT id FROM question_metadata "
                    "WHERE id = ANY(:ids) "
                    "AND coalesce(pipeline_metadata->>'verified_provisional','') "
                    "<> 'true'"
                ),
                {"ids": list(ids)},
            )
            return {satir[0] for satir in sonuc}
    finally:
        await engine.dispose()


@pytest.fixture
async def beta_pool_ready(canli_db_baglantisi):
    if not await _beta_pool_available():
        pytest.skip("Beta clean havuzu (>=20) erişilemez — gerçek DB gerekli")
    return canli_db_baglantisi


async def test_select_beta_questions_returns_requested_count(beta_pool_ready):
    """İstenen sayıda soru döndürür (havuz >= istenen)."""
    engine = OSYMExamEngine()
    questions = await engine._select_beta_questions(20, "TYT")
    assert len(questions) == 20


async def test_select_beta_questions_all_beta_clean(beta_pool_ready):
    """Dönen her soru verified_provisional ve aktif."""
    dsn = beta_pool_ready
    engine = OSYMExamEngine()
    questions = await engine._select_beta_questions(20, "TYT")
    assert questions, "Beta havuzundan soru gelmedi"
    for q in questions:
        assert q.is_active is True
    kirli = await _beta_clean_olmayanlar(dsn, {q.id for q in questions})
    assert not kirli, f"beta_clean olmayan sorular dondu: {sorted(kirli)[:3]}"


async def test_select_beta_questions_caps_at_pool_size(beta_pool_ready):
    """İstenen sayı havuzdan büyükse havuz boyutuyla sınırlanır (çökmez)."""
    dsn = beta_pool_ready
    engine = OSYMExamEngine()
    questions = await engine._select_beta_questions(10_000, "TYT")
    assert 0 < len(questions) <= 10_000
    # Tümü yine beta_clean olmalı
    assert not await _beta_clean_olmayanlar(dsn, {q.id for q in questions})


# ===========================================================================
# K3 — ogrenci KALITE KAPISI + sinav tipi (core/quality_gate.py politikasi)
# ===========================================================================
# 10_000 istenir cunku havuzun TAMAMI cekilir -> orneklem-flake olmaz:
# random.sample(pool, min(count, len(pool))) havuzun kendisini dondurur.


async def test_beta_questions_kalite_kapisinin_alt_kumesi(beta_pool_ready):
    """Donen her soru ``mv_safe_for_beta`` icinde olmali.

    ``core/quality_gate.py``: ogrenciye icerik donen HER sorgu kapidan gecer.
    Beta dali kapiyi uygulamiyordu; ayni dosyadaki standart dal (:1586)
    uyguluyordu.
    """
    dsn = beta_pool_ready
    engine = OSYMExamEngine()
    questions = await engine._select_beta_questions(10_000, "TYT")
    donen = {q.id for q in questions}
    assert donen, "Beta havuzundan soru gelmedi"

    kapi = await _kapi_id_kumesi(dsn)
    disarida = donen - kapi
    assert not disarida, (
        f"{len(disarida)}/{len(donen)} soru mv_safe_for_beta DISINDA "
        f"(ornek: {sorted(disarida)[:3]})"
    )

    # KONTROL KOLU: kapi uygulandi diye havuz bosalmamali/asiri daralmamali.
    beklenen = await _beklenen_havuz_boyutu(dsn, "TYT")
    assert len(donen) == beklenen, (
        f"Kapidan gecen TYT havuzu {beklenen}, donen {len(donen)} — "
        f"fix ya bos donduruyor ya da fazla daraltiyor"
    )


async def test_beta_questions_istenen_sinav_tipinde(beta_pool_ready):
    """ "TYT" istenince AYT sorusu donmemeli.

    Olculdu: "tyt" ilan edilen oturumlara AYT sorusu girdi. Havuzda
    exam_type=AYT olan 356 soru var ve beta dali exam_type'i hic gormuyordu.
    """
    dsn = beta_pool_ready
    engine = OSYMExamEngine()
    questions = await engine._select_beta_questions(10_000, "TYT")
    donen = {q.id for q in questions}
    assert donen, "Beta havuzundan soru gelmedi"

    tipler = await _exam_type_kumesi(dsn, donen)
    assert tipler == {"TYT"}, f"Beklenen {{'TYT'}}, donen exam_type kumesi: {tipler}"


async def test_beta_havuz_cache_sinav_tipine_gore_ayrisir(beta_pool_ready):
    """TTLCache anahtari exam_type icermezse AYT cagrisi TYT havuzunu doner.

    Ayni motor ORNEGI uzerinden iki dal cagrilir: cache anahtari dallari
    ayirmiyorsa ikinci cagri birincinin havuzunu okur ve iki id kumesi
    ortusur. (`_question_pool_cache` ornek duzeyinde, ttl=3600.)
    """
    dsn = beta_pool_ready
    engine = OSYMExamEngine()

    tyt = {q.id for q in await engine._select_beta_questions(10_000, "TYT")}
    ayt = {q.id for q in await engine._select_beta_questions(10_000, "AYT")}
    assert tyt and ayt, f"TYT={len(tyt)} AYT={len(ayt)} — bir dal bos"
    assert not (tyt & ayt), (
        f"{len(tyt & ayt)} soru iki dalda da dondu — cache anahtari "
        f"exam_type'i ayirmiyor"
    )
    assert len(ayt) == await _beklenen_havuz_boyutu(dsn, "AYT")


async def test_select_questions_beta_dali_config_sinav_tipini_gecirir(
    beta_pool_ready,
):
    """URETIM KABLOSU: ``_select_questions`` beta dali config'in tipini gecirir.

    NEDEN VAR (mutasyonla olculdu): cagri yerindeki
    ``exam_config.exam_type.value.upper()`` sabit ``"AYT"`` ile degistirildiginde
    diger 5 beta testi de dahil HICBIR test dusmedi (1 failed / 33 passed =
    taban). Fonksiyonu dogrudan cagiran test, o fonksiyonun URETIMDE dogru
    argumanla cagrildigini KANITLAMAZ — iki ayri sozlesme.

    Ders #26: enum degeri lowercase ("tyt"), DB UPPERCASE ("TYT").
    """
    from models.database import ExamType

    dsn = beta_pool_ready
    config = OSYMExamConfig(
        exam_type=ExamType.TYT,
        total_questions=10_000,
        duration_minutes=135,
        subject_distribution={},
        beta_practice=True,
    )
    questions = await OSYMExamEngine()._select_questions(config)
    donen = {q.id for q in questions}
    assert donen, "Beta dalindan soru gelmedi"
    assert await _exam_type_kumesi(dsn, donen) == {"TYT"}
    # KONTROL KOLU: dogru dal + dogru tip -> kapidan gecen TYT havuzunun TAMAMI
    assert len(donen) == await _beklenen_havuz_boyutu(dsn, "TYT")
