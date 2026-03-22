"""
P6: Explanation Extraction Pipeline
Extract best_answer metadata into explanation field for questions lacking explanations.

Format: "Doğru cevap: {answer} (Güven: %{confidence}, Kaynak: {method})"

Usage:
  cd backend
  python scripts/extract_explanations.py --dry-run   # Preview
  python scripts/extract_explanations.py              # Apply
"""

import argparse
import asyncio
import sys

from sqlalchemy import text

sys.path.insert(0, ".")

METHOD_LABELS = {
    "bayes_1of1_orig": "Kitap cevap anahtarı",
    "bayes_2of2_orig": "Kitap cevap anahtarı (çapraz doğrulanmış)",
    "bayes_3of4_orig": "Kitap cevap anahtarı (3/4 doğrulama)",
    "bayes_4of4_orig": "Kitap cevap anahtarı (4/4 tam doğrulama)",
    "ai_crop_solve": "AI çözüm analizi",
    "ai_crossval": "AI çapraz doğrulama",
}


async def main(dry_run: bool = True):
    from core.database import get_db_session_context

    preview = text("""
        SELECT
            pipeline_metadata->>'best_method' AS method,
            COUNT(*) AS cnt
        FROM question_bank
        WHERE is_active = true
          AND (explanation IS NULL OR explanation = '')
          AND pipeline_metadata->>'best_answer' IS NOT NULL
        GROUP BY 1
        ORDER BY 2 DESC
    """)

    update_query = text("""
        UPDATE question_bank
        SET explanation = CONCAT(
            'Doğru cevap: ', pipeline_metadata->>'best_answer',
            ' (Güven: %', ROUND((pipeline_metadata->>'best_confidence')::numeric * 100),
            ', Kaynak: ', pipeline_metadata->>'best_method', ')'
        )
        WHERE is_active = true
          AND (explanation IS NULL OR explanation = '')
          AND pipeline_metadata->>'best_answer' IS NOT NULL
          AND id IN (
            SELECT id FROM question_bank
            WHERE is_active = true
              AND (explanation IS NULL OR explanation = '')
              AND pipeline_metadata->>'best_answer' IS NOT NULL
            LIMIT 10000
          )
    """)

    count_query = text("""
        SELECT COUNT(*) FROM question_bank
        WHERE is_active = true
          AND (explanation IS NULL OR explanation = '')
          AND pipeline_metadata->>'best_answer' IS NOT NULL
    """)

    async with get_db_session_context() as db:
        result = await db.execute(preview)
        rows = result.all()
        print("Explanation missing, best_answer available:")
        for row in rows:
            label = METHOD_LABELS.get(row[0], row[0])
            print(f"  {label:>45}: {row[1]:,}")

        remaining_result = await db.execute(count_query)
        total = remaining_result.scalar()
        print(f"\nTotal to update: {total:,}")

        if dry_run:
            print("\n[DRY RUN] No changes made.")
            return

        updated_total = 0
        while True:
            remaining_result = await db.execute(count_query)
            remaining = remaining_result.scalar()
            if remaining == 0:
                break
            result = await db.execute(update_query)
            await db.commit()
            updated_total += result.rowcount
            print(
                f"  Batch: {result.rowcount:,} updated ({remaining - result.rowcount:,} remaining)"
            )

        print(f"\nTotal updated: {updated_total:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract explanations from pipeline_metadata"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
