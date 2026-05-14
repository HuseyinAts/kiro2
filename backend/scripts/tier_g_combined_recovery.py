#!/usr/bin/env python3
"""
Faz 1.5++ Tier G — Kombineli derin recovery.

Session 158 derin analiz bulguları:
  - Current missing 7,376 (has_diagram=true, image_null)
  - Gizli scope: has_diagram=NULL + visual cue = 1,395 satır
  - sim_0.40-0.50 bucket: 1,961 (Tier F 0.50 threshold reddetti)
  - invalid_qno: 853 (page-level recovery adayı)
  - no_key_match: 1,367 (page-level recovery adayı)
  - no_qno: 977 (page-level recovery adayı)
  - H6 page offset REDDEDILDI: ±1,2 page'de match yok

Tier G stratejisi (4 kademe, kapsamlı filter):
  G0 (UPDATE): has_diagram=NULL & visual_cue → has_diagram=true
  G1 (key+gevşek): q_no var + key match + sim>=0.40 (Tier F'tan daha gevşek)
  G2 (page-no-key): q_no var + no key match + page best sim>=0.55
  G3 (page-no-qno): q_no NULL/invalid + page best sim>=0.55

Filter scope (genişletilmiş):
  has_diagram=true OR (has_diagram=NULL AND visual_cue)

Defansif: pipeline_metadata.tier_g_match flag, judge sinyal.

Bilinen risk (kabul edilen sınır):
  G1 sim 0.40-0.50 bucket false-positive %30-40 olabilir.
  G2/G3 no-key veya no-qno page-level riskli ama gevşek scope.

Kullanim:
    cd backend
    python scripts/tier_g_combined_recovery.py --pilot
    python scripts/tier_g_combined_recovery.py --apply
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
G1_THRESHOLD = 0.40  # key match var, gevşek
G2_THRESHOLD = 0.55  # no key match, orta
G3_THRESHOLD = 0.55  # no q_no, orta
PILOT_N = 100
PILOT_SEED = 42

PROJECT_ROOT = Path(__file__).parent.parent.parent
D_DATASET = PROJECT_ROOT / "d-dataset"
OCR_PATH = D_DATASET / "output" / "ocr_crops" / "results.jsonl"
PILOT_TSV = (
    Path(__file__).parent.parent / "_pilots" / "20260515_tier_g_pilot_RESULT.tsv"
)
URL_PREFIX = "/static/crops"

# Visual cue tight pattern (Session 158 H5 doğrulandı)
VISUAL_CUE_REGEX = (
    r"(şekildeki|şekilde verilen|yukarıdaki şekil|yandaki şekil|"
    r"aşağıdaki şekil|grafiği verilmiş|grafiğe göre|tabloda verilen|"
    r"tabloya göre|aşağıdaki tablo|ABC üçgen|ABCD (kare|paralelkenar|"
    r"dikdörtgen|yamuk|dörtgen)|koordinat düzlem|altıgenin|beşgenin|"
    r"şemada görül|harita üzerinde|verilen şekil)"
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


def norm_book(name: str) -> str:
    if not name:
        return ""
    return unicodedata.normalize("NFC", name.replace("_", " ").strip())


def parse_q_no(raw: str | None) -> int | None:
    if not raw:
        return None
    m = re.match(r"^\s*([0-9]+)\.?\s*$", raw)
    return int(m.group(1)) if m else None


def text_sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    sa = set(unicodedata.normalize("NFC", a).lower().split())
    sb = set(unicodedata.normalize("NFC", b).lower().split())
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0


def parse_crop_q_no(crop_file: str) -> int | None:
    m = re.search(r"_p\d{4}_q(\d{1,3})", crop_file)
    return int(m.group(1)) if m else None


def build_ocr_index():
    print("[1/5] ocr_crops index", end=" ... ", flush=True)
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


def fetch_candidates(engine):
    """Tier G scope: has_diagram=true OR (NULL + visual cue)."""
    from sqlalchemy import text

    SQL = """
        SELECT id::text, source_book, source_page,
               pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' AS q_no_raw,
               question_text,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') AS hd
        FROM question_bank
        WHERE is_active=TRUE
          AND question_image_url IS NULL
          AND source_book IS NOT NULL
          AND source_page IS NOT NULL
          AND question_text IS NOT NULL
          AND LENGTH(question_text) > 20
          AND (
            (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') = 'true'
            OR (
              (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') IS NULL
              AND question_text ~* :p
            )
          )
    """
    print("[2/5] Tier G aday fetch", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as c:
        rows = list(c.execute(text(SQL), {"p": VISUAL_CUE_REGEX}))
    print(f"OK ({time() - t0:.1f}s, {len(rows):,} satir)")
    return rows


def match_row(qid, book, page, qno_raw, qtext, hd, ocr_idx):
    """G1 (key+gevşek) → G2 (page no-key) → G3 (page no-qno)."""
    nbook = norm_book(book)
    cands = ocr_idx.get((nbook, page), [])
    if not cands:
        return None

    qno = parse_q_no(qno_raw)

    # G1: key match + sim>=0.40 (Tier F'tan gevşek)
    if qno is not None:
        for e in cands:
            if e["soru_no"] == qno:
                sim = text_sim(qtext, e["text"])
                if sim >= G1_THRESHOLD:
                    return {
                        "tier": "G1",
                        "crop_file": e["crop_file"],
                        "crop_q_no": parse_crop_q_no(e["crop_file"]),
                        "matched_q_no": qno,
                        "similarity": round(sim, 3),
                        "ocr_text": e["text"],
                    }
                # G2: key found but sim<0.40, fall through to page-best
                break

        # G2: q_no var ama key match yok / sim<0.40 → page best
        best = max(cands, key=lambda e: text_sim(qtext, e["text"]))
        best_sim = text_sim(qtext, best["text"])
        if best_sim >= G2_THRESHOLD:
            return {
                "tier": "G2",
                "crop_file": best["crop_file"],
                "crop_q_no": parse_crop_q_no(best["crop_file"]),
                "matched_q_no": None,
                "similarity": round(best_sim, 3),
                "ocr_text": best["text"],
            }
        return None

    # G3: q_no yok → page best
    best = max(cands, key=lambda e: text_sim(qtext, e["text"]))
    best_sim = text_sim(qtext, best["text"])
    if best_sim >= G3_THRESHOLD:
        return {
            "tier": "G3",
            "crop_file": best["crop_file"],
            "crop_q_no": parse_crop_q_no(best["crop_file"]),
            "matched_q_no": None,
            "similarity": round(best_sim, 3),
            "ocr_text": best["text"],
        }
    return None


def match_all(rows, ocr_idx):
    print("[3/5] Tier G matching", end=" ... ", flush=True)
    t0 = time()
    matches = []
    stats = Counter()
    for qid, book, page, qno_raw, qtext, hd in rows:
        stats["total"] += 1
        stats[f"scope_hd_{hd or 'NULL'}"] += 1
        m = match_row(qid, book, page, qno_raw, qtext, hd, ocr_idx)
        if m is None:
            stats["no_match"] += 1
            continue
        stats[m["tier"]] += 1
        # Sim bucket
        s = m["similarity"]
        if s >= 0.70:
            stats["sim_high"] += 1
        elif s >= 0.55:
            stats["sim_mid"] += 1
        elif s >= 0.40:
            stats["sim_low"] += 1
        matches.append(
            {
                "id": qid,
                "book": book,
                "page": page,
                "q_no_raw": qno_raw,
                "db_text": qtext,
                "hd_pre": hd,
                **m,
            }
        )
    print(f"OK ({time() - t0:.1f}s)")
    print()
    print("  İstatistik:")
    total = stats["total"]
    keys = [
        "total",
        "scope_hd_true",
        "scope_hd_NULL",
        "G1",
        "G2",
        "G3",
        "sim_high",
        "sim_mid",
        "sim_low",
        "no_match",
    ]
    for k in keys:
        n = stats[k]
        pct = 100.0 * n / total if total else 0
        print(f"    {k:18s} {n:>6,} ({pct:5.2f}%)")
    return matches, stats


def write_pilot_tsv(matches, path=PILOT_TSV):
    import random

    random.seed(PILOT_SEED)
    samp = random.sample(matches, min(PILOT_N, len(matches)))
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "id",
        "book",
        "page",
        "q_no_raw",
        "tier",
        "similarity",
        "matched_q_no",
        "crop_q_no",
        "crop_file",
        "hd_pre",
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
                (m["q_no_raw"] or "NULL")[:20].replace("\t", " "),
                m["tier"],
                str(m["similarity"]),
                str(m["matched_q_no"]) if m["matched_q_no"] else "",
                str(m["crop_q_no"]) if m["crop_q_no"] else "",
                m["crop_file"],
                str(m["hd_pre"]) if m["hd_pre"] else "NULL",
                (m["db_text"] or "")[:100].replace("\t", " ").replace("\n", " "),
                (m["ocr_text"] or "")[:100].replace("\t", " ").replace("\n", " "),
                "",
            ]
            f.write("\t".join(row) + "\n")
    print(f"\n[PILOT] TSV: {path}")
    print(f"        {len(samp)} satir, verdict bos.")


def apply_matches(engine, matches, batch_size=500):
    from sqlalchemy import text

    # has_diagram=NULL → true update + image_url populate + tier_g_match flag
    UPDATE_SQL = """
        UPDATE question_bank
        SET question_image_url = :url,
            pipeline_metadata = jsonb_set(
                jsonb_set(
                    COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
                    '{tier_g_match}',
                    CAST(:flag_json AS jsonb),
                    TRUE
                ),
                '{ai_extras,has_diagram}',
                '"true"'::jsonb,
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
                book_dir = m["book"].replace(" ", "_")
                url = f"{URL_PREFIX}/{book_dir}/{m['crop_file']}"
                flag = {
                    "tier": m["tier"],
                    "crop_file": m["crop_file"],
                    "matched_q_no": m["matched_q_no"],
                    "crop_q_no": m["crop_q_no"],
                    "similarity": m["similarity"],
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
    parser = argparse.ArgumentParser(description="Tier G combined (Faz 1.5++)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--pilot", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    engine = get_engine()
    ocr_idx = build_ocr_index()
    rows = fetch_candidates(engine)
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
