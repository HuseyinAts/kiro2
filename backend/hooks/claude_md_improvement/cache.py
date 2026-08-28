"""
CLAUDE.md Self-Improvement için Redis Cache Layer.

REQ-10.6: Redis cache entegrasyonu.
KIRO2 performans optimizasyonu için cache mekanizması.

Boris Cherny Standards - Verification Feedback Loops
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheKeyPrefix(str, Enum):
    """Cache key prefix'leri."""

    RULE_EFFECTIVENESS = "claude_md:rule_eff"
    PATTERN = "claude_md:pattern"
    FEEDBACK = "claude_md:feedback"
    AB_TEST = "claude_md:ab_test"
    META_LEARNING = "claude_md:meta"
    DOC_UPDATE = "claude_md:doc"
    APPROVAL = "claude_md:approval"


@dataclass
class CacheConfig:
    """Cache konfigürasyonu."""

    # Redis bağlantı ayarları
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None

    # TTL ayarları (saniye)
    rule_effectiveness_ttl: int = 3600  # 1 saat
    pattern_ttl: int = 7200  # 2 saat
    feedback_ttl: int = 86400  # 24 saat
    ab_test_ttl: int = 1800  # 30 dakika
    meta_learning_ttl: int = 14400  # 4 saat

    # Performans ayarları
    max_connections: int = 10
    socket_timeout: float = 5.0
    decode_responses: bool = True

    @property
    def redis_url(self) -> str:
        """Redis URL oluştur."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ImprovementCache:
    """
    CLAUDE.md Self-Improvement için Redis cache layer.

    REQ-10.6 Implementation.

    Features:
    - Rule effectiveness caching
    - Pattern detection caching
    - A/B test results caching
    - Automatic TTL management
    - Cache invalidation
    """

    def __init__(self, config: CacheConfig | None = None):
        """
        Cache'i başlat.

        Args:
            config: Cache konfigürasyonu
        """
        self.config = config or CacheConfig()
        self._redis: Any | None = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Redis'e bağlan.

        Returns:
            Bağlantı başarılı ise True
        """
        try:
            import redis.asyncio as aioredis

            self._redis = await aioredis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=self.config.decode_responses,
                socket_timeout=self.config.socket_timeout,
            )

            # Bağlantı testi
            await self._redis.ping()
            self._connected = True
            logger.info("Redis cache bağlantısı başarılı")
            return True

        except ImportError:
            logger.warning("redis.asyncio import edilemedi, cache devre dışı")
            self._connected = False
            return False

        except Exception as e:
            logger.error(f"Redis bağlantı hatası: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Redis bağlantısını kapat."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Redis cache bağlantısı kapatıldı")

    @property
    def is_connected(self) -> bool:
        """Cache bağlantı durumu."""
        return self._connected

    def _make_key(self, prefix: CacheKeyPrefix, *parts: str) -> str:
        """
        Cache key oluştur.

        Args:
            prefix: Key prefix
            *parts: Key parçaları

        Returns:
            Tam cache key
        """
        key_parts = [prefix.value] + list(parts)
        return ":".join(key_parts)

    def _hash_content(self, content: str) -> str:
        """İçerik hash'i oluştur."""
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:12]

    # =========================================================================
    # RULE EFFECTIVENESS CACHE
    # =========================================================================

    async def get_rule_effectiveness(self, rule_id: str) -> float | None:
        """
        Kural etkinlik skorunu cache'den al.

        Args:
            rule_id: Kural ID'si

        Returns:
            Etkinlik skoru veya None
        """
        if not self._connected:
            return None

        try:
            key = self._make_key(CacheKeyPrefix.RULE_EFFECTIVENESS, rule_id)
            value = await self._redis.get(key)

            if value:
                return float(value)
            return None

        except Exception as e:
            logger.error(f"Cache get hatası: {e}")
            return None

    async def set_rule_effectiveness(
        self, rule_id: str, score: float, ttl: int | None = None
    ) -> bool:
        """
        Kural etkinlik skorunu cache'e yaz.

        Args:
            rule_id: Kural ID'si
            score: Etkinlik skoru
            ttl: TTL (saniye), None ise varsayılan

        Returns:
            Başarılı ise True
        """
        if not self._connected:
            return False

        try:
            key = self._make_key(CacheKeyPrefix.RULE_EFFECTIVENESS, rule_id)
            ttl = ttl or self.config.rule_effectiveness_ttl

            await self._redis.setex(key, ttl, str(score))
            return True

        except Exception as e:
            logger.error(f"Cache set hatası: {e}")
            return False

    async def invalidate_rule(self, rule_id: str) -> bool:
        """
        Kural cache'ini geçersiz kıl.

        Args:
            rule_id: Kural ID'si

        Returns:
            Başarılı ise True
        """
        if not self._connected:
            return False

        try:
            key = self._make_key(CacheKeyPrefix.RULE_EFFECTIVENESS, rule_id)
            await self._redis.delete(key)
            logger.info(f"Cache invalidate: {rule_id}")
            return True

        except Exception as e:
            logger.error(f"Cache invalidate hatası: {e}")
            return False

    async def get_all_rule_scores(self) -> dict[str, float]:
        """
        Tüm kural skorlarını al.

        Returns:
            {rule_id: score} dict
        """
        if not self._connected:
            return {}

        try:
            pattern = self._make_key(CacheKeyPrefix.RULE_EFFECTIVENESS, "*")
            scores = {}

            async for key in self._redis.scan_iter(pattern):
                rule_id = key.split(":")[-1]
                value = await self._redis.get(key)
                if value:
                    scores[rule_id] = float(value)

            return scores

        except Exception as e:
            logger.error(f"Cache scan hatası: {e}")
            return {}

    # =========================================================================
    # PATTERN CACHE
    # =========================================================================

    async def get_pattern(self, pattern_id: str) -> dict[str, Any] | None:
        """
        Pattern verisini cache'den al.

        Args:
            pattern_id: Pattern ID'si

        Returns:
            Pattern verisi veya None
        """
        if not self._connected:
            return None

        try:
            key = self._make_key(CacheKeyPrefix.PATTERN, pattern_id)
            value = await self._redis.get(key)

            if value:
                return json.loads(value)
            return None

        except Exception as e:
            logger.error(f"Pattern cache get hatası: {e}")
            return None

    async def set_pattern(
        self, pattern_id: str, data: dict[str, Any], ttl: int | None = None
    ) -> bool:
        """
        Pattern verisini cache'e yaz.

        Args:
            pattern_id: Pattern ID'si
            data: Pattern verisi
            ttl: TTL (saniye)

        Returns:
            Başarılı ise True
        """
        if not self._connected:
            return False

        try:
            key = self._make_key(CacheKeyPrefix.PATTERN, pattern_id)
            ttl = ttl or self.config.pattern_ttl

            await self._redis.setex(key, ttl, json.dumps(data))
            return True

        except Exception as e:
            logger.error(f"Pattern cache set hatası: {e}")
            return False

    # =========================================================================
    # FEEDBACK CACHE
    # =========================================================================

    async def cache_feedback_batch(
        self, rule_id: str, feedbacks: list[dict[str, Any]]
    ) -> bool:
        """
        Feedback batch'ini cache'e yaz.

        Args:
            rule_id: Kural ID'si
            feedbacks: Feedback listesi

        Returns:
            Başarılı ise True
        """
        if not self._connected:
            return False

        try:
            key = self._make_key(CacheKeyPrefix.FEEDBACK, rule_id)
            ttl = self.config.feedback_ttl

            # Mevcut feedback'leri al
            existing = await self._redis.get(key)
            if existing:
                existing_data = json.loads(existing)
            else:
                existing_data = []

            # Yeni feedback'leri ekle
            existing_data.extend(feedbacks)

            # Son 1000 feedback'i tut
            if len(existing_data) > 1000:
                existing_data = existing_data[-1000:]

            await self._redis.setex(key, ttl, json.dumps(existing_data))
            return True

        except Exception as e:
            logger.error(f"Feedback cache hatası: {e}")
            return False

    async def get_cached_feedbacks(
        self, rule_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Cache'den feedback'leri al.

        Args:
            rule_id: Kural ID'si
            limit: Maksimum feedback sayısı

        Returns:
            Feedback listesi
        """
        if not self._connected:
            return []

        try:
            key = self._make_key(CacheKeyPrefix.FEEDBACK, rule_id)
            value = await self._redis.get(key)

            if value:
                feedbacks = json.loads(value)
                return feedbacks[-limit:]
            return []

        except Exception as e:
            logger.error(f"Feedback cache get hatası: {e}")
            return []

    # =========================================================================
    # A/B TEST CACHE
    # =========================================================================

    async def cache_ab_test_result(self, test_id: str, result: dict[str, Any]) -> bool:
        """
        A/B test sonucunu cache'e yaz.

        Args:
            test_id: Test ID'si
            result: Test sonucu

        Returns:
            Başarılı ise True
        """
        if not self._connected:
            return False

        try:
            key = self._make_key(CacheKeyPrefix.AB_TEST, test_id)
            ttl = self.config.ab_test_ttl

            await self._redis.setex(key, ttl, json.dumps(result))
            return True

        except Exception as e:
            logger.error(f"A/B test cache hatası: {e}")
            return False

    async def get_ab_test_result(self, test_id: str) -> dict[str, Any] | None:
        """
        A/B test sonucunu cache'den al.

        Args:
            test_id: Test ID'si

        Returns:
            Test sonucu veya None
        """
        if not self._connected:
            return None

        try:
            key = self._make_key(CacheKeyPrefix.AB_TEST, test_id)
            value = await self._redis.get(key)

            if value:
                return json.loads(value)
            return None

        except Exception as e:
            logger.error(f"A/B test cache get hatası: {e}")
            return None

    # =========================================================================
    # APPROVAL WORKFLOW CACHE
    # =========================================================================

    async def cache_pending_approval(
        self,
        request_id: str,
        changes: dict[str, Any],
        ttl: int = 86400,  # 24 saat
    ) -> bool:
        """
        Bekleyen onay isteğini cache'e yaz.

        Args:
            request_id: İstek ID'si
            changes: Değişiklikler
            ttl: TTL (saniye)

        Returns:
            Başarılı ise True
        """
        if not self._connected:
            return False

        try:
            key = self._make_key(CacheKeyPrefix.APPROVAL, request_id)
            data = {
                "changes": changes,
                "created_at": datetime.now(UTC).isoformat(),
                "status": "pending",
            }

            await self._redis.setex(key, ttl, json.dumps(data))
            return True

        except Exception as e:
            logger.error(f"Approval cache hatası: {e}")
            return False

    async def get_pending_approval(self, request_id: str) -> dict[str, Any] | None:
        """
        Bekleyen onay isteğini al.

        Args:
            request_id: İstek ID'si

        Returns:
            Onay verisi veya None
        """
        if not self._connected:
            return None

        try:
            key = self._make_key(CacheKeyPrefix.APPROVAL, request_id)
            value = await self._redis.get(key)

            if value:
                return json.loads(value)
            return None

        except Exception as e:
            logger.error(f"Approval cache get hatası: {e}")
            return None

    async def remove_pending_approval(self, request_id: str) -> bool:
        """
        Onay isteğini sil.

        Args:
            request_id: İstek ID'si

        Returns:
            Başarılı ise True
        """
        if not self._connected:
            return False

        try:
            key = self._make_key(CacheKeyPrefix.APPROVAL, request_id)
            await self._redis.delete(key)
            return True

        except Exception as e:
            logger.error(f"Approval cache delete hatası: {e}")
            return False

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    async def clear_all(self, prefix: CacheKeyPrefix | None = None) -> int:
        """
        Cache'i temizle.

        Args:
            prefix: Sadece bu prefix'li key'leri sil

        Returns:
            Silinen key sayısı
        """
        if not self._connected:
            return 0

        try:
            if prefix:
                pattern = f"{prefix.value}:*"
            else:
                pattern = "claude_md:*"

            count = 0
            async for key in self._redis.scan_iter(pattern):
                await self._redis.delete(key)
                count += 1

            logger.info(f"Cache temizlendi: {count} key silindi")
            return count

        except Exception as e:
            logger.error(f"Cache clear hatası: {e}")
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """
        Cache istatistiklerini al.

        Returns:
            İstatistik dict'i
        """
        if not self._connected:
            return {"connected": False}

        try:
            info = await self._redis.info()

            # Prefix başına key sayısı
            prefix_counts = {}
            for prefix in CacheKeyPrefix:
                pattern = f"{prefix.value}:*"
                count = 0
                async for _ in self._redis.scan_iter(pattern):
                    count += 1
                prefix_counts[prefix.name] = count

            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": sum(prefix_counts.values()),
                "keys_by_prefix": prefix_counts,
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }

        except Exception as e:
            logger.error(f"Cache stats hatası: {e}")
            return {"connected": True, "error": str(e)}

    async def health_check(self) -> bool:
        """
        Cache sağlık kontrolü.

        Returns:
            Sağlıklı ise True
        """
        if not self._connected:
            return False

        try:
            await self._redis.ping()
            return True
        except Exception:
            return False


# =============================================================================
# IN-MEMORY FALLBACK CACHE
# =============================================================================


@dataclass
class CacheEntry:
    """Tek bir cache girişi."""

    value: Any
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


class InMemoryCache:
    """
    Redis kullanılamadığında fallback cache.

    Thread-safe değil, sadece single-threaded kullanım için.
    """

    def __init__(self, max_size: int = 10000):
        """
        In-memory cache başlat.

        Args:
            max_size: Maksimum entry sayısı
        """
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        """Key'e karşılık gelen değeri al."""
        entry = self._cache.get(key)

        if entry is None:
            return None

        if datetime.now(UTC) > entry.expires_at:
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Değeri cache'e yaz."""
        # Max size kontrolü
        if len(self._cache) >= self._max_size:
            self._evict_expired()

            if len(self._cache) >= self._max_size:
                # En eski entry'yi sil
                oldest_key = min(
                    self._cache.keys(), key=lambda k: self._cache[k].created_at
                )
                del self._cache[oldest_key]

        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
        return True

    def delete(self, key: str) -> bool:
        """Key'i sil."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def _evict_expired(self) -> int:
        """Süresi dolmuş entry'leri temizle."""
        now = datetime.now(UTC)
        expired_keys = [k for k, v in self._cache.items() if now > v.expires_at]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def clear(self) -> int:
        """Tüm cache'i temizle."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def stats(self) -> dict[str, Any]:
        """Cache istatistikleri."""
        self._evict_expired()
        return {
            "type": "in_memory",
            "total_keys": len(self._cache),
            "max_size": self._max_size,
        }


# =============================================================================
# CACHE FACTORY
# =============================================================================


async def create_cache(
    use_redis: bool = True, config: CacheConfig | None = None
) -> ImprovementCache | InMemoryCache:
    """
    Cache instance oluştur.

    Args:
        use_redis: Redis kullanılsın mı
        config: Cache konfigürasyonu

    Returns:
        Cache instance
    """
    if use_redis:
        cache = ImprovementCache(config)
        connected = await cache.connect()

        if connected:
            return cache
        logger.warning("Redis bağlantısı başarısız, in-memory cache kullanılıyor")

    return InMemoryCache()
