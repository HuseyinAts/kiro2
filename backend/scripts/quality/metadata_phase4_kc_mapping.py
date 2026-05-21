#!/usr/bin/env python3
"""
Phase 4: KC mapping + q_matrix from topic hierarchy.

Step 1: Seed knowledge_components table from topic_hierarchy
  - For each topic in hierarchy, create a KC with same ID
  - BKT params from defaults (will be refined later)

Step 2: Map question → KCs
  - Primary KC = primary_topic_id
  - Secondary KCs = from secondary_topics JSON
  - Insert into question_kc_mapping

Step 3: Build q_matrix
  - List of KC IDs this question tests (binary skill mask)
  - Store as JSON array in question_bank.q_matrix

Step 4: Update question_bank.kc_ids (denormalized for fast lookup)
"""

import json
import os
import sys

import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DSN = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()

    # Step 1: seed knowledge_components from topic_hierarchy
    print("[step 1] Seeding knowledge_components from topic_hierarchy...")
    cur.execute("""
        INSERT INTO knowledge_components (kc_id, kc_name, parent_topic_id, description,
                                          bkt_p_init, bkt_p_transit, bkt_p_guess, bkt_p_slip)
        SELECT
          id, name_tr, parent_id, COALESCE(description, name_tr),
          0.4, 0.12, 0.20, 0.10
        FROM topic_hierarchy
        ON CONFLICT (kc_id) DO NOTHING
    """)
    kc_inserted = cur.rowcount
    conn.commit()
    print(f"  knowledge_components inserted: {kc_inserted:,}")

    # Build topic_hierarchy lookups
    cur.execute("SELECT id, name_tr FROM topic_hierarchy")
    th_rows = cur.fetchall()
    name_to_id = {n.lower().strip(): i for (i, n) in th_rows if n}
    valid_kc_ids = {i for (i, _) in th_rows}
    print(
        f"  topic_hierarchy: name→id={len(name_to_id):,}  valid_kc_ids={len(valid_kc_ids):,}\n"
    )

    # Step 2 + 3 + 4: process questions
    print("\n[step 2-4] Processing questions...")
    cur.execute("""
        SELECT id::text, primary_topic_id, secondary_topics::text
        FROM question_bank
        WHERE is_active=true AND (kc_ids IS NULL OR q_matrix IS NULL)
    """)
    rows = cur.fetchall()
    print(f"[scan] {len(rows):,} rows to process")

    qk_inserts = []  # (question_id, kc_id, weight)
    qb_updates = []  # (qid, kc_ids_json, q_matrix_json)

    for r in rows:
        qid, primary, secondary_json = r
        kc_set = []
        # primary KC weight 1.0
        if primary:
            kc_set.append((primary, 1.0))
        # secondary topics weight 0.5 — resolve names to topic_ids via lookup
        if secondary_json:
            try:
                sec = json.loads(secondary_json)
                if isinstance(sec, list):
                    for s in sec:
                        tid = None
                        wt = 0.5
                        if isinstance(s, dict):
                            tid = s.get("topic_id") or s.get("id")
                            wt = float(s.get("weight", 0.5))
                            # Also try name resolution if id missing
                            if not tid and s.get("name"):
                                tid = name_to_id.get(s["name"].lower().strip())
                        elif isinstance(s, str):
                            # First try as id (if UUID-like) else resolve as name
                            if "-" in s and len(s) > 20:
                                tid = s
                            else:
                                tid = name_to_id.get(s.lower().strip())
                        if tid and tid != primary:
                            kc_set.append((tid, wt))
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass
        # Dedupe (keep highest weight)
        seen = {}
        for kc, w in kc_set:
            if kc not in seen or seen[kc] < w:
                seen[kc] = w
        kc_set = sorted(seen.items())

        kc_ids = [kc for kc, _ in kc_set]
        # q_matrix as binary skill mask
        q_matrix = {kc: 1 for kc, _ in kc_set}

        for kc, w in kc_set:
            # Only insert if kc_id is in knowledge_components (FK-safe)
            if kc in valid_kc_ids:
                qk_inserts.append((qid, kc, w))

        qb_updates.append(
            (
                qid,
                json.dumps(kc_ids, ensure_ascii=False),
                json.dumps(q_matrix, ensure_ascii=False),
            )
        )

    print(
        f"[compute done] {len(qk_inserts):,} KC mappings, {len(qb_updates):,} qb updates"
    )

    # Bulk insert into question_kc_mapping
    print("\n[apply step 2] question_kc_mapping bulk insert...")
    CHUNK = 10000
    for i in range(0, len(qk_inserts), CHUNK):
        batch = qk_inserts[i : i + CHUNK]
        # Filter: only insert if kc_id exists in knowledge_components
        execute_values(
            cur,
            """
            INSERT INTO question_kc_mapping (question_id, kc_id, weight)
            VALUES %s
            ON CONFLICT (question_id, kc_id) DO UPDATE SET weight = EXCLUDED.weight
            """,
            batch,
            page_size=10000,
        )
        conn.commit()
        if (i // CHUNK + 1) % 5 == 0 or i + CHUNK >= len(qk_inserts):
            print(
                f"  inserted {min(i + CHUNK, len(qk_inserts)):,}/{len(qk_inserts):,}",
                flush=True,
            )

    # Step 3+4: update kc_ids and q_matrix on question_bank
    print("\n[apply step 3+4] question_bank kc_ids + q_matrix update...")
    for i in range(0, len(qb_updates), CHUNK):
        batch = qb_updates[i : i + CHUNK]
        cur.execute("""
            CREATE TEMP TABLE _qb4 (
                qid VARCHAR PRIMARY KEY,
                kc_ids TEXT,
                q_matrix TEXT
            ) ON COMMIT DROP
        """)
        execute_values(cur, "INSERT INTO _qb4 VALUES %s", batch, page_size=10000)
        cur.execute("""
            UPDATE question_bank q
            SET kc_ids = b.kc_ids::json,
                q_matrix = b.q_matrix::json
            FROM _qb4 b WHERE q.id::text = b.qid
        """)
        conn.commit()
        print(
            f"  qb updated {min(i + CHUNK, len(qb_updates)):,}/{len(qb_updates):,}",
            flush=True,
        )

    print("\n[done]")
    conn.close()


if __name__ == "__main__":
    main()
