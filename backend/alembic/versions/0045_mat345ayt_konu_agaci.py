"""345 2025 AYT Matematik Soru Bankasi: kitabin kendi konu agaci (MAT-345A25).

Revision ID: 0045_mat345ayt_agac
Revises: 0044_mat345_eski_hat_cevap
Create Date: 2026-09-24

NEDEN
-----
Bu kitabin ithali her soruyu bir konu dugumune baglar. MAT kokunun altinda
genel MAT.* dugumleri ve 0042'nin TYT alt agaci (MAT-345T25) var; kitabin
kendi 15 konusu (or. 'Ikinci Dereceden Denklemler', 'Turev - II',
'Integral - I') onlarla birebir ortusmuyor. Sessizce "en yakin" dugume
baglamak yanlis veridir; bu migration kitabin agacini MAT-345A25 onekiyle
ayri bir alt agac olarak kurar (0033 / 0041 / 0042 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/345_2025_ayt_matematik_konu_haritasi.json`
ile BIREBIR aynidir (ASCII katlanmis); o dosya:
  * 6 bolum + 15 konu + baslangic sayfalari: kitabin KENDI icindekiler
    sayfalari (dosya 3-4). Bolum ayraci sayfalari yalniz 'BOLUM NN' basiyor;
    bolumlerin ayrica adi YOK, 'Bolum NN' olarak kuruldu (uydurulmadi).
  * Bagimsiz dogrulama: 187 testin 187'si tek bir icindekiler araligina
    dusuyor; bantta konu adi basili 176 testin 176'sinda bant == aralik.
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Bolum kok+1, konu kok+2. Sorular KONU dugumune baglanir; bolum dugumleri
soru tasimaz (yalniz gruplama).

6 bolum + 15 konu = 21 dugum.

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

revision: str = "0045_mat345ayt_agac"
down_revision: Union[str, None] = "0044_mat345_eski_hat_cevap"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "mat345ayt_konu_gunlugu_0045"
MAT_KOK_KODU = "MAT"
KOD_ONEKI = "MAT-345A25"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    ("MAT-345A25-B01", "Bolum 01"),
    ("MAT-345A25-B02", "Bolum 02"),
    ("MAT-345A25-B03", "Bolum 03"),
    ("MAT-345A25-B04", "Bolum 04"),
    ("MAT-345A25-B05", "Bolum 05"),
    ("MAT-345A25-B06", "Bolum 06"),
)

# (ust bolum kodu, kod, ad)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("MAT-345A25-B01", "MAT-345A25-B01-01", "Polinomlar"),
    ("MAT-345A25-B01", "MAT-345A25-B01-02", "Ikinci Dereceden Denklemler"),
    ("MAT-345A25-B01", "MAT-345A25-B01-03", "Parabol"),
    ("MAT-345A25-B01", "MAT-345A25-B01-04", "Esitsizlikler"),
    ("MAT-345A25-B02", "MAT-345A25-B02-01", "Trigonometri - I"),
    ("MAT-345A25-B02", "MAT-345A25-B02-02", "Trigonometri - II"),
    ("MAT-345A25-B03", "MAT-345A25-B03-01", "Logaritma"),
    ("MAT-345A25-B04", "MAT-345A25-B04-01", "Diziler"),
    ("MAT-345A25-B04", "MAT-345A25-B04-02", "Fonksiyonlar"),
    ("MAT-345A25-B05", "MAT-345A25-B05-01", "Limit - Sureklilik"),
    ("MAT-345A25-B05", "MAT-345A25-B05-02", "Turev - I"),
    ("MAT-345A25-B05", "MAT-345A25-B05-03", "Turev - II"),
    ("MAT-345A25-B05", "MAT-345A25-B05-04", "Integral - I"),
    ("MAT-345A25-B05", "MAT-345A25-B05-05", "Integral - II"),
    ("MAT-345A25-B06", "MAT-345A25-B06-01", "Sayma - Olasilik"),
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
    "345 2025 AYT Matematik Soru Bankasi'nin kendi icindekiler sayfalarindan "
    "(dosya 3-4) uretildi (0045)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0045] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0045] mv_safe_for_beta yenilendi")


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
        _log.info("[0045] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": MAT_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0045] %s kok konusu yok -- atlandi", MAT_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz MAT-345A25 deseni; MAT.* genel dugumlerine DOKUNULMAZ. LIKE deseni
    # '-' ile biter ki MAT-345A250 gibi bir onek yanlislikla eslesmesin.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "-%"},
        ).fetchall()
    }

    kimlik: dict[str, str] = {}

    def _id_al(kod: str) -> str:
        mevcut_id: str = b.execute(
            sa.text("SELECT id FROM topic_hierarchy WHERE code = :k"), {"k": kod}
        ).scalar_one()
        return mevcut_id

    eklenen = 0
    for kod, ad in BOLUMLER:
        if kod in mevcut:
            kimlik[kod] = _id_al(kod)
            continue
        kimlik[kod] = _yaz(b, kod, ad, kok_level + 1, kok_id)
        eklenen += 1

    for ust, kod, ad in KONULAR:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 2, kimlik[ust])
        eklenen += 1

    _log.info(
        "[0045] %s bolum + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0045] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0045] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Once yapraklar (konu), sonra bolumler: cocugu olan silinmez.
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
    _log.info("[0045] downgrade tamam; silinmeye aday dugum: %s", len(idler))
