"""
Error Cluster API — F15 Endpoints

Collaborative filtering of student error patterns: cluster similar mistakes,
surface peer recommendations, and reveal individual error signatures.
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
    """Get error clusters for a specific topic.

    Groups common student mistakes into clusters to identify recurring
    misconceptions. Useful for targeted remediation.

    Args:
        subject: Subject code (e.g. MATEMATIK, FIZIK).
        topic_id: Topic identifier within the subject.
        current_user: The authenticated student.

    Returns:
        List of error clusters with misconception labels.

    Raises:
        HTTPException: 404 if topic not found, 500 on error.
    """
    from services.error_cluster_service import get_error_clusters_for_topic

    try:
        async with get_db_session_context() as db:
            result = await get_error_clusters_for_topic(
                db=db,
                subject=subject.upper(),
                topic_id=topic_id,
            )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Konu bulunamadı veya hata verisi yok",
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return ErrorClustersResponse(**result)

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


@router.get(
    "/recommendations/{cluster_id}",
    response_model=PeerRecommendationsResponse,
    summary="Küme için akran önerileri",
    description="Belirli bir hata kümesine düşen öğrenciler için akranların başarılı olduğu kaynak önerilerini döner.",
)
async def get_peer_recommendations(
    cluster_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PeerRecommendationsResponse:
    """Get peer recommendations for a specific error cluster.

    Uses collaborative filtering to surface resources and strategies
    that helped students who previously fell into this error cluster.

    Args:
        cluster_id: Unique identifier of the error cluster.
        current_user: The authenticated student.

    Returns:
        Ranked list of peer-validated recommendations.

    Raises:
        HTTPException: 404 if cluster not found, 500 on error.
    """
    from services.error_cluster_service import get_peer_recommendations

    try:
        async with get_db_session_context() as db:
            result = await get_peer_recommendations(
                db=db,
                cluster_id=cluster_id,
                student_id=current_user.id,
            )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Küme bulunamadı",
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return PeerRecommendationsResponse(**result)

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
    recurring weak spots and actionable fix suggestions.

    Args:
        subject: Subject code (e.g. MATEMATIK, FIZIK).
        current_user: The authenticated student.

    Returns:
        Error pattern summary with suggested remediation per topic.

    Raises:
        HTTPException: 500 on error.
    """
    from services.error_cluster_service import cluster_student_errors

    try:
        async with get_db_session_context() as db:
            result = await cluster_student_errors(
                db=db,
                student_id=current_user.id,
                subject=subject.upper(),
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return StudentErrorPatternsResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Öğrenci hata örüntüleri hatası: {e}",
            extra_data={"user": current_user.id, "subject": subject},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hata örüntüleri alınırken hata oluştu",
        )
