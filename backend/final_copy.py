#!/usr/bin/env python3
import asyncio, asyncpg, logging, json, uuid, os
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def copy():
    db_password = os.getenv("DATABASE_PASSWORD", "")
    conn = await asyncpg.connect(host="localhost", port=5434, user="postgres", password=db_password, database="turkiye_sinav_db")
    try:
        sorular = await conn.fetch("SELECT metin, secenekler, dogru_cevap, sinav_tipi, konu, alt_konu, zorluk, irt_discrimination, irt_difficulty, irt_guessing FROM sorular WHERE aktif = true")
        logger.info(f"{len(sorular)} questions found")
        inserted = 0
        for s in sorular:
            try:
                opts = json.loads(s['secenekler']) if isinstance(s['secenekler'], str) else s['secenekler']
                konu = (s['konu'] or 'Test').split('-')[0].strip().upper()
                subject = {'MATEMATIK': 'MATEMATIK', 'TÜRKÇE': 'TURKCE', 'TURKCE': 'TURKCE', 'FIZIK': 'FIZIK', 'KIMYA': 'KIMYA', 'BIYOLOJI': 'BIYOLOJI', 'TEST': 'MATEMATIK'}.get(konu, 'MATEMATIK')
                diff = {'kolay': 'EASY', 'orta': 'MEDIUM', 'zor': 'HARD'}.get(s['zorluk'], 'MEDIUM')
                await conn.execute("""
                    INSERT INTO questions (id, question_text, option_a, option_b, option_c, option_d, option_e, correct_answer, exam_type, subject_area, topic, subtopic, difficulty, irt_discrimination, irt_difficulty, irt_guessing, aktif)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, true)
                """, str(uuid.uuid4()), s['metin'], opts.get('A',''), opts.get('B',''), opts.get('C',''), opts.get('D',''), opts.get('E',''), s['dogru_cevap'], s['sinav_tipi'], subject, s['konu'], s['alt_konu'], diff, 
                s['irt_discrimination'] or 1.0, s['irt_difficulty'] or 0.0, s['irt_guessing'] or 0.25)
                inserted += 1
            except Exception as e:
                logger.error(f"Error: {str(e)[:100]}")
        logger.info(f"Copied {inserted}/{len(sorular)}")
        count = await conn.fetchval("SELECT COUNT(*) FROM questions")
        logger.info(f"Total in questions table: {count}")
        await conn.close()
        return inserted
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 0

count = asyncio.run(copy())
print(f"\nSuccess! {count} questions copied to questions table!")
