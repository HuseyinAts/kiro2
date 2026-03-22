"""
P8: IRT Parameter Bootstrap Pipeline
Bootstrap IRT 3PL parameters for questions without real calibration data.
Maps difficulty_level to initial a/b/c values; idempotent (skips calibrated questions).

Mapping (difficulty_level → a, b, c):
  very_easy -> a=0.8, b=-2.0, c=0.20
  easy      -> a=1.0, b=-1.0, c=0.20
  medium    -> a=1.2, b= 0.0, c=0.20
  hard      -> a=1.0, b= 1.0, c=0.15
  very_hard -> a=0.8, b= 2.0, c=0.10

Idempotent guard: only updates rows where is_calibrated=false OR calibration_sample_size=0.
Use --force to overwrite real calibration data (destructive — use with care).

Usage:
  cd backend
  python scripts/bootstrap_irt_params.py --dry-run   # Preview distribution
  python scripts/bootstrap_irt_params.py              # Apply bootstrap
  python scripts/bootstrap_irt_params.py --force      # Overwrite all (incl. calibrated)
"""

import argparse
import asyncio
import sys

from sqlalchemy import text

sys.path.insert(0, ".")

PARAMS = {
    "very_easy": {"a": 0.8, "b": -2.0, "c": 0.20},
    "easy": {"a": 1.0, "b": -1.0, "c": 0.20},
    "medium": {"a": 1.2, "b": 0.0, "c": 0.20},
    "hard": {"a": 1.0, "b": 1.0, "c": 0.15},
    "very_hard": {"a": 0.8, "b": 2.0, "c": 0.10},
}


async def main(dry_run: bool = True, force: bool = False) -> None:
    from core.database import get_db_session_context

    where_clause = (
        "WHERE is_active = true"
        if force
        else "WHERE is_active = true AND (is_calibrated = false OR calibration_sample_size = 0)"
    )

    preview = text(f"""
        SELECT
            difficulty_level,
            COUNT(*) AS cnt,
            COUNT(NULLIF(is_calibrated, false)) AS already_calibrated
        FROM question_bank
        {where_clause}
        GROUP BY difficulty_level
        ORDER BY difficulty_level
    """)

    update_query = text(f"""
        UPDATE question_bank
        SET
            irt_discrimination = CASE difficulty_level
                WHEN 'very_easy' THEN 0.8
                WHEN 'easy'      THEN 1.0
                WHEN 'medium'    THEN 1.2
                WHEN 'hard'      THEN 1.0
                WHEN 'very_hard' THEN 0.8
                ELSE 1.0 END,
            irt_difficulty = CASE difficulty_level
                WHEN 'very_easy' THEN -2.0
                WHEN 'easy'      THEN -1.0
                WHEN 'medium'    THEN  0.0
                WHEN 'hard'      THEN  1.0
                WHEN 'very_hard' THEN  2.0
                ELSE 0.0 END,
            irt_guessing = CASE difficulty_level
                WHEN 'very_easy' THEN 0.20
                WHEN 'easy'      THEN 0.20
                WHEN 'medium'    THEN 0.20
                WHEN 'hard'      THEN 0.15
                WHEN 'very_hard' THEN 0.10
                ELSE 0.20 END,
            irt_upper_asymptote = 1.0,
            is_calibrated = false,
            calibration_sample_size = 0
        {where_clause}
    """)

    async with get_db_session_context() as db:
        result = await db.execute(preview)
        rows = result.all()

        scope = (
            "ALL active"
            if force
            else "bootstrap targets (is_calibrated=false or sample=0)"
        )
        print(f"Distribution ({scope}):")
        total = 0
        for row in rows:
            level = row[0] or "NULL"
            cnt = row[1]
            calibrated = row[2]
            params = PARAMS.get(level, {})
            param_str = (
                f"a={params['a']}, b={params['b']:5.1f}, c={params['c']:.2f}"
                if params
                else "→ default (a=1.0, b=0.0, c=0.20)"
            )
            print(
                f"  {level:>10}: {cnt:>6,} questions  ({param_str})"
                + (f"  [{calibrated} already calibrated]" if calibrated else "")
            )
            total += cnt
        print(f"  {'TOTAL':>10}: {total:>6,} questions")

        if force:
            print("\n[--force] Will overwrite calibrated questions too!")

        if dry_run:
            print("\n[DRY RUN] No changes made. Run without --dry-run to apply.")
            return

        result = await db.execute(update_query)
        await db.commit()
        print(f"\nUpdated {result.rowcount:,} questions with bootstrap IRT parameters.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bootstrap IRT 3PL parameters from difficulty_level"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview only, no changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite even calibrated questions (destructive)",
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, force=args.force))
