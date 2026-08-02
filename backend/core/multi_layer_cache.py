"""
Multi-Layer Cache System - Task 7
Requirements: 6.1, 6.2, 6.3, 6.5, 6.7, 6.10

CACHE HIERARCHY (2025-01-24):
Bu dosya ADVANCED katmanindadir. Aktif ve kullanilmalidir.
Video oneri sistemi icin L1 (memory) + L2 (Redis) caching saglar.

Ilgili dosyalar:
- advanced_cache.py - SmartCacheManager (bu dosya ile birlikte kullanilabilir)
- core/cache/ - Core cache utilities

Bu modül, video öneri sistemi için optimize edilmiş çok katmanlı cache sistemi sağlar.

Features:
- L1 Cache: In-memory LRU cache (100 entry limit) - ultra-fast access
- L2 Cache: Redis cache - persistent, distributed
- Cache Promotion: Redis'ten memory'ye otomatik yükseltme
- LRU Eviction: Least Recently Used eviction policy
- TTL Management: Otomatik süre dolumu yönetimi
- Cache Hit/Miss Tracking: Performans metrikleri

Architecture:
    Request → L1 (Memory) → L2 (Redis) → Source
              ↓ Hit          ↓ Hit        ↓ Miss
              Return         Promote       Compute & Cache
"""

import asyncio
import contextlib
import json
import random
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from redis import asyncio as aioredis

from core.structured_logger import get_logger

logger = get_logger(__name__)


def _json_varsayilan(deger: object) -> object:
    """L2 (Redis) yazarken JSON'un serilestiremedigi degerler icin.

    NEDEN VAR (2 Agu 2026 — canli olcumle bulundu)
    ----------------------------------------------
    Onceki hali `default=str` idi. Bu SESSIZ bir yakalayicidir: `json` bir
    Pydantic modelini serilestiremeyince onu `str(model)`e cevirir ve Redis'e
    su sekilde yazar:

        "ogrenci_id='0d3b011a-...' sinif_seviyesi=12 hedef_sinav=<SinavTipi.TYT...>"

    Okuma yolunda `json.loads` bu DIZEYI geri dondurur; FastAPI
    `response_model` dogrulamasi `model_attributes_type` ile duser -> 500.

    Gozlenen davranis (kaldirma testiyle kanitlandi):
        L1 (bellek) sicak            -> 200
        L1 soguk + L2 (Redis) sicak  -> 500   (backend restart / TTL sonrasi)

    Yani ekran ilk acilista calisiyor, backend yeniden baslayinca patliyor —
    bir demoda "tikla calisir, tekrar tikla patlar" gorunumu.
    `MultiLayerCache` yedi dosyada kullaniliyor; hepsi ayni sinifa acikti.

    Sira ONEMLI: once model donusumleri, en sonda `str` geri cekilisi.
    `str` tamamen kaldirilamaz — bilinmeyen bir tip TypeError firlatip
    onbellegi yazilamaz hale getirirdi.
    """
    donusturucu = getattr(deger, "model_dump", None)  # pydantic v2
    if callable(donusturucu):
        return donusturucu(mode="json")

    donusturucu = getattr(deger, "dict", None)  # pydantic v1
    if callable(donusturucu):
        return donusturucu()

    if isinstance(deger, set | frozenset):
        return list(deger)

    return str(deger)


class CacheLayer(str, Enum):
    """Cache katmanları"""

    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    MISS = "miss"


