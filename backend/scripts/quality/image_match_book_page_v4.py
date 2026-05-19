#!/usr/bin/env python3
"""
Image match v4 (Tier 7) — book + page from pipeline_metadata.crop_file.

Bazı NULL satırlarda `pipeline_metadata.crop_file` field VAR (eski Tier C-G
çıktısı) ama page veya q_no diğer fieldlardan çıkarılmamış. crop_file string'i
zaten `<book>_pNNNN_qXX.png` formatında — direkt parse et + disk'te dene.

Ayrıca: source_book bilgisi varsa o klasördeki crop_file dosyasını ara,
filename pattern farklı book name kullansa bile fuzzy book match ile bul.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CROPS_BASE = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def _fold_diacritics(s: str) -> str:
    tr_map = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")
    return s.translate(tr_map).lower()


_DISK_DIRS: list[str] | None = None
_BOOK_CACHE: dict[str, str] = {}


def find_disk_dir(book: str) -> str | None:
    global _DISK_DIRS
    if not book:
        return None
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


def find_via_crop_file(book: str, crop_file: str) -> str | None:
    """Try crop_file in resolved disk dir."""
    if not crop_file:
        return None
    book_dir = find_disk_dir(book) if book else None
    candidates = []
    if book_dir:
        candidates.append(book_dir)
    # Also try: extract book_dir from crop_file itself (legacy "<book>_pNNNN_qXX.png")
    m = re.match(r"^(.+)_p\d{4}_q\d{1,2}\.(png|jpg)$", crop_file)
    if m and m.group(1) not in candidates:
        candidates.append(m.group(1))

    for d in candidates:
        fpath = CROPS_BASE / d / crop_file
        if fpath.exists():
            return f"/static/crops/{d}/{crop_file}"
    return None


def find_via_page_meta(book: str, pm: dict, question_text: str = "") -> str | None:
    """If we have source_book + some page hint, scan all pages."""
    book_dir = find_disk_dir(book) if book else None
    if not book_dir:
        return None
    dir_path = CROPS_BASE / book_dir
    if not dir_path.exists():
        return None

    # Try page hints from various pm fields
    page_candidates = []
    for key in ("page_number", "page", "answer_page"):
        v = pm.get(key)
        if isinstance(v, int) and v > 0:
            page_candidates.append(v)
        elif isinstance(v, str) and v.isdigit():
            page_candidates.append(int(v))

    # request_key fallback
    rk = pm.get("request_key", "")
    m = re.search(r"sayfa_(\d+)", str(rk))
    if m:
        page_candidates.append(int(m.group(1)))

    if not page_candidates:
        return None

    # Try qno hints
    qno_candidates = []
    ai = pm.get("ai_extras", {}) or {}
    for src in (ai.get("q_no"), ai.get("q_index_in_page"), pm.get("question_number")):
        try:
            qno_candidates.append(int(src))
        except (TypeError, ValueError):
            continue
    # Default: try q01-q10
    if not qno_candidates:
        qno_candidates = list(range(1, 16))

    for page in set(page_candidates):
        page_str = f"{page:04d}"
        for qno in qno_candidates:
            for q_str in (f"q{qno:02d}", f"q{qno}"):
                for ext in (".png", ".jpg"):
                    fname = f"{book_dir}_p{page_str}_{q_str}{ext}"
                    if (dir_path / fname).exists():
                        return f"/static/crops/{book_dir}/{fname}"
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

    limit = f"LIMIT {args.pilot}" if args.pilot else ""
    with eng.connect() as c:
        rows = c.execute(
            text(
                f"SELECT id::text, source_book, question_text, pipeline_metadata::text AS pm "
                f"FROM question_bank WHERE is_active=true "
                f"AND (question_image_url IS NULL OR question_image_url='') "
                f"{limit}"
            )
        ).fetchall()

    print(f"[scan] {len(rows):,} NULL image rows")

    found_crop_file, found_page_scan, not_found = 0, 0, 0
    matches = []

    for r in rows:
        try:
            pm = json.loads(r.pm) if r.pm else {}
        except json.JSONDecodeError:
            pm = {}

        url = None

        # Tier 7a: crop_file direct
        cf = pm.get("crop_file")
        if cf:
            url = find_via_crop_file(r.source_book or "", cf)
            if url:
                found_crop_file += 1

        # Tier 7b: page meta scan
        if not url and r.source_book:
            url = find_via_page_meta(r.source_book, pm, r.question_text or "")
            if url:
                found_page_scan += 1

        if url:
            matches.append((r.id, url))
        else:
            not_found += 1

    print(
        f"\n[result] crop_file={found_crop_file:,}, page_scan={found_page_scan:,}, not_found={not_found:,}"
    )
    print(f"[total found] {len(matches):,}")

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
                            "  '{image_match_book_page_v4}', "
                            '  \'{"date":"2026-05-19","source":"v4"}\'::jsonb, '
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
