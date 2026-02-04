"""Quick load test"""
import asyncio
import time
import httpx
import statistics

async def test_endpoint(url, num_requests=20):
    """Test single endpoint with concurrent requests"""
    async def single_request():
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                duration = (time.time() - start) * 1000
                return {"success": response.status_code == 200, "duration": duration}
        except Exception as e:
            return {"success": False, "duration": (time.time() - start) * 1000, "error": str(e)}

    # Run requests concurrently
    start_time = time.time()
    results = await asyncio.gather(*[single_request() for _ in range(num_requests)])
    total_time = time.time() - start_time

    # Calculate stats
    durations = [r['duration'] for r in results if r['success']]
    success_count = sum(1 for r in results if r['success'])

    return {
        "url": url,
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "avg_ms": statistics.mean(durations) if durations else 0,
        "min_ms": min(durations) if durations else 0,
        "max_ms": max(durations) if durations else 0,
        "median_ms": statistics.median(durations) if durations else 0,
        "total_time": total_time,
        "rps": len(results) / total_time if total_time > 0 else 0
    }

async def main():
    print("="*70)
    print("QUICK LOAD TEST")
    print("="*70)

    endpoints = [
        "http://localhost:8000/health",
        "http://localhost:8000/",
        "http://localhost:8000/api/v1/learning-style/hybrid-codes",
        "http://localhost:8000/api/v1/learning-style/statistics",
    ]

    for endpoint in endpoints:
        print(f"\n[TEST] {endpoint}")
        print("   Running 20 concurrent requests...")

        stats = await test_endpoint(endpoint, num_requests=20)

        print(f"   Success: {stats['success']}/{stats['total']}")
        print(f"   Avg: {stats['avg_ms']:.0f}ms")
        print(f"   Min: {stats['min_ms']:.0f}ms")
        print(f"   Max: {stats['max_ms']:.0f}ms")
        print(f"   Median: {stats['median_ms']:.0f}ms")
        print(f"   RPS: {stats['rps']:.1f}")

        if stats['avg_ms'] < 200:
            print(f"   [OK] EXCELLENT")
        elif stats['avg_ms'] < 500:
            print(f"   [WARN] ACCEPTABLE")
        else:
            print(f"   [FAIL] SLOW")

        await asyncio.sleep(1)

    print("\n" + "="*70)
    print("[OK] Load test completed!")

if __name__ == "__main__":
    asyncio.run(main())
