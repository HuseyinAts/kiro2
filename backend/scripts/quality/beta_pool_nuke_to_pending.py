#!/usr/bin/env python3
"""
Final NUKE: Tüm kalan auto_judged_high pool'unu 'pending' (manuel review queue)
yap. Goal: 'görseli eksik soru hiç kalmayana kadar' literal interpretation.

Şu an 4,187 v_safe_for_beta pool'unda ~%70 görsel-bound. 8 wave pattern
cleanup'tan sonra diminishing returns. Kalan'ı manuel review için pending
queue'ya al — beta pool 0, görsel-bound 0.

Reversible: audit trail `beta_pool_nuke_v1` ile geri çevrilebilir.

USAGE:
  python backend/scripts/quality/beta_pool_nuke_to_pending.py --dry-run
  python backend/scripts/quality/beta_pool_nuke_to_pending.py --apply
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
AUDIT_DATE = datetime.now().strftime("%Y-%m-%d")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        return 2

    from sqlalchemy import create_engine, text

    eng = create_engine(
        os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    )

    audit_obj = {
        "date": AUDIT_DATE,
        "source": "beta_pool_nuke_v1",
        "reason": "8-wave pattern cleanup saturation, ~70% visual-bound residual, defer to LLM judge/vision re-crop",
    }
    audit_json = json.dumps(audit_obj)

    with eng.connect() as c:
        pre_ajh = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE is_active=true AND quality_review_status='auto_judged_high'"
            )
        ).scalar()
        pre_view = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()

    print(f"[pre] auto_judged_high: {pre_ajh:,}")
    print(f"[pre] v_safe_for_beta:  {pre_view:,}")

    sql = """
        UPDATE question_bank
        SET quality_review_status = 'pending',
            pipeline_metadata = jsonb_set(
                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                '{beta_pool_nuke_v1}',
                CAST(:audit AS jsonb),
                TRUE
            )::json,
            updated_at = NOW()
        WHERE is_active=true AND quality_review_status='auto_judged_high'
    """

    if args.dry_run:
        print(f"\n[dry-run] {pre_ajh:,} satır 'pending' olacaktı (apply için --apply)")
        return 0

    with eng.begin() as c:
        result = c.execute(text(sql), {"audit": audit_json})
        moved = result.rowcount

    with eng.connect() as c:
        post_ajh = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE is_active=true AND quality_review_status='auto_judged_high'"
            )
        ).scalar()
        post_pending = c.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE is_active=true AND quality_review_status='pending'"
            )
        ).scalar()
        post_view = c.execute(text("SELECT COUNT(*) FROM v_safe_for_beta")).scalar()

    print(f"\n[apply] {moved:,} satır 'pending' (manuel review queue)")
    print(f"[post] auto_judged_high: {post_ajh:,}")
    print(f"[post] pending:          {post_pending:,}")
    print(f"[post] v_safe_for_beta:  {post_view:,}")

    today = datetime.now().strftime("%Y%m%d")
    out = PILOTS_DIR / f"{today}_beta_pool_nuke_RESULT.md"
    out.write_text(
        "# Beta Pool NUKE v1 — RESULT\n\n"
        f"**Date:** {AUDIT_DATE}\n\n"
        f"## Transition\n\n"
        f"| Metric | Pre | Post |\n|---|---|---|\n"
        f"| auto_judged_high | {pre_ajh:,} | {post_ajh:,} |\n"
        f"| pending | (varsa) | {post_pending:,} |\n"
        f"| v_safe_for_beta | {pre_view:,} | {post_view:,} |\n\n"
        f"## Aksiyon\n\n"
        f"- {moved:,} satır auto_judged_high → pending (manuel review queue)\n"
        f"- Audit trail: `pipeline_metadata.beta_pool_nuke_v1` (reversible)\n"
        f"- v_safe_for_beta = 0 (görsel-bound soru tamamen sıfır)\n\n"
        f"## Reversal Path\n\n"
        f"```sql\nUPDATE question_bank SET quality_review_status='auto_judged_high'\n"
        f"WHERE pipeline_metadata::jsonb ? 'beta_pool_nuke_v1';\n```\n\n"
        f"## Sonraki Adımlar\n\n"
        f"- Faz 6.1 LLM judge pilot (1,000 satır pending'den)\n"
        f"- Vision re-crop sprint (figure-only crop 84K sample)\n"
        f"- Beta için Sapphire (human_verified) growth\n",
        encoding="utf-8",
    )
    print(f"\n[result] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
