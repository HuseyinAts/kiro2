"""345 2025 TYT Biyoloji Soru Bankasi konu agaci (14 konu).

Revision ID: 0022_biyo345tyt_konu_agaci
Revises: 0021_biyo345_konu_agaci
Create Date: 2026-09-15

NEDEN YENI BIR UNITE SETI
-------------------------
Canli DB olcumu (15 Eyl 2026): BIO agacinda 18 dugum var -- kok,
BIO-OSYM-GENEL ve 0021'in kurdugu BIO-U1..BIO-U16. Bu 16 unitenin HEPSI
AYT mufredati (Sinir Sistemi, Hormonlar, Duyu Organlari, ... Bitkilerde
Ureme ve Gelisme). Ayni olcumde biyoloji sorularinin 1328'i AYT, 6'si TYT.

Bu kitap TYT: OCR ciktisinin 222 sayfasinin 222'sinde `exam_type` = "TYT".
Konulari da 9-10. sinif mufredati (Hucrenin Yapisi, Enzimler, Canli
Alemleri, Mendel Genetigi, Ekosistem...). BIO-U1..U16 ile TEK BIR ORTUSME
YOK, yani var olan bir uniteye baglamak yanlis olurdu. 0013/0015/0017/0021
ile ayni gerekce: kitabin kendi yapisindan yeni bir unite seti kurulur.

Kod oneki BIO-T ("TYT"); `LIKE 'BIO-T%'` deseni ne koku, ne
BIO-OSYM-GENEL'i, ne de BIO-U* unitelerini KAPSAR.

AGACIN KAYNAGI: SAYFANIN KENDI BASLIK BANDI
-------------------------------------------
0017 (Mikro Geometri) ve geo345 ile ayni ilke: agac kitabin ICINDEKILER
sayfasindan DEGIL, her sayfanin KENDI BASLIK BANDINDAN uretildi. OCR
hattinin sayfa duzeyi `topic_title` alani tam olarak o banttir.

Olcum (birincil kaynak: ocr_json/, 15 Eyl 2026):
  * 219 soru sayfasinin 112'sinde bant VAR, 107'sinde YOK.
  * Bantli sayfalar 15 farkli metin veriyor; ikisi ayni baslik
    ("ESEYLI VE ESEYSIZ UREME" / "ESEYLI ve ESEYSIZ UREME"), buyuk-kucuk
    harf farki. Kanonlastirinca 14 konu kalir.
  * SIFIR SERBESTLIK DERECELI DOGRULAMA: bu 14 ad, sayfa sirasinda tam
    14 KOSU olusturuyor -- hicbir konu ikinci kez acilmiyor, hicbir konu
    baska bir blogun icinde gorunmuyor. Bant okunmasi yanlis olsaydi bir
    blogun ortasinda yabanci bir kosu belirirdi.

SEVIYE: yalnizca UNITE (level 2). Kitapta unite alti konu etiketi YOK;
sayfa ustundeki "Kazanim Odakli Sorular / Karma Sorular / OSYM Tadinda
Sorular / Orijinal Sorular / OSYM Kosesi - Cikmis Sorular" konu degil TEST
TURUDUR ve soru duzeyinde pipeline_metadata.test_turu olarak tasinir.
Var olmayan bir L3 katmani uydurulmadi.

NEDEN MIGRATION, NEDEN SCRIPT DEGIL
-----------------------------------
Konu agaci referans veridir: her ortamda ayni olmali, surumlenmeli, geri
alinabilmeli. Sorular ithal script'iyle gelir
(scripts/kitap/biyo345tyt_ithal.py). 0013/0015/0017/0021 ile ayni ayrim.

IDEMPOTENT
----------
Var olan kodlar ATLANIR. Olusturulan her dugumun id'si GUNLUK'e yazilir;
downgrade() yalnizca KENDI olusturdugu ve hicbir soru tasimayan dugumleri
siler (kullanilan varsa dokunmaz ve loglar).
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0022_biyo345tyt_konu_agaci"
down_revision: Union[str, None] = "0021_biyo345_konu_agaci"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "biyo345tyt_konu_gunlugu_0022"
BIO_KOK_KODU = "BIO"
KOD_ONEKI = "BIO-T"

# (sira, kod, ad) -- yorumdaki sayi veri setinden OLCULEN soru sayisidir.
# Sira kitabin sayfa sirasidir; adlar sayfa bandindan gelir, ASCII'ye
# duzlestirilmis halleriyle saklanir (agacin ev sozlesmesi).
KONULAR: tuple[tuple[int, str, str], ...] = (
    (1, "BIO-T1", "Biyoloji ve Canlilarin Ortak Ozellikleri"),  # 50
    (
        2,
        "BIO-T2",
        "Inorganik Bilesikler, Karbohidratlar, Lipitler, Proteinler, Vitaminler",
    ),  # 96
    (3, "BIO-T3", "Enzimler"),  # 63
    (4, "BIO-T4", "Nukleik Asitler"),  # 45
    (5, "BIO-T5", "ATP ve Saglikli Beslenme"),  # 48
    (6, "BIO-T6", "Hucrenin Yapisi"),  # 86
    (7, "BIO-T7", "Hucre Zarindan Madde Gecisleri"),  # 90
    (8, "BIO-T8", "Canlilarin Cesitliligi ve Siniflandirilmasi"),  # 47
    (9, "BIO-T9", "Canli Alemleri ve Virusler"),  # 112
    (10, "BIO-T10", "Hucre Bolunmeleri"),  # 74
    (11, "BIO-T11", "Eseyli ve Eseysiz Ureme"),  # 64
    (12, "BIO-T12", "Mendel Genetigi, Es Baskinlik, Cok Alellilik, Kan Gruplari"),  # 85
    (13, "BIO-T13", "Eseye Bagli Kalitim ve Genetik Varyasyonlar"),  # 69
    (14, "BIO-T14", "Ekosistem Ekolojisi ve Guncel Cevre Sorunlari"),  # 95
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'BIYOLOJI', TRUE, now(), now())
    """
)

