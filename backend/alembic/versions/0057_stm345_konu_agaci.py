"""345 2025 Start Matematik: kitabin kendi unite agaci (MAT-345S25).

Revision ID: 0057_stm345_agac
Revises: 0056_prg345_beta_onay
Create Date: 2026-09-25

NEDEN
-----
Bu kitabin ithali her testi kitabin 16 unitesinden birine baglar. MAT
kokunun altindaki dugumler (MAT.*, MAT-345T25-*, ...) baska kitaplarin ya da
genel siniflandirmanin agaclaridir; bu kitabin uniteleri ('Toplama ve
Cikarma Islemi' ... 'Carpanlara Ayirma') onlarla birebir ortusmez. Sessizce
"en yakin" dugume baglamak yanlis veridir; bu migration kitabin agacini
MAT-345S25 onekiyle ayri bir alt agac olarak kurar (0042 / 0055 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/345_2025_start_matematik_konu_haritasi.json`
ile BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya:
  * 16 unite: kitabin unite ayraci sayfalari (dosya 4, 18, 38, 52, 70,
    90, 122, 144, 162, 176, 190, 202, 220, 240, 270, 300; '<no>. <ad>',
    gozle).
  * Bagimsiz dogrulama: ayrac adlari icindekiler sayfasiyla (dosya 3) 16/16,
    ayrac dosyasi == icindekiler basili sayfasi + 1 16/16; 45 testin 90
    sayfasinin bandindaki unite adi 90/90 ayni.
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Unite kok+1 (MAT kokunun altinda); 45 testin 371 sorusu unite dugumune
baglanir. Kitap uniteyi alt konuya bolmuyor (test bandi yalniz unite adini
basar). 16 dugum.

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

revision: str = "0057_stm345_agac"
down_revision: Union[str, None] = "0056_prg345_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "stm345_konu_gunlugu_0057"
MAT_KOK_KODU = "MAT"
KOD_ONEKI = "MAT-345S25"

# (kod, ad)
UNITELER: tuple[tuple[str, str], ...] = (
    ("MAT-345S25-U01", "Toplama ve \u00c7\u0131karma \u0130\u015flemi"),
    ("MAT-345S25-U02", "\u00c7arpma ve B\u00f6lme \u0130\u015flemi"),
    ("MAT-345S25-U03", "\u0130\u015flem \u00d6nceli\u011fi"),
    ("MAT-345S25-U04", "Harfli \u0130fadeler"),
    ("MAT-345S25-U05", "Basit Denklem \u00c7\u00f6z\u00fcm\u00fc"),
    ("MAT-345S25-U06", "Rasyonel Say\u0131lar"),
    ("MAT-345S25-U07", "Ondal\u0131k G\u00f6sterim"),
    ("MAT-345S25-U08", "Say\u0131 K\u00fcmeleri"),
    ("MAT-345S25-U09", "Oran ve Orant\u0131"),
    ("MAT-345S25-U10", "Rasyonel Denklemlerin \u00c7\u00f6z\u00fcm\u00fc"),
    ("MAT-345S25-U11", "\u0130ki Bilinmeyenli Denklemler"),
    ("MAT-345S25-U12", "Basit E\u015fitsizlikler"),
    ("MAT-345S25-U13", "Mutlak De\u011fer"),
    ("MAT-345S25-U14", "\u00dcsl\u00fc \u0130fadeler"),
    ("MAT-345S25-U15", "K\u00f6kl\u00fc \u0130fadeler"),
    ("MAT-345S25-U16", "\u00c7arpanlara Ay\u0131rma"),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'MATEMATIK', TRUE, now(), now())
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
    "345 2025 Start Matematik'in unite ayraci sayfalarindan "
    "(dosya 4, 18, 38, 52, 70, 90, 122, 144, 162, 176, 190, 202, 220, 240, "
    "270, 300) uretildi (0057)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0057] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0057] mv_safe_for_beta yenilendi")


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
        _log.info("[0057] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": MAT_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0057] %s kok konusu yok -- atlandi", MAT_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz MAT-345S25 deseni; diger MAT dugumlerine DOKUNULMAZ. LIKE deseni
    # '-' ile biter ki MAT-345S250 gibi bir onek yanlislikla eslesmesin.
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
        "[0057] %s unite tanimi; bu kosumda eklenen dugum: %s",
        len(UNITELER),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0057] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0057] %s dugum hala soru tasiyor -- SILINMEDI "
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
    _log.info("[0057] downgrade tamam; silinmeye aday dugum: %s", len(idler))
