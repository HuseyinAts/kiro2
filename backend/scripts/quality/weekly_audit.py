#!/usr/bin/env python3
"""
Faz 2.1 — Haftalık 30 random sample audit harness (retroactive impl, Session 161d).

Plan v1 Faz 2.1: "weekly_audit.py — backend/scripts/quality/weekly_audit.py".
Memory'de completed işaretli ama dosya yoktu — manuel SQL'le yapılan one-shot
audit'leri (C1/C2/C3) bir araya getiren reusable version.

USAGE:
  # Manuel:
  python -m backend.scripts.quality.weekly_audit

  # Cron-like (Faz 2.5 Task Scheduler tetikler):
  # → 20260524_weekly_RAW.tsv üretir → scoring_template --prepare → SCORING.tsv

SCOPE (her hafta):
  - 30 random sample (deterministic seed=ISO_year+week)
  - Source: bronze_clean veya legacy_v3_unaudited (eligible review pool)
  - Output: backend/_pilots/<YYYYMMDD>_weekly_RAW.tsv

CHAIN:
  weekly_audit → RAW.tsv → scoring_template --prepare → SCORING.tsv
  → Hüseyin doldurur → drift_dashboard → ma_tracker
"""

from __future__ import annotations

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

# Eligible pool: pipeline-fix geçmiş veya legacy_v3 (audit/curation adayları)
ELIGIBLE_WHERE = """
    is_active = TRUE
    AND quality_review_status IN ('bronze_clean', 'legacy_v3_unaudited')
"""

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

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def main() -> int:
    from sqlalchemy import text

    today = date.today()
    iso_year, iso_week, _ = today.isocalendar()
    seed = f"weekly_{iso_year}W{iso_week:02d}"

    eng = get_engine()
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
        FROM question_bank
        WHERE {ELIGIBLE_WHERE}
        ORDER BY md5(CAST(id AS text) || :seed)
        LIMIT :n
    """
    with eng.connect() as c:
        result = c.execute(text(sql), {"seed": seed, "n": SAMPLE_N}).fetchall()
    rows = [dict(r._mapping) for r in result]

    if not rows:
        sys.exit("[error] Hiç sample alınamadı (pool boş?)")

    out_path = PILOTS_DIR / f"{today.strftime('%Y%m%d')}_weekly_RAW.tsv"
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

    print(f"[done] {len(rows)} sample → {out_path}")
    print(f"[seed] {seed} (ISO year+week)")

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

    print(
        f"\n[next] Hüseyin scoring: "
        f"{out_path.with_name(out_path.stem + '_SCORING.tsv')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
