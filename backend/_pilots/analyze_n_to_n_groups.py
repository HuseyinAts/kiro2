#!/usr/bin/env python3
"""Analyze N-to-N (book, page) groups: DB row count vs disk crop count distribution."""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _fold(s: str) -> str:
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


_DISK_DIRS = None
_BOOK_CACHE: dict[str, str] = {}


def find_disk_dir(book: str) -> str | None:
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
    db_tokens = set(_fold(book).split()) - {"soru", "bankası", "bankasi"}
    if len(db_tokens) >= 3:
        best, best_score = None, 0
        for d in _DISK_DIRS:
            d_tokens = set(_fold(d.replace("_", " ")).split()) - {
                "soru",
                "bankası",
                "bankasi",
            }
            common = db_tokens & d_tokens
            if len(common) > best_score:
                best, best_score = d, len(common)
        if best_score >= max(3, len(db_tokens) - 1):
            _BOOK_CACHE[book] = best
            return best
    _BOOK_CACHE[book] = ""
    return None


from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

with eng.connect() as c:
    rows = c.execute(
        text("""
        SELECT id::text, source_book, pipeline_metadata::text AS pm
        FROM question_bank
        WHERE is_active=true
          AND (question_image_url IS NULL OR question_image_url='')
          AND source_book IS NOT NULL
          AND pipeline_metadata::jsonb ? 'request_key'
        """)
    ).fetchall()

print(f"NULL with request_key: {len(rows):,}")

groups: defaultdict[tuple[str, int], list[str]] = defaultdict(list)
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
    groups[(r.source_book, page)].append(r.id)

# Match against disk
distribution = Counter()
matchable_n_to_n = 0
n_to_n_breakdown = Counter()

for (book, page), row_ids in groups.items():
    book_dir = find_disk_dir(book)
    if not book_dir:
        distribution["no_book_dir"] += 1
        continue
    dir_path = CROPS_BASE / book_dir
    meta_path = dir_path / f"{book_dir}_p{page:04d}_meta.json"
    if not meta_path.exists():
        distribution["no_meta"] += 1
        continue
    try:
        md = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        distribution["bad_meta"] += 1
        continue
    questions = md.get("questions", [])
    if not questions:
        distribution["empty_meta"] += 1
        continue

    db_n = len(row_ids)
    disk_n = len(questions)
    key = f"db{db_n}_disk{disk_n}"
    distribution[key] += 1
    if db_n == disk_n and db_n >= 2:
        matchable_n_to_n += 1
        n_to_n_breakdown[f"{db_n}x{db_n}"] += 1

print("\n[distribution] top 30")
for k, v in distribution.most_common(30):
    print(f"  {k:20s} : {v:,}")

print("\n[summary]")
print(f"  Matchable N-to-N (equal count, N>=2): {matchable_n_to_n:,} groups")
for k, v in sorted(n_to_n_breakdown.items()):
    n = int(k.split("x")[0])
    print(f"    {k}: {v:,} groups → {v * n:,} rows")
