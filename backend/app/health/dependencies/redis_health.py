"""
Redis Health Checker

Bu modul, Redis cache bağlantısının sağlık kontrolünü yapar.
Cache hit/miss rates, memory usage ve availability izlenir.

Requirements:
    REQ-6.1: PING komutu ile health check
    REQ-6.2: Hit rate, miss rate, eviction rate ölçümü
    REQ-6.3: Hit rate %70 altında -> cache stratejisi önerisi
    REQ-6.4: Memory usage %90 üstünde -> eviction uyarısı
    REQ-6.5: Redis unreachable -> cache bypass mode
    REQ-6.6: Cache recovery -> cache warming başlat
"""

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


@dataclass
class RedisHealthMetrics:
    """
    Redis sağlık metrikleri.

    Attributes:
        is_healthy: Redis erişilebilir mi
        response_time_ms: PING response süresi (ms)
        hit_rate: Cache hit oranı (0.0-1.0)
        miss_rate: Cache miss oranı (0.0-1.0)
        eviction_rate: Eviction oranı
        memory_used_bytes: Kullanılan memory (bytes)
        memory_max_bytes: Maksimum memory (bytes)
        memory_usage_percent: Memory kullanım yüzdesi
        connected_clients: Bağlı client sayısı
        timestamp: Ölçüm zamanı
        error_message: Hata mesajı (varsa)
    """
    is_healthy: bool
    response_time_ms: float
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    eviction_rate: float = 0.0
    memory_used_bytes: int = 0
    memory_max_bytes: int = 0
    memory_usage_percent: float = 0.0
    connected_clients: int = 0
    timestamp: datetime = None
    error_message: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


