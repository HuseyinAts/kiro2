"""
Soru Meydani API — Ogrenci Soru-Cevap Forumu (F1)
Endpoints: /api/v1/soru-meydani/*

- Soru sor (sablon bazli)
- Soru listele (konu filtreli)
- Cozum oner
- Cozume oy ver
- Cozumu kabul et
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.soru_meydani import ForumQuestion, ForumSolution, ForumVote
from services.social_content_filter import get_social_content_filter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/soru-meydani", tags=["Soru Meydani"])

# XP Constants
XP_ASK_QUESTION = 5
XP_SUBMIT_SOLUTION = 10
XP_ACCEPTED_SOLUTION = 25
XP_HELPFUL_VOTE = 2

# Question templates — free text is NOT allowed
QUESTION_TYPES = {
    "how_to_solve": "Bu soruyu nasil cozerim?",
    "explain_concept": "Bu konuyu anlamiyorum, aciklar misiniz?",
    "which_formula": "Hangi formulu kullanmaliyim?",
    "check_my_work": "Cozumum dogru mu?",
    "alternative_method": "Farkli bir cozum yolu var mi?",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class QuestionCreate(BaseModel):
    question_bank_id: str | None = None
    subject_area: str = Field(..., min_length=2, max_length=50)
    topic: str | None = Field(None, max_length=100)
    question_type: str = Field(
        ...,
        pattern=r"^(how_to_solve|explain_concept|which_formula|check_my_work|alternative_method)$",
    )
    title: str = Field(..., min_length=5, max_length=200)
    body: str | None = Field(None, max_length=500)


class SolutionCreate(BaseModel):
    body: str = Field(..., min_length=10, max_length=2000)
    image_url: str | None = Field(None, max_length=500)


class VoteCreate(BaseModel):
    vote_type: str = Field(..., pattern=r"^(helpful|not_helpful)$")


# ---------------------------------------------------------------------------
# Question Endpoints
# ---------------------------------------------------------------------------


@router.post("/questions", response_model=dict[str, Any])
async def ask_question(
    body: QuestionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Soru sor (sablon bazli, content filter ile kontrol)."""
    user_id = str(current_user.id)

    # Content filter
    content_filter = get_social_content_filter()
    text_to_check = f"{body.title} {body.body or ''}"
    filter_result = await content_filter.filter_content(text_to_check, user_id)
    if not filter_result.passed:
        raise HTTPException(
            400,
            f"Icerik uygun degil: {filter_result.blocked_layer}",
        )

    # Gunluk soru limiti (max 5/gun)
    from datetime import UTC, datetime

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_count = (
        await db.execute(
            select(func.count())
            .select_from(ForumQuestion)
            .where(
                ForumQuestion.student_id == user_id,
                ForumQuestion.created_at >= today_start,
            )
        )
    ).scalar() or 0

    if daily_count >= 5:
        raise HTTPException(429, "Gunluk soru limitine ulastiniz (5/gun).")

    question = ForumQuestion(
        student_id=user_id,
        question_bank_id=body.question_bank_id,
        subject_area=body.subject_area,
        topic=body.topic,
        question_type=body.question_type,
        title=body.title,
        body=body.body,
    )
    db.add(question)
    await db.commit()

    return {
        "success": True,
        "data": {"id": question.id, "question_type": body.question_type},
        "message": "Sorunuz yayinlandi!",
    }


@router.get("/questions", response_model=dict[str, Any])
async def list_questions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    subject_area: str | None = Query(None),
    status: str | None = Query(None, pattern=r"^(open|answered|closed)$"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """Soru listele (konu ve durum filtresi)."""
    stmt = (
        select(ForumQuestion)
        .where(ForumQuestion.flagged.is_(False))
        .order_by(ForumQuestion.created_at.desc())
    )

    if subject_area:
        stmt = stmt.where(ForumQuestion.subject_area == subject_area)
    if status:
        stmt = stmt.where(ForumQuestion.status == status)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    questions = result.scalars().all()

    # Count
    count_stmt = (
        select(func.count())
        .select_from(ForumQuestion)
        .where(ForumQuestion.flagged.is_(False))
    )
    if subject_area:
        count_stmt = count_stmt.where(ForumQuestion.subject_area == subject_area)
    if status:
        count_stmt = count_stmt.where(ForumQuestion.status == status)
    total = (await db.execute(count_stmt)).scalar() or 0

    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": q.id,
                    "student_id": q.student_id,
                    "subject_area": q.subject_area,
                    "topic": q.topic,
                    "question_type": q.question_type,
                    "title": q.title,
                    "status": q.status,
                    "solution_count": q.solution_count,
                    "created_at": q.created_at.isoformat() if q.created_at else None,
                }
                for q in questions
            ],
            "total": total,
        },
    }


