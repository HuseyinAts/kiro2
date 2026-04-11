"""
Task 92: Instant Feedback API
DEHB için anında geri bildirim sistemi
"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.dependencies import get_current_user
from core.structured_logger import get_logger
from models.database import User

logger = get_logger(__name__)
router = APIRouter(
    prefix="/api/v1/adhd-support/feedback", tags=["ADHD Support - Instant Feedback"]
)


# Request/Response Models
class AnswerFeedbackRequest(BaseModel):
    is_correct: bool
    question_id: str
    subject: str
    difficulty: str


class StreakResponse(BaseModel):
    current_streak: int
    best_streak: int
    milestone_reached: bool
    milestone_value: int = 0
    multiplier: float


class PerformanceDataPoint(BaseModel):
    time: str
    score: int
    streak: int
    average: float


class PerformanceRecordRequest(BaseModel):
    score: int = Field(..., ge=0, le=100)
    questions_answered: int = Field(..., ge=1)
    correct_answers: int = Field(..., ge=0)
    subject: str = None
    difficulty: str = None


# Session 147 (GF86/GF87): ORM models in `models/streak_tracking.py` drift
# from the actual PostgreSQL schema in three ways:
#   1. `streak_tracking` has a NOT NULL `student_id` column the ORM does not
#      declare, so ORM-built INSERTs crash with NotNullViolationError.
#   2. `performance_history.id` is a real `uuid` column, but the ORM binds
#      it as VARCHAR with `default=lambda: str(uuid4())`, which asyncpg
#      refuses to implicitly cast with DatatypeMismatchError.
#   3. `streak_tracking.streak_start_date` is `date` (not `timestamp`) and
#      `last_correct_answer` is tz-naive — both trip asyncpg's offset-aware
#      vs offset-naive datetime subtraction.
# Fixing the ORM globally risks breaking other consumers, so this file uses
# raw SQL with named parameters instead. `gen_random_uuid()` / `now()` are
# applied at the DB level so we never bind UUID / tz-aware values from
# Python, which sidesteps all three drifts in one pass.

MILESTONES = [3, 5, 10, 15, 20, 30, 50, 100]


async def _fetch_streak(db: AsyncSession, user_id: str) -> dict | None:
    row = await db.execute(
        text(
            """
            SELECT id, current_streak, best_streak, milestones_reached
            FROM streak_tracking
            WHERE student_id = :uid
            LIMIT 1
            """
        ),
        {"uid": user_id},
    )
    first = row.mappings().first()
    if not first:
        return None
    return dict(first)


# Endpoints
@router.post("/answer", response_model=dict)
async def submit_answer_feedback(
    request: AnswerFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Cevap geri bildirimi - seri ve performans güncelleme"""
    try:
        user_id = str(current_user.id)
        streak = await _fetch_streak(db, user_id)

        if not streak:
            await db.execute(
                text(
                    """
                    INSERT INTO streak_tracking
                        (id, student_id, user_id, current_streak, best_streak,
                         milestones_reached, created_at, updated_at)
                    VALUES
                        (gen_random_uuid()::text, :uid, :uid, 0, 0,
                         '[]'::json, now(), now())
                    """
                ),
                {"uid": user_id},
            )
            streak = {
                "current_streak": 0,
                "best_streak": 0,
                "milestones_reached": [],
            }

        current_streak = int(streak["current_streak"] or 0)
        best_streak = int(streak["best_streak"] or 0)
        milestones_reached = list(streak["milestones_reached"] or [])

        milestone_reached = False
        milestone_value = 0

        if request.is_correct:
            old_streak = current_streak
            current_streak += 1
            best_streak = max(best_streak, current_streak)

            for milestone in MILESTONES:
                if current_streak >= milestone and old_streak < milestone:
                    milestone_reached = True
                    milestone_value = milestone
                    if milestone not in milestones_reached:
                        milestones_reached.append(milestone)
                    break

            streak_start = date.today() if current_streak == 1 else None
            await db.execute(
                text(
                    """
                    UPDATE streak_tracking
                    SET current_streak = :cs,
                        best_streak = :bs,
                        last_correct_answer = now(),
                        streak_start_date = COALESCE(:ssd, streak_start_date),
                        milestones_reached = CAST(:ms AS json),
                        updated_at = now()
                    WHERE student_id = :uid
                    """
                ),
                {
                    "cs": current_streak,
                    "bs": best_streak,
                    "ssd": streak_start,
                    "ms": _json_array(milestones_reached),
                    "uid": user_id,
                },
            )
        else:
            current_streak = 0
            await db.execute(
                text(
                    """
                    UPDATE streak_tracking
                    SET current_streak = 0,
                        streak_start_date = NULL,
                        updated_at = now()
                    WHERE student_id = :uid
                    """
                ),
                {"uid": user_id},
            )

        await db.commit()

        multiplier = 1.0 + (current_streak / 10) if current_streak >= 5 else 1.0

        return {
            "success": True,
            "is_correct": request.is_correct,
            "streak": {
                "current": current_streak,
                "best": best_streak,
                "milestone_reached": milestone_reached,
                "milestone_value": milestone_value,
            },
            "points_multiplier": round(multiplier, 1),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process answer feedback: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


def _json_array(values: list) -> str:
    """Serialize a list of ints/strings to a JSON array literal."""
    import json

    return json.dumps(values)


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Mevcut seri bilgisini getir"""
    try:
        streak = await _fetch_streak(db, str(current_user.id))

        if not streak:
            return StreakResponse(
                current_streak=0,
                best_streak=0,
                milestone_reached=False,
                multiplier=1.0,
            )

        current_streak = int(streak["current_streak"] or 0)
        best_streak = int(streak["best_streak"] or 0)

        multiplier = 1.0 + (current_streak / 10) if current_streak >= 5 else 1.0

        return StreakResponse(
            current_streak=current_streak,
            best_streak=best_streak,
            milestone_reached=False,
            multiplier=round(multiplier, 1),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get streak: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/performance", response_model=dict)
async def record_performance(
    request: PerformanceRecordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Performans kaydı oluştur"""
    try:
        user_id = str(current_user.id)
        streak = await _fetch_streak(db, user_id)
        streak_at_time = int(streak["current_streak"] or 0) if streak else 0

        row = await db.execute(
            text(
                """
                INSERT INTO performance_history
                    (id, user_id, score, questions_answered, correct_answers,
                     subject, difficulty, streak_at_time, recorded_at)
                VALUES
                    (gen_random_uuid(), :uid, :score, :qa, :ca,
                     :subj, :diff, :sat, now())
                RETURNING id
                """
            ),
            {
                "uid": user_id,
                "score": request.score,
                "qa": request.questions_answered,
                "ca": request.correct_answers,
                "subj": request.subject,
                "diff": request.difficulty,
                "sat": streak_at_time,
            },
        )
        performance_id = row.scalar_one()
        await db.commit()

        return {
            "success": True,
            "performance_id": str(performance_id),
            "score": request.score,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record performance: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/performance/history", response_model=list[PerformanceDataPoint])
async def get_performance_history(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Performans geçmişini getir"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        rows = await db.execute(
            text(
                """
                SELECT score, streak_at_time, recorded_at
                FROM performance_history
                WHERE user_id = :uid AND recorded_at >= :cutoff
                ORDER BY recorded_at
                """
            ),
            {"uid": str(current_user.id), "cutoff": cutoff_date},
        )

        data = []
        total_score = 0
        for i, perf in enumerate(rows.mappings().all(), 1):
            total_score += perf["score"]
            avg = total_score / i

            data.append(
                PerformanceDataPoint(
                    time=perf["recorded_at"].strftime("%H:%M"),
                    score=perf["score"],
                    streak=perf["streak_at_time"],
                    average=round(avg, 1),
                )
            )

        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance history: {e}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
