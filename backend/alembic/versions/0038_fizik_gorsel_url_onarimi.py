"""345 AYT Fizik + Mikro TYT Fizik satirlarinin gorsel URL'lerini onarir

Revision ID: 0038_fizik_gorsel_url
Revises: 0037_geo_beta_onay
Create Date: 2026-09-22

AYNI HATA, KALAN IKI KITAP
--------------------------
0036 geometri iki kitabini onarmisti. Ayni hata iki kitapta daha vardi ve
geometri onarimindan SONRA yapilan taramada ortaya cikti (DB genelinde
`/static/crops` ile baslamayan gorsel URL sayisi 0 beklenirken 2542 cikti):

    345 2025 AYT Fizik Soru Bankasi ........... 1295 satir
    Mikro Orijinal TYT Fizik Soru Bankasi 2025  1247 satir
                                                ----
                                                2542

`core/application.py` (satir 441-443) `CROP_IMAGE_DIR`i bir DOSYA SISTEMI
DIZINI olarak alir ve `/static/crops` URL yoluna mount eder. Iki ithal
araci da dizini URL kolonuna yazmisti:

    d-dataset/output/crops/FIZ345_AYT/<uuid>.png
    d-dataset/output/crops/MIKRO_FIZIK_TYT/<uuid>.png

Bu deger tarayicinin cozemeyecegi goreli bir yoldur.

ETKI: SIFIR (henuz)
-------------------
Iki kitap da TAMAMEN PASIF (is_active 0/1308 ve 0/1326), yani canli
serviste bozuk bir gorsel YOK. Onarim, ileride bir aktiflestirme
migration'i yazildiginda 0037'de oldugu gibi gec kalmamak icin simdi
yapilir. 345 AYT Fizik'in 1007 sorusu (%77) sekil iceriyor.

KIRPIM DOSYALARI ZATEN YERINDE
------------------------------
Geometride kirpimlar yanlis dizine yazilmisti; burada degil. Olculdu:

    servis dizini (docker bind: kiro2/d-dataset/output/crops)
      FIZ345_AYT ........ 1295 png   (DB'deki gorselli satir sayisi 1295)
      MIKRO_FIZIK_TYT ... 1247 png   (DB'deki gorselli satir sayisi 1247)

Ornek satirlarin dosyalari diskte tek tek dogrulandi. Bu yuzden bu
migration YALNIZCA URL bicimini duzeltir; dosya tasima yoktur.

NE YAPAR
--------
Yalnizca bu iki `source_book` icin, yalnizca URL'si `/static/crops/` ile
BASLAMAYAN satirlarda, dosya adi korunarak onek `/static/crops/<ONEK>/`
yapilir. Dosya adi var olan degerden ALINIR, yeniden turetilmez.

Ithal araclari da ayni commit'te duzeltildi, yoksa yeniden kosuldugunda
ayni hatali degeri tekrar yazarlardi.

GERI ALINABILIR
---------------
Degisen her satirin onceki URL'si GUNLUK'e yazilir; downgrade tam olarak
o degeri geri koyar.

Revizyon adi 21 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0038_fizik_gorsel_url"
down_revision: Union[str, None] = "0037_geo_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "fizik_gorsel_url_gunlugu_0038"
DOGRU_ONEK = "/static/crops/"

# (source_book, crop oneki) -- crop oneki ithal aracindaki CROP_ONEK ile ayni.
KAYNAKLAR: tuple[tuple[str, str], ...] = (
    ("345 2025 AYT Fizik Soru Bankasi", "FIZ345_AYT"),
    ("Mikro Orijinal TYT Fizik Soru Bankasi 2025", "MIKRO_FIZIK_TYT"),
)

_HEDEF_SQL = """
SELECT qc.id, qc.question_image_url
  FROM question_content qc
  JOIN question_metadata qm ON qm.id = qc.id
 WHERE qm.source_book = :kaynak
   AND qc.question_image_url IS NOT NULL
   AND qc.question_image_url NOT LIKE :onek
"""


def _tablolar_var(b) -> bool:
    denetci = sa.inspect(b)
    return all(denetci.has_table(t) for t in ("question_content", "question_metadata"))


def _gunlugu_kur() -> None:
    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_url", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def _yeni_url(eski: str, crop_onek: str) -> str:
    """Dosya adini korur, onunu /static/crops/<ONEK>/ yapar."""
    dosya = eski.rsplit("/", 1)[-1]
    return f"{DOGRU_ONEK}{crop_onek}/{dosya}"


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0038] soru tablolari yok (taze DB?) -- atlandi")
        return

    hedefler: list[tuple[str, str, str]] = []
    for kaynak, crop_onek in KAYNAKLAR:
        satirlar = b.execute(
            sa.text(_HEDEF_SQL), {"kaynak": kaynak, "onek": f"{DOGRU_ONEK}%"}
        ).fetchall()
        for sid, eski in satirlar:
            hedefler.append((sid, eski, _yeni_url(eski, crop_onek)))
        _log.info("[0038] %s: onarilacak %s satir", kaynak, len(satirlar))

    if not hedefler:
        _log.info("[0038] onarilacak satir yok -- atlandi")
        return

    _gunlugu_kur()
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, onceki_url) VALUES (:id, :url)"  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad, kullanici girdisi degil
        ),
        [{"id": sid, "url": eski} for sid, eski, _ in hedefler],
    )
    b.execute(
        sa.text(
            "UPDATE question_content SET question_image_url = :yeni WHERE id = :id"
        ),
        [{"id": sid, "yeni": yeni} for sid, _, yeni in hedefler],
    )
    _log.info("[0038] gorsel URL onarildi: %s satir", len(hedefler))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0038] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return

    kayitlar = b.execute(
        sa.text(f"SELECT id, onceki_url FROM {GUNLUK}")  # noqa: S608  # nosec B608 - GUNLUK sabit modul duzeyi ad, kullanici girdisi degil
    ).fetchall()
    if kayitlar:
        b.execute(
            sa.text(
                "UPDATE question_content SET question_image_url = :url WHERE id = :id"
            ),
            [{"id": sid, "url": url} for sid, url in kayitlar],
        )
    _log.info("[0038] geri alindi: %s satir eski URL'sine dondu", len(kayitlar))
    op.drop_table(GUNLUK)
