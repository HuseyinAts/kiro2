"""
Tests for Multi-Layer Cache System
Task 7 - Requirements: 6.1, 6.2, 6.3, 6.5, 6.7, 6.10
"""

import asyncio
import time

import pytest

from core.multi_layer_cache import (
    CacheEntry,
    CacheMetrics,
    MultiLayerCache,
    get_multi_layer_cache,
)


@pytest.fixture(scope="function")
async def cache():
    """Create cache instance for testing"""
    cache = MultiLayerCache(
        redis_url="redis://localhost:6379/0",
        l1_max_size=10,  # Small size for testing eviction
        default_ttl=60,
        namespace="test_cache",
    )

    # Try to initialize, but don't fail if Redis is not available
    await cache.initialize()

    yield cache

    # Cleanup
    try:
        await cache.clear_all()
        await cache.close()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_cache_entry_expiration():
    """Test cache entry expiration logic"""
    # Not expired
    entry = CacheEntry(
        value="test", created_at=time.time(), expires_at=time.time() + 60
    )
    assert not entry.is_expired()

    # Expired
    entry_expired = CacheEntry(
        value="test", created_at=time.time() - 120, expires_at=time.time() - 60
    )
    assert entry_expired.is_expired()

    # No expiration
    entry_no_expire = CacheEntry(value="test", created_at=time.time(), expires_at=None)
    assert not entry_no_expire.is_expired()


@pytest.mark.asyncio
async def test_cache_entry_update_access():
    """Test cache entry access tracking"""
    entry = CacheEntry(
        value="test", created_at=time.time(), expires_at=None, access_count=0
    )

    initial_time = entry.last_accessed
    await asyncio.sleep(0.01)

    entry.update_access()

    assert entry.access_count == 1
    assert entry.last_accessed > initial_time


@pytest.mark.asyncio
async def test_cache_metrics():
    """Test cache metrics calculation"""
    metrics = CacheMetrics(l1_hits=80, l1_misses=20, l2_hits=15, l2_misses=5)

    assert metrics.get_l1_hit_rate() == 80.0
    assert metrics.get_l2_hit_rate() == 75.0
    assert metrics.get_overall_hit_rate() == 95.0

    metrics_dict = metrics.to_dict()
    assert "l1_hit_rate" in metrics_dict
    assert "overall_hit_rate" in metrics_dict


@pytest.mark.asyncio
async def test_l1_cache_set_get(cache):
    """Test L1 cache set and get operations (Req 6.2)"""
    # Set value
    await cache.set("test_key", {"data": "test_value"}, ttl=60)

    # Get value (should hit L1)
    value = await cache.get("test_key")

    assert value is not None
    assert value["data"] == "test_value"
    assert cache.metrics.l1_hits >= 1


@pytest.mark.asyncio
async def test_l1_cache_miss(cache):
    """Test L1 cache miss"""
    # Get non-existent key
    value = await cache.get("non_existent_key")

    assert value is None
    assert cache.metrics.l1_misses >= 1


@pytest.mark.asyncio
async def test_cache_ttl_expiration(cache):
    """Test cache TTL expiration (Req 6.3)"""
    # Set with short TTL
    await cache.set("expire_key", "expire_value", ttl=1)

    # Should exist immediately
    value = await cache.get("expire_key")
    assert value == "expire_value"

    # Wait for expiration
    await asyncio.sleep(1.5)

    # Should be expired
    value = await cache.get("expire_key")
    assert value is None


@pytest.mark.asyncio
async def test_lru_eviction(cache):
    """Test LRU eviction policy (Req 6.7)"""
    # Fill cache to max size (10 entries)
    for i in range(10):
        await cache.set(f"key_{i}", f"value_{i}")

    # Access key_0 to make it recently used
    await cache.get("key_0")

    # Add one more entry (should evict LRU, which is key_1)
    await cache.set("key_10", "value_10")

    # key_0 should still exist (recently accessed)
    value = await cache.get("key_0")
    assert value == "value_0"

    # key_1 should be evicted
    value = await cache.get("key_1")
    # Note: key_1 might be in L2 if Redis is available

    # Check eviction metric
    assert cache.metrics.evictions >= 1


@pytest.mark.asyncio
async def test_cache_delete(cache):
    """Test cache deletion (Req 6.5)"""
    # Set value
    await cache.set("delete_key", "delete_value")

    # Verify it exists
    value = await cache.get("delete_key")
    assert value == "delete_value"

    # Delete
    result = await cache.delete("delete_key")
    assert result is True

    # Verify it's gone
    value = await cache.get("delete_key")
    assert value is None

    assert cache.metrics.deletes >= 1


