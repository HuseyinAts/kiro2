"""
Productive Failure API — F9 Endpoints

Pretest-before-instruction cycle: students attempt problems first to activate
prior knowledge, then instruction follows. Growth is measured pre vs post.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/productive-failure", tags=["Productive Failure"])
logger = get_logger("productive_failure_api")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class PretestStartRequest(BaseModel):
    topic_id: str = Field(..., min_length=1, description="Konu ID'si")
    subject: str = Field(..., min_length=1, description="Ders (ör. MATEMATIK)")
    count: int = Field(default=3, ge=1, le=10, description="Pretest soru sayısı")


class PretestStartResponse(BaseModel):
    topic_id: str
    questions: list[dict[str, Any]]
    session_token: str


class PretestResultItem(BaseModel):
    question_id: str = Field(..., description="Soru UUID'si")
    selected_answer: str = Field(..., description="Seçilen cevap (A–E)")
    is_correct: bool = Field(..., description="Doğru mu?")


class PretestSubmitRequest(BaseModel):
    topic_id: str = Field(..., min_length=1, description="Konu ID'si")
    results: list[PretestResultItem] = Field(..., description="Pretest cevap listesi")


class PretestSubmitResponse(BaseModel):
    topic_id: str
    total: int
    correct: int
    score_pct: float
    mastery_before: float
    message: str


class GrowthRequest(BaseModel):
    pretest_results: list[PretestResultItem] = Field(
        ..., description="Öğretim öncesi sonuçlar"
    )
    posttest_results: list[PretestResultItem] = Field(
        ..., description="Öğretim sonrası sonuçlar"
    )


class GrowthResponse(BaseModel):
    pretest_score: float
    posttest_score: float
    growth: float
    growth_pct: float
    productive_failure_effective: bool
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/pretest/start",
    response_model=PretestStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Konuya özel pretest başlat",
    description="Öğrenciye öğretim öncesi soru seti sunar (productive failure döngüsü).",
)
async def start_pretest(
    request: PretestStartRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PretestStartResponse:
    """Start a pretest session for a topic.

    Questions are served before instruction to activate prior knowledge
    and promote deeper learning through initial productive struggle.

    Args:
        request: Topic, subject, and desired question count.
        current_user: The authenticated student.

    Returns:
        Pretest questions and a session token for tracking.

    Raises:
        HTTPException: 400 if topic is invalid, 500 on unexpected error.
    """
    from services.productive_failure_service import get_pretest_questions

    try:
        async with get_db_session_context() as db:
            result = await get_pretest_questions(
                db=db,
                student_id=current_user.id,
                topic_id=request.topic_id,
                subject=request.subject,
                count=request.count,
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return PretestStartResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Pretest başlatma hatası: {e}",
            extra_data={"user": current_user.id, "topic_id": request.topic_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pretest başlatılırken hata oluştu",
        )


@router.post(
    "/pretest/submit",
    response_model=PretestSubmitResponse,
    summary="Pretest sonuçlarını kaydet",
    description="Öğrencinin pretest cevaplarını kaydeder ve başlangıç ustalık seviyesini hesaplar.",
)
async def submit_pretest(
    request: PretestSubmitRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PretestSubmitResponse:
    """Submit pretest results and record baseline mastery.

    Establishes the student's prior knowledge level before instruction.
    This record is used later to calculate learning growth via /growth.

    Args:
        request: Topic ID and list of answered question results.
        current_user: The authenticated student.

    Returns:
        Score summary and baseline mastery level.

    Raises:
        HTTPException: 400 on validation error, 500 on unexpected error.
    """
    from services.productive_failure_service import record_pretest_result

    try:
        results_payload = [item.model_dump() for item in request.results]

        async with get_db_session_context() as db:
            result = await record_pretest_result(
                db=db,
                student_id=current_user.id,
                topic_id=request.topic_id,
                results=results_payload,
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return PretestSubmitResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Pretest kayıt hatası: {e}",
            extra_data={"user": current_user.id, "topic_id": request.topic_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pretest kaydedilirken hata oluştu",
        )


@router.post(
    "/growth",
    response_model=GrowthResponse,
    summary="Pretest–posttest büyüme hesapla",
    description=(
        "Öğretim öncesi (pretest) ve sonrası (posttest) sonuçlarını karşılaştırarak "
        "öğrenme büyümesini hesaplar. Saf hesaplama — veritabanı işlemi yoktur."
    ),
)
async def calculate_growth(
    request: GrowthRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GrowthResponse:
    """Calculate learning growth between pretest and posttest.

    Pure computation endpoint — no DB write needed.
    Compares baseline vs post-instruction performance to quantify
    the effectiveness of the productive failure cycle.

    Args:
        request: Pretest and posttest result lists.
        current_user: The authenticated student.

    Returns:
        Growth metrics and whether productive failure was effective.

    Raises:
        HTTPException: 400 on invalid input, 500 on unexpected error.
    """
    from services.productive_failure_service import calculate_growth

    try:
        pretest_payload = [item.model_dump() for item in request.pretest_results]
        posttest_payload = [item.model_dump() for item in request.posttest_results]

        result = await calculate_growth(
            student_id=current_user.id,
            pretest_results=pretest_payload,
            posttest_results=posttest_payload,
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return GrowthResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Büyüme hesaplama hatası: {e}",
            extra_data={"user": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Büyüme hesaplanırken hata oluştu",
        )
