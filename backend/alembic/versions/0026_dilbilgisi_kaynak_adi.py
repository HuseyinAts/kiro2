"""Dilbilgisi kitabinin source_book yazimini ASCII sozlesmesine cevirir.

Revision ID: 0026_dilbilgisi_kaynak_adi
Revises: 0025_dilbilgisi_konu_agaci
Create Date: 2026-09-16

OLCUM
-----
Canli DB (16 Eyl 2026): `question_metadata.source_book` degeri

    "Aktif Ogrenme Tyt Dilbilgisi Soru Bankas" + U+0131 + " 2025"   17 satir

Tek sozlesme disi karakter U+0131 (noktasiz i), "Bankasi" sozcugunde.
Satirlar eski gemini hattindan (kiro2_batch_v4.14e) kalma.

NEDEN DEGISMELI
---------------
scripts/kitap/kaynak_sozlesmesi.py'nin ADLANDIRMA SOZLESMESI maddesi 1:
source_book yalnizca yazdirilabilir ASCII olabilir -- bu ad SQL parametresi,
dosya adi, log satiri ve rapor basligi olarak dolasir. `kaynak_adi_dogrula`
U+0131 tasiyan adi REDDEDER, dolayisiyla bu kitap KAYNAK_KAYITLARI'na
sozlesmeye uygun haliyle eklenemez ve `ayristir` cagrilamaz.

Bu kitabin yeni ithali (537 soru) ASCII adla yazilir. Iki yazim yan yana
kalirsa:
  * normalize_anahtar ikisini de "aktifogrenmetytdilbilgisisorubankasi2025"
    diye cozer -- yani AYNI KITABIN IKI YAZIMI olur; 0019'un kapattigi
    delik yeniden acilir,
  * tests/e2e/test_kaynak_sozlesmesi.py::test_iki_yazim_ayni_kitaba_cozulmuyor
    KIRMIZI olur,
  * source_book ile filtreleyen her koruma 17 satiri disarida birakir.

0019'DAN FARKI
--------------
0019 bir BIRLESTIRME idi: hedef yazim DB'de zaten vardi ve 0019 hedef
yoksa bilerek DURUYOR ("birlestirme degil, yeniden adlandirma olurdu").
Burada hedef yazim DB'de YOK; bu bilincli bir YENIDEN ADLANDIRMA ve
gerekcesi yukarida yazili. 0019'un makinesi degil, ayni ilkesi kullanildi.

DOGRU YAZIM TAHMIN EDILMEDI, OLCULDU
------------------------------------
Diskteki kitap klasoru:
    veriseti/zkitap/screenshots/Aktif Ogrenme Tyt Dilbilgisi Soru Bankas<U+0131> 2025
Bu adin ASCII katlanmasi (kaynak_sozlesmesi.katla) tam olarak hedef yazimi
verir. Baska hicbir sey degistirilmedi: "Tyt" buyuk harfe cevrilmedi,
sozcuk sirasi korundu -- tek karakterlik fark.

KAPSAM
------
YALNIZCA source_book kolonu degisir. Soru metni, sikler, cevap, konu
baglantisi, is_active, review_status, kapi durumu -- HICBIRINE dokunulmaz.
Silme yok. Kullanicinin "mevcut 17 satira dokunma" karari icerik ve
aktiflik eksenindedir; burada degisen yalnizca kimlik kolonunun yazimidir.

GERI ALINABILIR
---------------
Degisen her satirin ONCEKI source_book degeri GUNLUK'e yazilir; downgrade()
tam olarak o degeri geri koyar.

Revizyon adi 24 karakter (sinir 32 -- alembic_version.version_num varchar(32)).
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0026_dilbilgisi_kaynak_adi"
down_revision: Union[str, None] = "0025_dilbilgisi_konu_agaci"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "dilbilgisi_kaynak_adi_gunlugu_0026"

# Turkce harf kod noktasi olarak yazilir -- kaynak dosya ASCII kalir.
ESKI = "Aktif Ogrenme Tyt Dilbilgisi Soru Bankas" + chr(0x0131) + " 2025"
YENI = "Aktif Ogrenme Tyt Dilbilgisi Soru Bankasi 2025"


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table("question_metadata"):
        _log.info("[0026] question_metadata yok (taze DB?) -- atlandi")
        return

    idler = (
        b.execute(
            sa.text("SELECT id FROM question_metadata WHERE source_book = :eski"),
            {"eski": ESKI},
        )
        .scalars()
        .all()
    )
    if not idler:
        _log.info("[0026] sozlesme disi yazim bulunamadi -- atlandi")
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
        [{"id": sid, "eski": ESKI} for sid in idler],
    )
    b.execute(
        sa.text(
            "UPDATE question_metadata SET source_book = :yeni "
            "WHERE source_book = :eski"
        ),
        {"eski": ESKI, "yeni": YENI},
    )
    _log.info("[0026] %s satirin source_book yazimi ASCII'ye cevrildi", len(idler))


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0026] %s yok -- downgrade atlandi", GUNLUK)
        return
    if not sa.inspect(b).has_table("question_metadata"):
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
    _log.info("[0026] geri alindi: %s satir eski yazimina dondu", len(kayitlar))
    op.drop_table(GUNLUK)
