#!/usr/bin/env python3
"""
Phase 2 v2: Bulk UPDATE via VALUES (much faster).

Reads all rows, computes metadata, dumps to TEMP TABLE, then JOIN UPDATE.
~100x faster than row-by-row UPDATE.
"""

import argparse
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


def fisher_info_3pl(theta, a, b, c):
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
    q = 1.0 - p
    return a * a * ((p - c) / (1.0 - c)) ** 2 * (q / p)


def fisher_info_peak(a, b, c):
    if c == 0:
        return b, fisher_info_3pl(b, a, b, c)
    best_theta = b
    best_info = fisher_info_3pl(b, a, b, c)
    for delta in range(1, 31):
        for sign in (-1, 1):
            theta = b + sign * delta * 0.1
            info = fisher_info_3pl(theta, a, b, c)
            if info > best_info:
                best_info = info
                best_theta = theta
    return best_theta, best_info


def estimate_se(a, b, c, n):
    if n < 10:
        return 0.5, 1.5, 0.1
    _, i_max = fisher_info_peak(a, b, c)
    se_a = 0.4 / sqrt(n)
    se_b = 1.0 / sqrt(max(1.0, n * i_max))
    se_c = 0.05 / sqrt(n) if c > 0.01 else 0.0
    return round(se_a, 4), round(se_b, 4), round(se_c, 4)


def canonical_hash(qt, opts):
    parts = [unicodedata.normalize("NFC", qt or "").strip().lower()]
    for o in opts:
        parts.append(unicodedata.normalize("NFC", o or "").strip().lower())
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assign_variant():
    r = random.random()
    return "A" if r < 0.7 else ("B" if r < 0.9 else "C")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--only-missing",
        action="store_true",
        help="Skip rows where irt_se_a already set",
    )
    args = ap.parse_args()

    print("[query] active rows with IRT params...")
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    where = "WHERE is_active=true AND irt_discrimination IS NOT NULL AND irt_difficulty IS NOT NULL"
    if args.only_missing:
        where += " AND irt_se_a IS NULL"
    cur.execute(f"""
        SELECT id::text, irt_discrimination, irt_difficulty, COALESCE(irt_guessing, 0),
               COALESCE(irt_n_responses, 0),
               question_text, option_a, option_b, option_c, option_d, option_e
        FROM question_bank {where}
    """)
    rows = cur.fetchall()
    print(f"[scan] {len(rows):,} candidate rows\n")

    print("[compute] generating updates...")
    updates = []
    for r in rows:
        qid, a, b, c, n, qt, oa, ob, oc, od, oe = r
        a, b, c, n = float(a), float(b), float(c), int(n)
        se_a, se_b, se_c = estimate_se(a, b, c, n)
        tp, ip = fisher_info_peak(a, b, c)
        canon = canonical_hash(qt, (oa, ob, oc, od, oe))
        variant = assign_variant()
        method = "EAP_approx_3PL" if c > 0 else "EAP_approx_2PL"
        updates.append(
            (qid, se_a, se_b, se_c, method, round(ip, 4), round(tp, 4), canon, variant)
        )
    print(f"[done] {len(updates):,} updates ready")

    if not args.apply:
        print("[dry-run] Pass --apply")
        return

    print("[apply] CREATE TEMP TABLE + bulk insert + JOIN UPDATE...")
    cur.execute("""
        CREATE TEMP TABLE _meta_phase2 (
            qid VARCHAR PRIMARY KEY,
            se_a NUMERIC, se_b NUMERIC, se_c NUMERIC,
            method VARCHAR, ip NUMERIC, tp NUMERIC,
            canon VARCHAR, variant VARCHAR
        ) ON COMMIT DROP
    """)
    print("  TEMP TABLE created")
    execute_values(
        cur,
        "INSERT INTO _meta_phase2 (qid, se_a, se_b, se_c, method, ip, tp, canon, variant) VALUES %s",
        updates,
        page_size=5000,
    )
    print(f"  Inserted {cur.rowcount:,} rows into TEMP")

    cur.execute("""
        UPDATE question_bank q
        SET irt_se_a = m.se_a,
            irt_se_b = m.se_b,
            irt_se_c = m.se_c,
            irt_method_used = m.method,
            fisher_info_max = m.ip,
            fisher_info_theta = m.tp,
            canonical_form_id = m.canon,
            variant_id = m.variant,
            metadata_filled_at = NOW()
        FROM _meta_phase2 m
        WHERE q.id::text = m.qid
    """)
    print(f"  UPDATE affected {cur.rowcount:,} rows")
    conn.commit()
    print("[done]")
    conn.close()


if __name__ == "__main__":
    main()
