"""
Distributed Monitoring Sidekick
FAZ 3.2: Health/Monitoring optimization for microservices architecture
Provides unified monitoring, distributed tracing, and alerting
"""

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

import httpx
from prometheus_client import Counter, Gauge, Histogram, Info

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ServiceHealth:
    """Health status for a service"""
    service_name: str
    status: ServiceStatus
    response_time_ms: float
    last_check: datetime
    details: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class TraceSpan:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    service_name: str
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: dict[str, str] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)
    error: bool = False

    def finish(self) -> None:
        """Complete the span"""
        self.end_time = datetime.now()
        self.duration_ms = (
            (self.end_time - self.start_time).total_seconds() * 1000
        )


@dataclass
class Alert:
    """Monitoring alert"""
    id: str
    severity: AlertSeverity
    service_name: str
    message: str
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False


class MicroserviceRegistry:
    """Registry of all microservices for monitoring"""

    SERVICES = {
        "backend": {
            "url": "http://localhost:8000",
            "health_endpoint": "/health",
            "critical": True,
        },
        "exam-service": {
            "url": "http://localhost:8001",
            "health_endpoint": "/health",
            "critical": True,
        },
        "question-service": {
            "url": "http://localhost:8002",
            "health_endpoint": "/health",
            "critical": True,
        },
        "irt-service": {
            "url": "http://localhost:8003",
            "health_endpoint": "/health",
            "critical": False,
        },
        "ai-service": {
            "url": "http://localhost:8004",
            "health_endpoint": "/health",
            "critical": False,
        },
        "learning-path-service": {
            "url": "http://localhost:8005",
            "health_endpoint": "/health",
            "critical": False,
        },
    }

    @classmethod
    def get_all_services(cls) -> dict[str, dict]:
        """Get all registered services"""
        return cls.SERVICES.copy()

    @classmethod
    def get_critical_services(cls) -> dict[str, dict]:
        """Get critical services only"""
        return {
            name: config
            for name, config in cls.SERVICES.items()
            if config.get("critical", False)
        }


