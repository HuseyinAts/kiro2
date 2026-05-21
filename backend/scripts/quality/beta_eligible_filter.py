#!/usr/bin/env python3
"""
Faz 5+6 Alternative: Rule-based beta-eligible filter (ANTHROPIC API'siz).

Faz 4.1 ground truth (200 sample) pattern'lerini 84,905 bronze_clean'a uygula.
LLM judge yerine deterministic rule-based filter.

RULES:
  R1: legacy_v3_unaudited → 'rejected' (Plan v1 hardcoded %87 hata)
  R2: bronze_clean + book ILIKE 'Aromat%' → 'rejected' (Tier5 wrong_topic systemic)
  R3: bronze_clean + book ILIKE '%Edebiyat_Sokagi_Dil_Bilgisi%' → bronze_clean (manual queue)
      + pipeline_metadata.manual_review_required=true (solution-leak risk)
  R4: kalan bronze_clean → 'auto_judged_high' (Gold tier, beta-eligible)

CONVENTION v3 statuses:
  - auto_judged_high: LLM/rule judge yüksek güven → Gold, beta-eligible
  - rejected: Reddedildi
  - bronze_clean: Judge için hazır (kalan manual queue)

USAGE:
  python backend/scripts/quality/beta_eligible_filter.py --dry-run
  python backend/scripts/quality/beta_eligible_filter.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")
FILTER_VERSION = "v1_faz_4_1_patterns"


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
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
        print("[error] --dry-run veya --apply gerekli")
        return 2

    from sqlalchemy import text

    eng = get_engine()
    mode = "apply" if args.apply else "dryrun"
    result_md = PILOTS_DIR / f"20260517_beta_eligible_filter_{mode}_RESULT.md"

    audit_obj = {"date": AUDIT_DATE, "filter_version": FILTER_VERSION}
    audit_json = json.dumps(audit_obj)

    print(f"[mode] {mode}")

    # Pre-state
    with eng.connect() as c:
        pre = c.execute(
            text(
                "SELECT quality_review_status, COUNT(*) FROM question_bank "
                "WHERE is_active=true GROUP BY 1 ORDER BY 2 DESC"
            )
        ).fetchall()
    print("[pre-state]")
    for s, n in pre:
        print(f"  {s or 'NULL':25s} {n:>10,}")
    print()

    # R1: legacy_v3 → rejected
    r1_sql = """
        UPDATE question_bank
        SET quality_review_status = 'rejected',
            pipeline_metadata = jsonb_set(
                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                '{beta_filter_v1}',
                CAST(:audit AS jsonb) || '{"rule":"R1_legacy_v3"}'::jsonb,
                TRUE
            )::json,
            updated_at = NOW()
        WHERE is_active=true AND quality_review_status='legacy_v3_unaudited'
    """

    # R2: bronze_clean + Aromat → rejected
    r2_sql = """
        UPDATE question_bank
        SET quality_review_status = 'rejected',
            pipeline_metadata = jsonb_set(
                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                '{beta_filter_v1}',
                CAST(:audit AS jsonb) || '{"rule":"R2_aromat_wrong_topic"}'::jsonb,
                TRUE
            )::json,
            updated_at = NOW()
        WHERE is_active=true AND quality_review_status='bronze_clean'
          AND (source_book ILIKE 'Aromat%' OR source_book ILIKE 'Aromot%')
    """

    # R3: Edebiyat Sokagi Dil Bilgisi → manual_review flag (status değişmez)
    r3_sql = """
        UPDATE question_bank
        SET pipeline_metadata = jsonb_set(
                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                '{beta_filter_v1}',
                CAST(:audit AS jsonb) || '{"rule":"R3_edebiyat_sokagi_solution_leak", "manual_review_required":true}'::jsonb,
                TRUE
            )::json,
            updated_at = NOW()
        WHERE is_active=true AND quality_review_status='bronze_clean'
          AND source_book ILIKE '%Edebiyat_Sokagi_Dil_Bilgisi%'
    """

    # R4: kalan bronze_clean → auto_judged_high (Gold)
    r4_sql = """
        UPDATE question_bank
        SET quality_review_status = 'auto_judged_high',
            pipeline_metadata = jsonb_set(
                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                '{beta_filter_v1}',
                CAST(:audit AS jsonb) || '{"rule":"R4_rule_based_gold"}'::jsonb,
                TRUE
            )::json,
            updated_at = NOW()
        WHERE is_active=true AND quality_review_status='bronze_clean'
          AND NOT (source_book ILIKE 'Aromat%' OR source_book ILIKE 'Aromot%')
          AND NOT (source_book ILIKE '%Edebiyat_Sokagi_Dil_Bilgisi%')
          AND NOT (
              pipeline_metadata::jsonb ? 'quality_flags'
              AND pipeline_metadata::jsonb -> 'quality_flags' ?| ARRAY['duplicate_option_values','answer_uncertain','numeric_q_nonnumeric_a','empty_options']
          )
    """

    rules = [
        ("R1_legacy_v3_reject", r1_sql),
        ("R2_aromat_reject", r2_sql),
        ("R3_edebiyat_sokagi_manual", r3_sql),
        ("R4_kalan_auto_judged_high", r4_sql),
    ]

    counts = {}
    start = time.time()
    if args.apply:
        for name, sql in rules:
            with eng.begin() as c:
                result = c.execute(text(sql), {"audit": audit_json})
                counts[name] = result.rowcount
            print(f"[apply] {name}: {counts[name]:,} satır UPDATE")
    else:
        # Dry-run: SELECT COUNT
        for name, sql in rules:
            # WHERE clause çıkar
            where_part = sql.split("WHERE", 1)[1]
            count_sql = f"SELECT COUNT(*) FROM question_bank WHERE {where_part}"
            with eng.connect() as c:
                # :audit param dummy needed
                n = c.execute(text(count_sql), {"audit": audit_json}).scalar()
            counts[name] = n
            print(f"[dry-run] {name}: {n:,} satır (would UPDATE)")
    elapsed = time.time() - start

    # Post-state
    with eng.connect() as c:
        post = c.execute(
            text(
                "SELECT quality_review_status, COUNT(*) FROM question_bank "
                "WHERE is_active=true GROUP BY 1 ORDER BY 2 DESC"
            )
        ).fetchall()
        view_count = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()
    print()
    print("[post-state]")
    for s, n in post:
        print(f"  {s or 'NULL':25s} {n:>10,}")
    print(f"\n[v_safe_for_beta] {view_count:,} satır")

    # RESULT MD
    lines = []
    lines.append(f"# Beta Eligible Filter — {mode.upper()} RESULT\n")
    lines.append(f"**Date:** {AUDIT_DATE}")
    lines.append(f"**Filter version:** {FILTER_VERSION}")
    lines.append(f"**Mode:** {mode}")
    lines.append(f"**Elapsed:** {elapsed:.1f}s\n")
    lines.append("## Rule Counts\n")
    lines.append("| Rule | Count |\n|---|---|")
    for name, n in counts.items():
        lines.append(f"| {name} | {n:,} |")
    lines.append("")
    lines.append("## Pre/Post State\n")
    lines.append("| Status | Pre | Post |\n|---|---|---|")
    pre_d = {s: n for s, n in pre}
    post_d = {s: n for s, n in post}
    for s in sorted(set(pre_d) | set(post_d)):
        lines.append(f"| {s} | {pre_d.get(s, 0):,} | {post_d.get(s, 0):,} |")
    lines.append("")
    lines.append(f"**v_safe_for_beta:** {view_count:,}")
    lines.append("")
    lines.append("## Audit trail format\n")
    lines.append(
        '```json\n{"beta_filter_v1": {"date": "...", "filter_version": "v1_faz_4_1_patterns", "rule": "R1_legacy_v3 / R2_aromat / R3_edebiyat / R4_gold"}}\n```'
    )

    result_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[result] {result_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
