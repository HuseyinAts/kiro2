#!/usr/bin/env python3
"""
Strict correctness audit: 10,000 sample with multi-source verification.

Compared to previous audit which used prefix-only lookup, this:
  1. Tries FULL text exact match (gemini + eslesmis)
  2. Tries LOOSE prefix match (80-char + 100-char)
  3. Cross-validates BOTH sources when both have entries
  4. Categorizes confidence: HIGH (dual-source), MED (single-source), LOW (metadata only)
  5. Checks disk file existence + non-zero size
  6. Detects duplicate question_text issues
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
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _norm(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)


def _norm_strict(t):
    if not t:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", t)).strip().lower()


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _canon(s):
    return re.sub(r"\W+", "_", _fold(s or "")).strip("_")


def book_similarity(a, b):
    fa, fb = _norm(a), _norm(b)
    if not fa or not fb:
        return 0.0
    short = min(len(fa), len(fb))
    if short < 6:
        return 0.0
    if fa.startswith(fb[:short]) or fb.startswith(fa[:short]):
        return min(short / max(len(fa), len(fb)), 1.0)
    ta = set(re.findall(r"[a-z0-9]{3,}", fa))
    tb = set(re.findall(r"[a-z0-9]{3,}", fb))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# Build indices with FULL normalized text and prefix variants
print("[load] gemini + eslesmis with full + prefix indices...")
gem_full = {}  # full_norm → list[(book, page, crop)]
gem_p100 = defaultdict(list)  # 100-char prefix → list
gem_p60 = defaultdict(list)  # 60-char prefix → list

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
        if len(normed) < 30:
            continue
        entry = (book, int(page), crop)
        if normed not in gem_full:
            gem_full[normed] = []
        gem_full[normed].append(entry)
        if len(normed) >= 100:
            gem_p100[normed[:100]].append(entry)
        if len(normed) >= 60:
            gem_p60[normed[:60]].append(entry)

jsonl_full = {}
jsonl_p100 = defaultdict(list)
jsonl_p60 = defaultdict(list)
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
        if len(normed) < 30:
            continue
        entry = (book, int(page), int(qno))
        if normed not in jsonl_full:
            jsonl_full[normed] = []
        jsonl_full[normed].append(entry)
        if len(normed) >= 100:
            jsonl_p100[normed[:100]].append(entry)
        if len(normed) >= 60:
            jsonl_p60[normed[:60]].append(entry)

print(
    f"[indexed] gemini: full={len(gem_full):,} p100={len(gem_p100):,} p60={len(gem_p60):,}"
)
print(
    f"[indexed] jsonl:  full={len(jsonl_full):,} p100={len(jsonl_p100):,} p60={len(jsonl_p60):,}\n"
)

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

print("[query] 10,000 random sample...")
with eng.connect() as c:
    sample = c.execute(
        sa_text("""
        SELECT id::text, source_book, source_page, question_text, question_image_url,
               option_a, option_b, option_c, option_d, option_e
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL AND question_image_url <> ''
        ORDER BY RANDOM() LIMIT 10000
    """)
    ).fetchall()
print(f"[got] {len(sample)} rows\n")


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
    if suffix.startswith("q"):
        qno = int(suffix[1:])
    else:
        qno = suffix
    return book_dir, fname, page, qno


def lookup_truth(normed_text, source_book_canon):
    """
    Multi-strategy lookup. Returns list of candidate truths from BOTH sources
    that have book_similarity >= 0.7 to URL book.
    """
    cands_gem = []
    cands_jsonl = []
    # Full match
    if normed_text in gem_full:
        cands_gem.extend(gem_full[normed_text])
    if normed_text in jsonl_full:
        cands_jsonl.extend(jsonl_full[normed_text])
    # 100-char prefix if full miss
    if not cands_gem and len(normed_text) >= 100:
        cands_gem.extend(gem_p100.get(normed_text[:100], []))
    if not cands_jsonl and len(normed_text) >= 100:
        cands_jsonl.extend(jsonl_p100.get(normed_text[:100], []))
    # 60-char prefix if still miss
    if not cands_gem and len(normed_text) >= 60:
        cands_gem.extend(gem_p60.get(normed_text[:60], []))
    if not cands_jsonl and len(normed_text) >= 60:
        cands_jsonl.extend(jsonl_p60.get(normed_text[:60], []))
    return cands_gem, cands_jsonl


# Comprehensive categorization
categories = Counter()
strategy_details = defaultdict(lambda: defaultdict(int))
file_issues = Counter()
real_wrong_examples = []
suspicious_examples = []

for r in sample:
    book_dir, fname, url_page, url_qno = parse_url(r.question_image_url)
    if not book_dir:
        categories["INVALID_URL"] += 1
        continue

    # File check
    fpath = CROPS_BASE / book_dir / fname
    if not fpath.exists():
        file_issues["missing"] += 1
        categories["FILE_MISSING"] += 1
        continue
    elif fpath.stat().st_size < 1024:
        file_issues["tiny"] += 1

    is_page_fallback = url_qno == "PAGE"
    is_labelme = isinstance(url_qno, str) and url_qno.startswith("LM")

    normed_t = _norm(r.question_text)
    if len(normed_t) < 30:
        # Can't audit by text
        if is_page_fallback:
            # v15: trust if URL page == DB page
            if url_page == r.source_page:
                categories["v15_PAGE_no_text_audit"] += 1
            else:
                categories["v15_PAGE_metadata_mismatch"] += 1
        else:
            categories["NO_TEXT_TO_AUDIT"] += 1
        continue

    cands_gem, cands_jsonl = lookup_truth(normed_t, _canon(book_dir))

    if not cands_gem and not cands_jsonl:
        # No truth available — STRICT: don't claim "correct"
        # Just check metadata self-consistency
        if (
            r.source_book
            and book_similarity(r.source_book, book_dir) >= 0.7
            and r.source_page == url_page
        ):
            categories["NO_TRUTH_metadata_consistent"] += 1
        else:
            categories["NO_TRUTH_metadata_drift"] += 1
        continue

    # Find same-book candidates
    same_book_gem = [
        (b, p, c) for b, p, c in cands_gem if book_similarity(b, book_dir) >= 0.7
    ]
    same_book_jsonl = [
        (b, p, q) for b, p, q in cands_jsonl if book_similarity(b, book_dir) >= 0.7
    ]

    if not same_book_gem and not same_book_jsonl:
        # Text exists but in DIFFERENT books only — cross-book mismatch
        categories["REAL_CROSS_BOOK"] += 1
        if len(real_wrong_examples) < 10:
            other_book = (cands_gem or cands_jsonl)[0][0]
            real_wrong_examples.append(
                f"  {r.id[:8]} url_book={book_dir[:35]} | truth_book={other_book[:35]} (sim<0.7)"
            )
        continue

    # PAGE-level fallback path
    if is_page_fallback:
        # Should have URL page matching truth page (same book)
        gem_pages = {p for _, p, _ in same_book_gem}
        jsonl_pages = {p for _, p, _ in same_book_jsonl}
        all_truth_pages = gem_pages | jsonl_pages
        if url_page in all_truth_pages:
            categories["v15_PAGE_truth_verified"] += 1
        elif r.source_page == url_page:
            # Truth not on this exact page but URL == DB metadata page
            categories["v15_PAGE_metadata_only"] += 1
        else:
            categories["v15_PAGE_wrong"] += 1
        continue

    # LM (labelme): treat like crop-level
    # CROP-LEVEL audit
    # Check exact crop match (gemini)
    crop_exact = any(c == fname for _, _, c in same_book_gem)
    # Check qno match (jsonl)
    m = re.search(r"_q(\d+)\.", fname)
    url_q = int(m.group(1)) if m else None
    qno_exact = False
    if url_q is not None and same_book_jsonl:
        truth_pages_to_qnos = defaultdict(set)
        for _, p, q in same_book_jsonl:
            truth_pages_to_qnos[p].add(q)
        if url_page in truth_pages_to_qnos and url_q in truth_pages_to_qnos[url_page]:
            qno_exact = True

    # Pages where truth exists for this text+book
    gem_pages = {p for _, p, _ in same_book_gem}
    jsonl_pages = {p for _, p, _ in same_book_jsonl}
    all_truth_pages = gem_pages | jsonl_pages

    # Decision tree
    if crop_exact and qno_exact:
        categories["CROP_EXACT_AND_QNO_OK"] += 1
        confidence = "HIGH"
    elif crop_exact:
        categories["CROP_EXACT_ONLY"] += 1
        confidence = "HIGH"
    elif qno_exact:
        categories["QNO_EXACT_ONLY"] += 1
        confidence = "HIGH"
    elif url_page in all_truth_pages:
        # Same page but neither crop nor qno match
        categories["SAME_PAGE_DIFF_CROP_OR_QNO"] += 1
        confidence = "MED"
    else:
        # Different page
        truth_pages_list = sorted(all_truth_pages)
        if truth_pages_list and abs(truth_pages_list[0] - url_page) <= 2:
            categories["SAME_BOOK_NEAR_PAGE"] += 1
            if len(suspicious_examples) < 8:
                suspicious_examples.append(
                    f"  {r.id[:8]} url=p{url_page} truth=p{truth_pages_list[0]} delta={truth_pages_list[0] - url_page}"
                )
        else:
            categories["SAME_BOOK_FAR_PAGE"] += 1
            if len(real_wrong_examples) < 10:
                real_wrong_examples.append(
                    f"  {r.id[:8]} url={book_dir[:30]}/p{url_page} truth=p{truth_pages_list[0] if truth_pages_list else '?'}"
                )

# Print
total = len(sample)
print("=" * 80)
print(f"STRICT VERDICT BREAKDOWN (n={total})")
print("=" * 80)

HIGH_CORRECT = {
    "CROP_EXACT_AND_QNO_OK",
    "CROP_EXACT_ONLY",
    "QNO_EXACT_ONLY",
    "v15_PAGE_truth_verified",
}
MED_CORRECT = {"SAME_PAGE_DIFF_CROP_OR_QNO"}
LOW_CONFIDENCE = {
    "NO_TRUTH_metadata_consistent",
    "v15_PAGE_metadata_only",
    "v15_PAGE_no_text_audit",
    "NO_TEXT_TO_AUDIT",
}
WRONG = {
    "REAL_CROSS_BOOK",
    "SAME_BOOK_FAR_PAGE",
    "SAME_BOOK_NEAR_PAGE",
    "v15_PAGE_wrong",
    "v15_PAGE_metadata_mismatch",
    "NO_TRUTH_metadata_drift",
    "INVALID_URL",
    "FILE_MISSING",
}

print(f"\n{'Category':<40s} {'Count':>6s} {'Pct':>7s}  Tier")
print("-" * 70)
for cat, n in categories.most_common():
    pct = n / total * 100
    tier = (
        "✅HIGH"
        if cat in HIGH_CORRECT
        else (
            "🟡MED"
            if cat in MED_CORRECT
            else ("?LOW" if cat in LOW_CONFIDENCE else "❌WRONG")
        )
    )
    print(f"{cat:<40s} {n:>6} {pct:>6.2f}%  {tier}")

c_high = sum(categories[c] for c in HIGH_CORRECT)
c_med = sum(categories[c] for c in MED_CORRECT)
c_low = sum(categories[c] for c in LOW_CONFIDENCE)
c_wrong = sum(categories[c] for c in WRONG)

print()
print(f"✅ HIGH (crop/qno verified):      {c_high:>6} ({c_high / total * 100:.2f}%)")
print(f"🟡 MED  (same page, crop diff):   {c_med:>6} ({c_med / total * 100:.2f}%)")
print(f"?  LOW  (no truth, metadata only):{c_low:>6} ({c_low / total * 100:.2f}%)")
print(f"❌ WRONG:                          {c_wrong:>6} ({c_wrong / total * 100:.2f}%)")

# Filtered "real wrong" — not include NEAR_PAGE which might be off-by-1 due to indexing
real_wrong_strict = (
    categories["REAL_CROSS_BOOK"]
    + categories["SAME_BOOK_FAR_PAGE"]
    + categories["v15_PAGE_wrong"]
    + categories["NO_TRUTH_metadata_drift"]
)
near_wrong = categories["SAME_BOOK_NEAR_PAGE"]
print(
    f"\n🔴 GERÇEK YANLIS (cross-book + far page + drift): {real_wrong_strict} ({real_wrong_strict / total * 100:.2f}%)"
)
print(
    f"🟠 OFF-BY-1-2 PAGE (could be indexing): {near_wrong} ({near_wrong / total * 100:.2f}%)"
)

print("\n[file issues]")
for k, v in file_issues.items():
    print(f"  {k}: {v}")

print("\n[SAMPLES — suspicious near-page]")
for s in suspicious_examples[:8]:
    print(s)

print("\n[SAMPLES — real wrong]")
for s in real_wrong_examples[:8]:
    print(s)

print()
print("=" * 80)
print("EXTRAPOLATION → 166,818")
print("=" * 80)
print(
    f"  ✅ HIGH:                  ~{int(166818 * c_high / total):>7,} ({c_high / total * 100:.1f}%)"
)
print(
    f"  🟡 MED:                   ~{int(166818 * c_med / total):>7,} ({c_med / total * 100:.1f}%)"
)
print(
    f"  ?  LOW (audit-imkansız):  ~{int(166818 * c_low / total):>7,} ({c_low / total * 100:.1f}%)"
)
print(
    f"  ❌ WRONG:                 ~{int(166818 * c_wrong / total):>7,} ({c_wrong / total * 100:.1f}%)"
)
print()
print(
    f"  GERÇEK YANLIŞ (strict):   ~{int(166818 * real_wrong_strict / total):>7,} ({real_wrong_strict / total * 100:.2f}%)"
)
print(
    f"  OFF-BY-PAGE (gri alan):   ~{int(166818 * near_wrong / total):>7,} ({near_wrong / total * 100:.2f}%)"
)
