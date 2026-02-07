"""
Test Structured Logging ve Metrics Collection Integration
Task 10 verification tests
"""

import pytest
import time
from backend.core.structured_logger import (
    get_logger,
    log_api_request,
    log_api_response,
    log_error_with_context,
)
from backend.core.metrics_collector import (
    MetricsCollector,
    get_metrics_collector,
    reset_metrics_collector,
)


class TestStructuredLogger:
    """Test StructuredLogger functionality"""

    def test_logger_creation(self):
        """Test logger instance creation"""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_log_request(self):
        """Test request logging"""
        logger = get_logger("test_api")

        # Should not raise exception
        logger.log_request(
            request_id="test-123",
            endpoint="/api/youtube/recommendations",
            method="POST",
            profile={"goals": ["TYT Matematik"]},
        )

    def test_log_response(self):
        """Test response logging"""
        logger = get_logger("test_api")

        # Should not raise exception
        logger.log_response(
            request_id="test-123",
            endpoint="/api/youtube/recommendations",
            status=200,
            response_time=1234.5,
            cache_hit=True,
            video_count=15,
        )

    def test_log_error_context(self):
        """Test error logging with context"""
        logger = get_logger("test_api")

        # Should not raise exception
        logger.log_error_context(
            error_type="TestError",
            error_message="Test error message",
            context="test_context",
            request_id="test-123",
        )

    def test_logger_binding(self):
        """Test context binding"""
        logger = get_logger("test_api")

        # Bind context
        logger.bind(request_id="test-456", user_id=789)

        # Should not raise exception
        logger.info("test_event", extra_data="test")

        # Unbind
        logger.unbind("request_id")


class TestMetricsCollector:
    """Test MetricsCollector functionality"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Reset metrics before each test"""
        reset_metrics_collector()
        yield
        reset_metrics_collector()

    def test_metrics_collector_creation(self):
        """Test metrics collector instance creation"""
        collector = MetricsCollector()
        assert collector is not None

    def test_singleton_pattern(self):
        """Test global metrics collector singleton"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2

    def test_request_tracking(self):
        """Test request start/end tracking"""
        collector = MetricsCollector()

        # Start request
        collector.start_request("test-req-1")

        # Simulate some work
        time.sleep(0.1)

        # End request
        collector.end_request("test-req-1", success=True, cache_hit=False)

        # Verify metrics
        snapshot = collector.get_snapshot()
        assert snapshot.total_requests == 1
        assert snapshot.successful_requests == 1
        assert snapshot.failed_requests == 0

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation"""
        collector = MetricsCollector()

        # Simulate requests
        for i in range(10):
            collector.start_request(f"req-{i}")
            cache_hit = i < 8  # 80% cache hit
            collector.end_request(f"req-{i}", success=True, cache_hit=cache_hit)

        # Verify cache hit rate
        hit_rate = collector.get_cache_hit_rate()
        assert 0.79 <= hit_rate <= 0.81  # ~80%

    def test_response_time_percentiles(self):
        """Test response time percentile calculation"""
        collector = MetricsCollector()

        # Simulate requests with varying response times
        for i in range(100):
            collector.start_request(f"req-{i}")
            time.sleep(0.001 * (i % 10))  # 0-9ms
            collector.end_request(f"req-{i}", success=True)

        # Get percentiles
        percentiles = collector.get_response_time_percentiles()
        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
        assert percentiles["p50"] >= 0
        assert percentiles["p95"] >= percentiles["p50"]
        assert percentiles["p99"] >= percentiles["p95"]

    def test_error_recording(self):
        """Test error recording"""
        collector = MetricsCollector()

        # Record errors
        collector.record_error("req-1", "timeout")
        collector.record_error("req-2", "network")

        # End requests as failed
        collector.start_request("req-1")
        collector.end_request("req-1", success=False)

        collector.start_request("req-2")
        collector.end_request("req-2", success=False)

        # Verify error rate
        snapshot = collector.get_snapshot()
        assert snapshot.failed_requests == 2

    def test_youtube_quota_tracking(self):
        """Test YouTube API quota tracking"""
        collector = MetricsCollector()

        # Record API calls
        collector.record_youtube_api_call(quota_cost=1)
        collector.record_youtube_api_call(quota_cost=5)
        collector.record_youtube_api_call(quota_cost=10)

        # Verify quota
        snapshot = collector.get_snapshot()
        assert snapshot.youtube_api_quota_used == 16

    def test_cache_operations(self):
        """Test cache operation recording"""
        collector = MetricsCollector()

        # Record cache operations
        collector.record_cache_operation("get")
        collector.record_cache_operation("set")
        collector.record_cache_operation("delete")

        # Should not raise exception
        collector.update_cache_size(100)

    def test_prometheus_metrics_export(self):
        """Test Prometheus metrics export"""
        collector = MetricsCollector()

        # Simulate some activity
        collector.start_request("test-req")
        collector.end_request("test-req", success=True, cache_hit=True)

        # Get Prometheus metrics
        metrics_data = collector.get_prometheus_metrics()
        assert metrics_data is not None
        assert isinstance(metrics_data, bytes)

        # Verify content type
        content_type = collector.get_metrics_content_type()
        assert "text/plain" in content_type or "prometheus" in content_type.lower()


class TestIntegration:
    """Test integration between logger and metrics"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Reset metrics before each test"""
        reset_metrics_collector()
        yield
        reset_metrics_collector()

    def test_request_flow_with_logging_and_metrics(self):
        """Test complete request flow with both logging and metrics"""
        logger = get_logger("test_integration")
        collector = get_metrics_collector()

        request_id = "integration-test-123"
        endpoint = "/api/youtube/recommendations"

        # Log request start
        log_api_request(
            logger,
            method="POST",
            path=endpoint,
            request_id=request_id,
            profile={"goals": ["TYT Matematik"]},
        )

        # Start metrics tracking
        collector.start_request(request_id, endpoint)

        # Simulate processing
        time.sleep(0.05)

        # End metrics tracking
        collector.end_request(
            request_id, success=True, cache_hit=False, endpoint=endpoint
        )

        # Log response
        log_api_response(
            logger,
            method="POST",
            path=endpoint,
            status_code=200,
            duration_ms=50.0,
            request_id=request_id,
            cache_hit=False,
            video_count=15,
        )

        # Verify metrics
        snapshot = collector.get_snapshot()
        assert snapshot.total_requests == 1
        assert snapshot.successful_requests == 1
        assert snapshot.cache_misses == 1

    def test_error_flow_with_logging_and_metrics(self):
        """Test error flow with both logging and metrics"""
        logger = get_logger("test_integration")
        collector = get_metrics_collector()

        request_id = "error-test-456"
        endpoint = "/api/youtube/recommendations"

        # Start request
        collector.start_request(request_id, endpoint)

        # Simulate error
        try:
            raise ValueError("Test error")
        except Exception as e:
            # Log error
            log_error_with_context(
                logger, error=e, context="video_discovery", request_id=request_id
            )

            # Record error in metrics
            collector.record_error(request_id, "ValueError", endpoint)
            collector.end_request(request_id, success=False, endpoint=endpoint)

        # Verify metrics
        snapshot = collector.get_snapshot()
        assert snapshot.failed_requests == 1
        assert snapshot.error_rate > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
