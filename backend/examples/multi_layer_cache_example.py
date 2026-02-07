"""
Multi-Layer Cache Usage Example
Task 7 - Requirements: 6.1, 6.2, 6.3, 6.5, 6.7, 6.10

Bu örnek, multi-layer cache sisteminin nasıl kullanılacağını gösterir.
"""

import asyncio
import hashlib
import json

from core.multi_layer_cache import MultiLayerCache, get_multi_layer_cache


async def example_basic_usage():
    """Basic cache usage example"""
    print("\n=== Basic Cache Usage ===\n")

    # Initialize cache
    cache = MultiLayerCache(
        redis_url="redis://localhost:6379/0",
        l1_max_size=100,
        default_ttl=3600,
        namespace="video_cache",
    )

    await cache.initialize()

    # Set value
    await cache.set(
        "user:123:profile",
        {"name": "Ahmet Yılmaz", "level": "orta", "subjects": ["matematik", "fizik"]},
    )

    # Get value (L1 hit)
    profile = await cache.get("user:123:profile")
    print(f"Profile: {profile}")

    # Get metrics
    metrics = cache.get_metrics()
    print(f"\nMetrics: {json.dumps(metrics, indent=2, ensure_ascii=False)}")

    await cache.close()


async def example_student_profile_cache():
    """
    Student profile caching example
    Req 6.1: Cache video önerilerini student profile hash'ine göre
    """
    print("\n=== Student Profile Cache ===\n")

    cache = await get_multi_layer_cache()

    # Student profile
    student_profile = {
        "goals": ["Matematik TYT", "Fizik TYT"],
        "currentLevel": {"matematik": 65, "fizik": 55},
        "learningStyle": "görsel",
    }

    # Generate cache key from profile hash
    profile_str = json.dumps(student_profile, sort_keys=True)
    profile_hash = hashlib.md5(profile_str.encode()).hexdigest()
    cache_key = f"video_rec:{profile_hash}"

    print(f"Profile hash: {profile_hash}")
    print(f"Cache key: {cache_key}")

    # Simulate video recommendations
    video_recommendations = [
        {
            "subject": "Matematik TYT",
            "videos": [
                {"title": "Üçgenler - Temel Kavramlar", "duration": 720},
                {"title": "Denklemler - Çözüm Yöntemleri", "duration": 900},
            ],
        },
        {
            "subject": "Fizik TYT",
            "videos": [
                {"title": "Hareket - Hız ve İvme", "duration": 600},
                {"title": "Kuvvet ve Enerji", "duration": 840},
            ],
        },
    ]

    # Cache recommendations (Req 6.3: TTL 1 hour)
    await cache.set(cache_key, video_recommendations, ttl=3600)
    print("\n✓ Video recommendations cached")

    # Retrieve from cache (Req 6.2: <100ms from L1)
    import time

    start = time.time()
    cached_recs = await cache.get(cache_key)
    elapsed_ms = (time.time() - start) * 1000

    print(f"\n✓ Retrieved from cache in {elapsed_ms:.2f}ms")
    print(f"Recommendations: {len(cached_recs)} subjects")

    # Show metrics
    metrics = cache.get_metrics()
    print(f"\nCache hit rate: {metrics['overall_hit_rate']}")

    await cache.close()


async def example_lru_eviction():
    """
    LRU eviction example
    Req 6.7: LRU eviction policy
    """
    print("\n=== LRU Eviction Example ===\n")

    # Small cache for demonstration
    cache = MultiLayerCache(
        redis_url="redis://localhost:6379/0",
        l1_max_size=5,  # Only 5 entries
        default_ttl=60,
        namespace="lru_demo",
    )

    await cache.initialize()

    # Fill cache
    print("Filling cache with 5 entries...")
    for i in range(5):
        await cache.set(f"key_{i}", f"value_{i}")

    print(f"L1 cache size: {cache.get_l1_stats()['size']}")

    # Access key_0 to make it recently used
    await cache.get("key_0")
    print("\n✓ Accessed key_0 (now most recently used)")

    # Add new entry (should evict key_1, the LRU)
    print("\nAdding key_5 (should evict LRU entry)...")
    await cache.set("key_5", "value_5")

    # Check which keys exist
    print("\nChecking keys:")
    for i in range(6):
        value = await cache.get(f"key_{i}")
        status = "✓ EXISTS" if value else "✗ EVICTED"
        print(f"  key_{i}: {status}")

    print(f"\nEvictions: {cache.metrics.evictions}")

    await cache.close()


