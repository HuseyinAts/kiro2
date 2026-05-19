#!/usr/bin/env python3
"""
PILOT v2: For N-to-N (book, page) groups, attempt text-based assignment.

For each group with N DB rows and N disk crops:
  - Look up each DB question_text in JSONL → may yield (book, page, qno) truth
  - If truth says "this text is qno=8 on page 187", check if disk has q08 crop
  - That's the correct match (regardless of ordering)

This bypasses the ordering problem entirely if we have JSONL truth.
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
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _norm(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", text)


def _fold(s):
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


print("[load] JSONL...")
# Build BOTH: exact-hash + prefix index for text lookup
jsonl_by_prefix = defaultdict(list)  # short_prefix → [(book, page, qno, full_norm)]
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
        if len(normed) < 40:
            continue
        key = normed[:40]
        jsonl_by_prefix[key].append((book, int(page), int(qno), normed))
print(f"[done] {len(jsonl_by_prefix):,} prefixes\n")

from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

with eng.connect() as c:
    rows = c.execute(
        sa_text("""
        SELECT id::text, source_book, question_text,
               pipeline_metadata::text AS pm
        FROM question_bank
        WHERE is_active=true
          AND (question_image_url IS NULL OR question_image_url='')
          AND source_book IS NOT NULL
          AND pipeline_metadata::jsonb ? 'request_key'
        """)
    ).fetchall()

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
    groups[(r.source_book, page)].append({"id": r.id, "text": r.question_text})

# Filter N-to-N
n_to_n = []
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
    n_to_n.append((book, page, book_dir, row_list, questions, dir_path))

print(f"[total] N-to-N groups: {len(n_to_n):,}\n")

# For each group, look up each DB row in JSONL → get truth qno
matches_to_apply = []
no_jsonl = 0
disk_missing = 0
verified_count = 0

for book, page, book_dir, row_list, disk_qs, dir_path in n_to_n:
    sb_folded = _fold(book)
    # Build disk index map: qno → crop filename
    disk_by_idx = {q.get("index"): q.get("crop") for q in disk_qs}

    for db_row in row_list:
        normed = _norm(db_row["text"])
        if len(normed) < 40:
            no_jsonl += 1
            continue

        # Try prefix lookup
        cands = jsonl_by_prefix.get(normed[:40], [])
        truth_qno = None
        for tb, tp, tq, tnorm in cands:
            if _fold(tb) == sb_folded and tp == page:
                # Tighter check: does full normed match?
                # Use the longer of the two for prefix comparison
                min_len = min(len(normed), len(tnorm))
                if (min_len >= 80 and normed[:80] == tnorm[:80]) or normed == tnorm:
                    truth_qno = tq
                    break

        if truth_qno is None:
            no_jsonl += 1
            continue

        # Truth says this text is qno=X on this page → check disk has q0X crop
        crop_name = disk_by_idx.get(truth_qno)
        if not crop_name:
            disk_missing += 1
            continue
        if not (dir_path / crop_name).exists():
            disk_missing += 1
            continue

        url = f"/static/crops/{book_dir}/{crop_name}"
        matches_to_apply.append((db_row["id"], url, book, page, truth_qno))
        verified_count += 1

print("[result]")
print(f"  verified (DB↔JSONL↔disk): {verified_count:,}")
print(f"  no_jsonl_match:           {no_jsonl:,}")
print(f"  disk_qno_missing:         {disk_missing:,}")
print(f"  total_to_apply:           {len(matches_to_apply):,}")

# Sample preview
print("\n[sample first 5]")
for m in matches_to_apply[:5]:
    print(f"  {m[0][:8]} {m[2][:25]} p{m[3]} q{m[4]} → {m[1][-50:]}")

# Save to TSV for apply
out = PROJECT_ROOT / "backend" / "_pilots" / "n_to_n_text_matches.tsv"
with out.open("w", encoding="utf-8") as f:
    f.write("id\turl\tbook\tpage\tqno\n")
    for qid, url, book, page, qno in matches_to_apply:
        f.write(f"{qid}\t{url}\t{book}\t{page}\t{qno}\n")
print(f"\n[saved] {out}")
