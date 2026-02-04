"""Quick Redis connection test without emoji characters"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from core.redis_cache import RedisCache

# Test connection
cache = RedisCache()
print(f"Redis Connected: {cache.is_connected()}")

if cache.is_connected():
    # Test basic operations
    cache.set("test_key", {"message": "Hello!"}, ttl=60)
    value = cache.get("test_key")
    print(f"Test value: {value}")

    # Test stats
    stats = cache.get_stats()
    print(f"Redis Stats:")
    print(f"  Connected: {stats.get('connected')}")
    print(f"  Memory: {stats.get('used_memory_human')}")
    print(f"  Clients: {stats.get('connected_clients')}")
    print(f"  Hit Rate: {stats.get('hit_rate')}")

    # Cleanup
    cache.delete("test_key")
    print("\nRedis is working! Ready for caching implementation.")
else:
    print("ERROR: Redis not available")
