"""Student feedback API — Faz 7.2.

Beta öğrencilerinin hatalı/tuhaf soru raporlaması için endpoint'ler.
Gerçek student feedback ile LLM-circular risk mitigasyonu.

Endpoints:
- POST /api/v1/quality/feedback/flag       — flag oluştur (student)
- GET  /api/v1/quality/feedback/my-flags   — kullanıcının kendi flag'leri
- GET  /api/v1/quality/feedback/summary    — flag aggregate (admin)
- POST /api/v1/quality/feedback/{id}/resolve — admin flag çözümü

Faz 4.1 vision findings'den türetilen flag_type'lar:
- wrong_answer: matematik hesap hatası
- wrong_topic: Aromat-tipi subject_area bug
- solution_visible: image içinde ÇÖZÜM görünür
- incomplete_text: OCR kesim
- other: serbest metin
"""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# S1.2 — reuse @rate_limit decorator from learning_path_v2 (Task 7'de unified'e taşınır)
from api.learning_path_v2 import rate_limit
from core.database import get_async_session
from core.dependencies import (
    AuthenticatedUser,
    get_current_admin_user,
    get_current_user,
)
from models.student_question_flag import StudentQuestionFlag

router = APIRouter(prefix="/api/v1/quality/feedback", tags=["quality-feedback"])


FlagType = Literal[
    "wrong_answer",
    "wrong_topic",
    "solution_visible",
    "incomplete_text",
    "circular",
    "figure_needed",
    "other",
]

ResolutionType = Literal["confirmed", "rejected", "duplicate"]


class FlagCreate(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=64)
    flag_type: FlagType
    note: str | None = Field(None, max_length=2000)


class FlagResponse(BaseModel):
    id: str
    user_id: str
    question_id: str
    flag_type: str
    note: str | None
    created_at: datetime
    resolved_at: datetime | None
    resolution: str | None

    model_config = ConfigDict(from_attributes=True)


class FlagSummaryEntry(BaseModel):
    flag_type: str
    total: int
    unresolved: int


class FlagSummary(BaseModel):
    total_flags: int
    unresolved: int
    by_type: list[FlagSummaryEntry]


class FlagResolve(BaseModel):
    resolution: ResolutionType


@router.post(
    "/flag",
    response_model=FlagResponse,
    status_code=status.HTTP_201_CREATED,
)
@rate_limit("flag_submit")  # S1.2 — 10/minute IP-based rate limit
async def create_flag(
    request: Request,  # Required by slowapi limiter
    payload: FlagCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> FlagResponse:
    """Öğrenci soru hata raporu gönderir."""
    from models.question_bank import QuestionBankItem

    question = await db.get(QuestionBankItem, payload.question_id)
    print(
        f"DEBUG_QUESTION: payload.question_id={payload.question_id}, question={question}"
    )
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question_id not found or constraint violation",
        )

    flag = StudentQuestionFlag(
        id=str(uuid.uuid4()),
        user_id=str(current_user.id),
        question_id=payload.question_id,
        flag_type=payload.flag_type,
        note=payload.note,
    )
    db.add(flag)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        err_str = (str(exc.orig) if exc.orig else str(exc)).lower()
        # S1.1 — distinguish UNIQUE violation from FK violation
        if (
            "uq_student_flags_user_question_type" in err_str
            or "duplicate key" in err_str
            or "unique constraint" in err_str
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu soruyu zaten aynı türde bildirdiniz.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question_id not found or constraint violation",
        ) from exc
    await db.refresh(flag)
    return FlagResponse.model_validate(flag)


@router.get("/my-flags", response_model=list[FlagResponse])
async def list_my_flags(
    limit: int = Query(50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> list[FlagResponse]:
    """Kullanıcının kendi flag geçmişi (son N kayıt)."""
    stmt = (
        select(StudentQuestionFlag)
        .where(StudentQuestionFlag.user_id == str(current_user.id))
        .order_by(StudentQuestionFlag.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [FlagResponse.model_validate(r) for r in rows]


@router.get("/summary", response_model=FlagSummary)
async def get_summary(
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session),
) -> FlagSummary:
    """Admin için flag aggregate (toplam + flag_type bazlı)."""
    total_stmt = select(func.count()).select_from(StudentQuestionFlag)
    unresolved_stmt = (
        select(func.count())
        .select_from(StudentQuestionFlag)
        .where(StudentQuestionFlag.resolved_at.is_(None))
    )
    by_type_stmt = (
        select(
            StudentQuestionFlag.flag_type,
            func.count().label("total"),
            func.sum(
                case(
                    (StudentQuestionFlag.resolved_at.is_(None), 1),
                    else_=0,
                )
            ).label("unresolved"),
        )
        .group_by(StudentQuestionFlag.flag_type)
        .order_by(func.count().desc())
    )

    total = (await db.execute(total_stmt)).scalar_one()
    unresolved = (await db.execute(unresolved_stmt)).scalar_one()
    by_type_rows = (await db.execute(by_type_stmt)).all()

    by_type = [
        FlagSummaryEntry(
            flag_type=row.flag_type,
            total=int(row.total or 0),
            unresolved=int(row.unresolved or 0),
        )
        for row in by_type_rows
    ]
    return FlagSummary(
        total_flags=int(total or 0),
        unresolved=int(unresolved or 0),
        by_type=by_type,
    )


@router.post("/{flag_id}/resolve", response_model=FlagResponse)
async def resolve_flag(
    flag_id: str,
    payload: FlagResolve,
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session),
) -> FlagResponse:
    """Admin bir flag'i karara bağlar."""
    stmt = select(StudentQuestionFlag).where(StudentQuestionFlag.id == flag_id)
    flag = (await db.execute(stmt)).scalar_one_or_none()
    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="flag not found"
        )
    flag.resolution = payload.resolution
    flag.resolved_at = datetime.utcnow()
    flag.resolved_by = str(admin.id)
    await db.commit()
    await db.refresh(flag)
    return FlagResponse.model_validate(flag)
