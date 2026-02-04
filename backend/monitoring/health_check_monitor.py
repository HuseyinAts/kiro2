"""
Health Check Monitoring Service
Teknofest 2025 - Eğitim Eylemci Projesi

Periyodik health check yapan ve metrikleri Prometheus'a expose eden servis.
Requirements: 4.5, 4.11, 5.4
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Optional

from prometheus_client import Gauge, Counter, Histogram

logger = logging.getLogger(__name__)


class HealthCheckMonitor:
    """
    Health check monitoring servisi

    Periyodik olarak health check endpoint'ini çağırır ve sonuçları
    Prometheus metriklerine kaydeder.
    """

    def __init__(self, health_check_service, check_interval: int = 30, registry=None):
        """
        Initialize health check monitor

        Args:
            health_check_service: HealthCheckService instance
            check_interval: Health check interval in seconds (default: 30)
            registry: Prometheus registry
        """
        self.health_check_service = health_check_service
        self.check_interval = check_interval
        self.registry = registry

        # Monitoring state
        self._running = False
        self._last_check_time: Optional[datetime] = None
        self._consecutive_failures = 0

        # Initialize Prometheus metrics
        self._init_metrics()

        logger.info(f"HealthCheckMonitor initialized with {check_interval}s interval")

    def _init_metrics(self):
        """Initialize Prometheus metrics for health monitoring"""

        # Gauge: Component health status (1 = healthy, 0 = unhealthy)
        self.component_health_status = Gauge(
            "health_check_component_status",
            "Health status of system components (1=healthy, 0=unhealthy)",
            ["component"],
            registry=self.registry,
        )

        # Gauge: Overall system health (1 = healthy, 0 = unhealthy)
        self.overall_health_status = Gauge(
            "health_check_overall_status",
            "Overall system health status (1=healthy, 0=unhealthy)",
            registry=self.registry,
        )

        # Histogram: Health check response time
        self.health_check_response_time = Histogram(
            "health_check_response_time_ms",
            "Health check response time in milliseconds",
            buckets=(10, 50, 100, 200, 500, 1000, 2000),
            registry=self.registry,
        )

        # Counter: Health check executions
        self.health_check_executions = Counter(
            "health_check_executions_total",
            "Total number of health check executions",
            ["status"],  # success, failure
            registry=self.registry,
        )

        # Counter: Component failures
        self.component_failures = Counter(
            "health_check_component_failures_total",
            "Total number of component health check failures",
            ["component"],
            registry=self.registry,
        )

        # Gauge: Consecutive failures
        self.consecutive_failures_gauge = Gauge(
            "health_check_consecutive_failures",
            "Number of consecutive health check failures",
            registry=self.registry,
        )

        # Gauge: Last successful check timestamp
        self.last_successful_check = Gauge(
            "health_check_last_successful_timestamp",
            "Timestamp of last successful health check",
            registry=self.registry,
        )

        logger.info("Health check monitoring metrics initialized")

    async def start(self):
        """Start health check monitoring loop"""
        if self._running:
            logger.warning("Health check monitor already running")
            return

        self._running = True
        logger.info("Starting health check monitoring loop")

        try:
            while self._running:
                await self._perform_health_check()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Health check monitoring loop error: {e}", exc_info=True)
            self._running = False

    async def stop(self):
        """Stop health check monitoring loop"""
        logger.info("Stopping health check monitoring loop")
        self._running = False

    async def _perform_health_check(self):
        """Perform health check and update metrics"""
        start_time = time.time()

        try:
            # Call health check service
            health_result = await self.health_check_service.check_health()

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            self.health_check_response_time.observe(response_time_ms)

            # Update last check time
            self._last_check_time = datetime.now()

            # Update overall health status
            overall_healthy = health_result.overall_status.value == "healthy"
            self.overall_health_status.set(1 if overall_healthy else 0)

            # Update component health statuses
            for component in health_result.components:
                component_healthy = component.status.value == "healthy"

                self.component_health_status.labels(
                    component=component.name.lower().replace(" ", "_")
                ).set(1 if component_healthy else 0)

                # Track component failures
                if not component_healthy:
                    self.component_failures.labels(
                        component=component.name.lower().replace(" ", "_")
                    ).inc()

                    logger.warning(
                        f"Component unhealthy: {component.name} - "
                        f"{component.error_message}"
                    )

            # Update success metrics
            self.health_check_executions.labels(status="success").inc()
            self._consecutive_failures = 0
            self.consecutive_failures_gauge.set(0)
            self.last_successful_check.set(time.time())

            # Log health check result
            logger.info(
                f"Health check completed: status={health_result.overall_status.value}, "
                f"response_time={response_time_ms:.2f}ms"
            )

            # Log detailed component status
            for component in health_result.components:
                logger.debug(
                    f"  - {component.name}: {component.status.value} "
                    f"({component.response_time_ms:.2f}ms)"
                )

        except Exception as e:
            # Health check failed
            response_time_ms = (time.time() - start_time) * 1000

            self.health_check_executions.labels(status="failure").inc()
            self._consecutive_failures += 1
            self.consecutive_failures_gauge.set(self._consecutive_failures)

            # Set all components to unhealthy
            self.overall_health_status.set(0)

            logger.error(
                f"Health check failed: {e} "
                f"(consecutive failures: {self._consecutive_failures})",
                exc_info=True,
            )

            # Alert if too many consecutive failures
            if self._consecutive_failures >= 3:
                logger.critical(
                    f"CRITICAL: {self._consecutive_failures} consecutive "
                    f"health check failures!"
                )

    def get_status(self) -> Dict:
        """
        Get current monitoring status

        Returns:
            Dict: Monitoring status information
        """
        return {
            "running": self._running,
            "check_interval": self.check_interval,
            "last_check_time": (
                self._last_check_time.isoformat() if self._last_check_time else None
            ),
            "consecutive_failures": self._consecutive_failures,
        }


# Global health check monitor instance
_global_health_monitor: Optional[HealthCheckMonitor] = None


def get_health_monitor() -> Optional[HealthCheckMonitor]:
    """
    Get global health check monitor instance

    Returns:
        HealthCheckMonitor: Global monitor instance or None
    """
    return _global_health_monitor


def set_health_monitor(monitor: HealthCheckMonitor):
    """
    Set global health check monitor instance

    Args:
        monitor: HealthCheckMonitor instance
    """
    global _global_health_monitor
    _global_health_monitor = monitor
    logger.info("Global health check monitor instance set")


async def start_health_monitoring(health_check_service, check_interval: int = 30):
    """
    Start health check monitoring

    Args:
        health_check_service: HealthCheckService instance
        check_interval: Check interval in seconds
    """
    monitor = HealthCheckMonitor(
        health_check_service=health_check_service, check_interval=check_interval
    )

    set_health_monitor(monitor)

    # Start monitoring in background
    asyncio.create_task(monitor.start())

    logger.info("Health check monitoring started")


async def stop_health_monitoring():
    """Stop health check monitoring"""
    monitor = get_health_monitor()
    if monitor:
        await monitor.stop()
        logger.info("Health check monitoring stopped")
