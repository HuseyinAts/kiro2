#!/usr/bin/env python3
"""
Strategy C: Unused-crop narrow-down.

For each (book, page) group:
  1. Find disk crops (meta.json questions)
  2. Find which crops are already referenced by WITH-image rows
  3. Compute unused_crops = disk - used
  4. If null_count == 1 AND unused == 1 → deterministic match
  5. If null_count == unused (small N), defer (ordering 0%)

This refines v6 by accounting for already-used crops on the page.
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


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


from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

# Get ALL active rows (both NULL and WITH-image) to compute usage
print("[scan] all active rows with source_book+page or request_key...")
with eng.connect() as c:
    rows = c.execute(
        text("""
        SELECT id::text, source_book, source_page, question_image_url,
               pipeline_metadata::text AS pm
        FROM question_bank
        WHERE is_active=true
          AND source_book IS NOT NULL
        """)
    ).fetchall()
print(f"[loaded] {len(rows):,} active rows")

# Group by (book, page) — use source_page directly when available, else parse request_key
groups: defaultdict[tuple[str, int], dict] = defaultdict(
    lambda: {"null_ids": [], "used_crops": set()}
)
for r in rows:
    page = r.source_page
    if page is None and r.pm:
        try:
            pm = json.loads(r.pm)
            rk = pm.get("request_key", "")
            m = re.search(r"sayfa_(\d+)", rk)
            if m:
                page = int(m.group(1))
        except json.JSONDecodeError:
            continue
    if page is None:
        continue

    key = (r.source_book, int(page))
    if not r.question_image_url:
        groups[key]["null_ids"].append(r.id)
    else:
        # Parse filename qNN from URL
        m = re.search(r"_p\d+_q(\d+)\.", r.question_image_url)
        if m:
            groups[key]["used_crops"].add(int(m.group(1)))

print(f"[groups] {len(groups):,} (book, page) groups\n")

# For each group, check unused crop math
matches = []
stats = {"deterministic": 0, "ambiguous": 0, "no_meta": 0, "no_null": 0}

for (book, page), g in groups.items():
    if not g["null_ids"]:
        stats["no_null"] += 1
        continue

    book_dir = find_disk_dir(book)
    if not book_dir:
        stats["no_meta"] += 1
        continue
    meta_path = CROPS_BASE / book_dir / f"{book_dir}_p{page:04d}_meta.json"
    if not meta_path.exists():
        stats["no_meta"] += 1
        continue
    try:
        md = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        stats["no_meta"] += 1
        continue
    questions = md.get("questions", [])
    if not questions:
        stats["no_meta"] += 1
        continue

    disk_indices = {q.get("index") for q in questions if q.get("index") is not None}
    unused = disk_indices - g["used_crops"]
    null_count = len(g["null_ids"])

    if null_count == 1 and len(unused) == 1:
        # Deterministic: exactly 1 NULL, exactly 1 unused crop
        target_idx = next(iter(unused))
        crop = next((q for q in questions if q.get("index") == target_idx), None)
        if crop and crop.get("crop"):
            crop_path = CROPS_BASE / book_dir / crop["crop"]
            if crop_path.exists():
                url = f"/static/crops/{book_dir}/{crop['crop']}"
                matches.append(
                    (
                        g["null_ids"][0],
                        url,
                        book[:30],
                        page,
                        target_idx,
                        "1-unused-1-null",
                    )
                )
                stats["deterministic"] += 1
    else:
        stats["ambiguous"] += 1

print("[result]")
for k, v in stats.items():
    print(f"  {k:18s}: {v:,}")
print(f"\n[deterministic matches]: {len(matches):,}")

if matches:
    print("\n[sample first 3]")
    for m in matches[:3]:
        print(f"  {m[0][:8]} {m[2]} p{m[3]} q{m[4]} → {m[1][-50:]}")

    print(f"\n[apply] UPDATE {len(matches):,} satır...")
    for i in range(0, len(matches), 500):
        batch = matches[i : i + 500]
        with eng.begin() as c:
            for qid, url, book, page, qno, reason in batch:
                c.execute(
                    text("""
                        UPDATE question_bank
                        SET question_image_url=:url,
                            pipeline_metadata = jsonb_set(
                                COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                '{image_match_strategy_c_unused}',
                                CAST(:audit AS jsonb),
                                TRUE
                            )::json,
                            updated_at=NOW()
                        WHERE id::text=:qid
                    """),
                    {
                        "url": url,
                        "qid": qid,
                        "audit": json.dumps(
                            {
                                "date": "2026-05-19",
                                "source": "strategy_c_unused_crop",
                                "page": int(page),
                                "target_idx": int(qno),
                                "reason": reason,
                            }
                        ),
                    },
                )
    print("[done]")

with eng.connect() as c:
    null_n = c.execute(
        text(
            "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
            "AND (question_image_url IS NULL OR question_image_url='')"
        )
    ).scalar()
    print(f"\nFINAL NULL: {null_n:,}")
