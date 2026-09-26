"""345 2025 TYT Kimya: kitabin kendi unite agaci (KIM-345T25).

Revision ID: 0062_kmt345_agac
Revises: 0061_fzt345_beta_onay
Create Date: 2026-09-27

NEDEN
-----
Bu kitabin ithali her testi kitabin 9 unitesinden birine baglar. KIM
kokunun altindaki dugumler baska kitaplarin agaclaridir; bu kitabin
uniteleri ('Kimya Bilimi' ... 'Kimya Her Yerde') onlarla birebir
ortusmez. Sessizce "en yakin" dugume baglamak yanlis veridir; bu migration
kitabin agacini KIM-345T25 onekiyle ayri bir alt agac olarak kurar
(0042 / 0055 / 0057 / 0060 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/345_2025_tyt_kimya_konu_haritasi.json`
ile BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya:
  * 9 unite: icindekiler (dosya 3-4, gozle), basili baslangic sayfalari.
  * Bagimsiz dogrulama: 9/9 unitenin ilk soru sayfasinin ust bandinda
    '1. TEST' rozeti + ilk konu adi; 138 testin her biri tek unitenin
    sayfa araliginda.
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Unite kok+1 (KIM kokunun altinda); 138 testin 1307 sorusu unite dugumune
baglanir. Kitap uniteyi konulara boler ama unite sonundaki 'OSYM TADINDA'
testleri butun uniteyi kapsar; konu duzeyi haritada kayitli, agaca
yazilmaz. 9 dugum.

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

revision: str = "0062_kmt345_agac"
down_revision: Union[str, None] = "0061_fzt345_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "kmt345_konu_gunlugu_0062"
KIM_KOK_KODU = "KIM"
KOD_ONEKI = "KIM-345T25"

# (kod, ad)
UNITELER: tuple[tuple[str, str], ...] = (
    ("KIM-345T25-U01", "Kimya Bilimi"),
    ("KIM-345T25-U02", "Atom ve Periyodik Sistem"),
    ("KIM-345T25-U03", "Kimyasal T\xfcrler Aras\u0131 Etkile\u015fimler"),
    ("KIM-345T25-U04", "Maddenin Halleri"),
    ("KIM-345T25-U05", "Do\u011fa ve Kimya"),
    ("KIM-345T25-U06", "Kimyan\u0131n Temel Kanunlar\u0131 ve Kimyasal Hesaplamalar"),
    ("KIM-345T25-U07", "Kar\u0131\u015f\u0131mlar"),
    ("KIM-345T25-U08", "Asitler, Bazlar ve Tuzlar"),
    ("KIM-345T25-U09", "Kimya Her Yerde"),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'KIMYA', TRUE, now(), now())
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
    "345 2025 TYT Kimya Soru Bankasi'nin icindekiler sayfalarindan (dosya 3-4) "
    "uretildi; baslangic sayfasi bantlariyla dogrulandi (0062)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0062] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0062] mv_safe_for_beta yenilendi")


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
        _log.info("[0062] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KIM_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0062] %s kok konusu yok -- atlandi", KIM_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz KIM-345T25 deseni; diger KIM dugumlerine DOKUNULMAZ. LIKE deseni
    # '-' ile biter ki KIM-345T250 gibi bir onek yanlislikla eslesmesin.
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
        "[0062] %s unite tanimi; bu kosumda eklenen dugum: %s",
        len(UNITELER),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0062] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0062] %s dugum hala soru tasiyor -- SILINMEDI "
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
    _log.info("[0062] downgrade tamam; silinmeye aday dugum: %s", len(idler))
