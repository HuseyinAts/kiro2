"""
Alert System - API Response Time Optimization

Bu modül, P95 latency threshold aşımları için alert sistemi sağlar.
Alert throttling ve severity seviyeleri desteklenir.

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-8.2
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity seviyeleri."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """
    Alert veri yapısı.

    Attributes:
        name: Alert adı
        message: Alert mesajı
        severity: Alert severity seviyesi
        endpoint: İlgili endpoint (opsiyonel)
        value: Tetikleyen değer
        threshold: Threshold değeri
        timestamp: Alert zamanı
        metadata: Ek metadata
    """
    name: str
    message: str
    severity: AlertSeverity
    endpoint: str | None = None
    value: float = 0.0
    threshold: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Alert'i dictionary'e dönüştürür."""
        return {
            "name": self.name,
            "message": self.message,
            "severity": self.severity.value,
            "endpoint": self.endpoint,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class AlertManager:
    """
    Alert yönetim sınıfı.

    P95 latency threshold aşımları için alert üretir.
    Alert throttling ile aynı alert'in tekrar tekrar gönderilmesi engellenir.

    Attributes:
        p95_threshold_ms: P95 latency threshold (ms)
        throttle_seconds: Aynı alert için minimum bekleme süresi (saniye)
        enabled: Alert sisteminin aktif olup olmadığı

    Example:
        manager = AlertManager(p95_threshold_ms=200)

        # Check latency and trigger alert if needed
        manager.check_latency("/api/questions", p95_ms=250)

        # Manual alert
        manager.send_alert(
            name="high_error_rate",
            message="Error rate exceeded 5%",
            severity=AlertSeverity.CRITICAL
        )
    """

    def __init__(
        self,
        p95_threshold_ms: float = 200.0,
        throttle_seconds: float = 300.0,  # 5 minutes
        enabled: bool = True
    ):
        """
        AlertManager başlatır.

        Args:
            p95_threshold_ms: P95 latency threshold (milliseconds)
            throttle_seconds: Alert throttling süresi (saniye)
            enabled: Alert sistemini etkinleştir
        """
        self.p95_threshold_ms = p95_threshold_ms
        self.throttle_seconds = throttle_seconds
        self.enabled = enabled

        # Track last alert times for throttling
        self._last_alert_times: dict[str, float] = {}

        # Alert handlers (callbacks)
        self._handlers: list[Callable[[Alert], None]] = []

        # Alert history
        self._alert_history: list[Alert] = []
        self._max_history = 1000

        logger.info(
            f"AlertManager initialized: P95 threshold={p95_threshold_ms}ms, "
            f"throttle={throttle_seconds}s"
        )

    def add_handler(self, handler: Callable[[Alert], None]) -> None:
        """
        Alert handler ekler.

        Args:
            handler: Alert callback fonksiyonu
        """
        self._handlers.append(handler)
        logger.debug(f"Alert handler added: {handler.__name__}")

    def remove_handler(self, handler: Callable[[Alert], None]) -> None:
        """
        Alert handler kaldırır.

        Args:
            handler: Kaldırılacak handler
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
            logger.debug(f"Alert handler removed: {handler.__name__}")

    def _should_throttle(self, alert_key: str) -> bool:
        """
        Alert'in throttle edilip edilmeyeceğini kontrol eder.

        Args:
            alert_key: Alert tanımlayıcısı

        Returns:
            True ise alert throttle edilmeli
        """
        current_time = time.time()
        last_time = self._last_alert_times.get(alert_key, 0)

        if current_time - last_time < self.throttle_seconds:
            return True

        self._last_alert_times[alert_key] = current_time
        return False

    def send_alert(
        self,
        name: str,
        message: str,
        severity: AlertSeverity,
        endpoint: str | None = None,
        value: float = 0.0,
        threshold: float = 0.0,
        metadata: dict | None = None,
        force: bool = False
    ) -> bool:
        """
        Alert gönderir.

        Args:
            name: Alert adı
            message: Alert mesajı
            severity: Severity seviyesi
            endpoint: İlgili endpoint (opsiyonel)
            value: Tetikleyen değer
            threshold: Threshold değeri
            metadata: Ek metadata
            force: Throttling'i atla

        Returns:
            True ise alert başarıyla gönderildi
        """
        if not self.enabled:
            return False

        # Create alert key for throttling
        alert_key = f"{name}:{endpoint or 'global'}"

        # Check throttling
        if not force and self._should_throttle(alert_key):
            logger.debug(f"Alert throttled: {alert_key}")
            return False

        # Create alert
        alert = Alert(
            name=name,
            message=message,
            severity=severity,
            endpoint=endpoint,
            value=value,
            threshold=threshold,
            metadata=metadata or {}
        )

        # Log alert based on severity
        log_message = (
            f"[{severity.value.upper()}] {name}: {message} "
            f"(value={value:.2f}, threshold={threshold:.2f})"
        )

        if severity == AlertSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == AlertSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Store in history
        self._alert_history.append(alert)
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history:]

        # Call handlers
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

        return True

    def check_latency(
        self,
        endpoint: str,
        p95_ms: float,
        p99_ms: float | None = None
    ) -> bool:
        """
        Latency'yi kontrol eder ve gerekirse alert gönderir.

        Args:
            endpoint: API endpoint
            p95_ms: P95 latency (milliseconds)
            p99_ms: P99 latency (milliseconds, opsiyonel)

        Returns:
            True ise alert gönderildi
        """
        alert_sent = False

        # Check P95 threshold
        if p95_ms > self.p95_threshold_ms:
            severity = AlertSeverity.WARNING
            if p95_ms > self.p95_threshold_ms * 2:
                severity = AlertSeverity.CRITICAL

            alert_sent = self.send_alert(
                name="high_p95_latency",
                message=f"P95 latency ({p95_ms:.2f}ms) exceeded threshold ({self.p95_threshold_ms}ms)",
                severity=severity,
                endpoint=endpoint,
                value=p95_ms,
                threshold=self.p95_threshold_ms,
                metadata={"p99_ms": p99_ms} if p99_ms else {}
            )

        # Check P99 if provided (critical if > 500ms per REQ-8.6)
        if p99_ms and p99_ms > 500:
            self.send_alert(
                name="high_p99_latency",
                message=f"P99 latency ({p99_ms:.2f}ms) exceeded 500ms SLA",
                severity=AlertSeverity.CRITICAL,
                endpoint=endpoint,
                value=p99_ms,
                threshold=500.0
            )
            alert_sent = True

        return alert_sent

    def check_error_rate(
        self,
        endpoint: str,
        error_rate: float,
        threshold: float = 0.01  # 1%
    ) -> bool:
        """
        Error rate kontrol eder ve gerekirse alert gönderir.

        Args:
            endpoint: API endpoint
            error_rate: Error rate (0.0 - 1.0)
            threshold: Error rate threshold (default: 1%)

        Returns:
            True ise alert gönderildi
        """
        if error_rate > threshold:
            severity = AlertSeverity.WARNING
            if error_rate > threshold * 5:  # 5x threshold = critical
                severity = AlertSeverity.CRITICAL

            return self.send_alert(
                name="high_error_rate",
                message=f"Error rate ({error_rate*100:.2f}%) exceeded threshold ({threshold*100:.2f}%)",
                severity=severity,
                endpoint=endpoint,
                value=error_rate * 100,
                threshold=threshold * 100
            )

        return False

    def check_throughput(
        self,
        endpoint: str,
        rps: float,
        min_threshold: float = 100.0
    ) -> bool:
        """
        Throughput kontrol eder ve düşükse alert gönderir.

        Args:
            endpoint: API endpoint
            rps: Requests per second
            min_threshold: Minimum beklenen RPS

        Returns:
            True ise alert gönderildi
        """
        if rps < min_threshold:
            return self.send_alert(
                name="low_throughput",
                message=f"Throughput ({rps:.2f} rps) below threshold ({min_threshold} rps)",
                severity=AlertSeverity.WARNING,
                endpoint=endpoint,
                value=rps,
                threshold=min_threshold
            )

        return False

    def get_alert_history(
        self,
        limit: int = 100,
        severity: AlertSeverity | None = None
    ) -> list[dict]:
        """
        Alert geçmişini döndürür.

        Args:
            limit: Maksimum alert sayısı
            severity: Filtrelenecek severity (opsiyonel)

        Returns:
            Alert listesi
        """
        alerts = self._alert_history

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return [a.to_dict() for a in alerts[-limit:]]

    def clear_throttle_cache(self) -> None:
        """Throttle cache'ini temizler."""
        self._last_alert_times.clear()
        logger.info("Alert throttle cache cleared")


# =============================================================================
# DEFAULT ALERT HANDLERS
# =============================================================================

def log_alert_handler(alert: Alert) -> None:
    """
    Varsayılan log handler.

    Args:
        alert: Alert nesnesi
    """
    # Already logged in send_alert, this is for additional structured logging
    try:
        import structlog
        struct_logger = structlog.get_logger()
        struct_logger.bind(**alert.to_dict()).msg("Alert triggered")
    except ImportError:
        pass  # structlog not available


def webhook_alert_handler(alert: Alert) -> None:
    """
    Webhook alert handler (placeholder).

    Args:
        alert: Alert nesnesi
    """
    # Placeholder for webhook integration
    # In production, this would send to Slack, PagerDuty, etc.


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    """
    Global AlertManager instance döndürür.

    Returns:
        AlertManager singleton instance
    """
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
        # Add default handler
        _alert_manager.add_handler(log_alert_handler)
    return _alert_manager
