"""
Database Health Checker

Bu modul, PostgreSQL veritabanı bağlantısının sağlık kontrolünü yapar.
Connection pool durumu, query performance ve availability izlenir.

Requirements:
    REQ-5.1: SELECT 1 query ile health check
    REQ-5.2: Active/idle connection sayısı ölçümü
    REQ-5.3: Connection pool %90 dolu uyarısı
    REQ-5.4: Query response time < 50ms hedefi
    REQ-5.5: Database unreachable -> tüm DB endpoint'ler degraded
    REQ-5.6: Connection leak tespiti ve trace raporu
"""

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


@dataclass
class DatabaseHealthMetrics:
    """
    Database sağlık metrikleri.

    Attributes:
        is_healthy: Veritabanı erişilebilir mi
        response_time_ms: SELECT 1 query süresi (ms)
        active_connections: Aktif bağlantı sayısı
        idle_connections: Boşta bağlantı sayısı
        pool_size: Connection pool boyutu
        pool_usage_percent: Pool kullanım yüzdesi
        timestamp: Ölçüm zamanı
        error_message: Hata mesajı (varsa)
    """
    is_healthy: bool
    response_time_ms: float
    active_connections: int = 0
    idle_connections: int = 0
    pool_size: int = 0
    pool_usage_percent: float = 0.0
    timestamp: datetime = None
    error_message: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


