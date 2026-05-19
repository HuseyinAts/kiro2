#!/usr/bin/env python3
"""
Audit + classify NEAR (n-1 of n options match) rows.

For each NEAR row, examine the SINGLE non-matching option pair:
  - If DB option and JSONL option are EDIT-DISTANCE close → encoding artifact (KEEP)
  - If completely different → real different question (ROLLBACK to NULL)

This refines the 7,302 NEAR classification into truly correct vs wrong.
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


def levenshtein(a, b, max_dist=10):
    """Edit distance, capped at max_dist for performance."""
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    if abs(len(a) - len(b)) > max_dist:
        return max_dist + 1
    if len(a) > len(b):
        a, b = b, a
    prev = list(range(len(a) + 1))
    for i, ch_b in enumerate(b):
        curr = [i + 1]
        for j, ch_a in enumerate(a):
            cost = 0 if ch_a == ch_b else 1
            curr.append(min(curr[-1] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
        if min(prev) > max_dist:
            return max_dist + 1
    return prev[-1]


# Load gemini crop → options
print("[load] gemini crop_file → options...")
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
            gem_by_crop[crop] = {
                "A": _norm_opt(sec.get("A", "")),
                "B": _norm_opt(sec.get("B", "")),
                "C": _norm_opt(sec.get("C", "")),
                "D": _norm_opt(sec.get("D", "")),
                "E": _norm_opt(sec.get("E", "")),
            }
print(f"[indexed] {len(gem_by_crop):,} crops\n")

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Pull all crop-level HAS-image rows with options
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
print(f"[scan] {len(rows):,} crop-level rows with full options\n")

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()

# Classify NEAR cases (4/5 match) and analyze the single mismatch
near_kept = []  # encoding artifact — KEEP
near_rollback = []  # real different — ROLLBACK
stats = Counter()

for r in rows:
    url = r.question_image_url
    fname = url.split("/")[-1] if url else ""
    gem_opts = gem_by_crop.get(fname)
    if not gem_opts:
        continue

    db_opts = {
        "A": _norm_opt(r.option_a or ""),
        "B": _norm_opt(r.option_b or ""),
        "C": _norm_opt(r.option_c or ""),
        "D": _norm_opt(r.option_d or ""),
        "E": _norm_opt(r.option_e or ""),
    }

    # Compute match
    matches = 0
    non_empty = 0
    mismatch_pairs = []
    for k in "ABCDE":
        d = db_opts[k]
        j = gem_opts[k]
        if not d or not j:
            continue
        non_empty += 1
        if d == j:
            matches += 1
        else:
            mismatch_pairs.append((k, d, j))

    if non_empty < 5 or matches != non_empty - 1:
        continue  # not NEAR (4/5)

    # Single mismatch pair
    if len(mismatch_pairs) != 1:
        continue
    k, d, j = mismatch_pairs[0]
    # Edit-distance analysis
    edit = levenshtein(d, j, max_dist=8)
    # Length-normalized edit
    max_len = max(len(d), len(j))
    if max_len == 0:
        continue
    edit_ratio = edit / max_len

    if edit <= 2 or edit_ratio < 0.2:
        # very close → encoding artifact
        stats["KEEP_encoding_artifact"] += 1
        near_kept.append((r.id, k, d[:25], j[:25], edit))
    elif edit <= 5 or edit_ratio < 0.4:
        # moderate diff → uncertain, lean KEEP
        stats["KEEP_minor_diff"] += 1
        near_kept.append((r.id, k, d[:25], j[:25], edit))
    else:
        # large diff → real different option
        stats["ROLLBACK_real_diff"] += 1
        near_rollback.append((r.id, k, d[:30], j[:30], edit))

print("[NEAR analysis] processed rows")
for k, v in stats.most_common():
    print(f"  {k}: {v:,}")

print(f"\nKEEP (encoding/minor): {len(near_kept):,}")
print(f"ROLLBACK (real diff):  {len(near_rollback):,}")

print("\n[KEEP examples]")
for ex in near_kept[:5]:
    print(f"  {ex[0][:8]} opt{ex[1]} db={ex[2]!r:30s} jsonl={ex[3]!r:30s} edit={ex[4]}")

print("\n[ROLLBACK examples]")
for ex in near_rollback[:5]:
    print(f"  {ex[0][:8]} opt{ex[1]} db={ex[2]!r:35s} jsonl={ex[3]!r:35s} edit={ex[4]}")

if args.apply and near_rollback:
    print(f"\n[apply] Rollback {len(near_rollback):,} satır...")
    ids = [x[0] for x in near_rollback]
    for i in range(0, len(ids), 1000):
        batch = ids[i : i + 1000]
        with eng.begin() as c:
            c.execute(
                sa_text("""
                UPDATE question_bank
                SET question_image_url = NULL,
                    pipeline_metadata = jsonb_set(
                        COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                        '{near_rollback_real_diff}',
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
                            "reason": "NEAR options match: single option real-diff (edit>5)",
                        }
                    ),
                },
            )
    print("[done]")
elif args.apply:
    print("\n[apply] no rollback candidates")
else:
    print("\n[dry-run] Use --apply to rollback")
