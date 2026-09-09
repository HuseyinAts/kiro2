"""Etiket duzeltmeleri: 21 soru dogru ders kokune, 52 soru AYT, 3 yanlis anahtar pasif

Revision ID: 0009_etiket_duzeltme
Revises: 0008_kalibrasyon_bayragi
Create Date: 2026-09-09

UC DUZELTME, HEPSI GUNLUKLU VE GERI ALINABILIR (rapor madde 14 yan bulgu,
madde 19; docs/veritabani-denetimi-20260909.md)
-------------------------------------------------------------------------
1. KOK UYUSMAZLIGI (21 soru, hepsi elle okundu): soru dogrudan bir DERS
   KOKUNE bagli (konu yok) ama kok baska dersin: FIZ kokunde 5 KIMYA
   (elektrokimya, cozunurluk, ester, alkan, atom teorisi), FEN kokunde 1
   KIMYA (elektron dizilimi), SOS kokunde 11 TARIH + 4 COGRAFYA. Icerik
   `subject_area` ile uyusuyor, konu yanlis. Duzeltme: primary_topic_id =
   dersin kendi koku (KIM/TAR/COG). Konu duzeyi yine "kok" -- konu atamasi
   ayri is (1.011 soru kok duzeyinde).
2. EXAM_TYPE (52 soru): source_book "Esen Apt Ayt Fizik 2025" (icerik
   KIMYA, kaynak adi yanlis) altindaki sorularin 52'si TYT etiketli; hepsi
   KIM.DEN konusunda, 3 ornek okundu: bag entalpisi, denge sabiti (Kc),
   hibritlesme -- 11-12. sinif (AYT) konulari, kitap adi da AYT.
   Duzeltme: exam_type = 'AYT'.
3. YANLIS ANAHTAR (3 soru pasif): kapidan gecen 31 `bayes_*` (cozucu
   oylamasi) anahtarli sorunun hepsi elle cozuldu; 26 dogru, 5 supheli,
   3'unde anahtar/soru kesin kusurlu:
     cd403a4d: "en az kac carpma" -- 2*5*7+3+11-13 = 71 ile 2 (parantezle
               7*11-(13+5):2+3 ile 1); siklar 3..7, anahtar 3: soru/sik
               bozuk.
     ef3e1c75: |a-c|=b kosulunu saglayan uc basamakli sayi 90 (26 degil);
               dogru sik D (I ve III), anahtar C.
     c1ab0540: metin OCR'da bozuk ("ugultusuna bir dunyaya", "gidide");
               dogru sik E, anahtar C.
   Duzeltme: is_active = false (silinmez). Kalan 2 suphelinin (1dd54e6a
   Tevhid-i Tedrisat, dab0707f paragraf) karari icerik tarafinin.

GUNLUK: etiket_duzeltme_gunlugu_0009(id, alan, eski_deger) -- downgrade
her satiri eski degerine dondurur, tabloyu dusurur. Taze DB'de (satirlar
yoksa) her iki yon is-yapmaz ve loglar.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0009_etiket_duzeltme"
down_revision: Union[str, None] = "0008_kalibrasyon_bayragi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "etiket_duzeltme_gunlugu_0009"

# subject_area -> kok kodu (yalnizca bu migration'in dokundugu dersler)
_DERS_KOKU = {"KIMYA": "KIM", "TARIH": "TAR", "COGRAFYA": "COG"}
# Kok kodu -> o kokun dersi (uyusmazlik tespiti icin)
_KOK_DERSI = {"FIZ": "FIZIK", "FEN": "FEN", "SOS": "SOSYAL"}

_YANLIS_KAYNAK = "Esen Apt Ayt Fizik 2025"

_PASIF = (
    "cd403a4d-3ec6-59c1-9a6b-5a03036f126d",
    "ef3e1c75-96f0-53c4-b0d8-fdb66c6fc90e",
    "c1ab0540-607a-5ca8-a0f8-21e26621cea5",
)

# Konu tasima + pasife alma sayaci degistirir (0005/0006/0007 ile ayni SQL);
# bekci test_total_questions_sayaci_gercekle_uyusur bunu yakalar (olculdu).
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


def _kok_id(b, kod: str) -> Union[str, None]:
    sonuc: Union[str, None] = b.execute(
        sa.text(
            "SELECT id FROM topic_hierarchy "
            "WHERE code = :kod AND parent_id IS NULL AND subject_area IS NULL"
        ),
        {"kod": kod},
    ).scalar()
    return sonuc


def _gunlukle(b, satirlar: list) -> None:
    if satirlar:
        b.execute(
            sa.text(
                f"INSERT INTO {GUNLUK} (id, alan, eski_deger) "  # noqa: S608 -- sabit tablo adi  # nosec B608
                "VALUES (:id, :alan, :eski)"
            ),
            [{"id": s[0], "alan": s[1], "eski": s[2]} for s in satirlar],
        )


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("question_bank"):
        _log.info("[0009] question_bank yok (taze DB?) -- atlandi")
        return
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("alan", sa.String(), nullable=False),
        sa.Column("eski_deger", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", "alan"),
    )

    # 1) Yanlis kokteki sorular -> dersin koku (yalnizca dogrudan koke bagli olanlar).
    tasinan = 0
    for yanlis_kok, _ders in _KOK_DERSI.items():
        kaynak_kok = _kok_id(b, yanlis_kok)
        if kaynak_kok is None:
            continue
        for ders, hedef_kod in _DERS_KOKU.items():
            hedef_kok = _kok_id(b, hedef_kod)
            if hedef_kok is None:
                continue
            satirlar = (
                b.execute(
                    sa.text(
                        "SELECT q.id FROM question_bank q JOIN question_metadata m ON m.id = q.id "
                        "WHERE q.primary_topic_id = :kok AND upper(m.subject_area) = :ders"
                    ),
                    {"kok": kaynak_kok, "ders": ders},
                )
                .scalars()
                .all()
            )
            if not satirlar:
                continue
            _gunlukle(b, [(sid, "primary_topic_id", kaynak_kok) for sid in satirlar])
            b.execute(
                sa.text(
                    "UPDATE question_bank SET primary_topic_id = :hedef, updated_at = now() "
                    "WHERE id = ANY(:ids)"
                ),
                {"hedef": hedef_kok, "ids": list(satirlar)},
            )
            tasinan += len(satirlar)

    # 2) Yanlis adli AYT kitabinin TYT etiketli sorulari -> AYT.
    ayt = (
        b.execute(
            sa.text(
                "SELECT id FROM question_metadata "
                "WHERE source_book = :kaynak AND exam_type = 'TYT'"
            ),
            {"kaynak": _YANLIS_KAYNAK},
        )
        .scalars()
        .all()
    )
    _gunlukle(b, [(sid, "exam_type", "TYT") for sid in ayt])
    if ayt:
        b.execute(
            sa.text(
                "UPDATE question_metadata SET exam_type = 'AYT' WHERE id = ANY(:ids)"
            ),
            {"ids": list(ayt)},
        )

    # 3) Kesin kusurlu anahtar -> pasif.
    pasif = (
        b.execute(
            sa.text(
                "SELECT id FROM question_bank WHERE id = ANY(:ids) AND is_active IS TRUE"
            ),
            {"ids": list(_PASIF)},
        )
        .scalars()
        .all()
    )
    _gunlukle(b, [(sid, "is_active", "true") for sid in pasif])
    if pasif:
        b.execute(
            sa.text(
                "UPDATE question_bank SET is_active = FALSE, updated_at = now() "
                "WHERE id = ANY(:ids)"
            ),
            {"ids": list(pasif)},
        )
    b.execute(sa.text(_SAYAC_SQL))
    _log.info(
        "[0009] %s soru dogru koke tasindi, %s soru AYT, %s soru pasif",
        tasinan,
        len(ayt),
        len(pasif),
    )


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0009] %s yok -- geri alinacak bir sey yok", GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(f"SELECT id, alan, eski_deger FROM {GUNLUK}")  # noqa: S608 -- sabit tablo adi  # nosec B608
    ).all()
    for sid, alan, eski in kayitlar:
        if alan == "primary_topic_id":
            b.execute(
                sa.text(
                    "UPDATE question_bank SET primary_topic_id = :eski, updated_at = now() "
                    "WHERE id = :id"
                ),
                {"eski": eski, "id": sid},
            )
        elif alan == "exam_type":
            b.execute(
                sa.text(
                    "UPDATE question_metadata SET exam_type = :eski WHERE id = :id"
                ),
                {"eski": eski, "id": sid},
            )
        elif alan == "is_active":
            b.execute(
                sa.text(
                    "UPDATE question_bank SET is_active = TRUE, updated_at = now() "
                    "WHERE id = :id"
                ),
                {"id": sid},
            )
    b.execute(sa.text(_SAYAC_SQL))
    op.drop_table(GUNLUK)
    _log.info("[0009] %s kayit geri alindi, %s dusuruldu", len(kayitlar), GUNLUK)
