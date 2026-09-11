"""Bolunmus source_book adini tekillestirir (Aromat Tyt Turkce Model Sorular).

Revision ID: 0019_kaynak_adi_tekil
Revises: 0018_mikro_geo_beta_onay
Create Date: 2026-09-11

BAGLAM
------
`question_metadata.source_book` bu depoda bir etiket degil KIMLIKTIR: toplu
onay/aktiflestirme migration'lari (0011, 0012, 0014, 0016, 0018) hedeflerini
bu kolona gore secer ve ithal scriptlerinin "bu satir baska kitaba ait,
dokunma" korumasi da buna bakar.

11 Eyl 2026'da tum kolon tarandi: 192 farkli deger, 9407 satir. Degerler
Turkce katlanip (c-cedilla -> c vb.) kucuk harfe indirilip alfanumerik
disi karakterler atilarak normalize edildiginde TEK BIR CAKISMA cikti --
ayni kitap iki yazimla bolunmus, fark tek harfte:

    "Aromat Tyt T(U+00FC)rk c  e Model Sorular"   8 satir  -- duz 'c' (U+0063)
    "Aromat Tyt T(U+00FC)rk c- e Model Sorular"   1 satir  -- 'c' cedilla (U+00E7)

Hangisinin dogru oldugu tahmin edilmedi, OLCULDU: diskteki kitap klasoru
`veriseti/zkitap/screenshots/` altinda duz 'c' ile yazili
(8 satirlik yazimla birebir). Tek satirlik olan dizgi hatasidir.

NEDEN ONEMLI
------------
Bolunmus ad, source_book ile filtreleyen HER korumada sessiz bir delik acar:
koruma "benim kitabim" derken 9 satirin 1'ini disarida birakir. Bu satir
o kitabin toplu onayindan, toplu pasiflestirmesinden ve yabanci-satir
korumasindan kacar. Sorun 1 satirlik degil, SINIF olarak onemlidir; bu
yuzden ayni turda commit'le birlikte scripts/kitap/kaynak_sozlesmesi.py
adlandirma sozlesmesini ve tests/e2e/test_kaynak_sozlesmesi.py da "iki
farkli yazim ayni kitaba cozulmesin" bekcisini getiriyor.

KAPSAM
------
YALNIZCA source_book kolonu degisir. Soru metni, sikler, cevap, konu
baglantisi, is_active, kapi durumu -- hicbirine dokunulmaz. Silme yok.

GERI ALINABILIR
---------------
Degisen her satirin ONCEKI source_book degeri GUNLUK'e yazilir; downgrade()
tam olarak o degeri geri koyar.

Revizyon adi 20 karakter (sinir 32 -- alembic_version.version_num varchar(32)).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0019_kaynak_adi_tekil"
down_revision: Union[str, None] = "0018_mikro_geo_beta_onay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "kaynak_adi_tekil_gunlugu_0019"

# Turkce harfler kod noktasi olarak yazilir -- kaynak dosya ASCII kalir.
_GOVDE = "Aromat Tyt T" + chr(0x00FC) + "rk{0}e Model Sorular"
YANLIS = _GOVDE.format(chr(0x00E7))  # 'c' cedilla -- 1 satir, dizgi hatasi
DOGRU = _GOVDE.format("c")  # duz 'c' -- 8 satir, diskteki klasor adi

# (yanlis, dogru) ciftleri. Bugun tek cift var; liste, ileride cikarsa
# ayni gunluk/downgrade makinesinin yeniden kullanilabilmesi icin.
BIRLESTIRME: tuple[tuple[str, str], ...] = ((YANLIS, DOGRU),)


def _tablolar_var(b) -> bool:
    return bool(sa.inspect(b).has_table("question_metadata"))


def upgrade() -> None:
    b = op.get_bind()
    if not _tablolar_var(b):
        _log.info("[0019] question_metadata yok (taze DB?) -- atlandi")
        return

    hedef: list[tuple[str, str, str]] = []
    for yanlis, dogru in BIRLESTIRME:
        idler = (
            b.execute(
                sa.text(
                    "SELECT id FROM question_metadata WHERE source_book = :yanlis"
                ),
                {"yanlis": yanlis},
            )
            .scalars()
            .all()
        )
        if not idler:
            _log.info("[0019] bolunmus yazim bulunamadi -- atlandi")
            continue
        varis = b.execute(
            sa.text(
                "SELECT count(*) FROM question_metadata WHERE source_book = :dogru"
            ),
            {"dogru": dogru},
        ).scalar_one()
        if varis == 0:
            # Hedef yazim yoksa birlestirme degil, yeniden adlandirma olurdu.
            # Sessizce yapmak yerine durulur: olcum degismis demektir.
            _log.warning(
                "[0019] hedef yazim DB'de yok -- birlestirme atlandi (%s satir)",
                len(idler),
            )
            continue
        hedef.extend((sid, yanlis, dogru) for sid in idler)

    if not hedef:
        return

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("onceki_source_book", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, onceki_source_book)"  # noqa: S608  # nosec B608
            " VALUES (:id, :eski)"
        ),
        [{"id": sid, "eski": yanlis} for sid, yanlis, _ in hedef],
    )
    for sid, _, dogru in hedef:
        b.execute(
            sa.text(
                "UPDATE question_metadata SET source_book = :dogru WHERE id = :id"
            ),
            {"id": sid, "dogru": dogru},
        )
    _log.info("[0019] %s satirin source_book yazimi tekillestirildi", len(hedef))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0019] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not _tablolar_var(b):
        op.drop_table(GUNLUK)
        return

    kayitlar = b.execute(
        sa.text(
            f"SELECT id, onceki_source_book FROM {GUNLUK}"  # noqa: S608  # nosec B608
        )
    ).fetchall()
    for sid, eski in kayitlar:
        b.execute(
            sa.text("UPDATE question_metadata SET source_book = :eski WHERE id = :id"),
            {"id": sid, "eski": eski},
        )
    _log.info("[0019] geri alindi: %s satir eski yazimina dondu", len(kayitlar))
    op.drop_table(GUNLUK)
