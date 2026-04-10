"""
KIRO2 — DAG API Router
========================
Endpoint'ler:
  GET  /api/v1/dag/topics/{topic_id}/check   → Konuya çalışabilir mi?
  GET  /api/v1/dag/topics/{topic_id}/path    → Öğrenme yolu
  GET  /api/v1/dag/subjects/{subject_id}/next → Sıradaki konu önerisi
  GET  /api/v1/dag/topics                    → Tüm konular (topological sıra)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db, get_redis
from app.services.dag_service import DAGService

router = APIRouter(prefix="/api/v1/dag", tags=["DAG"])


def get_dag_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> DAGService:
    return DAGService(db=db, redis=redis)


@router.get(
    "/topics/{topic_id}/check",
    summary="Konuya çalışmaya hazır mı?",
    description="Önkoşulların mastery durumunu kontrol eder.",
)
async def check_topic_readiness(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    svc: DAGService = Depends(get_dag_service),
):
    result = await svc.check_can_study_topic(str(current_user.id), topic_id)
    return {
        "topic_id": result.topic_id,
        "can_proceed": result.can_proceed,
        "blocking_prereqs": result.blocking_prereqs,
        "warning_prereqs": result.warning_prereqs,
        "mastery_scores": result.mastery_scores,
    }


@router.get(
    "/topics/{topic_id}/path",
    summary="Hedefe giden öğrenme yolu",
)
async def get_learning_path(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    svc: DAGService = Depends(get_dag_service),
):
    path = await svc.get_learning_path_for_user(str(current_user.id), topic_id)
    return {
        "target_topic_id": path.topic_id,
        "ordered_steps": path.ordered_steps,
        "total_topics": path.total_topics,
        "estimated_sessions": path.estimated_sessions,
    }


@router.get(
    "/subjects/{subject_id}/next",
    summary="Sıradaki önerilen konu",
)
async def get_next_topic(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    svc: DAGService = Depends(get_dag_service),
):
    next_tid = await svc.get_next_recommended_topic(str(current_user.id), subject_id)
    return {"next_topic_id": next_tid}


@router.get(
    "/topics",
    summary="Tüm konular (topological sırayla)",
)
async def list_topics(
    subject_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    svc: DAGService = Depends(get_dag_service),
):
    dag = await svc.get_dag()
    if subject_id:
        # topic_hierarchy.subject_area UPPERCASE — defansif normalize
        # (.claude/rules/case-convention.md, Session 134 audit)
        nodes = dag.get_subject_topics(subject_id.upper())
    else:
        nodes = dag.get_all_topics()

    return [
        {
            "topic_id": n.topic_id,
            "name": n.name,
            "subject_id": n.subject_id,
            "level": n.level,
            "prereq_count": len(n.prereqs),
        }
        for n in nodes
    ]
