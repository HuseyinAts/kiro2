"""
Mnemonic Hints API — F19 Endpoints

AI-generated Turkish memory aids for frequently-missed YKS questions.
Mnemonics are generated on-demand and cached in the database.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.database import get_db_session_context
from core.dependencies import AuthenticatedUser, get_current_user
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/mnemonics", tags=["Mnemonic Hints"])
logger = get_logger("mnemonic_api")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class MnemonicResponse(BaseModel):
    question_id: str
    has_mnemonic: bool
    mnemonic_hint: str | None = None
    generated_at: str | None = None
    language: str = "tr"


class GenerateMnemonicRequest(BaseModel):
    force: bool = Field(
        default=False,
        description="Mevcut hatırlatıcı varsa yeniden üret",
    )


class GenerateMnemonicResponse(BaseModel):
    question_id: str
    mnemonic_hint: str
    generated_at: str
    was_cached: bool


class BatchGenerateRequest(BaseModel):
    subject: str = Field(..., min_length=1, description="Ders (ör. MATEMATIK)")
    limit: int = Field(
        default=100, ge=1, le=500, description="Toplu üretilecek maksimum soru sayısı"
    )


class BatchGenerateResponse(BaseModel):
    subject: str
    requested: int
    generated: int
    skipped: int
    failed: int
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{question_id}",
    response_model=MnemonicResponse,
    summary="Soru için hatırlatıcı ipucu getir",
    description="Belirtilen soruya ait önceden üretilmiş Türkçe hatırlatıcı ipucunu döner. Mevcut değilse 404 döner.",
)
async def get_mnemonic(
    question_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MnemonicResponse:
    """Get the mnemonic hint for a question.

    Returns a cached AI-generated Turkish memory aid for the given question.
    Returns 404 if no mnemonic has been generated yet — callers should
    follow up with POST /{question_id}/generate in that case.

    Args:
        question_id: UUID of the question.
        current_user: The authenticated student.

    Returns:
        Mnemonic hint if available.

    Raises:
        HTTPException: 404 if no mnemonic exists, 500 on error.
    """
    from services.mnemonic_service import get_mnemonic

    try:
        async with get_db_session_context() as db:
            result = await get_mnemonic(db=db, question_id=question_id)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bu soru için hatırlatıcı ipucu bulunamadı",
            )

        return MnemonicResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Hatırlatıcı getirme hatası: {e}",
            extra_data={"user": current_user.id, "question_id": question_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hatırlatıcı ipucu alınırken hata oluştu",
        )


@router.post(
    "/{question_id}/generate",
    response_model=GenerateMnemonicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Soru için hatırlatıcı ipucu üret",
    description="Belirtilen soru için LLM kullanarak Türkçe hatırlatıcı ipucu üretir ve veritabanına kaydeder.",
)
async def generate_mnemonic(
    question_id: str,
    request: GenerateMnemonicRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GenerateMnemonicResponse:
    """Generate a mnemonic hint for a question using the LLM.

    Calls the AI service to create a memorable Turkish phrase or story
    that helps students recall the correct answer. Results are cached
    so subsequent GET requests return immediately without re-generating.

    Args:
        question_id: UUID of the question.
        request: Whether to force regeneration even if one already exists.
        current_user: The authenticated student.

    Returns:
        The newly generated (or cached) mnemonic hint.

    Raises:
        HTTPException: 404 if question not found, 500 on error.
    """
    from services.mnemonic_service import generate_mnemonic

    try:
        async with get_db_session_context() as db:
            result = await generate_mnemonic(
                db=db,
                question_id=question_id,
                force=request.force,
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

        return GenerateMnemonicResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Hatırlatıcı üretme hatası: {e}",
            extra_data={"user": current_user.id, "question_id": question_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hatırlatıcı ipucu üretilirken hata oluştu",
        )


@router.post(
    "/batch",
    response_model=BatchGenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="[Admin] Toplu hatırlatıcı üret",
    description="Belirtilen ders için henüz hatırlatıcısı olmayan sorulara toplu LLM üretimi yapar.",
)
async def batch_generate_mnemonics(
    request: BatchGenerateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> BatchGenerateResponse:
    """Batch generate mnemonic hints for a subject.

    Admin operation: iterates through questions in the subject that
    lack mnemonics and generates hints via the LLM in bulk.
    Accepted with 202 — large batches run asynchronously.

    Args:
        request: Subject code and maximum number of questions to process.
        current_user: The authenticated user (admin check in service).

    Returns:
        Summary of generated, skipped, and failed counts.

    Raises:
        HTTPException: 403 if not admin, 500 on error.
    """
    from services.mnemonic_service import batch_generate_mnemonics

    try:
        async with get_db_session_context() as db:
            result = await batch_generate_mnemonics(
                db=db,
                subject=request.subject.upper(),
                limit=request.limit,
                requested_by=current_user.id,
            )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result["error"],
            )

        return BatchGenerateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Toplu hatırlatıcı üretme hatası: {e}",
            extra_data={"user": current_user.id, "subject": request.subject},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Toplu üretim sırasında hata oluştu",
        )
