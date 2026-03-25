"""
KIRO2 — Learning Path Daily Plan API
=======================================
Endpoint'ler:
  GET  /api/v1/learning-path/today   → Günlük plan (ZPD+DAG+IRT+FSRS)
  GET  /api/v1/learning-path/next    → Sıradaki konu (bir ders)
  GET  /api/v1/learning-path/status  → Tüm dersler durum özeti
  GET  /api/v1/learning-path/weekly  → 7 günlük plan önizlemesi
  POST /api/v1/learning-path/goal    → Sınav hedefi kaydet
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, User
from app.services.learning_path_orchestrator import (
    LearningPathOrchestrator,
    DailyPlan,
    StudyBlock,
)

logger = logging.getLogger("kiro2.lp_daily_api")

router = APIRouter(
    prefix="/api/v1/learning-path",
    tags=["Learning Path Daily"],
)


# ─── Request / Response Modeller ─────────────────────────────────────────────

class GoalRequest(BaseModel):
    exam_type: str = Field("TYT", description="TYT | AYT_SAY | AYT_EA | AYT_SOZ")
    exam_date: str = Field(..., description="YYYY-MM-DD")
    daily_minutes: int = Field(120, ge=30, le=480)
    target_university: Optional[str] = None
    target_department: Optional[str] = None


class StudyBlockOut(BaseModel):
    subject: str
    topic_name: str
    activity_type: str
    duration_minutes: int
    question_count: int
    difficulty_band: str
    reason: str
    priority: int


class SubjectStatusOut(BaseModel):
    subject: str
    theta: float
    mastery_pct: float
    fsrs_due_count: int
    zpd_lower: float
    zpd_upper: float
    priority_score: float
    level_label: str
    needs_cat: bool = False   # True → CAT yapılmamış, seviye bilinmiyor


class DailyPlanOut(BaseModel):
    plan_date: str
    exam_date: str
    days_remaining: int
    total_minutes: int
    blocks: List[StudyBlockOut]
    fsrs_review_count: int
    new_topic_count: int
    weak_subject: Optional[str]
    strong_subject: Optional[str]
    motivational_note: str
    generated_at: str


# ─── Yardımcılar ─────────────────────────────────────────────────────────────

def _theta_label(theta: float) -> str:
    if theta < -1.5: return "Temel"
    if theta < -0.5: return "Başlangıç"
    if theta <  0.5: return "Orta"
    if theta <  1.5: return "İleri"
    return "Uzman"


async def _get_user_goal(db: AsyncSession, user_id: str) -> dict:
    """Kullanıcının kayıtlı sınav hedefini çek."""
    try:
        result = await db.execute(text("""
            SELECT exam_type, exam_date, daily_minutes
            FROM yks_exam_goals WHERE user_id = :uid
            ORDER BY created_at DESC LIMIT 1
        """), {"uid": user_id})
        row = result.fetchone()
        if row:
            return {
                "exam_type": row.exam_type,
                "exam_date": row.exam_date,
                "daily_minutes": row.daily_minutes,
            }
    except Exception:
        pass
    return {
        "exam_type": "TYT",
        "exam_date": date(date.today().year, 6, 7),
        "daily_minutes": 120,
    }


# ─── Endpoint'ler ─────────────────────────────────────────────────────────────

@router.get("/status", response_model=List[SubjectStatusOut])
async def get_subject_statuses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tüm derslerin θ, mastery%, FSRS vadesi, ZPD, öncelik özetini döndür."""
    orch = LearningPathOrchestrator(db=db)
    statuses = await orch.get_student_subject_statuses(str(current_user.id))
    return [
        SubjectStatusOut(
            subject=s.subject,
            theta=round(s.theta, 3),
            mastery_pct=s.mastery_pct,
            fsrs_due_count=s.fsrs_due_count,
            zpd_lower=round(s.zpd_lower, 2),
            zpd_upper=round(s.zpd_upper, 2),
            priority_score=s.priority_score,
            level_label="CAT Gerekiyor" if s.needs_cat else _theta_label(s.theta),
            needs_cat=s.needs_cat,
        )
        for s in statuses
    ]


