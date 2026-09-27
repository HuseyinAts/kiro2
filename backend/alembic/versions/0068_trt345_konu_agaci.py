"""345 2025 TYT Turkce: kitabin kendi unite / konu agaci (TUR-345T25).

Revision ID: 0068_trt345_agac
Revises: 0067_sos345_beta_onay
Create Date: 2026-09-27

NEDEN
-----
Bu kitabin ithali her testi (207 test, 2070 soru) kitabin unite / konu
yapisina baglar. TUR kokunun altindaki dugumler baska kitaplarin
agaclaridir (TUR-BS*, TUR-D*, TUR-345P25-*); bu kitabin konulari onlarla
birebir ortusmez. Bu migration kitabin agacini TUR-345T25 onekiyle ayri bir
alt agac olarak kurar (0042 / 0055 / 0057 / 0060 / 0062 / 0065 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/345_2025_tyt_turkce_konu_haritasi.json`
ile BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya:
  * 8 unite: icindekiler (dosya 3-4, gozle) + unite kapak sayfalari.
  * 27 konu: cevap anahtari tablosunun konu basliklari; her konunun ilk test
    sayfasi == icindekiler sayfasi; 420 soru sayfasinin ust bandi (iki
    bagimsiz okuma, fark 0) anahtarla ayni (tur, no, konu).
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Unite kok+1 (TUR kokunun altinda, 8 dugum), konu kok+2 (uniteye bagli, 27
dugum). KO / OT / OR testleri konu dugumune, KA ('Karma Sorular') testleri
unite dugumune baglanir.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca
onlari siler (once konular, sonra uniteler) ve SORU TASIYAN ya da COCUGU
OLAN dugume DOKUNMAZ.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0068_trt345_agac"
down_revision: Union[str, None] = "0067_sos345_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "trt345_konu_gunlugu_0068"
KOK = "TUR"
KOD_ONEKI = "TUR-345T25"
ALAN = "TURKCE"

# (kod, ad)
UNITELER: tuple[tuple[str, str], ...] = (
    ("TUR-345T25-U01", "ANLAM B\u0130LG\u0130S\u0130"),
    ("TUR-345T25-U02", "SES - YAZIM - NOKTALAMA"),
    ("TUR-345T25-U03", "S\xd6ZC\xdcK YAPISI"),
    ("TUR-345T25-U04", "\u0130S\u0130M SOYLU S\xd6ZC\xdcKLER"),
    ("TUR-345T25-U05", "F\u0130\u0130LLER (EYLEMLER)"),
    ("TUR-345T25-U06", "C\xdcMLE B\u0130LG\u0130S\u0130"),
    ("TUR-345T25-U07", "ANLATIM BOZUKLU\u011eU"),
    ("TUR-345T25-U08", "KARMA D\u0130L B\u0130LG\u0130S\u0130"),
)

# (kod, ad, unite kodu)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("TUR-345T25-U01-K01", "S\xd6ZC\xdcKTE ANLAM", "TUR-345T25-U01"),
    ("TUR-345T25-U01-K02", "DEY\u0130M VE ATAS\xd6Z\xdc", "TUR-345T25-U01"),
    ("TUR-345T25-U01-K03", "C\xdcMLEDE KAVRAMLAR", "TUR-345T25-U01"),
    ("TUR-345T25-U01-K04", "C\xdcMLE YORUMU", "TUR-345T25-U01"),
    ("TUR-345T25-U01-K05", "ANLATIM TEKN\u0130KLER\u0130", "TUR-345T25-U01"),
    ("TUR-345T25-U01-K06", "PARAGRAF YORUMU", "TUR-345T25-U01"),
    ("TUR-345T25-U01-K07", "PARAGRAFTA YARDIMCI D\xdc\u015e\xdcNCE", "TUR-345T25-U01"),
    ("TUR-345T25-U01-K08", "PARAGRAF YAPISI", "TUR-345T25-U01"),
    ("TUR-345T25-U02-K01", "SES B\u0130LG\u0130S\u0130", "TUR-345T25-U02"),
    ("TUR-345T25-U02-K02", "YAZIM KURALLARI", "TUR-345T25-U02"),
    ("TUR-345T25-U02-K03", "NOKTALAMA \u0130\u015eARETLER\u0130", "TUR-345T25-U02"),
    ("TUR-345T25-U03-K01", "S\xd6ZC\xdcK YAPISI", "TUR-345T25-U03"),
    ("TUR-345T25-U04-K01", "\u0130S\u0130M (AD)", "TUR-345T25-U04"),
    ("TUR-345T25-U04-K02", "SIFAT (\xd6N AD)", "TUR-345T25-U04"),
    ("TUR-345T25-U04-K03", "ZAM\u0130R (ADIL)", "TUR-345T25-U04"),
    ("TUR-345T25-U04-K04", "ZARF (BEL\u0130RTE\xc7)", "TUR-345T25-U04"),
    ("TUR-345T25-U04-K05", "EDAT (\u0130LGE\xc7) - BA\u011eLA\xc7 - \xdcNLEM", "TUR-345T25-U04"),
    ("TUR-345T25-U05-K01", "F\u0130\u0130L - F\u0130\u0130L \xc7EK\u0130M\u0130", "TUR-345T25-U05"),
    ("TUR-345T25-U05-K02", "F\u0130\u0130L - EK F\u0130\u0130L", "TUR-345T25-U05"),
    ("TUR-345T25-U05-K03", "F\u0130\u0130L - F\u0130\u0130LDE YAPI", "TUR-345T25-U05"),
    ("TUR-345T25-U05-K04", "F\u0130\u0130L - F\u0130\u0130L\u0130MS\u0130LER", "TUR-345T25-U05"),
    ("TUR-345T25-U05-K05", "F\u0130\u0130L - F\u0130\u0130LDE \xc7ATI", "TUR-345T25-U05"),
    ("TUR-345T25-U06-K01", "S\xd6Z \xd6BEKLER\u0130", "TUR-345T25-U06"),
    ("TUR-345T25-U06-K02", "C\xdcMLEN\u0130N \xd6GELER\u0130", "TUR-345T25-U06"),
    ("TUR-345T25-U06-K03", "C\xdcMLE \xc7E\u015e\u0130TLER\u0130", "TUR-345T25-U06"),
    ("TUR-345T25-U07-K01", "ANLAMA DAYALI ANLATIM BOZUKLUKLARI", "TUR-345T25-U07"),
    ("TUR-345T25-U07-K02", "D\u0130L B\u0130LG\u0130S\u0130NE DAYALI ANLATIM BOZUKLUKLARI", "TUR-345T25-U07"),
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
    "345 2025 TYT Turkce Soru Bankasi'nin icindekiler, cevap anahtari konu "
    "basliklari ve soru sayfasi ust bantlarindan (iki bagimsiz okuma) uretildi (0068)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0068] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0068] mv_safe_for_beta yenilendi")


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
        _log.info("[0068] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    r = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": KOK},
    ).fetchone()
    if r is None:
        _log.warning("[0068] %s kok konusu yok -- atlandi", KOK)
        return
    kok_id, kok_level = r[0], int(r[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz TUR-345T25 deseni; TUR kokunun diger dugumlerine DOKUNULMAZ. LIKE
    # deseni '-' ile biter ki TUR-345T250 gibi bir onek yanlislikla eslesmesin.
    mevcut = {
        r[0]: r[1]
        for r in b.execute(
            sa.text("SELECT code, id FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "-%"},
        ).fetchall()
    }

    eklenen = 0
    unite_id = {}
    for kod, ad in UNITELER:
        if kod in mevcut:
            unite_id[kod] = mevcut[kod]
            continue
        unite_id[kod] = _yaz(b, kod, ad, kok_level + 1, kok_id, alan=ALAN)
        eklenen += 1
    for kod, ad, unite in KONULAR:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 2, unite_id[unite], alan=ALAN)
        eklenen += 1

    _log.info(
        "[0068] %s unite + %s konu tanimi; bu kosumda eklenen dugum: %s",
        len(UNITELER),
        len(KONULAR),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0068] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0068] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Iki duzey: once yapraklar (konular), sonra cocugu kalmayan uniteler;
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
    _log.info("[0068] downgrade tamam; silinmeye aday dugum: %s", len(idler))
