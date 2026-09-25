"""345 2025 AYT Turk Edebiyati Soru Bankasi: kitabin kendi konu agaci (EDB-345A25).

Revision ID: 0053_edb345ayt_agac
Revises: 0052_kim345ayt_eski_etiket
Create Date: 2026-09-25

NEDEN
-----
Bu kitabin ithali her soruyu bir konu ya da unite dugumune baglar. EDB
kokunun altindaki dugumler (EDB-OSYM-GENEL, EDB-BS1..) baska kitaplarin
agaclaridir; bu kitabin 10 unitesi ve 46 konusu (or. 'Guzel Sanatlar ve
Edebiyat', 'Garipciler (I. Yeni)') onlarla birebir ortusmuyor. Sessizce
"en yakin" dugume baglamak yanlis veridir; bu migration kitabin agacini
EDB-345A25 onekiyle ayri bir alt agac olarak kurar (0045 / 0049 deseni).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar `veriseti/zkitap/cikti/345_2025_ayt_edebiyat_konu_haritasi.json`
ile BIREBIR aynidir (Turkce harfler kaynakta \\u kacisli); o dosya:
  * 10 unite + 46 konu + baslangic sayfalari: kitabin KENDI icindekiler
    sayfalari (dosya 3-4); unite ayraci sayfalari 5, 39, 71, 113, 147, 191,
    221, 255, 275, 299 (unite 10 = Genel Bakis Testleri, konusu yok).
  * Bagimsiz dogrulama: 148 test bant kosusunun 148'i anahtarin test
    sirasiyla ayni; 46 konunun 46'sinda icindekiler baslangic sayfasi ==
    konunun ilk testinin ilk sayfasi.
Bu migration dosyasi o JSON'dan URETILDI.

DUZEY
-----
Unite kok+1, konu kok+2. Kazanim Odakli ve OSYM Tadinda testler (104 test,
1026 soru) KONU dugumune; Karma, Orijinal ve Genel Bakis testleri (44 test,
358 soru) UNITE dugumune baglanir: kitap bunlarin bandinda unite adini basar.

10 unite + 46 konu = 56 dugum.

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

revision: str = "0053_edb345ayt_agac"
down_revision: Union[str, None] = "0052_kim345ayt_eski_etiket"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "edb345ayt_konu_gunlugu_0053"
EDB_KOK_KODU = "EDB"
KOD_ONEKI = "EDB-345A25"

# (kod, ad)
UNITELER: tuple[tuple[str, str], ...] = (
    (
        "EDB-345A25-U01",
        "T\u00fcrk Edebiyat\u0131na Giri\u015f ve \u00d6\u011fretici Metinler",
    ),
    (
        "EDB-345A25-U02",
        "Co\u015fku ve Heyecan\u0131 Dile Getiren Metinler (\u015eiir Bilgisi)",
    ),
    (
        "EDB-345A25-U03",
        "\u0130slamiyet \u00d6ncesi ve \u0130slami D\u00f6nem T\u00fcrk \u015eiiri",
    ),
    ("EDB-345A25-U04", "Tanzimat'tan Mill\u00ee Edebiyat'a T\u00fcrk \u015eiiri"),
    ("EDB-345A25-U05", "Cumhuriyet D\u00f6nemi T\u00fcrk \u015eiiri"),
    (
        "EDB-345A25-U06",
        "Geleneksel Anlat\u0131 T\u00fcrleri - Tanzimat'tan Cumhuriyet'e Hik\u00e2ye",
    ),
    ("EDB-345A25-U07", "Tanzimat'tan Cumhuriyet'e Roman"),
    ("EDB-345A25-U08", "Tanzimat'tan Cumhuriyet'e Tiyatro"),
    (
        "EDB-345A25-U09",
        "Bat\u0131 Edebiyat\u0131 ve Edeb\u00ee Ak\u0131mlar - \u0130lkler ve Roman \u00d6zetleri",
    ),
    ("EDB-345A25-U10", "Genel Bak\u0131\u015f Testleri"),
)

# (ust unite kodu, kod, ad)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("EDB-345A25-U01", "EDB-345A25-U01-01", "G\u00fczel Sanatlar ve Edebiyat"),
    (
        "EDB-345A25-U01",
        "EDB-345A25-U01-02",
        "Tarih \u0130\u00e7inde T\u00fcrk Edebiyat\u0131",
    ),
    (
        "EDB-345A25-U01",
        "EDB-345A25-U01-03",
        "S\u00f6zl\u00fc Anlat\u0131m T\u00fcrleri",
    ),
    (
        "EDB-345A25-U01",
        "EDB-345A25-U01-04",
        "Ki\u015fisel Ya\u015fam\u0131 Konu Edinen Metinler",
    ),
    (
        "EDB-345A25-U01",
        "EDB-345A25-U01-05",
        "Gazete \u00c7evresinde Geli\u015fen Metinler",
    ),
    (
        "EDB-345A25-U02",
        "EDB-345A25-U02-01",
        "\u015eiirde Yap\u0131 ve Ahenk Unsurlar\u0131",
    ),
    (
        "EDB-345A25-U02",
        "EDB-345A25-U02-02",
        "Naz\u0131m Bi\u00e7imleri ve T\u00fcrleri",
    ),
    ("EDB-345A25-U02", "EDB-345A25-U02-03", "S\u00f6z Sanatlar\u0131"),
    (
        "EDB-345A25-U02",
        "EDB-345A25-U02-04",
        "\u015eiirde Konu ve Tema - Ger\u00e7eklik",
    ),
    (
        "EDB-345A25-U03",
        "EDB-345A25-U03-01",
        "\u0130slamiyet \u00d6ncesi T\u00fcrk \u015eiiri",
    ),
    (
        "EDB-345A25-U03",
        "EDB-345A25-U03-02",
        "Ge\u00e7i\u015f D\u00f6nemi T\u00fcrk \u015eiiri",
    ),
    ("EDB-345A25-U03", "EDB-345A25-U03-03", "Halk \u015eiiri"),
    ("EDB-345A25-U03", "EDB-345A25-U03-04", "Divan \u015eiiri"),
    ("EDB-345A25-U03", "EDB-345A25-U03-05", "Divan Nesri"),
    ("EDB-345A25-U04", "EDB-345A25-U04-01", "Tanzimat \u015eiiri"),
    (
        "EDB-345A25-U04",
        "EDB-345A25-U04-02",
        "Servetif\u00fcnun ve Fecri\u00e2ti \u015eiiri",
    ),
    ("EDB-345A25-U04", "EDB-345A25-U04-03", "Mill\u00ee Edebiyat \u015eiiri"),
    (
        "EDB-345A25-U04",
        "EDB-345A25-U04-04",
        "Ba\u011f\u0131ms\u0131z \u015eairler ve Fikir Ak\u0131mlar\u0131 - Manzum Hik\u00e2ye ve Mensur \u015eiir",
    ),
    (
        "EDB-345A25-U05",
        "EDB-345A25-U05-01",
        "\u00d6z \u015eiir ve Yedi Me\u015faleciler",
    ),
    (
        "EDB-345A25-U05",
        "EDB-345A25-U05-02",
        "Mill\u00ee Edebiyat Zevk ve Anlay\u0131\u015f\u0131n\u0131 S\u00fcrd\u00fcren \u015eiir",
    ),
    ("EDB-345A25-U05", "EDB-345A25-U05-03", "Serbest Naz\u0131m ve Toplumcu \u015eiir"),
    ("EDB-345A25-U05", "EDB-345A25-U05-04", "Garip\u00e7iler (I. Yeni)"),
    (
        "EDB-345A25-U05",
        "EDB-345A25-U05-05",
        "Garip D\u0131\u015f\u0131nda Yenili\u011fi S\u00fcrd\u00fcren \u015eiir",
    ),
    ("EDB-345A25-U05", "EDB-345A25-U05-06", "II. Yeni \u015eiiri"),
    ("EDB-345A25-U05", "EDB-345A25-U05-07", "1980 Sonras\u0131 T\u00fcrk \u015eiiri"),
    ("EDB-345A25-U05", "EDB-345A25-U05-08", "Cumhuriyet D\u00f6nemi Halk \u015eiiri"),
    (
        "EDB-345A25-U05",
        "EDB-345A25-U05-09",
        "T\u00fcrk D\u00fcnyas\u0131 \u015eairleri",
    ),
    (
        "EDB-345A25-U06",
        "EDB-345A25-U06-01",
        "Dede Korkut Hik\u00e2yeleri - Mesnevi - Halk Hik\u00e2yeleri",
    ),
    ("EDB-345A25-U06", "EDB-345A25-U06-02", "Destan - Efsane - Masal - Fabl"),
    (
        "EDB-345A25-U06",
        "EDB-345A25-U06-03",
        "Hik\u00e2ye T\u00fcr\u00fcn\u00fcn Genel \u00d6zellikleri",
    ),
    (
        "EDB-345A25-U06",
        "EDB-345A25-U06-04",
        "Tanzimat'tan Mill\u00ee Edebiyat'a Hik\u00e2ye",
    ),
    ("EDB-345A25-U06", "EDB-345A25-U06-05", "Cumhuriyet D\u00f6nemi'nde Hik\u00e2ye"),
    (
        "EDB-345A25-U07",
        "EDB-345A25-U07-01",
        "Roman T\u00fcr\u00fcn\u00fcn Genel \u00d6zellikleri",
    ),
    ("EDB-345A25-U07", "EDB-345A25-U07-02", "Tanzimat Roman\u0131"),
    ("EDB-345A25-U07", "EDB-345A25-U07-03", "Servetif\u00fcnun Roman\u0131"),
    ("EDB-345A25-U07", "EDB-345A25-U07-04", "Mill\u00ee Edebiyat Roman\u0131"),
    ("EDB-345A25-U07", "EDB-345A25-U07-05", "Cumhuriyet Roman\u0131"),
    (
        "EDB-345A25-U08",
        "EDB-345A25-U08-01",
        "Tiyatro T\u00fcr\u00fcn\u00fcn Genel \u00d6zellikleri",
    ),
    ("EDB-345A25-U08", "EDB-345A25-U08-02", "Geleneksel T\u00fcrk Tiyatrosu"),
    (
        "EDB-345A25-U08",
        "EDB-345A25-U08-03",
        "Tanzimat'tan Mill\u00ee Edebiyat'a Tiyatro",
    ),
    ("EDB-345A25-U08", "EDB-345A25-U08-04", "Cumhuriyet Tiyatrosu"),
    ("EDB-345A25-U09", "EDB-345A25-U09-01", "Bat\u0131 Edebiyat\u0131"),
    ("EDB-345A25-U09", "EDB-345A25-U09-02", "Edeb\u00ee Ak\u0131mlar"),
    ("EDB-345A25-U09", "EDB-345A25-U09-03", "T\u00fcrk Edebiyat\u0131nda \u0130lkler"),
    (
        "EDB-345A25-U09",
        "EDB-345A25-U09-04",
        "T\u00fcrk Edebiyat\u0131nda Roman \u00d6zetleri",
    ),
    (
        "EDB-345A25-U09",
        "EDB-345A25-U09-05",
        "D\u00fcnya Edebiyat\u0131nda Roman \u00d6zetleri",
    ),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'EDEBIYAT', TRUE, now(), now())
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
    "345 2025 AYT Turk Edebiyati Soru Bankasi'nin kendi icindekiler "
    "sayfalarindan (dosya 3-4) uretildi (0053)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0053] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0053] mv_safe_for_beta yenilendi")


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
        _log.info("[0053] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": EDB_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0053] %s kok konusu yok -- atlandi", EDB_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz EDB-345A25 deseni; diger EDB dugumlerine DOKUNULMAZ. LIKE deseni
    # '-' ile biter ki EDB-345A250 gibi bir onek yanlislikla eslesmesin.
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
    for kod, ad in UNITELER:
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
        "[0053] %s unite + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0053] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0053] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Once yapraklar (konu), sonra uniteler: cocugu olan silinmez.
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
    _log.info("[0053] downgrade tamam; silinmeye aday dugum: %s", len(idler))
