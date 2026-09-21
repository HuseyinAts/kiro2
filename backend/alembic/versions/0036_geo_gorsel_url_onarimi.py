"""ACIL + C1CELL geometri satirlarinin gorsel URL'lerini onarir

Revision ID: 0036_geo_gorsel_url
Revises: 0035_c1cellgeo_agac
Create Date: 2026-09-21

HATA NE
-------
`core/application.py` (satir 441-443) soyle yapar:

    crop_dir = os.environ.get("CROP_IMAGE_DIR", "d-dataset/output/crops")
    app.mount("/static/crops", StaticFiles(directory=crop_dir), name="crops")

Yani `CROP_IMAGE_DIR` bir DOSYA SISTEMI DIZINIDIR ve `/static/crops` URL
yoluna baglanir. `question_image_url` kolonuna yazilmasi gereken sey URL'dir.

Calisan kitaplar bunu dogru yapiyordu:

    geo345_ithal.py ....... /static/crops/GEO345/<id>.png
    mikro_geo ............. /static/crops/MIKRO_GEO/mikro-geo-s0195-03.png

Iki geometri ithal araci ise DIZINI URL kolonuna yazdi:

    acil_geo_ithal.py ..... d-dataset/output/crops/ACILGEO_2324/s0005_sol_1.png
    c1cell_geo_ithal.py ... d-dataset/output/crops/C1CELLGEO_2024/s0008_sol_1.png

Bu deger tarayicinin cozemeyecegi GORELI bir yoldur; `/static/crops` altinda
da degildir. Satirlar PASIF oldugu icin kimseye gorunmedi, ama aktiflestirme
oncesi onarilmasi sart: ACIL'in 1513, C1CELL'in 1519 sorusu SEKIL iceriyor ve
sekil olmadan cozulemez (toplam 3032 soru).

OLCUM (21 Eyl 2026, canli DB)
-----------------------------
    kitap                                     satir   gorselli   /static/ ile
    ACIL 2023-2024 TYT-AYT Geometri            1730       1730              0
    C1CELL 2024 TYT-AYT Geometri               1770       1770              0

Ayni olcumde modern ithalli 15 kitabin HICBIRINDE `/_figonly/` URL yok; bu
migration o ayri konuya DOKUNMAZ, yalnizca yol bicimini duzeltir.

NE YAPAR
--------
Yalnizca bu iki `source_book` icin, yalnizca URL'si `/static/crops/` ile
BASLAMAYAN satirlarda, son iki bilesen (<ONEK>/<dosya>) korunarak onek
`/static/crops/` yapilir. Baska kaynaga, baska kolona dokunmaz.

Kaynak adlari `scripts/kitap/kaynak_sozlesmesi.py::KAYNAK_KAYITLARI` ile
ayni yazimdir (sozlesme geregi ASCII).

GERI ALINABILIR
---------------
Degisen her satirin onceki URL'si GUNLUK'e yazilir; downgrade tam olarak o
degeri geri koyar.

Ithal araclari da ayni commit'te duzeltildi, yoksa yeniden kosuldugunda ayni
hatali degeri tekrar yazarlardi.

Revizyon adi 19 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0036_geo_gorsel_url"
down_revision: Union[str, None] = "0035_c1cellgeo_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "geo_gorsel_url_gunlugu_0036"
DOGRU_ONEK = "/static/crops/"

# (source_book, crop oneki) -- crop oneki ithal aracindaki CROP_ONEK ile ayni.
KAYNAKLAR: tuple[tuple[str, str], ...] = (
    ("ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi", "ACILGEO_2324"),
    ("C1CELL 2024 TYT-AYT Geometri Soru Bankasi", "C1CELLGEO_2024"),
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
    """Son iki bileseni (<ONEK>/<dosya>) korur, onunu /static/crops/ yapar.

    Dosya adi kirpim script'inin urettigi deterministik addir; burada
    yeniden turetilmez, var olan degerden ALINIR.
    """
    dosya = eski.rsplit("/", 1)[-1]
    return f"{DOGRU_ONEK}{crop_onek}/{dosya}"


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0036] soru tablolari yok (taze DB?) -- atlandi")
        return

    hedefler: list[tuple[str, str, str]] = []
    for kaynak, crop_onek in KAYNAKLAR:
        satirlar = b.execute(
            sa.text(_HEDEF_SQL), {"kaynak": kaynak, "onek": f"{DOGRU_ONEK}%"}
        ).fetchall()
        for sid, eski in satirlar:
            hedefler.append((sid, eski, _yeni_url(eski, crop_onek)))
        _log.info("[0036] %s: onarilacak %s satir", kaynak, len(satirlar))

    if not hedefler:
        _log.info("[0036] onarilacak satir yok -- atlandi")
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
    _log.info("[0036] gorsel URL onarildi: %s satir", len(hedefler))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0036] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0036] geri alindi: %s satir eski URL'sine dondu", len(kayitlar))
    op.drop_table(GUNLUK)