class RedisHealthChecker:
    """
    Redis cache sağlık kontrolü yapan sınıf.

    Bu sınıf, Redis'in erişilebilir olduğunu doğrular,
    cache performans metriklerini toplar ve memory
    kullanımını izler.

    Attributes:
        redis_client: Redis client instance
        hit_rate_threshold: Minimum kabul edilebilir hit rate
        memory_warning_threshold: Memory uyarı eşiği (%)
    """

    def __init__(
        self,
        redis_client,
        hit_rate_threshold: float = 0.70,
        memory_warning_threshold: float = 90.0
    ):
        """
        RedisHealthChecker sınıfını başlatır.

        Args:
            redis_client: Redis client instance
            hit_rate_threshold: Minimum hit rate eşiği (varsayılan: 0.70)
            memory_warning_threshold: Memory uyarı eşiği (varsayılan: 90%)
        """
        self.redis_client = redis_client
        self.hit_rate_threshold = hit_rate_threshold
        self.memory_warning_threshold = memory_warning_threshold

        # Cache bypass mode flag
        self._bypass_mode = False

        # Cache warming callbacks
        self._warming_callbacks: list = []

        logger.info(
            f"RedisHealthChecker başlatıldı: "
            f"hit_rate_threshold={hit_rate_threshold}, "
            f"memory_warning={memory_warning_threshold}%"
        )

    async def check_health(self) -> RedisHealthMetrics:
        """
        Redis sağlık kontrolü yapar.

        PING komutu göndererek Redis'in erişilebilir olduğunu
        doğrular ve performans metriklerini toplar.

        Returns:
            RedisHealthMetrics instance

        Requirements:
            REQ-6.1: PING komutu ile health check
        """
        start_time = time.time()

        try:
            # PING komutu gönder
            pong = await self.redis_client.ping()

            if not pong:
                raise Exception("PING failed - no response")

            response_time_ms = (time.time() - start_time) * 1000

            # Cache ve memory metriklerini topla
            cache_metrics = await self._get_cache_metrics()
            memory_metrics = await self._get_memory_metrics()

            metrics = RedisHealthMetrics(
                is_healthy=True,
                response_time_ms=response_time_ms,
                hit_rate=cache_metrics.get("hit_rate", 0.0),
                miss_rate=cache_metrics.get("miss_rate", 0.0),
                eviction_rate=cache_metrics.get("eviction_rate", 0.0),
                memory_used_bytes=memory_metrics.get("used", 0),
                memory_max_bytes=memory_metrics.get("max", 0),
                memory_usage_percent=memory_metrics.get("usage_percent", 0.0),
                connected_clients=cache_metrics.get("connected_clients", 0)
            )

            # Hit rate uyarısı
            if metrics.hit_rate < self.hit_rate_threshold and metrics.hit_rate > 0:
                await self._handle_low_hit_rate(metrics)

            # Memory uyarısı
            if metrics.memory_usage_percent > self.memory_warning_threshold:
                await self._handle_high_memory_usage(metrics)

            # Bypass mode'dan çık
            if self._bypass_mode:
                await self._exit_bypass_mode()

            # Metrikleri kaydet
            await self._store_metrics(metrics)

            logger.debug(
                f"Redis health check tamamlandı: "
                f"{response_time_ms:.2f}ms, "
                f"hit_rate: {metrics.hit_rate:.1%}, "
                f"memory: {metrics.memory_usage_percent:.1f}%"
            )

            return metrics

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            logger.error(f"Redis health check hatası: {e}")

            metrics = RedisHealthMetrics(
                is_healthy=False,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )

            await self._handle_redis_unavailable()

            return metrics

    async def _get_cache_metrics(self) -> dict:
        """
        Cache performans metriklerini toplar.

        Returns:
            Cache metrikleri dict'i

        Requirements:
            REQ-6.2: Hit rate, miss rate, eviction rate ölçümü
        """
        try:
            info = await self.redis_client.info("stats")
            clients_info = await self.redis_client.info("clients")

            # Hit/miss hesaplama
            hits = int(info.get("keyspace_hits", 0))
            misses = int(info.get("keyspace_misses", 0))
            total = hits + misses

            hit_rate = hits / total if total > 0 else 0.0
            miss_rate = misses / total if total > 0 else 0.0

            # Eviction rate
            evicted_keys = int(info.get("evicted_keys", 0))
            total_keys = await self.redis_client.dbsize()
            eviction_rate = evicted_keys / total_keys if total_keys > 0 else 0.0

            return {
                "hit_rate": hit_rate,
                "miss_rate": miss_rate,
                "eviction_rate": eviction_rate,
                "total_hits": hits,
                "total_misses": misses,
                "evicted_keys": evicted_keys,
                "connected_clients": int(clients_info.get("connected_clients", 0))
            }
        except Exception as e:
            logger.error(f"Cache metrikleri alınamadı: {e}")
            return {}

    async def _get_memory_metrics(self) -> dict:
        """
        Memory kullanım metriklerini toplar.

        Returns:
            Memory metrikleri dict'i

        Requirements:
            REQ-6.4: Memory usage izleme
        """
        try:
            info = await self.redis_client.info("memory")

            used = int(info.get("used_memory", 0))
            max_memory = int(info.get("maxmemory", 0))

            # maxmemory ayarlanmamışsa sistem limitine bak
            if max_memory == 0:
                max_memory = int(info.get("total_system_memory", 0))

            usage_percent = (used / max_memory * 100) if max_memory > 0 else 0.0

            return {
                "used": used,
                "max": max_memory,
                "usage_percent": usage_percent,
                "peak": int(info.get("used_memory_peak", 0)),
                "fragmentation_ratio": float(info.get("mem_fragmentation_ratio", 1.0))
            }
        except Exception as e:
            logger.error(f"Memory metrikleri alınamadı: {e}")
            return {}

    async def _handle_low_hit_rate(self, metrics: RedisHealthMetrics) -> None:
        """
        Düşük hit rate durumunu işler.

        Args:
            metrics: Redis sağlık metrikleri

        Requirements:
            REQ-6.3: Hit rate %70 altında -> cache stratejisi önerisi
        """
        warning_message = (
            f"⚠️ REDIS LOW HIT RATE UYARISI!\n"
            f"Hit Rate: {metrics.hit_rate:.1%} (minimum: {self.hit_rate_threshold:.1%})\n"
            f"Miss Rate: {metrics.miss_rate:.1%}\n\n"
            f"Öneriler:\n"
            f"1. Cache key pattern'larını gözden geçirin\n"
            f"2. TTL değerlerini optimize edin\n"
            f"3. Sık erişilen verileri önceden cache'leyin\n"
            f"4. Cache invalidation stratejisini kontrol edin"
        )

        logger.warning(warning_message)

        # Alert kaydet
        try:
            await self.redis_client.lpush(
                "kiro2:health:alerts:redis",
                warning_message
            )
            await self.redis_client.ltrim(
                "kiro2:health:alerts:redis",
                0, 99
            )
        except Exception as e:
            logger.error(f"Low hit rate alert kaydedilemedi: {e}")

    async def _handle_high_memory_usage(self, metrics: RedisHealthMetrics) -> None:
        """
        Yüksek memory kullanımı durumunu işler.

        Args:
            metrics: Redis sağlık metrikleri

        Requirements:
            REQ-6.4: Memory usage %90 üstünde -> eviction uyarısı
        """
        warning_message = (
            f"🚨 REDIS HIGH MEMORY USAGE!\n"
            f"Memory Usage: {metrics.memory_usage_percent:.1f}%\n"
            f"Used: {metrics.memory_used_bytes / 1024 / 1024:.2f} MB\n"
            f"Max: {metrics.memory_max_bytes / 1024 / 1024:.2f} MB\n\n"
            f"Uyarı: Eviction policy aktif olabilir!\n"
            f"Öneriler:\n"
            f"1. maxmemory ayarını artırın\n"
            f"2. Gereksiz key'leri temizleyin\n"
            f"3. TTL'leri kısaltın\n"
            f"4. Eviction policy'yi gözden geçirin"
        )

        logger.warning(warning_message)

        try:
            await self.redis_client.lpush(
                "kiro2:health:alerts:critical",
                warning_message
            )
        except Exception as e:
            logger.error(f"High memory alert kaydedilemedi: {e}")

    async def _handle_redis_unavailable(self) -> None:
        """
        Redis erişilemez durumunu işler.

        Requirements:
            REQ-6.5: Redis unreachable -> cache bypass mode
        """
        logger.critical("🚨 REDIS UNAVAILABLE! Bypass mode aktif.")

        self._bypass_mode = True

        # Not: Redis unavailable olduğu için Redis'e kayıt yapamayız
        # Bu durumda local logging ve monitoring sistemleri kullanılmalı

    async def _exit_bypass_mode(self) -> None:
        """
        Bypass mode'dan çıkar ve cache warming başlatır.

        Requirements:
            REQ-6.6: Cache recovery -> cache warming başlat
        """
        if not self._bypass_mode:
            return

        logger.info("Redis recovery - Bypass mode devre dışı, cache warming başlıyor")

        self._bypass_mode = False

        # Cache warming callbacks'leri çağır
        for callback in self._warming_callbacks:
            try:
                if callable(callback):
                    await callback() if hasattr(callback, '__await__') else callback()
            except Exception as e:
                logger.error(f"Cache warming callback hatası: {e}")

        # Warming başladığını kaydet
        try:
            await self.redis_client.set(
                "kiro2:health:redis:last_warming",
                datetime.now(UTC).isoformat(),
                ex=3600
            )
        except Exception as e:
            logger.error(f"Cache warming kaydedilemedi: {e}")

    def register_warming_callback(self, callback) -> None:
        """
        Cache warming callback'i kaydeder.

        Args:
            callback: Cache warming fonksiyonu
        """
        self._warming_callbacks.append(callback)

    def is_bypass_mode(self) -> bool:
        """
        Bypass mode aktif mi kontrol eder.

        Returns:
            True ise bypass mode aktif
        """
        return self._bypass_mode

    async def _store_metrics(self, metrics: RedisHealthMetrics) -> None:
        """
        Metrikleri Redis'e kaydeder.

        Args:
            metrics: Redis sağlık metrikleri
        """
        if not metrics.is_healthy:
            return

        try:
            redis_key = "kiro2:health:redis:metrics"

            await self.redis_client.hset(
                redis_key,
                mapping={
                    "is_healthy": str(metrics.is_healthy),
                    "response_time_ms": str(metrics.response_time_ms),
                    "hit_rate": str(metrics.hit_rate),
                    "miss_rate": str(metrics.miss_rate),
                    "eviction_rate": str(metrics.eviction_rate),
                    "memory_used_bytes": str(metrics.memory_used_bytes),
                    "memory_max_bytes": str(metrics.memory_max_bytes),
                    "memory_usage_percent": str(metrics.memory_usage_percent),
                    "connected_clients": str(metrics.connected_clients),
                    "timestamp": metrics.timestamp.isoformat()
                }
            )

            await self.redis_client.expire(redis_key, 300)  # 5 dakika

        except Exception as e:
            logger.error(f"Redis metrikleri kaydedilemedi: {e}")

    async def is_redis_available(self) -> bool:
        """
        Redis'in kullanılabilir olup olmadığını hızlıca kontrol eder.

        Returns:
            True ise Redis kullanılabilir
        """
        if self._bypass_mode:
            return False

        try:
            return await self.redis_client.ping()
        except Exception:
            return False