@router.get("/today", response_model=DailyPlanOut)
async def get_today_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bugünkü kişiselleştirilmiş çalışma planı (ZPD+DAG+IRT+FSRS)."""
    goal = await _get_user_goal(db, str(current_user.id))
    orch = LearningPathOrchestrator(db=db)
    exam_d = goal["exam_date"] if isinstance(goal["exam_date"], date) \
             else date.fromisoformat(str(goal["exam_date"]))
    plan = await orch.generate_daily_plan(
        user_id=str(current_user.id),
        available_minutes=goal["daily_minutes"],
        exam_date=exam_d,
        exam_type=goal["exam_type"],
    )
    return DailyPlanOut(
        plan_date=plan.plan_date.isoformat(),
        exam_date=plan.exam_date.isoformat(),
        days_remaining=plan.days_remaining,
        total_minutes=plan.total_minutes,
        blocks=[StudyBlockOut(
            subject=b.subject, topic_name=b.topic_name,
            activity_type=b.activity_type, duration_minutes=b.duration_minutes,
            question_count=b.question_count, difficulty_band=b.difficulty_band,
            reason=b.reason, priority=b.priority,
        ) for b in plan.blocks],
        fsrs_review_count=plan.fsrs_review_count,
        new_topic_count=plan.new_topic_count,
        weak_subject=plan.weak_subject,
        strong_subject=plan.strong_subject,
        motivational_note=plan.motivational_note,
        generated_at=plan.generated_at.isoformat(),
    )


@router.get("/next")
async def get_next_topic(
    subject: str = Query(..., description="Ders adı (örn. MATEMATIK)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Belirli bir ders için ZPD+DAG bazlı sıradaki konuyu döndür."""
    orch = LearningPathOrchestrator(db=db)
    return await orch.get_next_topic(str(current_user.id), subject.upper())


@router.get("/weekly")
async def get_weekly_preview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """7 günlük plan önizlemesi — hangi gün hangi derse odaklanılacak."""
    goal = await _get_user_goal(db, str(current_user.id))
    orch = LearningPathOrchestrator(db=db)
    statuses = await orch.get_student_subject_statuses(str(current_user.id))
    exam_d = goal["exam_date"] if isinstance(goal["exam_date"], date) \
             else date.fromisoformat(str(goal["exam_date"]))
    today = date.today()
    subjects_by_priority = [s.subject for s in statuses]
    day_names = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]
    weekly = []
    for i in range(7):
        day = today + timedelta(days=i)
        if not subjects_by_priority:
            break
        p_idx = i % len(subjects_by_priority)
        s_idx = (i + 1) % len(subjects_by_priority)
        s_primary = statuses[p_idx]
        weekly.append({
            "date": day.isoformat(),
            "day_label": day_names[day.weekday()],
            "is_today": day == today,
            "primary_subject": subjects_by_priority[p_idx],
            "secondary_subject": subjects_by_priority[s_idx],
            "estimated_minutes": goal["daily_minutes"],
            "days_to_exam": max(1, (exam_d - day).days),
            "focus_reason": f"θ={s_primary.theta:.2f} — {_theta_label(s_primary.theta)}",
        })
    return {"weekly_plan": weekly, "exam_date": exam_d.isoformat()}


@router.post("/goal")
async def save_student_goal(
    goal: GoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Öğrencinin sınav hedefini (tarih, tür, günlük süre) kaydet."""
    try:
        await db.execute(text("""
            INSERT INTO yks_exam_goals
                (user_id, exam_type, exam_date, daily_minutes,
                 target_university, target_department, created_at, updated_at)
            VALUES (:uid, :exam_type, :exam_date, :daily_minutes,
                    :target_univ, :target_dept, NOW(), NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                exam_type = EXCLUDED.exam_type,
                exam_date = EXCLUDED.exam_date,
                daily_minutes = EXCLUDED.daily_minutes,
                target_university = EXCLUDED.target_university,
                target_department = EXCLUDED.target_department,
                updated_at = NOW()
        """), {
            "uid": str(current_user.id),
            "exam_type": goal.exam_type,
            "exam_date": date.fromisoformat(goal.exam_date) if isinstance(goal.exam_date, str) else goal.exam_date,
            "daily_minutes": goal.daily_minutes,
            "target_univ": goal.target_university,
            "target_dept": goal.target_department,
        })
        await db.commit()
        return {"status": "ok", "message": "Hedef kaydedildi."}
    except Exception as e:
        await db.rollback()
        logger.error(f"Hedef kaydetme hatası: {e}")
        raise HTTPException(status_code=500, detail="Hedef kaydedilemedi.")
