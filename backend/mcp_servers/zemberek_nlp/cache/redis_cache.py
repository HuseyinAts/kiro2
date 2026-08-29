"""
Zemberek NLP Redis Cache
Async Redis caching with namespace support for NLP operations
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from ..config import get_config, get_ttl

logger = logging.getLogger(__name__)


class CacheStats:
    """Track cache statistics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.start_time = datetime.now()

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds"""
        return (datetime.now() - self.start_time).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": f"{self.hit_rate:.2%}",
            "uptime_seconds": self.uptime_seconds,
        }


class ZemberekCache:
    """Async Redis cache for Zemberek NLP operations"""

    def __init__(self):
        self.config = get_config()
        self._client: aioredis.Redis | None = None
        self._connected = False
        self.stats = CacheStats()

    async def connect(self) -> bool:
        """Initialize Redis connection"""
        if not self.config.cache_enabled:
            logger.info("[ZemberekCache] Caching disabled by config")
            return False

        if aioredis is None:
            logger.warning("[ZemberekCache] redis.asyncio not available")
            return False

        try:
            self._client = aioredis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                password=self.config.redis_password,
                db=self.config.redis_db,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(
                f"[ZemberekCache] Connected to Redis: {self.config.redis_host}:{self.config.redis_port}"
            )
            return True
        except Exception as e:
            logger.warning(f"[ZemberekCache] Redis connection failed: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("[ZemberekCache] Disconnected from Redis")

    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis"""
        return self._connected and self._client is not None

    async def get_cached(
        self, tool_name: str, input_text: str
    ) -> dict[str, Any] | None:
        """
        Get cached result for a tool operation

        Args:
            tool_name: Name of the NLP tool (morphology, tokenization, etc.)
            input_text: Input text that was processed

        Returns:
            Cached result dict or None if not found
        """
        if not self.is_connected:
            return None

        cache_key = generate_cache_key(
            self.config.cache_namespace, tool_name, input_text
        )

        try:
            value = await self._client.get(cache_key)
            if value:
                self.stats.hits += 1
                logger.debug(f"[ZemberekCache] HIT: {tool_name} ({cache_key[:20]}...)")
                return json.loads(value)
            self.stats.misses += 1
            logger.debug(f"[ZemberekCache] MISS: {tool_name} ({cache_key[:20]}...)")
            return None
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"[ZemberekCache] GET error: {e}")
            return None

    async def set_cached(
        self,
        tool_name: str,
        input_text: str,
        result: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """
        Cache a tool operation result

        Args:
            tool_name: Name of the NLP tool
            input_text: Input text that was processed
            result: Result to cache
            ttl: Optional TTL override (uses tool default if None)

        Returns:
            Success status
        """
        if not self.is_connected:
            return False

        cache_key = generate_cache_key(
            self.config.cache_namespace, tool_name, input_text
        )
        cache_ttl = ttl or get_ttl(tool_name)

        try:
            # Remove the 'cached' and 'latency_ms' fields before storing
            cache_data = {
                k: v for k, v in result.items() if k not in ("cached", "latency_ms")
            }
            value = json.dumps(cache_data, ensure_ascii=False)
            await self._client.setex(cache_key, cache_ttl, value)
            logger.debug(
                f"[ZemberekCache] SET: {tool_name} ({cache_key[:20]}...) TTL={cache_ttl}s"
            )
            return True
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"[ZemberekCache] SET error: {e}")
            return False

    async def delete_cached(self, tool_name: str, input_text: str) -> bool:
        """Delete a specific cached result"""
        if not self.is_connected:
            return False

        cache_key = generate_cache_key(
            self.config.cache_namespace, tool_name, input_text
        )

        try:
            await self._client.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"[ZemberekCache] DELETE error: {e}")
            return False

    async def clear_tool_cache(self, tool_name: str) -> int:
        """Clear all cached results for a specific tool"""
        if not self.is_connected:
            return 0

        pattern = f"{self.config.cache_namespace}:{tool_name}:*"

        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                deleted = await self._client.delete(*keys)
                logger.info(f"[ZemberekCache] Cleared {deleted} keys for {tool_name}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"[ZemberekCache] CLEAR error: {e}")
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        stats = self.stats.to_dict()
        stats["connected"] = self.is_connected

        if self.is_connected:
            try:
                info = await self._client.info("stats")
                stats["redis_stats"] = {
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
            except Exception:
                pass

        return stats


def generate_cache_key(namespace: str, tool_name: str, input_text: str) -> str:
    """
    Generate a cache key for a tool operation

    Args:
        namespace: Cache namespace (e.g., "zemberek")
        tool_name: Tool name (e.g., "morphology")
        input_text: Input text

    Returns:
        Cache key: {namespace}:{tool}:{hash}

    Example:
        "zemberek:morphology:a1b2c3d4e5f6..."
    """
    # Normalize input text (lowercase, strip whitespace)
    normalized = input_text.strip().lower()
    # Generate MD5 hash
    text_hash = hashlib.md5(
        normalized.encode("utf-8"), usedforsecurity=False
    ).hexdigest()
    return f"{namespace}:{tool_name}:{text_hash}"


# Global cache instance
_cache_instance: ZemberekCache | None = None


async def get_cache() -> ZemberekCache:
    """Get or create global cache instance"""
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = ZemberekCache()
        await _cache_instance.connect()

    return _cache_instance


async def close_cache() -> None:
    """Close global cache instance"""
    global _cache_instance

    if _cache_instance is not None:
        await _cache_instance.disconnect()
        _cache_instance = None
