"""
Test Performance Improvement with Redis Caching
Compare response times before and after caching
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import time
import requests
from statistics import mean

BASE_URL = "http://localhost:9000"


def test_endpoint(name, url, iterations=5):
    """Test endpoint multiple times and measure response time"""
    times = []

    print(f"\n{name}:")
    print(f"URL: {url}")
    print(f"Testing {iterations} iterations...")

    for i in range(iterations):
        start = time.time()
        try:
            response = requests.get(url, timeout=10)
            elapsed = (time.time() - start) * 1000  # Convert to ms

            if response.status_code == 200:
                times.append(elapsed)
                status = "CACHED" if i > 0 and elapsed < 100 else "UNCACHED"
                print(f"  Iteration {i+1}: {elapsed:.2f}ms ({status})")
            else:
                print(f"  Iteration {i+1}: ERROR {response.status_code}")
        except Exception as e:
            print(f"  Iteration {i+1}: ERROR - {str(e)}")

    if times:
        first_call = times[0]
        cached_calls = times[1:] if len(times) > 1 else []
        avg_cached = mean(cached_calls) if cached_calls else 0

        print(f"\nResults:")
        print(f"  First call (uncached): {first_call:.2f}ms")
        if cached_calls:
            print(f"  Cached calls average: {avg_cached:.2f}ms")
            improvement = ((first_call - avg_cached) / first_call) * 100
            print(f"  Improvement: {improvement:.1f}% faster")

        return {
            "name": name,
            "first_call": first_call,
            "cached_avg": avg_cached,
            "improvement": improvement if cached_calls else 0,
            "times": times,
        }

    return None


def main():
    print("=" * 70)
    print("REDIS CACHING PERFORMANCE TEST")
    print("=" * 70)
    print(f"Backend: {BASE_URL}")
    print(f"Testing caching implementation...")

    # Test endpoints
    endpoints = [
        ("Health Check", f"{BASE_URL}/health"),
        (
            "Random Questions TYT",
            f"{BASE_URL}/api/v1/soru-bankasi/rastgele-sorular?sinav_tipi=TYT&soru_sayisi=2",
        ),
        (
            "Random Questions AYT",
            f"{BASE_URL}/api/v1/soru-bankasi/rastgele-sorular?sinav_tipi=AYT&soru_sayisi=1",
        ),
    ]

    results = []
    for name, url in endpoints:
        result = test_endpoint(name, url, iterations=5)
        if result:
            results.append(result)
        time.sleep(0.5)  # Small delay between tests

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY - CACHING PERFORMANCE")
    print("=" * 70)

    if results:
        print(f"\n{'Endpoint':<30} {'Uncached':<12} {'Cached':<12} {'Improvement':<12}")
        print("-" * 70)

        for r in results:
            print(
                f"{r['name']:<30} {r['first_call']:>10.2f}ms {r['cached_avg']:>10.2f}ms {r['improvement']:>10.1f}%"
            )

        # Overall stats
        total_first = sum(r["first_call"] for r in results)
        total_cached = sum(r["cached_avg"] for r in results)
        overall_improvement = (
            ((total_first - total_cached) / total_first) * 100 if total_first > 0 else 0
        )

        print("-" * 70)
        print(
            f"{'OVERALL AVERAGE':<30} {total_first/len(results):>10.2f}ms {total_cached/len(results):>10.2f}ms {overall_improvement:>10.1f}%"
        )

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

        # Expected targets
        print("\nExpected vs Actual:")
        print(
            f"  Target improvement: ~60-70% faster (from API_CONNECTIVITY_FINAL_REPORT.md)"
        )
        print(f"  Actual improvement: {overall_improvement:.1f}% faster")

        if overall_improvement >= 60:
            print(f"\n  Status: TARGET EXCEEDED! ({overall_improvement:.1f}% >= 60%)")
        elif overall_improvement >= 50:
            print(f"\n  Status: GOOD PERFORMANCE ({overall_improvement:.1f}%)")
        else:
            print(f"\n  Status: NEEDS INVESTIGATION ({overall_improvement:.1f}% < 50%)")


if __name__ == "__main__":
    main()
