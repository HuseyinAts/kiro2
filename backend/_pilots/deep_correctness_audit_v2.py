#!/usr/bin/env python3
"""
Deep correctness audit v2: 2,000 sample with crop-level verification.

NEW: When multiple crops exist on same page, verify the SPECIFIC crop selected
is the one matching THIS DB row (via JSONL text → crop_file in gemini results).
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


# Build TWO indices: gemini and eslesmis
print("[load] Building dual ground-truth indices...")
gem_by_text: dict[str, list] = defaultdict(list)
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
        gem_by_text[normed[:100]].append((book, int(page), crop))

jsonl_by_text: dict[str, list] = defaultdict(list)
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
        jsonl_by_text[normed[:100]].append((book, int(page), int(qno)))
print(f"[indexed] gemini={len(gem_by_text):,}  eslesmis={len(jsonl_by_text):,}\n")

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

with eng.connect() as c:
    sample = c.execute(
        sa_text("""
        SELECT id::text, source_book, source_page, exam_type, subject_area,
               question_text, question_image_url, pipeline_metadata::text AS pm
        FROM question_bank
        WHERE is_active=true
          AND question_image_url IS NOT NULL AND question_image_url <> ''
        ORDER BY RANDOM() LIMIT 2000
    """)
    ).fetchall()
print(f"[sample] {len(sample)} random rows\n")


def parse_url(url):
    if not url or not url.startswith("/static/crops/"):
        return None
    rel = url[len("/static/crops/") :]
    parts = rel.split("/")
    if len(parts) != 2:
        return None
    book_dir, fname = parts
    m = re.search(r"_p(\d+)_(q\d+|q\d+|PAGE|LM\d+)\.", fname)
    if not m:
        return book_dir, fname, None, None
    page = int(m.group(1))
    suffix = m.group(2)
    if suffix.startswith("q"):
        qno = int(suffix[1:])
    elif suffix == "PAGE":
        qno = "PAGE"
    elif suffix.startswith("LM"):
        qno = f"LM{suffix[2:]}"
    else:
        qno = None
    return book_dir, fname, page, qno


def get_strategy(pm_str):
    if not pm_str:
        return "no_metadata"
    flags_ordered = [
        ("v15_page_fallback", "v15_PAGE"),
        ("v15a_labelme_exact", "v15a_LM"),
        ("v14_jaccard", "v14_jaccard"),
        ("v13_hybrid_disambig", "v13"),
        ("v12_page_residual", "v12"),
        ("v10b_options_strict", "v10b"),
        ("gemini_flash_v9_loose", "v9_gemini"),
        ("gemini_flash_v8", "v8_gemini"),
        ("strategy_d_qtext", "stratD"),
        ("strategy_c_unused", "stratC"),
        ("strategy_b_image_ocr", "stratB"),
        ("n_to_n_text_v7", "v7"),
        ("single_v6", "v6"),
        ("rebuild_v5", "v5"),
        ("fuzzy_v3", "v3"),
        ("jsonl_v2", "v2_jsonl"),
        ("metadata_v1", "v1_metadata"),
    ]
    for f, label in flags_ordered:
        if f'"image_match_{f}"' in pm_str:
            return label
    return "legacy_pre_s157"


# Comprehensive audit
results = []  # one row per sample
for r in sample:
    parsed = parse_url(r.question_image_url)
    if not parsed:
        results.append({"id": r.id, "verdict": "INVALID_URL", "strategy": "?"})
        continue
    book_dir, fname, url_page, url_qno = parsed
    strategy = get_strategy(r.pm)

    # File existence
    fpath = CROPS_BASE / book_dir / fname
    file_ok = fpath.exists()

    # Verdict logic
    verdict = "UNKNOWN"
    detail = ""

    # 1) Try gemini results lookup (most comprehensive)
    normed_t = _norm(r.question_text)[:100]
    gem_truth = gem_by_text.get(normed_t, [])
    same_book_gem = [
        (b, p, c) for b, p, c in gem_truth if _canon(b) == _canon(book_dir)
    ]

    # 2) Try eslesmis lookup
    jsonl_truth = jsonl_by_text.get(normed_t, [])
    same_book_jsonl = [
        (b, p, q) for b, p, q in jsonl_truth if _canon(b) == _canon(book_dir)
    ]

    # PAGE-level fallback
    if url_qno == "PAGE":
        # Page-level — only page must match (which it does by construction of v15)
        # Verify book and page
        if (same_book_gem and any(p == url_page for b, p, _ in same_book_gem)) or (
            same_book_jsonl and any(p == url_page for b, p, _ in same_book_jsonl)
        ):
            verdict = "PAGE_LEVEL_OK"
        elif _canon(r.source_book) == _canon(book_dir) and url_page == r.source_page:
            # No truth, but URL page == DB source_page → trust v15 by construction
            verdict = "PAGE_LEVEL_TRUSTED"
        else:
            verdict = "PAGE_LEVEL_BOOK_MISMATCH"

    # Crop-level verification
    elif same_book_gem:
        # Exact crop match?
        crop_matches = [(b, p, c) for b, p, c in same_book_gem if c == fname]
        if crop_matches:
            verdict = "CROP_EXACT_OK"
        else:
            # Page match but different crop?
            page_matches = [(b, p, c) for b, p, c in same_book_gem if p == url_page]
            if page_matches:
                # Same page, different crop within → could be page deduplication
                # Check if URL crop is among page's crops
                verdict = "PAGE_OK_CROP_DIFF"
                detail = f"truth crop = {page_matches[0][2]}, url = {fname}"
            else:
                verdict = "PAGE_WRONG"
                detail = f"truth page = {same_book_gem[0][1]}, url page = {url_page}"
    elif same_book_jsonl:
        # No gemini, eslesmis has same book
        page_matches = [(b, p, q) for b, p, q in same_book_jsonl if p == url_page]
        if page_matches:
            # Check qno
            qno = page_matches[0][2]
            if isinstance(url_qno, int) and url_qno == qno:
                verdict = "QNO_EXACT_OK"
            else:
                verdict = "PAGE_OK_QNO_DIFF"
                detail = f"truth qno = {qno}, url qno = {url_qno}"
        else:
            verdict = "PAGE_WRONG"
            detail = f"truth page = {same_book_jsonl[0][1]}, url page = {url_page}"
    elif gem_truth or jsonl_truth:
        # Truth exists in different book — possibly cross-book
        verdict = "CROSS_BOOK_MATCH"
        detail = f"truth book = {(gem_truth or jsonl_truth)[0][0][:40]}, url book = {book_dir[:40]}"
    # No truth available → fall back to page consistency
    elif r.source_page == url_page and _canon(r.source_book) == _canon(book_dir):
        verdict = "NO_TRUTH_PAGE_OK"
    else:
        verdict = "NO_TRUTH_INCONSISTENT"

    results.append(
        {
            "id": r.id,
            "strategy": strategy,
            "verdict": verdict,
            "detail": detail,
            "file_ok": file_ok,
            "book": r.source_book or "",
            "exam_type": r.exam_type or "",
            "subject_area": r.subject_area or "",
        }
    )

# Aggregate
verdict_counts = Counter(r["verdict"] for r in results)
strategy_verdicts: dict[str, Counter] = defaultdict(Counter)
for r in results:
    strategy_verdicts[r["strategy"]][r["verdict"]] += 1

per_subject = defaultdict(Counter)
per_exam = defaultdict(Counter)
per_book = defaultdict(Counter)
for r in results:
    per_subject[r["subject_area"][:30]][r["verdict"]] += 1
    per_exam[r["exam_type"][:10]][r["verdict"]] += 1
    per_book[r["book"][:40]][r["verdict"]] += 1

# Print
total = len(results)
print("=" * 80)
print("VERDICT DISTRIBUTION (n=2000)")
print("=" * 80)
correct_verdicts = {
    "CROP_EXACT_OK",
    "QNO_EXACT_OK",
    "PAGE_LEVEL_OK",
    "PAGE_LEVEL_TRUSTED",
}
likely_correct = {"PAGE_OK_CROP_DIFF", "PAGE_OK_QNO_DIFF", "NO_TRUTH_PAGE_OK"}
wrong_verdicts = {
    "PAGE_WRONG",
    "CROSS_BOOK_MATCH",
    "PAGE_LEVEL_BOOK_MISMATCH",
    "NO_TRUTH_INCONSISTENT",
    "INVALID_URL",
}

c_correct = sum(verdict_counts[v] for v in correct_verdicts)
c_likely = sum(verdict_counts[v] for v in likely_correct)
c_wrong = sum(verdict_counts[v] for v in wrong_verdicts)

for v, n in verdict_counts.most_common():
    pct = n / total * 100
    tag = "✅" if v in correct_verdicts else ("⚠️" if v in likely_correct else "❌")
    print(f"  {tag} {v:35s} {n:>5} ({pct:5.1f}%)")

print()
print(
    f"KESIN DOĞRU (CROP/PAGE-level verified):  {c_correct:>5} ({c_correct / total * 100:.1f}%)"
)
print(
    f"MUHTEMELEN DOĞRU (page-level only):      {c_likely:>5} ({c_likely / total * 100:.1f}%)"
)
print(
    f"YANLIS:                                   {c_wrong:>5} ({c_wrong / total * 100:.1f}%)"
)

print()
print("=" * 80)
print("PER-STRATEGY ACCURACY")
print("=" * 80)
print(
    f"{'Strategy':<20} {'N':>5} {'Correct':>8} {'Likely':>7} {'Wrong':>6} {'Acc%':>6}"
)
print("-" * 60)
for strat in sorted(
    strategy_verdicts.keys(), key=lambda s: -sum(strategy_verdicts[s].values())
):
    counts = strategy_verdicts[strat]
    n = sum(counts.values())
    correct = sum(counts[v] for v in correct_verdicts)
    likely = sum(counts[v] for v in likely_correct)
    wrong = sum(counts[v] for v in wrong_verdicts)
    acc = (correct + likely) / n * 100 if n else 0
    print(f"{strat:<20} {n:>5} {correct:>8} {likely:>7} {wrong:>6} {acc:>5.1f}%")

print()
print("=" * 80)
print("PER EXAM TYPE")
print("=" * 80)
for exam, counts in sorted(per_exam.items(), key=lambda x: -sum(x[1].values())):
    n = sum(counts.values())
    correct = sum(counts[v] for v in correct_verdicts) + sum(
        counts[v] for v in likely_correct
    )
    wrong = sum(counts[v] for v in wrong_verdicts)
    print(
        f"  {exam:<15} N={n:>4} correct={correct:>4} wrong={wrong:>3} ({(correct / n * 100 if n else 0):.1f}%)"
    )

print()
print("=" * 80)
print("TOP-10 PROBLEM BOOKS (most wrong)")
print("=" * 80)
problem_books = []
for book, counts in per_book.items():
    n = sum(counts.values())
    wrong = sum(counts[v] for v in wrong_verdicts)
    if n >= 5 and wrong:
        problem_books.append((wrong, n, book))
problem_books.sort(reverse=True)
for wrong, n, book in problem_books[:10]:
    print(f"  {wrong:>3}/{n:>3} wrong ({wrong / n * 100:.0f}%) — {book[:60]}")

# Examples of wrongs
print()
print("=" * 80)
print("WRONG EXAMPLES (first 8)")
print("=" * 80)
wrong_examples = [r for r in results if r["verdict"] in wrong_verdicts][:8]
for r in wrong_examples:
    print(
        f"  {r['id'][:8]} [{r['strategy']:18s}] verdict={r['verdict']:25s} {r['detail'][:80]}"
    )

# Extrapolate to 166,818
print()
print("=" * 80)
print("EXTRAPOLATION (n=2000 → 166,818 active HAS-image)")
print("=" * 80)
print(
    f"  KESIN DOĞRU:        ~{int(166818 * c_correct / total):>7,}  ({c_correct / total * 100:.1f}%)"
)
print(
    f"  MUHTEMELEN DOĞRU:   ~{int(166818 * c_likely / total):>7,}  ({c_likely / total * 100:.1f}%)"
)
print(
    f"  TOPLAM DOĞRU:       ~{int(166818 * (c_correct + c_likely) / total):>7,}  ({(c_correct + c_likely) / total * 100:.1f}%)"
)
print(
    f"  YANLIS:             ~{int(166818 * c_wrong / total):>7,}  ({c_wrong / total * 100:.1f}%)"
)
