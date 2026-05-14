#!/usr/bin/env python3
"""
Faz 1.5+ — Tier F recovery (asymmetric threshold).

Kök neden bulgusu (Session 158 audit):
  14,672 satır D_match_failed (%99 of missing) → disk+OCR VAR ama
  Tier C/D/E threshold 0.70 reddetti.
  Sample 50'de: sim 0.50-0.70 bucket %64 (key match var, text overlap zayıf).

Strateji (asymmetric threshold):
  F1 (key match): ocr_crops'ta (book, page, q_no) AYNEN var → sim>=0.50
       Mantık: OCR pipeline'ın "bu crop bu soru" demesi guçlu sinyal
       Text bonus düşük olabilir (CAP/Aromat/Bilgi Sarmal OCR kalitesi düşük)
  F2 (REDDEDİLDİ): pure text similarity fallback risk yüksek → atla

Bu sadece D1-style logic, D2 yok. Tier D'nin yakaladığı D2 (269) zaten
ayrı, dokunulmaz.

Risk:
  - 0.50-0.70 bucket'da false-positive oranı pilot ile ölçülecek
  - Tier D pilot %96 (sim>=0.70). Bu daha gevşek, accuracy düşebilir
  - Defansif: pipeline_metadata.tier_f_match flag + similarity → judge
    sonradan düşük-sim'leri öncelikli inceler

Kullanim:
    cd backend
    python scripts/tier_f_recovery.py --pilot
    python scripts/tier_f_recovery.py --dry-run
    python scripts/tier_f_recovery.py --apply
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
SIM_THRESHOLD = 0.50  # F1 asymmetric — key match var, gevşek threshold
PILOT_N = 100
PILOT_SEED = 42

PROJECT_ROOT = Path(__file__).parent.parent.parent
D_DATASET = PROJECT_ROOT / "d-dataset"
OCR_PATH = D_DATASET / "output" / "ocr_crops" / "results.jsonl"
PILOT_TSV = (
    Path(__file__).parent.parent / "_pilots" / "20260515_tier_f_pilot_RESULT.tsv"
)
URL_PREFIX = "/static/crops"


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


def norm_book(name: str) -> str:
    if not name:
        return ""
    return unicodedata.normalize("NFC", name.replace("_", " ").strip())


def text_sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    sa = set(unicodedata.normalize("NFC", a).lower().split())
    sb = set(unicodedata.normalize("NFC", b).lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def parse_q_no_raw(raw: str | None) -> int | None:
    if not raw:
        return None
    m = re.match(r"^\s*([0-9]+)\.?\s*$", raw)
    return int(m.group(1)) if m else None


def parse_crop_q_no(crop_file: str) -> int | None:
    m = re.search(r"_p\d{4}_q(\d{1,3})", crop_file)
    return int(m.group(1)) if m else None


def build_ocr_index():
    print("[1/4] ocr_crops index", end=" ... ", flush=True)
    t0 = time()
    idx: dict[tuple, list[dict]] = defaultdict(list)
    with OCR_PATH.open(encoding="utf-8") as f:
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
            if not book:
                continue
            sn = d.get("soru_no")
            try:
                sn = int(sn)
            except (TypeError, ValueError):
                sn = None
            idx[(book, page)].append(
                {
                    "soru_no": sn,
                    "crop_file": d.get("crop_file", ""),
                    "text": d.get("soru_metni", "") or "",
                }
            )
    print(f"OK ({time() - t0:.1f}s, {len(idx):,} page-key)")
    return idx


def fetch_missing_rows(engine):
    from sqlalchemy import text

    SQL = """
        SELECT id::text, source_book, source_page,
               pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' AS q_no_raw,
               question_text
        FROM question_bank
        WHERE is_active=TRUE
          AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') = 'true'
          AND question_image_url IS NULL
          AND source_book IS NOT NULL
          AND source_page IS NOT NULL
          AND question_text IS NOT NULL
          AND LENGTH(question_text) > 20
    """
    print("[2/4] DB missing rows fetch", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as c:
        rows = list(c.execute(text(SQL)))
    print(f"OK ({time() - t0:.1f}s, {len(rows):,} satir)")
    return rows


def match_all(rows, ocr_idx):
    """F1: key match var → sim>=0.50."""
    print("[3/4] F1 key-match (sim>=0.50)", end=" ... ", flush=True)
    t0 = time()
    matches = []
    stats = Counter()
    for qid, book, page, qno_raw, qtext in rows:
        stats["total"] += 1
        qno = parse_q_no_raw(qno_raw)
        if qno is None:
            stats["no_qno"] += 1
            continue
        nbook = norm_book(book)
        cands = ocr_idx.get((nbook, page), [])
        if not cands:
            stats["no_page_ocr"] += 1
            continue
        # Key match: q_no eşleşmesi VAR mı?
        key_entry = None
        for e in cands:
            if e["soru_no"] == qno:
                key_entry = e
                break
        if key_entry is None:
            stats["no_key_match"] += 1
            continue
        sim = text_sim(qtext, key_entry["text"])
        if sim < SIM_THRESHOLD:
            stats[f"sim_below_{SIM_THRESHOLD}"] += 1
            continue
        stats["matched"] += 1
        if sim >= 0.70:
            stats["sim_high_70+"] += 1
        elif sim >= 0.60:
            stats["sim_mid_60_70"] += 1
        else:
            stats["sim_low_50_60"] += 1
        crop_file = key_entry["crop_file"]
        book_dir = book.replace(" ", "_")
        matches.append(
            {
                "id": qid,
                "book": book,
                "page": page,
                "db_q_no": qno,
                "db_text": qtext,
                "crop_file": crop_file,
                "crop_q_no": parse_crop_q_no(crop_file),
                "similarity": round(sim, 3),
                "ocr_text": key_entry["text"],
                "url": f"{URL_PREFIX}/{book_dir}/{crop_file}",
            }
        )
    print(f"OK ({time() - t0:.1f}s)")
    print()
    print("  İstatistik:")
    total = stats["total"]
    for k in [
        "total",
        "matched",
        "sim_high_70+",
        "sim_mid_60_70",
        "sim_low_50_60",
        f"sim_below_{SIM_THRESHOLD}",
        "no_key_match",
        "no_page_ocr",
        "no_qno",
    ]:
        n = stats[k]
        pct = 100.0 * n / total if total else 0
        print(f"    {k:25s} {n:>6,} ({pct:5.2f}%)")
    return matches, stats


def write_pilot_tsv(matches, path=PILOT_TSV):
    random.seed(PILOT_SEED)
    samp = random.sample(matches, min(PILOT_N, len(matches)))
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "id",
        "book",
        "page",
        "db_q_no",
        "crop_q_no",
        "similarity",
        "crop_file",
        "db_text_preview",
        "ocr_text_preview",
        "verdict",
    ]
    with path.open("w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for m in samp:
            row = [
                m["id"],
                m["book"][:50].replace("\t", " "),
                str(m["page"]),
                str(m["db_q_no"]),
                str(m["crop_q_no"]) if m["crop_q_no"] is not None else "",
                str(m["similarity"]),
                m["crop_file"],
                (m["db_text"] or "")[:100].replace("\t", " ").replace("\n", " "),
                (m["ocr_text"] or "")[:100].replace("\t", " ").replace("\n", " "),
                "",
            ]
            f.write("\t".join(row) + "\n")
    print(f"\n[PILOT] TSV: {path}")
    print(f"        {len(samp)} satir, verdict bos.")


def apply_matches(engine, matches, batch_size=500):
    from sqlalchemy import text

    UPDATE_SQL = """
        UPDATE question_bank
        SET question_image_url = :url,
            pipeline_metadata = jsonb_set(
                COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
                '{tier_f_match}',
                CAST(:flag_json AS jsonb),
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
                flag = {
                    "tier": "F1",
                    "crop_file": m["crop_file"],
                    "db_q_no": m["db_q_no"],
                    "crop_q_no": m["crop_q_no"],
                    "similarity": m["similarity"],
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
    parser = argparse.ArgumentParser(description="Tier F recovery (Faz 1.5+)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--pilot", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    engine = get_engine()
    ocr_idx = build_ocr_index()
    rows = fetch_missing_rows(engine)
    matches, _ = match_all(rows, ocr_idx)

    if args.pilot:
        write_pilot_tsv(matches)
        return
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
