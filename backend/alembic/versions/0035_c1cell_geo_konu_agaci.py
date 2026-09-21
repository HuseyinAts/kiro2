"""C1CELL 2024 TYT-AYT Geometri Soru Bankasi -- konu agaci (GEO altina).

NEDEN
-----
Bu kitabin ithali her soruyu bir konu dugumune baglar. GEO kokunun altinda
zaten bir agac var (GEO-U1..GEO-U5) ve ACIL 2023-2024'un kendi agaci
(GEO-ACL24) duruyor, ama C1CELL'in KENDI konu adlari ikisiyle de birebir
ortusmuyor: bu kitapta "Aciortay-Kenarortay ve Ucgenin Merkezleri",
"Eskenar Dortgen ve Deltoid", "Nokta ve Dogrunun Analitik Incelenmesi" gibi
dugumler var. Sessizce "en yakin" dugume baglamak yanlis veridir. Bu
migration kitabin kendi agacini GEO-C1C24 onekiyle ayri bir alt agac olarak
kurar (0034_acilgeo_agac deseninin aynisi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
21 ana konu ve baslangic sayfalari kitabin KENDI ICINDEKILER sayfalarindan
(s5-s6) okundu (Faz 0, K0.7). Konular 5 bolume toplandi; bolum adlari
kitabin konu gruplarini tanimlar. Kodlar ve sayfa araliklari
`veriseti/zkitap/cikti/c1cell_2024_geometri_konu_haritasi.json` ile BIREBIR
aynidir -- ithal aracinin konu eslemesi bu kodlari arar.

BAGIMSIZ DOGRULAMA
------------------
163 birimin (test) tamami bas_sayfasindan tek bir konunun sayfa araligina
dustu; konusuz birim YOK.

5 bolum + 21 konu = 26 dugum.

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

revision: str = "0035_c1cellgeo_agac"
down_revision: Union[str, None] = "0034_acilgeo_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "c1cellgeo_konu_gunlugu_0035"
GEO_KOK_KODU = "GEO"
KOD_ONEKI = "GEO-C1C24"

BOLUMLER: tuple[tuple[str, str], ...] = (
    ("GEO-C1C24-B01", "UCGENLER"),
    ("GEO-C1C24-B02", "COKGENLER VE DORTGENLER"),
    ("GEO-C1C24-B03", "CEMBER VE DAIRE"),
    ("GEO-C1C24-B04", "KATI CISIMLER"),
    ("GEO-C1C24-B05", "ANALITIK GEOMETRI"),
)

# (ust kod, kod, ad)
KONULAR: tuple[tuple[str, str, str], ...] = (
    ("GEO-C1C24-B01", "GEO-C1C24-B01-01", "Dogruda Aci"),
    ("GEO-C1C24-B01", "GEO-C1C24-B01-02", "Ucgende Acilar"),
    ("GEO-C1C24-B01", "GEO-C1C24-B01-03", "Dik Ucgen"),
    ("GEO-C1C24-B01", "GEO-C1C24-B01-04", "Ikizkenar Ucgen"),
    ("GEO-C1C24-B01", "GEO-C1C24-B01-05", "Eskenar Ucgen"),
    ("GEO-C1C24-B01", "GEO-C1C24-B01-06", "Aciortay-Kenarortay ve Ucgenin Merkezleri"),
    ("GEO-C1C24-B01", "GEO-C1C24-B01-07", "Ucgende Benzerlik"),
    ("GEO-C1C24-B01", "GEO-C1C24-B01-08", "Ucgenin Alani"),
    ("GEO-C1C24-B01", "GEO-C1C24-B01-09", "Aci-Kenar Bagintilari"),
    ("GEO-C1C24-B02", "GEO-C1C24-B02-10", "Cokgenler"),
    ("GEO-C1C24-B02", "GEO-C1C24-B02-11", "Dortgenler"),
    ("GEO-C1C24-B02", "GEO-C1C24-B02-12", "Yamuk"),
    ("GEO-C1C24-B02", "GEO-C1C24-B02-13", "Paralelkenar"),
    ("GEO-C1C24-B02", "GEO-C1C24-B02-14", "Eskenar Dortgen ve Deltoid"),
    ("GEO-C1C24-B02", "GEO-C1C24-B02-15", "Dikdortgen"),
    ("GEO-C1C24-B02", "GEO-C1C24-B02-16", "Kare"),
    ("GEO-C1C24-B03", "GEO-C1C24-B03-17", "Cember ve Daire"),
    ("GEO-C1C24-B04", "GEO-C1C24-B04-18", "Kati Cisimler"),
    ("GEO-C1C24-B05", "GEO-C1C24-B05-19", "Nokta ve Dogrunun Analitik Incelenmesi"),
    ("GEO-C1C24-B05", "GEO-C1C24-B05-20", "Donusum Geometrisi"),
    ("GEO-C1C24-B05", "GEO-C1C24-B05-21", "Cemberin Analitik Incelenmesi"),
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
    "C1CELL 2024 TYT-AYT Geometri Soru Bankasi'nin kendi icindekiler "
    "sayfalarindan (s5-s6) okundu; 163 birimin tamami tek bir konunun sayfa "
    "araliginda kaldi (0035_c1cellgeo_agac)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0035] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0035] mv_safe_for_beta yenilendi")


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
        _log.info("[0035] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": GEO_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0035] %s kok konusu yok -- atlandi", GEO_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Yalniz GEO-C1C24 deseni; mevcut GEO-U* ve GEO-ACL24 agaclarina DOKUNULMAZ.
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
        "[0035] %s bolum + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0035] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0035] %s dugum hala soru tasiyor -- SILINMEDI "
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
    _log.info("[0035] downgrade tamam; silinmeye aday dugum: %s", len(idler))
