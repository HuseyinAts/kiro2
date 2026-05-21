#!/usr/bin/env python3
"""
R1 legacy_v3 False-Negative Restore — APPLY (full population).

Pilot script `backend/_pilots/r1_legacy_v3_fn_restore_pilot.py` 100 sample
stratified audit ile auto-rule kriterini doğruladı (~%87 restorable,
Faz 6.6 %24+ bulgusunun üzerinde).

Bu script 18,397 R1_legacy_v3 reject havuzunun tamamına aynı kuralı
uygular. Conservative — false-positive YOK hedefli. Apply default OFF.

Restore criteria (pilot ile aynı, 6 koşul):
  1. question_image_url IS NOT NULL ve boş değil
  2. 5 option (a-e) tümü dolu
  3. correct_answer ∈ {A,B,C,D,E}
  4. LENGTH(question_text) >= 50
  5. Text 5+ tekrarlı karakter içermiyor (regex (.)\\1{4,})
  6. Text 4+ ardışık nokta içermiyor (regex \\.{4,})

Audit trail: pipeline_metadata.r1_restore_v1 eklenir.
Önceki beta_filter_v1 metadata korunur (rollback için).

USAGE:
  python backend/scripts/quality/r1_legacy_v3_restore_apply.py --dry-run
  python backend/scripts/quality/r1_legacy_v3_restore_apply.py --apply
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
RESTORE_VERSION = "r1_restore_v1"
PILOT_RESTORABLE_PCT = 87.0  # 100 sample pilot (2026-05-21)

# Restore WHERE clause — auto-rule 6 koşul + R1 reject
# Postgres regex: ~ case-sensitive, !~ negation
# Repeat char: (.)\1{4,} → herhangi karakter 5+ tekrar
# Ellipsis: \.{4,} → 4+ ardışık nokta
RESTORE_WHERE = r"""
    is_active = TRUE
    AND quality_review_status = 'rejected'
    AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = 'R1_legacy_v3'
    -- 1. has_image
    AND question_image_url IS NOT NULL
    AND question_image_url <> ''
    -- 2. has_5_options
    AND option_a IS NOT NULL AND option_a <> ''
    AND option_b IS NOT NULL AND option_b <> ''
    AND option_c IS NOT NULL AND option_c <> ''
    AND option_d IS NOT NULL AND option_d <> ''
    AND option_e IS NOT NULL AND option_e <> ''
    -- 3. valid_correct_answer
    AND correct_answer IN ('A','B','C','D','E')
    -- 4. text_min_len
    AND LENGTH(question_text) >= 50
    -- 5. text_no_repeat (5+ tekrarlı karakter yok)
    AND question_text !~ '(.)\1{4,}'
    -- 6. text_no_ellipsis (4+ ardışık nokta yok)
    AND question_text !~ '\.{4,}'
