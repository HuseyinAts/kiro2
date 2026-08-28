"""
Redis Cache Service - Task 58.3
REQ-48.89-48.92: Cache sistemi

DEPRECATED (2025-01-25):
Bu dosya deprecated. Kullan: core/cache/cache_manager.py

Migration Guide:
    # ESKİ (bu dosya)
    from core.cache_service import CacheService, get_cache_service
    cache = get_cache_service()
    await cache.async_set("key", value, ttl=3600)

    # YENİ (tercih edilen)
    from core.cache import cache_manager
    await cache_manager.set("key", value, ttl=3600)

Neden deprecated?
- core/cache/ dizini ana cache sistemi
- cache_manager.py async-first design
- Bu dosya redis_cache.py ile overlap ediyor

Backward Compatibility:
Bu dosya silinmeyecek, ancak yeni kod icin
core/cache/ kullanilmali.
"""

import hashlib
import json
import pickle
from collections.abc import Callable
from functools import wraps
from typing import Any

import redis
from redis.asyncio import Redis as AsyncRedis

from core.config import get_settings
from core.structured_logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CacheService:
    """
    Redis cache service with sync and async support
    """

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or getattr(
            settings, "redis_url", "redis://localhost:6379"
        )
        self._sync_client: redis.Redis | None = None
        self._async_client: AsyncRedis | None = None
        self.default_ttl = 3600  # 1 hour
        self.namespace = "kiro"

    @property
    def sync_client(self) -> redis.Redis:
        """Get sync Redis client"""
        if self._sync_client is None:
            try:
                self._sync_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,  # We'll handle serialization ourselves
                )
                self._sync_client.ping()
                logger.info("Redis sync client connected")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._sync_client

    @property
    async def async_client(self) -> AsyncRedis:
        """Get async Redis client"""
        if self._async_client is None:
            try:
                self._async_client = await AsyncRedis.from_url(
                    self.redis_url, decode_responses=False
                )
                await self._async_client.ping()
                logger.info("Redis async client connected")
            except Exception as e:
                logger.error(f"Failed to connect to Redis async: {e}")
                raise
        return self._async_client

    def _make_key(self, key: str, namespace: str | None = None) -> str:
        """Create namespaced cache key"""
        ns = namespace or self.namespace
        return f"{ns}:{key}"

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first (faster, human-readable)
            return json.dumps(value).encode("utf-8")
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)

    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage"""
        if not value:
            return None

        try:
            # Try JSON first
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(value)

    # ==================== SYNC METHODS ====================

    def get(self, key: str, namespace: str | None = None) -> Any | None:
        """Get value from cache (sync)"""
        try:
            full_key = self._make_key(key, namespace)
            value = self.sync_client.get(full_key)
            if value:
                logger.debug(f"Cache HIT: {full_key}")
                return self._deserialize(value)
            logger.debug(f"Cache MISS: {full_key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        namespace: str | None = None,
    ) -> bool:
        """Set value in cache (sync)"""
        try:
            full_key = self._make_key(key, namespace)
            serialized = self._serialize(value)
            ttl_seconds = ttl or self.default_ttl

            self.sync_client.setex(full_key, ttl_seconds, serialized)
            logger.debug(f"Cache SET: {full_key} (TTL: {ttl_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str, namespace: str | None = None) -> bool:
        """Delete key from cache (sync)"""
        try:
            full_key = self._make_key(key, namespace)
            result = self.sync_client.delete(full_key)
            logger.debug(f"Cache DELETE: {full_key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def exists(self, key: str, namespace: str | None = None) -> bool:
        """Check if key exists (sync)"""
        try:
            full_key = self._make_key(key, namespace)
            return bool(self.sync_client.exists(full_key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    def clear_namespace(self, namespace: str | None = None) -> int:
        """Clear all keys in namespace (sync)"""
        try:
            ns = namespace or self.namespace
            pattern = f"{ns}:*"
            keys = self.sync_client.keys(pattern)
            if keys:
                count = self.sync_client.delete(*keys)
                logger.info(f"Cleared {count} keys from namespace: {ns}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache clear namespace error: {e}")
            return 0

    def get_ttl(self, key: str, namespace: str | None = None) -> int:
        """Get remaining TTL in seconds (sync)"""
        try:
            full_key = self._make_key(key, namespace)
            return self.sync_client.ttl(full_key)
        except Exception as e:
            logger.error(f"Cache get_ttl error: {e}")
            return -1

    # ==================== ASYNC METHODS ====================

    async def async_get(self, key: str, namespace: str | None = None) -> Any | None:
        """Get value from cache (async)"""
        try:
            client = await self.async_client
            full_key = self._make_key(key, namespace)
            value = await client.get(full_key)
            if value:
                logger.debug(f"Cache HIT: {full_key}")
                return self._deserialize(value)
            logger.debug(f"Cache MISS: {full_key}")
            return None
        except Exception as e:
            logger.error(f"Cache async_get error: {e}")
            return None

    async def async_set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        namespace: str | None = None,
    ) -> bool:
        """Set value in cache (async)"""
        try:
            client = await self.async_client
            full_key = self._make_key(key, namespace)
            serialized = self._serialize(value)
            ttl_seconds = ttl or self.default_ttl

            await client.setex(full_key, ttl_seconds, serialized)
            logger.debug(f"Cache SET: {full_key} (TTL: {ttl_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"Cache async_set error: {e}")
            return False

    async def async_delete(self, key: str, namespace: str | None = None) -> bool:
        """Delete key from cache (async)"""
        try:
            client = await self.async_client
            full_key = self._make_key(key, namespace)
            result = await client.delete(full_key)
            logger.debug(f"Cache DELETE: {full_key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache async_delete error: {e}")
            return False

    # ==================== CACHE DECORATORS ====================

    def cached(
        self,
        ttl: int | None = None,
        namespace: str | None = None,
        key_func: Callable | None = None,
    ):
        """
        Decorator to cache function results (sync)

        Usage:
            @cache_service.cached(ttl=3600, namespace="questions")
            def get_question(question_id: str):
                # expensive operation
                return question
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default: hash function name + args
                    key_parts = (
                        [func.__name__]
                        + [str(arg) for arg in args]
                        + [f"{k}={v}" for k, v in sorted(kwargs.items())]
                    )
                    cache_key = hashlib.md5(
                        ":".join(key_parts).encode(), usedforsecurity=False
                    ).hexdigest()

                # Try to get from cache
                cached_value = self.get(cache_key, namespace)
                if cached_value is not None:
                    return cached_value

                # Execute function
                result = func(*args, **kwargs)

                # Store in cache
                self.set(cache_key, result, ttl, namespace)

                return result

            return wrapper

        return decorator

    def async_cached(
        self,
        ttl: int | None = None,
        namespace: str | None = None,
        key_func: Callable | None = None,
    ):
        """
        Decorator to cache async function results

        Usage:
            @cache_service.async_cached(ttl=3600, namespace="questions")
            async def get_question(question_id: str):
                # expensive async operation
                return question
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    key_parts = (
                        [func.__name__]
                        + [str(arg) for arg in args]
                        + [f"{k}={v}" for k, v in sorted(kwargs.items())]
                    )
                    cache_key = hashlib.md5(
                        ":".join(key_parts).encode(), usedforsecurity=False
                    ).hexdigest()

                # Try to get from cache
                cached_value = await self.async_get(cache_key, namespace)
                if cached_value is not None:
                    return cached_value

                # Execute function
                result = await func(*args, **kwargs)

                # Store in cache
                await self.async_set(cache_key, result, ttl, namespace)

                return result

            return wrapper

        return decorator

    # ==================== CACHE INVALIDATION STRATEGIES ====================

    def invalidate_pattern(self, pattern: str, namespace: str | None = None) -> int:
        """
        Invalidate all keys matching pattern

        Example:
            cache_service.invalidate_pattern("question:*")
        """
        try:
            ns = namespace or self.namespace
            full_pattern = f"{ns}:{pattern}"
            keys = self.sync_client.keys(full_pattern)
            if keys:
                count = self.sync_client.delete(*keys)
                logger.info(
                    f"Invalidated {count} keys matching pattern: {full_pattern}"
                )
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate_pattern error: {e}")
            return 0

    def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            info = self.sync_client.info("stats")
            return {
                "total_connections": info.get("total_connections_received", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0)
                    / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                )
                * 100,
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# ==================== GLOBAL INSTANCE ====================

_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# ==================== CONVENIENCE FUNCTIONS ====================


def cache_get(key: str, namespace: str | None = None) -> Any | None:
    """Convenience function to get from cache"""
    return get_cache_service().get(key, namespace)


def cache_set(
    key: str, value: Any, ttl: int | None = None, namespace: str | None = None
) -> bool:
    """Convenience function to set in cache"""
    return get_cache_service().set(key, value, ttl, namespace)


def cache_delete(key: str, namespace: str | None = None) -> bool:
    """Convenience function to delete from cache"""
    return get_cache_service().delete(key, namespace)


def cache_clear_namespace(namespace: str | None = None) -> int:
    """Convenience function to clear namespace"""
    return get_cache_service().clear_namespace(namespace)
