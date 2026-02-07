#!/usr/bin/env python3
"""
Copy questions from sorular table to questions table
"""
import asyncio
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def copy_questions():
    """Copy data from sorular to questions with column mapping"""
    conn = await asyncpg.connect(
        host="localhost",
        port=5434,
        user="postgres",
        password="1470",
        database="turkiye_sinav_db"
    )

    try:
        logger.info("Connected to database")

        # Get all questions from sorular
        sorular = await conn.fetch("""
            SELECT
                metin,
                secenekler,
                dogru_cevap,
                sinav_tipi,
                konu,
                alt_konu,
                zorluk,
                irt_discrimination,
                irt_difficulty,
                irt_guessing
            FROM sorular
            WHERE aktif = true
        """)

        logger.info(f"Found {len(sorular)} questions in sorular table")

        # Insert into questions table
        inserted = 0
        for soru in sorular:
            try:
                await conn.execute("""
                    INSERT INTO questions (
                        stem,
                        options,
                        correct_answer,
                        exam_type,
                        subject,
                        topic,
                        subtopic,
                        difficulty,
                        irt_discrimination,
                        irt_difficulty,
                        irt_guessing,
                        status
                    ) VALUES (
                        $1, $2::jsonb, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'active'
                    )
                """,
                    soru['metin'],
                    soru['secenekler'],
                    soru['dogru_cevap'],
                    soru['sinav_tipi'],
                    soru['konu'],
                    soru['konu'],  # Use konu for topic as well
                    soru['alt_konu'],
                    soru['zorluk'],
                    soru['irt_discrimination'],
                    soru['irt_difficulty'],
                    soru['irt_guessing']
                )
                inserted += 1
            except Exception as e:
                logger.error(f"Error inserting question: {e}")

        logger.info(f"✅ Successfully copied {inserted}/{len(sorular)} questions")

        # Verify
        count = await conn.fetchval("SELECT COUNT(*) FROM questions")
        logger.info(f"Total questions in questions table: {count}")

        await conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(copy_questions())
    if success:
        print("\n✅ Questions copied successfully!")
    else:
        print("\n❌ Failed to copy questions!")
