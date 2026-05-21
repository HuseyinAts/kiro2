#!/usr/bin/env python3
"""
Duplicate crop usage detection.

If same crop_file is assigned to multiple DB rows:
  - Only ONE row can be correct (1 image = 1 question)
  - The rest are wrong matches (option-collision FPs or text-match collisions)

Strategy:
  - For each crop used by N>1 rows, identify the BEST row to keep:
    - PERFECT options match (5/5) → strongest evidence
    - Highest book/page metadata consistency
    - Earliest assigned (legacy_pre_s157 typically older but less reliable)
  - Rollback the rest
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GEMINI = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"


def _norm_opt(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)[:40]


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _canon(s):
    return re.sub(r"\W+", "_", _fold(s or "")).strip("_")


# Load gemini crop → opts (skip if cached approach not used)
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
        book = d.get("book", "")
        page = d.get("page_num")
        if crop:
            gem_by_crop[crop] = {
                "book": book,
                "page": int(page) if page is not None else None,
                "opts": {k: _norm_opt(sec.get(k, "")) for k in "ABCDE"},
            }

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
)

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()

# Find duplicate-used crops (not _PAGE.png which intentionally shares pages)
print("[query] duplicate crop usage...")
with eng.connect() as c:
    dups = c.execute(
        sa_text("""
        SELECT question_image_url, COUNT(*) AS n
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL
          AND question_image_url NOT LIKE '%_PAGE.png'
        GROUP BY question_image_url
        HAVING COUNT(*) >= 2
        """)
    ).fetchall()
duplicate_urls = {r.question_image_url: r.n for r in dups}
print(f"[found] {len(duplicate_urls):,} crops used by 2+ rows")
print(f"[total rows on duplicated crops] ~{sum(duplicate_urls.values()):,}\n")

# Pull all rows for these crops
with eng.connect() as c:
    rows = c.execute(
        sa_text("""
        SELECT id::text, source_book, source_page, question_image_url,
               option_a, option_b, option_c, option_d, option_e,
               pipeline_metadata::text AS pm, created_at
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL
          AND question_image_url NOT LIKE '%_PAGE.png'
        """)
    ).fetchall()

groups = defaultdict(list)
for r in rows:
    if r.question_image_url in duplicate_urls:
        groups[r.question_image_url].append(r)


def score_row(r, gem):
    """Higher score = better candidate to keep."""
    fname = r.question_image_url.split("/")[-1]
    s = 0
    if not gem:
        return s
    # Book match
    db_canon = _canon(r.source_book or "")
    gem_canon = _canon(gem["book"])
    if db_canon == gem_canon:
        s += 100
    elif db_canon.startswith(gem_canon[:20]) or gem_canon.startswith(db_canon[:20]):
        s += 60
    # Page match
    if r.source_page == gem["page"]:
        s += 50
    # Options match
    db_opts = {k: _norm_opt(getattr(r, f"option_{k.lower()}") or "") for k in "ABCDE"}
    m = sum(
        1
        for k in "ABCDE"
        if db_opts[k] and gem["opts"][k] and db_opts[k] == gem["opts"][k]
    )
    s += m * 20
    return s


# For each duplicate group, keep the highest-score row, rollback rest
to_rollback = []
keep_count = 0
for url, group in groups.items():
    fname = url.split("/")[-1]
    gem = gem_by_crop.get(fname)
    scored = [(score_row(r, gem), r.id) for r in group]
    scored.sort(reverse=True)
    # Keep top 1
    keep_count += 1
    for sc, qid in scored[1:]:
        to_rollback.append(qid)

print("[plan]")
print(f"  Keep top-scored row per crop: {keep_count:,}")
print(f"  Rollback: {len(to_rollback):,}")

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
                        '{duplicate_crop_rollback}',
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
                            "reason": "Same crop assigned to multiple DB rows — kept highest-score, rolled back rest",
                        }
                    ),
                },
            )
        if (i // 1000 + 1) % 10 == 0:
            print(f"  batch {i // 1000 + 1}")
    print("[done]")
else:
    print("\n[dry-run] Pass --apply to rollback")
