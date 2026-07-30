"""
Celery Application Configuration
PHASE 1 Sprint 3: Async Processing

Background task infrastructure for:
- Email sending
- Report generation
- Video processing
- Bulk operations
- Scheduled tasks
"""

import os
from typing import ClassVar

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

# Redis broker URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "kiro2",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "tasks.email_tasks",
        "tasks.report_tasks",
        "tasks.video_tasks",
        "tasks.bulk_tasks",
        "tasks.claude_md_improvement_tasks",
        "tasks.mega_feature_tasks",
        "tasks.social_tasks",
        "tasks.daily_plan_tasks",  # Günlük plan yenileme
        "tasks.push_tasks",  # Streak retention push (P0.1)
        "tasks.quality_gate_tasks",  # mv_safe_for_beta yenileme
    ],
)

# Celery Configuration
celery_app.conf.update(
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    # Task routing
    task_routes={
        "tasks.email_tasks.*": {"queue": "emails"},
        "tasks.report_tasks.*": {"queue": "reports"},
        "tasks.video_tasks.*": {"queue": "videos"},
        "tasks.bulk_tasks.*": {"queue": "bulk"},
        "tasks.claude_md_improvement_tasks.*": {"queue": "claude_md"},
        "tasks.mega_feature_tasks.*": {"queue": "features"},
        "tasks.quality_gate_tasks.*": {"queue": "features"},
    },
    # Rotası olmayan görevlerin varsayılan kuyruğu. Celery'nin kendi varsayılanı
    # "celery"dir ve worker onu dinlemez (docker-compose: -Q default,emails,...),
    # yani rotasız her görev sessizce çürürdü — 29 Tem 2026'da Redis'in "celery"
    # kuyruğunda 3.367 tüketilmemiş mesaj ölçüldü. Sözleşme:
    # tests/unit/test_celery_routing_contract.py
    task_default_queue="default",
    # Task queues with priorities
    task_queues=(
        Queue(
            "default", Exchange("default"), routing_key="default", priority=5
        ),  # task_default_queue hedefi — rotasız görevler buraya düşer
        Queue(
            "emails", Exchange("emails"), routing_key="email", priority=9
        ),  # High priority
        Queue(
            "claude_md", Exchange("claude_md"), routing_key="claude_md", priority=7
        ),  # High-medium priority (CLAUDE.md self-improvement)
        Queue(
            "reports", Exchange("reports"), routing_key="report", priority=5
        ),  # Medium priority
        Queue(
            "videos", Exchange("videos"), routing_key="video", priority=3
        ),  # Low priority
        Queue(
            "bulk", Exchange("bulk"), routing_key="bulk", priority=1
        ),  # Lowest priority
        Queue(
            "features", Exchange("features"), routing_key="feature", priority=5
        ),  # Medium priority (F2/F6/F15 periodic tasks)
    ),
    # Task execution limits
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    # Retry configuration
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Result backend
    result_expires=86400,  # 24 hours (batch/report tasks can take 30-60 min)
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    # Worker configuration
    worker_prefetch_multiplier=1,  # Fair distribution; 4 causes starvation with long tasks
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    worker_disable_rate_limits=False,
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Beat schedule for periodic tasks
    beat_schedule={
        # Daily report generation (every day at 8 AM)
        "generate-daily-reports": {
            "task": "tasks.report_tasks.generate_daily_analytics_report",
            "schedule": crontab(hour=8, minute=0),
        },
        # Weekly report generation (every Monday at 9 AM)
        "generate-weekly-reports": {
            "task": "tasks.report_tasks.generate_weekly_summary_report",
            "schedule": crontab(hour=9, minute=0, day_of_week=1),
        },
        # Kalite kapısı: mv_safe_for_beta gecelik yenileme (03:30).
        # Asıl tetik küratör yargısıdır (tasks.quality_gate_tasks.
        # schedule_safe_pool_refresh); bu yalnız emniyet ağı — offline demote
        # script'leri uygulama dışından çalıştığı için tetiklenemiyor.
        # 03:00 IRT kalibrasyonuyla çakışmasın diye 03:30.
        "refresh-safe-pool-nightly": {
            "task": "tasks.quality_gate_tasks.refresh_safe_pool",
            "schedule": crontab(hour=3, minute=30),
        },
        # Arama index'ini kalite kapısıyla eşitle (04:00).
        # SIRA KRİTİK: 03:30 matview yenilemesinden SONRA. Ters sıra bir gün
        # eski havuzu indeksler.
        # 31 Tem 2026'da ölçüldü: PG↔ES arasında hiç senkron yolu yoktu; index
        # 1 Nis'ta tek toplu yüklemeyle yazılmış ve o günden beri hiç
        # değişmemişti. Sonuç: ES'te 60.605 kayıt kapıdan geçmiyordu, kapıdaki
        # 21.462 kayıt ise ES'te hiç yoktu.
        "sync-search-index-nightly": {
            "task": "tasks.es_sync_tasks.sync_search_index",
            "schedule": crontab(hour=4, minute=0),
        },
        # Cache cleanup (every hour)
        "cleanup-expired-cache": {
            "task": "tasks.bulk_tasks.cleanup_expired_cache_entries",
            "schedule": crontab(minute=0),  # Every hour
        },
        # Video cache refresh (every 6 hours)
        "refresh-video-cache": {
            "task": "tasks.video_tasks.refresh_popular_video_cache",
            "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        },
        # CLAUDE.md Self-Improvement Tasks — DISABLED (dependent services deprecated)
        # Uncomment when services are restored: feedback_service, pattern_service,
        # performance_monitor_service, rule_evolution_service
        # "claude-md-collect-feedback-hourly": {
        #     "task": "tasks.claude_md_improvement_tasks.collect_feedback_hourly",
        #     "schedule": crontab(minute=0),
        # },
        # "claude-md-detect-patterns-daily": {
        #     "task": "tasks.claude_md_improvement_tasks.detect_patterns_daily",
        #     "schedule": crontab(hour=2, minute=0),
        # },
        # "claude-md-monitor-performance": {
        #     "task": "tasks.claude_md_improvement_tasks.monitor_performance",
        #     "schedule": 300.0,
        # },
        # "claude-md-detect-anomalies": {
        #     "task": "tasks.claude_md_improvement_tasks.detect_anomalies",
        #     "schedule": 900.0,
        # },
        # "claude-md-check-rule-evolution-weekly": {
        #     "task": "tasks.claude_md_improvement_tasks.check_rule_evolution",
        #     "schedule": crontab(hour=3, minute=0, day_of_week=1),
        # },
        # F2: League weekly reset (every Monday at midnight)
        "league-weekly-reset": {
            "task": "tasks.mega_feature_tasks.process_weekly_league_reset",
            "schedule": crontab(hour=0, minute=0, day_of_week=1),  # Monday 00:00
        },
        # F6: Daily coaching suggestions (every day at 6 AM)
        "daily-coaching-suggestions": {
            "task": "tasks.mega_feature_tasks.generate_daily_coaching_suggestions",
            "schedule": crontab(hour=6, minute=0),  # Daily 06:00
        },
        # F15: Weekly error clustering (every Sunday at 23:00)
        "weekly-error-clustering": {
            "task": "tasks.mega_feature_tasks.run_weekly_error_clustering",
            "schedule": crontab(hour=23, minute=0, day_of_week=0),  # Sunday 23:00
        },
        # IRT: Weekly calibration (every Sunday at 03:00)
        "weekly-irt-calibration": {
            "task": "kiro2.tasks.irt_calibration",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 03:00
            "kwargs": {"batch_size": 200},
        },
        # Social: Birlikte Streak break detection (daily at 00:05)
        "social-birlikte-streak-check": {
            "task": "tasks.social_tasks.check_birlikte_streaks",
            "schedule": crontab(hour=0, minute=5),
        },
        # Social: Duel voting expiry (every 30 minutes)
        "social-duel-voting-expiry": {
            "task": "tasks.social_tasks.expire_duel_voting",
            "schedule": 1800.0,  # 30 minutes
        },
        # Social: Oba challenge expiry (daily at 00:10)
        "social-oba-challenge-expiry": {
            "task": "tasks.social_tasks.expire_oba_challenges",
            "schedule": crontab(hour=0, minute=10),
        },
        # LEARNING PATH: Daily plan refresh (every day at 02:00)
        "refresh-daily-plans": {
            "task": "tasks.refresh_daily_plans",
            "schedule": crontab(hour=2, minute=0),
        },
        # RETENTION (P0.1): Streak hatırlatıcı — her akşam 20:00
        "send-streak-reminders": {
            "task": "tasks.push_tasks.send_streak_reminders",
            "schedule": crontab(hour=20, minute=0),
        },
    },
)


# Task base class with common functionality
# `.Task` uygulama örneğine bağlı olarak çalışma anında üretilir; mypy statik olarak göremez.
class BaseTask(celery_app.Task):  # type: ignore[name-defined]
    """Base task with retry and logging"""

    # Only retry transient failures — broad Exception retry causes non-recoverable
    # errors (bad data, validation errors) to waste retries before final failure
    autoretry_for = (ConnectionError, TimeoutError, OSError)
    retry_kwargs: ClassVar[dict[str, int]] = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure"""
        from core.structured_logger import get_logger

        logger = get_logger(__name__)
        logger.error(
            "celery_task_failed",
            task_id=task_id,
            task_name=self.name,
            exception=str(exc),
            args=args,
            kwargs=kwargs,
        )

    def on_success(self, retval, task_id, args, kwargs):
        """Log task success"""
        from core.structured_logger import get_logger

        logger = get_logger(__name__)
        logger.info(
            "celery_task_success",
            task_id=task_id,
            task_name=self.name,
            args=args,
            kwargs=kwargs,
        )


# Set base task
celery_app.Task = BaseTask

# IRT kalibrasyon task'ını register et
try:
    from app.tasks.calibration_task import make_celery_task
    from core.database import get_db_session_context

    run_irt_calibration = make_celery_task(celery_app, get_db_session_context)
except Exception as _e:
    import logging

    logging.getLogger(__name__).warning(
        f"IRT calibration task register edilemedi: {_e}"
    )

# Export
__all__ = ["celery_app"]
