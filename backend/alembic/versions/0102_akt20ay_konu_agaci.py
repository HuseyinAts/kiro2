"""2019-2020 Aktif AYT Kimya: kitabin kendi bolum / konu agaci (KIM-AKT20AY).

Revision ID: 0102_akt20ay_agac
Revises: 0101_akt20k0_beta_onay
Create Date: 2026-09-28

NEDEN
-----
Bu kitabin ithali her testi (71 test, 937 soru) kitabin bolum / konu
yapisina baglar. KIM kokunun altindaki dugumler baska kitaplarin agaclaridir;
bu migration kitabin agacini KIM-AKT20AY onekiyle ayri bir alt agac olarak kurar
(0071 / 0074 deseni; kitap_hat/migration_uret.py ile uretildi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/aktif_2020_ayt_kimya_konu_haritasi.json` ile
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

revision: str = "0102_akt20ay_agac"
down_revision: Union[str, None] = "0101_akt20k0_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "akt20ay_konu_gunlugu_0102"
KOK = "KIM"
KOD_ONEKI = "KIM-AKT20AY"
ALAN = "KIMYA"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    (
        "KIM-AKT20AY-B01",
        "MODERN ATOM TEOR\u0130S\u0130 / PER\u0130YOD\u0130K S\u0130STEM",
    ),
    ("KIM-AKT20AY-B02", "GAZLAR"),
    (
        "KIM-AKT20AY-B03",
        "SIVI \u00c7\u00d6ZELT\u0130LER VE \u00c7\u00d6Z\u00dcN\u00dcRL\u00dcK",
    ),
    ("KIM-AKT20AY-B04", "K\u0130MYASAL TEPK\u0130MELERDE ENERJ\u0130"),
    ("KIM-AKT20AY-B05", "K\u0130MYASAL TEPK\u0130MELERDE HIZ"),
    ("KIM-AKT20AY-B06", "K\u0130MYASAL TEPK\u0130MELERDE DENGE"),
    ("KIM-AKT20AY-B07", "SULU \u00c7\u00d6ZELT\u0130LERDE DENGE"),
    ("KIM-AKT20AY-B08", "K\u0130MYA VE ELEKTR\u0130K"),
    ("KIM-AKT20AY-B09", "KARBON K\u0130MYASINA G\u0130R\u0130\u015e"),
    ("KIM-AKT20AY-B10", "H\u0130DROKARBONLAR"),
    ("KIM-AKT20AY-B11", "FONKS\u0130YONEL GRUPLAR"),
    (
        "KIM-AKT20AY-B12",
        "ENERJ\u0130 KAYNAKLARI VE B\u0130L\u0130MSEL GEL\u0130\u015eMELER",
    ),
)

# (kod, ad, bolum kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("KIM-AKT20AY-B01-K01", "Modern Atom Teorisi", "KIM-AKT20AY-B01"),
    ("KIM-AKT20AY-B01-K02", "Periyodik Sistem", "KIM-AKT20AY-B01"),
    ("KIM-AKT20AY-B02-K01", "Gazlar", "KIM-AKT20AY-B02"),
    (
        "KIM-AKT20AY-B03-K01",
        "S\u0131v\u0131 \u00c7\u00f6zeltiler ve \u00c7\u00f6z\u00fcn\u00fcrl\u00fck",
        "KIM-AKT20AY-B03",
    ),
    ("KIM-AKT20AY-B04-K01", "Kimyasal Tepkimelerde Enerji", "KIM-AKT20AY-B04"),
    ("KIM-AKT20AY-B05-K01", "Kimyasal Tepkimelerde H\u0131z", "KIM-AKT20AY-B05"),
    ("KIM-AKT20AY-B06-K01", "Kimyasal Tepkimelerde Denge", "KIM-AKT20AY-B06"),
    ("KIM-AKT20AY-B07-K01", "Sulu \u00c7\u00f6zeltilerde Denge", "KIM-AKT20AY-B07"),
    ("KIM-AKT20AY-B08-K01", "Kimya ve Elektrik", "KIM-AKT20AY-B08"),
    ("KIM-AKT20AY-B09-K01", "Karbon Kimyas\u0131na Giri\u015f", "KIM-AKT20AY-B09"),
    ("KIM-AKT20AY-B10-K01", "Hidrokarbonlar", "KIM-AKT20AY-B10"),
    ("KIM-AKT20AY-B11-K01", "Fonksiyonel Gruplar", "KIM-AKT20AY-B11"),
    (
        "KIM-AKT20AY-B12-K01",
        "Enerji Kaynaklar\u0131 ve Bilimsel Geli\u015fmeler",
        "KIM-AKT20AY-B12",
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
    "2019-2020 Aktif AYT Kimya icindekiler ve test ust bantlarindan (iki bagimsiz okuma) "
    "uretildi (0102)."
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
        _log.info("[0102] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0102] mv_safe_for_beta yenilendi")


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
        _log.info("[0102] topic_hierarchy yok (taze DB?) -- atlandi")
        return
    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0102] %s kok konusu yok -- atlandi", KOK)
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
        "[0102] %s bolum + %s konu tanimi; eklenen dugum: %s",
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
        _log.info("[0102] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0102] %s dugum hala soru tasiyor -- SILINMEDI", len(kullanilan)
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
    _log.info("[0102] downgrade tamam; silinmeye aday dugum: %s", len(idler))
