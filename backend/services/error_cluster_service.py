"""
Error Clustering Service — F15
Collaborative filtering of student error patterns.

"Bu hatayı yapanların %67'si X konusunu çalışarak iyileşti."
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger
from models.error_cluster import ErrorCluster, PeerRecommendation

logger = get_logger("error_cluster_service")


async def get_error_clusters_for_topic(
    *,
    db: AsyncSession,
    subject: str,
    topic_id: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Get error clusters relevant to a topic."""
    query = select(ErrorCluster).where(
        ErrorCluster.subject == subject.upper(),
        ErrorCluster.student_count >= 3,
    )

    if topic_id:
        # JSONB contains check
        query = query.where(ErrorCluster.topic_ids.contains([topic_id]))

    query = query.order_by(ErrorCluster.student_count.desc()).limit(limit)
    result = await db.execute(query)
    clusters = result.scalars().all()

    return [
        {
            "cluster_id": c.id,
            "error_pattern": c.error_pattern,
            "student_count": c.student_count,
            "topic_ids": c.topic_ids,
            "remediation": c.recommended_remediation,
        }
        for c in clusters
    ]


async def get_peer_recommendations(
    *,
    db: AsyncSession,
    cluster_id: str,
    min_improvement: float = 0.1,
) -> list[dict]:
    """Get "students like you did X" recommendations."""
    result = await db.execute(
        select(PeerRecommendation)
        .where(
            PeerRecommendation.cluster_id == cluster_id,
            PeerRecommendation.improvement_rate >= min_improvement,
            PeerRecommendation.sample_size >= 5,
        )
        .order_by(PeerRecommendation.improvement_rate.desc())
        .limit(5)
    )
    recs = result.scalars().all()

    return [
        {
            "source_topic": r.source_topic,
            "target_topic": r.target_topic,
            "improvement_rate": round(r.improvement_rate, 2),
            "sample_size": r.sample_size,
            "description": r.description,
        }
        for r in recs
    ]


async def cluster_student_errors(
    *,
    db: AsyncSession,
    student_id: str,
    subject: str,
) -> list[dict]:
    """Analyze a student's error patterns and find matching clusters.

    Uses error_type from student_answers to find common patterns.
    """
    from models.exam_db import StudentAnswer

    # Get recent wrong answers with error_type
    result = await db.execute(
        select(
            StudentAnswer.error_type,
            func.count().label("count"),
        )
        .where(
            StudentAnswer.student_id == student_id,
            StudentAnswer.is_correct == False,  # noqa: E712
            StudentAnswer.error_type.isnot(None),
        )
        .group_by(StudentAnswer.error_type)
        .order_by(func.count().desc())
        .limit(5)
    )
    error_counts = result.all()

    if not error_counts:
        return []

    error_type_counts = {et: c for et, c in error_counts}
    error_types = list(error_type_counts.keys())

    # Single query for all matching clusters (replaces N separate queries)
    clusters_result = await db.execute(
        select(ErrorCluster)
        .where(
            ErrorCluster.subject == subject.upper(),
            or_(*[ErrorCluster.error_pattern.contains(et) for et in error_types]),
        )
        .order_by(ErrorCluster.student_count.desc())
        .limit(10)  # max 5 error types × 2 clusters each
    )
    all_clusters = clusters_result.scalars().all()

    if not all_clusters:
        return []

    # Single query for all peer recommendations (replaces N×M separate queries)
    cluster_ids = [c.id for c in all_clusters]
    recs_result = await db.execute(
        select(PeerRecommendation)
        .where(
            PeerRecommendation.cluster_id.in_(cluster_ids),
            PeerRecommendation.improvement_rate >= 0.1,
            PeerRecommendation.sample_size >= 5,
        )
        .order_by(PeerRecommendation.improvement_rate.desc())
    )
    all_recs = recs_result.scalars().all()

    # Group recs by cluster_id in Python (no DB round trips)
    recs_by_cluster: dict[str, list[dict]] = {cid: [] for cid in cluster_ids}
    for r in all_recs:
        recs_by_cluster[r.cluster_id].append(
            {
                "source_topic": r.source_topic,
                "target_topic": r.target_topic,
                "improvement_rate": round(r.improvement_rate, 2),
                "sample_size": r.sample_size,
                "description": r.description,
            }
        )

    # Build suggestions by matching clusters to error types in Python
    suggestions = []
    for error_type, count in error_counts:
        matched = 0
        for cluster in all_clusters:
            if error_type in cluster.error_pattern and matched < 2:
                suggestions.append(
                    {
                        "error_type": error_type,
                        "error_count": count,
                        "cluster": {
                            "id": cluster.id,
                            "pattern": cluster.error_pattern,
                            "student_count": cluster.student_count,
                        },
                        "recommendations": recs_by_cluster.get(cluster.id, [])[:5],
                    }
                )
                matched += 1

    return suggestions


async def build_error_clusters(
    *,
    db: AsyncSession,
    subject: str,
    min_cluster_size: int = 3,
) -> dict:
    """Batch job: rebuild error clusters from student_answers data.

    Should be run weekly via Celery task.
    """
    from models.exam_db import StudentAnswer

    # Get all wrong answers with error types for this subject
    result = await db.execute(
        select(
            StudentAnswer.student_id,
            StudentAnswer.error_type,
        ).where(
            StudentAnswer.is_correct == False,  # noqa: E712
            StudentAnswer.error_type.isnot(None),
        )
    )
    rows = result.all()

    # Count error patterns
    pattern_students: dict[str, set[str]] = {}
    for student_id, error_type in rows:
        key = f"{error_type}:{subject}"
        if key not in pattern_students:
            pattern_students[key] = set()
        pattern_students[key].add(student_id)

    # Create/update clusters
    created = 0
    updated = 0
    for pattern, students in pattern_students.items():
        if len(students) < min_cluster_size:
            continue

        existing = await db.execute(
            select(ErrorCluster).where(
                ErrorCluster.error_pattern == pattern,
                ErrorCluster.subject == subject.upper(),
            )
        )
        cluster = existing.scalar_one_or_none()

        if cluster:
            cluster.student_count = len(students)
            updated += 1
        else:
            cluster = ErrorCluster(
                subject=subject.upper(),
                error_pattern=pattern,
                student_count=len(students),
                topic_ids=[],
                recommended_remediation={},
            )
            db.add(cluster)
            created += 1

    await db.flush()

    return {
        "subject": subject,
        "clusters_created": created,
        "clusters_updated": updated,
        "total_patterns": len(pattern_students),
    }
