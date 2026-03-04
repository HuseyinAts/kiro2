#!/usr/bin/env python3
"""
Update morphology metrics for question_bank rows.

Calculates word_count, unique_word_count, average_word_length,
readability_score, morphology_complexity for all questions.

Usage:
    cd backend
    python scripts/update_morphology.py [--batch-size 5000] [--dry-run]
"""

import argparse
import math
import os
import re
import sys
import unicodedata
from pathlib import Path
from time import time


def tokenize_turkish(text: str) -> list[str]:
    """Simple Turkish-aware word tokenizer."""
    if not text:
        return []
    # Remove math symbols, special chars, keep Turkish letters
    text = unicodedata.normalize("NFC", text)
    # Split on whitespace and punctuation (keep apostrophe in words)
    words = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜâîû0-9']+", text)
    return [w for w in words if len(w) > 0]


def count_sentences(text: str) -> int:
    """Count sentences based on punctuation."""
    if not text:
        return 0
    # Split on sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)
    return max(1, len([s for s in sentences if s.strip()]))


def calc_readability(word_count: int, sentence_count: int, avg_word_len: float) -> float:
    """Simple readability score (0-100, higher = easier to read).

    Based on average sentence length and word length.
    Turkish adaptation of Flesch-Kincaid.
    """
    if word_count == 0 or sentence_count == 0:
        return 50.0  # Default for empty text
    avg_sentence_len = word_count / sentence_count
    # Turkish readability formula (simplified)
    score = 206.835 - (1.015 * avg_sentence_len) - (84.6 * (avg_word_len / 5.0))
    return max(0.0, min(100.0, score))


def calc_morphology_complexity(text: str, unique_ratio: float, avg_word_len: float) -> float:
    """Morphology complexity score (0-1).

    Turkish agglutinative morphology: longer words = more suffixes = more complex.
    """
    # Factors: word length, unique ratio, presence of special patterns
    length_factor = min(1.0, avg_word_len / 10.0)  # Normalized to 10-char max
    variety_factor = 1.0 - unique_ratio  # More repeated words = simpler
    return round((length_factor * 0.6 + variety_factor * 0.4), 4)


def compute_metrics(text: str) -> dict:
    """Compute all morphology metrics for a question text."""
    words = tokenize_turkish(text)
    word_count = len(words)

    if word_count == 0:
        return {
            "word_count": 0,
            "unique_word_count": 0,
            "average_word_length": 0.0,
            "readability_score": 50.0,
            "morphology_complexity": 0.0,
        }

    unique_words = set(w.lower() for w in words)
    unique_word_count = len(unique_words)
    avg_word_len = sum(len(w) for w in words) / word_count
    sentence_count = count_sentences(text)
    unique_ratio = unique_word_count / word_count

    return {
        "word_count": word_count,
        "unique_word_count": unique_word_count,
        "average_word_length": round(avg_word_len, 2),
        "readability_score": round(calc_readability(word_count, sentence_count, avg_word_len), 2),
        "morphology_complexity": calc_morphology_complexity(text, unique_ratio, avg_word_len),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Update morphology metrics")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:changeme@localhost:5434/kiro2",
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")

    from sqlalchemy import create_engine, text
    engine = create_engine(db_url)

    print("=" * 60)
    print("Morphology Metrics Update")
    print("=" * 60)

    # Fetch all questions with word_count = 0
    with engine.connect() as conn:
        total = conn.execute(text(
            "SELECT COUNT(*) FROM question_bank WHERE word_count = 0"
        )).scalar()
        print(f"Questions to process: {total:,}")

    if total == 0:
        print("Nothing to update.")
        return

    if args.dry_run:
        # Sample 5 questions
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT id, question_text FROM question_bank WHERE word_count = 0 LIMIT 5"
            )).fetchall()
        for r in rows:
            m = compute_metrics(r[1])
            print(f"  {r[0][:8]}... words={m['word_count']}, "
                  f"unique={m['unique_word_count']}, "
                  f"avg_len={m['average_word_length']}, "
                  f"readability={m['readability_score']}, "
                  f"complexity={m['morphology_complexity']}")
        print("\n[DRY RUN] No changes made.")
        return

    # Batch update
    t0 = time()
    updated = 0

    with engine.connect() as conn:
        offset = 0
        while offset < total:
            rows = conn.execute(text(
                "SELECT id, question_text FROM question_bank "
                "WHERE word_count = 0 "
                "ORDER BY id LIMIT :limit OFFSET :offset"
            ), {"limit": args.batch_size, "offset": offset}).fetchall()

            if not rows:
                break

            # Compute metrics for batch
            updates = []
            for r in rows:
                m = compute_metrics(r[1])
                updates.append({
                    "qid": r[0],
                    "wc": m["word_count"],
                    "uwc": m["unique_word_count"],
                    "awl": m["average_word_length"],
                    "rs": m["readability_score"],
                    "mc": m["morphology_complexity"],
                })

            # Batch UPDATE
            with engine.begin() as tx:
                for u in updates:
                    tx.execute(text(
                        "UPDATE question_bank SET "
                        "word_count = :wc, "
                        "unique_word_count = :uwc, "
                        "average_word_length = :awl, "
                        "readability_score = :rs, "
                        "morphology_complexity = :mc "
                        "WHERE id = :qid"
                    ), u)

            updated += len(rows)
            pct = updated / total * 100
            print(f"  [{pct:5.1f}%] {updated:,}/{total:,}")
            offset += args.batch_size

    t_total = time() - t0
    print(f"\n{'=' * 60}")
    print(f"Updated: {updated:,} questions in {t_total:.1f}s")

    # Verify
    with engine.connect() as conn:
        stats = conn.execute(text(
            "SELECT "
            "  AVG(word_count), AVG(unique_word_count), "
            "  AVG(average_word_length), AVG(readability_score), "
            "  AVG(morphology_complexity) "
            "FROM question_bank"
        )).fetchone()
        remaining = conn.execute(text(
            "SELECT COUNT(*) FROM question_bank WHERE word_count = 0"
        )).scalar()
        print(f"Remaining empty: {remaining:,}")
        print(f"Avg word_count: {stats[0]:.1f}")
        print(f"Avg unique_words: {stats[1]:.1f}")
        print(f"Avg word_length: {stats[2]:.2f}")
        print(f"Avg readability: {stats[3]:.1f}")
        print(f"Avg complexity: {stats[4]:.4f}")


if __name__ == "__main__":
    main()
