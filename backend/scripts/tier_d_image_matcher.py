#!/usr/bin/env python3
"""
Faz 1.2 — Tier D image matcher (page_match_other_q, ~25K satir).

Tier C exact_match'i kacirdigi satirlar (image=null, has_diagram=true, valid q_no)
icin ocr_crops/results.jsonl text similarity ile crop_file eslestirme.

Strateji (2 kademe, 0.70 threshold):
  D1 (key direct): ocr_crops'ta (book, page, q_no) varsa
                   text similarity (Jaccard, NFC normalize) >= 0.70 → match
  D2 (page fallback): D1 fail veya threshold alti → ayni (book, page) icindeki
                      tum crop'lar arasinda en yuksek similarity (best match)
                      yine >= 0.70 → match

Modlar:
  --pilot       100 random satir, TSV rapor, UPDATE YOK
  --dry-run     Tum satirlar, stats + sample, UPDATE YOK
  --apply       Tum satirlar, DB UPDATE

Cikti:
  --pilot   → backend/_pilots/20260515_tier_d_pilot_RESULT.tsv (manuel onay icin)
  --apply   → question_bank.question_image_url populate + pipeline_metadata.tier_d_match
"""

from __future__ import annotations

import argparse
import json
import os
import random
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from time import time

# =============================================================================
# Paths
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
D_DATASET = PROJECT_ROOT / "d-dataset"
OCR_CROPS_PATH = D_DATASET / "output" / "ocr_crops" / "results.jsonl"
CROP_BASE = D_DATASET / "output" / "crops"
PILOT_TSV = (
    Path(__file__).parent.parent / "_pilots" / "20260515_tier_d_pilot_RESULT.tsv"
)

URL_PREFIX = "/static/crops"
SIM_THRESHOLD = 0.70
PILOT_N = 100
PILOT_SEED = 42
AUDIT_DATE = "2026-05-15"


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
    """NFC + underscore→space + strip."""
    if not name:
        return ""
    return unicodedata.normalize("NFC", name.replace("_", " ").strip())


def safe_int(value) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def text_similarity(text_a: str, text_b: str) -> float:
    """Word overlap Jaccard, NFC normalize, lowercase."""
    if not text_a or not text_b:
        return 0.0
    a = unicodedata.normalize("NFC", text_a).lower().split()
    b = unicodedata.normalize("NFC", text_b).lower().split()
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def crop_url_from_filename(crop_file: str, book_name_db: str) -> str:
    """Build /static/crops/<dir>/<file> URL.

    Dir from filename prefix before _pNNNN_qNN.png pattern.
    """
    import re

    m = re.match(r"^(.+)_p\d{4}_q\d{2}.*\.png$", crop_file)
    dir_name = m.group(1) if m else crop_file.rsplit("_", 1)[0]
    return f"{URL_PREFIX}/{dir_name}/{crop_file}"


def parse_crop_q_no(crop_file: str) -> int | None:
    """Extract q_no from filename like '..._p0021_q05.png' or '_q05 (1).png'."""
    import re

    m = re.search(r"_p\d{4}_q(\d{1,3})", crop_file)
    return int(m.group(1)) if m else None


# =============================================================================
# Index builders
# =============================================================================


def build_ocr_index() -> dict[tuple, list[dict]]:
    """ocr_crops → {(norm_book, page): [{soru_no, crop_file, text}, ...]}.

    Liste tutulur (ayni page'de birden fazla crop) D2 fallback icin.
    """
    print("[1/5] ocr_crops index olusturuluyor", end=" ... ", flush=True)
    t0 = time()
    if not OCR_CROPS_PATH.exists():
        raise FileNotFoundError(OCR_CROPS_PATH)

    idx: dict[tuple, list[dict]] = defaultdict(list)
    errors = 0
    n = 0

    with OCR_CROPS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                errors += 1
                continue
            n += 1
            book = norm_book(d.get("book", ""))
            page = safe_int(d.get("page_num"))
            soru_no = safe_int(d.get("soru_no"))
            crop_file = d.get("crop_file", "")
            text = d.get("soru_metni", "") or ""
            if not book or page is None or not crop_file:
                continue
            idx[(book, page)].append(
                {
                    "soru_no": soru_no,
                    "crop_file": crop_file,
                    "text": text,
                }
            )

    print(
        f"OK ({time() - t0:.1f}s, {n:,} entries, {len(idx):,} page-key, {errors} parse-err)"
    )
    return idx


