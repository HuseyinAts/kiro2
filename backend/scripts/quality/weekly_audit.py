#!/usr/bin/env python3
"""
Faz 2.1 + Faz 2.6 — Haftalık 30 random sample audit harness.

Post-Faz 5+6 pool kompozisyonu değişti (bronze 84,905 → 197, auto_judged_high
0 → 81,776). ELIGIBLE pool artık 'v_safe_for_beta' view (student'ın
gördüğü Gold pool) + ayrıca 'rejected' pool false-negative kontrolü için.

USAGE:
  # Default: Gold pool (v_safe_for_beta) — baseline tracking
  python -m backend.scripts.quality.weekly_audit

  # Reject pool — false-negative kontrolü (Faz 5+6 filter audit)
  python -m backend.scripts.quality.weekly_audit --pool reject

  # Sadece Edebiyat Sokagi manual queue
  python -m backend.scripts.quality.weekly_audit --pool manual_queue

SCOPE (her hafta):
  - 30 random sample (deterministic seed=ISO_year+week+pool)
  - Output: backend/_pilots/<YYYYMMDD>_weekly_<pool>_RAW.tsv
  - Auto-chain: scoring_template --prepare → SCORING.tsv

CHAIN:
  weekly_audit → RAW.tsv → scoring_template --prepare → SCORING.tsv
  → Hüseyin doldurur → drift_dashboard → ma_tracker
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
SAMPLE_N = 30


# Pool tanımları — Faz 5+6 alternative sonrası composition
POOLS = {
    "gold": {
        "label": "v_safe_for_beta (Gold pool — student sees)",
        "source": "v_safe_for_beta",
        "where": "1=1",
    },
    "reject": {
        "label": "rejected (false-negative check)",
        "source": "question_bank",
        "where": "is_active = TRUE AND quality_review_status = 'rejected'",
    },
    "manual_queue": {
        "label": "Edebiyat Sokagi manual queue (bronze_clean)",
        "source": "question_bank",
        "where": ("is_active = TRUE AND quality_review_status = 'bronze_clean'"),
    },
}

COLUMNS = [
    "id",
    "subject_area",
    "source_book",
    "source_page",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
    "correct_answer",
    "question_image_url",
    "match_tier",
    "quality_review_status",
]


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def main() -> int:
    from sqlalchemy import text

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--pool",
        choices=sorted(POOLS.keys()),
        default="gold",
        help="Audit pool seçimi (default: gold)",
    )
    args = ap.parse_args()
    pool = POOLS[args.pool]

    today = date.today()
    iso_year, iso_week, _ = today.isocalendar()
    seed = f"weekly_{iso_year}W{iso_week:02d}_{args.pool}"

    eng = get_engine()

    # Pre-state: pool size + composition
    with eng.connect() as c:
        pool_size = c.execute(
            text(f"SELECT COUNT(*) FROM {pool['source']} WHERE {pool['where']}")
        ).scalar()

    if pool_size == 0:
        sys.exit(f"[error] Pool '{args.pool}' boş ({pool['label']})")

    if pool_size < SAMPLE_N:
        print(
            f"[warn] Pool '{args.pool}' size={pool_size} < {SAMPLE_N} — "
            f"tüm satırlar dahil edilecek"
        )

    sql = f"""
        SELECT
            CAST(id AS text) AS id,
            subject_area,
            source_book,
            source_page,
            question_text,
            option_a, option_b, option_c, option_d, option_e,
            correct_answer,
            question_image_url,
            pipeline_metadata::jsonb ->> 'match_tier' AS match_tier,
            quality_review_status
        FROM {pool["source"]}
        WHERE {pool["where"]}
        ORDER BY md5(CAST(id AS text) || :seed)
        LIMIT :n
    """
    with eng.connect() as c:
        result = c.execute(text(sql), {"seed": seed, "n": SAMPLE_N}).fetchall()
    rows = [dict(r._mapping) for r in result]

    if not rows:
        sys.exit(f"[error] Hiç sample alınamadı (pool '{args.pool}' filtresi?)")

    out_path = PILOTS_DIR / f"{today.strftime('%Y%m%d')}_weekly_{args.pool}_RAW.tsv"
    PILOTS_DIR.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            cleaned = {
                k: (str(row.get(k) or "").replace("\t", " ").replace("\r", " "))
                for k in COLUMNS
            }
            writer.writerow(cleaned)

    print(f"[pool] {args.pool} — {pool['label']}")
    print(f"[pool-size] {pool_size:,} eligible satır")
    print(f"[sampled] {len(rows)} satır")
    print(f"[seed] {seed}")
    print(f"[output] {out_path}")

    # Auto-prepare SCORING.tsv
    print("\n[chain] scoring_template --prepare çağırılıyor...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.scripts.quality.scoring_template",
            "--prepare",
            str(out_path),
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"[warn] prepare başarısız: {result.stderr}", flush=True)

    scoring_path = out_path.with_name(out_path.stem + "_SCORING.tsv")
    print(f"\n[next] Hüseyin scoring: {scoring_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
