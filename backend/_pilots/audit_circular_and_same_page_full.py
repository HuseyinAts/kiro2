#!/usr/bin/env python3
"""
Full audit of CIRCULAR + SAME_PAGE_CROP_DIFF categories (~17,000 rows).

INDEPENDENT verification via OPTIONS (option_a..option_e):
  - DB options were set BEFORE image matching (independent signal)
  - Look up URL's crop_file in gemini results.jsonl → get its secenekler
  - Compare DB options vs JSONL secenekler
  - If match: row's image content really matches THIS question
  - If mismatch: wrong crop assignment (real error)

For SAME_PAGE_DIFF_CROP:
  - The URL crop is on correct page but different question within page
  - Options should still match if it's the right question
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


def _norm_opt(t):
    """Strict option normalize for comparison."""
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)[:40]  # limit to 40 chars


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


# Build gemini index: crop_file → (book, page, soru_metni_normed, secenekler)
print("[load] gemini crop_file → secenekler index...")
gem_by_crop = {}
gem_by_text_p100 = defaultdict(list)
gem_book_page_qno_to_crop = {}  # (book_canon, page, question_index) → crop
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
        qi = d.get("question_index")
        sec = d.get("secenekler", {}) or {}
        if not (book and page is not None and crop):
            continue
        opts = {
            "A": _norm_opt(sec.get("A", "")),
            "B": _norm_opt(sec.get("B", "")),
            "C": _norm_opt(sec.get("C", "")),
            "D": _norm_opt(sec.get("D", "")),
            "E": _norm_opt(sec.get("E", "")),
        }
        gem_by_crop[crop] = {
            "book": book,
            "page": int(page),
            "text": _norm(t),
            "opts": opts,
            "qi": qi,
        }
        if t:
            normed = _norm(t)
            if len(normed) >= 100:
                gem_by_text_p100[normed[:100]].append((book, int(page), crop, opts))

# Eslesmis: (book, page) → list of qno entries
print("[load] eslesmis indices...")
es_by_text_p100 = defaultdict(list)
es_by_book_page = defaultdict(list)
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
            es_by_text_p100[normed[:100]].append((book, int(page), int(qno)))
        es_by_book_page[(_fold(book), int(page))].append(int(qno))

print(
    f"[indexed] gem crops: {len(gem_by_crop):,} | gem text-p100: {len(gem_by_text_p100):,}"
)
print(
    f"[indexed] es text-p100: {len(es_by_text_p100):,} | es (book,page): {len(es_by_book_page):,}\n"
)

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Pull ALL rows where strategy is v8/v9/v10b OR row hits same-page-diff-crop
print("[query] all HAS-image rows with crop-level URL (not _PAGE)...")
with eng.connect() as c:
    all_rows = c.execute(
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
          AND option_a IS NOT NULL AND option_e IS NOT NULL
        """)
    ).fetchall()
print(f"[got] {len(all_rows):,} candidate rows\n")


def parse_url(url):
    if not url or not url.startswith("/static/crops/"):
        return None, None, None, None
    rel = url[len("/static/crops/") :]
    parts = rel.split("/")
    if len(parts) != 2:
        return None, None, None, None
    book_dir, fname = parts
    m = re.search(r"_p(\d+)_(q\d+|LM\d+)\.", fname)
    if not m:
        return book_dir, fname, None, None
    page = int(m.group(1))
    suffix = m.group(2)
    qno = (
        int(suffix[1:])
        if suffix.startswith("q") and not suffix.startswith("LM")
        else suffix
    )
    return book_dir, fname, page, qno


def get_strategy(pm_str):
    if not pm_str:
        return "no_metadata"
    for f in [
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
    ]:
        if f'"image_match_{f}"' in pm_str:
            return f
    return "legacy_pre_s157"


def opts_match(db_opts, jsonl_opts):
    """Count matching options. Returns (matches, total_non_empty)."""
    matches = 0
    non_empty = 0
    for k in "ABCDE":
        db_v = _norm_opt(db_opts.get(k, ""))
        j_v = jsonl_opts.get(k, "")
        if not db_v or not j_v:
            continue
        non_empty += 1
        if db_v == j_v:
            matches += 1
    return matches, non_empty


# Classify each row
audit_results = Counter()
strategy_results = defaultdict(Counter)
options_match_dist = Counter()
samples_per_verdict = defaultdict(list)

GEMINI_DERIVED = {
    "gemini_flash_v8",
    "gemini_flash_v9_loose",
    "v10b_options_strict",
    "v14_jaccard",
}
ESLESMIS_DERIVED = {"rebuild_v5", "jsonl_v2", "fuzzy_v3"}

