"""
Study Planner Service — F7 Çalışma Planlayıcı

YKS tarihine kadar kalan haftalara konu dağılımı yapar.
IRT ability tahmini zayıf konulara daha fazla süre atar.
Monte Carlo simülasyonu ile tahmini net puan hesaplar.
"""
from __future__ import annotations

import math
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger("study_planner_service")

# YKS konu havuzu — ağırlıklı tahsis için
YKS_SUBJECTS: list[dict] = [
    {"id": "matematik", "name": "Matematik", "weight": 1.5, "question_count": 40},
    {"id": "fizik", "name": "Fizik", "weight": 1.2, "question_count": 14},
    {"id": "kimya", "name": "Kimya", "weight": 1.2, "question_count": 13},
    {"id": "biyoloji", "name": "Biyoloji", "weight": 1.0, "question_count": 13},
    {"id": "turkce", "name": "Türkçe", "weight": 1.3, "question_count": 40},
    {"id": "tarih", "name": "Tarih", "weight": 1.0, "question_count": 10},
    {"id": "cografya", "name": "Coğrafya", "weight": 0.8, "question_count": 5},
    {"id": "geometri", "name": "Geometri", "weight": 1.2, "question_count": 10},
]

# Simülasyon parametreleri
MONTE_CARLO_RUNS = 1000
DEFAULT_ABILITY = 0.0   # IRT theta (standart normal)


async def get_current_plan(*, db: AsyncSession, student_id: str) -> dict | None:
    """Öğrencinin aktif çalışma planını haftalık hedeflerle birlikte getirir.

    Returns:
        {plan_id, yks_date, days_left, total_weeks, current_week, weekly_hours,
         weeks: [{week_number, topics, target_questions,
                  completed_questions, accuracy}]}
        ya da None (plan yoksa).
    """
    try:
        from sqlalchemy import and_, select
        from sqlalchemy.orm import selectinload

        from models.study_planner import StudyPlan  # lazy import

        result = await db.execute(
            select(StudyPlan)
            .options(selectinload(StudyPlan.weekly_goals))
            .where(
                and_(
                    StudyPlan.student_id == student_id,
                    StudyPlan.is_active == True,  # noqa: E712
                )
            )
            .order_by(StudyPlan.created_at.desc())
            .limit(1)
        )
        plan = result.scalars().first()
        if not plan:
            return None

        return _serialize_plan(plan)

    except Exception as exc:
        logger.warning(
            "Study plan fetch fallback",
            extra_data={"student_id": student_id, "error": str(exc)},
        )
        return None


