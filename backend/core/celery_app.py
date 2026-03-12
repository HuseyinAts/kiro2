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
from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange

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
    },
    # Task queues with priorities
    task_queues=(
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
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    # Worker configuration
    worker_prefetch_multiplier=4,
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
        # CLAUDE.md Self-Improvement Tasks
        "claude-md-collect-feedback-hourly": {
            "task": "tasks.claude_md_improvement_tasks.collect_feedback_hourly",
            "schedule": crontab(minute=0),  # Every hour
        },
        "claude-md-detect-patterns-daily": {
            "task": "tasks.claude_md_improvement_tasks.detect_patterns_daily",
            "schedule": crontab(hour=2, minute=0),  # Daily at 02:00
        },
        "claude-md-monitor-performance": {
            "task": "tasks.claude_md_improvement_tasks.monitor_performance",
            "schedule": 300.0,  # Every 5 minutes
        },
        "claude-md-detect-anomalies": {
            "task": "tasks.claude_md_improvement_tasks.detect_anomalies",
            "schedule": 900.0,  # Every 15 minutes
        },
        "claude-md-check-rule-evolution-weekly": {
            "task": "tasks.claude_md_improvement_tasks.check_rule_evolution",
            "schedule": crontab(hour=3, minute=0, day_of_week=1),  # Monday 03:00
        },
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
    },
)


# Task base class with common functionality
class BaseTask(celery_app.Task):
    """Base task with retry and logging"""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
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

# Export
__all__ = ["celery_app"]