"""


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
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        print("[error] --dry-run veya --apply gerekli")
        return 2

    eng = get_engine()
    mode = "apply" if args.apply else "dryrun"
    result_md = PILOTS_DIR / f"20260521_r1_fn_restore_{mode}_RESULT.md"

    audit_obj = {
        "date": AUDIT_DATE,
        "restore_version": RESTORE_VERSION,
        "reason": "false_negative_recovery",
        "pilot_restorable_pct": PILOT_RESTORABLE_PCT,
        "previous_status": "rejected",
        "previous_rule": "R1_legacy_v3",
        "criteria_summary": ("image+5opt+valid_ca+len>=50+no_repeat_char+no_ellipsis"),
    }
    audit_json = json.dumps(audit_obj)

    print(f"[mode] {mode}")
    print(f"[version] {RESTORE_VERSION}")
    print(f"[pilot] {PILOT_RESTORABLE_PCT}% restorable in 100 sample")
    print()

    # Pre-state
    with eng.connect() as c:
        pre_total_rejected = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                "AND quality_review_status='rejected'"
            )
        ).scalar()
        pre_r1_rejected = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                "AND quality_review_status='rejected' "
                "AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = 'R1_legacy_v3'"
            )
        ).scalar()
        try:
            pre_view = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()
        except Exception:
            pre_view = None
        pre_auto_high = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                "AND quality_review_status='auto_judged_high'"
            )
        ).scalar()

    print("[pre-state]")
    print(f"  rejected total:           {pre_total_rejected:>10,}")
    print(f"  rejected via R1:          {pre_r1_rejected:>10,}")
    print(f"  auto_judged_high:         {pre_auto_high:>10,}")
    if pre_view is not None:
        print(f"  v_safe_for_beta:          {pre_view:>10,}")
    print()

    # Count rows to be restored
    count_sql = f"SELECT COUNT(*) FROM question_bank WHERE {RESTORE_WHERE}"
    with eng.connect() as c:
        n_restore = c.execute(text(count_sql)).scalar()
    pct_of_r1 = n_restore / pre_r1_rejected * 100 if pre_r1_rejected else 0
    print(f"[restore target] {n_restore:,} satır → auto_judged_high")
    print(f"  R1 havuzunun %{pct_of_r1:.1f}'i (pilot tahmini: %{PILOT_RESTORABLE_PCT})")
    print()

    # Subject breakdown
    breakdown_sql = f"""
        SELECT subject_area, COUNT(*) AS cnt
        FROM question_bank
        WHERE {RESTORE_WHERE}
        GROUP BY 1 ORDER BY 2 DESC
    """
    with eng.connect() as c:
        breakdown = c.execute(text(breakdown_sql)).fetchall()
    print("[subject breakdown (restore)]")
    for s, cnt in breakdown:
        print(f"  {s:15s} {cnt:>6,}")
    print()

    # NOT-restorable (kept rejected) breakdown — debugging için
    not_restorable_sql = """
        SELECT
            COUNT(*) FILTER (
                WHERE question_image_url IS NULL OR question_image_url = ''
            ) AS no_image,
            COUNT(*) FILTER (
                WHERE option_a IS NULL OR option_b IS NULL OR option_c IS NULL
                  OR option_d IS NULL OR option_e IS NULL
                  OR option_a = '' OR option_b = '' OR option_c = ''
                  OR option_d = '' OR option_e = ''
            ) AS partial_options,
            COUNT(*) FILTER (
                WHERE correct_answer NOT IN ('A','B','C','D','E')
                   OR correct_answer IS NULL
            ) AS invalid_ca,
            COUNT(*) FILTER (
                WHERE LENGTH(question_text) < 50
            ) AS too_short,
            COUNT(*) FILTER (
                WHERE question_text ~ '(.)\\1{4,}'
            ) AS repeat_char,
            COUNT(*) FILTER (
                WHERE question_text ~ '\\.{4,}'
            ) AS ellipsis_garbage
        FROM question_bank
        WHERE is_active = TRUE
          AND quality_review_status = 'rejected'
          AND pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule' = 'R1_legacy_v3'
    """
    with eng.connect() as c:
        nr = c.execute(text(not_restorable_sql)).fetchone()
    print("[NOT-restorable causes (R1 pool, can overlap)]")
    print(f"  no_image:         {nr[0]:>6,}")
    print(f"  partial_options:  {nr[1]:>6,}")
    print(f"  invalid_ca:       {nr[2]:>6,}")
    print(f"  too_short (<50):  {nr[3]:>6,}")
    print(f"  repeat_char:      {nr[4]:>6,}")
    print(f"  ellipsis:         {nr[5]:>6,}")
    print()

    # Apply
    counts = {"restored": 0}
    elapsed = 0.0
    if args.apply:
        print("[!] APPLY MODE — Bu işlem GERİ ALINABİLİR (audit trail mevcut)")
        print("[!] Rollback için: pipeline_metadata.r1_restore_v1 işaretli satırlar")
        print("[!] Devam etmek için 5 saniye bekleyin (Ctrl+C ile iptal)")
        time.sleep(5)

        start = time.time()
        restore_sql = f"""
            UPDATE question_bank
            SET quality_review_status = 'auto_judged_high',
                pipeline_metadata = jsonb_set(
                    COALESCE(CAST(pipeline_metadata AS jsonb), '{{}}'::jsonb),
                    '{{r1_restore_v1}}',
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
        post_rejected = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                "AND quality_review_status='rejected'"
            )
        ).scalar()
        post_auto_high = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                "AND quality_review_status='auto_judged_high'"
            )
        ).scalar()
        try:
            post_view = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()
        except Exception:
            post_view = None

    print("[post-state]")
    print(
        f"  rejected total:    {post_rejected:>10,} "
        f"(Δ {post_rejected - pre_total_rejected:+,})"
    )
    print(
        f"  auto_judged_high:  {post_auto_high:>10,} "
        f"(Δ {post_auto_high - pre_auto_high:+,})"
    )
    if pre_view is not None and post_view is not None:
        print(f"  v_safe_for_beta:   {post_view:>10,} (Δ {post_view - pre_view:+,})")
    print()

    # RESULT MD
    lines = [
        f"# R1 legacy_v3 False-Negative Restore — {mode.upper()} RESULT",
        "",
        f"**Date:** {AUDIT_DATE}",
        f"**Version:** {RESTORE_VERSION}",
        f"**Mode:** {mode}",
        f"**Elapsed:** {elapsed:.1f}s",
        f"**Pilot:** %{PILOT_RESTORABLE_PCT} restorable (100 sample, 2026-05-21)",
        "",
        "## Context",
        "",
        "Faz 6.6 reject audit'i R1_legacy_v3 filtresinin %24 false-negative",
        "rate gösterdiğini tespit etti. R1 kural: `legacy_v3_unaudited` durumundaki",
        "tüm satırları toptan reject — audit edilmemiş ≠ kötü olduğu için fazla agresif.",
        "",
        "Bu restore conservative auto-rule ile (image + 5 opt + valid CA + len + no garbage)",
        "false-positive YOK hedefli kurtarma yapar.",
        "",
        "## Restore Filter",
        "",
        "```sql",
        "WHERE quality_review_status = 'rejected'",
        "  AND beta_filter_v1.rule = 'R1_legacy_v3'",
        "  AND question_image_url IS NOT NULL AND <> ''",
        "  AND option_a..option_e all NOT NULL AND <> ''",
        "  AND correct_answer IN ('A','B','C','D','E')",
        "  AND LENGTH(question_text) >= 50",
        "  AND question_text !~ '(.)\\1{4,}'  -- no 5+ repeat char",
        "  AND question_text !~ '\\.{4,}'      -- no 4+ ellipsis",
        "```",
        "",
        "## Pre/Post State",
        "",
        "| Metric | Pre | Post | Δ |",
        "|---|---|---|---|",
        (
            f"| rejected total | {pre_total_rejected:,} | {post_rejected:,} | "
            f"{post_rejected - pre_total_rejected:+,} |"
        ),
        f"| rejected via R1 | {pre_r1_rejected:,} | (after restore) | — |",
        (
            f"| auto_judged_high | {pre_auto_high:,} | {post_auto_high:,} | "
            f"{post_auto_high - pre_auto_high:+,} |"
        ),
    ]
    if pre_view is not None and post_view is not None:
        lines.append(
            f"| v_safe_for_beta | {pre_view:,} | {post_view:,} | "
            f"{post_view - pre_view:+,} |"
        )
    lines.append(f"| **Restored** | — | — | **{counts['restored']:,}** |")
    lines.extend(
        [
            "",
            "## Subject Breakdown (restored)",
            "",
            "| Subject | Count |",
            "|---|---|",
        ]
    )
    for s, cnt in breakdown:
        lines.append(f"| {s} | {cnt:,} |")

    lines.extend(
        [
            "",
            "## NOT-Restorable Causes (R1 pool, can overlap)",
            "",
            "| Cause | Count |",
            "|---|---|",
            f"| no_image | {nr[0]:,} |",
            f"| partial_options | {nr[1]:,} |",
            f"| invalid_correct_answer | {nr[2]:,} |",
            f"| too_short (<50 char) | {nr[3]:,} |",
            f"| repeat_char (5+) | {nr[4]:,} |",
            f"| ellipsis_garbage (4+ dots) | {nr[5]:,} |",
            "",
            "## Audit Trail",
            "",
            "Restored satırlarda `pipeline_metadata.r1_restore_v1`:",
            "```json",
            json.dumps(audit_obj, indent=2, ensure_ascii=False),
            "```",
            "",
            "Önceki `beta_filter_v1` audit korunur (rollback için).",
            "",
            "## Rollback SQL",
            "",
            "```sql",
            "UPDATE question_bank",
            "SET quality_review_status = 'rejected',",
            "    pipeline_metadata = (pipeline_metadata::jsonb - 'r1_restore_v1')::json,",
            "    updated_at = NOW()",
            "WHERE pipeline_metadata::jsonb ? 'r1_restore_v1'",
            "  AND pipeline_metadata::jsonb -> 'r1_restore_v1' ->> 'restore_version'"
            f" = '{RESTORE_VERSION}';",
            "```",
            "",
        ]
    )

    result_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[result] {result_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
