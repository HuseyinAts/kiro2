#!/usr/bin/env python3
"""
v8 — Gemini Flash 2.5 OCR direct crop_file lookup.

Found d-dataset/output/ocr_crops/results.jsonl: 333,690 entries from the
Gemini Flash 2.5 OCR pipeline. Each entry has:
  - book, page_num, crop_file (the disk filename!)
  - question_index (1-based page index)
  - soru_metni (OCR'd question text)

NULL DB rows come from THIS exact pipeline (kiro2_batch_v4.14e source).
Question_text in DB == soru_metni in JSONL == crop_file mapping.

This is the deterministic key we've been missing.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GEMINI_JSONL = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _norm(t: str) -> str:
    if not t:
        return ""
    t = unicodedata.normalize("NFC", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


def _fold(s: str) -> str:
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


_DISK_DIRS = None


def find_disk_dir(book: str) -> str | None:
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
    ap.add_argument("--pilot", type=int, default=0, help="Pilot N samples only")
    args = ap.parse_args()

    # Build Gemini index: normalized question text → list of (book, page, crop_file)
    print(f"[load] {GEMINI_JSONL.name}...")
    text_idx: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    n_loaded = 0
    n_skipped_empty = 0
    n_skipped_short = 0
    with GEMINI_JSONL.open(encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = d.get("soru_metni") or ""
            book = d.get("book", "")
            page = d.get("page_num")
            crop = d.get("crop_file", "")
            if not text:
                n_skipped_empty += 1
                continue
            normed = _norm(text)
            if len(normed) < 30:
                n_skipped_short += 1
                continue
            if not (book and page is not None and crop):
                continue
            text_idx[normed].append((book, int(page), crop))
            n_loaded += 1
    print(
        f"[done] indexed={n_loaded:,} skipped_empty={n_skipped_empty:,} short={n_skipped_short:,}"
    )
    print(f"[index] {len(text_idx):,} unique normalized text keys\n")

    from sqlalchemy import create_engine
    from sqlalchemy import text as sa_text

    eng = create_engine(
        os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    )

    # Scan NULL rows
    print("[scan] NULL DB rows...")
    limit_clause = f"LIMIT {args.pilot}" if args.pilot else ""
    with eng.connect() as c:
        rows = c.execute(
            sa_text(f"""
            SELECT id::text, source_book, question_text, source_page
            FROM question_bank
            WHERE is_active=true
              AND (question_image_url IS NULL OR question_image_url='')
              AND question_text IS NOT NULL
            {limit_clause}
        """)
        ).fetchall()
    print(f"[null] {len(rows):,} rows to process\n")

    matches = []
    no_text_match = 0
    no_disk_dir = 0
    no_crop_on_disk = 0
    ambiguous_no_book_match = 0

    for r in rows:
        normed = _norm(r.question_text)
        if len(normed) < 30:
            no_text_match += 1
            continue
        cands = text_idx.get(normed, [])
        if not cands:
            no_text_match += 1
            continue

        # Prefer same source_book
        chosen = None
        sb_folded = _fold(r.source_book or "")
        for cb, cp, cc in cands:
            if _fold(cb) == sb_folded:
                chosen = (cb, cp, cc)
                break
        if not chosen:
            # If only one candidate book overall, accept; else ambiguous
            unique_books = {_fold(cb) for cb, _, _ in cands}
            if len(unique_books) == 1:
                chosen = cands[0]
            else:
                ambiguous_no_book_match += 1
                continue

        cb, cp, cc = chosen
        disk_dir = find_disk_dir(cb)
        if not disk_dir:
            no_disk_dir += 1
            continue
        crop_path = CROPS_BASE / disk_dir / cc
        if not crop_path.exists():
            # Try with the book name in the crop_file (it might already include disk-dir prefix)
            no_crop_on_disk += 1
            continue

        url = f"/static/crops/{disk_dir}/{cc}"
        matches.append((r.id, url, cb, cp, cc))

    print("[result]")
    print(f"  matches:                {len(matches):,}")
    print(f"  no_text_match:          {no_text_match:,}")
    print(f"  ambiguous_book:         {ambiguous_no_book_match:,}")
    print(f"  no_disk_dir:            {no_disk_dir:,}")
    print(f"  no_crop_on_disk:        {no_crop_on_disk:,}")

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
                                    '{image_match_gemini_flash_v8}',
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
                                    "source": "v8_gemini_flash_2.5_ocr_results_jsonl",
                                    "matched_book": book,
                                    "matched_page": int(page),
                                    "matched_crop": crop,
                                }
                            ),
                        },
                    )
            if (i // 500 + 1) % 10 == 0:
                print(f"  batch {i // 500 + 1}/{(len(matches) + 499) // 500}")
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
        print("\n[dry-run] Pass --apply to write to DB.")


if __name__ == "__main__":
    main()
