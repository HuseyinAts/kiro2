#!/usr/bin/env python3
"""
Content correctness audit: cross-check each tier's image_url against JSONL truth.

Method:
  1. Load JSONL prefix index (text_prefix → list[(book, page, qno)])
  2. For each tier, take 50 random samples
  3. Parse image_url → (book_dir, page, qno_from_url)
  4. Lookup DB question_text in JSONL → (book, page, qno_truth)
  5. Match if image_url's (page, qno) == truth's (page, qno)
"""

import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
JSONL_PATH = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"


def _norm_loose(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9çğıöşüâîû]", "", text)
    return text


def _fold(s: str) -> str:
    tr_map = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")
    return s.translate(tr_map).lower()


PREFIX_LEN = 80

print("[load] JSONL → prefix index...")
idx: defaultdict = defaultdict(list)
with JSONL_PATH.open(encoding="utf-8") as f:
    for line in f:
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        text = d.get("text") or ""
        book = d.get("book_name", "")
        page = d.get("page_number")
        qno = d.get("question_number")
        if not (text and book and page and qno):
            continue
        normed = _norm_loose(text)
        if len(normed) < PREFIX_LEN:
            normed = normed.ljust(PREFIX_LEN)
        idx[normed[:PREFIX_LEN]].append((book, int(page), int(qno)))
print(f"[done] {len(idx):,} unique prefixes\n")


def parse_url(url: str) -> tuple[str, int, int] | None:
    """/static/crops/<book>/<book>_pNNNN_qXX.png → (book, page, qno)"""
    if not url or not url.startswith("/static/crops/"):
        return None
    rel = url[len("/static/crops/") :]
    parts = rel.split("/")
    if len(parts) != 2:
        return None
    book_dir, fname = parts
    m = re.search(r"_p(\d{4})_q(\d+)\.", fname)
    if not m:
        return None
    return book_dir, int(m.group(1)), int(m.group(2))


from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

tiers = [
    "image_match_metadata_v1",
    "image_match_jsonl_v2",
    "image_match_fuzzy_v3",
    "image_match_book_page_v4",
]

print("# Content Audit per Tier (50 random sample each)\n")

for tier in tiers:
    sql = text(f"""
        SELECT id::text, source_book, question_text, question_image_url
        FROM question_bank
        WHERE pipeline_metadata::jsonb ? '{tier}'
          AND question_image_url IS NOT NULL
          AND question_text IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 50
    """)
    with eng.connect() as c:
        rows = c.execute(sql).fetchall()

    matched, mismatch_pageqno, no_jsonl, parse_fail = 0, 0, 0, 0
    mismatch_samples = []

    for r in rows:
        parsed = parse_url(r.question_image_url)
        if not parsed:
            parse_fail += 1
            continue
        url_book, url_page, url_qno = parsed

        # Lookup DB question_text in JSONL
        normed = _norm_loose(r.question_text)
        if len(normed) < PREFIX_LEN:
            normed = normed.ljust(PREFIX_LEN)
        prefix = normed[:PREFIX_LEN]
        truth_candidates = idx.get(prefix, [])

        if not truth_candidates:
            no_jsonl += 1
            continue

        # Prefer same-book; fall back to any
        best_truth = None
        url_book_folded = _fold(url_book)
        for tb, tp, tq in truth_candidates:
            if _fold(tb).replace(" ", "_") == url_book_folded:
                best_truth = (tb, tp, tq)
                break
        if not best_truth:
            best_truth = truth_candidates[0]

        truth_book, truth_page, truth_qno = best_truth

        # Compare page + qno (book is implied if folded matches)
        if truth_page == url_page and truth_qno == url_qno:
            matched += 1
        else:
            mismatch_pageqno += 1
            if len(mismatch_samples) < 3:
                mismatch_samples.append(
                    {
                        "id": r.id[:8],
                        "url": r.question_image_url[:100],
                        "url_p_q": f"p{url_page} q{url_qno}",
                        "truth_p_q": f"p{truth_page} q{truth_qno}",
                        "truth_book": truth_book[:40],
                    }
                )

    total = matched + mismatch_pageqno + no_jsonl + parse_fail
    print(f"## {tier} (N={total})")
    print(
        f"  matched         : {matched:>3} ({matched / total * 100 if total else 0:.1f}%)"
    )
    print(
        f"  mismatch_page/qno: {mismatch_pageqno:>3} ({mismatch_pageqno / total * 100 if total else 0:.1f}%)"
    )
    print(
        f"  no_jsonl_entry  : {no_jsonl:>3} ({no_jsonl / total * 100 if total else 0:.1f}%)"
    )
    print(f"  parse_fail      : {parse_fail:>3}")
    if mismatch_samples:
        print("  mismatch samples:")
        for s in mismatch_samples:
            print(
                f"    {s['id']} {s['url_p_q']} vs truth {s['truth_p_q']} ({s['truth_book']})"
            )
    print()