async def example_cache_invalidation():
    """
    Cache invalidation example
    Req 6.5: Cache invalidation stratejisi
    """
    print("\n=== Cache Invalidation Example ===\n")

    cache = MultiLayerCache(
        redis_url="redis://localhost:6379/0",
        l1_max_size=100,
        namespace="invalidation_demo",
    )

    await cache.initialize()

    # Cache multiple user profiles
    print("Caching user profiles...")
    for user_id in [1, 2, 3]:
        await cache.set(
            f"user:{user_id}:profile", {"id": user_id, "name": f"User {user_id}"}
        )

    # Cache some products
    await cache.set("product:1", {"name": "Product 1"})
    await cache.set("product:2", {"name": "Product 2"})

    print("✓ Cached 3 user profiles and 2 products")

    # Invalidate all user profiles
    print("\nInvalidating all user profiles (user:*)...")
    await cache.invalidate_pattern("user:*")

    # Check what remains
    print("\nChecking cache:")
    print(
        f"  user:1:profile: {'EXISTS' if await cache.get('user:1:profile') else 'INVALIDATED'}"
    )
    print(
        f"  user:2:profile: {'EXISTS' if await cache.get('user:2:profile') else 'INVALIDATED'}"
    )
    print(f"  product:1: {'EXISTS' if await cache.get('product:1') else 'INVALIDATED'}")

    await cache.close()


async def example_get_or_compute():
    """
    Get or compute example
    Demonstrates cache-aside pattern
    """
    print("\n=== Get or Compute Example ===\n")

    cache = await get_multi_layer_cache()

    compute_count = 0

    async def expensive_computation():
        """Simulate expensive operation"""
        nonlocal compute_count
        compute_count += 1
        print(f"  → Computing (call #{compute_count})...")
        await asyncio.sleep(0.1)  # Simulate delay
        return {"result": "expensive_data", "computed_at": compute_count}

    # First call - should compute
    print("First call (cache miss):")
    result1 = await cache.get_or_compute("expensive_key", expensive_computation, ttl=60)
    print(f"  Result: {result1}")

    # Second call - should use cache
    print("\nSecond call (cache hit):")
    result2 = await cache.get_or_compute("expensive_key", expensive_computation, ttl=60)
    print(f"  Result: {result2}")

    print(f"\nTotal computations: {compute_count} (should be 1)")

    await cache.close()


async def example_async_operations():
    """
    Async operations example
    Req 6.10: Async cache güncelleme
    """
    print("\n=== Async Operations Example ===\n")

    cache = MultiLayerCache(
        redis_url="redis://localhost:6379/0", l1_max_size=100, namespace="async_demo"
    )

    await cache.initialize()

    # Concurrent cache operations
    print("Performing 10 concurrent cache operations...")

    import time

    start = time.time()

    tasks = []
    for i in range(10):
        task = cache.set(f"async_key_{i}", {"data": f"value_{i}"})
        tasks.append(task)

    await asyncio.gather(*tasks)

    elapsed = time.time() - start
    print(f"✓ Completed in {elapsed:.3f}s")

    # Verify all cached
    print("\nVerifying cached values...")
    for i in range(10):
        value = await cache.get(f"async_key_{i}")
        assert value is not None, f"Key async_key_{i} not found"

    print("✓ All values cached successfully")

    await cache.close()


async def example_performance_metrics():
    """Performance metrics example"""
    print("\n=== Performance Metrics Example ===\n")

    cache = MultiLayerCache(
        redis_url="redis://localhost:6379/0", l1_max_size=50, namespace="metrics_demo"
    )

    await cache.initialize()

    # Simulate workload
    print("Simulating workload...")

    # Cache some data
    for i in range(20):
        await cache.set(f"data_{i}", {"value": i})

    # Mix of hits and misses
    for i in range(30):
        key = f"data_{i % 25}"  # Some will miss
        await cache.get(key)

    # Get comprehensive metrics
    metrics = cache.get_metrics()
    l1_stats = cache.get_l1_stats()

    print("\n=== Cache Metrics ===")
    print(f"L1 Hits: {metrics['l1_hits']}")
    print(f"L1 Misses: {metrics['l1_misses']}")
    print(f"L1 Hit Rate: {metrics['l1_hit_rate']}")
    print(f"Overall Hit Rate: {metrics['overall_hit_rate']}")
    print(f"L1 Size: {metrics['l1_size']}/{metrics['l1_max_size']}")
    print(f"L1 Utilization: {metrics['l1_utilization']}")
    print(f"Promotions: {metrics['promotions']}")
    print(f"Evictions: {metrics['evictions']}")

    print("\n=== L1 Statistics ===")
    print(f"Total Accesses: {l1_stats['total_accesses']}")
    print(f"Avg Access Count: {l1_stats['avg_access_count']:.2f}")
    print(f"Total Size: {l1_stats['total_size_bytes']} bytes")

    await cache.close()


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Multi-Layer Cache System Examples")
    print("=" * 60)

    try:
        await example_basic_usage()
        await example_student_profile_cache()
        await example_lru_eviction()
        await example_cache_invalidation()
        await example_get_or_compute()
        await example_async_operations()
        await example_performance_metrics()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
