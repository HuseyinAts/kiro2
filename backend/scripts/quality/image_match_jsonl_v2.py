#!/usr/bin/env python3
"""
Image match v2 (Tier 5) — eslesmis_sorucevap.jsonl üzerinden match.

For NULL image_url satırlar that have no ai_extras/request_key (eski format),
question_text → JSONL match → (book, page, q_no) → disk filename.

NO RE-OCR. Just text-equality lookup against pre-existing JSONL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
JSONL_PATH = PROJECT_ROOT / "d-dataset" / "eslesmis_sorucevap.jsonl"
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _norm(text: str) -> str:
    """Normalize for hash-based equality match."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    # Remove whitespace + lowercase (no diacritic strip, NFC handles it)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _text_hash(text: str) -> str:
    return hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()[:16]


def _fold_diacritics(s: str) -> str:
    tr_map = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")
    return s.translate(tr_map).lower()


_DISK_DIRS: list[str] | None = None
_BOOK_MAPPING_CACHE: dict[str, str] = {}


def _load_disk_dirs():
    global _DISK_DIRS
    if _DISK_DIRS is None:
        _DISK_DIRS = sorted(d.name for d in CROPS_BASE.iterdir() if d.is_dir())
    return _DISK_DIRS


def find_disk_dir(book: str) -> str | None:
    if book in _BOOK_MAPPING_CACHE:
        return _BOOK_MAPPING_CACHE[book] or None
    disk_dirs = _load_disk_dirs()
    # Exact normalized
    for variant in [book.replace(" ", "_"), re.sub(r"\s+", "_", book.strip())]:
        if variant in disk_dirs:
            _BOOK_MAPPING_CACHE[book] = variant
            return variant
    # Diacritic-folded
    folded = _fold_diacritics(book.replace(" ", "_"))
    for d in disk_dirs:
        if _fold_diacritics(d) == folded:
            _BOOK_MAPPING_CACHE[book] = d
            return d
    # Token overlap
    db_tokens = set(_fold_diacritics(book).split()) - {"soru", "bankası", "bankasi"}
    if len(db_tokens) >= 3:
        best, best_score = None, 0
        for d in disk_dirs:
            d_tokens = set(_fold_diacritics(d.replace("_", " ")).split()) - {
                "soru",
                "bankası",
                "bankasi",
            }
            common = db_tokens & d_tokens
            if len(common) > best_score:
                best, best_score = d, len(common)
        if best_score >= max(3, len(db_tokens) - 1):
            _BOOK_MAPPING_CACHE[book] = best
            return best
    _BOOK_MAPPING_CACHE[book] = ""
    return None


def build_jsonl_index() -> dict[str, tuple[str, int, int]]:
    """text_hash → (book_name, page_number, question_number)."""
    idx: dict[str, tuple[str, int, int]] = {}
    print(f"[load] {JSONL_PATH}")
    with JSONL_PATH.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
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
            h = _text_hash(text)
            idx[h] = (book, int(page), int(qno))
            if (i + 1) % 20000 == 0:
                print(f"  [scan] {i + 1:,} lines, {len(idx):,} unique hashes")
    print(f"[done] {len(idx):,} unique text hashes")
    return idx


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
            fpath = dir_path / fname
            if fpath.exists():
                return f"/static/crops/{book_dir}/{fname}"
    # meta.json fallback
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=0)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    from sqlalchemy import create_engine, text

    eng = create_engine(
        os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
    )

    # Load JSONL index
    jsonl_idx = build_jsonl_index()

    # NULL image rows
    limit = f"LIMIT {args.pilot}" if args.pilot else ""
    with eng.connect() as c:
        rows = c.execute(
            text(
                f"SELECT id::text, question_text FROM question_bank "
                f"WHERE is_active=true "
                f"AND (question_image_url IS NULL OR question_image_url='') "
                f"AND question_text IS NOT NULL "
                f"{limit}"
            )
        ).fetchall()

    print(f"\n[scan] {len(rows):,} NULL image_url rows")

    found, not_found, no_match_hash = 0, 0, 0
    matches = []
    for r in rows:
        h = _text_hash(r.question_text)
        match = jsonl_idx.get(h)
        if not match:
            no_match_hash += 1
            continue
        book, page, qno = match
        url = find_crop_disk(book, page, qno)
        if url:
            found += 1
            matches.append((r.id, url))
        else:
            not_found += 1

    print(
        f"\n[result] found={found:,}, not_found={not_found:,}, no_hash_match={no_match_hash:,}"
    )

    if args.apply and matches:
        print(f"\n[apply] {len(matches):,} satır güncelleniyor...")
        for i in range(0, len(matches), 500):
            batch = matches[i : i + 500]
            with eng.begin() as c:
                for qid, url in batch:
                    c.execute(
                        text(
                            "UPDATE question_bank SET question_image_url=:url, "
                            "pipeline_metadata = jsonb_set("
                            "  COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb), "
                            "  '{image_match_jsonl_v2}', "
                            '  \'{"date":"2026-05-19","source":"image_match_jsonl_v2"}\'::jsonb, '
                            "  TRUE"
                            ")::json, "
                            "updated_at=NOW() "
                            "WHERE id::text=:qid"
                        ),
                        {"url": url, "qid": qid},
                    )
            print(
                f"  batch {i // 500 + 1}/{(len(matches) + 499) // 500}: {len(batch)} done"
            )

    for qid, url in matches[:3]:
        print(f"  sample: {qid[:8]} → {url[:80]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
