"""Neofizik TYT Fizik soru bankasi icin FIZ alt konu agacini kurar

Revision ID: 0015_neofizik_tyt_konu_agaci
Revises: 0014_neofizik_beta_toplu_onay
Create Date: 2026-09-10

BAGLAM
------
0013 ayni yayinevinin AYT kitabinin agacini kurmustu (FIZ-NEO-B<n>...).
Bu migration TYT kitabinin agacini kurar: 7 unite, altinda 35 konu blogu.
Kodlar FIZ-NEOT-U<n> ve FIZ-NEOT-U<n>-<KONU> onekini kullanir; 0013'un
"FIZ-NEO-%" desenine TAKILMAZ (8. karakter '-' degil 'T'), yani iki kitabin
agaclari birbirinin sorgusuna sizmaz.

AGACIN KAYNAGI VE CAPRAZ DOGRULAMASI
------------------------------------
Unite/konu listesi kitabin ICINDEKILER sayfasindan okundu. Bagimsiz ikinci
kaynak her sayfanin KENDI BASLIK BANDIDIR (konu adi + TEST N). Iki kaynak
238 icerik sayfasinin 238'inde uyusuyor (veriseti/zkitap/cikti/TYT_YONTEM.md).
Ucuncu bagimsiz kaynak basili cevap anahtarlaridir: 109 test blogunun
109'unda anahtardaki cevap sayisi o bloktaki soru sayisiyla birebir esit.

"Cikmis Sorular" her unitenin sonunda ayri bir blok olarak basili; kitabin
kendi yapisi boyle oldugu icin agacta da ayri yaprak olarak durur (7 adet).
Bu yapraklardaki 91 sorunun tamaminda metinde basili sinav/yil etiketi var
(TYT 2018-2024, MSU 2019-2024) -- konu agaci ile yil etiketi 91/91 uyusuyor.

NEDEN MIGRATION, NEDEN SCRIPT DEGIL
-----------------------------------
Konu agaci referans veridir (schema-benzeri): her ortamda ayni olmali,
surumlenmeli ve geri alinabilmeli. Sorularin kendisi ithal script'iyle gelir
(scripts/kitap/neofizik_tyt_ithal.py). 0011/0012/0013 ile ayni ayrim.

IDEMPOTENT
----------
Var olan kodlar ATLANIR. Olusturulan her dugumun id'si GUNLUK'e yazilir;
downgrade() yalnizca KENDI olusturdugu ve hicbir soru tasimayan dugumleri
siler (kullanilan varsa dokunmaz ve loglar).

topic_hierarchy.code varchar(50) oldugu icin konu kodu 50 karakterde
kesilir -- ithal script'indeki konu_kodu() ile birebir ayni kural.
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0015_neofizik_tyt_konu_agaci"
down_revision: Union[str, None] = "0014_neofizik_beta_toplu_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "neofizik_tyt_konu_gunlugu_0015"
FIZ_KOK_KODU = "FIZ"
KOD_ONEKI = "FIZ-NEOT-"

UNITELER: tuple[tuple[int, str, str], ...] = (
    (1, "FIZ-NEOT-U1", "Fizik Bilimine Giris"),
    (2, "FIZ-NEOT-U2", "Madde ve Ozellikleri"),
    (3, "FIZ-NEOT-U3", "Kuvvet ve Hareket"),
    (4, "FIZ-NEOT-U4", "Enerji ve Hayat"),
    (5, "FIZ-NEOT-U5", "Elektromanyetizma"),
    (6, "FIZ-NEOT-U6", "Dalgalar"),
    (7, "FIZ-NEOT-U7", "Optik"),
)

# (unite_no, kod, ad)  -- yorumdaki sayi kitaptan olculen soru sayisidir
KONULAR: tuple[tuple[int, str, str], ...] = (
    (1, "FIZ-NEOT-U1-FIZIK-BILIMINE-GIRIS", "Fizik Bilimine Giris"),  # 30
    (1, "FIZ-NEOT-U1-CIKMIS-SORULAR", "Cikmis Sorular"),  # 6
    (2, "FIZ-NEOT-U2-DAYANIKLILIK-ADEZYON-KOHEZYON-YUZEY-GE", "Dayaniklilik, Adezyon, Kohezyon, Yuzey Gerilimi"),  # 24
    (2, "FIZ-NEOT-U2-OZKUTLE", "Ozkutle"),  # 23
    (2, "FIZ-NEOT-U2-KATI-CISIMLERIN-YAPTIGI-BASINC", "Kati Cisimlerin Yaptigi Basinc"),  # 39
    (2, "FIZ-NEOT-U2-SIVILARIN-BASINCI", "Sivilarin Basinci"),  # 46
    (2, "FIZ-NEOT-U2-ACIK-HAVA-VE-GAZ-BASINCI-AKISKANLARIN", "Acik Hava ve Gaz Basinci - Akiskanlarin Basinci"),  # 32
    (2, "FIZ-NEOT-U2-KALDIRMA-KUVVETI", "Kaldirma Kuvveti"),  # 32
    (2, "FIZ-NEOT-U2-ISI-SICAKLIK-IC-ENERJI-VE-GENLESME", "Isi, Sicaklik, Ic Enerji ve Genlesme"),  # 48
    (2, "FIZ-NEOT-U2-CIKMIS-SORULAR", "Cikmis Sorular"),  # 30
    (3, "FIZ-NEOT-U3-DOGRUSAL-HAREKET", "Dogrusal Hareket"),  # 44
    (3, "FIZ-NEOT-U3-NEWTON-UN-HAREKET-YASALARI", "Newton'un Hareket Yasalari"),  # 33
    (3, "FIZ-NEOT-U3-CIKMIS-SORULAR", "Cikmis Sorular"),  # 13
    (4, "FIZ-NEOT-U4-IS-ENERJI-VE-GUC", "Is, Enerji ve Guc"),  # 16
    (4, "FIZ-NEOT-U4-MEKANIK-ENERJI", "Mekanik Enerji"),  # 8
    (4, "FIZ-NEOT-U4-ENERJININ-KORUNUMU-VE-DONUSUMLERI", "Enerjinin Korunumu ve Donusumleri"),  # 24
    (4, "FIZ-NEOT-U4-VERIM-VE-ENERJI-KAYNAKLARI", "Verim ve Enerji Kaynaklari"),  # 8
    (4, "FIZ-NEOT-U4-CIKMIS-SORULAR", "Cikmis Sorular"),  # 4
    (5, "FIZ-NEOT-U5-ELEKTROSTATIK", "Elektrostatik"),  # 33
    (5, "FIZ-NEOT-U5-ELEKTRIK-AKIMI", "Elektrik Akimi"),  # 48
    (5, "FIZ-NEOT-U5-MANYETIZMA", "Manyetizma"),  # 25
    (5, "FIZ-NEOT-U5-CIKMIS-SORULAR", "Cikmis Sorular"),  # 12
    (6, "FIZ-NEOT-U6-DALGALARIN-TEMEL-BILESENLERI", "Dalgalarin Temel Bilesenleri"),  # 32
    (6, "FIZ-NEOT-U6-YAY-DALGASI", "Yay Dalgasi"),  # 32
    (6, "FIZ-NEOT-U6-SU-DALGASI", "Su Dalgasi"),  # 33
    (6, "FIZ-NEOT-U6-SES-DEPREM-VE-ELEKTROMANYETIK-DALGA", "Ses, Deprem ve Elektromanyetik Dalga"),  # 28
    (6, "FIZ-NEOT-U6-CIKMIS-SORULAR", "Cikmis Sorular"),  # 9
    (7, "FIZ-NEOT-U7-AYDINLANMA", "Aydinlanma"),  # 22
    (7, "FIZ-NEOT-U7-GOLGE-VE-YARI-GOLGE", "Golge ve Yari Golge"),  # 22
    (7, "FIZ-NEOT-U7-DUZLEM-AYNA", "Duzlem Ayna"),  # 30
    (7, "FIZ-NEOT-U7-KURESEL-AYNA", "Kuresel Ayna"),  # 23
    (7, "FIZ-NEOT-U7-KIRILMA", "Kirilma"),  # 24
    (7, "FIZ-NEOT-U7-MERCEKLER", "Mercekler"),  # 20
    (7, "FIZ-NEOT-U7-PRIZMALAR-VE-RENK", "Prizmalar ve Renk"),  # 21
    (7, "FIZ-NEOT-U7-CIKMIS-SORULAR", "Cikmis Sorular"),  # 17
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
    "Neofizik TYT Fizik Soru Bankasi icindekiler agacindan uretildi; sayfa "
    "baslik bandiyla 238/238 sayfada capraz dogrulandi "
    "(0015_neofizik_tyt_konu_agaci)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; tekrar kosumda ayni id uretilir."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0015] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0015] mv_safe_for_beta yenilendi")


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0015] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": FIZ_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0015] %s kok konusu yok -- atlandi", FIZ_KOK_KODU)
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
            ust = kok_id if level_ofset == 1 else _dugum_id(f"FIZ-NEOT-U{unite_no}")
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
        "[0015] %s unite + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0015] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0015] %s dugum hala soru tasiyor -- SILINMEDI (once sorulari tasi): %s",
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
        _log.info("[0015] geri alindi: %s dugum silindi", len(idler))
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)
    op.drop_table(GUNLUK)
