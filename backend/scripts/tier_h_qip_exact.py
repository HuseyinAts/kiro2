#!/usr/bin/env python3
"""
Faz 1.5+++ Tier H — q_index_in_page direct exact match.

KRİTİK KEŞIF (Session 158 derin analiz):
  `pipeline_metadata.ai_extras.q_index_in_page` field = page-içi 1-based sıra.
  Disk crop filename `_p<page:04d>_q<NN:02d>.png` ile DIREKT EŞLEŞIR.

Tier C ile fark:
  - Tier C: `ai_extras.q_no` (kitap test numarası, OCR yanlış okuyabilir)
  - Tier H: `ai_extras.q_index_in_page` (page-içi sıra, OCR pipeline kayıtlı)

Sample doğrulama:
  DB: source_page=213, q_index_in_page=1
  Disk: ..._p0213_q01.png ✓

Potansiyel:
  - 63,197 aday → 49,468 exact match (%78.3)
  - 3,757 has_diagram=true (current 4,994 missing'in %75)
  - Geriye: 1,237 has_diagram=true missing (Plan v1 <%5 SAĞLANIR)

Strateji:
  - image_url IS NULL & q_index_in_page numeric & disk file exists
  - URL: /static/crops/<book_dir>/<filename>
  - Defansif: pipeline_metadata.tier_h_match flag

Risk: q_index_in_page yanlış olabilir mi?
  - OCR pipeline page-scan output (deterministic counting)
  - Disk crop'lar aynı pipeline'dan üretilmiş
  - Sample 8/8 doğru — exact filename match güvenilir

Kullanim:
    cd backend
    python scripts/tier_h_qip_exact.py --dry-run
    python scripts/tier_h_qip_exact.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from time import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AUDIT_DATE = "2026-05-15"
URL_PREFIX = "/static/crops"
PROJECT_ROOT = Path(__file__).parent.parent.parent
CROPS_ROOT = PROJECT_ROOT / "d-dataset" / "output" / "crops"


def get_engine():
    from sqlalchemy import create_engine

    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass
    db_url = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")
    return create_engine(db_url)


def build_disk_cache():
    print("[1/4] Disk dosya cache", end=" ... ", flush=True)
    t0 = time()
    cache: dict[str, set[str]] = {}
    cache_lower: dict[str, str] = {}
    for p in CROPS_ROOT.iterdir():
        if not p.is_dir():
            continue
        try:
            files = {
                f.name for f in p.iterdir() if f.is_file() and f.name.endswith(".png")
            }
        except (PermissionError, OSError):
            files = set()
        cache[p.name] = files
        cache_lower[p.name.lower()] = p.name
    print(f"OK ({time() - t0:.1f}s, {len(cache)} kitap)")
    return cache, cache_lower


def fetch_candidates(engine):
    from sqlalchemy import text

    SQL = """
        SELECT id::text, source_book, source_page,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page')::int AS qip,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') AS hd
        FROM question_bank
        WHERE is_active=TRUE
          AND question_image_url IS NULL
          AND source_book IS NOT NULL
          AND source_page IS NOT NULL
          AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page') ~ '^[0-9]+$'
    """
    print("[2/4] DB aday fetch", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as c:
        rows = list(c.execute(text(SQL)))
    print(f"OK ({time() - t0:.1f}s, {len(rows):,} satir)")
    return rows


def match_all(rows, disk_cache, disk_cache_lower):
    print("[3/4] Tier H exact match", end=" ... ", flush=True)
    t0 = time()
    matches = []
    stats = Counter()
    for qid, book, page, qip, hd in rows:
        stats["total"] += 1
        stats[f"hd_{hd or 'NULL'}"] += 1
        book_dir = book.replace(" ", "_")
        files = disk_cache.get(book_dir)
        if files is None:
            actual_name = disk_cache_lower.get(book_dir.lower())
            if actual_name:
                files = disk_cache.get(actual_name)
                book_dir = actual_name
        if not files:
            stats["no_book_dir"] += 1
            continue
        expected_suffix = f"_p{page:04d}_q{qip:02d}.png"
        # Prefer exact suffix match (skip "(1).png" variants)
        primary = [f for f in files if f.endswith(expected_suffix)]
        if not primary:
            stats["no_disk_match"] += 1
            continue
        crop_file = primary[0]
        stats["matched"] += 1
        if hd == "true":
            stats["matched_hd_true"] += 1
        elif hd is None:
            stats["matched_hd_NULL"] += 1
        else:
            stats["matched_hd_false"] += 1
        matches.append(
            {
                "id": qid,
                "book": book,
                "book_dir": book_dir,
                "page": page,
                "qip": qip,
                "crop_file": crop_file,
                "hd_pre": hd,
            }
        )
    print(f"OK ({time() - t0:.1f}s)")
    print()
    print("  İstatistik:")
    total = stats["total"]
    for k in [
        "total",
        "matched",
        "matched_hd_true",
        "matched_hd_NULL",
        "matched_hd_false",
        "no_disk_match",
        "no_book_dir",
    ]:
        n = stats[k]
        if n:
            pct = 100.0 * n / total if total else 0
            print(f"    {k:22s} {n:>6,} ({pct:5.2f}%)")
    return matches, stats


def apply_matches(engine, matches, batch_size=1000):
    from sqlalchemy import text

    # has_diagram=NULL ise true'ya update et + image_url + tier_h flag
    UPDATE_SQL = """
        UPDATE question_bank
        SET question_image_url = :url,
            pipeline_metadata = jsonb_set(
                jsonb_set(
                    COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
                    '{tier_h_match}',
                    CAST(:flag_json AS jsonb),
                    TRUE
                ),
                '{ai_extras,has_diagram}',
                CASE
                    WHEN (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') IS NULL
                    THEN '"true"'::jsonb
                    ELSE pipeline_metadata::jsonb -> 'ai_extras' -> 'has_diagram'
                END,
                TRUE
            )::json
        WHERE id = :id
          AND question_image_url IS NULL
    """
    print(f"\n[4/4] DB update (batch={batch_size}) ...")
    updated = 0
    failed = 0
    skipped = 0
    with engine.begin() as conn:
        for i in range(0, len(matches), batch_size):
            batch = matches[i : i + batch_size]
            for m in batch:
                url = f"{URL_PREFIX}/{m['book_dir']}/{m['crop_file']}"
                flag = {
                    "tier": "H",
                    "crop_file": m["crop_file"],
                    "q_index_in_page": m["qip"],
                    "hd_pre": m["hd_pre"],
                    "audit_date": AUDIT_DATE,
                }
                try:
                    r = conn.execute(
                        text(UPDATE_SQL),
                        {
                            "id": m["id"],
                            "url": url,
                            "flag_json": json.dumps(flag),
                        },
                    )
                    if r.rowcount > 0:
                        updated += 1
                    else:
                        skipped += 1
                except Exception as e:
                    failed += 1
                    if failed <= 3:
                        print(f"  [WARN] {m['id'][:8]}: {e}")
            done = i + len(batch)
            pct = done / len(matches) * 100
            print(
                f"  [{pct:5.1f}%] {done:,}/{len(matches):,} "
                f"({updated:,} updated, {skipped:,} skipped, {failed:,} failed)"
            )
    print(f"\nUpdated: {updated}, Skipped: {skipped}, Failed: {failed}")
    return updated


def main():
    parser = argparse.ArgumentParser(
        description="Tier H q_index_in_page exact (Faz 1.5+++)"
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    engine = get_engine()
    cache, cache_lower = build_disk_cache()
    rows = fetch_candidates(engine)
    matches, _ = match_all(rows, cache, cache_lower)

    if args.dry_run:
        print(f"\n[DRY-RUN] {len(matches):,} match. UPDATE atilmadi.")
        return
    if not matches:
        print("\nMatch yok.")
        return
    print(f"\n[APPLY] {len(matches):,} satir...")
    apply_matches(engine, matches)
    print("\nTamamlandi.")


if __name__ == "__main__":
    main()
