# Multi-Layer Cache System

**Task 7 - Requirements: 6.1, 6.2, 6.3, 6.5, 6.7, 6.10**

## Overview

Multi-layer cache sistemi, video öneri sisteminin performansını optimize etmek için tasarlanmış iki katmanlı bir cache çözümüdür.

### Architecture

```
Request Flow:
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  L1 Cache (In-Memory LRU)      │  ← Ultra-fast (<1ms)
│  - 100 entry limit              │
│  - OrderedDict (LRU)            │
│  - No network overhead          │
└──────┬──────────────────────────┘
       │ Miss
       ▼
┌─────────────────────────────────┐
│  L2 Cache (Redis)               │  ← Fast (~5-10ms)
│  - Persistent                   │
│  - Distributed                  │
│  - Larger capacity              │
└──────┬──────────────────────────┘
       │ Miss
       ▼
┌─────────────────────────────────┐
│  Source (Database/API)          │  ← Slow (100ms-3s)
│  - Compute/Fetch                │
│  - Cache result                 │
└─────────────────────────────────┘
```

### Key Features

1. **L1 Cache (Memory)**
   - In-memory LRU cache using OrderedDict
   - 100 entry limit (configurable)
   - Ultra-fast access (<1ms)
   - Automatic LRU eviction

2. **L2 Cache (Redis)**
   - Persistent, distributed cache
   - Larger capacity
   - Survives application restarts
   - Fast access (~5-10ms)

3. **Cache Promotion**
   - L2 hits automatically promoted to L1
   - Optimizes frequently accessed data

4. **TTL Management**
   - Default 1 hour TTL
   - Configurable per entry
   - Automatic expiration

5. **Cache Invalidation**
   - Single key deletion
   - Pattern-based invalidation
   - Namespace support

## Requirements Mapping

| Requirement | Implementation |
|-------------|----------------|
| **6.1** - Cache video önerilerini student profile hash'ine göre | ✓ Profile hash-based cache keys |
| **6.2** - Aynı profile için 100ms içinde dönme | ✓ L1 cache <1ms response time |
| **6.3** - Cache TTL 1 saat | ✓ Default TTL 3600 seconds |
| **6.5** - Cache invalidation stratejisi | ✓ Pattern-based invalidation |
| **6.7** - LRU eviction policy | ✓ OrderedDict-based LRU |
| **6.10** - Async cache güncelleme | ✓ Full async/await support |

## Usage

### Basic Usage

```python
from core.multi_layer_cache import MultiLayerCache

# Initialize cache
cache = MultiLayerCache(
    redis_url="redis://localhost:6379/0",
    l1_max_size=100,
    default_ttl=3600,
    namespace="video_cache"
)

await cache.initialize()

# Set value
await cache.set("key", {"data": "value"}, ttl=3600)

# Get value
value = await cache.get("key")

# Delete value
await cache.delete("key")

# Close connection
await cache.close()
```

### Student Profile Caching (Req 6.1)

```python
import hashlib
import json

# Generate cache key from student profile
student_profile = {
    "goals": ["Matematik TYT", "Fizik TYT"],
    "currentLevel": {"matematik": 65, "fizik": 55},
    "learningStyle": "görsel"
}

profile_str = json.dumps(student_profile, sort_keys=True)
profile_hash = hashlib.md5(profile_str.encode()).hexdigest()
cache_key = f"video_rec:{profile_hash}"

# Cache video recommendations
video_recommendations = [...]
await cache.set(cache_key, video_recommendations, ttl=3600)

# Retrieve (fast from L1)
cached_recs = await cache.get(cache_key)
```

### Get or Compute Pattern

```python
async def expensive_computation():
    # Expensive operation
    return await fetch_from_database()

# Get from cache or compute
result = await cache.get_or_compute(
    "expensive_key",
    expensive_computation,
    ttl=3600
)
```

### Cache Invalidation (Req 6.5)

```python
# Delete single key
await cache.delete("user:123:profile")

# Invalidate pattern
await cache.invalidate_pattern("user:*")

# Clear all
await cache.clear_all()
```

### Global Instance

```python
from core.multi_layer_cache import get_multi_layer_cache

# Get or create global instance
cache = await get_multi_layer_cache()

# Use cache
await cache.set("key", "value")
```

## Performance Characteristics

### Response Times

| Cache Layer | Typical Response Time | Use Case |
|-------------|----------------------|----------|
| L1 (Memory) | <1ms | Hot data, frequently accessed |
| L2 (Redis) | 5-10ms | Warm data, recently accessed |
| Source | 100ms-3s | Cold data, first access |

### Cache Hit Rates

Target hit rates:
- **L1 Hit Rate**: 60-70% (frequently accessed data)
- **L2 Hit Rate**: 20-30% (among L1 misses)
- **Overall Hit Rate**: 80-90% (combined L1+L2)

### Memory Usage

- **L1 Cache**: ~1-10 MB (100 entries, avg 10-100 KB each)
- **L2 Cache**: Limited by Redis configuration

## Monitoring

### Get Metrics

```python
metrics = cache.get_metrics()

print(f"L1 Hit Rate: {metrics['l1_hit_rate']}")
print(f"L2 Hit Rate: {metrics['l2_hit_rate']}")
print(f"Overall Hit Rate: {metrics['overall_hit_rate']}")
print(f"L1 Size: {metrics['l1_size']}/{metrics['l1_max_size']}")
print(f"Promotions: {metrics['promotions']}")
print(f"Evictions: {metrics['evictions']}")
```

