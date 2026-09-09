"""Kalibrasyon bayragi sozlesmesi -- 9 Eyl 2026 canli olcumu.

KUSUR
-----
question_statistics'te 20 satir is_calibrated=true idi; hepsinde
calibration_sample_size=0, irt_n_responses=0, irt_calibrated=false,
times_asked<=1. Kaynak: core/irt_daemon.py (devre disi) metin
ozelliklerinden "kalibre" edip bayragi yanit verisi olmadan true yapiyordu.

SOZLESME (alembic/versions/0008_kalibrasyon_bayragi.py)
------------------------------------------------------
    is_calibrated = true  =>  calibration_sample_size > 0
                              VEYA irt_n_responses > 0

Bir bayragin "kalibre" demesi icin arkasinda en az bir gercek yanit
orneklemi olmali. Bayrak sifirlamasi 0008 ile yapildi; bu test geri
gelmesini yakalar (sinav motoru ve kalibrasyon raporlari bayraga guvenir).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def baglanti():
    dsn = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)
    motor = create_async_engine(dsn, poolclass=NullPool)
    try:
        conn = await motor.connect()
    except Exception as exc:  # DB ayakta degil -- kapiyi fail-close etme
        await motor.dispose()
        pytest.skip(f"DB erisilemiyor: {type(exc).__name__}")
    try:
        yield conn
    finally:
        await conn.close()
        await motor.dispose()


async def test_kalibre_bayragi_orneklemsiz_olamaz(baglanti) -> None:
    """is_calibrated=true olan her satirin en az bir yanit orneklemi olmali."""
    sonuc = await baglanti.execute(
        text(
            """
            SELECT id, calibration_sample_size, irt_n_responses,
                   irt_method, times_asked
              FROM question_statistics
             WHERE is_calibrated IS TRUE
               AND COALESCE(calibration_sample_size, 0) = 0
               AND COALESCE(irt_n_responses, 0) = 0
             ORDER BY id
             LIMIT 25
            """
        )
    )
    orneklemsiz = sonuc.fetchall()
    if orneklemsiz:
        dokum = "\n".join(
            f"  {r.id}  orneklem={r.calibration_sample_size}/{r.irt_n_responses}"
            f"  yontem={r.irt_method}  soruldu={r.times_asked}"
            for r in orneklemsiz
        )
        mesaj = (
            f"{len(orneklemsiz)} satir orneklemsiz is_calibrated=true tasiyor "
            "(0008 sozlesmesi: bayrak => orneklem > 0):\n" + dokum
        )
        pytest.fail(mesaj)
