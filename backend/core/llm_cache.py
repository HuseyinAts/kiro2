"""
KIRO2 Enhanced LLM Cache System
Optimized caching for LLM responses with Turkish language support
"""

import hashlib
import json
import logging
from datetime import datetime
from functools import wraps
from typing import Any

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMCacheConfig(BaseModel):
    """LLM Cache configuration"""

    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 3600  # 1 hour
    long_ttl: int = 86400  # 24 hours for stable content
    max_prompt_length: int = 4000  # Truncate very long prompts
    enable_compression: bool = True
    enable_embedding_cache: bool = True
    key_prefix: str = "kiro2:llm"

    # Turkish optimization
    turkish_normalization: bool = True

    # Cost tracking
    track_token_usage: bool = True

    # Semantic similarity (future feature)
    enable_semantic_matching: bool = False
    semantic_threshold: float = 0.95


class CacheEntry(BaseModel):
    """Cache entry structure"""

    response: str
    prompt_hash: str
    model: str
    timestamp: datetime
    token_count: int | None = None
    cost: float | None = None
    metadata: dict[str, Any] = {}


class LLMCacheStats(BaseModel):
    """LLM Cache statistics"""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_tokens_saved: int = 0
    total_cost_saved: float = 0.0

    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    @property
    def miss_ratio(self) -> float:
        """Calculate cache miss ratio"""
        return 1.0 - self.hit_ratio


