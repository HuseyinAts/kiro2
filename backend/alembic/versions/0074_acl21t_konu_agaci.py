"""2020-2021 ACIL TYT Matematik: kitabin kendi bolum / konu agaci (MAT-ACL21T).

Revision ID: 0074_acl21t_agac
Revises: 0073_acl20t_beta_onay
Create Date: 2026-09-27

NEDEN
-----
Bu kitabin ithali her testi (150 test, 2113 soru) kitabin bolum / konu
yapisina baglar. MAT kokunun altindaki dugumler baska kitaplarin
agaclaridir (MAT-345T25-*, MAT-ACL20T-*, ...); bu kitabin konulari onlarla birebir
ortusmez. Bu migration kitabin agacini MAT-ACL21T onekiyle ayri bir alt
agac olarak kurar (0042 / 0057 / 0068 / 0071 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/acil_2021_tyt_matematik_konu_haritasi.json`
ile BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya:
  * 13 bolum + 30 konu: icindekiler (dosya 3) ve konu baslangic sayfalari;
  * her testin sayfalari tek bir konu araliginda; test ilk sayfasi ust
    bandi (iki bagimsiz okuma, fark 0) o konuyla ayni ya da basili alt
    basligi (BOLME / BOLUNEBILME, EBOB / EKOK, problem turleri, ...).
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Bolum kok+1 (MAT kokunun altinda, 13 dugum), konu kok+2 (bolume bagli, 30
dugum). Sorular konu dugumune baglanir; bolum dugumleri yalniz gruplama.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca
onlari siler (once konular, sonra bolumler) ve SORU TASIYAN ya da COCUGU
OLAN dugume DOKUNMAZ.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0074_acl21t_agac"
down_revision: Union[str, None] = "0073_acl20t_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acl21t_konu_gunlugu_0074"
KOK = "MAT"
KOD_ONEKI = "MAT-ACL21T"
ALAN = "MATEMATIK"

# (kod, ad)
BOLUMLER: tuple[tuple[str, str], ...] = (
    ("MAT-ACL21T-B01", "SAYILAR"),
    ("MAT-ACL21T-B02", "RASYONEL VE ONDALIKLI SAYILAR"),
    ("MAT-ACL21T-B03", "BAS\u0130T E\u015e\u0130TS\u0130ZL\u0130K-MUTLAK DE\u011eER"),
    ("MAT-ACL21T-B04", "\xdcSL\xdc-K\xd6KL\xdc SAYILAR"),
    ("MAT-ACL21T-B05", "\xc7ARPANLARA AYIRMA"),
    ("MAT-ACL21T-B06", "ORAN-ORANTI"),
    ("MAT-ACL21T-B07", "B\u0130R\u0130NC\u0130 DERECEDEN DENKLEMLER"),
    ("MAT-ACL21T-B08", "PROBLEMLER"),
    ("MAT-ACL21T-B09", "SEMBOL\u0130K MANTIK"),
    ("MAT-ACL21T-B10", "K\xdcMELER-KARTEZYEN \xc7ARPIM"),
    ("MAT-ACL21T-B11", "FONKS\u0130YONLAR"),
    ("MAT-ACL21T-B12", "SAYMA-OLASILIK"),
    ("MAT-ACL21T-B13", "\u0130STAT\u0130ST\u0130K"),
)

# (kod, ad, bolum kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("MAT-ACL21T-B01-K01", "Pozitif ve Negatif Tam Say\u0131lar", "MAT-ACL21T-B01"),
    ("MAT-ACL21T-B01-K02", "Tek ve \xc7ift Say\u0131lar", "MAT-ACL21T-B01"),
    (
        "MAT-ACL21T-B01-K03",
        "En K\xfc\xe7\xfck ve En B\xfcy\xfck De\u011fer Bulma",
        "MAT-ACL21T-B01",
    ),
    (
        "MAT-ACL21T-B01-K04",
        "Ard\u0131\u015f\u0131k Say\u0131lar ve \xd6r\xfcnt\xfc",
        "MAT-ACL21T-B01",
    ),
    ("MAT-ACL21T-B01-K05", "\u0130\u015flem Yetene\u011fi", "MAT-ACL21T-B01"),
    ("MAT-ACL21T-B01-K06", "Basamak Kavram\u0131", "MAT-ACL21T-B01"),
    ("MAT-ACL21T-B01-K07", "B\xf6lme-B\xf6l\xfcnebilme", "MAT-ACL21T-B01"),
    ("MAT-ACL21T-B01-K08", "Fakt\xf6riyel", "MAT-ACL21T-B01"),
    (
        "MAT-ACL21T-B01-K09",
        "Asal Say\u0131lar-Asal \xc7arpanlara Ay\u0131rma",
        "MAT-ACL21T-B01",
    ),
    ("MAT-ACL21T-B01-K10", "EBOB-EKOK", "MAT-ACL21T-B01"),
    ("MAT-ACL21T-B01-K11", "Periyodik Problemler", "MAT-ACL21T-B01"),
    (
        "MAT-ACL21T-B02-K01",
        "Rasyonel ve Ondal\u0131kl\u0131 Say\u0131lar",
        "MAT-ACL21T-B02",
    ),
    ("MAT-ACL21T-B03-K01", "Basit E\u015fitsizlik", "MAT-ACL21T-B03"),
    ("MAT-ACL21T-B03-K02", "Mutlak De\u011fer", "MAT-ACL21T-B03"),
    ("MAT-ACL21T-B04-K01", "\xdcsl\xfc Say\u0131lar", "MAT-ACL21T-B04"),
    ("MAT-ACL21T-B04-K02", "K\xf6kl\xfc Say\u0131lar", "MAT-ACL21T-B04"),
    ("MAT-ACL21T-B04-K03", "Reel Say\u0131lar", "MAT-ACL21T-B04"),
    ("MAT-ACL21T-B05-K01", "\xc7arpanlara Ay\u0131rma", "MAT-ACL21T-B05"),
    ("MAT-ACL21T-B06-K01", "Oran-Orant\u0131", "MAT-ACL21T-B06"),
    ("MAT-ACL21T-B06-K02", "Bilin\xe7li T\xfcketim Aritmeti\u011fi", "MAT-ACL21T-B06"),
    ("MAT-ACL21T-B07-K01", "Birinci Dereceden Denklemler", "MAT-ACL21T-B07"),
    ("MAT-ACL21T-B08-K01", "Problemler", "MAT-ACL21T-B08"),
    ("MAT-ACL21T-B09-K01", "Sembolik Mant\u0131k", "MAT-ACL21T-B09"),
    ("MAT-ACL21T-B10-K01", "K\xfcmeler-Kartezyen \xc7arp\u0131m", "MAT-ACL21T-B10"),
    ("MAT-ACL21T-B11-K01", "Fonksiyonlar", "MAT-ACL21T-B11"),
    ("MAT-ACL21T-B12-K01", "Perm\xfctasyon", "MAT-ACL21T-B12"),
    ("MAT-ACL21T-B12-K02", "Kombinasyon", "MAT-ACL21T-B12"),
    ("MAT-ACL21T-B12-K03", "Binom A\xe7\u0131l\u0131m\u0131", "MAT-ACL21T-B12"),
    ("MAT-ACL21T-B12-K04", "Olas\u0131l\u0131k", "MAT-ACL21T-B12"),
    ("MAT-ACL21T-B13-K01", "\u0130statistik", "MAT-ACL21T-B13"),
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
    "2020-2021 ACIL TYT Matematik Soru Bankasi'nin icindekiler sayfasi ve test "
    "ust bantlarindan (iki bagimsiz okuma) uretildi (0074)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0074] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0074] mv_safe_for_beta yenilendi")


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
            f"INSERT INTO {GUNLUK} (id, kod, olusturuldu) "  # noqa: S608  # nosec B608
            "VALUES (:id, :kod, TRUE)"
        ),
        {"id": yeni_id, "kod": kod},
    )
    return yeni_id


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0074] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0074] %s kok konusu yok -- atlandi", KOK)
        return
    kok_id, kok_level = r[0], int(r[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz MAT-ACL21T deseni; MAT kokunun diger dugumlerine DOKUNULMAZ. LIKE
    # deseni '-' ile biter ki MAT-ACL21T0 gibi bir onek yanlislikla eslesmesin.
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
        "[0074] %s bolum + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0074] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0074] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Iki duzey: once yapraklar (konular), sonra cocugu kalmayan bolumler;
        # cocugu olan dugum silinmez.
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
    _log.info("[0074] downgrade tamam; silinmeye aday dugum: %s", len(idler))
