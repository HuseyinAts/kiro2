#!/usr/bin/env python3
"""
Tier C image matcher — DB-driven exact match.

Hedef populasyon (49,313 satir):
    is_active = TRUE
    AND quality_review_status = 'unverified'
    AND question_image_url IS NULL
    AND ai_extras.has_diagram = TRUE

Bu populasyon Tier A+B kapsami disinda (107K v4.14e Gemini Flash batch
production JSONL'de yok, dogrudan DB'ye yazilmis).

Pattern (audit_missing_image_v2 kanitladi, 16,440 exact_match):
    {book_underscored}_p{page:04d}_q{qno:02d}.png

Audit RESULT: backend/_pilots/20260515_missing_image_v2_RESULT.md

Kullanim:
    cd backend
    python scripts/populate_image_urls_tier_c.py --dry-run
    python scripts/populate_image_urls_tier_c.py --apply
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from time import time

# Reuse proven helpers from Tier A+B script
sys.path.insert(0, str(Path(__file__).parent))
from populate_image_urls import (
    CROP_BASE,
    URL_PREFIX,
)

# =============================================================================
# Tier C target SQL (audit_missing_image_repair_potential.py'den dogrulandi)
# =============================================================================

TARGET_SQL = """
SELECT
    id::text AS id,
    source_book,
    source_page,
    pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' AS q_no,
    pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' AS match_quality
FROM question_bank
WHERE is_active = TRUE
  AND quality_review_status = 'unverified'
  AND question_image_url IS NULL
  AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram')::boolean = TRUE
"""


# =============================================================================
# Helpers (Tier C-spesifik, mevcut populate_image_urls.py ile uyumlu)
# =============================================================================


def book_to_dir_name(book: str) -> str:
    """DB source_book -> disk dir adi (audit_v2 ile ayni stratey).

    Bosluk -> underscore. NFC normalize. Turkce karakterler korunur.
    """
    if not book:
        return ""
    return unicodedata.normalize("NFC", book.replace(" ", "_").strip())


def safe_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def expected_filename(book_dir: str, page: int, q_no: int) -> str:
    """`{book}_p{page:04d}_q{qno:02d}.png` — audit_v2 ile bire bir."""
    return f"{book_dir}_p{page:04d}_q{q_no:02d}.png"


def build_disk_file_index() -> tuple[dict[str, Path], dict[Path, set[str]]]:
    """Tum kitap dir'lerini ve icindeki dosya set'lerini cache'le.

    Returns:
        (dir_index, file_cache)
        dir_index: {dir_name: Path, dir_name_lower: Path}
        file_cache: {Path: {filename, ...}}
    """
    print(
        f"[1/4] Disk file index kuruluyor: {CROP_BASE}",
        end=" ... ",
        flush=True,
    )
    t0 = time()
    dir_index: dict[str, Path] = {}
    file_cache: dict[Path, set[str]] = {}

    for p in CROP_BASE.iterdir():
        if not p.is_dir():
            continue
        dir_index[p.name] = p
        dir_index[p.name.lower()] = p
        try:
            file_cache[p] = {f.name for f in p.iterdir() if f.is_file()}
        except (PermissionError, OSError):
            file_cache[p] = set()

    n_dirs = len(set(dir_index.values()))
    n_files = sum(len(s) for s in file_cache.values())
    print(f"OK ({time() - t0:.1f}s, {n_dirs} dir, {n_files:,} file)")
    return dir_index, file_cache


def find_book_dir(book: str, dir_index: dict[str, Path]) -> Path | None:
    """DB book name -> disk Path. Case-insensitive fallback."""
    cand = book_to_dir_name(book)
    if not cand:
        return None
    if cand in dir_index:
        return dir_index[cand]
    cand_lower = cand.lower()
    if cand_lower in dir_index:
        return dir_index[cand_lower]
    return None


# =============================================================================
# DB Engine
# =============================================================================


def get_engine():
    from sqlalchemy import create_engine

    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:1470@localhost:5434/kiro2",
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")
    return create_engine(db_url)


# =============================================================================
# Phases
# =============================================================================


def fetch_target_rows(engine) -> list[dict]:
    """49,313 satiri DB'den cek."""
    from sqlalchemy import text

    print("[2/4] DB'den hedef satirlar cekiliyor", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as conn:
        rows = [dict(r._mapping) for r in conn.execute(text(TARGET_SQL))]
    print(f"OK ({time() - t0:.1f}s, {len(rows):,} satir)")
    return rows


def match_tier_c(
    rows: list[dict],
    dir_index: dict[str, Path],
    file_cache: dict[Path, set[str]],
) -> tuple[list[dict], Counter]:
    """Her satir icin disk'te exact_match dene.

    Returns:
        (matched_results, stats_counter)
        matched_results: [{id, book, page, q_no, crop_file, url}, ...]
    """
    print("[3/4] Tier C exact match", end=" ... ", flush=True)
    t0 = time()
    results: list[dict] = []
    stats: Counter = Counter()

    for row in rows:
        stats["total"] += 1

        book = row.get("source_book") or ""
        page = safe_int(row.get("source_page"))
        q_no = safe_int(row.get("q_no"))

        if not book or page is None or q_no is None:
            stats["invalid_key"] += 1
            continue

        book_dir = find_book_dir(book, dir_index)
        if book_dir is None:
            stats["no_book_dir"] += 1
            continue

        dir_name = book_dir.name
        expected = expected_filename(dir_name, page, q_no)

        files = file_cache.get(book_dir, set())
        if expected in files:
            url = f"{URL_PREFIX}/{dir_name}/{expected}"
            results.append(
                {
                    "id": row["id"],
                    "book": book,
                    "page": page,
                    "q_no": q_no,
                    "crop_file": expected,
                    "url": url,
                }
            )
            stats["exact_match"] += 1
        else:
            stats["no_exact"] += 1

    print(f"OK ({time() - t0:.1f}s, {len(results):,}/{len(rows):,} matched)")
    print()
    print("  Match istatistikleri:")
    for st, n in stats.most_common():
        pct = 100.0 * n / stats["total"]
        print(f"    {st:20s} {n:>7,} ({pct:5.1f}%)")
    return results, stats


def update_database(engine, results: list[dict], batch_size: int = 1000) -> int:
    """Batch UPDATE question_bank.question_image_url. Idempotent."""
    from sqlalchemy import text

    UPDATE_SQL = """
        UPDATE question_bank
        SET question_image_url = :url
        WHERE id = :id
          AND (question_image_url IS NULL OR question_image_url != :url)
    """

    print(f"[4/4] DB update (batch={batch_size}) ...")
    updated = 0
    skipped = 0

    with engine.begin() as conn:
        for i in range(0, len(results), batch_size):
            batch = results[i : i + batch_size]
            for row in batch:
                r = conn.execute(
                    text(UPDATE_SQL),
                    {"url": row["url"], "id": row["id"]},
                )
                if r.rowcount > 0:
                    updated += 1
                else:
                    skipped += 1
            done = i + len(batch)
            pct = done / len(results) * 100
            print(
                f"  [{pct:5.1f}%] {done:,}/{len(results):,} "
                f"({updated:,} updated, {skipped:,} skipped)"
            )

    # Verification
    with engine.connect() as conn:
        with_url = conn.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE question_image_url IS NOT NULL"
            )
        ).scalar()
        total = conn.execute(text("SELECT COUNT(*) FROM question_bank")).scalar()

    print()
    print("DB dogrulama:")
    print(
        f"  question_image_url NOT NULL: {with_url:,} / {total:,} ({with_url * 100 / total:.1f}%)"
    )
    print(f"  Bu run'da yeni populate: {updated:,}")
    print(f"  Skip (zaten ayni veya UUID match yok): {skipped:,}")
    return updated