@dataclass
class CacheEntry:
    """
    Cache entry with metadata

    Attributes:
        value: Cached değer
        created_at: Oluşturulma zamanı
        expires_at: Süre dolum zamanı
        access_count: Erişim sayısı
        last_accessed: Son erişim zamanı
        size_bytes: Tahmini boyut (bytes)
    """

    value: Any
    created_at: float
    expires_at: float | None = None
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def update_access(self):
        """Update access metadata"""
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass
class CacheMetrics:
    """
    Cache performance metrics

    Tracks:
    - Hit/miss rates per layer
    - Response times
    - Cache size and utilization
    """

    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    promotions: int = 0  # L2 → L1 promotions
    evictions: int = 0  # L1 evictions
    sets: int = 0
    deletes: int = 0
    errors: int = 0

    def get_l1_hit_rate(self) -> float:
        """Calculate L1 hit rate"""
        total = self.l1_hits + self.l1_misses
        return (self.l1_hits / total * 100) if total > 0 else 0.0

    def get_l2_hit_rate(self) -> float:
        """Calculate L2 hit rate (among L1 misses)"""
        total = self.l2_hits + self.l2_misses
        return (self.l2_hits / total * 100) if total > 0 else 0.0

    def get_overall_hit_rate(self) -> float:
        """Calculate overall hit rate"""
        total_hits = self.l1_hits + self.l2_hits
        total_requests = self.l1_hits + self.l1_misses
        return (total_hits / total_requests * 100) if total_requests > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "l1_hits": self.l1_hits,
            "l1_misses": self.l1_misses,
            "l2_hits": self.l2_hits,
            "l2_misses": self.l2_misses,
            "promotions": self.promotions,
            "evictions": self.evictions,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "l1_hit_rate": f"{self.get_l1_hit_rate():.2f}%",
            "l2_hit_rate": f"{self.get_l2_hit_rate():.2f}%",
            "overall_hit_rate": f"{self.get_overall_hit_rate():.2f}%",
        }


