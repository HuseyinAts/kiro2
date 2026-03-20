#!/usr/bin/env python3
"""
Populate image_ocr_text, image_width, image_height in question_bank.

Iki kaynak:
  1. OCR metin: d-dataset/output/ocr_crops/results.jsonl (soru_metni alani)
  2. Boyutlar: Disk'teki crop PNG dosyalari (PIL ile okuma)

Kullanim:
    cd backend
    python scripts/populate_image_metadata.py --dry-run
    python scripts/populate_image_metadata.py --apply
"""

import argparse
import json
import os
import re
import sys
import unicodedata
import uuid
from collections import Counter
from pathlib import Path
from time import time

KIRO2_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

PROJECT_ROOT = Path(__file__).parent.parent.parent
D_DATASET = PROJECT_ROOT / "d-dataset"
OCR_CROPS_PATH = D_DATASET / "output" / "ocr_crops" / "results.jsonl"
PRODUCTION_JSONL = D_DATASET / "eslesmis_sorucevap.jsonl"
CROP_BASE = D_DATASET / "output" / "crops"


def norm_book(name: str) -> str:
    if not name:
        return ""
    return unicodedata.normalize("NFC", name.replace("_", " ").strip())


def safe_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def generate_question_id(book_name: str, page: int, q_num: int) -> str:
    key = f"{book_name}|{page}|{q_num}"
    return str(uuid.uuid5(KIRO2_NAMESPACE, key))


def extract_crop_dir(crop_file: str) -> str | None:
    m = re.match(r"^(.+)_p\d{4}_q\d{2}\.png$", crop_file)
    return m.group(1) if m else None


