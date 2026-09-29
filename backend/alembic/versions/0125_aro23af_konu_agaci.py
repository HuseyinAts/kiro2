"""2023-2024 AROMAT AYT Fizik Soru Bankasi: kitabin kendi bolum / konu agaci (FIZ-ARO23AF).

Revision ID: 0125_aro23af_agac
Revises: 0124_apo19km_beta_onay
Create Date: 2026-09-28

NEDEN
-----
Bu kitabin ithali her testi (145 test, 1167 soru) kitabin bolum / konu
yapisina baglar. FIZ kokunun altindaki dugumler baska kitaplarin agaclaridir;
bu migration kitabin agacini FIZ-ARO23AF onekiyle ayri bir alt agac olarak kurar
(0071 / 0074 deseni; kitap_hat/migration_uret.py ile uretildi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/aromat_2024_ayt_fizik_konu_haritasi.json` ile
BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya icindekiler ve
test ust bandindan (iki bagimsiz okuma) uretildi.

DUZEY
-----
Bolum kok+1, konu kok+2; sorular konu dugumune baglanir.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca onlari
siler ve SORU TASIYAN ya da COCUGU OLAN dugume DOKUNMAZ.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0125_aro23af_agac"
down_revision: Union[str, None] = "0124_apo19km_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "aro23af_konu_gunlugu_0125"
KOK = "FIZ"
KOD_ONEKI = "FIZ-ARO23AF"
ALAN = "FIZIK"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    ("FIZ-ARO23AF-B01", "B\u00d6L\u00dcM - 1"),
    ("FIZ-ARO23AF-B02", "B\u00d6L\u00dcM - 2"),
    ("FIZ-ARO23AF-B03", "B\u00d6L\u00dcM - 3"),
    ("FIZ-ARO23AF-B04", "B\u00d6L\u00dcM - 4"),
    ("FIZ-ARO23AF-B05", "B\u00d6L\u00dcM - 5"),
    ("FIZ-ARO23AF-B06", "B\u00d6L\u00dcM - 6"),
    ("FIZ-ARO23AF-B07", "B\u00d6L\u00dcM - 7"),
    ("FIZ-ARO23AF-B08", "B\u00d6L\u00dcM - 8"),
    ("FIZ-ARO23AF-B09", "B\u00d6L\u00dcM - 9"),
    ("FIZ-ARO23AF-B10", "B\u00d6L\u00dcM - 10"),
    ("FIZ-ARO23AF-B11", "B\u00d6L\u00dcM - 11"),
    ("FIZ-ARO23AF-B12", "B\u00d6L\u00dcM - 12"),
)

# (kod, ad, bolum kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("FIZ-ARO23AF-B01-K01", "Vekt\u00f6rler", "FIZ-ARO23AF-B01"),
    ("FIZ-ARO23AF-B01-K02", "Ba\u011f\u0131l Hareket", "FIZ-ARO23AF-B01"),
    ("FIZ-ARO23AF-B01-K03", "Newton'\u0131n Hareket Yasalar\u0131", "FIZ-ARO23AF-B01"),
    ("FIZ-ARO23AF-B02-K01", "Bir Boyutta Sabit \u0130vmeli Hareket", "FIZ-ARO23AF-B02"),
    ("FIZ-ARO23AF-B02-K02", "Yery\u00fcz\u00fcnde Hareket", "FIZ-ARO23AF-B02"),
    ("FIZ-ARO23AF-B03-K01", "Enerji", "FIZ-ARO23AF-B03"),
    ("FIZ-ARO23AF-B03-K02", "\u0130tme ve \u00c7izgisel Momentum", "FIZ-ARO23AF-B03"),
    ("FIZ-ARO23AF-B04-K01", "Tork, Denge ve K\u00fctle Merkezi", "FIZ-ARO23AF-B04"),
    ("FIZ-ARO23AF-B04-K02", "Basit Makineler", "FIZ-ARO23AF-B04"),
    (
        "FIZ-ARO23AF-B05-K01",
        "Elektriksel Kuvvet, Alan, Potansiyel ve Enerji",
        "FIZ-ARO23AF-B05",
    ),
    (
        "FIZ-ARO23AF-B05-K02",
        "D\u00fczg\u00fcn Elektrik Alan ve S\u0131\u011fa",
        "FIZ-ARO23AF-B05",
    ),
    ("FIZ-ARO23AF-B06-K01", "Manyetizma", "FIZ-ARO23AF-B06"),
    ("FIZ-ARO23AF-B06-K02", "Elektromanyetik \u0130nd\u00fcklenme", "FIZ-ARO23AF-B06"),
    (
        "FIZ-ARO23AF-B06-K03",
        "Alternatif Ak\u0131m ve Transformat\u00f6rler",
        "FIZ-ARO23AF-B06",
    ),
    ("FIZ-ARO23AF-B07-K01", "\u00c7embersel Hareket", "FIZ-ARO23AF-B07"),
    (
        "FIZ-ARO23AF-B07-K02",
        "D\u00f6nerek \u00d6teleme Hareketi, A\u00e7\u0131sal Momentum ve K\u00fctle \u00c7ekim Kuvveti",
        "FIZ-ARO23AF-B07",
    ),
    ("FIZ-ARO23AF-B08-K01", "Basit Harmonik Hareket", "FIZ-ARO23AF-B08"),
    ("FIZ-ARO23AF-B09-K01", "Dalga Mekani\u011fi", "FIZ-ARO23AF-B09"),
    (
        "FIZ-ARO23AF-B10-K01",
        "Atom Kavram\u0131n\u0131n Tarihsel Geli\u015fimi",
        "FIZ-ARO23AF-B10",
    ),
    (
        "FIZ-ARO23AF-B10-K02",
        "Atom Alt\u0131 Par\u00e7ac\u0131klar ve Radyoaktivite",
        "FIZ-ARO23AF-B10",
    ),
    ("FIZ-ARO23AF-B11-K01", "Modern Fizik", "FIZ-ARO23AF-B11"),
    (
        "FIZ-ARO23AF-B12-K01",
        "Modern Fizi\u011fin Teknolojideki Uygulamalar\u0131",
        "FIZ-ARO23AF-B12",
    ),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, :alan, TRUE, now(), now())
    """
)

