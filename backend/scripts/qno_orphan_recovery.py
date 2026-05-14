#!/usr/bin/env python3
"""
Faz 1.7 — q_no=invalid orphan recovery (~7,510 satir).

audit_v2 invalid_q_no kategorisi:
  - 5,793 trailing-dot: "1.", "2.", ... (Tier C/D regex reddetti)
  - 1,717 other: OCR yanlış başlık yakalamış ("AROMAT MODELİ",
    "Örnek 2", "Soru 5", "KILAVUZ SORU" vb.) — q_no yok

Strateji:
  E1 (trailing-dot, 5793): strip dot -> Tier C/D logic
       a) exact_match: disk'te `_pNNNN_qNN.png` var
       b) text similarity (D1+D2 logic, threshold 0.70)
  E2 (no q_no, 1717): page-level best similarity
       Tek crop varsa direkt eşle, çoklu ise en yüksek sim
       Threshold 0.60 (q_no info yok, daha gevşek)

Felsefe (Faz 1.2/1.4/1.9 ile uyumlu): pipeline_metadata.tier_e_match flag
+ question_image_url populate. Defansif: sim<threshold ise UPDATE etmez.

Bilinen risk:
  - "Other" satırlar (Örnek 2 etc.) gerçek soru numarası olmayabilir
    (sayfa içi tek "örnek" soru). Page-level match emin değil.
  - Threshold 0.60 gevşek -> false-positive riski yüksek
  - Trailing-dot satırlar high-confidence

Kullanim:
    cd backend
    python scripts/qno_orphan_recovery.py --dry-run
    python scripts/qno_orphan_recovery.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from time import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AUDIT_DATE = "2026-05-15"
SIM_THRESHOLD_E1 = 0.70  # Tier D baseline
SIM_THRESHOLD_E2 = 0.70  # Tier D pilot %96 accuracy ile aynı (uniformity)

PROJECT_ROOT = Path(__file__).parent.parent.parent
D_DATASET = PROJECT_ROOT / "d-dataset"
OCR_CROPS_PATH = D_DATASET / "output" / "ocr_crops" / "results.jsonl"
CROPS_ROOT = D_DATASET / "output" / "crops"

URL_PREFIX = "/static/crops"


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
        "DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2"
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")
    return create_engine(db_url)


# =============================================================================
# Helpers
# =============================================================================


def norm_book(name: str) -> str:
    if not name:
        return ""
    return unicodedata.normalize("NFC", name.replace("_", " ").strip())


def parse_q_no(raw: str | None) -> int | None:
    """Strip trailing dot/whitespace, return int or None."""
    if not raw:
        return None
    m = re.match(r"^\s*([0-9]+)\.?\s*$", raw)
    return int(m.group(1)) if m else None


def text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    sa = set(unicodedata.normalize("NFC", a).lower().split())
    sb = set(unicodedata.normalize("NFC", b).lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def parse_crop_q_no(crop_file: str) -> int | None:
    m = re.search(r"_p\d{4}_q(\d{1,3})", crop_file)
    return int(m.group(1)) if m else None


def crop_url(crop_file: str, book_dir_name: str) -> str:
    return f"{URL_PREFIX}/{book_dir_name}/{crop_file}"


# =============================================================================
# Index builders
# =============================================================================


def build_disk_index() -> dict[str, set[str]]:
    """{book_dir_name (lowercase): {filenames}}."""
    print("[1/5] Disk crop index", end=" ... ", flush=True)
    t0 = time()
    idx: dict[str, set[str]] = {}
    for p in CROPS_ROOT.iterdir():
        if not p.is_dir():
            continue
        try:
            idx[p.name] = {f.name for f in p.iterdir() if f.is_file()}
        except (PermissionError, OSError):
            idx[p.name] = set()
    print(f"OK ({time() - t0:.1f}s, {len(idx)} kitap)")
    return idx


def build_ocr_index() -> dict[tuple, list[dict]]:
    """{(book_normalized, page): [{soru_no, crop_file, text}]}."""
    print("[2/5] ocr_crops index", end=" ... ", flush=True)
    t0 = time()
    idx: dict[tuple, list[dict]] = defaultdict(list)
    with OCR_CROPS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            book = norm_book(d.get("book", ""))
            try:
                page = int(d.get("page_num"))
            except (TypeError, ValueError):
                continue
            crop = d.get("crop_file", "")
            if not book or not crop:
                continue
            soru_no = d.get("soru_no")
            try:
                soru_no = int(soru_no)
            except (TypeError, ValueError):
                soru_no = None
            idx[(book, page)].append(
                {
                    "soru_no": soru_no,
                    "crop_file": crop,
                    "text": d.get("soru_metni", "") or "",
                }
            )
    print(f"OK ({time() - t0:.1f}s, {len(idx):,} page-key)")
    return idx


def fetch_orphan_rows(engine) -> list[tuple]:
    from sqlalchemy import text

    SQL = """
        SELECT id::text, source_book, source_page,
               pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' AS q_no_raw,
               question_text
        FROM question_bank
        WHERE is_active = TRUE
          AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') = 'true'
          AND question_image_url IS NULL
          AND source_book IS NOT NULL
          AND source_page IS NOT NULL
          AND pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' !~ '^[0-9]+$'
          AND question_text IS NOT NULL
          AND LENGTH(question_text) > 20
    """
    print("[3/5] DB orphan satır fetch", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as c:
        rows = list(c.execute(text(SQL)))
    print(f"OK ({time() - t0:.1f}s, {len(rows):,} satir)")
    return rows


# =============================================================================
# Match logic
# =============================================================================


def find_book_dir(book_db: str, disk_idx: dict[str, set[str]]) -> str | None:
    """DB book name → disk dir name (whitespace -> underscore)."""
    cand = book_db.replace(" ", "_")
    if cand in disk_idx:
        return cand
    # Lowercase fallback
    for k in disk_idx:
        if k.lower() == cand.lower():
            return k
    return None


def match_row(
    qid: str,
    book: str,
    page: int,
    q_no_raw: str | None,
    db_text: str,
    disk_idx: dict[str, set[str]],
    ocr_idx: dict[tuple, list[dict]],
) -> dict | None:
    """E1 trailing-dot path or E2 no-q_no path."""
    book_dir = find_book_dir(book, disk_idx)
    if book_dir is None:
        return None

    parsed_q_no = parse_q_no(q_no_raw)
    nbook = norm_book(book)
    candidates = ocr_idx.get((nbook, page), [])

    # E1a: exact disk match
    if parsed_q_no is not None:
        expected_suffix = f"_p{page:04d}_q{parsed_q_no:02d}.png"
        files = disk_idx.get(book_dir, set())
        exact = [f for f in files if f.endswith(expected_suffix)]
        if exact:
            crop_file = exact[0]
            return {
                "tier": "E1a",
                "crop_file": crop_file,
                "crop_q_no": parsed_q_no,
                "parsed_q_no": parsed_q_no,
                "similarity": None,
                "url": crop_url(crop_file, book_dir),
            }

    # E1b: q_no direct + similarity
    if parsed_q_no is not None and candidates:
        for entry in candidates:
            if entry["soru_no"] == parsed_q_no:
                sim = text_similarity(db_text, entry["text"])
                if sim >= SIM_THRESHOLD_E1:
                    return {
                        "tier": "E1b",
                        "crop_file": entry["crop_file"],
                        "crop_q_no": parse_crop_q_no(entry["crop_file"]),
                        "parsed_q_no": parsed_q_no,
                        "similarity": round(sim, 3),
                        "url": crop_url(entry["crop_file"], book_dir),
                    }
        # E1c: page best similarity (D2 logic, q_no parsed)
        best = None
        best_sim = 0.0
        for entry in candidates:
            sim = text_similarity(db_text, entry["text"])
            if sim > best_sim:
                best_sim = sim
                best = entry
        if best and best_sim >= SIM_THRESHOLD_E1:
            return {
                "tier": "E1c",
                "crop_file": best["crop_file"],
                "crop_q_no": parse_crop_q_no(best["crop_file"]),
                "parsed_q_no": parsed_q_no,
                "similarity": round(best_sim, 3),
                "url": crop_url(best["crop_file"], book_dir),
            }

    # E2: no q_no — page level best (gevşek threshold)
    if candidates:
        best = None
        best_sim = 0.0
        for entry in candidates:
            sim = text_similarity(db_text, entry["text"])
            if sim > best_sim:
                best_sim = sim
                best = entry
        if best and best_sim >= SIM_THRESHOLD_E2:
            return {
                "tier": "E2",
                "crop_file": best["crop_file"],
                "crop_q_no": parse_crop_q_no(best["crop_file"]),
                "parsed_q_no": None,
                "similarity": round(best_sim, 3),
                "url": crop_url(best["crop_file"], book_dir),
            }

    return None


def match_all(rows, disk_idx, ocr_idx) -> tuple[list[dict], Counter]:
    print("[4/5] Match", end=" ... ", flush=True)
    t0 = time()
    matches = []
    stats = Counter()
    for qid, book, page, q_no_raw, qtext in rows:
        stats["total"] += 1
        m = match_row(qid, book, page, q_no_raw, qtext, disk_idx, ocr_idx)
        if m is None:
            stats["no_match"] += 1
            continue
        stats[m["tier"]] += 1
        matches.append(
            {
                "id": qid,
                "book": book,
                "page": page,
                "q_no_raw": q_no_raw,
                **m,
            }
        )
    print(f"OK ({time() - t0:.1f}s)")
    print()
    print("  İstatistik:")
    total = stats["total"]
    for k in ["total", "E1a", "E1b", "E1c", "E2", "no_match"]:
        n = stats[k]
        pct = 100.0 * n / total if total else 0
        print(f"    {k:10s} {n:>6,} ({pct:5.2f}%)")
    return matches, stats


# =============================================================================
# Apply
# =============================================================================


def apply_matches(engine, matches, batch_size=500) -> int:
    from sqlalchemy import text

    UPDATE_SQL = """
        UPDATE question_bank
        SET question_image_url = :url,
            pipeline_metadata = jsonb_set(
                COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
                '{tier_e_match}',
                CAST(:flag_json AS jsonb),
                TRUE
            )::json
        WHERE id = :id
          AND question_image_url IS NULL
    """
    print(f"\n[5/5] DB update (batch={batch_size}) ...")
    updated = 0
    failed = 0
    skipped = 0
    with engine.begin() as conn:
        for i in range(0, len(matches), batch_size):
            batch = matches[i : i + batch_size]
            for m in batch:
                flag = {
                    "tier": m["tier"],
                    "crop_file": m["crop_file"],
                    "parsed_q_no": m["parsed_q_no"],
                    "crop_q_no": m["crop_q_no"],
                    "similarity": m["similarity"],
                    "q_no_raw": m["q_no_raw"],
                    "audit_date": AUDIT_DATE,
                }
                try:
                    r = conn.execute(
                        text(UPDATE_SQL),
                        {
                            "id": m["id"],
                            "url": m["url"],
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
                        print(f"  [WARN] id={m['id'][:8]}: {e}")
            done = i + len(batch)
            pct = done / len(matches) * 100
            print(
                f"  [{pct:5.1f}%] {done:,}/{len(matches):,} "
                f"({updated:,} updated, {skipped:,} skipped, {failed:,} failed)"
            )
    with engine.connect() as conn:
        n_flag = conn.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE pipeline_metadata::jsonb -> 'tier_e_match' IS NOT NULL"
            )
        ).scalar()
    print(f"\nDB dogrulama: tier_e_match flag = {n_flag:,}")
    return updated


# =============================================================================
# Sample
# =============================================================================


def print_sample(matches: list[dict], n: int = 10) -> None:
    if not matches:
        return
    import random

    random.seed(42)
    samp = random.sample(matches, min(n, len(matches)))
    print()
    print(f"Sample ({n}):")
    print("-" * 100)
    for m in samp:
        sim = m["similarity"] if m["similarity"] is not None else "n/a"
        raw = m["q_no_raw"].encode("ascii", "replace").decode("ascii")[:25]
        cf = m["crop_file"].encode("ascii", "replace").decode("ascii")
        print(
            f"  id={m['id'][:8]} {m['tier']:4s} q_no_raw={raw!r} -> "
            f"parsed={m['parsed_q_no']} crop_q={m['crop_q_no']} sim={sim} file={cf[:60]}"
        )
    print("-" * 100)


# =============================================================================
# Entry point
# =============================================================================


def main():
    parser = argparse.ArgumentParser(description="q_no orphan recovery (Faz 1.7)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    engine = get_engine()
    disk_idx = build_disk_index()
    ocr_idx = build_ocr_index()
    rows = fetch_orphan_rows(engine)
    matches, _ = match_all(rows, disk_idx, ocr_idx)
    print_sample(matches)

    if args.dry_run:
        print(f"\n[DRY-RUN] {len(matches):,} match. UPDATE atilmadi.")
        return
    if not matches:
        print("\nMatch yok, cikis.")
        return
    print(f"\n[APPLY] {len(matches):,} satir...")
    apply_matches(engine, matches)
    print("\nTamamlandi.")


if __name__ == "__main__":
    main()
