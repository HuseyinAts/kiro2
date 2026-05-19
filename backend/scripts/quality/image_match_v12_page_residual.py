#!/usr/bin/env python3
"""
v12 — Page residual unique match.

After v8/v9/v10b applied, on each (book, page) we have:
  - Some DB rows with image_url (already matched)
  - Some NULL rows
  - Some JSONL crops unused (not referenced by any current image_url)

If on a (book, page):
  - DB has exactly 1 NULL row AND
  - JSONL has exactly 1 unused crop (not used by any current image_url anywhere)

→ deterministic 1-1 mapping.

This is similar to Strategy C (unused-crop narrow-down) but uses JSONL
as crop source instead of meta.json, and only acts when residual is unique.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GEMINI_JSONL = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _book_key(book: str) -> str:
    if not book:
        return ""
    folded = _fold(book)
    folded = re.sub(r"[_\-]+", " ", folded)
    folded = re.sub(r"\s+", " ", folded).strip()
    return folded


_DISK_DIRS = None


def find_disk_dir(book):
    global _DISK_DIRS
    if not book:
        return None
    if _DISK_DIRS is None:
        _DISK_DIRS = sorted(d.name for d in CROPS_BASE.iterdir() if d.is_dir())
    for v in [book.replace(" ", "_"), re.sub(r"\s+", "_", book.strip())]:
        if v in _DISK_DIRS:
            return v
    folded = _fold(book.replace(" ", "_"))
    for d in _DISK_DIRS:
        if _fold(d) == folded:
            return d
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    print(f"[load] {GEMINI_JSONL.name}...")
    # Index: (book_key, page) → list[crop]
    page_crops: dict[tuple[str, int], list[str]] = defaultdict(list)
    with GEMINI_JSONL.open(encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            book = d.get("book", "")
            page = d.get("page_num")
            crop = d.get("crop_file", "")
            if not (book and page is not None and crop):
                continue
            page_crops[(_book_key(book), int(page))].append(crop)
    print(f"[indexed] {len(page_crops):,} (book, page) groups\n")

    from sqlalchemy import create_engine
    from sqlalchemy import text as sa_text

    eng = create_engine(
        os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
    )

    # For each (book, page), find:
    #   - count of NULL DB rows
    #   - set of crop filenames already used by image_url
    print("[scan] active rows by (book, page)...")
    with eng.connect() as c:
        rows = c.execute(
            sa_text("""
            SELECT id::text, source_book, source_page, question_image_url
            FROM question_bank
            WHERE is_active=true
              AND source_book IS NOT NULL AND source_page IS NOT NULL
        """)
        ).fetchall()

    by_page: dict[tuple[str, int], dict] = defaultdict(
        lambda: {"null_ids": [], "used_crops": set(), "source_book_orig": ""}
    )
    for r in rows:
        bk = _book_key(r.source_book)
        key = (bk, int(r.source_page))
        by_page[key]["source_book_orig"] = r.source_book
        if not r.question_image_url:
            by_page[key]["null_ids"].append(r.id)
        else:
            # Extract filename from URL
            fname = r.question_image_url.split("/")[-1] if r.question_image_url else ""
            if fname:
                by_page[key]["used_crops"].add(fname)

    print(f"[pages] {len(by_page):,} (book, page) groups in DB\n")

    matches = []
    stats = {
        "deterministic_residual": 0,
        "no_jsonl_page": 0,
        "multi_null_multi_unused": 0,
        "multi_null_single_unused": 0,
        "single_null_multi_unused": 0,
        "no_nulls": 0,
        "no_unused_crops": 0,
    }

    for (bk, page), g in by_page.items():
        if not g["null_ids"]:
            stats["no_nulls"] += 1
            continue

        jsonl_crops = page_crops.get((bk, page), [])
        if not jsonl_crops:
            stats["no_jsonl_page"] += 1
            continue

        unused = [c for c in jsonl_crops if c not in g["used_crops"]]
        if not unused:
            stats["no_unused_crops"] += 1
            continue

        n_null = len(g["null_ids"])
        n_unused = len(unused)

        if n_null == 1 and n_unused == 1:
            crop = unused[0]
            disk_dir = find_disk_dir(g["source_book_orig"])
            if not disk_dir:
                continue
            crop_path = CROPS_BASE / disk_dir / crop
            if not crop_path.exists():
                continue
            url = f"/static/crops/{disk_dir}/{crop}"
            matches.append((g["null_ids"][0], url, g["source_book_orig"], page, crop))
            stats["deterministic_residual"] += 1
        elif n_null == 1 and n_unused > 1:
            stats["single_null_multi_unused"] += 1
        elif n_null > 1 and n_unused == 1:
            stats["multi_null_single_unused"] += 1
        else:
            stats["multi_null_multi_unused"] += 1

    print("[result]")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")
    print(f"\n[matches]: {len(matches):,}")

    if matches:
        print("\n[sample first 5]")
        for m in matches[:5]:
            print(f"  {m[0][:8]} {m[2][:30]} p{m[3]} → {m[4]}")

    if args.apply and matches:
        print(f"\n[apply] UPDATE {len(matches):,} satır...")
        for i in range(0, len(matches), 500):
            batch = matches[i : i + 500]
            with eng.begin() as c:
                for qid, url, book, page, crop in batch:
                    c.execute(
                        sa_text("""
                            UPDATE question_bank
                            SET question_image_url=:url,
                                pipeline_metadata = jsonb_set(
                                    COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                    '{image_match_v12_page_residual}',
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
                                    "source": "v12_page_residual_unique",
                                    "matched_page": int(page),
                                    "matched_crop": crop,
                                }
                            ),
                        },
                    )
        print("[done]")
        with eng.connect() as c:
            null_n = c.execute(
                sa_text(
                    "SELECT COUNT(*) FROM question_bank WHERE is_active=true "
                    "AND (question_image_url IS NULL OR question_image_url='')"
                )
            ).scalar()
            print(f"\nFINAL NULL: {null_n:,}")
    else:
        print("\n[dry-run]")


if __name__ == "__main__":
    main()
