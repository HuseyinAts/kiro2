"""
KIRO2 Unified Monitoring System
Consolidated monitoring solution combining all monitoring functionality
"""

import asyncio
import logging
import statistics
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Union

import psutil

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to collect"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    RATE = "rate"


class AlertLevel(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringCategory(Enum):
    """Monitoring categories for KIRO2 platform"""

    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    AUTH = "auth"
    EXAM = "exam"
    USER = "user"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BUSINESS = "business"


@dataclass
class MetricPoint:
    """Single metric data point"""

    timestamp: datetime
    name: str
    value: Union[int, float]
    metric_type: MetricType
    category: MonitoringCategory
    labels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System performance metrics"""

    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: list[float]
    active_connections: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class APIMetrics:
    """API performance metrics"""

    endpoint: str
    method: str
    status_code: int
    response_time: float
    request_size: int
    response_size: int
    user_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DatabaseMetrics:
    """Database performance metrics"""

    query_type: str
    execution_time: float
    rows_affected: int
    table_name: str | None = None
    query_hash: str | None = None
    connection_pool_size: int = 0
    active_connections: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """Alert definition"""

    id: str
    level: AlertLevel
    title: str
    message: str
    category: MonitoringCategory
    timestamp: datetime
    resolved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class MonitoringConfig:
    """Unified monitoring configuration"""

    def __init__(
        self,
        collection_interval: int = 60,  # seconds
        retention_hours: int = 24,
        max_metrics_memory: int = 10000,
        enable_system_monitoring: bool = True,
        enable_api_monitoring: bool = True,
        enable_db_monitoring: bool = True,
        enable_alerts: bool = True,
        # Thresholds
        cpu_threshold: float = 80.0,
        memory_threshold: float = 85.0,
        disk_threshold: float = 90.0,
        response_time_threshold: float = 5.0,  # seconds
        error_rate_threshold: float = 0.05,  # 5%
        # Export settings
        export_prometheus: bool = False,
        export_json: bool = True,
        export_elasticsearch: bool = False,
    ):
        self.collection_interval = collection_interval
        self.retention_hours = retention_hours
        self.max_metrics_memory = max_metrics_memory
        self.enable_system_monitoring = enable_system_monitoring
        self.enable_api_monitoring = enable_api_monitoring
        self.enable_db_monitoring = enable_db_monitoring
        self.enable_alerts = enable_alerts

        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.response_time_threshold = response_time_threshold
        self.error_rate_threshold = error_rate_threshold

        self.export_prometheus = export_prometheus
        self.export_json = export_json
        self.export_elasticsearch = export_elasticsearch


class MetricsAggregator:
    """Metrics aggregation and calculation"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_buffer: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )

    def add_metric(self, metric: MetricPoint):
        """Add metric to aggregation buffer"""
        key = f"{metric.category.value}:{metric.name}"
        self.metrics_buffer[key].append(metric)

    def get_statistics(
        self, category: MonitoringCategory, name: str
    ) -> dict[str, float]:
        """Get statistical summary for a metric"""
        key = f"{category.value}:{name}"
        values = [
            m.value
            for m in self.metrics_buffer[key]
            if isinstance(m.value, (int, float))
        ]

        if not values:
            return {}

        return {
            "count": len(values),
            "sum": sum(values),
            "avg": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "p50": statistics.median(values),
            "p95": statistics.quantiles(values, n=20)[18]
            if len(values) >= 20
            else max(values),
            "p99": statistics.quantiles(values, n=100)[98]
            if len(values) >= 100
            else max(values),
        }

    def get_rate(
        self, category: MonitoringCategory, name: str, window_minutes: int = 5
    ) -> float:
        """Calculate rate per minute"""
        key = f"{category.value}:{name}"
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_metrics = [
            m for m in self.metrics_buffer[key] if m.timestamp >= cutoff_time
        ]

        if len(recent_metrics) < 2:
            return 0.0

        time_span = (
            recent_metrics[-1].timestamp - recent_metrics[0].timestamp
        ).total_seconds() / 60
        return len(recent_metrics) / time_span if time_span > 0 else 0.0


class AlertManager:
    """Alert management and notification"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.alerts: list[Alert] = []
        self.alert_rules: list[Callable] = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default alert rules"""
        if not self.config.enable_alerts:
            return

        # System alerts
        self.alert_rules.extend(
            [
                lambda metrics: self._check_cpu_usage(metrics),
                lambda metrics: self._check_memory_usage(metrics),
                lambda metrics: self._check_disk_usage(metrics),
                lambda metrics: self._check_response_time(metrics),
                lambda metrics: self._check_error_rate(metrics),
            ]
        )

    def _check_cpu_usage(self, metrics: list[MetricPoint]) -> Alert | None:
        """Check CPU usage threshold"""
        cpu_metrics = [
            m
            for m in metrics
            if m.name == "cpu_percent" and m.category == MonitoringCategory.SYSTEM
        ]
        if not cpu_metrics:
            return None

        latest = cpu_metrics[-1]
        if latest.value > self.config.cpu_threshold:
            return Alert(
                id=f"cpu_high_{int(time.time())}",
                level=AlertLevel.WARNING if latest.value < 90 else AlertLevel.CRITICAL,
                title="High CPU Usage",
                message=f"CPU usage is {latest.value:.1f}% (threshold: {self.config.cpu_threshold}%)",
                category=MonitoringCategory.SYSTEM,
                timestamp=latest.timestamp,
                metadata={
                    "cpu_percent": latest.value,
                    "threshold": self.config.cpu_threshold,
                },
            )
        return None

    def _check_memory_usage(self, metrics: list[MetricPoint]) -> Alert | None:
        """Check memory usage threshold"""
        memory_metrics = [
            m
            for m in metrics
            if m.name == "memory_percent" and m.category == MonitoringCategory.SYSTEM
        ]
        if not memory_metrics:
            return None

        latest = memory_metrics[-1]
        if latest.value > self.config.memory_threshold:
            return Alert(
                id=f"memory_high_{int(time.time())}",
                level=AlertLevel.WARNING if latest.value < 95 else AlertLevel.CRITICAL,
                title="High Memory Usage",
                message=f"Memory usage is {latest.value:.1f}% (threshold: {self.config.memory_threshold}%)",
                category=MonitoringCategory.SYSTEM,
                timestamp=latest.timestamp,
                metadata={
                    "memory_percent": latest.value,
                    "threshold": self.config.memory_threshold,
                },
            )
        return None

    def _check_disk_usage(self, metrics: list[MetricPoint]) -> Alert | None:
        """Check disk usage threshold"""
        disk_metrics = [
            m
            for m in metrics
            if m.name == "disk_percent" and m.category == MonitoringCategory.SYSTEM
        ]
        if not disk_metrics:
            return None

        latest = disk_metrics[-1]
        if latest.value > self.config.disk_threshold:
            return Alert(
                id=f"disk_high_{int(time.time())}",
                level=AlertLevel.CRITICAL,
                title="High Disk Usage",
                message=f"Disk usage is {latest.value:.1f}% (threshold: {self.config.disk_threshold}%)",
                category=MonitoringCategory.SYSTEM,
                timestamp=latest.timestamp,
                metadata={
                    "disk_percent": latest.value,
                    "threshold": self.config.disk_threshold,
                },
            )
        return None

    def _check_response_time(self, metrics: list[MetricPoint]) -> Alert | None:
        """Check API response time threshold"""
        api_metrics = [
            m
            for m in metrics
            if m.name == "response_time" and m.category == MonitoringCategory.API
        ]
        if not api_metrics:
            return None

        # Check average response time in last 5 minutes
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_metrics = [m for m in api_metrics if m.timestamp >= cutoff_time]

        if recent_metrics:
            avg_response_time = statistics.mean([m.value for m in recent_metrics])
            if avg_response_time > self.config.response_time_threshold:
                return Alert(
                    id=f"response_time_high_{int(time.time())}",
                    level=AlertLevel.WARNING,
                    title="High API Response Time",
                    message=f"Average response time is {avg_response_time:.2f}s (threshold: {self.config.response_time_threshold}s)",
                    category=MonitoringCategory.API,
                    timestamp=datetime.now(),
                    metadata={
                        "avg_response_time": avg_response_time,
                        "threshold": self.config.response_time_threshold,
                    },
                )
        return None

    def _check_error_rate(self, metrics: list[MetricPoint]) -> Alert | None:
        """Check API error rate threshold"""
        api_metrics = [
            m
            for m in metrics
            if m.name == "status_code" and m.category == MonitoringCategory.API
        ]
        if not api_metrics:
            return None

        # Check error rate in last 5 minutes
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_metrics = [m for m in api_metrics if m.timestamp >= cutoff_time]

        if len(recent_metrics) >= 10:  # Need minimum requests
            error_count = len([m for m in recent_metrics if m.value >= 400])
            error_rate = error_count / len(recent_metrics)

            if error_rate > self.config.error_rate_threshold:
                return Alert(
                    id=f"error_rate_high_{int(time.time())}",
                    level=AlertLevel.ERROR,
                    title="High API Error Rate",
                    message=f"Error rate is {error_rate:.1%} (threshold: {self.config.error_rate_threshold:.1%})",
                    category=MonitoringCategory.API,
                    timestamp=datetime.now(),
                    metadata={
                        "error_rate": error_rate,
                        "threshold": self.config.error_rate_threshold,
                    },
                )
        return None

    def check_alerts(self, metrics: list[MetricPoint]) -> list[Alert]:
        """Check all alert rules and return new alerts"""
        new_alerts = []

        for rule in self.alert_rules:
            try:
                alert = rule(metrics)
                if alert:
                    new_alerts.append(alert)
            except Exception as e:
                logger.error(f"Alert rule failed: {e}")

        # Add to alerts list
        self.alerts.extend(new_alerts)

        # Keep only recent alerts
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]

        return new_alerts


