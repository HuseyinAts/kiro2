"""
Redis Caching Layer
High-performance caching for Knowledge Graph queries, CAT sessions, and hot data

DEPRECATED (2025-01-25):
Bu dosya deprecated. Kullan: core/cache/cache_manager.py

Migration Guide:
    # ESKİ (bu dosya)
    from core.redis_cache import RedisCache, get_cache, cached
    cache = get_cache()
    cache.set("key", value, ttl=3600)

    # YENİ (tercih edilen)
    from core.cache import cache_manager, cache_result
    await cache_manager.set("key", value, ttl=3600)

    # Decorator kullanimi
    @cache_result(prefix="my_data", expire=3600)
    async def my_function():
        ...

Neden deprecated?
- core/cache/ dizini ana cache sistemi
- cache_manager.py async-first design
- Bu dosya cache_service.py ile overlap ediyor

Backward Compatibility:
Bu dosya silinmeyecek, ancak yeni kod icin
core/cache/ kullanilmali. Sync-only kod icin
bu dosya gecici olarak kullanilabilir.
"""

import hashlib
import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

import redis

# SECURITY: Use centralized Settings for all configuration
from core.config import get_settings

# CODE QUALITY: Use structured logger instead of print statements
logger = logging.getLogger(__name__)


class RedisCache:
    """Redis caching wrapper for KIRO platform"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None,
        decode_responses: bool = True,
    ):
        """
        Initialize Redis connection

        Args:
            host: Redis host (default: from Settings)
            port: Redis port (default: from Settings)
            db: Redis database number
            password: Redis password (if authentication enabled)
            decode_responses: Decode byte responses to strings
        """
        # SECURITY: Get config from centralized Settings
        settings = get_settings()
        self.host = host or settings.redis_host
        self.port = port or settings.redis_port
        self.db = db or settings.redis_db
        self.password = password or settings.redis_password

        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=decode_responses,
                socket_timeout=5,
                socket_connect_timeout=5,
            )

            # Test connection
            self.client.ping()
            self.connected = True
            logger.info(f"Redis connected: {self.host}:{self.port}")

        except (redis.ConnectionError, redis.TimeoutError) as e:
            self.client = None
            self.connected = False
            logger.warning(f"Redis not available: {e}. Caching will be disabled.")

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.client:
            return False

        try:
            self.client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
            return False

    def get(self, key: str) -> Any | None:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.connected:
            return None

        try:
            value = self.client.get(key)
            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except (redis.RedisError, ConnectionError) as e:
            logger.error(f"Redis GET error for key: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: 1 hour)

        Returns:
            Success status
        """
        if not self.connected:
            return False

        try:
            # Serialize value if needed
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value, ensure_ascii=False)

            self.client.setex(key, ttl, value)
            return True

        except (redis.RedisError, ConnectionError) as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.connected:
            return False

        try:
            self.client.delete(key)
            return True
        except (redis.RedisError, ConnectionError) as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Redis pattern (e.g., "knowledge_graph:*")

        Returns:
            Number of keys deleted
        """
        if not self.connected:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except (redis.RedisError, ConnectionError) as e:
            logger.error(f"Redis DELETE_PATTERN error for pattern '{pattern}': {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.connected:
            return False

        try:
            return self.client.exists(key) > 0
        except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
            return False

    def incr(self, key: str, amount: int = 1) -> int | None:
        """Increment counter"""
        if not self.connected:
            return None

        try:
            return self.client.incr(key, amount)
        except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
            return None

    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key"""
        if not self.connected:
            return False

        try:
            return self.client.expire(key, ttl)
        except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
            return False

    def get_stats(self) -> dict:
        """Get Redis statistics"""
        if not self.connected:
            return {"connected": False}

        try:
            info = self.client.info()
            return {
                "connected": True,
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
            }
        except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
            return {"connected": False}

    def _calculate_hit_rate(self, info: dict) -> str:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        if total == 0:
            return "N/A"

        hit_rate = (hits / total) * 100
        return f"{hit_rate:.2f}%"

    def flush_db(self) -> bool:
        """Flush all keys in current database (use with caution!)"""
        if not self.connected:
            return False

        try:
            self.client.flushdb()
            return True
        except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
            return False


# Global cache instance
_cache_instance: RedisCache | None = None


def get_cache() -> RedisCache:
    """Get or create global Redis cache instance"""
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = RedisCache()

    return _cache_instance


def cache_key(*args, prefix: str = "", **kwargs) -> str:
    """
    Generate cache key from arguments

    Args:
        *args: Positional arguments
        prefix: Key prefix
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Combine all arguments
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])

    # Create hash for long keys
    key_str = ":".join(key_parts)
    if len(key_str) > 200:
        key_hash = hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()[:16]
        key_str = key_hash

    # Add prefix
    if prefix:
        return f"{prefix}:{key_str}"

    return key_str


def cached(ttl: int = 3600, prefix: str = "", key_func: Callable | None = None):
    """
    Decorator to cache function results

    Args:
        ttl: Cache TTL in seconds
        prefix: Cache key prefix
        key_func: Custom key generation function

    Example:
        @cached(ttl=600, prefix="knowledge_graph")
        def get_student_gaps(student_id: str):
            # expensive operation
            return gaps
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()

            if not cache.connected:
                # Cache not available, execute function directly
                return func(*args, **kwargs)

            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = cache_key(*args, prefix=prefix or func.__name__, **kwargs)

            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(key, result, ttl)

            return result

        return wrapper

    return decorator


# Cache configurations for different data types
CACHE_TTL = {
    "knowledge_graph_stats": 300,  # 5 minutes
    "knowledge_graph_gaps": 600,  # 10 minutes
    "knowledge_graph_recommendations": 600,  # 10 minutes
    "cat_session": 3600,  # 1 hour
    "question_details": 1800,  # 30 minutes
    "leaderboard": 60,  # 1 minute
    "expert_stats": 300,  # 5 minutes
    "hot_questions": 600,  # 10 minutes
}


def get_ttl(cache_type: str) -> int:
    """Get TTL for cache type"""
    return CACHE_TTL.get(cache_type, 3600)


# Example usage
if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(level=logging.INFO)

    # Test Redis connection
    cache = get_cache()

    if cache.connected:
        logger.info("Redis is working!")

        # Test basic operations
        cache.set("test_key", {"message": "Hello Redis!"}, ttl=10)
        value = cache.get("test_key")
        logger.info(f"Cached value: {value}")

        # Test stats
        stats = cache.get_stats()
        logger.info(f"Stats: {stats}")

        # Clean up
        cache.delete("test_key")
    else:
        logger.warning("Redis not available (app will work without caching)")
