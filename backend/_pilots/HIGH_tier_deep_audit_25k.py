#!/usr/bin/env python3
"""
HIGH tier deep audit (n=25,000).

GOAL: Determine if "HIGH (text→crop verified)" classification is reliable or
contains circular verification artifacts.

CIRCULARITY problem:
  - v8/v9 strategies USED gemini results.jsonl as source
  - Auditing those rows AGAINST gemini results.jsonl is CIRCULAR
  - Need INDEPENDENT verification

INDEPENDENT signals available:
  1. eslesmis_sorucevap.jsonl (production v3.5+) — different pipeline, ~73K entries
  2. ocr_crops/results.jsonl (raw Gemini OCR) — primary source for v8/v9
  3. d-dataset crop disk filenames (file existence + naming)
  4. DB options (option_a..option_e) — assigned BEFORE image matching
  5. DB metadata: source_book, source_page, exam_type, subject_area

Verification scheme:
  - For each HIGH match, attempt INDEPENDENT verification:
    a) If matched via gemini, try to find SAME question in eslesmis (independent)
    b) If both agree → HIGH_DUAL_VERIFIED
    c) If only original source has it → HIGH_SINGLE_SOURCE (CIRCULAR risk)
    d) If options match disk crop's meta.json bbox sequence → INDEPENDENT
  - Check crop file size + filename pattern
  - Check for duplicate crop assignment (same crop assigned to N DB rows)
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
JSONL_ESLESMIS = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
JSONL_GEMINI = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _norm(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


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


# Build indices
print("[load] indices...")
gem_by_text_p100: dict = defaultdict(list)
gem_by_crop: dict = {}  # crop_file → (book, page, soru_metni_normed)
with JSONL_GEMINI.open(encoding="utf-8") as f:
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
        if len(normed) >= 100:
            gem_by_text_p100[normed[:100]].append((book, int(page), crop))
        gem_by_crop[crop] = (book, int(page), normed)

eslesmis_by_text_p100: dict = defaultdict(list)
with JSONL_ESLESMIS.open(encoding="utf-8") as f:
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
        if len(normed) >= 100:
            eslesmis_by_text_p100[normed[:100]].append((book, int(page), int(qno)))

print(
    f"[indexed] gemini text: {len(gem_by_text_p100):,} | gemini crop_file: {len(gem_by_crop):,}"
)
print(f"[indexed] eslesmis text: {len(eslesmis_by_text_p100):,}\n")

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Pre-compute: which crops are used by how many DB rows? (duplicate detection)
print("[query] crop usage distribution...")
with eng.connect() as c:
    crop_usage = c.execute(
        sa_text("""
        SELECT question_image_url, COUNT(*) AS n
        FROM question_bank
        WHERE is_active=true AND question_image_url IS NOT NULL
          AND question_image_url NOT LIKE '%_PAGE.png'
        GROUP BY question_image_url
        HAVING COUNT(*) >= 2
        """)
    ).fetchall()
duplicate_crop_usage = {r.question_image_url: r.n for r in crop_usage}
print(f"[crops used by 2+ DB rows]: {len(duplicate_crop_usage):,}\n")

# Sample 25,000 — but filter to only HIGH category rows (those text-verifiable)
print("[query] 25,000 sample with question_text...")
with eng.connect() as c:
    sample = c.execute(
        sa_text("""
        SELECT id::text, source_book, source_page,
               question_text, question_image_url,
               option_a, option_b, option_c, option_d, option_e,
               pipeline_metadata::text AS pm
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL AND question_image_url <> ''
          AND question_image_url NOT LIKE '%_PAGE.png'
          AND question_text IS NOT NULL
          AND LENGTH(question_text) >= 80
        ORDER BY RANDOM() LIMIT 25000
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
    qno = int(suffix[1:]) if suffix.startswith("q") and suffix != "PAGE" else suffix
    return book_dir, fname, page, qno


def get_strategy(pm_str):
    if not pm_str:
        return "no_metadata"
    flags_ordered = [
        "v15_page_fallback",
        "v15a_labelme_exact",
        "v14_jaccard",
        "v13_hybrid_disambig",
        "v12_page_residual",
        "v10b_options_strict",
        "gemini_flash_v9_loose",
        "gemini_flash_v8",
        "strategy_d_qtext",
        "strategy_c_unused",
        "strategy_b_image_ocr",
        "n_to_n_text_v7",
        "single_v6",
        "rebuild_v5",
        "fuzzy_v3",
        "jsonl_v2",
        "metadata_v1",
    ]
    for f in flags_ordered:
        if f'"image_match_{f}"' in pm_str:
            return f
    return "legacy_pre_s157"


# Classify each row's audit reliability
GEMINI_DERIVED = {"gemini_flash_v8", "gemini_flash_v9_loose"}  # CIRCULAR vs gemini
JSONL_DERIVED = {"rebuild_v5", "jsonl_v2", "fuzzy_v3"}  # CIRCULAR vs eslesmis

