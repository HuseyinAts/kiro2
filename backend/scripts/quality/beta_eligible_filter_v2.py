#!/usr/bin/env python3
"""
Bug #9 fix — Rule-based OCR truncation residual filter (API-free).

Faz 5+6 v1 (`beta_eligible_filter.py`) sonrası `auto_judged_high` pool'da
kalan OCR cut-off pattern'ini hedefler.

  R6:  question_text terminal punctuation YOK (. ? ! » " ' ) ])
       → OCR cut-off, Faz 1.10 re-OCR sonrası kalan residual

İPTAL EDİLEN RULE'LAR (sample audit, 18 May 2026):
  R5a (repeated_char 7+):  YANLIŞ POZİTİF — 7/8 sample MEŞRU fill-in-blank
       sorularını yakalıyor ("(-) yüklü iyonlara ............ denir.")
  R5b (ends_with_ellipsis): MIXED — paragraf sorularda "..." meşru
       ("Çünkü ...." soruya devam beklentisi)
  → Bug #5 (AI nonsense detection) Faz 6.1 judge pipeline'a defer

DRY-RUN ÖRNEKLEME (17 May 2026, auto_judged_high=84,239):
  R6 truncation_no_terminal :  318  (%0.38)

Sample audit (R6, 5/5 gerçek cut-off):
  "Bu çöze..." (kelime ortası)
  "_{1}^{1}H, _{6}^{12}C, _" (LaTeX cut-off)
  "$O_1$ ve $O_2$ kaynakl" (kelime ortası)
  "...filmden filme tekrarl" (kelime ortası)
  "|AB" (LaTeX cut-off)

Convention v3 status flow:
  auto_judged_high → rejected (audit trail: beta_filter_v2)

Bug #7 + #10:
  → Bug #11 (commit 4bc0a6e29) ile NEUTRALIZED
    - image-required regex 52,970 satır exclude (runtime filter)
    - frontend question_image_url render suppress (defensive)
  → E2E smoke ile post-fix doğrulanır (ayrı task)

USAGE:
  python backend/scripts/quality/beta_eligible_filter_v2.py --dry-run
  python backend/scripts/quality/beta_eligible_filter_v2.py --apply
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
FILTER_VERSION = "v2_truncation_only"


def get_engine():
    from sqlalchemy import create_engine

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "/kiro2_db", "/kiro2"
    )
    return create_engine(db_url)


# Rule SQL — predicates kept inline so dry-run count matches apply UPDATE exactly.

R5A_PREDICATE = "question_text ~ '(.)\\1{6,}'"
R5B_PREDICATE = "question_text ~ '\\.\\.\\.\\s*$'"
R6_PREDICATE = "question_text ~ '[^\\.\\?\\!\\»\"''\\)\\]]\\s*$'"


def _rule_sql(rule_name: str, predicate: str) -> str:
    return f"""
        UPDATE question_bank
        SET quality_review_status = 'rejected',
            pipeline_metadata = jsonb_set(
                COALESCE(CAST(pipeline_metadata AS jsonb), '{{}}'::jsonb),
                '{{beta_filter_v2}}',
                CAST(:audit AS jsonb) || CAST('{{"rule":"{rule_name}"}}' AS jsonb),
                TRUE
            )::json,
            updated_at = NOW()
        WHERE is_active=true
          AND quality_review_status='auto_judged_high'
          AND {predicate}
    """


def _count_sql(predicate: str) -> str:
    return f"""
        SELECT COUNT(*) FROM question_bank
        WHERE is_active=true
          AND quality_review_status='auto_judged_high'
          AND {predicate}
    """


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
    today = datetime.now().strftime("%Y%m%d")
    result_md = PILOTS_DIR / f"{today}_beta_eligible_filter_v2_{mode}_RESULT.md"

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

    # R5a (repeated_char) + R5b (ellipsis) IPTAL — sample audit yanlış pozitif
    # (fill-in-blank "..........." pattern Türkçe eğitimde meşru kullanım)
    # Bug #5 nonsense detection → Faz 6.1 LLM judge'a defer
    rules = [
        ("R6_truncation_no_terminal", R6_PREDICATE),
    ]

    counts: dict[str, int] = {}
    start = time.time()

    if args.apply:
        # Sıra: R5a → R5b → R6. R5a/R5b match olan satırlar R6'da artık
        # `auto_judged_high` olmadığı için R6 sayısı dry-run'dan az olabilir.
        # Bu doğru ve istenen davranış (her satır tek rule altında işlenir).
        for name, pred in rules:
            sql = _rule_sql(name, pred)
            with eng.begin() as c:
                result = c.execute(text(sql), {"audit": audit_json})
                counts[name] = result.rowcount
            print(f"[apply] {name}: {counts[name]:,} satır UPDATE")
    else:
        for name, pred in rules:
            with eng.connect() as c:
                n = c.execute(text(_count_sql(pred))).scalar()
            counts[name] = n or 0
            print(f"[dry-run] {name}: {counts[name]:,} satır (would UPDATE)")

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

    lines = []
    lines.append(f"# Beta Eligible Filter v2 — {mode.upper()} RESULT\n")
    lines.append(f"**Date:** {AUDIT_DATE}")
    lines.append(f"**Filter version:** {FILTER_VERSION}")
    lines.append(f"**Mode:** {mode}")
    lines.append(f"**Elapsed:** {elapsed:.1f}s\n")
    lines.append("## Rule Counts\n")
    lines.append("| Rule | Count |\n|---|---|")
    for name, n in counts.items():
        lines.append(f"| {name} | {n:,} |")
    lines.append(f"| **TOTAL (overlap dahil)** | **{sum(counts.values()):,}** |")
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
    lines.append("## Bug coverage\n")
    lines.append("| Bug | Status |\n|---|---|")
    lines.append(
        "| Bug #5 AI nonsense filter | DEFER → Faz 6.1 LLM judge (rule-based yanlış pozitif riski yüksek) |"
    )
    lines.append("| Bug #9 OCR truncation residual | R6 ✅ |")
    lines.append(
        "| Bug #7 question-image MISMATCH | NEUTRALIZED via Bug #11 (image suppress) |"
    )
    lines.append(
        "| Bug #10 image yok/yanlış | NEUTRALIZED via Bug #11 (image suppress) |"
    )
    lines.append(
        "| Bug #11 vision audit classification | DEFER — post-beta vision re-crop |"
    )
    lines.append("")
    lines.append("## Audit trail format\n")
    lines.append(
        '```json\n{"beta_filter_v2": {"date": "...", "filter_version": "v2_nonsense_truncation", "rule": "R5a / R5b / R6"}}\n```'
    )

    result_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[result] {result_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
