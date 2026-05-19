#!/usr/bin/env python3
"""
PERFECT rows metadata consistency audit + fix.

PERFECT (5/5 options match) → URL crop IS this question content (verified).
Audit metadata fields:
  1. source_book canonical == URL book_dir canonical
  2. source_page == URL filename page
  3. correct_answer is valid letter (A-E)

Mismatch handling:
  - If image is verified (PERFECT) but metadata differs → UPDATE metadata to URL truth
    (URL came from gemini OCR which is the content-aligned source)
  - For correct_answer: if missing/invalid, flag but don't auto-fix (needs answer key)
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


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _canon(s):
    return re.sub(r"\W+", "_", _fold(s or "")).strip("_")


def book_sim(a, b):
    fa, fb = _canon(a), _canon(b)
    if not fa or not fb:
        return 0.0
    if fa == fb:
        return 1.0
    short = min(len(fa), len(fb))
    if fa.startswith(fb[:short]) or fb.startswith(fa[:short]):
        return min(short / max(len(fa), len(fb)), 1.0)
    ta = set(re.findall(r"[a-z0-9]{3,}", fa))
    tb = set(re.findall(r"[a-z0-9]{3,}", fb))
    return len(ta & tb) / len(ta | tb) if (ta and tb) else 0.0


print("[load] gemini crops + opts...")
gem_by_crop = {}
with GEMINI.open(encoding="utf-8") as f:
    for line in f:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        crop = d.get("crop_file", "")
        book = d.get("book", "")
        page = d.get("page_num")
        sec = d.get("secenekler", {}) or {}
        if crop:
            gem_by_crop[crop] = {
                "book": book,
                "page": int(page) if page is not None else None,
                "opts": {k: _norm_opt(sec.get(k, "")) for k in "ABCDE"},
            }
print(f"[indexed] {len(gem_by_crop):,}\n")

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
        SELECT id::text, source_book, source_page, question_image_url, correct_answer,
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

# Filter to PERFECT only (5/5 options match)
perfect_rows = []
for r in rows:
    fname = r.question_image_url.split("/")[-1] if r.question_image_url else ""
    gem = gem_by_crop.get(fname)
    if not gem:
        continue
    db_opts = {k: _norm_opt(getattr(r, f"option_{k.lower()}") or "") for k in "ABCDE"}
    matches = sum(
        1
        for k in "ABCDE"
        if db_opts[k] and gem["opts"][k] and db_opts[k] == gem["opts"][k]
    )
    non_empty = sum(1 for k in "ABCDE" if db_opts[k] and gem["opts"][k])
    if matches == 5 and non_empty == 5:
        perfect_rows.append((r, fname, gem))
print(f"[PERFECT subset]: {len(perfect_rows):,}\n")

# Audit each PERFECT row
stats = Counter()
metadata_fixes = []  # (id, new_book, new_page) — UPDATE plan
answer_issues = []
samples = {"book_mismatch": [], "page_mismatch": [], "answer_invalid": []}

VALID_ANS = {"A", "B", "C", "D", "E"}

for r, fname, gem in perfect_rows:
    # URL parsing for page
    m = re.search(r"_p(\d+)_q(\d+)\.", fname)
    if not m:
        stats["INVALID_URL"] += 1
        continue
    url_page = int(m.group(1))
    url_book_dir = r.question_image_url.split("/")[-2]

    # Book consistency
    db_book = r.source_book or ""
    url_book = gem["book"]
    book_sim_score = book_sim(db_book, url_book)
    book_mismatch = book_sim_score < 0.5

    # Page consistency
    page_mismatch = r.source_page != url_page

    # Answer validity
    ans = (r.correct_answer or "").strip().upper()
    ans_invalid = ans not in VALID_ANS

    if book_mismatch or page_mismatch:
        stats["METADATA_MISMATCH"] += 1
        new_book = url_book if book_mismatch else r.source_book
        new_page = url_page if page_mismatch else r.source_page
        metadata_fixes.append(
            (r.id, new_book, int(new_page), book_mismatch, page_mismatch)
        )
        if book_mismatch and len(samples["book_mismatch"]) < 4:
            samples["book_mismatch"].append(
                f"  {r.id[:8]} db_book={db_book[:35]!r} → url_book={url_book[:35]!r} (sim={book_sim_score:.2f})"
            )
        if page_mismatch and len(samples["page_mismatch"]) < 4:
            samples["page_mismatch"].append(
                f"  {r.id[:8]} db_page={r.source_page} → url_page={url_page}"
            )
    else:
        stats["METADATA_OK"] += 1

    if ans_invalid:
        stats["ANSWER_INVALID"] += 1
        answer_issues.append(r.id)
        if len(samples["answer_invalid"]) < 3:
            samples["answer_invalid"].append(f"  {r.id[:8]} correct_answer={ans!r}")

print("[result]")
for k, v in stats.most_common():
    print(f"  {k}: {v:,}")

print(f"\n[metadata fixes proposed]: {len(metadata_fixes):,}")
print(f"[answer issues]: {len(answer_issues):,}")

print("\n[samples — book mismatch]")
for s in samples["book_mismatch"]:
    print(s)
print("\n[samples — page mismatch]")
for s in samples["page_mismatch"]:
    print(s)
print("\n[samples — answer invalid]")
for s in samples["answer_invalid"]:
    print(s)

if args.apply and metadata_fixes:
    # PERFECT options + METADATA_MISMATCH = OPTION COLLISION FALSE POSITIVE
    # Image shows a different question that just happens to have same options
    # (e.g., generic "Yalnız I/II/III, I ve II/III" arrangement)
    # → ROLLBACK URL (trust DB metadata, treat URL match as collision)
    print(f"\n[apply] Rollback {len(metadata_fixes):,} URL (option-collision FP)...")
    ids = [x[0] for x in metadata_fixes]
    for i in range(0, len(ids), 1000):
        batch = ids[i : i + 1000]
        with eng.begin() as c:
            c.execute(
                sa_text("""
                UPDATE question_bank
                SET question_image_url = NULL,
                    pipeline_metadata = jsonb_set(
                        COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                        '{perfect_options_collision_rollback}',
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
                            "reason": "PERFECT options match but book/page metadata diverges → option-collision FP",
                        }
                    ),
                },
            )
    print("[done]")
else:
    print("\n[dry-run] Pass --apply to rollback option-collision FPs")