verdict_counts = Counter()
file_stats = Counter()
duplicate_uses = 0
sample_categorized = []

for r in sample:
    book_dir, fname, url_page, url_qno = parse_url(r.question_image_url)
    if not book_dir or fname is None:
        verdict_counts["INVALID_URL"] += 1
        continue

    # Disk verification
    fpath = CROPS_BASE / book_dir / fname
    if not fpath.exists():
        verdict_counts["FILE_MISSING"] += 1
        continue
    fsize = fpath.stat().st_size
    if fsize < 2048:  # <2KB suspicious
        file_stats["tiny_file"] += 1
    elif fsize > 5 * 1024 * 1024:  # >5MB
        file_stats["large_file"] += 1
    else:
        file_stats["normal"] += 1

    # Duplicate crop usage
    if r.question_image_url in duplicate_crop_usage:
        duplicate_uses += 1

    strategy = get_strategy(r.pm)

    # Independent verification
    normed_text = _norm(r.question_text)
    if len(normed_text) < 100:
        verdict_counts["TEXT_TOO_SHORT"] += 1
        continue
    prefix = normed_text[:100]

    gem_cands = gem_by_text_p100.get(prefix, [])
    es_cands = eslesmis_by_text_p100.get(prefix, [])

    # Filter to same-book candidates
    gem_same_book = [
        (b, p, c) for b, p, c in gem_cands if book_similarity(b, book_dir) >= 0.7
    ]
    es_same_book = [
        (b, p, q) for b, p, q in es_cands if book_similarity(b, book_dir) >= 0.7
    ]

    # CIRCULARITY check
    is_circular = (strategy in GEMINI_DERIVED and not es_same_book) or (
        strategy in JSONL_DERIVED and not gem_same_book
    )

    # Crop-level verification
    gem_crop_match = any(c == fname for _, _, c in gem_same_book)
    url_q_int = None
    m = re.search(r"_q(\d+)\.", fname)
    if m:
        url_q_int = int(m.group(1))

    es_qno_match = False
    if url_q_int is not None:
        for _, p, q in es_same_book:
            if p == url_page and q == url_q_int:
                es_qno_match = True
                break

    # Cross-source dual verification
    if gem_crop_match and es_qno_match:
        verdict_counts["DUAL_VERIFIED"] += 1
        if len(sample_categorized) < 5:
            sample_categorized.append(("DUAL", r.id, strategy, fname))
    elif gem_crop_match and not es_same_book:
        if strategy in GEMINI_DERIVED:
            verdict_counts["GEMINI_ONLY_CIRCULAR"] += 1
        else:
            verdict_counts["GEMINI_ONLY_INDEPENDENT"] += 1
    elif es_qno_match and not gem_same_book:
        if strategy in JSONL_DERIVED:
            verdict_counts["ESLESMIS_ONLY_CIRCULAR"] += 1
        else:
            verdict_counts["ESLESMIS_ONLY_INDEPENDENT"] += 1
    elif gem_crop_match and es_same_book and not es_qno_match:
        # Gemini says yes, eslesmis disagrees on qno
        verdict_counts["GEMINI_OK_ESLESMIS_DISAGREE"] += 1
    elif es_qno_match and gem_same_book and not gem_crop_match:
        # Eslesmis says yes, gemini disagrees on crop
        verdict_counts["ESLESMIS_OK_GEMINI_DISAGREE"] += 1
    else:
        # Neither verified at crop/qno level
        # Same-book + same-page?
        gem_pages = {p for _, p, _ in gem_same_book}
        es_pages = {p for _, p, _ in es_same_book}
        if url_page in (gem_pages | es_pages):
            verdict_counts["SAME_BOOK_PAGE_NO_CROP"] += 1
        elif gem_same_book or es_same_book:
            verdict_counts["SAME_BOOK_DIFFERENT_PAGE"] += 1
        elif gem_cands or es_cands:
            verdict_counts["DIFFERENT_BOOK"] += 1
        else:
            verdict_counts["NO_TRUTH_AT_ALL"] += 1

# Print
total = len(sample)
print("=" * 80)
print(f"HIGH-TIER DEEP AUDIT (n={total})")
print("=" * 80)
print(f"\n{'Verdict':<40s} {'Count':>6s} {'Pct':>7s}")
print("-" * 60)
for v, n in verdict_counts.most_common():
    print(f"{v:<40s} {n:>6} {n / total * 100:>6.2f}%")

