#!/usr/bin/env python3
"""
Faz 1.9 — Book key cross-reference flag.

answers_v8.answers_page_inline (78,720 satir, page_inline OCR conf 0.85)
ile question_bank.correct_answer karsilastir, pipeline_metadata.book_key_match
field'ina flag yaz.

Strateji A1 (defansif, 8-sample pixel-dogrulanmis):
  agree    -> high-conf flag, judge bypass adayi
  disagree -> needs_review flag, judge'a YUKSEK oncelik
  no_key   -> unchanged

PILOT bulgular: 16,159 match (qbank %17.5), agree=7,425, disagree=8,734.
%87.5 SQLite dogru, %12.5 qbank dogru -> A2 reddedildi (UPDATE riski).

Audit RESULT: backend/_pilots/20260514_book_key_audit_RESULT.md

Kullanim:
    cd backend
    python scripts/book_key_cross_reference.py --dry-run
    python scripts/book_key_cross_reference.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from time import time

# =============================================================================
# Paths
# =============================================================================

SQLITE_DB = Path("C:/Users/husey/kiro2/d-dataset/output/answer_keys_v8/answers_v8.db")
AUDIT_DATE = "2026-05-14"
SOURCE_TAG = "answers_v8.page_inline"


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


def load_sqlite_keys() -> dict[tuple, dict]:
    """SQLite answers_page_inline -> RAM dict.

    Returns:
        {(book_name, page_number, question_number): {"answer", "confidence"}}
    """
    print(f"[1/4] SQLite key yukle: {SQLITE_DB.name}", end=" ... ", flush=True)
    t0 = time()
    if not SQLITE_DB.exists():
        print(f"ERROR: {SQLITE_DB} bulunamadi", file=sys.stderr)
        sys.exit(1)

    d: dict[tuple, dict] = {}
    conn = sqlite3.connect(SQLITE_DB)
    for book, page, qno, ans, conf in conn.execute(
        "SELECT book_name, page_number, question_number, answer, confidence "
        "FROM answers_page_inline"
    ):
        d[(book, page, qno)] = {"answer": ans, "confidence": conf}
    conn.close()
    print(f"OK ({time() - t0:.1f}s, {len(d):,} key)")
    return d


def fetch_qbank_joinable(engine) -> list[tuple]:
    """Joinable subset of question_bank."""
    from sqlalchemy import text

    SQL = """
        SELECT
            id,
            source_book,
            source_page,
            (pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no')::int AS q_no,
            correct_answer
        FROM question_bank
        WHERE is_active = TRUE
          AND source_book IS NOT NULL
          AND source_page IS NOT NULL
          AND pipeline_metadata::jsonb -> 'ai_extras' ->> 'q_no' ~ '^[0-9]+$'
          AND correct_answer IS NOT NULL
    """
    print("[2/4] question_bank joinable subset fetch", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as c:
        rows = list(c.execute(text(SQL)))
    print(f"OK ({time() - t0:.1f}s, {len(rows):,} satir)")
    return rows


def match_and_flag(
    qb_rows: list[tuple],
    sqlite_dict: dict[tuple, dict],
) -> tuple[list[dict], Counter]:
    """Her qbank satiri icin SQLite key kontrol et + flag uret."""
    print("[3/4] Match + flag", end=" ... ", flush=True)
    t0 = time()
    results: list[dict] = []
    stats: Counter = Counter()

    for qb_id, book, page, qno, qb_ans in qb_rows:
        stats["qbank_total"] += 1
        key = (book, page, qno)
        if key not in sqlite_dict:
            stats["no_key"] += 1
            continue

        sqlite_entry = sqlite_dict[key]
        sqlite_ans = sqlite_entry["answer"]
        status = "agree" if sqlite_ans == qb_ans else "disagree"
        stats[status] += 1

        flag = {
            "status": status,
            "sqlite_answer": sqlite_ans,
            "qbank_answer": qb_ans,
            "sqlite_confidence": sqlite_entry["confidence"],
            "source": SOURCE_TAG,
            "audit_date": AUDIT_DATE,
        }
        results.append({"id": qb_id, "flag": flag})

    elapsed = time() - t0
    print(f"OK ({elapsed:.1f}s)")
    print()
    print("  Match istatistikleri:")
    total = stats["qbank_total"]
    for st in ["qbank_total", "no_key", "agree", "disagree"]:
        n = stats[st]
        pct = 100.0 * n / total if total else 0
        print(f"    {st:12s} {n:>7,} ({pct:5.1f}%)")

    matched = stats["agree"] + stats["disagree"]
    if matched:
        agree_pct = 100.0 * stats["agree"] / matched
        print(f"    -> agree of matched:    {agree_pct:5.1f}%")
    return results, stats


def apply_flags(engine, results: list[dict], batch_size: int = 1000) -> int:
    """JSON merge UPDATE pipeline_metadata.book_key_match. Idempotent."""
    from sqlalchemy import text

    UPDATE_SQL = """
        UPDATE question_bank
        SET pipeline_metadata = jsonb_set(
            COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
            '{book_key_match}',
            CAST(:flag_json AS jsonb),
            TRUE
        )::json
        WHERE id = :id
    """

    print(f"[4/4] DB update (JSON merge, batch={batch_size}) ...")
    updated = 0
    failed = 0

    with engine.begin() as conn:
        for i in range(0, len(results), batch_size):
            batch = results[i : i + batch_size]
            for row in batch:
                try:
                    r = conn.execute(
                        text(UPDATE_SQL),
                        {
                            "id": row["id"],
                            "flag_json": json.dumps(row["flag"]),
                        },
                    )
                    if r.rowcount > 0:
                        updated += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    if failed <= 3:
                        print(f"  [WARN] id={row['id'][:8]} fail: {e}")

            done = i + len(batch)
            pct = done / len(results) * 100
            print(
                f"  [{pct:5.1f}%] {done:,}/{len(results):,} "
                f"({updated:,} updated, {failed:,} failed)"
            )

    # Verify
    with engine.connect() as conn:
        agree_n = conn.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE pipeline_metadata::jsonb -> 'book_key_match' ->> 'status' = 'agree'"
            )
        ).scalar()
        disagree_n = conn.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE pipeline_metadata::jsonb -> 'book_key_match' ->> 'status' = 'disagree'"
            )
        ).scalar()

    print()
    print("DB dogrulama:")
    print(f"  book_key_match=agree:    {agree_n:,}")
    print(f"  book_key_match=disagree: {disagree_n:,}")
    print(f"  TOPLAM flag:             {agree_n + disagree_n:,}")
    print(f"  Bu run'da updated:       {updated:,}")
    print(f"  Failed:                  {failed:,}")
    return updated


# =============================================================================
# Sample / Reporting
# =============================================================================


def print_sample(results: list[dict], n: int = 5) -> None:
    import random

    random.seed(42)
    samples = random.sample(results, min(n, len(results)))
    print()
    print(f"Random sample ({n} flag):")
    print("-" * 100)
    for s in samples:
        flag = s["flag"]
        print(
            f"  id={s['id'][:8]}.. status={flag['status']:8s} "
            f"qb={flag['qbank_answer']} sqlite={flag['sqlite_answer']} "
            f"conf={flag['sqlite_confidence']:.2f}"
        )
    print("-" * 100)


# =============================================================================
# Entry point
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Book key cross-reference flag (Faz 1.9)"
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="Report only")
    g.add_argument("--apply", action="store_true", help="Apply DB UPDATE")
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    print("=" * 60)
    print("book_key_cross_reference.py — Faz 1.9")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print("Strategy: A1 defansif (agree=high-conf, disagree=needs_review)")
    print()

    sqlite_dict = load_sqlite_keys()

    engine = get_engine()
    qb_rows = fetch_qbank_joinable(engine)

    if not qb_rows:
        print("[ERROR] qbank joinable subset bos!", file=sys.stderr)
        sys.exit(1)

    results, _stats = match_and_flag(qb_rows, sqlite_dict)

    if not results:
        print("[ERROR] Hicbir flag uretilmedi.", file=sys.stderr)
        sys.exit(1)

    print_sample(results)

    if args.apply:
        updated = apply_flags(engine, results, args.batch_size)
        print()
        print(
            f"Done. {updated:,} satirin pipeline_metadata.book_key_match field'i set edildi."
        )
    else:
        print()
        print("[DRY RUN] DB degistirilmedi. --apply ile calistir.")

    engine.dispose()


if __name__ == "__main__":
    main()
