"""
Performance Monitoring Service - Task 58.4
REQ-48.99-48.101: API performance tracking, metrics collection

Features:
- Request/response time tracking
- Endpoint performance metrics
- Memory and CPU monitoring
- Performance alerts
- Integration with Prometheus metrics
"""
import time
import psutil
import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.structured_logger import get_logger
from core.cache_service import get_cache_service

logger = get_logger(__name__)
cache = get_cache_service()


# ==================== PERFORMANCE METRICS ====================


class PerformanceMetrics:
    """Collect and store performance metrics"""

    def __init__(self):
        self.request_times: Dict[str, List[float]] = defaultdict(list)
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.slow_requests: List[dict] = []
        self.slow_threshold = 2.0  # 2 seconds

    def record_request(
        self, endpoint: str, method: str, duration: float, status_code: int
    ):
        """Record a request"""
        key = f"{method} {endpoint}"

        # Record timing
        self.request_times[key].append(duration)
        self.request_counts[key] += 1

        # Record errors
        if status_code >= 400:
            self.error_counts[key] += 1

        # Track slow requests
        if duration > self.slow_threshold:
            self.slow_requests.append(
                {
                    "endpoint": key,
                    "duration": duration,
                    "status_code": status_code,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Keep only last 100 slow requests
            if len(self.slow_requests) > 100:
                self.slow_requests = self.slow_requests[-100:]

            logger.warning(f"Slow request: {key} ({duration:.3f}s)")

    def get_endpoint_stats(self, endpoint: str) -> dict:
        """Get statistics for an endpoint"""
        if endpoint not in self.request_times:
            return {}

        times = self.request_times[endpoint]
        return {
            "count": self.request_counts[endpoint],
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "p95_time": self._percentile(times, 95),
            "p99_time": self._percentile(times, 99),
            "error_count": self.error_counts.get(endpoint, 0),
            "error_rate": self.error_counts.get(endpoint, 0)
            / max(self.request_counts[endpoint], 1),
        }

    def get_all_stats(self) -> dict:
        """Get statistics for all endpoints"""
        return {
            endpoint: self.get_endpoint_stats(endpoint)
            for endpoint in self.request_times.keys()
        }

    def get_slow_requests(self, limit: int = 20) -> List[dict]:
        """Get recent slow requests"""
        return self.slow_requests[-limit:]

    def get_top_endpoints(self, limit: int = 10, sort_by: str = "count") -> List[tuple]:
        """
        Get top endpoints by metric

        Args:
            limit: Number of endpoints to return
            sort_by: 'count', 'avg_time', 'error_rate'
        """
        stats = []
        for endpoint in self.request_times.keys():
            endpoint_stats = self.get_endpoint_stats(endpoint)
            stats.append((endpoint, endpoint_stats))

        # Sort
        if sort_by == "count":
            stats.sort(key=lambda x: x[1]["count"], reverse=True)
        elif sort_by == "avg_time":
            stats.sort(key=lambda x: x[1]["avg_time"], reverse=True)
        elif sort_by == "error_rate":
            stats.sort(key=lambda x: x[1]["error_rate"], reverse=True)

        return stats[:limit]

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100.0))
        return sorted_data[min(index, len(sorted_data) - 1)]

    def reset(self):
        """Reset all metrics"""
        self.request_times.clear()
        self.request_counts.clear()
        self.error_counts.clear()
        self.slow_requests.clear()


# Global metrics instance
_metrics = PerformanceMetrics()


def get_performance_metrics() -> PerformanceMetrics:
    """Get global metrics instance"""
    return _metrics


# ==================== MIDDLEWARE ====================


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request performance

    Usage:
        from fastapi import FastAPI
        from core.performance_monitor import PerformanceMonitoringMiddleware

        app = FastAPI()
        app.add_middleware(PerformanceMonitoringMiddleware)
    """

    def __init__(self, app: ASGIApp, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track request performance"""
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Process request
        response = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.error(
                f"Request failed: {request.method} {request.url.path}", exc_info=e
            )
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            _metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                duration=duration,
                status_code=status_code,
            )

            # Add performance headers
            if response is not None:
                response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response


# ==================== SYSTEM METRICS ====================


class SystemMetrics:
    """Monitor system resources"""

    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=1)

    @staticmethod
    def get_memory_usage() -> dict:
        """Get memory usage information"""
        mem = psutil.virtual_memory()
        return {
            "total_mb": mem.total / (1024 * 1024),
            "available_mb": mem.available / (1024 * 1024),
            "used_mb": mem.used / (1024 * 1024),
            "percent": mem.percent,
        }

    @staticmethod
    def get_disk_usage() -> dict:
        """Get disk usage information"""
        disk = psutil.disk_usage("/")
        return {
            "total_gb": disk.total / (1024 * 1024 * 1024),
            "used_gb": disk.used / (1024 * 1024 * 1024),
            "free_gb": disk.free / (1024 * 1024 * 1024),
            "percent": disk.percent,
        }

    @staticmethod
    def get_network_io() -> dict:
        """Get network I/O statistics"""
        net = psutil.net_io_counters()
        return {
            "bytes_sent_mb": net.bytes_sent / (1024 * 1024),
            "bytes_recv_mb": net.bytes_recv / (1024 * 1024),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        }

    @classmethod
    def get_all_metrics(cls) -> dict:
        """Get all system metrics"""
        return {
            "cpu_percent": cls.get_cpu_usage(),
            "memory": cls.get_memory_usage(),
            "disk": cls.get_disk_usage(),
            "network": cls.get_network_io(),
            "timestamp": datetime.now().isoformat(),
        }


# ==================== PERFORMANCE ALERTS ====================


