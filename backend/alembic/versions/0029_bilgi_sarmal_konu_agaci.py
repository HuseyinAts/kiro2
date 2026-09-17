"""Bilgi Sarmal TYT Turkce konu agacini kurar (9 bolum + 32 konu)

Revision ID: 0029_bilgi_sarmal_agac
Revises: 0028_dilbilgisi_cevap
Create Date: 2026-09-17

BAGLAM
------
"Bilgi Sarmal Tyt Turkce Soru Bankasi" ithali icin TUR kokunun altina IKI
SEVIYELI bir alt agac kurar:

    TUR
     +- TUR-BS1 .. TUR-BS9        kitabin kendi 9 BOLUM'u
         +- TUR-BS<n>-NN          o bolumun gercek konulari (32 dugum)

AGAC NEREDEN OKUNDU
-------------------
Kitabin KENDI cevap anahtarindan (s332-336). Anahtar her test blogu icin
bolum basligini, konu adini ve testin basladigi sayfayi basiyor. Iki
bagimsiz okuma bu 114 blogu ayni sirada ve ayni `Sayfa:` degerleriyle
verdi; bolum numaralari 1..9 kesintisiz ve sirali cikti.

NEDEN BAZI TESTLER KONU DUGUMU ALMIYOR
--------------------------------------
Anahtardaki 63 farkli test adinin bir bolumu bir KONUYU degil, bolumun
tamamini tarayan KARMA testtir: "Sarmal Test - N", "OSYM Tipi ...",
"SIMULASYON-N", "... (Karma)", "Tarama Testi". Bunlara ayri konu dugumu
acmak agaci yalancilastirirdi; bu testlerin sorulari dogrudan kendi BOLUM
dugumune baglanir ve satirda `konu_eslesme_duzeyi='bolum_karma_test'`
yazar. Olculen dagilim: 956 soru konu dugumune, 512 soru bolum dugumune.

Ayni desen 0021/0022/0025'te kullanilan `uuid5(NAMESPACE_OID, "topic:"+kod)`
ile deterministik id uretir; tekrar kosumda ayni id gelir.

GERI ALINABILIR
---------------
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

revision: str = "0029_bilgi_sarmal_agac"
down_revision: Union[str, None] = "0028_dilbilgisi_cevap"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "bilgi_sarmal_konu_gunlugu_0029"
TUR_KOK_KODU = "TUR"
KOD_ONEKI = "TUR-BS"

BOLUMLER: tuple[tuple[int, str, str], ...] = (
    (1, "TUR-BS1", "SOZCUK DUZEYINDE ANLAM"),
    (2, "TUR-BS2", "CUMLEDE ANLAM"),
    (3, "TUR-BS3", "PARAGRAFTA ANLATIM"),
    (4, "TUR-BS4", "PARAGRAF DUZEYINDE ANLAM"),
    (5, "TUR-BS5", "SES - YAZIM - NOKTALAMA"),
    (6, "TUR-BS6", "SOZCUKTE YAPI"),
    (7, "TUR-BS7", "SOZCUK TURLERI"),
    (8, "TUR-BS8", "CUMLENIN OGELERI CUMLE TURLERI"),
    (9, "TUR-BS9", "ANLATIM BOZUKLUKLARI"),
)

# (ust bolum kodu, sira, kod, ad)
KONULAR: tuple[tuple[str, int, str, str], ...] = (
    ("TUR-BS1", 1, "TUR-BS1-01", "Sozcuk Duzeyinde Anlam"),
    ("TUR-BS2", 1, "TUR-BS2-01", "Cumle Tamamlama ve Cumle Olusturma"),
    ("TUR-BS2", 2, "TUR-BS2-02", "Cumle Tamamlama"),
    ("TUR-BS2", 3, "TUR-BS2-03", "Cumle Yorumu"),
    ("TUR-BS2", 4, "TUR-BS2-04", "Cumlede Kesin Yargi - Yargi Birlestirme"),
    ("TUR-BS2", 5, "TUR-BS2-05", "Yargilar Arasi Iliskiler ve Kavramlar"),
    ("TUR-BS3", 1, "TUR-BS3-01", "Anlatim Bicimleri"),
    ("TUR-BS3", 2, "TUR-BS3-02", "Anlatimin Nitelikleri"),
    ("TUR-BS4", 1, "TUR-BS4-01", "Paragrafin Yapisi"),
    ("TUR-BS4", 2, "TUR-BS4-02", "Paragrafta Cumle Ekleme"),
    ("TUR-BS4", 3, "TUR-BS4-03", "Paragrafta Konu ve Ana Dusunce"),
    ("TUR-BS4", 4, "TUR-BS4-04", "Paragrafta Yardimci Dusunceler"),
    ("TUR-BS4", 5, "TUR-BS4-05", "Kisi Ozellikleri"),
    ("TUR-BS4", 6, "TUR-BS4-06", "Paragrafin Hangi Soruya Karsilik Oldugu"),
    ("TUR-BS5", 1, "TUR-BS5-01", "Ses Bilgisi"),
    ("TUR-BS5", 2, "TUR-BS5-02", "Yazim Kurallari"),
    ("TUR-BS5", 3, "TUR-BS5-03", "Noktalama Isaretleri"),
    ("TUR-BS6", 1, "TUR-BS6-01", "Sozcukte Yapi (Bicim Bilgisi)"),
    ("TUR-BS7", 1, "TUR-BS7-01", "Adlar (Isimler)"),
    ("TUR-BS7", 2, "TUR-BS7-02", "Sifatlar (On Adlar)"),
    ("TUR-BS7", 3, "TUR-BS7-03", "Tamlamalar"),
    ("TUR-BS7", 4, "TUR-BS7-04", "Zamirler (Adillar)"),
    ("TUR-BS7", 5, "TUR-BS7-05", "Zarflar (Belirtecler)"),
    ("TUR-BS7", 6, "TUR-BS7-06", "Edat - Baglac - Unlem"),
    ("TUR-BS7", 7, "TUR-BS7-07", "Eylemler"),
    ("TUR-BS7", 8, "TUR-BS7-08", "Eylemsiler"),
    ("TUR-BS7", 9, "TUR-BS7-09", "Eylemde Cati"),
    ("TUR-BS7", 10, "TUR-BS7-10", "Ek Fiil"),
    ("TUR-BS8", 1, "TUR-BS8-01", "Cumlenin Ogeleri"),
    ("TUR-BS8", 2, "TUR-BS8-02", "Cumle Turleri"),
    ("TUR-BS8", 3, "TUR-BS8-03", "Dil, Iletisim, Gosterge Bilim"),
    ("TUR-BS9", 1, "TUR-BS9-01", "Anlatim Bozukluklari"),
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
    "Bilgi Sarmal TYT Turkce Soru Bankasi'nin kendi cevap anahtarindan "
    "(s332-336) okundu; 114 test blogu iki bagimsiz okumada ayni sirayla "
    "ve ayni sayfa numaralariyla cikti (0029_bilgi_sarmal_agac)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; 0013/0015/0017/0021/0022/0025 ile ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0029] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0029] mv_safe_for_beta yenilendi")


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
        _log.info("[0029] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": TUR_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0029] %s kok konusu yok -- atlandi", TUR_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # TUR-BS deseni, 0025'in TUR-D* kodlarini ve TUR kokunu KAPSAMAZ.
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
            mevcut_id = b.execute(
                sa.text("SELECT id FROM topic_hierarchy WHERE code = :k"), {"k": kod}
            ).scalar_one()
            bolum_id[kod] = mevcut_id
            continue
        bolum_id[kod] = _yaz(b, kod, ad, kok_level + 1, kok_id)
        eklenen += 1

    for ust, _sira, kod, ad in KONULAR:
        if kod in mevcut:
            continue
        _yaz(b, kod, ad, kok_level + 2, bolum_id[ust])
        eklenen += 1

    _log.info(
        "[0029] %s bolum + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0029] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0029] %s dugum hala soru tasiyor -- SILINMEDI "
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
    _log.info("[0029] downgrade tamam; silinmeye aday dugum: %s", len(idler))
