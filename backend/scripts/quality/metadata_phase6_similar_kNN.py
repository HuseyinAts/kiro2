#!/usr/bin/env python3
"""
Phase 6: similar_question_ids[] via pgvector kNN.

Her gold sorunun embedding'i kullanılarak top-K (default 10) en benzer gold soru
ID'leri JSON array olarak `question_bank.similar_question_ids` kolonuna yazılır.

pgvector HNSW index (m=16, ef_construction=200) ile sorgu başına ~21ms.

CLI:
  python metadata_phase6_similar_kNN.py --top-k 10 --chunk 500 --apply
  python metadata_phase6_similar_kNN.py --top-k 10 --chunk 500  # dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DSN = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=10, help="Top K similar per question")
    ap.add_argument("--chunk", type=int, default=500, help="Chunk size for progress")
    ap.add_argument("--apply", action="store_true", help="Persist updates to DB")
    ap.add_argument("--limit", type=int, default=0, help="0 = all gold")
    args = ap.parse_args()

    conn = psycopg2.connect(DSN)
    cur = conn.cursor()

    print(f"[phase6] top_k={args.top_k} chunk={args.chunk} apply={args.apply}")

    # 1. Fetch gold question IDs (already embedded)
    where_limit = f"LIMIT {args.limit}" if args.limit > 0 else ""
    cur.execute(
        f"""
        SELECT q.id::text
        FROM question_bank q
        WHERE q.is_active
          AND q.embedding IS NOT NULL
          AND q.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
          AND q.similar_question_ids IS NULL
        ORDER BY q.id
        {where_limit}
        """
    )
    qids = [row[0] for row in cur.fetchall()]
    total = len(qids)
    print(f"[phase6] {total:,} pending gold questions to process")

    if not qids:
        print("[phase6] Nothing to do.")
        return

    t0 = time.time()
    success = 0
    fail = 0
    write_buf = []

    for idx, qid in enumerate(qids):
        # kNN: find top_k similar from same gold pool (excluding self)
        try:
            cur.execute(
                """
                SELECT q2.id::text
                FROM question_bank q2,
                     (SELECT embedding FROM question_bank WHERE id::text = %s) AS me
                WHERE q2.id::text != %s
                  AND q2.is_active
                  AND q2.embedding IS NOT NULL
                  AND q2.pipeline_metadata->'beta_filter_v1'->>'rule' = 'R4_rule_based_gold'
                ORDER BY q2.embedding <=> me.embedding
                LIMIT %s
                """,
                (qid, qid, args.top_k),
            )
            sim_ids = [r[0] for r in cur.fetchall()]
            if len(sim_ids) >= 1:
                write_buf.append((sim_ids, qid))
                success += 1
            else:
                fail += 1
        except Exception as e:
            fail += 1
            print(f"  [err] qid={qid[:8]}: {e}", flush=True)

        # Flush every chunk
        if (idx + 1) % args.chunk == 0 or (idx + 1) == total:
            elapsed = time.time() - t0
            rate = (idx + 1) / max(elapsed, 0.001)
            eta_sec = (total - (idx + 1)) / max(rate, 0.001)
            print(
                f"  [{idx + 1}/{total}] success={success:,} fail={fail:,} "
                f"rate={rate * 60:.1f}/min eta={eta_sec / 60:.1f}min",
                flush=True,
            )
            if args.apply and write_buf:
                # Bulk UPDATE
                execute_values(
                    cur,
                    """
                    UPDATE question_bank q SET similar_question_ids = v.sim::json
                    FROM (VALUES %s) AS v(sim, qid)
                    WHERE q.id::text = v.qid
                    """,
                    [(psycopg2.extras.Json(sids), q) for (sids, q) in write_buf],
                    template="(%s, %s)",
                )
                conn.commit()
                write_buf = []

    dt = time.time() - t0
    print(
        f"\n[phase6] Done. {success:,} updated, {fail:,} failed in {dt / 60:.1f}min "
        f"(avg {dt / max(success, 1) * 1000:.0f}ms/row)"
    )
    conn.close()


if __name__ == "__main__":
    main()