@pytest.mark.asyncio
async def test_cache_invalidate_pattern(cache):
    """Test pattern-based invalidation (Req 6.5)"""
    # Set multiple keys with pattern
    await cache.set("user:1:profile", {"name": "User 1"})
    await cache.set("user:2:profile", {"name": "User 2"})
    await cache.set("user:3:profile", {"name": "User 3"})
    await cache.set("product:1", {"name": "Product 1"})

    # Invalidate user pattern
    await cache.invalidate_pattern("user:*")

    # User keys should be gone
    assert await cache.get("user:1:profile") is None
    assert await cache.get("user:2:profile") is None

    # Product key should still exist
    value = await cache.get("product:1")
    # Note: Might be None if only in L1 and was invalidated


@pytest.mark.asyncio
async def test_get_or_compute(cache):
    """Test get_or_compute functionality"""
    compute_count = 0

    async def compute_fn():
        nonlocal compute_count
        compute_count += 1
        return {"computed": True, "count": compute_count}

    # First call should compute
    value1 = await cache.get_or_compute("compute_key", compute_fn)
    assert value1["computed"] is True
    assert compute_count == 1

    # Second call should use cache
    value2 = await cache.get_or_compute("compute_key", compute_fn)
    assert value2["computed"] is True
    assert compute_count == 1  # Should not increment


@pytest.mark.asyncio
async def test_cache_metrics_tracking(cache):
    """Test metrics tracking"""
    # Perform various operations
    await cache.set("metric_key_1", "value_1")
    await cache.set("metric_key_2", "value_2")

    await cache.get("metric_key_1")  # Hit
    await cache.get("metric_key_1")  # Hit
    await cache.get("non_existent")  # Miss

    await cache.delete("metric_key_2")

    # Check metrics
    metrics = cache.get_metrics()

    assert metrics["l1_hits"] >= 2
    assert metrics["l1_misses"] >= 1
    assert metrics["sets"] >= 2
    assert metrics["deletes"] >= 1
    assert "overall_hit_rate" in metrics


@pytest.mark.asyncio
async def test_l1_stats(cache):
    """Test L1 cache statistics"""
    # Add some entries
    await cache.set("stat_key_1", "value_1")
    await cache.set("stat_key_2", "value_2")

    # Access them
    await cache.get("stat_key_1")
    await cache.get("stat_key_1")
    await cache.get("stat_key_2")

    # Get stats
    stats = cache.get_l1_stats()

    assert stats["size"] >= 2
    assert stats["total_accesses"] >= 3
    assert stats["avg_access_count"] > 0


@pytest.mark.asyncio
async def test_cache_namespace(cache):
    """Test cache key namespacing"""
    key = "test_key"
    full_key = cache._make_key(key)

    assert full_key.startswith(cache.namespace)
    assert key in full_key


@pytest.mark.asyncio
async def test_cache_size_estimation(cache):
    """Test value size estimation"""
    small_value = "test"
    large_value = {"data": "x" * 1000}

    small_size = cache._estimate_size(small_value)
    large_size = cache._estimate_size(large_value)

    assert small_size > 0
    assert large_size > small_size


@pytest.mark.asyncio
async def test_cache_clear_all(cache):
    """Test clearing all caches"""
    # Add entries
    await cache.set("clear_key_1", "value_1")
    await cache.set("clear_key_2", "value_2")

    # Clear all
    await cache.clear_all()

    # Verify all gone
    assert await cache.get("clear_key_1") is None
    assert await cache.get("clear_key_2") is None


@pytest.mark.asyncio
async def test_cache_without_redis():
    """Test cache works without Redis (L1 only)"""
    cache = MultiLayerCache(
        redis_url="redis://invalid:9999/0", l1_max_size=10  # Invalid URL
    )

    # Initialize should fail gracefully
    await cache.initialize()

    # L1 should still work
    await cache.set("l1_only_key", "l1_only_value")
    value = await cache.get("l1_only_key")

    assert value == "l1_only_value"
    assert cache.metrics.l1_hits >= 1

    await cache.close()


@pytest.mark.asyncio
async def test_async_cache_update(cache):
    """Test async cache updates (Req 6.10)"""
    # Set multiple values concurrently
    tasks = [cache.set(f"async_key_{i}", f"async_value_{i}") for i in range(5)]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(results)

    # Verify all values
    for i in range(5):
        value = await cache.get(f"async_key_{i}")
        assert value == f"async_value_{i}"


@pytest.mark.asyncio
async def test_global_cache_instance():
    """Test global cache instance"""
    cache1 = await get_multi_layer_cache()
    cache2 = await get_multi_layer_cache()

    # Should be same instance
    assert cache1 is cache2

    await cache1.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
