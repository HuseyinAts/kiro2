#!/usr/bin/env python3
"""
Strategy H Audit + Apply: (book, source_page, q_index_in_page) → JSONL unique_id.

Hypothesis: DB pipeline_metadata.ai_extras.q_index_in_page maps directly to
JSONL question_index for the same (book, page). They came from same Gemini
Flash 2.5 OCR run.

Audit method:
  - Take 100 NULL rows that ALREADY have image_url (control group)
  - Wait — they don't have image_url. Take rows that just got matched via v8/v9
  - Compare proposed crop (via H) vs actual matched crop

Actually simpler: just sample 50 NULL rows, try H lookup, dry-run only,
print proposed crop_file. Then take 50 audited rows where v8 exact-matched,
compare v8's crop with H's proposed crop.

Method 2: validate by checking if H's proposed crop_file matches v8 result
for rows where both apply.
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
GEMINI_JSONL = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"


def _fold(s: str) -> str:
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


print(f"[load] {GEMINI_JSONL.name}...")
# Index: (book_folded, page) → list of (question_index, crop_file)
page_idx: dict[tuple[str, int], list[tuple[int, str]]] = defaultdict(list)
with GEMINI_JSONL.open(encoding="utf-8") as f:
    for line in f:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        book = d.get("book", "")
        page = d.get("page_num")
        qi = d.get("question_index")
        crop = d.get("crop_file", "")
        if not (book and page is not None and qi is not None and crop):
            continue
        page_idx[(_fold(book), int(page))].append((int(qi), crop))
print(f"[indexed] {len(page_idx):,} (book, page) groups\n")

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# AUDIT METHOD: For rows that ALREADY got matched via v8 (which is exact text match,
# considered ground truth), compare H's proposed crop vs v8's actual crop.
print("[audit] cross-checking H proposal against v8 ground truth matches...")
with eng.connect() as c:
    sample = c.execute(
        sa_text("""
        SELECT
          id::text,
          source_book,
          source_page,
          (pipeline_metadata::jsonb->'ai_extras'->>'q_index_in_page')::int AS qip,
          question_image_url,
          pipeline_metadata::jsonb->'image_match_gemini_flash_v8'->>'matched_crop' AS v8_crop
        FROM question_bank
        WHERE pipeline_metadata::jsonb ? 'image_match_gemini_flash_v8'
          AND pipeline_metadata::jsonb->'ai_extras'->>'q_index_in_page' IS NOT NULL
          AND source_page IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 500
    """)
    ).fetchall()

print(f"[sample] {len(sample)} v8-matched rows with qip + source_page\n")

stats = {
    "h_matches_v8_exact": 0,
    "h_matches_v8_shifted_plus1": 0,
    "h_matches_v8_shifted_minus1": 0,
    "h_no_jsonl_page": 0,
    "h_no_qip_match": 0,
    "h_proposed_wrong": 0,
}
mismatch_examples = []

for r in sample:
    sb_folded = _fold(r.source_book or "")
    page_cands = page_idx.get((sb_folded, int(r.source_page)), [])
    if not page_cands:
        stats["h_no_jsonl_page"] += 1
        continue

    # Check direct match
    direct = None
    plus1 = None
    minus1 = None
    for qi, crop in page_cands:
        if qi == r.qip:
            direct = crop
        if qi == r.qip + 1:
            plus1 = crop
        if qi == r.qip - 1:
            minus1 = crop

    v8 = r.v8_crop
    if direct == v8:
        stats["h_matches_v8_exact"] += 1
    elif plus1 == v8:
        stats["h_matches_v8_shifted_plus1"] += 1
    elif minus1 == v8:
        stats["h_matches_v8_shifted_minus1"] += 1
    elif direct is None:
        stats["h_no_qip_match"] += 1
    else:
        stats["h_proposed_wrong"] += 1
        if len(mismatch_examples) < 5:
            mismatch_examples.append(f"  qip={r.qip} → H proposes={direct} but v8={v8}")

print("[result]")
total = sum(stats.values())
for k, v in stats.items():
    pct = (v / total * 100) if total else 0
    print(f"  {k}: {v} ({pct:.1f}%)")

correct_count = (
    stats["h_matches_v8_exact"]
    + stats["h_matches_v8_shifted_plus1"]
    + stats["h_matches_v8_shifted_minus1"]
)
verifiable = correct_count + stats["h_proposed_wrong"]
if verifiable:
    acc_exact = stats["h_matches_v8_exact"] / verifiable * 100
    acc_with_shift = correct_count / verifiable * 100
    print(f"\n[accuracy on verifiable={verifiable}]")
    print(f"  exact qip==question_index: {acc_exact:.1f}%")
    print(f"  with shift ±1 fallback:    {acc_with_shift:.1f}%")

if mismatch_examples:
    print("\n[mismatch examples]")
    for e in mismatch_examples:
        print(e)
