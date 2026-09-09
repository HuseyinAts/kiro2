"""Iki supheli cozucu-anahtarli sorunun karari: 1dd54e6a pasif, dab0707f kalir

Revision ID: 0010_supheli_anahtar
Revises: 0009_etiket_duzeltme
Create Date: 2026-09-09

0009'da kapidan gecen 31 `bayes_*` anahtarli sorunun tamami elle cozulmus,
3'u kesin kusurlu diye pasife alinmis, 2'si "supheli" diye kullaniciya
birakilmisti. Kullanici karari bana devretti (9 Eyl 2026, gece); ikisi
yeniden okundu:

- 1dd54e6a (TARIH, anahtar C "I ve III", bayes_1of2 guven %54): Tevhid-i
  Tedrisat Kanunu'nun hedefi egitimde birlik / dusunce ve duyguda birlesmis
  toplum (I). "Yerli ureticiyi korumak" (II) iktisat; "rejim sorununu
  ortadan kaldirmak" (III) halifeligin kaldirilmasi / Cumhuriyet'in ilanina
  atfedilir, egitim kanununa degil. Dogru sik A ("Yalniz I"). Iki bagimsiz
  sinyal (tek-cozucu %54 + bu okuma) uyusmuyor -> PASIF (silinmez), insan
  incelemesine kadar servis edilmez.
- dab0707f (TURKCE, anahtar B, %54): "pencere acar" cumlesi II'den sonra da
  (III'un "distan goruruz" karsitligini hazirlar) III'ten sonra da okunabilir;
  anahtar B savunulabilir, yanlis oldugu GOSTERILEMIYOR -> AKTIF KALIR.

Gunluk: 0009'un etiket_duzeltme_gunlugu_0009 tablosuna (id, 'is_active',
'true') satiri; downgrade satiri geri alip siler. 0009 downgrade edilmisse
(tablo yoksa) is-yapmaz ve loglar.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0010_supheli_anahtar"
down_revision: Union[str, None] = "0009_etiket_duzeltme"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "etiket_duzeltme_gunlugu_0009"
_PASIF = "1dd54e6a-55d3-55af-87b1-60a7d31f8f9b"


def upgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0010] %s yok (0009 uygulanmamis?) -- atlandi", GUNLUK)
        return
    aktif = b.execute(
        sa.text("SELECT is_active FROM question_bank WHERE id = :id"), {"id": _PASIF}
    ).scalar()
    if not aktif:
        _log.info("[0010] %s zaten pasif ya da yok -- atlandi", _PASIF[:8])
        return
    b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id, alan, eski_deger) "  # noqa: S608 -- sabit tablo adi  # nosec B608
            "VALUES (:id, 'is_active', 'true') ON CONFLICT DO NOTHING"
        ),
        {"id": _PASIF},
    )
    b.execute(
        sa.text(
            "UPDATE question_bank SET is_active = FALSE, updated_at = now() WHERE id = :id"
        ),
        {"id": _PASIF},
    )
    b.execute(
        sa.text(
            "UPDATE topic_hierarchy t SET total_questions = total_questions - 1, "
            "updated_at = now() FROM question_bank q "
            "WHERE q.id = :id AND t.id = q.primary_topic_id AND t.total_questions > 0"
        ),
        {"id": _PASIF},
    )
    _log.info("[0010] %s pasife alindi", _PASIF[:8])


def downgrade() -> None:
    b = op.get_bind()
    if not sa.inspect(b).has_table(GUNLUK):
        _log.info("[0010] %s yok -- geri alinacak bir sey yok", GUNLUK)
        return
    var = b.execute(
        sa.text(
            f"SELECT 1 FROM {GUNLUK} WHERE id = :id AND alan = 'is_active'"  # noqa: S608 -- sabit tablo adi  # nosec B608
        ),
        {"id": _PASIF},
    ).scalar()
    if not var:
        _log.info("[0010] gunluk kaydi yok -- atlandi")
        return
    b.execute(
        sa.text(
            "UPDATE question_bank SET is_active = TRUE, updated_at = now() WHERE id = :id"
        ),
        {"id": _PASIF},
    )
    b.execute(
        sa.text(
            "UPDATE topic_hierarchy t SET total_questions = total_questions + 1, "
            "updated_at = now() FROM question_bank q "
            "WHERE q.id = :id AND t.id = q.primary_topic_id"
        ),
        {"id": _PASIF},
    )
    b.execute(
        sa.text(
            f"DELETE FROM {GUNLUK} WHERE id = :id AND alan = 'is_active'"  # noqa: S608 -- sabit tablo adi  # nosec B608
        ),
        {"id": _PASIF},
    )
    _log.info("[0010] %s yeniden aktif", _PASIF[:8])