class LLMCache:
    """
    Enhanced LLM Cache with Turkish language optimization

    Features:
    - Async Redis-based caching
    - Turkish character normalization
    - Token and cost tracking
    - TTL management
    - Compression for large responses
    - Fallback to in-memory cache
    - Statistics tracking
    """

    def __init__(self, config: LLMCacheConfig | None = None):
        self.config = config or LLMCacheConfig()
        self.redis_client: redis.Redis | None = None
        self.stats = LLMCacheStats()

        # In-memory fallback cache (LRU with max size)
        self._memory_cache: dict[str, CacheEntry] = {}
        self._memory_cache_max_size = 100
        self._memory_cache_access: dict[str, datetime] = {}

        # Connection status
        self._redis_available = False

    async def initialize(self) -> bool:
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=10,
            )

            # Test connection
            await self.redis_client.ping()
            self._redis_available = True
            logger.info("LLM Cache initialized successfully with Redis")
            return True

        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory cache: {e}")
            self._redis_available = False
            return False

    def _normalize_prompt(self, prompt: str) -> str:
        """
        Normalize prompt for consistent caching

        - Trims whitespace
        - Normalizes Turkish characters if enabled
        - Truncates if too long
        """
        # Trim whitespace
        normalized = prompt.strip()

        # Turkish character normalization (optional)
        if self.config.turkish_normalization:
            # Normalize common Turkish variations
            replacements = {
                "İ": "i",
                "I": "i",
                "Ş": "ş",
                "Ğ": "ğ",
                "Ü": "ü",
                "Ö": "ö",
                "Ç": "ç",
            }
            for old, new in replacements.items():
                normalized = normalized.replace(old, new)

        # Truncate if too long
        if len(normalized) > self.config.max_prompt_length:
            normalized = normalized[: self.config.max_prompt_length]
            logger.debug(f"Prompt truncated to {self.config.max_prompt_length} chars")

        return normalized

    def _generate_cache_key(self, prompt: str, model: str = "default", **kwargs) -> str:
        """
        Generate unique cache key for prompt

        Args:
            prompt: The LLM prompt
            model: Model identifier (gpt-4, claude, etc.)
            **kwargs: Additional parameters affecting response

        Returns:
            SHA256 hash as cache key
        """
        # Normalize prompt
        normalized_prompt = self._normalize_prompt(prompt)

        # Include model and relevant kwargs in hash
        cache_input = {"prompt": normalized_prompt, "model": model, **kwargs}

        # Generate hash
        cache_string = json.dumps(cache_input, sort_keys=True, ensure_ascii=False)
        prompt_hash = hashlib.sha256(cache_string.encode("utf-8")).hexdigest()

        # Add prefix
        cache_key = f"{self.config.key_prefix}:{model}:{prompt_hash}"

        return cache_key

    async def get(self, prompt: str, model: str = "default", **kwargs) -> str | None:
        """
        Get cached LLM response

        Args:
            prompt: The LLM prompt
            model: Model identifier
            **kwargs: Additional parameters

        Returns:
            Cached response or None if not found
        """
        self.stats.total_requests += 1
        cache_key = self._generate_cache_key(prompt, model, **kwargs)

        try:
            # Try Redis first
            if self._redis_available and self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    entry = CacheEntry.parse_raw(cached_data)
                    self.stats.cache_hits += 1

                    # Update token/cost savings
                    if entry.token_count:
                        self.stats.total_tokens_saved += entry.token_count
                    if entry.cost:
                        self.stats.total_cost_saved += entry.cost

                    logger.debug(f"Cache HIT for key: {cache_key[:16]}...")
                    return entry.response

            # Fallback to memory cache
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                self._memory_cache_access[cache_key] = datetime.now()
                self.stats.cache_hits += 1
                logger.debug(f"Memory cache HIT for key: {cache_key[:16]}...")
                return entry.response

            # Cache miss
            self.stats.cache_misses += 1
            logger.debug(f"Cache MISS for key: {cache_key[:16]}...")
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats.cache_misses += 1
            return None

    async def set(
        self,
        prompt: str,
        response: str,
        model: str = "default",
        ttl: int | None = None,
        token_count: int | None = None,
        cost: float | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> bool:
        """
        Cache LLM response

        Args:
            prompt: The LLM prompt
            response: The LLM response to cache
            model: Model identifier
            ttl: Time to live in seconds (None = use default)
            token_count: Token count for this response
            cost: Cost in USD for this response
            metadata: Additional metadata
            **kwargs: Additional parameters

        Returns:
            True if successfully cached
        """
        cache_key = self._generate_cache_key(prompt, model, **kwargs)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        # Create cache entry
        entry = CacheEntry(
            response=response,
            prompt_hash=prompt_hash,
            model=model,
            timestamp=datetime.now(),
            token_count=token_count,
            cost=cost,
            metadata=metadata or {},
        )

        try:
            # Try Redis first
            if self._redis_available and self.redis_client:
                entry_json = entry.json()
                ttl_seconds = ttl or self.config.default_ttl

                await self.redis_client.setex(cache_key, ttl_seconds, entry_json)
                logger.debug(
                    f"Cached to Redis with TTL {ttl_seconds}s: {cache_key[:16]}..."
                )
                return True

            # Fallback to memory cache
            self._memory_cache[cache_key] = entry
            self._memory_cache_access[cache_key] = datetime.now()

            # Enforce max size (LRU eviction)
            if len(self._memory_cache) > self._memory_cache_max_size:
                # Remove oldest accessed entry
                oldest_key = min(
                    self._memory_cache_access.keys(),
                    key=lambda k: self._memory_cache_access[k],
                )
                del self._memory_cache[oldest_key]
                del self._memory_cache_access[oldest_key]
                logger.debug("Evicted oldest entry from memory cache")

            logger.debug(f"Cached to memory: {cache_key[:16]}...")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def invalidate(self, pattern: str = "*") -> int:
        """
        Invalidate cache entries matching pattern

        Args:
            pattern: Redis key pattern (e.g., "kiro2:llm:gpt-4:*")

        Returns:
            Number of keys deleted
        """
        if not self._redis_available or not self.redis_client:
            return 0

        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching '{pattern}'")
                return deleted
            return 0

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats_dict = {
            "total_requests": self.stats.total_requests,
            "cache_hits": self.stats.cache_hits,
            "cache_misses": self.stats.cache_misses,
            "hit_ratio": self.stats.hit_ratio,
            "miss_ratio": self.stats.miss_ratio,
            "total_tokens_saved": self.stats.total_tokens_saved,
            "total_cost_saved": self.stats.total_cost_saved,
            "redis_available": self._redis_available,
            "memory_cache_size": len(self._memory_cache),
        }

        # Get Redis info if available
        if self._redis_available and self.redis_client:
            try:
                info = await self.redis_client.info()
                stats_dict["redis_memory_used"] = info.get("used_memory_human", "N/A")
                stats_dict["redis_connected_clients"] = info.get("connected_clients", 0)
            except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
                pass

        return stats_dict

    async def clear_all(self) -> bool:
        """Clear entire cache (use with caution!)"""
        try:
            if self._redis_available and self.redis_client:
                await self.redis_client.flushdb()

            self._memory_cache.clear()
            self._memory_cache_access.clear()

            logger.warning("Cache cleared completely")
            return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("LLM Cache connection closed")


def cached_llm(
    ttl: int = 3600, model: str = "default", cache_instance: LLMCache | None = None
):
    """
    Decorator for caching LLM function calls

    Usage:
        @cached_llm(ttl=3600, model="gpt-4")
        async def generate_response(prompt: str) -> str:
            return await openai.ChatCompletion.create(...)
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(prompt: str, **kwargs):
            # Use provided cache instance or create default
            cache = cache_instance or LLMCache()

            # Try to get from cache
            cached_response = await cache.get(prompt, model, **kwargs)
            if cached_response:
                return cached_response

            # Generate new response
            response = await func(prompt, **kwargs)

            # Cache the response
            await cache.set(
                prompt=prompt, response=response, model=model, ttl=ttl, **kwargs
            )

            return response

        return wrapper

    return decorator


# Global cache instance
_global_llm_cache: LLMCache | None = None


async def get_llm_cache() -> LLMCache:
    """Get or create global LLM cache instance"""
    global _global_llm_cache

    if _global_llm_cache is None:
        _global_llm_cache = LLMCache()
        await _global_llm_cache.initialize()

    return _global_llm_cache


# Example usage:
"""
# Basic usage
cache = await get_llm_cache()

# Get cached response
response = await cache.get(
    prompt="What is 2+2?",
    model="gpt-4",
    temperature=0.7
)

if response:
    print(f"Cached: {response}")
else:
    # Generate new response
    response = await llm_service.generate("What is 2+2?")

    # Cache it
    await cache.set(
        prompt="What is 2+2?",
        response=response,
        model="gpt-4",
        token_count=50,
        cost=0.001
    )

# Using decorator
@cached_llm(ttl=3600, model="gpt-4")
async def ask_llm(prompt: str) -> str:
    return await openai_client.generate(prompt)

# Get stats
stats = await cache.get_stats()
print(f"Hit ratio: {stats['hit_ratio']:.2%}")
print(f"Cost saved: ${stats['total_cost_saved']:.2f}")
"""
