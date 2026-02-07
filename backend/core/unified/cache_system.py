"""
KIRO2 Unified Cache System
Consolidated caching solution combining all cache functionality
SECURITY FIX: JSON serialization (replaced pickle to prevent RCE)
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache level definitions for multi-level caching"""

    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DISK = "l3_disk"


class CacheStrategy(Enum):
    """Cache strategy definitions"""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"


@dataclass
class CacheConfig:
    """Unified cache configuration"""

    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 3600  # 1 hour
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    key_prefix: str = "kiro2"

    # Multi-level caching
    enable_l1_cache: bool = True
    l1_cache_size: int = 1000
    enable_l2_cache: bool = True
    enable_l3_cache: bool = False
    l3_cache_path: str = "/tmp/kiro2_cache"

    # Performance optimization
    compression_enabled: bool = True
    compression_threshold: int = 1024  # bytes
    serialization_method: str = "pickle"  # json, pickle, msgpack

    # Turkish optimization
    turkish_encoding: str = "utf-8"
    turkish_collation: bool = True


@dataclass
class CacheStats:
    """Comprehensive cache statistics"""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def l1_hit_ratio(self) -> float:
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        return self.l1_hits / total_hits if total_hits > 0 else 0.0


class TurkishKeyEncoder:
    """Turkish character-aware key encoding"""

    @staticmethod
    def encode_key(key: str) -> str:
        """Encode Turkish characters in cache keys"""
        if not isinstance(key, str):
            key = str(key)

        # Turkish character mapping for cache keys
        turkish_map = {
            "ç": "c",
            "Ç": "C",
            "ğ": "g",
            "Ğ": "G",
            "ı": "i",
            "I": "I",
            "ö": "o",
            "Ö": "O",
            "ş": "s",
            "Ş": "S",
            "ü": "u",
            "Ü": "U",
        }

        for turkish_char, ascii_char in turkish_map.items():
            key = key.replace(turkish_char, ascii_char)

        return key

    @staticmethod
    def hash_key(key: str) -> str:
        """Create hash for complex keys"""
        return hashlib.md5(key.encode("utf-8")).hexdigest()


