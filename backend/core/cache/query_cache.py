"""
Query Cache - API Response Time Optimization

Bu modül, Redis tabanlı query result caching sağlar.
Write-through invalidation ve cache warming destekler.

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-5.4
"""

import hashlib
import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class QueryCache:
    """
    Redis tabanlı query cache.

    Database query sonuçlarını cache'ler.
    TTL-based expiration ve pattern-based invalidation destekler.

    Attributes:
        redis: Redis client instance
        default_ttl: Default TTL (saniye)
        key_prefix: Cache key prefix

    Example:
        cache = QueryCache(redis_client, default_ttl=300)

        # Cache query result
        result = await cache.get_or_set(
            key="questions:math:page1",
            getter=lambda: db.execute(query),
            ttl=600
        )

        # Invalidate on update
        await cache.invalidate_pattern("questions:*")
    """

    def __init__(
        self, redis: Any = None, default_ttl: int = 300, key_prefix: str = "qcache:"
    ):
        """
        QueryCache başlatır.

        Args:
            redis: Redis client instance (or None for no-op)
            default_ttl: Default cache TTL (saniye)
            key_prefix: Cache key prefix
        """
        self.redis = redis
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._enabled = redis is not None

        if self._enabled:
            logger.info(
                f"QueryCache initialized: prefix={key_prefix}, default_ttl={default_ttl}s"
            )
        else:
            logger.warning("QueryCache disabled: Redis client not provided")

    def _make_key(self, key: str) -> str:
        """Full cache key oluşturur."""
        return f"{self.key_prefix}{key}"

    def _hash_key(self, data: Any) -> str:
        """Data'yı hash'leyerek key oluşturur."""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True, default=str)
        elif not isinstance(data, str):
            data = str(data)
        return hashlib.md5(data.encode(), usedforsecurity=False).hexdigest()[:16]

    async def get(self, key: str) -> Any | None:
        """
        Cache'den değer alır.

        Args:
            key: Cache key

        Returns:
            Cached value veya None
        """
        if not self._enabled:
            return None

        try:
            full_key = self._make_key(key)
            cached = await self.redis.get(full_key)

            if cached:
                logger.debug(f"Cache hit: {key}")
                return json.loads(cached)

            logger.debug(f"Cache miss: {key}")
            return None

        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Cache'e değer yazar.

        Args:
            key: Cache key
            value: Değer (JSON serializable)
            ttl: TTL (saniye, None=default)

        Returns:
            True ise başarılı
        """
        if not self._enabled:
            return False

        try:
            full_key = self._make_key(key)
            ttl = ttl or self.default_ttl

            # Serialize value
            serialized = json.dumps(value, default=str)

            await self.redis.setex(full_key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False

    async def get_or_set(
        self, key: str, getter: Callable, ttl: int | None = None
    ) -> Any:
        """
        Cache'den al veya getter ile doldur.

        Args:
            key: Cache key
            getter: Değer üretici async/sync fonksiyon
            ttl: TTL (saniye)

        Returns:
            Cached veya fresh value
        """
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Get fresh value
        import asyncio

        if asyncio.iscoroutinefunction(getter):
            value = await getter()
        else:
            value = getter()

        # Cache and return
        await self.set(key, value, ttl)
        return value

    async def delete(self, key: str) -> bool:
        """
        Cache entry'yi siler.

        Args:
            key: Cache key

        Returns:
            True ise silindi
        """
        if not self._enabled:
            return False

        try:
            full_key = self._make_key(key)
            result = await self.redis.delete(full_key)
            logger.debug(f"Cache delete: {key} (deleted={result})")
            return result > 0

        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Pattern'e uyan tüm key'leri siler.

        Args:
            pattern: Glob pattern (e.g., "questions:*")

        Returns:
            Silinen key sayısı
        """
        if not self._enabled:
            return 0

        try:
            full_pattern = self._make_key(pattern)
            deleted = 0

            # Use SCAN for safe iteration
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor, match=full_pattern, count=100
                )

                if keys:
                    await self.redis.delete(*keys)
                    deleted += len(keys)

                if cursor == 0:
                    break

            logger.info(f"Cache invalidate: {pattern} (deleted={deleted})")
            return deleted

        except Exception as e:
            logger.error(f"Cache invalidate error for {pattern}: {e}")
            return 0

    async def get_hash(self, key: str) -> dict | None:
        """
        Redis hash'i alır.

        Args:
            key: Hash key

        Returns:
            Hash dict veya None
        """
        if not self._enabled:
            return None

        try:
            full_key = self._make_key(key)
            result = await self.redis.hgetall(full_key)

            if result:
                # Decode values
                return {k: json.loads(v) for k, v in result.items()}

            return None

        except Exception as e:
            logger.error(f"Cache get_hash error for {key}: {e}")
            return None

    async def set_hash(self, key: str, data: dict, ttl: int | None = None) -> bool:
        """
        Redis hash'e yazar.

        Args:
            key: Hash key
            data: Hash dict
            ttl: TTL (saniye)

        Returns:
            True ise başarılı
        """
        if not self._enabled:
            return False

        try:
            full_key = self._make_key(key)

            # Serialize values
            encoded = {k: json.dumps(v, default=str) for k, v in data.items()}

            # Use pipeline for atomic operation
            pipe = self.redis.pipeline()
            pipe.hset(full_key, mapping=encoded)
            if ttl:
                pipe.expire(full_key, ttl or self.default_ttl)
            await pipe.execute()

            logger.debug(f"Cache set_hash: {key}")
            return True

        except Exception as e:
            logger.error(f"Cache set_hash error for {key}: {e}")
            return False


