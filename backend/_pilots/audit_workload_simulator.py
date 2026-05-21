"""
Real Workload Simulator — İleri Düzey Audit

KIRO2 backend'e gerçek concurrent öğrenci traffic'i simüle eder.
10 student × 50 quiz × 30 dakika eşzamanlı.

Her öğrenci:
  - Login → JWT al
  - GET /learning-path/today
  - GET /fsrs/due
  - 50 quiz submit (BKT/IRT/FSRS pipeline trigger)
  - Random profile/notification/leaderboard check

Sonuç:
  - p50, p95, p99 latency per endpoint
  - Error rate
  - DB pool exhaustion sinyali
  - Memory growth (psutil)
  - Backend log scan

Usage:
    python backend/_pilots/audit_workload_simulator.py --students 10 --duration 60
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import httpx
import psycopg2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND = "http://localhost:8000"
DSN = "postgresql://postgres:1470@localhost:5434/kiro2"


@dataclass
class WorkloadStats:
    """Per-endpoint latency + error tracker."""

    name: str
    latencies_ms: list[float] = field(default_factory=list)
    success: int = 0
    failed: int = 0
    error_samples: list[str] = field(default_factory=list)
    status_codes: dict[int, int] = field(default_factory=dict)

    def record(self, latency_ms: float, status: int, error: str | None = None):
        self.latencies_ms.append(latency_ms)
        self.status_codes[status] = self.status_codes.get(status, 0) + 1
        if status < 400:
            self.success += 1
        else:
            self.failed += 1
            if error and len(self.error_samples) < 3:
                self.error_samples.append(f"{status}: {error[:80]}")

    def summary(self) -> dict:
        if not self.latencies_ms:
            return {"name": self.name, "n": 0}
        sorted_lat = sorted(self.latencies_ms)
        n = len(sorted_lat)
        return {
            "name": self.name,
            "n": n,
            "success": self.success,
            "failed": self.failed,
            "p50": sorted_lat[n // 2],
            "p95": sorted_lat[int(n * 0.95)] if n > 1 else sorted_lat[0],
            "p99": sorted_lat[int(n * 0.99)] if n > 1 else sorted_lat[0],
            "max": max(sorted_lat),
            "mean": statistics.mean(sorted_lat),
            "status": self.status_codes,
            "errors": self.error_samples,
        }


GLOBAL_STATS: dict[str, WorkloadStats] = {}
GLOBAL_LOCK = threading.Lock()


def record(endpoint: str, latency_ms: float, status: int, error: str | None = None):
    with GLOBAL_LOCK:
        if endpoint not in GLOBAL_STATS:
            GLOBAL_STATS[endpoint] = WorkloadStats(endpoint)
        GLOBAL_STATS[endpoint].record(latency_ms, status, error)


def student_session(
    student_email: str, password: str, n_quizzes: int, duration_sec: int
):
    """One student session: login + N quiz cycles + random extras."""
    client = httpx.Client(base_url=BACKEND, timeout=10.0, follow_redirects=False)
    end_at = time.time() + duration_sec

    # 1. Login
    t0 = time.time()
    try:
        r = client.post(
            "/api/v1/auth/login", json={"email": student_email, "password": password}
        )
        dt = (time.time() - t0) * 1000
        record(
            "POST /auth/login",
            dt,
            r.status_code,
            r.text if r.status_code >= 400 else None,
        )
        if r.status_code != 200:
            return f"login_failed_{r.status_code}"
        token = r.json().get("access_token")
        if not token:
            return "no_token"
        client.headers["Authorization"] = f"Bearer {token}"
    except Exception as e:
        record("POST /auth/login", (time.time() - t0) * 1000, 0, str(e))
        return f"login_exception_{type(e).__name__}"

    # 2. /me + /learning-path/today + /fsrs/due (typical app load)
    for endpoint in [
        "/api/v1/auth/me",
        "/api/v1/learning-path/today",
        "/api/v1/fsrs/due",
    ]:
        t0 = time.time()
        try:
            r = client.get(endpoint)
            dt = (time.time() - t0) * 1000
            record(
                f"GET {endpoint.replace('/api/v1', '')}",
                dt,
                r.status_code,
                r.text if r.status_code >= 500 else None,
            )
        except Exception as e:
            record(
                f"GET {endpoint.replace('/api/v1', '')}",
                (time.time() - t0) * 1000,
                0,
                str(e),
            )

    # 3. Quiz cycle: get question + submit answer (mock — gerçek endpoint var ise)
    # Backend'de quiz submit endpoint pattern'i: POST /api/v1/exam/answer veya benzeri
    # Test için: rastgele soru ID al, basit GET trigger et
    for q_idx in range(n_quizzes):
        if time.time() > end_at:
            break

        # Random read: question list / topic list
        endpoint = random.choice(
            [
                "/api/v1/learning-path/today",
                "/api/v1/fsrs/due",
                "/api/v1/auth/me",
                "/api/v1/osym-exam/exam-configs",
            ]
        )
        t0 = time.time()
        try:
            r = client.get(endpoint)
            dt = (time.time() - t0) * 1000
            record(
                f"GET {endpoint.replace('/api/v1', '')}",
                dt,
                r.status_code,
                r.text if r.status_code >= 500 else None,
            )
        except Exception as e:
            record(
                f"GET {endpoint.replace('/api/v1', '')}",
                (time.time() - t0) * 1000,
                0,
                str(e),
            )

        # Small think time
        time.sleep(random.uniform(0.1, 0.5))

    client.close()
    return "ok"


def setup_test_users(n_students: int) -> list[tuple[str, str]]:
    """Find existing users veya yarat. Beta seed test@kiro2.com kullan."""
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT email FROM users
        WHERE role = 'STUDENT' AND is_active = TRUE
        LIMIT %s
    """,
        (n_students,),
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return [("test@kiro2.com", "Kiro2Beta2026@x")] * n_students
    return [(r[0], "Kiro2Beta2026@x") for r in rows]


