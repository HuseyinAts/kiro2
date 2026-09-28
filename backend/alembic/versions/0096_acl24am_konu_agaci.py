"""Acil 2024 AYT Matematik Kitap-1: kitabin kendi bolum / konu agaci (MAT-ACL24AM).

Revision ID: 0096_acl24am_agac
Revises: 0095_acl25s2_beta_onay
Create Date: 2026-09-28

NEDEN
-----
Bu kitabin ithali her testi (67 test, 340 soru) kitabin bolum / konu
yapisina baglar. MAT kokunun altindaki dugumler baska kitaplarin agaclaridir;
bu migration kitabin agacini MAT-ACL24AM onekiyle ayri bir alt agac olarak kurar
(0071 / 0074 deseni; kitap_hat/migration_uret.py ile uretildi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/acil_2024_ayt_matematik_kitap1_konu_haritasi.json` ile
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

revision: str = "0096_acl24am_agac"
down_revision: Union[str, None] = "0095_acl25s2_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl24am_konu_gunlugu_0096"
KOK = "MAT"
KOD_ONEKI = "MAT-ACL24AM"
ALAN = "MATEMATIK"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    ("MAT-ACL24AM-B01", "POL\u0130NOM"),
    ("MAT-ACL24AM-B02", "\u0130K\u0130NC\u0130 DERECEDEN DENKLEM"),
    ("MAT-ACL24AM-B03", "KARMA\u015eIK SAYILAR"),
    ("MAT-ACL24AM-B04", "PARABOL"),
    ("MAT-ACL24AM-B05", "FONKS\u0130YON UYGULAMALARI"),
    ("MAT-ACL24AM-B06", "E\u015e\u0130TS\u0130ZL\u0130KLER"),
    ("MAT-ACL24AM-B07", "TR\u0130GONOMETR\u0130"),
)

# (kod, ad, bolum kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("MAT-ACL24AM-B01-K01", "Polinomlar", "MAT-ACL24AM-B01"),
    ("MAT-ACL24AM-B02-K01", "\u0130kinci Dereceden Denklemler", "MAT-ACL24AM-B02"),
    ("MAT-ACL24AM-B03-K01", "Karma\u015f\u0131k Say\u0131lar", "MAT-ACL24AM-B03"),
    ("MAT-ACL24AM-B04-K01", "Parabol", "MAT-ACL24AM-B04"),
    ("MAT-ACL24AM-B05-K01", "Fonksiyonlar\u0131n Uygulamalar\u0131", "MAT-ACL24AM-B05"),
    ("MAT-ACL24AM-B06-K01", "E\u015fitsizlikler", "MAT-ACL24AM-B06"),
    ("MAT-ACL24AM-B07-K01", "Trigonometri I. B\u00f6l\u00fcm", "MAT-ACL24AM-B07"),
    ("MAT-ACL24AM-B07-K02", "Trigonometri II. B\u00f6l\u00fcm", "MAT-ACL24AM-B07"),
    ("MAT-ACL24AM-B07-K03", "Trigonometri III. B\u00f6l\u00fcm", "MAT-ACL24AM-B07"),
    ("MAT-ACL24AM-B07-K04", "Trigonometri IV. B\u00f6l\u00fcm", "MAT-ACL24AM-B07"),
    ("MAT-ACL24AM-B07-K05", "Trigonometri V. B\u00f6l\u00fcm", "MAT-ACL24AM-B07"),
    ("MAT-ACL24AM-B07-K06", "Trigonometri VI. B\u00f6l\u00fcm", "MAT-ACL24AM-B07"),
    ("MAT-ACL24AM-B07-K07", "Trigonometri VII. B\u00f6l\u00fcm", "MAT-ACL24AM-B07"),
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
    "Acil 2024 AYT Matematik Kitap-1 icindekiler ve test ust bantlarindan (iki bagimsiz okuma) "
    "uretildi (0096)."
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
        _log.info("[0096] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0096] mv_safe_for_beta yenilendi")


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
        _log.info("[0096] topic_hierarchy yok (taze DB?) -- atlandi")
        return
    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0096] %s kok konusu yok -- atlandi", KOK)
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
        "[0096] %s bolum + %s konu tanimi; eklenen dugum: %s",
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
        _log.info("[0096] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0096] %s dugum hala soru tasiyor -- SILINMEDI", len(kullanilan)
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
    _log.info("[0096] downgrade tamam; silinmeye aday dugum: %s", len(idler))
