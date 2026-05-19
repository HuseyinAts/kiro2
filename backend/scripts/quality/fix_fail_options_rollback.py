#!/usr/bin/env python3
"""
Rollback rows where DB options FAIL match with crop's JSONL options.

After previous cleanups:
  - NEAR rollback (real-diff): 558 done
  - PERFECT-collision rollback: 964 done
  - Duplicate crop rollback: 24,665 done

Now: For remaining HAS-image crop-level rows, identify FAIL (<50% options match)
and rollback. These have DB options ≠ crop's content → wrong assignment.
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


print("[load] gemini crop opts...")
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
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
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
print(f"[scan] {len(rows):,} crop-level rows\n")

fail_ids = []
partial_ids = []
verdict_counts = Counter()

for r in rows:
    fname = r.question_image_url.split("/")[-1]
    gem_opts = gem_by_crop.get(fname)
    if not gem_opts:
        verdict_counts["NO_CROP_IN_GEMINI"] += 1
        continue

    db_opts = {k: _norm_opt(getattr(r, f"option_{k.lower()}") or "") for k in "ABCDE"}
    matches = 0
    non_empty = 0
    for k in "ABCDE":
        if db_opts[k] and gem_opts[k]:
            non_empty += 1
            if db_opts[k] == gem_opts[k]:
                matches += 1

    if non_empty < 3:
        verdict_counts["NOT_ENOUGH_OPTIONS"] += 1
        continue

    if matches == non_empty:
        verdict_counts["PERFECT"] += 1
    elif matches >= non_empty - 1 and non_empty >= 4:
        verdict_counts["NEAR"] += 1
    elif matches >= non_empty / 2:
        verdict_counts["PARTIAL"] += 1
        partial_ids.append(r.id)
    else:
        verdict_counts["FAIL"] += 1
        fail_ids.append(r.id)

print("[result]")
for k, v in verdict_counts.most_common():
    print(f"  {k}: {v:,}")
print(f"\nFAIL rollback candidates:    {len(fail_ids):,}")
print(f"PARTIAL rollback candidates: {len(partial_ids):,}")

target = fail_ids + partial_ids
print(f"Total to rollback (FAIL + PARTIAL): {len(target):,}")

if args.apply and target:
    print(f"\n[apply] rollback {len(target):,} satır...")
    for i in range(0, len(target), 1000):
        batch = target[i : i + 1000]
        with eng.begin() as c:
            c.execute(
                sa_text("""
                UPDATE question_bank
                SET question_image_url = NULL,
                    pipeline_metadata = jsonb_set(
                        COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                        '{fail_options_rollback}',
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
                            "reason": "DB options FAIL match (<50%) with crop's JSONL options — wrong crop assignment",
                        }
                    ),
                },
            )
        if (i // 1000 + 1) % 10 == 0:
            print(f"  batch {i // 1000 + 1}")
    print("[done]")
else:
    print("\n[dry-run] Pass --apply to rollback")
