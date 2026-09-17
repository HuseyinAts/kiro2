"""Bilgi Sarmal AYT Edebiyat Soru Bankasi -- konu agaci (EDB kokunun altina).

NEDEN
-----
Bu kitabin ithali (scripts/kitap/bilgi_sarmal_edebiyat_ithal.py) her soruyu
bir konu dugumune baglar. EDB kokunun altinda bu kosumdan once YALNIZCA
`EDB-OSYM-GENEL` vardi; Edebiyat agaci pratikte YOKTU. Bu migration olmadan
ithal DURUR (konu kodu bulunamaz), cunku sessizce koke baglamak yanlis
veridir.

KAYNAK
------
Dugum adlari UYDURULMADI: kitabin kendi CEVAP ANAHTARI bolumundeki
(dosya s409-416) bolum basliklari ve test konu adlarindan alindi. Anahtar
IKI BAGIMSIZ okumayla cikarildi; 130 test blogunun bolum/konu adlari iki
okumada ayni sirayla cikti (tek fark iki blokta "Dini/Dini" sapkasiydi,
B okumasi esas alindi).

5 bolum (EDB-BS1..EDB-BS5) + 53 konu dugumu (EDB-BS<n>-NN).
SARMAL TEST / OSYM TIPI / Roman Karma gibi KARMA testler bir konuyu degil
bolumun tamamini tarar; onlar konu dugumune DEGIL kendi BOLUM dugumune
baglanir (ithal tarafinda `konu_eslesme_duzeyi='bolum'`).

GERI ALINABILIRLIK
------------------
Bu kosumda olusturulan her dugum GUNLUK'e yazilir; downgrade yalnizca
onlari siler ve SORU TASIYAN ya da COCUGU OLAN dugume DOKUNMAZ.

Revizyon adi 22 karakter (sinir 32).
"""

import logging
import uuid
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0031_bs_edebiyat_agac"
down_revision: Union[str, None] = "0030_bs_kaynak_adi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "bs_edebiyat_konu_gunlugu_0031"
EDB_KOK_KODU = "EDB"
KOD_ONEKI = "EDB-BS"

BOLUMLER: tuple[tuple[int, str, str], ...] = (
    (1, "EDB-BS1", "EDEBI AKIMLAR EDEBIYATA GIRIS EDEBIYATIN GUZEL SANATLARLA VE BILIMLE ILISKISI"),
    (2, "EDB-BS2", "MASAL - FABL - DESTAN - EFSANE - HIKAYE (OYKU)"),
    (3, "EDB-BS3", "DUYGU VE HEYECANI DILE GETIREN METINLER (SIIR)"),
    (4, "EDB-BS4", "ROMAN"),
    (5, "EDB-BS5", "TIYATRO (GOSTERMEYE DAYALI METINLER)"),
)

