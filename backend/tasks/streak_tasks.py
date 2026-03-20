"""
Streak kontrol Celery tasklari.

FAZ-2.5 Gorev 2.5.1 — Master Plan v2.0
Her gece 00:05'te calisir, streak'leri gunceller.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

try:
    from core.celery_app import celery_app
except ImportError:
    celery_app = None  # type: ignore


def _check_streaks_impl():
    """Streak kontrol implementasyonu (test edilebilir)."""
    import os

    import psycopg2

    db_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5434/kiro2"
    )
    today = date.today()
    yesterday = today - timedelta(days=1)

    with psycopg2.connect(db_url) as conn, conn.cursor() as cur:
        # Son aktivitesi 2+ gun once olan streak'leri sifirla (freeze yoksa)
        cur.execute(
            """
                UPDATE streaks
                SET current_streak = 0
                WHERE last_activity < %s
                  AND freeze_count = 0
                  AND current_streak > 0
                """,
            (yesterday,),
        )
        reset_count = cur.rowcount

        # Freeze hakki olan streaks'leri azalt
        cur.execute(
            """
                UPDATE streaks
                SET freeze_count = freeze_count - 1,
                    last_activity = %s
                WHERE last_activity < %s
                  AND freeze_count > 0
                  AND current_streak > 0
                """,
            (today, yesterday),
        )
        freeze_count = cur.rowcount

        conn.commit()

    logger.info(
        "Streak check: %d sifirland, %d freeze kullanildi", reset_count, freeze_count
    )
    return {"reset": reset_count, "freeze_used": freeze_count}


if celery_app is not None:

    @celery_app.task(name="tasks.streak_tasks.check_streaks", bind=True, max_retries=3)
    def check_streaks(self):
        """Her gece 00:05'te streak'leri kontrol et."""
        try:
            return _check_streaks_impl()
        except Exception as exc:
            logger.error("Streak check hatasi: %s", exc)
            raise self.retry(exc=exc, countdown=300) from exc