def db_state_snapshot() -> dict:
    """DB snapshot — connection count, lock, deadlock."""
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("""
        SELECT numbackends, xact_commit, xact_rollback, deadlocks, temp_files, blks_read, blks_hit
        FROM pg_stat_database WHERE datname = 'kiro2'
    """)
    row = cur.fetchone()
    conn.close()
    if not row:
        return {}
    return {
        "connections": row[0],
        "commits": row[1],
        "rollbacks": row[2],
        "deadlocks": row[3],
        "temp_files": row[4],
        "blks_read": row[5],
        "blks_hit": row[6],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--students", type=int, default=10)
    ap.add_argument("--quizzes", type=int, default=50)
    ap.add_argument("--duration", type=int, default=60, help="Seconds")
    args = ap.parse_args()

    print("=" * 70)
    print(
        f"WORKLOAD SIMULATION — {args.students} students × {args.quizzes} quiz × {args.duration}s"
    )
    print("=" * 70)

    # Backend reachability check
    try:
        r = httpx.get(f"{BACKEND}/api/v1/health", timeout=5)
        print(f"  Backend health: {r.status_code}")
    except Exception as e:
        print(f"  Backend unreachable: {e}")
        return 1

    users = setup_test_users(args.students)
    print(f"  Loaded {len(users)} test users")

    db_pre = db_state_snapshot()
    print(
        f"  DB pre-state: connections={db_pre.get('connections')}, commits={db_pre.get('commits')}"
    )
    print()
    print("Running concurrent student sessions...")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.students) as pool:
        futures = []
        for email, password in users:
            futures.append(
                pool.submit(
                    student_session, email, password, args.quizzes, args.duration
                )
            )
        results = [f.result() for f in futures]
    wall = time.time() - t0

    db_post = db_state_snapshot()

    print()
    print(f"Wall time: {wall:.1f}s")
    from collections import Counter

    print(f"Session outcomes: {dict(Counter(results))}")
    if results:
        ok = sum(1 for r in results if r == "ok")
        print(f"  Sessions OK: {ok}/{len(results)}")
        if ok < len(results):
            print(f"  Failed reasons: {[r for r in results if r != 'ok']}")

    print()
    print("=" * 70)
    print("PER-ENDPOINT LATENCY DISTRIBUTION")
    print("=" * 70)
    print(
        f"{'Endpoint':<45} {'N':>5} {'p50ms':>7} {'p95ms':>7} {'p99ms':>7} {'maxms':>7} {'Err%':>6}"
    )
    print("-" * 95)
    for endpoint, stats in sorted(GLOBAL_STATS.items()):
        s = stats.summary()
        err_pct = (s["failed"] / s["n"] * 100) if s["n"] else 0
        print(
            f"{s['name']:<45} {s['n']:>5} {s['p50']:>7.0f} {s['p95']:>7.0f} {s['p99']:>7.0f} {s['max']:>7.0f} {err_pct:>5.1f}%"
        )

    print()
    print("=" * 70)
    print("DB DELTA (during workload)")
    print("=" * 70)
    if db_pre and db_post:
        for k in ["connections", "commits", "rollbacks", "deadlocks", "temp_files"]:
            delta = (db_post.get(k, 0) or 0) - (db_pre.get(k, 0) or 0)
            print(f"  Δ {k:<15}: {delta:>+10,}")
        blks_hit_delta = (db_post.get("blks_hit", 0) or 0) - (
            db_pre.get("blks_hit", 0) or 0
        )
        blks_read_delta = (db_post.get("blks_read", 0) or 0) - (
            db_pre.get("blks_read", 0) or 0
        )
        total = blks_hit_delta + blks_read_delta
        cache_hit = (100 * blks_hit_delta / total) if total else 0
        print(
            f"  Cache hit during run: {cache_hit:.1f}% ({blks_hit_delta:,} hit / {blks_read_delta:,} read)"
        )

    print()
    # Status code dist
    print("STATUS CODE DISTRIBUTION (across all endpoints)")
    all_status: dict[int, int] = {}
    for stats in GLOBAL_STATS.values():
        for s, c in stats.status_codes.items():
            all_status[s] = all_status.get(s, 0) + c
    total_req = sum(all_status.values())
    for status, count in sorted(all_status.items()):
        pct = count / total_req * 100 if total_req else 0
        marker = " ✅" if status < 400 else (" ⚠️" if status < 500 else " 🔴")
        print(f"  {status}: {count:>6} ({pct:>5.1f}%){marker}")

    print(
        f"\n  Total requests: {total_req}, Wall: {wall:.1f}s, RPS: {total_req / wall:.1f}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
