#!/usr/bin/env python3
"""
Tier H v2 — q_index_in_page OFFSET-AWARE exact match.

v1 BUG (Session 158): DB qip 0-indexed (%92.9 sayfa) ama Tier H v1
`qip → q<qip:02d>.png` direct match yaptı → 1 offset hatası.
49,468 satırın çoğu YANLIŞ image_url ile populate edildi.
ROLLBACK uygulandı (15 May 2026).

v2 strateji:
  1. Her sayfa için DB min(qip) hesapla (offset belirleme)
     - min(qip) = 0 → offset = +1 (DB 0-indexed → disk 1-indexed)
     - min(qip) = 1 → offset = 0 (already aligned)
     - min(qip) >= 2 → edge case, offset = 1 - min(qip) (kayma var)
  2. target_q = qip + offset
  3. Disk'te `_p<page:04d>_q<target_q:02d>.png` var → match
  4. Defansif: substring overlap doğrulaması (OCR text varsa) — pilot için

Kullanim:
    cd backend
    python scripts/tier_h_v2_qip_offset.py --pilot
    python scripts/tier_h_v2_qip_offset.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from time import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AUDIT_DATE = "2026-05-15"
URL_PREFIX = "/static/crops"
PILOT_N = 100
PILOT_SEED = 42
PROJECT_ROOT = Path(__file__).parent.parent.parent
CROPS_ROOT = PROJECT_ROOT / "d-dataset" / "output" / "crops"
OCR_PATH = PROJECT_ROOT / "d-dataset" / "output" / "ocr_crops" / "results.jsonl"
PILOT_TSV = (
    Path(__file__).parent.parent / "_pilots" / "20260515_tier_h_v2_pilot_RESULT.tsv"
)


def get_engine():
    from sqlalchemy import create_engine

    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")
    return create_engine(db_url)


def norm_book(s):
    return unicodedata.normalize("NFC", (s or "").strip())


def substring_overlap(db_text, ocr_text):
    """En uzun N-word substring DB → OCR."""
    db_n = re.sub(
        r"\s+", " ", unicodedata.normalize("NFC", db_text or "").lower()
    ).strip()
    ocr_n = re.sub(
        r"\s+", " ", unicodedata.normalize("NFC", ocr_text or "").lower()
    ).strip()
    db_words = db_n.split()
    if not db_words:
        return 0
    for window in [10, 8, 6, 5, 4]:
        if window > len(db_words):
            continue
        for i in range(len(db_words) - window + 1):
            if " ".join(db_words[i : i + window]) in ocr_n:
                return window
    return 0


def build_disk_cache():
    print("[1/6] Disk cache", end=" ... ", flush=True)
    t0 = time()
    cache = {}
    cache_lower = {}
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


def build_ocr_index():
    print("[2/6] OCR index", end=" ... ", flush=True)
    t0 = time()
    idx = defaultdict(dict)  # {(book, page): {crop_file: text}}
    with OCR_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            book = norm_book((d.get("book", "") or "").replace("_", " "))
            try:
                page = int(d.get("page_num"))
            except (TypeError, ValueError):
                continue
            cf = d.get("crop_file", "")
            if book and cf:
                idx[(book, page)][cf] = d.get("soru_metni", "") or ""
    print(f"OK ({time() - t0:.1f}s, {len(idx):,} page-key)")
    return idx


def fetch_candidates(engine):
    from sqlalchemy import text

    SQL = """
        SELECT id::text, source_book, source_page,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page')::int AS qip,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') AS hd,
               LEFT(question_text, 400) AS qt
        FROM question_bank
        WHERE is_active=TRUE
          AND question_image_url IS NULL
          AND source_book IS NOT NULL
          AND source_page IS NOT NULL
          AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_index_in_page') ~ '^[0-9]+$'
    """
    print("[3/6] DB aday fetch", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as c:
        rows = list(c.execute(text(SQL)))
    print(f"OK ({time() - t0:.1f}s, {len(rows):,})")
    return rows


def compute_page_offsets(rows):
    """Her (book, page) için min(qip) → offset."""
    print("[4/6] Page-level offset hesaplama", end=" ... ", flush=True)
    t0 = time()
    page_min = defaultdict(lambda: 10**9)
    for _, book, page, qip, _, _ in rows:
        key = (book, page)
        page_min[key] = min(page_min[key], qip)
    # offset = (target ilk crop's q_no = 1) - min(qip)
    page_offset = {}
    for key, mn in page_min.items():
        page_offset[key] = 1 - mn  # 0-based→+1, 1-based→0, 2-based→-1
    print(f"OK ({time() - t0:.1f}s, {len(page_offset):,} sayfa)")
    # Histogram
    offset_hist = Counter(page_offset.values())
    print(f"   Offset histogram: {dict(offset_hist.most_common(5))}")
    return page_offset


def match_all(
    rows, disk_cache, disk_cache_lower, page_offset, ocr_idx, validate_text=False
):
    print("[5/6] v2 offset-aware match", end=" ... ", flush=True)
    t0 = time()
    matches = []
    stats = Counter()
    for qid, book, page, qip, hd, qt in rows:
        stats["total"] += 1
        offset = page_offset.get((book, page), 0)
        target_q = qip + offset
        if target_q < 1:
            stats["target_neg"] += 1
            continue
        book_dir = book.replace(" ", "_")
        files = disk_cache.get(book_dir)
        if files is None:
            actual = disk_cache_lower.get(book_dir.lower())
            if actual:
                files = disk_cache.get(actual)
                book_dir = actual
        if not files:
            stats["no_book_dir"] += 1
            continue
        expected = f"_p{page:04d}_q{target_q:02d}.png"
        primary = [f for f in files if f.endswith(expected)]
        if not primary:
            stats["no_disk_match"] += 1
            continue
        crop_file = primary[0]
        # Validate text if requested
        sub_score = -1
        if validate_text:
            nbook = norm_book(book)
            ocr_text = ocr_idx.get((nbook, page), {}).get(crop_file, "")
            sub_score = substring_overlap(qt, ocr_text)
            if sub_score < 4:
                stats["sim_below_4"] += 1
                # Still include but flag
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
                "offset": offset,
                "target_q": target_q,
                "crop_file": crop_file,
                "hd_pre": hd,
                "sub_score": sub_score,
                "db_text": qt,
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
        "target_neg",
        "sim_below_4",
    ]:
        n = stats[k]
        if n:
            print(f"    {k:22s} {n:>6,} ({100 * n / total:5.2f}%)")
    return matches, stats


def write_pilot_tsv(matches, ocr_idx):
    random.seed(PILOT_SEED)
    samp = random.sample(matches, min(PILOT_N, len(matches)))
    PILOT_TSV.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "id",
        "book",
        "page",
        "qip",
        "offset",
        "target_q",
        "sub_score",
        "crop_file",
        "hd_pre",
        "db_text_preview",
        "ocr_text_preview",
        "verdict",
    ]
    with PILOT_TSV.open("w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for m in samp:
            nbook = norm_book(m["book"])
            ocr_t = ocr_idx.get((nbook, m["page"]), {}).get(m["crop_file"], "")
            row = [
                m["id"],
                m["book"][:50].replace("\t", " "),
                str(m["page"]),
                str(m["qip"]),
                str(m["offset"]),
                str(m["target_q"]),
                str(m["sub_score"]),
                m["crop_file"],
                str(m["hd_pre"]) if m["hd_pre"] else "NULL",
                (m["db_text"] or "")[:120].replace("\t", " ").replace("\n", " "),
                ocr_t[:120].replace("\t", " ").replace("\n", " "),
                "",
            ]
            f.write("\t".join(row) + "\n")
    print(f"\n[PILOT] TSV: {PILOT_TSV} ({len(samp)} satır)")


def apply_matches(engine, matches, batch_size=1000):
    from sqlalchemy import text

    UPDATE_SQL = """
        UPDATE question_bank
        SET question_image_url = :url,
            pipeline_metadata = jsonb_set(
                COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
                '{tier_h_v2_match}',
                CAST(:flag_json AS jsonb),
                TRUE
            )::json
        WHERE id = :id AND question_image_url IS NULL
    """
    print(f"\n[6/6] DB UPDATE (batch={batch_size})...")
    updated = 0
    failed = 0
    skipped = 0
    with engine.begin() as conn:
        for i in range(0, len(matches), batch_size):
            batch = matches[i : i + batch_size]
            for m in batch:
                url = f"{URL_PREFIX}/{m['book_dir']}/{m['crop_file']}"
                flag = {
                    "tier": "H_v2",
                    "crop_file": m["crop_file"],
                    "qip": m["qip"],
                    "offset": m["offset"],
                    "target_q": m["target_q"],
                    "sub_score": m["sub_score"],
                    "hd_pre": m["hd_pre"],
                    "audit_date": AUDIT_DATE,
                }
                try:
                    r = conn.execute(
                        text(UPDATE_SQL),
                        {"id": m["id"], "url": url, "flag_json": json.dumps(flag)},
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
                f"  [{pct:5.1f}%] {done:,}/{len(matches):,} ({updated} updated, {failed} failed)"
            )
    print(f"\nUpdated: {updated}, Skipped: {skipped}, Failed: {failed}")
    return updated


def main():
    parser = argparse.ArgumentParser(description="Tier H v2 offset-aware")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--pilot", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    engine = get_engine()
    cache, cache_lower = build_disk_cache()
    ocr_idx = build_ocr_index()
    rows = fetch_candidates(engine)
    page_offset = compute_page_offsets(rows)
    matches, _ = match_all(
        rows, cache, cache_lower, page_offset, ocr_idx, validate_text=args.pilot
    )
    if args.pilot:
        write_pilot_tsv(matches, ocr_idx)
        return
    if args.dry_run:
        print(f"\n[DRY-RUN] {len(matches):,} match")
        return
    if not matches:
        print("\nMatch yok")
        return
    print(f"\n[APPLY] {len(matches):,} satır...")
    apply_matches(engine, matches)
    print("\nTamamlandi.")


if __name__ == "__main__":
    main()
