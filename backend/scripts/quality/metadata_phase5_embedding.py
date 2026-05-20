#!/usr/bin/env python3
"""
Phase 5: Embedding backfill via Ollama nomic-embed-text (768-dim).

Idempotent: yalnızca embedding IS NULL satırları işler.
Bulk UPDATE + ThreadPoolExecutor paralel istek.

CLI:
  python metadata_phase5_embedding.py --limit 1000 --apply
  python metadata_phase5_embedding.py --limit 50000 --apply --parallel 4 --gold-only
"""

import argparse
import json
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DSN = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
EMBED_DIM = 768

# nomic-embed-text prefix: "search_document:" indexleme için, "search_query:" arama için
NOMIC_PREFIX = "search_document: "

# Thread-local storage (worker reuses its own opener)
_tls = threading.local()


def get_embedding(text: str):
    """nomic-embed-text → 768-dim vector. Returns list[float] or None."""
    if not text or not text.strip():
        return None
    prefixed = NOMIC_PREFIX + text[:2000]
    data = json.dumps({"model": EMBED_MODEL, "input": prefixed}).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/embed",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    embs = resp.get("embeddings", [])
    if not embs:
        return None
    emb = embs[0]
    if len(emb) != EMBED_DIM:
        return None
    return emb


def build_text(question_text, options):
    """Question text + non-null options birleşik metin."""
    parts = [question_text] if question_text else []
    parts.extend(o for o in options if o and o.strip())
    return " ".join(parts)


def worker(row):
    """Thread worker: embed single row, return result dict (no DB)."""
    qid, qt, oa, ob, oc, od, oe = row
    text = build_text(qt, [oa, ob, oc, od, oe])
    try:
        emb = get_embedding(text)
        if emb is None:
            return {"qid": qid, "ok": False, "reason": "empty_or_dim_mismatch"}
        return {"qid": qid, "ok": True, "emb": emb}
    except Exception as e:
        return {"qid": qid, "ok": False, "reason": f"{type(e).__name__}:{str(e)[:120]}"}


def bulk_write(writer_conn, results, model_name):
    """Bulk UPDATE embedding column. Per-row UPDATE in single transaction."""
    cur = writer_conn.cursor()
    success = 0
    failed = 0
    for r in results:
        if not r["ok"]:
            failed += 1
            continue
        try:
            cur.execute(
                """
                UPDATE question_bank
                SET embedding = %s::vector,
                    embedding_model = %s,
                    embedding_updated_at = NOW()
                WHERE id::text = %s
                """,
                (str(r["emb"]), model_name, r["qid"]),
            )
            success += 1
        except Exception as e:
            failed += 1
            print(f"  [db] update fail {r['qid'][:8]}: {str(e)[:100]}", flush=True)
    writer_conn.commit()
    return success, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1000, help="Max rows to process")
    ap.add_argument("--apply", action="store_true", help="Persist UPDATEs to DB")
    ap.add_argument("--parallel", type=int, default=3, help="Concurrent embed requests")
    ap.add_argument("--bulk-size", type=int, default=50, help="Bulk UPDATE batch size")
    ap.add_argument(
        "--gold-only",
        action="store_true",
        help="Filter to R4_rule_based_gold only",
    )
    args = ap.parse_args()

    conn = psycopg2.connect(DSN)
    cur = conn.cursor()

    gold_filter = (
        "AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'"
        if args.gold_only
        else ""
    )

    cur.execute(
        f"""
        SELECT id::text, question_text, option_a, option_b, option_c, option_d, option_e
        FROM question_bank q
        WHERE is_active = true
          AND question_text IS NOT NULL
          AND embedding IS NULL
          {gold_filter}
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (args.limit,),
    )
    rows = cur.fetchall()
    conn.close()

    print(
        f"[scan] {len(rows):,} rows to embed via {EMBED_MODEL} "
        f"(parallel={args.parallel}, bulk={args.bulk_size}, apply={args.apply})\n",
        flush=True,
    )

    if not rows:
        print("[done] no rows to process")
        return

    writer = psycopg2.connect(DSN) if args.apply else None

    success = 0
    failed = 0
    t_start = time.time()
    pending = []

    def flush():
        nonlocal success, failed
        if not pending:
            return
        if args.apply:
            s, f = bulk_write(writer, pending, EMBED_MODEL)
            success += s
            failed += f
        else:
            success += sum(1 for r in pending if r["ok"])
            failed += sum(1 for r in pending if not r["ok"])
        pending.clear()

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = {pool.submit(worker, row): row for row in rows}
        for f in as_completed(futures):
            result = f.result()
            pending.append(result)

            if len(pending) >= args.bulk_size:
                flush()
                elapsed = time.time() - t_start
                completed = success + failed
                rate = completed / elapsed * 60 if elapsed > 0 else 0
                print(
                    f"  [{completed}/{len(rows)}] success={success} "
                    f"failed={failed} rate={rate:.1f}/min",
                    flush=True,
                )

    flush()

    elapsed = time.time() - t_start
    rate = (success + failed) / elapsed * 60 if elapsed > 0 else 0
    print(
        f"\n[done] processed {len(rows)} | success={success} failed={failed} | "
        f"time={elapsed / 60:.1f}min | final_rate={rate:.1f}/min"
    )
    if writer:
        writer.close()


if __name__ == "__main__":
    main()
