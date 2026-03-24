"""
Social Features Celery Tasks

Scheduled tasks for social features automation:
- Birlikte Streak break detection (daily 00:05)
- Cozum Duellosu voting expiry (every 30 min)
- Oba Seferleri challenge expiry (daily 00:10)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    from core.celery_app import celery_app
except ImportError:
    celery_app = None  # type: ignore


# ---------------------------------------------------------------------------
# F5: Birlikte Streak Break Detection
# ---------------------------------------------------------------------------


def _check_birlikte_streaks_impl() -> dict[str, Any]:
    """Check streak pairs and reset broken streaks."""
    result = asyncio.run(_check_birlikte_streaks_async())
    return result


async def _check_birlikte_streaks_async() -> dict[str, Any]:
    """Async implementation: reset streaks where both partners missed yesterday."""
    from datetime import date, timedelta

    from sqlalchemy import and_, select

    from core.database import get_db_session_context
    from models.birlikte_streak import StreakDailyLog, StreakPair

    yesterday = date.today() - timedelta(days=1)
    reset_count = 0

    async with get_db_session_context() as db:
        # Get all active pairs
        pairs_result = await db.execute(
            select(StreakPair).where(
                and_(
                    StreakPair.status == "active",
                    StreakPair.current_streak > 0,
                )
            )
        )
        pairs = pairs_result.scalars().all()

        for pair in pairs:
            # Check if both partners logged yesterday
            logs_result = await db.execute(
                select(StreakDailyLog).where(
                    and_(
                        StreakDailyLog.pair_id == pair.id,
                        StreakDailyLog.log_date == yesterday,
                    )
                )
            )
            logs = logs_result.scalars().all()
            logged_students = {log.student_id for log in logs}

            # Both must have logged — if either missed, streak breaks
            if (
                pair.student_a_id not in logged_students
                or pair.student_b_id not in logged_students
            ):
                pair.current_streak = 0
                reset_count += 1

        await db.commit()

    logger.info("birlikte_streak_check: %d pairs reset", reset_count)
    return {"reset": reset_count, "checked": len(pairs)}


# ---------------------------------------------------------------------------
# F2: Cozum Duellosu Voting Expiry
# ---------------------------------------------------------------------------


def _expire_duel_voting_impl() -> dict[str, Any]:
    """Auto-determine winners for expired duel voting periods."""
    result = asyncio.run(_expire_duel_voting_async())
    return result


async def _expire_duel_voting_async() -> dict[str, Any]:
    """Async implementation: close expired duels and determine winners."""
    from sqlalchemy import and_, func, select

    from core.database import get_db_session_context
    from models.cozum_duellosu import (
        SolutionDuel,
        SolutionDuelSubmission,
        SolutionDuelVote,
    )

    now = datetime.now(UTC)
    expired_count = 0
    winners_determined = 0

    async with get_db_session_context() as db:
        # Find duels in 'voting' status past their voting_ends_at
        duels_result = await db.execute(
            select(SolutionDuel).where(
                and_(
                    SolutionDuel.status == "voting",
                    SolutionDuel.voting_ends_at <= now,
                )
            )
        )
        duels = duels_result.scalars().all()

        for duel in duels:
            # Count votes per submission
            votes_result = await db.execute(
                select(
                    SolutionDuelVote.submission_id,
                    func.count().label("vote_count"),
                )
                .where(SolutionDuelVote.duel_id == duel.id)
                .group_by(SolutionDuelVote.submission_id)
            )
            vote_counts = {
                row.submission_id: row.vote_count for row in votes_result.all()
            }

            if vote_counts:
                winner_submission_id = max(vote_counts, key=vote_counts.get)
                # Get the submission to find the student
                sub_result = await db.execute(
                    select(SolutionDuelSubmission).where(
                        SolutionDuelSubmission.id == winner_submission_id
                    )
                )
                winner_sub = sub_result.scalar_one_or_none()
                if winner_sub:
                    duel.winner_id = winner_sub.student_id
                    winners_determined += 1

            duel.status = "completed"
            expired_count += 1

        await db.commit()

    logger.info(
        "duel_voting_expiry: %d duels expired, %d winners determined",
        expired_count,
        winners_determined,
    )
    return {"expired": expired_count, "winners_determined": winners_determined}


# ---------------------------------------------------------------------------
# F3: Oba Seferleri Challenge Expiry
# ---------------------------------------------------------------------------


def _expire_oba_challenges_impl() -> dict[str, Any]:
    """Mark expired Oba challenges as completed (whether target met or not)."""
    result = asyncio.run(_expire_oba_challenges_async())
    return result


async def _expire_oba_challenges_async() -> dict[str, Any]:
    """Async implementation: close expired challenges."""
    from datetime import date

    from sqlalchemy import and_, select

    from core.database import get_db_session_context
    from models.oba_seferleri import ObaChallenge

    today = date.today()
    expired_count = 0
    completed_count = 0

    async with get_db_session_context() as db:
        challenges_result = await db.execute(
            select(ObaChallenge).where(
                and_(
                    ObaChallenge.completed.is_(False),
                    ObaChallenge.end_date < today,
                )
            )
        )
        challenges = challenges_result.scalars().all()

        for challenge in challenges:
            challenge.completed = True
            expired_count += 1
            if challenge.current_value >= challenge.target_value:
                completed_count += 1

        await db.commit()

    logger.info(
        "oba_challenge_expiry: %d expired, %d met target",
        expired_count,
        completed_count,
    )
    return {
        "expired": expired_count,
        "met_target": completed_count,
        "missed_target": expired_count - completed_count,
    }


# ---------------------------------------------------------------------------
# Register Celery tasks
# ---------------------------------------------------------------------------

if celery_app is not None:

    @celery_app.task(
        name="tasks.social_tasks.check_birlikte_streaks",
        bind=True,
        max_retries=3,
    )
    def check_birlikte_streaks(self):
        """Daily streak pair check (00:05)."""
        try:
            return _check_birlikte_streaks_impl()
        except Exception as exc:
            logger.error("birlikte_streak_check_failed: %s", exc)
            raise self.retry(exc=exc, countdown=300) from exc

    @celery_app.task(
        name="tasks.social_tasks.expire_duel_voting",
        bind=True,
        max_retries=3,
    )
    def expire_duel_voting(self):
        """Expire duel voting periods (every 30 min)."""
        try:
            return _expire_duel_voting_impl()
        except Exception as exc:
            logger.error("duel_voting_expiry_failed: %s", exc)
            raise self.retry(exc=exc, countdown=60) from exc

    @celery_app.task(
        name="tasks.social_tasks.expire_oba_challenges",
        bind=True,
        max_retries=3,
    )
    def expire_oba_challenges(self):
        """Expire Oba challenges past end_date (daily 00:10)."""
        try:
            return _expire_oba_challenges_impl()
        except Exception as exc:
            logger.error("oba_challenge_expiry_failed: %s", exc)
            raise self.retry(exc=exc, countdown=300) from exc
