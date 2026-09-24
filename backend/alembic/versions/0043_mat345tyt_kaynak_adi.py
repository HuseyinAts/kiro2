"""345 2025 TYT Matematik kitabinin eski hat source_book yazimini ASCII'ye cevirir

Revision ID: 0043_mat345tyt_kaynak_adi
Revises: 0042_mat345tyt_agac
Create Date: 2026-09-24

NEDEN
-----
`question_metadata.source_book` bu depoda bir etiket degil KIMLIKtir
(bkz. scripts/kitap/kaynak_sozlesmesi.py). Yeni ithal (mat345tyt_ithal.py)
ASCII adi kullanir:

    "345 2025 TYT Matematik Soru Bankasi"

DB'de bu kitaptan eski hattan gelen 12 satir var ve yazimi:

    "345 2025 Tyt Matematik Soru Bankas<U+0131>"   <- 'Tyt', dotless-i

Iki yazim `normalize_anahtar` ile AYNI anahtara cozuluyor; yan yana
kalirlarsa kitap IKIYE BOLUNUR ve source_book ile filtreleyen her koruma
sessizce delik birakir (0019 Aromat, 0030 Bilgi Sarmal ile ayni durum).

OLCULDU (24 Eyl 2026, yerel DB): ayni anahtara cozulen TEK deger eski
yazimdir; yani bu bir AD DUZELTMESIDIR, birlestirme degil. Ayni yayinevinin
'345 2024 Tyt Matematik Soru Bankasi' (18 satir) ve '345 2025 Ayt Matematik
Soru Bankasi' (11 satir) FARKLI anahtara cozuluyor, onlara dokunulmaz.

KAPSAM
------
Yalnizca `question_metadata.source_book` kolonu. Satirlarin metni,
sikleri, cevabi, konusu, is_active/is_public durumu ve pipeline_metadata
alani DEGISMEZ. Guncelleme tam eslesme ile yapilir.

GERI ALINABILIR
---------------
Degisen her satirin id'si ve onceki degeri GUNLUK'e yazilir; downgrade tam
olarak onlari geri koyar.

Revizyon adi 25 karakter (sinir 32).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0043_mat345tyt_kaynak_adi"
down_revision: Union[str, None] = "0042_mat345tyt_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "mat345tyt_kaynak_adi_gunlugu_0043"

# Kaynak dosyasi ASCII kalsin diye Turkce harf chr() ile yazilir.
ESKI = "345 2025 Tyt Matematik Soru Bankas" + chr(0x0131)
YENI = "345 2025 TYT Matematik Soru Bankasi"


def _tablo_var(b) -> bool:
    # Acik anotasyon: depo kokundeki pyproject.toml `warn_return_any = true`.
    var: bool = sa.inspect(b).has_table("question_metadata")
    return var


def upgrade() -> None:
    b = op.get_bind()
    if not _tablo_var(b):
        _log.info("[0043] question_metadata yok (taze DB?) -- atlandi")
        return

    hedef = [
        r[0]
        for r in b.execute(
            sa.text("SELECT id FROM question_metadata WHERE source_book = :eski"),
            {"eski": ESKI},
        ).fetchall()
    ]
    if not hedef:
        _log.info("[0043] eski yazimla satir yok -- atlandi")
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
    _log.info("[0043] source_book yazimi duzeltildi: %s satir", len(hedef))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0043] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0043] geri alindi: %s satir eski yazimina dondu", len(kayitlar))
    op.drop_table(GUNLUK)
