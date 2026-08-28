"""Kalite kapısı bakım görevleri — mv_safe_for_beta yenileme.

NEDEN
-----
Öğrenci-yüzü soru seçimi `mv_safe_for_beta` matview'ini okur (bkz.
core/quality_gate.py). Matview `v_safe_for_beta`'nın anlık görüntüsüdür;
zamanlı yenilenmezse bayatlar. Bayatlığın iki yönü var:

  - yeni onaylanan soru geç görünür              -> zararsız
  - demote edilen soru bir süre daha servis edilir -> TEHLİKELİ

İkinci yön, ".claude/rules/testing.md Ders #31"in (status yargısı != servis
dışı) zaman-penceresine dönüşmüş hâlidir. Bu yüzden yenileme iki tetikle
çalışır: gecelik beat (emniyet ağı) + küratör yargısından sonra (asıl tetik).

NEDEN SECURITY DEFINER FONKSİYON ÇAĞIRIYORUZ
--------------------------------------------
Uygulama DB'ye `kiro2_app` (non-superuser) ile bağlanıyor; matview'in sahibi
`postgres`. `REFRESH MATERIALIZED VIEW` SAHİPLİK ister, dolayısıyla worker
matview'i doğrudan yenileyemez. Migration `refresh_safe_for_beta()` adında
SECURITY DEFINER bir fonksiyon yaratıp `kiro2_app`'e yalnız EXECUTE veriyor.
(bkz. alembic/versions/20260727_mv_safe_for_beta.py)

`REFRESH ... CONCURRENTLY`'nin plpgsql fonksiyonu ve açık transaction içinde
çalıştığı canlı PG 18.1'de deneyle doğrulandı — yaygın "transaction bloğunda
çalışmaz" inanışı CREATE/DROP INDEX CONCURRENTLY için geçerli, REFRESH için
değil.

NEDEN ADVISORY LOCK
-------------------
Küratör bir oturumda düzinelerce yargı verir. Her yargı ayrı bir yenileme
kuyruğa alırsa, ~2,3 saniyelik tam yeniden doldurma arka arkaya onlarca kez
koşar. `pg_try_advisory_xact_lock` ile ilk görev kilidi alır, aynı anda
uyanan diğerleri ANINDA atlar — yani patlama tek yenilemeye indirgenir.
Transaction-scoped varyant bilinçli: bağlantı havuza dönerken kilit sızmaz.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from core.celery_app import celery_app
except ImportError:  # test/CLI ortamında broker yokken import kırılmasın
    celery_app = None  # type: ignore[assignment]


# Advisory lock anahtarı. Sabit bir int64; hashtext yerine elle seçildi ki
# PostgreSQL sürümleri arasında hash davranışı değişse bile kayması imkânsız
# olsun. Başka bir advisory lock kullanan yer eklenirse bu tabloyu büyüt.
_REFRESH_LOCK_KEY = 727_20260727


async def _refresh_safe_pool_async() -> dict[str, Any]:
    from sqlalchemy import text

    from core.database import get_db_session_context

    async with get_db_session_context() as db:
        got_lock = (
            await db.execute(
                text("SELECT pg_try_advisory_xact_lock(:k)"),
                {"k": _REFRESH_LOCK_KEY},
            )
        ).scalar()

        if not got_lock:
            # Başka bir yenileme koşuyor. Bu görevin işi zaten o yenilemeyle
            # yapılmış olacak — beklemek yerine atla (küratör patlamasını
            # tek yenilemeye indirgeyen mekanizma tam olarak bu).
            logger.info("safe_pool_refresh_skipped: başka yenileme sürüyor")
            return {"refreshed": False, "reason": "lock_busy"}

        await db.execute(text("SELECT refresh_safe_for_beta()"))
        await db.commit()

        row_count = (
            await db.execute(text("SELECT count(*) FROM mv_safe_for_beta"))
        ).scalar()

    logger.info("safe_pool_refresh_ok: %s satır", row_count)
    return {"refreshed": True, "rows": row_count}


def _refresh_safe_pool_impl() -> dict[str, Any]:
    return asyncio.run(_refresh_safe_pool_async())


def schedule_safe_pool_refresh(*, countdown: int = 60) -> None:
    """Kalite yargısı değişince yenilemeyi kuyruğa al (fire-and-forget).

    Çağıran uçları (küratör verdict, admin CRUD) ASLA kırmamalı: broker
    erişilemezse yalnız log düşer. Yenileme gecikirse en kötü ihtimalle
    gecelik beat yakalar.

    `countdown` bilinçli: küratörün ardışık yargıları tek pencerede toplanır,
    uyanan görevlerden yalnız biri advisory lock'ı alır.
    """
    if celery_app is None:
        return
    try:
        celery_app.send_task(
            "tasks.quality_gate_tasks.refresh_safe_pool",
            countdown=countdown,
        )
    except Exception as exc:  # broker down / redis timeout
        logger.warning("safe_pool_refresh_schedule_failed: %s", exc)


if celery_app is not None:

    @celery_app.task(
        name="tasks.quality_gate_tasks.refresh_safe_pool",
        bind=True,
        max_retries=3,
    )
    def refresh_safe_pool(self):
        """mv_safe_for_beta'yı CONCURRENTLY yenile."""
        try:
            return _refresh_safe_pool_impl()
        except Exception as exc:
            logger.error("safe_pool_refresh_failed: %s", exc)
            raise self.retry(exc=exc, countdown=300) from exc
