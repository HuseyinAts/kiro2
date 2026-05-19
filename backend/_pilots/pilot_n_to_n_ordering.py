#!/usr/bin/env python3
"""
PILOT: N-to-N (book, page) groups where DB count == disk count.

Strategy:
  - Sort disk crops by bbox.y (reading order, top→bottom)
  - Sort DB rows by created_at (insertion order proxy)
  - 1-to-1 pair them
  - Cross-check each pair against JSONL truth (normalized text match)
  - Report accuracy

This is a READ-ONLY audit. No DB writes.
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

PROJECT_ROOT = Path(__file__).parent.parent.parent
JSONL_PATH = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"

random.seed(42)


def _norm(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", text)


def _fold(s: str) -> str:
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


_DISK_DIRS = None
_BOOK_CACHE = {}


def find_disk_dir(book):
    global _DISK_DIRS
    if not book:
        return None
    if book in _BOOK_CACHE:
        return _BOOK_CACHE[book] or None
    if _DISK_DIRS is None:
        _DISK_DIRS = sorted(d.name for d in CROPS_BASE.iterdir() if d.is_dir())
    for v in [book.replace(" ", "_"), re.sub(r"\s+", "_", book.strip())]:
        if v in _DISK_DIRS:
            _BOOK_CACHE[book] = v
            return v
    folded = _fold(book.replace(" ", "_"))
    for d in _DISK_DIRS:
        if _fold(d) == folded:
            _BOOK_CACHE[book] = d
            return d
    _BOOK_CACHE[book] = ""
    return None


# Build JSONL prefix index for ground-truth verification
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
        if len(normed) < 60:
            continue
        jsonl_idx[normed[:80]].append((book, int(page), int(qno)))
print(f"[done] {len(jsonl_idx):,} unique prefixes\n")

from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Get NULL rows with request_key
with eng.connect() as c:
    rows = c.execute(
        text("""
        SELECT id::text, source_book, question_text,
               pipeline_metadata::text AS pm,
               created_at
        FROM question_bank
        WHERE is_active=true
          AND (question_image_url IS NULL OR question_image_url='')
          AND source_book IS NOT NULL
          AND pipeline_metadata::jsonb ? 'request_key'
        """)
    ).fetchall()

# Group by (book, page) and capture row metadata
groups = defaultdict(list)
for r in rows:
    try:
        pm = json.loads(r.pm)
    except json.JSONDecodeError:
        continue
    rk = pm.get("request_key", "")
    m = re.search(r"sayfa_(\d+)", rk)
    if not m:
        continue
    page = int(m.group(1))
    ai = pm.get("ai_extras", {}) or {}
    qip = ai.get("q_index_in_page")
    try:
        qip_int = int(qip) if qip is not None else None
    except (ValueError, TypeError):
        qip_int = None
    groups[(r.source_book, page)].append(
        {
            "id": r.id,
            "text": r.question_text,
            "created_at": r.created_at,
            "q_index_in_page": qip_int,
        }
    )

# Filter to N-to-N where N>=2
n_to_n_groups = []
for (book, page), row_list in groups.items():
    book_dir = find_disk_dir(book)
    if not book_dir:
        continue
    dir_path = CROPS_BASE / book_dir
    meta_path = dir_path / f"{book_dir}_p{page:04d}_meta.json"
    if not meta_path.exists():
        continue
    try:
        md = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        continue
    questions = md.get("questions", [])
    if len(questions) != len(row_list) or len(row_list) < 2:
        continue
    n_to_n_groups.append((book, page, book_dir, row_list, questions))

print(f"[total] N-to-N matchable groups: {len(n_to_n_groups):,}\n")

# Sample 100 random groups for pilot
sample = random.sample(n_to_n_groups, min(100, len(n_to_n_groups)))
print(f"[pilot] sampling {len(sample)} groups\n")

# For each group, try TWO ordering strategies and check accuracy
results = {
    "by_created_at": {"correct": 0, "wrong": 0, "no_truth": 0},
    "by_qip": {"correct": 0, "wrong": 0, "no_truth": 0, "no_qip": 0},
}

mismatch_examples = []

for book, page, book_dir, row_list, disk_qs in sample:
    # Sort disk crops by bbox y1 (reading order: top→bottom, then left→right)
    def bbox_key(q):
        bbox = q.get("bbox") or [0, 0, 0, 0]
        # bbox = [x1, y1, x2, y2]
        return (bbox[1], bbox[0]) if len(bbox) >= 2 else (q.get("index", 999), 0)

    disk_sorted = sorted(disk_qs, key=bbox_key)

    # Strategy 1: sort DB rows by created_at
    db_by_created = sorted(row_list, key=lambda r: r["created_at"])

    # Strategy 2: sort DB rows by q_index_in_page (if all have it)
    qips = [r["q_index_in_page"] for r in row_list]
    has_all_qip = all(q is not None for q in qips)

    for strategy_name, db_sorted in [
        ("by_created_at", db_by_created),
        (
            "by_qip",
            sorted(row_list, key=lambda r: r["q_index_in_page"] or 999)
            if has_all_qip
            else None,
        ),
    ]:
        if db_sorted is None:
            results[strategy_name]["no_qip"] += len(row_list)
            continue

        for db_row, disk_q in zip(db_sorted, disk_sorted):
            # Check against JSONL
            normed = _norm(db_row["text"])
            if len(normed) < 60:
                results[strategy_name]["no_truth"] += 1
                continue
            cands = jsonl_idx.get(normed[:80], [])
            if not cands:
                results[strategy_name]["no_truth"] += 1
                continue

            # Find truth qno
            sb_folded = _fold(book)
            truth_qno = None
            for tb, tp, tq in cands:
                if _fold(tb) == sb_folded and tp == page:
                    truth_qno = tq
                    break
            if truth_qno is None:
                # Try any book-match
                for tb, tp, tq in cands:
                    if _fold(tb) == sb_folded:
                        truth_qno = tq
                        break
            if truth_qno is None:
                results[strategy_name]["no_truth"] += 1
                continue

            # disk_q index is 1-based (from filename qNN)
            disk_idx = disk_q.get("index", 0)
            if disk_idx == truth_qno:
                results[strategy_name]["correct"] += 1
            else:
                results[strategy_name]["wrong"] += 1
                if len(mismatch_examples) < 5 and strategy_name == "by_created_at":
                    mismatch_examples.append(
                        {
                            "book": book[:30],
                            "page": page,
                            "db_text": db_row["text"][:80],
                            "mapped_disk_idx": disk_idx,
                            "truth_qno": truth_qno,
                        }
                    )

print("[results]")
for strategy, stats in results.items():
    total_verifiable = stats["correct"] + stats["wrong"]
    acc = stats["correct"] / total_verifiable * 100 if total_verifiable else 0
    print(f"  {strategy}:")
    print(f"    correct: {stats['correct']:,}")
    print(f"    wrong:   {stats['wrong']:,}")
    print(f"    no_truth: {stats['no_truth']:,}")
    if "no_qip" in stats:
        print(f"    no_qip:   {stats['no_qip']:,}")
    print(f"    accuracy: {acc:.1f}% (on verifiable)")
    print()

if mismatch_examples:
    print("[mismatch examples — by_created_at]")
    for ex in mismatch_examples:
        print(
            f"  {ex['book']} p{ex['page']} q{ex['truth_qno']} → mapped to q{ex['mapped_disk_idx']}"
        )
        print(f"    text: {ex['db_text']}")
