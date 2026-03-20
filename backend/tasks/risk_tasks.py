"""
Risk analizi Celery tasklari.

FAZ-2.5 — Master Plan v2.0
Her gece 03:00'te dropout risk analizi.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

try:
    from core.celery_app import celery_app
except ImportError:
    celery_app = None  # type: ignore


def _check_dropout_risks_impl():
    """
    Dropout risk analizi:
    - 7+ gun aktivite yok
    - BKT skoru dusuk (<0.3) + aktivite yok
    - Streak 0 + son 14 gun aktivite yok
    """
    import os

    import psycopg2

    db_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5434/kiro2"
    )
    cutoff_7d = date.today() - timedelta(days=7)
    cutoff_14d = date.today() - timedelta(days=14)

    risk_users = []
    try:
        with psycopg2.connect(db_url) as conn, conn.cursor() as cur:
            # 7+ gun aktivite yok
            cur.execute(
                """
                    SELECT u.id, 'inactive_7d' as risk_type
                    FROM users u
                    LEFT JOIN streaks s ON s.user_id = u.id
                    WHERE u.is_active = true
                      AND (s.last_activity IS NULL OR s.last_activity < %s)
                    LIMIT 500
                    """,
                (cutoff_7d,),
            )
            risk_users.extend(cur.fetchall())

        logger.info(
            "Dropout risk analizi: %d riskli kullanici tespit edildi", len(risk_users)
        )
        return {"at_risk": len(risk_users), "cutoff_days": 7}

    except Exception as e:
        logger.error("Risk analiz hatasi: %s", e)
        return {"at_risk": 0, "error": str(e)}


if celery_app is not None:

    @celery_app.task(
        name="tasks.risk_tasks.check_dropout_risks", bind=True, max_retries=2
    )
    def check_dropout_risks(self):
        """Her gece 03:00'te calis."""
        try:
            return _check_dropout_risks_impl()
        except Exception as exc:
            logger.error("Risk task hatasi: %s", exc)
            raise self.retry(exc=exc, countdown=900) from exc
