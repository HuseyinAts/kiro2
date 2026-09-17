"""Bilgi Sarmal TYT Turkce kitabinin source_book yazimini ASCII'ye cevirir

Revision ID: 0030_bs_kaynak_adi
Revises: 0029_bilgi_sarmal_agac
Create Date: 2026-09-17

NEDEN
-----
`question_metadata.source_book` bu depoda bir etiket degil KIMLIKtir
(bkz. scripts/kitap/kaynak_sozlesmesi.py): aktiflestirme migration'lari ve
ithal scriptlerinin "yabanci satir" korumasi hedeflerini bu kolona gore
secer. Sozlesme yeni ithaller icin YALNIZ ASCII ve ardisik cift bosluk
yasagi getiriyor.

DB'de bu kitaptan eski hattan gelen 13 satir var ve yazimi:

    "Bilgi Sarmal  Tyt Turkce Soru Bankasi"   <- iki bosluk, u-umlaut, dotless-i

Yeni ithal ASCII adi kullanacak. Iki yazim ayni kolonda yan yana kalirsa
kitap IKIYE BOLUNUR ve source_book ile filtreleyen her koruma sessizce
delik birakir -- 0019'un birlestirdigi "Aromat" ciftliginin aynisi.

OLCULDU (17 Eyl 2026, canli DB): `normalize_anahtar` (Turkce katlama +
kucuk harf + alfanumerik disi atma) ile ayni anahtara cozulen TEK deger
eski yazimdir; yani bu bir AD DUZELTMESIDIR, birlestirme degil. Ayni
yayinevinin diger Turkce kitaplari ("... 2022 2023", "... 2024") yil
sonekleri yuzunden FARKLI anahtara cozuluyor, onlara dokunulmaz.

KAPSAM
------
Yalnizca `question_metadata.source_book` kolonu. Satirlarin metni,
sikleri, cevabi, konusu, is_active/is_public durumu ve pipeline_metadata
alani DEGISMEZ. Guncelleme tam eslesme ile yapilir; baska hicbir yazim
etkilenmez.

GERI ALINABILIR
---------------
Degisen her satirin id'si ve onceki degeri GUNLUK'e yazilir; downgrade tam
olarak onlari geri koyar.

Revizyon adi 17 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0030_bs_kaynak_adi"
down_revision: Union[str, None] = "0029_bilgi_sarmal_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "bilgi_sarmal_kaynak_adi_gunlugu_0030"

# Kaynak dosyasi ASCII kalsin diye Turkce harfler chr() ile yazilir.
ESKI = "Bilgi Sarmal  Tyt T" + chr(0x00FC) + "rkce Soru Bankas" + chr(0x0131)
YENI = "Bilgi Sarmal Tyt Turkce Soru Bankasi"


def _tablo_var(b) -> bool:
    return sa.inspect(b).has_table("question_metadata")


def upgrade() -> None:
    b = op.get_bind()
    if not _tablo_var(b):
        _log.info("[0030] question_metadata yok (taze DB?) -- atlandi")
        return

    hedef = [
        r[0]
        for r in b.execute(
            sa.text("SELECT id FROM question_metadata WHERE source_book = :eski"),
            {"eski": ESKI},
        ).fetchall()
    ]
    if not hedef:
        _log.info("[0030] eski yazimla satir yok -- atlandi")
        return

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_kaynak", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, onceki_kaynak) "  # noqa: S608  # nosec B608
            "VALUES (:id, :eski)"
        ),
        [{"id": i, "eski": ESKI} for i in hedef],
    )
    b.execute(
        sa.text(
            "UPDATE question_metadata SET source_book = :yeni WHERE id = ANY(:idler)"
        ),
        {"yeni": YENI, "idler": hedef},
    )
    _log.info("[0030] source_book yazimi duzeltildi: %s satir", len(hedef))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0030] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablo_var(b):
        op.drop_table(GUNLUK)
        return
    kayitlar = b.execute(
        sa.text(f"SELECT id, onceki_kaynak FROM {GUNLUK}")  # noqa: S608  # nosec B608
    ).fetchall()
    for sid, eski in kayitlar:
        b.execute(
            sa.text("UPDATE question_metadata SET source_book = :eski WHERE id = :id"),
            {"id": sid, "eski": eski},
        )
    _log.info("[0030] geri alindi: %s satir eski yazimina dondu", len(kayitlar))
    op.drop_table(GUNLUK)
