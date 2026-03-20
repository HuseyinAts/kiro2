"""
Push notification Celery tasklari.

FAZ-2.5 — Master Plan v2.0
Her aksam 20:00'de streak hatirlaticlari gonder.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from core.celery_app import celery_app
except ImportError:
    celery_app = None  # type: ignore


def _send_streak_reminders_impl():
    """
    Streak hatirlatici push notification gonder.
    Bugun aktivitesi olmayan ogrencilere hatirlatici gonder.
    """
    import os
    from datetime import date

    import psycopg2

    db_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5434/kiro2"
    )
    today = date.today()

    try:
        with psycopg2.connect(db_url) as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT u.id, s.current_streak
                    FROM users u
                    JOIN streaks s ON s.user_id = u.id
                    WHERE s.current_streak > 0
                      AND (s.last_activity IS NULL OR s.last_activity < %s)
                    LIMIT 1000
                    """,
                (today,),
            )
            users = cur.fetchall()

        logger.info("%d ogrenciye streak hatirlatici gonderilecek", len(users))

        # TODO: VAPID push notification entegrasyonu
        # pywebpush kullanarak gercek push gonder
        # Su an sadece loglama
        for user_id, streak in users[:10]:  # Test icin sadece 10 kullanici
            logger.debug("Streak hatirlatici: user=%s streak=%d", user_id, streak)

        return {"sent": len(users), "status": "queued"}

    except Exception as e:
        logger.error("Push reminder hatasi: %s", e)
        return {"sent": 0, "status": "error", "error": str(e)}


if celery_app is not None:

    @celery_app.task(
        name="tasks.push_tasks.send_streak_reminders", bind=True, max_retries=2
    )
    def send_streak_reminders(self):
        """Her aksam 20:00'de calis."""
        try:
            return _send_streak_reminders_impl()
        except Exception as exc:
            logger.error("Push task hatasi: %s", exc)
            raise self.retry(exc=exc, countdown=600) from exc
