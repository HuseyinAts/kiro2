"""
Knowledge Graph API — F4 Granüler Bilgi Haritası

Endpoints:
  GET  /api/v1/knowledge-map/{subject}             — Ön koşul DAG'ı
  GET  /api/v1/knowledge-map/{subject}/state        — Öğrenci hakimiyet katmanı
  GET  /api/v1/knowledge-map/{subject}/suggestions  — Sonraki konu önerileri
  POST /api/v1/knowledge-map/update                 — Cevap sonrası hakimiyet güncelleme
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger
from core.turkish_nlp_utils import normalize_tr

router = APIRouter(prefix="/api/v1/knowledge-map", tags=["Knowledge Map"])
logger = get_logger("knowledge_graph_api")


# ---------------------------------------------------------------------------
# Pydantic modelleri
# ---------------------------------------------------------------------------


class KnowledgeNodeItem(BaseModel):
    id: str
    name: str
    prerequisites: list[str]
    difficulty_range: list[float]


class KnowledgeEdgeItem(BaseModel):
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")

    model_config = {"populate_by_name": True}


class PrerequisiteDagResponse(BaseModel):
    subject: str
    nodes: list[KnowledgeNodeItem]
    edges: list[dict]


class KnowledgeStateItem(BaseModel):
    knowledge_point_id: str
    name: str
    mastery_level: float
    confidence: float
    last_assessed: str | None = None
    status: str  # locked | available | mastered


class TopicSuggestionItem(BaseModel):
    knowledge_point_id: str
    name: str
    mastery_level: float
    reason: str


class UpdateKnowledgeRequest(BaseModel):
    knowledge_point_id: str = Field(..., min_length=1, max_length=100)
    is_correct: bool


class UpdateKnowledgeResponse(BaseModel):
    knowledge_point_id: str
    student_id: str
    old_mastery: float
    new_mastery: float
    delta: float
    is_correct: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{subject}",
    response_model=PrerequisiteDagResponse,
    summary="Ön koşul DAG'ı",
    description=(
        "Belirtilen ders için tüm bilgi noktalarını ve aralarındaki"
        " ön koşul ilişkilerini döner."
    ),
)
async def get_prerequisite_dag(
    subject: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PrerequisiteDagResponse:
    """Get prerequisite DAG for a subject.

    Returns all knowledge points (nodes) and their prerequisite
    relationships (edges) for the given subject. Used to render
    the knowledge map graph.

    Args:
        subject: Subject code (e.g. matematik, fizik).
        current_user: The authenticated student.

    Returns:
        DAG with nodes and directed edges.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.knowledge_graph_service import build_prerequisite_dag

    normalized = normalize_tr(subject)
    try:
        async with get_db_session_context() as db:
            result = await build_prerequisite_dag(db=db, subject=normalized)

        return PrerequisiteDagResponse(
            subject=normalized,
            nodes=[KnowledgeNodeItem(**n) for n in result["nodes"]],
            edges=result["edges"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "DAG fetch error",
            extra_data={"user": current_user.id, "subject": subject, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bilgi haritası yüklenirken hata oluştu",
        )


@router.get(
    "/{subject}/state",
    response_model=list[KnowledgeStateItem],
    summary="Öğrenci hakimiyet katmanı",
    description=(
        "Oturum açmış öğrencinin belirtilen dersteki her bilgi noktasına"
        " ait hakimiyet düzeyini döner."
    ),
)
async def get_student_knowledge_state(
    subject: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[KnowledgeStateItem]:
    """Get mastery overlay for the authenticated student.

    Each knowledge point is annotated with mastery_level (0-1),
    confidence, last assessment date, and status
    (locked / available / mastered).

    Args:
        subject: Subject code.
        current_user: The authenticated student.

    Returns:
        List of knowledge state items ordered by DAG position.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.knowledge_graph_service import get_student_knowledge_state

    normalized = normalize_tr(subject)
    try:
        async with get_db_session_context() as db:
            states = await get_student_knowledge_state(
                db=db,
                student_id=current_user.id,
                subject=normalized,
            )

        return [KnowledgeStateItem(**s) for s in states]

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Knowledge state fetch error",
            extra_data={"user": current_user.id, "subject": subject, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Öğrenci bilgi durumu alınırken hata oluştu",
        )


@router.get(
    "/{subject}/suggestions",
    response_model=list[TopicSuggestionItem],
    summary="Sonraki konu önerileri",
    description=(
        "Kilit açık ve hakimiyeti düşük bilgi noktalarını"
        " sonraki çalışma hedefi olarak önerir."
    ),
)
async def get_topic_suggestions(
    subject: str,
    limit: int = Query(5, ge=1, le=20, description="Maksimum öneri sayısı"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[TopicSuggestionItem]:
    """Get next topic suggestions for the authenticated student.

    Unlocked knowledge points with mastery < 0.8 are ranked by
    lowest mastery first (most urgent topics first).

    Args:
        subject: Subject code.
        limit: Maximum number of suggestions to return.
        current_user: The authenticated student.

    Returns:
        Ranked list of topic suggestions with rationale.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.knowledge_graph_service import suggest_next_topics

    normalized = normalize_tr(subject)
    try:
        async with get_db_session_context() as db:
            suggestions = await suggest_next_topics(
                db=db,
                student_id=current_user.id,
                subject=normalized,
                limit=limit,
            )

        return [TopicSuggestionItem(**s) for s in suggestions]

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Topic suggestions error",
            extra_data={"user": current_user.id, "subject": subject, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Konu önerileri alınırken hata oluştu",
        )


@router.post(
    "/update",
    response_model=UpdateKnowledgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Hakimiyet güncelle",
    description=(
        "Bir soruya verilen cevap sonrası ilgili bilgi noktasının"
        " hakimiyet düzeyini Bayesian yöntemle günceller."
    ),
)
async def update_knowledge_state(
    body: UpdateKnowledgeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UpdateKnowledgeResponse:
    """Update knowledge state after answering a question.

    Uses a simple Bayesian update rule:
      correct → mastery += 0.1 * (1 - mastery)
      wrong   → mastery -= 0.1 * mastery

    Mastery is clamped to [0.0, 1.0].

    Args:
        body: knowledge_point_id and whether the answer was correct.
        current_user: The authenticated student.

    Returns:
        Updated mastery values and delta.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.knowledge_graph_service import update_knowledge_state

    try:
        async with get_db_session_context() as db:
            result = await update_knowledge_state(
                db=db,
                student_id=current_user.id,
                knowledge_point_id=body.knowledge_point_id,
                is_correct=body.is_correct,
            )

        return UpdateKnowledgeResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Knowledge state update error",
            extra_data={
                "user": current_user.id,
                "kp_id": body.knowledge_point_id,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hakimiyet güncellenirken hata oluştu",
        )
