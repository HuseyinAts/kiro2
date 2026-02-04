"""
Advanced Cache Strategies
Multi-layer caching with smart invalidation and preloading
Target: Improve cache hit rate and reduce latency
"""
import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Cache eviction strategies"""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    key: str
    value: Any
    created_at: float
    expires_at: Optional[float]
    access_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0
    tags: Set[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()


class SmartCacheManager:
    """
    Advanced cache manager with intelligent strategies

    Features:
    - Multi-layer caching (L1: memory, L2: Redis)
    - Tag-based invalidation
    - Predictive preloading
    - Automatic warming
    - Cache statistics and monitoring
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        l1_size: int = 1000,
        l2_enabled: bool = True,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl: int = 3600,
    ):
        self.redis_url = redis_url
        self.l1_size = l1_size
        self.l2_enabled = l2_enabled
        self.strategy = strategy
        self.default_ttl = default_ttl

        # L1 cache (in-memory)
        self.l1_cache: Dict[str, CacheEntry] = {}

        # L2 cache (Redis)
        self.redis_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None

        # Tag index for invalidation
        self.tag_index: Dict[str, Set[str]] = {}  # tag -> keys

        # Metrics
        self.metrics = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "sets": 0,
            "deletes": 0,
            "invalidations": 0,
            "preloads": 0,
        }

    async def initialize(self):
        """Initialize cache connections"""
        if self.l2_enabled and self.redis_client is None:
            try:
                self.redis_pool = ConnectionPool.from_url(
                    self.redis_url, max_connections=20, decode_responses=False
                )
                self.redis_client = redis.Redis(connection_pool=self.redis_pool)
                await self.redis_client.ping()
                logger.info("Redis L2 cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed, using L1 only: {e}")
                self.l2_enabled = False

    async def close(self):
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.redis_pool:
            await self.redis_pool.disconnect()

    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get value from cache (L1 -> L2 hierarchy)

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        # Try L1 cache first
        if key in self.l1_cache:
            entry = self.l1_cache[key]

            # Check TTL
            if entry.expires_at and time.time() > entry.expires_at:
                await self.delete(key)
                self.metrics["l1_misses"] += 1
                return default

            # Update access metadata
            entry.access_count += 1
            entry.last_accessed = time.time()

            self.metrics["l1_hits"] += 1
            logger.debug(f"L1 cache hit: {key}")
            return entry.value

        self.metrics["l1_misses"] += 1

        # Try L2 cache (Redis)
        if self.l2_enabled:
            try:
                value_bytes = await self.redis_client.get(key)
                if value_bytes:
                    value = json.loads(value_bytes)

                    # Promote to L1
                    await self._set_l1(key, value, None)

                    self.metrics["l2_hits"] += 1
                    logger.debug(f"L2 cache hit: {key}")
                    return value
            except Exception as e:
                logger.error(f"L2 cache get error: {e}")

        self.metrics["l2_misses"] += 1
        return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None,
    ):
        """
        Set value in cache (L1 + L2)

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (seconds)
            tags: Tags for invalidation
        """
        ttl = ttl or self.default_ttl
        tags = tags or set()

        self.metrics["sets"] += 1

        # Set in L1
        await self._set_l1(key, value, ttl, tags)

        # Set in L2 (Redis)
        if self.l2_enabled:
            try:
                value_bytes = json.dumps(value).encode()
                await self.redis_client.setex(key, ttl, value_bytes)

                # Store tags in Redis
                if tags:
                    for tag in tags:
                        await self.redis_client.sadd(f"tag:{tag}", key)
                        await self.redis_client.expire(f"tag:{tag}", ttl)

            except Exception as e:
                logger.error(f"L2 cache set error: {e}")

    async def _set_l1(
        self, key: str, value: Any, ttl: Optional[int], tags: Optional[Set[str]] = None
    ):
        """Set value in L1 cache"""
        # Evict if cache is full
        if len(self.l1_cache) >= self.l1_size:
            await self._evict_l1()

        expires_at = None
        if ttl:
            expires_at = time.time() + ttl

        # Estimate size
        size_bytes = len(json.dumps(value).encode())

        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            expires_at=expires_at,
            access_count=1,
            last_accessed=time.time(),
            size_bytes=size_bytes,
            tags=tags or set(),
        )

        self.l1_cache[key] = entry

        # Update tag index
        if tags:
            for tag in tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = set()
                self.tag_index[tag].add(key)

    async def _evict_l1(self):
        """Evict entry from L1 based on strategy"""
        if not self.l1_cache:
            return

        if self.strategy == CacheStrategy.LRU:
            # Evict least recently used
            key_to_evict = min(
                self.l1_cache.keys(), key=lambda k: self.l1_cache[k].last_accessed
            )
        elif self.strategy == CacheStrategy.LFU:
            # Evict least frequently used
            key_to_evict = min(
                self.l1_cache.keys(), key=lambda k: self.l1_cache[k].access_count
            )
        elif self.strategy == CacheStrategy.TTL:
            # Evict soonest to expire
            key_to_evict = min(
                self.l1_cache.keys(),
                key=lambda k: self.l1_cache[k].expires_at or float("inf"),
            )
        else:  # FIFO
            # Evict oldest
            key_to_evict = min(
                self.l1_cache.keys(), key=lambda k: self.l1_cache[k].created_at
            )

        del self.l1_cache[key_to_evict]
        logger.debug(f"Evicted from L1: {key_to_evict} (strategy: {self.strategy})")

    async def delete(self, key: str):
        """Delete from both L1 and L2"""
        self.metrics["deletes"] += 1

        # Delete from L1
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            # Remove from tag index
            for tag in entry.tags:
                if tag in self.tag_index:
                    self.tag_index[tag].discard(key)
            del self.l1_cache[key]

        # Delete from L2
        if self.l2_enabled:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"L2 cache delete error: {e}")

    async def invalidate_by_tag(self, tag: str):
        """
        Invalidate all cache entries with given tag

        Args:
            tag: Tag to invalidate
        """
        self.metrics["invalidations"] += 1

        # Invalidate in L1
        if tag in self.tag_index:
            keys_to_delete = list(self.tag_index[tag])
            for key in keys_to_delete:
                await self.delete(key)
            del self.tag_index[tag]

        # Invalidate in L2
        if self.l2_enabled:
            try:
                keys = await self.redis_client.smembers(f"tag:{tag}")
                if keys:
                    await self.redis_client.delete(*keys)
                await self.redis_client.delete(f"tag:{tag}")
            except Exception as e:
                logger.error(f"L2 tag invalidation error: {e}")

        logger.info(f"Invalidated cache tag: {tag}")

    async def invalidate_by_pattern(self, pattern: str):
        """
        Invalidate all cache entries matching pattern

        Args:
            pattern: Key pattern (e.g., "user:*")
        """
        self.metrics["invalidations"] += 1

        # Invalidate in L1
        keys_to_delete = [
            k for k in self.l1_cache.keys() if self._match_pattern(k, pattern)
        ]
        for key in keys_to_delete:
            await self.delete(key)

        # Invalidate in L2
        if self.l2_enabled:
            try:
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"L2 pattern invalidation error: {e}")

        logger.info(f"Invalidated cache pattern: {pattern}")

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching"""
        if "*" in pattern:
            prefix = pattern.split("*")[0]
            return key.startswith(prefix)
        return key == pattern

    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable,
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None,
    ) -> Any:
        """
        Get from cache or compute if missing

        Args:
            key: Cache key
            compute_fn: Function to compute value
            ttl: Time to live
            tags: Tags for invalidation

        Returns:
            Cached or computed value
        """
        # Try cache first
        value = await self.get(key)
        if value is not None:
            return value

        # Compute value
        if asyncio.iscoroutinefunction(compute_fn):
            value = await compute_fn()
        else:
            value = compute_fn()

        # Cache result
        await self.set(key, value, ttl, tags)

        return value

    async def preload(
        self, keys_and_values: List[Tuple[str, Any]], ttl: Optional[int] = None
    ):
        """
        Preload multiple keys (cache warming)

        Args:
            keys_and_values: List of (key, value) tuples
            ttl: Time to live
        """
        self.metrics["preloads"] += len(keys_and_values)

        for key, value in keys_and_values:
            await self.set(key, value, ttl)

        logger.info(f"Preloaded {len(keys_and_values)} cache entries")

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics"""
        total_requests = self.metrics["l1_hits"] + self.metrics["l1_misses"]

        l1_hit_rate = (
            self.metrics["l1_hits"] / total_requests if total_requests > 0 else 0.0
        )

        l2_hit_rate = (
            self.metrics["l2_hits"] / self.metrics["l1_misses"]
            if self.metrics["l1_misses"] > 0
            else 0.0
        )

        overall_hit_rate = (
            (self.metrics["l1_hits"] + self.metrics["l2_hits"]) / total_requests
            if total_requests > 0
            else 0.0
        )

        total_size_bytes = sum(e.size_bytes for e in self.l1_cache.values())

        return {
            **self.metrics,
            "l1_size": len(self.l1_cache),
            "l1_max_size": self.l1_size,
            "l1_hit_rate": l1_hit_rate,
            "l2_enabled": self.l2_enabled,
            "l2_hit_rate": l2_hit_rate,
            "overall_hit_rate": overall_hit_rate,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": total_size_bytes / (1024 * 1024),
            "strategy": self.strategy.value,
            "tag_count": len(self.tag_index),
        }

    async def clear(self):
        """Clear all caches"""
        self.l1_cache.clear()
        self.tag_index.clear()

        if self.l2_enabled:
            try:
                await self.redis_client.flushdb()
            except Exception as e:
                logger.error(f"L2 cache clear error: {e}")

        logger.info("All caches cleared")


# Decorator for caching function results
def cached(
    ttl: Optional[int] = None, tags: Optional[Set[str]] = None, key_prefix: str = ""
):
    """
    Decorator to cache function results

    Example:
        @cached(ttl=3600, tags={"user"}, key_prefix="user_profile")
        async def get_user_profile(user_id: str):
            return await db.query(...)
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Get cache manager (assume global instance)
            cache = await get_smart_cache()

            # Try cache
            result = await cache.get(cache_key)
            if result is not None:
                return result

            # Compute and cache
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl, tags)

            return result

        return wrapper

    return decorator


# Global cache instance
_global_cache: Optional[SmartCacheManager] = None


async def get_smart_cache(config: Optional[Dict[str, Any]] = None) -> SmartCacheManager:
    """Get or create global cache manager"""
    global _global_cache

    if _global_cache is None:
        config = config or {}
        _global_cache = SmartCacheManager(**config)
        await _global_cache.initialize()

    return _global_cache


def get_cache_manager() -> Optional[SmartCacheManager]:
    """
    Get the global cache manager for metrics/monitoring

    Returns:
        SmartCacheManager instance, or None if not initialized
    """
    global _global_cache
    return _global_cache
