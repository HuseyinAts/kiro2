"""
Gunluk plan uretimini test et - learning_path_orchestrator ile
"""
import asyncio, sys, json
sys.path.insert(0, r'C:\Users\husey\kiro2\backend')

async def main():
    from datetime import date
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text

    DB_URL = "postgresql+asyncpg://postgres:changeme_strong_password_here@localhost:5434/kiro2"
    engine = create_async_engine(DB_URL, pool_size=3)
    AsyncSess = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSess() as db:
        # yks_exam_goals sahibi bir kullanici bul
        r = await db.execute(text(
            "SELECT user_id::text, exam_type, exam_date FROM yks_exam_goals LIMIT 1"
        ))
        row = r.fetchone()
        if not row:
            print("yks_exam_goals bos!")
            return
        uid, exam_type, exam_date = str(row[0]), row[1], row[2]
        print(f"Test kullanici: {uid[:16]}... | {exam_type} | {exam_date}")

        # student_abilities kontrol
        r2 = await db.execute(text(
            "SELECT subject_id, theta FROM student_abilities WHERE student_id=:uid LIMIT 5"
        ), {"uid": uid})
        rows2 = r2.fetchall()
        print(f"student_abilities: {len(rows2)} ders")
        for row2 in rows2:
            print(f"  subject_id={row2[0]} theta={row2[1]}")

        # Orchestrator import dene
        try:
            from app.services.learning_path_orchestrator import LearningPathOrchestrator
            orch = LearningPathOrchestrator(db=db)
            exam_d = exam_date if isinstance(exam_date, date) else date.fromisoformat(str(exam_date))
            plan = await orch.generate_daily_plan(
                user_id=uid,
                available_minutes=120,
                exam_date=exam_d,
                exam_type=exam_type,
            )
            print(f"\nPLAN OK!")
            print(f"  plan_date={plan.plan_date}")
            print(f"  days_remaining={plan.days_remaining}")
            print(f"  total_minutes={plan.total_minutes}")
            print(f"  blok sayisi={len(plan.blocks)}")
            if plan.blocks:
                b = plan.blocks[0]
                print(f"  ilk blok: {b.subject} / {b.topic_name} / {b.activity_type}")
        except Exception as e:
            print(f"\nOrchestrator HATA: {type(e).__name__}: {e}")

    await engine.dispose()

asyncio.run(main())
