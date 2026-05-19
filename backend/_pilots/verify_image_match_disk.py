#!/usr/bin/env python3
"""Verify that ALL image_url values match an actual disk file."""

import os
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"

from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

tiers = [
    "image_match_metadata_v1",
    "image_match_jsonl_v2",
    "image_match_fuzzy_v3",
    "image_match_book_page_v4",
]

print("# Image URL → Disk Existence Verification\n")
print(f"CROPS_BASE: {CROPS_BASE}")
print()

grand_ok, grand_miss = 0, 0
miss_samples_by_tier: dict[str, list[tuple[str, str]]] = defaultdict(list)

for tier in tiers:
    sql = f"""
        SELECT id::text, question_image_url
        FROM question_bank
        WHERE pipeline_metadata::jsonb ? '{tier}'
          AND question_image_url IS NOT NULL
    """
    ok, missing = 0, 0
    miss_samples = []
    with eng.connect() as c:
        for row in c.execute(text(sql)):
            url = row.question_image_url
            # URL format: /static/crops/<book>/<file>.png
            if not url.startswith("/static/crops/"):
                missing += 1
                if len(miss_samples) < 5:
                    miss_samples.append((row.id, url))
                continue
            rel = url[len("/static/crops/") :]
            fpath = CROPS_BASE / rel
            if fpath.exists():
                ok += 1
            else:
                missing += 1
                if len(miss_samples) < 5:
                    miss_samples.append((row.id, url))
    grand_ok += ok
    grand_miss += missing
    miss_samples_by_tier[tier] = miss_samples

    pct = ok / (ok + missing) * 100 if (ok + missing) else 0
    print(f"  {tier}: ok={ok:,}, missing={missing:,}, exist_rate={pct:.2f}%")
    if miss_samples:
        for i, (qid, u) in enumerate(miss_samples[:3]):
            print(f"    miss sample {i}: {qid[:8]} → {u[:80]}")

print("\n## GRAND TOTAL")
print(f"  ok={grand_ok:,}, missing={grand_miss:,}")
total = grand_ok + grand_miss
print(f"  exist_rate={grand_ok / total * 100:.3f}%")
