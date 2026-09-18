"""345 2025 AYT Fizik Soru Bankasi -- konu agaci (FIZ altina).

NEDEN
-----
Bu kitabin ithali (scripts/kitap/fiz345_ithal.py) her soruyu bir konu
dugumune baglar. FIZ kokunun altinda mevcut bir agac ve B1'de eklenen
FIZ-MO alt agaci var, ama bu kitabin KENDI bolum/konu adlari ikisiyle de
birebir ortusmuyor; sessizce en yakin dugume baglamak yanlis veridir. Bu
migration kitabin kendi agacini FIZ-345 onekiyle ayri bir alt agac olarak
kurar (TUR-BS / EDB-BS / FIZ-MO deseninin aynisi).

KAYNAK
------
Dugum adlari UYDURULMADI:
  * 20 bolum ve sayfa araliklari kitabin KENDI ICINDEKILER sayfasindan
    (dosya f3 ve f4) okundu;
  * konu adlari her testin sayfa ustundeki BASLIK BANDINDAN alindi
    (ornek "ESNEKLIK POTANSIYEL ENERJISI"); 190 testin 190'inin bandi
    okundu.
Bandin adi bolum adiyla ayniysa ya da birden cok bolumu kapsiyorsa
(ornek "BIR ve IKI BOYUTTA HAREKET") soru konu dugumune DEGIL bolum
dugumune baglanir.

BAGIMSIZ DOGRULAMA
------------------
Testlerin sayfa sinirlari cevap satirindaki numaralandirmadan turetildi
(190 test). Icindekilerden gelen bolum araliklariyla karsilastirildi:
190 testin 190'i tek bir bolumun icinde kaldi, bolum sinirini asan test
YOK.

20 bolum + 40 konu dugumu.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca
onlari siler ve SORU TASIYAN ya da COCUGU OLAN dugume DOKUNMAZ.

Revizyon adi 15 karakter (sinir 32).
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0033_fiz345_agac"
down_revision: Union[str, None] = "0032_mikro_fizik_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "fiz345_konu_gunlugu_0033"
FIZ_KOK_KODU = "FIZ"
KOD_ONEKI = "FIZ-345"

BOLUMLER: tuple[tuple[int, str, str], ...] = (
    (1, "FIZ-345-B01", "VEKTORLER"),
    (2, "FIZ-345-B02", "BAGIL HAREKET"),
    (3, "FIZ-345-B03", "NEWTON'IN HAREKET YASALARI"),
    (4, "FIZ-345-B04", "BIR BOYUTTA SABIT IVMELI HAREKET"),
    (5, "FIZ-345-B05", "IKI BOYUTTA HAREKET"),
    (6, "FIZ-345-B06", "ENERJI"),
    (7, "FIZ-345-B07", "ITME VE CIZGISEL MOMENTUM"),
    (8, "FIZ-345-B08", "TORK"),
    (9, "FIZ-345-B09", "DENGE"),
    (10, "FIZ-345-B10", "KUTLE VE AGIRLIK MERKEZI"),
    (11, "FIZ-345-B11", "BASIT MAKINELER"),
    (12, "FIZ-345-B12", "ELEKTRIK"),
    (13, "FIZ-345-B13", "MANYETIZMA"),
    (14, "FIZ-345-B14", "ALTERNATIF AKIM VE TRANSFORMATORLER"),
    (15, "FIZ-345-B15", "CEMBERSEL HAREKET"),
    (16, "FIZ-345-B16", "BASIT HARMONIK HAREKET"),
    (17, "FIZ-345-B17", "DALGA MEKANIGI"),
    (18, "FIZ-345-B18", "ATOM FIZIGINE GIRIS VE RADYOAKTIVITE"),
    (19, "FIZ-345-B19", "MODERN FIZIK"),
    (20, "FIZ-345-B20", "MODERN FIZIGIN TEKNOLOJIDEKI UYGULAMALARI"),
)

# (ust bolum kodu, sira, kod, ad)
KONULAR: tuple[tuple[str, int, str, str], ...] = (
    ("FIZ-345-B04", 1, "FIZ-345-B04-01", "DUZGUN HIZLANAN DOGRUSAL HAREKET"),
    ("FIZ-345-B04", 2, "FIZ-345-B04-02", "DUZGUN YAVASLAYAN DOGRUSAL HAREKET"),
    ("FIZ-345-B06", 1, "FIZ-345-B06-01", "IS ve ENERJI ILISKISI"),
    ("FIZ-345-B06", 2, "FIZ-345-B06-02", "ESNEKLIK POTANSIYEL ENERJISI"),
    ("FIZ-345-B06", 3, "FIZ-345-B06-03", "SURTUNMESIZ ORTAMDA ENERJI KORUNUMU"),
    ("FIZ-345-B06", 4, "FIZ-345-B06-04", "SURTUNMELI ORTAMDA ENERJI KORUNUMU"),
    ("FIZ-345-B07", 1, "FIZ-345-B07-01", "CARPISMALAR"),
    ("FIZ-345-B11", 1, "FIZ-345-B11-01", "KALDIRAC ve MAKARALAR"),
    ("FIZ-345-B11", 2, "FIZ-345-B11-02", "PALANGA - EGIK DUZLEM ve CIKRIK"),
    ("FIZ-345-B11", 3, "FIZ-345-B11-03", "KASNAKLAR - DISLI CARKLAR ve VIDA"),
    ("FIZ-345-B12", 1, "FIZ-345-B12-01", "ELEKTRIKSEL KUVVET ve ELEKTRIK ALANI"),
    (
        "FIZ-345-B12",
        2,
        "FIZ-345-B12-02",
        "ELEKTRIK POTANSIYEL ENERJI ve ELEKTRIK POTANSIYELI",
    ),
    (
        "FIZ-345-B12",
        3,
        "FIZ-345-B12-03",
        "IKI NOKTA ARASI POTANSIYEL FARK ve ELEKTRIKSEL IS",
    ),
    (
        "FIZ-345-B12",
        4,
        "FIZ-345-B12-04",
        "YUKLU PARCACIKLARIN DUZGUN ELEKTRIK ALANDA HAREKETI",
    ),
    ("FIZ-345-B12", 5, "FIZ-345-B12-05", "SIGACLAR"),
    ("FIZ-345-B14", 1, "FIZ-345-B14-01", "ALTERNATIF AKIM"),
    ("FIZ-345-B14", 2, "FIZ-345-B14-02", "TRANSFORMATORLER"),
    ("FIZ-345-B15", 1, "FIZ-345-B15-01", "DUZGUN CEMBERSEL HAREKET"),
    ("FIZ-345-B15", 2, "FIZ-345-B15-02", "MERKEZCIL KUVVET"),
    ("FIZ-345-B15", 3, "FIZ-345-B15-03", "DUSEY DUZLEMDE DUZGUN CEMBERSEL HAREKET"),
    ("FIZ-345-B15", 4, "FIZ-345-B15-04", "DONEREK OTELEME HAREKETI"),
    ("FIZ-345-B15", 5, "FIZ-345-B15-05", "ACISAL MOMENTUM"),
    ("FIZ-345-B15", 6, "FIZ-345-B15-06", "KUTLE CEKIM KUVVETI ve KEPLER YASASI"),
    ("FIZ-345-B16", 1, "FIZ-345-B16-01", "YAY SARKACI"),
    ("FIZ-345-B16", 2, "FIZ-345-B16-02", "BASIT SARKAC"),
    ("FIZ-345-B17", 1, "FIZ-345-B17-01", "SU DALGALARINDA KIRINIM ve GIRISIM"),
    ("FIZ-345-B17", 2, "FIZ-345-B17-02", "CIFT YARIKTA GIRISIM ve TEK YARIKTA KIRINIM"),
    ("FIZ-345-B17", 3, "FIZ-345-B17-03", "ELEKTROMANYETIK DALGALAR ve DOPPLER OLAYI"),
    ("FIZ-345-B18", 1, "FIZ-345-B18-01", "ATOM MODELLERI"),
    ("FIZ-345-B18", 2, "FIZ-345-B18-02", "ATOMUN UYARILMASI ve ENERJI SEVIYELERI"),
    ("FIZ-345-B18", 3, "FIZ-345-B18-03", "BUYUK PATLAMA ve ATOM ALTI PARCACIKLAR"),
    ("FIZ-345-B18", 4, "FIZ-345-B18-04", "RADYOAKTIVITE"),
    ("FIZ-345-B19", 1, "FIZ-345-B19-01", "OZEL GORELILIK TEORISI"),
    ("FIZ-345-B19", 2, "FIZ-345-B19-02", "KUANTUM FIZIGINE GIRIS"),
    ("FIZ-345-B19", 3, "FIZ-345-B19-03", "FOTOELEKTRIK OLAY"),
    ("FIZ-345-B19", 4, "FIZ-345-B19-04", "URETECE BAGLI DEVRELER"),
    ("FIZ-345-B19", 5, "FIZ-345-B19-05", "COMPTON SACILMASI"),
    ("FIZ-345-B20", 1, "FIZ-345-B20-01", "GORUNTULEME CIHAZLARI"),
    ("FIZ-345-B20", 2, "FIZ-345-B20-02", "YARI ILETKEN TEKNOLOJISI"),
    ("FIZ-345-B20", 3, "FIZ-345-B20-03", "SUPER ILETKENLER, NANOTEKNOLOJI ve LASER"),
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
    "345 2025 AYT Fizik Soru Bankasi'nin kendi icindekiler sayfasi (f3-f4) "
    "ve her testin sayfa ustundeki baslik bandindan okundu; 190 testin "
    "190'inin bandi okunabildi ve icindekilerden turetilen sayfa "
    "araliklariyla ortustu -- hicbir test iki bolume yayilmadi "
    "(0033_fiz345_agac)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0033] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0033] mv_safe_for_beta yenilendi")


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
        _log.info("[0033] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": FIZ_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0033] %s kok konusu yok -- atlandi", FIZ_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # FIZ-345 deseni; mevcut FIZ agacinin diger dugumlerini KAPSAMAZ.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "%"},
        ).fetchall()
    }

    bolum_id: dict[str, str] = {}
    eklenen = 0
    for _sira, kod, ad in BOLUMLER:
        if kod in mevcut:
            bolum_id[kod] = b.execute(
                sa.text("SELECT id FROM topic_hierarchy WHERE code = :k"), {"k": kod}
            ).scalar_one()
            continue
        bolum_id[kod] = _yaz(b, kod, ad, kok_level + 1, kok_id)
        eklenen += 1

    for ust, _sira, kod, ad in KONULAR:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 2, bolum_id[ust])
        eklenen += 1

    _log.info(
        "[0033] %s bolum + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0033] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0033] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Once yapraklar, sonra bolumler: cocugu olan dugum silinmez.
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
    _log.info("[0033] downgrade tamam; silinmeye aday dugum: %s", len(idler))