# =============================================================================
# Sample
# =============================================================================


def print_sample(results: list[dict], n: int = 10) -> None:
    print()
    print(f"Random sample ({n} satir):")
    print("-" * 100)
    for r in random.sample(results, min(n, len(results))):
        book_short = r["book"][:40]
        print(
            f"  id={r['id'][:8]}.. {book_short:40s} "
            f"p{r['page']:04d} q{r['q_no']:02d} -> {r['crop_file']}"
        )
    print("-" * 100)


# =============================================================================
# Entry point
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="Tier C image matcher (DB-driven)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="Report only")
    g.add_argument("--apply", action="store_true", help="Apply DB UPDATE")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    if not CROP_BASE.exists():
        print(f"[ERROR] Crop base bulunamadi: {CROP_BASE}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("populate_image_urls_tier_c.py")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print()

    # Phase 1: Disk index
    dir_index, file_cache = build_disk_file_index()

    # Phase 2: DB fetch
    engine = get_engine()
    rows = fetch_target_rows(engine)

    if not rows:
        print("[WARN] Hedef satir bulunamadi (49,313 bekleniyordu).")
        sys.exit(0)

    # Phase 3: Match
    results, _stats = match_tier_c(rows, dir_index, file_cache)

    if not results:
        print("[ERROR] Hicbir match yok.")
        sys.exit(1)

    print_sample(results, args.sample_size)

    # Phase 4: Apply
    if args.apply:
        updated = update_database(engine, results, args.batch_size)
        print()
        print(f"Done. {updated:,} satir question_image_url populate edildi.")
    else:
        print()
        print("[DRY RUN] DB degistirilmedi. --apply ile calistir.")

    engine.dispose()


if __name__ == "__main__":
    main()