@router.get("/questions/{question_id}", response_model=dict[str, Any])
async def get_question_detail(
    question_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Soru detayi + cozumleri."""
    result = await db.execute(
        select(ForumQuestion).where(ForumQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(404, "Soru bulunamadi.")

    # Cozumleri getir
    solutions_result = await db.execute(
        select(ForumSolution)
        .where(
            ForumSolution.question_id == question_id,
            ForumSolution.flagged.is_(False),
        )
        .order_by(ForumSolution.helpful_count.desc())
    )
    solutions = solutions_result.scalars().all()

    return {
        "success": True,
        "data": {
            "question": {
                "id": question.id,
                "student_id": question.student_id,
                "subject_area": question.subject_area,
                "topic": question.topic,
                "question_type": question.question_type,
                "title": question.title,
                "body": question.body,
                "status": question.status,
                "solution_count": question.solution_count,
                "accepted_solution_id": question.accepted_solution_id,
                "created_at": question.created_at.isoformat()
                if question.created_at
                else None,
            },
            "solutions": [
                {
                    "id": s.id,
                    "solver_id": s.solver_id,
                    "body": s.body,
                    "image_url": s.image_url,
                    "helpful_count": s.helpful_count,
                    "not_helpful_count": s.not_helpful_count,
                    "is_accepted": s.is_accepted,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in solutions
            ],
        },
    }


# ---------------------------------------------------------------------------
# Solution Endpoints
# ---------------------------------------------------------------------------


@router.post("/questions/{question_id}/solutions", response_model=dict[str, Any])
async def submit_solution(
    question_id: str,
    body: SolutionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Cozum oner (soruyu soran kisi olamaz)."""
    user_id = str(current_user.id)

    # Soru kontrolu
    q_result = await db.execute(
        select(ForumQuestion).where(ForumQuestion.id == question_id)
    )
    question = q_result.scalar_one_or_none()
    if not question:
        raise HTTPException(404, "Soru bulunamadi.")
    if question.student_id == user_id:
        raise HTTPException(400, "Kendi sorunuza cozum oneremezsiniz.")
    if question.status == "closed":
        raise HTTPException(400, "Bu soru kapanmis.")

    # Content filter
    content_filter = get_social_content_filter()
    filter_result = await content_filter.filter_content(body.body, user_id)
    if not filter_result.passed:
        raise HTTPException(
            400,
            f"Icerik uygun degil: {filter_result.blocked_layer}",
        )

    # Gunluk cozum limiti (max 10/gun)
    from datetime import UTC, datetime

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_count = (
        await db.execute(
            select(func.count())
            .select_from(ForumSolution)
            .where(
                ForumSolution.solver_id == user_id,
                ForumSolution.created_at >= today_start,
            )
        )
    ).scalar() or 0

    if daily_count >= 10:
        raise HTTPException(429, "Gunluk cozum limitine ulastiniz (10/gun).")

    solution = ForumSolution(
        question_id=question_id,
        solver_id=user_id,
        body=body.body,
        image_url=body.image_url,
    )
    db.add(solution)

    # Soru cozum sayisini artir
    question.solution_count = (question.solution_count or 0) + 1
    if question.status == "open":
        question.status = "answered"

    await db.commit()

    # S179 fix (B-P0-36): actually write the XP transaction so leaderboard
    # reflects it. Pre-fix the "+10 XP" string was display-only — the
    # XPTransaction row was never created and the leaderboard ignored the
    # solution. award_xp + update_leaderboard chains via services.
    awarded_xp = 0
    try:
        from services.learning_event_service import GamificationDBService

        awarded_xp = XP_SUBMIT_SOLUTION
        await GamificationDBService.award_xp(
            student_id=user_id,
            amount=awarded_xp,
            source="soru_meydani_solution",
            db=db,
        )
        await GamificationDBService.update_leaderboard(student_id=user_id, db=db)
        await db.commit()
    except Exception:
        logger.exception(
            "Soru Meydani XP award FAILED solver=%s solution=%s",
            user_id,
            solution.id,
        )
        # Rollback the XP-only commit so the solution insert survives.
        await db.rollback()
        awarded_xp = 0

    return {
        "success": True,
        "data": {"id": solution.id, "xp_awarded": awarded_xp},
        "message": (
            f"Cozumunuz yayinlandi! +{awarded_xp} XP"
            if awarded_xp
            else "Cozumunuz yayinlandi. XP later olarak hesaplanacak."
        ),
    }


# ---------------------------------------------------------------------------
# Vote Endpoints
# ---------------------------------------------------------------------------


@router.post("/solutions/{solution_id}/vote", response_model=dict[str, Any])
async def vote_solution(
    solution_id: str,
    body: VoteCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Cozume oy ver (kullanici basina 1 kez)."""
    user_id = str(current_user.id)

    # Cozum kontrolu
    s_result = await db.execute(
        select(ForumSolution).where(ForumSolution.id == solution_id)
    )
    solution = s_result.scalar_one_or_none()
    if not solution:
        raise HTTPException(404, "Cozum bulunamadi.")
    if solution.solver_id == user_id:
        raise HTTPException(400, "Kendi cozumunuze oy veremezsiniz.")

    # Daha once oy vermis mi
    existing = await db.execute(
        select(ForumVote).where(
            ForumVote.voter_id == user_id,
            ForumVote.solution_id == solution_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Bu cozume zaten oy verdiniz.")

    vote = ForumVote(
        voter_id=user_id,
        solution_id=solution_id,
        vote_type=body.vote_type,
    )
    db.add(vote)

    # Cozumun oy sayisini guncelle
    if body.vote_type == "helpful":
        solution.helpful_count = (solution.helpful_count or 0) + 1
    else:
        solution.not_helpful_count = (solution.not_helpful_count or 0) + 1

    await db.commit()

    return {
        "success": True,
        "message": "Oyunuz kaydedildi.",
    }


# ---------------------------------------------------------------------------
# Accept Solution
# ---------------------------------------------------------------------------


@router.post(
    "/questions/{question_id}/accept/{solution_id}",
    response_model=dict[str, Any],
)
async def accept_solution(
    question_id: str,
    solution_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Cozumu kabul et (sadece soruyu soran yapabilir)."""
    user_id = str(current_user.id)

    # Soru kontrolu
    q_result = await db.execute(
        select(ForumQuestion).where(ForumQuestion.id == question_id)
    )
    question = q_result.scalar_one_or_none()
    if not question:
        raise HTTPException(404, "Soru bulunamadi.")
    if question.student_id != user_id:
        raise HTTPException(403, "Sadece soruyu soran kabul edebilir.")
    if question.accepted_solution_id:
        raise HTTPException(400, "Zaten kabul edilmis bir cozum var.")

    # Cozum kontrolu
    s_result = await db.execute(
        select(ForumSolution).where(
            ForumSolution.id == solution_id,
            ForumSolution.question_id == question_id,
        )
    )
    solution = s_result.scalar_one_or_none()
    if not solution:
        raise HTTPException(404, "Cozum bulunamadi.")

    # Kabul et
    question.accepted_solution_id = solution_id
    question.status = "closed"
    solution.is_accepted = True
    solution.xp_awarded = XP_ACCEPTED_SOLUTION

    await db.commit()

    return {
        "success": True,
        "message": f"Cozum kabul edildi! Cozen +{XP_ACCEPTED_SOLUTION} XP kazandi.",
    }


# ---------------------------------------------------------------------------
# Question Types (for frontend template selection)
# ---------------------------------------------------------------------------


@router.get("/question-types", response_model=dict[str, Any])
async def get_question_types(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Kullanilabilir soru sablonlarini listele."""
    return {
        "success": True,
        "data": [{"type": k, "label": v} for k, v in QUESTION_TYPES.items()],
    }
