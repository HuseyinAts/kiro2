"""
Comprehensive tests for Unified Monitoring System
Target: 80%+ test coverage
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import psutil

from core.unified.monitoring_system import (
    UnifiedMonitoringManager,
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
    get_monitoring_manager,
    initialize_monitoring,
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

    def test_custom_config(self):
        """Test custom configuration values"""
        config = MonitoringConfig(
            collection_interval=30,
            retention_hours=12,
            cpu_threshold=70.0,
            memory_threshold=80.0,
            enable_alerts=False,
        )

        assert config.collection_interval == 30
        assert config.retention_hours == 12
        assert config.cpu_threshold == 70.0
        assert config.memory_threshold == 80.0
        assert config.enable_alerts is False


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


class TestAPIMetrics:
    """Test APIMetrics data class"""

    def test_api_metrics_creation(self):
        """Test APIMetrics creation"""
        timestamp = datetime.now()
        metrics = APIMetrics(
            endpoint="/api/v1/users",
            method="GET",
            status_code=200,
            response_time=0.5,
            request_size=1024,
            response_size=2048,
            user_id="user123",
            timestamp=timestamp,
        )

        assert metrics.endpoint == "/api/v1/users"
        assert metrics.method == "GET"
        assert metrics.status_code == 200
        assert metrics.response_time == 0.5
        assert metrics.user_id == "user123"
        assert metrics.timestamp == timestamp


class TestDatabaseMetrics:
    """Test DatabaseMetrics data class"""

    def test_database_metrics_creation(self):
        """Test DatabaseMetrics creation"""
        timestamp = datetime.now()
        metrics = DatabaseMetrics(
            query_type="SELECT",
            execution_time=0.1,
            rows_affected=100,
            table_name="users",
            query_hash="abc123",
            connection_pool_size=10,
            active_connections=5,
            timestamp=timestamp,
        )

        assert metrics.query_type == "SELECT"
        assert metrics.execution_time == 0.1
        assert metrics.rows_affected == 100
        assert metrics.table_name == "users"
        assert metrics.query_hash == "abc123"
        assert metrics.timestamp == timestamp


class TestAlert:
    """Test Alert data class"""

    def test_alert_creation(self):
        """Test Alert creation"""
        timestamp = datetime.now()
        alert = Alert(
            id="alert_001",
            level=AlertLevel.WARNING,
            title="High CPU Usage",
            message="CPU usage is 85%",
            category=MonitoringCategory.SYSTEM,
            timestamp=timestamp,
            resolved=False,
            metadata={"cpu_percent": 85.0},
        )

        assert alert.id == "alert_001"
        assert alert.level == AlertLevel.WARNING
        assert alert.title == "High CPU Usage"
        assert alert.message == "CPU usage is 85%"
        assert alert.category == MonitoringCategory.SYSTEM
        assert alert.resolved is False
        assert alert.metadata == {"cpu_percent": 85.0}


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

    def test_get_statistics_empty(self):
        """Test statistics with no metrics"""
        aggregator = MetricsAggregator()
        stats = aggregator.get_statistics(MonitoringCategory.SYSTEM, "cpu_percent")
        assert stats == {}

    def test_get_rate(self):
        """Test rate calculation"""
        aggregator = MetricsAggregator()
        now = datetime.now()

        # Add metrics over time
        for i in range(5):
            metric = MetricPoint(
                timestamp=now - timedelta(minutes=i),
                name="requests",
                value=1,
                metric_type=MetricType.COUNTER,
                category=MonitoringCategory.API,
            )
            aggregator.add_metric(metric)

        rate = aggregator.get_rate(
            MonitoringCategory.API, "requests", window_minutes=10
        )
        assert rate > 0  # Should have positive rate


class TestAlertManager:
    """Test AlertManager class"""

    def test_alert_manager_creation(self):
        """Test AlertManager creation"""
        config = MonitoringConfig()
        alert_manager = AlertManager(config)

        assert alert_manager.config == config
        assert len(alert_manager.alerts) == 0
        assert len(alert_manager.alert_rules) > 0  # Should have default rules

    def test_alert_manager_disabled(self):
        """Test AlertManager with alerts disabled"""
        config = MonitoringConfig(enable_alerts=False)
        alert_manager = AlertManager(config)

        assert len(alert_manager.alert_rules) == 0  # No rules when disabled

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

    def test_check_memory_alert(self):
        """Test memory usage alert"""
        config = MonitoringConfig(memory_threshold=80.0)
        alert_manager = AlertManager(config)

        # Create high memory metric
        high_memory_metric = MetricPoint(
            timestamp=datetime.now(),
            name="memory_percent",
            value=90.0,
            metric_type=MetricType.GAUGE,
            category=MonitoringCategory.SYSTEM,
        )

        alerts = alert_manager.check_alerts([high_memory_metric])

        assert len(alerts) > 0
        memory_alert = next((a for a in alerts if "Memory" in a.title), None)
        assert memory_alert is not None
        assert memory_alert.level in [AlertLevel.WARNING, AlertLevel.CRITICAL]


@pytest.mark.asyncio
class TestUnifiedMonitoringManager:
    """Test UnifiedMonitoringManager class"""

    def test_manager_creation(self):
        """Test monitoring manager creation"""
        manager = UnifiedMonitoringManager()

        assert manager.config is not None
        assert isinstance(manager.config, MonitoringConfig)
        assert manager._initialized is False
        assert len(manager.metrics) == 0

    def test_manager_with_custom_config(self):
        """Test manager with custom config"""
        config = MonitoringConfig(collection_interval=30, enable_alerts=False)
        manager = UnifiedMonitoringManager(config)

        assert manager.config == config
        assert manager.config.collection_interval == 30
        assert manager.config.enable_alerts is False

    async def test_initialize_and_shutdown(self):
        """Test manager initialization and shutdown"""
        config = MonitoringConfig(
            enable_system_monitoring=False
        )  # Disable to avoid background tasks
        manager = UnifiedMonitoringManager(config)

        await manager.initialize()
        assert manager._initialized is True

        await manager.shutdown()
        # No exception should be raised

    def test_add_metric(self):
        """Test adding custom metrics"""
        manager = UnifiedMonitoringManager()

        manager.add_metric(
            name="test_metric",
            value=100.0,
            metric_type=MetricType.GAUGE,
            category=MonitoringCategory.PERFORMANCE,
            labels={"test": "true"},
            metadata={"description": "Test metric"},
        )

        assert len(manager.metrics) == 1
        metric = manager.metrics[0]
        assert metric.name == "test_metric"
        assert metric.value == 100.0
        assert metric.metric_type == MetricType.GAUGE
        assert metric.category == MonitoringCategory.PERFORMANCE
        assert metric.labels == {"test": "true"}
        assert metric.metadata == {"description": "Test metric"}

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    @patch("psutil.net_io_counters")
    @patch("psutil.getloadavg")
    @patch("psutil.net_connections")
    def test_collect_system_metrics(
        self,
        mock_connections,
        mock_loadavg,
        mock_net_io,
        mock_disk,
        mock_memory,
        mock_cpu,
    ):
        """Test system metrics collection"""
        # Mock psutil functions
        mock_cpu.return_value = 75.0

        mock_memory_obj = MagicMock()
        mock_memory_obj.percent = 60.0
        mock_memory_obj.used = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory_obj.available = 2 * 1024 * 1024 * 1024  # 2GB
        mock_memory.return_value = mock_memory_obj

        mock_disk_obj = MagicMock()
        mock_disk_obj.percent = 50.0
        mock_disk_obj.free = 100 * 1024 * 1024 * 1024  # 100GB
        mock_disk.return_value = mock_disk_obj

        mock_net_obj = MagicMock()
        mock_net_obj.bytes_sent = 500 * 1024 * 1024  # 500MB
        mock_net_obj.bytes_recv = 300 * 1024 * 1024  # 300MB
        mock_net_io.return_value = mock_net_obj

        mock_loadavg.return_value = (1.5, 1.2, 1.0)
        mock_connections.return_value = [None] * 150  # 150 connections

        manager = UnifiedMonitoringManager()
        metrics = manager.collect_system_metrics()

        assert isinstance(metrics, SystemMetrics)
        assert metrics.cpu_percent == 75.0
        assert metrics.memory_percent == 60.0
        assert metrics.disk_percent == 50.0
        assert metrics.load_average == [1.5, 1.2, 1.0]
        assert metrics.active_connections == 150

        # Check that metrics were stored
        assert len(manager.metrics) > 0

        # Find CPU metric
        cpu_metrics = [m for m in manager.metrics if m.name == "cpu_percent"]
        assert len(cpu_metrics) > 0
        assert cpu_metrics[0].value == 75.0

    @patch("psutil.cpu_percent")
    def test_collect_system_metrics_error(self, mock_cpu):
        """Test system metrics collection with error"""
        mock_cpu.side_effect = Exception("psutil error")

        manager = UnifiedMonitoringManager()

        with pytest.raises(Exception):
            manager.collect_system_metrics()

    def test_record_api_call(self):
        """Test API call recording"""
        manager = UnifiedMonitoringManager()

        manager.record_api_call(
            endpoint="/api/v1/users",
            method="GET",
            status_code=200,
            response_time=0.5,
            request_size=1024,
            response_size=2048,
            user_id="user123",
        )

        # Should have created multiple metrics
        assert len(manager.metrics) > 0

        # Check for response_time metric
        response_time_metrics = [
            m for m in manager.metrics if m.name == "response_time"
        ]
        assert len(response_time_metrics) > 0
        assert response_time_metrics[0].value == 0.5
        assert response_time_metrics[0].category == MonitoringCategory.API

        # Check for status_code metric
        status_code_metrics = [m for m in manager.metrics if m.name == "status_code"]
        assert len(status_code_metrics) > 0
        assert status_code_metrics[0].value == 200

    def test_record_api_call_disabled(self):
        """Test API call recording when disabled"""
        config = MonitoringConfig(enable_api_monitoring=False)
        manager = UnifiedMonitoringManager(config)

        manager.record_api_call(
            endpoint="/api/v1/users", method="GET", status_code=200, response_time=0.5
        )

        # No metrics should be recorded
        assert len(manager.metrics) == 0

    def test_record_database_query(self):
        """Test database query recording"""
        manager = UnifiedMonitoringManager()

        manager.record_database_query(
            query_type="SELECT",
            execution_time=0.1,
            rows_affected=100,
            table_name="users",
            query_hash="abc123",
        )

        # Should have created multiple metrics
        assert len(manager.metrics) > 0

        # Check for query time metric
        query_time_metrics = [m for m in manager.metrics if m.name == "db_query_time"]
        assert len(query_time_metrics) > 0
        assert query_time_metrics[0].value == 0.1
        assert query_time_metrics[0].category == MonitoringCategory.DATABASE

    def test_record_database_query_disabled(self):
        """Test database query recording when disabled"""
        config = MonitoringConfig(enable_db_monitoring=False)
        manager = UnifiedMonitoringManager(config)

        manager.record_database_query(
            query_type="SELECT", execution_time=0.1, rows_affected=100
        )

        # No metrics should be recorded
        assert len(manager.metrics) == 0

    def test_get_metrics_summary(self):
        """Test metrics summary"""
        manager = UnifiedMonitoringManager()

        # Add some test metrics
        for i in range(5):
            manager.add_metric(
                name="test_metric",
                value=float(i),
                metric_type=MetricType.GAUGE,
                category=MonitoringCategory.SYSTEM,
            )

        summary = manager.get_metrics_summary(hours=1)

        assert summary["total_metrics"] == 5
        assert summary["time_range_hours"] == 1
        assert "categories" in summary
        assert "metrics" in summary
        assert summary["categories"]["system"] == 5

    def test_get_metrics_summary_filtered(self):
        """Test metrics summary with category filter"""
        manager = UnifiedMonitoringManager()

        # Add metrics for different categories
        manager.add_metric("metric1", 1.0, MetricType.GAUGE, MonitoringCategory.SYSTEM)
        manager.add_metric("metric2", 2.0, MetricType.GAUGE, MonitoringCategory.API)
        manager.add_metric("metric3", 3.0, MetricType.GAUGE, MonitoringCategory.SYSTEM)

        summary = manager.get_metrics_summary(category=MonitoringCategory.SYSTEM)

        assert summary["total_metrics"] == 2  # Only system metrics
        assert summary["categories"]["system"] == 2

    def test_memory_management(self):
        """Test memory management with max metrics limit"""
        config = MonitoringConfig(max_metrics_memory=5, retention_hours=1)
        manager = UnifiedMonitoringManager(config)

        # Add more metrics than the limit
        for i in range(10):
            manager.add_metric(
                name=f"metric_{i}",
                value=float(i),
                metric_type=MetricType.GAUGE,
                category=MonitoringCategory.SYSTEM,
            )

        # Should have triggered cleanup
        assert len(manager.metrics) <= config.max_metrics_memory

    async def test_health_check(self):
        """Test health check"""
        manager = UnifiedMonitoringManager()

        # Add some test data
        manager.add_metric("test", 1.0, MetricType.GAUGE, MonitoringCategory.SYSTEM)

        health = manager.health_check()

        assert "initialized" in health
        assert "config" in health
        assert "metrics" in health
        assert "alerts" in health
        assert health["metrics"]["total_stored"] == 1


class TestGlobalFunctions:
    """Test global functions"""

    def test_get_monitoring_manager(self):
        """Test get_monitoring_manager function"""
        manager1 = get_monitoring_manager()
        manager2 = get_monitoring_manager()

        # Should return the same instance (singleton)
        assert manager1 is manager2
        assert isinstance(manager1, UnifiedMonitoringManager)

    @pytest.mark.asyncio
    async def test_initialize_monitoring(self):
        """Test initialize_monitoring function"""
        await initialize_monitoring()

        manager = get_monitoring_manager()
        assert manager._initialized is True


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


class TestBackwardCompatibility:
    """Test backward compatibility aliases"""

    def test_aliases_exist(self):
        """Test that backward compatibility aliases exist"""
        from core.unified.monitoring_system import (
            MonitoringService,
            PerformanceMonitor,
            MetricsCollector,
            AnalyticsMonitoring,
            ApplicationMetrics,
        )

        # All aliases should point to UnifiedMonitoringManager
        assert MonitoringService == UnifiedMonitoringManager
        assert PerformanceMonitor == UnifiedMonitoringManager
        assert MetricsCollector == UnifiedMonitoringManager
        assert AnalyticsMonitoring == UnifiedMonitoringManager
        assert ApplicationMetrics == UnifiedMonitoringManager


@pytest.mark.integration
class TestMonitoringIntegration:
    """Integration tests for monitoring system"""

    @pytest.mark.asyncio
    async def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow"""
        config = MonitoringConfig(
            collection_interval=1,  # Short interval for testing
            enable_system_monitoring=False,  # Disable to control test
            enable_alerts=True,
        )
        manager = UnifiedMonitoringManager(config)

        await manager.initialize()

        try:
            # Record various metrics
            manager.record_api_call("/test", "GET", 200, 0.5)
            manager.record_database_query("SELECT", 0.1, 10)
            manager.add_metric(
                "custom_metric", 42.0, MetricType.GAUGE, MonitoringCategory.BUSINESS
            )

            # Check that metrics were recorded
            assert len(manager.metrics) > 0

            # Get summary
            summary = manager.get_metrics_summary()
            assert summary["total_metrics"] > 0

            # Health check
            health = manager.health_check()
            assert health["initialized"] is True

        finally:
            await manager.shutdown()


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=core.unified.monitoring_system",
            "--cov-report=term-missing",
        ]
    )
