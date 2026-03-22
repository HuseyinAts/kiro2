"""
P4: quality_score Pipeline
Map pipeline_metadata->>'confidence_level' to quality_score for questions with score=0.
Bkz. fix_explanation_language.py (P6) — explanation dil düzeltmesi için ayrı script.

Mapping:
  very_high -> 90
  high      -> 80
  medium    -> 50
  low       -> 20
  NULL   -> 0 (unchanged)

Usage:
  cd backend
  python scripts/update_quality_scores.py --dry-run   # Preview
  python scripts/update_quality_scores.py              # Apply
"""

import argparse
import asyncio
import sys

from sqlalchemy import text

sys.path.insert(0, ".")


async def main(dry_run: bool = True):
    from core.database import get_db_session_context

    query = text("""
        UPDATE question_bank
        SET quality_score = CASE
            WHEN pipeline_metadata->>'confidence_level' = 'very_high' THEN 90
            WHEN pipeline_metadata->>'confidence_level' = 'high' THEN 80
            WHEN pipeline_metadata->>'confidence_level' = 'medium' THEN 50
            WHEN pipeline_metadata->>'confidence_level' = 'low' THEN 20
            ELSE 0
        END
        WHERE quality_score = 0
          AND is_active = true
          AND pipeline_metadata->>'confidence_level' IS NOT NULL
    """)

    preview = text("""
        SELECT
            pipeline_metadata->>'confidence_level' AS conf,
            COUNT(*) AS cnt
        FROM question_bank
        WHERE quality_score = 0 AND is_active = true
        GROUP BY pipeline_metadata->>'confidence_level'
        ORDER BY cnt DESC
    """)

    async with get_db_session_context() as db:
        result = await db.execute(preview)
        rows = result.all()
        print("Current distribution (quality_score=0, is_active=true):")
        for row in rows:
            print(f"  {row[0] or 'NULL':>10}: {row[1]:,} questions")

        if dry_run:
            print("\n[DRY RUN] No changes made. Run without --dry-run to apply.")
            return

        result = await db.execute(query)
        await db.commit()
        print(f"\nUpdated {result.rowcount:,} questions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update quality_score from pipeline_metadata"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview only, no changes"
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
