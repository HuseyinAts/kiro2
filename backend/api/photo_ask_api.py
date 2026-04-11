"""
Photo Ask API — F3 "Fotoğrafla Sor" Endpoints
Upload a photo of a question → OCR → find similar questions → AI solve.
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/photo-ask", tags=["Fotoğrafla Sor"])
logger = get_logger("photo_ask_api")

# 10 MB max upload size
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class MatchedQuestion(BaseModel):
    id: str
    question_text: Optional[str] = None
    question_image_url: Optional[str] = None
    exam_type: Optional[str] = None
    subject_area: Optional[str] = None
    source_book: Optional[str] = None
    difficulty: Optional[str] = None
    correct_answer: Optional[str] = None
    options: Optional[dict[str, Optional[str]]] = None
    explanation: Optional[str] = None
    similarity: float


class AISolution(BaseModel):
    solution: str
    model: str
    generated: bool
    error: Optional[str] = None


class PhotoAskResponse(BaseModel):
    status: str  # matched, partial_match, ai_solved, ocr_failed
    ocr_text: str
    ocr_confidence: float
    ocr_time_ms: Optional[int] = None
    matched_questions: list[MatchedQuestion]
    ai_solution: Optional[AISolution] = None
    total_time_ms: int
    message: str


class QuestionSolutionResponse(BaseModel):
    question_id: str
    question_text: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    options: Optional[dict[str, Optional[str]]] = None


# ---------------------------------------------------------------------------
# Upload + process
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=PhotoAskResponse,
    summary="Fotoğraf yükle, OCR + benzer soru ara",
)
async def upload_and_search(
    file: UploadFile = File(...),
    subject: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Upload a photo of a question. Returns OCR text, similar questions, and AI solution."""
    from services.photo_ask_service import process_photo_ask

    # Validate content type
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Desteklenmeyen dosya tipi: {file.content_type}. "
                   f"Desteklenen: {', '.join(ALLOWED_TYPES)}",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Dosya boyutu çok büyük. Maksimum: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Boş dosya yüklendi",
        )

    try:
        async with get_db_session_context() as db:
            result = await process_photo_ask(
                db=db,
                file_content=content,
                filename=file.filename or "upload.jpg",
                subject_area=subject,
                student_id=current_user.id,
            )

        return PhotoAskResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Photo ask error: {e}", extra_data={"user": current_user.id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fotoğraf işlenirken hata oluştu",
        )


# ---------------------------------------------------------------------------
# Get solution for a matched question
# ---------------------------------------------------------------------------

@router.get(
    "/solution/{question_id}",
    response_model=QuestionSolutionResponse,
    summary="Eşleşen sorunun çözümünü getir",
)
async def get_solution(
    question_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get the solution/explanation for a matched question from question_bank."""
    from sqlalchemy import select

    from models.question_bank import QuestionBankItem

    async with get_db_session_context() as db:
        result = await db.execute(
            select(QuestionBankItem).where(
                QuestionBankItem.id == question_id,
                QuestionBankItem.is_active == True,  # noqa: E712
            )
        )
        q = result.scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Soru bulunamadı",
        )

    return QuestionSolutionResponse(
        question_id=str(q.id),
        question_text=q.question_text,
        correct_answer=q.correct_answer,
        explanation=getattr(q, "explanation", None),
        options={
            "A": q.option_a, "B": q.option_b, "C": q.option_c,
            "D": q.option_d, "E": q.option_e,
        },
    )


# ---------------------------------------------------------------------------
# AI solve (standalone, without upload)
# ---------------------------------------------------------------------------

@router.post(
    "/ai-solve",
    summary="AI ile soru çöz (metin girişi)",
)
async def ai_solve(
    question_text: str = "",
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Generate AI solution for a question text (without photo upload)."""
    from services.photo_ask_service import generate_ai_solution

    if not question_text or len(question_text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Soru metni en az 10 karakter olmalı",
        )

    result = await generate_ai_solution(question_text.strip())

    return {
        "question_text": question_text.strip(),
        "solution": result.get("solution", ""),
        "model": result.get("model", ""),
        "generated": result.get("generated", False),
    }
