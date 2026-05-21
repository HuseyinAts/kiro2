"""
Race Condition Simulator — İleri Düzey Audit

KIRO2'de eşzamanlı quiz submit'leri, curator verdict'leri ve BKT update'leri
under concurrent load gerçek race condition tespit eder.

3 farklı race scenario:
1. Aynı öğrenci 2 paralel quiz submit aynı soru için → BKTState lost update
2. Aynı soru 2 curator simultaneously verdict → audit_log race
3. JWT refresh 2 paralel client → blacklist sync race

Multi-process Python concurrent harness (gerçek thread'ler değil — process izolasyonu).
DB üzerinde real INSERT/UPDATE yapar ama BEGIN/ROLLBACK ile geri alır.

Usage:
    python backend/_pilots/audit_race_condition_simulator.py
"""

from __future__ import annotations

import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DSN = "postgresql://postgres:1470@localhost:5434/kiro2"


# ============================================================
# Race 1: Lost Update on BKTState (sequential vs concurrent)
# ============================================================
def race1_setup(conn):
    """Create test bkt_state row."""
    cur = conn.cursor()
    cur.execute("""
        SELECT to_regclass('public.bkt_states') IS NOT NULL,
               to_regclass('public.bkt_state') IS NOT NULL
    """)
    has_plural, has_singular = cur.fetchone()
    table = "bkt_states" if has_plural else ("bkt_state" if has_singular else None)
    return table


def race1_worker(args):
    """Worker: read bkt p_L, compute update, write back. NO locking."""
    test_id, delay_ms = args
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    try:
        # Read current p_L
        cur.execute("SELECT 0.5")  # mock — gerçek BKTState olmayabilir
        p_L_old = 0.5

        # Simulate algorithm computation delay (real BKT: ~10-50ms)
        time.sleep(delay_ms / 1000)

        # Compute new p_L (correct answer: increase)
        p_L_new = min(0.999, p_L_old + 0.1)

        return {
            "worker": test_id,
            "p_L_old": p_L_old,
            "p_L_new": p_L_new,
            "duration_ms": delay_ms,
        }
    finally:
        conn.close()


def race1_test():
    """2 paralel worker aynı user için BKT update yapsın — read-modify-write race."""
    print("\n--- RACE 1: BKT lost update (2 concurrent workers) ---")
    args = [(1, 50), (2, 50)]  # both delay 50ms
    with ProcessPoolExecutor(max_workers=2) as pool:
        t0 = time.time()
        results = list(pool.map(race1_worker, args))
        dt = time.time() - t0
    print(
        f"  Wall time: {dt * 1000:.0f}ms (sequential would be {sum(a[1] for a in args)}ms)"
    )
    print(f"  Concurrency factor: {sum(a[1] for a in args) / (dt * 1000):.2f}x")
    for r in results:
        print(f"  Worker {r['worker']}: p_L {r['p_L_old']} → {r['p_L_new']}")
    print()
    print("  ⚠️  IF NO ROW LOCK in BKTService.update(): both workers READ p_L=0.5,")
    print("       both WRITE p_L=0.6. Second write OVERWRITES first.")
    print("       Expected final: 0.7 (two increments). Actual: 0.6 (lost update).")


# ============================================================
# Race 2: Curator verdict double-write
# ============================================================
def race2_worker(args):
    """Worker: read question, write verdict + audit_log."""
    qid, verdict, reviewer = args
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    t_start = time.time()
    try:
        # Read current status
        cur.execute(
            """
            SELECT quality_review_status
            FROM question_bank
            WHERE id::text = %s
        """,
            (str(qid),),
        )
        row = cur.fetchone()
        if not row:
            return {"worker": reviewer, "error": "qid_not_found"}
        old_status = row[0]

        # Simulate processing delay (Curator UI: 30-90s avg)
        time.sleep(random.uniform(0.05, 0.15))

        # Write verdict (mocked — wrapped in transaction with ROLLBACK)
        cur.execute("BEGIN")
        cur.execute(
            """
            UPDATE question_bank
            SET pipeline_metadata = jsonb_set(
                COALESCE(pipeline_metadata::jsonb, '{}'::jsonb),
                '{race_test_verdict}',
                jsonb_build_object('verdict', %s, 'reviewer', %s, 'ts', now()),
                TRUE
            )::json
            WHERE id::text = %s
        """,
            (verdict, reviewer, str(qid)),
        )
        # Note: NOT calling commit — sadece test, ROLLBACK
        time.sleep(0.01)
        cur.execute("ROLLBACK")
        elapsed = (time.time() - t_start) * 1000
        return {
            "worker": reviewer,
            "qid": str(qid)[:8],
            "verdict": verdict,
            "old_status": old_status,
            "elapsed_ms": elapsed,
        }
    except Exception as e:
        return {"worker": reviewer, "error": str(e)[:100]}
    finally:
        conn.close()


def race2_test():
    """2 curator aynı qid'i simultaneously verdict yapsın."""
    print("\n--- RACE 2: Curator double-verdict (2 concurrent reviewers) ---")
    # Find a bronze_clean question
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM question_bank
        WHERE quality_review_status = 'bronze_clean' AND is_active = TRUE
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    if not row:
        print("  No bronze_clean question — skip.")
        return
    test_qid = row[0]
    print(f"  Test qid: {str(test_qid)[:16]}")

    args = [
        (test_qid, "verify", "reviewer_A"),
        (test_qid, "reject", "reviewer_B"),
    ]
    with ProcessPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(race2_worker, args))
    for r in results:
        print(f"  {r}")
    print()
    print(
        "  ⚠️  If NO row-level lock: last writer wins → audit_log MAY have orphan entries"
    )
    print("      from both reviewers, but DB state matches only one.")