def fetch_candidates(engine) -> list[tuple]:
    """Tier D adayi satirlar: has_diagram + image_url IS NULL + valid q_no."""
    from sqlalchemy import text

    SQL = """
        SELECT id, source_book, source_page,
               (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no')::int AS q_no,
               question_text
        FROM question_bank
        WHERE is_active = TRUE
          AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram') = 'true'
          AND question_image_url IS NULL
          AND source_book IS NOT NULL
          AND source_page IS NOT NULL
          AND pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' ~ '^[0-9]+$'
          AND question_text IS NOT NULL
          AND LENGTH(question_text) > 20
    """
    print("[2/5] DB Tier D adaylari fetch", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as c:
        rows = list(c.execute(text(SQL)))
    print(f"OK ({time() - t0:.1f}s, {len(rows):,} satir)")
    return rows


# =============================================================================
# Match logic
# =============================================================================


def match_row(
    qb_id: str,
    book: str,
    page: int,
    db_q_no: int,
    db_text: str,
    ocr_index: dict[tuple, list[dict]],
) -> dict | None:
    """D1 (key direct) → D2 (page fallback). Threshold-passing match doner.

    Returns:
        {tier, crop_file, crop_q_no, similarity, ocr_soru_no, ocr_text}
        veya None (match yok / threshold alti).
    """
    nbook = norm_book(book)
    key = (nbook, page)
    candidates = ocr_index.get(key, [])
    if not candidates:
        return None

    # D1: ocr_crops'ta soru_no == db_q_no varsa
    for entry in candidates:
        if entry["soru_no"] == db_q_no:
            sim = text_similarity(db_text, entry["text"])
            if sim >= SIM_THRESHOLD:
                return {
                    "tier": "D1",
                    "crop_file": entry["crop_file"],
                    "crop_q_no": parse_crop_q_no(entry["crop_file"]),
                    "similarity": round(sim, 3),
                    "ocr_soru_no": entry["soru_no"],
                    "ocr_text": entry["text"],
                }

    # D2: page'deki tum crop'larda en yuksek similarity
    best = None
    best_sim = 0.0
    for entry in candidates:
        sim = text_similarity(db_text, entry["text"])
        if sim > best_sim:
            best_sim = sim
            best = entry
    if best and best_sim >= SIM_THRESHOLD:
        return {
            "tier": "D2",
            "crop_file": best["crop_file"],
            "crop_q_no": parse_crop_q_no(best["crop_file"]),
            "similarity": round(best_sim, 3),
            "ocr_soru_no": best["soru_no"],
            "ocr_text": best["text"],
        }
    return None


def match_all(
    rows: list[tuple], ocr_index: dict[tuple, list[dict]]
) -> tuple[list[dict], Counter]:
    print("[3/5] Tier D matching", end=" ... ", flush=True)
    t0 = time()
    matches: list[dict] = []
    stats: Counter = Counter()

    for qb_id, book, page, q_no, qtext in rows:
        stats["total"] += 1
        m = match_row(qb_id, book, page, q_no, qtext, ocr_index)
        if m is None:
            stats["no_match"] += 1
            continue
        stats[m["tier"]] += 1
        if m["crop_q_no"] != q_no:
            stats[f"{m['tier']}_q_shifted"] += 1
        matches.append(
            {
                "id": qb_id,
                "book": book,
                "page": page,
                "db_q_no": q_no,
                "db_text": qtext,
                **m,
            }
        )

    print(f"OK ({time() - t0:.1f}s)")
    print()
    print("  Tier D istatistikleri:")
    total = stats["total"]
    keys = ["total", "D1", "D2", "D1_q_shifted", "D2_q_shifted", "no_match"]
    for k in keys:
        n = stats[k]
        pct = 100.0 * n / total if total else 0
        print(f"    {k:20s} {n:>7,} ({pct:5.2f}%)")
    return matches, stats


# =============================================================================
# Pilot TSV reporting
# =============================================================================


def write_pilot_tsv(matches: list[dict], path: Path = PILOT_TSV) -> None:
    """100 random satir TSV — manuel pixel-onay icin."""
    random.seed(PILOT_SEED)
    sample = random.sample(matches, min(PILOT_N, len(matches)))

    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "id",
        "book",
        "page",
        "db_q_no",
        "ocr_soru_no",
        "crop_q_no",
        "tier",
        "similarity",
        "crop_file",
        "db_text_preview",
        "ocr_text_preview",
        "verdict",
    ]
    with path.open("w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for m in sample:
            row = [
                m["id"],
                m["book"][:50].replace("\t", " "),
                str(m["page"]),
                str(m["db_q_no"]),
                str(m["ocr_soru_no"]) if m["ocr_soru_no"] is not None else "",
                str(m["crop_q_no"]) if m["crop_q_no"] is not None else "",
                m["tier"],
                str(m["similarity"]),
                m["crop_file"],
                (m["db_text"] or "")[:100].replace("\t", " ").replace("\n", " "),
                (m["ocr_text"] or "")[:100].replace("\t", " ").replace("\n", " "),
                "",  # verdict: ok / wrong / unclear
            ]
            f.write("\t".join(row) + "\n")
    print(f"\n[PILOT] TSV yazildi: {path}")
    print(
        f"        {len(sample)} satir, verdict kolonu bos. Manuel doldur ve geri don."
    )


# =============================================================================
# Apply (DB update)
# =============================================================================


def apply_matches(engine, matches: list[dict], batch_size: int = 500) -> int:
    """question_image_url populate + pipeline_metadata.tier_d_match flag."""
    from sqlalchemy import text

    UPDATE_SQL = """
        UPDATE question_bank
        SET question_image_url = :url,
            pipeline_metadata = jsonb_set(
                COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
                '{tier_d_match}',
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
                url = crop_url_from_filename(m["crop_file"], m["book"])
                flag = {
                    "tier": m["tier"],
                    "similarity": m["similarity"],
                    "ocr_soru_no": m["ocr_soru_no"],
                    "crop_q_no": m["crop_q_no"],
                    "crop_file": m["crop_file"],
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
                        print(f"  [WARN] id={m['id'][:8]}: {e}")

            done = i + len(batch)
            pct = done / len(matches) * 100
            print(
                f"  [{pct:5.1f}%] {done:,}/{len(matches):,} "
                f"({updated:,} updated, {skipped:,} skipped, {failed:,} failed)"
            )

    # Verify
    with engine.connect() as conn:
        n_url = conn.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE pipeline_metadata::jsonb -> 'tier_d_match' IS NOT NULL"
            )
        ).scalar()
    print()
    print(f"DB dogrulama: tier_d_match flag = {n_url:,}")
    print(f"Updated: {updated:,}, Skipped: {skipped:,}, Failed: {failed:,}")
    return updated


# =============================================================================
# Sample print
# =============================================================================


def print_sample(matches: list[dict], n: int = 6) -> None:
    if not matches:
        return
    random.seed(PILOT_SEED)
    sample = random.sample(matches, min(n, len(matches)))
    print(f"\n[4/5] Random sample ({n}):")
    print("-" * 100)
    for m in sample:
        print(
            f"  id={m['id'][:8]}.. {m['tier']} sim={m['similarity']:.3f} "
            f"db_q={m['db_q_no']} crop_q={m['crop_q_no']} "
            f"file={m['crop_file'][:60]}"
        )
    print("-" * 100)


# =============================================================================
# Entry point
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="Tier D image matcher (Faz 1.2)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--pilot", action="store_true", help="100 random row TSV")
    g.add_argument("--dry-run", action="store_true", help="Full stats, no UPDATE")
    g.add_argument("--apply", action="store_true", help="UPDATE DB")
    args = parser.parse_args()

    engine = get_engine()
    ocr_index = build_ocr_index()
    rows = fetch_candidates(engine)
    matches, _ = match_all(rows, ocr_index)
    print_sample(matches)

    if args.pilot:
        write_pilot_tsv(matches)
        return

    if args.dry_run:
        print(f"\n[DRY-RUN] {len(matches):,} match candidate. UPDATE atilmadi.")
        return

    if not matches:
        print("\nMatch yok, cikis.")
        return

    print(f"\n[APPLY] {len(matches):,} satira tier_d_match + image_url yaziliyor...")
    apply_matches(engine, matches)
    print("\nTamamlandi.")


if __name__ == "__main__":
    main()
