#!/usr/bin/env python3
"""
Image match v1 — Re-OCR YOK. Sadece DB metadata + disk filename pattern.

Goal: 'görseli eksik soruların görsellerini re-OCR yöntemini kullanmadan bul'

Strateji:
  1. question_bank.pipeline_metadata.request_key → sayfa numarası (sayfa_0269)
  2. pipeline_metadata.ai_extras.q_no → sayfa içi soru no (1-based)
  3. source_book + normalized → disk klasör adı
  4. Beklenen crop: <book>/<book>_p<NNNN>_q<NN>.png
  5. Disk varsa image_url set et

USAGE:
  python backend/scripts/quality/image_match_metadata_v1.py --pilot 100
  python backend/scripts/quality/image_match_metadata_v1.py --full --apply
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
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"


def normalize_book_name(book: str) -> list[str]:
    """source_book → possible disk folder name variants."""
    if not book:
        return []
    candidates = []
    candidates.append(book.replace(" ", "_"))
    candidates.append(re.sub(r"\s+", "_", book.strip()))
    base = re.sub(r"[\s\-_]+", "_", book.strip())
    if base not in candidates:
        candidates.append(base)
    return candidates


def _fold_diacritics(s: str) -> str:
    """Türkçe diacritic → ASCII fold for fuzzy matching."""
    tr_map = str.maketrans(
        "ÇĞİÖŞÜçğıöşü",
        "CGIOSUcgiosu",
    )
    return s.translate(tr_map).lower()


# Cached disk directory list (loaded once)
_DISK_DIRS: list[str] | None = None
_BOOK_MAPPING_CACHE: dict[str, str] = {}


def _load_disk_dirs() -> list[str]:
    global _DISK_DIRS
    if _DISK_DIRS is None:
        if CROPS_BASE.exists():
            _DISK_DIRS = sorted(d.name for d in CROPS_BASE.iterdir() if d.is_dir())
        else:
            _DISK_DIRS = []
    return _DISK_DIRS


def find_disk_dir(book: str) -> str | None:
    """Return best matching disk directory name for a DB book name."""
    if book in _BOOK_MAPPING_CACHE:
        return _BOOK_MAPPING_CACHE[book] or None
    disk_dirs = _load_disk_dirs()

    # 1) Exact normalized match
    for variant in normalize_book_name(book):
        if variant in disk_dirs:
            _BOOK_MAPPING_CACHE[book] = variant
            return variant

    # 2) Diacritic-folded match
    folded_db = _fold_diacritics(book.replace(" ", "_"))
    for d in disk_dirs:
        if _fold_diacritics(d) == folded_db:
            _BOOK_MAPPING_CACHE[book] = d
            return d

    # 3) Substring/prefix fuzzy match (sufficient overlap)
    db_tokens = set(_fold_diacritics(book).split())
    db_tokens.discard("soru")
    db_tokens.discard("bankasi")
    db_tokens.discard("bankası")
    if len(db_tokens) >= 3:
        best, best_score = None, 0
        for d in disk_dirs:
            d_tokens = set(_fold_diacritics(d.replace("_", " ")).split())
            d_tokens.discard("soru")
            d_tokens.discard("bankasi")
            d_tokens.discard("bankası")
            common = db_tokens & d_tokens
            if len(common) > best_score:
                best, best_score = d, len(common)
        if best_score >= max(3, len(db_tokens) - 1):
            _BOOK_MAPPING_CACHE[book] = best
            return best

    _BOOK_MAPPING_CACHE[book] = ""
    return None


def extract_page_num(request_key: str) -> int | None:
    """request_key='sayfa_0269_<hash>' → 269"""
    if not request_key:
        return None
    m = re.search(r"sayfa_(\d+)", request_key)
    return int(m.group(1)) if m else None


def find_crop(book: str, page: int, q_no: int | str) -> str | None:
    """Try to find crop file on disk. Returns relative path or None."""
    if not book or page is None or q_no is None:
        return None

    # Normalize q_no (handle "7" string → 7, "07" → 7)
    try:
        q_int = int(str(q_no).strip())
    except (ValueError, TypeError):
        return None

    book_dir = find_disk_dir(book)
    if not book_dir:
        return None

    page_str = f"{page:04d}"
    dir_path = CROPS_BASE / book_dir
    if not dir_path.exists():
        return None

    # Tier 1: Direct filename match — book_pXXXX_qNN.png
    for q_str in (f"q{q_int:02d}", f"q{q_int}"):
        for ext in (".png", ".jpg"):
            fname = f"{book_dir}_p{page_str}_{q_str}{ext}"
            fpath = dir_path / fname
            if fpath.exists():
                return f"/static/crops/{book_dir}/{fname}"

    # Tier 2: meta.json fallback — lookup by index in page
    meta_path = dir_path / f"{book_dir}_p{page_str}_meta.json"
    if meta_path.exists():
        try:
            md = json.loads(meta_path.read_text(encoding="utf-8"))
            questions = md.get("questions", [])
            # Try matching by index (q_int matches index field)
            for q in questions:
                if q.get("index") == q_int:
                    crop_name = q.get("crop")
                    if crop_name and (dir_path / crop_name).exists():
                        return f"/static/crops/{book_dir}/{crop_name}"
        except (json.JSONDecodeError, OSError):
            pass

    return None


def find_crop_by_qidx(book: str, page: int, q_idx_in_page: int) -> str | None:
    """Tier 3 fallback: use q_index_in_page (0-based) instead of q_no.

    NOTE: q_index_in_page can be 0-indexed OR 1-indexed depending on book.
    Try both.
    """
    if not book or page is None or q_idx_in_page is None:
        return None
    book_dir = find_disk_dir(book)
    if not book_dir:
        return None

    page_str = f"{page:04d}"
    dir_path = CROPS_BASE / book_dir
    if not dir_path.exists():
        return None

    # Try 0-indexed (index = q_idx+1) and 1-indexed (index = q_idx)
    for q_int in (q_idx_in_page + 1, q_idx_in_page):
        if q_int < 1:
            continue
        for q_str in (f"q{q_int:02d}", f"q{q_int}"):
            for ext in (".png", ".jpg"):
                fname = f"{book_dir}_p{page_str}_{q_str}{ext}"
                fpath = dir_path / fname
                if fpath.exists():
                    return f"/static/crops/{book_dir}/{fname}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=0, help="N sample pilot (no DB write)")
    ap.add_argument("--full", action="store_true", help="All NULL image rows")
    ap.add_argument(
        "--apply", action="store_true", help="Apply DB UPDATE (else dry-run)"
    )
    args = ap.parse_args()

    from sqlalchemy import create_engine, text

    eng = create_engine(
        os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    )

    if args.pilot:
        limit_sql = f"LIMIT {args.pilot}"
    elif args.full:
        limit_sql = ""
    else:
        print("[error] --pilot N veya --full gerekli")
        return 2

    sql = f"""
        SELECT id::text, source_book, pipeline_metadata::text
        FROM question_bank
        WHERE is_active=true
          AND (question_image_url IS NULL OR question_image_url='')
          AND source_book IS NOT NULL
          AND pipeline_metadata IS NOT NULL
        {limit_sql}
    """

    found, not_found, no_metadata = 0, 0, 0
    matches = []  # (id, url)

    with eng.connect() as c:
        rows = c.execute(text(sql)).fetchall()

    print(f"[scan] {len(rows):,} rows to process")

    for r in rows:
        pm = json.loads(r.pipeline_metadata) if r.pipeline_metadata else {}
        request_key = pm.get("request_key", "")
        ai_extras = pm.get("ai_extras", {}) or {}
        q_no = ai_extras.get("q_no")
        page = extract_page_num(request_key)

        q_idx = ai_extras.get("q_index_in_page")
        # Tier 4: legacy crop_file field (pre-v4.14e dataset)
        crop_file = pm.get("crop_file")

        if page is None and not crop_file:
            no_metadata += 1
            continue
        if not crop_file and q_no is None and q_idx is None:
            no_metadata += 1
            continue

        url = None
        if q_no is not None and page is not None:
            url = find_crop(r.source_book, page, q_no)
        if not url and q_idx is not None and page is not None:
            url = find_crop_by_qidx(r.source_book, page, int(q_idx))
        if not url and crop_file:
            # Tier 4: direct legacy crop_file lookup
            book_dir = find_disk_dir(r.source_book)
            if book_dir:
                fpath = CROPS_BASE / book_dir / crop_file
                if fpath.exists():
                    url = f"/static/crops/{book_dir}/{crop_file}"

        if url:
            found += 1
            matches.append((r.id, url))
        else:
            not_found += 1

    print(
        f"\n[result] found={found:,}, not_found={not_found:,}, no_metadata={no_metadata:,}"
    )
    print(f"[match rate] {found / (found + not_found + no_metadata) * 100:.1f}%")

    if args.apply and matches:
        print(f"\n[apply] updating {len(matches):,} rows...")
        batch_size = 500
        for i in range(0, len(matches), batch_size):
            batch = matches[i : i + batch_size]
            with eng.begin() as c:
                for qid, url in batch:
                    c.execute(
                        text(
                            "UPDATE question_bank SET question_image_url=:url, "
                            "pipeline_metadata = jsonb_set("
                            "  COALESCE(CAST(pipeline_metadata AS jsonb), '{}'::jsonb), "
                            "  '{image_match_metadata_v1}', "
                            '  \'{"date":"2026-05-19","source":"image_match_metadata_v1"}\'::jsonb, '
                            "  TRUE"
                            ")::json, "
                            "updated_at=NOW() "
                            "WHERE id::text=:qid"
                        ),
                        {"url": url, "qid": qid},
                    )
            print(
                f"  batch {i // batch_size + 1}/{(len(matches) + batch_size - 1) // batch_size}: {len(batch)} done"
            )

    # Sample print
    print("\n[sample matches]")
    for qid, url in matches[:5]:
        print(f"  {qid[:8]} → {url[:80]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
