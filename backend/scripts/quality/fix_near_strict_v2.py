#!/usr/bin/env python3
"""
NEAR strict rollback v2: rollback ALL NEAR with edit ≥ 4.

Previous fix_near_classification.py used permissive OR logic:
  edit ≤ 5 OR ratio < 0.4 → keep

This left 336 rows with edit>5 (kept due to low ratio) and 665 borderline.

Strict v2: edit ≥ 4 → rollback (regardless of ratio).
This is safer for "hatasız" goal — kept only edit 1-3 (clear encoding artifacts).
"""

import argparse
import json
import os
import re
import sys
import unicodedata
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
ap.add_argument("--threshold", type=int, default=4)
args = ap.parse_args()

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
          AND option_a IS NOT NULL AND option_b IS NOT NULL
          AND option_c IS NOT NULL AND option_d IS NOT NULL AND option_e IS NOT NULL
        """)
    ).fetchall()

to_rollback = []
near_kept = 0
for r in rows:
    fname = r.question_image_url.split("/")[-1]
    gem = gem_by_crop.get(fname)
    if not gem:
        continue
    db_opts = {k: _norm_opt(getattr(r, f"option_{k.lower()}") or "") for k in "ABCDE"}
    matches = 0
    non_empty = 0
    mismatch = None
    for k in "ABCDE":
        if db_opts[k] and gem[k]:
            non_empty += 1
            if db_opts[k] == gem[k]:
                matches += 1
            else:
                mismatch = (db_opts[k], gem[k])

    if non_empty == 5 and matches == 4 and mismatch:
        d, j = mismatch
        e = lev(d, j)
        if e >= args.threshold:
            to_rollback.append(r.id)
        else:
            near_kept += 1

print(f"[result] NEAR strict (threshold edit>={args.threshold})")
print(f"  ROLLBACK: {len(to_rollback):,}")
print(f"  KEEP:     {near_kept:,}")

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
                        '{near_strict_v2_rollback}',
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
                            "reason": f"NEAR strict v2: 1 option edit_distance >= {args.threshold}",
                        }
                    ),
                },
            )
    print("[done]")
else:
    print("\n[dry-run]")