def build_ocr_index() -> dict[tuple, dict]:
    """Load ocr_crops -> {(norm_book, page, soru_no): {crop_file, text}}."""
    print(f"Loading OCR index: {OCR_CROPS_PATH.name} ...", end=" ", flush=True)
    t0 = time()
    index: dict[tuple, dict] = {}
    errors = 0

    with open(OCR_CROPS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                errors += 1
                continue

            soru_no = safe_int(d.get("soru_no"))
            if soru_no is None:
                continue

            book = norm_book(d.get("book", ""))
            page = safe_int(d.get("page_num"))
            if not book or page is None:
                continue

            key = (book, page, soru_no)
            index[key] = {
                "crop_file": d.get("crop_file", ""),
                "text": d.get("soru_metni", "") or "",
            }

    print(f"{len(index):,} entries ({time()-t0:.1f}s, errors: {errors})")
    return index


def get_image_dimensions(crop_file: str) -> tuple[int, int] | None:
    """Get width, height from crop PNG file."""
    dir_name = extract_crop_dir(crop_file)
    if not dir_name:
        return None
    path = CROP_BASE / dir_name / crop_file
    if not path.exists():
        return None
    try:
        from PIL import Image
        with Image.open(path) as img:
            return img.size  # (width, height)
    except Exception:
        return None


def match_and_collect(ocr_index):
    """Match production questions to OCR text and image dimensions."""
    print(f"\nMatching production JSONL: {PRODUCTION_JSONL.name} ...")
    t0 = time()

    results = []
    stats = Counter()

    with open(PRODUCTION_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                stats["parse_error"] += 1
                continue

            stats["total"] += 1
            book = norm_book(d.get("book_name", ""))
            page = safe_int(d.get("page_number"))
            qnum = safe_int(d.get("question_number"))
            if not book or page is None or qnum is None:
                stats["invalid_key"] += 1
                continue

            q_id = generate_question_id(d.get("book_name", ""), page, qnum)
            key = (book, page, qnum)

            # OCR text
            ocr_text = None
            crop_file = None
            if key in ocr_index:
                ocr_entry = ocr_index[key]
                ocr_text = ocr_entry["text"]
                crop_file = ocr_entry["crop_file"]

            # Image dimensions (from URL-mapped crop or OCR crop)
            # Try to find crop_file from the question's existing image URL
            crop_file_for_dims = crop_file
            if not crop_file_for_dims:
                # Try constructing from other tier mappings
                # Skip — we only have dimensions for matched crops
                pass

            dims = None
            if crop_file_for_dims:
                dims = get_image_dimensions(crop_file_for_dims)

            if ocr_text or dims:
                entry = {"id": q_id}
                if ocr_text:
                    entry["ocr_text"] = ocr_text
                    stats["has_ocr"] += 1
                if dims:
                    entry["width"] = dims[0]
                    entry["height"] = dims[1]
                    stats["has_dims"] += 1
                results.append(entry)

    elapsed = time() - t0
    print(f"\nMatching complete ({elapsed:.1f}s)")
    print(f"  Total production:  {stats['total']:,}")
    print(f"  Has OCR text:      {stats.get('has_ocr', 0):,}")
    print(f"  Has dimensions:    {stats.get('has_dims', 0):,}")
    print(f"  TOTAL with data:   {len(results):,}")

    return results


def update_database(results, batch_size=1000):
    """Batch UPDATE question_bank with OCR text and dimensions."""
    from sqlalchemy import create_engine, text

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:changeme@localhost:5434/kiro2",
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")

    print(f"\nDB: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    engine = create_engine(db_url)

    updated_ocr = 0
    updated_dims = 0

    with engine.begin() as conn:
        for i in range(0, len(results), batch_size):
            batch = results[i : i + batch_size]
            for row in batch:
                # Update OCR text
                if "ocr_text" in row:
                    result = conn.execute(text("""
                        UPDATE question_bank
                        SET image_ocr_text = :ocr_text
                        WHERE id = :id
                          AND (image_ocr_text IS NULL OR image_ocr_text != :ocr_text)
                    """), {"ocr_text": row["ocr_text"], "id": row["id"]})
                    if result.rowcount > 0:
                        updated_ocr += 1

                # Update dimensions
                if "width" in row:
                    result = conn.execute(text("""
                        UPDATE question_bank
                        SET image_width = :width, image_height = :height
                        WHERE id = :id
                          AND (image_width IS NULL OR image_width != :width)
                    """), {"width": row["width"], "height": row["height"], "id": row["id"]})
                    if result.rowcount > 0:
                        updated_dims += 1

            done = i + len(batch)
            pct = done / len(results) * 100
            print(f"  [{pct:5.1f}%] {done:,}/{len(results):,} "
                  f"(ocr: {updated_ocr:,}, dims: {updated_dims:,})")

    # Verify
    with engine.connect() as conn:
        ocr_count = conn.execute(text(
            "SELECT COUNT(*) FROM question_bank WHERE image_ocr_text IS NOT NULL"
        )).scalar()
        dims_count = conn.execute(text(
            "SELECT COUNT(*) FROM question_bank WHERE image_width IS NOT NULL"
        )).scalar()
        total = conn.execute(text("SELECT COUNT(*) FROM question_bank")).scalar()

    engine.dispose()

    print(f"\nDB verification:")
    print(f"  image_ocr_text NOT NULL: {ocr_count:,} / {total:,}")
    print(f"  image_width NOT NULL:    {dims_count:,} / {total:,}")
    print(f"  Updated OCR: {updated_ocr:,}, dims: {updated_dims:,}")

    return updated_ocr, updated_dims


def main():
    parser = argparse.ArgumentParser(description="Populate image metadata")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Usage: specify --dry-run or --apply")
        sys.exit(1)

    for path, label in [
        (OCR_CROPS_PATH, "OCR crops source"),
        (PRODUCTION_JSONL, "Production JSONL"),
        (CROP_BASE, "Crop base dir"),
    ]:
        if not path.exists():
            print(f"[ERROR] {label} not found: {path}")
            sys.exit(1)

    print("=" * 60)
    print("populate_image_metadata.py")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print()

    ocr_index = build_ocr_index()
    results = match_and_collect(ocr_index)

    if not results:
        print("\n[WARNING] No matches found!")
        sys.exit(1)

    ocr_count = sum(1 for r in results if "ocr_text" in r)
    dims_count = sum(1 for r in results if "width" in r)
    print(f"\nBreakdown:")
    print(f"  OCR text:    {ocr_count:,}")
    print(f"  Dimensions:  {dims_count:,}")
    print(f"  Total:       {len(results):,}")

    if args.apply:
        updated = update_database(results, args.batch_size)
        print(f"\nDone! OCR: {updated[0]:,}, dims: {updated[1]:,} updated.")
    else:
        print("\n[DRY RUN] No database changes made.")
        print("Run with --apply to update the database.")


if __name__ == "__main__":
    main()
