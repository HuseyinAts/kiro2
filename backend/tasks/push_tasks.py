"""
Push notification Celery tasklari.

FAZ-2.5 — Master Plan v2.0
Her aksam 20:00'de streak hatirlaticlari gonder.

Retention geri-getirme (P0.1): bugun aktivitesi olmayan ama serisi devam eden
ogrencilere in-app notification (notifications tablosu) gonderir. VAPID web-push
henuz yok (pwa subscribe_implemented=False); in-app bildirim gercek kanaldir.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

try:
    from core.celery_app import celery_app
except ImportError:
    celery_app = None  # type: ignore

_DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5434/kiro2"

_INSERT_NOTIFICATION_SQL = """
    INSERT INTO notifications
        (id, user_id, title, message, notification_type, is_read, action_url, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


def build_streak_reminder_notifications(rows):
    """
    At-risk (user_id, current_streak) satirlarini notification dict'lerine cevir.

    Saf fonksiyon (DB yok) — her at-risk ogrenci icin TEK bildirim uretir ve
    listeyi TRUNCATE ETMEZ (eski `users[:10]` bug'i giderildi).
    """
    notifications = []
    for user_id, streak in rows:
        notifications.append(
            {
                "id": uuid.uuid4().hex,
                "user_id": user_id,
                "title": "Serini koru! \U0001f525",
                "message": (
                    f"{streak} gunluk serini kaybetmek uzeresin. "
                    "Bugun bir soru coz, serini surdur!"
                ),
                "notification_type": "uyari",
                "action_url": "/dashboard",
            }
        )
    return notifications


def _send_streak_reminders_impl(connect=None, db_url=None):
    """
    Streak hatirlatici in-app notification gonder.

    Bugun aktivitesi olmayan ama serisi > 0 olan ogrencilere notifications
    tablosuna bildirim INSERT eder.

    Args:
        connect: psycopg2.connect benzeri callable (test icin enjekte edilebilir).
        db_url:  DB baglanti stringi (None ise DATABASE_URL env).
    """
    import os
    from datetime import date

    if connect is None:
        import psycopg2

        connect = psycopg2.connect
    if db_url is None:
        db_url = os.environ.get("DATABASE_URL", _DEFAULT_DB_URL)

    today = date.today()

    try:
        with connect(db_url) as conn, conn.cursor() as cur:
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

            notifications = build_streak_reminder_notifications(users)
            now = datetime.now(UTC)
            for n in notifications:
                cur.execute(
                    _INSERT_NOTIFICATION_SQL,
                    (
                        n["id"],
                        n["user_id"],
                        n["title"],
                        n["message"],
                        n["notification_type"],
                        False,
                        n["action_url"],
                        now,
                    ),
                )

        logger.info(
            "%d ogrenciye streak hatirlatici notification olusturuldu",
            len(notifications),
        )
        return {"sent": len(notifications), "status": "sent"}

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
