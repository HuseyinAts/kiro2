"""
DINA Cognitive Diagnostic API — F11 Endpoints

Deterministic Input, Noisy-And-gate (DINA) model for diagnosing
student mastery of fine-grained nano-skills underlying each question.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/dina", tags=["DINA Cognitive Diagnosis"])
logger = get_logger("dina_api")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SkillMasteryItem(BaseModel):
    skill_id: str
    skill_name: str
    mastery_prob: float
    mastered: bool


class SkillProfileResponse(BaseModel):
    student_id: str
    subject: str
    skills: list[SkillMasteryItem]
    profile_updated_at: str | None = None


class MasteryEstimateRequest(BaseModel):
    question_id: str = Field(..., min_length=1, description="Soru UUID'si")
    is_correct: bool = Field(..., description="Öğrenci doğru yanıtladı mı?")


class MasteryEstimateResponse(BaseModel):
    question_id: str
    updated_skills: list[SkillMasteryItem]
    overall_mastery_delta: float


class CalibrateRequest(BaseModel):
    subject: str = Field(..., min_length=1, description="Ders (ör. MATEMATIK)")
    max_iterations: int = Field(
        default=20, ge=1, le=100, description="EM algoritması maksimum iterasyon sayısı"
    )


class CalibrateResponse(BaseModel):
    subject: str
    iterations_run: int
    converged: bool
    log_likelihood: float
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/profile/{subject}",
    response_model=SkillProfileResponse,
    summary="Öğrenci nano-skill ustalık profili",
    description="Belirtilen ders için öğrencinin nano-skill ustalık olasılıklarını döner.",
)
async def get_skill_profile(
    subject: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SkillProfileResponse:
    """Get student's nano-skill mastery profile for a subject.

    Returns probability estimates for each nano-skill derived from
    the student's response history using the DINA model.

    Args:
        subject: Subject code (e.g. MATEMATIK, FIZIK).
        current_user: The authenticated student.

    Returns:
        Per-skill mastery probabilities and binary mastery flags.

    Raises:
        HTTPException: 404 if no profile data exists, 500 on error.
    """
    from services.dina_service import get_student_skill_profile

    try:
        async with get_db_session_context() as db:
            result = await get_student_skill_profile(
                db=db,
                student_id=current_user.id,
                subject=subject.upper(),
            )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{subject} için beceri profili bulunamadı",
            )

        return SkillProfileResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Beceri profili hatası: {e}",
            extra_data={"user": current_user.id, "subject": subject},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Beceri profili alınırken hata oluştu",
        )


@router.post(
    "/estimate",
    response_model=MasteryEstimateResponse,
    summary="Soru cevabına göre ustalık güncelle",
    description="Bir soruya verilen cevap sonrası DINA modeliyle nano-skill ustalık olasılıklarını günceller.",
)
async def estimate_mastery(
    request: MasteryEstimateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MasteryEstimateResponse:
    """Estimate and update mastery after answering a question.

    Uses Bayesian updating via the DINA model to revise nano-skill
    mastery probabilities based on a single question response.

    Args:
        request: Question ID and whether the student answered correctly.
        current_user: The authenticated student.

    Returns:
        Updated skill mastery items and overall mastery delta.

    Raises:
        HTTPException: 404 if question not found, 500 on error.
    """
    from services.dina_service import estimate_student_mastery

    try:
        async with get_db_session_context() as db:
            result = await estimate_student_mastery(
                db=db,
                student_id=current_user.id,
                question_id=request.question_id,
                is_correct=request.is_correct,
            )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soru bulunamadı",
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return MasteryEstimateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Ustalık güncelleme hatası: {e}",
            extra_data={"user": current_user.id, "question_id": request.question_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ustalık güncellenirken hata oluştu",
        )


@router.post(
    "/calibrate",
    response_model=CalibrateResponse,
    summary="[Admin] EM kalibrasyon tetikle",
    description="Belirtilen ders için DINA slip/guess parametrelerini EM algoritmasıyla yeniden kalibre eder.",
)
async def calibrate_parameters(
    request: CalibrateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CalibrateResponse:
    """Trigger EM calibration of DINA parameters for a subject.

    Runs the Expectation-Maximisation algorithm over the response
    history to update slip and guess parameters per nano-skill.
    Admin-only operation — typically run offline or nightly.

    Args:
        request: Subject code and maximum EM iterations.
        current_user: The authenticated user (admin check in service).

    Returns:
        Calibration run summary including convergence status.

    Raises:
        HTTPException: 403 if not admin, 500 on error.
    """
    from services.dina_service import calibrate_parameters

    try:
        async with get_db_session_context() as db:
            result = await calibrate_parameters(
                db=db,
                subject=request.subject.upper(),
                max_iterations=request.max_iterations,
                requested_by=current_user.id,
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result["error"],
            )

        return CalibrateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"DINA kalibrasyon hatası: {e}",
            extra_data={"user": current_user.id, "subject": request.subject},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kalibrasyon sırasında hata oluştu",
        )
