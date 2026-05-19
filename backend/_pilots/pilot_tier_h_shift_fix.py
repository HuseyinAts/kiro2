#!/usr/bin/env python3
"""
PILOT: Tier H Rollback Shift-Fix audit.

Hypothesis: Tier H was rolled back because DB q_index_in_page is 0-based but
disk filename qNN is 1-based. If we shift +1 from qip, we get the correct
disk filename.

Audit:
  - Sample 100 NULL rows with tier_h_rollback.original_crop_file
  - For each, check disk has shifted crop file
  - Cross-verify against JSONL truth (where available)
  - Measure shift-by-1 accuracy
"""

import json
import os
import random
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

random.seed(42)
PROJECT_ROOT = Path(__file__).parent.parent.parent
JSONL_PATH = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _norm(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


print("[load] JSONL prefix index...")
jsonl_idx = defaultdict(list)
with JSONL_PATH.open(encoding="utf-8") as f:
    for line in f:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = d.get("text") or ""
        book = d.get("book_name", "")
        page = d.get("page_number")
        qno = d.get("question_number")
        if not (t and book and page and qno):
            continue
        normed = _norm(t)
        if len(normed) < 50:
            continue
        jsonl_idx[normed[:60]].append((book, int(page), int(qno)))
print(f"[done] {len(jsonl_idx):,} unique prefixes\n")

from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

with eng.connect() as c:
    rows = c.execute(
        text("""
        SELECT
          id::text AS id,
          source_book,
          question_text,
          pipeline_metadata::jsonb->'ai_extras'->>'q_index_in_page' AS qip,
          pipeline_metadata::jsonb->'tier_h_rollback'->>'original_crop_file' AS orig_crop,
          pipeline_metadata::jsonb->>'request_key' AS rk
        FROM question_bank
        WHERE is_active=true
          AND (question_image_url IS NULL OR question_image_url='')
          AND pipeline_metadata::jsonb->'tier_h_rollback' ? 'original_crop_file'
        """)
    ).fetchall()
print(f"[total] {len(rows):,} NULL rows with tier_h_rollback.original_crop_file")

# Sample 100
sample = random.sample(list(rows), min(100, len(rows)))
print(f"[sample] {len(sample)}\n")

stats = {
    "shift_qip_plus_1_correct": 0,
    "shift_qip_plus_1_wrong": 0,
    "orig_already_correct": 0,
    "no_jsonl_truth": 0,
    "orig_unparseable": 0,
    "disk_missing_shifted": 0,
    "disk_missing_orig": 0,
}

examples_correct = []
examples_wrong = []

for r in sample:
    orig = r.orig_crop or ""
    m = re.search(r"^(.+?)_p(\d{4})_q(\d+)\.(png|jpg)$", orig)
    if not m:
        stats["orig_unparseable"] += 1
        continue
    book_dir, page_s, qno_orig_s, ext = m.group(1), m.group(2), m.group(3), m.group(4)
    page = int(page_s)
    qno_orig = int(qno_orig_s)
    try:
        qip = int(r.qip) if r.qip is not None else None
    except (ValueError, TypeError):
        qip = None

    # Lookup JSONL truth
    normed = _norm(r.question_text)
    if len(normed) < 50:
        stats["no_jsonl_truth"] += 1
        continue
    cands = jsonl_idx.get(normed[:60], [])
    truth_qno = None
    sb_folded = _fold(r.source_book or "")
    for tb, tp, tq in cands:
        if _fold(tb) == sb_folded and tp == page:
            truth_qno = tq
            break
    if truth_qno is None:
        for tb, tp, tq in cands:
            if _fold(tb) == sb_folded:
                truth_qno = tq
                break
    if truth_qno is None:
        stats["no_jsonl_truth"] += 1
        continue

    # Hypothesis 1: original crop qno was correct (no shift)
    # Hypothesis 2: shift +1 (qip+1) gives correct qno
    shifted = qno_orig + 1 if qip is not None and qno_orig == qip else qno_orig

    # Check shifted file existence
    book_dir_path = CROPS_BASE / book_dir
    shifted_name = f"{book_dir}_p{page:04d}_q{shifted:02d}.{ext}"
    orig_name = f"{book_dir}_p{page:04d}_q{qno_orig:02d}.{ext}"

    if not (book_dir_path / shifted_name).exists():
        stats["disk_missing_shifted"] += 1
        continue

    # Compare
    if truth_qno == shifted:
        stats["shift_qip_plus_1_correct"] += 1
        if len(examples_correct) < 3:
            examples_correct.append(
                f"  {r.id[:8]} qip={qip} orig=q{qno_orig:02d} shift=q{shifted:02d} truth=q{truth_qno} ✓"
            )
    elif truth_qno == qno_orig:
        stats["orig_already_correct"] += 1
    else:
        stats["shift_qip_plus_1_wrong"] += 1
        if len(examples_wrong) < 3:
            examples_wrong.append(
                f"  {r.id[:8]} qip={qip} orig=q{qno_orig:02d} shift=q{shifted:02d} truth=q{truth_qno} ✗"
            )

print("[result]")
total_verifiable = (
    stats["shift_qip_plus_1_correct"]
    + stats["shift_qip_plus_1_wrong"]
    + stats["orig_already_correct"]
)
for k, v in stats.items():
    print(f"  {k}: {v}")
print()
if total_verifiable:
    shift_acc = stats["shift_qip_plus_1_correct"] / total_verifiable * 100
    orig_acc = stats["orig_already_correct"] / total_verifiable * 100
    print(f"Shift +1 accuracy: {shift_acc:.1f}%")
    print(f"Original (no shift) accuracy: {orig_acc:.1f}%")
    print(f"Total verifiable: {total_verifiable}")

print("\n[examples correct]")
for e in examples_correct:
    print(e)
print("\n[examples wrong]")
for e in examples_wrong:
    print(e)
