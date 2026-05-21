#!/usr/bin/env python3
"""
Audit v15 PAGE fallback metadata consistency.

For each v15 PAGE row, verify:
  - URL book_dir matches source_book (canonical)
  - URL page matches source_page
  - PNG file exists on disk

If mismatch, rollback to NULL.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _canon(s):
    return re.sub(r"\W+", "_", _fold(s or "")).strip("_")


from sqlalchemy import create_engine
from sqlalchemy import text as sa_text

eng = create_engine(
    os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
)

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()

with eng.connect() as c:
    rows = c.execute(
        sa_text("""
        SELECT id::text, source_book, source_page, question_image_url
        FROM question_bank
        WHERE is_active=true
          AND question_image_url LIKE '%_PAGE.png'
        """)
    ).fetchall()

print(f"[scan] {len(rows):,} v15 PAGE rows\n")

stats = Counter()
rollback_ids = []
sample_examples = []

for r in rows:
    url = r.question_image_url or ""
    if not url.startswith("/static/crops/"):
        stats["INVALID_URL"] += 1
        rollback_ids.append(r.id)
        continue

    rel = url[len("/static/crops/") :]
    parts = rel.split("/")
    if len(parts) != 2:
        stats["INVALID_URL"] += 1
        rollback_ids.append(r.id)
        continue
    book_dir, fname = parts

    m = re.search(r"_p(\d+)_PAGE\.png", fname)
    if not m:
        stats["INVALID_FNAME"] += 1
        rollback_ids.append(r.id)
        continue
    url_page = int(m.group(1))

    # File existence
    fpath = CROPS_BASE / book_dir / fname
    if not fpath.exists():
        stats["FILE_MISSING"] += 1
        rollback_ids.append(r.id)
        continue

    # Book consistency
    db_canon = _canon(r.source_book or "")
    url_canon = _canon(book_dir)
    if not db_canon or not url_canon:
        stats["MISSING_BOOK"] += 1
        continue

    # Permissive match: one must be prefix of other (for truncation cases)
    if (
        db_canon == url_canon
        or db_canon.startswith(url_canon[: min(len(url_canon), 30)])
        or url_canon.startswith(db_canon[: min(len(db_canon), 30)])
    ):
        book_match = True
    else:
        # Token overlap
        ta = set(re.findall(r"[a-z0-9]{3,}", db_canon))
        tb = set(re.findall(r"[a-z0-9]{3,}", url_canon))
        sim = len(ta & tb) / len(ta | tb) if (ta and tb) else 0
        book_match = sim >= 0.5

    # Page consistency
    page_match = r.source_page == url_page

    if book_match and page_match:
        stats["OK"] += 1
    elif book_match and not page_match:
        stats["WRONG_PAGE"] += 1
        rollback_ids.append(r.id)
        if len(sample_examples) < 5:
            sample_examples.append(
                f"  {r.id[:8]} url_page={url_page} db_page={r.source_page} book_ok"
            )
    elif not book_match and page_match:
        stats["WRONG_BOOK"] += 1
        rollback_ids.append(r.id)
        if len(sample_examples) < 5:
            sample_examples.append(
                f"  {r.id[:8]} url={book_dir[:40]} db={(r.source_book or '')[:40]}"
            )
    else:
        stats["WRONG_BOTH"] += 1
        rollback_ids.append(r.id)
        if len(sample_examples) < 5:
            sample_examples.append(
                f"  {r.id[:8]} url=({book_dir[:30]}, p{url_page}) db=({(r.source_book or '')[:30]}, p{r.source_page})"
            )

print("[result]")
for k, v in stats.most_common():
    print(f"  {k}: {v:,}")

print(f"\n[rollback candidates]: {len(rollback_ids):,}")
print("\n[sample failures]")
for ex in sample_examples:
    print(ex)

if args.apply and rollback_ids:
    print(f"\n[apply] rollback {len(rollback_ids):,} satır...")
    for i in range(0, len(rollback_ids), 1000):
        batch = rollback_ids[i : i + 1000]
        with eng.begin() as c:
            c.execute(
                sa_text("""
                UPDATE question_bank
                SET question_image_url = NULL,
                    pipeline_metadata = jsonb_set(
                        COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                        '{v15_page_rollback}',
                        CAST(:audit AS jsonb),
                        TRUE
                    )::json,
                    updated_at = NOW()
                WHERE id::text = ANY(:ids)
                """),
                {
                    "ids": batch,
                    "audit": json.dumps(
                        {
                            "date": "2026-05-19",
                            "reason": "v15 PAGE metadata inconsistency (book/page mismatch)",
                        }
                    ),
                },
            )
    print("[done]")
elif args.apply:
    print("\n[apply] no rollback needed — all clean")
else:
    print("\n[dry-run] Pass --apply to rollback")
