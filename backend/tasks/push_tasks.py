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
import re
import uuid
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

# SQLAlchemy URL'i (postgresql+asyncpg://) psycopg2'ye verilemez: psycopg2 '+asyncpg'
# ekini tanimaz, dizeyi key=value baglanti stringi sanip `invalid dsn` atar — ve
# hata metnine DSN'in TAMAMINI gomer. 6 Agu 2026'da olculdu: gorev 4 gun boyunca
# her koşuda patti ve kiro2_app parolasi worker log'una 14 kez dustu.
_SQLALCHEMY_DRIVER_RE = re.compile(r"^(postgres(?:ql)?)\+[a-z0-9_]+://", re.IGNORECASE)

# Hata metinlerinde gecen baglanti dizelerindeki parola alanini maskele.
# (Desen: sema, ardindan kullanici adi, ardindan parola, ardindan @ isareti.)
_DSN_CREDENTIALS_RE = re.compile(r"([a-z0-9+]+://[^:/@\s]+):[^@\s]+@", re.IGNORECASE)


def _libpq_dsn(url: str) -> str:
    """SQLAlchemy URL'ini psycopg2'nin anladigi libpq DSN'ine cevir."""
    return _SQLALCHEMY_DRIVER_RE.sub(r"\1://", url)


def _redact_dsn(text: str) -> str:
    """Metindeki DSN parolalarini maskele (log ve donus degeri icin)."""
    return _DSN_CREDENTIALS_RE.sub(r"\1:***@", text)


try:
    from core.celery_app import celery_app
except ImportError:
    celery_app = None

# Yalnizca DATABASE_URL tanimsizken kullanilan yerel gelistirme varsayilani.
# Uretimde ASLA bu dala dusulmemeli; dusulurse baglanti zaten reddedilir.
_DEFAULT_DB_URL = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)

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
    db_url = _libpq_dsn(db_url)

    # ONCEDEN VAR OLAN: yerel saat dilimine bagli. Dosya asagida datetime.now(UTC)
    # kullaniyor, yani naive/aware karisimi var (gf82 ile ayni sinif). Duzeltmek
    # gece yarisi civari kimin hatirlatici aldigini DEGISTIRIR - ayri gorev.
    today = date.today()  # noqa: DTZ011

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
        # psycopg2 hata metnine DSN'i gomer. Donus degeri Celery sonuc
        # backend'ine de yazildigi icin IKI sizinti yuzeyi var - ikisi de maskeli.
        guvenli = _redact_dsn(str(e))
        logger.error("Push reminder hatasi: %s", guvenli)
        return {"sent": 0, "status": "error", "error": guvenli}


if celery_app is not None:

    @celery_app.task(
        name="tasks.push_tasks.send_streak_reminders", bind=True, max_retries=2
    )
    def send_streak_reminders(self):
        """Her aksam 20:00'de calis."""
        try:
            return _send_streak_reminders_impl()
        except Exception as exc:
            logger.error("Push task hatasi: %s", _redact_dsn(str(exc)))
            raise self.retry(exc=exc, countdown=600) from exc