# (ust bolum kodu, sira, kod, ad)
KONULAR: tuple[tuple[str, int, str, str], ...] = (
    ("EDB-BS1", 1, "EDB-BS1-01", "Edebi Akimlar ve Temsilcileri"),
    ("EDB-BS1", 2, "EDB-BS1-02", "Edebiyata Giris - Edebiyatin Bilim ve Guzel Sanatlarla Iliskisi"),
    ("EDB-BS1", 3, "EDB-BS1-03", "Turk Edebiyatinin Donemleri - Edebiyatin Donemlere Ayrilmasindaki Olcutler"),
    ("EDB-BS1", 4, "EDB-BS1-04", "Turk Edebiyatinin Ilk Yazili Urunleri"),
    ("EDB-BS1", 5, "EDB-BS1-05", "Metinlerin Siniflandirilmasi"),
    ("EDB-BS1", 6, "EDB-BS1-06", "Ogretici Metinler"),
    ("EDB-BS1", 7, "EDB-BS1-07", "Sozlu Anlatim"),
    ("EDB-BS2", 1, "EDB-BS2-01", "Masal / Fabl"),
    ("EDB-BS2", 2, "EDB-BS2-02", "Destan / Efsane"),
    ("EDB-BS2", 3, "EDB-BS2-03", "Hikaye Turleri ve Unsurlari"),
    ("EDB-BS2", 4, "EDB-BS2-04", "Dede Korkut Hikayeleri / Halk Hikayeleri"),
    ("EDB-BS2", 5, "EDB-BS2-05", "Mesnevi"),
    ("EDB-BS2", 6, "EDB-BS2-06", "Tanzimat-Servetifunun Donemi Hikayeleri"),
    ("EDB-BS2", 7, "EDB-BS2-07", "Milli Edebiyat Donemi Hikayeleri"),
    ("EDB-BS2", 8, "EDB-BS2-08", "Cumhuriyet Donemi Hikayeleri"),
    ("EDB-BS3", 1, "EDB-BS3-01", "Siirin Yapi Ozellikleri / Ahenk Unsurlari"),
    ("EDB-BS3", 2, "EDB-BS3-02", "Siir Turleri ve Siirde Tema"),
    ("EDB-BS3", 3, "EDB-BS3-03", "Soz Sanatlari / Siirin Dili ve Anlatimi"),
    ("EDB-BS3", 4, "EDB-BS3-04", "Islamiyet Oncesi Turk Siiri"),
    ("EDB-BS3", 5, "EDB-BS3-05", "Gecis Donemi Eserleri"),
    ("EDB-BS3", 6, "EDB-BS3-06", "Anonim Halk Siiri"),
    ("EDB-BS3", 7, "EDB-BS3-07", "Asik Tarzi Halk Siiri"),
    ("EDB-BS3", 8, "EDB-BS3-08", "Dini / Tasavvufi Halk Siiri"),
    ("EDB-BS3", 9, "EDB-BS3-09", "Divan Siiri"),
    ("EDB-BS3", 10, "EDB-BS3-10", "Tanzimat Siiri"),
    ("EDB-BS3", 11, "EDB-BS3-11", "Servetifunun Siiri"),
    ("EDB-BS3", 12, "EDB-BS3-12", "Fecriati Siiri"),
    ("EDB-BS3", 13, "EDB-BS3-13", "Saf (Oz) Siir"),
    ("EDB-BS3", 14, "EDB-BS3-14", "Milli Edebiyat Siiri"),
    ("EDB-BS3", 15, "EDB-BS3-15", "Cumhuriyet Donemi Turk Siiri (Saf Oz) Siir Anlayisi"),
    ("EDB-BS3", 16, "EDB-BS3-16", "Cumhuriyet Donemi Turk Siiri (Toplumcu Siir)"),
    ("EDB-BS3", 17, "EDB-BS3-17", "Cumhuriyet Donemi Turk Siiri (Toplumcu Siir ve Maviciler)"),
    ("EDB-BS3", 18, "EDB-BS3-18", "Cumhuriyet Donemi Turk Siiri (Milli Edebiyat Zevk ve Anlayisini Surdurenler)"),
    ("EDB-BS3", 19, "EDB-BS3-19", "Cumhuriyet Donemi Turk Siiri (Garip Siiri I. Yeni)"),
    ("EDB-BS3", 20, "EDB-BS3-20", "Cumhuriyet Donemi Turk Siiri (Ikinci Yeni Siiri)"),
    ("EDB-BS3", 21, "EDB-BS3-21", "Cumhuriyet Donemi Turk Siiri (Dini Degerleri ve Metafizigi One Cikaran Siir)"),
    ("EDB-BS3", 22, "EDB-BS3-22", "Cumhuriyet Donemi Turk Siiri (1960 Sonrasi (II. Yeni Sonrasi) Toplumcu Siir)"),
    ("EDB-BS3", 23, "EDB-BS3-23", "Cumhuriyet Donemi Turk Siiri (1980 Sonrasi Siir)"),
    ("EDB-BS3", 24, "EDB-BS3-24", "Cumhuriyet Donemi Turk Siiri (Halk Siiri)"),
    ("EDB-BS3", 25, "EDB-BS3-25", "Cumhuriyet Donemi Turk Siiri (Turkiye Disindaki Turk Siiri)"),
    ("EDB-BS4", 1, "EDB-BS4-01", "Roman Turunun Genel Ozellikleri"),
    ("EDB-BS4", 2, "EDB-BS4-02", "Turk ve Dunya Edebiyatinda Roman"),
    ("EDB-BS4", 3, "EDB-BS4-03", "Tanzimat Donemi'nde Roman"),
    ("EDB-BS4", 4, "EDB-BS4-04", "Servetifunun Donemi'nde Roman"),
    ("EDB-BS4", 5, "EDB-BS4-05", "Milli Edebiyat Donemi'nde Roman"),
    ("EDB-BS4", 6, "EDB-BS4-06", "Cumhuriyet Donemi'nde Milli Anlayisini Surduren Romanlar"),
    ("EDB-BS4", 7, "EDB-BS4-07", "Toplumsal Gercekciler"),
    ("EDB-BS4", 8, "EDB-BS4-08", "Bireyin Ic Dunyasini Esas Alanlar"),
    ("EDB-BS4", 9, "EDB-BS4-09", "Modernizmi Esas Alanlar"),
    ("EDB-BS5", 1, "EDB-BS5-01", "Genel Bilgiler, Tiyatro Terimleri"),
    ("EDB-BS5", 2, "EDB-BS5-02", "Geleneksel Turk Tiyatrosu"),
    ("EDB-BS5", 3, "EDB-BS5-03", "Dunya Edebiyati'nda / Tanzimat ve Servetifunun Donemi'nde Tiyatro"),
    ("EDB-BS5", 4, "EDB-BS5-04", "Milli Edebiyat ve Cumhuriyet Donemi'nde Tiyatro"),
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
    "Bilgi Sarmal AYT Edebiyat Soru Bankasi'nin kendi cevap anahtarindan "
    "(dosya s409-416) okundu; 130 test blogu iki bagimsiz okumada ayni "
    "sirayla ve ayni sayfa numaralariyla cikti. Anahtarin sayfa listesi, "
    "metin hic okunmadan olculen basli-bant piksel kanaliyla 130/130 "
    "ortustu (0031_bs_edebiyat_agac)."
)


