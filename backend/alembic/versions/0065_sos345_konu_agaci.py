"""345 2025 TYT Sosyal Bilgiler: kitabin kendi konu agaci (345T25).

Revision ID: 0065_sos345_agac
Revises: 0064_kmt345_beta_onay
Create Date: 2026-09-27

NEDEN
-----
Bu kitabin ithali her testi (150 test, 1233 soru) kitabin ust bandinda
basili konusuna baglar. TAR / COG / SOS koklerinin altindaki dugumler baska
kitaplarin agaclaridir; bu kitabin konulari onlarla birebir ortusmez. Bu
migration kitabin konularini 345T25 onekli ayri alt agaclar olarak kurar
(0042 / 0055 / 0057 / 0060 / 0062 deseni). Felsefe ve Din Kulturu icin ayri
kok yok; SOS ('Sosyal Bilimler') kokunun altina SOS-345T25-FEL / -DIN
onekiyle yazilir, dugumun subject_area'si FELSEFE / DIN.

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/345_2025_tyt_sosyal_konu_haritasi.json`
ile BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya:
  * 300 soru sayfasinin ust bandi (DERS, KONU, TEST, GUN) iki bagimsiz
    okuma, normalize fark 0.
  * Her testin iki sayfasinda bant (gun, test) == anahtar tablosu satiri.
  * Konu = test basligi; dugum = (ders, konu tabani) -- sondaki ' - I/II'
    eki atilir.
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Kok+1: TARIH 25, COGRAFYA 12, FELSEFE 15, DIN 17 = 69 dugum.

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

revision: str = "0065_sos345_agac"
down_revision: Union[str, None] = "0064_kmt345_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "sos345_konu_gunlugu_0065"
KOKLER = ("TAR", "COG", "SOS")
KOD_ONEKLERI = ("TAR-345T25", "COG-345T25", "SOS-345T25")

# (kod, ad, kok kodu, subject_area)
UNITELER: tuple[tuple[str, str, str, str], ...] = (
    (
        "TAR-345T25-U01",
        "TAR\u0130H VE ZAMAN / \u0130NSANLI\u011eIN \u0130LK D\xd6NEMLER\u0130",
        "TAR",
        "TARIH",
    ),
    (
        "TAR-345T25-U02",
        "\u0130NSANLI\u011eIN \u0130LK D\xd6NEMLER\u0130",
        "TAR",
        "TARIH",
    ),
    ("COG-345T25-U01", "DO\u011eA, \u0130NSAN VE CO\u011eRAFYA", "COG", "COGRAFYA"),
    ("SOS-345T25-FEL-U01", "FELSEFEY\u0130 TANIMA", "SOS", "FELSEFE"),
    ("SOS-345T25-DIN-U01", "B\u0130LG\u0130 VE \u0130NAN\xc7", "SOS", "DIN"),
    (
        "TAR-345T25-U03",
        "\u0130NSANLI\u011eIN \u0130LK D\xd6NEMLER\u0130 - / ORTA \xc7A\u011e'DA D\xdcNYA",
        "TAR",
        "TARIH",
    ),
    (
        "TAR-345T25-U04",
        "\u0130LK VE ORTA \xc7A\u011eLARDA / T\xdcRK D\xdcNYASI",
        "TAR",
        "TARIH",
    ),
    (
        "COG-345T25-U02",
        "D\xdcNYA'NIN \u015eEKL\u0130 VE HAREKETLER\u0130",
        "COG",
        "COGRAFYA",
    ),
    ("SOS-345T25-FEL-U02", "FELSEFE \u0130LE D\xdc\u015e\xdcNME", "SOS", "FELSEFE"),
    ("SOS-345T25-DIN-U02", "\u0130SLAM'DA \u0130NAN\xc7 ESASLARI", "SOS", "DIN"),
    (
        "TAR-345T25-U05",
        "\u0130SLAM MEDEN\u0130YET\u0130N\u0130N DO\u011eU\u015eU",
        "TAR",
        "TARIH",
    ),
    (
        "TAR-345T25-U06",
        "T\xdcRKLER\u0130N \u0130SLAM\u0130YET'\u0130 KABUL\xdc VE / \u0130LK T\xdcRK \u0130SLAM DEVLETLER\u0130",
        "TAR",
        "TARIH",
    ),
    ("SOS-345T25-DIN-U03", "\u0130SLAM'DA \u0130BADETLER", "SOS", "DIN"),
    (
        "TAR-345T25-U07",
        "T\xdcRKLER\u0130N \u0130SLAM\u0130YET'\u0130 KABUL\xdc VE \u0130LK T\xdcRK / \u0130SLAM DEVLETLER\u0130 - DEVLETLE\u015eME VE / YERLE\u015eME S\xdcREC\u0130NDE SEL\xc7UKLU T\xdcRK\u0130YES\u0130",
        "TAR",
        "TARIH",
    ),
    (
        "TAR-345T25-U08",
        "DEVLETLE\u015eME VE YERLE\u015eME / S\xdcREC\u0130NDE SEL\xc7UKLU T\xdcRK\u0130YES\u0130",
        "TAR",
        "TARIH",
    ),
    ("COG-345T25-U03", "CO\u011eRAF\u0130 KONUM", "COG", "COGRAFYA"),
    (
        "SOS-345T25-FEL-U03",
        "FELSEFEN\u0130N TEMEL KONULARI VE / PROBLEMLER\u0130 (VARLIK FELSEFES\u0130)",
        "SOS",
        "FELSEFE",
    ),
    (
        "TAR-345T25-U09",
        "BEYL\u0130KTEN DEVLETE OSMANLI / S\u0130YASET\u0130 (1302 - 1453)",
        "TAR",
        "TARIH",
    ),
    ("COG-345T25-U04", "HAR\u0130TA B\u0130LG\u0130S\u0130", "COG", "COGRAFYA"),
    (
        "TAR-345T25-U10",
        "DEVLETLE\u015eME S\xdcREC\u0130NDE / SAVA\u015e\xc7ILAR VE ASKERLER",
        "TAR",
        "TARIH",
    ),
    (
        "TAR-345T25-U11",
        "BEYL\u0130KTEN DEVLETE OSMANLI / MEDEN\u0130YET\u0130",
        "TAR",
        "TARIH",
    ),
    (
        "SOS-345T25-FEL-U04",
        "FELSEFEN\u0130N TEMEL KONULARI VE / PROBLEMLER\u0130 (B\u0130LG\u0130 FELSEFES\u0130)",
        "SOS",
        "FELSEFE",
    ),
    ("SOS-345T25-DIN-U04", "GEN\xc7L\u0130K VE DE\u011eERLER", "SOS", "DIN"),
    ("TAR-345T25-U12", "D\xdcNYA G\xdcC\xdc OSMANLI / (1453 - 1595)", "TAR", "TARIH"),
    ("COG-345T25-U05", "\u0130KL\u0130M B\u0130LG\u0130S\u0130", "COG", "COGRAFYA"),
    ("TAR-345T25-U13", "SULTAN VE OSMANLI MERKEZ TE\u015eK\u0130LATI", "TAR", "TARIH"),
    (
        "SOS-345T25-FEL-U05",
        "FELSEFEN\u0130N TEMEL KONULARI VE / PROBLEMLER\u0130 (B\u0130L\u0130M FELSEFES\u0130)",
        "SOS",
        "FELSEFE",
    ),
    (
        "TAR-345T25-U14",
        "KLAS\u0130K \xc7A\u011e'DA OSMANLI / TOPLUM D\xdcZEN\u0130",
        "TAR",
        "TARIH",
    ),
    (
        "TAR-345T25-U15",
        "DE\u011e\u0130\u015eEN D\xdcNYA DENGELER\u0130 / KAR\u015eISINDA OSMANLI S\u0130YASET\u0130 / (1595-1774)",
        "TAR",
        "TARIH",
    ),
    (
        "SOS-345T25-FEL-U06",
        "FELSEFEN\u0130N TEMEL KONULARI VE / PROBLEMLER\u0130 (AHLAK FELSEFES\u0130)",
        "SOS",
        "FELSEFE",
    ),
    ("SOS-345T25-DIN-U05", "G\xd6N\xdcL CO\u011eRAFYAMIZ", "SOS", "DIN"),
    (
        "SOS-345T25-DIN-U06",
        "ALLAH VE \u0130NSAN \u0130L\u0130\u015eK\u0130LER\u0130",
        "SOS",
        "DIN",
    ),
    (
        "TAR-345T25-U16",
        "DE\u011e\u0130\u015e\u0130M \xc7A\u011eINDA AVRUPA / VE OSMANLI",
        "TAR",
        "TARIH",
    ),
    ("COG-345T25-U06", "\u0130\xc7 VE DI\u015e KUVVETLER", "COG", "COGRAFYA"),
    (
        "SOS-345T25-FEL-U07",
        "FELSEFEN\u0130N TEMEL KONULARI VE / PROBLEMLER\u0130 (D\u0130N FELSEFES\u0130)",
        "SOS",
        "FELSEFE",
    ),
    ("SOS-345T25-DIN-U07", "HZ MUHAMMET (SAV) VE GEN\xc7L\u0130K", "SOS", "DIN"),
    (
        "TAR-345T25-U17",
        "DEVR\u0130MLER \xc7A\u011eINDA DE\u011e\u0130\u015eEN / DEVLET - TOPLUM \u0130L\u0130\u015eK\u0130LER\u0130",
        "TAR",
        "TARIH",
    ),
    (
        "SOS-345T25-FEL-U08",
        "FELSEFEN\u0130N TEMEL KONULARI VE / PROBLEMLER\u0130 (S\u0130YASET FELSEFES\u0130)",
        "SOS",
        "FELSEFE",
    ),
    ("SOS-345T25-DIN-U08", "D\u0130N VE HAYAT", "SOS", "DIN"),
    (
        "TAR-345T25-U18",
        "ULUSLARARASI \u0130L\u0130\u015eK\u0130LERDE / DENGE STRATEJ\u0130S\u0130 (1774-1914)",
        "TAR",
        "TARIH",
    ),
    (
        "SOS-345T25-FEL-U09",
        "FELSEFEN\u0130N TEMEL KONULARI VE / PROBLEMLER\u0130 (SANAT FELSEFES\u0130)",
        "SOS",
        "FELSEFE",
    ),
    ("COG-345T25-U07", "SU - TOPRAK - B\u0130TK\u0130", "COG", "COGRAFYA"),
    ("SOS-345T25-DIN-U09", "AHLAK\u0130 TUTUM VE DAVRANI\u015eLAR", "SOS", "DIN"),
    (
        "TAR-345T25-U19",
        "ULUSLARARASI \u0130L\u0130\u015eK\u0130LERDE DENGE / STRATEJ\u0130S\u0130 (1774-1914) - IV / XIX VE XX. / Y\xdcZYILDA DE\u011e\u0130\u015eEN SOSYOEKONOM\u0130K HAYAT",
        "TAR",
        "TARIH",
    ),
    (
        "TAR-345T25-U20",
        "XX. Y\xdcZYIL BA\u015eLARINDA / OSMANLI DEVLET\u0130 VE D\xdcNYA",
        "TAR",
        "TARIH",
    ),
    ("COG-345T25-U08", "N\xdcFUS, YERLE\u015eME VE G\xd6\xc7", "COG", "COGRAFYA"),
    ("SOS-345T25-FEL-U10", "FELSEF\u0130 OKUMA VE YAZMA", "SOS", "FELSEFE"),
    (
        "TAR-345T25-U21",
        "M\u0130LL\xce M\xdcCADELE - HAZIRLIK D\xd6NEM\u0130",
        "TAR",
        "TARIH",
    ),
    (
        "SOS-345T25-FEL-U11",
        "M\xd6 6. Y\xdcZYIL / MS 2. Y\xdcZYIL FELSEFES\u0130",
        "SOS",
        "FELSEFE",
    ),
    (
        "SOS-345T25-DIN-U10",
        "\u0130SLAM D\xdc\u015e\xdcNCES\u0130NDE \u0130T\u0130KAD\u0130, S\u0130YAS\u0130 / VE FIKH\u0130 YORUMLAR",
        "SOS",
        "DIN",
    ),
    ("SOS-345T25-DIN-U11", "D\xdcNYA VE AH\u0130RET", "SOS", "DIN"),
    ("COG-345T25-U09", "EKONOM\u0130K FAAL\u0130YETLER", "COG", "COGRAFYA"),
    (
        "SOS-345T25-FEL-U12",
        "MS 2. Y\xdcZYIL / 15. Y\xdcZYIL FELSEFES\u0130",
        "SOS",
        "FELSEFE",
    ),
    ("SOS-345T25-DIN-U12", "KUR'AN'A G\xd6RE HZ MUHAMMED", "SOS", "DIN"),
    ("TAR-345T25-U22", "M\u0130LL\xce M\xdcCADELE - CEPHELER", "TAR", "TARIH"),
    ("COG-345T25-U10", "B\xd6LGE KAVRAMI", "COG", "COGRAFYA"),
    (
        "SOS-345T25-FEL-U13",
        "15. Y\xdcZYIL / 17. Y\xdcZYIL FELSEFES\u0130",
        "SOS",
        "FELSEFE",
    ),
    ("SOS-345T25-DIN-U13", "KUR'AN'DA BAZI KAVRAMLAR", "SOS", "DIN"),
    ("SOS-345T25-DIN-U14", "\u0130SLAM VE B\u0130L\u0130M", "SOS", "DIN"),
    (
        "TAR-345T25-U23",
        "ATAT\xdcRK\xc7\xdcL\xdcK VE T\xdcRK \u0130NKILABI",
        "TAR",
        "TARIH",
    ),
    ("COG-345T25-U11", "B\xd6LGELER VE \xdcLKELER", "COG", "COGRAFYA"),
    (
        "SOS-345T25-FEL-U14",
        "18. Y\xdcZYIL / 19. Y\xdcZYIL FELSEFES\u0130",
        "SOS",
        "FELSEFE",
    ),
    ("COG-345T25-U12", "\xc7EVRE VE TOPLUM", "COG", "COGRAFYA"),
    ("SOS-345T25-DIN-U15", "ANADOLU'DA \u0130SLAM", "SOS", "DIN"),
    ("SOS-345T25-FEL-U15", "20. Y\xdcZYIL FELSEFES\u0130", "SOS", "FELSEFE"),
    (
        "TAR-345T25-U24",
        "\u0130K\u0130 SAVA\u015e ARASINDAK\u0130 D\xd6NEMDE / T\xdcRK\u0130YE VE D\xdcNYA- II. D\xdcNYA SAVA\u015eI S\xdcREC\u0130NDE / T\xdcRK\u0130YE VE D\xdcNYA- II. D\xdcNYA SAVA\u015eI SONRASINDA / T\xdcRK\u0130YE VE D\xdcNYA",
        "TAR",
        "TARIH",
    ),
    (
        "SOS-345T25-DIN-U16",
        "\u0130SLAM D\xdc\u015e\xdcNCES\u0130NDE TASAVVUF\u0130 / YORUMLAR",
        "SOS",
        "DIN",
    ),
    (
        "TAR-345T25-U25",
        "II. D\xdcNYA SAVA\u015eI SONRASINDA T\xdcRK\u0130YE VE D\xdcNYA- / TOPLUMSAL DEVR\u0130M \xc7A\u011eINDA D\xdcNYA VE T\xdcRK\u0130YE- / Y\xdcZYILIN E\u015e\u0130\u011e\u0130NDE T\xdcRK\u0130YE VE D\xdcNYA",
        "TAR",
        "TARIH",
    ),
    ("SOS-345T25-DIN-U17", "G\xdcNCEL D\u0130N\xce MESELELER", "SOS", "DIN"),
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
    "345 2025 TYT Sosyal Bilgiler Soru Bankasi'nin soru sayfasi ust bantlarindan "
    "(ders, konu; iki bagimsiz okuma) uretildi (0065)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0065] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0065] mv_safe_for_beta yenilendi")


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
        _log.info("[0065] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kokler = {}
    for kod in KOKLER:
        r = b.execute(
            sa.text(
                "SELECT id, level FROM topic_hierarchy "
                "WHERE code = :k AND parent_id IS NULL"
            ),
            {"k": kod},
        ).fetchone()
        if r is None:
            _log.warning("[0065] %s kok konusu yok -- atlandi", kod)
            return
        kokler[kod] = (r[0], int(r[1]))

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz 345T25 desenleri; koklerin diger dugumlerine DOKUNULMAZ. LIKE
    # deseni '-' ile biter ki TAR-345T250 gibi bir onek yanlislikla eslesmesin.
    mevcut = set()
    for onek in KOD_ONEKLERI:
        mevcut |= {
            r[0]
            for r in b.execute(
                sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
                {"onek": onek + "-%"},
            ).fetchall()
        }

    eklenen = 0
    for kod, ad, kok_kodu, alan in UNITELER:
        if kod in mevcut:
            continue
        kok_id, kok_level = kokler[kok_kodu]
        _yaz(b, kod, ad, kok_level + 1, kok_id, alan=alan)
        eklenen += 1

    _log.info(
        "[0065] %s unite tanimi; bu kosumda eklenen dugum: %s",
        len(UNITELER),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0065] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0065] %s dugum hala soru tasiyor -- SILINMEDI "
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
    _log.info("[0065] downgrade tamam; silinmeye aday dugum: %s", len(idler))
