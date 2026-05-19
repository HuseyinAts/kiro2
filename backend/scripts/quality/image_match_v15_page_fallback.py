#!/usr/bin/env python3
"""
v15 — Page-level zkitap screenshot fallback.

For NULL rows that have a zkitap sayfa_NNNN.png:
  - Copy screenshot to d-dataset/output/crops/<book>/<book>_pNNNN_PAGE.png
  - Set image_url = /static/crops/<book>/<book>_pNNNN_PAGE.png
  - One file per (book, page) — multiple NULL rows on same page share the URL

This is a FALLBACK — page-level image, not question-specific crop. Student
sees the whole page (which includes their question). Better than NULL.

Source: veriseti/zkitap/screenshots/<zk_dir>/sayfa_NNNN.png
Dest:   d-dataset/output/crops/<dd_dir>/<dd_dir>_pNNNN_PAGE.png

If no d-dataset dir exists, create one (for zkitap-only books).
"""

import argparse
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ZKITAP = PROJECT_ROOT / "veriseti" / "zkitap" / "screenshots"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _canon(s):
    return re.sub(r"\W+", "_", _fold(s)).strip("_")


_DD_DIRS = None
_ZK_DIRS = None


def find_dd_dir(book):
    global _DD_DIRS
    if _DD_DIRS is None:
        _DD_DIRS = {_canon(d.name): d.name for d in CROPS_BASE.iterdir() if d.is_dir()}
    return _DD_DIRS.get(_canon(book))


def find_zk_dir(book):
    global _ZK_DIRS
    if _ZK_DIRS is None:
        _ZK_DIRS = {_canon(d.name): d.name for d in ZKITAP.iterdir() if d.is_dir()}
    return _ZK_DIRS.get(_canon(book))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    from sqlalchemy import create_engine, text

    eng = create_engine(
        os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
    )

    print("[scan] NULL rows with source_book + source_page...")
    with eng.connect() as c:
        rows = c.execute(
            text("""
            SELECT id::text, source_book, source_page
            FROM question_bank
            WHERE is_active=true
              AND (question_image_url IS NULL OR question_image_url='')
              AND source_book IS NOT NULL AND source_page IS NOT NULL
        """)
        ).fetchall()
    print(f"[null] {len(rows):,} candidates\n")

    # Group by (book, page) — one copy per page
    by_page: dict[tuple[str, int], list[str]] = defaultdict(list)
    book_orig: dict[tuple[str, int], str] = {}
    for r in rows:
        bk = _canon(r.source_book)
        key = (bk, int(r.source_page))
        by_page[key].append(r.id)
        book_orig[key] = r.source_book

    print(f"[pages] {len(by_page):,} unique (book, page) groups\n")

    matches: list[tuple[str, str, str, int]] = []
    file_copies: list[tuple[Path, Path]] = []  # (src, dst)
    stats = {
        "copied_pages": 0,
        "rows_matched": 0,
        "no_zk_dir": 0,
        "no_zk_png": 0,
        "no_dd_dir_created": 0,
    }

    for key, null_ids in by_page.items():
        zk_dir = find_zk_dir(book_orig[key])
        if not zk_dir:
            stats["no_zk_dir"] += 1
            continue
        page = key[1]
        src = ZKITAP / zk_dir / f"sayfa_{page:04d}.png"
        if not src.exists():
            stats["no_zk_png"] += 1
            continue

        # Choose dest dir: existing d-dataset dir or create from zkitap dir name
        dd_dir = find_dd_dir(book_orig[key])
        if not dd_dir:
            # Use zkitap dir name normalized for d-dataset
            dd_dir = zk_dir.replace(" ", "_")
            stats["no_dd_dir_created"] += 1

        dest_name = f"{dd_dir}_p{page:04d}_PAGE.png"
        dest_path = CROPS_BASE / dd_dir / dest_name
        file_copies.append((src, dest_path))
        url = f"/static/crops/{dd_dir}/{dest_name}"
        for qid in null_ids:
            matches.append((qid, url, dd_dir, page))
        stats["copied_pages"] += 1
        stats["rows_matched"] += len(null_ids)

    print("[plan]")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")
    print(f"\n[matches]: {len(matches):,} rows, {len(file_copies):,} file copies")

    if matches and args.apply:
        print(f"\n[copy] {len(file_copies):,} PNG files...")
        copied = skipped = 0
        for i, (src, dst) in enumerate(file_copies):
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                skipped += 1
            else:
                try:
                    shutil.copy2(src, dst)
                    copied += 1
                except Exception as e:
                    print(f"  copy fail {src.name}: {e}")
                    skipped += 1
            if (i + 1) % 1000 == 0:
                print(f"  copied {copied:,} / skipped {skipped:,}")
        print(f"[copy done] copied={copied:,} skipped={skipped:,}")

        print(f"\n[apply] UPDATE {len(matches):,} satır...")
        for i in range(0, len(matches), 500):
            batch = matches[i : i + 500]
            with eng.begin() as c:
                for qid, url, dd_dir, page in batch:
                    c.execute(
                        text("""
                            UPDATE question_bank
                            SET question_image_url=:url,
                                pipeline_metadata = jsonb_set(
                                    COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                    '{image_match_v15_page_fallback}',
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
                                    "source": "v15_page_level_fallback_zkitap",
                                    "type": "page_fallback",
                                    "matched_page": int(page),
                                }
                            ),
                        },
                    )
            if (i // 500 + 1) % 10 == 0:
                print(f"  batch {i // 500 + 1}/{(len(matches) + 499) // 500}")
        print("[done]")
        with eng.connect() as c:
            null_n = c.execute(
                text(
                    "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                    "AND (question_image_url IS NULL OR question_image_url='')"
                )
            ).scalar()
            print(f"\nFINAL NULL: {null_n:,}")
    else:
        print("\n[dry-run]")


if __name__ == "__main__":
    main()
