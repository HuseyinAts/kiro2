"""
Mastery Confidence API — F13

Exposes IRT-based confidence intervals and mastery confidence levels
so the frontend can render uncertainty bands around ability estimates.

Endpoints:
  GET /api/v1/mastery-confidence/{subject}           — Subject-level confidence
  GET /api/v1/mastery-confidence/topics/{subject}    — Per-topic confidence breakdown
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/mastery-confidence", tags=["Mastery Confidence"])
logger = get_logger("mastery_confidence_api")

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

ConfidenceLevel = Literal["low", "medium", "high"]

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SubjectConfidenceResponse(BaseModel):
    """Subject-level mastery confidence response."""

    subject: str
    ability_estimate: float = Field(
        ...,
        ge=-4.0,
        le=4.0,
        description="IRT theta estimate on the [-4, 4] scale",
    )
    confidence_interval_95: list[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="[low, high] bounds of the 95% confidence interval",
    )
    confidence_level: ConfidenceLevel = Field(
        ...,
        description="low (CI width >1.5) | medium (0.8-1.5) | high (<0.8)",
    )
    response_count: int = Field(..., ge=0, description="Number of answered questions")
    message_tr: str = Field(..., description="Human-readable Turkish status message")


class TopicConfidenceItem(BaseModel):
    """Confidence data for a single topic."""

    topic_id: str
    name: str
    mastery: float = Field(..., ge=0.0, le=1.0, description="Mastery level 0-1")
    confidence_level: ConfidenceLevel
    response_count: int = Field(..., ge=0)


class TopicConfidenceResponse(BaseModel):
    """Per-topic confidence breakdown response."""

    subject: str
    topics: list[TopicConfidenceItem]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _compute_confidence_level(ci_low: float, ci_high: float) -> ConfidenceLevel:
    """Derive a categorical confidence level from the CI width.

    Args:
        ci_low: Lower bound of the 95% CI.
        ci_high: Upper bound of the 95% CI.

    Returns:
        'low'    when CI width > 1.5  (noisy estimate, few responses)
        'medium' when CI width 0.8-1.5
        'high'   when CI width < 0.8  (precise estimate)
    """
    width = ci_high - ci_low
    if width > 1.5:
        return "low"
    if width >= 0.8:
        return "medium"
    return "high"


def _build_message_tr(confidence_level: ConfidenceLevel, response_count: int) -> str:
    """Return a Turkish UI message describing the estimate quality.

    Args:
        confidence_level: Categorical confidence.
        response_count: Number of questions the student has answered.

    Returns:
        Human-readable Turkish sentence.
    """
    if confidence_level == "low":
        if response_count == 0:
            return "Henüz soru çözmediniz; tahmin yapılamıyor."
        return (
            f"{response_count} soru çözdünüz, daha fazla veri gerekli. "
            "Daha kesin bir tahmin için en az 10 soru çözün."
        )
    if confidence_level == "medium":
        return (
            f"{response_count} soruya dayalı tahmin. "
            "Orta düzeyde güven; daha fazla pratikle kesinleşecek."
        )
    # high
    return f"Tahminimiz güvenilir — {response_count} soruya dayalı kesin ölçüm."


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{subject}",
    response_model=SubjectConfidenceResponse,
    summary="Konu bazlı mastery güven aralığı",
    description=(
        "Oturum açmış öğrencinin belirtilen derse ait IRT yetenek tahmini,"
        " %95 güven aralığı ve güven seviyesini döner."
    ),
)
async def get_subject_mastery_confidence(
    subject: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SubjectConfidenceResponse:
    """Return IRT ability estimate and confidence interval for a subject.

    Reads the student's answer history for the given subject, runs a
    lightweight MLE ability estimation, and derives the 95% CI from the
    test information function.

    Args:
        subject: Subject code (e.g. 'matematik', 'fizik').
        current_user: The authenticated student.

    Returns:
        Ability estimate, CI bounds, categorical confidence, response count,
        and a Turkish status message.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.mastery_confidence_service import get_subject_confidence

    try:
        async with get_db_session_context() as db:
            data = await get_subject_confidence(
                db=db,
                student_id=current_user.id,
                subject=subject.lower(),
            )

        ci_low, ci_high = data["ci_low"], data["ci_high"]
        confidence_level = _compute_confidence_level(ci_low, ci_high)
        response_count: int = data["response_count"]

        return SubjectConfidenceResponse(
            subject=subject.lower(),
            ability_estimate=round(data["ability"], 4),
            confidence_interval_95=[round(ci_low, 4), round(ci_high, 4)],
            confidence_level=confidence_level,
            response_count=response_count,
            message_tr=_build_message_tr(confidence_level, response_count),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Subject confidence fetch error",
            extra_data={
                "user": current_user.id,
                "subject": subject,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Güven aralığı hesaplanırken hata oluştu",
        )


@router.get(
    "/topics/{subject}",
    response_model=TopicConfidenceResponse,
    summary="Konu içi topic bazlı güven dağılımı",
    description=(
        "Belirtilen dersteki her alt konunun hakimiyet düzeyi ve"
        " güven seviyesini döner."
    ),
)
async def get_topic_mastery_confidence(
    subject: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> TopicConfidenceResponse:
    """Return per-topic mastery and confidence for a subject.

    Aggregates response counts and mastery estimates per topic within
    the given subject and returns a categorical confidence level for each.

    Args:
        subject: Subject code (e.g. 'matematik', 'fizik').
        current_user: The authenticated student.

    Returns:
        List of topics with mastery and confidence_level for each.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.mastery_confidence_service import get_topics_confidence

    try:
        async with get_db_session_context() as db:
            topic_rows = await get_topics_confidence(
                db=db,
                student_id=current_user.id,
                subject=subject.lower(),
            )

        topics = [
            TopicConfidenceItem(
                topic_id=row["topic_id"],
                name=row["name"],
                mastery=round(row["mastery"], 4),
                confidence_level=_compute_confidence_level(
                    row["ci_low"], row["ci_high"]
                ),
                response_count=row["response_count"],
            )
            for row in topic_rows
        ]

        return TopicConfidenceResponse(subject=subject.lower(), topics=topics)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Topic confidence fetch error",
            extra_data={
                "user": current_user.id,
                "subject": subject,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Konu güven dağılımı alınırken hata oluştu",
        )
