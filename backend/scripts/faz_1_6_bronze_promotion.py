#!/usr/bin/env python3
"""
Faz 1.6 — Bronze tier promotion migration (Session 161c/162).

PURPOSE:
  Pipeline-fix uygulanmış satırlara `quality_review_status = 'bronze_clean'` SET.
  Convention v3 (qrs_v3_20260514 alembic deployed) sonrası bekleyen tek Faz 1
  iş kalemi.

FILTER (gevşek, Plan v1 hedefi ~80-100K uyumlu):
  - is_active = TRUE
  - quality_review_status = 'unverified'
  - question_image_url IS NOT NULL  (pipeline-fix kanıtı, Tier A/B/C/D/E/F/G/I)
  - quality_flags problem işaretleri YOK:
      duplicate_option_values, answer_uncertain, numeric_q_nonnumeric_a, empty_options

EXPECTED: 84,905 satır UPDATE (pre-flight count).

AUDIT TRAIL:
  pipeline_metadata.faz_1_6_bronze = {
    "date": "<date>",
    "prev_status": "unverified",
    "filter_version": "v1_loose"
  }

OUTPUTS:
  backend/_pilots/20260516_faz_1_6_bronze_BACKUP.tsv
  backend/_pilots/20260516_faz_1_6_bronze_RESULT.md

USAGE:
  python backend/scripts/faz_1_6_bronze_promotion.py --dry-run
  python backend/scripts/faz_1_6_bronze_promotion.py --apply
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")
FILTER_VERSION = "v1_loose"
BATCH_SIZE = 5000


FILTER_WHERE = """
WHERE is_active = TRUE
  AND quality_review_status = 'unverified'
  AND question_image_url IS NOT NULL
  AND NOT (
    pipeline_metadata::jsonb ? 'quality_flags'
    AND pipeline_metadata::jsonb -> 'quality_flags' ?| ARRAY[
      'duplicate_option_values',
      'answer_uncertain',
      'numeric_q_nonnumeric_a',
      'empty_options'
    ]
  )
"""

SELECT_BACKUP_SQL = (
    f"SELECT id, quality_review_status FROM question_bank {FILTER_WHERE} ORDER BY id"
)
SELECT_COUNT_SQL = f"SELECT COUNT(*) FROM question_bank {FILTER_WHERE}"


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        print("[error] --dry-run veya --apply gerekli", flush=True)
        return 2

    from sqlalchemy import text

    eng = get_engine()
    mode = "apply" if args.apply else "dryrun"
    backup_path = PILOTS_DIR / f"20260516_faz_1_6_bronze_BACKUP_{mode}.tsv"
    result_md = PILOTS_DIR / f"20260516_faz_1_6_bronze_{mode}_RESULT.md"

    # Pre-state count
    with eng.connect() as c:
        pre_dist = c.execute(
            text(
                "SELECT quality_review_status, COUNT(*) FROM question_bank "
                "WHERE is_active=true GROUP BY 1 ORDER BY 2 DESC"
            )
        ).fetchall()
        candidate_count = c.execute(text(SELECT_COUNT_SQL)).scalar()

    print(f"[mode] {mode}")
    print(f"[candidates] {candidate_count:,} satır filter eşleşti")
    print("[pre-state]")
    for s, n in pre_dist:
        print(f"  {s or 'NULL':30s} {n:>10,}")

    # BACKUP (pre-state of all candidates)
    print(f"\n[backup] {backup_path.name} yazılıyor...", flush=True)
    start = time.time()
    with backup_path.open("w", encoding="utf-8") as bf:
        bf.write("id\tprev_status\n")
        with eng.connect() as c:
            rs = c.execution_options(stream_results=True).execute(
                text(SELECT_BACKUP_SQL)
            )
            n = 0
            for row in rs:
                bf.write(f"{row[0]}\t{row[1]}\n")
                n += 1
    print(f"[backup] {n:,} satır yazıldı ({time.time() - start:.1f}s)")

    if args.dry_run:
        print("\n[dry-run] UPDATE atlandı, RESULT yazılıyor")
        write_result_md(result_md, mode, candidate_count, pre_dist, applied=0)
        return 0

    # APPLY — batched UPDATE
    print(
        f"\n[apply] {candidate_count:,} satır UPDATE (batch={BATCH_SIZE:,})...",
        flush=True,
    )
    start = time.time()
    audit_obj = {
        "date": AUDIT_DATE,
        "prev_status": "unverified",
        "filter_version": FILTER_VERSION,
    }
    import json as _json

    audit_json = _json.dumps(audit_obj)

    # Tek UPDATE — PostgreSQL atomic transaction (filter WHERE inline)
    update_sql = f"""
        UPDATE question_bank
        SET quality_review_status = 'bronze_clean',
            pipeline_metadata = CASE
                WHEN pipeline_metadata IS NULL THEN CAST(:audit AS json)
                ELSE CAST(
                    jsonb_set(
                        CAST(pipeline_metadata AS jsonb),
                        '{{faz_1_6_bronze}}',
                        CAST(:audit AS jsonb),
                        TRUE
                    ) AS json
                )
            END,
            updated_at = NOW()
        {FILTER_WHERE}
    """
    with eng.begin() as c:
        result = c.execute(text(update_sql), {"audit": audit_json})
        applied = result.rowcount
    elapsed = time.time() - start
    print(
        f"[apply] {applied:,} satır UPDATE ({elapsed:.1f}s, {applied / elapsed:.0f}/s)"
    )

    # Post-state count
    with eng.connect() as c:
        post_dist = c.execute(
            text(
                "SELECT quality_review_status, COUNT(*) FROM question_bank "
                "WHERE is_active=true GROUP BY 1 ORDER BY 2 DESC"
            )
        ).fetchall()
        view_count = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()
    print("\n[post-state]")
    for s, n in post_dist:
        print(f"  {s or 'NULL':30s} {n:>10,}")
    print(f"\n[v_safe_for_beta] {view_count:,} (bronze_clean dahil DEĞİL bekleniyor)")

    write_result_md(
        result_md, mode, candidate_count, pre_dist, applied, post_dist, view_count
    )
    print(f"\n[done] RESULT: {result_md.name}")
    return 0


def write_result_md(
    path, mode, candidate_count, pre_dist, applied, post_dist=None, view_count=None
):
    lines = []
    lines.append(f"# Faz 1.6 Bronze Promotion — {mode.upper()} RESULT")
    lines.append(f"\n**Date:** {AUDIT_DATE}")
    lines.append(
        f"**Filter version:** {FILTER_VERSION} (gevşek: image_url + no problem flags)"
    )
    lines.append(f"**Candidates:** {candidate_count:,}")
    if applied:
        lines.append(f"**Applied:** {applied:,}")
    lines.append("\n## Pre-state")
    lines.append("| Status | Count |\n|---|---|")
    for s, n in pre_dist:
        lines.append(f"| {s or 'NULL'} | {n:,} |")
    if post_dist:
        lines.append("\n## Post-state")
        lines.append("| Status | Count |\n|---|---|")
        for s, n in post_dist:
            lines.append(f"| {s or 'NULL'} | {n:,} |")
        lines.append(
            f"\n**v_safe_for_beta:** {view_count:,} (bronze_clean view'a alınmaz)"
        )
    lines.append(
        f"\n**BACKUP TSV:** `backend/_pilots/20260516_faz_1_6_bronze_BACKUP_{mode}.tsv`"
    )
    lines.append("\n## Audit trail format")
    lines.append(
        '```json\n{"faz_1_6_bronze": {"date": "<date>", "prev_status": "unverified", "filter_version": "v1_loose"}}\n```'
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
