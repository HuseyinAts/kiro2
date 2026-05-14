#!/usr/bin/env python3
"""
Faz 1.3 — OCR text validator (Turkce sozluk + n-gram).

Corpus-based heuristik:
  S1 (rare_token_ratio): Trusted vocab = freq>=3. Per-row rare token oran.
  S2 (4+ consonant anomaly): Turkcede 4+ unsuz pes pese nadirdir.
       Yabanci/notation false-positive bilinen sinir.
  KOMBINE: rare_ratio >= 0.15 AND >=1 rare token icinde 4+ unsuz pattern

Felsefe (Faz 1.4/1.9 ile uyumlu): DEFANSIF flag-only. UPDATE etmez,
judge'a "incele" sinyali.

Bilinen sinir (false-positive):
  - Geometri etiketleri (TFCN, ABCDEFGHK) -> cogu lowercased = rare
  - Yabanci isimler (Schliemann, Winckler) -> rare + 4+ unsuz
  - Kimya nomenklaturu (cyclopentanol) -> rare + 4+ unsuz
  - Osmanlica/Divan edebiyati -> rare ama 4+ unsuz nadir
  - Tip terimleri (ekstremitelerdeki) -> 4+ unsuz icinde valid TR

~60-70 satir flag bekleniyor (corpus zaten OCR temiz).

Kullanim:
    cd backend
    python scripts/ocr_text_validator.py --dry-run
    python scripts/ocr_text_validator.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from time import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AUDIT_DATE = "2026-05-15"
MIN_TOKENS = 8
TRUSTED_FREQ_THRESHOLD = 3
RARE_RATIO_THRESHOLD = 0.15
TOKEN_RE = re.compile(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}")
LATEX_RE = re.compile(r"\$[^$]*\$")
CONSONANTS = "bcçdfgğhjklmnprsştvyz"
FOUR_CONS = re.compile(rf"[{CONSONANTS}]{{4,}}")


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
# Tokenizer & scorer
# =============================================================================


def tokenize(text_in: str) -> list[str]:
    s = LATEX_RE.sub(" ", text_in)
    s = unicodedata.normalize("NFC", s).lower()
    return TOKEN_RE.findall(s)


def score_row(toks: list[str], trusted: set[str]) -> dict | None:
    """Returns flag dict if combined signal triggers, else None."""
    if len(toks) < MIN_TOKENS:
        return None
    rare_tokens = [t for t in toks if t not in trusted]
    rare_ratio = len(rare_tokens) / len(toks)
    if rare_ratio < RARE_RATIO_THRESHOLD:
        return None
    # 4+ unsuz, rare token icinde
    anomaly_tokens = sorted({t for t in rare_tokens if FOUR_CONS.search(t)})
    if not anomaly_tokens:
        return None
    return {
        "rare_token_ratio": round(rare_ratio, 4),
        "anomaly_tokens": anomaly_tokens[:5],  # ilk 5
        "anomaly_count": len(anomaly_tokens),
        "audit_date": AUDIT_DATE,
    }


# =============================================================================
# Phases
# =============================================================================


def fetch_all_rows(engine) -> list[tuple]:
    from sqlalchemy import text

    SQL = """
        SELECT id::text, question_text
        FROM question_bank
        WHERE is_active = TRUE
          AND question_text IS NOT NULL
    """
    print("[1/4] question_bank fetch", end=" ... ", flush=True)
    t0 = time()
    with engine.connect() as c:
        rows = list(c.execute(text(SQL)))
    print(f"OK ({time() - t0:.1f}s, {len(rows):,} satir)")
    return rows


def build_trusted_vocab(rows: list[tuple]) -> tuple[set[str], dict]:
    print(
        f"[2/4] Trusted vocab (freq>={TRUSTED_FREQ_THRESHOLD}) build",
        end=" ... ",
        flush=True,
    )
    t0 = time()
    freq: Counter = Counter()
    tokenized: dict[str, list[str]] = {}
    for qid, qt in rows:
        toks = tokenize(qt)
        freq.update(toks)
        tokenized[qid] = toks
    trusted = {w for w, n in freq.items() if n >= TRUSTED_FREQ_THRESHOLD}
    print(
        f"OK ({time() - t0:.1f}s, {len(freq):,} unique, {len(trusted):,} trusted "
        f"= {100 * len(trusted) / len(freq):.1f}%)"
    )
    return trusted, tokenized


def score_all(
    rows: list[tuple],
    trusted: set[str],
    tokenized: dict[str, list[str]],
) -> tuple[list[dict], Counter]:
    print("[3/4] Per-row scoring", end=" ... ", flush=True)
    t0 = time()
    results: list[dict] = []
    stats: Counter = Counter()
    for qid, qt in rows:
        stats["total"] += 1
        toks = tokenized.get(qid, [])
        flag = score_row(toks, trusted)
        if flag is None:
            stats["clean"] += 1
            continue
        stats["flagged"] += 1
        results.append({"id": qid, "flag": flag})
    print(f"OK ({time() - t0:.1f}s)")
    print()
    print("  Sonuc:")
    total = stats["total"]
    for k in ["total", "clean", "flagged"]:
        n = stats[k]
        pct = 100.0 * n / total if total else 0
        print(f"    {k:10s} {n:>7,} ({pct:5.3f}%)")
    return results, stats


def apply_flags(engine, results: list[dict], batch_size: int = 200) -> int:
    from sqlalchemy import text

    UPDATE_SQL = """
        UPDATE question_bank
        SET pipeline_metadata = jsonb_set(
            COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
            '{ocr_quality_flag}',
            CAST(:flag_json AS jsonb),
            TRUE
        )::json
        WHERE id = :id
    """
    print(f"\n[4/4] DB update (batch={batch_size}) ...")
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
                        print(f"  [WARN] id={row['id'][:8]}: {e}")
            done = i + len(batch)
            pct = done / len(results) * 100
            print(
                f"  [{pct:5.1f}%] {done:,}/{len(results):,} "
                f"({updated:,} updated, {failed:,} failed)"
            )

    with engine.connect() as conn:
        n_flag = conn.execute(
            text(
                "SELECT COUNT(*) FROM question_bank "
                "WHERE pipeline_metadata::jsonb -> 'ocr_quality_flag' IS NOT NULL"
            )
        ).scalar()
    print()
    print(f"DB dogrulama: ocr_quality_flag = {n_flag:,}")
    return updated


# =============================================================================
# Sample
# =============================================================================


def print_sample(results: list[dict], n: int = 8) -> None:
    if not results:
        return
    import random

    random.seed(42)
    samp = random.sample(results, min(n, len(results)))
    print()
    print(f"Random sample ({n}):")
    print("-" * 100)
    for r in samp:
        f = r["flag"]
        bad = ",".join(
            t.encode("ascii", "replace").decode("ascii") for t in f["anomaly_tokens"]
        )
        print(
            f"  id={r['id'][:8]} rare={f['rare_token_ratio']:.2%} "
            f"anom_count={f['anomaly_count']} tokens=[{bad}]"
        )
    print("-" * 100)


# =============================================================================
# Entry point
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR text validator (Faz 1.3)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    engine = get_engine()
    rows = fetch_all_rows(engine)
    trusted, tokenized = build_trusted_vocab(rows)
    results, _ = score_all(rows, trusted, tokenized)
    print_sample(results)

    if args.dry_run:
        print(f"\n[DRY-RUN] {len(results):,} flag adayi. UPDATE atilmadi.")
        return
    if not results:
        print("\nFlag yok, cikis.")
        return
    print(f"\n[APPLY] {len(results):,} satira ocr_quality_flag yaziliyor...")
    apply_flags(engine, results)
    print("\nTamamlandi.")


if __name__ == "__main__":
    main()
