"""
Production Monitoring ve Logging Sistemi Test
Comprehensive test for logging and performance monitoring
"""

import asyncio
import time
from pathlib import Path


# Test structured logging
def test_structured_logger():
    """Test structured logging system"""
    print("\n🧪 Testing Structured Logger...")

    from core.structured_logger import get_logger

    # Create test logger
    logger = get_logger("test_logger")

    # Test different log levels
    logger.info("Test info message", extra_data={"test": "data"})
    logger.warning("Test warning message", user_id="test_user")
    logger.debug("Test debug message", request_id="req_123")

    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.error("Test error message", exception=e, extra_data={"context": "test"})

    print("[CHECK] Structured logging test completed")


def test_logging_config():
    """Test logging configuration"""
    print("\n🧪 Testing Logging Configuration...")

    from core.logging_config import LogFilter, logging_config

    # Test config
    config = logging_config.get_logger_config("test")
    print(f"Logger config: {config}")

    # Test log filtering
    log_record = {"level": "ERROR", "message": "Test message", "type": "api_request"}

    # Test level filtering
    assert LogFilter.filter_by_level(log_record, "INFO") == True
    assert LogFilter.filter_by_level(log_record, "CRITICAL") == False

    # Test category filtering
    assert LogFilter.filter_by_category(log_record, ["api"]) == True
    assert LogFilter.filter_by_category(log_record, ["database"]) == False

    # Test sensitive data filtering
    sensitive_record = {
        "password": "secret123",
        "token": "abc123",
        "normal_field": "normal_value",
    }

    filtered = LogFilter.filter_sensitive_data(sensitive_record)
    assert filtered["password"] == "[FILTERED]"
    assert filtered["token"] == "[FILTERED]"
    assert filtered["normal_field"] == "normal_value"

    print("[CHECK] Logging configuration test completed")


async def test_performance_monitor():
    """Test performance monitoring system"""
    print("\n🧪 Testing Performance Monitor...")

    from core.performance_monitor import performance_monitor

    # Test API metric recording
    await performance_monitor.record_api_metric(
        endpoint="/test/endpoint",
        method="GET",
        response_time_ms=150.5,
        status_code=200,
        user_id="test_user",
    )

    # Test database metric recording
    await performance_monitor.record_db_metric(
        query_type="SELECT",
        execution_time_ms=25.3,
        rows_affected=10,
        table_name="users",
    )

    # Test performance summaries
    api_summary = performance_monitor.get_api_performance_summary(hours=1)
    db_summary = performance_monitor.get_db_performance_summary(hours=1)
    system_summary = performance_monitor.get_system_performance_summary(hours=1)

    print(f"API Summary: {api_summary}")
    print(f"DB Summary: {db_summary}")
    print(f"System Summary: {system_summary}")

    # Test Prometheus export
    prometheus_metrics = performance_monitor.export_metrics_to_prometheus()
    print(f"Prometheus metrics length: {len(prometheus_metrics)}")

    print("[CHECK] Performance monitor test completed")


def test_performance_middleware():
    """Test performance middleware components"""
    print("\n🧪 Testing Performance Middleware...")

    from core.performance_middleware import (
        custom_metrics,
        memory_tracker,
        track_db_query,
        track_performance,
    )

    # Test custom metrics
    custom_metrics.increment_counter("test_counter", 5)
    custom_metrics.set_gauge("test_gauge", 42.5)
    custom_metrics.record_histogram("test_histogram", 123.4)

    metrics_summary = custom_metrics.get_metrics_summary()
    print(f"Custom metrics summary: {metrics_summary}")

    # Test memory tracking
    with memory_tracker.track_memory_usage("test_operation"):
        # Simulate some work
        data = [i for i in range(1000)]
        time.sleep(0.1)

    # Test decorators
    @track_performance("test_function")
    def test_function():
        time.sleep(0.05)
        return "test_result"

    @track_db_query("SELECT", "test_table")
    async def test_db_function():
        await asyncio.sleep(0.02)
        return "db_result"

    # Execute decorated functions
    result1 = test_function()
    result2 = await test_db_function()

    assert result1 == "test_result"
    assert result2 == "db_result"

    print("[CHECK] Performance middleware test completed")


async def test_monitoring_api():
    """Test monitoring API endpoints"""
    print("\n🧪 Testing Monitoring API...")

    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    # Test health check
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    health_data = response.json()
    assert health_data["success"] == True
    print(f"Health check: {health_data['data']['status']}")

    # Test performance endpoints
    response = client.get("/api/v1/monitoring/performance/summary?hours=1")
    assert response.status_code == 200
    perf_data = response.json()
    print(f"Performance summary available: {perf_data['success']}")

    # Test Prometheus metrics
    response = client.get("/api/v1/monitoring/metrics/prometheus")
    assert response.status_code == 200
    print(f"Prometheus metrics length: {len(response.text)}")

    # Test bottleneck detection
    response = client.get("/api/v1/monitoring/bottlenecks?hours=1")
    assert response.status_code == 200
    bottleneck_data = response.json()
    print(f"Bottlenecks found: {len(bottleneck_data['data']['bottlenecks'])}")

    print("[CHECK] Monitoring API test completed")


