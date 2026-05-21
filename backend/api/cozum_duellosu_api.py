"""
Cozum Duellosu API — Solution Duel (F2)
Endpoints: /api/v1/cozum-duellosu/*

- Duello baslat (sistem eslestirmeli)
- Cozum gonder
- Topluluk oylama
- Sonuc gor
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.cozum_duellosu import SolutionDuel, SolutionDuelSubmission, SolutionDuelVote
from services.social_content_filter import get_social_content_filter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cozum-duellosu", tags=["Cozum Duellosu"])

XP_WINNER = 30
XP_LOSER = 10
VOTING_HOURS = 24


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DuelCreate(BaseModel):
    question_bank_id: str
    subject_area: str = Field(..., min_length=2, max_length=50)
    solve_time_seconds: int = Field(300, ge=60, le=900)


class SubmissionCreate(BaseModel):
    body: str = Field(..., min_length=10, max_length=2000)
    image_url: str | None = Field(None, max_length=500)


class DuelVoteCreate(BaseModel):
    submission_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/create", response_model=dict[str, Any])
async def create_duel(
    body: DuelCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Duello olustur — rakip beklemeye al veya mevcut eslestir."""
    user_id = str(current_user.id)

    # Aktif duello kontrolu
    active = await db.execute(
        select(SolutionDuel).where(
            SolutionDuel.status.in_(["waiting", "active"]),
            (SolutionDuel.challenger_id == user_id)
            | (SolutionDuel.opponent_id == user_id),
        )
    )
    if active.scalar_one_or_none():
        raise HTTPException(400, "Zaten aktif bir duellonuz var.")

    # Bekleyen duello var mi? (ayni konu)
    waiting = await db.execute(
        select(SolutionDuel).where(
            SolutionDuel.status == "waiting",
            SolutionDuel.subject_area == body.subject_area,
            SolutionDuel.challenger_id != user_id,
        )
    )
    match = waiting.scalar_one_or_none()

    if match:
        match.opponent_id = user_id
        match.status = "active"
        match.started_at = datetime.now(UTC)
        await db.commit()
        return {
            "success": True,
            "data": {"duel_id": match.id, "matched": True},
            "message": "Rakip bulundu! Duello basladi.",
        }

    # S179 fix (B-P0-42): question_bank_id must exist in question_bank.
    # Pre-fix the literal string "auto" (or any other arbitrary value)
    # was stored, leaving voters unable to ever load the soru.
    from models.question_bank import QuestionBankItem  # local import

    qb_check = await db.execute(
        select(QuestionBankItem.id).where(
            QuestionBankItem.id == body.question_bank_id,
            QuestionBankItem.is_active == True,  # noqa: E712
        )
    )
    if not qb_check.scalar_one_or_none():
        raise HTTPException(
            status_code=422,
            detail={
                "error": "question_bank_id_invalid",
                "message": (
                    "Geçerli bir aktif soru ID'si gerekli. "
                    "'auto' veya rastgele literal kabul edilmez."
                ),
            },
        )

    duel = SolutionDuel(
        question_bank_id=body.question_bank_id,
        subject_area=body.subject_area,
        challenger_id=user_id,
        solve_time_seconds=body.solve_time_seconds,
    )
    db.add(duel)
    await db.commit()

    return {
        "success": True,
        "data": {"duel_id": duel.id, "matched": False},
        "message": "Rakip bekleniyor...",
    }


