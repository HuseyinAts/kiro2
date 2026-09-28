"""2023-2024 Aktif Ogrenme Biyoloji: kitabin kendi bolum / konu agaci (BIO-AKT24BY).

Revision ID: 0107_akt24by_agac
Revises: 0106_acl25s2_ortak_oncul
Create Date: 2026-09-28

NEDEN
-----
Bu kitabin ithali her testi (42 test, 528 soru) kitabin bolum / konu
yapisina baglar. BIO kokunun altindaki dugumler baska kitaplarin agaclaridir;
bu migration kitabin agacini BIO-AKT24BY onekiyle ayri bir alt agac olarak kurar
(0071 / 0074 deseni; kitap_hat/migration_uret.py ile uretildi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/aktif_2024_biyoloji_konu_haritasi.json` ile
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

revision: str = "0107_akt24by_agac"
down_revision: Union[str, None] = "0106_acl25s2_ortak_oncul"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "akt24by_konu_gunlugu_0107"
KOK = "BIO"
KOD_ONEKI = "BIO-AKT24BY"
ALAN = "BIYOLOJI"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    ("BIO-AKT24BY-B01", "YA\u015eAM B\u0130L\u0130M\u0130 B\u0130YOLOJ\u0130"),
    ("BIO-AKT24BY-B02", "H\u00dcCRE"),
    ("BIO-AKT24BY-B03", "CANLILAR D\u00dcNYASI"),
    ("BIO-AKT24BY-B04", "H\u00dcCRE B\u00d6L\u00dcNMELER\u0130"),
    ("BIO-AKT24BY-B05", "KALITIMIN GENEL \u0130LKELER\u0130"),
)

# (kod, ad, bolum kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("BIO-AKT24BY-B01-K01", "Ya\u015fam Bilimi Biyoloji", "BIO-AKT24BY-B01"),
    ("BIO-AKT24BY-B02-K01", "H\u00fccre", "BIO-AKT24BY-B02"),
    ("BIO-AKT24BY-B03-K01", "Canl\u0131lar D\u00fcnyas\u0131", "BIO-AKT24BY-B03"),
    ("BIO-AKT24BY-B04-K01", "H\u00fccre B\u00f6l\u00fcnmeleri", "BIO-AKT24BY-B04"),
    (
        "BIO-AKT24BY-B05-K01",
        "Kal\u0131t\u0131m\u0131n Genel \u0130lkeleri",
        "BIO-AKT24BY-B05",
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
    "2023-2024 Aktif Ogrenme Biyoloji icindekiler ve test ust bantlarindan (iki bagimsiz okuma) "
    "uretildi (0107)."
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
        _log.info("[0107] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0107] mv_safe_for_beta yenilendi")


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
        _log.info("[0107] topic_hierarchy yok (taze DB?) -- atlandi")
        return
    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0107] %s kok konusu yok -- atlandi", KOK)
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
        "[0107] %s bolum + %s konu tanimi; eklenen dugum: %s",
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
        _log.info("[0107] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0107] %s dugum hala soru tasiyor -- SILINMEDI", len(kullanilan)
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
    _log.info("[0107] downgrade tamam; silinmeye aday dugum: %s", len(idler))
