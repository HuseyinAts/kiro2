"""
KIRO2 — FSRS API Router
========================
Endpoint'ler:
  GET  /api/v1/fsrs/due                → Vadesi gelen kartları listele
  POST /api/v1/fsrs/review             → Tek yanıt güncelleme (standalone)
  GET  /api/v1/fsrs/stats              → Kullanıcı istatistikleri
  GET  /api/v1/fsrs/due-count          → Hızlı kart sayısı (badge için)
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db
from app.schemas.fsrs_schemas import (
    DueCountResponse,
    DueItemResponse,
    ReviewRequest,
    ReviewResponse,
    StatsResponse,
)
from app.services.fsrs_service import FSRSService

router = APIRouter(prefix="/api/v1/fsrs", tags=["FSRS"])


@router.get(
    "/due",
    response_model=list[DueItemResponse],
    summary="Vadesi gelen tekrar kartlarını getir",
)
async def get_due_items(
    subject_id: UUID | None = Query(None, description="Derse göre filtrele"),
    limit:      int            = Query(20,  ge=1, le=100),
    current_user: User         = Depends(get_current_user),
    db: AsyncSession           = Depends(get_db),
) -> list[DueItemResponse]:
    svc = FSRSService(db)
    items = await svc.get_due_items(
        str(current_user.id),
        subject_id=str(subject_id) if subject_id else None,
        limit=limit,
    )
    return [
        DueItemResponse(
            question_id=s.question_id,
            stability=round(s.stability, 3),
            difficulty=round(s.difficulty, 2),
            due_date=s.due_date,
            retrievability=round(s.retrievability, 3),
            urgency_score=round(s.urgency_score, 3),
            state=s.state,
            reps=s.reps,
            lapses=s.lapses,
            stem=irt.get("question_text"),
            options={
                "A": irt.get("option_a", ""),
                "B": irt.get("option_b", ""),
                "C": irt.get("option_c", ""),
                "D": irt.get("option_d", ""),
            },
            subject_id=irt.get("subject_id"),
        )
        for s, irt in items
    ]


@router.post(
    "/review",
    response_model=ReviewResponse,
    summary="Standalone tekrar yanıtla (CAT dışı)",
)
async def submit_review(
    body:         ReviewRequest,
    current_user: User         = Depends(get_current_user),
    db: AsyncSession           = Depends(get_db),
) -> ReviewResponse:
    svc    = FSRSService(db)
    result = await svc.apply_review(
        user_id=str(current_user.id),
        question_id=str(body.question_id),
        is_correct=body.is_correct,
        response_ms=body.response_ms,
        item_b=body.item_b,
    )
    ns = result.new_state
    return ReviewResponse(
        question_id=ns.question_id,
        new_stability=round(ns.stability, 3),
        new_difficulty=round(ns.difficulty, 2),
        interval_days=result.interval_days,
        due_date=ns.due_date,
        state=ns.state,
        puan=result.puan,
    )


@router.get(
    "/due-count",
    response_model=DueCountResponse,
    summary="Vadesi gelen kart sayısı (hızlı)",
)
async def get_due_count(
    current_user: User       = Depends(get_current_user),
    db: AsyncSession         = Depends(get_db),
) -> DueCountResponse:
    svc   = FSRSService(db)
    count = await svc.get_due_count(str(current_user.id))
    return DueCountResponse(count=count)


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Öğrencinin FSRS istatistikleri",
)
async def get_stats(
    current_user: User       = Depends(get_current_user),
    db: AsyncSession         = Depends(get_db),
) -> StatsResponse:
    from sqlalchemy import text

    result = await db.execute(text("""
        SELECT
            COUNT(*)                                            AS total,
            SUM(CASE WHEN state = 0 THEN 1 ELSE 0 END)         AS new_count,
            SUM(CASE WHEN state IN (1,3) THEN 1 ELSE 0 END)    AS learning,
            SUM(CASE WHEN state = 2 THEN 1 ELSE 0 END)         AS review,
            SUM(CASE WHEN due_date <= NOW() + INTERVAL '4 hours'
                      AND state IN (1,2,3)
                     THEN 1 ELSE 0 END)                         AS due_now,
            ROUND(AVG(stability)::NUMERIC, 2)                  AS avg_stability,
            SUM(lapses)                                         AS total_lapses
        FROM user_item_fsrs
        WHERE user_id = :uid
    """), {"uid": str(current_user.id)})

    row = result.fetchone()
    if not row or not row.total:
        return StatsResponse()

    return StatsResponse(
        total_cards=int(row.total),
        new_count=int(row.new_count or 0),
        learning_count=int(row.learning or 0),
        review_count=int(row.review or 0),
        due_now=int(row.due_now or 0),
        avg_stability=float(row.avg_stability or 0),
        total_lapses=int(row.total_lapses or 0),
    )
