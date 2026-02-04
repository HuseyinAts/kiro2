"""
Tests for core/metrics_collector.py
Tests health checker and performance monitor
"""
import pytest


class TestHealthChecker:
    """Test HealthChecker class"""

    def test_health_checker_initialization(self):
        """Test HealthChecker initializes with healthy status"""
        from core.metrics_collector import HealthChecker

        checker = HealthChecker()

        assert checker.status == "healthy"

    def test_check_health_returns_dict(self):
        """Test check_health returns a dictionary"""
        from core.metrics_collector import HealthChecker

        checker = HealthChecker()
        health = checker.check_health()

        assert isinstance(health, dict)

    def test_check_health_has_status(self):
        """Test check_health includes status"""
        from core.metrics_collector import HealthChecker

        checker = HealthChecker()
        health = checker.check_health()

        assert "status" in health
        assert health["status"] == "healthy"

    def test_check_health_has_timestamp(self):
        """Test check_health includes timestamp"""
        from core.metrics_collector import HealthChecker

        checker = HealthChecker()
        health = checker.check_health()

        assert "timestamp" in health
        assert isinstance(health["timestamp"], str)


class TestPerformanceMonitor:
    """Test PerformanceMonitor class"""

    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initializes with empty metrics"""
        from core.metrics_collector import PerformanceMonitor

        monitor = PerformanceMonitor()

        assert isinstance(monitor.metrics, dict)
        assert len(monitor.metrics) == 0

    def test_record_metric(self):
        """Test recording a metric"""
        from core.metrics_collector import PerformanceMonitor

        monitor = PerformanceMonitor()
        monitor.record_metric("cpu_usage", 45.5)

        assert "cpu_usage" in monitor.metrics
        assert monitor.metrics["cpu_usage"] == 45.5

    def test_record_multiple_metrics(self):
        """Test recording multiple metrics"""
        from core.metrics_collector import PerformanceMonitor

        monitor = PerformanceMonitor()
        monitor.record_metric("cpu_usage", 45.5)
        monitor.record_metric("memory_usage", 67.8)
        monitor.record_metric("requests_count", 1234)

        assert len(monitor.metrics) == 3
        assert monitor.metrics["cpu_usage"] == 45.5
        assert monitor.metrics["memory_usage"] == 67.8
        assert monitor.metrics["requests_count"] == 1234

    def test_get_metrics_returns_dict(self):
        """Test get_metrics returns a dictionary"""
        from core.metrics_collector import PerformanceMonitor

        monitor = PerformanceMonitor()
        monitor.record_metric("test", 123)
        metrics = monitor.get_metrics()

        assert isinstance(metrics, dict)

    def test_get_metrics_returns_copy(self):
        """Test get_metrics returns a copy, not the original"""
        from core.metrics_collector import PerformanceMonitor

        monitor = PerformanceMonitor()
        monitor.record_metric("test", 123)

        metrics1 = monitor.get_metrics()
        metrics1["test"] = 999  # Modify copy

        metrics2 = monitor.get_metrics()
        assert metrics2["test"] == 123  # Original unchanged

    def test_get_metrics_empty(self):
        """Test get_metrics returns empty dict when no metrics"""
        from core.metrics_collector import PerformanceMonitor

        monitor = PerformanceMonitor()
        metrics = monitor.get_metrics()

        assert metrics == {}

    def test_update_existing_metric(self):
        """Test updating an existing metric"""
        from core.metrics_collector import PerformanceMonitor

        monitor = PerformanceMonitor()
        monitor.record_metric("counter", 10)
        monitor.record_metric("counter", 20)

        assert monitor.metrics["counter"] == 20


class TestGlobalMetrics:
    """Test global metrics instance"""

    def test_global_metrics_exists(self):
        """Test global_metrics instance exists"""
        from core.metrics_collector import global_metrics, PerformanceMonitor

        assert global_metrics is not None
        assert isinstance(global_metrics, PerformanceMonitor)

    def test_global_metrics_is_singleton(self):
        """Test global_metrics is a singleton"""
        from core.metrics_collector import global_metrics

        # Import again
        from core import metrics_collector

        assert metrics_collector.global_metrics is global_metrics
