#!/usr/bin/env python3
"""
Crop PNG dosyalarini question_bank.question_image_url alanina eslestir.

Strateji (2 Tier, dogrulanmis):
  Tier A: v3_tier15.jsonl.bak'taki direkt crop_file mapping
          + production JSONL'de merge_source=v3* filtresi
          → 32,046 soru, ~%99.99 dogruluk

  Tier B: ocr_crops/results.jsonl'deki soru_no match
          + text similarity >=70% dogrulama
          → ~26,477 soru, ~%98+ dogruluk

  Toplam: ~58,523 soru (%75.7 coverage), 0 collision

Kullanim:
    cd backend
    python scripts/populate_image_urls.py --dry-run
    python scripts/populate_image_urls.py --apply
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

# Same namespace as import_d_dataset.py for deterministic UUID
KIRO2_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


# =============================================================================
# Paths
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
D_DATASET = PROJECT_ROOT / "d-dataset"

TIER15_PATH = D_DATASET / "output" / "matched_v3" / "eslesmis_sorucevap_v3_with_tier15.jsonl.bak"
OCR_CROPS_PATH = D_DATASET / "output" / "ocr_crops" / "results.jsonl"
PRODUCTION_JSONL = D_DATASET / "eslesmis_sorucevap.jsonl"
CROP_BASE = D_DATASET / "output" / "crops"

URL_PREFIX = "/static/crops"


# =============================================================================
# Helpers
# =============================================================================

def norm_book(name: str) -> str:
    """Normalize book name for matching: NFC + underscore→space + strip."""
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


def extract_crop_dir(crop_file: str) -> str | None:
    """Extract directory name from crop filename.

    Example: 'DirName_p0006_q02.png' → 'DirName'
    """
    m = re.match(r"^(.+)_p\d{4}_q\d{2}\.png$", crop_file)
    return m.group(1) if m else None


def text_similarity(text_a: str, text_b: str) -> float:
    """Word overlap Jaccard similarity (Turkish NFC normalized)."""
    if not text_a or not text_b:
        return 0.0
    words_a = set(unicodedata.normalize("NFC", text_a).lower().split())
    words_b = set(unicodedata.normalize("NFC", text_b).lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def crop_exists(crop_file: str) -> bool:
    """Check if crop PNG file exists on disk."""
    dir_name = extract_crop_dir(crop_file)
    if not dir_name:
        return False
    return (CROP_BASE / dir_name / crop_file).exists()


def crop_url(crop_file: str) -> str | None:
    """Build URL from crop filename."""
    dir_name = extract_crop_dir(crop_file)
    if not dir_name:
        return None
    return f"{URL_PREFIX}/{dir_name}/{crop_file}"


def generate_question_id(book_name: str, page: int, q_num: int) -> str:
    """Generate deterministic UUID from question identity triple.

    Must match import_d_dataset.py's generate_question_id().
    """
    key = f"{book_name}|{page}|{q_num}"
    return str(uuid.uuid5(KIRO2_NAMESPACE, key))


# =============================================================================
# Index Builders
# =============================================================================

def build_tier15_index() -> dict[tuple, str]:
    """Load v3_tier15 → {(norm_book, page, qnum): crop_file}."""
    print(f"Loading Tier A index: {TIER15_PATH.name} ...", end=" ", flush=True)
    t0 = time()
    index: dict[tuple, str] = {}
    errors = 0

    with open(TIER15_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                errors += 1
                continue
            book = norm_book(d.get("book_name", ""))
            page = safe_int(d.get("page_number"))
            qnum = safe_int(d.get("question_number"))
            cf = d.get("crop_file", "")
            if not book or page is None or qnum is None or not cf:
                continue
            index[(book, page, qnum)] = cf

    print(f"{len(index):,} entries ({time()-t0:.1f}s, {errors} errors)")
    return index


def build_ocr_index() -> dict[tuple, dict]:
    """Load ocr_crops → {(norm_book, page, soru_no): {crop_file, text}}."""
    print(f"Loading Tier B index: {OCR_CROPS_PATH.name} ...", end=" ", flush=True)
    t0 = time()
    index: dict[tuple, dict] = {}
    skipped_none = 0
    errors = 0

    with open(OCR_CROPS_PATH, encoding="utf-8") as f:
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
                skipped_none += 1
                continue

            book = norm_book(d.get("book", ""))
            page = safe_int(d.get("page_num"))
            if not book or page is None:
                continue

            key = (book, page, soru_no)
            # Keep last entry if duplicate (later = better OCR usually)
            index[key] = {
                "crop_file": d.get("crop_file", ""),
                "text": d.get("soru_metni", "") or "",
            }

    print(f"{len(index):,} entries ({time()-t0:.1f}s, "
          f"soru_no=None: {skipped_none:,}, errors: {errors})")
    return index


# =============================================================================
# Main Matching
# =============================================================================

def match_questions(tier15_index, ocr_index):
    """Match production JSONL questions to crop files.

    Returns list of {book_name, page_number, question_number, crop_file, url, tier}.
    """
    print(f"\nMatching production JSONL: {PRODUCTION_JSONL.name} ...")
    t0 = time()

    results = []
    stats = Counter()
    disk_missing = 0

    with open(PRODUCTION_JSONL, encoding="utf-8") as f:
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

            merge_source = d.get("merge_source", "") or ""
            prod_text = d.get("text", "") or ""
            key = (book, page, qnum)

            crop_file = None
            tier = None

            # --- Tier A: v3* merge_source + tier15 direct mapping ---
            if merge_source.startswith("v3") and key in tier15_index:
                crop_file = tier15_index[key]
                tier = "A"

            # --- Tier B: ocr_crops soru_no match + text similarity ---
            if crop_file is None and key in ocr_index:
                ocr_entry = ocr_index[key]
                ocr_text = ocr_entry["text"]
                sim = text_similarity(prod_text, ocr_text)
                if sim >= 0.70:
                    crop_file = ocr_entry["crop_file"]
                    tier = "B"
                else:
                    stats["tier_b_low_sim"] += 1

            if crop_file is None:
                stats["no_match"] += 1
                continue

            # Verify file exists on disk
            if not crop_exists(crop_file):
                disk_missing += 1
                stats["disk_missing"] += 1
                continue

            url = crop_url(crop_file)
            if not url:
                stats["url_error"] += 1
                continue

            # Generate deterministic UUID (same as import_d_dataset.py)
            q_id = generate_question_id(d.get("book_name", ""), page, qnum)

            results.append({
                "id": q_id,
                "book_name": d.get("book_name", ""),
                "page_number": page,
                "question_number": qnum,
                "crop_file": crop_file,
                "url": url,
                "tier": tier,
            })
            stats[f"tier_{tier.lower()}"] += 1

    elapsed = time() - t0
    print(f"\nMatching complete ({elapsed:.1f}s)")
    print(f"  Total production:  {stats['total']:,}")
    print(f"  Tier A (v3+tier15): {stats.get('tier_a', 0):,}")
    print(f"  Tier B (ocr+text):  {stats.get('tier_b', 0):,}")
    print(f"  Low similarity:     {stats.get('tier_b_low_sim', 0):,}")
    print(f"  No match:           {stats.get('no_match', 0):,}")
    print(f"  Disk missing:       {disk_missing:,}")
    print(f"  TOTAL MATCHED:      {len(results):,} "
          f"({len(results)*100/stats['total']:.1f}%)")

    return results


# =============================================================================
# DB Update
# =============================================================================

def update_database(results, batch_size=1000):
    """Batch UPDATE question_bank.question_image_url."""
    from sqlalchemy import create_engine, text

    # Load .env for DATABASE_URL
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:changeme@localhost:5434/kiro2",
    )
    # Force sync driver
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")

    print(f"\nDB: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    engine = create_engine(db_url)

    UPDATE_SQL = """
        UPDATE question_bank
        SET question_image_url = :url
        WHERE id = :id
          AND (question_image_url IS NULL OR question_image_url != :url)
    """

    updated = 0
    skipped = 0

    with engine.begin() as conn:
        for i in range(0, len(results), batch_size):
            batch = results[i : i + batch_size]
            for row in batch:
                result = conn.execute(text(UPDATE_SQL), {
                    "url": row["url"],
                    "id": row["id"],
                })
                if result.rowcount > 0:
                    updated += 1
                else:
                    skipped += 1

            done = i + len(batch)
            pct = done / len(results) * 100
            print(f"  [{pct:5.1f}%] {done:,}/{len(results):,} "
                  f"({updated:,} updated, {skipped:,} skipped)")

    # Verify
    with engine.connect() as conn:
        total_with_url = conn.execute(text(
            "SELECT COUNT(*) FROM question_bank "
            "WHERE question_image_url IS NOT NULL"
        )).scalar()
        total_all = conn.execute(text(
            "SELECT COUNT(*) FROM question_bank"
        )).scalar()

    engine.dispose()

    print("\nDB verification:")
    print(f"  question_image_url NOT NULL: {total_with_url:,} / {total_all:,} "
          f"({total_with_url*100/total_all:.1f}%)")
    print(f"  Updated this run: {updated:,}")
    print(f"  Skipped (already set or no match): {skipped:,}")

    return updated


# =============================================================================
# Sample Report
# =============================================================================

def print_sample(results, n=10):
    """Print random sample for manual verification."""
    import random
    sample = random.sample(results, min(n, len(results)))
    print(f"\nSample ({n} random):")
    print("-" * 100)
    for r in sample:
        print(f"  [{r['tier']}] {r['book_name'][:40]:40s} p{r['page_number']:04d} "
              f"q{r['question_number']:02d} -> {r['crop_file']}")
    print("-" * 100)


# =============================================================================
# Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Populate question_image_url from crop files")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no DB changes")
    parser.add_argument("--apply", action="store_true", help="Apply changes to database")
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Usage: specify --dry-run or --apply")
        sys.exit(1)

    # Verify paths
    for path, label in [
        (TIER15_PATH, "Tier A source"),
        (OCR_CROPS_PATH, "Tier B source"),
        (PRODUCTION_JSONL, "Production JSONL"),
        (CROP_BASE, "Crop base dir"),
    ]:
        if not path.exists():
            print(f"[ERROR] {label} not found: {path}")
            sys.exit(1)

    print("=" * 60)
    print("populate_image_urls.py")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print()

    # Phase 1: Build indexes
    tier15_index = build_tier15_index()
    ocr_index = build_ocr_index()

    # Phase 2: Match
    results = match_questions(tier15_index, ocr_index)

    if not results:
        print("\n[WARNING] No matches found!")
        sys.exit(1)

    # Phase 3: Report
    tier_a = sum(1 for r in results if r["tier"] == "A")
    tier_b = sum(1 for r in results if r["tier"] == "B")
    print("\nTier breakdown:")
    print(f"  A (v3+tier15):  {tier_a:,}")
    print(f"  B (ocr+text):   {tier_b:,}")
    print(f"  Total:          {len(results):,}")

    print_sample(results)

    # Phase 4: DB update
    if args.apply:
        updated = update_database(results, args.batch_size)
        print(f"\nDone! {updated:,} questions updated.")
    else:
        print("\n[DRY RUN] No database changes made.")
        print("Run with --apply to update the database.")


if __name__ == "__main__":
    main()
