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


async def test_ayni_ebeveyn_altinda_ayni_adli_aktif_konu_tek(baglanti) -> None:
    """Cift taksonomi bekcisi (9 Eyl 2026, migration 0006).

    Olculdu: TUR altinda "Paragraf" iki kez (TUR.PAR 7 soru, TYT-TR-03 134
    soru) ve "Dil Bilgisi" iki kez (TUR.DIL 9, TYT-TR-02 51). Ogrenci ayni
    konuyu iki kez goruyor, ilerleme ikiye bolunuyordu. Kural: ayni ebeveyn
    altinda ayni adli aktif konu en fazla BIR tane.

    Farkli ebeveyn altindaki ayni ad (GEO koku vs MAT.GEO) bilincli olarak
    kapsam DISI -- o ikisi kopya degil (bkz. 0006 docstring).
    """
    sonuc = await baglanti.execute(
        text(
            """
            SELECT p.code AS ebeveyn, lower(c.name_tr) AS ad,
                   array_agg(c.code ORDER BY c.code) AS kodlar
              FROM topic_hierarchy c
              JOIN topic_hierarchy p ON p.id = c.parent_id
             WHERE c.is_active IS TRUE
             GROUP BY p.code, lower(c.name_tr)
            HAVING count(*) > 1
             ORDER BY 1, 2
            """
        )
    )
    kopya = sonuc.fetchall()
    if kopya:
        dokum = "\n".join(f"  {r.ebeveyn} / {r.ad}: {r.kodlar}" for r in kopya)
        pytest.fail(f"Ayni ebeveyn altinda ayni adli birden fazla aktif konu:\n{dokum}")


# 0005'in ders -> kok kodu eslemesi (migration'daki CTE ile ayni; ikisi de
# olculmus canli veriden). Bir konu subject_area tasiyorsa, agacta yukari
# cikildiginda ulasilan kok BU kod olmali -- MAT.GEO'nun GEOMETRI etiketiyle
# GEO altina tasinmasi (0007) bu sozlesmeyi korur; MATEMATIK etiketiyle GEO
# altina konsaydi (ya da tersi) burasi duserdi.
_DERS_KOKU = {
    "FIZIK": "FIZ",
    "KIMYA": "KIM",
    "BIYOLOJI": "BIO",
    "MATEMATIK": "MAT",
    "GEOMETRI": "GEO",
    "TURKCE": "TUR",
    "EDEBIYAT": "EDB",
    "TARIH": "TAR",
    "COGRAFYA": "COG",
    "SOSYAL": "SOS",
    "FEN": "FEN",
    "GENEL": "GEN",
    "PARAGRAF": "PAR",
}


async def test_konunun_dersi_ile_koku_uyusur(baglanti) -> None:
    """subject_area tasiyan aktif konu, o dersin kokunun alt agacinda olmali."""
    sonuc = await baglanti.execute(
        text(
            """
            WITH RECURSIVE yukari AS (
                SELECT id, code, parent_id, upper(subject_area) AS ders, id AS baslangic
                  FROM topic_hierarchy WHERE is_active AND subject_area IS NOT NULL
                UNION ALL
                SELECT p.id, p.code, p.parent_id, y.ders, y.baslangic
                  FROM topic_hierarchy p JOIN yukari y ON p.id = y.parent_id
            )
            SELECT b.code AS konu, y.ders, y.code AS kok
              FROM yukari y JOIN topic_hierarchy b ON b.id = y.baslangic
             WHERE y.parent_id IS NULL
             ORDER BY 1
            """
        )
    )
    yanlis = [
        (r.konu, r.ders, r.kok)
        for r in sonuc.fetchall()
        if _DERS_KOKU.get(r.ders) not in (None, r.kok)
    ]
    assert not yanlis, f"dersi ile koku uyusmayan konular (konu, ders, kok): {yanlis}"


async def test_geometri_kokundeki_sorular_geometri_etiketli(baglanti) -> None:
    """GEO alt agacindaki aktif sorularin question_metadata.subject_area'si GEOMETRI.

    0007 bekcisi: konu tasinip sorular etiketlenmezse (ya da tersi) duser.
    Taze DB'de GEO altinda soru yoktur -> bos kume, gecer (yapisal sozlesme).
    """
    sonuc = await baglanti.execute(
        text(
            """
            WITH RECURSIVE geo AS (
                SELECT id FROM topic_hierarchy
                 WHERE code = 'GEO' AND parent_id IS NULL AND subject_area IS NULL
                UNION ALL
                SELECT c.id FROM topic_hierarchy c JOIN geo g ON c.parent_id = g.id
            )
            SELECT upper(m.subject_area) AS alan, count(*) AS adet
              FROM question_bank b
              JOIN question_metadata m ON m.id = b.id
             WHERE b.is_active AND b.primary_topic_id IN (SELECT id FROM geo)
             GROUP BY 1
            """
        )
    )
    dagilim = {r.alan: r.adet for r in sonuc.fetchall()}
    yabanci = {k: v for k, v in dagilim.items() if k != "GEOMETRI"}
    assert not yabanci, f"GEO alt agacinda GEOMETRI olmayan soru: {yabanci}"


async def test_sorunun_dersi_ile_konusunun_koku_uyusur(baglanti) -> None:
    """Aktif sorunun question_metadata.subject_area'si, konusunun kokuyle uyusmali.

    0009 bekcisi: 21 soru dogrudan yanlis derse ait bir koke bagliydi (FIZ
    kokunde KIMYA, SOS kokunde TARIH/COGRAFYA, FEN kokunde KIMYA); elle
    okundu, icerik etiketle uyusuyordu, konu yanlisti. Sozlesme genel:
    hangi kok altinda olursa olsun, sorunun dersi kokun dersi olmali.
    Taze DB'de soru yoktur -> bos kume, gecer.
    """
    sonuc = await baglanti.execute(
        text(
            """
            WITH RECURSIVE yukari AS (
                SELECT t.id, t.code, t.parent_id, t.id AS baslangic
                  FROM topic_hierarchy t
                UNION ALL
                SELECT p.id, p.code, p.parent_id, y.baslangic
                  FROM topic_hierarchy p JOIN yukari y ON p.id = y.parent_id
            )
            SELECT y.code AS kok, upper(m.subject_area) AS ders, count(*) AS adet
              FROM question_bank b
              JOIN question_metadata m ON m.id = b.id
              JOIN yukari y ON y.baslangic = b.primary_topic_id AND y.parent_id IS NULL
             WHERE b.is_active AND m.subject_area IS NOT NULL
             GROUP BY 1, 2
             ORDER BY 1, 2
            """
        )
    )
    yanlis = [
        (r.kok, r.ders, r.adet)
        for r in sonuc.fetchall()
        if _DERS_KOKU.get(r.ders) not in (None, r.kok)
    ]
    assert not yanlis, f"dersi kokuyle uyusmayan sorular (kok, ders, adet): {yanlis}"
