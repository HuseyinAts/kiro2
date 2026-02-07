"""
Prometheus Metrics - API Response Time Optimization

Bu modül, Prometheus client library kullanarak latency, throughput ve error metrics toplar.
Histogram, Summary ve Counter metric tipleri kullanılır.

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-8.1, REQ-8.4, REQ-8.5
"""

import time
import logging
from typing import Optional, Callable, Any
from functools import wraps
from contextlib import contextmanager

try:
    from prometheus_client import (
        Histogram,
        Counter,
        Gauge,
        Summary,
        generate_latest,
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        REGISTRY,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Stub implementations for when prometheus is not available
    class StubMetric:
        def labels(self, **kwargs): return self
        def observe(self, value): pass
        def inc(self, amount=1): pass
        def dec(self, amount=1): pass
        def set(self, value): pass

    Histogram = Counter = Gauge = Summary = StubMetric
    REGISTRY = None

logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS METRICS DEFINITIONS
# =============================================================================

# Request latency histogram with buckets optimized for API response times
# Buckets: 5ms, 10ms, 25ms, 50ms, 100ms, 200ms, 500ms, 1s, 2.5s, 5s, 10s
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint", "method", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.5, 5.0, 10.0)
) if PROMETHEUS_AVAILABLE else StubMetric()

# Request latency summary for percentile calculations (P50, P95, P99)
REQUEST_LATENCY_SUMMARY = Summary(
    "http_request_latency_summary_seconds",
    "HTTP request latency percentiles",
    ["endpoint", "method"],
    # Calculate P50, P90, P95, P99 percentiles
) if PROMETHEUS_AVAILABLE else StubMetric()

# Request count counter
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["endpoint", "method", "status"]
) if PROMETHEUS_AVAILABLE else StubMetric()

# Error count counter (5xx responses)
ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors (5xx)",
    ["endpoint", "method", "status", "error_type"]
) if PROMETHEUS_AVAILABLE else StubMetric()

# Active requests gauge
ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Currently active HTTP requests",
    ["endpoint", "method"]
) if PROMETHEUS_AVAILABLE else StubMetric()

# Cache hit/miss counter
CACHE_OPERATIONS = Counter(
    "cache_operations_total",
    "Cache operations",
    ["operation", "result"]  # operation: get/set/delete, result: hit/miss/success/failure
) if PROMETHEUS_AVAILABLE else StubMetric()

