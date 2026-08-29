"""
Question Bank IRT Parameter Calibration Pipeline

Executes empirical multi-feature IRT parameter derivation across all questions in question_bank,
replacing dummy/default IRT values with continuous 4PL parameters (a, b, c, d).

Usage:
    python backend/scripts/quality/calibrate_question_bank_irt.py            # dry-run report
    python backend/scripts/quality/calibrate_question_bank_irt.py --apply    # apply updates
"""

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from services.empirical_irt_calibrator import EmpiricalIRTCalibrator

DSN = os.environ.get(
    "KIRO2_DSN",
    "host=localhost port=5434 dbname=kiro2 user=postgres",
)
BATCH_SIZE = 2000


def calculate_irt_based_difficulty_str(b: float) -> str:
    if b < -1.5:
        return "very_easy"
    if b < -0.5:
        return "easy"
    if b <= 0.5:
        return "medium"
    if b <= 1.5:
        return "hard"
    return "very_hard"


def fetch_questions(cur):
    cur.execute(
        """
        SELECT id::text, difficulty_level::text, bloom_level, bloom_category,
               question_text, option_e, irt_difficulty, irt_discrimination, irt_guessing, irt_upper_asymptote
        FROM question_bank
        WHERE is_active = TRUE
        """
    )
    return cur.fetchall()


def dry_run(rows):
    print(
        f"\n=== IRT EMPIRICAL CALIBRATION DRY-RUN — Total Questions: {len(rows):,} ==="
    )

    a_vals, b_vals, c_vals, d_vals = [], [], [], []
    b_bands: Counter[str] = Counter()

    for row in rows:
        (
            qid,
            diff,
            bloom_lvl,
            bloom_cat,
            qtext,
            opt_e,
            _old_b,
            _old_a,
            _old_c,
            _old_d,
        ) = row
        params = EmpiricalIRTCalibrator.calibrate_item(
            {
                "id": qid,
                "difficulty_level": diff,
                "bloom_level": bloom_lvl,
                "bloom_category": bloom_cat,
                "question_text": qtext,
                "option_e": opt_e,
            }
        )
        a_vals.append(params["irt_a"])
        b_vals.append(params["irt_b"])
        c_vals.append(params["irt_c"])
        d_vals.append(params["irt_d"])

        band_label = calculate_irt_based_difficulty_str(params["irt_b"])
        b_bands[band_label] += 1

    b_mean = sum(b_vals) / len(b_vals)
    b_std = (sum((x - b_mean) ** 2 for x in b_vals) / len(b_vals)) ** 0.5

    a_mean = sum(a_vals) / len(a_vals)
    c_mean = sum(c_vals) / len(c_vals)

    print(f"Total Unique b values: {len(set(b_vals)):,} / {len(b_vals):,}")
    print(
        f"Difficulty (b): mean={b_mean:.3f}, std={b_std:.3f}, min={min(b_vals):.3f}, max={max(b_vals):.3f}"
    )
    print(
        f"Discrimination (a): mean={a_mean:.3f}, min={min(a_vals):.3f}, max={max(a_vals):.3f}"
    )
    print(
        f"Guessing (c): mean={c_mean:.3f}, min={min(c_vals):.3f}, max={max(c_vals):.3f}"
    )
    print(f"Upper Asymptote (d): min={min(d_vals):.3f}, max={max(d_vals):.3f}")

    print("\nDifficulty Band Distribution:")
    for b_label in ["very_easy", "easy", "medium", "hard", "very_hard"]:
        cnt = b_bands.get(b_label, 0)
        pct = 100.0 * cnt / len(rows)
        print(f"  {b_label:12s}: {cnt:>8,} ({pct:5.1f}%)")

    print("\nSample 5 Calibrated Items:")
    for row in rows[:5]:
        qid, diff, bloom_lvl, bloom_cat, qtext, opt_e, old_b, old_a, _old_c, _old_d = (
            row
        )
        p = EmpiricalIRTCalibrator.calibrate_item(
            {
                "id": qid,
                "difficulty_level": diff,
                "bloom_level": bloom_lvl,
                "bloom_category": bloom_cat,
                "question_text": qtext,
                "option_e": opt_e,
            }
        )
        print(
            f"  ID: {qid[:8]} | Diff: {diff:9s} | Bloom: {bloom_lvl} | OLD (a={old_a}, b={old_b}) -> NEW (a={p['irt_a']}, b={p['irt_b']}, c={p['irt_c']}, d={p['irt_d']})"
        )

    print("\n(Dry-run completed. Run with --apply to commit to database.)")


def apply_calibration(conn, cur, rows):
    print(f"\n=== APPLYING IRT CALIBRATION — {len(rows):,} Questions ===")

    done = 0
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i : i + BATCH_SIZE]
        payload = []
        for row in chunk:
            (
                qid,
                diff,
                bloom_lvl,
                bloom_cat,
                qtext,
                opt_e,
                _old_b,
                _old_a,
                _old_c,
                _old_d,
            ) = row
            p = EmpiricalIRTCalibrator.calibrate_item(
                {
                    "id": qid,
                    "difficulty_level": diff,
                    "bloom_level": bloom_lvl,
                    "bloom_category": bloom_cat,
                    "question_text": qtext,
                    "option_e": opt_e,
                }
            )
            b_diff_str = calculate_irt_based_difficulty_str(p["irt_b"])
            payload.append(
                (
                    p["irt_discrimination"],
                    p["irt_difficulty"],
                    p["irt_guessing"],
                    p["irt_upper_asymptote"],
                    b_diff_str,
                    qid,
                )
            )

        cur.executemany(
            """
            UPDATE question_bank
            SET irt_discrimination = %s,
                irt_difficulty = %s,
                irt_guessing = %s,
                irt_upper_asymptote = %s,
                irt_based_difficulty = %s,
                is_calibrated = TRUE,
                last_difficulty_update = NOW()
            WHERE id = %s
            """,
            payload,
        )
        conn.commit()
        done += len(chunk)
        print(f"  Calibrated {done:,} / {len(rows):,} questions...", end="\r")

    print(
        f"\n[SUCCESS] Successfully calibrated {done:,} questions with non-dummy continuous IRT parameters!"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate IRT parameters for question_bank."
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply updates to database."
    )
    args = parser.parse_args()

    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    try:
        rows = fetch_questions(cur)
        if not rows:
            print("No questions found in question_bank.")
            return
        if args.apply:
            apply_calibration(conn, cur, rows)
        else:
            dry_run(rows)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    main()
