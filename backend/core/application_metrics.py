"""
Application Metrics Module
Provides metric collection and monitoring functionality for KIRO2 platform
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Application metric types"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    
    # Custom metric types referenced across core/analytics
    API_REQUEST = "api_request"
    API_RESPONSE_TIME = "api_response_time"
    API_ERROR = "api_error"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    QUEUE_ENQUEUE = "queue_enqueue"
    QUEUE_PROCESS_SUCCESS = "queue_process_success"
    QUEUE_PROCESS_FAILURE = "queue_process_failure"
    WEBSOCKET_MESSAGE_SENT = "websocket_message_sent"
    WEBSOCKET_MESSAGE_FAILED = "websocket_message_failed"
    EXAM_STARTED = "exam_started"
    EXAM_COMPLETED = "exam_completed"
    EVENT_PUBLISHED = "event_published"
    EVENT_HANDLED = "event_handled"
    EVENT_ERROR = "event_error"



@dataclass
class MetricData:
    """Metric data structure"""

    name: str
    value: Any
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class ApplicationMetricsCollector:
    """Application metrics collector"""

    def __init__(self):
        """Initialize metrics collector"""
        self.metrics: dict[str, MetricData] = {}
        self.enabled = True

    def record_metric(
        self,
        name: str,
        value: Any,
        metric_type: MetricType = MetricType.GAUGE,
        tags: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Record a metric"""
        if not self.enabled:
            return

        metric = MetricData(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            metadata=metadata or {},
        )

        self.metrics[name] = metric
        logger.debug(f"Recorded metric: {name} = {value} ({metric_type.value})")

    def increment_counter(
        self, name: str, value: int = 1, tags: dict[str, str] | None = None
    ):
        """Increment a counter metric"""
        current = self.get_metric_value(name, 0)
        self.record_metric(name, current + value, MetricType.COUNTER, tags)

    def set_gauge(self, name: str, value: float, tags: dict[str, str] | None = None):
        """Set a gauge metric"""
        self.record_metric(name, value, MetricType.GAUGE, tags)

    def record_timer(
        self, name: str, duration_ms: float, tags: dict[str, str] | None = None
    ):
        """Record a timer metric"""
        self.record_metric(name, duration_ms, MetricType.TIMER, tags)

    def record_error(
        self, name: str, error_message: str, tags: dict[str, str] | None = None
    ):
        """Record an error metric"""
        self.increment_counter(f"{name}.errors", 1, tags)
        self.record_metric(f"{name}.last_error", error_message, MetricType.GAUGE, tags)

    def get_metric_value(self, name: str, default: Any = None) -> Any:
        """Get metric value by name"""
        if name in self.metrics:
            return self.metrics[name].value
        return default

    def get_metric(self, name: str) -> MetricData | None:
        """Get metric data by name"""
        return self.metrics.get(name)

    def get_all_metrics(self) -> dict[str, MetricData]:
        """Get all recorded metrics"""
        return self.metrics.copy()

    def clear_metrics(self):
        """Clear all recorded metrics"""
        self.metrics.clear()

    def enable(self):
        """Enable metrics collection"""
        self.enabled = True

    def disable(self):
        """Disable metrics collection"""
        self.enabled = False


# Global metrics collector instance
_global_metrics_collector = ApplicationMetricsCollector()


def get_metrics_collector() -> ApplicationMetricsCollector:
    """Get the global metrics collector instance"""
    return _global_metrics_collector


def record_application_metric(
    name: str,
    value: Any,
    metric_type: MetricType = MetricType.GAUGE,
    tags: dict[str, str] | None = None,
):
    """Convenience function to record an application metric"""
    collector = get_metrics_collector()
    collector.record_metric(name, value, metric_type, tags)


def increment_application_counter(
    name: str, value: int = 1, tags: dict[str, str] | None = None
):
    """Convenience function to increment an application counter"""
    collector = get_metrics_collector()
    collector.increment_counter(name, value, tags)


def set_application_gauge(name: str, value: float, tags: dict[str, str] | None = None):
    """Convenience function to set an application gauge"""
    collector = get_metrics_collector()
    collector.set_gauge(name, value, tags)


def record_application_timer(
    name: str, duration_ms: float, tags: dict[str, str] | None = None
):
    """Convenience function to record an application timer"""
    collector = get_metrics_collector()
    collector.record_timer(name, duration_ms, tags)
