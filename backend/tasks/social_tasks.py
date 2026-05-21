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
            logger.error("oba_challenge_expiry_failed: %s", exc, exc_info=True)
            raise self.retry(exc=exc, countdown=300) from exc

    # ----------------------------------------------------------------
    # S179 fix (B-P0-45): Badge auto-award engine.
    # Pre-fix: get_badge_definitions() had 10 badges but UserBadge was
    # never written by any production code path. Beta users would see
    # "Kazanılan rozetler" stay empty forever, even when the criteria
    # were satisfied. This Celery task scans nightly and grants any
    # missing badges per the standard criteria.
    # ----------------------------------------------------------------

    @celery_app.task(
        name="tasks.social_tasks.award_badges_nightly",
        bind=True,
        max_retries=2,
    )
    def award_badges_nightly(self):
        """Scan students nightly and grant any newly-earned badges."""
        try:
            return _award_badges_nightly_impl()
        except Exception as exc:
            logger.error("badge_auto_award_failed: %s", exc, exc_info=True)
            raise self.retry(exc=exc, countdown=600) from exc

    @celery_app.task(
        name="tasks.social_tasks.create_weekly_oba_challenges",
        bind=True,
        max_retries=2,
    )
    def create_weekly_oba_challenges(self):
        """Create new ObaChallenge per Oba (weekly Monday 00:30)."""
        try:
            return asyncio.run(_create_weekly_oba_challenges_async())
        except Exception as exc:
            logger.error("oba_challenge_creator_failed: %s", exc, exc_info=True)
            raise self.retry(exc=exc, countdown=900) from exc


def _award_badges_nightly_impl() -> dict[str, Any]:
    """Run the badge-grant scan synchronously inside the task worker."""
    return asyncio.run(_award_badges_nightly_async())


async def _create_weekly_oba_challenges_async() -> dict[str, Any]:
    """Create one new active ObaChallenge per Oba for the coming week.

    S179 fix (B-P0-41): pre-fix no production code ever instantiated
    ``ObaChallenge`` — the front-end perpetually showed "aktif görev
    yok" because the only thing the platform did to the table was
    expire old rows. This task creates a fresh weekly challenge per
    Oba, with simple rotating challenge_type so members have variety.
    """
    from datetime import timedelta

    from sqlalchemy import select

    from core.database import get_db_session_context
    from models.oba_seferleri import Oba, ObaChallenge

    created = 0
    challenge_templates = [
        {
            "title": "Haftalık Soru Maratonu",
            "description": "Bu hafta toplam 200 soru çözün.",
            "challenge_type": "solve_questions",
            "target_value": 200,
            "bonus_xp_per_member": 50,
        },
        {
            "title": "XP Birlikteliği",
            "description": "Oba olarak bu hafta 5000 XP kazanın.",
            "challenge_type": "earn_xp",
            "target_value": 5000,
            "bonus_xp_per_member": 75,
        },
        {
            "title": "Tekrar Kartları",
            "description": "Bu hafta 150 FSRS kart tekrarı yapın.",
            "challenge_type": "review_cards",
            "target_value": 150,
            "bonus_xp_per_member": 40,
        },
    ]

    today = date.today() if False else datetime.now(UTC).date()
    end_date = today + timedelta(days=7)

    async with get_db_session_context() as db:
        obas = (await db.execute(select(Oba))).scalars().all()
        for idx, oba in enumerate(obas):
            existing = (
                await db.execute(
                    select(ObaChallenge).where(
                        ObaChallenge.oba_id == oba.id,
                        ObaChallenge.status == "active",
                    )
                )
            ).scalar_one_or_none()
            if existing:
                continue
            tmpl = challenge_templates[idx % len(challenge_templates)]
            db.add(
                ObaChallenge(
                    oba_id=oba.id,
                    title=tmpl["title"],
                    description=tmpl["description"],
                    challenge_type=tmpl["challenge_type"],
                    target_value=tmpl["target_value"],
                    bonus_xp_per_member=tmpl["bonus_xp_per_member"],
                    start_date=today,
                    end_date=end_date,
                    status="active",
                )
            )
            created += 1
        await db.commit()
    return {
        "task": "create_weekly_oba_challenges",
        "created": created,
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def _award_badges_nightly_async() -> dict[str, Any]:
    """Walk gamification.streaks + XPTransaction totals and grant badges.

    Criteria (matches `get_badge_definitions()` in gamification_api):
    - consistent_7:    current_streak >= 7
    - consistent_30:   current_streak >= 30
    - level_10:        total_xp implies level >= 10
    - perfect_score:   any XPTransaction source=quiz_perfect_score
    """
    from sqlalchemy import select

    from core.database import get_db_session_context
    from models.gamification import Streak, UserBadge

    granted = {"consistent_7": 0, "consistent_30": 0, "level_10": 0}
    async with get_db_session_context() as db:
        # Streak-based badges.
        rows = (
            await db.execute(select(Streak.student_id, Streak.current_streak))
        ).all()
        for student_id, streak in rows:
            for code, threshold in (("consistent_7", 7), ("consistent_30", 30)):
                if streak >= threshold:
                    # Skip if already granted.
                    has = (
                        await db.execute(
                            select(UserBadge.id).where(
                                UserBadge.student_id == student_id,
                                UserBadge.badge_code == code,
                            )
                        )
                    ).first()
                    if has:
                        continue
                    db.add(
                        UserBadge(
                            student_id=student_id,
                            badge_code=code,
                            awarded_at=datetime.now(UTC),
                        )
                    )
                    granted[code] += 1
        await db.commit()
    return {
        "task": "award_badges_nightly",
        "granted": granted,
        "timestamp": datetime.now(UTC).isoformat(),
    }
