"""RLS kiracı GUC'unun canlı Postgres'e karşı bekçisi (S241 B1).

Bu test **gerçek veritabanına** koşar. Sebep yapısal: kusur SQLAlchemy'de değil,
Postgres'in RLS motorunda yaşıyordu. `sqlite` veya mock'lu bir test bu sınıfı
**göremez** — nitekim aylarca göremedi: `exam_sessions` tablosunda bugüne kadar
**0 satır** var ve hiçbir test bunu yakalamadı.

Ölçülen kusur: `tenant_isolation` politikası fail-closed
(`WITH CHECK (organization_id::text = current_setting('app.current_org_id', true))`).
GUC set edilmemiş bağlantıda `current_setting(...,true)` NULL döner,
`'org_legacy_default' = NULL` → NULL → INSERT reddedilir.

DSN yoksa test **skip** olur (sessizce sqlite'a DÜŞMEZ — `L-...-test-dsn` kuralı).
Denetim: `docs/audits/2026-08-20_a1_altin_yol_olcum.md` B1
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from core.tenant_context import (
    aktif_kullaniciyi_kur,
    kiraci_baglamini_temizle,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def _temiz_baglam():
    kiraci_baglamini_temizle()
    yield
    kiraci_baglamini_temizle()


@pytest.fixture
async def db_yoneticisi():
    """Postgres DSN'inden KENDI motorunu kurar.

    Global `db_manager`'a BAĞLANMAZ — `tests/conftest.py:153-169` onu test
    süresince sqlite motoruna monkeypatch ediyor ve hangi testin o fixture
    aktifken koştuğuna göre lehçe DEĞİŞİYOR. Ölçüldü: aynı koşumda ilk test
    sqlite, kalan üçü postgresql görüyordu — yani kontrol kolu rastgele
    skip oluyordu, ki bu bir bekçide kabul edilemez.

    Dinleyici (`core/database._rls_guc_kur`) `sqlalchemy.orm.Session` üzerine
    GLOBAL kayıtlı olduğu için kendi motorumuz da onu tetikler; gerçek kanca
    ölçülmeye devam eder.

    DSN yoksa veya postgres değilse SKIP — sessizce sqlite'a DÜŞMEZ.
    """
    import os

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    import core.database as _db_modulu  # noqa: F401 - dinleyicinin kaydini garanti eder

    dsn = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
    if "postgresql" not in dsn:
        pytest.skip(f"postgresql DSN gerekli (TEST_DATABASE_URL/DATABASE_URL): {dsn!r}")

    motor = create_async_engine(dsn, poolclass=NullPool)
    fabrika = async_sessionmaker(motor, expire_on_commit=False)

    class _Yonetici:
        @staticmethod
        def get_session():
            return fabrika()

    try:
        yield _Yonetici()
    finally:
        await motor.dispose()


async def _bir_ogrenci_id(db_yoneticisi) -> str:
    async with db_yoneticisi.get_session() as s:
        satir = (
            await s.execute(
                text("SELECT id FROM users WHERE organization_id IS NOT NULL LIMIT 1")
            )
        ).first()
    if satir is None:
        pytest.skip("users tablosunda org'lu kullanıcı yok")
    return str(satir[0])


async def test_baglam_yokken_guc_kurulmaz(db_yoneticisi):
    """KONTROL KOLU: kanca körü körüne değil, koşullu çalışıyor.

    Bu assert olmadan "GUC hep set ediliyor" yazan bir gövde de yeşil kalırdı ve
    arka plan işleri (Celery) yanlış kiracıyla koşabilirdi.
    """
    async with db_yoneticisi.get_session() as s:
        deger = (
            await s.execute(text("SELECT current_setting('app.current_org_id', true)"))
        ).scalar()
    assert deger in (None, ""), f"bağlam yokken GUC kurulmuş: {deger!r}"


async def test_baglam_varken_guc_kullanicinin_orgunu_tasir(db_yoneticisi):
    ogrenci_id = await _bir_ogrenci_id(db_yoneticisi)
    async with db_yoneticisi.get_session() as s:
        beklenen = (
            await s.execute(
                text("SELECT organization_id FROM users WHERE id = :uid"),
                {"uid": ogrenci_id},
            )
        ).scalar()

    aktif_kullaniciyi_kur(ogrenci_id)
    async with db_yoneticisi.get_session() as s:
        gelen = (
            await s.execute(text("SELECT current_setting('app.current_org_id', true)"))
        ).scalar()
    assert gelen == str(beklenen), f"GUC {gelen!r}, beklenen {beklenen!r}"


async def test_exam_sessions_insert_baglamsiz_reddedilir(db_yoneticisi):
    """Kusurun kendisi: bağlam yokken RLS INSERT'i keser.

    Bu test düzeltmeden ÖNCE de geçerdi — kusuru değil, **RLS'in gerçekten
    uygulandığını** çiviler. Kaldırılırsa bir sonraki tur "RLS zaten kapalıymış"
    diye yanlış sonuca varabilir.
    """
    from sqlalchemy.exc import DBAPIError

    ogrenci_id = await _bir_ogrenci_id(db_yoneticisi)
    with pytest.raises(DBAPIError) as yakalanan:
        async with db_yoneticisi.get_session() as s:
            await s.execute(
                text(
                    "INSERT INTO exam_sessions "
                    "(id, student_id, organization_id, exam_type, exam_name, "
                    " total_questions, duration_minutes, status, "
                    " current_question_index, time_spent_seconds, "
                    " total_correct, total_wrong, total_empty, "
                    " raw_score, estimated_ability, ability_confidence) "
                    "VALUES (:sid, :uid, 'org_legacy_default', 'TYT', 'RLS BEKCI', "
                    " 1, 1, 'not_started', 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)"
                ),
                {"sid": str(uuid.uuid4()), "uid": ogrenci_id},
            )
            await s.commit()

    # SIKI ANKRAJ: hata RLS'ten gelmeli. Gevsek `pytest.raises(DBAPIError)` bir
    # NOT NULL ihlaliyle de gecerdi -- ilk yazimda tam olarak bu oldu ve test
    # YANLIS SEBEPLE yesil kalabilirdi. Mesaj Postgres'in RLS reddine ozgu.
    metin = str(yakalanan.value).lower()
    assert (
        "row-level security" in metin or "insufficientprivilege" in metin
    ), f"hata RLS kaynakli DEGIL, test yanlis sebeple gecmis olabilir: {metin[:300]}"


async def test_exam_sessions_insert_baglamla_gecer(db_yoneticisi):
    """Düzeltmenin yük taşıyan assert'i — bu, A1'in teslim ayağının kendisi.

    Satır yazılır, geri okunur ve **silinir** (test kalıcı veri bırakmaz).
    """
    ogrenci_id = await _bir_ogrenci_id(db_yoneticisi)
    aktif_kullaniciyi_kur(ogrenci_id)
    sid = str(uuid.uuid4())

    async with db_yoneticisi.get_session() as s:
        org = (
            await s.execute(
                text("SELECT organization_id FROM users WHERE id = :uid"),
                {"uid": ogrenci_id},
            )
        ).scalar()
        await s.execute(
            text(
                "INSERT INTO exam_sessions "
                "(id, student_id, organization_id, exam_type, exam_name, "
                " total_questions, duration_minutes, status, "
                " current_question_index, time_spent_seconds, "
                " total_correct, total_wrong, total_empty, "
                " raw_score, estimated_ability, ability_confidence) "
                "VALUES (:sid, :uid, :org, 'TYT', 'RLS BEKCI', "
                " 1, 1, 'not_started', 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)"
            ),
            {"sid": sid, "uid": ogrenci_id, "org": str(org)},
        )
        await s.commit()

    try:
        async with db_yoneticisi.get_session() as s:
            okunan = (
                await s.execute(
                    text("SELECT exam_name FROM exam_sessions WHERE id = :sid"),
                    {"sid": sid},
                )
            ).scalar()
        assert okunan == "RLS BEKCI", "satır yazıldı ama RLS okumada kesti"
    finally:
        aktif_kullaniciyi_kur(ogrenci_id)
        async with db_yoneticisi.get_session() as s:
            await s.execute(
                text("DELETE FROM exam_sessions WHERE id = :sid"), {"sid": sid}
            )
            await s.commit()
