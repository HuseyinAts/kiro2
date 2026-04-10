"""
Redis Cache Manager - Performance Optimization
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from redis import asyncio as aioredis

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """Cache connection status"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class ConnectionMetrics:
    """Cache connection metrics"""

    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0
    reconnection_attempts: int = 0
    last_connection_time: datetime | None = None
    last_error_time: datetime | None = None
    last_error_message: str | None = None

    def to_dict(self) -> dict:
        """Convert metrics to dictionary"""
        return {
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "failed_connections": self.failed_connections,
            "reconnection_attempts": self.reconnection_attempts,
            "last_connection_time": self.last_connection_time.isoformat()
            if self.last_connection_time
            else None,
            "last_error_time": self.last_error_time.isoformat()
            if self.last_error_time
            else None,
            "last_error_message": self.last_error_message,
        }


class CacheManager:
    """Gelişmiş Redis cache yönetimi"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = None
        self.redis_url = redis_url
        self.hit_count = 0
        self.miss_count = 0
        self.enabled = True
        self._initialized = False
        self._init_lock = None

    async def initialize(self) -> bool:
        """Redis bağlantısı kur"""
        try:
            import os

            max_conn = int(os.getenv("REDIS_MAX_CONNECTIONS", "100"))
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,
                max_connections=max_conn,
                socket_keepalive=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )

            # Bağlantıyı test et
            await self.redis.ping()
            logger.info("Redis bağlantısı başarılı (max_connections=%d)", max_conn)
            return True

        except Exception as e:
            logger.error("Redis bağlantı hatası: %s — cache devre dışı", e)
            self.enabled = False
            return False

    async def _ensure_initialized(self):
        """Lazy initialization - ilk kullanımda initialize et"""
        if self._initialized:
            return

        if self._init_lock is None:
            import asyncio

            self._init_lock = asyncio.Lock()

        async with self._init_lock:
            if self._initialized:
                return
            await self.initialize()
            self._initialized = True

    async def close(self):
        """Redis bağlantısını kapat"""
        if self.redis:
            await self.redis.close()

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Cache key oluştur"""
        data = str(args) + str(sorted(kwargs.items()))
        hash_key = hashlib.md5(data.encode()).hexdigest()
        return f"{prefix}:{hash_key}"

    async def get(self, key: str) -> Any | None:
        """Cache'den veri al"""
        await self._ensure_initialized()

        if not self.enabled or not self.redis:
            return None

        try:
            cached = await self.redis.get(key)
            if cached:
                self.hit_count += 1
                # SECURITY FIX: JSON deserialization (safe, prevents RCE)
                return json.loads(cached)

            self.miss_count += 1
            return None

        except json.JSONDecodeError as e:
            print(f"Cache JSON decode error: {e}")
            # Invalid cache data, delete it
            await self.delete(key)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Cache'e veri kaydet"""
        await self._ensure_initialized()

        if not self.enabled or not self.redis:
            return False

        try:
            # SECURITY FIX: JSON serialization (safe, prevents RCE)
            # Note: Only JSON-serializable types supported (dict, list, str, int, float, bool, None)
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await self.redis.setex(key, ttl, serialized)
            return True

        except (TypeError, ValueError) as e:
            print(f"Cache serialization error (non-JSON-serializable): {e}")
            return False
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def get_or_set(self, key: str, factory_func: callable, ttl: int = 300) -> Any:
        """Cache'den al veya hesapla ve kaydet"""

        # Cache'den kontrol et
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Cache miss - hesapla
        result = await factory_func()

        # Cache'e kaydet
        await self.set(key, result, ttl)

        return result

    async def delete(self, key: str) -> bool:
        """Cache'den sil"""
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("Cache delete error: %s", e)
            return False

    async def invalidate_pattern(self, pattern: str):
        """Pattern'e uyan tüm cache'leri temizle (pipeline ile batch delete)"""
        if not self.enabled or not self.redis:
            return

        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=1000)
                if keys:
                    pipe = self.redis.pipeline()
                    for key in keys:
                        pipe.delete(key)
                    await pipe.execute()
                if cursor == 0:
                    break
        except Exception as e:
            logger.error("Cache invalidate error: %s", e)

    def get_stats(self) -> dict:
        """Cache istatistikleri"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0

        return {
            "enabled": self.enabled,
            "hits": self.hit_count,
            "misses": self.miss_count,
            "total_requests": total,
            "hit_rate": f"{hit_rate:.2f}%",
            "timestamp": datetime.now().isoformat(),
        }

    async def clear_all(self):
        """Tüm cache'i temizle"""
        if not self.enabled or not self.redis:
            return

        try:
            await self.redis.flushdb()
            print("[OK] Cache temizlendi")
        except Exception as e:
            print(f"Cache clear error: {e}")


# Global instance — env var'dan URL oku, fallback localhost
cache_manager = CacheManager(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)


# Cache decorator functions
def cache_result(prefix: str, expire: int = 300):
    """
    Generic cache decorator

    Args:
        prefix: Cache key prefix
        expire: Expiration time in seconds
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                return cached

            # Cache miss - execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, ttl=expire)

            return result

        return wrapper

    return decorator


def cache_learning_style(expire: int = 7200):
    """Cache decorator for learning style data (2 hours)"""
    return cache_result("learning_style", expire=expire)


def cache_exam_results(expire: int = 86400):
    """Cache decorator for exam results (24 hours)"""
    return cache_result("exam_results", expire=expire)


def cache_recommendations(expire: int = 3600):
    """Cache decorator for recommendations (1 hour)"""
    return cache_result("recommendations", expire=expire)


def cache_content(expire: int = 1800):
    """Cache decorator for content (30 minutes)"""
    return cache_result("content", expire=expire)


# Alias for backwards compatibility and API consistency
CacheService = CacheManager

__all__ = [
    "CacheManager",
    "CacheService",  # Alias for CacheManager
    "ConnectionMetrics",
    "ConnectionStatus",
    "cache_content",
    "cache_exam_results",
    "cache_learning_style",
    "cache_manager",
    "cache_recommendations",
    "cache_result",
]
