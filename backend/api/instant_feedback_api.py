"""
Task 92: Instant Feedback API
DEHB için anında geri bildirim sistemi
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from models.database import User
from models.streak_tracking import StreakTracking, PerformanceHistory
from core.structured_logger import get_logger

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


# Endpoints
@router.post("/answer", response_model=Dict)
def submit_answer_feedback(
    request: AnswerFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cevap geri bildirimi - seri ve performans güncelleme"""
    try:
        streak = (
            db.query(StreakTracking)
            .filter(StreakTracking.user_id == current_user.id)
            .first()
        )

        if not streak:
            streak = StreakTracking(
                user_id=current_user.id, current_streak=0, best_streak=0
            )
            db.add(streak)

        milestone_reached = False
        milestone_value = 0
        MILESTONES = [3, 5, 10, 15, 20, 30, 50, 100]

        if request.is_correct:
            old_streak = streak.current_streak
            streak.current_streak += 1
            streak.last_correct_answer = datetime.now(timezone.utc)

            if streak.current_streak == 1:
                streak.streak_start_date = datetime.now(timezone.utc)

            if streak.current_streak > streak.best_streak:
                streak.best_streak = streak.current_streak

            # Check milestones
            for milestone in MILESTONES:
                if streak.current_streak >= milestone and old_streak < milestone:
                    milestone_reached = True
                    milestone_value = milestone
                    milestones = streak.milestones_reached or []
                    if milestone not in milestones:
                        milestones.append(milestone)
                        streak.milestones_reached = milestones
                    break
        else:
            streak.current_streak = 0
            streak.streak_start_date = None

        db.commit()

        multiplier = (
            1.0 + (streak.current_streak / 10) if streak.current_streak >= 5 else 1.0
        )

        return {
            "success": True,
            "is_correct": request.is_correct,
            "streak": {
                "current": streak.current_streak,
                "best": streak.best_streak,
                "milestone_reached": milestone_reached,
                "milestone_value": milestone_value,
            },
            "points_multiplier": round(multiplier, 1),
        }

    except Exception as e:
        logger.error(f"Failed to process answer feedback: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/streak", response_model=StreakResponse)
def get_streak(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Mevcut seri bilgisini getir"""
    try:
        streak = (
            db.query(StreakTracking)
            .filter(StreakTracking.user_id == current_user.id)
            .first()
        )

        if not streak:
            return StreakResponse(
                current_streak=0, best_streak=0, milestone_reached=False, multiplier=1.0
            )

        multiplier = (
            1.0 + (streak.current_streak / 10) if streak.current_streak >= 5 else 1.0
        )

        return StreakResponse(
            current_streak=streak.current_streak,
            best_streak=streak.best_streak,
            milestone_reached=False,
            multiplier=round(multiplier, 1),
        )

    except Exception as e:
        logger.error(f"Failed to get streak: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/performance", response_model=Dict)
def record_performance(
    request: PerformanceRecordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Performans kaydı oluştur"""
    try:
        streak = (
            db.query(StreakTracking)
            .filter(StreakTracking.user_id == current_user.id)
            .first()
        )

        performance = PerformanceHistory(
            user_id=current_user.id,
            score=request.score,
            questions_answered=request.questions_answered,
            correct_answers=request.correct_answers,
            subject=request.subject,
            difficulty=request.difficulty,
            streak_at_time=streak.current_streak if streak else 0,
        )

        db.add(performance)
        db.commit()

        return {"success": True, "performance_id": str(performance.id), "score": request.score}

    except Exception as e:
        logger.error(f"Failed to record performance: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/performance/history", response_model=List[PerformanceDataPoint])
def get_performance_history(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Performans geçmişini getir"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        performances = (
            db.query(PerformanceHistory)
            .filter(
                PerformanceHistory.user_id == current_user.id,
                PerformanceHistory.recorded_at >= cutoff_date,
            )
            .order_by(PerformanceHistory.recorded_at)
            .all()
        )

        # Calculate running average
        data = []
        total_score = 0
        for i, perf in enumerate(performances, 1):
            total_score += perf.score
            avg = total_score / i

            data.append(
                PerformanceDataPoint(
                    time=perf.recorded_at.strftime("%H:%M"),
                    score=perf.score,
                    streak=perf.streak_at_time,
                    average=round(avg, 1),
                )
            )

        return data

    except Exception as e:
        logger.error(f"Failed to get performance history: {e}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")