# Database query latency
DB_QUERY_LATENCY = Histogram(
    "db_query_latency_seconds",
    "Database query latency in seconds",
    ["query_type", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
) if PROMETHEUS_AVAILABLE else StubMetric()


# =============================================================================
# METRICS COLLECTOR CLASS
# =============================================================================

class MetricsCollector:
    """
    Merkezi metrics toplama ve yönetim sınıfı.

    Prometheus metrics'lerini toplar, percentile hesaplar ve
    SLA violation'ları tespit eder.

    Attributes:
        enabled: Metrics toplamanın aktif olup olmadığı
        sla_p50_ms: P50 SLA hedefi (ms)
        sla_p95_ms: P95 SLA hedefi (ms)
        sla_p99_ms: P99 SLA hedefi (ms)

    Example:
        collector = MetricsCollector()

        # Record a request
        with collector.track_request("/api/questions", "GET"):
            response = await get_questions()

        # Get metrics
        metrics = collector.get_metrics_text()
    """

    def __init__(
        self,
        enabled: bool = True,
        sla_p50_ms: float = 100.0,
        sla_p95_ms: float = 200.0,
        sla_p99_ms: float = 500.0
    ):
        """
        MetricsCollector başlatır.

        Args:
            enabled: Metrics toplamayı etkinleştir
            sla_p50_ms: P50 SLA hedefi (milliseconds)
            sla_p95_ms: P95 SLA hedefi (milliseconds)
            sla_p99_ms: P99 SLA hedefi (milliseconds)
        """
        self.enabled = enabled and PROMETHEUS_AVAILABLE
        self.sla_p50_ms = sla_p50_ms
        self.sla_p95_ms = sla_p95_ms
        self.sla_p99_ms = sla_p99_ms

        # Per-endpoint timing storage for local percentile calculation
        self._endpoint_timings: dict[str, list[float]] = {}
        self._max_timings_per_endpoint = 1000

        if self.enabled:
            logger.info(
                f"MetricsCollector initialized: SLA targets P50={sla_p50_ms}ms, "
                f"P95={sla_p95_ms}ms, P99={sla_p99_ms}ms"
            )
        else:
            logger.warning("MetricsCollector disabled (prometheus_client not available)")

    def record_latency(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_seconds: float
    ) -> None:
        """
        Request latency kaydeder.

        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP response status code
            duration_seconds: Request duration in seconds
        """
        if not self.enabled:
            return

        try:
            # Record to histogram
            REQUEST_LATENCY.labels(
                endpoint=endpoint,
                method=method,
                status=str(status_code)
            ).observe(duration_seconds)

            # Record to summary for percentiles
            REQUEST_LATENCY_SUMMARY.labels(
                endpoint=endpoint,
                method=method
            ).observe(duration_seconds)

            # Increment request count
            REQUEST_COUNT.labels(
                endpoint=endpoint,
                method=method,
                status=str(status_code)
            ).inc()

            # Track locally for percentile calculation
            key = f"{method}:{endpoint}"
            if key not in self._endpoint_timings:
                self._endpoint_timings[key] = []

            timings = self._endpoint_timings[key]
            timings.append(duration_seconds * 1000)  # Convert to ms

            # Trim old timings
            if len(timings) > self._max_timings_per_endpoint:
                self._endpoint_timings[key] = timings[-self._max_timings_per_endpoint:]

            # Log slow requests
            duration_ms = duration_seconds * 1000
            if duration_ms > self.sla_p95_ms:
                logger.warning(
                    f"Slow request detected: {method} {endpoint} took {duration_ms:.2f}ms "
                    f"(SLA P95: {self.sla_p95_ms}ms)"
                )

        except Exception as e:
            logger.error(f"Failed to record latency metric: {e}")

    def record_error(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        error_type: str = "unknown"
    ) -> None:
        """
        Error kaydeder.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP error status code (5xx)
            error_type: Error type/classification
        """
        if not self.enabled:
            return

        try:
            ERROR_COUNT.labels(
                endpoint=endpoint,
                method=method,
                status=str(status_code),
                error_type=error_type
            ).inc()

            logger.error(
                f"Error recorded: {method} {endpoint} - {status_code} ({error_type})"
            )

        except Exception as e:
            logger.error(f"Failed to record error metric: {e}")

    def record_cache_operation(
        self,
        operation: str,
        result: str
    ) -> None:
        """
        Cache işlemini kaydeder.

        Args:
            operation: İşlem tipi (get, set, delete)
            result: Sonuç (hit, miss, success, failure)
        """
        if not self.enabled:
            return

        try:
            CACHE_OPERATIONS.labels(
                operation=operation,
                result=result
            ).inc()
        except Exception as e:
            logger.error(f"Failed to record cache metric: {e}")

    def record_db_query(
        self,
        query_type: str,
        table: str,
        duration_seconds: float
    ) -> None:
        """
        Database query latency kaydeder.

        Args:
            query_type: Query tipi (select, insert, update, delete)
            table: Tablo adı
            duration_seconds: Query süresi (saniye)
        """
        if not self.enabled:
            return

        try:
            DB_QUERY_LATENCY.labels(
                query_type=query_type,
                table=table
            ).observe(duration_seconds)

            # Log slow queries (> 50ms as per REQ-5.6)
            duration_ms = duration_seconds * 1000
            if duration_ms > 50:
                logger.warning(
                    f"Slow query detected: {query_type} on {table} took {duration_ms:.2f}ms"
                )

        except Exception as e:
            logger.error(f"Failed to record DB query metric: {e}")

    @contextmanager
    def track_request(self, endpoint: str, method: str):
        """
        Request tracking context manager.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Yields:
            dict: Tracking context with timing info

        Example:
            with collector.track_request("/api/users", "GET") as ctx:
                response = await get_users()
                ctx["status_code"] = 200
        """
        context = {"status_code": 200, "error_type": None}
        start_time = time.perf_counter()

        if self.enabled:
            try:
                ACTIVE_REQUESTS.labels(endpoint=endpoint, method=method).inc()
            except Exception:
                pass

        try:
            yield context
        except Exception as e:
            context["status_code"] = 500
            context["error_type"] = type(e).__name__
            raise
        finally:
            duration = time.perf_counter() - start_time

            if self.enabled:
                try:
                    ACTIVE_REQUESTS.labels(endpoint=endpoint, method=method).dec()
                except Exception:
                    pass

            self.record_latency(
                endpoint=endpoint,
                method=method,
                status_code=context["status_code"],
                duration_seconds=duration
            )

            if context["status_code"] >= 500:
                self.record_error(
                    endpoint=endpoint,
                    method=method,
                    status_code=context["status_code"],
                    error_type=context["error_type"] or "unknown"
                )

    def get_percentiles(self, endpoint: str, method: str) -> dict[str, float]:
        """
        Endpoint için percentile değerlerini hesaplar.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Returns:
            P50, P95, P99 değerleri (ms)
        """
        key = f"{method}:{endpoint}"
        timings = self._endpoint_timings.get(key, [])

        if not timings:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_timings = sorted(timings)
        n = len(sorted_timings)

        def percentile(p: float) -> float:
            idx = int(n * p / 100)
            return sorted_timings[min(idx, n - 1)]

        return {
            "p50": percentile(50),
            "p95": percentile(95),
            "p99": percentile(99)
        }

    def check_sla_compliance(self, endpoint: str, method: str) -> dict[str, Any]:
        """
        SLA uyumluluğunu kontrol eder.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Returns:
            SLA compliance durumu
        """
        percentiles = self.get_percentiles(endpoint, method)

        return {
            "endpoint": endpoint,
            "method": method,
            "percentiles": percentiles,
            "sla_targets": {
                "p50_ms": self.sla_p50_ms,
                "p95_ms": self.sla_p95_ms,
                "p99_ms": self.sla_p99_ms
            },
            "compliant": {
                "p50": percentiles["p50"] <= self.sla_p50_ms,
                "p95": percentiles["p95"] <= self.sla_p95_ms,
                "p99": percentiles["p99"] <= self.sla_p99_ms
            },
            "overall_compliant": (
                percentiles["p50"] <= self.sla_p50_ms and
                percentiles["p95"] <= self.sla_p95_ms and
                percentiles["p99"] <= self.sla_p99_ms
            )
        }

    def get_metrics_text(self) -> str:
        """
        Prometheus formatında metrics text döndürür.

        Returns:
            Prometheus metrics text
        """
        if not self.enabled or not PROMETHEUS_AVAILABLE:
            return "# Prometheus metrics not available\n"

        try:
            return generate_latest(REGISTRY).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return f"# Error generating metrics: {e}\n"

    def get_content_type(self) -> str:
        """Prometheus content type döndürür."""
        if PROMETHEUS_AVAILABLE:
            return CONTENT_TYPE_LATEST
        return "text/plain"


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Global MetricsCollector instance döndürür.

    Returns:
        MetricsCollector singleton instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# =============================================================================
# DECORATOR FOR AUTOMATIC METRICS
# =============================================================================

def track_metrics(endpoint: Optional[str] = None):
    """
    Fonksiyon için otomatik metrics tracking decorator.

    Args:
        endpoint: Override endpoint name (default: function name)

    Returns:
        Decorated function

    Example:
        @track_metrics("/api/users")
        async def get_users():
            ...
    """
    def decorator(func: Callable) -> Callable:
        nonlocal endpoint
        if endpoint is None:
            endpoint = f"/{func.__name__}"

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            with collector.track_request(endpoint, "FUNC") as ctx:
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    ctx["status_code"] = 500
                    ctx["error_type"] = type(e).__name__
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            with collector.track_request(endpoint, "FUNC") as ctx:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    ctx["status_code"] = 500
                    ctx["error_type"] = type(e).__name__
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
