#!/usr/bin/env python3
"""Judge Pipeline Runner — Bronze pool batch processor.

Runs Opus + Pro double-check on bronze_clean rows, writes verdict to
quality_review_status + pipeline_metadata.judge_v1.

ARCHITECTURE:
  - Outer ThreadPool: N rows in parallel (default 10 workers)
  - Inner ThreadPool(2): Opus + Pro called in parallel per row
  - Per-row latency: max(opus, pro) ≈ 13s vs sequential 26s
  - Throughput: ~40-60 rows/min @ 10 workers

USAGE:
  # Pilot (Faz 6.1) — 1,000 sample, dry-run, no DB UPDATE
  python -m backend.scripts.judge.runner --pilot --dry-run --workers 5

  # Pilot live (after dry-run audit OK)
  python -m backend.scripts.judge.runner --pilot --workers 10 --run-id pilot1k_20260520

  # Full (Faz 6.3) — Bronze 80K, resume-able
  python -m backend.scripts.judge.runner --full --resume --workers 10 --run-id full_20260601

  # Geometri safety_blocked retry pile (Session 161+ Faz 5.8)
  python -m backend.scripts.judge.runner --retry-safety-blocked --workers 5

PRE-DEPLOY CHECKLIST (Spec §10.1):
  [ ] Faz 5.4 holdout F1 ≥ 0.80
  [ ] False positive ≤ %5 on 50-sample
  [ ] Cost projection sapma ≤ %10 (50 sample dry-run)
  [ ] ANTHROPIC_API_KEY + GEMINI_API_KEY env set
  [ ] Pre-run pg_dump backup of question_bank.quality_review_status (Faz 0.4)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PILOTS_DIR = PROJECT_ROOT / "backend" / "_pilots"

# Local imports
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
from scripts.judge import client, prompt_v1  # noqa: E402
from scripts.judge.aggregator import (  # noqa: E402
    RESULT_TSV_HEADER,
    build_audit_delta,
    estimate_call_cost_usd,
    result_tsv_row,
    status_for_verdict,
)

# ============================================================================
# DB ACCESS (uses same engine pattern as tier_i_reocr_apply.py)
# ============================================================================


def get_engine():
    """Lazy SQLAlchemy engine. Uses DATABASE_URL or falls back to local default."""
    from sqlalchemy import create_engine

    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5434/kiro2",
    ).replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    return create_engine(url, pool_size=20, max_overflow=10)


def fetch_bronze_rows(
    engine, *, limit: int | None = None, run_id_seed: str = "judge"
) -> list[dict]:
    """
    Fetch bronze_clean rows for judge processing.

    Stable random ordering via md5(id || run_id_seed) so re-runs with same
    run_id pick same row order (idempotent with checkpoint).
    """
    from sqlalchemy import text

    sql = """
        SELECT id::text AS id,
               question_text,
               option_a, option_b, option_c, option_d, option_e,
               correct_answer,
               subject_area,
               exam_type,
               question_image_url,
               quality_review_status
        FROM question_bank
        WHERE quality_review_status = 'bronze_clean'
          AND is_active = TRUE
        ORDER BY md5(id::text || :seed)
    """
    if limit:
        sql += f" LIMIT {int(limit)}"

    with engine.connect() as conn:
        rs = conn.execute(text(sql), {"seed": run_id_seed})
        return [dict(r._mapping) for r in rs.fetchall()]


def update_db(
    engine, *, id_: str, new_status: str, audit_delta: dict, dry_run: bool = False
):
    """Apply quality_review_status + pipeline_metadata.judge_v1 to question_bank."""
    if dry_run:
        return

    from sqlalchemy import text

    delta_json = json.dumps(audit_delta, ensure_ascii=False)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE question_bank
                SET quality_review_status = :status,
                    pipeline_metadata = (
                        COALESCE(pipeline_metadata, '{}'::json)::jsonb
                        || CAST(:delta AS jsonb)
                    )::json,
                    updated_at = NOW()
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {"status": new_status, "delta": delta_json, "id": id_},
        )


# ============================================================================
# CHECKPOINT (Tier I pattern)
# ============================================================================


def checkpoint_path(run_id: str) -> Path:
    return PILOTS_DIR / f"judge_checkpoint_{run_id}.json"


def load_checkpoint(run_id: str) -> set[str]:
    path = checkpoint_path(run_id)
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8"))["processed_ids"])


def save_checkpoint(run_id: str, processed: set[str]):
    path = checkpoint_path(run_id)
    path.write_text(
        json.dumps({"processed_ids": sorted(processed)}, ensure_ascii=False),
        encoding="utf-8",
    )


# ============================================================================
# PER-ROW WORKER
# ============================================================================


class Locks:
    stats = threading.Lock()
    checkpoint = threading.Lock()
    result_write = threading.Lock()
    backup_write = threading.Lock()
    print_log = threading.Lock()


def call_both_models_parallel(
    *,
    user_prompt: str,
    opus_system: str,
    pro_full: str,
    safety_block_dangerous: bool,
) -> tuple[dict, dict]:
    """
    Call Opus + Pro IN PARALLEL using inner ThreadPoolExecutor(2).
    Reduces per-row latency from 26s → ~13s.
    """
    with ThreadPoolExecutor(max_workers=2) as inner:
        opus_fut = inner.submit(client.call_opus, system=opus_system, user=user_prompt)
        pro_fut = inner.submit(
            client.call_pro,
            full_prompt=pro_full,
            safety_block_dangerous=safety_block_dangerous,
        )
        return opus_fut.result(), pro_fut.result()


def process_row(
    row: dict,
    args,
    backup_f,
    result_f,
    stats: Counter,
    processed: set,
) -> str:
    """Single bronze_clean row → judge → DB update."""
    id_ = row["id"]
    book_answer = row["correct_answer"]

    # Build prompts
    options = {
        "A": row["option_a"] or "",
        "B": row["option_b"] or "",
        "C": row["option_c"] or "",
        "D": row["option_d"] or "",
        "E": row["option_e"] or "",
    }
    try:
        user_prompt = prompt_v1.build_user_prompt(
            subject_area=row["subject_area"] or "UNKNOWN",
            exam_type=row["exam_type"] or "TYT",
            question_text=row["question_text"] or "",
            options=options,
            book_answer=book_answer,
        )
    except ValueError as e:
        with Locks.stats:
            stats["build_prompt_error"] += 1
        with Locks.result_write:
            result_f.write(
                f"{id_}\t{args.run_id}\tERR\tERR\tERR\t\t\tprompt_build\tprompt\t0.0\n"
            )
        with Locks.print_log:
            print(f"[ERR-PROMPT {id_[:8]}] {e}", flush=True)
        return "build_prompt_error"

    if args.dry_run:
        # Synthetic stub for dry-run mode (no API calls)
        opus_result = client.call_dummy(verdict="PASS", answer=book_answer)
        pro_result = client.call_dummy(verdict="PASS", answer=book_answer)
    else:
        opus_system = prompt_v1.build_opus_system()
        pro_full = prompt_v1.build_pro_full_prompt(user_prompt=user_prompt)
        opus_result, pro_result = call_both_models_parallel(
            user_prompt=user_prompt,
            opus_system=opus_system,
            pro_full=pro_full,
            safety_block_dangerous=args.safety_block_dangerous,
        )

    # Build audit delta + decision
    audit_delta = build_audit_delta(
        run_id=args.run_id,
        opus_result=opus_result,
        pro_result=pro_result,
        book_answer=book_answer,
    )
    combined = audit_delta["judge_v1"]["combined_verdict"]
    new_status = status_for_verdict(combined, row["quality_review_status"])
    cost = estimate_call_cost_usd(opus_result, pro_result)

    # BACKUP (status snapshot for rollback)
    with Locks.backup_write:
        backup_f.write(f"{id_}\t{row['quality_review_status']}\n")

    # DB UPDATE (skipped in dry-run)
    try:
        update_db(
            args._engine,
            id_=id_,
            new_status=new_status,
            audit_delta=audit_delta,
            dry_run=args.dry_run,
        )
    except Exception as e:
        with Locks.stats:
            stats["db_update_error"] += 1
        with Locks.result_write:
            result_f.write(
                f"{id_}\t{args.run_id}\tDB_ERR\t\t\t\t\t{str(e)[:60]}\tdb_error\t{cost:.6f}\n"
            )
        with Locks.print_log:
            print(f"[DB-ERR {id_[:8]}] {str(e)[:80]}", flush=True)
        return "db_update_error"

    # RESULT TSV
    with Locks.result_write:
        result_f.write(
            result_tsv_row(
                id_=id_, run_id=args.run_id, audit_delta=audit_delta, cost_usd=cost
            )
            + "\n"
        )

    # Stats + checkpoint
    with Locks.stats:
        stats[combined.lower()] += 1
        if combined == "PASS":
            stats["status_auto_judged_high"] += 1
        elif combined == "FAIL":
            stats["status_rejected"] += 1
        else:
            stats["status_unchanged_escalate"] += 1
        stats["total_cost_usd"] = stats.get("total_cost_usd", 0.0) + cost

    with Locks.checkpoint:
        processed.add(id_)

    return combined.lower()


# ============================================================================
# MAIN
# ============================================================================


def main():
    ap = argparse.ArgumentParser()

    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pilot", action="store_true", help="1,000 sample (Faz 6.1)")
    mode.add_argument("--full", action="store_true", help="Full Bronze pool (Faz 6.3)")
    mode.add_argument("--limit", type=int, help="Custom row limit (smoke testing)")
    mode.add_argument(
        "--retry-safety-blocked",
        action="store_true",
        help="Re-run only previously gemini_safety_blocked rows with safety_settings=BLOCK_NONE",
    )

    ap.add_argument("--dry-run", action="store_true", help="No API calls, no DB UPDATE")
    ap.add_argument(
        "--resume", action="store_true", help="Skip checkpoint-completed IDs"
    )
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument(
        "--run-id", required=True, help="Unique run identifier (in checkpoint, audit)"
    )
    ap.add_argument(
        "--safety-block-dangerous",
        action="store_true",
        help="Pass safety_settings=BLOCK_NONE to Gemini (Session 161+ Geometri retry)",
    )

    args = ap.parse_args()

    # Env check (skipped for dry-run)
    if not args.dry_run:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("[error] ANTHROPIC_API_KEY env var required", file=sys.stderr)
            return 1
        if not os.getenv("GEMINI_API_KEY"):
            print("[error] GEMINI_API_KEY env var required", file=sys.stderr)
            return 1

    # Resolve row limit
    if args.pilot:
        row_limit = 1000
    elif args.limit:
        row_limit = args.limit
    else:
        row_limit = None  # full

    # File paths
    backup_path = PILOTS_DIR / f"judge_BACKUP_{args.run_id}.tsv"
    result_path = PILOTS_DIR / f"judge_RESULT_{args.run_id}.tsv"

    # DB fetch
    engine = get_engine()
    args._engine = engine
    print(f"[db] fetching bronze_clean rows (limit={row_limit})...", flush=True)
    rows = fetch_bronze_rows(engine, limit=row_limit, run_id_seed=args.run_id)
    print(f"[db] {len(rows):,} rows fetched", flush=True)

    if not rows:
        print("[done] No bronze_clean rows to judge.")
        return 0

    # Resume
    processed = load_checkpoint(args.run_id) if args.resume else set()
    if processed:
        print(f"[resume] {len(processed):,} already processed, skipping")
        rows = [r for r in rows if r["id"] not in processed]
        print(f"[resume] {len(rows):,} remaining")

    if not rows:
        print("[done] All rows already processed.")
        return 0

    # Open files
    open_mode = "a" if args.resume else "w"
    backup_f = open(backup_path, open_mode, encoding="utf-8")
    result_f = open(result_path, open_mode, encoding="utf-8")
    if not args.resume:
        backup_f.write("id\tprev_status\n")
        result_f.write(RESULT_TSV_HEADER + "\n")

    stats = Counter()
    start_ts = time.time()
    n_total = len(rows)

    print(
        f"[judge] {prompt_v1.PROMPT_VERSION} mode={'dry' if args.dry_run else 'live'} workers={args.workers}",
        flush=True,
    )
    print(f"[judge] run_id={args.run_id}", flush=True)

    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(process_row, r, args, backup_f, result_f, stats, processed): r[
                "id"
            ]
            for r in rows
        }
        for fut in as_completed(futures):
            completed += 1
            try:
                fut.result()
            except Exception as e:
                with Locks.print_log:
                    print(f"[fut-err] {e}", flush=True)

            if completed % 25 == 0:
                elapsed = time.time() - start_ts
                rate = completed / elapsed if elapsed > 0 else 0
                eta_s = (n_total - completed) / rate if rate > 0 else 0
                with Locks.print_log:
                    print(
                        f"[{completed:04d}/{n_total:04d}] "
                        f"rate={rate * 60:.1f}/min "
                        f"elapsed={elapsed / 60:.1f}m "
                        f"eta={eta_s / 60:.1f}m "
                        f"cost=${stats.get('total_cost_usd', 0):.2f}",
                        flush=True,
                    )
                with Locks.checkpoint:
                    save_checkpoint(args.run_id, processed)

            if completed % 10 == 0:
                with Locks.result_write:
                    result_f.flush()

    # Final
    with Locks.checkpoint:
        save_checkpoint(args.run_id, processed)
    backup_f.close()
    result_f.close()

    elapsed = time.time() - start_ts
    print(f"\n[done] {completed} processed in {elapsed / 60:.1f} min")
    print("[stats]")
    for k, v in stats.most_common():
        if isinstance(v, float):
            print(f"  {k:30s} ${v:.4f}")
        else:
            print(f"  {k:30s} {v:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