def _dugum_id(kod: str) -> str:
    """Kod -> deterministik id; 0013/0015/0017/0021/0022/0025/0029 ile ayni formul."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"topic:{kod}"))


def _refresh_safe_for_beta(b) -> None:
    var = b.execute(
        sa.text("SELECT to_regprocedure('public.refresh_safe_for_beta()')")
    ).scalar()
    if var is None:
        _log.info("[0031] refresh_safe_for_beta() yok -- atlandi (taze/CI DB)")
        return
    b.execute(sa.text("SELECT refresh_safe_for_beta()"))
    _log.info("[0031] mv_safe_for_beta yenilendi")


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
        _log.info("[0031] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    kok = b.execute(
        sa.text(
            "SELECT id, level FROM topic_hierarchy "
            "WHERE code = :k AND parent_id IS NULL"
        ),
        {"k": EDB_KOK_KODU},
    ).fetchone()
    if kok is None:
        _log.warning("[0031] %s kok konusu yok -- atlandi", EDB_KOK_KODU)
        return
    kok_id, kok_level = kok[0], int(kok[1])

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("kod", sa.String(), nullable=False),
        sa.Column("olusturuldu", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # EDB-BS deseni; EDB-OSYM-GENEL'i ve EDB kokunu KAPSAMAZ.
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
        "[0031] %s bolum + %s konu tanimi; bu kosumda eklenen dugum: %s",
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
        _log.info("[0031] %s yok -- downgrade atlandi", GUNLUK)
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
                "[0031] %s dugum hala soru tasiyor -- SILINMEDI "
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
    _log.info("[0031] downgrade tamam; silinmeye aday dugum: %s", len(idler))
