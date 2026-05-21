#!/usr/bin/env python3
"""
Deep dive into wrong cases: separate REAL wrongs from canonicalization artifacts.
"""

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
JSONL = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
GEMINI = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"


def _norm(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


# Build ground truth: text → ALL (book, page, crop)
print("[load] truth indices...")
gem_idx = defaultdict(list)
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
        if len(normed) < 50:
            continue
        gem_idx[normed[:100]].append((book, int(page), crop))

jsonl_idx = defaultdict(list)
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
        if len(normed) < 50:
            continue
        jsonl_idx[normed[:100]].append((book, int(page), int(qno)))
print(f"[indexed] gemini={len(gem_idx):,}  eslesmis={len(jsonl_idx):,}\n")

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Get rows where audit found "wrong" — large sample to catch them
with eng.connect() as c:
    sample = c.execute(
        sa_text("""
        SELECT id::text, source_book, source_page, question_text, question_image_url
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL AND question_image_url <> ''
          AND question_text IS NOT NULL
          AND LENGTH(question_text) >= 80
        ORDER BY RANDOM() LIMIT 3000
    """)
    ).fetchall()


def parse_url(url):
    if not url or not url.startswith("/static/crops/"):
        return None, None, None, None
    rel = url[len("/static/crops/") :]
    parts = rel.split("/")
    if len(parts) != 2:
        return None, None, None, None
    book_dir, fname = parts
    m = re.search(r"_p(\d+)_(q\d+|PAGE|LM\d+)\.", fname)
    if not m:
        return book_dir, fname, None, None
    page = int(m.group(1))
    suffix = m.group(2)
    qno = int(suffix[1:]) if suffix.startswith("q") else suffix
    return book_dir, fname, page, qno


def book_similarity(a, b):
    """Permissive similarity: are these the SAME book just spelled differently?"""
    fa = _norm(a)
    fb = _norm(b)
    if not fa or not fb:
        return 0
    short = min(len(fa), len(fb))
    if short < 6:
        return 0
    # Check if shorter is prefix of longer (truncation case)
    if fa.startswith(fb[:short]) or fb.startswith(fa[:short]):
        return min(short / max(len(fa), len(fb)), 1.0)
    # Token overlap
    ta = set(re.findall(r"[a-z0-9]{3,}", fa))
    tb = set(re.findall(r"[a-z0-9]{3,}", fb))
    if not ta or not tb:
        return 0
    return len(ta & tb) / len(ta | tb)


# Categorize wrongs
categories = Counter()
real_wrong = []
false_wrong = []
no_text_truth = 0

for r in sample:
    book_dir, fname, url_page, url_qno = parse_url(r.question_image_url)
    if not book_dir:
        categories["INVALID_URL"] += 1
        continue

    normed_t = _norm(r.question_text)[:100]
    gem_truths = gem_idx.get(normed_t, [])
    jsonl_truths = jsonl_idx.get(normed_t, [])

    if not gem_truths and not jsonl_truths:
        # No text truth → check page+book consistency
        if url_page == r.source_page and _norm(r.source_book) == _norm(book_dir):
            categories["NO_TRUTH_CONSISTENT"] += 1
        elif url_qno == "PAGE":
            # v15 fallback: trust if page matches
            if url_page == r.source_page:
                categories["NO_TRUTH_PAGE_FALLBACK_OK"] += 1
            else:
                categories["PAGE_FALLBACK_PAGE_MISMATCH"] += 1
        else:
            no_text_truth += 1
            categories["NO_TRUTH_NO_VERIFY"] += 1
        continue

    # Find best truth match (highest book similarity)
    best_truth_book = None
    best_sim = 0
    best_match = None
    for tb, tp, tcrop in gem_truths:
        sim = book_similarity(tb, book_dir)
        if sim > best_sim:
            best_sim = sim
            best_truth_book = tb
            best_match = (tb, tp, tcrop, "gemini")
    if not best_truth_book and jsonl_truths:
        for tb, tp, tq in jsonl_truths:
            sim = book_similarity(tb, book_dir)
            if sim > best_sim:
                best_sim = sim
                best_truth_book = tb
                best_match = (tb, tp, tq, "jsonl")

    if not best_match:
        categories["NO_SAME_BOOK_TRUTH"] += 1
        continue

    truth_book, truth_page, truth_id, truth_src = best_match

    # Different book OR same book?
    if best_sim < 0.5:
        # Different book - real cross-book error OR different edition
        categories["REAL_CROSS_BOOK"] += 1
        if len(real_wrong) < 8:
            real_wrong.append(
                {
                    "id": r.id[:8],
                    "url_book": book_dir[:50],
                    "truth_book": truth_book[:50],
                    "sim": f"{best_sim:.2f}",
                }
            )
        continue

    # Same book — check page
    if url_qno == "PAGE":
        # Page-level: only check page
        if url_page == truth_page:
            categories["PAGE_FALLBACK_OK_TRUTH"] += 1
        else:
            categories["PAGE_FALLBACK_WRONG_PAGE"] += 1
            if len(real_wrong) < 8:
                real_wrong.append(
                    {
                        "id": r.id[:8],
                        "url_book": book_dir[:40],
                        "url_page": url_page,
                        "truth_page": truth_page,
                        "kind": "page_fallback_wrong_page",
                    }
                )
    # Crop-level: check page AND crop/qno
    elif url_page == truth_page:
        if truth_src == "gemini" and truth_id == fname:
            categories["CROP_EXACT_OK"] += 1
        elif truth_src == "gemini":
            # Same book, same page, different crop within page
            categories["SAME_PAGE_DIFF_CROP"] += 1
        else:
            # jsonl: check qno
            m = re.search(r"_q(\d+)\.", fname)
            url_q = int(m.group(1)) if m else None
            if url_q == truth_id:
                categories["QNO_EXACT_OK"] += 1
            else:
                categories["SAME_PAGE_DIFF_QNO"] += 1
    else:
        categories["SAME_BOOK_DIFF_PAGE"] += 1
        if len(real_wrong) < 8:
            real_wrong.append(
                {
                    "id": r.id[:8],
                    "url_book": book_dir[:40],
                    "url_page": url_page,
                    "truth_page": truth_page,
                    "kind": "same_book_diff_page",
                }
            )

# Report
total = len(sample)
print("=" * 80)
print(f"DETAILED VERDICT CATEGORIES (n={total})")
print("=" * 80)

correct_cats = {
    "NO_TRUTH_CONSISTENT",
    "NO_TRUTH_PAGE_FALLBACK_OK",
    "PAGE_FALLBACK_OK_TRUTH",
    "CROP_EXACT_OK",
    "QNO_EXACT_OK",
}
likely_correct_cats = {"SAME_PAGE_DIFF_CROP", "SAME_PAGE_DIFF_QNO"}
uncertain_cats = {"NO_TRUTH_NO_VERIFY", "NO_SAME_BOOK_TRUTH"}
wrong_cats = {
    "REAL_CROSS_BOOK",
    "PAGE_FALLBACK_WRONG_PAGE",
    "SAME_BOOK_DIFF_PAGE",
    "PAGE_FALLBACK_PAGE_MISMATCH",
    "INVALID_URL",
}

for cat, n in categories.most_common():
    pct = n / total * 100
    tag = (
        "✅"
        if cat in correct_cats
        else (
            "⚠️"
            if cat in likely_correct_cats
            else ("?" if cat in uncertain_cats else "❌")
        )
    )
    print(f"  {tag} {cat:<35s} {n:>5} ({pct:>5.1f}%)")

c_correct = sum(categories[c] for c in correct_cats)
c_likely = sum(categories[c] for c in likely_correct_cats)
c_uncertain = sum(categories[c] for c in uncertain_cats)
c_wrong = sum(categories[c] for c in wrong_cats)

print("\n[summary]")
print(
    f"  KESIN DOĞRU (crop/page-level):  {c_correct:>5} ({c_correct / total * 100:.1f}%)"
)
print(
    f"  MUHTEMELEN DOĞRU (page within): {c_likely:>5} ({c_likely / total * 100:.1f}%)"
)
print(
    f"  BELİRSİZ (no truth available):  {c_uncertain:>5} ({c_uncertain / total * 100:.1f}%)"
)
print(f"  YANLIS:                          {c_wrong:>5} ({c_wrong / total * 100:.1f}%)")

print(f"\nREAL WRONG EXAMPLES (n={len(real_wrong)}):")
for ex in real_wrong:
    print(f"  {ex}")

# Extrapolate
print("\n" + "=" * 80)
print("EXTRAPOLATION → 166,818 active HAS-image")
print("=" * 80)
print(f"  KESIN DOĞRU:        ~{int(166818 * c_correct / total):>7,}")
print(f"  MUHTEMELEN DOĞRU:   ~{int(166818 * c_likely / total):>7,}")
print(f"  BELİRSİZ:           ~{int(166818 * c_uncertain / total):>7,}")
print(f"  YANLIS:             ~{int(166818 * c_wrong / total):>7,}")
print(
    f"\n  TOPLAM tahmin doğru: ~{int(166818 * (c_correct + c_likely) / total):>7,} (%{(c_correct + c_likely) / total * 100:.1f})"
)