def cached_query(
    key_template: str, ttl: int = 300, key_params: list[str] | None = None
):
    """
    Query caching decorator.

    Args:
        key_template: Cache key template (e.g., "questions:{subject}:{page}")
        ttl: Cache TTL (saniye)
        key_params: Key template'te kullanılacak param adları

    Returns:
        Decorated function

    Example:
        @cached_query("questions:{subject}:page{page}", ttl=600)
        async def get_questions(subject: str, page: int = 1):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get query cache from context or skip
            try:
                from core.cache import get_query_cache

                cache = get_query_cache()
            except ImportError:
                # No cache available, execute directly
                return await func(*args, **kwargs)

            # Build cache key
            if key_params:
                key_values = {p: kwargs.get(p, "") for p in key_params}
            else:
                key_values = kwargs

            try:
                cache_key = key_template.format(**key_values)
            except KeyError:
                # Missing key param, execute directly
                return await func(*args, **kwargs)

            # Try cache
            return await cache.get_or_set(
                key=cache_key, getter=lambda: func(*args, **kwargs), ttl=ttl
            )

        return wrapper

    return decorator


class QueryCacheWarmer:
    """
    Cache warming utility.

    Popüler query'leri önceden cache'ler.

    Example:
        warmer = QueryCacheWarmer(cache)
        warmer.add_query("popular_questions", get_popular_questions)
        await warmer.warm_all()
    """

    def __init__(self, cache: QueryCache):
        """
        QueryCacheWarmer başlatır.

        Args:
            cache: QueryCache instance
        """
        self.cache = cache
        self._queries: dict[str, tuple[Callable, int]] = {}

    def add_query(self, key: str, getter: Callable, ttl: int = 600) -> None:
        """
        Warming listesine query ekler.

        Args:
            key: Cache key
            getter: Query fonksiyonu
            ttl: TTL (saniye)
        """
        self._queries[key] = (getter, ttl)

    def remove_query(self, key: str) -> None:
        """Query'yi listeden kaldırır."""
        self._queries.pop(key, None)

    async def warm(self, key: str) -> bool:
        """
        Tek bir query'yi warm eder.

        Args:
            key: Cache key

        Returns:
            True ise başarılı
        """
        if key not in self._queries:
            return False

        getter, ttl = self._queries[key]

        try:
            import asyncio

            if asyncio.iscoroutinefunction(getter):
                value = await getter()
            else:
                value = getter()

            await self.cache.set(key, value, ttl)
            logger.info(f"Cache warmed: {key}")
            return True

        except Exception as e:
            logger.error(f"Cache warm error for {key}: {e}")
            return False

    async def warm_all(self) -> dict[str, bool]:
        """
        Tüm query'leri warm eder.

        Returns:
            Key -> success mapping
        """
        results = {}
        for key in self._queries:
            results[key] = await self.warm(key)
        return results


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_query_cache: QueryCache | None = None


def get_query_cache() -> QueryCache:
    """
    Global QueryCache instance döndürür.

    Returns:
        QueryCache singleton instance
    """
    global _query_cache
    if _query_cache is None:
        # Try to get Redis client
        try:
            from core.cache import cache_manager

            _query_cache = QueryCache(redis=cache_manager.redis, default_ttl=300)
        except (ImportError, AttributeError):
            _query_cache = QueryCache(redis=None)
    return _query_cache


def init_query_cache(redis: Any, ttl: int = 300) -> QueryCache:
    """
    QueryCache'i initialize eder.

    Args:
        redis: Redis client
        ttl: Default TTL

    Returns:
        Initialized QueryCache
    """
    global _query_cache
    _query_cache = QueryCache(redis=redis, default_ttl=ttl)
    return _query_cache
