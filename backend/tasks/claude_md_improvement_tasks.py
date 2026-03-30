"""
CLAUDE.md Self-Improvement Background Tasks.

Scheduled tasks for automated feedback collection, pattern detection,
and performance monitoring.

Spec: claude-md-self-improvement Phase 10 (Deployment)
- REQ-10.1.1: Hourly feedback collection
- REQ-10.1.2: Daily pattern detection
- REQ-10.1.3: Continuous performance monitoring

Author: KIRO2 Team
Date: 2026-01-19
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from core.celery_app import celery_app
from core.structured_logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# REQ-10.1.1: Hourly Feedback Collection
# ============================================================================


@celery_app.task(
    bind=True,
    name="tasks.claude_md_improvement_tasks.collect_feedback_hourly",
    max_retries=3,
    default_retry_delay=60,
)
def collect_feedback_hourly(self) -> dict[str, Any]:
    """
    Collect and aggregate feedback every hour.

    This task:
    1. Fetches all feedback from the last hour
    2. Calculates effectiveness scores per rule
    3. Updates rule_effectiveness table
    4. Checks for improvement triggers

    Returns:
        Collection results with statistics

    Performance Target: < 30s for typical workload
    """
    try:
        logger.info(
            "feedback_collection_started",
            task_id=self.request.id,
            scheduled_at=datetime.now(UTC).isoformat(),
        )

        # Run async collection in sync context
        result = asyncio.run(_collect_feedback_async())

        logger.info(
            "feedback_collection_completed",
            task_id=self.request.id,
            records_processed=result.get("records_processed", 0),
            rules_updated=result.get("rules_updated", 0),
            triggers_created=result.get("triggers_created", 0),
        )

        return result

    except Exception as e:
        logger.error(
            "feedback_collection_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise self.retry(exc=e)


async def _collect_feedback_async() -> dict[str, Any]:
    """Async implementation of feedback collection."""
    from core.database import get_db_session_context
    from services._deprecated.feedback_service import FeedbackService

    async with get_db_session_context() as session:
        service = FeedbackService()

        # Get feedback from last hour
        cutoff = datetime.now(UTC) - timedelta(hours=1)

        # Aggregate and update effectiveness
        result = await service.aggregate_recent_feedback(
            session=session,
            since=cutoff,
        )

        await session.commit()

        return {
            "records_processed": result.get("total_records", 0),
            "rules_updated": len(result.get("updated_rules", [])),
            "triggers_created": len(result.get("triggers", [])),
            "collection_time": datetime.now(UTC).isoformat(),
        }


# ============================================================================
# REQ-10.1.2: Daily Pattern Detection
# ============================================================================


@celery_app.task(
    bind=True,
    name="tasks.claude_md_improvement_tasks.detect_patterns_daily",
    max_retries=2,
    default_retry_delay=300,
)
def detect_patterns_daily(self) -> dict[str, Any]:
    """
    Run pattern detection daily at 02:00 UTC.

    This task:
    1. Runs K-means clustering on error patterns
    2. Identifies success patterns
    3. Detects anti-patterns
    4. Generates recommendations

    Returns:
        Pattern detection results

    Performance Target: < 10s (REQ-2.8.5)
    """
    try:
        logger.info(
            "pattern_detection_started",
            task_id=self.request.id,
            scheduled_at=datetime.now(UTC).isoformat(),
        )

        result = asyncio.run(_detect_patterns_async())

        logger.info(
            "pattern_detection_completed",
            task_id=self.request.id,
            error_patterns=result.get("error_patterns_count", 0),
            success_patterns=result.get("success_patterns_count", 0),
            anti_patterns=result.get("anti_patterns_count", 0),
        )

        return result

    except Exception as e:
        logger.error(
            "pattern_detection_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise self.retry(exc=e)


async def _detect_patterns_async() -> dict[str, Any]:
    """Async implementation of pattern detection."""
    import time

    from core.database import get_db_session_context
    from services._deprecated.pattern_service import PatternDetectionService

    start_time = time.time()

    async with get_db_session_context() as session:
        service = PatternDetectionService(db=session)

        # Detect error patterns (REQ-2.1)
        error_patterns = await service.detect_error_patterns(
            window_days=30,
            min_occurrences=3,
        )

        # Detect success patterns (REQ-2.2)
        success_patterns = await service.detect_success_patterns(
            window_days=30,
            min_effectiveness=0.8,
        )

        # Detect anti-patterns (REQ-2.3)
        anti_patterns = await service.detect_anti_patterns(
            window_days=30,
            max_effectiveness=0.4,
        )

        # Generate recommendations (REQ-2.6)
        recommendations = await service.get_recommendations()

        detection_time = time.time() - start_time

        return {
            "error_patterns_count": len(error_patterns),
            "success_patterns_count": len(success_patterns),
            "anti_patterns_count": len(anti_patterns),
            "recommendations_count": len(recommendations),
            "detection_time_seconds": round(detection_time, 2),
            "detection_timestamp": datetime.now(UTC).isoformat(),
        }


# ============================================================================
# REQ-10.1.3: Continuous Performance Monitoring
# ============================================================================


@celery_app.task(
    bind=True,
    name="tasks.claude_md_improvement_tasks.monitor_performance",
    max_retries=3,
    default_retry_delay=30,
)
def monitor_performance(self) -> dict[str, Any]:
    """
    Monitor performance every 5 minutes.

    This task:
    1. Captures current performance metrics
    2. Compares against baseline
    3. Detects regressions (> 5% drop)
    4. Triggers auto-rollback if needed

    Returns:
        Monitoring results

    Performance Target: < 10s
    """
    try:
        logger.info(
            "performance_monitoring_started",
            task_id=self.request.id,
            scheduled_at=datetime.now(UTC).isoformat(),
        )

        result = asyncio.run(_monitor_performance_async())

        # Log regression warning if detected
        if result.get("regression_detected"):
            logger.warning(
                "performance_regression_detected",
                task_id=self.request.id,
                metric=result.get("regression_metric"),
                drop_percentage=result.get("drop_percentage"),
            )

        logger.info(
            "performance_monitoring_completed",
            task_id=self.request.id,
            success_rate=result.get("current_success_rate"),
            regression_detected=result.get("regression_detected", False),
        )

        return result

    except Exception as e:
        logger.error(
            "performance_monitoring_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise self.retry(exc=e)


async def _monitor_performance_async() -> dict[str, Any]:
    """Async implementation of performance monitoring."""
    from core.database import get_db_session_context
    from services._deprecated.performance_monitor_service import (
        PerformanceMonitorService,
    )

    async with get_db_session_context() as session:
        service = PerformanceMonitorService(db=session)

        # Get current metrics
        current_metrics = await service.get_current_metrics()

        # Compare with baseline
        await service.compare_with_baseline()

        # Check for regression (REQ-7.3)
        regression_result = await service.detect_regression()

        # Trigger rollback if needed
        rollback_triggered = False
        if regression_result.get("regression_detected"):
            # REQ-7.3: Automatic rollback trigger
            rollback_result = await service.trigger_auto_rollback()
            rollback_triggered = rollback_result.get("success", False)

        return {
            "current_success_rate": current_metrics.task_success_rate,
            "current_latency": current_metrics.avg_latency,
            "current_quality": current_metrics.quality_score,
            "regression_detected": regression_result.get("regression_detected", False),
            "regression_metric": regression_result.get("metric"),
            "drop_percentage": regression_result.get("drop_percentage"),
            "rollback_triggered": rollback_triggered,
            "monitoring_timestamp": datetime.now(UTC).isoformat(),
        }


# ============================================================================
# Anomaly Detection Task
# ============================================================================


@celery_app.task(
    bind=True,
    name="tasks.claude_md_improvement_tasks.detect_anomalies",
    max_retries=2,
)
def detect_anomalies(self) -> dict[str, Any]:
    """
    Detect anomalies in metrics every 15 minutes.

    REQ-7.5: Z-score > 3 identifies outliers.

    Returns:
        Anomaly detection results
    """
    try:
        logger.info(
            "anomaly_detection_started",
            task_id=self.request.id,
        )

        result = asyncio.run(_detect_anomalies_async())

        if result.get("anomalies_detected", 0) > 0:
            logger.warning(
                "anomalies_detected",
                task_id=self.request.id,
                count=result.get("anomalies_detected"),
                metrics=result.get("anomalous_metrics"),
            )

        return result

    except Exception as e:
        logger.error(
            "anomaly_detection_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise self.retry(exc=e)


async def _detect_anomalies_async() -> dict[str, Any]:
    """Async implementation of anomaly detection."""
    from core.database import get_db_session_context
    from services._deprecated.performance_monitor_service import (
        PerformanceMonitorService,
    )

    async with get_db_session_context() as session:
        service = PerformanceMonitorService(db=session)

        # Detect anomalies (Z-score > 3)
        anomalies = await service.detect_anomalies()

        return {
            "anomalies_detected": len(anomalies),
            "anomalous_metrics": [a.metric for a in anomalies],
            "detection_timestamp": datetime.now(UTC).isoformat(),
        }


# ============================================================================
# Scheduled Rule Evolution Check
# ============================================================================


@celery_app.task(
    bind=True,
    name="tasks.claude_md_improvement_tasks.check_rule_evolution",
)
def check_rule_evolution(self) -> dict[str, Any]:
    """
    Check for rules needing evolution (weekly task).

    Identifies rules with effectiveness < 0.6 and
    creates improvement triggers.

    Returns:
        Evolution check results
    """
    try:
        logger.info(
            "rule_evolution_check_started",
            task_id=self.request.id,
        )

        result = asyncio.run(_check_rule_evolution_async())

        logger.info(
            "rule_evolution_check_completed",
            task_id=self.request.id,
            low_performing_rules=result.get("low_performing_count"),
        )

        return result

    except Exception as e:
        logger.error(
            "rule_evolution_check_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise


async def _check_rule_evolution_async() -> dict[str, Any]:
    """Async implementation of rule evolution check."""
    from core.database import get_db_session_context
    from services._deprecated.rule_evolution_service import RuleEvolutionService

    async with get_db_session_context() as session:
        service = RuleEvolutionService(db=session)

        # Find low-performing rules
        low_performing = await service.detect_low_performing_rules(
            threshold=0.6,
        )

        # Create triggers for each
        triggers_created = 0
        for rule in low_performing:
            await service.create_evolution_trigger(rule.rule_id)
            triggers_created += 1

        await session.commit()

        return {
            "low_performing_count": len(low_performing),
            "triggers_created": triggers_created,
            "check_timestamp": datetime.now(UTC).isoformat(),
        }


# ============================================================================
# Celery Beat Schedule Configuration
# ============================================================================

# Add to Celery beat schedule in core/celery_app.py:
CELERY_BEAT_SCHEDULE = {
    "collect-feedback-hourly": {
        "task": "tasks.claude_md_improvement_tasks.collect_feedback_hourly",
        "schedule": 3600.0,  # Every hour
    },
    "detect-patterns-daily": {
        "task": "tasks.claude_md_improvement_tasks.detect_patterns_daily",
        "schedule": 86400.0,  # Every 24 hours
        # Run at 02:00 UTC
    },
    "monitor-performance": {
        "task": "tasks.claude_md_improvement_tasks.monitor_performance",
        "schedule": 300.0,  # Every 5 minutes
    },
    "detect-anomalies": {
        "task": "tasks.claude_md_improvement_tasks.detect_anomalies",
        "schedule": 900.0,  # Every 15 minutes
    },
    "check-rule-evolution-weekly": {
        "task": "tasks.claude_md_improvement_tasks.check_rule_evolution",
        "schedule": 604800.0,  # Every week
    },
}
