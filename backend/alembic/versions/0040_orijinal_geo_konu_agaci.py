"""Orijinal 2024 TYT-AYT Geometri: kitabin kendi konu agaci (GEO-ORJ24).

NEDEN
-----
Bu kitabin ithali her soruyu bir konu dugumune baglar. GEO kokunun altinda
zaten baska agaclar var (GEO-U1..GEO-U5, GEO-ACL24, GEO-C1C24) ama Orijinal
2024'un KENDI konu adlari hicbiriyle birebir ortusmuyor: bu kitapta her
bolumun sonunda ayri bir "OSYM'de Cikmis Sorular" dugumu var ve konu adlari
kendi dizilisini izliyor. Sessizce "en yakin" dugume baglamak yanlis
veridir; bu migration kitabin agacini GEO-ORJ24 onekiyle ayri bir alt agac
olarak kurar (0034 / 0035 deseninin aynisi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
Kodlar ve adlar
`veriseti/zkitap/cikti/orijinal_2024_geometri_konu_haritasi.json` ile
BIREBIR aynidir; o dosya kitabin icindekiler sayfalarinin IKI BAGIMSIZ
okumasindan ve 425 sayfalik TEST rozeti taramasindan uretildi (test sayisi
otoritesi rozet, icindekiler degil -- iki konuda kitabin kendi dizgi hatasi
olculdu). Bu migration dosyasi o JSON'dan URETILDI.

BAGIMSIZ DOGRULAMA
------------------
231 birimin (test + OSYM bolumu) tamami tek bir konunun sayfa araliginda
kaldi; konusuz birim YOK. Ithal araci ayrica her birimin konu kodunu sayfa
araligiyla yeniden dogrular.

5 bolum + 35 konu (30 adli konu + 5 OSYM dugumu) = 40 dugum.

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

revision: str = "0040_orijinalgeo_agac"
down_revision: Union[str, None] = "0039_fizik_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "orijinalgeo_konu_gunlugu_0040"
GEO_KOK_KODU = "GEO"
KOD_ONEKI = "GEO-ORJ24"

BOLUMLER: tuple[tuple[str, str], ...] = (
    ("GEO-ORJ24-B01", "UCGENLER"),
    ("GEO-ORJ24-B02", "COKGENLER VE DORTGENLER"),
    ("GEO-ORJ24-B03", "CEMBER VE DAIRE"),
    ("GEO-ORJ24-B04", "ANALITIK GEOMETRI"),
    ("GEO-ORJ24-B05", "KATI CISIMLER"),
)

# (ust kod, kod, ad)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-01", "Temel Kavramlar ve Dogruda Acilar"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-02", "Ucgende Acilar"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-03", "Dik ve Ozel Ucgenler"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-04", "Ikizkenar Ucgen"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-05", "Eskenar Ucgen"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-06", "Ucgende Aciortay Bagintilari"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-07", "Ucgende Kenarortay Bagintilari"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-08", "Ucgende Eslik ve Benzerlik"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-09", "Ucgende Merkezler"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-10", "Ucgende Alan"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-11", "Ucgende Aci-Kenar Bagintilari"),
    ("GEO-ORJ24-B01", "GEO-ORJ24-B01-12", "OSYM'de Cikmis Sorular (Ucgenler)"),
    ("GEO-ORJ24-B02", "GEO-ORJ24-B02-01", "Cokgen ve Duzgun Cokgenler"),
    ("GEO-ORJ24-B02", "GEO-ORJ24-B02-02", "Dortgenler"),
    ("GEO-ORJ24-B02", "GEO-ORJ24-B02-03", "Deltoid"),
    ("GEO-ORJ24-B02", "GEO-ORJ24-B02-04", "Paralelkenar"),
    ("GEO-ORJ24-B02", "GEO-ORJ24-B02-05", "Eskenar Dortgen"),
    ("GEO-ORJ24-B02", "GEO-ORJ24-B02-06", "Dikdortgen"),
    ("GEO-ORJ24-B02", "GEO-ORJ24-B02-07", "Kare"),
    ("GEO-ORJ24-B02", "GEO-ORJ24-B02-08", "Yamuk"),
    ("GEO-ORJ24-B02", "GEO-ORJ24-B02-09", "OSYM'de Cikmis Sorular (Cokgenler ve Dortgenler)"),
    ("GEO-ORJ24-B03", "GEO-ORJ24-B03-01", "Cemberde Aci"),
    ("GEO-ORJ24-B03", "GEO-ORJ24-B03-02", "Cemberde Uzunluk"),
    ("GEO-ORJ24-B03", "GEO-ORJ24-B03-03", "Dairede Cevre ve Alan"),
    ("GEO-ORJ24-B03", "GEO-ORJ24-B03-04", "OSYM'de Cikmis Sorular (Cember ve Daire)"),
    ("GEO-ORJ24-B04", "GEO-ORJ24-B04-01", "Noktanin Analitik Incelenmesi"),
    ("GEO-ORJ24-B04", "GEO-ORJ24-B04-02", "Dogrunun Analitik Incelenmesi"),
    ("GEO-ORJ24-B04", "GEO-ORJ24-B04-03", "Analitik Duzlemde Donusumler"),
    ("GEO-ORJ24-B04", "GEO-ORJ24-B04-04", "Cemberin Analitik Incelenmesi"),
    ("GEO-ORJ24-B04", "GEO-ORJ24-B04-05", "OSYM'de Cikmis Sorular (Analitik Geometri)"),
    ("GEO-ORJ24-B05", "GEO-ORJ24-B05-01", "Prizmalar"),
    ("GEO-ORJ24-B05", "GEO-ORJ24-B05-02", "Piramit"),
    ("GEO-ORJ24-B05", "GEO-ORJ24-B05-03", "Kure"),
    ("GEO-ORJ24-B05", "GEO-ORJ24-B05-04", "Donel Cisimler"),
    ("GEO-ORJ24-B05", "GEO-ORJ24-B05-05", "OSYM'de Cikmis Sorular (Kati Cisimler)"),
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
    "Orijinal 2024 TYT-AYT Geometri Soru Bankasi'nin kendi konu haritasindan "
    "uretildi; test sayisi otoritesi sayfadaki TEST rozeti (0040)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0040] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0040] mv_safe_for_beta yenilendi")


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
        _log.info("[0040] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": GEO_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0040] %s kok konusu yok -- atlandi", GEO_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz GEO-ORJ24 deseni; mevcut GEO-U*, GEO-ACL24, GEO-C1C24
    # agaclarina DOKUNULMAZ.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "%"},
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
        "[0040] %s bolum + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0040] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0040] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # Once yapraklar, sonra bolumler: cocugu olan silinmez.
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
    _log.info("[0040] downgrade tamam; silinmeye aday dugum: %s", len(idler))
