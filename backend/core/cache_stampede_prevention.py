"""
Cache Stampede Prevention
PERFORMANCE FIX: Prevent thundering herd problem when cache expires
"""
import asyncio
import hashlib
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class CacheStampedePreventor:
    """
    Prevents cache stampede (thundering herd) problem

    When a cached value expires and multiple requests try to regenerate it simultaneously,
    this class ensures only ONE request actually regenerates the value while others wait.
    """

    def __init__(self):
        self.locks: dict[str, asyncio.Lock] = {}
        self.lock_creation_lock = asyncio.Lock()

    async def get_lock(self, key: str) -> asyncio.Lock:
        """Get or create lock for a specific cache key"""
        if key not in self.locks:
            async with self.lock_creation_lock:
                # Double-check after acquiring lock
                if key not in self.locks:
                    self.locks[key] = asyncio.Lock()

        return self.locks[key]

    async def get_with_lock(
        self,
        cache_key: str,
        cache_get: Callable,
        cache_set: Callable,
        compute_fn: Callable,
        ttl: int = 3600,
    ) -> Any:
        """
        Get value from cache with stampede prevention

        Args:
            cache_key: Key to store/retrieve from cache
            cache_get: Async function to get from cache (returns None if miss)
            cache_set: Async function to set in cache
            compute_fn: Async function to compute value if cache miss
            ttl: Time to live in seconds

        Returns:
            Cached or computed value
        """
        # Try to get from cache first (fast path)
        value = await cache_get(cache_key)
        if value is not None:
            return value

        # Cache miss - acquire lock to prevent stampede
        lock = await self.get_lock(cache_key)

        async with lock:
            # Double-check cache after acquiring lock
            # Another request might have filled it while we were waiting
            value = await cache_get(cache_key)
            if value is not None:
                logger.debug(f"[CACHE] Value found after lock acquisition: {cache_key}")
                return value

            # Still a miss - compute the value
            logger.info(f"[CACHE] Computing value for: {cache_key}")
            value = await compute_fn()

            # Store in cache
            await cache_set(cache_key, value, ttl)

            return value


# Global instance
_stampede_preventor = CacheStampedePreventor()


def cached_with_lock(ttl: int = 3600, key_prefix: str | None = None) -> Callable:
    """
    Decorator for caching with stampede prevention

    Usage:
        @cached_with_lock(ttl=3600, key_prefix="irt_params")
        async def get_irt_parameters(question_ids: List[int]) -> dict:
            # Expensive computation
            return calculate_irt_parameters(question_ids)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name and arguments
            key_base = key_prefix or func.__name__
            args_str = str(args) + str(sorted(kwargs.items()))
            args_hash = hashlib.md5(args_str.encode()).hexdigest()
            cache_key = f"{key_base}:{args_hash}"

            # Import cache dynamically to avoid circular imports
            from core.cache import cache_manager

            # Define cache operations
            async def cache_get(key: str) -> Any | None:
                if not cache_manager.enabled:
                    return None
                return await cache_manager.get(key)

            async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
                if cache_manager.enabled:
                    await cache_manager.set(key, value, ttl_seconds)

            async def compute() -> Any:
                return await func(*args, **kwargs)

            # Use stampede prevention
            return await _stampede_preventor.get_with_lock(
                cache_key=cache_key,
                cache_get=cache_get,
                cache_set=cache_set,
                compute_fn=compute,
                ttl=ttl,
            )

        return wrapper

    return decorator


# Example usage pattern for services
async def get_cached_with_stampede_prevention(
    cache_key: str,
    compute_fn: Callable,
    ttl: int = 3600,
) -> Any:
    """
    Standalone function for cache stampede prevention

    Usage:
        from core.cache_stampede_prevention import get_cached_with_stampede_prevention

        async def expensive_operation():
            # Do expensive work
            return result

        result = await get_cached_with_stampede_prevention(
            cache_key="my_key",
            compute_fn=expensive_operation,
            ttl=3600
        )
    """
    from core.cache import cache_manager

    async def cache_get(key: str) -> Any | None:
        if not cache_manager.enabled:
            return None
        return await cache_manager.get(key)

    async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
        if cache_manager.enabled:
            await cache_manager.set(key, value, ttl_seconds)

    return await _stampede_preventor.get_with_lock(
        cache_key=cache_key,
        cache_get=cache_get,
        cache_set=cache_set,
        compute_fn=compute_fn,
        ttl=ttl,
    )
