"""345 2025 AYT Kimya kitabinin eski hat source_book yazimini ASCII'ye cevirir

Revision ID: 0050_kim345ayt_kaynak_adi
Revises: 0049_kim345ayt_agac
Create Date: 2026-09-25

NEDEN
-----
`question_metadata.source_book` bu depoda bir etiket degil KIMLIKtir
(bkz. scripts/kitap/kaynak_sozlesmesi.py). Yeni ithal (kim345ayt_ithal.py)
ASCII adi kullanir:

    "345 2025 AYT Kimya Soru Bankasi"

DB'de bu kitaptan eski hattan gelen 161 satir var (43'u exam_type AYT,
118'i exam_type TYT) ve yazimi:

    "345 2025 Ayt Kimya Soru Bankas<U+0131>"   <- 'Ayt', dotless-i

Iki yazim `normalize_anahtar` ile AYNI anahtara cozuluyor; yan yana
kalirlarsa kitap IKIYE BOLUNUR ve source_book ile filtreleyen her koruma
sessizce delik birakir (0043 / 0046 ile ayni durum).

OLCULDU (25 Eyl 2026, yerel DB): ayni anahtara cozulen TEK deger eski
yazimdir; yani bu bir AD DUZELTMESIDIR, birlestirme degil. Ayni yayinevinin
'345 2024 Ayt Kimya Soru Bankas<U+0131>' (202 satir, onceki baski),
'345 2025 Tyt Kimya Soru Bankas<U+0131>' ve '345 Tyt Kimya Soru Bankas<U+0131>'
FARKLI anahtara cozuluyor, onlara dokunulmaz.

KAPSAM
------
Yalnizca `question_metadata.source_book` kolonu. Satirlarin metni,
sikleri, cevabi, konusu, exam_type'i (118 satirin 'TYT' etiketi dahil --
ayri karar), is_active/is_public durumu ve pipeline_metadata alani
DEGISMEZ. Guncelleme tam eslesme ile yapilir.

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

revision: str = "0050_kim345ayt_kaynak_adi"
down_revision: Union[str, None] = "0049_kim345ayt_agac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "kim345ayt_kaynak_adi_gunlugu_0050"

# Kaynak dosyasi ASCII kalsin diye Turkce harf chr() ile yazilir.
ESKI = "345 2025 Ayt Kimya Soru Bankas" + chr(0x0131)
YENI = "345 2025 AYT Kimya Soru Bankasi"


def _tablo_var(b) -> bool:
    # Acik anotasyon: depo kokundeki pyproject.toml `warn_return_any = true`.
    var: bool = sa.inspect(b).has_table("question_metadata")
    return var


def upgrade() -> None:
    b = op.get_bind()
    if not _tablo_var(b):
        _log.info("[0050] question_metadata yok (taze DB?) -- atlandi")
        return

    hedef = [
        r[0]
        for r in b.execute(
            sa.text("SELECT id FROM question_metadata WHERE source_book = :eski"),
            {"eski": ESKI},
        ).fetchall()
    ]
    if not hedef:
        _log.info("[0050] eski yazimla satir yok -- atlandi")
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
    _log.info("[0050] source_book yazimi duzeltildi: %s satir", len(hedef))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0050] %s yok -- downgrade atlandi", GUNLUK)
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
    _log.info("[0050] geri alindi: %s satir eski yazimina dondu", len(kayitlar))
    op.drop_table(GUNLUK)