async def create_or_update_plan(
    *, db: AsyncSession, student_id: str, yks_date: str, weekly_hours: int = 20
) -> dict:
    """Çalışma planı oluşturur ya da mevcut aktif planı günceller.

    Kalan haftaları hesaplar, IRT ability tahminlerine göre konulara
    ağırlıklı soru hedefi atar.

    Args:
        db: Veritabanı oturumu.
        student_id: Öğrenci kimliği.
        yks_date: YKS tarihi (ISO format: 'YYYY-MM-DD').
        weekly_hours: Haftada kaç saat çalışma planlanıyor (varsayılan: 20).

    Returns:
        Oluşturulan/güncellenen plan dict'i.
    """
    try:
        from sqlalchemy import and_, select
        from sqlalchemy.orm import selectinload

        from models.study_planner import StudyPlan, WeeklyGoal  # lazy import

        # Mevcut aktif planı devre dışı bırak
        existing_result = await db.execute(
            select(StudyPlan)
            .options(selectinload(StudyPlan.weekly_goals))
            .where(
                and_(
                    StudyPlan.student_id == student_id,
                    StudyPlan.is_active == True,  # noqa: E712
                )
            )
        )
        existing = existing_result.scalars().first()
        if existing:
            existing.is_active = False
            db.add(existing)

        # Kalan hafta sayısını hesapla
        today = date.today()
        try:
            exam_date = date.fromisoformat(yks_date)
        except ValueError:
            exam_date = today + timedelta(weeks=20)  # Geçersiz tarihe güvenli fallback

        delta_days = (exam_date - today).days
        total_weeks = max(1, delta_days // 7)

        # IRT ability tabanlı konu ağırlıkları al
        abilities = await _get_subject_abilities(db=db, student_id=student_id)

        plan = StudyPlan(
            student_id=student_id,
            yks_date=exam_date,
            is_active=True,
            total_weeks=total_weeks,
            weekly_hours=weekly_hours,
        )
        db.add(plan)
        await db.flush()  # plan.id'yi al

        # Haftalık soru hedeflerini dağıt
        # Zayıf konular (düşük ability) daha fazla tekrar alır
        weekly_question_budget = weekly_hours * 15  # ~15 soru/saat
        topic_weights = _calculate_topic_weights(abilities)

        for week_num in range(1, total_weeks + 1):
            # İlk haftalarda temel konular, son haftalarda tekrar ağırlıklı
            progress_ratio = week_num / total_weeks
            topics = _select_topics_for_week(topic_weights, progress_ratio)
            target = int(weekly_question_budget * (1 + 0.1 * progress_ratio))

            goal = WeeklyGoal(
                plan_id=plan.id,
                week_number=week_num,
                topics=topics,
                target_questions=target,
                completed_questions=0,
            )
            db.add(goal)

        await db.commit()
        await db.refresh(plan)

        logger.info(
            "Study plan created",
            extra_data={
                "student_id": student_id,
                "total_weeks": total_weeks,
                "yks_date": yks_date,
                "weekly_hours": weekly_hours,
            },
        )

        return _serialize_plan(plan)

    except Exception as exc:
        logger.error(
            "Study plan creation failed",
            extra_data={"student_id": student_id, "error": str(exc)},
        )
        # Fallback: DB olmadan basit plan döndür
        return _mock_plan(
            student_id=student_id, yks_date=yks_date, weekly_hours=weekly_hours
        )


async def update_weekly_progress(
    *, db: AsyncSession, student_id: str, week_number: int, completed_questions: int
) -> dict:
    """Belirli bir haftanın tamamlanan soru sayısını günceller.

    Args:
        db: Veritabanı oturumu.
        student_id: Öğrenci kimliği.
        week_number: Hafta numarası (1-indexed).
        completed_questions: Tamamlanan soru sayısı.

    Returns:
        {plan_id, week_number, target_questions, completed_questions,
         completion_rate, updated}
    """
    try:
        from sqlalchemy import and_, select

        from models.study_planner import StudyPlan, WeeklyGoal  # lazy import

        # Aktif planı bul
        plan_result = await db.execute(
            select(StudyPlan).where(
                and_(
                    StudyPlan.student_id == student_id,
                    StudyPlan.is_active == True,  # noqa: E712
                )
            )
        )
        plan = plan_result.scalars().first()
        if not plan:
            return {"error": "Aktif plan bulunamadı", "updated": False}

        goal_result = await db.execute(
            select(WeeklyGoal).where(
                and_(
                    WeeklyGoal.plan_id == plan.id,
                    WeeklyGoal.week_number == week_number,
                )
            )
        )
        goal = goal_result.scalars().first()
        if not goal:
            return {"error": f"Hafta {week_number} bulunamadı", "updated": False}

        goal.completed_questions = completed_questions
        db.add(goal)
        await db.commit()
        await db.refresh(goal)

        completion_rate = (
            completed_questions / goal.target_questions
            if goal.target_questions > 0
            else 0.0
        )

        return {
            "plan_id": plan.id,
            "week_number": week_number,
            "target_questions": goal.target_questions,
            "completed_questions": completed_questions,
            "completion_rate": round(completion_rate, 3),
            "updated": True,
        }

    except Exception as exc:
        logger.warning(
            "Weekly progress update fallback",
            extra_data={
                "student_id": student_id,
                "week_number": week_number,
                "error": str(exc),
            },
        )
        return {"error": str(exc), "updated": False}


async def project_score(*, db: AsyncSession, student_id: str) -> dict:
    """Monte Carlo simülasyonu ile tahmini YKS net skorunu hesaplar.

    Her konu için IRT ability tahminini kullanarak 1000 simülasyon çalıştırır.
    Güven aralığı %90 (5. ile 95. yüzdelik dilim).

    Returns:
        {projected_net: float, confidence_interval: [low, high], trend: str,
         subject_projections: [{subject, projected_net, ability}]}
    """
    abilities = await _get_subject_abilities(db=db, student_id=student_id)

    results: list[float] = []
    subject_projections: list[dict] = []

    for run in range(MONTE_CARLO_RUNS):
        total_net = 0.0
        for subject in YKS_SUBJECTS:
            ability = abilities.get(subject["id"], DEFAULT_ABILITY)
            q_count = subject["question_count"]

            # IRT 3PL başarı olasılığı (basitleştirilmiş: c=0.2, a=1.0)
            p_correct = _irt_probability(ability)
            # YKS'de yanlış -0.25 net etkisi var
            correct = sum(1 for _ in range(q_count) if random.random() < p_correct)
            wrong = q_count - correct
            net = correct - (wrong * 0.25)
            total_net += max(0, net)

        results.append(total_net)

    results.sort()
    low = results[int(MONTE_CARLO_RUNS * 0.05)]
    high = results[int(MONTE_CARLO_RUNS * 0.95)]
    median = results[MONTE_CARLO_RUNS // 2]

    # Trend: Son 4 hafta progress verisi ile hesapla
    trend = await _calculate_progress_trend(db=db, student_id=student_id)

    # Konu bazlı projeksiyonlar
    for subject in YKS_SUBJECTS:
        ability = abilities.get(subject["id"], DEFAULT_ABILITY)
        p = _irt_probability(ability)
        proj_correct = p * subject["question_count"]
        proj_wrong = (1 - p) * subject["question_count"]
        proj_net = max(0, proj_correct - proj_wrong * 0.25)
        subject_projections.append({
            "subject": subject["name"],
            "projected_net": round(proj_net, 1),
            "ability": round(ability, 2),
            "p_correct": round(p, 2),
        })

    return {
        "projected_net": round(median, 1),
        "confidence_interval": [round(low, 1), round(high, 1)],
        "trend": trend,
        "simulation_runs": MONTE_CARLO_RUNS,
        "subject_projections": sorted(subject_projections, key=lambda x: x["subject"]),
    }


async def get_weekly_report(*, db: AsyncSession, student_id: str) -> dict:
    """Mevcut hafta için plan vs gerçek karşılaştırması döndürür.

    Returns:
        {week_number, target_questions, completed_questions, completion_rate,
         topics, days_remaining_in_week, on_track: bool}
    """
    try:
        from sqlalchemy import and_, select
        from sqlalchemy.orm import selectinload

        from models.study_planner import StudyPlan  # lazy import

        plan_result = await db.execute(
            select(StudyPlan)
            .options(selectinload(StudyPlan.weekly_goals))
            .where(
                and_(
                    StudyPlan.student_id == student_id,
                    StudyPlan.is_active == True,  # noqa: E712
                )
            )
        )
        plan = plan_result.scalars().first()
        if not plan:
            return {"error": "Aktif plan bulunamadı"}

        current_week = _current_week_number(plan)
        goal = next(
            (g for g in plan.weekly_goals if g.week_number == current_week), None
        )

        if not goal:
            return {"error": f"Hafta {current_week} hedefi bulunamadı"}

        completion_rate = (
            goal.completed_questions / goal.target_questions
            if goal.target_questions > 0
            else 0.0
        )

        # Hafta içinde kalan gün sayısı (Pazartesi=0)
        today = datetime.now(timezone.utc)
        days_remaining = 6 - today.weekday()  # 0=Pazartesi, 6=Pazar

        # Günlük yetişmek için gereken soru sayısı
        remaining_questions = max(0, goal.target_questions - goal.completed_questions)
        daily_target = (
            math.ceil(remaining_questions / days_remaining)
            if days_remaining > 0
            else remaining_questions
        )

        return {
            "week_number": current_week,
            "target_questions": goal.target_questions,
            "completed_questions": goal.completed_questions,
            "completion_rate": round(completion_rate, 3),
            "topics": goal.topics or [],
            "days_remaining_in_week": days_remaining,
            "daily_target_to_catch_up": daily_target,
            "on_track": completion_rate >= (1 - days_remaining / 7),
        }

    except Exception as exc:
        logger.warning(
            "Weekly report fallback",
            extra_data={"student_id": student_id, "error": str(exc)},
        )
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# İç yardımcılar
# ---------------------------------------------------------------------------

def _irt_probability(ability: float, difficulty: float = 0.0) -> float:
    """IRT 3PL başarı olasılığı (basitleştirilmiş: a=1.0, c=0.2)."""
    c = 0.20
    return c + (1 - c) / (1 + math.exp(-1.0 * (ability - difficulty)))


async def _get_subject_abilities(
    *, db: AsyncSession, student_id: str
) -> dict[str, float]:
    """Öğrencinin konu başına IRT ability tahminlerini getirir."""
    try:
        from sqlalchemy import select

        from models.learning_path import LearningPathStudentProfile  # lazy import

        result = await db.execute(
            select(LearningPathStudentProfile).where(
                LearningPathStudentProfile.student_id == student_id
            )
        )
        profile = result.scalars().first()

        if profile and profile.subject_abilities:
            return dict(profile.subject_abilities)

    except Exception:
        pass

    # Varsayılan: tüm konularda orta seviye (0.0)
    return {s["id"]: DEFAULT_ABILITY for s in YKS_SUBJECTS}


def _calculate_topic_weights(abilities: dict[str, float]) -> dict[str, float]:
    """Ability tahminlerine göre ters ağırlıklandırma yapar.

    Düşük ability → daha fazla çalışma süresi atar.
    """
    weights: dict[str, float] = {}
    for subject in YKS_SUBJECTS:
        sid = subject["id"]
        ability = abilities.get(sid, DEFAULT_ABILITY)
        # Ability -2 ile +2 arasında; düşük ability → yüksek ağırlık
        raw_weight = subject["weight"] * (1 + max(0, -ability))
        weights[sid] = raw_weight

    # Normalize et (toplam = 1)
    total = sum(weights.values()) or 1.0
    return {k: v / total for k, v in weights.items()}


def _select_topics_for_week(
    topic_weights: dict[str, float], progress_ratio: float
) -> list[str]:
    """Hafta için 3-4 konu seçer. Son haftalarda düşük ability konulara odaklanır."""
    # Ağırlığa göre sırala
    sorted_topics = sorted(topic_weights.items(), key=lambda x: x[1], reverse=True)

    # İlk yarıda tüm konuları dengeli dağıt; ikinci yarıda en zayıf konulara odaklan
    if progress_ratio < 0.5:
        selected = [t[0] for t in sorted_topics[:4]]
    else:
        # En yüksek ağırlıklı (en zayıf) 3 konu
        selected = [t[0] for t in sorted_topics[:3]]

    return selected


def _current_week_number(plan) -> int:
    """Planın başlangıcına göre hangi haftada olduğumuzu hesaplar."""
    today = date.today()
    plan_start: date = (
        plan.created_at.date()
        if isinstance(plan.created_at, datetime)
        else plan.created_at
    )
    delta = today - plan_start
    return max(1, min(plan.total_weeks, (delta.days // 7) + 1))


def _serialize_plan(plan) -> dict:
    """StudyPlan modelini dict'e dönüştürür."""
    today = date.today()
    exam_date = (
        plan.yks_date
        if isinstance(plan.yks_date, date)
        else date.fromisoformat(str(plan.yks_date))
    )
    days_left = max(0, (exam_date - today).days)
    current_week = _current_week_number(plan)

    goals = (
        sorted(plan.weekly_goals, key=lambda g: g.week_number)
        if plan.weekly_goals
        else []
    )
    total_target = sum(g.target_questions for g in goals)
    total_completed = sum(g.completed_questions for g in goals)

    return {
        "plan_id": plan.id,
        "yks_date": exam_date.isoformat(),
        "days_left": days_left,
        "total_weeks": plan.total_weeks,
        "current_week": current_week,
        "weekly_hours": getattr(plan, "weekly_hours", 20),
        "total_target_questions": total_target,
        "total_completed_questions": total_completed,
        "overall_completion_rate": (
            round(total_completed / total_target, 3) if total_target > 0 else 0.0
        ),
        "weeks": [
            {
                "week_number": g.week_number,
                "topics": g.topics or [],
                "target_questions": g.target_questions,
                "completed_questions": g.completed_questions,
                "accuracy": getattr(g, "accuracy_rate", None),
                "is_current": g.week_number == current_week,
            }
            for g in goals
        ],
    }


def _mock_plan(*, student_id: str, yks_date: str, weekly_hours: int) -> dict:
    """DB olmadan basit bir plan yapısı döndürür (fallback)."""
    today = date.today()
    try:
        exam_date = date.fromisoformat(yks_date)
    except ValueError:
        exam_date = today + timedelta(weeks=20)

    days_left = max(0, (exam_date - today).days)
    total_weeks = max(1, days_left // 7)
    weekly_target = weekly_hours * 15

    return {
        "plan_id": str(uuid.uuid4()),
        "yks_date": exam_date.isoformat(),
        "days_left": days_left,
        "total_weeks": total_weeks,
        "current_week": 1,
        "weekly_hours": weekly_hours,
        "total_target_questions": weekly_target * total_weeks,
        "total_completed_questions": 0,
        "overall_completion_rate": 0.0,
        "weeks": [
            {
                "week_number": w,
                "topics": [s["id"] for s in YKS_SUBJECTS[: 4]],
                "target_questions": weekly_target,
                "completed_questions": 0,
                "accuracy": None,
                "is_current": w == 1,
            }
            for w in range(1, min(total_weeks + 1, 5))  # Sadece ilk 4 haftayı önizle
        ],
    }


async def _calculate_progress_trend(*, db: AsyncSession, student_id: str) -> str:
    """Son 4 haftanın completion rate'ini analiz eder ve trend döndürür."""
    try:
        from sqlalchemy import and_, select
        from sqlalchemy.orm import selectinload

        from models.study_planner import StudyPlan  # lazy import

        plan_result = await db.execute(
            select(StudyPlan)
            .options(selectinload(StudyPlan.weekly_goals))
            .where(
                and_(
                    StudyPlan.student_id == student_id,
                    StudyPlan.is_active == True,  # noqa: E712
                )
            )
        )
        plan = plan_result.scalars().first()
        if not plan or not plan.weekly_goals:
            return "stable"

        current_week = _current_week_number(plan)
        recent_goals = [
            g for g in plan.weekly_goals
            if 1 <= g.week_number < current_week
        ][-4:]  # Son 4 hafta

        if len(recent_goals) < 2:
            return "stable"

        rates = [
            g.completed_questions / g.target_questions
            if g.target_questions > 0
            else 0.0
            for g in recent_goals
        ]

        # Basit lineer trend: sonlar mı artıyor mu azalıyor mu?
        first_half = sum(rates[: len(rates) // 2]) / (len(rates) // 2)
        second_half = sum(rates[len(rates) // 2 :]) / (len(rates) - len(rates) // 2)

        if second_half > first_half + 0.05:
            return "improving"
        elif second_half < first_half - 0.05:
            return "declining"
        return "stable"

    except Exception:
        return "stable"