processed = 0
for r in all_rows:
    book_dir, fname, url_page, url_qno = parse_url(r.question_image_url)
    if not book_dir or fname is None:
        audit_results["INVALID_URL"] += 1
        continue

    strategy = get_strategy(r.pm)

    # Look up URL's crop in gemini → get its options
    gem_entry = gem_by_crop.get(fname)
    db_opts = {
        "A": r.option_a or "",
        "B": r.option_b or "",
        "C": r.option_c or "",
        "D": r.option_d or "",
        "E": r.option_e or "",
    }

    if not gem_entry:
        audit_results["CROP_NOT_IN_GEMINI"] += 1
        strategy_results[strategy]["CROP_NOT_IN_GEMINI"] += 1
        continue

    # Options match check (INDEPENDENT signal)
    m_count, total_opts = opts_match(db_opts, gem_entry["opts"])
    if total_opts < 3:
        audit_results["NOT_ENOUGH_OPTIONS"] += 1
        continue

    options_match_dist[f"{m_count}/{total_opts}"] += 1

    # Verdict based on options match
    if m_count == total_opts and total_opts >= 5:
        verdict = "OPT_5_5_PERFECT"
    elif m_count == total_opts:  # 3/3 or 4/4
        verdict = "OPT_ALL_MATCH"
    elif m_count >= total_opts - 1 and total_opts >= 4:
        verdict = "OPT_NEAR_MATCH"
    elif m_count >= total_opts / 2:
        verdict = "OPT_PARTIAL"
    else:
        verdict = "OPT_FAIL"

    audit_results[verdict] += 1
    strategy_results[strategy][verdict] += 1

    # Save samples
    if len(samples_per_verdict[verdict]) < 3:
        samples_per_verdict[verdict].append(
            {
                "id": r.id[:8],
                "strategy": strategy,
                "fname": fname,
                "db_opts": {k: db_opts[k][:30] for k in "ABCDE"},
                "jsonl_opts": {k: gem_entry["opts"][k][:30] for k in "ABCDE"},
                "match": f"{m_count}/{total_opts}",
            }
        )

    processed += 1

print(f"[processed] {processed:,} rows audited with options\n")

# Report
print("=" * 80)
print(f"OPTIONS-BASED AUDIT (n={processed})")
print("=" * 80)
print(f"\n{'Verdict':<25s} {'Count':>7s} {'Pct':>7s}")
print("-" * 45)
for v, n in audit_results.most_common():
    print(f"{v:<25s} {n:>7,} {n / sum(audit_results.values()) * 100:>6.2f}%")

print()
print("=" * 80)
print("PER-STRATEGY OPTIONS-MATCH ACCURACY")
print("=" * 80)
print(
    f"\n{'Strategy':<25s} {'Total':>7s} {'Perfect':>9s} {'Near':>7s} {'Partial':>9s} {'Fail':>7s} {'Acc%':>6s}"
)
print("-" * 75)
for strat in sorted(
    strategy_results.keys(), key=lambda s: -sum(strategy_results[s].values())
):
    counts = strategy_results[strat]
    total = sum(counts.values())
    perfect = counts.get("OPT_5_5_PERFECT", 0) + counts.get("OPT_ALL_MATCH", 0)
    near = counts.get("OPT_NEAR_MATCH", 0)
    partial = counts.get("OPT_PARTIAL", 0)
    fail = counts.get("OPT_FAIL", 0)
    missing = counts.get("CROP_NOT_IN_GEMINI", 0)
    audited = perfect + near + partial + fail
    acc = (perfect + near) / audited * 100 if audited else 0
    print(
        f"{strat:<25s} {total:>7,} {perfect:>9,} {near:>7,} {partial:>9,} {fail:>7,} {acc:>5.1f}%"
    )

# Options match distribution
print()
print("=" * 80)
print("OPTIONS MATCH SCORE DISTRIBUTION")
print("=" * 80)
for k, v in sorted(options_match_dist.items()):
    print(f"  {k}: {v:,}")

# Samples
print()
print("=" * 80)
print("SAMPLES PER VERDICT")
print("=" * 80)
for v in ["OPT_5_5_PERFECT", "OPT_NEAR_MATCH", "OPT_PARTIAL", "OPT_FAIL"]:
    samples = samples_per_verdict.get(v, [])
    if samples:
        print(f"\n--- {v} ---")
        for s in samples[:2]:
            print(f"  {s['id']} [{s['strategy']}] match={s['match']}")
            for k in "ABCDE":
                d = s["db_opts"][k][:30]
                j = s["jsonl_opts"][k][:30]
                marker = "✓" if _norm_opt(d) == _norm_opt(j) and d else " "
                print(f"    {k}: {marker} db={d!r:35s} jsonl={j!r}")

print()
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
perfect = audit_results.get("OPT_5_5_PERFECT", 0) + audit_results.get(
    "OPT_ALL_MATCH", 0
)
near = audit_results.get("OPT_NEAR_MATCH", 0)
partial = audit_results.get("OPT_PARTIAL", 0)
fail = audit_results.get("OPT_FAIL", 0)
missing = audit_results.get("CROP_NOT_IN_GEMINI", 0)
total_audited = perfect + near + partial + fail
print(f"  TOTAL HAS-image audited:     {len(all_rows):,}")
print(f"  Crop in gemini index:        {processed:,}")
print(f"  Crop NOT in gemini:          {missing:,}")
print()
print(
    f"  ✅ PERFECT (all opts match):  {perfect:,}  ({perfect / total_audited * 100:.2f}%)"
)
print(f"  ✅ NEAR  (n-1 of n match):    {near:,}  ({near / total_audited * 100:.2f}%)")
print(
    f"  ⚠️  PARTIAL (≥50% match):     {partial:,}  ({partial / total_audited * 100:.2f}%)"
)
print(f"  ❌ FAIL (<50% match):         {fail:,}  ({fail / total_audited * 100:.2f}%)")
print()
print(f"  💎 KESIN DOĞRU (perfect):     {perfect:,}")
print(
    f"  ✅ HIGH CONFIDENT (perf+near):{perfect + near:,}  ({(perfect + near) / total_audited * 100:.1f}%)"
)
print(
    f"  ❌ LIKELY WRONG (partial+fail):{partial + fail:,}  ({(partial + fail) / total_audited * 100:.1f}%)"
)