### L1 Statistics

```python
l1_stats = cache.get_l1_stats()

print(f"Total Accesses: {l1_stats['total_accesses']}")
print(f"Avg Access Count: {l1_stats['avg_access_count']}")
print(f"Total Size: {l1_stats['total_size_bytes']} bytes")
```

## Configuration

### Environment Variables

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Cache settings
CACHE_L1_MAX_SIZE=100
CACHE_DEFAULT_TTL=3600
CACHE_NAMESPACE=video_cache
```

### Tuning Parameters

```python
cache = MultiLayerCache(
    redis_url="redis://localhost:6379/0",
    l1_max_size=100,      # L1 cache size (entries)
    default_ttl=3600,     # Default TTL (seconds)
    namespace="video_cache"  # Cache key namespace
)
```

## LRU Eviction Policy (Req 6.7)

L1 cache uses **Least Recently Used (LRU)** eviction:

1. Cache entries stored in OrderedDict
2. On access, entry moved to end (most recent)
3. When full, first entry (least recent) evicted
4. Evicted entries remain in L2 (Redis)

```python
# Example: LRU eviction
cache = MultiLayerCache(l1_max_size=5)

# Fill cache
for i in range(5):
    await cache.set(f"key_{i}", f"value_{i}")

# Access key_0 (now most recent)
await cache.get("key_0")

# Add key_5 (evicts key_1, the LRU)
await cache.set("key_5", "value_5")

# key_0 still in L1 (recently accessed)
# key_1 evicted from L1 (but still in L2)
```

## Error Handling

### Redis Connection Failure

Cache gracefully degrades to L1-only mode:

```python
await cache.initialize()  # Logs warning if Redis fails

# Cache still works with L1 only
await cache.set("key", "value")  # Works
value = await cache.get("key")   # Works
```

### Serialization Errors

Non-JSON-serializable objects are logged and skipped:

```python
# This will fail gracefully
await cache.set("key", some_complex_object)
# Returns False, logs error
```

## Best Practices

### 1. Use Profile Hashing for Cache Keys

```python
# Good: Deterministic hash
profile_hash = hashlib.md5(
    json.dumps(profile, sort_keys=True).encode()
).hexdigest()

# Bad: Non-deterministic
cache_key = f"profile_{random.random()}"
```

### 2. Set Appropriate TTLs

```python
# Short-lived data (5 minutes)
await cache.set("session", data, ttl=300)

# Medium-lived data (1 hour) - default
await cache.set("recommendations", data, ttl=3600)

# Long-lived data (24 hours)
await cache.set("static_content", data, ttl=86400)
```

### 3. Use Namespaces

```python
# Separate namespaces for different data types
video_cache = MultiLayerCache(namespace="video_cache")
user_cache = MultiLayerCache(namespace="user_cache")
```

### 4. Monitor Cache Performance

```python
# Regular monitoring
metrics = cache.get_metrics()

if metrics['overall_hit_rate'] < 70:
    logger.warning("Low cache hit rate", metrics=metrics)
```

### 5. Invalidate Stale Data

```python
# Invalidate on data update
async def update_user_profile(user_id, new_data):
    await db.update(user_id, new_data)
    await cache.delete(f"user:{user_id}:profile")
```

## Testing

Run tests:

```bash
cd backend
pytest tests/test_multi_layer_cache.py -v
```

Run examples:

```bash
cd backend
python examples/multi_layer_cache_example.py
```

## Integration with Video Recommendation Service

```python
from core.multi_layer_cache import get_multi_layer_cache

class VideoRecommendationService:
    def __init__(self):
        self.cache = None
    
    async def initialize(self):
        self.cache = await get_multi_layer_cache()
    
    async def get_recommendations(self, student_profile):
        # Generate cache key
        cache_key = self._generate_cache_key(student_profile)
        
        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Cache miss - compute recommendations
        recommendations = await self._compute_recommendations(student_profile)
        
        # Cache result
        await self.cache.set(cache_key, recommendations, ttl=3600)
        
        return recommendations
    
    def _generate_cache_key(self, profile):
        profile_str = json.dumps(profile, sort_keys=True)
        profile_hash = hashlib.md5(profile_str.encode()).hexdigest()
        return f"video_rec:{profile_hash}"
```

## Troubleshooting

### Low Cache Hit Rate

**Problem**: Overall hit rate < 70%

**Solutions**:
1. Increase L1 cache size
2. Increase TTL for stable data
3. Review cache key generation (ensure deterministic)
4. Check for cache invalidation issues

### High Memory Usage

**Problem**: L1 cache consuming too much memory

**Solutions**:
1. Reduce `l1_max_size`
2. Implement size-based eviction
3. Monitor entry sizes
4. Use compression for large values

### Redis Connection Issues

**Problem**: Redis connection failures

**Solutions**:
1. Check Redis server status
2. Verify connection URL
3. Check network connectivity
4. Review Redis logs
5. Cache will work in L1-only mode

## References

- [Redis Documentation](https://redis.io/documentation)
- [Python OrderedDict](https://docs.python.org/3/library/collections.html#collections.OrderedDict)
- [LRU Cache Algorithm](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU))
- [Cache-Aside Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)

## Changelog

### Version 1.0.0 (Task 7)
- Initial implementation
- L1 (Memory) + L2 (Redis) architecture
- LRU eviction policy
- TTL management
- Cache promotion
- Pattern-based invalidation
- Async/await support
- Comprehensive metrics
