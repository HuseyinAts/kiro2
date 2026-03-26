"""
KIRO2 — Placement Test API
===========================
Endpoint'ler:
  POST /api/v1/placement/start         → Test başlat
  POST /api/v1/placement/{id}/answer   → Yanıt gönder
  GET  /api/v1/placement/{id}          → Durum sorgula
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db, get_redis
from app.services.placement_service import PlacementTestService, _theta_to_label

router = APIRouter(prefix="/api/v1/placement", tags=["Placement Test"])


# ── Schemas ──────────────────────────────────────────────────────


class StartPlacementRequest(BaseModel):
    subject_id: str
    school_type: str = Field(
        "default",
        description="Lise turu: anadolu | fen | ozel | imam_hatip | meslek | default",
    )


class AnswerPlacementRequest(BaseModel):
    """Placement yanıtı — doğruluğu backend belirler (client manipülasyonunu önler)."""

    question_id: str
    answer: str  # "A" | "B" | "C" | "D" | "E"
    response_time_ms: int | None = None


# ── Dependency ───────────────────────────────────────────────────


def get_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> PlacementTestService:
    # Redis None ise direkt bağlan (her backend instance için güvenli fallback)
    if redis is None:
        try:
            import redis.asyncio as _aioredis

            redis = _aioredis.from_url("redis://localhost:6379", decode_responses=False)
        except Exception:
            pass
    return PlacementTestService(db=db, redis=redis)


# ── Endpoints ────────────────────────────────────────────────────


@router.post(
    "/start",
    status_code=status.HTTP_201_CREATED,
    summary="Placement test başlat",
)
async def start_placement(
    body: StartPlacementRequest,
    current_user: User = Depends(get_current_user),
    svc: PlacementTestService = Depends(get_service),
) -> dict[str, Any]:
    try:
        return await svc.start(
            user_id=str(current_user.id),
            subject_id=body.subject_id.upper(),  # DB buyuk harf kullanıyor
            school_type=body.school_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/{session_id}/answer",
    summary="Placement yanıtı gönder",
)
async def answer_placement(
    session_id: str,
    body: AnswerPlacementRequest,
    current_user: User = Depends(get_current_user),
    svc: PlacementTestService = Depends(get_service),
) -> dict[str, Any]:
    state = await svc.get_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Placement oturumu bulunamadi")
    if state.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Erisim reddedildi")

    # Doğruluğu server-side belirle (client manipülasyonunu önler)
    from sqlalchemy import text

    row = await svc.db.execute(
        text(
            "SELECT correct_answer FROM question_bank WHERE id = :qid AND is_active = TRUE"
        ),
        {"qid": body.question_id},
    )
    q_row = row.fetchone()
    if q_row is None:
        raise HTTPException(status_code=404, detail="Soru bulunamadi")
    is_correct = body.answer.upper() == q_row.correct_answer.upper()

    try:
        return await svc.answer(session_id, body.question_id, is_correct)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get(
    "/{session_id}",
    summary="Placement oturum durumu",
)
async def get_placement_state(
    session_id: str,
    current_user: User = Depends(get_current_user),
    svc: PlacementTestService = Depends(get_service),
) -> dict[str, Any]:
    state = await svc.get_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Bulunamadi")
    if state.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Erisim reddedildi")
    return {
        "session_id": state.session_id,
        "theta": state.theta,
        "se": state.se,
        "n_questions": state.n_questions,
        "is_complete": state.is_complete,
        "level_hint": _theta_to_label(
            state.theta
        ),  # PlacementState.level_label yok; fonksiyon kullan
        "b_range": [state.b_min, state.b_max],
    }
