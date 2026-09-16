"""Aktif Ogrenme TYT Dilbilgisi Soru Bankasi 2025 konu agaci (16 unite + OSYM).

Revision ID: 0025_dilbilgisi_konu_agaci
Revises: 0024_biyo345tyt_gorsel
Create Date: 2026-09-16

NEDEN YENI BIR UNITE SETI
-------------------------
Canli DB olcumu (16 Eyl 2026): TURKCE ders alaninda 7 dugum var ve HEPSI
level 2 -- TUR.ANL (Anlam Bilgisi, 22 soru), TUR.DIL (Dil Bilgisi, 60),
TUR.PAR (Paragraf, 141), TUR.YAZ (Yazim Kurallari, 11), TYT-TR-01 (Anlama,
42), TYT-TR-02 (Dil Bilgisi, 0), TYT-TR-03 (Paragraf, 0). Hepsi TUR kokune
(f5b7f58c-df65-4de2-964e-44bca4ae8ca6, level 1) bagli.

Bu 7 dugum KABA: bir dilbilgisi soru bankasinin 16 ayri unitesi ("Ses
Bilgisi", "Fiilde Cati", "Cumlenin Ogeleri", "Anlatim Bozukluklari" ...)
icin tek bir "Dil Bilgisi" dugumu ayrim uretmiyor; ustelik ayni ad iki kez
var (TUR.DIL ve TYT-TR-02). Var olan bir dugume baglamak konu duzeyinde
adaptif secimi imkansiz kilardi. 0013/0015/0017/0021/0022 ile ayni gerekce:
kitabin kendi yapisindan yeni bir unite seti kurulur.

Kod oneki TUR-D ("Dilbilgisi"). Olcum: `code LIKE 'TUR-D%'` deseni su an
SIFIR satir donduruyor; TUR.ANL/TUR.DIL/TUR.PAR/TUR.YAZ (nokta ayracli) ve
TYT-TR-* kaliplarinin HICBIRINI kapsamiyor. TUR kokunun kendisi de kapsam
disi.

AGACIN KAYNAGI: SAYFANIN KENDI BASLIK BANDI
-------------------------------------------
0017/0021/0022 ile ayni ilke: agac ICINDEKILER sayfasindan DEGIL, her soru
sayfasinin KENDI turuncu baslik bandindan uretildi.

Olcum (birincil kaynak: veriseti/zkitap/screenshots/<kitap>/, 16 Eyl 2026):
  * 224 sayfanin 90'i soru sayfasi. IKI BAGIMSIZ KANAL bu 90'i ayni
    kumede birlestirdi, sifir uyusmazlik:
      kanal 1 -- bant renk imzasi (turuncu>2000 VE mavi>2000) -> 86 sayfa
      kanal 2 -- sayfa altinda basili cevap seridi var mi     -> ayni 86
      + OSYM bandi (yesil+fistik) -> 221-224, 4 sayfa
  * 44 testin ilk sayfasinin bandi okundu; 17 farkli ad cikti
    (16 dilbilgisi unitesi + "OSYM SORULARI").
  * SIFIR SERBESTLIK DERECELI DOGRULAMA: bu 17 ad sayfa sirasinda tam 17
    KOSU olusturuyor -- hicbir unite ikinci kez acilmiyor. Bant okunmasi
    yanlis olsaydi bir blogun ortasinda yabanci bir kosu belirirdi.

BASILI ROZET KUSURU (varsayimla gecistirilmedi)
----------------------------------------------
"Konu Testi N" rozeti 16 unitenin 15'inde 1..N duzgun ilerliyor. TEK sapma:
SOZCUK TURLERI - ZARF (BELIRTEC) -> basili rozetler [1, 1] (s117 ve s119).
Sifir serbestlik dereceli kanal (cevap seridi numaralandirmasi) s117+s118'i
bir test (soru 1-12), s119+s120'yi AYRI bir test (soru 1-12) olarak kesin
ayiriyor. Bu dugum agaci etkilemiyor (ikisi de ayni uniteye baglaniyor);
soru duzeyinde pipeline_metadata.basili_test_rozeti olarak tasinir.

SEVIYE: yalnizca UNITE (level 2). Kitapta unite alti konu etiketi YOK.
Sayfa ustundeki "Konu Testi N" / "OSYM Sorulari" konu degil TEST TURUDUR ve
soru duzeyinde tasinir. Var olmayan bir L3 katmani uydurulmadi.

TUR-OSYM-GENEL
--------------
Kitabin son 4 sayfasi (221-224) unite ustu, karma cikmis OSYM sorulari.
Tek bir uniteye baglamak yanlis olurdu. BIO-OSYM-GENEL / EDB-OSYM-GENEL /
FIZ-OSYM-GENEL ile ayni kalip: ders duzeyinde "siniflandirilmamis" dugum.
Turkce'de boyle bir dugum YOKTU (olcum: code ILIKE '%OSYM%' -> 3 satir,
ucu de baska ders). Bu migration onu da kurar.

NEDEN MIGRATION, NEDEN SCRIPT DEGIL
-----------------------------------
Konu agaci referans veridir: her ortamda ayni olmali, surumlenmeli, geri
alinabilmeli. Sorular ayri gelir. 0013/0015/0017/0021/0022 ile ayni ayrim.

IDEMPOTENT
----------
Var olan kodlar ATLANIR. Olusturulan her dugumun id'si GUNLUK'e yazilir;
downgrade() yalnizca KENDI olusturdugu ve hicbir soru tasimayan dugumleri
siler (kullanilan varsa dokunmaz ve loglar).
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0025_dilbilgisi_konu_agaci"
down_revision: Union[str, None] = "0024_biyo345tyt_gorsel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "dilbilgisi_konu_gunlugu_0025"
TUR_KOK_KODU = "TUR"
KOD_ONEKI = "TUR-D"
OSYM_KODU = "TUR-OSYM-GENEL"

# (sira, kod, ad) -- sira kitabin sayfa sirasidir; adlar sayfa bandindan
# gelir, ASCII'ye duzlestirilmis halleriyle saklanir (agacin ev sozlesmesi).
# Yorumdaki sayi veri setinden OLCULEN ithal edilecek soru sayisidir.
KONULAR: tuple[tuple[int, str, str], ...] = (
    (1, "TUR-D1", "Ses Bilgisi"),  # 23
    (2, "TUR-D2", "Yazim Kurallari"),  # 34
    (3, "TUR-D3", "Noktalama Isaretleri"),  # 36
    (4, "TUR-D4", "Ekler ve Sozcuk Yapisi"),  # 46
    (5, "TUR-D5", "Sozcuk Turleri - Isim (Ad)"),  # 26
    (6, "TUR-D6", "Sozcuk Turleri - Sifat (On Ad)"),  # 25
    (7, "TUR-D7", "Tamlamalar"),  # 23
    (8, "TUR-D8", "Sozcuk Turleri - Zamir (Adil)"),  # 25
    (9, "TUR-D9", "Sozcuk Turleri - Zarf (Belirtec)"),  # 23
    (10, "TUR-D10", "Sozcuk Turleri - Edat (Ilgec) / Baglac / Unlem"),  # 25
    (11, "TUR-D11", "Sozcuk Turleri - Fiiller (Eylemler)"),  # 33
    (12, "TUR-D12", "Fiilimsiler (Eylemsiler)"),  # 24
    (13, "TUR-D13", "Fiilde (Eylemde) Cati"),  # 40
    (14, "TUR-D14", "Cumlenin Ogeleri"),  # 35
    (15, "TUR-D15", "Cumle Turleri"),  # 51
    (16, "TUR-D16", "Anlatim Bozukluklari"),  # 52
    (17, OSYM_KODU, "OSYM Kitapcik (siniflandirilmamis)"),  # 16
)

_EKLE = sa.text(
    """
    INSERT INTO topic_hierarchy
        (id, level, parent_id, code, name_tr, name_en, description, osym_relevance,
         osym_frequency, total_questions, average_difficulty, difficulty_level,
         subject_area, is_active, created_at, updated_at)
    VALUES (:id, :level, :parent_id, :code, :name_tr, NULL, :aciklama, 0.5,
            0, 0, 0.5, 0.5, 'TURKCE', TRUE, now(), now())
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
    "Aktif Ogrenme TYT Dilbilgisi Soru Bankasi 2025 sayfa baslik bandindan "
    "okundu; 224 sayfanin 90'i soru sayfasi (iki bagimsiz kanal, sifir "
    "uyusmazlik) ve 17 ad sayfa sirasinda tam 17 kosu olusturuyor "
    "(0025_dilbilgisi_konu_agaci)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; tekrar kosumda ayni id uretilir.

    0013/0015/0017/0021/0022 ile BIREBIR ayni formul.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0025] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0025] mv_safe_for_beta yenilendi")


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("topic_hierarchy"):
        _log.info("[0025] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": TUR_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0025] %s kok konusu yok -- atlandi", TUR_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # DIKKAT: bu iki desen TUR kokunu, TUR.ANL/TUR.DIL/TUR.PAR/TUR.YAZ
    # (nokta ayracli) ve TYT-TR-* dugumlerini KAPSAMAZ; hicbirine
    # dokunulmuyor.
    mevcut = {
        r[0]
        for r in b.execute(
            sa.text(
                "SELECT code FROM topic_hierarchy "
                "WHERE code LIKE :onek OR code = :osym"
            ),
            {"onek": KOD_ONEKI + "%", "osym": OSYM_KODU},
        ).fetchall()
    }

    eklenen = 0
    for _sira, kod, ad in KONULAR:
        if kod in mevcut:
            continue
        yeni_id = _dugum_id(kod)
        b.execute(
            _EKLE,
            {
                "id": yeni_id,
                "level": kok_level + 1,
                "parent_id": kok_id,
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
        "[0025] %s konu tanimi; bu kosumda eklenen dugum: %s",
        len(KONULAR),
        eklenen,
    )
    if sa.inspect(b).has_table("question_bank"):
        b.execute(sa.text(_SAYAC_SQL))
        _refresh_safe_for_beta(b)


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0025] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0025] %s dugum hala soru tasiyor -- SILINMEDI "
                "(once sorulari tasi): %s",
                len(kullanilan),
                sorted(kullanilan)[:3],
            )
            idler = [i for i in idler if i not in kullanilan]
    if idler:
        b.execute(
            sa.text(
                "DELETE FROM topic_hierarchy WHERE id = ANY(:idler) "
                "AND NOT EXISTS (SELECT 1 FROM topic_hierarchy c "
                "WHERE c.parent_id = topic_hierarchy.id)"
            ),
            {"idler": idler},
        )
    op.drop_table(GUNLUK)
    _log.info("[0025] downgrade tamam; silinen dugum: %s", len(idler))