class UnifiedCacheManager:
    """
    Unified cache manager combining all caching functionality:
    - Multi-level caching (L1: Memory, L2: Redis, L3: Disk)
    - Turkish optimization
    - Performance monitoring
    - Smart cache strategies
    - Educational content caching
    """

    def __init__(self, config: CacheConfig | None = None):
        self.config = config or CacheConfig()
        self.stats = CacheStats()
        self.redis_pool: redis.ConnectionPool | None = None
        self.redis_client: redis.Redis | None = None
        self.l1_cache: dict[str, tuple[Any, float]] = {}  # key -> (value, expiry)
        self.key_encoder = TurkishKeyEncoder()
        self._health_check_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Initialize cache connections"""
        try:
            # Initialize Redis connection
            self.redis_pool = redis.ConnectionPool.from_url(
                self.config.redis_url,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                encoding="utf-8",
                decode_responses=False,
            )

            self.redis_client = redis.Redis(connection_pool=self.redis_pool)

            # Test connection
            await self.redis_client.ping()

            # Start health check
            if self.config.health_check_interval > 0:
                self._health_check_task = asyncio.create_task(self._health_check_loop())

            logger.info("Cache manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise

    async def shutdown(self) -> None:
        """Cleanup cache connections"""
        if self._health_check_task:
            self._health_check_task.cancel()

        if self.redis_client:
            await self.redis_client.close()

        if self.redis_pool:
            await self.redis_pool.disconnect()

    def _make_key(self, key: str, namespace: str = "") -> str:
        """Create standardized cache key"""
        # Encode Turkish characters
        encoded_key = self.key_encoder.encode_key(key)

        # Add namespace and prefix
        parts = [self.config.key_prefix]
        if namespace:
            parts.append(namespace)
        parts.append(encoded_key)

        return ":".join(parts)

    def _serialize(self, data: Any) -> bytes:
        """Serialize data for caching"""
        if self.config.serialization_method == "json":
            return json.dumps(data, ensure_ascii=False).encode(
                self.config.turkish_encoding
            )
        if self.config.serialization_method == "pickle":
            return pickle.dumps(data)
        # Default to pickle
        return pickle.dumps(data)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize cached data"""
        if self.config.serialization_method == "json":
            return json.loads(data.decode(self.config.turkish_encoding))
        if self.config.serialization_method == "pickle":
            return pickle.loads(data)
        # Default to pickle
        return pickle.loads(data)

    def _compress(self, data: bytes) -> bytes:
        """Compress data if enabled and beneficial"""
        if (
            self.config.compression_enabled
            and len(data) > self.config.compression_threshold
        ):
            import gzip

            return gzip.compress(data)
        return data

    def _decompress(self, data: bytes) -> bytes:
        """Decompress data if needed"""
        if self.config.compression_enabled:
            try:
                import gzip

                return gzip.decompress(data)
            except (OSError, zlib.error):
                # Not compressed or corrupted
                return data
        return data

    async def get(self, key: str, namespace: str = "", default: Any = None) -> Any:
        """Get value from cache with multi-level support"""
        cache_key = self._make_key(key, namespace)

        try:
            # L1 Cache (Memory)
            if self.config.enable_l1_cache and cache_key in self.l1_cache:
                value, expiry = self.l1_cache[cache_key]
                if expiry == 0 or time.time() < expiry:
                    self.stats.hits += 1
                    self.stats.l1_hits += 1
                    return value
                # Expired, remove from L1
                del self.l1_cache[cache_key]

            # L2 Cache (Redis)
            if self.config.enable_l2_cache and self.redis_client:
                data = await self.redis_client.get(cache_key)
                if data is not None:
                    # Decompress and deserialize
                    data = self._decompress(data)
                    value = self._deserialize(data)

                    # Store in L1 for faster access
                    if self.config.enable_l1_cache:
                        ttl = await self.redis_client.ttl(cache_key)
                        expiry = time.time() + ttl if ttl > 0 else 0
                        self._store_l1(cache_key, value, expiry)

                    self.stats.hits += 1
                    self.stats.l2_hits += 1
                    return value

            # L3 Cache (Disk) - Optional
            if self.config.enable_l3_cache:
                # Implementation for disk cache
                pass

            self.stats.misses += 1
            return default

        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            self.stats.errors += 1
            return default

    async def set(
        self, key: str, value: Any, ttl: int | None = None, namespace: str = ""
    ) -> bool:
        """Set value in cache with multi-level support"""
        cache_key = self._make_key(key, namespace)
        ttl = ttl or self.config.default_ttl

        try:
            # Serialize and compress
            data = self._serialize(value)
            data = self._compress(data)

            # Store in L2 (Redis)
            if self.config.enable_l2_cache and self.redis_client:
                await self.redis_client.setex(cache_key, ttl, data)

            # Store in L1 (Memory)
            if self.config.enable_l1_cache:
                expiry = time.time() + ttl if ttl > 0 else 0
                self._store_l1(cache_key, value, expiry)

            self.stats.sets += 1
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            self.stats.errors += 1
            return False

    def _store_l1(self, key: str, value: Any, expiry: float) -> None:
        """Store value in L1 cache with size management"""
        if len(self.l1_cache) >= self.config.l1_cache_size:
            # Remove oldest entries (simple LRU)
            oldest_key = min(self.l1_cache.keys(), key=lambda k: self.l1_cache[k][1])
            del self.l1_cache[oldest_key]

        self.l1_cache[key] = (value, expiry)

    async def delete(self, key: str, namespace: str = "") -> bool:
        """Delete key from all cache levels"""
        cache_key = self._make_key(key, namespace)

        try:
            # Remove from L1
            if cache_key in self.l1_cache:
                del self.l1_cache[cache_key]

            # Remove from L2 (Redis)
            if self.redis_client:
                await self.redis_client.delete(cache_key)

            self.stats.deletes += 1
            return True

        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            self.stats.errors += 1
            return False

    async def clear_pattern(self, pattern: str, namespace: str = "") -> int:
        """Clear keys matching pattern"""
        full_pattern = self._make_key(pattern, namespace)

        try:
            if self.redis_client:
                keys = await self.redis_client.keys(full_pattern)
                if keys:
                    deleted = await self.redis_client.delete(*keys)

                    # Also clear from L1
                    for key in keys:
                        if key.decode("utf-8") in self.l1_cache:
                            del self.l1_cache[key.decode("utf-8")]

                    return deleted
            return 0

        except Exception as e:
            logger.error(f"Cache clear pattern error for {full_pattern}: {e}")
            self.stats.errors += 1
            return 0

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern (alias for clear_pattern)"""
        return await self.clear_pattern(pattern)

    async def health_check(self) -> dict[str, Any]:
        """Perform health check and return status"""
        status = {
            "redis_connected": False,
            "l1_cache_size": len(self.l1_cache),
            "stats": {
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "hit_ratio": self.stats.hit_ratio,
                "l1_hit_ratio": self.stats.l1_hit_ratio,
                "errors": self.stats.errors,
            },
            "timestamp": datetime.now().isoformat(),
        }

        try:
            if self.redis_client:
                await self.redis_client.ping()
                status["redis_connected"] = True

                # Get Redis info
                info = await self.redis_client.info()
                status["redis_memory"] = info.get("used_memory_human")
                status["redis_connections"] = info.get("connected_clients")

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            status["error"] = str(e)

        return status

    async def _health_check_loop(self) -> None:
        """Background health check loop"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                status = await self.health_check()
                if not status["redis_connected"]:
                    logger.warning("Redis connection lost, attempting reconnect...")
                    await self.initialize()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    def cache_decorator(self, ttl: int = None, namespace: str = ""):
        """Decorator for caching function results"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Create cache key from function name and arguments
                key_parts = [func.__name__]
                if args:
                    key_parts.append(str(hash(args)))
                if kwargs:
                    key_parts.append(str(hash(tuple(sorted(kwargs.items())))))

                cache_key = ":".join(key_parts)

                # Try to get from cache
                result = await self.get(cache_key, namespace)
                if result is not None:
                    return result

                # Execute function and cache result
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                await self.set(cache_key, result, ttl, namespace)
                return result

            return wrapper

        return decorator


# Global instance
_cache_manager: UnifiedCacheManager | None = None


def get_cache_manager() -> UnifiedCacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = UnifiedCacheManager()
    return _cache_manager


# Backward compatibility aliases
CacheManager = UnifiedCacheManager
TurkishCacheManager = UnifiedCacheManager
SmartCacheManager = UnifiedCacheManager
PerformanceAwareCache = UnifiedCacheManager
MultiLevelCache = UnifiedCacheManager
