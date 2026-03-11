"""
API Performance Benchmark Script
Measures response times for critical KIRO2 endpoints.

Usage:
    python scripts/benchmark_api.py [--base-url http://localhost:8000] [--rounds 5]

Requires:
    - Backend running at base_url
    - Seed data loaded (test@kiro2.com user)
"""

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone

import httpx


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_ROUNDS = 5
LOGIN_EMAIL = os.environ.get("BENCHMARK_EMAIL")
LOGIN_PASSWORD = os.environ.get("BENCHMARK_PASSWORD")

if not LOGIN_EMAIL or not LOGIN_PASSWORD:
    print("Error: BENCHMARK_EMAIL and BENCHMARK_PASSWORD env vars required")
    print("  Usage: BENCHMARK_EMAIL=x BENCHMARK_PASSWORD=y python scripts/benchmark_api.py")
    sys.exit(1)


ENDPOINTS = [
    {"method": "GET", "path": "/health", "auth": False, "name": "Health Check"},
    {"method": "GET", "path": "/sorular?limit=20", "auth": True, "name": "Questions (limit=20)"},
    {"method": "GET", "path": "/api/v1/student-dashboard/istatistikler", "auth": True, "name": "Dashboard Stats"},
    {"method": "GET", "path": "/api/v1/gamification/points", "auth": True, "name": "Gamification Points"},
    {"method": "GET", "path": "/api/v1/gamification/leaderboard?period=alltime&limit=10", "auth": True, "name": "Leaderboard"},
]


def login(client: httpx.Client, base_url: str) -> dict:
    """Login and return cookies/headers for auth."""
    resp = client.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
        follow_redirects=True,
    )
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("access_token") or data.get("token")
        if token:
            return {"Authorization": f"Bearer {token}"}
    # Try cookie-based auth (httpOnly cookie set by server)
    if resp.cookies:
        return {}  # Cookies auto-attached by client
    print(f"Login failed: {resp.status_code} {resp.text[:200]}")
    sys.exit(1)


def benchmark_endpoint(
    client: httpx.Client,
    base_url: str,
    endpoint: dict,
    auth_headers: dict,
    rounds: int,
) -> dict:
    """Benchmark a single endpoint."""
    url = f"{base_url}{endpoint['path']}"
    method = endpoint["method"]
    headers = auth_headers if endpoint["auth"] else {}

    times_ms = []
    errors = 0

    # Warm-up round (not measured)
    try:
        client.request(method, url, headers=headers, timeout=30.0)
    except Exception:
        pass

    # Measured rounds
    for _ in range(rounds):
        try:
            start = time.perf_counter()
            resp = client.request(method, url, headers=headers, timeout=30.0)
            elapsed = (time.perf_counter() - start) * 1000  # ms

            if resp.status_code < 400:
                times_ms.append(elapsed)
            else:
                errors += 1
                times_ms.append(elapsed)
        except Exception:
            errors += 1
            times_ms.append(30000)  # timeout marker

    result = {
        "name": endpoint["name"],
        "path": endpoint["path"],
        "method": method,
        "rounds": rounds,
        "errors": errors,
    }

    if times_ms:
        result["min_ms"] = round(min(times_ms), 1)
        result["avg_ms"] = round(statistics.mean(times_ms), 1)
        result["max_ms"] = round(max(times_ms), 1)
        result["p95_ms"] = round(sorted(times_ms)[int(len(times_ms) * 0.95)], 1) if len(times_ms) > 1 else round(times_ms[0], 1)
        result["pass"] = result["p95_ms"] < 2000  # <2s target
    else:
        result["min_ms"] = result["avg_ms"] = result["max_ms"] = result["p95_ms"] = None
        result["pass"] = False

    return result


def main():
    parser = argparse.ArgumentParser(description="KIRO2 API Benchmark")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    parser.add_argument("--output", help="JSON output file path")
    args = parser.parse_args()

    print(f"KIRO2 API Benchmark — {args.base_url} — {args.rounds} rounds")
    print("=" * 70)

    # Check backend is up
    try:
        resp = httpx.get(f"{args.base_url}/health", timeout=30.0)
        print(f"Backend: UP (status={resp.status_code})")
    except Exception:
        print(f"Backend: DOWN at {args.base_url}")
        sys.exit(1)

    with httpx.Client() as client:
        # Login
        print("Logging in...", end=" ")
        auth_headers = login(client, args.base_url)
        print("OK")
        print("=" * 70)

        # Run benchmarks
        results = []
        for ep in ENDPOINTS:
            result = benchmark_endpoint(client, args.base_url, ep, auth_headers, args.rounds)
            results.append(result)

            status = "PASS" if result["pass"] else "FAIL"
            print(
                f"[{status}] {result['name']:<25} "
                f"avg={result['avg_ms']:>7.1f}ms  "
                f"p95={result['p95_ms']:>7.1f}ms  "
                f"min={result['min_ms']:>7.1f}ms  "
                f"max={result['max_ms']:>7.1f}ms  "
                f"err={result['errors']}"
            )

    # Summary
    print("=" * 70)
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    print(f"Result: {passed}/{total} endpoints under 2s (p95)")

    # Save JSON
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "rounds": args.rounds,
        "results": results,
        "summary": {"passed": passed, "total": total},
    }

    output_path = args.output or "scripts/benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Report saved: {output_path}")


if __name__ == "__main__":
    main()