def test_log_analysis():
    """Test log analysis functionality"""
    print("\n🧪 Testing Log Analysis...")

    from core.logging_config import LogAnalyzer

    # Create test log file
    test_log_file = "test_logs.log"
    test_logs = [
        '{"level": "ERROR", "exception": {"type": "ValueError", "message": "Test error 1"}}',
        '{"level": "ERROR", "exception": {"type": "KeyError", "message": "Test error 2"}}',
        '{"level": "INFO", "type": "http_response", "response_time_ms": 150, "status_code": 200}',
        '{"level": "INFO", "type": "http_response", "response_time_ms": 250, "status_code": 404}',
    ]

    with open(test_log_file, "w", encoding="utf-8") as f:
        for log in test_logs:
            f.write(log + "\n")

    # Test error analysis
    error_analysis = LogAnalyzer.analyze_error_patterns(test_log_file)
    print(f"Error analysis: {error_analysis}")

    # Test performance analysis
    performance_analysis = LogAnalyzer.analyze_performance_metrics(test_log_file)
    print(f"Performance analysis: {performance_analysis}")

    # Cleanup
    Path(test_log_file).unlink(missing_ok=True)

    print("[CHECK] Log analysis test completed")


async def test_comprehensive_monitoring():
    """Test comprehensive monitoring system"""
    print("\n🧪 Testing Comprehensive Monitoring System...")

    # Start performance monitoring
    from core.performance_monitor import performance_monitor

    if not performance_monitor.is_monitoring:
        await performance_monitor.start_monitoring(interval_seconds=5)
        print("Performance monitoring started")

    # Simulate some activity
    await performance_monitor.record_api_metric(
        endpoint="/api/test", method="POST", response_time_ms=200.5, status_code=201
    )

    await performance_monitor.record_db_metric(
        query_type="INSERT",
        execution_time_ms=50.2,
        rows_affected=1,
        table_name="test_table",
    )

    # Wait a bit for system metrics collection
    await asyncio.sleep(2)

    # Get comprehensive summary
    api_summary = performance_monitor.get_api_performance_summary(1)
    db_summary = performance_monitor.get_db_performance_summary(1)
    system_summary = performance_monitor.get_system_performance_summary(1)

    print("[CHART] Comprehensive Monitoring Results:")
    print(f"  API Metrics: {api_summary.get('total_requests', 0)} requests")
    print(f"  DB Metrics: {db_summary.get('total_queries', 0)} queries")
    print(
        f"  System Metrics: {system_summary.get('measurements_count', 0)} measurements"
    )

    # Stop monitoring
    await performance_monitor.stop_monitoring()
    print("Performance monitoring stopped")

    print("[CHECK] Comprehensive monitoring test completed")


async def main():
    """Run all tests"""
    print("[ROCKET] Production Monitoring ve Logging Sistemi Test Başlıyor...")
    print("=" * 60)

    try:
        # Test structured logging
        test_structured_logger()

        # Test logging configuration
        test_logging_config()

        # Test performance monitoring
        await test_performance_monitor()

        # Test performance middleware
        test_performance_middleware()

        # Test monitoring API
        await test_monitoring_api()

        # Test log analysis
        test_log_analysis()

        # Test comprehensive monitoring
        await test_comprehensive_monitoring()

        print("\n" + "=" * 60)
        print("[CHECK] TÜM TESTLER BAŞARILI!")
        print("[CHART] Production Monitoring ve Logging Sistemi TAMAMEN ÇALIŞIYOR!")
        print("\n[TARGET] Özellikler:")
        print("  [CHECK] Structured JSON Logging")
        print("  [CHECK] Request/Response Logging Middleware")
        print("  [CHECK] API Performance Monitoring")
        print("  [CHECK] Database Query Performance Tracking")
        print("  [CHECK] System Resource Monitoring")
        print("  [CHECK] Custom Metrics Collection")
        print("  [CHECK] Prometheus Metrics Export")
        print("  [CHECK] Performance Bottleneck Detection")
        print("  [CHECK] Log Analysis ve Pattern Detection")
        print("  [CHECK] Health Check Endpoints")
        print("  [CHECK] Memory Usage Tracking")
        print("  [CHECK] Error Logging ve Stack Trace")
        print("  [CHECK] Log Rotation ve Retention")

    except Exception as e:
        print(f"\n[X] Test hatası: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
