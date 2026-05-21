#!/usr/bin/env python3
"""
Faz 6.6 — Reject pile audit (false-negative kontrol).

W20 baseline'da 3/30 = %10 false-negative tespit edildi (3'ü de R1
legacy_v3 mass reject kurbanı). Bu audit hipotezi 100 sample ile test eder:

  H0: R1 false-negative rate = %10
  H1: R2 false-negative rate ≈ %0 (Aromat wrong_topic systemic)

Sampling: 50 R1 + 50 R2 stratified (audit trail: pipeline_metadata.beta_filter_v1.rule)
Seed: deterministic 'faz_6_6_reject_audit_v1'

USAGE:
  python -m backend.scripts.quality.faz_6_6_reject_audit
"""

from __future__ import annotations

import csv
import os
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
AUDIT_DATE = date.today().strftime("%Y%m%d")
SEED = "faz_6_6_reject_audit_v1"
N_PER_RULE = 50

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
    "reject_rule",
    "match_tier",
    "verdict",
    "error_type",
    "notes",
]


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def sample_stratified(eng, n_per_rule: int):
    from sqlalchemy import text

    sql = """
        SELECT
            CAST(id AS text) AS id,
            subject_area,
            source_book,
            source_page,
            question_text,
            option_a, option_b, option_c, option_d, option_e,
            correct_answer,
            question_image_url,
            pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' AS reject_rule,
            pipeline_metadata::jsonb ->> 'match_tier' AS match_tier
        FROM question_bank
        WHERE is_active = TRUE
          AND quality_review_status = 'rejected'
          AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = :rule
        ORDER BY md5(CAST(id AS text) || :seed)
        LIMIT :n
    """
    rules = ["R1_legacy_v3", "R2_aromat_wrong_topic"]
    all_rows = []
    for rule in rules:
        with eng.connect() as c:
            result = c.execute(
                text(sql), {"rule": rule, "seed": SEED + rule, "n": n_per_rule}
            ).fetchall()
        rows = [dict(r._mapping) for r in result]
        print(f"[{rule}] {len(rows)} sample")
        all_rows.extend(rows)
    return all_rows


def main() -> int:
    eng = get_engine()
    rows = sample_stratified(eng, N_PER_RULE)

    out_path = PILOTS_DIR / f"{AUDIT_DATE}_faz_6_6_reject_audit_RAW.tsv"
    PILOTS_DIR.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            cleaned = {}
            for k in COLUMNS:
                v = row.get(k)
                if v is None:
                    cleaned[k] = ""
                else:
                    cleaned[k] = str(v).replace("\t", " ").replace("\r", " ")
            writer.writerow(cleaned)

    print(f"\n[done] {len(rows)} sample → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
