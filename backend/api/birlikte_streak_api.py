"""
Birlikte Streak API — Streak Ortakligi (F5)
Endpoints: /api/v1/birlikte-streak/*

- Streak ortakligi iste (sistem eslestirir)
- Gunluk gorev tamamlandi bildir
- Streak durumu gor
- Ortaklik bitir
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.birlikte_streak import StreakDailyLog, StreakPair

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/birlikte-streak", tags=["Birlikte Streak"])

XP_DAILY_BOTH = 5
XP_7_DAY_BONUS = 30
XP_30_DAY_BONUS = 100


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/request", response_model=dict[str, Any])
async def request_streak_partner(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Streak ortakligi iste. Sistem uygun bir ortak eslestirir."""
    user_id = str(current_user.id)

    # Aktif ortaklik kontrolu
    existing = await db.execute(
        select(StreakPair).where(
            StreakPair.status == "active",
            or_(
                StreakPair.student_a_id == user_id,
                StreakPair.student_b_id == user_id,
            ),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Zaten aktif bir streak ortakliginiz var.")

    # Bekleyen partner var mi?
    waiting_result = await db.execute(
        select(StreakPair).where(
            StreakPair.status == "waiting",
            StreakPair.student_a_id != user_id,
        )
    )
    waiting = waiting_result.scalar_one_or_none()

    if waiting:
        # Eslesme!
        waiting.student_b_id = user_id
        waiting.status = "active"
        await db.commit()
        return {
            "success": True,
            "data": {"pair_id": waiting.id, "matched": True},
            "message": "Streak ortaginiz bulundu!",
        }

    # Beklemeye al
    pair = StreakPair(
        student_a_id=user_id,
        student_b_id="",  # Henuz eslesme yok
        status="waiting",
    )
    db.add(pair)
    await db.commit()

    return {
        "success": True,
        "data": {"pair_id": pair.id, "matched": False},
        "message": "Ortak bekleniyor...",
    }


@router.get("/status", response_model=dict[str, Any])
async def get_streak_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Aktif streak ortakliginin durumunu gor."""
    user_id = str(current_user.id)

    result = await db.execute(
        select(StreakPair).where(
            StreakPair.status.in_(["active", "waiting"]),
            or_(
                StreakPair.student_a_id == user_id,
                StreakPair.student_b_id == user_id,
            ),
        )
    )
    pair = result.scalar_one_or_none()

    if not pair:
        return {
            "success": True,
            "data": None,
            "message": "Aktif streak ortakliginiz yok.",
        }

    # Bugunun durumu
    today = date.today()
    today_logs = await db.execute(
        select(StreakDailyLog).where(
            StreakDailyLog.pair_id == pair.id,
            StreakDailyLog.log_date == today,
        )
    )
    logs = {log.student_id: log.completed for log in today_logs.scalars().all()}

    partner_id = (
        pair.student_b_id if pair.student_a_id == user_id else pair.student_a_id
    )

    return {
        "success": True,
        "data": {
            "pair_id": pair.id,
            "status": pair.status,
            "current_streak": pair.current_streak,
            "max_streak": pair.max_streak,
            "total_xp": pair.total_xp_earned,
            "my_today": logs.get(user_id, False),
            "partner_today": logs.get(partner_id, False),
        },
    }


@router.post("/complete-today", response_model=dict[str, Any])
async def complete_today(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Bugunku gorevi tamamlandi olarak isaretle."""
    user_id = str(current_user.id)

    # Aktif pair bul
    result = await db.execute(
        select(StreakPair).where(
            StreakPair.status == "active",
            or_(
                StreakPair.student_a_id == user_id,
                StreakPair.student_b_id == user_id,
            ),
        )
    )
    pair = result.scalar_one_or_none()
    if not pair:
        raise HTTPException(400, "Aktif streak ortakliginiz yok.")

    today = date.today()

    # Zaten tamamlamis mi?
    existing = await db.execute(
        select(StreakDailyLog).where(
            StreakDailyLog.pair_id == pair.id,
            StreakDailyLog.student_id == user_id,
            StreakDailyLog.log_date == today,
        )
    )
    if existing.scalar_one_or_none():
        return {
            "success": True,
            "message": "Bugunku gorev zaten tamamlandi.",
        }

    # Kaydet
    log = StreakDailyLog(
        pair_id=pair.id,
        student_id=user_id,
        log_date=today,
        completed=True,
    )
    db.add(log)

    # Partner da tamamlamis mi?
    partner_id = (
        pair.student_b_id if pair.student_a_id == user_id else pair.student_a_id
    )
    partner_log = await db.execute(
        select(StreakDailyLog).where(
            StreakDailyLog.pair_id == pair.id,
            StreakDailyLog.student_id == partner_id,
            StreakDailyLog.log_date == today,
            StreakDailyLog.completed.is_(True),
        )
    )

    xp_earned = 0
    bonus = 0
    if partner_log.scalar_one_or_none():
        # Ikisi de tamamladi — streak devam!
        pair.current_streak = (pair.current_streak or 0) + 1
        pair.max_streak = max(pair.max_streak or 0, pair.current_streak)
        xp_earned = XP_DAILY_BOTH
        pair.total_xp_earned = (pair.total_xp_earned or 0) + xp_earned

        # Milestone bonuslari
        if pair.current_streak == 7:
            bonus = XP_7_DAY_BONUS
        elif pair.current_streak == 30:
            bonus = XP_30_DAY_BONUS

        if bonus:
            pair.total_xp_earned += bonus

    await db.commit()

    return {
        "success": True,
        "data": {
            "streak": pair.current_streak,
            "xp_earned": xp_earned + bonus,
            "bonus": bonus,
        },
        "message": "Gunluk gorev tamamlandi!"
        + (f" +{bonus} bonus XP!" if bonus else ""),
    }
