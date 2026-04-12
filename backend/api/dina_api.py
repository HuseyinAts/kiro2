"""
DINA Cognitive Diagnostic API — F11 Endpoints

Deterministic Input, Noisy-And-gate (DINA) model for diagnosing
student mastery of fine-grained nano-skills underlying each question.

Session 151 (prophylactic `list[dict]` sweep): two sibling bugs in the
same file as Session 143 GF65 `estimate_student_mastery`.

1. `get_skill_profile` — `get_student_skill_profile` returns `list[dict]`
   of per-nano-skill mastery rows (or `[]` for a new student). The
   handler did `SkillProfileResponse(**result)` which crashes with
   `TypeError: argument after ** must be a mapping, not list`. Same class
   as Session 143 GF65 DINA (`estimate_student_mastery`) and Session 150
   GF125 error-clusters — now **rule-of-four** for service/caller
   `list[dict]` contract drift (GF65 + GF125 + GF151a + GF151b below).

2. `calibrate_parameters` — three-part bug: (a) the service function is a
   pure sync math routine taking `responses`, `skill_masteries`,
   `q_matrix` — not the `db`, `subject`, `requested_by` kwargs the
   handler passed; (b) the handler `await`ed a sync function; (c) the
   service returns `tuple[dict, dict]`, which `CalibrateResponse(**result)`
   also cannot unpack. The endpoint was unfinished glue code. Degrade to
   503 with a clear "admin calibration pipeline not wired" message,
   matching the GF106/GF113/GF115 schema-drift pattern — a follow-up
   should either wire the full EM pipeline (load responses/masteries/
   q-matrix from DB, call the sync function, persist slip/guess) or
   delete the endpoint.
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
            rows = await get_student_skill_profile(
                db=db,
                student_id=str(current_user.id),
                subject=subject.upper(),
            )
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

    # Service returns list[dict] with shape:
    #   {"nano_skill_id", "skill_name", "subject", "mastery",
    #    "confidence", "response_count", "knowledge_point_id"}
    # Empty list = student has no mastery records yet → 404, so clients
    # can distinguish "no profile data" from a crash.
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{subject} için beceri profili bulunamadı",
        )

    skills = [
        SkillMasteryItem(
            skill_id=str(row["nano_skill_id"]),
            skill_name=str(row.get("skill_name") or row["nano_skill_id"])[:64],
            mastery_prob=float(row["mastery"]),
            mastered=float(row["mastery"]) >= 0.5,
        )
        for row in rows
    ]

    return SkillProfileResponse(
        student_id=str(current_user.id),
        subject=subject.upper(),
        skills=skills,
        profile_updated_at=None,
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

        # Service contract: returns list[dict] of per-nano-skill updates,
        # or [] when the question has no Q-matrix entries (not yet mapped
        # to any nano-skill) — treat [] as 404 so clients can distinguish
        # "question not in DINA model" from a crash.
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soru DINA bilgi haritasında bulunamadı",
            )

        # Map the raw service rows to the response schema. The service
        # does not return skill_name (no join), so fall back to the
        # nano_skill_id short prefix. `mastered` uses the conventional
        # DINA 0.5 threshold on posterior mastery probability.
        updated_skills = [
            SkillMasteryItem(
                skill_id=str(row["nano_skill_id"]),
                skill_name=str(row.get("skill_name") or row["nano_skill_id"])[:64],
                mastery_prob=float(row["mastery"]),
                mastered=float(row["mastery"]) >= 0.5,
            )
            for row in result
        ]

        # Overall delta: average deviation from the neutral 0.5 prior.
        # The service currently does not return per-row prior mastery,
        # so this is a coarse signal rather than a true pre/post delta.
        overall_delta = (
            sum(item.mastery_prob - 0.5 for item in updated_skills)
            / len(updated_skills)
            if updated_skills
            else 0.0
        )

        return MasteryEstimateResponse(
            question_id=request.question_id,
            updated_skills=updated_skills,
            overall_mastery_delta=round(overall_delta, 4),
        )

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
    # Session 151: this handler never worked — the service function is a
    # pure sync math routine with a completely different signature
    # (`responses`, `skill_masteries`, `q_matrix`, `max_iterations`,
    # `convergence_threshold`) and returns `tuple[dict, dict]`, not a
    # response envelope. Wiring the full EM pipeline requires loading
    # responses, current masteries, and the q-matrix from the DB, calling
    # the sync function off the event loop, and persisting the resulting
    # slip/guess parameters — out of scope for a prophylactic fix. Degrade
    # to 503 in the GF106/GF113/GF115 schema-drift pattern until the
    # admin calibration pipeline is either wired or the endpoint is
    # removed.
    logger.warning(
        "DINA calibration endpoint called but pipeline is not wired",
        extra_data={
            "user": current_user.id,
            "subject": request.subject,
            "max_iterations": request.max_iterations,
        },
    )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "DINA kalibrasyon pipeline'ı henüz aktif değil: "
            "admin EM iş akışı yeniden yapılandırılıyor."
        ),
    )
