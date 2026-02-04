"""
Health Check Service - Task 4
Learning Path Video Yükleme Sorunu Çözümü

Servis sağlık durumu izleme ve raporlama servisi.
YouTube API, Database ve Redis Cache sağlık kontrollerini yapar.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 4.12
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.cache_service import CacheService
from services.real_youtube_api import RealYouTubeAPI

# Import db_manager with error handling
try:
    from database.connection import db_manager
except ImportError:
    # Fallback if database module has issues
    db_manager = None

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Sağlık durumu enum"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Bileşen sağlık durumu"""

    name: str
    status: HealthStatus
    response_time_ms: float
    error_message: Optional[str] = None
    last_check: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Dict'e çevir"""
        return {
            "name": self.name,
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "error_message": self.error_message,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "details": self.details or {},
        }


@dataclass
class SystemHealth:
    """Sistem sağlık durumu"""

    overall_status: HealthStatus
    components: List[ComponentHealth]
    metrics: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Dict'e çevir"""
        return {
            "overall_status": self.overall_status.value,
            "components": [c.to_dict() for c in self.components],
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class StartupHealthCheck:
    """
    Startup sağlık kontrolü sonucu (Requirement 0)

    Sistem başlangıcında tüm kritik bağımlılıkların sağlık durumunu içerir.
    """

    success: bool
    components: List[ComponentHealth]
    warnings: List[str]
    errors: List[str]
    startup_time_ms: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Dict'e çevir"""
        return {
            "success": self.success,
            "components": [c.to_dict() for c in self.components],
            "warnings": self.warnings,
            "errors": self.errors,
            "startup_time_ms": round(self.startup_time_ms, 2),
            "timestamp": self.timestamp.isoformat(),
        }


class HealthCheckService:
    """
    Sistem sağlık durumu izleme servisi

    YouTube API, Database ve Redis Cache sağlık kontrollerini yapar.
    Overall health status belirler ve sistem metriklerini toplar.
    """

    def __init__(
        self,
        youtube_api: Optional[RealYouTubeAPI] = None,
        cache_service: Optional[CacheService] = None,
    ):
        """
        Initialize health check service

        Args:
            youtube_api: YouTube API servisi (opsiyonel, lazy init)
            cache_service: Cache servisi (opsiyonel, lazy init)
        """
        self._youtube_api = youtube_api
        self._cache_service = cache_service
        self._metrics_cache: Dict[str, Any] = {}
        self._last_metrics_update: Optional[datetime] = None

    @property
    def youtube_api(self) -> RealYouTubeAPI:
        """YouTube API instance'ını al (lazy init)"""
        if self._youtube_api is None:
            self._youtube_api = RealYouTubeAPI()
        return self._youtube_api

    @property
    def cache_service(self) -> CacheService:
        """Cache service instance'ını al (lazy init)"""
        if self._cache_service is None:
            self._cache_service = CacheService()
        return self._cache_service

    async def check_health(self) -> SystemHealth:
        """
        Tüm bileşenlerin sağlık kontrolü

        Requirements: 4.1, 4.2, 4.3

        Returns:
            SystemHealth: Sistem sağlık durumu
        """
        logger.info("Sistem sağlık kontrolü başlatılıyor...")

        components = []

        # 1. YouTube API health check
        youtube_health = await self._check_youtube_api()
        components.append(youtube_health)

        # 2. Database health check
        db_health = await self._check_database()
        components.append(db_health)

        # 3. Redis Cache health check
        cache_health = await self._check_cache()
        components.append(cache_health)

        # 4. Overall status belirle
        overall_status = self._determine_overall_status(components)

        # 5. Sistem metriklerini topla
        metrics = await self._collect_metrics()

        system_health = SystemHealth(
            overall_status=overall_status,
            components=components,
            metrics=metrics,
            timestamp=datetime.now(),
        )

        logger.info(
            f"Sağlık kontrolü tamamlandı: {overall_status.value} "
            f"({len([c for c in components if c.status == HealthStatus.HEALTHY])}/{len(components)} healthy)"
        )

        return system_health

    async def _check_youtube_api(self) -> ComponentHealth:
        """
        YouTube API sağlık kontrolü

        Requirements: 4.3, 4.7

        Returns:
            ComponentHealth: YouTube API sağlık durumu
        """
        start_time = time.time()

        try:
            # YouTube API bağlantı testi
            # API key kontrolü
            api_key = self.youtube_api.api_key

            if not api_key or api_key == "test-youtube-api-key":
                # Test mode - degraded
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="YouTube API",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    error_message="YouTube API key not configured (test mode)",
                    last_check=datetime.now(),
                    details={"api_key_configured": False, "test_mode": True},
                )

            # Basit bir test sorgusu yap
            # Not: Gerçek API çağrısı quota kullanır, bu yüzden sadece key varlığını kontrol ediyoruz
            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="YouTube API",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                details={"api_key_configured": True, "test_mode": False},
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"YouTube API sağlık kontrolü başarısız: {str(e)}")

            return ComponentHealth(
                name="YouTube API",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e),
                last_check=datetime.now(),
                details={"error_type": type(e).__name__},
            )

    async def _check_database(self) -> ComponentHealth:
        """
        Database sağlık kontrolü

        Requirements: 4.3

        Returns:
            ComponentHealth: Database sağlık durumu
        """
        start_time = time.time()

        try:
            # Check if db_manager is available
            if db_manager is None:
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="Database",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    error_message="Database manager not initialized",
                    last_check=datetime.now(),
                    details={"error_type": "NotInitialized"},
                )

            # Database bağlantı testi
            async with db_manager.async_session_factory() as session:
                # Basit bir query çalıştır
                from sqlalchemy import text

                result = await session.execute(text("SELECT 1"))
                result.scalar()

            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="Database",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                details={
                    "connection_pool_size": db_manager.async_engine.pool.size()
                    if hasattr(db_manager.async_engine, "pool")
                    else None,
                    "database_type": "PostgreSQL"
                    if "postgresql" in str(db_manager.async_engine.url)
                    else "SQLite",
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database sağlık kontrolü başarısız: {str(e)}")

            return ComponentHealth(
                name="Database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e),
                last_check=datetime.now(),
                details={"error_type": type(e).__name__},
            )

    async def _check_cache(self) -> ComponentHealth:
        """
        Redis Cache sağlık kontrolü

        Requirements: 4.3

        Returns:
            ComponentHealth: Cache sağlık durumu
        """
        start_time = time.time()

        try:
            # Redis ping testi
            client = await self.cache_service.async_client
            await client.ping()

            response_time = (time.time() - start_time) * 1000

            # Redis info al
            info = await client.info()

            return ComponentHealth(
                name="Redis Cache",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                details={
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "N/A"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Redis Cache sağlık kontrolü başarısız: {str(e)}")

            return ComponentHealth(
                name="Redis Cache",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e),
                last_check=datetime.now(),
                details={"error_type": type(e).__name__},
            )

    def _determine_overall_status(
        self, components: List[ComponentHealth]
    ) -> HealthStatus:
        """
        Overall status belirle

        Requirements: 4.6

        Logic:
        - Herhangi bir bileşen UNHEALTHY ise -> UNHEALTHY
        - Herhangi bir bileşen DEGRADED ise -> DEGRADED
        - Tüm bileşenler HEALTHY ise -> HEALTHY

        Args:
            components: Bileşen sağlık durumları

        Returns:
            HealthStatus: Overall sağlık durumu
        """
        unhealthy_count = sum(
            1 for c in components if c.status == HealthStatus.UNHEALTHY
        )

        degraded_count = sum(1 for c in components if c.status == HealthStatus.DEGRADED)

        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def _collect_metrics(self) -> Dict[str, Any]:
        """
        Sistem metriklerini topla

        Requirements: 4.4, 4.12

        Returns:
            Dict: Sistem metrikleri
        """
        # Cache'den metrikleri al (5 dakika cache)
        now = datetime.now()
        if (
            self._last_metrics_update is None
            or (now - self._last_metrics_update).total_seconds() > 300
        ):
            # Metrikleri yeniden topla
            self._metrics_cache = await self._fetch_fresh_metrics()
            self._last_metrics_update = now

        return self._metrics_cache

    async def _fetch_fresh_metrics(self) -> Dict[str, Any]:
        """
        Fresh metrikleri topla

        Returns:
            Dict: Sistem metrikleri
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": self._get_uptime_seconds(),
        }

        # Video API metrikleri (cache'den)
        try:
            cache_key = "video_api:metrics:24h"
            cached_metrics = self.cache_service.sync_client.get(
                self.cache_service._make_key(cache_key)
            )

            if cached_metrics:
                video_metrics = self.cache_service._deserialize(cached_metrics)
                metrics.update(
                    {
                        "total_requests_24h": video_metrics.get("total_requests", 0),
                        "success_rate_24h": video_metrics.get("success_rate", 0.0),
                        "avg_response_time_1h": video_metrics.get(
                            "avg_response_time", 0.0
                        ),
                        "cache_hit_rate_1h": video_metrics.get("cache_hit_rate", 0.0),
                        "error_rate_1h": video_metrics.get("error_rate", 0.0),
                    }
                )
            else:
                # Default values
                metrics.update(
                    {
                        "total_requests_24h": 0,
                        "success_rate_24h": 100.0,
                        "avg_response_time_1h": 0.0,
                        "cache_hit_rate_1h": 0.0,
                        "error_rate_1h": 0.0,
                    }
                )

        except Exception as e:
            logger.warning(f"Metrik toplama hatası: {str(e)}")
            metrics.update(
                {
                    "total_requests_24h": 0,
                    "success_rate_24h": 100.0,
                    "avg_response_time_1h": 0.0,
                    "cache_hit_rate_1h": 0.0,
                    "error_rate_1h": 0.0,
                }
            )

        return metrics

    def _get_uptime_seconds(self) -> int:
        """
        Sistem uptime'ını al (saniye)

        Returns:
            int: Uptime saniye
        """
        # Bu basit bir implementasyon
        # Production'da process start time'ı track edilmeli
        try:
            import psutil

            process = psutil.Process()
            return int(time.time() - process.create_time())
        except Exception:
            # psutil yoksa veya hata varsa 0 dön
            return 0

    async def startup_health_check(self) -> StartupHealthCheck:
        """
        Sistem başlangıç sağlık kontrolü (Requirement 0)

        Tüm kritik bağımlılıkları kontrol eder ve sonuçları loglar.
        Kritik servis başarısız olsa bile uygulama başlar,
        ancak WARNING seviyesinde log kaydedilir.

        Requirements: 0.1, 0.2, 0.6, 0.7, 1.9, 4.6, 4.9

        Returns:
            StartupHealthCheck: Başlangıç sağlık kontrolü sonucu
        """
        logger.info("🚀 Sistem başlangıç sağlık kontrolü başlatılıyor...")
        start_time = time.time()

        components = []
        warnings = []
        errors = []

        # 1. Database health check (Req 0.1)
        logger.info("📊 Database sağlık kontrolü yapılıyor...")
        try:
            db_health = await self._check_database()
            components.append(db_health)

            if db_health.status == HealthStatus.UNHEALTHY:
                error_msg = f"Database unhealthy: {db_health.error_message}"
                errors.append(error_msg)
                logger.warning(f"⚠️ {error_msg}")
            elif db_health.status == HealthStatus.DEGRADED:
                warning_msg = f"Database degraded: {db_health.error_message}"
                warnings.append(warning_msg)
                logger.warning(f"⚠️ {warning_msg}")
            else:
                logger.info(
                    f"✅ Database healthy (response time: {db_health.response_time_ms:.2f}ms)"
                )
        except Exception as e:
            error_msg = f"Database check failed: {str(e)}"
            errors.append(error_msg)
            logger.error(f"❌ {error_msg}")

        # 2. Redis cache health check (Req 0.1)
        logger.info("💾 Redis Cache sağlık kontrolü yapılıyor...")
        try:
            cache_health = await self._check_cache()
            components.append(cache_health)

            if cache_health.status == HealthStatus.UNHEALTHY:
                error_msg = f"Redis cache unhealthy: {cache_health.error_message}"
                errors.append(error_msg)
                logger.warning(f"⚠️ {error_msg}")
            elif cache_health.status == HealthStatus.DEGRADED:
                warning_msg = f"Redis cache degraded: {cache_health.error_message}"
                warnings.append(warning_msg)
                logger.warning(f"⚠️ {warning_msg}")
            else:
                logger.info(
                    f"✅ Redis Cache healthy (response time: {cache_health.response_time_ms:.2f}ms)"
                )
        except Exception as e:
            error_msg = f"Cache check failed: {str(e)}"
            errors.append(error_msg)
            logger.error(f"❌ {error_msg}")

        # 3. YouTube API health check (Req 0.1)
        logger.info("🎥 YouTube API sağlık kontrolü yapılıyor...")
        try:
            youtube_health = await self._check_youtube_api()
            components.append(youtube_health)

            if youtube_health.status == HealthStatus.UNHEALTHY:
                error_msg = f"YouTube API unhealthy: {youtube_health.error_message}"
                errors.append(error_msg)
                logger.warning(f"⚠️ {error_msg}")
            elif youtube_health.status == HealthStatus.DEGRADED:
                warning_msg = f"YouTube API degraded: {youtube_health.error_message}"
                warnings.append(warning_msg)
                logger.warning(f"⚠️ {warning_msg}")
            else:
                logger.info(
                    f"✅ YouTube API healthy (response time: {youtube_health.response_time_ms:.2f}ms)"
                )
        except Exception as e:
            error_msg = f"YouTube API check failed: {str(e)}"
            errors.append(error_msg)
            logger.error(f"❌ {error_msg}")

        # 4. Calculate startup time
        startup_time_ms = (time.time() - start_time) * 1000

        # 5. Determine success (başarılı = en az 1 component healthy)
        healthy_count = sum(1 for c in components if c.status == HealthStatus.HEALTHY)
        success = healthy_count > 0

        # 6. Create result
        result = StartupHealthCheck(
            success=success,
            components=components,
            warnings=warnings,
            errors=errors,
            startup_time_ms=startup_time_ms,
            timestamp=datetime.now(),
        )

        # 7. Log structured result (Req 0.2, 0.6)
        if success:
            logger.info(
                f"✅ Başlangıç sağlık kontrolü BAŞARILI - "
                f"{healthy_count}/{len(components)} servis healthy, "
                f"{len(warnings)} uyarı, {len(errors)} hata, "
                f"süre: {startup_time_ms:.2f}ms"
            )
        else:
            logger.warning(
                f"⚠️ Başlangıç sağlık kontrolü UYARI - "
                f"{healthy_count}/{len(components)} servis healthy, "
                f"{len(warnings)} uyarı, {len(errors)} hata, "
                f"süre: {startup_time_ms:.2f}ms"
            )

        # 8. Log component details
        for component in components:
            status_emoji = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNHEALTHY: "❌",
            }
            logger.info(
                f"  {status_emoji[component.status]} {component.name}: "
                f"{component.status.value} ({component.response_time_ms:.2f}ms)"
            )

        return result


# Global instance
_health_check_service: Optional[HealthCheckService] = None


def get_health_check_service() -> HealthCheckService:
    """
    Health check service instance'ını al (singleton)

    Returns:
        HealthCheckService: Health check service instance
    """
    global _health_check_service

    if _health_check_service is None:
        _health_check_service = HealthCheckService()

    return _health_check_service
