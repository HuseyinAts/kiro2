"""
Metrics Collector Usage Example
Demonstrates how to use the MetricsCollector for video API monitoring
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.metrics_collector import get_metrics_collector


async def simulate_video_requests():
    """Simulate video recommendation requests with metrics tracking"""

    # Get the global metrics collector
    metrics_collector = get_metrics_collector()

    print("=" * 80)
    print("Video API Metrics Collection Example")
    print("=" * 80)
    print()

    # Simulate 20 video requests
    print("Simulating 20 video recommendation requests...")
    print()

    for i in range(20):
        request_id = f"example-request-{i}"

        # Start request tracking
        metrics_collector.start_request(request_id)

        # Simulate request processing (50-200ms)
        processing_time = 0.05 + (i % 4) * 0.05
        await asyncio.sleep(processing_time)

        # Determine success/failure (90% success rate)
        success = i < 18

        # Determine cache hit/miss (70% cache hit rate)
        cache_hit = i % 10 < 7

        # End request tracking
        metrics_collector.end_request(
            request_id=request_id, success=success, cache_hit=cache_hit
        )

        # Record error if failed
        if not success:
            error_type = "TimeoutError" if i == 18 else "NetworkError"
            metrics_collector.record_error(request_id=request_id, error_type=error_type)

        # Simulate YouTube API calls (only on cache miss)
        if not cache_hit:
            metrics_collector.record_youtube_api_call(quota_cost=1)

        print(
            f"  Request {i+1}/20: {'✓' if success else '✗'} "
            f"({'cache hit' if cache_hit else 'cache miss'}) "
            f"- {processing_time*1000:.0f}ms"
        )

    print()
    print("-" * 80)
    print("Metrics Summary")
    print("-" * 80)
    print()

    # Get metrics snapshot
    snapshot = metrics_collector.get_snapshot()

    print(f"Total Requests:        {snapshot.total_requests}")
    print(f"Successful Requests:   {snapshot.successful_requests}")
    print(f"Failed Requests:       {snapshot.failed_requests}")
    print(
        f"Success Rate:          {(snapshot.successful_requests/snapshot.total_requests)*100:.1f}%"
    )
    print()

    print(f"Cache Hits:            {snapshot.cache_hits}")
    print(f"Cache Misses:          {snapshot.cache_misses}")
    print(f"Cache Hit Rate:        {snapshot.cache_hit_rate*100:.1f}%")
    print()

    print(f"Avg Response Time:     {snapshot.avg_response_time*1000:.2f}ms")
    print(f"P50 Response Time:     {snapshot.p50_response_time*1000:.2f}ms")
    print(f"P95 Response Time:     {snapshot.p95_response_time*1000:.2f}ms")
    print(f"P99 Response Time:     {snapshot.p99_response_time*1000:.2f}ms")
    print()

    print(f"YouTube API Quota:     {snapshot.youtube_api_quota_used} / 10000")
    print(f"Error Rate:            {snapshot.error_rate*100:.1f}%")
    print()

    # Get response time percentiles
    percentiles = metrics_collector.get_response_time_percentiles()
    print("Response Time Distribution:")
    print(f"  P50 (median):        {percentiles['p50']*1000:.2f}ms")
    print(f"  P95:                 {percentiles['p95']*1000:.2f}ms")
    print(f"  P99:                 {percentiles['p99']*1000:.2f}ms")
    print()

    print("-" * 80)
    print("Prometheus Metrics Export")
    print("-" * 80)
    print()

    # Get Prometheus metrics
    prometheus_metrics = metrics_collector.get_prometheus_metrics()

    # Show first 500 characters
    metrics_preview = prometheus_metrics.decode("utf-8")[:500]
    print(metrics_preview)
    print("...")
    print()

    print(f"Total metrics size: {len(prometheus_metrics)} bytes")
    print()

    print("=" * 80)
    print("Metrics collection example completed!")
    print("=" * 80)
    print()
    print("To access metrics in production:")
    print("  - Prometheus format: GET /api/youtube/metrics/prometheus")
    print("  - JSON snapshot:     GET /api/youtube/metrics/snapshot")
    print()


async def demonstrate_cache_operations():
    """Demonstrate cache operation tracking"""

    metrics_collector = get_metrics_collector()

    print("=" * 80)
    print("Cache Operations Tracking Example")
    print("=" * 80)
    print()

    # Simulate cache operations
    print("Simulating cache operations...")

    for i in range(10):
        metrics_collector.record_cache_operation("get")
        if i % 3 == 0:
            metrics_collector.record_cache_operation("set")
        if i % 5 == 0:
            metrics_collector.record_cache_operation("delete")

    # Update cache size
    metrics_collector.update_cache_size(150)

    print("  - 10 cache GET operations")
    print("  - 4 cache SET operations")
    print("  - 2 cache DELETE operations")
    print("  - Cache size updated to 150 entries")
    print()

    print("Cache operations tracked successfully!")
    print()


async def demonstrate_youtube_quota_tracking():
    """Demonstrate YouTube API quota tracking"""

    metrics_collector = get_metrics_collector()

    print("=" * 80)
    print("YouTube API Quota Tracking Example")
    print("=" * 80)
    print()

    # Simulate YouTube API calls with different costs
    print("Simulating YouTube API calls...")
    print()

    api_calls = [
        ("search", 100),
        ("video details", 1),
        ("channel info", 1),
        ("search", 100),
        ("video details", 1),
    ]

    for operation, cost in api_calls:
        metrics_collector.record_youtube_api_call(quota_cost=cost)
        print(f"  - {operation}: {cost} quota units")

    print()

    snapshot = metrics_collector.get_snapshot()
    quota_used = snapshot.youtube_api_quota_used
    quota_limit = 10000
    quota_percentage = (quota_used / quota_limit) * 100

    print(f"Total quota used: {quota_used} / {quota_limit} ({quota_percentage:.1f}%)")
    print()

    if quota_percentage >= 80:
        print("⚠️  WARNING: YouTube API quota is above 80%!")
    else:
        print("✓ YouTube API quota is within safe limits")

    print()


async def main():
    """Main example runner"""

    # Run all examples
    await simulate_video_requests()
    await demonstrate_cache_operations()
    await demonstrate_youtube_quota_tracking()

    print("=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
