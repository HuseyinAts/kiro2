"""
Daily Quest API - Gunluk Gorev Sistemi
Endpoints: /api/v1/daily-quests/*

Her gun 3 gorev uretilir:
1. CAT oturumu tamamla
2. FSRS tekrar kart coz
3. Rastgele: duel / streak / realm quest

3/3 tamamlaninca bonus XP.
"""

import logging
import random
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.gamification import DailyQuest
from services.learning_event_service import GamificationDBService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/daily-quests", tags=["Daily Quests"])

# ---------------------------------------------------------------------------
# Quest templates
# ---------------------------------------------------------------------------

QUEST_TEMPLATES = [
    {
        "quest_type": "cat_session",
        "title": "CAT Oturumu Tamamla",
        "description": "Adaptif bir test oturumu tamamla.",
        "target_value": 1,
        "xp_reward": 15,
    },
    {
        "quest_type": "fsrs_review",
        "title": "Tekrar Kartlarini Coz",
        "description": "En az 5 FSRS tekrar kartini cevapla.",
        "target_value": 5,
        "xp_reward": 10,
    },
]

BONUS_POOL = [
    {
        "quest_type": "duel",
        "title": "Duello Yap",
        "description": "Bir arkadasinla duello yap.",
        "target_value": 1,
        "xp_reward": 20,
    },
    {
        "quest_type": "streak_check",
        "title": "Gunluk Giris",
        "description": "Bugunku streak'ini koparma!",
        "target_value": 1,
        "xp_reward": 5,
    },
    {
        "quest_type": "realm_quest",
        "title": "Alem Gorevi",
        "description": "Bir alem gorevini tamamla.",
        "target_value": 1,
        "xp_reward": 15,
    },
    {
        "quest_type": "solve_10",
        "title": "10 Soru Coz",
        "description": "Herhangi bir konudan 10 soru coz.",
        "target_value": 10,
        "xp_reward": 12,
    },
]

BONUS_XP = 25  # 3/3 tamamlaninca bonus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _ensure_today_quests(user_id: str, db: AsyncSession) -> list[DailyQuest]:
    """Bugun icin gorevler yoksa olustur, varsa dondur. Race-condition safe."""
    today = date.today()

    result = await db.execute(
        select(DailyQuest).where(
            DailyQuest.student_id == user_id,
            DailyQuest.quest_date == today,
        )
    )
    existing = list(result.scalars().all())
    if existing:
        return existing

    # Sabit 2 + havuzdan rastgele 1
    quests_to_create = list(QUEST_TEMPLATES)
    bonus = random.choice(BONUS_POOL)
    quests_to_create.append(bonus)

    # Use ON CONFLICT DO NOTHING to handle concurrent creation
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    for tmpl in quests_to_create:
        stmt = (
            pg_insert(DailyQuest)
            .values(
                quest_date=today,
                student_id=user_id,
                quest_type=tmpl["quest_type"],
                title=tmpl["title"],
                description=tmpl.get("description"),
                target_value=tmpl["target_value"],
                xp_reward=tmpl["xp_reward"],
            )
            .on_conflict_do_nothing(
                index_elements=["quest_date", "student_id", "quest_type"]
            )
        )
        await db.execute(stmt)

    await db.commit()

    # Re-read to get final state (ours or concurrent winner's)
    result2 = await db.execute(
        select(DailyQuest).where(
            DailyQuest.student_id == user_id,
            DailyQuest.quest_date == today,
        )
    )
    return list(result2.scalars().all())


def _quest_to_dict(q: DailyQuest) -> dict:
    return {
        "id": q.id,
        "quest_type": q.quest_type,
        "title": q.title,
        "description": q.description,
        "target_value": q.target_value,
        "current_value": q.current_value,
        "xp_reward": q.xp_reward,
        "completed": q.completed,
        "completed_at": q.completed_at.isoformat() if q.completed_at else None,
        "bonus_claimed": q.bonus_claimed,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/today", response_model=dict[str, Any])
async def get_today_quests(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Bugunku gorevleri getir (yoksa olustur)."""
    user_id = str(current_user.id)
    quests = await _ensure_today_quests(user_id, db)

    completed_count = sum(1 for q in quests if q.completed)
    all_done = completed_count == len(quests)
    bonus_available = all_done and not any(q.bonus_claimed for q in quests)

    return {
        "success": True,
        "data": {
            "quests": [_quest_to_dict(q) for q in quests],
            "completed_count": completed_count,
            "total_count": len(quests),
            "all_completed": all_done,
            "bonus_available": bonus_available,
            "bonus_xp": BONUS_XP,
        },
    }


@router.post("/{quest_id}/progress", response_model=dict[str, Any])
async def update_quest_progress(
    quest_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Gorev ilerlemesini guncelle. Tamamlaninca XP ver."""
    user_id = str(current_user.id)

    result = await db.execute(
        select(DailyQuest).where(
            DailyQuest.id == quest_id,
            DailyQuest.student_id == user_id,
        )
    )
    quest = result.scalar_one_or_none()
    if not quest:
        raise HTTPException(404, "Gorev bulunamadi.")
    if quest.completed:
        return {
            "success": True,
            "data": _quest_to_dict(quest),
            "message": "Gorev zaten tamamlandi.",
        }

    quest.current_value = min(quest.current_value + 1, quest.target_value)

    xp_awarded = 0
    if quest.current_value >= quest.target_value:
        quest.completed = True
        quest.completed_at = datetime.now(UTC)
        # XP ver
        xp_awarded = quest.xp_reward
        await GamificationDBService.award_xp(
            student_id=user_id,
            amount=xp_awarded,
            source="daily_quest",
            db=db,
        )

    await db.commit()

    return {
        "success": True,
        "data": _quest_to_dict(quest),
        "xp_awarded": xp_awarded,
        "message": "Gorev tamamlandi!"
        if quest.completed
        else f"Ilerleme: {quest.current_value}/{quest.target_value}",
    }


@router.post("/claim-bonus", response_model=dict[str, Any])
async def claim_daily_bonus(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """3/3 gorev tamamlandi ise bonus XP al."""
    user_id = str(current_user.id)
    today = date.today()

    result = await db.execute(
        select(DailyQuest).where(
            DailyQuest.student_id == user_id,
            DailyQuest.quest_date == today,
        )
    )
    quests = list(result.scalars().all())

    if not quests:
        raise HTTPException(400, "Bugunku gorevler bulunamadi.")

    if not all(q.completed for q in quests):
        raise HTTPException(400, "Tum gorevler tamamlanmadi.")

    if any(q.bonus_claimed for q in quests):
        raise HTTPException(400, "Bonus zaten alindi.")

    # Mark claimed FIRST (atomicity — prevents double-award on crash)
    for q in quests:
        q.bonus_claimed = True
    await db.flush()

    # Bonus XP
    await GamificationDBService.award_xp(
        student_id=user_id,
        amount=BONUS_XP,
        source="daily_bonus",
        db=db,
    )

    await db.commit()

    return {
        "success": True,
        "data": {"bonus_xp": BONUS_XP},
        "message": f"Tebrikler! +{BONUS_XP} bonus XP kazandiniz!",
    }
