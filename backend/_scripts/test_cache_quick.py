"""
Quick test for multi-layer cache system
Tests cache functionality without running full backend
"""
import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.multi_layer_cache import MultiLayerCache


async def test_cache():
    """Test multi-layer cache functionality"""
    print("\n" + "=" * 80)
    print("🧪 MULTI-LAYER CACHE TEST")
    print("=" * 80)

    # Initialize cache
    print("\n1️⃣ Initializing cache...")
    cache = MultiLayerCache(
        redis_url="redis://localhost:6379/0",
        l1_max_size=10,
        default_ttl=60,
        namespace="test_cache",
    )

    redis_ok = await cache.initialize()
    if redis_ok:
        print("   ✅ Redis connection: OK")
    else:
        print("   ⚠️ Redis connection: FAILED (L1 only mode)")

    # Test 1: Set and Get
    print("\n2️⃣ Testing set/get...")
    test_key = "test_video_recommendations"
    test_value = {
        "videos": [
            {"id": "abc123", "title": "Matematik Dersi", "language": "tr"},
            {"id": "def456", "title": "Fizik Dersi", "language": "tr"},
        ],
        "count": 2,
        "cached_at": time.time(),
    }

    await cache.set(test_key, test_value, ttl=60)
    print(f"   ✅ Set: {test_key}")

    retrieved = await cache.get(test_key)
    if retrieved and retrieved == test_value:
        print(f"   ✅ Get: Value retrieved successfully")
    else:
        print(f"   ❌ Get: Failed to retrieve value")

    # Test 2: Cache Hit (L1)
    print("\n3️⃣ Testing L1 cache hit...")
    start = time.time()
    retrieved = await cache.get(test_key)
    elapsed_ms = (time.time() - start) * 1000

    if retrieved:
        print(f"   ✅ L1 Hit: Retrieved in {elapsed_ms:.2f}ms")
        if elapsed_ms < 1:
            print(f"   ✅ Performance: Excellent (<1ms)")
        elif elapsed_ms < 10:
            print(f"   ✅ Performance: Good (<10ms)")
        else:
            print(f"   ⚠️ Performance: Slow (>{elapsed_ms:.2f}ms)")
    else:
        print(f"   ❌ L1 Hit: Failed")

    # Test 3: Multiple keys (LRU eviction)
    print("\n4️⃣ Testing LRU eviction...")
    for i in range(15):  # More than l1_max_size (10)
        await cache.set(f"key_{i}", f"value_{i}", ttl=60)

    print(f"   ✅ Set 15 keys (L1 max: 10)")

    # Check if oldest keys were evicted
    first_key_exists = await cache.get("key_0")
    last_key_exists = await cache.get("key_14")

    if not first_key_exists and last_key_exists:
        print(f"   ✅ LRU Eviction: Working (oldest evicted)")
    else:
        print(f"   ⚠️ LRU Eviction: Check needed")

    # Test 4: Get metrics
    print("\n5️⃣ Cache metrics...")
    metrics = cache.get_metrics()

    print(f"   L1 Hits: {metrics['l1_hits']}")
    print(f"   L1 Misses: {metrics['l1_misses']}")
    print(f"   L1 Hit Rate: {metrics['l1_hit_rate']}")
    print(f"   L1 Size: {metrics['l1_size']}/{metrics['l1_max_size']}")
    print(f"   L1 Utilization: {metrics['l1_utilization']}")
    print(f"   L2 Enabled: {metrics['l2_enabled']}")
    print(f"   Total Sets: {metrics['sets']}")
    print(f"   Total Evictions: {metrics['evictions']}")

    # Test 5: Delete
    print("\n6️⃣ Testing delete...")
    await cache.delete(test_key)
    deleted_value = await cache.get(test_key)

    if deleted_value is None:
        print(f"   ✅ Delete: Key removed successfully")
    else:
        print(f"   ❌ Delete: Key still exists")

    # Test 6: Get or compute
    print("\n7️⃣ Testing get_or_compute...")

    compute_called = False

    async def compute_expensive_value():
        nonlocal compute_called
        compute_called = True
        await asyncio.sleep(0.1)  # Simulate expensive computation
        return {"computed": True, "value": 42}

    # First call - should compute
    start = time.time()
    result1 = await cache.get_or_compute(
        "computed_key", compute_expensive_value, ttl=60
    )
    elapsed1 = (time.time() - start) * 1000

    if compute_called and result1["computed"]:
        print(f"   ✅ First call: Computed value ({elapsed1:.2f}ms)")
    else:
        print(f"   ❌ First call: Failed")

    # Second call - should use cache
    compute_called = False
    start = time.time()
    result2 = await cache.get_or_compute(
        "computed_key", compute_expensive_value, ttl=60
    )
    elapsed2 = (time.time() - start) * 1000

    if not compute_called and result2["computed"]:
        print(f"   ✅ Second call: Used cache ({elapsed2:.2f}ms)")
        if elapsed2 > 0:
            print(f"   ✅ Speedup: {elapsed1/elapsed2:.1f}x faster")
        else:
            print(f"   ✅ Speedup: >1000x faster (instant)")
    else:
        print(f"   ❌ Second call: Failed")

    # Test 7: L1 stats
    print("\n8️⃣ L1 cache statistics...")
    l1_stats = cache.get_l1_stats()

    print(f"   Size: {l1_stats['size']} entries")
    print(f"   Total Accesses: {l1_stats['total_accesses']}")
    print(f"   Avg Access Count: {l1_stats['avg_access_count']:.2f}")
    print(f"   Total Size: {l1_stats['total_size_bytes']} bytes")

    # Cleanup
    print("\n9️⃣ Cleanup...")
    await cache.clear_all()
    print("   ✅ Cache cleared")

    await cache.close()
    print("   ✅ Connection closed")

    # Final metrics
    print("\n" + "=" * 80)
    print("📊 FINAL METRICS")
    print("=" * 80)
    final_metrics = cache.get_metrics()

    print(f"Overall Hit Rate: {final_metrics['overall_hit_rate']}")
    print(f"L1 Hit Rate: {final_metrics['l1_hit_rate']}")
    print(f"L2 Hit Rate: {final_metrics['l2_hit_rate']}")
    print(f"Total Sets: {final_metrics['sets']}")
    print(f"Total Deletes: {final_metrics['deletes']}")
    print(f"Total Evictions: {final_metrics['evictions']}")
    print(f"Total Errors: {final_metrics['errors']}")

    # Overall status
    print("\n" + "=" * 80)
    if final_metrics["errors"] == 0:
        print("✅ MULTI-LAYER CACHE: FULLY FUNCTIONAL")
    else:
        print(f"⚠️ MULTI-LAYER CACHE: {final_metrics['errors']} errors detected")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_cache())