class DatabaseHealthChecker:
    """
    PostgreSQL veritabanı sağlık kontrolü yapan sınıf.

    Bu sınıf, veritabanı bağlantısının sağlıklı olup olmadığını
    kontrol eder, connection pool durumunu izler ve performans
    metriklerini toplar.

    Attributes:
        engine: SQLAlchemy async engine
        redis_client: Redis client (metrikleri cache için)
        response_time_threshold: Query response time hedefi (ms)
        pool_warning_threshold: Pool kullanım uyarı eşiği (%)
    """

    def __init__(
        self,
        engine: AsyncEngine,
        redis_client=None,
        response_time_threshold: float = 50.0,
        pool_warning_threshold: float = 90.0
    ):
        """
        DatabaseHealthChecker sınıfını başlatır.

        Args:
            engine: SQLAlchemy AsyncEngine instance
            redis_client: Redis client (opsiyonel)
            response_time_threshold: Query süresi hedefi (ms)
            pool_warning_threshold: Pool uyarı eşiği (%)
        """
        self.engine = engine
        self.redis_client = redis_client
        self.response_time_threshold = response_time_threshold
        self.pool_warning_threshold = pool_warning_threshold

        # Connection tracking for leak detection
        self._connection_history: list[dict] = []
        self._max_history_size = 1000

        logger.info(
            f"DatabaseHealthChecker başlatıldı: "
            f"threshold={response_time_threshold}ms, "
            f"pool_warning={pool_warning_threshold}%"
        )

    async def check_health(self) -> DatabaseHealthMetrics:
        """
        Veritabanı sağlık kontrolü yapar.

        SELECT 1 query'si çalıştırarak veritabanının erişilebilir
        olduğunu doğrular ve response time'ı ölçer.

        Returns:
            DatabaseHealthMetrics instance

        Requirements:
            REQ-5.1: SELECT 1 query ile health check
            REQ-5.4: Query response time < 50ms hedefi
        """
        start_time = time.time()

        try:
            async with self.engine.connect() as conn:
                # SELECT 1 query çalıştır
                await conn.execute(text("SELECT 1"))

            response_time_ms = (time.time() - start_time) * 1000

            # Connection pool metrikleri
            pool_metrics = await self._get_pool_metrics()

            metrics = DatabaseHealthMetrics(
                is_healthy=True,
                response_time_ms=response_time_ms,
                active_connections=pool_metrics.get("active", 0),
                idle_connections=pool_metrics.get("idle", 0),
                pool_size=pool_metrics.get("size", 0),
                pool_usage_percent=pool_metrics.get("usage_percent", 0.0)
            )

            # Performance uyarısı
            if response_time_ms > self.response_time_threshold:
                logger.warning(
                    f"Database response time yüksek: {response_time_ms:.2f}ms "
                    f"(hedef: {self.response_time_threshold}ms)"
                )

            # Pool uyarısı
            if metrics.pool_usage_percent > self.pool_warning_threshold:
                await self._handle_pool_warning(metrics)

            # Connection tracking
            self._track_connection(metrics)

            # Redis'e kaydet
            await self._store_metrics(metrics)

            logger.debug(
                f"Database health check tamamlandı: "
                f"{response_time_ms:.2f}ms, "
                f"pool: {metrics.pool_usage_percent:.1f}%"
            )

            return metrics

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            logger.error(f"Database health check hatası: {e}")

            metrics = DatabaseHealthMetrics(
                is_healthy=False,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )

            await self._store_metrics(metrics)
            await self._handle_database_unavailable()

            return metrics

    async def _get_pool_metrics(self) -> dict:
        """
        Connection pool metriklerini toplar.

        Returns:
            Pool metrikleri dict'i

        Requirements:
            REQ-5.2: Active/idle connection sayısı ölçümü
        """
        try:
            pool = self.engine.pool

            # SQLAlchemy pool stats
            size = pool.size() if hasattr(pool, 'size') else 0
            checkedin = pool.checkedin() if hasattr(pool, 'checkedin') else 0
            checkedout = pool.checkedout() if hasattr(pool, 'checkedout') else 0
            overflow = pool.overflow() if hasattr(pool, 'overflow') else 0

            active = checkedout
            idle = checkedin
            total = size + overflow

            usage_percent = (active / total * 100) if total > 0 else 0.0

            return {
                "size": size,
                "active": active,
                "idle": idle,
                "overflow": overflow,
                "total": total,
                "usage_percent": usage_percent
            }
        except Exception as e:
            logger.error(f"Pool metrikleri alınamadı: {e}")
            return {"size": 0, "active": 0, "idle": 0, "usage_percent": 0.0}

    async def _handle_pool_warning(self, metrics: DatabaseHealthMetrics) -> None:
        """
        Connection pool uyarısını işler.

        Args:
            metrics: Database sağlık metrikleri

        Requirements:
            REQ-5.3: Connection pool %90 dolu uyarısı
        """
        warning_message = (
            f"⚠️ DATABASE CONNECTION POOL UYARISI!\n"
            f"Pool Kullanımı: {metrics.pool_usage_percent:.1f}%\n"
            f"Aktif: {metrics.active_connections}\n"
            f"Boşta: {metrics.idle_connections}\n"
            f"Toplam: {metrics.pool_size}"
        )

        logger.warning(warning_message)

        # Redis'e alert kaydet
        if self.redis_client:
            try:
                await self.redis_client.lpush(
                    "kiro2:health:alerts:database",
                    warning_message
                )
                await self.redis_client.ltrim(
                    "kiro2:health:alerts:database",
                    0, 99
                )
            except Exception as e:
                logger.error(f"Pool warning kaydedilemedi: {e}")

    async def _handle_database_unavailable(self) -> None:
        """
        Database erişilemez durumunu işler.

        Requirements:
            REQ-5.5: Database unreachable -> tüm DB endpoint'ler degraded
        """
        logger.critical("🚨 DATABASE UNAVAILABLE!")

        # Redis'e unavailable flag'i kaydet
        if self.redis_client:
            try:
                await self.redis_client.set(
                    "kiro2:health:database:available",
                    "false",
                    ex=60  # 1 dakika
                )

                # Alert kaydet
                alert_message = (
                    f"🚨 DATABASE UNAVAILABLE!\n"
                    f"Timestamp: {datetime.now(UTC).isoformat()}\n"
                    f"Tüm DB-dependent endpoint'ler degraded olarak işaretlendi."
                )

                await self.redis_client.lpush(
                    "kiro2:health:alerts:critical",
                    alert_message
                )
            except Exception as e:
                logger.error(f"Database unavailable alert kaydedilemedi: {e}")

    def _track_connection(self, metrics: DatabaseHealthMetrics) -> None:
        """
        Connection geçmişini takip eder (leak detection için).

        Args:
            metrics: Database sağlık metrikleri
        """
        self._connection_history.append({
            "timestamp": metrics.timestamp.isoformat(),
            "active": metrics.active_connections,
            "idle": metrics.idle_connections,
            "pool_usage": metrics.pool_usage_percent
        })

        # Geçmiş boyutunu sınırla
        if len(self._connection_history) > self._max_history_size:
            self._connection_history = self._connection_history[-self._max_history_size:]

    async def detect_connection_leak(self) -> dict | None:
        """
        Connection leak tespiti yapar.

        Returns:
            Leak tespit edilirse detaylı rapor, yoksa None

        Requirements:
            REQ-5.6: Connection leak tespiti ve trace raporu
        """
        if len(self._connection_history) < 10:
            return None

        # Son 10 ölçümde sürekli artan active connection var mı?
        recent = self._connection_history[-10:]
        active_counts = [h["active"] for h in recent]

        # Monoton artan mı kontrol et
        is_increasing = all(
            active_counts[i] <= active_counts[i + 1]
            for i in range(len(active_counts) - 1)
        )

        # Son değer başlangıçtan en az 2x büyük mü?
        potential_leak = (
            is_increasing and
            active_counts[-1] > 0 and
            active_counts[-1] >= active_counts[0] * 2
        )

        if potential_leak:
            leak_report = {
                "detected_at": datetime.now(UTC).isoformat(),
                "severity": "warning",
                "analysis": {
                    "initial_active": active_counts[0],
                    "current_active": active_counts[-1],
                    "growth_rate": (active_counts[-1] / active_counts[0]
                                   if active_counts[0] > 0 else float('inf')),
                    "trend": "monotonically_increasing"
                },
                "recent_history": recent,
                "recommendations": [
                    "Check for unclosed database sessions in application code",
                    "Review async context managers for proper cleanup",
                    "Check for long-running transactions",
                    "Consider reducing connection pool size for testing"
                ]
            }

            logger.warning(f"Connection leak tespit edildi: {leak_report}")

            # Redis'e kaydet
            if self.redis_client:
                try:
                    await self.redis_client.set(
                        "kiro2:health:database:leak_report",
                        str(leak_report),
                        ex=3600  # 1 saat
                    )
                except Exception as e:
                    logger.error(f"Leak report kaydedilemedi: {e}")

            return leak_report

        return None

    async def _store_metrics(self, metrics: DatabaseHealthMetrics) -> None:
        """
        Metrikleri Redis'e kaydeder.

        Args:
            metrics: Database sağlık metrikleri
        """
        if not self.redis_client:
            return

        try:
            redis_key = "kiro2:health:database:metrics"

            await self.redis_client.hset(
                redis_key,
                mapping={
                    "is_healthy": str(metrics.is_healthy),
                    "response_time_ms": str(metrics.response_time_ms),
                    "active_connections": str(metrics.active_connections),
                    "idle_connections": str(metrics.idle_connections),
                    "pool_size": str(metrics.pool_size),
                    "pool_usage_percent": str(metrics.pool_usage_percent),
                    "timestamp": metrics.timestamp.isoformat(),
                    "error_message": metrics.error_message or ""
                }
            )

            await self.redis_client.expire(redis_key, 300)  # 5 dakika

        except Exception as e:
            logger.error(f"Database metrikleri kaydedilemedi: {e}")

    async def is_database_available(self) -> bool:
        """
        Database'in kullanılabilir olup olmadığını hızlıca kontrol eder.

        Redis cache kullanarak gereksiz query'lerden kaçınır.

        Returns:
            True ise database kullanılabilir
        """
        # Önce Redis cache'e bak
        if self.redis_client:
            try:
                cached = await self.redis_client.get(
                    "kiro2:health:database:available"
                )
                if cached:
                    return cached.decode() == "true"
            except Exception:
                pass

        # Cache miss veya Redis yok, doğrudan kontrol et
        metrics = await self.check_health()
        return metrics.is_healthy