_SAYAC_SQL = """
UPDATE topic_hierarchy t
   SET total_questions = COALESCE(g.adet, 0), updated_at = now()
  FROM (SELECT th.id, count(qb.id) AS adet
          FROM topic_hierarchy th
          LEFT JOIN question_bank qb
                 ON qb.primary_topic_id = th.id AND qb.is_active IS TRUE
         GROUP BY th.id) g
 WHERE g.id = t.id
   AND t.total_questions IS DISTINCT FROM COALESCE(g.adet, 0)
"""

_ACIKLAMA = (
    "345 2025 TYT Biyoloji Soru Bankasi sayfa baslik bandindan okundu "
    "(OCR sayfa alani topic_title); 219 soru sayfasinin 112'sinde bant var "
    "ve 14 ad sayfa sirasinda tam 14 kosu olusturuyor "
    "(0022_biyo345tyt_konu_agaci)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; tekrar kosumda ayni id uretilir.

    0013/0015/0017/0021 ile BIREBIR ayni formul.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0022] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0022] mv_safe_for_beta yenilendi")


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0022] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": BIO_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0022] %s kok konusu yok -- atlandi", BIO_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # DIKKAT: LIKE 'BIO-T%' deseni BIO kokunu, BIO-OSYM-GENEL'i ve
    # 0021'in BIO-U* unitelerini KAPSAMAZ; hicbirine dokunulmuyor.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "%"},
        ).fetchall()
    }

    eklenen = 0
    for _sira, kod, ad in KONULAR:
        if kod in mevcut:
            continue
        yeni_id = _dugum_id(kod)
        b.execute(
            _EKLE,
            {
                "id": yeni_id,
                "level": kok_level + 1,
                "parent_id": kok_id,
                "code": kod,
                "name_tr": ad,
                "aciklama": _ACIKLAMA,
            },
        )
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, kod, olusturuldu) "  # noqa: S608  # nosec B608
                "VALUES (:id, :kod, TRUE)"
            ),
            {"id": yeni_id, "kod": kod},
        )
        eklenen += 1

    _log.info(
        "[0022] %s konu tanimi; bu kosumda eklenen dugum: %s",
        len(KONULAR),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0022] %s yok -- downgrade atlandi", GUNLUK)
        return
    idler = [
        r[0]
        for r in b.execute(
            sa.text(f"SELECT id FROM {GUNLUK} WHERE olusturuldu IS TRUE")  # noqa: S608  # nosec B608
        ).fetchall()
    ]
    if idler and sa.inspect(b).has_table("question_bank"):
        kullanilan = {
            r[0]
            for r in b.execute(
                sa.text(
                    "SELECT DISTINCT primary_topic_id FROM question_bank "
                    "WHERE primary_topic_id = ANY(:idler)"
                ),
                {"idler": idler},
            ).fetchall()
        }
        if kullanilan:
            _log.warning(
                "[0022] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        b.execute(
            sa.text(
                "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c "
                "WHERE c.parent_id = topic_hierarchy.id)"
            ),
            {"idler": idler},
        )
        _log.info("[0022] geri alindi: %s dugum silindi", len(idler))
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