_ACIKLAMA = (
    "2023-2024 AROMAT AYT Fizik Soru Bankasi icindekiler ve test ust bantlarindan (iki bagimsiz okuma) "
    "uretildi (0125)."
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


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0125] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0125] mv_safe_for_beta yenilendi")


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _yaz(b, kod, ad, level, parent_id, *, alan) -> str:
    yeni_id = _dugum_id(kod)
    b.execute(
        _EKLE,
        {
            "id": yeni_id,
            "level": level,
            "parent_id": parent_id,
            "code": kod,
            "name_tr": ad,
            "aciklama": _ACIKLAMA,
            "alan": alan,
        },
    )
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, kod, olusturuldu) "  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
            "VALUES (:id, :kod, TRUE)"
        ),
        {"id": yeni_id, "kod": kod},
    )
    return yeni_id


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0125] topic_hierarchy yok (taze DB?) -- atlandi")
        return
    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0125] %s kok konusu yok -- atlandi", KOK)
        return
    kok_id, kok_level = r[0], int(r[1])
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Yalniz KOD_ONEKI deseni; kokun diger dugumlerine DOKUNULMAZ ('-' ile biten desen).
    mevcut = {
        r[0]: r[1]
        for r in b.execute(
            sa.text("SELECT code, id FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "-%"},
        ).fetchall()
    }
    eklenen = 0
    bolum_id = {}
    for kod, ad in BOLUMLER:
        if kod in mevcut:
            bolum_id[kod] = mevcut[kod]
            continue
        bolum_id[kod] = _yaz(b, kod, ad, kok_level + 1, kok_id, alan=ALAN)
        eklenen += 1
    for kod, ad, bolum in KONULAR:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 2, bolum_id[bolum], alan=ALAN)
        eklenen += 1
    _log.info(
        "[0125] %s bolum + %s konu tanimi; eklenen dugum: %s",
        len(BOLUMLER),
        len(KONULAR),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0125] %s yok -- downgrade atlandi", GUNLUK)
        return
    idler = [
        r[0]
        for r in b.execute(
            sa.text(f"SELECT id FROM {GUNLUK} WHERE olusturuldu IS TRUE")  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad
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
                "[0125] %s dugum hala soru tasiyor -- SILINMEDI", len(kullanilan)
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        for _ in range(2):
            b.execute(
                sa.text(
                    "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                    "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c "
                    "WHERE c.parent_id = topic_hierarchy.id)"
                ),
                {"idler": idler},
            )
    op.drop_table(GUNLUK)
    _log.info("[0125] downgrade tamam; silinmeye aday dugum: %s", len(idler))
