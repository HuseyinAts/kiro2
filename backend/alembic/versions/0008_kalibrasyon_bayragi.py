"""Orneklemsiz is_calibrated bayraklari sifirlandi (gunluk tablosuyla geri alinabilir)

Revision ID: 0008_kalibrasyon_bayragi
Revises: 0007_mat_geo_geometri
Create Date: 2026-09-09

KARAR (docs/veritabani-denetimi-20260909.md madde 3 / capa seti)
-----------------------------------------------------------------
Havuzda is_anchor=true soru yok, 510 yanit var, en cok sorulan soru 10 kez
sorulmus: IRT kalibrasyonu icin yeterli orneklem hicbir soruda yok. Buna
ragmen 20 question_statistics satiri is_calibrated=true tasiyor; hepsinde
calibration_sample_size=0, irt_n_responses=0, irt_calibrated=false,
irt_method='bootstrap_difficulty_prior', times_asked<=1.

Kaynak olculdu: core/irt_daemon.py (baslatilmasi core/application.py'de
yorum satirinda, calismiyor) metin ozelliklerinden "kalibre" ediyor ve
bayragi yanit verisi olmadan true yapiyordu. Bayrak, sinav motorunun
ve kalibrasyon raporlarinin "guvenilir b parametresi" varsayimi icin
kullanildigindan, orneklemsiz true degerler yanlis pozitiftir.

NE DEGISIR
----------
1. is_calibrated_sifirlama_gunlugu tablosu olusturulur (id, zaman).
2. is_calibrated=true VE orneklem sifir (calibration_sample_size=0 VE
   irt_n_responses=0) olan satirlarin id'leri gunluge yazilir.
3. Bu satirlarda is_calibrated=false yapilir. irt_method ve diger
   alanlara DOKUNULMAZ (bayrak disi hicbir bilgi kaybolmaz).

Sozlesme (tests/db/test_kalibrasyon_bayragi.py):
  is_calibrated=true  =>  calibration_sample_size>0 VEYA irt_n_responses>0
Servis tarafinda services/question_bank_service.py::calibrate_question_irt
artik sample_size<1 ile cagrilamaz (IRTValidationError).

GERI ALINABILIRLIK
------------------
downgrade gunlukteki id'lerde is_calibrated=true yapar ve gunlugu dusurur.
Gunluk bos/yoksa (taze CI) her iki yon de is-yapmaz ve bunu loglar.
"""

import logging
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0008_kalibrasyon_bayragi"
down_revision: Union[str, None] = "0007_mat_geo_geometri"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

GUNLUK = "is_calibrated_sifirlama_gunlugu"

# Orneklemsiz "kalibre" satir: bayrak true ama iki orneklem sayaci da sifir.
_ORNEKLEMSIZ_KOSUL = (
    "is_calibrated IS TRUE "
    "AND COALESCE(calibration_sample_size, 0) = 0 "
    "AND COALESCE(irt_n_responses, 0) = 0"
)


def _tablo_var(b, ad: str) -> bool:
    return bool(sa.inspect(b).has_table(ad))


def upgrade() -> None:
    b = op.get_bind()
    if not _tablo_var(b, "question_statistics"):
        _log.info("[0008] question_statistics yok (taze DB?) -- atlandi")
        return

    op.create_table(
        GUNLUK,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "sifirlama_zamani",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    yazilan = b.execute(
        sa.text(
            f"INSERT INTO {GUNLUK} (id) "  # noqa: S608 -- sabit tablo adi  # nosec B608
            f"SELECT id FROM question_statistics WHERE {_ORNEKLEMSIZ_KOSUL}"
        )
    ).rowcount
    sifirlanan = b.execute(
        sa.text(
            "UPDATE question_statistics SET is_calibrated = FALSE "  # noqa: S608 -- sabit kosul  # nosec B608
            f"WHERE {_ORNEKLEMSIZ_KOSUL}"
        )
    ).rowcount
    _log.info(
        "[0008] %s satir gunluge yazildi, %s bayrak sifirlandi", yazilan, sifirlanan
    )


def downgrade() -> None:
    b = op.get_bind()
    if not _tablo_var(b, GUNLUK):
        _log.info("[0008] %s yok -- geri alinacak bir sey yok", GUNLUK)
        return
    geri = b.execute(
        sa.text(
            "UPDATE question_statistics s SET is_calibrated = TRUE "  # noqa: S608 -- sabit tablo adi  # nosec B608
            f"FROM {GUNLUK} g WHERE g.id = s.id"
        )
    ).rowcount
    op.drop_table(GUNLUK)
    _log.info("[0008] %s bayrak geri alindi, %s dusuruldu", geri, GUNLUK)
