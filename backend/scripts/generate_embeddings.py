#!/usr/bin/env python3
"""
Generate embeddings for question_bank using Ollama nomic-embed-text.

Uses batch processing with progress tracking and resume support.
Stores 768-dim vectors in pgvector embedding column.

Usage:
    cd backend
    python scripts/generate_embeddings.py [--batch-size 100] [--ollama-url http://localhost:11434]
"""

import argparse
import json
import os
import unicodedata
import urllib.request
from pathlib import Path
from time import time


def get_db_engine():
    """Create SQLAlchemy engine with correct DB URL."""
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:changeme@localhost:5434/kiro2",  # pragma: allowlist secret
    )
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgresql+aiopg://", "postgresql://")
    db_url = db_url.replace("/kiro2_db", "/kiro2")

    from sqlalchemy import create_engine

    return create_engine(db_url)


def generate_embeddings_batch(
    texts: list[str], ollama_url: str, model: str
) -> list[list[float]]:
    """Generate embeddings for a batch of texts via Ollama API."""
    data = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(
        f"{ollama_url}/api/embed",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read())

    if "error" in result:
        raise RuntimeError(f"Ollama error: {result['error']}")

    embeddings = result.get("embeddings")
    if not embeddings or not isinstance(embeddings, list):
        raise RuntimeError("Ollama returned invalid response: missing 'embeddings' key")

    return embeddings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate embeddings for question_bank"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Questions per Ollama batch (default: 100)",
    )
    parser.add_argument(
        "--ollama-url", default="http://localhost:11434", help="Ollama API URL"
    )
    parser.add_argument(
        "--model", default="nomic-embed-text", help="Embedding model name"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without changes"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of questions to process (0=all)",
    )
    args = parser.parse_args()

    from sqlalchemy import text

    engine = get_db_engine()

    print("=" * 60)
    print("Embedding Generation — nomic-embed-text (768d)")
    print("=" * 60)

    # Count questions without embeddings (resume support)
    with engine.connect() as conn:
        total_null = conn.execute(
            text("SELECT COUNT(*) FROM question_bank WHERE embedding IS NULL")
        ).scalar()
        total_all = conn.execute(text("SELECT COUNT(*) FROM question_bank")).scalar()

    already_done = total_all - total_null
    print(f"Total questions: {total_all:,}")
    print(f"Already embedded: {already_done:,}")
    print(f"Remaining: {total_null:,}")
    print(f"Batch size: {args.batch_size}")
    print(f"Model: {args.model}")

    if total_null == 0:
        print("\nAll questions already have embeddings!")
        return

    to_process = min(total_null, args.limit) if args.limit > 0 else total_null

    if args.dry_run:
        rate = 20.0  # estimated texts/sec
        est_min = to_process / rate / 60
        print(f"\n[DRY RUN] Would process {to_process:,} questions")
        print(f"Estimated time: ~{est_min:.0f} minutes at ~{rate:.0f} texts/sec")
        return

    # Fetch all IDs without embeddings upfront (parameterized LIMIT)
    with engine.connect() as conn:
        if args.limit > 0:
            all_rows = conn.execute(
                text(
                    "SELECT id, question_text FROM question_bank "
                    "WHERE embedding IS NULL ORDER BY id LIMIT :lim"
                ),
                {"lim": to_process},
            ).fetchall()
        else:
            all_rows = conn.execute(
                text(
                    "SELECT id, question_text FROM question_bank "
                    "WHERE embedding IS NULL ORDER BY id"
                )
            ).fetchall()

    print(f"\nProcessing {len(all_rows):,} questions...")
    t0 = time()
    processed = 0
    errors = 0
    skipped = 0

    for batch_start in range(0, len(all_rows), args.batch_size):
        batch = all_rows[batch_start : batch_start + args.batch_size]

        # Filter out empty/null texts (I6: avoid meaningless embeddings)
        valid = [(r[0], r[1]) for r in batch if r[1] and r[1].strip()]
        skipped += len(batch) - len(valid)
        if not valid:
            continue

        ids = [v[0] for v in valid]
        # NFC normalize and Turkish lowercase text before embedding (I4)
        try:
            from core.turkish_nlp_utils import normalize_tr

            texts = [
                normalize_tr(unicodedata.normalize("NFC", v[1]))[:2000] for v in valid
            ]
        except ImportError:
            # Fallback for standalone script execution without backend in PYTHONPATH
            import sys
            from pathlib import Path

            backend_dir = Path(__file__).parent.parent
            if str(backend_dir) not in sys.path:
                sys.path.insert(0, str(backend_dir))
            from core.turkish_nlp_utils import normalize_tr

            texts = [
                normalize_tr(unicodedata.normalize("NFC", v[1]))[:2000] for v in valid
            ]

        # Prefix with "search_document: " for nomic-embed-text
        prefixed_texts = [f"search_document: {t}" for t in texts]

        try:
            embeddings = generate_embeddings_batch(
                prefixed_texts, args.ollama_url, args.model
            )
        except Exception as e:
            print(f"\n  ERROR at batch {batch_start}: {e}")
            errors += len(valid)
            continue

        # Bulk write embeddings to DB (executemany for efficiency)
        params = [
            {"emb": "[" + ",".join(str(x) for x in emb) + "]", "qid": qid}
            for qid, emb in zip(ids, embeddings, strict=False)
        ]
        with engine.begin() as tx:
            tx.execute(
                text("UPDATE question_bank SET embedding = :emb WHERE id = :qid"),
                params,
            )

        processed += len(valid)
        elapsed = time() - t0
        rate = processed / max(elapsed, 0.001)
        remaining = (len(all_rows) - processed) / max(rate, 0.1)
        pct = processed / len(all_rows) * 100

        print(
            f"  [{pct:5.1f}%] {processed:,}/{len(all_rows):,} "
            f"({rate:.1f} q/s, ETA: {remaining/60:.1f}m)",
            end="\r",
        )

    t_total = time() - t0
    print(f"\n\n{'=' * 60}")
    print(f"Completed: {processed:,} embeddings in {t_total/60:.1f} minutes")
    if processed > 0 and t_total > 0:
        print(f"Rate: {processed/t_total:.1f} questions/sec")
    if errors:
        print(f"Errors: {errors:,}")
    if skipped:
        print(f"Skipped (empty text): {skipped:,}")

    # Final stats
    with engine.connect() as conn:
        null_remaining = conn.execute(
            text("SELECT COUNT(*) FROM question_bank WHERE embedding IS NULL")
        ).scalar()
    print(f"Remaining without embedding: {null_remaining:,}")


if __name__ == "__main__":
    main()
