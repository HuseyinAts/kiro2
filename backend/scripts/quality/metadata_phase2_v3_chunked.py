#!/usr/bin/env python3
"""Phase 2 v3: chunked bulk updates (5K rows per transaction)."""

import hashlib
import os
import random
import sys
import unicodedata
from math import exp, sqrt

import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
random.seed(42)

DSN = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")


def fisher_3pl(theta, a, b, c):
    if a <= 0:
        return 0.0
    z = a * (theta - b)
    try:
        p_star = 1.0 / (1.0 + exp(-z))
    except OverflowError:
        p_star = 1.0 if z > 0 else 0.0
    p = c + (1.0 - c) * p_star
    if p <= 0 or p >= 1:
        return 0.0
    return a * a * ((p - c) / (1.0 - c)) ** 2 * ((1 - p) / p)


def peak_info(a, b, c):
    if c == 0:
        return b, fisher_3pl(b, a, b, c)
    best_t, best_i = b, fisher_3pl(b, a, b, c)
    for d in range(1, 31):
        for s in (-1, 1):
            t = b + s * d * 0.1
            i = fisher_3pl(t, a, b, c)
            if i > best_i:
                best_i, best_t = i, t
    return best_t, best_i


def se_est(a, b, c, n):
    if n < 10:
        return 0.5, 1.5, 0.1
    _, imx = peak_info(a, b, c)
    return (
        round(0.4 / sqrt(n), 4),
        round(1.0 / sqrt(max(1.0, n * imx)), 4),
        round(0.05 / sqrt(n) if c > 0.01 else 0.0, 4),
    )


def canon_hash(qt, opts):
    parts = [unicodedata.normalize("NFC", qt or "").strip().lower()]
    for o in opts:
        parts.append(unicodedata.normalize("NFC", o or "").strip().lower())
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def variant():
    r = random.random()
    return "A" if r < 0.7 else ("B" if r < 0.9 else "C")


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("""
        SELECT id::text, irt_discrimination, irt_difficulty, COALESCE(irt_guessing, 0),
               COALESCE(irt_n_responses, 0), question_text,
               option_a, option_b, option_c, option_d, option_e
        FROM question_bank
        WHERE is_active=true AND irt_se_a IS NULL
          AND irt_discrimination IS NOT NULL AND irt_difficulty IS NOT NULL
    """)
    rows = cur.fetchall()
    print(f"[scan] {len(rows):,} rows needing IRT compute", flush=True)

    updates = []
    for r in rows:
        qid, a, b, c, n, qt, *opts = r
        a, b, c, n = float(a), float(b), float(c), int(n)
        sa, sb, sc = se_est(a, b, c, n)
        tp, ip = peak_info(a, b, c)
        ch = canon_hash(qt, opts)
        v = variant()
        m = "EAP_approx_3PL" if c > 0 else "EAP_approx_2PL"
        updates.append((qid, sa, sb, sc, m, round(ip, 4), round(tp, 4), ch, v))
    print(f"[compute done] {len(updates):,} updates", flush=True)

    CHUNK = 5000
    total_chunks = (len(updates) + CHUNK - 1) // CHUNK
    for i in range(0, len(updates), CHUNK):
        batch = updates[i : i + CHUNK]
        # Build VALUES list for ad-hoc table
        # Use execute_values with template trick: INSERT into temp, JOIN UPDATE
        cur.execute("""
            CREATE TEMP TABLE _b (
                qid VARCHAR PRIMARY KEY,
                sa NUMERIC, sb NUMERIC, sc NUMERIC, m VARCHAR,
                ip NUMERIC, tp NUMERIC, ch VARCHAR, v VARCHAR
            ) ON COMMIT DROP
        """)
        execute_values(
            cur,
            "INSERT INTO _b VALUES %s",
            batch,
            page_size=5000,
        )
        cur.execute("""
            UPDATE question_bank q
            SET irt_se_a = b.sa, irt_se_b = b.sb, irt_se_c = b.sc,
                irt_method_used = b.m,
                fisher_info_max = b.ip, fisher_info_theta = b.tp,
                canonical_form_id = b.ch, variant_id = b.v,
                metadata_filled_at = NOW()
            FROM _b b WHERE q.id::text = b.qid
        """)
        conn.commit()
        chunk_idx = i // CHUNK + 1
        print(
            f"  chunk {chunk_idx}/{total_chunks} ({cur.rowcount} updated)", flush=True
        )
    print("[done]", flush=True)
    conn.close()


if __name__ == "__main__":
    main()
