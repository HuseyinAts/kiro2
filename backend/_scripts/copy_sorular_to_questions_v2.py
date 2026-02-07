#!/usr/bin/env python3
import asyncio
import asyncpg
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def copy_questions():
    conn = await asyncpg.connect(
        host="localhost",
        port=5434,
        user="postgres",
        password="1470",
        database="turkiye_sinav_db"
    )

    try:
        logger.info("Connected to database")

        sorular = await conn.fetch("""
            SELECT metin, secenekler, dogru_cevap, sinav_tipi, konu, alt_konu, zorluk,
                   irt_discrimination, irt_difficulty, irt_guessing
            FROM sorular WHERE aktif = true
        """)

        logger.info(f"Found {len(sorular)} questions in sorular table")

        inserted = 0
        for soru in sorular:
            try:
                # Parse secenekler JSON
                if isinstance(soru['secenekler'], str):
                    secenekler = json.loads(soru['secenekler'])
                else:
                    secenekler = soru['secenekler']

                # Map konu to subject_area enum
                konu = soru['konu'] or 'Test'
                konu_first = konu.split(' - ')[0].split('-')[0].strip().upper()
                
                subject_map = {
                    'MATEMATIK': 'MATEMATIK',
                    'TÜRKÇE': 'TURKCE',
                    'TURKCE': 'TURKCE',
                    'FEN': 'FEN',
                    'FIZIK': 'FIZIK',
                    'KIMYA': 'KIMYA',
                    'BIYOLOJI': 'BIYOLOJI',
                    'TEST': 'MATEMATIK',  # Default for test questions
                    'INGILIZCE': 'INGILIZCE',
                    'İNGILIZCE': 'INGILIZCE'
                }
                subject_area = subject_map.get(konu_first, 'MATEMATIK')

                # Map zorluk to difficulty enum
                zorluk_map = {
                    'kolay': 'easy',
                    'orta': 'medium',
                    'zor': 'hard'
                }
                difficulty = zorluk_map.get(soru['zorluk'], 'medium')

                await conn.execute("""
                    INSERT INTO questions (
                        question_text, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, exam_type, subject_area, topic, subtopic, difficulty,
                        irt_discrimination, irt_difficulty, irt_guessing, aktif
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, true
                    )
                """,
                    soru['metin'],
                    secenekler.get('A', ''),
                    secenekler.get('B', ''),
                    secenekler.get('C', ''),
                    secenekler.get('D', ''),
                    secenekler.get('E', ''),
                    soru['dogru_cevap'],
                    soru['sinav_tipi'],
                    subject_area,
                    soru['konu'],
                    soru['alt_konu'],
                    difficulty,
                    soru['irt_discrimination'],
                    soru['irt_difficulty'],
                    soru['irt_guessing']
                )
                inserted += 1
                if inserted % 50 == 0:
                    logger.info(f"Progress: {inserted}/{len(sorular)}")
            except Exception as e:
                logger.error(f"Error inserting question: {e}")

        logger.info(f"Successfully copied {inserted}/{len(sorular)} questions")

        count = await conn.fetchval("SELECT COUNT(*) FROM questions")
        logger.info(f"Total questions in questions table: {count}")

        await conn.close()
        return inserted

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    count = asyncio.run(copy_questions())
    print(f"\n{count} questions copied successfully!")
