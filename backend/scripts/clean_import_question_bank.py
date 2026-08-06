import asyncio
import hashlib
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: PTH100, PTH120

from sqlalchemy import select, text
from uuid6 import uuid7

from core.database import db_manager, get_db_session_context
from data.question_bank_data import QuestionBankData
from models.question_bank import (
    QuestionBankItem,
    QuestionDifficultyLevel,
    TopicHierarchy,
)


async def clean_import():
    print("Starting clean import of question bank data...")
    await db_manager.initialize()

    try:
        async with get_db_session_context() as session:
            # Load seed data
            data = QuestionBankData()
            all_questions = data.tyt_questions + data.ayt_questions + data.ydt_questions

            print(f"Loaded {len(all_questions)} questions from seed data.")

            # Truncate existing question_bank table safely
            await session.execute(text("TRUNCATE TABLE question_bank CASCADE"))

            # Helper dict to store created topics
            topic_map = {}

            for q in all_questions:
                # Process topics
                konu = q.get("konu")
                alt_konu = q.get("alt_konu")
                topic_key = f"{konu} - {alt_konu}"

                if topic_key not in topic_map:
                    # Check if exists in DB
                    stmt = select(TopicHierarchy).where(
                        TopicHierarchy.name_tr == alt_konu
                    )
                    result = await session.execute(stmt)
                    topic = result.scalars().first()

                    if not topic:
                        # Find parent
                        parent_stmt = select(TopicHierarchy).where(
                            TopicHierarchy.name_tr == konu
                        )
                        parent_result = await session.execute(parent_stmt)
                        parent = parent_result.scalars().first()

                        if not parent:
                            parent = TopicHierarchy(
                                code=f"SEED_{konu.replace(' ', '_').upper()}",
                                name_tr=konu,
                                level=1,
                            )
                            session.add(parent)
                            await session.flush()

                        topic = TopicHierarchy(
                            code=f"SEED_{alt_konu.replace(' ', '_').upper()}",
                            name_tr=alt_konu,
                            level=2,
                            parent_id=parent.id,
                        )
                        session.add(topic)
                        await session.flush()

                    topic_map[topic_key] = topic.id

                # Map options
                secenekler = q.get("secenekler", [])

                def clean_opt(opt_str):
                    if ")" in opt_str:
                        return opt_str.split(")", 1)[1].strip()
                    return opt_str

                opt_a = clean_opt(secenekler[0]) if len(secenekler) > 0 else ""
                opt_b = clean_opt(secenekler[1]) if len(secenekler) > 1 else ""
                opt_c = clean_opt(secenekler[2]) if len(secenekler) > 2 else ""
                opt_d = clean_opt(secenekler[3]) if len(secenekler) > 3 else ""
                opt_e = clean_opt(secenekler[4]) if len(secenekler) > 4 else None

                # Map difficulty
                z = q.get("zorluk_seviyesi", "orta").lower()
                diff_map = {
                    "çok kolay": QuestionDifficultyLevel.VERY_EASY,
                    "kolay": QuestionDifficultyLevel.EASY,
                    "orta": QuestionDifficultyLevel.MEDIUM,
                    "zor": QuestionDifficultyLevel.HARD,
                    "çok zor": QuestionDifficultyLevel.VERY_HARD,
                }
                diff = diff_map.get(z, QuestionDifficultyLevel.MEDIUM)

                exam_type = q.get("sinav_tipi", "TYT")
                subject_area = q.get("konu", "Genel")

                # Create question item
                q_item = QuestionBankItem(
                    id=str(uuid7()),
                    question_text=q["soru_metni"],
                    option_a=opt_a,
                    option_b=opt_b,
                    option_c=opt_c,
                    option_d=opt_d,
                    option_e=opt_e,
                    correct_answer=q["dogru_cevap"],
                    explanation=q.get("cozum_aciklamasi"),
                    primary_topic_id=topic_map[topic_key],
                    difficulty_level=diff,
                    irt_difficulty=q.get("irt_difficulty", 0.0),
                    irt_discrimination=q.get("irt_discrimination", 1.0),
                    irt_guessing=q.get("irt_guessing", 0.25),
                    irt_upper_asymptote=1.0,
                    is_active=True,
                    bloom_level=1,
                    bloom_category="knowledge",
                    exam_type=exam_type,
                    subject_area=subject_area,
                    grade_level=12,
                    # md5 burada içerik parmak izi, güvenlik primitifi değil.
                    # NOT: tuz olarak soru_id kullanılması, aynı metnin her
                    # kopyasına farklı hash verdiği için uq_qb_soru_hash_active
                    # kısıtının etrafından dolaşılmasına yol açtı (5 Ağu 2026).
                    soru_hash=hashlib.md5(
                        f"{q.get('soru_id', '')}_{q['soru_metni']}".encode(),
                        usedforsecurity=False,
                    ).hexdigest(),
                )
                session.add(q_item)

            print("Committing to database...")
            await session.commit()
            print("Clean import completed successfully!")

    except Exception as e:
        print(f"Error during clean import: {e}")
    finally:
        await db_manager.close()


if __name__ == "__main__":
    # --- DEPRECATED MÜHÜR (5 Ağu 2026 içerik kaybı) ---
    # Satır 28'deki TRUNCATE ... CASCADE + 21 sentetik tohum sorusunun yazımı
    # question_bank'ı 187.835 satırdan 2.304 satır / 21 benzersiz metne düşürdü
    # (%98,77 kayıp). soru_hash kimlik-tuzlu üretildiği için benzersizlik kapısı
    # (uq_qb_soru_hash_active) çalıştı ama ETRAFINDAN DOLAŞILDI — kapı ölü değildi.
    # Kurtarma: backups/kiro2_pre_schema_restore_20260727.dump (şema 78/78 uyumlu).
    # Üretim veritabanında çalıştırma YASAK.
    if os.environ.get("ALLOW_DESTRUCTIVE_SEED_IMPORT") != "1":
        sys.stderr.write(
            "MÜHÜRLÜ (5 Ağu 2026): TRUNCATE + tohum yazımı 187.835 soruyu 2.304'e "
            "düşürdü. Override: ALLOW_DESTRUCTIVE_SEED_IMPORT=1\n"
        )
        sys.exit(2)
    asyncio.run(clean_import())