class UnifiedMonitoringManager:
    """
    Unified monitoring manager combining all monitoring functionality:
    - System metrics collection
    - API performance monitoring
    - Database monitoring
    - Alert management
    - Metrics aggregation
    - Export capabilities
    """

    def __init__(self, config: MonitoringConfig | None = None):
        self.config = config or MonitoringConfig()
        self.metrics: list[MetricPoint] = []
        self.aggregator = MetricsAggregator()
        self.alert_manager = AlertManager(self.config)
        self._collection_task: asyncio.Task | None = None
        self._last_network_stats = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize monitoring system"""
        if self._initialized:
            return

        try:
            # Start background collection if enabled
            if self.config.enable_system_monitoring:
                self._collection_task = asyncio.create_task(self._collection_loop())

            self._initialized = True
            logger.info("Unified monitoring system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize monitoring system: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown monitoring system"""
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

    def add_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType,
        category: MonitoringCategory,
        labels: dict[str, str] = None,
        metadata: dict[str, Any] = None,
    ) -> None:
        """Add a custom metric"""
        metric = MetricPoint(
            timestamp=datetime.now(),
            name=name,
            value=value,
            metric_type=metric_type,
            category=category,
            labels=labels or {},
            metadata=metadata or {},
        )

        self._store_metric(metric)

    def _store_metric(self, metric: MetricPoint) -> None:
        """Store metric and manage memory"""
        self.metrics.append(metric)
        self.aggregator.add_metric(metric)

        # Cleanup old metrics to manage memory
        if len(self.metrics) > self.config.max_metrics_memory:
            cutoff_time = datetime.now() - timedelta(hours=self.config.retention_hours)
            self.metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory
            memory = psutil.virtual_memory()

            # Disk
            disk = psutil.disk_usage("/")

            # Network
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)

            # Load average (Unix only)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                load_avg = [0.0, 0.0, 0.0]

            # Active connections
            try:
                connections = len(psutil.net_connections())
            except:
                connections = 0

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_percent=disk.percent,
                disk_free_gb=disk.free / (1024 * 1024 * 1024),
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                load_average=load_avg,
                active_connections=connections,
            )

            # Store as individual metrics
            self._store_system_metrics(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise

    def _store_system_metrics(self, metrics: SystemMetrics) -> None:
        """Store system metrics as individual metric points"""
        system_metrics = [
            ("cpu_percent", metrics.cpu_percent, MetricType.GAUGE),
            ("memory_percent", metrics.memory_percent, MetricType.GAUGE),
            ("memory_used_mb", metrics.memory_used_mb, MetricType.GAUGE),
            ("disk_percent", metrics.disk_percent, MetricType.GAUGE),
            ("disk_free_gb", metrics.disk_free_gb, MetricType.GAUGE),
            ("network_sent_mb", metrics.network_sent_mb, MetricType.COUNTER),
            ("network_recv_mb", metrics.network_recv_mb, MetricType.COUNTER),
            ("active_connections", metrics.active_connections, MetricType.GAUGE),
        ]

        for name, value, metric_type in system_metrics:
            self.add_metric(name, value, metric_type, MonitoringCategory.SYSTEM)

    def record_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        request_size: int = 0,
        response_size: int = 0,
        user_id: str = None,
    ) -> None:
        """Record API call metrics"""
        if not self.config.enable_api_monitoring:
            return

        # Store individual metrics
        labels = {"endpoint": endpoint, "method": method}

        self.add_metric(
            "response_time",
            response_time,
            MetricType.HISTOGRAM,
            MonitoringCategory.API,
            labels,
        )
        self.add_metric(
            "status_code",
            status_code,
            MetricType.COUNTER,
            MonitoringCategory.API,
            labels,
        )
        self.add_metric(
            "request_size",
            request_size,
            MetricType.HISTOGRAM,
            MonitoringCategory.API,
            labels,
        )
        self.add_metric(
            "response_size",
            response_size,
            MetricType.HISTOGRAM,
            MonitoringCategory.API,
            labels,
        )

        # Create API metrics object
        api_metrics = APIMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            request_size=request_size,
            response_size=response_size,
            user_id=user_id,
        )

        # Store in metadata for detailed analysis
        self.add_metric(
            "api_call",
            1,
            MetricType.COUNTER,
            MonitoringCategory.API,
            labels,
            asdict(api_metrics),
        )

    def record_database_query(
        self,
        query_type: str,
        execution_time: float,
        rows_affected: int = 0,
        table_name: str = None,
        query_hash: str = None,
    ) -> None:
        """Record database query metrics"""
        if not self.config.enable_db_monitoring:
            return

        labels = {"query_type": query_type}
        if table_name:
            labels["table"] = table_name

        self.add_metric(
            "db_query_time",
            execution_time,
            MetricType.HISTOGRAM,
            MonitoringCategory.DATABASE,
            labels,
        )
        self.add_metric(
            "db_rows_affected",
            rows_affected,
            MetricType.HISTOGRAM,
            MonitoringCategory.DATABASE,
            labels,
        )
        self.add_metric(
            "db_query_count", 1, MetricType.COUNTER, MonitoringCategory.DATABASE, labels
        )

    async def _collection_loop(self) -> None:
        """Background metrics collection loop"""
        while True:
            try:
                await asyncio.sleep(self.config.collection_interval)

                # Collect system metrics
                if self.config.enable_system_monitoring:
                    self.collect_system_metrics()

                # Check alerts
                if self.config.enable_alerts:
                    recent_metrics = [
                        m
                        for m in self.metrics
                        if m.timestamp >= datetime.now() - timedelta(minutes=10)
                    ]
                    new_alerts = self.alert_manager.check_alerts(recent_metrics)

                    for alert in new_alerts:
                        logger.warning(f"Alert: {alert.title} - {alert.message}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

    def get_metrics_summary(
        self, category: MonitoringCategory = None, hours: int = 1
    ) -> dict[str, Any]:
        """Get metrics summary"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_metrics = [
            m
            for m in self.metrics
            if m.timestamp >= cutoff_time and (not category or m.category == category)
        ]

        summary = {
            "total_metrics": len(filtered_metrics),
            "time_range_hours": hours,
            "categories": {},
            "metrics": {},
        }

        # Group by category
        by_category = defaultdict(list)
        for metric in filtered_metrics:
            by_category[metric.category.value].append(metric)

        for cat, metrics_list in by_category.items():
            summary["categories"][cat] = len(metrics_list)

        # Group by metric name for statistics
        by_name = defaultdict(list)
        for metric in filtered_metrics:
            key = f"{metric.category.value}:{metric.name}"
            by_name[key].append(metric.value)

        for key, values in by_name.items():
            if values and all(isinstance(v, (int, float)) for v in values):
                summary["metrics"][key] = {
                    "count": len(values),
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1],
                }

        return summary

    def get_alerts(
        self, level: AlertLevel = None, resolved: bool = None
    ) -> list[Alert]:
        """Get alerts with optional filtering"""
        alerts = self.alert_manager.alerts

        if level:
            alerts = [a for a in alerts if a.level == level]

        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def health_check(self) -> dict[str, Any]:
        """Perform monitoring system health check"""
        return {
            "initialized": self._initialized,
            "config": {
                "collection_interval": self.config.collection_interval,
                "retention_hours": self.config.retention_hours,
                "system_monitoring": self.config.enable_system_monitoring,
                "api_monitoring": self.config.enable_api_monitoring,
                "db_monitoring": self.config.enable_db_monitoring,
                "alerts_enabled": self.config.enable_alerts,
            },
            "metrics": {
                "total_stored": len(self.metrics),
                "memory_usage_mb": len(self.metrics) * 0.001,  # Rough estimate
                "oldest_metric": self.metrics[0].timestamp.isoformat()
                if self.metrics
                else None,
                "newest_metric": self.metrics[-1].timestamp.isoformat()
                if self.metrics
                else None,
            },
            "alerts": {
                "total": len(self.alert_manager.alerts),
                "unresolved": len(
                    [a for a in self.alert_manager.alerts if not a.resolved]
                ),
                "critical": len(
                    [
                        a
                        for a in self.alert_manager.alerts
                        if a.level == AlertLevel.CRITICAL
                    ]
                ),
            },
            "system": self.collect_system_metrics().__dict__
            if self._initialized
            else None,
        }


# Global instance
_monitoring_manager: UnifiedMonitoringManager | None = None


def get_monitoring_manager() -> UnifiedMonitoringManager:
    """Get global monitoring manager instance"""
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = UnifiedMonitoringManager()
    return _monitoring_manager


async def initialize_monitoring():
    """Initialize monitoring system"""
    manager = get_monitoring_manager()
    await manager.initialize()


# Backward compatibility aliases
MonitoringService = UnifiedMonitoringManager
PerformanceMonitor = UnifiedMonitoringManager
MetricsCollector = UnifiedMonitoringManager
AnalyticsMonitoring = UnifiedMonitoringManager
ApplicationMetrics = UnifiedMonitoringManager
APIMonitoringMiddleware = UnifiedMonitoringManager
ProductionHealthMonitor = UnifiedMonitoringManager
PerformanceMiddleware = UnifiedMonitoringManager
PerformanceMonitoring = UnifiedMonitoringManager
