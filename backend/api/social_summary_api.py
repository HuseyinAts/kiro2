"""
Social Summary API — Aggregate XP across all social features
Endpoint: /api/v1/social/summary
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.dependencies import AuthenticatedUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/social", tags=["Social Summary"])


@router.get("/summary", response_model=dict[str, Any])
async def get_social_summary(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Aggregate XP from all social features for current user."""
    user_id = str(current_user.id)

    # F1: Soru Meydani — count questions + solutions
    from models.soru_meydani import ForumQuestion, ForumSolution

    q_count = (
        await db.execute(
            select(func.count())
            .select_from(ForumQuestion)
            .where(ForumQuestion.student_id == user_id)
        )
    ).scalar() or 0

    s_count = (
        await db.execute(
            select(func.count())
            .select_from(ForumSolution)
            .where(ForumSolution.solver_id == user_id)
        )
    ).scalar() or 0

    forum_xp = q_count * 5 + s_count * 10  # XP_ASK=5, XP_SOLVE=10

    # F2: Cozum Duellosu — count wins
    from models.cozum_duellosu import SolutionDuel

    duel_wins = (
        await db.execute(
            select(func.count())
            .select_from(SolutionDuel)
            .where(SolutionDuel.winner_id == user_id)
        )
    ).scalar() or 0

    duel_xp = duel_wins * 25  # XP_WIN=25

    # F3: Oba Seferleri — sum contributions
    from models.oba_seferleri import ObaChallengeProgress

    oba_contrib = (
        await db.execute(
            select(func.coalesce(func.sum(ObaChallengeProgress.contribution), 0)).where(
                ObaChallengeProgress.student_id == user_id
            )
        )
    ).scalar() or 0

    oba_xp = int(oba_contrib)  # 1 XP per contribution unit

    # F4: Pomodoro — count completed rounds
    from models.pomodoro import PomodoroParticipant

    pomo_rounds = (
        await db.execute(
            select(
                func.coalesce(func.sum(PomodoroParticipant.rounds_completed), 0)
            ).where(PomodoroParticipant.student_id == user_id)
        )
    ).scalar() or 0

    pomo_xp = int(pomo_rounds) * 5  # XP_PER_ROUND=5

    # F5: Birlikte Streak — total XP from pair
    from sqlalchemy import or_

    from models.birlikte_streak import StreakPair

    streak_result = await db.execute(
        select(func.coalesce(func.sum(StreakPair.total_xp_earned), 0)).where(
            or_(
                StreakPair.student_a_id == user_id,
                StreakPair.student_b_id == user_id,
            )
        )
    )
    streak_xp = int(streak_result.scalar() or 0)

    # F6: Usta-Cirak — session count

    from models.usta_cirak import MentorPair, MentorSession

    mentor_sessions = (
        await db.execute(
            select(func.count())
            .select_from(MentorSession)
            .join(MentorPair, MentorSession.pair_id == MentorPair.id)
            .where(
                or_(
                    MentorPair.mentor_id == user_id,
                    MentorPair.mentee_id == user_id,
                )
            )
            .where(MentorSession.ended_at.isnot(None))
        )
    ).scalar() or 0

    mentor_xp = mentor_sessions * 15  # Average of mentor(20)+mentee(10)

    total_xp = forum_xp + duel_xp + oba_xp + pomo_xp + streak_xp + mentor_xp

    return {
        "success": True,
        "data": {
            "total_xp": total_xp,
            "forum_xp": forum_xp,
            "duel_xp": duel_xp,
            "oba_xp": oba_xp,
            "pomodoro_xp": pomo_xp,
            "streak_xp": streak_xp,
            "mentor_xp": mentor_xp,
            "details": {
                "questions_asked": q_count,
                "solutions_given": s_count,
                "duel_wins": duel_wins,
                "oba_contributions": int(oba_contrib),
                "pomodoro_rounds": int(pomo_rounds),
                "mentor_sessions": mentor_sessions,
            },
        },
    }
