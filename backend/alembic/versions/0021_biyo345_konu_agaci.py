"""345 2025 AYT Biyoloji Soru Bankasi konu agaci (16 bolum).

Revision ID: 0021_biyo345_konu_agaci
Revises: 0020_geo_kod_notrlestir
Create Date: 2026-09-14

BAGLAM
------
Canli DB olcumu (14 Eyl 2026): BIYOLOJI dersinin konu agaci PRATIKTE YOK.
topic_hierarchy'de yalnizca iki BIO satiri var:

    BIO             level 1  "Biyoloji"                       (kok)
    BIO-OSYM-GENEL  level 2  "OSYM Kitapcik (siniflandirilmamis)"

Yani bugune kadar biyoloji sorulari ya koke ya da "siniflandirilmamis"
dugumune baglanabiliyordu. Bu migration kitabin KENDI bolum yapisindan
16 unite dugumu kurar (BIO-U1 ... BIO-U16) -- 0013/0015/0017'nin fizik ve
geometri icin yaptiginin aynisi.

AGACIN KAYNAGI VE NASIL DOGRULANDI
----------------------------------
Bolum adlari ICINDEKILER sayfasindan DEGIL, kitabin 16 BOLUM AYRAC
SAYFASINDAN okundu (sayfa goruntusu: backend/_geo_gecici/biyo_bolum.png).
Ayrac sayfalari bagimsiz olarak bulundu: anahtar seridi tespit edicisi
374 sayfanin 57'sinde anahtar bulamadi; bunlarin 16'si duzenli araliklarla
gelen bolum ayraclari (kalani icindekiler ve konu anlatimi sayfalari, hepsi
kucuk resim izgarasiyla tek tek dogrulandi).

Ayrac sayfalari (dosya no):
    0006 0028 0050 0072 0098 0122 0148 0166
    0184 0204 0228 0256 0282 0306 0334 0364

SOZU EDILMESI GEREKEN TEK SAPMA: 11. ayrac sayfasinda IKI baslik basili --
"GENDEN PROTEINE ve BIYOTEKNOLOJI" ve "CANLILAR ve CEVRE". Mufredatta bunlar
ayri unitedir ama KITAP ikisini tek bolum olarak basmis; sayfa ust bilgisi de
bolum boyunca (s0229-s0255) neredeyse hep "GENDEN PROTEINE ve BIYOTEKNOLOJI"
diyor, yalnizca s0249'da "CANLILAR ve CEVRE" goruldu -- ikiye bolmek icin
yeterli sinyal yok. Bu yuzden dugum, kitabin bastigi gibi tek ve iki basligi
birden tasiyor. Uydurulmus bir ayrim yapilmadi.

SEVIYE: yalnizca UNITE (level 2). Kitapta unite alti konu etiketi YOK; test
basliklari ("3. TEST - KAZANIM ODAKLI SORULAR", "KARMA SORULAR 2",
"OSYM TADINDA SORULAR 1", "ORIJINAL SORULAR") konu degil TEST TURUDUR ve
soru duzeyinde pipeline_metadata.test_basligi olarak tasinir. Var olmayan bir
L3 katmani uydurmak yerine granulerlik oldugu gibi birakildi.

NEDEN MIGRATION, NEDEN SCRIPT DEGIL
-----------------------------------
Konu agaci referans veridir: her ortamda ayni olmali, surumlenmeli, geri
alinabilmeli. Sorular ithal script'iyle gelir
(scripts/kitap/biyo345_ithal.py). 0013/0015/0017 ile ayni ayrim.

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

revision: str = "0021_biyo345_konu_agaci"
down_revision: Union[str, None] = "0020_geo_kod_notrlestir"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "biyo345_konu_gunlugu_0021"
BIO_KOK_KODU = "BIO"
KOD_ONEKI = "BIO-U"

# (unite_no, kod, ad)  -- yorumdaki sayi veri setinden OLCULEN soru sayisidir
UNITELER: tuple[tuple[int, str, str], ...] = (
    (1, "BIO-U1", "Sinir Sistemi"),  # 78
    (2, "BIO-U2", "Hormonlar"),  # 82
    (3, "BIO-U3", "Duyu Organlari"),  # 78
    (4, "BIO-U4", "Destek ve Hareket Sistemleri"),  # 95
    (5, "BIO-U5", "Sindirim Sistemi"),  # 89
    (6, "BIO-U6", "Dolasim Sistemleri ve Bagisiklik"),  # 93
    (7, "BIO-U7", "Solunum Sistemi"),  # 66
    (8, "BIO-U8", "Uriner Sistem"),  # 68
    (9, "BIO-U9", "Insanda Ureme ve Gelisme"),  # 72
    (10, "BIO-U10", "Komunite ve Populasyon Ekolojisi"),  # 71
    (11, "BIO-U11", "Genden Proteine ve Biyoteknoloji; Canlilar ve Cevre"),  # 100
    (12, "BIO-U12", "Fotosentez - Kemosentez"),  # 96
    (13, "BIO-U13", "Hucresel Solunum"),  # 85
    (14, "BIO-U14", "Bitkilerin Yapisi"),  # 99
    (15, "BIO-U15", "Bitki Fizyolojisi"),  # 98
    (16, "BIO-U16", "Bitkilerde Ureme ve Gelisme"),  # 47
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
    "345 2025 AYT Biyoloji Soru Bankasi bolum ayrac sayfalarindan okundu "
    "(16/16 baslik); ayrac sayfalari anahtar seridi tespit edicisinin "
    "anahtarsiz buldugu 57 sayfa icinden gorsel olarak dogrulandi "
    "(0021_biyo345_konu_agaci)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; tekrar kosumda ayni id uretilir.

    0013/0015/0017 ile BIREBIR ayni formul.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0021] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0021] mv_safe_for_beta yenilendi")


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0021] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": BIO_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0021] %s kok konusu yok -- atlandi", BIO_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # DIKKAT: LIKE 'BIO-U%' deseni BIO kokunu ve BIO-OSYM-GENEL'i KAPSAMAZ;
    # ikisine de dokunulmuyor.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "%"},
        ).fetchall()
    }

    eklenen = 0
    for _unite_no, kod, ad in UNITELER:
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
        "[0021] %s unite tanimi; bu kosumda eklenen dugum: %s",
        len(UNITELER),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0021] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0021] %s dugum hala soru tasiyor -- SILINMEDI "
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
        _log.info("[0021] geri alindi: %s dugum silindi", len(idler))
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
