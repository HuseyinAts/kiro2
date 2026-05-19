#!/usr/bin/env python3
"""Audit v10 (options hash) against v8 (text exact match) ground truth."""

import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
GEMINI_JSONL = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"


def _norm(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _opts_hash(a, b, c, d, e):
    parts = []
    for label, val in zip("ABCDE", (a, b, c, d, e)):
        n = _norm(val or "")
        if not n:
            return None
        parts.append(f"{label}={n}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]


print("[load] JSONL opts index...")
opts_idx = defaultdict(list)
with GEMINI_JSONL.open(encoding="utf-8") as f:
    for line in f:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        book = d.get("book", "")
        page = d.get("page_num")
        crop = d.get("crop_file", "")
        sec = d.get("secenekler", {}) or {}
        if not (book and page is not None and crop and isinstance(sec, dict)):
            continue
        h = _opts_hash(
            sec.get("A"), sec.get("B"), sec.get("C"), sec.get("D"), sec.get("E")
        )
        if h:
            opts_idx[h].append((book, int(page), crop))
print(f"[done] {len(opts_idx):,} unique hashes\n")

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Audit against v8 (text-exact, ground truth)
with eng.connect() as c:
    sample = c.execute(
        sa_text("""
        SELECT id::text, source_book,
               option_a, option_b, option_c, option_d, option_e,
               pipeline_metadata::jsonb->'image_match_gemini_flash_v8'->>'matched_crop' AS v8_crop
        FROM question_bank
        WHERE pipeline_metadata::jsonb ? 'image_match_gemini_flash_v8'
          AND option_a IS NOT NULL AND option_b IS NOT NULL
          AND option_c IS NOT NULL AND option_d IS NOT NULL AND option_e IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 500
    """)
    ).fetchall()
print(f"[sample] {len(sample)} v8-matched rows for audit\n")

stats = {
    "v10_proposes_same_as_v8": 0,
    "v10_proposes_different": 0,
    "v10_no_options_match": 0,
    "v10_ambiguous": 0,
}
diff_examples = []

for r in sample:
    h = _opts_hash(r.option_a, r.option_b, r.option_c, r.option_d, r.option_e)
    if not h:
        stats["v10_no_options_match"] += 1
        continue
    cands = opts_idx.get(h, [])
    if not cands:
        stats["v10_no_options_match"] += 1
        continue

    sb_folded = _fold(r.source_book or "")
    same_book = [c for c in cands if _fold(c[0]) == sb_folded]
    if len(same_book) == 1:
        proposed = same_book[0][2]
    elif same_book and len(same_book) > 1:
        stats["v10_ambiguous"] += 1
        continue
    elif len({_fold(b) for b, _, _ in cands}) == 1:
        proposed = cands[0][2]
    else:
        stats["v10_ambiguous"] += 1
        continue

    if proposed == r.v8_crop:
        stats["v10_proposes_same_as_v8"] += 1
    else:
        stats["v10_proposes_different"] += 1
        if len(diff_examples) < 5:
            diff_examples.append(f"  v10={proposed} | v8={r.v8_crop}")

print("[result]")
for k, v in stats.items():
    print(f"  {k}: {v}")

verifiable = stats["v10_proposes_same_as_v8"] + stats["v10_proposes_different"]
if verifiable:
    acc = stats["v10_proposes_same_as_v8"] / verifiable * 100
    print(f"\n[accuracy on verifiable={verifiable}]")
    print(f"  v10 == v8: {acc:.1f}%")

if diff_examples:
    print("\n[differences]")
    for e in diff_examples:
        print(e)
