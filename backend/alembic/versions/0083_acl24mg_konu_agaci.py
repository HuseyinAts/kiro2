"""2024 ACIL TYT Matematik Geometri Kitap-1: kitabin kendi bolum / konu agaci (MAT-ACL24MG).

Revision ID: 0083_acl24mg_agac
Revises: 0082_acl23kc_beta_onay
Create Date: 2026-09-28

NEDEN
-----
Bu kitabin ithali her testi (92 test, 505 soru) kitabin bolum / konu
yapisina baglar. MAT kokunun altindaki dugumler baska kitaplarin agaclaridir;
bu migration kitabin agacini MAT-ACL24MG onekiyle ayri bir alt agac olarak kurar
(0071 / 0074 deseni; kitap_hat/migration_uret.py ile uretildi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/acil_2024_tyt_matematik_kitap1_konu_haritasi.json` ile
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

revision: str = "0083_acl24mg_agac"
down_revision: Union[str, None] = "0082_acl23kc_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl24mg_konu_gunlugu_0083"
KOK = "MAT"
KOD_ONEKI = "MAT-ACL24MG"
ALAN = "MATEMATIK"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    ("MAT-ACL24MG-B01", "SAYILAR"),
    ("MAT-ACL24MG-B02", "RASYONEL SAYI"),
    ("MAT-ACL24MG-B03", "B\u0130R\u0130NC\u0130 DERECEDEN DENKLEMLER"),
    ("MAT-ACL24MG-B04", "BAS\u0130T E\u015e\u0130TS\u0130ZL\u0130K"),
    ("MAT-ACL24MG-B05", "MUTLAK DE\u011eER"),
    ("MAT-ACL24MG-B06", "\u00dcSL\u00dc SAYILAR"),
    ("MAT-ACL24MG-B07", "K\u00d6KL\u00dc SAYILAR"),
    ("MAT-ACL24MG-B08", "\u00c7ARPANLARA AYIRMA"),
    ("MAT-ACL24MG-B09", "ORAN-ORANTI"),
)

# (kod, ad, bolum kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("MAT-ACL24MG-B01-K01", "Say\u0131 K\u00fcmeleri", "MAT-ACL24MG-B01"),
    (
        "MAT-ACL24MG-B01-K02",
        "Pozitif-Negatif Say\u0131lar / Tek-\u00c7ift Say\u0131lar / Ard\u0131\u015f\u0131k Say\u0131lar",
        "MAT-ACL24MG-B01",
    ),
    ("MAT-ACL24MG-B01-K03", "Basamak Kavram\u0131", "MAT-ACL24MG-B01"),
    (
        "MAT-ACL24MG-B01-K04",
        "En K\u00fc\u00e7\u00fck ve En B\u00fcy\u00fck De\u011fer Bulma",
        "MAT-ACL24MG-B01",
    ),
    ("MAT-ACL24MG-B01-K05", "B\u00f6lme", "MAT-ACL24MG-B01"),
    (
        "MAT-ACL24MG-B01-K06",
        "B\u00f6lme ve B\u00f6l\u00fcnebilme Kurallar\u0131",
        "MAT-ACL24MG-B01",
    ),
    ("MAT-ACL24MG-B01-K07", "Fakt\u00f6riyel", "MAT-ACL24MG-B01"),
    (
        "MAT-ACL24MG-B01-K08",
        "Asal Say\u0131lar ve Asal \u00c7arpanlara Ay\u0131rma",
        "MAT-ACL24MG-B01",
    ),
    ("MAT-ACL24MG-B01-K09", "EBOB-EKOK", "MAT-ACL24MG-B01"),
    (
        "MAT-ACL24MG-B02-K01",
        "Rasyonel ve Ondal\u0131kl\u0131 Say\u0131lar",
        "MAT-ACL24MG-B02",
    ),
    (
        "MAT-ACL24MG-B03-K01",
        "Birinci Dereceden Bir ve \u0130ki Bilinmeyenli Denklemler",
        "MAT-ACL24MG-B03",
    ),
    ("MAT-ACL24MG-B04-K01", "Birinci Dereceden E\u015fitsizlikler", "MAT-ACL24MG-B04"),
    ("MAT-ACL24MG-B05-K01", "Mutlak De\u011fer", "MAT-ACL24MG-B05"),
    ("MAT-ACL24MG-B06-K01", "\u00dcsl\u00fc Say\u0131lar", "MAT-ACL24MG-B06"),
    ("MAT-ACL24MG-B07-K01", "K\u00f6kl\u00fc Say\u0131lar", "MAT-ACL24MG-B07"),
    ("MAT-ACL24MG-B08-K01", "\u00c7arpanlara Ay\u0131rma", "MAT-ACL24MG-B08"),
    ("MAT-ACL24MG-B09-K01", "Oran-Orant\u0131", "MAT-ACL24MG-B09"),
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
    "2024 ACIL TYT Matematik Geometri Kitap-1 icindekiler ve test ust bantlarindan (iki bagimsiz okuma) "
    "uretildi (0083)."
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
        _log.info("[0083] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0083] mv_safe_for_beta yenilendi")


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
        _log.info("[0083] topic_hierarchy yok (taze DB?) -- atlandi")
        return
    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0083] %s kok konusu yok -- atlandi", KOK)
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
        "[0083] %s bolum + %s konu tanimi; eklenen dugum: %s",
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
        _log.info("[0083] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0083] %s dugum hala soru tasiyor -- SILINMEDI", len(kullanilan)
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
    _log.info("[0083] downgrade tamam; silinmeye aday dugum: %s", len(idler))