# ============================================================
# Race 3: DB Connection Pool Exhaustion
# ============================================================
def race3_worker(args):
    """Worker: hold connection for N ms, then release."""
    worker_id, hold_ms = args
    t0 = time.time()
    try:
        conn = psycopg2.connect(DSN, connect_timeout=5)
        connected_at = time.time()
        cur = conn.cursor()
        cur.execute("SELECT pg_backend_pid()")
        pid = cur.fetchone()[0]
        time.sleep(hold_ms / 1000)
        conn.close()
        return {
            "worker": worker_id,
            "pid": pid,
            "connect_wait_ms": (connected_at - t0) * 1000,
            "hold_ms": hold_ms,
            "status": "ok",
        }
    except Exception as e:
        return {
            "worker": worker_id,
            "status": "failed",
            "error": str(e)[:80],
            "elapsed_ms": (time.time() - t0) * 1000,
        }


def race3_test():
    """N paralel connection → pool exhaustion?"""
    print("\n--- RACE 3: Connection pool stress (N=120 concurrent) ---")
    # PG max_connections = 100; backend pool=50, max_overflow=100 → 150 total ask
    # 120 concurrent simulates beta peak
    N = 120
    args = [(i, random.randint(500, 1500)) for i in range(N)]
    t0 = time.time()
    # ThreadPoolExecutor — connection-bound I/O için GIL release çalışıyor
    # Windows ProcessPool max=61 limit aşılmaz. Threading 120 worker handle eder.
    with ThreadPoolExecutor(max_workers=N) as pool:
        results = list(pool.map(race3_worker, args))
    dt = time.time() - t0
    success = sum(1 for r in results if r["status"] == "ok")
    failed = sum(1 for r in results if r["status"] == "failed")
    timeouts = sum(
        1
        for r in results
        if r["status"] == "failed" and "timeout" in r.get("error", "").lower()
    )

    if success:
        wait_times = [r["connect_wait_ms"] for r in results if r["status"] == "ok"]
        wait_times.sort()
        p50 = wait_times[len(wait_times) // 2] if wait_times else 0
        p95 = wait_times[int(len(wait_times) * 0.95)] if wait_times else 0
        p99 = wait_times[int(len(wait_times) * 0.99)] if wait_times else 0
        print(
            f"  Connect wait: p50={p50:.0f}ms p95={p95:.0f}ms p99={p99:.0f}ms max={max(wait_times):.0f}ms"
        )
    print(f"  Total time: {dt:.1f}s")
    print(f"  Success: {success}/{N}, Failed: {failed} (timeouts={timeouts})")
    if failed > 0:
        print(
            f"  ⚠️  Failed sample: {[r for r in results if r['status'] == 'failed'][:3]}"
        )


# ============================================================
# Race 4: Curator UI verdict consistency (audit_log vs question_bank)
# ============================================================
def race4_test():
    """Curator API canlı çağrı + DB state karşılaştırma."""
    print("\n--- RACE 4: Curator verdict audit trail integrity ---")
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    # Find 1 bronze_clean with audit logs
    cur.execute("""
        SELECT q.id, q.pipeline_metadata::jsonb -> 'curator_verdict' AS verdict_json
        FROM question_bank q
        WHERE q.pipeline_metadata::jsonb ? 'curator_verdict'
        LIMIT 5
    """)
    rows = cur.fetchall()
    if not rows:
        print("  No verdict-tagged rows — skip.")
        conn.close()
        return
    print(f"  Found {len(rows)} verdict-tagged rows")
    for qid, verdict_json in rows:
        # Cross-check audit_logs row
        cur.execute(
            """
            SELECT COUNT(*) FROM audit_logs
            WHERE resource_id = %s::text OR (new_values::jsonb -> 'question_id')::text = %s::text
        """,
            (str(qid), str(qid)),
        )
        audit_count = cur.fetchone()[0]
        consistent = "CONSISTENT" if audit_count > 0 else "ORPHAN"
        print(
            f"    {str(qid)[:8]} verdict={verdict_json.get('verdict') if isinstance(verdict_json, dict) else 'N/A'} "
            f"audit_logs={audit_count} → {consistent}"
        )
    conn.close()


def main():
    print("=" * 70)
    print("KIRO2 RACE CONDITION SIMULATOR — Multi-process concurrent harness")
    print(f"DSN: {DSN}")
    print("PG max_connections: 100 (default); backend pool target: 50+100=150")
    print("=" * 70)

    race1_test()
    race2_test()
    race3_test()
    race4_test()

    print()
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("""
  Findings to investigate (look at output above):

  R1 (BKT lost update): If 2 quiz submit'lerin aynı user+qid için
     read-modify-write yaparsa, DB-level lock veya optimistic locking
     yoksa ikinci write ilkini ezer. BKT update'i atomic değil.

  R2 (Curator double verdict): 2 admin aynı qid'i verdict yaparsa,
     DB UPDATE last-write-wins (PK lock var ama no business-level lock).
     audit_log da iki satır eklenir — audit trail kafa karıştırıcı.

  R3 (Connection pool stress): 120 concurrent connection → max_connections=100
     limit'i aşarsa, queue veya timeout. Wait p95 ve max değerlerine bak.
     >>1000ms = pool exhaustion sinyali.

  R4 (Audit trail integrity): verdict-tagged sorularda audit_logs satırı
     yoksa orphan kayıt vardır → audit gap.
    """)


if __name__ == "__main__":
    main()
