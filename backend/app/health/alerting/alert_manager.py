"""
Alert Manager

Bu modul, health check sonuçlarına göre alert yönetimini sağlar.
Threshold-based alerting ve throttling desteklenir.

Requirements:
    REQ-8.3: Threshold-based alerting
    REQ-8.4: Alert throttling ve multi-channel notification
    REQ-2.6: Kritik endpoint başarısızlığında anında alert
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert ciddiyet seviyesi."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Alert tipi."""
    ENDPOINT_DOWN = "endpoint_down"
    HIGH_LATENCY = "high_latency"
    HIGH_ERROR_RATE = "high_error_rate"
    SLA_VIOLATION = "sla_violation"
    CIRCUIT_OPENED = "circuit_opened"
    DEPENDENCY_UNHEALTHY = "dependency_unhealthy"
    DEPLOYMENT_FAILED = "deployment_failed"
    LOW_HEALTH_SCORE = "low_health_score"


@dataclass
class Alert:
    """Alert veri modeli."""
    id: str
    type: AlertType
    severity: AlertSeverity
    endpoint: str
    message: str
    details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved: bool = False
    resolved_at: datetime | None = None

    def to_dict(self) -> dict:
        """Dict'e dönüştürür."""
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "endpoint": self.endpoint,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class AlertThreshold:
    """Alert eşik değerleri."""
    response_time_warning_ms: float = 200.0
    response_time_critical_ms: float = 500.0
    error_rate_warning: float = 0.01  # 1%
    error_rate_critical: float = 0.05  # 5%
    health_score_warning: int = 70
    health_score_critical: int = 50


