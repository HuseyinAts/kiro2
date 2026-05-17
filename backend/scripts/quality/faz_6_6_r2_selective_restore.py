#!/usr/bin/env python3
"""
Faz 6.6 Opsiyon B — R2 selective restore.

Faz 6.6 audit: R2 (Aromat) %94 false-negative. Single-subject Aromat
kitapları (Matematik, Fizik, Edebiyat, Paragraf, Türkce) doğru etiketli.
Sadece multi-disiplin volumler (Fen Bilimleri, Sosyal Bilimler) wrong_topic.

Bu script: rejected (R2) → auto_judged_high, AMA SADECE single-subject Aromat.
Multi-disp Aromat rejected kalır.

Tahmini etki:
  - Restore: ~2,463 satır (Fizik 1339 + Matematik 790 + Paragraf 207 + Edebiyat 60 + Türkce 67)
  - Keep rejected: ~469 satır (Fen Bilimleri 372 + Sosyal Bilimler 97)

Audit trail: pipeline_metadata.beta_filter_v2_r2_restore eklenir.

USAGE:
  python -m backend.scripts.quality.faz_6_6_r2_selective_restore --dry-run
  python -m backend.scripts.quality.faz_6_6_r2_selective_restore --apply
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
RESTORE_VERSION = "v2_r2_selective_restore_faz_6_6"

# WHERE clause: rejected via R2, NOT multi-disp
RESTORE_WHERE = """
    is_active = TRUE
    AND quality_review_status = 'rejected'
    AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = 'R2_aromat_wrong_topic'
    AND source_book NOT ILIKE '%Fen Bilimleri%'
    AND source_book NOT ILIKE '%Sosyal Bilimler%'
"""


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

    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        print("[error] --dry-run veya --apply gerekli")
        return 2

    eng = get_engine()
    mode = "apply" if args.apply else "dryrun"
    result_md = PILOTS_DIR / f"20260517_faz_6_6_r2_restore_{mode}_RESULT.md"

    audit_obj = {
        "date": AUDIT_DATE,
        "restore_version": RESTORE_VERSION,
        "previous_status": "rejected",
        "previous_rule": "R2_aromat_wrong_topic",
        "reason": "single_subject_aromat_correct_label",
    }
    audit_json = json.dumps(audit_obj)

    print(f"[mode] {mode}")
    print("[criteria] Single-subject Aromat (NOT Fen Bilimleri, NOT Sosyal Bilimler)")
    print()

    # Pre-state
    with eng.connect() as c:
        pre_total = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                "AND quality_review_status='rejected'"
            )
        ).scalar()
        pre_r2 = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                "AND quality_review_status='rejected' "
                "AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = 'R2_aromat_wrong_topic'"
            )
        ).scalar()
        pre_view = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()

    print("[pre-state]")
    print(f"  rejected total:           {pre_total:>10,}")
    print(f"  rejected via R2 (Aromat): {pre_r2:>10,}")
    print(f"  v_safe_for_beta:          {pre_view:>10,}")
    print()

    # Count rows to be restored
    count_sql = f"SELECT COUNT(*) FROM question_bank WHERE {RESTORE_WHERE}"
    with eng.connect() as c:
        n_restore = c.execute(text(count_sql)).scalar()
    print(f"[restore target] {n_restore:,} satır → auto_judged_high")
    print()

    # Source book breakdown
    breakdown_sql = f"""
        SELECT source_book, COUNT(*) AS cnt
        FROM question_bank
        WHERE {RESTORE_WHERE}
        GROUP BY 1 ORDER BY 2 DESC
    """
    with eng.connect() as c:
        breakdown = c.execute(text(breakdown_sql)).fetchall()
    print("[breakdown (restore)]")
    for sb, cnt in breakdown:
        print(f"  {sb[:60]:60s} {cnt:>6,}")
    print()

    # Apply
    counts = {"restored": 0}
    elapsed = 0.0
    if args.apply:
        start = time.time()
        restore_sql = f"""
            UPDATE question_bank
            SET quality_review_status = 'auto_judged_high',
                pipeline_metadata = jsonb_set(
                    COALESCE(CAST(pipeline_metadata AS jsonb), '{{}}'::jsonb),
                    '{{beta_filter_v2_r2_restore}}',
                    CAST(:audit AS jsonb),
                    TRUE
                )::json,
                updated_at = NOW()
            WHERE {RESTORE_WHERE}
        """
        with eng.begin() as c:
            result = c.execute(text(restore_sql), {"audit": audit_json})
            counts["restored"] = result.rowcount
        elapsed = time.time() - start
        print(f"[apply] {counts['restored']:,} satır UPDATE ({elapsed:.1f}s)")
    else:
        counts["restored"] = n_restore
        print(f"[dry-run] {n_restore:,} satır UPDATE atlandı")

    print()

    # Post-state
    with eng.connect() as c:
        post_total = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                "AND quality_review_status='rejected'"
            )
        ).scalar()
        post_view = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()
    print("[post-state]")
    print(f"  rejected total: {post_total:>10,}  (Δ {post_total - pre_total:+,})")
    print(f"  v_safe_for_beta: {post_view:>10,} (Δ {post_view - pre_view:+,})")
    print()

    # RESULT MD
    lines = [
        f"# Faz 6.6 Opsiyon B — R2 Selective Restore ({mode.upper()})",
        "",
        f"**Date:** {AUDIT_DATE}",
        f"**Version:** {RESTORE_VERSION}",
        f"**Mode:** {mode}",
        f"**Elapsed:** {elapsed:.1f}s",
        "",
        "## Criteria",
        "",
        "Single-subject Aromat kitapları (Matematik, Fizik, Türkçe, Edebiyat,",
        "Paragraf) doğru etiketli — wrong_topic değil. Faz 5+6 R2 mass reject",
        "yanlıştı. Sadece multi-disiplin volumler rejected kalmalı.",
        "",
        "**Restore filter:**",
        "```sql",
        "WHERE quality_review_status = 'rejected'",
        "  AND beta_filter_v1.rule = 'R2_aromat_wrong_topic'",
        "  AND source_book NOT ILIKE '%Fen Bilimleri%'",
        "  AND source_book NOT ILIKE '%Sosyal Bilimler%'",
        "```",
        "",
        "## Pre/Post State",
        "",
        "| Metric | Pre | Post | Δ |",
        "|---|---|---|---|",
        f"| rejected total | {pre_total:,} | {post_total:,} | {post_total - pre_total:+,} |",
        f"| rejected via R2 | {pre_r2:,} | (after restore) | — |",
        f"| v_safe_for_beta | {pre_view:,} | {post_view:,} | {post_view - pre_view:+,} |",
        f"| Restored | — | — | **{counts['restored']:,}** |",
        "",
        "## Source Book Breakdown (restored)",
        "",
        "| Source Book | Count |",
        "|---|---|",
    ]
    for sb, cnt in breakdown:
        lines.append(f"| {sb} | {cnt:,} |")
    lines.extend(
        [
            "",
            "## Audit Trail",
            "",
            "Restored satırlarda `pipeline_metadata.beta_filter_v2_r2_restore`:",
            "```json",
            json.dumps(audit_obj, indent=2, ensure_ascii=False),
            "```",
            "",
            "Önceki `beta_filter_v1` audit korunur (rollback için).",
            "",
        ]
    )

    result_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[result] {result_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
