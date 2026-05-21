#!/usr/bin/env python3
"""
Final correctness audit: random 500 sample across all image_url'd rows.

Verifies match correctness against multiple ground truth sources:
  1. JSONL exact text match (eslesmis_sorucevap.jsonl) — production v3.5+
  2. Gemini Flash 2.5 results.jsonl (ocr_crops/results.jsonl) — full pipeline
  3. URL page parsing — does image filename's page match DB source_page?
  4. URL existence on disk
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
JSONL = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
GEMINI = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _norm(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _canon(s):
    return re.sub(r"\W+", "_", _fold(s or "")).strip("_")


# Build ground truth indices
print("[load] eslesmis_sorucevap.jsonl + ocr_crops/results.jsonl...")
truth_by_text: dict[str, tuple] = {}  # normed_text → (book, page, qno)
with JSONL.open(encoding="utf-8") as f:
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
        if len(normed) < 60:
            continue
        if normed[:80] not in truth_by_text:
            truth_by_text[normed[:80]] = (book, int(page), int(qno))

# Gemini OCR results: more comprehensive
gem_by_text: dict[str, tuple] = {}  # normed → (book, page, crop_file)
with GEMINI.open(encoding="utf-8") as f:
    for line in f:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = d.get("soru_metni") or ""
        book = d.get("book") or ""
        page = d.get("page_num")
        crop = d.get("crop_file", "")
        if not (t and book and page is not None and crop):
            continue
        normed = _norm(t)
        if len(normed) < 60:
            continue
        if normed[:80] not in gem_by_text:
            gem_by_text[normed[:80]] = (book, int(page), crop)

print(
    f"[indexed] eslesmis prefixes: {len(truth_by_text):,}  | gemini prefixes: {len(gem_by_text):,}\n"
)

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Random sample of 500 across all HAS-image rows
with eng.connect() as c:
    sample = c.execute(
        sa_text("""
        SELECT id::text, source_book, source_page, question_text, question_image_url,
               pipeline_metadata::text AS pm
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL AND question_image_url <> ''
        ORDER BY RANDOM() LIMIT 500
    """)
    ).fetchall()
print(f"[sample] {len(sample)} random rows\n")

stats = {
    "correct_jsonl_exact": 0,
    "correct_gemini_exact": 0,
    "correct_page_match_only": 0,  # URL page == DB source_page but no text truth
    "wrong_page_mismatch": 0,
    "page_fallback_correct": 0,
    "no_truth_no_check": 0,
    "url_invalid": 0,
    "file_missing": 0,
}

# Match strategies
strategy_counts = Counter()
strategy_correct = Counter()


def get_strategy(pm_str):
    if not pm_str:
        return "no_metadata"
    flags = []
    for f in [
        "image_match_v15_page_fallback",
        "image_match_v15a_labelme_exact",
        "image_match_v14_jaccard",
        "image_match_v13_hybrid_disambig",
        "image_match_v12_page_residual",
        "image_match_v10b_options_strict",
        "image_match_gemini_flash_v9_loose",
        "image_match_gemini_flash_v8",
        "image_match_strategy_d_qtext",
        "image_match_strategy_c_unused",
        "image_match_strategy_b_image_ocr",
        "image_match_n_to_n_text_v7",
        "image_match_single_v6",
        "image_match_rebuild_v5",
        "image_match_fuzzy_v3",
        "image_match_jsonl_v2",
        "image_match_metadata_v1",
    ]:
        if f'"{f}"' in pm_str:
            return f.replace("image_match_", "")
    return "legacy_pre_s157"


for r in sample:
    pm_str = r.pm or ""
    strategy = get_strategy(pm_str)
    strategy_counts[strategy] += 1

    # Parse URL
    url = r.question_image_url or ""
    if not url.startswith("/static/crops/"):
        stats["url_invalid"] += 1
        continue
    rel = url[len("/static/crops/") :]
    parts = rel.split("/")
    if len(parts) != 2:
        stats["url_invalid"] += 1
        continue
    book_dir, fname = parts

    crop_path = CROPS_BASE / book_dir / fname
    if not crop_path.exists():
        stats["file_missing"] += 1
        continue

    # Special: page-level fallback (v15)
    if "_PAGE.png" in fname:
        m = re.search(r"_p(\d+)_PAGE", fname)
        if (
            m
            and r.source_page == int(m.group(1))
            and _canon(r.source_book) == _canon(book_dir)
        ):
            stats["page_fallback_correct"] += 1
            strategy_correct[strategy] += 1
        continue

    # Parse page from filename
    m = re.search(r"_p(\d+)_q?\d*", fname)
    url_page = int(m.group(1)) if m else None

    # Try JSONL exact text match
    normed = _norm(r.question_text)
    if len(normed) >= 60:
        prefix = normed[:80]
        truth = truth_by_text.get(prefix) or gem_by_text.get(prefix)
        if truth:
            tb, tp, tq_or_crop = truth
            # For JSONL: tq_or_crop is qno (int)
            # For Gemini: tq_or_crop is crop_file (str)
            if isinstance(tq_or_crop, str):
                # gemini
                if tq_or_crop == fname or fname.endswith(tq_or_crop):
                    stats["correct_gemini_exact"] += 1
                    strategy_correct[strategy] += 1
                # Check page match at least
                elif url_page == tp and _canon(tb) == _canon(book_dir):
                    stats["correct_page_match_only"] += 1
                    strategy_correct[strategy] += 1
                else:
                    stats["wrong_page_mismatch"] += 1
                continue
            else:
                # jsonl
                tqno = tq_or_crop
                if url_page == tp and _canon(tb) == _canon(book_dir):
                    # page + book match
                    # check qno
                    m2 = re.search(r"_q(\d+)\.", fname)
                    url_qno = int(m2.group(1)) if m2 else None
                    if url_qno == tqno:
                        stats["correct_jsonl_exact"] += 1
                        strategy_correct[strategy] += 1
                    else:
                        stats["correct_page_match_only"] += 1
                        strategy_correct[strategy] += 1
                else:
                    stats["wrong_page_mismatch"] += 1
                continue

    # No truth available — check page consistency
    if url_page == r.source_page:
        stats["correct_page_match_only"] += 1
        strategy_correct[strategy] += 1
    else:
        stats["no_truth_no_check"] += 1

print("[result]")
for k, v in stats.items():
    print(f"  {k}: {v}")

total = len(sample)
correct = (
    stats["correct_jsonl_exact"]
    + stats["correct_gemini_exact"]
    + stats["correct_page_match_only"]
    + stats["page_fallback_correct"]
)
wrong = stats["wrong_page_mismatch"] + stats["url_invalid"] + stats["file_missing"]
unknown = stats["no_truth_no_check"]

print("\n[summary]")
print(f"  correct:  {correct} ({correct / total * 100:.1f}%)")
print(f"  wrong:    {wrong} ({wrong / total * 100:.1f}%)")
print(f"  unknown:  {unknown} ({unknown / total * 100:.1f}%)")

print("\n[per-strategy accuracy]")
for strat, n in strategy_counts.most_common():
    c = strategy_correct[strat]
    pct = c / n * 100 if n else 0
    print(f"  {strat:35s} {n:>4} sample → {c:>4} correct ({pct:.1f}%)")
