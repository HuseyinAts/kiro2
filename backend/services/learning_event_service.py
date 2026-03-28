"""
Learning Event Service — Central event coordinator for quiz/exam/assessment completions.

Handles: BKT update, FSRS card scheduling, XP award, Streak update, Badge check.
Each subsystem is best-effort: failure in one does NOT block the others.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class LearningEventService:
    """Coordinates post-event side-effects across BKT, FSRS, XP, Streak."""

    @staticmethod
    async def on_quiz_completed(
        *,
        student_id: str,
        question_results: list[dict[str, Any]],
        q_meta: dict[str, dict[str, Any]],
        score: float,
        passed: bool,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Called after a quiz is submitted. Triggers BKT + XP + Streak."""
        report: dict[str, Any] = {"bkt": None, "xp": None, "streak": None}

        # 1. BKT update (per question, with cumulative IRT history)
        try:
            from services.bkt_service import BKTService

            # Build IRT history incrementally so eap_theta gets real data
            answered_questions: list[dict] = []
            responses_history: list[bool] = []
            for qr in question_results:
                meta = q_meta.get(qr["question_id"], {})
                t_id = meta.get("topic_id")
                if t_id:
                    # Add current question's IRT params to cumulative history
                    answered_questions.append(
                        {
                            "irt_a": float(meta.get("irt_a", 1.0)),
                            "irt_b": float(meta.get("irt_b", 0.0)),
                            "irt_c": float(meta.get("irt_c", 0.2)),
                        }
                    )
                    responses_history.append(bool(qr["is_correct"]))

                    await BKTService.record_answer(
                        student_id=student_id,
                        topic_id=str(t_id),
                        subject_slug=meta.get("subject", "matematik"),
                        correct=qr["is_correct"],
                        rating=3 if qr["is_correct"] else 1,
                        db=db,
                        answered_questions=list(answered_questions),
                        responses=list(responses_history),
                    )
            await db.flush()
            report["bkt"] = "ok"
        except Exception as e:
            logger.warning("BKT update skipped: %s", e)
            report["bkt"] = f"error: {e}"

        # 2. XP award
        try:
            correct_count = sum(1 for r in question_results if r["is_correct"])
            xp_amount = correct_count * 10
            if passed:
                xp_amount += 50  # bonus for passing
            await GamificationDBService.award_xp(
                student_id=student_id,
                amount=xp_amount,
                source="quiz",
                db=db,
            )
            report["xp"] = xp_amount
        except Exception as e:
            logger.warning("XP award skipped: %s", e)
            report["xp"] = f"error: {e}"

        # 3. Streak update
        try:
            await GamificationDBService.update_streak(
                student_id=student_id,
                db=db,
            )
            report["streak"] = "ok"
        except Exception as e:
            logger.warning("Streak update skipped: %s", e)
            report["streak"] = f"error: {e}"

        # 4. Badge check (best-effort)
        try:
            badges = await GamificationDBService.check_quiz_badges(
                student_id=student_id,
                score=score,
                passed=passed,
                db=db,
            )
            report["badges"] = badges
        except Exception as e:
            logger.warning("Badge check skipped: %s", e)
            report["badges"] = f"error: {e}"

        # 5. Leaderboard update (best-effort, Redis)
        try:
            if report.get("xp") and isinstance(report["xp"], int):
                await GamificationDBService.update_leaderboard(
                    student_id=student_id, db=db
                )
                report["leaderboard"] = "ok"
        except Exception as e:
            logger.warning("Leaderboard update skipped: %s", e)
            report["leaderboard"] = f"error: {e}"

        await db.commit()
        return report

    @staticmethod
    async def on_exam_completed(
        *,
        student_id: str,
        correct_answers: int,
        total_questions: int,
        net_score: float,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Called after an OSYM exam is completed."""
        report: dict[str, Any] = {"xp": None, "streak": None}

        # XP: 5 per correct, bonus if >70% net
        try:
            xp_amount = correct_answers * 5
            if total_questions > 0 and (correct_answers / total_questions) > 0.7:
                xp_amount += 100
            await GamificationDBService.award_xp(
                student_id=student_id,
                amount=xp_amount,
                source="sinav",
                db=db,
            )
            report["xp"] = xp_amount
        except Exception as e:
            logger.warning("Exam XP award skipped: %s", e)
            report["xp"] = f"error: {e}"

        # Streak
        try:
            await GamificationDBService.update_streak(student_id=student_id, db=db)
            report["streak"] = "ok"
        except Exception as e:
            logger.warning("Exam streak update skipped: %s", e)
            report["streak"] = f"error: {e}"

        await db.commit()
        return report

    @staticmethod
    async def on_assessment_completed(
        *,
        student_id: str,
        subjects: dict[str, dict[str, float]],
        db: AsyncSession,
    ) -> dict[str, Any]:
        """
        Called after placement assessment.
        subjects: {"matematik": {"theta": 0.5, "se": 0.8}, ...}
        Creates StudentAbility + BKTState rows for each subject.
        """
        report: dict[str, Any] = {"abilities": 0, "bkt_states": 0}

        try:
            from models.gamification import BKTState, StudentAbility

            SUBJECT_ID_MAP = {
                "matematik": 1,
                "geometri": 2,
                "fizik": 3,
                "kimya": 4,
                "biyoloji": 5,
                "turkce": 6,
                "tarih": 7,
                "cografya": 8,
                "edebiyat": 9,
                "felsefe": 10,
                "din": 11,
            }

            for subj_name, data in subjects.items():
                theta = data.get("theta", 0.0)
                se = data.get("se", 1.0)
                subj_id = SUBJECT_ID_MAP.get(subj_name.lower())
                if subj_id is None:
                    continue

                # Upsert StudentAbility
                stmt = (
                    pg_insert(StudentAbility)
                    .values(
                        student_id=student_id,
                        subject_id=subj_id,
                        theta=theta,
                        theta_se=se,
                    )
                    .on_conflict_do_update(
                        index_elements=["student_id", "subject_id"],
                        set_={"theta": theta, "theta_se": se},
                    )
                )
                await db.execute(stmt)
                report["abilities"] += 1

                # Init BKT state with p_learn derived from theta
                p_learn = max(0.05, min(0.95, (theta + 3) / 6))
                stmt_bkt = (
                    pg_insert(BKTState)
                    .values(
                        student_id=student_id,
                        topic_id=subj_name.lower(),
                        p_learn=round(p_learn, 4),
                        p_transit=0.10,
                        p_guess=0.20,
                        p_slip=0.10,
                        mastery_status="learning" if p_learn < 0.80 else "mastered",
                    )
                    .on_conflict_do_update(
                        index_elements=["student_id", "topic_id"],
                        set_={"p_learn": round(p_learn, 4)},
                    )
                )
                await db.execute(stmt_bkt)
                report["bkt_states"] += 1

            await db.commit()
        except Exception as e:
            logger.error("Assessment persistence failed: %s", e)
            report["error"] = str(e)

        return report


class GamificationDBService:
    """DB-backed XP, Streak, and Badge operations."""

    @staticmethod
    async def award_xp(
        *,
        student_id: str,
        amount: int,
        source: str,
        topic_id: str | None = None,
        db: AsyncSession,
    ) -> int:
        """Insert XPTransaction + update users.total_xp. Returns new total."""
        from models.gamification import XPTransaction

        # Insert transaction
        txn = XPTransaction(
            student_id=student_id,
            amount=amount,
            source=source,
            topic_id=topic_id,
        )
        db.add(txn)

        # Update user total_xp
        from models.database import User

        stmt = (
            update(User)
            .where(User.id == student_id)
            .values(total_xp=User.total_xp + amount)
            .returning(User.total_xp)
        )
        result = await db.execute(stmt)
        row = result.first()
        new_total = row[0] if row else amount
        await db.flush()
        return new_total

    @staticmethod
    async def update_streak(
        *,
        student_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Upsert daily streak."""
        from models.gamification import Streak

        today = date.today()
        result = await db.execute(select(Streak).where(Streak.user_id == student_id))
        streak = result.scalar_one_or_none()

        if streak is None:
            streak = Streak(
                user_id=student_id,
                current_streak=1,
                largest_streak=1,
                last_activity=today,
                total_days_active=1,
            )
            db.add(streak)
        elif streak.last_activity == today:
            pass  # already active today
        elif streak.last_activity and (today - streak.last_activity).days == 1:
            streak.current_streak += 1
            streak.largest_streak = max(streak.largest_streak, streak.current_streak)
            streak.last_activity = today
            streak.total_days_active += 1
        else:
            # streak broken
            streak.current_streak = 1
            streak.last_activity = today
            streak.total_days_active += 1

        await db.flush()
        return {
            "current_streak": streak.current_streak,
            "largest_streak": streak.largest_streak,
        }

    @staticmethod
    async def get_points_summary(
        *,
        student_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Get XP summary from DB."""
        from sqlalchemy import func as sa_func

        from models.gamification import XPTransaction

        # Total XP
        total_result = await db.execute(
            select(sa_func.coalesce(sa_func.sum(XPTransaction.amount), 0)).where(
                XPTransaction.student_id == student_id
            )
        )
        total_xp = total_result.scalar() or 0

        # Today's XP
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        daily_result = await db.execute(
            select(sa_func.coalesce(sa_func.sum(XPTransaction.amount), 0)).where(
                XPTransaction.student_id == student_id,
                XPTransaction.created_at >= today_start,
            )
        )
        daily_xp = daily_result.scalar() or 0

        # Weekly XP (last 7 days)
        from datetime import timedelta

        week_start = today_start - timedelta(days=7)
        weekly_result = await db.execute(
            select(sa_func.coalesce(sa_func.sum(XPTransaction.amount), 0)).where(
                XPTransaction.student_id == student_id,
                XPTransaction.created_at >= week_start,
            )
        )
        weekly_xp = weekly_result.scalar() or 0

        return {
            "total_points": total_xp,
            "daily_points": daily_xp,
            "weekly_points": weekly_xp,
        }

    @staticmethod
    async def get_point_history(
        *,
        student_id: str,
        days: int = 30,
        limit: int | None = None,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Get XP transaction history from DB."""
        from datetime import timedelta

        from models.gamification import XPTransaction

        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(XPTransaction)
            .where(
                XPTransaction.student_id == student_id,
                XPTransaction.created_at >= cutoff,
            )
            .order_by(XPTransaction.created_at.desc())
        )
        if limit:
            stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        rows = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "user_id": r.student_id,
                "points": r.amount,
                "reason": r.source,
                "metadata": {"topic_id": r.topic_id} if r.topic_id else None,
                "timestamp": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    @staticmethod
    async def get_streak(
        *,
        student_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Get streak info from DB."""
        from models.gamification import Streak

        result = await db.execute(select(Streak).where(Streak.user_id == student_id))
        streak = result.scalar_one_or_none()
        if streak is None:
            return {"current_streak": 0, "largest_streak": 0, "total_days_active": 0}
        return {
            "current_streak": streak.current_streak,
            "largest_streak": streak.largest_streak,
            "total_days_active": streak.total_days_active,
            "last_activity": streak.last_activity.isoformat()
            if streak.last_activity
            else None,
        }

    @staticmethod
    async def check_quiz_badges(
        *,
        student_id: str,
        score: float,
        passed: bool,
        db: AsyncSession,
    ) -> list[str]:
        """Check and award badges after quiz completion. Returns list of newly awarded badge IDs."""
        from sqlalchemy import func as sa_func

        from models.gamification import Streak, UserBadge, XPTransaction

        awarded: list[str] = []

        # Count total quizzes completed (XP transactions with source='quiz')
        quiz_count_result = await db.execute(
            select(sa_func.count()).where(
                XPTransaction.student_id == student_id,
                XPTransaction.source == "quiz",
            )
        )
        quiz_count = quiz_count_result.scalar() or 0

        # Get streak info
        streak_result = await db.execute(
            select(Streak).where(Streak.user_id == student_id)
        )
        streak = streak_result.scalar_one_or_none()
        current_streak = streak.current_streak if streak else 0

        # Badge definitions: (badge_id, criteria_check)
        badge_checks = [
            ("first_quiz", quiz_count >= 1),
            ("quiz_10", quiz_count >= 10),
            ("quiz_50", quiz_count >= 50),
            ("quiz_100", quiz_count >= 100),
            ("perfect_score", score >= 100.0),
            ("consistent_7", current_streak >= 7),
            ("consistent_30", current_streak >= 30),
        ]

        for badge_id, criteria_met in badge_checks:
            if not criteria_met:
                continue
            # Check if already earned
            existing = await db.execute(
                select(UserBadge).where(
                    UserBadge.user_id == student_id,
                    UserBadge.badge_id == badge_id,
                )
            )
            if existing.scalar_one_or_none():
                continue
            # Award the badge
            new_badge = UserBadge(
                user_id=student_id,
                badge_id=badge_id,
            )
            db.add(new_badge)
            awarded.append(badge_id)

        if awarded:
            await db.flush()
            logger.info("Badges awarded to %s: %s", student_id, awarded)

        return awarded

    @staticmethod
    async def update_leaderboard(
        *,
        student_id: str,
        db: AsyncSession,
    ) -> None:
        """Update Redis leaderboard with user's current total XP."""
        try:
            from redis import Redis

            from models.database import User

            # Get current total_xp from DB
            result = await db.execute(
                select(User.total_xp).where(User.id == student_id)
            )
            row = result.first()
            if not row:
                return
            total_xp = row[0] or 0

            # Update Redis sorted set (best-effort)
            import os

            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            r = Redis.from_url(redis_url, decode_responses=True)
            r.zadd("leaderboard:global", {student_id: total_xp})
            r.close()
        except Exception as e:
            logger.warning("Redis leaderboard update failed: %s", e)
