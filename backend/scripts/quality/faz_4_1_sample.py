#!/usr/bin/env python3
"""
Faz 4.1 — 200 manuel curated set stratified sample (Session 161d).

Plan v1 Faz 4.1: judge calibration prereq, 4 strata × 50 sample = 200 total.

STRATA:
  exact          → match_tier='tier1_page_inline'         (pool 22,110)
  fuzzy          → match_tier='tier1b_position_page_inline' (pool 18,820)
  fallback       → match_tier='tier5_qindex_page_inline'   (pool   798)
  v3.5 residual  → quality_review_status='legacy_v3_unaudited' (pool 18,397)

ai_crop_solve (607) bilinçli dışarda — judge ayrı kalibre eder (Faz 5.8).

REPRODUCIBILITY: Random deterministic via md5(id || '<seed>') ORDER BY, seed='faz_4_1_v1'.

OUTPUT:
  backend/_pilots/20260516_faz_4_1_curated_set_RAW.tsv (200 satır + header)
  Kolonlar: id, strata, subject_area, source_book, source_page, question_text,
            option_a..e, correct_answer, has_diagram, question_image_url,
            match_tier, quality_review_status

NEXT STEP:
  python -m backend.scripts.quality.scoring_template --prepare <RAW>.tsv
  → Hüseyin doldurur (verdict/error_type/notes) → judge calibration ground truth.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
OUTPUT_TSV = PILOTS_DIR / "20260516_faz_4_1_curated_set_RAW.tsv"
SEED = "faz_4_1_v1"
SAMPLE_PER_STRATA = 50

STRATA_QUERIES = [
    (
        "exact",
        "pipeline_metadata::jsonb ->> 'match_tier' = 'tier1_page_inline'",
    ),
    (
        "fuzzy",
        "pipeline_metadata::jsonb ->> 'match_tier' = 'tier1b_position_page_inline'",
    ),
    (
        "fallback",
        "pipeline_metadata::jsonb ->> 'match_tier' = 'tier5_qindex_page_inline'",
    ),
    (
        "v3.5_residual",
        "quality_review_status = 'legacy_v3_unaudited'",
    ),
]

COLUMNS = [
    "id",
    "strata",
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


def main() -> int:
    from sqlalchemy import create_engine, text

    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    eng = create_engine(db_url)

    all_rows: list[dict] = []
    with eng.connect() as c:
        for strata_label, where_clause in STRATA_QUERIES:
            sql = f"""
                SELECT
                    CAST(id AS text) AS id,
                    subject_area,
                    source_book,
                    source_page,
                    question_text,
                    option_a,
                    option_b,
                    option_c,
                    option_d,
                    option_e,
                    correct_answer,
                    question_image_url,
                    pipeline_metadata::jsonb ->> 'match_tier' AS match_tier,
                    quality_review_status
                FROM question_bank
                WHERE is_active = TRUE
                  AND ({where_clause})
                ORDER BY md5(CAST(id AS text) || :seed)
                LIMIT :n
            """
            result = c.execute(
                text(sql), {"seed": SEED, "n": SAMPLE_PER_STRATA}
            ).fetchall()
            for r in result:
                row = dict(r._mapping)
                row["strata"] = strata_label
                all_rows.append(row)
            print(
                f"[strata] {strata_label:15s} sampled {len(result):3d} / target {SAMPLE_PER_STRATA}",
                flush=True,
            )

    if not all_rows:
        sys.exit("[error] Hiç sample alınamadı")

    PILOTS_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_TSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in all_rows:
            # Multi-line cells: tab + CR temizle (TSV güvenliği)
            cleaned = {}
            for k in COLUMNS:
                v = row.get(k)
                if v is None:
                    cleaned[k] = ""
                else:
                    cleaned[k] = str(v).replace("\t", " ").replace("\r", " ")
            writer.writerow(cleaned)

    print(f"\n[done] {len(all_rows)} satır → {OUTPUT_TSV}")
    print(
        f"[next] python -m backend.scripts.quality.scoring_template --prepare {OUTPUT_TSV}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
