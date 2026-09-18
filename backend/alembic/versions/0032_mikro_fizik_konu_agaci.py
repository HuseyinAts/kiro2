"""Mikro Orijinal TYT Fizik Soru Bankasi 2025 -- konu agaci (FIZ altina).

NEDEN
-----
Bu kitabin ithali (scripts/kitap/mikro_fizik_ithal.py) her soruyu bir konu
dugumune baglar. FIZ kokunun altinda mevcut bir agac var, ama bu kitabin
KENDI bolum/kazanim adlari o agacla birebir ortusmuyor; sessizce en yakin
dugume baglamak yanlis veridir. Bu migration kitabin kendi agacini
FIZ-MO onekiyle ayri bir alt agac olarak kurar (BS Turkce'deki TUR-BS ve
Edebiyat'taki EDB-BS deseninin aynisi).

KAYNAK
------
Dugum adlari UYDURULMADI:
  * 11 bolum ve sayfa araliklari kitabin KENDI ICINDEKILER sayfasindan
    (dosya s4) okundu;
  * konu adlari her testin sayfa ustundeki BASLIK BANDINDAN alindi
    (ornek "KAZANIM TESTI (Duzgun Dogrusal Hareket) - 3"); 186 testin
    186'sinin bandi okundu, hicbiri eksik/okunamaz degildi.
Karma testler (OSYM TARZI / OSYM TARZI ORIJINAL) bir konuyu degil bolumun
tamamini tarar; onlar konu dugumune DEGIL bolum dugumune baglanir.

11 bolum + 49 konu dugumu.

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca
onlari siler ve SORU TASIYAN ya da COCUGU OLAN dugume DOKUNMAZ.

Revizyon adi 21 karakter (sinir 32).
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0032_mikro_fizik_agac"
down_revision: Union[str, None] = "0031_bs_edebiyat_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "mikro_fizik_konu_gunlugu_0032"
FIZ_KOK_KODU = "FIZ"
KOD_ONEKI = "FIZ-MO"

BOLUMLER: tuple[tuple[int, str, str], ...] = (
    (1, "FIZ-MO1", "FIZIK BILIMINE GIRIS"),
    (2, "FIZ-MO2", "MADDE VE OZELLIKLERI"),
    (3, "FIZ-MO3", "HAREKET"),
    (4, "FIZ-MO4", "NEWTON'IN HAREKET YASALARI"),
    (5, "FIZ-MO5", "IS VE ENERJI"),
    (6, "FIZ-MO6", "ISI VE SICAKLIK"),
    (7, "FIZ-MO7", "ELEKTRIK VE MANYETIZMA"),
    (8, "FIZ-MO8", "BASINC"),
    (9, "FIZ-MO9", "KALDIRMA KUVVETI"),
    (10, "FIZ-MO10", "DALGALAR"),
    (11, "FIZ-MO11", "OPTIK"),
)

# (ust bolum kodu, sira, kod, ad)
KONULAR: tuple[tuple[str, int, str, str], ...] = (
    ("FIZ-MO1", 1, "FIZ-MO1-01", "Fizik Bilimine Giris"),
    ("FIZ-MO2", 1, "FIZ-MO2-01", "Kutle-Hacim-Ozkutle"),
    ("FIZ-MO2", 2, "FIZ-MO2-02", "Ozkutle"),
    ("FIZ-MO2", 3, "FIZ-MO2-03", "Dayaniklilik"),
    ("FIZ-MO2", 4, "FIZ-MO2-04", "Adezyon-Kohezyon-Kilcallik"),
    ("FIZ-MO3", 1, "FIZ-MO3-01", "Temel Hareket Kavramlar"),
    ("FIZ-MO3", 2, "FIZ-MO3-02", "Duzgun Dogrusal Hareket"),
    ("FIZ-MO3", 3, "FIZ-MO3-03", "Duzgun Dogrusal Hareket Grafikleri"),
    ("FIZ-MO3", 4, "FIZ-MO3-04", "Ortalama Hiz ve Surat"),
    ("FIZ-MO3", 5, "FIZ-MO3-05", "Ivme Kavrami, Sabit Ivmeli Hareket"),
    ("FIZ-MO3", 6, "FIZ-MO3-06", "Karma"),
    ("FIZ-MO4", 1, "FIZ-MO4-01", "Kuvvet ve Ozellikleri"),
    ("FIZ-MO4", 2, "FIZ-MO4-02", "Newton'in Hareket Yasalari"),
    ("FIZ-MO4", 3, "FIZ-MO4-03", "Surtunme Kuvveti"),
    ("FIZ-MO5", 1, "FIZ-MO5-01", "Is ve Enerji"),
    ("FIZ-MO5", 2, "FIZ-MO5-02", "Enerji Kaynaklari"),
    ("FIZ-MO5", 3, "FIZ-MO5-03", "Karma"),
    ("FIZ-MO6", 1, "FIZ-MO6-01", "Temel Kavramlar"),
    ("FIZ-MO6", 2, "FIZ-MO6-02", "Hal Degisimi"),
    ("FIZ-MO6", 3, "FIZ-MO6-03", "Isinin Yayilma Yollari"),
    ("FIZ-MO6", 4, "FIZ-MO6-04", "Genlesme"),
    ("FIZ-MO6", 5, "FIZ-MO6-05", "Karma"),
    ("FIZ-MO7", 1, "FIZ-MO7-01", "Elektrostatik"),
    ("FIZ-MO7", 2, "FIZ-MO7-02", "Elektrik Akimi, Potansiyel Farki ve Direnc"),
    ("FIZ-MO7", 3, "FIZ-MO7-03", "Esdeger Direnc"),
    ("FIZ-MO7", 4, "FIZ-MO7-04", "Elektrik Devreleri"),
    ("FIZ-MO7", 5, "FIZ-MO7-05", "Elektrik Devreleri ve Esdeger Direnc"),
    ("FIZ-MO7", 6, "FIZ-MO7-06", "Ureteclerin Emk'si, Seri ve Paralel Baglanmasi"),
    ("FIZ-MO7", 7, "FIZ-MO7-07", "Lambali Devreleri"),
    ("FIZ-MO7", 8, "FIZ-MO7-08", "Miknatis ve Manyetik Alan"),
    ("FIZ-MO7", 9, "FIZ-MO7-09", "Akim - Manyetik Alan Iliskisi"),
    ("FIZ-MO8", 1, "FIZ-MO8-01", "Kati Basinci"),
    ("FIZ-MO8", 2, "FIZ-MO8-02", "Sivi Basinci"),
    ("FIZ-MO8", 3, "FIZ-MO8-03", "Gaz Basinci"),
    ("FIZ-MO8", 4, "FIZ-MO8-04", "Akiskan Basinci"),
    ("FIZ-MO9", 1, "FIZ-MO9-01", "Archimedes Ilkesi"),
    ("FIZ-MO10", 1, "FIZ-MO10-01", "Dalgalarin Genel Ozellikleri"),
    ("FIZ-MO10", 2, "FIZ-MO10-02", "Yay Dalgalari"),
    ("FIZ-MO10", 3, "FIZ-MO10-03", "Yay Dalgasi"),
    ("FIZ-MO10", 4, "FIZ-MO10-04", "Su Dalgasi"),
    ("FIZ-MO10", 5, "FIZ-MO10-05", "Ses Dalgasi ve Deprem Dalgasi"),
    ("FIZ-MO10", 6, "FIZ-MO10-06", "Karma"),
    ("FIZ-MO11", 1, "FIZ-MO11-01", "Aydinlanma"),
    ("FIZ-MO11", 2, "FIZ-MO11-02", "Golge"),
    ("FIZ-MO11", 3, "FIZ-MO11-03", "Yansima ve Duzlem Ayna"),
    ("FIZ-MO11", 4, "FIZ-MO11-04", "Kuresel Aynalar"),
    ("FIZ-MO11", 5, "FIZ-MO11-05", "Kirilma"),
    ("FIZ-MO11", 6, "FIZ-MO11-06", "Kirilma ve Renk"),
    ("FIZ-MO11", 7, "FIZ-MO11-07", "Mercekler"),
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
    "Mikro Orijinal TYT Fizik Soru Bankasi 2025'in kendi icindekiler sayfasi "
    "ve test basliklarindan okundu; 186 testin 186'sinda baslik bandi "
    "okunabildi ve icindekilerden turetilen sayfa araliklariyla ortustu "
    "(0032_mikro_fizik_agac)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; onceki agac migration'lariyla ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0032] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0032] mv_safe_for_beta yenilendi")


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
        _log.info("[0032] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": FIZ_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0032] %s kok konusu yok -- atlandi", FIZ_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # FIZ-MO deseni; mevcut FIZ agacinin diger dugumlerini KAPSAMAZ.
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
        "[0032] %s bolum + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0032] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0032] %s dugum hala soru tasiyor -- SILINMEDI "
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
    _log.info("[0032] downgrade tamam; silinmeye aday dugum: %s", len(idler))
