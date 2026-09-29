"""2019-2020 Apotemi TYT-AYT Fizik Soru Bankasi: kitabin kendi bolum / konu agaci (FIZ-APO19FZ).

Revision ID: 0119_apo19fz_agac
Revises: 0118_apo19mt_beta_onay
Create Date: 2026-09-28

NEDEN
-----
Bu kitabin ithali her testi (216 test, 2180 soru) kitabin bolum / konu
yapisina baglar. FIZ kokunun altindaki dugumler baska kitaplarin agaclaridir;
bu migration kitabin agacini FIZ-APO19FZ onekiyle ayri bir alt agac olarak kurar
(0071 / 0074 deseni; kitap_hat/migration_uret.py ile uretildi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/apotemi_2019_tyt_ayt_fizik_konu_haritasi.json` ile
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

revision: str = "0119_apo19fz_agac"
down_revision: Union[str, None] = "0118_apo19mt_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "apo19fz_konu_gunlugu_0119"
KOK = "FIZ"
KOD_ONEKI = "FIZ-APO19FZ"
ALAN = "FIZIK"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    ("FIZ-APO19FZ-B01", "1. B\u00d6L\u00dcM"),
    ("FIZ-APO19FZ-B02", "2. B\u00d6L\u00dcM"),
    ("FIZ-APO19FZ-B03", "3. B\u00d6L\u00dcM"),
    ("FIZ-APO19FZ-B04", "4. B\u00d6L\u00dcM"),
)

# (kod, ad, bolum kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("FIZ-APO19FZ-B01-K01", "Fizik Bilimine Giri\u015f", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B01-K02", "Madde ve \u00d6zellikleri", "FIZ-APO19FZ-B01"),
    (
        "FIZ-APO19FZ-B01-K03",
        "S\u0131v\u0131lar\u0131n Kald\u0131rma Kuvveti",
        "FIZ-APO19FZ-B01",
    ),
    ("FIZ-APO19FZ-B01-K04", "Bas\u0131n\u00e7", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B01-K05", "Is\u0131 ve S\u0131cakl\u0131k", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B01-K06", "Genle\u015fme", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B01-K07", "Tekrar Testi", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B01-K08", "Vekt\u00f6rler", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B01-K09", "Kuvvet ve Denge", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B01-K10", "Tork", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B01-K11", "Basit Makineler", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B01-K12", "A\u011f\u0131rl\u0131k Merkezi", "FIZ-APO19FZ-B01"),
    ("FIZ-APO19FZ-B02-K01", "Hareket", "FIZ-APO19FZ-B02"),
    ("FIZ-APO19FZ-B02-K02", "Ba\u011f\u0131l Hareket", "FIZ-APO19FZ-B02"),
    ("FIZ-APO19FZ-B02-K03", "Newton'un Hareket Yasalar\u0131", "FIZ-APO19FZ-B02"),
    (
        "FIZ-APO19FZ-B02-K04",
        "Yery\u00fcz\u00fcnde At\u0131\u015f Hareketleri",
        "FIZ-APO19FZ-B02",
    ),
    ("FIZ-APO19FZ-B02-K05", "\u0130\u015f - G\u00fc\u00e7 - Enerji", "FIZ-APO19FZ-B02"),
    ("FIZ-APO19FZ-B02-K06", "Tekrar Testi", "FIZ-APO19FZ-B02"),
    ("FIZ-APO19FZ-B02-K07", "\u0130tme ve \u00c7izgisel Momentum", "FIZ-APO19FZ-B02"),
    (
        "FIZ-APO19FZ-B02-K08",
        "D\u00fczg\u00fcn \u00c7embersel Hareket",
        "FIZ-APO19FZ-B02",
    ),
    ("FIZ-APO19FZ-B02-K09", "A\u00e7\u0131sal Momentum", "FIZ-APO19FZ-B02"),
    (
        "FIZ-APO19FZ-B02-K10",
        "Genel \u00c7ekim ve Kepler Kanunlar\u0131",
        "FIZ-APO19FZ-B02",
    ),
    ("FIZ-APO19FZ-B02-K11", "Basit Harmonik Hareket", "FIZ-APO19FZ-B02"),
    ("FIZ-APO19FZ-B03-K01", "Elektrostatik", "FIZ-APO19FZ-B03"),
    ("FIZ-APO19FZ-B03-K02", "Elektriksel Potansiyel", "FIZ-APO19FZ-B03"),
    (
        "FIZ-APO19FZ-B03-K03",
        "D\u00fczg\u00fcn Elektrik Alan ve S\u0131\u011fa",
        "FIZ-APO19FZ-B03",
    ),
    ("FIZ-APO19FZ-B03-K04", "Elektrik Ak\u0131m\u0131", "FIZ-APO19FZ-B03"),
    ("FIZ-APO19FZ-B03-K05", "Tekrar Testi", "FIZ-APO19FZ-B03"),
    ("FIZ-APO19FZ-B03-K06", "Manyetizma", "FIZ-APO19FZ-B03"),
    ("FIZ-APO19FZ-B04-K01", "Optik", "FIZ-APO19FZ-B04"),
    ("FIZ-APO19FZ-B04-K02", "Dalgalar", "FIZ-APO19FZ-B04"),
    ("FIZ-APO19FZ-B04-K03", "Tekrar Testi", "FIZ-APO19FZ-B04"),
    ("FIZ-APO19FZ-B04-K04", "Dalga Mekani\u011fi", "FIZ-APO19FZ-B04"),
    (
        "FIZ-APO19FZ-B04-K05",
        "Atom Fizi\u011fine Giri\u015f ve Radyoaktivite",
        "FIZ-APO19FZ-B04",
    ),
    ("FIZ-APO19FZ-B04-K06", "Modern Fizik", "FIZ-APO19FZ-B04"),
    (
        "FIZ-APO19FZ-B04-K07",
        "Modern Fizi\u011fin Teknolojideki Uygulamalar\u0131",
        "FIZ-APO19FZ-B04",
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
    "2019-2020 Apotemi TYT-AYT Fizik Soru Bankasi icindekiler ve test ust bantlarindan (iki bagimsiz okuma) "
    "uretildi (0119)."
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
        _log.info("[0119] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0119] mv_safe_for_beta yenilendi")


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
        _log.info("[0119] topic_hierarchy yok (taze DB?) -- atlandi")
        return
    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0119] %s kok konusu yok -- atlandi", KOK)
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
        "[0119] %s bolum + %s konu tanimi; eklenen dugum: %s",
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
        _log.info("[0119] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0119] %s dugum hala soru tasiyor -- SILINMEDI", len(kullanilan)
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
    _log.info("[0119] downgrade tamam; silinmeye aday dugum: %s", len(idler))
