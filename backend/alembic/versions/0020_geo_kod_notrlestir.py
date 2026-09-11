"""GEO konu agacinin kodlarini yayinevi-bagimsiz hale getirir.

Revision ID: 0020_geo_kod_notrlestir
Revises: 0019_kaynak_adi_tekil
Create Date: 2026-09-11

BAGLAM
------
0017, ilk geometri kitabi (Mikro Orijinal) ithal edilirken `GEO` kokunun
altina 5 unite + 31 yaprak kurdu ve kodlari yayinevinin adiyla
isimlendirdi: `GEO-MIKRO-U1-UCGENDE-ACI` gibi. O gun tek geometri kitabi
vardi, ad sorun degildi.

Ikinci geometri kitabi (345 Yayinlari / UcDortBes, TYT-AYT Geometri 1-2)
geldi. "Ucgende Aci" matematiksel olarak ayni konudur: iki kitabin sorulari
AYNI yapraga baglanmali, yoksa ayni konu ogrenciye iki kez gorunur ve
`total_questions` bolunur. Ama yaprak kodu "MIKRO" diyorsa, icinde iki
yayinevinin sorusu duran bir dugum yanlis yayinevini ima eder.

Urun sahibi 11 Eyl 2026'da karari verdi: once namespace notrlestirilecek,
sonra 345 sorulari ayni yapraklara baglanacak.

NE DEGISIYOR, NE DEGISMIYOR
---------------------------
DEGISEN: yalnizca `topic_hierarchy.code` oneki.

    GEO-MIKRO-U1                 ->  GEO-U1
    GEO-MIKRO-U1-UCGENDE-ACI     ->  GEO-U1-UCGENDE-ACI
    ... (36 dugum; kok `GEO` zaten notr, ona dokunulmuyor)

DEGISMEYEN: `topic_hierarchy.id`. Bu yuzden
`question_bank.primary_topic_id` HIC DOKUNULMUYOR -- 1211 sorunun konu
baglantisi oldugu gibi kaliyor. `name_tr`, `level`, `parent_id`,
`subject_area`, `total_questions` de degismiyor.

11 EYL 2026 OLCUMU (canli DB)
-----------------------------
    GEO alt agaci                     : 37 dugum (1 kok + 5 unite + 31 yaprak)
    yeniden adlandirilacak            : 36
    uretilecek notr kodun DB'de esi   : 0  (cakisma yok)
    en uzun notr kod                  : 28 karakter (topic_hierarchy.code varchar(50))
    GEO yapraklarina bagli soru       : 1211, hepsi tek kaynaktan
                                        (Mikro Orijinal 2025 AYT Geometri)

SAYAC VE VIEW NEDEN YENILENMIYOR
--------------------------------
Ev kalibinda gecisler `_SAYAC_SQL` ile `total_questions`i ve
`refresh_safe_for_beta()` ile materyalize gorunumu tazeler. Burada ikisi de
GEREKSIZ ve bilerek yok: sayac `primary_topic_id` uzerinden sayar, view
`primary_topic_id` tasir; bu gecis hicbir id'ye dokunmuyor. Gereksiz
tazeleme, "bir sey degisti" izlenimi birakan gurultu olurdu.

GERI ALINABILIR
---------------
Degisen her dugumun ONCEKI kodu GUNLUK'e yazilir; downgrade() tam olarak o
kodu geri koyar. Silme yok.

Revizyon adi 23 karakter (sinir 32 -- alembic_version.version_num varchar(32)).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0020_geo_kod_notrlestir"
down_revision: Union[str, None] = "0019_kaynak_adi_tekil"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "geo_kod_notrlestir_gunlugu_0020"
ESKI_ONEK = "GEO-MIKRO-"
YENI_ONEK = "GEO-"
KOD_SINIRI = 50  # topic_hierarchy.code varchar(50)


def _tablo_var(b) -> bool:
    return bool(sa.inspect(b).has_table("topic_hierarchy"))


def _notr(kod: str) -> str:
    return YENI_ONEK + kod[len(ESKI_ONEK) :]


def upgrade() -> None:
    b = op.get_bind()
    if not _tablo_var(b):
        _log.info("[0020] topic_hierarchy yok (taze DB?) -- atlandi")
        return

    satirlar = b.execute(
        sa.text(
            "SELECT id, code FROM topic_hierarchy"
            " WHERE code LIKE :desen ORDER BY code"
        ),
        {"desen": ESKI_ONEK + "%"},
    ).fetchall()
    if not satirlar:
        _log.info("[0020] %s onekli dugum yok -- atlandi", ESKI_ONEK)
        return

    yeni = {sid: _notr(kod) for sid, kod in satirlar}
    uzun = [k for k in yeni.values() if len(k) > KOD_SINIRI]
    if uzun:
        raise RuntimeError(f"[0020] kod siniri asildi: {uzun}")

    # Cakisma: uretilen notr kod BASKA bir dugumde zaten duruyor mu?
    # Duruyorsa yeniden adlandirma sessizce iki konuyu birlestirmeye
    # calisirdi -- bu bir birlestirme gecisi DEGIL, durulur.
    mevcut = {
        r[0]: r[1]
        for r in b.execute(
            sa.text("SELECT code, id FROM topic_hierarchy WHERE code = ANY(:kodlar)"),
            {"kodlar": list(yeni.values())},
        ).fetchall()
    }
    carpisan = {k: v for k, v in mevcut.items() if v not in yeni}
    if carpisan:
        raise RuntimeError(f"[0020] hedef kod baska dugumde dolu: {carpisan}")

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("eski_code", sa.String(), nullable=False),
        sa.Column("yeni_code", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, eski_code, yeni_code)"  # noqa: S608  # nosec B608
            " VALUES (:id, :eski, :yeni)"
        ),
        [{"id": sid, "eski": kod, "yeni": yeni[sid]} for sid, kod in satirlar],
    )
    for sid, _kod in satirlar:
        b.execute(
            sa.text(
                "UPDATE topic_hierarchy SET code = :yeni, updated_at = now()"
                " WHERE id = :id"
            ),
            {"id": sid, "yeni": yeni[sid]},
        )
    _log.info("[0020] %s dugumun kodu yayinevi-bagimsiz hale getirildi", len(satirlar))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0020] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablo_var(b):
        op.drop_table(GUNLUK)
        return

    kayitlar = b.execute(
        sa.text(f"SELECT id, eski_code FROM {GUNLUK}")  # noqa: S608  # nosec B608
    ).fetchall()
    for sid, eski in kayitlar:
        b.execute(
            sa.text(
                "UPDATE topic_hierarchy SET code = :eski, updated_at = now()"
                " WHERE id = :id"
            ),
            {"id": sid, "eski": eski},
        )
    _log.info("[0020] geri alindi: %s dugum eski koduna dondu", len(kayitlar))
    op.drop_table(GUNLUK)