class DistributedTracer:
    """Distributed tracing for microservices"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.active_spans: dict[str, TraceSpan] = {}
        self._trace_storage: list[TraceSpan] = []
        self._max_stored_traces = 10000

        # Prometheus metrics
        self.span_duration = Histogram(
            "trace_span_duration_seconds",
            "Duration of trace spans",
            ["service", "operation"],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )
        self.active_spans_gauge = Gauge(
            "trace_active_spans",
            "Number of active spans",
            ["service"],
        )

    def start_span(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tags: Optional[dict[str, str]] = None,
    ) -> TraceSpan:
        """Start a new trace span"""
        span = TraceSpan(
            trace_id=trace_id or str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            service_name=self.service_name,
            operation_name=operation_name,
            start_time=datetime.now(),
            tags=tags or {},
        )
        self.active_spans[span.span_id] = span
        self.active_spans_gauge.labels(service=self.service_name).inc()
        return span

    def finish_span(self, span: TraceSpan) -> None:
        """Finish a trace span"""
        span.finish()

        # Record metrics
        self.span_duration.labels(
            service=self.service_name,
            operation=span.operation_name,
        ).observe(span.duration_ms / 1000)

        # Remove from active and store
        self.active_spans.pop(span.span_id, None)
        self.active_spans_gauge.labels(service=self.service_name).dec()

        # Store completed span
        self._trace_storage.append(span)
        if len(self._trace_storage) > self._max_stored_traces:
            self._trace_storage = self._trace_storage[-self._max_stored_traces:]

    def get_trace(self, trace_id: str) -> list[TraceSpan]:
        """Get all spans for a trace"""
        return [s for s in self._trace_storage if s.trace_id == trace_id]

    def inject_headers(self, span: TraceSpan) -> dict[str, str]:
        """Generate headers for trace propagation"""
        return {
            "X-Trace-ID": span.trace_id,
            "X-Span-ID": span.span_id,
            "X-Parent-Span-ID": span.parent_span_id or "",
        }

    def extract_headers(self, headers: dict[str, str]) -> tuple[Optional[str], Optional[str]]:
        """Extract trace info from headers"""
        return (
            headers.get("X-Trace-ID") or headers.get("x-trace-id"),
            headers.get("X-Span-ID") or headers.get("x-span-id"),
        )


class ServiceHealthChecker:
    """Health checker for all microservices"""

    def __init__(self):
        self.health_cache: dict[str, ServiceHealth] = {}
        self.cache_ttl = timedelta(seconds=30)

        # Prometheus metrics
        self.service_up = Gauge(
            "service_up",
            "Whether the service is up (1) or down (0)",
            ["service"],
        )
        self.service_response_time = Histogram(
            "service_health_check_duration_seconds",
            "Health check response time",
            ["service"],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )
        self.health_check_errors = Counter(
            "health_check_errors_total",
            "Total health check errors",
            ["service"],
        )

    async def check_service(
        self,
        service_name: str,
        service_config: dict[str, Any],
    ) -> ServiceHealth:
        """Check health of a single service"""
        url = f"{service_config['url']}{service_config['health_endpoint']}"
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    status = ServiceStatus.HEALTHY
                    details = response.json() if response.content else {}
                elif response.status_code == 503:
                    status = ServiceStatus.DEGRADED
                    details = response.json() if response.content else {}
                else:
                    status = ServiceStatus.UNHEALTHY
                    details = {"status_code": response.status_code}

                # Record metrics
                self.service_up.labels(service=service_name).set(
                    1 if status == ServiceStatus.HEALTHY else 0
                )
                self.service_response_time.labels(
                    service=service_name
                ).observe(response_time / 1000)

                return ServiceHealth(
                    service_name=service_name,
                    status=status,
                    response_time_ms=response_time,
                    last_check=datetime.now(),
                    details=details,
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.service_up.labels(service=service_name).set(0)
            self.health_check_errors.labels(service=service_name).inc()

            return ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_message=str(e),
            )

    async def check_all_services(self) -> dict[str, ServiceHealth]:
        """Check health of all registered services"""
        services = MicroserviceRegistry.get_all_services()
        tasks = []

        for name, config in services.items():
            tasks.append(self.check_service(name, config))

        results = await asyncio.gather(*tasks)

        health_map = {}
        for health in results:
            health_map[health.service_name] = health
            self.health_cache[health.service_name] = health

        return health_map

    def get_cached_health(
        self,
        service_name: str,
    ) -> Optional[ServiceHealth]:
        """Get cached health status"""
        cached = self.health_cache.get(service_name)
        if cached:
            age = datetime.now() - cached.last_check
            if age < self.cache_ttl:
                return cached
        return None

    def get_overall_status(
        self,
        health_map: dict[str, ServiceHealth],
    ) -> ServiceStatus:
        """Determine overall system status"""
        critical_services = MicroserviceRegistry.get_critical_services()

        unhealthy_critical = False
        any_degraded = False

        for name, health in health_map.items():
            if name in critical_services:
                if health.status == ServiceStatus.UNHEALTHY:
                    unhealthy_critical = True
                elif health.status == ServiceStatus.DEGRADED:
                    any_degraded = True
            else:
                if health.status != ServiceStatus.HEALTHY:
                    any_degraded = True

        if unhealthy_critical:
            return ServiceStatus.UNHEALTHY
        elif any_degraded:
            return ServiceStatus.DEGRADED
        return ServiceStatus.HEALTHY


class AlertManager:
    """Manages monitoring alerts"""

    def __init__(self):
        self.alerts: list[Alert] = []
        self.alert_handlers: list[Callable[[Alert], None]] = []
        self._max_alerts = 1000

        # Prometheus metrics
        self.alerts_total = Counter(
            "monitoring_alerts_total",
            "Total alerts generated",
            ["severity", "service"],
        )
        self.active_alerts = Gauge(
            "monitoring_active_alerts",
            "Number of active (unresolved) alerts",
            ["severity"],
        )

    def register_handler(self, handler: Callable[[Alert], None]) -> None:
        """Register an alert handler"""
        self.alert_handlers.append(handler)

    def create_alert(
        self,
        severity: AlertSeverity,
        service_name: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> Alert:
        """Create and dispatch a new alert"""
        alert = Alert(
            id=str(uuid.uuid4()),
            severity=severity,
            service_name=service_name,
            message=message,
            timestamp=datetime.now(),
            details=details or {},
        )

        self.alerts.append(alert)
        if len(self.alerts) > self._max_alerts:
            self.alerts = self.alerts[-self._max_alerts:]

        # Update metrics
        self.alerts_total.labels(
            severity=severity.value,
            service=service_name,
        ).inc()
        self.active_alerts.labels(severity=severity.value).inc()

        # Dispatch to handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

        return alert

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                self.active_alerts.labels(
                    severity=alert.severity.value
                ).dec()
                return True
        return False

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
    ) -> list[Alert]:
        """Get active (unresolved) alerts"""
        active = [a for a in self.alerts if not a.resolved]
        if severity:
            active = [a for a in active if a.severity == severity]
        return active

    def get_alerts_by_service(self, service_name: str) -> list[Alert]:
        """Get alerts for a specific service"""
        return [a for a in self.alerts if a.service_name == service_name]


class DistributedMonitoringSidekick:
    """
    Main monitoring sidekick for KIRO2 microservices

    Features:
    - Distributed tracing across services
    - Health checking for all microservices
    - Alerting system with severity levels
    - Prometheus metrics integration
    - Kubernetes probe support
    """

    def __init__(self, service_name: str = "kiro2-backend"):
        self.service_name = service_name
        self.tracer = DistributedTracer(service_name)
        self.health_checker = ServiceHealthChecker()
        self.alert_manager = AlertManager()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # System info
        self.system_info = Info(
            "kiro2_monitoring",
            "KIRO2 monitoring sidekick information",
        )
        self.system_info.info({
            "service": service_name,
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
        })

    async def start_background_monitoring(
        self,
        interval_seconds: int = 30,
    ) -> None:
        """Start background health monitoring"""
        self._running = True

        async def monitor_loop():
            while self._running:
                try:
                    await self._run_health_checks()
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                await asyncio.sleep(interval_seconds)

        self._monitoring_task = asyncio.create_task(monitor_loop())
        logger.info(
            f"[Monitoring Sidekick] Started background monitoring "
            f"(interval: {interval_seconds}s)"
        )

    async def stop_background_monitoring(self) -> None:
        """Stop background health monitoring"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("[Monitoring Sidekick] Stopped background monitoring")

    async def _run_health_checks(self) -> None:
        """Run health checks and generate alerts if needed"""
        health_map = await self.health_checker.check_all_services()

        for service_name, health in health_map.items():
            if health.status == ServiceStatus.UNHEALTHY:
                self.alert_manager.create_alert(
                    severity=AlertSeverity.ERROR,
                    service_name=service_name,
                    message=f"Service {service_name} is unhealthy",
                    details={
                        "error": health.error_message,
                        "response_time_ms": health.response_time_ms,
                    },
                )
            elif health.status == ServiceStatus.DEGRADED:
                self.alert_manager.create_alert(
                    severity=AlertSeverity.WARNING,
                    service_name=service_name,
                    message=f"Service {service_name} is degraded",
                    details=health.details,
                )

    async def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status"""
        health_map = await self.health_checker.check_all_services()
        overall_status = self.health_checker.get_overall_status(health_map)
        active_alerts = self.alert_manager.get_active_alerts()

        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "services": {
                name: {
                    "status": health.status.value,
                    "response_time_ms": health.response_time_ms,
                    "last_check": health.last_check.isoformat(),
                    "error": health.error_message,
                }
                for name, health in health_map.items()
            },
            "alerts": {
                "total_active": len(active_alerts),
                "by_severity": {
                    severity.value: len([
                        a for a in active_alerts
                        if a.severity == severity
                    ])
                    for severity in AlertSeverity
                },
            },
            "monitoring": {
                "background_active": self._running,
                "service_name": self.service_name,
            },
        }

    def trace_request(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ):
        """Context manager for tracing requests"""
        return TracingContext(
            tracer=self.tracer,
            operation_name=operation_name,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )

    # Kubernetes probe endpoints
    async def liveness_probe(self) -> dict[str, Any]:
        """Kubernetes liveness probe"""
        return {
            "status": "alive",
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
        }

    async def readiness_probe(self) -> dict[str, Any]:
        """Kubernetes readiness probe"""
        # Check critical dependencies
        critical_services = MicroserviceRegistry.get_critical_services()
        all_ready = True

        for name, config in critical_services.items():
            if name == self.service_name:
                continue
            cached = self.health_checker.get_cached_health(name)
            if cached and cached.status == ServiceStatus.UNHEALTHY:
                all_ready = False
                break

        return {
            "ready": all_ready,
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
        }

    async def startup_probe(self) -> dict[str, Any]:
        """Kubernetes startup probe"""
        return {
            "started": True,
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
        }


class TracingContext:
    """Context manager for distributed tracing"""

    def __init__(
        self,
        tracer: DistributedTracer,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ):
        self.tracer = tracer
        self.operation_name = operation_name
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.span: Optional[TraceSpan] = None

    def __enter__(self) -> TraceSpan:
        self.span = self.tracer.start_span(
            operation_name=self.operation_name,
            trace_id=self.trace_id,
            parent_span_id=self.parent_span_id,
        )
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.span:
            if exc_type:
                self.span.error = True
                self.span.logs.append({
                    "event": "error",
                    "error.type": str(exc_type.__name__) if exc_type else None,
                    "error.message": str(exc_val) if exc_val else None,
                })
            self.tracer.finish_span(self.span)

    async def __aenter__(self) -> TraceSpan:
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)


# Global monitoring sidekick instance
_monitoring_sidekick: Optional[DistributedMonitoringSidekick] = None


def get_monitoring_sidekick(
    service_name: str = "kiro2-backend",
) -> DistributedMonitoringSidekick:
    """Get global monitoring sidekick"""
    global _monitoring_sidekick
    if _monitoring_sidekick is None:
        _monitoring_sidekick = DistributedMonitoringSidekick(service_name)
    return _monitoring_sidekick


async def init_monitoring(service_name: str = "kiro2-backend") -> DistributedMonitoringSidekick:
    """Initialize and start monitoring sidekick"""
    sidekick = get_monitoring_sidekick(service_name)
    await sidekick.start_background_monitoring()
    return sidekick
