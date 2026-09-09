"""Mufredat agaci saglik bekcileri -- 9 Eyl 2026 canli olcumu.

KUSUR
-----
topic_hierarchy'de `subject_area` DOLU ama `parent_id` NULL olan 14 konu
vardi. services/question_bank_service.py:226-231 "kok konu" tanimini
`parent_id IS NULL` uzerinden yaptigi icin bu konular ana konu listesinde
DERS gibi gorunuyordu:

    get_topic_hierarchy(parent_id=None) -> 28 kayit
      KIM     Kimya              soru=263
      KIM.DEN Kimyasal Denge     soru=1262   <- konu, ders degil
      TYT-KIM-01 Atom Yapisi     soru=277    <- konu, ders degil
      ...

Ve Kimya'nin alt konu sayisi 0'di -- en cok icerige sahip derse (3.531
soru) tiklayan ogrenci bos liste goruyordu.

Agac disinda asili konulara bagli soru: 3.266 / 5.796 (%56).

Bu testler `alembic/versions/0005_mufredat_agaci_onarim.py` ile yapilan
onarimin geri gitmemesini sabitler.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def baglanti():
    dsn = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)
    motor = create_async_engine(dsn, poolclass=NullPool)
    try:
        conn = await motor.connect()
    except Exception as exc:  # DB ayakta degil -- kapiyi fail-close etme
        await motor.dispose()
        pytest.skip(f"DB erisilemiyor: {type(exc).__name__}")
    try:
        yield conn
    finally:
        await conn.close()
        await motor.dispose()


async def test_ders_belirten_konu_agacta_asili_kalmaz(baglanti) -> None:
    """subject_area DOLU olan her konunun bir ebeveyni olmali."""
    sonuc = await baglanti.execute(
        text(
            """
            SELECT code, name_tr, subject_area,
                   (SELECT count(*) FROM question_bank b
                     WHERE b.primary_topic_id = t.id) AS soru
              FROM topic_hierarchy t
             WHERE t.subject_area IS NOT NULL
               AND t.parent_id IS NULL
               AND t.is_active IS TRUE
             ORDER BY 4 DESC
            """
        )
    )
    asili = sonuc.fetchall()
    if asili:
        dokum = "\n".join(
            f"  {r.code:<14} {r.name_tr:<32} soru={r.soru}" for r in asili
        )
        pytest.fail(
            f"{len(asili)} konu bir derse bagli degil ve ana konu listesinde "
            f"DERS gibi gorunuyor:\n{dokum}"
        )


async def test_icerigi_olan_dersin_alt_konusu_vardir(baglanti) -> None:
    """Soru barindiran bir ders koku, en az bir alt konuya sahip olmali.

    Kusurun en somut hali: Kimya 3.531 soruya sahipti ve alt konu sayisi 0'di.
    """
    sonuc = await baglanti.execute(
        text(
            """
            SELECT k.code,
                   (SELECT count(*) FROM topic_hierarchy c
                     WHERE c.parent_id = k.id AND c.is_active IS TRUE) AS alt_konu,
                   (SELECT count(*) FROM question_bank b
                      JOIN question_metadata m ON m.id = b.id
                     WHERE m.subject_area = upper(k.name_tr)) AS soru
              FROM topic_hierarchy k
             WHERE k.parent_id IS NULL
               AND k.subject_area IS NULL
               AND k.is_active IS TRUE
            """
        )
    )
    bos = [r for r in sonuc.fetchall() if r.soru > 0 and r.alt_konu == 0]
    if bos:
        dokum = "\n".join(f"  {r.code}: {r.soru} soru, 0 alt konu" for r in bos)
        pytest.fail(f"Icerigi olan ama alt konusu olmayan ders(ler):\n{dokum}")


async def test_cocuk_seviyesi_ebeveyn_arti_bir(baglanti) -> None:
    """level tutarliligi: cocuk.level == ebeveyn.level + 1."""
    sonuc = await baglanti.execute(
        text(
            """
            SELECT c.code, c.level, p.code AS ebeveyn, p.level AS ebeveyn_level
              FROM topic_hierarchy c
              JOIN topic_hierarchy p ON p.id = c.parent_id
             WHERE c.level <> p.level + 1
            """
        )
    )
    bozuk = sonuc.fetchall()
    assert not bozuk, f"Seviye tutarsizligi: {[tuple(r) for r in bozuk]}"


async def test_test_artigi_uretim_agacinda_aktif_degil(baglanti) -> None:
    """Test fixture'lari ogrenciye gosterilen listede olmamali."""
    sonuc = await baglanti.execute(
        text(
            """
            -- Desen, 0005_mufredat_agaci_onarim.py'deki pasiflestirme
            -- kuraliyla BIREBIR ayni tutuluyor; ikisi ayrisirsa migration
            -- temizledigini saniyor ama bekci baska bir sey ariyor olurdu.
            -- Gozlenen adlandirma: TEST.BATCH2A (yerel), TEST.BATCH1B (CI),
            -- adlari "Test Konu Batch...".
            SELECT code, name_tr FROM topic_hierarchy
             WHERE is_active IS TRUE
               AND (code LIKE 'TEST.%' OR name_tr ILIKE 'Test Konu%')
            """
        )
    )
    artik = sonuc.fetchall()
    assert (
        not artik
    ), f"Uretim mufredat agacinda aktif test artigi var: {[tuple(r) for r in artik]}"


async def test_total_questions_sayaci_gercekle_uyusur(baglanti) -> None:
    """Denormalize sayac gercek sayimdan sapmamali.

    Olculdu (9 Eyl 2026): 57 konuda sapma vardi -- 56'sinda sayac 0 iken
    gercek sayim 1.262'ye kadar cikiyordu, MAT.TRV'de ise ters yonde
    (sayac 129, gercek 0). Bu alani okuyan her ekran yanlis sayi gosterir.
    """
    sonuc = await baglanti.execute(
        text(
            """
            SELECT t.code, t.total_questions AS sayac, count(b.id) AS gercek
              FROM topic_hierarchy t
              LEFT JOIN question_bank b
                     ON b.primary_topic_id = t.id AND b.is_active IS TRUE
             GROUP BY t.code, t.total_questions
            HAVING t.total_questions IS DISTINCT FROM count(b.id)
             ORDER BY count(b.id) DESC
            """
        )
    )
    sapma = sonuc.fetchall()
    if sapma:
        dokum = "\n".join(
            f"  {r.code:<14} sayac={r.sayac} gercek={r.gercek}" for r in sapma[:20]
        )
        pytest.fail(f"{len(sapma)} konuda total_questions sapmasi:\n{dokum}")