class PerformanceAlert:
    """Alert on performance issues"""

    def __init__(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        response_time_threshold: float = 3.0,
    ):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.response_time_threshold = response_time_threshold
        self.last_alert_time: Dict[str, datetime] = {}
        self.alert_cooldown = timedelta(minutes=5)

    def check_system_alerts(self) -> List[dict]:
        """Check for system resource alerts"""
        alerts = []

        # CPU alert
        cpu_usage = SystemMetrics.get_cpu_usage()
        if cpu_usage > self.cpu_threshold:
            if self._should_alert("cpu"):
                alerts.append(
                    {
                        "type": "cpu",
                        "severity": "warning",
                        "message": f"High CPU usage: {cpu_usage:.1f}%",
                        "value": cpu_usage,
                    }
                )
                logger.warning(f"High CPU usage detected: {cpu_usage:.1f}%")

        # Memory alert
        mem = SystemMetrics.get_memory_usage()
        if mem["percent"] > self.memory_threshold:
            if self._should_alert("memory"):
                alerts.append(
                    {
                        "type": "memory",
                        "severity": "warning",
                        "message": f'High memory usage: {mem["percent"]:.1f}%',
                        "value": mem["percent"],
                    }
                )
                logger.warning(f'High memory usage detected: {mem["percent"]:.1f}%')

        return alerts

    def check_endpoint_alerts(self) -> List[dict]:
        """Check for endpoint performance alerts"""
        alerts = []
        metrics = _metrics

        # Check top slow endpoints
        top_endpoints = metrics.get_top_endpoints(limit=5, sort_by="avg_time")

        for endpoint, stats in top_endpoints:
            if stats["avg_time"] > self.response_time_threshold:
                if self._should_alert(f"endpoint_{endpoint}"):
                    alerts.append(
                        {
                            "type": "slow_endpoint",
                            "severity": "warning",
                            "message": f'Slow endpoint: {endpoint} ({stats["avg_time"]:.2f}s avg)',
                            "endpoint": endpoint,
                            "avg_time": stats["avg_time"],
                        }
                    )
                    logger.warning(
                        f'Slow endpoint detected: {endpoint} ({stats["avg_time"]:.2f}s)'
                    )

        return alerts

    def _should_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent (cooldown logic)"""
        if alert_key not in self.last_alert_time:
            self.last_alert_time[alert_key] = datetime.now()
            return True

        time_since_last = datetime.now() - self.last_alert_time[alert_key]
        if time_since_last > self.alert_cooldown:
            self.last_alert_time[alert_key] = datetime.now()
            return True

        return False


# Global alert instance
_alert_system = PerformanceAlert()


# ==================== PERFORMANCE DECORATOR ====================


def monitor_performance(func_name: Optional[str] = None):
    """
    Decorator to monitor function performance

    Example:
        @monitor_performance("process_payment")
        async def process_payment(payment_id: int):
            # ... processing
            return result
    """

    def decorator(func: Callable) -> Callable:
        name = func_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.debug(f"Function {name} executed in {duration:.3f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Function {name} failed after {duration:.3f}s", exc_info=e
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.debug(f"Function {name} executed in {duration:.3f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Function {name} failed after {duration:.3f}s", exc_info=e
                )
                raise

        # Return appropriate wrapper
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# ==================== BACKGROUND MONITORING ====================


async def start_performance_monitoring(interval_seconds: int = 60):
    """
    Background task to continuously monitor performance

    Usage:
        import asyncio
        from core.performance_monitor import start_performance_monitoring

        asyncio.create_task(start_performance_monitoring(interval_seconds=60))
    """
    logger.info("Performance monitoring started")

    while True:
        try:
            # Check alerts
            system_alerts = _alert_system.check_system_alerts()
            endpoint_alerts = _alert_system.check_endpoint_alerts()

            all_alerts = system_alerts + endpoint_alerts

            # Log alerts
            if all_alerts:
                logger.warning(
                    f"Performance alerts: {len(all_alerts)}",
                    extra_data={"alerts": all_alerts},
                )

            # Cache system metrics
            system_metrics = SystemMetrics.get_all_metrics()
            cache.set("system_metrics", system_metrics, ttl=120, namespace="monitoring")

            # Cache endpoint stats
            endpoint_stats = _metrics.get_all_stats()
            cache.set("endpoint_stats", endpoint_stats, ttl=120, namespace="monitoring")

        except Exception as e:
            logger.error(f"Performance monitoring error: {e}", exc_info=e)

        # Wait for next interval
        await asyncio.sleep(interval_seconds)


# ==================== API ENDPOINTS (Usage Example) ====================

"""
Add these endpoints to your FastAPI app:

from fastapi import APIRouter
from core.performance_monitor import (
    get_performance_metrics,
    SystemMetrics
)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

@router.get("/performance/endpoints")
async def get_endpoint_performance():
    \"\"\"Get endpoint performance statistics\"\"\"
    metrics = get_performance_metrics()
    return {
        "all_stats": metrics.get_all_stats(),
        "top_by_count": metrics.get_top_endpoints(limit=10, sort_by='count'),
        "top_by_time": metrics.get_top_endpoints(limit=10, sort_by='avg_time'),
        "slow_requests": metrics.get_slow_requests(limit=20)
    }

@router.get("/performance/system")
async def get_system_performance():
    \"\"\"Get system resource metrics\"\"\"
    return SystemMetrics.get_all_metrics()

@router.post("/performance/reset")
async def reset_performance_metrics():
    \"\"\"Reset performance metrics\"\"\"
    metrics = get_performance_metrics()
    metrics.reset()
    return {"message": "Performance metrics reset"}
"""


# Global alias for backward compatibility - used by api/monitoring.py
performance_monitor = _metrics
