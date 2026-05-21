#!/usr/bin/env python3
"""
Faz 2.1 Audit Harness — Weekly 30 random sample quality drift monitoring.

PURPOSE:
  Quality pool plan v1'in haftalık audit aracı. Pipeline-fix sprintleri
  (Tier C-I) sonrası DB kalitesinin zaman içinde nasıl evrildiğini izler.

SCOPE:
  - 30 random sample seç (stratified: subject + image presence)
  - DB'den fetch + RAW TSV
  - Hüseyin scoring template (PASS/FAIL/UNCLEAR) için hazır format
  - Faz 2.3 drift dashboard input

USAGE:
  python backend/scripts/audit_harness.py                        # 30 sample, current week
  python backend/scripts/audit_harness.py --sample-size 50       # custom size
  python backend/scripts/audit_harness.py --seed 42              # reproducible
  python backend/scripts/audit_harness.py --stratify subject     # subject-balanced
  python backend/scripts/audit_harness.py --week 2026-W20        # historical re-run
  python backend/scripts/audit_harness.py --pool bronze_clean    # filter by status

OUTPUT:
  docs/audits/weekly/{YYYY}-W{WW}_audit_RAW.tsv     # scoring template
  docs/audits/weekly/{YYYY}-W{WW}_audit_META.json   # run metadata
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUDIT_DIR = PROJECT_ROOT / "docs" / "audits" / "weekly"
DEFAULT_SAMPLE_SIZE = 30
DEFAULT_STATUS_POOL = "unverified"  # Bronze proxy (pre Faz 1.6)


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def current_week_label() -> str:
    """ISO week label, e.g. '2026-W20'."""
    now = datetime.now()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def fetch_pool_size(engine, status_pool: str) -> int:
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE is_active = TRUE AND quality_review_status = :s"
            ),
            {"s": status_pool},
        )
        return result.scalar()


def fetch_random_sample(
    engine, status_pool: str, sample_size: int, seed: int, stratify: str | None
) -> list[dict]:
    """
    Random sample with optional stratification.

    Stratify="subject": equal sample per subject_area (rounds down if uneven).
    Stratify=None: pure random over status pool.
    """
    from sqlalchemy import text

    with engine.connect() as conn:
        if stratify == "subject":
            # 6 subjects × ~5 = 30
            subjects = conn.execute(
                text(
                    "SELECT DISTINCT subject_area FROM question_bank "
                    "WHERE is_active = TRUE AND quality_review_status = :s "
                    "AND subject_area IS NOT NULL"
                ),
                {"s": status_pool},
            ).fetchall()
            per_subject = max(1, sample_size // len(subjects))
            rows = []
            for (subj,) in subjects:
                r = conn.execute(
                    text(
                        """
                        SELECT id::text, question_text, option_a, option_b,
                               option_c, option_d, option_e, correct_answer,
                               question_image_url, subject_area, exam_type,
                               source_book
                        FROM question_bank
                        WHERE is_active = TRUE
                          AND quality_review_status = :s
                          AND subject_area = :subj
                        ORDER BY md5(id::text || :seed)
                        LIMIT :n
                        """
                    ),
                    {
                        "s": status_pool,
                        "subj": subj,
                        "seed": str(seed),
                        "n": per_subject,
                    },
                ).fetchall()
                rows.extend(r)
            return [
                {
                    "id": r[0],
                    "question_text": r[1],
                    "options": [r[2], r[3], r[4], r[5], r[6]],
                    "correct_answer": r[7],
                    "image_url": r[8],
                    "subject_area": r[9],
                    "exam_type": r[10],
                    "source_book": r[11],
                }
                for r in rows[:sample_size]
            ]
        r = conn.execute(
            text(
                """
                    SELECT id::text, question_text, option_a, option_b,
                           option_c, option_d, option_e, correct_answer,
                           question_image_url, subject_area, exam_type,
                           source_book
                    FROM question_bank
                    WHERE is_active = TRUE
                      AND quality_review_status = :s
                    ORDER BY md5(id::text || :seed)
                    LIMIT :n
                    """
            ),
            {"s": status_pool, "seed": str(seed), "n": sample_size},
        ).fetchall()
        return [
            {
                "id": x[0],
                "question_text": x[1],
                "options": [x[2], x[3], x[4], x[5], x[6]],
                "correct_answer": x[7],
                "image_url": x[8],
                "subject_area": x[9],
                "exam_type": x[10],
                "source_book": x[11],
            }
            for x in r
        ]


def write_raw_tsv(rows: list[dict], out_path: Path) -> None:
    """Hüseyin scoring template. PASS/FAIL/UNCLEAR + reason kolonu boş."""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(
            "id\tsubject\texam\tbook\timage_url\tq_text_preview\t"
            "opts_preview\tcorrect\tSCORE\tREASON\n"
        )
        for r in rows:
            q = (r["question_text"] or "")[:200].replace("\t", " ").replace("\n", " ")
            opts = " | ".join(
                f"{lt}={(o or '')[:30].replace(chr(9), ' ')}"
                for lt, o in zip("ABCDE", r["options"])
            )
            f.write(
                f"{r['id']}\t{r['subject_area'] or '-'}\t{r['exam_type'] or '-'}\t"
                f"{(r['source_book'] or '-')[:40]}\t{r['image_url'] or '-'}\t"
                f"{q}\t{opts}\t{r['correct_answer'] or '-'}\t\t\n"
            )


def write_meta(meta: dict, out_path: Path) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    ap.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Reproducible seed. Default: epoch seconds (varies).",
    )
    ap.add_argument("--stratify", choices=["subject", "none"], default="none")
    ap.add_argument(
        "--week", type=str, default=None, help="ISO week label. Default: current week."
    )
    ap.add_argument(
        "--pool",
        type=str,
        default=DEFAULT_STATUS_POOL,
        help="quality_review_status filter (Bronze proxy)",
    )
    ap.add_argument("--output-dir", type=Path, default=AUDIT_DIR)
    args = ap.parse_args()

    week = args.week or current_week_label()
    seed = args.seed if args.seed is not None else int(datetime.now().timestamp())
    stratify = None if args.stratify == "none" else args.stratify

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / f"{week}_audit_RAW.tsv"
    meta_path = args.output_dir / f"{week}_audit_META.json"

    if raw_path.exists():
        print(
            f"[skip] {raw_path.name} already exists. Use --week different label to re-run."
        )
        return 1

    engine = get_engine()
    pool_size = fetch_pool_size(engine, args.pool)
    print(f"[pool] {args.pool} size = {pool_size}")

    if pool_size < args.sample_size:
        print(f"[error] Pool too small ({pool_size} < {args.sample_size})")
        return 1

    print(
        f"[sample] selecting {args.sample_size} (seed={seed}, stratify={stratify})..."
    )
    rows = fetch_random_sample(engine, args.pool, args.sample_size, seed, stratify)
    print(f"[sample] {len(rows)} satır alındı")

    # Distribution
    by_subj = defaultdict(int)
    by_exam = defaultdict(int)
    with_img = 0
    for r in rows:
        by_subj[r["subject_area"] or "NULL"] += 1
        by_exam[r["exam_type"] or "NULL"] += 1
        if r["image_url"]:
            with_img += 1

    write_raw_tsv(rows, raw_path)
    meta = {
        "week": week,
        "seed": seed,
        "stratify": stratify,
        "pool": args.pool,
        "pool_size_at_run": pool_size,
        "sample_size": len(rows),
        "run_date": datetime.now().isoformat(),
        "distribution": {
            "by_subject": dict(by_subj),
            "by_exam_type": dict(by_exam),
            "with_image": with_img,
            "no_image": len(rows) - with_img,
        },
    }
    write_meta(meta, meta_path)

    print("\n[output]")
    print(f"  RAW : {raw_path}")
    print(f"  META: {meta_path}")
    print("\n[distribution]")
    print(f"  with_image: {with_img}/{len(rows)}")
    print(f"  subjects:   {dict(by_subj)}")
    print(f"  exam types: {dict(by_exam)}")

    print("\n[next]")
    print("  Hüseyin scoring template hazır. SCORE kolonuna PASS/FAIL/UNCLEAR yaz.")
    print("  Faz 2.3 (drift dashboard) bu TSV'leri tarayıp pass-rate timeline çizecek.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
