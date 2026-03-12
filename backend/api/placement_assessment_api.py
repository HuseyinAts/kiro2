"""
Placement Assessment API — F5 Adaptive Assessment Endpoints
16-question Bayesian adaptive test for initial student placement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

if TYPE_CHECKING:
    from services.placement_assessment_service import PlacementAssessment

router = APIRouter(prefix="/api/v1/assessment", tags=["Yerleştirme Sınavı"])
logger = get_logger("placement_assessment_api")

# In-memory session store (production: Redis)
_active_sessions: dict[str, PlacementAssessment] = {}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class StartAssessmentRequest(BaseModel):
    subjects: Optional[list[str]] = Field(
        None, description="Konu filtreleri (ör. ['MATEMATIK','FIZIK']). Boş = tüm konular."
    )


class StartAssessmentResponse(BaseModel):
    session_id: str
    total_questions: int
    current_question: int
    question_id: str
    subject: str
    difficulty: float
    theta_estimate: float
    theta_se: float
    confidence_level: str


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str = Field(..., pattern="^[A-E]$")


class NextQuestionResponse(BaseModel):
    session_id: str
    current_question: int
    total_questions: int
    question_id: Optional[str] = None
    subject: Optional[str] = None
    difficulty: Optional[float] = None
    theta_estimate: float
    theta_se: float
    confidence_level: str
    is_correct: bool
    is_complete: bool


class AssessmentResultResponse(BaseModel):
    session_id: str
    overall: dict
    subjects: dict


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/start",
    response_model=StartAssessmentResponse,
    summary="Yerleştirme sınavı başlat",
)
async def start_assessment(
    request: StartAssessmentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Start an adaptive placement assessment. Returns the first question."""
    from services.placement_assessment_service import (
        start_assessment as _start,
    )

    async with get_db_session_context() as db:
        result = await _start(
            db=db,
            student_id=current_user.id,
            subjects=request.subjects,
        )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result["error"],
        )

    # Store assessment state
    assessment = result.pop("_assessment")
    _active_sessions[result["session_id"]] = assessment

    return StartAssessmentResponse(**result)


@router.post(
    "/answer",
    response_model=NextQuestionResponse,
    summary="Soruya cevap gönder, sonraki soruyu al",
)
async def submit_answer(
    request: AnswerRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Submit answer, update ability estimate, get next question (or result)."""
    assessment = _active_sessions.get(request.session_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sınav oturumu bulunamadı",
        )

    # Verify ownership
    if assessment.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu oturum size ait değil",
        )

    # Check answer correctness server-side
    is_correct = await _check_correctness(request.question_id, request.answer)

    # Record response and update posterior
    theta, se = assessment.record_response(request.question_id, is_correct)

    # Select next question or finish
    next_item = None
    if not assessment.is_complete:
        next_item = assessment.select_next_item()
        if not next_item:
            # No more items available
            pass

    is_complete = assessment.is_complete or next_item is None

    return NextQuestionResponse(
        session_id=request.session_id,
        current_question=assessment.question_count,
        total_questions=MAX_QUESTIONS,
        question_id=next_item.item_id if next_item else None,
        subject=next_item.subject if next_item else None,
        difficulty=next_item.difficulty if next_item else None,
        theta_estimate=round(theta, 3),
        theta_se=round(se, 3),
        confidence_level=assessment.get_confidence_level(),
        is_correct=is_correct,
        is_complete=is_complete,
    )


MAX_QUESTIONS = 16


@router.get(
    "/result/{session_id}",
    response_model=AssessmentResultResponse,
    summary="Yerleştirme sınavı sonucu",
)
async def get_result(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get the knowledge state map after assessment completion."""
    from services.placement_assessment_service import get_knowledge_state

    assessment = _active_sessions.get(session_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sınav oturumu bulunamadı",
        )

    if assessment.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu oturum size ait değil",
        )

    knowledge = get_knowledge_state(assessment)

    return AssessmentResultResponse(
        session_id=session_id,
        overall=knowledge["overall"],
        subjects=knowledge["subjects"],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _check_correctness(question_id: str, answer: str) -> bool:
    """Server-side answer check against question_bank."""
    from sqlalchemy import select as sa_select

    from models.question_bank import QuestionBankItem

    async with get_db_session_context() as db:
        result = await db.execute(
            sa_select(QuestionBankItem.correct_answer).where(
                QuestionBankItem.id == question_id
            )
        )
        row = result.first()

    if not row or not row[0]:
        return False

    correct = row[0].strip().upper()
    if len(correct) > 1:
        correct = correct[0]
    return answer.upper() == correct
