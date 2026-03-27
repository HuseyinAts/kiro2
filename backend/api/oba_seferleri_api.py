"""
Oba Seferleri API — Takim Gorevleri (F3)
Endpoints: /api/v1/oba-seferleri/*

- Aktif gorev gor
- Bireysel katki
- Gorev tamamlama kontrolu
- Gorev gecmisi
"""

import logging
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.oba_seferleri import ObaChallenge, ObaChallengeProgress

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/oba-seferleri", tags=["Oba Seferleri"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ContributeRequest(BaseModel):
    amount: int = Field(..., ge=1, le=100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/active/{oba_id}", response_model=dict[str, Any])
async def get_active_challenge(
    oba_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Obanin aktif gorevini getir."""
    today = date.today()

    result = await db.execute(
        select(ObaChallenge).where(
            ObaChallenge.oba_id == oba_id,
            ObaChallenge.status == "active",
            ObaChallenge.start_date <= today,
            ObaChallenge.end_date >= today,
        )
    )
    challenge = result.scalar_one_or_none()

    if not challenge:
        return {
            "success": True,
            "data": None,
            "message": "Bu hafta aktif gorev yok.",
        }

    # Bireysel katkilari getir
    progress_result = await db.execute(
        select(ObaChallengeProgress)
        .where(ObaChallengeProgress.challenge_id == challenge.id)
        .order_by(ObaChallengeProgress.contribution.desc())
    )
    progress_list = progress_result.scalars().all()

    return {
        "success": True,
        "data": {
            "challenge": {
                "id": challenge.id,
                "title": challenge.title,
                "description": challenge.description,
                "challenge_type": challenge.challenge_type,
                "target_value": challenge.target_value,
                "current_value": challenge.current_value,
                "progress_pct": round(
                    (challenge.current_value / max(challenge.target_value, 1)) * 100, 1
                ),
                "bonus_xp_per_member": challenge.bonus_xp_per_member,
                "completed": challenge.completed,
                "start_date": challenge.start_date.isoformat(),
                "end_date": challenge.end_date.isoformat(),
            },
            "contributors": [
                {
                    "student_id": p.student_id,
                    "contribution": p.contribution,
                    "ratio": round(p.contribution_ratio, 2),
                }
                for p in progress_list
            ],
        },
    }


@router.post("/contribute/{challenge_id}", response_model=dict[str, Any])
async def contribute(
    challenge_id: str,
    body: ContributeRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Goreve katki ekle (otomatik veya manuel)."""
    from api.auth import _check_rate_limit, _record_attempt

    _check_rate_limit(request, "oba_contribute")
    _record_attempt(request, "oba_contribute")
    user_id = str(current_user.id)

    # Gorev kontrolu
    c_result = await db.execute(
        select(ObaChallenge).where(
            ObaChallenge.id == challenge_id,
            ObaChallenge.status == "active",
        )
    )
    challenge = c_result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(404, "Aktif gorev bulunamadi.")
    if challenge.completed:
        raise HTTPException(400, "Gorev zaten tamamlandi.")

    # Bireysel progress bul veya olustur
    p_result = await db.execute(
        select(ObaChallengeProgress).where(
            ObaChallengeProgress.challenge_id == challenge_id,
            ObaChallengeProgress.student_id == user_id,
        )
    )
    progress = p_result.scalar_one_or_none()

    if not progress:
        progress = ObaChallengeProgress(
            challenge_id=challenge_id,
            student_id=user_id,
        )
        db.add(progress)

    progress.contribution = (progress.contribution or 0) + body.amount
    challenge.current_value = (challenge.current_value or 0) + body.amount

    # Tamamlandi mi?
    completed_now = False
    if challenge.current_value >= challenge.target_value and not challenge.completed:
        challenge.completed = True
        challenge.status = "completed"
        challenge.completed_at = datetime.now(UTC)
        completed_now = True

    # Katki oranini guncelle
    if challenge.current_value > 0:
        progress.contribution_ratio = progress.contribution / challenge.current_value

    await db.commit()

    msg = "Katkiniz eklendi!"
    if completed_now:
        msg = (
            f"Gorev tamamlandi! Tum oba uyelerine +{challenge.bonus_xp_per_member} XP!"
        )

    return {
        "success": True,
        "data": {
            "contribution": progress.contribution,
            "challenge_current": challenge.current_value,
            "challenge_target": challenge.target_value,
            "completed": challenge.completed,
        },
        "message": msg,
    }


@router.get("/history/{oba_id}", response_model=dict[str, Any])
async def get_challenge_history(
    oba_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50),
):
    """Oba gorev gecmisini getir."""
    result = await db.execute(
        select(ObaChallenge)
        .where(ObaChallenge.oba_id == oba_id)
        .order_by(ObaChallenge.created_at.desc())
        .limit(limit)
    )
    challenges = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "title": c.title,
                "challenge_type": c.challenge_type,
                "target_value": c.target_value,
                "current_value": c.current_value,
                "completed": c.completed,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat(),
            }
            for c in challenges
        ],
    }


@router.get("/my-contributions", response_model=dict[str, Any])
async def get_my_contributions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(10, ge=1, le=50),
):
    """Kendi katkilarimi getir."""
    user_id = str(current_user.id)

    result = await db.execute(
        select(ObaChallengeProgress)
        .where(ObaChallengeProgress.student_id == user_id)
        .order_by(ObaChallengeProgress.updated_at.desc())
        .limit(limit)
    )
    contribs = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "challenge_id": c.challenge_id,
                "contribution": c.contribution,
                "ratio": round(c.contribution_ratio, 2),
                "xp_earned": c.xp_earned,
            }
            for c in contribs
        ],
    }