@router.get("/{duel_id}", response_model=dict[str, Any])
async def get_duel(
    duel_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Duello detayi ve gonderimleri gor."""
    result = await db.execute(select(SolutionDuel).where(SolutionDuel.id == duel_id))
    duel = result.scalar_one_or_none()
    if not duel:
        raise HTTPException(404, "Duello bulunamadi.")

    subs_result = await db.execute(
        select(SolutionDuelSubmission)
        .where(SolutionDuelSubmission.duel_id == duel_id)
        .order_by(SolutionDuelSubmission.submitted_at)
    )
    submissions = subs_result.scalars().all()

    return {
        "success": True,
        "data": {
            "duel": {
                "id": duel.id,
                "question_bank_id": duel.question_bank_id,
                "subject_area": duel.subject_area,
                "challenger_id": duel.challenger_id,
                "opponent_id": duel.opponent_id,
                "status": duel.status,
                "solve_time_seconds": duel.solve_time_seconds,
                "winner_id": duel.winner_id,
                "started_at": duel.started_at.isoformat() if duel.started_at else None,
            },
            "submissions": [
                {
                    "id": s.id,
                    "student_id": s.student_id,
                    "body": s.body,
                    "image_url": s.image_url,
                    "vote_count": s.vote_count,
                    "submitted_at": s.submitted_at.isoformat()
                    if s.submitted_at
                    else None,
                }
                for s in submissions
            ],
        },
    }


@router.post("/{duel_id}/submit", response_model=dict[str, Any])
async def submit_solution(
    duel_id: str,
    body: SubmissionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Duelloya cozum gonder."""
    user_id = str(current_user.id)

    duel_result = await db.execute(
        select(SolutionDuel).where(SolutionDuel.id == duel_id)
    )
    duel = duel_result.scalar_one_or_none()
    if not duel:
        raise HTTPException(404, "Duello bulunamadi.")
    if duel.status != "active":
        raise HTTPException(400, "Duello aktif degil.")
    if user_id not in (duel.challenger_id, duel.opponent_id):
        raise HTTPException(403, "Bu duellonun katilimcisi degilsiniz.")

    # Zaten gonderdi mi?
    existing = await db.execute(
        select(SolutionDuelSubmission).where(
            SolutionDuelSubmission.duel_id == duel_id,
            SolutionDuelSubmission.student_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Zaten cozum gonderdiniz.")

    # Content filter
    content_filter = get_social_content_filter()
    filter_result = await content_filter.filter_content(body.body, user_id)
    if not filter_result.passed:
        raise HTTPException(400, f"Icerik uygun degil: {filter_result.blocked_layer}")

    submission = SolutionDuelSubmission(
        duel_id=duel_id,
        student_id=user_id,
        body=body.body,
        image_url=body.image_url,
    )
    db.add(submission)

    # Iki taraf da gonderdiyse oylama baslasin
    sub_count = (
        await db.execute(
            select(func.count())
            .select_from(SolutionDuelSubmission)
            .where(SolutionDuelSubmission.duel_id == duel_id)
        )
    ).scalar() or 0

    if sub_count >= 1:  # +1 for current = 2
        duel.status = "voting"
        duel.voting_ends_at = datetime.now(UTC) + timedelta(hours=VOTING_HOURS)

    await db.commit()

    return {
        "success": True,
        "data": {"id": submission.id},
        "message": "Cozumunuz gonderildi!",
    }


@router.post("/{duel_id}/vote", response_model=dict[str, Any])
async def vote_duel(
    duel_id: str,
    body: DuelVoteCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Duelloda oy ver — katilimcilar oy veremez."""
    user_id = str(current_user.id)

    duel_result = await db.execute(
        select(SolutionDuel).where(SolutionDuel.id == duel_id)
    )
    duel = duel_result.scalar_one_or_none()
    if not duel:
        raise HTTPException(404, "Duello bulunamadi.")
    if duel.status != "voting":
        raise HTTPException(400, "Oylama aktif degil.")
    if user_id in (duel.challenger_id, duel.opponent_id):
        raise HTTPException(400, "Katilimcilar oy veremez.")

    # Zaten oy verdi mi?
    existing = await db.execute(
        select(SolutionDuelVote).where(
            SolutionDuelVote.duel_id == duel_id,
            SolutionDuelVote.voter_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Zaten oy verdiniz.")

    vote = SolutionDuelVote(
        duel_id=duel_id,
        voter_id=user_id,
        voted_for_id=body.submission_id,
    )
    db.add(vote)

    # Submission oy sayisini artir
    sub_result = await db.execute(
        select(SolutionDuelSubmission).where(
            SolutionDuelSubmission.id == body.submission_id
        )
    )
    sub = sub_result.scalar_one_or_none()
    if sub:
        sub.vote_count = (sub.vote_count or 0) + 1

    await db.commit()

    return {"success": True, "message": "Oyunuz kaydedildi."}


@router.get("/active/list", response_model=dict[str, Any])
async def list_active_duels(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    subject_area: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """Oylama bekleyen duellolari listele."""
    stmt = (
        select(SolutionDuel)
        .where(SolutionDuel.status == "voting")
        .order_by(SolutionDuel.voting_ends_at.asc())
        .limit(limit)
    )
    if subject_area:
        stmt = stmt.where(SolutionDuel.subject_area == subject_area)

    result = await db.execute(stmt)
    duels = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": d.id,
                "subject_area": d.subject_area,
                "question_bank_id": d.question_bank_id,
                "voting_ends_at": d.voting_ends_at.isoformat()
                if d.voting_ends_at
                else None,
            }
            for d in duels
        ],
    }
