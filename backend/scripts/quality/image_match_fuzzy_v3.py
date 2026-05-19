#!/usr/bin/env python3
"""
Image match v3 (Tier 6) — substring/fuzzy match for residual NULL rows.

Hash exact match fails because of subtle encoding/whitespace differences.
Use first-N chars normalized prefix as key + substring fallback.
"""

from __future__ import annotations

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
JSONL_PATH = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"

PREFIX_LEN = 80  # First 80 normalized chars as match key


def _norm_loose(text: str) -> str:
    """Aggressive normalization for fuzzy match.

    - NFKD normalize (strip combining marks)
    - Lowercase
    - Strip ALL whitespace + punctuation
    - Keep only alphanumeric (Turkish chars OK)
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    # Remove all whitespace + most punctuation, keep alphanumeric + Turkish letters
    text = re.sub(r"[^a-z0-9çğıöşüâîû]", "", text)
    return text


def _fold_diacritics(s: str) -> str:
    tr_map = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")
    return s.translate(tr_map).lower()


_DISK_DIRS: list[str] | None = None
_BOOK_CACHE: dict[str, str] = {}


def find_disk_dir(book: str) -> str | None:
    global _DISK_DIRS
    if book in _BOOK_CACHE:
        return _BOOK_CACHE[book] or None
    if _DISK_DIRS is None:
        _DISK_DIRS = sorted(d.name for d in CROPS_BASE.iterdir() if d.is_dir())
    for variant in [book.replace(" ", "_"), re.sub(r"\s+", "_", book.strip())]:
        if variant in _DISK_DIRS:
            _BOOK_CACHE[book] = variant
            return variant
    folded = _fold_diacritics(book.replace(" ", "_"))
    for d in _DISK_DIRS:
        if _fold_diacritics(d) == folded:
            _BOOK_CACHE[book] = d
            return d
    db_tokens = set(_fold_diacritics(book).split()) - {"soru", "bankası", "bankasi"}
    if len(db_tokens) >= 3:
        best, best_score = None, 0
        for d in _DISK_DIRS:
            d_tokens = set(_fold_diacritics(d.replace("_", " ")).split()) - {
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


def find_crop_disk(book: str, page: int, qno: int) -> str | None:
    book_dir = find_disk_dir(book)
    if not book_dir:
        return None
    dir_path = CROPS_BASE / book_dir
    if not dir_path.exists():
        return None
    page_str = f"{page:04d}"
    for q_str in (f"q{qno:02d}", f"q{qno}"):
        for ext in (".png", ".jpg"):
            fname = f"{book_dir}_p{page_str}_{q_str}{ext}"
            if (dir_path / fname).exists():
                return f"/static/crops/{book_dir}/{fname}"
    meta_path = dir_path / f"{book_dir}_p{page_str}_meta.json"
    if meta_path.exists():
        try:
            md = json.loads(meta_path.read_text(encoding="utf-8"))
            for q in md.get("questions", []):
                if q.get("index") == qno:
                    crop_name = q.get("crop")
                    if crop_name and (dir_path / crop_name).exists():
                        return f"/static/crops/{book_dir}/{crop_name}"
        except (json.JSONDecodeError, OSError):
            pass
    return None


def build_prefix_index() -> dict[str, list[tuple[str, int, int]]]:
    """prefix(80 normalized chars) → list of (book, page, qno)."""
    idx: defaultdict[str, list[tuple[str, int, int]]] = defaultdict(list)
    print(f"[load] {JSONL_PATH}")
    with JSONL_PATH.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = d.get("text") or ""
            if not text:
                continue
            book = d.get("book_name", "")
            page = d.get("page_number")
            qno = d.get("question_number")
            if not (book and page and qno):
                continue
            normed = _norm_loose(text)
            if len(normed) < PREFIX_LEN:
                continue
            prefix = normed[:PREFIX_LEN]
            idx[prefix].append((book, int(page), int(qno)))
            if (i + 1) % 20000 == 0:
                print(f"  [scan] {i + 1:,} lines, {len(idx):,} unique prefixes")
    print(f"[done] {len(idx):,} unique prefixes")
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=0)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    from sqlalchemy import create_engine, text

    eng = create_engine(
        os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
    )

    idx = build_prefix_index()

    limit = f"LIMIT {args.pilot}" if args.pilot else ""
    with eng.connect() as c:
        rows = c.execute(
            text(
                f"SELECT id::text, source_book, question_text FROM question_bank "
                f"WHERE is_active=true "
                f"AND (question_image_url IS NULL OR question_image_url='') "
                f"AND question_text IS NOT NULL "
                f"{limit}"
            )
        ).fetchall()

    print(f"\n[scan] {len(rows):,} NULL image rows")

    found, not_found, no_prefix = 0, 0, 0
    matches = []

    for r in rows:
        normed = _norm_loose(r.question_text)
        if len(normed) < PREFIX_LEN:
            no_prefix += 1
            continue
        prefix = normed[:PREFIX_LEN]
        candidates = idx.get(prefix, [])
        if not candidates:
            no_prefix += 1
            continue
        # Prefer same source_book if available
        if r.source_book:
            book_folded = _fold_diacritics(r.source_book)
            for book, page, qno in candidates:
                if _fold_diacritics(book) == book_folded:
                    url = find_crop_disk(book, page, qno)
                    if url:
                        found += 1
                        matches.append((r.id, url))
                        break
            else:
                # Fallback: any candidate
                for book, page, qno in candidates:
                    url = find_crop_disk(book, page, qno)
                    if url:
                        found += 1
                        matches.append((r.id, url))
                        break
                else:
                    not_found += 1
        else:
            for book, page, qno in candidates:
                url = find_crop_disk(book, page, qno)
                if url:
                    found += 1
                    matches.append((r.id, url))
                    break
            else:
                not_found += 1

    print(
        f"\n[result] found={found:,}, not_found={not_found:,}, no_prefix={no_prefix:,}"
    )

    if args.apply and matches:
        print(f"\n[apply] {len(matches):,} satır UPDATE...")
        for i in range(0, len(matches), 500):
            batch = matches[i : i + 500]
            with eng.begin() as c:
                for qid, url in batch:
                    c.execute(
                        text(
                            "UPDATE question_bank SET question_image_url=:url, "
                            "pipeline_metadata = jsonb_set("
                            "  COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb), "
                            "  '{image_match_fuzzy_v3}', "
                            '  \'{"date":"2026-05-19","source":"image_match_fuzzy_v3"}\'::jsonb, '
                            "  TRUE"
                            ")::json, "
                            "updated_at=NOW() "
                            "WHERE id::text=:qid"
                        ),
                        {"url": url, "qid": qid},
                    )
            print(f"  batch {i // 500 + 1}/{(len(matches) + 499) // 500}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
