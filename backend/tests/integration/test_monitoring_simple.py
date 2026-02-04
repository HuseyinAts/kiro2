"""
Simplified tests for Monitoring System components
Target: 80%+ test coverage
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import psutil

# Import individual components to avoid bcrypt issues
from core.unified.monitoring_system import (
    MonitoringConfig,
    MetricType,
    AlertLevel,
    MonitoringCategory,
    MetricPoint,
    SystemMetrics,
    APIMetrics,
    DatabaseMetrics,
    Alert,
    MetricsAggregator,
    AlertManager,
)


class TestMonitoringConfig:
    """Test MonitoringConfig class"""

    def test_default_config(self):
        """Test default configuration values"""
        config = MonitoringConfig()

        assert config.collection_interval == 60
        assert config.retention_hours == 24
        assert config.max_metrics_memory == 10000
        assert config.enable_system_monitoring is True
        assert config.enable_api_monitoring is True
        assert config.enable_db_monitoring is True
        assert config.enable_alerts is True
        assert config.cpu_threshold == 80.0
        assert config.memory_threshold == 85.0
        assert config.disk_threshold == 90.0
        assert config.response_time_threshold == 5.0
        assert config.error_rate_threshold == 0.05


class TestMetricPoint:
    """Test MetricPoint data class"""

    def test_metric_point_creation(self):
        """Test MetricPoint creation"""
        timestamp = datetime.now()
        metric = MetricPoint(
            timestamp=timestamp,
            name="cpu_percent",
            value=75.5,
            metric_type=MetricType.GAUGE,
            category=MonitoringCategory.SYSTEM,
            labels={"host": "server1"},
            metadata={"source": "psutil"},
        )

        assert metric.timestamp == timestamp
        assert metric.name == "cpu_percent"
        assert metric.value == 75.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.category == MonitoringCategory.SYSTEM
        assert metric.labels == {"host": "server1"}
        assert metric.metadata == {"source": "psutil"}


class TestSystemMetrics:
    """Test SystemMetrics data class"""

    def test_system_metrics_creation(self):
        """Test SystemMetrics creation"""
        timestamp = datetime.now()
        metrics = SystemMetrics(
            cpu_percent=75.0,
            memory_percent=60.0,
            memory_used_mb=4096.0,
            memory_available_mb=2048.0,
            disk_percent=50.0,
            disk_free_gb=100.0,
            network_sent_mb=500.0,
            network_recv_mb=300.0,
            load_average=[1.5, 1.2, 1.0],
            active_connections=150,
            timestamp=timestamp,
        )

        assert metrics.cpu_percent == 75.0
        assert metrics.memory_percent == 60.0
        assert metrics.memory_used_mb == 4096.0
        assert metrics.timestamp == timestamp
        assert metrics.load_average == [1.5, 1.2, 1.0]


class TestMetricsAggregator:
    """Test MetricsAggregator class"""

    def test_aggregator_creation(self):
        """Test MetricsAggregator creation"""
        aggregator = MetricsAggregator(window_size=50)
        assert len(aggregator.metrics_buffer) == 0

    def test_add_metric(self):
        """Test adding metrics to aggregator"""
        aggregator = MetricsAggregator()
        metric = MetricPoint(
            timestamp=datetime.now(),
            name="cpu_percent",
            value=75.0,
            metric_type=MetricType.GAUGE,
            category=MonitoringCategory.SYSTEM,
        )

        aggregator.add_metric(metric)
        key = f"{metric.category.value}:{metric.name}"
        assert len(aggregator.metrics_buffer[key]) == 1
        assert aggregator.metrics_buffer[key][0] == metric

    def test_get_statistics(self):
        """Test statistics calculation"""
        aggregator = MetricsAggregator()

        # Add multiple metrics
        for i in range(10):
            metric = MetricPoint(
                timestamp=datetime.now(),
                name="cpu_percent",
                value=float(50 + i * 5),  # 50, 55, 60, ..., 95
                metric_type=MetricType.GAUGE,
                category=MonitoringCategory.SYSTEM,
            )
            aggregator.add_metric(metric)

        stats = aggregator.get_statistics(MonitoringCategory.SYSTEM, "cpu_percent")

        assert stats["count"] == 10
        assert stats["min"] == 50.0
        assert stats["max"] == 95.0
        assert stats["avg"] == 72.5
        assert stats["sum"] == 725.0


class TestAlertManager:
    """Test AlertManager class"""

    def test_alert_manager_creation(self):
        """Test AlertManager creation"""
        config = MonitoringConfig()
        alert_manager = AlertManager(config)

        assert alert_manager.config == config
        assert len(alert_manager.alerts) == 0
        assert len(alert_manager.alert_rules) > 0  # Should have default rules

    def test_check_cpu_alert(self):
        """Test CPU usage alert"""
        config = MonitoringConfig(cpu_threshold=80.0)
        alert_manager = AlertManager(config)

        # Create high CPU metric
        high_cpu_metric = MetricPoint(
            timestamp=datetime.now(),
            name="cpu_percent",
            value=85.0,
            metric_type=MetricType.GAUGE,
            category=MonitoringCategory.SYSTEM,
        )

        alerts = alert_manager.check_alerts([high_cpu_metric])

        assert len(alerts) > 0
        cpu_alert = next((a for a in alerts if "CPU" in a.title), None)
        assert cpu_alert is not None
        assert cpu_alert.level in [AlertLevel.WARNING, AlertLevel.CRITICAL]
        assert "85.0%" in cpu_alert.message


class TestEnums:
    """Test enumeration classes"""

    def test_metric_type_enum(self):
        """Test MetricType enum"""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"
        assert MetricType.RATE.value == "rate"

    def test_alert_level_enum(self):
        """Test AlertLevel enum"""
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.ERROR.value == "error"
        assert AlertLevel.CRITICAL.value == "critical"

    def test_monitoring_category_enum(self):
        """Test MonitoringCategory enum"""
        assert MonitoringCategory.API.value == "api"
        assert MonitoringCategory.DATABASE.value == "database"
        assert MonitoringCategory.CACHE.value == "cache"
        assert MonitoringCategory.SYSTEM.value == "system"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