class AlertManager:
    """
    Alert yönetim sistemi.

    Bu sınıf, health check sonuçlarına göre alert oluşturur,
    throttling uygular ve çeşitli kanallardan bildirim gönderir.

    Attributes:
        redis_client: Redis client
        thresholds: Alert eşik değerleri
        throttle_minutes: Alert throttling süresi (dakika)
    """

    def __init__(
        self,
        redis_client=None,
        thresholds: AlertThreshold | None = None,
        throttle_minutes: int = 5
    ):
        """
        AlertManager sınıfını başlatır.

        Args:
            redis_client: Redis client
            thresholds: Alert eşik değerleri
            throttle_minutes: Throttling süresi (dakika)
        """
        self.redis_client = redis_client
        self.thresholds = thresholds or AlertThreshold()
        self.throttle_minutes = throttle_minutes

        # Son gönderilen alertler (throttling için)
        self._last_alerts: dict[str, datetime] = {}

        # Active alerts
        self._active_alerts: dict[str, Alert] = {}

        # Notifiers
        self._notifiers: list[Callable] = []

        # Alert counter
        self._alert_counter = 0

        logger.info(
            f"AlertManager başlatıldı: throttle={throttle_minutes}min"
        )

    def _generate_alert_id(self) -> str:
        """Unique alert ID oluşturur."""
        self._alert_counter += 1
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        return f"alert_{timestamp}_{self._alert_counter}"

    async def check_and_alert(
        self,
        endpoint: str,
        response_time_ms: float,
        error_rate: float,
        health_score: int,
        is_critical: bool = False
    ) -> Alert | None:
        """
        Metrikleri kontrol eder ve gerekirse alert oluşturur.

        Args:
            endpoint: Endpoint path
            response_time_ms: Response time (ms)
            error_rate: Hata oranı (0.0-1.0)
            health_score: Sağlık skoru (0-100)
            is_critical: Kritik endpoint mi

        Returns:
            Oluşturulan Alert veya None

        Requirements:
            REQ-8.3: Threshold-based alerting
        """
        # Response time kontrolü
        if response_time_ms >= self.thresholds.response_time_critical_ms:
            return await self.create_alert(
                type=AlertType.HIGH_LATENCY,
                severity=AlertSeverity.CRITICAL,
                endpoint=endpoint,
                message=f"Critical latency: {response_time_ms:.0f}ms",
                details={"response_time_ms": response_time_ms},
                is_critical=is_critical
            )
        if response_time_ms >= self.thresholds.response_time_warning_ms:
            return await self.create_alert(
                type=AlertType.HIGH_LATENCY,
                severity=AlertSeverity.WARNING,
                endpoint=endpoint,
                message=f"High latency: {response_time_ms:.0f}ms",
                details={"response_time_ms": response_time_ms},
                is_critical=is_critical
            )

        # Error rate kontrolü
        if error_rate >= self.thresholds.error_rate_critical:
            return await self.create_alert(
                type=AlertType.HIGH_ERROR_RATE,
                severity=AlertSeverity.CRITICAL,
                endpoint=endpoint,
                message=f"Critical error rate: {error_rate:.1%}",
                details={"error_rate": error_rate},
                is_critical=is_critical
            )
        if error_rate >= self.thresholds.error_rate_warning:
            return await self.create_alert(
                type=AlertType.HIGH_ERROR_RATE,
                severity=AlertSeverity.WARNING,
                endpoint=endpoint,
                message=f"High error rate: {error_rate:.1%}",
                details={"error_rate": error_rate},
                is_critical=is_critical
            )

        # Health score kontrolü
        if health_score < self.thresholds.health_score_critical:
            return await self.create_alert(
                type=AlertType.LOW_HEALTH_SCORE,
                severity=AlertSeverity.CRITICAL,
                endpoint=endpoint,
                message=f"Critical health score: {health_score}",
                details={"health_score": health_score},
                is_critical=is_critical
            )
        if health_score < self.thresholds.health_score_warning:
            return await self.create_alert(
                type=AlertType.LOW_HEALTH_SCORE,
                severity=AlertSeverity.WARNING,
                endpoint=endpoint,
                message=f"Low health score: {health_score}",
                details={"health_score": health_score},
                is_critical=is_critical
            )

        return None

    async def create_alert(
        self,
        type: AlertType,
        severity: AlertSeverity,
        endpoint: str,
        message: str,
        details: dict | None = None,
        is_critical: bool = False
    ) -> Alert | None:
        """
        Yeni alert oluşturur.

        Args:
            type: Alert tipi
            severity: Ciddiyet seviyesi
            endpoint: Endpoint path
            message: Alert mesajı
            details: Ek detaylar
            is_critical: Kritik endpoint mi (throttling bypass)

        Returns:
            Oluşturulan Alert veya None (throttled)

        Requirements:
            REQ-8.4: Alert throttling
            REQ-2.6: Kritik endpoint başarısızlığında anında alert
        """
        # Throttling kontrolü (kritik endpoint'ler için bypass)
        throttle_key = f"{type.value}:{endpoint}"

        if not is_critical and not self._should_send_alert(throttle_key):
            logger.debug(f"Alert throttled: {throttle_key}")
            return None

        # Alert oluştur
        alert = Alert(
            id=self._generate_alert_id(),
            type=type,
            severity=severity,
            endpoint=endpoint,
            message=message,
            details=details or {}
        )

        # Throttle timestamp güncelle
        self._last_alerts[throttle_key] = datetime.now(UTC)

        # Active alerts'e ekle
        self._active_alerts[alert.id] = alert

        # Loglama
        if severity == AlertSeverity.CRITICAL:
            logger.critical(f"🚨 ALERT: {message} ({endpoint})")
        elif severity == AlertSeverity.WARNING:
            logger.warning(f"⚠️ ALERT: {message} ({endpoint})")
        else:
            logger.info(f"ℹ️ ALERT: {message} ({endpoint})")

        # Redis'e kaydet
        await self._store_alert(alert)

        # Notifiers'ları çağır
        await self._send_notifications(alert)

        return alert

    def _should_send_alert(self, throttle_key: str) -> bool:
        """
        Alert gönderilmeli mi kontrol eder (throttling).

        Args:
            throttle_key: Throttle key (type:endpoint)

        Returns:
            True ise alert gönderilebilir

        Requirements:
            REQ-8.4: Max 1 alert per endpoint per 5 minutes
        """
        if throttle_key not in self._last_alerts:
            return True

        last_alert_time = self._last_alerts[throttle_key]
        elapsed = datetime.now(UTC) - last_alert_time

        return elapsed >= timedelta(minutes=self.throttle_minutes)

    async def resolve_alert(self, alert_id: str) -> bool:
        """
        Alert'i çözüldü olarak işaretler.

        Args:
            alert_id: Alert ID

        Returns:
            True ise başarılı
        """
        if alert_id not in self._active_alerts:
            return False

        alert = self._active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.now(UTC)

        logger.info(f"Alert çözüldü: {alert_id}")

        # Redis güncelle
        await self._store_alert(alert)

        # Active alerts'ten çıkar
        del self._active_alerts[alert_id]

        return True

    async def _store_alert(self, alert: Alert) -> None:
        """Alert'i Redis'e kaydeder."""
        if not self.redis_client:
            return

        try:
            # Alert detayını kaydet
            redis_key = f"kiro2:health:alerts:{alert.id}"
            await self.redis_client.set(
                redis_key,
                str(alert.to_dict()),
                ex=86400 * 7  # 7 gün
            )

            # Alert listesine ekle
            await self.redis_client.lpush(
                "kiro2:health:alerts:list",
                alert.id
            )
            await self.redis_client.ltrim(
                "kiro2:health:alerts:list",
                0, 999  # Son 1000 alert
            )

            # Severity bazlı liste
            await self.redis_client.lpush(
                f"kiro2:health:alerts:{alert.severity.value}",
                alert.id
            )
            await self.redis_client.ltrim(
                f"kiro2:health:alerts:{alert.severity.value}",
                0, 499
            )

        except Exception as e:
            logger.error(f"Alert kaydedilemedi: {e}")

    async def _send_notifications(self, alert: Alert) -> None:
        """
        Tüm notifier'lara bildirim gönderir.

        Args:
            alert: Alert instance
        """
        for notifier in self._notifiers:
            try:
                if asyncio.iscoroutinefunction(notifier):
                    await notifier(alert)
                else:
                    notifier(alert)
            except Exception as e:
                logger.error(f"Notifier hatası: {e}")

    def add_notifier(self, notifier: Callable) -> None:
        """
        Notifier ekler.

        Args:
            notifier: Notification callback fonksiyonu
        """
        self._notifiers.append(notifier)

    async def get_active_alerts(self) -> list[Alert]:
        """Aktif alert'leri getirir."""
        return list(self._active_alerts.values())

    async def get_alerts_by_severity(
        self,
        severity: AlertSeverity,
        limit: int = 100
    ) -> list[dict]:
        """
        Severity'ye göre alert'leri getirir.

        Args:
            severity: Ciddiyet seviyesi
            limit: Maksimum sayı

        Returns:
            Alert dict listesi
        """
        if not self.redis_client:
            return [
                a.to_dict()
                for a in self._active_alerts.values()
                if a.severity == severity
            ][:limit]

        try:
            alert_ids = await self.redis_client.lrange(
                f"kiro2:health:alerts:{severity.value}",
                0, limit - 1
            )

            alerts = []
            for alert_id in alert_ids:
                data = await self.redis_client.get(
                    f"kiro2:health:alerts:{alert_id.decode()}"
                )
                if data:
                    import ast
                    alerts.append(ast.literal_eval(data.decode()))

            return alerts

        except Exception as e:
            logger.error(f"Alerts getirilemedi: {e}")
            return []

    async def get_alert_stats(self) -> dict:
        """Alert istatistiklerini getirir."""
        stats = {
            "active_count": len(self._active_alerts),
            "by_severity": {
                "critical": 0,
                "warning": 0,
                "info": 0
            },
            "by_type": {}
        }

        for alert in self._active_alerts.values():
            stats["by_severity"][alert.severity.value] += 1

            type_key = alert.type.value
            if type_key not in stats["by_type"]:
                stats["by_type"][type_key] = 0
            stats["by_type"][type_key] += 1

        return stats
