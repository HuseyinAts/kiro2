import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from models.gamification import DailyQuest, Streak
from models.user_models import User
from services.leaderboard_service import leaderboard_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["gamification"],
    responses={404: {"description": "Not found"}},
)


@router.get("/status")
async def get_gamification_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get the user's current streak, xp, coins, and level.
    """
    streak = db.query(Streak).filter(Streak.user_id == current_user.id).first()

    return {
        "xp": current_user.total_xp,
        "level": current_user.level,
        "coins": current_user.virtual_currency,
        "current_streak": streak.current_streak if streak else 0,
        "largest_streak": streak.largest_streak if streak else 0,
        "freeze_count": streak.freeze_count if streak else 0,
    }


@router.get("/quests")
async def get_daily_quests(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get or generate today's daily quests for the user.
    """
    today = datetime.now(UTC).date()
    quests = (
        db.query(DailyQuest)
        .filter(
            DailyQuest.student_id == current_user.id, DailyQuest.quest_date == today
        )
        .all()
    )

    if not quests:
        # Generate default quests for today if none exist
        q1 = DailyQuest(
            student_id=current_user.id,
            quest_date=today,
            quest_type="streak_check",
            title="Serini Koru",
            description="Bugün uygulamaya girerek serini devam ettir.",
            target_value=1,
            current_value=1,  # Immediately complete since they are here
            completed=True,
            completed_at=func.now(),
            xp_reward=20,
            organization_id=current_user.organization_id,
        )
        q2 = DailyQuest(
            student_id=current_user.id,
            quest_date=today,
            quest_type="cat_session",
            title="Soru Avcısı",
            description="Bugün en az 10 soru çöz.",
            target_value=10,
            current_value=0,
            xp_reward=50,
            organization_id=current_user.organization_id,
        )
        q3 = DailyQuest(
            student_id=current_user.id,
            quest_date=today,
            quest_type="fsrs_review",
            title="Aralıklı Tekrar",
            description="Eksiklerini kapatmak için FSRS tekrar testini bitir.",
            target_value=1,
            current_value=0,
            xp_reward=100,
            organization_id=current_user.organization_id,
        )
        db.add_all([q1, q2, q3])

        # Award XP for the immediately completed streak check
        current_user.total_xp += q1.xp_reward

        db.commit()
        quests = [q1, q2, q3]

        # Async add to leaderboard
        await leaderboard_service.add_xp(current_user.id, q1.xp_reward)

    return [
        {
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "target": q.target_value,
            "current": q.current_value,
            "completed": q.completed,
            "xp_reward": q.xp_reward,
        }
        for q in quests
    ]


@router.post("/freeze/buy")
async def buy_streak_freeze(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Buy a streak freeze using virtual currency.
    """
    FREEZE_COST = 50
    if current_user.virtual_currency < FREEZE_COST:
        raise HTTPException(status_code=400, detail="Not enough coins")

    streak = db.query(Streak).filter(Streak.user_id == current_user.id).first()
    if not streak:
        streak = Streak(
            user_id=current_user.id,
            current_streak=0,
            largest_streak=0,
            freeze_count=1,
            organization_id=current_user.organization_id,
        )
        db.add(streak)
    else:
        streak.freeze_count += 1

    current_user.virtual_currency -= FREEZE_COST
    db.commit()
    return {
        "message": "Streak freeze purchased",
        "freeze_count": streak.freeze_count,
        "coins": current_user.virtual_currency,
    }


@router.get("/leaderboard")
async def get_leaderboard(
    league: str = "bronze", current_user: User = Depends(get_current_user)
):
    """
    Get weekly leaderboard and current user's rank.
    """
    top_users = await leaderboard_service.get_top_users(league_name=league, top_n=10)
    user_rank = await leaderboard_service.get_user_rank(
        current_user.id, league_name=league
    )

    return {"league": league, "top_users": top_users, "current_user_rank": user_rank}