# Group analysis
print()
print("=" * 80)
print("GROUPED ANALYSIS")
print("=" * 80)
strict_high = verdict_counts["DUAL_VERIFIED"]
gemini_only_indep = verdict_counts["GEMINI_ONLY_INDEPENDENT"]
gemini_only_circ = verdict_counts["GEMINI_ONLY_CIRCULAR"]
eslesmis_only_indep = verdict_counts["ESLESMIS_ONLY_INDEPENDENT"]
eslesmis_only_circ = verdict_counts["ESLESMIS_ONLY_CIRCULAR"]
disagree = (
    verdict_counts["GEMINI_OK_ESLESMIS_DISAGREE"]
    + verdict_counts["ESLESMIS_OK_GEMINI_DISAGREE"]
)
no_truth = verdict_counts["NO_TRUTH_AT_ALL"]
same_page_no_crop = verdict_counts["SAME_BOOK_PAGE_NO_CROP"]
diff_page = verdict_counts["SAME_BOOK_DIFFERENT_PAGE"]
diff_book = verdict_counts["DIFFERENT_BOOK"]

print(
    f"\n🟢 STRONGEST (DUAL: gemini + eslesmis both agree):  {strict_high:>5} ({strict_high / total * 100:.2f}%)"
)
print("🟢 STRONG (independent single-source verified):")
print(
    f"  via gemini (strategy NOT v8/v9):                  {gemini_only_indep:>5} ({gemini_only_indep / total * 100:.2f}%)"
)
print(
    f"  via eslesmis (strategy NOT v5/v2/v3):             {eslesmis_only_indep:>5} ({eslesmis_only_indep / total * 100:.2f}%)"
)
print("⚠️  WEAK (CIRCULAR: verified via own source):")
print(
    f"  gemini circular (v8/v9 audited by gemini):        {gemini_only_circ:>5} ({gemini_only_circ / total * 100:.2f}%)"
)
print(
    f"  eslesmis circular (v2/v3/v5 audited by eslesmis): {eslesmis_only_circ:>5} ({eslesmis_only_circ / total * 100:.2f}%)"
)
print(
    f"❌ DISAGREEMENT (sources conflict):                   {disagree:>5} ({disagree / total * 100:.2f}%)"
)
print(
    f"🟡 SAME-PAGE different crop within page:              {same_page_no_crop:>5} ({same_page_no_crop / total * 100:.2f}%)"
)
print(
    f"❌ DIFFERENT PAGE same book:                          {diff_page:>5} ({diff_page / total * 100:.2f}%)"
)
print(
    f"❌ DIFFERENT BOOK:                                    {diff_book:>5} ({diff_book / total * 100:.2f}%)"
)
print(
    f"?  NO TRUTH (cannot verify):                          {no_truth:>5} ({no_truth / total * 100:.2f}%)"
)

# Calculate "true HIGH" = STRONG (any) + STRONGEST
true_high = strict_high + gemini_only_indep + eslesmis_only_indep
weak_high = gemini_only_circ + eslesmis_only_circ
print()
print(
    f"💎 INDEPENDENT HIGH (truly verified):  {true_high:>5} ({true_high / total * 100:.2f}%)"
)
print(
    f"⚠️  CIRCULAR HIGH (own-source audit):   {weak_high:>5} ({weak_high / total * 100:.2f}%)"
)

# File stats
print("\n[file stats]")
for k, v in file_stats.items():
    print(f"  {k}: {v:,}")
print(
    f"[duplicate crop usage (assigned to 2+ DB rows)]: {duplicate_uses:,} ({duplicate_uses / total * 100:.2f}%)"
)

# Extrapolation
print()
print("=" * 80)
print("EXTRAPOLATION → 166,818 HAS-image rows")
print("=" * 80)


def show(label, n):
    print(f"  {label:<40s} ~{int(166818 * n / total):>8,}  ({n / total * 100:.2f}%)")


show("STRONGEST (dual-verified)", strict_high)
show("STRONG (independent single)", gemini_only_indep + eslesmis_only_indep)
show("WEAK (CIRCULAR)", weak_high)
show("DISAGREEMENT", disagree)
show("Same page, crop diff (MED)", same_page_no_crop)
show("Different page (WRONG)", diff_page)
show("Different book (WRONG)", diff_book)
show("No truth (LOW)", no_truth)

# Final
print()
print("💡 CORRECTED FINAL:")
true_verified = strict_high + gemini_only_indep + eslesmis_only_indep
likely_correct = (
    weak_high + same_page_no_crop
)  # not independently verified but circularly correct
real_wrong = diff_page + diff_book + disagree
unverified = no_truth
print(
    f"  ✅ INDEPENDENT TRUE-HIGH: ~{int(166818 * true_verified / total):,} ({true_verified / total * 100:.1f}%)"
)
print(
    f"  🟡 CIRCULAR/SAME-PAGE:    ~{int(166818 * likely_correct / total):,} ({likely_correct / total * 100:.1f}%)"
)
print(
    f"  ❌ WRONG (real):          ~{int(166818 * real_wrong / total):,} ({real_wrong / total * 100:.1f}%)"
)
print(
    f"  ?  UNVERIFIABLE:          ~{int(166818 * unverified / total):,} ({unverified / total * 100:.1f}%)"
)
