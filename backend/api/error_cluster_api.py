"""
Error Cluster API — F15 Endpoints

Collaborative filtering of student error patterns: cluster similar mistakes,
surface peer recommendations, and reveal individual error signatures.

Session 150 (GF125): three bugs fixed in one sweep.

1. FastAPI route ordering trap. The wildcard `/{subject}/{topic_id}` was
   declared before the static `/my-patterns/{subject}`, so FastAPI greedily
   matched `/my-patterns/MATEMATIK` with `subject="my-patterns"`,
   `topic_id="MATEMATIK"`. Static paths must be declared before wildcards.

2. Service/caller contract drift (identical class to Session 143 GF65
   DINA). `error_cluster_service.get_error_clusters_for_topic`,
   `get_peer_recommendations` and `cluster_student_errors` all return
   `list[dict]`, but the handlers did `ErrorClustersResponse(**result)` etc.
   TypeError on empty list → bare `except Exception` swallowed it → 500.

3. `get_peer_recommendations` handler passed `student_id=` but the
   service signature takes `min_improvement=` — the call would crash with
   TypeError "unexpected keyword argument" on any non-empty cluster.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/error-clusters", tags=["Error Clustering"])
logger = get_logger("error_cluster_api")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ErrorClusterItem(BaseModel):
    cluster_id: str
    cluster_label: str
    error_count: int
    common_misconception: str | None = None
    representative_question_ids: list[str]


class ErrorClustersResponse(BaseModel):
    subject: str
    topic_id: str
    clusters: list[ErrorClusterItem]
    total_clusters: int


class PeerRecommendationItem(BaseModel):
    recommendation_type: str
    title: str
    description: str
    resource_url: str | None = None
    estimated_improvement: float | None = None


class PeerRecommendationsResponse(BaseModel):
    cluster_id: str
    recommendations: list[PeerRecommendationItem]


class StudentErrorPatternItem(BaseModel):
    topic_id: str
    topic_name: str
    cluster_id: str
    error_frequency: int
    last_error_at: str | None = None
    suggested_fix: str | None = None


class StudentErrorPatternsResponse(BaseModel):
    student_id: str
    subject: str
    patterns: list[StudentErrorPatternItem]
    total_errors_analyzed: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
#
# IMPORTANT: static path segments must be declared BEFORE wildcard
# `/{subject}/{topic_id}` or FastAPI will shadow them. See the Session 150
# GF125 root cause in the module docstring.


@router.get(
    "/my-patterns/{subject}",
    response_model=StudentErrorPatternsResponse,
    summary="Öğrencinin hata örüntüleri",
    description="Oturum açmış öğrencinin belirtilen dersteki kişisel hata örüntülerini ve önerilen düzeltmeleri döner.",
)
async def get_my_error_patterns(
    subject: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StudentErrorPatternsResponse:
    """Get the authenticated student's own error patterns for a subject.

    Clusters the student's personal mistake history to highlight
    recurring weak spots and actionable fix suggestions. A student with
    no wrong-answer history returns an empty-patterns envelope, not a 500.
    """
    from services.error_cluster_service import cluster_student_errors

    try:
        async with get_db_session_context() as db:
            suggestions = await cluster_student_errors(
                db=db,
                student_id=str(current_user.id),
                subject=subject.upper(),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(
            f"Öğrenci hata örüntüleri hesaplanamadı: {e}",
            extra_data={"user": current_user.id, "subject": subject},
        )
        # Graceful empty response — feature requires exam history that this
        # student may not yet have.
        return StudentErrorPatternsResponse(
            student_id=str(current_user.id),
            subject=subject.upper(),
            patterns=[],
            total_errors_analyzed=0,
        )

    # Service returns list[dict] with shape:
    #   {"error_type", "error_count", "cluster": {"id", "pattern",
    #    "student_count"}, "recommendations": [...]}
    patterns: list[StudentErrorPatternItem] = []
    total_errors = 0
    for item in suggestions or []:
        cluster = item.get("cluster", {}) or {}
        error_count = int(item.get("error_count", 0))
        total_errors += error_count
        recs = item.get("recommendations") or []
        suggested_fix = recs[0].get("description") if recs else None
        patterns.append(
            StudentErrorPatternItem(
                topic_id=item.get("error_type", "unknown"),
                topic_name=cluster.get("pattern", item.get("error_type", "")),
                cluster_id=str(cluster.get("id", "")),
                error_frequency=error_count,
                last_error_at=None,
                suggested_fix=suggested_fix,
            )
        )

    return StudentErrorPatternsResponse(
        student_id=str(current_user.id),
        subject=subject.upper(),
        patterns=patterns,
        total_errors_analyzed=total_errors,
    )


@router.get(
    "/recommendations/{cluster_id}",
    response_model=PeerRecommendationsResponse,
    summary="Küme için akran önerileri",
    description="Belirli bir hata kümesine düşen öğrenciler için akranların başarılı olduğu kaynak önerilerini döner.",
)
async def get_peer_recommendations_endpoint(
    cluster_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PeerRecommendationsResponse:
    """Get peer recommendations for a specific error cluster."""
    from services.error_cluster_service import get_peer_recommendations

    try:
        async with get_db_session_context() as db:
            recs = await get_peer_recommendations(
                db=db,
                cluster_id=cluster_id,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Akran önerileri hatası: {e}",
            extra_data={"user": current_user.id, "cluster_id": cluster_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Akran önerileri alınırken hata oluştu",
        )

    # Service returns list[dict] with shape:
    #   {"source_topic", "target_topic", "improvement_rate", "sample_size",
    #    "description"}
    items: list[PeerRecommendationItem] = []
    for rec in recs or []:
        items.append(
            PeerRecommendationItem(
                recommendation_type="peer_study",
                title=f"{rec.get('source_topic', '')} → {rec.get('target_topic', '')}",
                description=rec.get("description", ""),
                resource_url=None,
                estimated_improvement=float(rec.get("improvement_rate", 0.0)),
            )
        )

    return PeerRecommendationsResponse(
        cluster_id=cluster_id,
        recommendations=items,
    )


@router.get(
    "/{subject}/{topic_id}",
    response_model=ErrorClustersResponse,
    summary="Konu hata kümelerini getir",
    description="Belirtilen konu için öğrenci hata örüntülerini kümelere ayırarak döner.",
)
async def get_error_clusters(
    subject: str,
    topic_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ErrorClustersResponse:
    """Get error clusters for a specific topic."""
    from services.error_cluster_service import get_error_clusters_for_topic

    try:
        async with get_db_session_context() as db:
            clusters = await get_error_clusters_for_topic(
                db=db,
                subject=subject.upper(),
                topic_id=topic_id,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Hata kümeleri getirme hatası: {e}",
            extra_data={
                "user": current_user.id,
                "subject": subject,
                "topic_id": topic_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hata kümeleri alınırken hata oluştu",
        )

    # Service returns list[dict] with shape:
    #   {"cluster_id", "error_pattern", "student_count", "topic_ids",
    #    "remediation"}
    items: list[ErrorClusterItem] = []
    for c in clusters or []:
        items.append(
            ErrorClusterItem(
                cluster_id=str(c.get("cluster_id", "")),
                cluster_label=c.get("error_pattern", ""),
                error_count=int(c.get("student_count", 0)),
                common_misconception=(
                    (c.get("remediation") or {}).get("misconception")
                    if isinstance(c.get("remediation"), dict)
                    else None
                ),
                representative_question_ids=[],
            )
        )

    return ErrorClustersResponse(
        subject=subject.upper(),
        topic_id=topic_id,
        clusters=items,
        total_clusters=len(items),
    )
