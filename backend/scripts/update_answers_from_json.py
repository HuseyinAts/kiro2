"""
Update Missing Answers from Extracted JSONs

Problem: Questions exist in database but without answers.
Solution: Update correct_answer field from newly extracted JSONs.
"""

import asyncio
import json
import os
from pathlib import Path

import asyncpg


async def update_answers():
    """Update missing answers from extracted JSONs"""

    print("=" * 80)
    print("UPDATING MISSING ANSWERS FROM EXTRACTED JSONS")
    print("=" * 80)
    print()

    # Connect
    print("Connecting to database...")
    conn = await asyncpg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5434")),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ["PGPASSWORD"],
        database=os.environ.get("PGDATABASE", "kiro2"),
    )
    print("[OK] Connected!")
    print()

    # Get all extracted JSONs
    json_dir = Path("osym_extracted")
    json_files = list(json_dir.glob("*.json"))

    print(f"Found {len(json_files)} JSON files")
    print()

    total_questions = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for json_file in json_files:
        print(f"Processing: {json_file.name}")

        try:
            data = json.load(open(json_file, encoding="utf-8"))
            questions = data.get("questions", [])

            for q in questions:
                total_questions += 1

                # Skip if no answer in JSON
                if not q.get("correct_answer"):
                    continue

                # Check if question exists without answer
                check_query = """
                    SELECT question_id, correct_answer FROM questions
                    WHERE stem = $1 AND year = $2 AND source = 'ÖSYM'
                    LIMIT 1
                """

                result = await conn.fetchrow(check_query, q["stem"], q.get("year"))

                if result:
                    question_id = result["question_id"]
                    existing_answer = result["correct_answer"]

                    # Update if no answer exists
                    if not existing_answer and q.get("correct_answer"):
                        update_query = """
                            UPDATE questions
                            SET correct_answer = $1
                            WHERE question_id = $2
                        """

                        await conn.execute(
                            update_query, q["correct_answer"], question_id
                        )
                        updated_count += 1

                        if updated_count <= 5:  # Show first 5
                            print(
                                f"  [UPDATE] {q['subject']}: {q['stem'][:50]}... -> {q['correct_answer']}"
                            )
                    else:
                        skipped_count += 1
                else:
                    skipped_count += 1

        except Exception as e:
            print(f"  [ERROR] {e}")
            error_count += 1

        if updated_count > 0 or error_count > 0:
            print(
                f"  Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}"
            )
            print()

    await conn.close()

    print("=" * 80)
    print("UPDATE COMPLETE!")
    print("=" * 80)
    print(f"Total questions processed: {total_questions:,}")
    print(f"Answers updated: {updated_count:,}")
    print(f"Skipped (already has answer): {skipped_count:,}")
    print(f"Errors: {error_count:,}")
    print()

    if updated_count > 0:
        print("[SUCCESS] Database updated with new answers!")
        print("Run check_import_stats.py to verify coverage improvement.")
    else:
        print("[INFO] No updates needed - all questions already have answers.")


if __name__ == "__main__":
    asyncio.run(update_answers())
