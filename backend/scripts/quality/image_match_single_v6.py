#!/usr/bin/env python3
"""
Image match v6 — Deterministic single-row + single-crop match.

For (book, page) combinations where DB has exactly 1 question AND
disk has exactly 1 crop → unambiguous match, apply it.

This is the only safe deterministic strategy when JSONL doesn't cover
the row. NO ambiguity, NO guessing.
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
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

# Step 1: Gather NULL rows with request_key
with eng.connect() as c:
    rows = c.execute(
        text(
            """
        SELECT id::text, source_book, pipeline_metadata::text AS pm
        FROM question_bank
        WHERE is_active=true
          AND (question_image_url IS NULL OR question_image_url='')
          AND source_book IS NOT NULL
          AND pipeline_metadata::jsonb ? 'request_key'
        """
        )
    ).fetchall()

print(f"NULL with request_key: {len(rows):,}")

# Step 2: Group by (book, page)
groups: defaultdict[tuple[str, int], list[str]] = defaultdict(list)
for r in rows:
    pm = json.loads(r.pm)
    rk = pm.get("request_key", "")
    m = re.search(r"sayfa_(\d+)", rk)
    if not m:
        continue
    page = int(m.group(1))
    groups[(r.source_book, page)].append(r.id)

print(f"(book, page) groups: {len(groups):,}")

# Step 3: For each group, check disk meta.json
single_match_count = 0
n_to_n_count = 0
matches: list[tuple[str, str]] = []  # (id, url)

for (book, page), row_ids in groups.items():
    book_dir = find_disk_dir(book)
    if not book_dir:
        continue
    dir_path = CROPS_BASE / book_dir
    meta_path = dir_path / f"{book_dir}_p{page:04d}_meta.json"
    if not meta_path.exists():
        continue
    try:
        md = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        continue
    questions = md.get("questions", [])
    if not questions:
        continue

    # Case 1: Single DB row + single disk crop = unambiguous
    if len(row_ids) == 1 and len(questions) == 1:
        crop_name = questions[0].get("crop")
        if crop_name and (dir_path / crop_name).exists():
            url = f"/static/crops/{book_dir}/{crop_name}"
            matches.append((row_ids[0], url))
            single_match_count += 1

print("\n[result]")
print(f"  single_match (1 DB + 1 disk): {single_match_count:,}")
print(f"  n-to-n potential (skip): {n_to_n_count:,}")

# Step 4: Apply
if matches:
    print(f"\n[apply] {len(matches):,} satır UPDATE")
    for i in range(0, len(matches), 500):
        batch = matches[i : i + 500]
        with eng.begin() as c:
            for qid, url in batch:
                c.execute(
                    text(
                        """
                        UPDATE question_bank
                        SET question_image_url=:url,
                            pipeline_metadata = jsonb_set(
                                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                '{image_match_single_v6}',
                                CAST(:audit AS jsonb),
                                TRUE
                            )::json,
                            updated_at=NOW()
                        WHERE id::text=:qid
                        """
                    ),
                    {
                        "url": url,
                        "qid": qid,
                        "audit": '{"date":"2026-05-19","source":"v6_single_row_single_crop"}',
                    },
                )
        if (i // 500 + 1) % 5 == 0:
            print(f"  batch {i // 500 + 1}")
    print("[done]")

# Final
with eng.connect() as c:
    null_n = c.execute(
        text(
            "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
            "AND (question_image_url IS NULL OR question_image_url='')"
        )
    ).scalar()
    print(f"\nFINAL NULL: {null_n:,}")
