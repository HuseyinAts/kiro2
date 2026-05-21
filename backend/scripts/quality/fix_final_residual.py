#!/usr/bin/env python3
"""
Final residual cleanup: rollback any HAS-image crop-level row where DB options
don't match crop's gemini options (including NEAR edit>3, PARTIAL, FAIL).

Single comprehensive script — no thresholds. If not PERFECT or NEAR(edit≤3) → rollback.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GEMINI = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"


def _norm_opt(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)[:40]


def lev(a, b, max_d=15):
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    if abs(len(a) - len(b)) > max_d:
        return max_d + 1
    if len(a) > len(b):
        a, b = b, a
    prev = list(range(len(a) + 1))
    for i, cb in enumerate(b):
        curr = [i + 1]
        for j, ca in enumerate(a):
            curr.append(
                min(curr[-1] + 1, prev[j + 1] + 1, prev[j] + (0 if ca == cb else 1))
            )
        prev = curr
    return prev[-1]


print("[load] gemini opts...")
gem_by_crop = {}
with GEMINI.open(encoding="utf-8") as f:
    for line in f:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        crop = d.get("crop_file", "")
        sec = d.get("secenekler", {}) or {}
        if crop:
            gem_by_crop[crop] = {k: _norm_opt(sec.get(k, "")) for k in "ABCDE"}

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
)

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()

# ALL crop-level rows, no option-null filter
with eng.connect() as c:
    rows = c.execute(
        sa_text("""
        SELECT id::text, question_image_url,
               option_a, option_b, option_c, option_d, option_e
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL AND question_image_url <> ''
          AND question_image_url NOT LIKE '%_PAGE.png'
          AND question_image_url NOT LIKE '%_LM%.png'
    """)
    ).fetchall()

to_rollback = []
verdicts = Counter()

for r in rows:
    fname = r.question_image_url.split("/")[-1]
    gem = gem_by_crop.get(fname)
    if not gem:
        verdicts["no_crop_in_gemini"] += 1
        continue
    db_opts = {k: _norm_opt(getattr(r, f"option_{k.lower()}") or "") for k in "ABCDE"}
    matches = non_empty = 0
    mismatches = []
    for k in "ABCDE":
        if db_opts[k] and gem[k]:
            non_empty += 1
            if db_opts[k] == gem[k]:
                matches += 1
            else:
                mismatches.append((db_opts[k], gem[k]))

    if non_empty < 3:
        verdicts["not_enough_opts"] += 1
        continue
    if matches == non_empty:
        verdicts["PERFECT"] += 1
        continue
    # Compute max edit distance among mismatches
    max_edit = 0
    for d, j in mismatches:
        e = lev(d, j)
        max_edit = max(max_edit, e)
    if matches == non_empty - 1 and non_empty >= 4 and max_edit <= 3:
        verdicts["NEAR_encoding(edit≤3)"] += 1
        continue
    # All others → ROLLBACK
    verdicts[f"ROLLBACK_match{matches}_non{non_empty}_maxedit{max_edit}"] += 1
    to_rollback.append(r.id)

print("[result]")
for k, v in verdicts.most_common(15):
    marker = (
        "✓"
        if k
        in {"PERFECT", "NEAR_encoding(edit≤3)", "not_enough_opts", "no_crop_in_gemini"}
        else "❌"
    )
    print(f"  {marker} {k:45s} {v:>6,}")

print(f"\nTotal to rollback: {len(to_rollback):,}")

if args.apply and to_rollback:
    print(f"\n[apply] rollback {len(to_rollback):,}...")
    for i in range(0, len(to_rollback), 1000):
        batch = to_rollback[i : i + 1000]
        with eng.begin() as c:
            c.execute(
                sa_text("""
                UPDATE question_bank
                SET question_image_url = NULL,
                    pipeline_metadata = jsonb_set(
                        COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                        '{final_residual_rollback}',
                        CAST(:audit AS jsonb),
                        TRUE
                    )::json,
                    updated_at = NOW()
                WHERE id::text = ANY(:ids)
                """),
                {
                    "ids": batch,
                    "audit": json.dumps(
                        {
                            "date": "2026-05-19",
                            "reason": "Final residual: not PERFECT and not NEAR_encoding(edit≤3)",
                        }
                    ),
                },
            )
    print("[done]")
else:
    print("\n[dry-run]")
