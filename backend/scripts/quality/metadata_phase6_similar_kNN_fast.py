#!/usr/bin/env python3
"""
Phase 6 FAST: similar_question_ids via numpy bulk cosine similarity.

pgvector HNSW + Python loop = 1.7s/row. Bunun yerine:
1. Tüm gold (~81K) embedding'i tek SELECT ile numpy array'e yükle (250MB)
2. Chunked matmul: similarity matrix per chunk (500 × 81K = 324MB)
3. argpartition ile top-K
4. Bulk UPDATE chunked

Hedef: <30 dakika.

CLI:
  python metadata_phase6_similar_kNN_fast.py --top-k 10 --chunk 500 --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DSN = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))


def fetch_embeddings():
    """Fetch all gold embeddings into numpy array."""
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    print("[phase6-fast] Fetching gold embeddings...")
    t0 = time.time()
    cur.execute(
        """
        SELECT id::text, embedding::text
        FROM question_bank
        WHERE is_active AND embedding IS NOT NULL
          AND pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
        ORDER BY id
        """
    )
    rows = cur.fetchall()
    conn.close()
    print(f"  fetched {len(rows):,} rows in {time.time() - t0:.1f}s")

    # Parse embeddings: "[0.12, -0.45, ...]" → np.array
    print("[phase6-fast] Parsing embeddings to numpy...")
    t0 = time.time()
    ids = [r[0] for r in rows]
    embs = np.zeros((len(rows), 768), dtype=np.float32)
    for i, (_, emb_str) in enumerate(rows):
        # Strip brackets, split by comma
        vals = emb_str.strip("[]").split(",")
        embs[i] = np.array(vals, dtype=np.float32)
        if (i + 1) % 10000 == 0:
            print(f"  parsed {i + 1:,}/{len(rows):,}", flush=True)
    # Normalize to unit vectors (for cosine = dot product)
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    embs_unit = embs / norms
    print(
        f"  parsed + normalized in {time.time() - t0:.1f}s "
        f"({embs_unit.nbytes / 1024 / 1024:.0f} MB)"
    )
    return ids, embs_unit


def compute_top_k(ids, embs, top_k, chunk_size):
    """Compute top-K similar for each row using chunked matmul."""
    n = len(ids)
    results = []  # (qid, [sim_id_1, ..., sim_id_K])
    print(f"[phase6-fast] Computing top-{top_k} for {n:,} rows, chunk={chunk_size}...")
    t0 = time.time()
    for cs in range(0, n, chunk_size):
        ce = min(cs + chunk_size, n)
        chunk = embs[cs:ce]  # (chunk_size, 768)
        # Cosine similarity = dot product (unit vectors)
        sims = chunk @ embs.T  # (chunk_size, n)
        # For each row in chunk, find top_k+1 (including self), exclude self
        # argpartition for unsorted top-K, then sort the K
        for i in range(ce - cs):
            global_idx = cs + i
            row_sims = sims[i]
            # Negate to use argpartition for descending
            top_indices = np.argpartition(-row_sims, top_k + 1)[: top_k + 1]
            # Sort these K+1 by descending similarity
            top_indices = top_indices[np.argsort(-row_sims[top_indices])]
            # Exclude self (global_idx)
            top_indices = top_indices[top_indices != global_idx][:top_k]
            sim_ids = [ids[j] for j in top_indices]
            results.append((ids[global_idx], sim_ids))
        if (ce % (chunk_size * 4) == 0) or ce == n:
            elapsed = time.time() - t0
            rate = ce / max(elapsed, 0.001)
            eta = (n - ce) / max(rate, 0.001)
            print(
                f"  [{ce}/{n}] elapsed={elapsed:.0f}s rate={rate:.0f}/s eta={eta:.0f}s",
                flush=True,
            )
    print(f"[phase6-fast] Top-K computation done in {time.time() - t0:.1f}s")
    return results


def bulk_update(results, write_chunk=1000):
    """Bulk UPDATE question_bank.similar_question_ids."""
    print(f"[phase6-fast] Bulk UPDATE {len(results):,} rows (chunk={write_chunk})...")
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    t0 = time.time()
    total = 0
    for cs in range(0, len(results), write_chunk):
        ce = min(cs + write_chunk, len(results))
        chunk = results[cs:ce]
        payload = [(json.dumps(sids), qid) for (qid, sids) in chunk]
        execute_values(
            cur,
            """
            UPDATE question_bank q SET similar_question_ids = v.sim::json
            FROM (VALUES %s) AS v(sim, qid)
            WHERE q.id::text = v.qid
            """,
            payload,
            template="(%s, %s)",
        )
        conn.commit()
        total += ce - cs
        if total % 5000 == 0 or ce == len(results):
            print(f"  written {total:,}/{len(results):,}", flush=True)
    conn.close()
    print(f"[phase6-fast] Bulk UPDATE done in {time.time() - t0:.1f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=500, help="Compute chunk size")
    ap.add_argument("--write-chunk", type=int, default=1000, help="Write chunk size")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    ids, embs = fetch_embeddings()
    results = compute_top_k(ids, embs, args.top_k, args.chunk)
    print(f"\n[phase6-fast] {len(results):,} top-K computed")
    print(f"  sample: {results[0][0][:8]} → {[s[:8] for s in results[0][1][:3]]}...")

    if args.apply:
        bulk_update(results, args.write_chunk)
    else:
        print("[phase6-fast] --apply not set; skipping DB writes")


if __name__ == "__main__":
    main()
