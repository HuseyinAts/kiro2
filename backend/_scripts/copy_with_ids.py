#!/usr/bin/env python3
import asyncio, asyncpg, logging, json, uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def copy_questions():
    conn = await asyncpg.connect(host="localhost", port=5434, user="postgres", password="1470", database="turkiye_sinav_db")
    try:
        sorular = await conn.fetch("SELECT metin, secenekler, dogru_cevap, sinav_tipi, konu, alt_konu, zorluk, irt_discrimination, irt_difficulty, irt_guessing FROM sorular WHERE aktif = true")
        logger.info(f"Found {len(sorular)} questions")
        inserted = 0
        for soru in sorular:
            try:
                secenekler = json.loads(soru['secenekler']) if isinstance(soru['secenekler'], str) else soru['secenekler']
                konu = (soru['konu'] or 'Test').split('-')[0].strip().upper()
                subject_map = {'MATEMATIK': 'MATEMATIK', 'TÜRKÇE': 'TURKCE', 'TURKCE': 'TURKCE', 'FIZIK': 'FIZIK', 'KIMYA': 'KIMYA', 'BIYOLOJI': 'BIYOLOJI', 'TEST': 'MATEMATIK'}
                subject_area = subject_map.get(konu, 'MATEMATIK')
                zorluk_map = {'kolay': 'EASY', 'orta': 'MEDIUM', 'zor': 'HARD'}
                difficulty = zorluk_map.get(soru['zorluk'], 'MEDIUM')
                await conn.execute("""
                    INSERT INTO questions (
                        id, question_text, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, exam_type, subject_area, topic, subtopic, difficulty,
                        irt_discrimination, irt_difficulty, irt_guessing, aktif
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, true)
                """,
                    str(uuid.uuid4()), soru['metin'], secenekler.get('A', ''), secenekler.get('B', ''), 
                    secenekler.get('C', ''), secenekler.get('D', ''), secenekler.get('E', ''),
                    soru['dogru_cevap'], soru['sinav_tipi'], subject_area, soru['konu'], soru['alt_konu'],
                    difficulty, soru['irt_discrimination'], soru['irt_difficulty'], soru['irt_guessing']
                )
                inserted += 1
            except Exception as e:
                logger.error(f"Error: {e}")
        logger.info(f"Copied {inserted}/{len(sorular)}")
        count = await conn.fetchval("SELECT COUNT(*) FROM questions")
        logger.info(f"Total: {count}")
        await conn.close()
        return inserted
    except Exception as e:
        logger.error(f"Error: {e}")
        return 0

if __name__ == "__main__":
    count = asyncio.run(copy_questions())
    print(f"{count} questions copied successfully!")
