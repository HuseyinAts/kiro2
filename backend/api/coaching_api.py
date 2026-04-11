"""
Proactive Coaching API — F6 Proaktif AI Koçluk

Endpoints:
  GET  /api/v1/coaching/suggestions                       — Koçluk önerileri
  GET  /api/v1/coaching/burnout-check                     — Burnout sinyali kontrolü
  POST /api/v1/coaching/signals                           — Bağlılık sinyali kaydet
  POST /api/v1/coaching/suggestions/{suggestion_id}/interact — Tıklama/reddetme takibi
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/coaching", tags=["Proaktif Koçluk"])
logger = get_logger("coaching_api")


# ---------------------------------------------------------------------------
# Pydantic modelleri
# ---------------------------------------------------------------------------


class CoachingSuggestionItem(BaseModel):
    id: str
    type: str
    title: str
    message: str
    priority: int
    action_url: str


class BurnoutCheckResponse(BaseModel):
    is_at_risk: bool
    signals: list[str]
    recommendation: str


class RecordSignalRequest(BaseModel):
    signal_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description=(
            "Sinyal türü"
            " (session_duration, post_error_pause, answer_speed_trend)"
        ),
    )
    value: float = Field(
        ...,
        description="Sayısal değer — süre için saniye, trend için normalize skor",
    )


class RecordSignalResponse(BaseModel):
    id: int | None = None
    student_id: str
    signal_type: str
    value: float
    recorded_at: str


class InteractRequest(BaseModel):
    action: str = Field(
        ...,
        pattern="^(clicked|dismissed)$",
        description="'clicked' veya 'dismissed'",
    )


class InteractResponse(BaseModel):
    suggestion_id: str
    student_id: str
    action: str
    recorded_at: str
    success: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/suggestions",
    response_model=list[CoachingSuggestionItem],
    summary="Koçluk önerileri",
    description=(
        "Öğrencinin hata örüntüsü, FSRS birikimi ve oturum sıklığına"
        " göre 1-3 koçluk önerisi döner."
    ),
)
async def get_suggestions(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CoachingSuggestionItem]:
    """Get proactive coaching suggestions for the authenticated student.

    Analyzes weakness patterns, burnout signals and FSRS backlog to
    produce up to 3 prioritized coaching suggestions.

    Args:
        current_user: The authenticated student.

    Returns:
        List of coaching suggestions sorted by priority (1 = highest).

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.proactive_coaching_service import generate_suggestions

    try:
        async with get_db_session_context() as db:
            suggestions = await generate_suggestions(
                db=db, student_id=current_user.id
            )

        return [CoachingSuggestionItem(**s) for s in suggestions]

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Coaching suggestions error",
            extra_data={"user": current_user.id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Koçluk önerileri alınırken hata oluştu",
        )


@router.get(
    "/burnout-check",
    response_model=BurnoutCheckResponse,
    summary="Burnout sinyali kontrolü",
    description=(
        "Öğrencinin son 7 günlük oturum verilerini inceleyerek"
        " burnout riski olup olmadığını değerlendirir."
    ),
)
async def check_burnout(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> BurnoutCheckResponse:
    """Check burnout risk signals for the authenticated student.

    Examines average session duration, session frequency and idle
    periods over the last 7 days. Returns risk flag and signals.

    Args:
        current_user: The authenticated student.

    Returns:
        Burnout risk assessment with signal descriptions and recommendation.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.proactive_coaching_service import detect_burnout_signals

    try:
        async with get_db_session_context() as db:
            result = await detect_burnout_signals(
                db=db, student_id=current_user.id
            )

        return BurnoutCheckResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Burnout check error",
            extra_data={"user": current_user.id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Burnout kontrolü yapılırken hata oluştu",
        )


@router.post(
    "/signals",
    response_model=RecordSignalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bağlılık sinyali kaydet",
    description=(
        "Oturum süresi, hata sonrası duraklama veya cevap hızı gibi"
        " davranışsal sinyalleri kaydeder."
    ),
)
async def record_signal(
    body: RecordSignalRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RecordSignalResponse:
    """Record a behavioral engagement signal.

    Signals feed the burnout detection and coaching suggestion engine.
    Valid signal types: session_duration, post_error_pause,
    answer_speed_trend.

    Args:
        body: Signal type and numeric value.
        current_user: The authenticated student.

    Returns:
        Recorded signal with id and timestamp.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.proactive_coaching_service import record_engagement_signal

    try:
        async with get_db_session_context() as db:
            result = await record_engagement_signal(
                db=db,
                student_id=current_user.id,
                signal_type=body.signal_type,
                value=body.value,
            )

        return RecordSignalResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Signal record error",
            extra_data={
                "user": current_user.id,
                "signal_type": body.signal_type,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sinyal kaydedilirken hata oluştu",
        )


@router.post(
    "/suggestions/{suggestion_id}/interact",
    response_model=InteractResponse,
    status_code=status.HTTP_200_OK,
    summary="Öneri etkileşimi kaydet",
    description=(
        "Öğrencinin bir koçluk önerisine tıklama veya"
        " reddetme eylemini kaydeder."
    ),
)
async def interact_with_suggestion(
    suggestion_id: str,
    body: InteractRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> InteractResponse:
    """Track click or dismiss interaction for a coaching suggestion.

    Records whether the student acted on or dismissed a suggestion.
    Used to measure coaching effectiveness and tune future suggestions.

    Args:
        suggestion_id: UUID string of the coaching suggestion.
        body: Interaction action — 'clicked' or 'dismissed'.
        current_user: The authenticated student.

    Returns:
        Interaction record with timestamp and success status.

    Raises:
        HTTPException: 400 if action is invalid, 500 on unexpected error.
    """
    from services.proactive_coaching_service import record_suggestion_interaction

    try:
        async with get_db_session_context() as db:
            result = await record_suggestion_interaction(
                db=db,
                suggestion_id=suggestion_id,
                student_id=current_user.id,
                action=body.action,
            )

        if not result.get("success") and "Geçersiz" in result.get("error", ""):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return InteractResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Suggestion interact error",
            extra_data={
                "user": current_user.id,
                "suggestion_id": suggestion_id,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Etkileşim kaydedilirken hata oluştu",
        )
