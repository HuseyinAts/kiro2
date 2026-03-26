"""
tasks/daily_plan_tasks.py
==========================
Celery task: her gece 02:00'de tüm kullanıcıların
daily_plans tablosunu yenile.
"""
from celery import shared_task
from celery.utils.log import get_task_logger
import asyncio
from datetime import date

logger = get_task_logger(__name__)


@shared_task(bind=True, name="tasks.refresh_daily_plans", max_retries=2)
def refresh_daily_plans(self):
    """
    Tüm yks_exam_goals sahibi kullanıcılar için
    günlük plan üret ve daily_plans tablosuna kaydet.
    Her gece 02:00'de Celery beat tarafından çalıştırılır.
    """
    try:
        result = asyncio.run(_async_refresh())
        logger.info(f"daily_plans yenilendi: {result}")
        return result
    except Exception as exc:
        logger.error(f"daily_plans yenileme hatasi: {exc}")
        raise self.retry(exc=exc, countdown=300)


async def _async_refresh():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    import json
    from core.config import settings

    DATABASE_URL = str(settings.database_url).replace(
        "postgresql://", "postgresql+asyncpg://"
    ).replace("postgresql+psycopg2://", "postgresql+asyncpg://")

    engine = create_async_engine(DATABASE_URL, pool_size=5)
    AsyncSess = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    from app.services.learning_path_orchestrator import LearningPathOrchestrator

    EXAM_DATE = date(date.today().year, 6, 7)
    ok = err = 0

    async with AsyncSess() as db:
        result = await db.execute(text(
            "SELECT DISTINCT user_id FROM user_theta"
        ))
        user_ids = [r[0] for r in result.fetchall()]
        logger.info(f"Planlanacak kullanici: {len(user_ids)}")

        for uid in user_ids:
            try:
                # Kullanicinin hedefini al
                goal_r = await db.execute(text(
                    "SELECT exam_type, exam_date, daily_minutes "
                    "FROM yks_exam_goals WHERE user_id = :uid"
                ), {"uid": uid})
                goal = goal_r.fetchone()
                exam_type = goal.exam_type if goal else "TYT"
                exam_dt   = goal.exam_date  if goal else EXAM_DATE
                daily_min = goal.daily_minutes if goal else 120

                if isinstance(exam_dt, str):
                    exam_dt = date.fromisoformat(str(exam_dt))

                orch = LearningPathOrchestrator(db=db)
                plan = await orch.generate_daily_plan(
                    user_id=uid,
                    available_minutes=daily_min,
                    exam_date=exam_dt,
                    exam_type=exam_type,
                )

                await db.execute(text("""
                    INSERT INTO daily_plans
                        (user_id, plan_date, exam_date, days_remaining,
                         total_minutes, plan_json, weak_subject,
                         strong_subject, motivational_note, generated_at)
                    VALUES
                        (:uid, :plan_date, :exam_date, :days_rem,
                         :total_min, :plan_json, :weak,
                         :strong, :note, NOW())
                    ON CONFLICT (user_id, plan_date) DO UPDATE SET
                        total_minutes     = EXCLUDED.total_minutes,
                        plan_json         = EXCLUDED.plan_json,
                        weak_subject      = EXCLUDED.weak_subject,
                        strong_subject    = EXCLUDED.strong_subject,
                        motivational_note = EXCLUDED.motivational_note,
                        generated_at      = NOW()
                """), {
                    "uid":       uid,
                    "plan_date": plan.plan_date,
                    "exam_date": plan.exam_date,
                    "days_rem":  plan.days_remaining,
                    "total_min": plan.total_minutes,
                    "plan_json": json.dumps({
                        "blocks": [
                            {"subject": b.subject,
                             "topic_name": b.topic_name,
                             "activity_type": b.activity_type,
                             "duration_minutes": b.duration_minutes,
                             "question_count": b.question_count,
                             "difficulty_band": b.difficulty_band,
                             "reason": b.reason,
                             "priority": b.priority}
                            for b in plan.blocks
                        ]
                    }, ensure_ascii=False),
                    "weak":  plan.weak_subject,
                    "strong": plan.strong_subject,
                    "note":  plan.motivational_note,
                })
                await db.commit()
                ok += 1
            except Exception as e:
                await db.rollback()
                err += 1
                logger.error(f"Plan hatasi uid={uid[:16]}: {e}")

    await engine.dispose()
    return {"ok": ok, "err": err, "date": str(date.today())}
