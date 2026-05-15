#!/usr/bin/env python3
"""
Faz 5.8 Tier I — Geometri safety_blocked retry (Session 162).

ROOT CAUSE (Session 160 finding):
  Original Tier I apply'da 346 satır Gemini 2.5 Pro `response.text quick accessor`
  hatası verdi. 10/10 sample analizi: TÜM error'lar Geometri kitaplarından
  (Mikro Orijinal-Tyt Ayt-Geometri 2, Acil Geometrinin ilacı, vb.) — Gemini
  safety filter geometrik şekilleri sistematik bloke ediyor
  (`finish_reason != STOP`, `HARM_CATEGORY_DANGEROUS_CONTENT` trigger).

STRATEGY:
  - Input: original `20260516_tier_i_apply_RESULT.tsv` `action == "error"` satırları (346)
  - Gemini GenerativeModel `safety_settings={...: BLOCK_NONE}` ile init
  - Aynı substring overlap algoritması (SUBSTR_APPLY=0.70 HIGH-only)
  - Aynı DB UPDATE pattern + `safety_mode="block_none"` audit flag
  - Ayrı BACKUP TSV + checkpoint (rollback için)

SAFETY MITIGATION:
  - SADECE bu 346 error satır için tek kullanımlık
  - Çıktı substring overlap ≥0.70 olmadan DB'ye YAZILMAZ
  - pipeline_metadata.tier_i_reocr.safety_mode = "block_none" audit trail
  - Geometri içeriği matematiksel/soyut → istenmeyen üretim riski düşük

USAGE:
  # Pilot 20 sample (production retry öncesi smoke test):
  python backend/scripts/tier_i_geometri_retry.py --apply --limit 20 --workers 5

  # Production: kalan satırları işle:
  python backend/scripts/tier_i_geometri_retry.py --apply --resume --workers 10
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

# Helper reuse (cerrahi — kanıtlanmış prod script'lere DOKUNMA)
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
    load_feasibility,
    resolve_crop_path,
    substring_overlap,
    update_db,
    write_backup_row,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"
ORIG_RESULT_TSV = PILOTS_DIR / "20260516_tier_i_apply_RESULT.tsv"
CHECKPOINT_FILE = PILOTS_DIR / "checkpoint_tier_i_geometri.json"


class Locks:
    stats = threading.Lock()
    checkpoint = threading.Lock()
    result_write = threading.Lock()
    backup_write = threading.Lock()
    print_log = threading.Lock()


def load_error_ids() -> set[str]:
    """Original Tier I apply RESULT.tsv'den action='error' ID'lerini topla."""
    error_ids: set[str] = set()
    with open(ORIG_RESULT_TSV, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        action_idx = header.index("action")
        id_idx = header.index("id")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(action_idx, id_idx):
                continue
            if parts[action_idx] == "error":
                error_ids.add(parts[id_idx])
    return error_ids


def load_geometri_checkpoint() -> set[str]:
    import json

    if not CHECKPOINT_FILE.exists():
        return set()
    try:
        return set(
            json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))["processed_ids"]
        )
    except Exception:
        return set()


def save_geometri_checkpoint(processed: set[str]):
    import json
    from datetime import datetime

    CHECKPOINT_FILE.write_text(
        json.dumps(
            {"processed_ids": list(processed), "ts": datetime.now().isoformat()}
        ),
        encoding="utf-8",
    )


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
    """Single-row worker. Aynı pipeline, retry_pass=2 ve safety_mode=block_none flag."""

    id_ = r["id"]
    book = r["book"]
    page = r["page"]
    q_no = r["q_no"]
    crop_file = r["crop_file"]

    crop_path = resolve_crop_path(book, crop_file)
    if not crop_path or not crop_path.exists():
        with Locks.stats:
            stats["no_crop_file"] += 1
        with Locks.result_write:
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t0\tnone\tno_crop_file\t\t0\n"
            )
        return "no_crop_file"

    db_row = db_data.get(id_)
    if not db_row:
        with Locks.stats:
            stats["no_db_row"] += 1
        return "no_db_row"
    db_text = db_row["text"] or ""

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

    if substr_pct < SUBSTR_APPLY:
        with Locks.stats:
            stats[f"{band}_skip"] += 1
        with Locks.result_write:
            result_f.write(
                f"{id_}\t{book}\t{page}\t{q_no}\t{substr_pct:.3f}\t{band}\tskip\t\t{len(ocr_text)}\n"
            )
        return f"{band}_skip"

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
            "safety_mode": "block_none",
            "retry_pass": 2,
            "prev_image_url": db_row.get("img_url"),
            "prev_ocr_text_len": len(db_row.get("ocr_text") or ""),
        }
    }
    # `update_db` `pipeline_metadata` JSON merge'i `tier_i_reocr` key altında yapıyor;
    # mevcut audit trail'i overwrite ediyor (retry_pass=2 yeni iz). İstenmedik durumda
    # backup TSV ve checkpoint geri dönüş sağlar.

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
    backup_path = PILOTS_DIR / f"20260516_tier_i_geometri_retry_BACKUP_{mode}.tsv"
    result_tsv = PILOTS_DIR / f"20260516_tier_i_geometri_retry_{mode}_RESULT.tsv"

    error_ids = load_error_ids()
    print(f"[input] {len(error_ids):,} error ID load edildi", flush=True)

    rows = load_feasibility()
    direct_rows = filter_direct_bucket(rows)
    error_rows = [r for r in direct_rows if r["id"] in error_ids]
    print(
        f"[match] {len(error_rows):,} error satır feasibility direct bucket ile eşleşti",
        flush=True,
    )

    import google.generativeai as genai
    from google.generativeai.types import HarmBlockThreshold, HarmCategory

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config={"temperature": 0.0, "max_output_tokens": 4096},
        safety_settings=safety_settings,
    )
    print(
        f"[gemini] {MODEL_NAME} initialized mode={mode} workers={args.workers} "
        f"safety=BLOCK_NONE (4 categories)",
        flush=True,
    )

    if args.limit:
        import random as _random

        rng = _random.Random(42)
        error_rows = rng.sample(error_rows, min(args.limit, len(error_rows)))
        print(f"[limit] {args.limit} sample (seed=42)", flush=True)

    processed = load_geometri_checkpoint() if args.resume and args.apply else set()
    if processed:
        print(
            f"[resume] {len(processed):,} satır önceden işlenmiş, atlanıyor",
            flush=True,
        )
        error_rows = [r for r in error_rows if r["id"] not in processed]

    ids = [r["id"] for r in error_rows]
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
    n_total = len(error_rows)
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
            for r in error_rows
        }
        for fut in as_completed(futures):
            completed_count += 1
            try:
                fut.result()
            except Exception as e:
                with Locks.print_log:
                    print(f"[fut-err] {e}", flush=True)

            if completed_count % 10 == 0:
                elapsed = time.time() - start_ts
                rate = completed_count / elapsed
                eta_s = (n_total - completed_count) / rate if rate > 0 else 0
                with Locks.print_log:
                    print(
                        f"[{completed_count:04d}/{n_total:04d}] "
                        f"rate={rate * 60:.1f}/min elapsed={elapsed / 60:.1f}m "
                        f"eta={eta_s / 60:.1f}m",
                        flush=True,
                    )
                with Locks.checkpoint:
                    if args.apply:
                        save_geometri_checkpoint(processed)

            if completed_count % 5 == 0:
                with Locks.result_write:
                    result_f.flush()

    with Locks.checkpoint:
        if args.apply:
            save_geometri_checkpoint(processed)
    backup_f.close()
    result_f.close()

    total_elapsed = time.time() - start_ts
    print(f"\n[done] {completed_count} tamamlandı, {total_elapsed / 60:.1f} dakika")
    print("[stats]")
    for k, v in stats.most_common():
        print(f"  {k:25s} {v:,}")

    err_count = stats.get("gemini_error", 0) + stats.get("json_fail", 0)
    err_pct = (err_count * 100 / completed_count) if completed_count else 0
    print(
        f"\n[summary] Error oranı: {err_count}/{completed_count} (%{err_pct:.1f}). "
        f"Threshold ≤%30 → production retry'ya geçilebilir."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
