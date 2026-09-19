"""ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi -- konu agaci (GEO altina).

NEDEN
-----
Bu kitabin ithali her soruyu bir konu dugumune baglar. GEO kokunun altinda
zaten bir agac var (GEO-U1..GEO-U5), ama bu kitabin KENDI bolum/konu adlari
onunla birebir ortusmuyor: kitapta "Ozel Ucgenler", "Ucgende Merkezler",
"Genel Dortgenler", "Cemberin Cevresi" gibi dugumler var, mevcut agacta yok;
mevcut agacta "Dik Ucgen", "Egim", "Esitsizlik Grafikleri" gibi dugumler var,
kitapta yok. Sessizce "en yakin" dugume baglamak yanlis veridir. Bu migration
kitabin kendi agacini GEO-ACL24 onekiyle ayri bir alt agac olarak kurar
(FIZ-345 / FIZ-MO / TUR-BS / EDB-BS deseninin aynisi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
  * 6 bolum, 27 konu ve konularin baslangic sayfalari kitabin KENDI
    ICINDEKILER sayfasindan (s3) okundu.
  * Bagimsiz ikinci kanal: 138 testin ILK sayfasinin ust bandi okundu
    (bandin ortasindaki kirmizi konu adi). 128 test icindekiler adiyla
    birebir; kalan 10'u ayni adin uzun hali ("OZEL UCGENLER Pisagor
    Bagintisi", "Analitik Geometri Karma Testler"). Celiski YOK.
  * Bandin kendi alt basligi olan uc test (8, 9, 10) icin uc ALT KONU
    dugumu acildi; adlari bandin kendisinden geliyor.
  * "Analitik Geometri" konusunun 7 testinin TAMAMI "Karma Testler"
    bandini tasidigi icin ayri bir alt dugum acilmadi (ebeveyniyle
    birebir ayni kumeyi kapsayan dugum bilgi tasimaz).

BAGIMSIZ DOGRULAMA
------------------
Testlerin sayfa sinirlari cevap anahtarindan (test sonu izgara kutusu)
turetildi. Icindekilerden gelen konu sayfa araliklariyla karsilastirildi:
138 testin 138'i tek bir konunun icinde kaldi, konu sinirini asan test YOK.

6 bolum + 27 konu + 3 alt konu = 36 dugum.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca
onlari siler ve SORU TASIYAN ya da COCUGU OLAN dugume DOKUNMAZ.

Revizyon adi 17 karakter (sinir 32).
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0034_acilgeo_agac"
down_revision: Union[str, None] = "0033_fiz345_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "acilgeo_konu_gunlugu_0034"
GEO_KOK_KODU = "GEO"
KOD_ONEKI = "GEO-ACL24"

BOLUMLER: tuple[tuple[str, str], ...] = (
    ("GEO-ACL24-B01", "UCGENLER"),
    ("GEO-ACL24-B02", "DORTGENLER"),
    ("GEO-ACL24-B03", "CEMBERLER"),
    ("GEO-ACL24-B04", "ANALITIK GEOMETRI"),
    ("GEO-ACL24-B05", "KATI CISIMLER"),
    ("GEO-ACL24-B06", "CEMBER ANALITIGI"),
)

# (ust kod, kod, ad)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("GEO-ACL24-B01", "GEO-ACL24-B01-01", "Dogruda Acilar"),
    ("GEO-ACL24-B01", "GEO-ACL24-B01-02", "Ucgende Acilar"),
    ("GEO-ACL24-B01", "GEO-ACL24-B01-03", "Ozel Ucgenler"),
    ("GEO-ACL24-B01", "GEO-ACL24-B01-04", "Aciortay"),
    ("GEO-ACL24-B01", "GEO-ACL24-B01-05", "Kenarortay"),
    ("GEO-ACL24-B01", "GEO-ACL24-B01-06", "Eslik ve Benzerlik"),
    ("GEO-ACL24-B01", "GEO-ACL24-B01-07", "Ucgende Alan"),
    ("GEO-ACL24-B01", "GEO-ACL24-B01-08", "Aci Kenar Bagintilari"),
    ("GEO-ACL24-B01", "GEO-ACL24-B01-09", "Ucgende Merkezler"),
    ("GEO-ACL24-B02", "GEO-ACL24-B02-01", "Genel Dortgenler"),
    ("GEO-ACL24-B02", "GEO-ACL24-B02-02", "Paralelkenar"),
    ("GEO-ACL24-B02", "GEO-ACL24-B02-03", "Eskenar Dortgen"),
    ("GEO-ACL24-B02", "GEO-ACL24-B02-04", "Dikdortgen"),
    ("GEO-ACL24-B02", "GEO-ACL24-B02-05", "Kare"),
    ("GEO-ACL24-B02", "GEO-ACL24-B02-06", "Deltoid"),
    ("GEO-ACL24-B02", "GEO-ACL24-B02-07", "Yamuk"),
    ("GEO-ACL24-B02", "GEO-ACL24-B02-08", "Cokgenler"),
    ("GEO-ACL24-B03", "GEO-ACL24-B03-01", "Cemberde Acilar"),
    ("GEO-ACL24-B03", "GEO-ACL24-B03-02", "Cemberde Uzunluk"),
    ("GEO-ACL24-B03", "GEO-ACL24-B03-03", "Cemberin Cevresi"),
    ("GEO-ACL24-B03", "GEO-ACL24-B03-04", "Dairenin Alani"),
    ("GEO-ACL24-B04", "GEO-ACL24-B04-01", "Noktanin Analitigi"),
    ("GEO-ACL24-B04", "GEO-ACL24-B04-02", "Dogrunun Analitigi"),
    ("GEO-ACL24-B04", "GEO-ACL24-B04-03", "Donusum Geometrisi"),
    ("GEO-ACL24-B04", "GEO-ACL24-B04-04", "Analitik Geometri"),
    ("GEO-ACL24-B05", "GEO-ACL24-B05-01", "Kati Cisimler"),
    ("GEO-ACL24-B06", "GEO-ACL24-B06-01", "Cemberin Analitik Incelenmesi"),
)

# Yalniz bandin KENDI alt basligini tasiyan testler icin.
ALT_KONULAR: tuple[tuple[str, str, str], ...] = (
    ("GEO-ACL24-B01-03", "GEO-ACL24-B01-03-01", "Pisagor Bagintisi"),
    (
        "GEO-ACL24-B01-03",
        "GEO-ACL24-B01-03-02",
        "Oklid Teoremi ve Acilarina Gore Ozel Ucgenler",
    ),
    ("GEO-ACL24-B01-03", "GEO-ACL24-B01-03-03", "Ikizkenar ve Eskenar Ucgen"),
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'GEOMETRI', TRUE, now(), now())
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
    "ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi'nin kendi icindekiler "
    "sayfasi (s3) ve 138 testin ilk sayfasindaki baslik bandindan okundu; "
    "iki kanal celismedi ve 138 testin 138'i tek bir konunun sayfa "
    "araliginda kaldi (0034_acilgeo_agac)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0034] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0034] mv_safe_for_beta yenilendi")


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
        _log.info("[0034] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": GEO_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0034] %s kok konusu yok -- atlandi", GEO_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz GEO-ACL24 deseni; mevcut GEO-U* agacina DOKUNULMAZ.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "%"},
        ).fetchall()
    }

    kimlik: dict[str, str] = {}

    def _id_al(kod: str) -> str:
        return b.execute(
            sa.text("SELECT id FROM topic_hierarchy WHERE code = :k"), {"k": kod}
        ).scalar_one()

    eklenen = 0
    for kod, ad in BOLUMLER:
        if kod in mevcut:
            kimlik[kod] = _id_al(kod)
            continue
        kimlik[kod] = _yaz(b, kod, ad, kok_level + 1, kok_id)
        eklenen += 1

    for ust, kod, ad in KONULAR:
        if kod in mevcut:
            kimlik[kod] = _id_al(kod)
            continue
        kimlik[kod] = _yaz(b, kod, ad, kok_level + 2, kimlik[ust])
        eklenen += 1

    for ust, kod, ad in ALT_KONULAR:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 3, kimlik[ust])
        eklenen += 1

    _log.info(
        "[0034] %s bolum + %s konu + %s alt konu tanimi; "
        "bu kosumda eklenen dugum: %s",
        len(BOLUMLER),
        len(KONULAR),
        len(ALT_KONULAR),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0034] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0034] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Once yapraklar, sonra konular, sonra bolumler: cocugu olan silinmez.
        for _ in range(3):
            b.execute(
                sa.text(
                    "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                    "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c "
                    "WHERE c.parent_id = topic_hierarchy.id)"
                ),
                {"idler": idler},
            )
    op.drop_table(GUNLUK)
    _log.info("[0034] downgrade tamam; silinmeye aday dugum: %s", len(idler))
