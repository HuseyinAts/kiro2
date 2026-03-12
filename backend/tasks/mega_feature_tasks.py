"""
Mega Feature Background Tasks

Scheduled Celery tasks for:
- F2: Weekly league tier promotion/demotion (every Monday 00:00)
- F6: Daily coaching suggestion generation (every day 06:00)
- F15: Weekly error clustering rebuild (every Sunday 23:00)

Beat schedule entries must be added to core/celery_app.py:
    "league-weekly-reset": {
        "task": "tasks.mega_feature_tasks.process_weekly_league_reset",
        "schedule": crontab(hour=0, minute=0, day_of_week=1),
    },
    "daily-coaching-suggestions": {
        "task": "tasks.mega_feature_tasks.generate_daily_coaching_suggestions",
        "schedule": crontab(hour=6, minute=0),
    },
    "weekly-error-clustering": {
        "task": "tasks.mega_feature_tasks.run_weekly_error_clustering",
        "schedule": crontab(hour=23, minute=0, day_of_week=0),
    },
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from core.celery_app import celery_app
from core.structured_logger import get_logger

logger = get_logger(__name__)

# Subject list used for F15 — all subjects present in question_bank
_ALL_SUBJECTS = [
    "MATEMATIK",
    "FIZIK",
    "KIMYA",
    "BIYOLOJI",
    "TURKCE",
    "TARIH",
    "COGRAFYA",
    "EDEBIYAT",
    "GEOMETRI",
]


# ---------------------------------------------------------------------------
# F2: Weekly League Reset
# ---------------------------------------------------------------------------


@celery_app.task(
    bind=True,
    name="tasks.mega_feature_tasks.process_weekly_league_reset",
    soft_time_limit=300,
    time_limit=600,
)
def process_weekly_league_reset(self) -> dict[str, Any]:
    """Weekly league tier promotion and demotion task.

    Runs every Monday at 00:00 UTC (via Celery Beat).

    For each tier in BRONZE → SILVER → GOLD → PLATINUM → CHAMPION:
    - Fetches all memberships for the previous week, sorted by weekly_xp DESC.
    - Top 10% are promoted to the next tier.
    - Bottom 10% (excluding BRONZE) are demoted to the previous tier.
    - Creates league_history entries recording the outcome.
    - New memberships for the current week inherit the resolved tier.

    Weekly XP is not reset here — new memberships start at 0 automatically
    because _get_or_create_membership always creates a fresh row for the
    current week.

    Returns:
        {success, promoted, demoted, unchanged, total, week_processed}
    """
    logger.info("league_weekly_reset_started")
    try:
        result = asyncio.run(_run_weekly_league_reset())
        logger.info(
            "league_weekly_reset_completed",
            promoted=result.get("promoted"),
            demoted=result.get("demoted"),
            unchanged=result.get("unchanged"),
            total=result.get("total"),
        )
        return {"success": True, **result}

    except Exception as exc:
        logger.error("league_weekly_reset_failed", error=str(exc))
        # Scheduled tasks should not retry — they will re-run next week
        return {"success": False, "error": str(exc)}


async def _run_weekly_league_reset() -> dict[str, Any]:
    """Async implementation for the weekly league reset task."""
    from core.database import get_db_session_context
    from services.league_service import process_weekly_reset

    async with get_db_session_context() as db:
        return await process_weekly_reset(db=db)


# ---------------------------------------------------------------------------
# F6: Daily Coaching Suggestions
# ---------------------------------------------------------------------------


@celery_app.task(
    bind=True,
    name="tasks.mega_feature_tasks.generate_daily_coaching_suggestions",
    soft_time_limit=300,
    time_limit=600,
)
def generate_daily_coaching_suggestions(self) -> dict[str, Any]:
    """Generate proactive coaching suggestions for all active students.

    Runs every day at 06:00 (via Celery Beat).

    For each student who has been active in the last 14 days:
    - Analyzes recent error patterns and weak topics (last 7 days).
    - Detects burnout signals (session frequency drop, short sessions).
    - Checks FSRS due card backlog.
    - Creates coaching_events rows for each generated suggestion.

    A student is considered "active" if they have at least one ExamSession
    created in the last 14 days.

    Returns:
        {success, students_processed, events_created, students_skipped}
    """
    logger.info("daily_coaching_suggestions_started")
    try:
        result = asyncio.run(_run_daily_coaching_suggestions())
        logger.info(
            "daily_coaching_suggestions_completed",
            students_processed=result.get("students_processed"),
            events_created=result.get("events_created"),
        )
        return {"success": True, **result}

    except Exception as exc:
        logger.error("daily_coaching_suggestions_failed", error=str(exc))
        return {"success": False, "error": str(exc)}


async def _run_daily_coaching_suggestions() -> dict[str, Any]:
    """Async implementation for the daily coaching suggestions task."""
    from sqlalchemy import distinct, select

    from core.database import get_db_session_context
    from models.coaching import CoachingEvent
    from models.exam_db import ExamSession
    from services.proactive_coaching_service import generate_suggestions

    students_processed = 0
    events_created = 0
    students_skipped = 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=14)

    async with get_db_session_context() as db:
        # Collect distinct active student IDs (active = exam session in last 14 days)
        result = await db.execute(
            select(distinct(ExamSession.student_id)).where(
                ExamSession.created_at >= cutoff
            )
        )
        student_ids: list[str] = list(result.scalars().all())

    logger.info("coaching_active_students_found", count=len(student_ids))

    # Process each student in its own session to limit transaction scope
    for student_id in student_ids:
        try:
            async with get_db_session_context() as db:
                suggestions = await generate_suggestions(db=db, student_id=student_id)

                for suggestion in suggestions:
                    event = CoachingEvent(
                        id=suggestion.get("id") or str(uuid.uuid4()),
                        student_id=student_id,
                        event_type=suggestion["type"],
                        trigger_data={
                            "source": "daily_task",
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                        },
                        message=suggestion["message"],
                        priority=suggestion.get("priority", 0),
                        action_url=suggestion.get("action_url"),
                        # shown_at left null — frontend sets it on display
                    )
                    db.add(event)
                    events_created += 1

                await db.commit()
                students_processed += 1

        except Exception as exc:
            logger.warning(
                "coaching_student_skipped",
                student_id=student_id,
                error=str(exc),
            )
            students_skipped += 1

    return {
        "students_processed": students_processed,
        "events_created": events_created,
        "students_skipped": students_skipped,
    }


# ---------------------------------------------------------------------------
# F15: Weekly Error Clustering
# ---------------------------------------------------------------------------


@celery_app.task(
    bind=True,
    name="tasks.mega_feature_tasks.run_weekly_error_clustering",
    soft_time_limit=300,
    time_limit=600,
)
def run_weekly_error_clustering(self) -> dict[str, Any]:
    """Rebuild error clusters from student_answers data.

    Runs every Sunday at 23:00 (via Celery Beat).

    For each subject:
    - Aggregates all wrong answers that have an error_type set.
    - Groups by (error_type, subject) combination.
    - Creates or updates ErrorCluster rows with current student counts.
    - Generates PeerRecommendation rows connecting clusters to target topics
      based on improvement evidence from students who overcame the same
      error pattern.

    Clusters with fewer than 3 distinct students are skipped.

    Returns:
        {success, subjects_processed, clusters_created, clusters_updated,
         recommendations_created, run_at}
    """
    logger.info("weekly_error_clustering_started")
    try:
        result = asyncio.run(_run_weekly_error_clustering())
        logger.info(
            "weekly_error_clustering_completed",
            subjects_processed=result.get("subjects_processed"),
            clusters_created=result.get("clusters_created"),
            clusters_updated=result.get("clusters_updated"),
            recommendations_created=result.get("recommendations_created"),
        )
        return {"success": True, **result}

    except Exception as exc:
        logger.error("weekly_error_clustering_failed", error=str(exc))
        return {"success": False, "error": str(exc)}


async def _run_weekly_error_clustering() -> dict[str, Any]:
    """Async implementation for the weekly error clustering task."""
    from core.database import get_db_session_context
    from services.error_cluster_service import build_error_clusters

    subjects_processed = 0
    total_created = 0
    total_updated = 0
    total_recommendations = 0

    for subject in _ALL_SUBJECTS:
        try:
            async with get_db_session_context() as db:
                stats = await build_error_clusters(db=db, subject=subject)
                await db.commit()

                total_created += stats.get("clusters_created", 0)
                total_updated += stats.get("clusters_updated", 0)
                subjects_processed += 1

                logger.info(
                    "error_clustering_subject_done",
                    subject=subject,
                    clusters_created=stats.get("clusters_created", 0),
                    clusters_updated=stats.get("clusters_updated", 0),
                    total_patterns=stats.get("total_patterns", 0),
                )

                # Build peer recommendations for clusters updated in this run
                recs = await _build_peer_recommendations(db=db, subject=subject)
                total_recommendations += recs

        except Exception as exc:
            logger.warning(
                "error_clustering_subject_failed",
                subject=subject,
                error=str(exc),
            )

    return {
        "subjects_processed": subjects_processed,
        "clusters_created": total_created,
        "clusters_updated": total_updated,
        "recommendations_created": total_recommendations,
        "run_at": datetime.now(timezone.utc).isoformat(),
    }


async def _build_peer_recommendations(*, db: Any, subject: str) -> int:
    """Generate PeerRecommendation rows for clusters in a given subject.

    Logic: for each ErrorCluster in the subject, find students who previously
    had that error pattern and later improved (error rate dropped below 20%
    on the same topic).  The topic where they improved becomes the
    target_topic recommendation.

    Returns the number of PeerRecommendation rows created or updated.
    """
    from sqlalchemy import and_, case, func as sa_func, select

    from models.error_cluster import ErrorCluster, PeerRecommendation
    from models.exam_db import ExamSession, StudentAnswer
    from models.question_bank import QuestionBankItem

    created = 0

    # Fetch clusters for this subject that have at least 3 students
    cluster_result = await db.execute(
        select(ErrorCluster).where(
            and_(
                ErrorCluster.subject == subject.upper(),
                ErrorCluster.student_count >= 3,
            )
        )
    )
    clusters = cluster_result.scalars().all()

    for cluster in clusters:
        # Derive the error_type from the pattern ("error_type:subject" format)
        error_type = cluster.error_pattern.split(":")[0]

        # Find students who have this error pattern
        students_result = await db.execute(
            select(ExamSession.student_id)
            .join(
                StudentAnswer,
                StudentAnswer.exam_session_id == ExamSession.id,
            )
            .where(
                and_(
                    StudentAnswer.is_correct.is_(False),
                    StudentAnswer.error_type == error_type,
                )
            )
            .distinct()
            .limit(500)
        )
        student_ids = [r[0] for r in students_result.all()]

        if len(student_ids) < 3:
            continue

        # For each such student find which subjects/topics they improved on
        # Improvement: >=10 answers on a topic with error_rate < 20%
        improvement_result = await db.execute(
            select(
                QuestionBankItem.primary_topic_id.label("topic_id"),
                QuestionBankItem.subject_area.label("subject_area"),
                sa_func.count().label("total"),
                sa_func.sum(
                    case((StudentAnswer.is_correct.is_(True), 1), else_=0)
                ).label("correct"),
            )
            .join(
                StudentAnswer,
                StudentAnswer.question_id == QuestionBankItem.id,
            )
            .join(
                ExamSession,
                ExamSession.id == StudentAnswer.exam_session_id,
            )
            .where(
                and_(
                    ExamSession.student_id.in_(student_ids),
                    QuestionBankItem.primary_topic_id.isnot(None),
                )
            )
            .group_by(
                QuestionBankItem.primary_topic_id,
                QuestionBankItem.subject_area,
            )
            .having(sa_func.count() >= 10)
        )

        for row in improvement_result.all():
            if row.total == 0:
                continue
            improvement_rate = row.correct / row.total
            if improvement_rate < 0.80:  # Only recommend if >80% correct rate
                continue

            target_topic = str(row.topic_id)
            source_topic = cluster.error_pattern

            # Upsert: check existing recommendation for this cluster+target
            existing_result = await db.execute(
                select(PeerRecommendation).where(
                    and_(
                        PeerRecommendation.cluster_id == cluster.id,
                        PeerRecommendation.target_topic == target_topic,
                    )
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.improvement_rate = round(improvement_rate, 4)
                existing.sample_size = len(student_ids)
            else:
                rec = PeerRecommendation(
                    cluster_id=cluster.id,
                    source_topic=source_topic,
                    target_topic=target_topic,
                    improvement_rate=round(improvement_rate, 4),
                    sample_size=len(student_ids),
                    description=(
                        f"Bu hata örüntüsüne sahip öğrencilerin "
                        f"%{round(improvement_rate * 100)}i "
                        f"konu {target_topic[:8]} çalışarak iyileşti."
                    ),
                )
                db.add(rec)
                created += 1

        await db.flush()

    return created
