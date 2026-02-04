"""
Test Import Script - Debug and Fix Connection Issue
"""
import asyncio
import asyncpg
import json
from pathlib import Path


async def test_import():
    """Test database import with proper connection handling"""

    # Direct connection test
    print("=" * 80)
    print("TESTING DATABASE IMPORT")
    print("=" * 80)
    print()

    # Connect directly
    print("Step 1: Connecting to database...")
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="changeme_strong_password_here",
            database="turkiye_sinav_db",
        )
        print("[OK] Connected!")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return

    # Load test JSON
    print("\nStep 2: Loading test JSON...")
    json_file = Path("osym_extracted/2025tyt_extracted.json")

    if not json_file.exists():
        print(f"[ERROR] File not found: {json_file}")
        await conn.close()
        return

    data = json.load(open(json_file, encoding="utf-8"))
    questions = data["questions"]

    print(f"[OK] Loaded {len(questions)} questions")
    print(f"     With answers: {sum(1 for q in questions if q.get('correct_answer'))}")

    # Test import first question
    print("\nStep 3: Testing import (first question)...")
    q = questions[0]

    try:
        # Check if exists
        check_query = """
            SELECT question_id FROM questions
            WHERE stem = $1 AND year = $2 AND source = 'ÖSYM'
            LIMIT 1
        """
        existing = await conn.fetchval(check_query, q["stem"], q.get("year"))

        if existing:
            print(f"[SKIP] Question already exists (ID: {existing})")
        else:
            # Insert
            insert_query = """
                INSERT INTO questions (
                    subject, topic, difficulty, exam_type, stem,
                    options, correct_answer, source, year, status, quality_score
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING question_id
            """

            question_id = await conn.fetchval(
                insert_query,
                q["subject"],
                q["subject"],  # topic = subject for now
                "orta",  # difficulty
                q["exam_type"],
                q["stem"],
                json.dumps(q["options"]),
                q.get("correct_answer"),
                "ÖSYM",
                q.get("year"),
                "active",
                10.0,
            )

            print(f"[OK] Imported! Question ID: {question_id}")

    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback

        traceback.print_exc()

    await conn.close()
    print("\n[OK] Test complete!")


if __name__ == "__main__":
    asyncio.run(test_import())
