#!/usr/bin/env python3
"""
Faz 1.10 Tier I Re-OCR — ThreadPool concurrent version (Session 160).

PURPOSE:
  Sequential script (`tier_i_reocr_apply.py`) per-call ~13s latency × 3,326
  satır = 11.7h ETA. Gemini Pro quota %0.4 kullanım = 95x boş kapasite.
  ThreadPool ile concurrent calls → 10x hızlanma (ETA ~1.15h).

QUALITY GUARANTEE:
  - Aynı substring overlap algoritması (substring_overlap)
  - Aynı HIGH threshold (substr >= 0.70 → apply, else skip)
  - Aynı DB UPDATE pattern (image_url + image_ocr_text + tier_i_reocr)
  - Aynı checkpoint format (resume backward compatible)
  - Aynı BACKUP TSV format (rollback için)

CONCURRENCY:
  - ThreadPoolExecutor(max_workers=N), default 10
  - File writes: threading.Lock
  - stats Counter: threading.Lock
  - checkpoint set: threading.Lock
  - engine.connect(): per-call (SA pool internal)
  - Gemini model: shared (SDK thread-safe per Google docs)

USAGE:
  # Önce mevcut sequential script'i durdur (PID 917):
  #   taskkill /F /PID 917  (Windows)
  # Sonra:
  python backend/scripts/tier_i_reocr_apply_threaded.py --apply --resume --workers 10

  # Smoke test:
  python backend/scripts/tier_i_reocr_apply_threaded.py --apply --workers 5 --limit 20
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Import sequential script's helpers (cerrahi reuse)
sys.path.insert(0, str(Path(__file__).parent))
from tier_i_reocr_apply import (  # noqa: E402
    AUDIT_DATE,
    MODEL_NAME,
    PROMPT_DIRECT,
    SUBSTR_APPLY,
    SUBSTR_HIGH,
    SUBSTR_LOW,
    build_image_url,
    call_gemini,
    fetch_db_data,
    filter_direct_bucket,
    get_engine,
    load_checkpoint,
    load_feasibility,
    resolve_crop_path,
    save_checkpoint,
    substring_overlap,
    update_db,
    write_backup_row,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"


class Locks:
    """Container for thread-safety locks."""

    stats = threading.Lock()
    checkpoint = threading.Lock()
    result_write = threading.Lock()
    backup_write = threading.Lock()
    print_log = threading.Lock()


def process_row(
    r: dict,
    model,
    db_data: dict,
    engine,
    args,
    backup_f,
    result_f,
    stats: Counter,
    processed: set,
) -> str:
    """
    Single-row worker. Returns terminal verdict string for stats.

    Thread-safety: stats, checkpoint, file writes use locks.
    """
    id_ = r["id"]
    book = r["book"]
    page = r["page"]
    q_no = r["q_no"]
    crop_file = r["crop_file"]

    # Crop path
    crop_path = resolve_crop_path(book, crop_file)
    if not crop_path or not crop_path.exists():
        with Locks.stats:
            stats["no_crop_file"] += 1
        with Locks.result_write:
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t0\tnone\tno_crop_file\t\t0\n"
            )
        return "no_crop_file"

    # DB row check
    db_row = db_data.get(id_)
    if not db_row:
        with Locks.stats:
            stats["no_db_row"] += 1
        return "no_db_row"
    db_text = db_row["text"] or ""

    # Gemini call (the long-latency op)
    try:
        result = call_gemini(model, crop_path, PROMPT_DIRECT)
    except Exception as e:
        with Locks.stats:
            stats["gemini_error"] += 1
        with Locks.result_write:
            result_f.write(f"{id_}\t{book}\t{page}\t{q_no}\t0\terror\terror\t\t0\n")
        with Locks.print_log:
            print(f"[ERR {id_[:8]}] {str(e)[:80]}", flush=True)
        return "gemini_error"

    if not result["ok"]:
        with Locks.stats:
            stats["json_fail"] += 1
        with Locks.result_write:
            result_f.write(f"{id_}\t{book}\t{page}\t{q_no}\t0\tjson_fail\tskip\t\t0\n")
        return "json_fail"

    data = result["data"]
    ocr_text = data.get("soru_metni", "") or ""
    substr_pct = substring_overlap(db_text, ocr_text)

    if substr_pct >= SUBSTR_HIGH:
        band = "high"
    elif substr_pct >= SUBSTR_LOW:
        band = "mid"
    else:
        band = "low"

    # HIGH-only mode
    if substr_pct < SUBSTR_APPLY:
        with Locks.stats:
            stats[f"{band}_skip"] += 1
        with Locks.result_write:
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t{substr_pct:.3f}\t{band}\tskip\t\t{len(ocr_text)}\n"
            )
        return f"{band}_skip"

    # BACKUP (pre-UPDATE state)
    with Locks.backup_write:
        write_backup_row(backup_f, id_, db_row)

    image_url = build_image_url(book, crop_file)
    metadata_delta = {
        "tier_i_reocr": {
            "date": AUDIT_DATE,
            "model": MODEL_NAME,
            "substr_pct": round(substr_pct, 3),
            "band": band,
            "ocr_method": "direct_crop",
            "prev_image_url": db_row.get("img_url"),
            "prev_ocr_text_len": len(db_row.get("ocr_text") or ""),
        }
    }

    # UPDATE
    try:
        update_db(
            engine, id_, image_url, ocr_text, metadata_delta, dry_run=args.dry_run
        )
        with Locks.stats:
            if args.dry_run:
                stats[f"would_apply_{band}"] += 1
            else:
                stats[f"applied_{band}"] += 1
        with Locks.result_write:
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t{substr_pct:.3f}\t{band}\t"
                f"{'apply' if not args.dry_run else 'dry'}\t{image_url}\t{len(ocr_text)}\n"
            )
        with Locks.checkpoint:
            if args.apply:
                processed.add(id_)
        return f"applied_{band}"
    except Exception as e:
        with Locks.stats:
            stats["db_update_error"] += 1
        with Locks.result_write:
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t{substr_pct:.3f}\t{band}\tdb_error\t\t{len(ocr_text)}\n"
            )
        with Locks.print_log:
            print(f"[DB-ERR {id_[:8]}] {str(e)[:80]}", flush=True)
        return "db_update_error"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()

    if not (args.apply or args.dry_run):
        print("[error] --apply veya --dry-run gerekli")
        return 1

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[error] GEMINI_API_KEY env var set değil")
        return 1

    mode = "apply" if args.apply else "dryrun"
    backup_path = PILOTS_DIR / f"20260516_tier_i_BACKUP_{mode}.tsv"
    result_tsv = PILOTS_DIR / f"20260516_tier_i_{mode}_RESULT.tsv"

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config={"temperature": 0.0, "max_output_tokens": 4096},
    )
    print(
        f"[gemini] {MODEL_NAME} initialized, mode={mode}, workers={args.workers}",
        flush=True,
    )

    rows = load_feasibility()
    direct_rows = filter_direct_bucket(rows)
    print(f"[feasibility] {len(direct_rows):,} direct bucket satır", flush=True)

    if args.dry_run and args.limit is None:
        args.limit = 100

    if args.limit:
        import random as _random

        rng = _random.Random(42)
        direct_rows = rng.sample(direct_rows, min(args.limit, len(direct_rows)))
        print(f"[limit] {args.limit} sample (seed=42)", flush=True)

    processed = load_checkpoint() if args.resume and args.apply else set()
    if processed:
        print(
            f"[resume] {len(processed):,} satır önceden işlenmiş, atlanıyor", flush=True
        )
        direct_rows = [r for r in direct_rows if r["id"] not in processed]

    ids = [r["id"] for r in direct_rows]
    print(f"[db] {len(ids):,} satır DB fetch...", flush=True)
    db_data = fetch_db_data(ids)
    print(f"[db] {len(db_data):,} satır alındı", flush=True)

    engine = get_engine()
    backup_f = open(backup_path, "a" if args.resume else "w", encoding="utf-8")
    if not args.resume:
        backup_f.write("id\tprev_image_url\tprev_image_ocr_text\n")
    result_f = open(result_tsv, "a" if args.resume else "w", encoding="utf-8")
    if not args.resume:
        result_f.write(
            "id\tbook\tpage\tq_no\tsubstr_pct\tband\taction\timage_url\tocr_text_len\n"
        )

    stats = Counter()
    start_ts = time.time()
    n_total = len(direct_rows)
    completed_count = 0

    print(
        f"[concurrent] Submitting {n_total} tasks to ThreadPool({args.workers})...",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                process_row,
                r,
                model,
                db_data,
                engine,
                args,
                backup_f,
                result_f,
                stats,
                processed,
            ): r["id"]
            for r in direct_rows
        }
        for fut in as_completed(futures):
            completed_count += 1
            try:
                fut.result()
            except Exception as e:
                with Locks.print_log:
                    print(f"[fut-err] {e}", flush=True)

            # Progress + periodic checkpoint
            if completed_count % 25 == 0:
                elapsed = time.time() - start_ts
                rate = completed_count / elapsed
                eta_s = (n_total - completed_count) / rate if rate > 0 else 0
                with Locks.print_log:
                    print(
                        f"[{completed_count:04d}/{n_total:04d}] "
                        f"rate={rate * 60:.1f}/min elapsed={elapsed / 60:.1f}m eta={eta_s / 60:.1f}m",
                        flush=True,
                    )
                with Locks.checkpoint:
                    if args.apply:
                        save_checkpoint(processed)

            # Periodic result flush
            if completed_count % 10 == 0:
                with Locks.result_write:
                    result_f.flush()

    # Final
    with Locks.checkpoint:
        if args.apply:
            save_checkpoint(processed)
    backup_f.close()
    result_f.close()

    total_elapsed = time.time() - start_ts
    print(f"\n[done] {completed_count} tamamlandı, {total_elapsed / 60:.1f} dakika")
    print("[stats]")
    for k, v in stats.most_common():
        print(f"  {k:25s} {v:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
