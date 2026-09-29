"""2019-2020 APOTEMI TYT Matematik Soru Bankasi: kitabin kendi bolum / konu agaci (MAT-APO19MT).

Revision ID: 0116_apo19mt_agac
Revises: 0115_akt25pr_beta_onay
Create Date: 2026-09-28

NEDEN
-----
Bu kitabin ithali her testi (122 test, 1382 soru) kitabin bolum / konu
yapisina baglar. MAT kokunun altindaki dugumler baska kitaplarin agaclaridir;
bu migration kitabin agacini MAT-APO19MT onekiyle ayri bir alt agac olarak kurar
(0071 / 0074 deseni; kitap_hat/migration_uret.py ile uretildi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/apotemi_2019_tyt_matematik_konu_haritasi.json` ile
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

revision: str = "0116_apo19mt_agac"
down_revision: Union[str, None] = "0115_akt25pr_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "apo19mt_konu_gunlugu_0116"
KOK = "MAT"
KOD_ONEKI = "MAT-APO19MT"
ALAN = "MATEMATIK"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    ("MAT-APO19MT-B01", "TEMEL KAVRAMLAR - SAYI BASAMAKLARI"),
    ("MAT-APO19MT-B02", "B\u00d6LME - B\u00d6L\u00dcNEB\u0130LME - EBOB - EKOK"),
    ("MAT-APO19MT-B03", "RASYONEL SAYILAR - MUTLAK DE\u011eER"),
    ("MAT-APO19MT-B04", "\u00dcSL\u00dc VE K\u00d6KL\u00dc SAYILAR"),
    ("MAT-APO19MT-B05", "\u00c7ARPANLARA AYIRMA - DENKLEM \u00c7\u00d6ZME"),
    ("MAT-APO19MT-B06", "ORAN - ORANTI - ORTALAMALAR"),
    ("MAT-APO19MT-B07", "PROBLEMLER"),
    ("MAT-APO19MT-B08", "MANTIK - K\u00dcMELER - KARTEZYEN \u00c7ARPIM"),
    ("MAT-APO19MT-B09", "FONKS\u0130YONLAR"),
    (
        "MAT-APO19MT-B10",
        "PERM\u00dcTASYON - KOMB\u0130NASYON - OLASILIK - \u0130STAT\u0130ST\u0130K",
    ),
    (
        "MAT-APO19MT-B11",
        "POL\u0130NOMLAR - \u0130K\u0130NC\u0130 DERECEDEN DENKLEMLER - KARMA\u015eIK SAYILAR",
    ),
)

# (kod, ad, bolum kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    (
        "MAT-APO19MT-B01-K01",
        "Temel Kavramlar, Tek ve \u00c7ift Say\u0131lar, Pozitif ve Negatif Say\u0131lar, Asal Say\u0131lar, Ard\u0131\u015f\u0131k Say\u0131lar, Fakt\u00f6riyel, Say\u0131 Basamaklar\u0131",
        "MAT-APO19MT-B01",
    ),
    (
        "MAT-APO19MT-B02-K01",
        "B\u00f6lme - B\u00f6l\u00fcnebilme, Asal \u00c7arpanlara Ay\u0131rma, \u00d6zel Say\u0131 Problemleri, EBOB - EKOK",
        "MAT-APO19MT-B02",
    ),
    (
        "MAT-APO19MT-B03-K01",
        "Rasyonel Say\u0131lar, S\u0131ralama, 1. Dereceden Denklem ve E\u015fitsizlikler, Mutlak De\u011fer",
        "MAT-APO19MT-B03",
    ),
    (
        "MAT-APO19MT-B04-K01",
        "\u00dcsl\u00fc Say\u0131lar, K\u00f6kl\u00fc Say\u0131lar",
        "MAT-APO19MT-B04",
    ),
    (
        "MAT-APO19MT-B05-K01",
        "\u00c7arpanlara Ay\u0131rma, Denklem \u00c7\u00f6zme",
        "MAT-APO19MT-B05",
    ),
    (
        "MAT-APO19MT-B06-K01",
        "Oran - Orant\u0131, Orant\u0131 Problemleri, Ortalamalar",
        "MAT-APO19MT-B06",
    ),
    ("MAT-APO19MT-B07-K01", "Problemler", "MAT-APO19MT-B07"),
    (
        "MAT-APO19MT-B08-K01",
        "Mant\u0131k, K\u00fcmeler, K\u00fcme Problemleri, Kartezyen \u00c7arp\u0131m",
        "MAT-APO19MT-B08",
    ),
    (
        "MAT-APO19MT-B09-K01",
        "Fonksiyonlar, Fonksiyon \u00c7e\u015fitleri",
        "MAT-APO19MT-B09",
    ),
    (
        "MAT-APO19MT-B10-K01",
        "Perm\u00fctasyon, Kombinasyon, Binom, Olas\u0131l\u0131k, \u0130statistik",
        "MAT-APO19MT-B10",
    ),
    (
        "MAT-APO19MT-B11-K01",
        "Polinomlar, \u0130kinci Dereceden Denklemler, Karma\u015f\u0131k Say\u0131lar",
        "MAT-APO19MT-B11",
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
    "2019-2020 APOTEMI TYT Matematik Soru Bankasi icindekiler ve test ust bantlarindan (iki bagimsiz okuma) "
    "uretildi (0116)."
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
        _log.info("[0116] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0116] mv_safe_for_beta yenilendi")


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
        _log.info("[0116] topic_hierarchy yok (taze DB?) -- atlandi")
        return
    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0116] %s kok konusu yok -- atlandi", KOK)
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
        "[0116] %s bolum + %s konu tanimi; eklenen dugum: %s",
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
        _log.info("[0116] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0116] %s dugum hala soru tasiyor -- SILINMEDI", len(kullanilan)
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
    _log.info("[0116] downgrade tamam; silinmeye aday dugum: %s", len(idler))
