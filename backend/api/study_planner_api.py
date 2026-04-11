"""
Study Planner API — F7 Çalışma Planlayıcı

Endpoints:
  GET   /api/v1/study-plan/current              — Aktif plan
  POST  /api/v1/study-plan/                     — Plan oluştur / güncelle
  PATCH /api/v1/study-plan/weekly/{week_number} — Haftalık ilerleme güncelle
  GET   /api/v1/study-plan/projection           — Puan projeksiyonu
  GET   /api/v1/study-plan/weekly-report        — Bu hafta plan vs gerçek
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/study-plan", tags=["Study Planner"])
logger = get_logger("study_planner_api")


# ---------------------------------------------------------------------------
# Pydantic modelleri
# ---------------------------------------------------------------------------


class WeekGoalItem(BaseModel):
    week_number: int
    topics: list[str]
    target_questions: int
    completed_questions: int
    accuracy: float | None = None
    is_current: bool


class StudyPlanResponse(BaseModel):
    plan_id: str | int
    yks_date: str
    days_left: int
    total_weeks: int
    current_week: int
    weekly_hours: int
    total_target_questions: int
    total_completed_questions: int
    overall_completion_rate: float
    weeks: list[WeekGoalItem]


class CreatePlanRequest(BaseModel):
    yks_date: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="YKS tarihi (ISO format: YYYY-MM-DD)",
    )
    weekly_hours: int = Field(
        default=20, ge=1, le=168, description="Haftada planlanmış çalışma saati"
    )


class UpdateWeeklyProgressRequest(BaseModel):
    completed_questions: int = Field(..., ge=0, description="Tamamlanan soru sayısı")


class SubjectProjectionItem(BaseModel):
    subject: str
    projected_net: float
    ability: float
    p_correct: float


class ScoreProjectionResponse(BaseModel):
    projected_net: float
    confidence_interval: list[float]
    trend: str
    simulation_runs: int
    subject_projections: list[SubjectProjectionItem]


class WeeklyReportResponse(BaseModel):
    week_number: int
    target_questions: int
    completed_questions: int
    completion_rate: float
    topics: list[str]
    days_remaining_in_week: int
    daily_target_to_catch_up: int
    on_track: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/current",
    response_model=StudyPlanResponse,
    summary="Aktif çalışma planı",
    description=(
        "Öğrencinin aktif çalışma planını tüm haftalık hedeflerle"
        " birlikte döner. Plan yoksa 404 döner."
    ),
)
async def get_current_plan(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StudyPlanResponse:
    """Get the active study plan for the authenticated student.

    Returns all weekly goals with target/completed questions and topic
    assignments. Returns 404 if no active plan exists.

    Args:
        current_user: The authenticated student.

    Returns:
        Full study plan with weekly breakdown.

    Raises:
        HTTPException: 404 if no active plan, 500 on unexpected error.
    """
    from services.study_planner_service import get_current_plan

    try:
        async with get_db_session_context() as db:
            plan = await get_current_plan(db=db, student_id=current_user.id)

        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Aktif çalışma planı bulunamadı."
                    " Lütfen önce bir plan oluşturun."
                ),
            )

        return StudyPlanResponse(**plan)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Get current plan error",
            extra_data={"user": current_user.id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Çalışma planı alınırken hata oluştu",
        )


@router.post(
    "/",
    response_model=StudyPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Plan oluştur / güncelle",
    description=(
        "Yeni bir çalışma planı oluşturur. Mevcut aktif plan varsa"
        " devre dışı bırakılır ve yenisi devreye girer."
    ),
)
async def create_or_update_plan(
    body: CreatePlanRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StudyPlanResponse:
    """Create or replace the active study plan.

    Deactivates any existing active plan and creates a new one
    with weekly goals distributed based on IRT ability estimates.

    Args:
        body: YKS date and weekly study hours.
        current_user: The authenticated student.

    Returns:
        Newly created study plan.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.study_planner_service import create_or_update_plan

    try:
        async with get_db_session_context() as db:
            plan = await create_or_update_plan(
                db=db,
                student_id=current_user.id,
                yks_date=body.yks_date,
                weekly_hours=body.weekly_hours,
            )

        return StudyPlanResponse(**plan)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Create plan error",
            extra_data={
                "user": current_user.id,
                "yks_date": body.yks_date,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Çalışma planı oluşturulurken hata oluştu",
        )


@router.patch(
    "/weekly/{week_number}",
    response_model=dict,
    summary="Haftalık ilerleme güncelle",
    description="Belirtilen haftanın tamamlanan soru sayısını günceller.",
)
async def update_weekly_progress(
    week_number: int = Path(
        ..., ge=1, le=200, description="Hafta numarası (1-indexed)"
    ),
    body: UpdateWeeklyProgressRequest = ...,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Update completed question count for a specific week.

    Args:
        week_number: Week number within the plan (1-indexed).
        body: Number of completed questions for the week.
        current_user: The authenticated student.

    Returns:
        Updated week progress with completion rate.

    Raises:
        HTTPException: 404 if plan or week not found, 500 on error.
    """
    from services.study_planner_service import update_weekly_progress

    try:
        async with get_db_session_context() as db:
            result = await update_weekly_progress(
                db=db,
                student_id=current_user.id,
                week_number=week_number,
                completed_questions=body.completed_questions,
            )

        if "error" in result:
            if "bulunamadı" in result["error"]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["error"],
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Update weekly progress error",
            extra_data={
                "user": current_user.id,
                "week_number": week_number,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Haftalık ilerleme güncellenirken hata oluştu",
        )


@router.get(
    "/projection",
    response_model=ScoreProjectionResponse,
    summary="Puan projeksiyonu",
    description=(
        "Monte Carlo simülasyonu ile tahmini YKS net skorunu"
        " ve %90 güven aralığını hesaplar."
    ),
)
async def get_score_projection(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ScoreProjectionResponse:
    """Get projected YKS score via Monte Carlo simulation.

    Runs 1000 simulations using IRT ability estimates per subject.
    Returns median projected net, 90% confidence interval (p5-p95),
    trend analysis from recent weeks, and per-subject breakdown.

    Args:
        current_user: The authenticated student.

    Returns:
        Score projection with confidence interval and subject details.

    Raises:
        HTTPException: 500 on unexpected error.
    """
    from services.study_planner_service import project_score

    try:
        async with get_db_session_context() as db:
            result = await project_score(db=db, student_id=current_user.id)

        return ScoreProjectionResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Score projection error",
            extra_data={"user": current_user.id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Puan projeksiyonu hesaplanırken hata oluştu",
        )


@router.get(
    "/weekly-report",
    response_model=WeeklyReportResponse,
    summary="Bu hafta plan vs gerçek",
    description=(
        "Mevcut haftanın hedef ve gerçekleşen soru sayılarını,"
        " kalan günleri ve yetişmek için gereken günlük hedefi döner."
    ),
)
async def get_weekly_report(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WeeklyReportResponse:
    """Get current week plan vs actual comparison.

    Shows target vs completed questions, days remaining in the week,
    daily catch-up target, and whether the student is on track.

    Args:
        current_user: The authenticated student.

    Returns:
        Weekly progress report.

    Raises:
        HTTPException: 404 if no active plan, 500 on unexpected error.
    """
    from services.study_planner_service import get_weekly_report

    try:
        async with get_db_session_context() as db:
            result = await get_weekly_report(db=db, student_id=current_user.id)

        if "error" in result:
            if "bulunamadı" in result["error"]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["error"],
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return WeeklyReportResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Weekly report error",
            extra_data={"user": current_user.id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Haftalık rapor alınırken hata oluştu",
        )
