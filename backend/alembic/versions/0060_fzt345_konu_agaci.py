"""345 2025 TYT Fizik: kitabin kendi unite agaci (FIZ-345T25).

Revision ID: 0060_fzt345_agac
Revises: 0059_stm345_beta_onay
Create Date: 2026-09-26

NEDEN
-----
Bu kitabin ithali her testi kitabin 19 unitesinden birine baglar. FIZ
kokunun altindaki dugumler (FIZ-345-*, FIZ-MO*, FIZ-NEO*, ...) baska
kitaplarin agaclaridir; bu kitabin uniteleri ('Fizik Bilimine Giris' ...
'Mercekler') onlarla birebir ortusmez. Sessizce "en yakin" dugume baglamak
yanlis veridir; bu migration kitabin agacini FIZ-345T25 onekiyle ayri bir
alt agac olarak kurar (0042 / 0055 / 0057 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/345_2025_tyt_fizik_konu_haritasi.json`
ile BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya:
  * 19 unite: icindekiler (dosya 3-4, gozle), basili baslangic sayfalari.
  * Bagimsiz dogrulama: 19/19 baslangic sayfasinin ust bandinda '1. bolum'
    rozeti + unite adi; 176 testin her biri tek unitenin sayfa araliginda.
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Unite kok+1 (FIZ kokunun altinda); 176 testin 1397 sorusu unite dugumune
baglanir. Kitap uniteyi 'N. bolum' parcalarina boler ama parca adi basmaz.
19 dugum.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca
onlari siler ve SORU TASIYAN ya da COCUGU OLAN dugume DOKUNMAZ.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0060_fzt345_agac"
down_revision: Union[str, None] = "0059_stm345_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "fzt345_konu_gunlugu_0060"
FIZ_KOK_KODU = "FIZ"
KOD_ONEKI = "FIZ-345T25"

# (kod, ad)
UNITELER: tuple[tuple[str, str], ...] = (
    ("FIZ-345T25-U01", "Fizik Bilimine Giri\u015f"),
    ("FIZ-345T25-U02", "Madde ve \xd6zellikleri"),
    ("FIZ-345T25-U03", "Hareket"),
    ("FIZ-345T25-U04", "Kuvvet"),
    ("FIZ-345T25-U05", "Enerji"),
    ("FIZ-345T25-U06", "Is\u0131 ve S\u0131cakl\u0131k"),
    ("FIZ-345T25-U07", "Elektrostatik"),
    ("FIZ-345T25-U08", "Elektrik Ak\u0131m\u0131"),
    ("FIZ-345T25-U09", "Manyetizma"),
    ("FIZ-345T25-U10", "Bas\u0131n\xe7"),
    ("FIZ-345T25-U11", "Kald\u0131rma Kuvveti"),
    ("FIZ-345T25-U12", "Yay Dalgalar\u0131"),
    ("FIZ-345T25-U13", "Su Dalgalar\u0131"),
    ("FIZ-345T25-U14", "Ses ve Deprem Dalgas\u0131"),
    (
        "FIZ-345T25-U15",
        "I\u015f\u0131k Ak\u0131s\u0131 - Ayd\u0131nlanma - G\xf6lge Olaylar\u0131",
    ),
    ("FIZ-345T25-U16", "Yans\u0131ma ve D\xfczlem Aynalar"),
    ("FIZ-345T25-U17", "Yans\u0131ma ve K\xfcresel Aynalar"),
    ("FIZ-345T25-U18", "I\u015f\u0131\u011f\u0131n K\u0131r\u0131lmas\u0131"),
    ("FIZ-345T25-U19", "Mercekler"),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'FIZIK', TRUE, now(), now())
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
    "345 2025 TYT Fizik Soru Bankasi'nin icindekiler sayfalarindan (dosya 3-4) "
    "uretildi; baslangic sayfasi bantlariyla dogrulandi (0060)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0060] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0060] mv_safe_for_beta yenilendi")


def _yaz(b, kod, ad, level, parent_id) -> str:
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
        },
    )
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, kod, olusturuldu) "  # noqa: S608  # nosec B608
            "VALUES (:id, :kod, TRUE)"
        ),
        {"id": yeni_id, "kod": kod},
    )
    return yeni_id


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0060] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": FIZ_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0060] %s kok konusu yok -- atlandi", FIZ_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz FIZ-345T25 deseni; diger FIZ dugumlerine DOKUNULMAZ. LIKE deseni
    # '-' ile biter ki FIZ-345T250 gibi bir onek yanlislikla eslesmesin.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "-%"},
        ).fetchall()
    }

    eklenen = 0
    for kod, ad in UNITELER:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 1, kok_id)
        eklenen += 1

    _log.info(
        "[0060] %s unite tanimi; bu kosumda eklenen dugum: %s",
        len(UNITELER),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0060] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0060] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Tek duzey; cocugu olan silinmez.
        b.execute(
            sa.text(
                "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c "
                "WHERE c.parent_id = topic_hierarchy.id)"
            ),
            {"idler": idler},
        )
    op.drop_table(GUNLUK)
    _log.info("[0060] downgrade tamam; silinmeye aday dugum: %s", len(idler))
