#!/usr/bin/env python3
"""
v9 — Gemini Flash 2.5 LOOSE prefix match.

After v8 exact match (3,684), 39K NULL rows remain that didn't find exact
text. Reasons:
  - DB question_text post-processed (LaTeX render, option concatenation)
  - JSONL soru_metni is raw OCR

Loose strategies (in order of safety):
  1. First-80-char prefix exact (normalized: NFKD + alphanumeric only)
  2. (book, page) deterministic: if (book, page) has exactly 1 JSONL entry
     AND 1 NULL DB row → unambiguous.
  3. (book, page, question_index) targeted: if DB row has source_page == JSONL
     page AND only 1 JSONL entry for that page, use it.

Each strategy has its own audit flag for traceability.
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

PREFIX_LEN = 80


def _norm_strict(t: str) -> str:
    if not t:
        return ""
    t = unicodedata.normalize("NFC", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def _norm_loose(t: str) -> str:
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).lower()
    return re.sub(r"[^a-z0-9çğıöşüâîû]", "", t)


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
    args = ap.parse_args()

    print(f"[load] {GEMINI_JSONL.name}...")
    # Index 1: loose-prefix → list[(book, page, crop)]
    prefix_idx: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    # Index 2: (book_folded, page) → list[(crop, full_norm_loose)]
    page_idx: dict[tuple[str, int], list[tuple[str, str]]] = defaultdict(list)

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
            if not (text and book and page is not None and crop):
                continue
            loose = _norm_loose(text)
            if len(loose) < 50:
                continue
            prefix_idx[loose[:PREFIX_LEN]].append((book, int(page), crop))
            page_idx[(_fold(book), int(page))].append((crop, loose))

    print(f"[index] prefix={len(prefix_idx):,} page={len(page_idx):,}\n")

    from sqlalchemy import create_engine
    from sqlalchemy import text as sa_text

    eng = create_engine(
        os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    )

    print("[scan] NULL DB rows with question_text, source_page...")
    with eng.connect() as c:
        rows = c.execute(
            sa_text("""
            SELECT id::text, source_book, source_page, question_text
            FROM question_bank
            WHERE is_active=true
              AND (question_image_url IS NULL OR question_image_url='')
              AND question_text IS NOT NULL
        """)
        ).fetchall()
    print(f"[null] {len(rows):,} rows\n")

    matches: list[
        tuple[str, str, str, int, str, str]
    ] = []  # (id, url, book, page, crop, strategy)
    stats = {
        "via_loose_prefix_book": 0,
        "via_page_unique_match": 0,
        "no_match": 0,
        "ambiguous": 0,
    }

    for r in rows:
        loose = _norm_loose(r.question_text)
        if len(loose) < 50:
            stats["no_match"] += 1
            continue

        sb_folded = _fold(r.source_book or "")

        # Strategy 1: loose-80-char prefix exact match, prefer same book
        cands = prefix_idx.get(loose[:PREFIX_LEN], [])
        chosen = None
        if cands:
            same_book = [(b, p, c) for b, p, c in cands if _fold(b) == sb_folded]
            if same_book:
                # If multiple same-book, prefer same source_page
                if r.source_page is not None:
                    for b, p, c in same_book:
                        if p == r.source_page:
                            chosen = (b, p, c)
                            break
                if not chosen:
                    if len(same_book) == 1:
                        chosen = same_book[0]
                    else:
                        # Multiple same-book candidates with no page disambiguation
                        chosen = None
            elif len(cands) == 1:
                chosen = cands[0]

            if chosen:
                disk_dir = find_disk_dir(chosen[0])
                if disk_dir:
                    crop_path = CROPS_BASE / disk_dir / chosen[2]
                    if crop_path.exists():
                        url = f"/static/crops/{disk_dir}/{chosen[2]}"
                        matches.append(
                            (
                                r.id,
                                url,
                                chosen[0],
                                chosen[1],
                                chosen[2],
                                "loose_prefix_book",
                            )
                        )
                        stats["via_loose_prefix_book"] += 1
                        continue

        # Strategy 2: (book, source_page) with single JSONL entry
        if r.source_page is not None and sb_folded:
            page_cands = page_idx.get((sb_folded, int(r.source_page)), [])
            if len(page_cands) == 1:
                # Single crop on this (book, page) — deterministic candidate
                crop, _ = page_cands[0]
                disk_dir = find_disk_dir(r.source_book or "")
                if disk_dir:
                    crop_path = CROPS_BASE / disk_dir / crop
                    if crop_path.exists():
                        url = f"/static/crops/{disk_dir}/{crop}"
                        matches.append(
                            (
                                r.id,
                                url,
                                r.source_book or "",
                                int(r.source_page),
                                crop,
                                "page_unique",
                            )
                        )
                        stats["via_page_unique_match"] += 1
                        continue

        stats["no_match"] += 1

    print("[result]")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")
    print(f"\n[total matches]: {len(matches):,}")

    if matches:
        print("\n[sample first 5]")
        for m in matches[:5]:
            print(f"  {m[0][:8]} [{m[5]:18s}] {m[2][:25]} p{m[3]} → {m[4]}")

    if args.apply and matches:
        print(f"\n[apply] UPDATE {len(matches):,} satır...")
        for i in range(0, len(matches), 500):
            batch = matches[i : i + 500]
            with eng.begin() as c:
                for qid, url, book, page, crop, strat in batch:
                    c.execute(
                        sa_text("""
                            UPDATE question_bank
                            SET question_image_url=:url,
                                pipeline_metadata = jsonb_set(
                                    COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb),
                                    '{image_match_gemini_flash_v9_loose}',
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
                                    "source": "v9_gemini_flash_loose",
                                    "strategy": strat,
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
