#!/usr/bin/env python3
"""
Faz 1.4 — Sanity checker (duplicate options + answer-fits-options).

question_bank icindeki aktif satirlari iki sanity kontrolden gecirir ve
problem varsa `pipeline_metadata.sanity_flags` field'ina flag yazar.

Kontroller:
  1) duplicate_options: option_a..e arasinda strict exact match (10 ikili)
     - placeholder ('(grafik)', '(sekil)', '(grafiK)') AYRI tip:
       placeholder_dup=True flag ile isaretlenir, judge sinyal alir
  2) answer_no_option: correct_answer (A-E) varken karsilik gelen option_*
     NULL veya bos string

Felsefe (Faz 1.9 ile uyumlu): DEFANSIF flag-only. UPDATE etmez, judge'a
yuksek oncelik sinyal yazar. Sadece problem var ise flag yazilir, clean
satirlar pipeline_metadata dokunulmaz (gurultu minimum).

Kullanim:
    cd backend
    python scripts/sanity_checker.py --dry-run
    python scripts/sanity_checker.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from itertools import combinations
from pathlib import Path
from time import time

AUDIT_DATE = "2026-05-15"
PLACEHOLDER_TOKENS = ("(grafik)", "(sekil)", "(şekil)", "(grafiK)", "(Sekil)")


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
# Sanity Logic
# =============================================================================


def is_placeholder(text: str | None) -> bool:
    """Image-only opsiyon placeholder mu? ('(grafik)' vb)."""
    if not text:
        return False
    return text.strip() in PLACEHOLDER_TOKENS


def check_row(row) -> dict | None:
    """Bir question_bank satirini sanity-check et.

    Args:
        row: (id, correct_answer, option_a, option_b, option_c, option_d, option_e)

    Returns:
        Flag dict (problem var ise), None (clean ise).
    """
    qb_id, correct, oa, ob, oc, od, oe = row
    options = {"A": oa, "B": ob, "C": oc, "D": od, "E": oe}

    flag: dict = {}

    # Kontrol 1: duplicate_options (strict exact match, 10 ikili)
    dup_pairs: list[list[str]] = []
    placeholder_dup = False
    for x, y in combinations(["A", "B", "C", "D", "E"], 2):
        vx, vy = options[x], options[y]
        if vx is None or vy is None:
            continue
        if len(vx) == 0 or len(vy) == 0:
            continue
        if vx == vy:
            dup_pairs.append([x, y])
            if is_placeholder(vx):
                placeholder_dup = True

    if dup_pairs:
        flag["duplicate_options"] = dup_pairs
        if placeholder_dup:
            flag["placeholder_dup"] = True

    # Kontrol 2: answer_no_option
    correct_option = options.get(correct) if correct in options else None
    if correct in options:
        if correct_option is None or len(correct_option.strip()) == 0:
            flag["answer_no_option"] = True

    if not flag:
        return None

    flag["audit_date"] = AUDIT_DATE
    return {"id": qb_id, "flag": flag}


# =============================================================================
# Phases
# =============================================================================


def fetch_question_rows(engine) -> list[tuple]:
    """Aktif sorular: id + correct_answer + 5 opsiyon."""
    from sqlalchemy import text

    SQL = """
        SELECT id, correct_answer,
               option_a, option_b, option_c, option_d, option_e
        FROM question_bank
        WHERE is_active = TRUE
    """
    print("[1/3] question_bank fetch", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as c:
        rows = list(c.execute(text(SQL)))
    print(f"OK ({time() - t0:.1f}s, {len(rows):,} satir)")
    return rows


def check_all(rows: list[tuple]) -> tuple[list[dict], Counter]:
    """Tum satirlari check et, flag dict listesi + stats don."""
    print("[2/3] Sanity check", end=" ... ", flush=True)
    t0 = time()
    results: list[dict] = []
    stats: Counter = Counter()

    for row in rows:
        stats["total"] += 1
        flag = check_row(row)
        if flag is None:
            stats["clean"] += 1
            continue
        results.append(flag)
        f = flag["flag"]
        if "duplicate_options" in f:
            stats["duplicate_options"] += 1
            if f.get("placeholder_dup"):
                stats["placeholder_dup"] += 1
        if f.get("answer_no_option"):
            stats["answer_no_option"] += 1
        if "duplicate_options" in f and f.get("answer_no_option"):
            stats["both"] += 1

    print(f"OK ({time() - t0:.1f}s)")
    print()
    print("  Sanity istatistikleri:")
    total = stats["total"]
    keys = [
        "total",
        "clean",
        "duplicate_options",
        "placeholder_dup",
        "answer_no_option",
        "both",
    ]
    for k in keys:
        n = stats[k]
        pct = 100.0 * n / total if total else 0
        print(f"    {k:20s} {n:>7,} ({pct:5.2f}%)")
    return results, stats


def apply_flags(engine, results: list[dict], batch_size: int = 500) -> int:
    """JSON merge UPDATE pipeline_metadata.sanity_flags. Idempotent."""
    from sqlalchemy import text

    UPDATE_SQL = """
        UPDATE question_bank
        SET pipeline_metadata = jsonb_set(
            COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
            '{sanity_flags}',
            CAST(:flag_json AS jsonb),
            TRUE
        )::json
        WHERE id = :id
    """

    print(f"[3/3] DB update (JSON merge, batch={batch_size}) ...")
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
        dup_n = conn.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE pipeline_metadata::jsonb -> 'sanity_flags' ? 'duplicate_options'"
            )
        ).scalar()
        ans_n = conn.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE (pipeline_metadata::jsonb -> 'sanity_flags' ->> 'answer_no_option')::bool IS TRUE"
            )
        ).scalar()

    print()
    print("DB dogrulama:")
    print(f"  sanity_flags duplicate_options:  {dup_n:,}")
    print(f"  sanity_flags answer_no_option:   {ans_n:,}")
    print(f"  Bu run'da updated:               {updated:,}")
    print(f"  Failed:                          {failed:,}")
    return updated


# =============================================================================
# Sample / Reporting
# =============================================================================


def print_sample(results: list[dict], n: int = 8) -> None:
    import random

    random.seed(42)
    samples = random.sample(results, min(n, len(results)))
    print()
    print(f"Random sample ({n} flag):")
    print("-" * 100)
    for s in samples:
        f = s["flag"]
        parts = []
        if "duplicate_options" in f:
            pairs = ",".join("=".join(p) for p in f["duplicate_options"])
            tag = "PLACEHOLDER_DUP" if f.get("placeholder_dup") else "DUP"
            parts.append(f"{tag}[{pairs}]")
        if f.get("answer_no_option"):
            parts.append("ANS_NO_OPT")
        print(f"  id={s['id'][:8]}.. {' '.join(parts)}")
    print("-" * 100)


# =============================================================================
# Entry point
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sanity checker (Faz 1.4): duplicate options + answer-fits-options"
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="Report only")
    g.add_argument("--apply", action="store_true", help="Apply UPDATE")
    args = parser.parse_args()

    engine = get_engine()
    rows = fetch_question_rows(engine)
    results, stats = check_all(rows)

    if results:
        print_sample(results)

    if args.dry_run:
        print()
        print(f"[DRY-RUN] {len(results):,} satir flag adayi. UPDATE atilmadi.")
        return

    if not results:
        print()
        print("Flag yazilacak satir yok. Cikis.")
        return

    print()
    print(f"[APPLY] {len(results):,} satira sanity_flags yaziliyor...")
    apply_flags(engine, results)
    print()
    print("Tamamlandi.")


if __name__ == "__main__":
    main()