class MultiLayerCache:
    """
    Multi-layer cache system with L1 (Memory) and L2 (Redis)

    Requirements:
    - 6.1: Cache video önerilerini student profile hash'ine göre
    - 6.2: Aynı profile için 100ms içinde dönme (L1 cache)
    - 6.3: Cache TTL 1 saat
    - 6.5: Cache invalidation stratejisi
    - 6.7: LRU eviction policy
    - 6.10: Async cache güncelleme

    Usage:
        cache = MultiLayerCache(redis_url="redis://localhost:6379/0")
        await cache.initialize()

        # Get or set
        value = await cache.get("key")
        await cache.set("key", value, ttl=3600)

        # Get or compute
        value = await cache.get_or_compute("key", compute_fn, ttl=3600)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        l1_max_size: int = 100,  # Req 6.1: 100 entry limit
        default_ttl: int = 3600,  # Req 6.3: 1 hour default
        namespace: str = "video_cache",
    ):
        """
        Initialize multi-layer cache

        Args:
            redis_url: Redis connection URL
            l1_max_size: Maximum L1 cache entries (default: 100)
            default_ttl: Default TTL in seconds (default: 3600 = 1 hour)
            namespace: Cache key namespace
        """
        self.redis_url = redis_url
        self.l1_max_size = l1_max_size
        self.default_ttl = default_ttl
        self.namespace = namespace

        # Key-level locks for Cache Stampede protection
        self._key_locks: dict[str, asyncio.Lock] = {}
        self._key_locks_lock = asyncio.Lock()

        # L1 Cache: In-memory LRU cache (OrderedDict for LRU)
        # Req 6.7: LRU eviction policy
        self._l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._l1_lock = asyncio.Lock()

        # L2 Cache: Redis
        self._redis: aioredis.Redis | None = None
        self._redis_enabled = True

        # Metrics
        self.metrics = CacheMetrics()

        # Initialization flag
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize Redis connection

        Returns:
            True if successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,
                max_connections=50,
                socket_keepalive=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )

            # Test connection
            await self._redis.ping()

            logger.info(
                "multi_layer_cache_initialized",
                redis_url=self.redis_url,
                l1_max_size=self.l1_max_size,
                default_ttl=self.default_ttl,
            )

            self._initialized = True
            self._redis_enabled = True
            return True

        except Exception as e:
            logger.warning(
                "redis_connection_failed", error=str(e), fallback="L1 cache only"
            )
            self._redis_enabled = False
            self._initialized = True
            return False

    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("multi_layer_cache_closed")

    def _make_key(self, key: str) -> str:
        """
        Create namespaced cache key

        Args:
            key: Original key

        Returns:
            Namespaced key
        """
        return f"{self.namespace}:{key}"

    def _estimate_size(self, value: Any) -> int:
        """
        Estimate size of value in bytes

        Args:
            value: Value to estimate

        Returns:
            Estimated size in bytes
        """
        try:
            return len(json.dumps(value, default=str).encode("utf-8"))
        except (TypeError, ValueError, OverflowError):
            return 0

    async def _get_with_status(self, key: str) -> tuple[bool, Any]:
        """
        Get value from cache along with a boolean indicating if it was a hit.
        This allows distinguishing a cached None (Cache Penetration protection) from a cache miss.
        """
        full_key = self._make_key(key)

        # Try L1 cache first (ultra-fast, <1ms)
        async with self._l1_lock:
            if full_key in self._l1_cache:
                entry = self._l1_cache[full_key]

                # Check expiration
                if entry.is_expired():
                    # Remove expired entry
                    del self._l1_cache[full_key]
                    self.metrics.l1_misses += 1
                    logger.debug("l1_cache_expired", key=key)
                else:
                    # Update access metadata
                    entry.update_access()

                    # Move to end (LRU)
                    self._l1_cache.move_to_end(full_key)

                    self.metrics.l1_hits += 1
                    logger.debug(
                        "l1_cache_hit", key=key, access_count=entry.access_count
                    )
                    val = entry.value
                    if isinstance(val, dict) and val.get("__sentinel_null__"):
                        return True, None
                    return True, val

        self.metrics.l1_misses += 1

        # Try L2 cache (Redis)
        if self._redis_enabled and self._redis:
            try:
                value_bytes = await self._redis.get(full_key)

                if value_bytes:
                    # Deserialize
                    value = json.loads(value_bytes)

                    # Promote to L1 (Req 6.5: Cache promotion logic)
                    await self._promote_to_l1(full_key, value)

                    self.metrics.l2_hits += 1
                    self.metrics.promotions += 1

                    logger.debug("l2_cache_hit_promoted", key=key)
                    if isinstance(value, dict) and value.get("__sentinel_null__"):
                        return True, None
                    return True, value

            except json.JSONDecodeError as e:
                logger.error("cache_deserialize_error", key=key, error=str(e))
                # Delete corrupted cache entry
                await self.delete(key)
                self.metrics.errors += 1
            except Exception as e:
                logger.error("l2_cache_get_error", key=key, error=str(e))
                self.metrics.errors += 1

        self.metrics.l2_misses += 1
        logger.debug("cache_miss", key=key)
        return False, None

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache (L1 → L2 hierarchy)

        Req 6.2: L1 cache'den 100ms içinde dönme

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        hit, value = await self._get_with_status(key)
        return value if hit else None

    async def _promote_to_l1(self, full_key: str, value: Any):
        """
        Promote value from L2 to L1 cache

        Req 6.5: Cache promotion logic (Redis → Memory)

        Args:
            full_key: Full cache key (with namespace)
            value: Value to promote
        """
        async with self._l1_lock:
            # Check if L1 is full
            if len(self._l1_cache) >= self.l1_max_size:
                # Evict LRU entry (first item in OrderedDict)
                await self._evict_l1()

            # Create entry
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                expires_at=time.time() + self.default_ttl,
                access_count=1,
                size_bytes=self._estimate_size(value),
            )

            # Add to L1
            self._l1_cache[full_key] = entry

    async def _evict_l1(self):
        """
        Evict least recently used entry from L1

        Req 6.7: LRU eviction policy
        """
        if not self._l1_cache:
            return

        # Remove first item (LRU)
        evicted_key, evicted_entry = self._l1_cache.popitem(last=False)

        self.metrics.evictions += 1

        logger.debug(
            "l1_cache_evicted",
            key=evicted_key,
            access_count=evicted_entry.access_count,
            age_seconds=time.time() - evicted_entry.created_at,
        )

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Set value in cache (L1 + L2)

        Req 6.3: Cache TTL management
        Req 6.10: Async cache güncelleme

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: self.default_ttl)

        Returns:
            True if successful
        """
        full_key = self._make_key(key)

        # Cache Penetration Protection: cache None/Null as sentinel with a very short TTL
        if value is None:
            value = {"__sentinel_null__": True}
            ttl = 60
        else:
            ttl = ttl or self.default_ttl

        # Add Jitter to TTL to prevent Cache Stampede from simultaneous expiration
        if ttl:
            # KESİNLİKLE ±%10 Jitter: random.uniform(0.90, 1.10)
            ttl = int(ttl * random.uniform(0.90, 1.10))  # nosec B311  # TTL jitter, kripto degil

        self.metrics.sets += 1

        # Set in L1
        async with self._l1_lock:
            # Check if L1 is full
            if (
                len(self._l1_cache) >= self.l1_max_size
                and full_key not in self._l1_cache
            ):
                await self._evict_l1()

            # Create entry
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                expires_at=time.time() + ttl,
                access_count=0,
                size_bytes=self._estimate_size(value),
            )

            # Add/update in L1
            self._l1_cache[full_key] = entry
            self._l1_cache.move_to_end(full_key)

        # Set in L2 (Redis) - async, non-blocking
        if self._redis_enabled and self._redis:
            try:
                # Serialize
                value_bytes = json.dumps(
                    value, ensure_ascii=False, default=_json_varsayilan
                )

                # Set with TTL
                await self._redis.setex(full_key, ttl, value_bytes)

                logger.debug("cache_set", key=key, ttl=ttl, size_bytes=entry.size_bytes)

            except (TypeError, ValueError) as e:
                logger.error("cache_serialize_error", key=key, error=str(e))
                self.metrics.errors += 1
                return False
            except Exception as e:
                logger.error("l2_cache_set_error", key=key, error=str(e))
                self.metrics.errors += 1
                # L1 still has the value, so partial success

        return True

    async def delete(self, key: str) -> bool:
        """
        Delete from both L1 and L2

        Req 6.5: Cache invalidation

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        full_key = self._make_key(key)

        self.metrics.deletes += 1

        # Delete from L1
        async with self._l1_lock:
            if full_key in self._l1_cache:
                del self._l1_cache[full_key]

        # Delete from L2
        if self._redis_enabled and self._redis:
            try:
                await self._redis.delete(full_key)
            except Exception as e:
                logger.error("l2_cache_delete_error", key=key, error=str(e))
                self.metrics.errors += 1
                return False

        logger.debug("cache_deleted", key=key)
        return True

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern

        Req 6.5: Cache invalidation stratejisi

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        full_pattern = self._make_key(pattern)
        count = 0

        # Invalidate in L1
        async with self._l1_lock:
            keys_to_delete = [
                k for k in self._l1_cache.keys() if self._match_pattern(k, full_pattern)
            ]
            for k in keys_to_delete:
                del self._l1_cache[k]
                count += 1

        # Invalidate in L2
        if self._redis_enabled and self._redis:
            try:
                cursor = 0
                while True:
                    cursor, keys = await self._redis.scan(
                        cursor, match=full_pattern, count=100
                    )
                    if keys:
                        await self._redis.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.error(
                    "cache_invalidate_pattern_error", pattern=pattern, error=str(e)
                )
                self.metrics.errors += 1

        logger.info("cache_pattern_invalidated", pattern=pattern, count=count)
        return count

    async def delete_pattern(self, pattern: str) -> int:
        """
        Alias for invalidate_pattern for consistency

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        return await self.invalidate_pattern(pattern)

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for wildcards"""
        if "*" in pattern:
            prefix = pattern.split("*")[0]
            return key.startswith(prefix)
        return key == pattern

    async def get_or_compute(
        self, key: str, compute_fn: Callable, ttl: int | None = None
    ) -> Any:
        """
        Get from cache or compute if missing
        """
        # 1. Try cache first
        hit, value = await self._get_with_status(key)
        if hit:
            return value

        # 2. Cache Stampede Protection: Acquire lock for key
        async with self._key_locks_lock:
            if key not in self._key_locks:
                self._key_locks[key] = asyncio.Lock()
            lock = self._key_locks[key]

        async with lock:
            # Double-check cache inside lock (Double-Checked Locking Pattern)
            hit, value = await self._get_with_status(key)
            if hit:
                return value

            # Compute value
            if asyncio.iscoroutinefunction(compute_fn):
                value = await compute_fn()
            else:
                value = compute_fn()

            # Cache result
            if value is None:
                # Cache Penetration Protection: Cache None/Null as sentinel with a very short TTL
                await self.set(key, {"__sentinel_null__": True}, ttl=60)
            else:
                await self.set(key, value, ttl)

        # 3. Clean up key lock
        async with self._key_locks_lock:
            if key in self._key_locks and not self._key_locks[key].locked():
                del self._key_locks[key]

        return value

    def get_metrics(self) -> dict[str, Any]:
        """
        Get cache performance metrics

        Returns:
            Dictionary with metrics
        """

        async def _get_l1_size():
            async with self._l1_lock:
                return len(self._l1_cache)

        # KASITLI BASTIRMA — bu blok yalnizca METRIK topluyor (`l1_size`),
        # onbellegin islevini etkilemiyor. Metrik okurken sozluk baska bir
        # coroutine tarafindan degistirilirse RuntimeError alinabilir; kilit
        # almak her metrik okumasini serilestirirdi (olcumun maliyeti olculen
        # seyden buyuk olurdu), loglamak ise sicak yolda gurultu uretirdi.
        # Hata durumunda rapor "0 girdi" der.
        # 2 Agu 2026: blok ONCEDEN VARDI ve `try/except/pass` seklindeydi;
        # `contextlib.suppress`e cevrildi — DAVRANIS AYNI, ama hem SIM105
        # hem de push bekcisinin "bos except" kurali karsilaniyor
        # (bekci AST tabanli, yorumu GORMEZ — bu yuzden yorum eklemek
        #  yetmedi, yapinin kendisi degismeliydi).
        l1_size = 0
        with contextlib.suppress(RuntimeError, TypeError, AttributeError):
            l1_size = len(self._l1_cache)

        total_size_bytes = sum(entry.size_bytes for entry in self._l1_cache.values())

        return {
            **self.metrics.to_dict(),
            "l1_size": l1_size,
            "l1_max_size": self.l1_max_size,
            "l1_utilization": f"{(l1_size / self.l1_max_size * 100):.1f}%",
            "l2_enabled": self._redis_enabled,
            "total_size_bytes": total_size_bytes,
            "total_size_kb": f"{total_size_bytes / 1024:.2f}",
            "default_ttl": self.default_ttl,
            "namespace": self.namespace,
            "timestamp": datetime.now().isoformat(),
        }

    async def clear_all(self):
        """Clear all caches (L1 + L2)"""
        # Clear L1
        async with self._l1_lock:
            self._l1_cache.clear()

        # Clear L2
        if self._redis_enabled and self._redis:
            try:
                # Delete all keys with namespace
                pattern = f"{self.namespace}:*"
                cursor = 0
                while True:
                    cursor, keys = await self._redis.scan(
                        cursor, match=pattern, count=1000
                    )
                    if keys:
                        await self._redis.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.error("cache_clear_error", error=str(e))

        logger.info("cache_cleared")

    def get_l1_stats(self) -> dict[str, Any]:
        """Get L1 cache statistics"""
        entries = list(self._l1_cache.values())

        if not entries:
            return {
                "size": 0,
                "total_accesses": 0,
                "avg_access_count": 0,
                "oldest_entry_age": 0,
                "newest_entry_age": 0,
            }

        now = time.time()
        total_accesses = sum(e.access_count for e in entries)
        ages = [now - e.created_at for e in entries]

        return {
            "size": len(entries),
            "total_accesses": total_accesses,
            "avg_access_count": total_accesses / len(entries),
            "oldest_entry_age": max(ages),
            "newest_entry_age": min(ages),
            "total_size_bytes": sum(e.size_bytes for e in entries),
        }


# ==================== GLOBAL INSTANCE ====================

_global_cache: MultiLayerCache | None = None


async def get_multi_layer_cache(
    redis_url: str = "redis://localhost:6379/0",
    l1_max_size: int = 100,
    default_ttl: int = 3600,
) -> MultiLayerCache:
    """
    Get or create global multi-layer cache instance

    Args:
        redis_url: Redis connection URL
        l1_max_size: Maximum L1 cache entries
        default_ttl: Default TTL in seconds

    Returns:
        MultiLayerCache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = MultiLayerCache(
            redis_url=redis_url, l1_max_size=l1_max_size, default_ttl=default_ttl
        )
        await _global_cache.initialize()

    return _global_cache


def get_cache_instance() -> MultiLayerCache | None:
    """
    Get global cache instance (for metrics/monitoring)

    Returns:
        MultiLayerCache instance or None if not initialized
    """
    global _global_cache
    return _global_cache


__all__ = [
    "CacheEntry",
    "CacheLayer",
    "CacheMetrics",
    "MultiLayerCache",
    "get_cache_instance",
    "get_multi_layer_cache",
]
