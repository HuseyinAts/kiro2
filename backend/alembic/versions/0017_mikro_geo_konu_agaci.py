"""Mikro Orijinal AYT Geometri soru bankasi icin GEO alt konu agacini kurar

Revision ID: 0017_mikro_geo_konu_agaci
Revises: 0016_neofizik_tyt_beta_onay
Create Date: 2026-09-11

BAGLAM
------
0013/0015 Neofizik'in AYT ve TYT fizik kitaplarinin agaclarini kurmustu
(FIZ-NEO-%, FIZ-NEOT-%). Bu migration bir BASKA yayinevinin geometri
kitabinin agacini kurar: 5 unite, altinda 31 konu. Kodlar GEO-MIKRO-U<n>
ve GEO-MIKRO-U<n>-<KONU> onekini kullanir; GEO kokunun altindaki mevcut
"MAT.GEO" dugumune dokunmaz.

AGACIN KAYNAGI VE CAPRAZ DOGRULAMASI
------------------------------------
Agac kitabin ICINDEKILER sayfasindan DEGIL, her sayfanin KENDI BASLIK
BANDINDAN uretildi (banner: kirmizi blokta konu adi, turkuaz/turuncu blokta
test adi). Iki bagimsiz okuma 237 test sayfasinin 237'sinde uyusuyor.

Ucuncu bagimsiz kaynak sayfa altindaki BASILI CEVAP SERIDIDIR: seritteki
numaralar testler boyunca kesintisiz aktigi icin sayfalar testlere
gruplanabiliyor. Seritten cikan 149 test grubu ile banner'dan cikan 149
test grubunun SAYFA KUMELERI BIREBIR AYNI.

Icindekiler sayfasi da 149 test sayiyor ama iki yerde kitabin kendisiyle
celisiyor (yayinevi dizgi hatalari, ikisi birbirini goturuyor):
  - "CEMBERDE UZUNLUK ... Kazanim Testi 1-2-3-4-5" diyor; kitapta 4 tane
    basili (banner adlari: Yaricap Kullanimi ve Cizimi / Kiris Ozellikleri 1
    / Teget Ozellikleri / Teget Cemberler -- "Kiris Ozellikleri 2" yok).
  - "DOGRUNUN ANALITIGI ... 340-359" basliginin altinda ayri bir test
    gizli: s358-359'daki banner "ESITSIZLIK GRAFIKLERI" diyor.
Bu yuzden agacta 31 konu var, icindekilerin saydigi 28 degil; fark
ESITSIZLIK GRAFIKLERI ve DONUSUMLER'in uc ayri banner konusuna
(OTELEME/DONME/SIMETRI DONUSUMU) acilmasidir.

"Cikmis Sorular" bu kitapta AYRI BIR BLOK DEGIL: tekil sorularin uzerinde
turuncu "Cikmis Soru (YIL / SINAV)" rozeti var (86 soru). Bu yuzden agacta
Neofizik'teki gibi ayri yaprak YOKTUR; etiket soru duzeyinde tasinir.

NEDEN MIGRATION, NEDEN SCRIPT DEGIL
-----------------------------------
Konu agaci referans veridir (schema-benzeri): her ortamda ayni olmali,
surumlenmeli ve geri alinabilmeli. Sorularin kendisi ithal script'iyle gelir
(scripts/kitap/mikro_geo_ithal.py). 0011/0012/0013/0015 ile ayni ayrim.

IDEMPOTENT
----------
Var olan kodlar ATLANIR. Olusturulan her dugumun id'si GUNLUK'e yazilir;
downgrade() yalnizca KENDI olusturdugu ve hicbir soru tasimayan dugumleri
siler (kullanilan varsa dokunmaz ve loglar).

ALEMBIC REVISION ADI 32 KARAKTERI ASAMAZ
----------------------------------------
alembic_version.version_num varchar(32). 0016'da bu sinir bir kez asilmisti
(33 karakter) ve migration tum UPDATE'leri kostuktan sonra son adimda
patlamisti. Bu dosyanin revision adi 24 karakter.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0017_mikro_geo_konu_agaci"
down_revision: Union[str, None] = "0016_neofizik_tyt_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "mikro_geo_konu_gunlugu_0017"
GEO_KOK_KODU = "GEO"
KOD_ONEKI = "GEO-MIKRO-"

UNITELER: tuple[tuple[int, str, str], ...] = (
    (1, "GEO-MIKRO-U1", "Ucgenler"),
    (2, "GEO-MIKRO-U2", "Dortgenler"),
    (3, "GEO-MIKRO-U3", "Cember ve Daire"),
    (4, "GEO-MIKRO-U4", "Analitik Geometri"),
    (5, "GEO-MIKRO-U5", "Kati Cisimler"),
)

# (unite_no, kod, ad)  -- yorumdaki sayi kitaptan OLCULEN soru sayisidir
KONULAR: tuple[tuple[int, str, str], ...] = (
    (1, "GEO-MIKRO-U1-DOGRUDA-ACI", "Dogruda Aci"),  # 52
    (1, "GEO-MIKRO-U1-UCGENDE-ACI", "Ucgende Aci"),  # 74
    (1, "GEO-MIKRO-U1-DIK-UCGEN", "Dik Ucgen"),  # 57
    (1, "GEO-MIKRO-U1-IKIZKENAR-UCGEN", "Ikizkenar Ucgen"),  # 40
    (1, "GEO-MIKRO-U1-ESKENAR-UCGEN", "Eskenar Ucgen"),  # 37
    (1, "GEO-MIKRO-U1-ACIORTAY", "Aciortay"),  # 42
    (1, "GEO-MIKRO-U1-KENARORTAY", "Kenarortay"),  # 42
    (1, "GEO-MIKRO-U1-BENZERLIK", "Benzerlik"),  # 79
    (1, "GEO-MIKRO-U1-UCGENDE-ESLIK", "Ucgende Eslik"),  # 29
    (1, "GEO-MIKRO-U1-UCGENDE-ALAN", "Ucgende Alan"),  # 70
    (1, "GEO-MIKRO-U1-ACI-KENAR-BAGINTILARI", "Aci-Kenar Bagintilari"),  # 32
    (2, "GEO-MIKRO-U2-DORTGENLER", "Dortgenler"),  # 21
    (2, "GEO-MIKRO-U2-YAMUK", "Yamuk"),  # 53
    (2, "GEO-MIKRO-U2-PARALELKENAR", "Paralelkenar"),  # 46
    (2, "GEO-MIKRO-U2-ESKENAR-DORTGEN", "Eskenar Dortgen"),  # 24
    (2, "GEO-MIKRO-U2-DELTOID", "Deltoid"),  # 19
    (2, "GEO-MIKRO-U2-DIKDORTGEN", "Dikdortgen"),  # 41
    (2, "GEO-MIKRO-U2-KARE", "Kare"),  # 40
    (2, "GEO-MIKRO-U2-COKGENLER", "Cokgenler"),  # 28
    (3, "GEO-MIKRO-U3-CEMBERDE-UZUNLUK", "Cemberde Uzunluk"),  # 69
    (3, "GEO-MIKRO-U3-CEMBERDE-ACI", "Cemberde Aci"),  # 48
    (3, "GEO-MIKRO-U3-DAIREDE-ALAN", "Dairede Alan"),  # 54
    (4, "GEO-MIKRO-U4-NOKTANIN-ANALITIGI", "Noktanin Analitigi"),  # 38
    (4, "GEO-MIKRO-U4-EGIM", "Egim"),  # 15
    (4, "GEO-MIKRO-U4-DOGRUNUN-ANALITIGI", "Dogrunun Analitigi"),  # 54
    (4, "GEO-MIKRO-U4-ESITSIZLIK-GRAFIKLERI", "Esitsizlik Grafikleri"),  # 9
    (4, "GEO-MIKRO-U4-OTELEME-DONUSUMU", "Oteleme Donusumu"),  # 10
    (4, "GEO-MIKRO-U4-DONME-DONUSUMU", "Donme Donusumu"),  # 12
    (4, "GEO-MIKRO-U4-SIMETRI-DONUSUMU", "Simetri Donusumu"),  # 10
    (4, "GEO-MIKRO-U4-CEMBERIN-ANALITIGI", "Cemberin Analitigi"),  # 24
    (5, "GEO-MIKRO-U5-KATI-CISIMLER", "Kati Cisimler"),  # 44
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
    "Mikro Orijinal 2025 AYT Geometri Soru Bankasi sayfa baslik bandindan "
    "uretildi; iki bagimsiz okuma 237/237 sayfada, basili cevap seridinden "
    "cikan test gruplariyla 149/149 testte uyusuyor "
    "(0017_mikro_geo_konu_agaci)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; tekrar kosumda ayni id uretilir."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0017] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0017] mv_safe_for_beta yenilendi")


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0017] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": GEO_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0017] %s kok konusu yok -- atlandi", GEO_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    mevcut = {
        r[0]
        for r in b.execute(
            sa.text("SELECT code FROM topic_hierarchy WHERE code LIKE :onek"),
            {"onek": KOD_ONEKI + "%"},
        ).fetchall()
    }

    eklenen = 0
    for level_ofset, kayitlar in ((1, UNITELER), (2, KONULAR)):
        for unite_no, kod, ad in kayitlar:
            if kod in mevcut:
                continue
            ust = kok_id if level_ofset == 1 else _dugum_id(f"GEO-MIKRO-U{unite_no}")
            yeni_id = _dugum_id(kod)
            b.execute(
                _EKLE,
                {
                    "id": yeni_id,
                    "level": kok_level + level_ofset,
                    "parent_id": ust,
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
            eklenen += 1

    _log.info(
        "[0017] %s unite + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0017] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0017] %s dugum hala soru tasiyor -- SILINMEDI (once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        # once yapraklar, sonra uniteler: alt dugumu olan silinmez
        for _ in range(2):
            b.execute(
                sa.text(
                    "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                    "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c "
                    "WHERE c.parent_id = topic_hierarchy.id)"
                ),
                {"idler": idler},
            )
        _log.info("[0017] geri alindi: %s dugum silindi", len(idler))
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
