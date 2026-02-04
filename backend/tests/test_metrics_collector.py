"""
Test suite for MetricsCollector
Tests Prometheus integration and metrics tracking
"""

import pytest
import time
from core.metrics_collector import (
    MetricsCollector,
    get_metrics_collector,
    reset_metrics_collector,
    MetricSnapshot,
)


class TestMetricsCollector:
    """MetricsCollector test suite"""

    def setup_method(self):
        """Her test öncesi yeni collector oluştur"""
        self.collector = MetricsCollector()

    def test_initialization(self):
        """MetricsCollector başlatma testi"""
        assert self.collector is not None
        assert self.collector.registry is not None
        assert self.collector.get_cache_hit_rate() == 0.0
        assert self.collector.get_avg_response_time() == 0.0

    def test_start_end_request_success(self):
        """Başarılı istek tracking testi"""
        request_id = "test-request-1"

        # Start request
        self.collector.start_request(request_id)

        # Simulate some work
        time.sleep(0.1)

        # End request
        self.collector.end_request(request_id=request_id, success=True, cache_hit=False)

        # Verify metrics
        snapshot = self.collector.get_snapshot()
        assert snapshot.total_requests == 1
        assert snapshot.successful_requests == 1
        assert snapshot.failed_requests == 0
        assert snapshot.avg_response_time > 0.0

    def test_start_end_request_with_cache_hit(self):
        """Cache hit ile istek tracking testi"""
        request_id = "test-request-2"

        self.collector.start_request(request_id)
        time.sleep(0.05)
        self.collector.end_request(request_id=request_id, success=True, cache_hit=True)

        # Verify cache metrics
        assert self.collector.get_cache_hit_rate() == 1.0
        snapshot = self.collector.get_snapshot()
        assert snapshot.cache_hits == 1
        assert snapshot.cache_misses == 0
        assert snapshot.cache_hit_rate == 1.0

    def test_start_end_request_with_cache_miss(self):
        """Cache miss ile istek tracking testi"""
        request_id = "test-request-3"

        self.collector.start_request(request_id)
        time.sleep(0.05)
        self.collector.end_request(request_id=request_id, success=True, cache_hit=False)

        # Verify cache metrics
        assert self.collector.get_cache_hit_rate() == 0.0
        snapshot = self.collector.get_snapshot()
        assert snapshot.cache_hits == 0
        assert snapshot.cache_misses == 1
        assert snapshot.cache_hit_rate == 0.0

    def test_mixed_cache_hits_and_misses(self):
        """Karışık cache hit/miss testi"""
        # 3 cache hit, 2 cache miss
        for i in range(5):
            request_id = f"test-request-{i}"
            self.collector.start_request(request_id)
            cache_hit = i < 3  # İlk 3 hit, son 2 miss
            self.collector.end_request(
                request_id=request_id, success=True, cache_hit=cache_hit
            )

        # Verify
        snapshot = self.collector.get_snapshot()
        assert snapshot.cache_hits == 3
        assert snapshot.cache_misses == 2
        assert snapshot.cache_hit_rate == 0.6  # 3/5

    def test_record_error(self):
        """Hata kaydı testi"""
        request_id = "test-request-error"

        self.collector.start_request(request_id)
        self.collector.record_error(request_id=request_id, error_type="TimeoutError")
        self.collector.end_request(
            request_id=request_id, success=False, cache_hit=False
        )

        # Verify error metrics
        snapshot = self.collector.get_snapshot()
        assert snapshot.failed_requests == 1
        assert snapshot.error_rate == 1.0  # 1 error / 1 total

    def test_response_time_percentiles(self):
        """Response time percentile testi"""
        # Simulate 100 requests with varying response times
        for i in range(100):
            request_id = f"test-request-{i}"
            self.collector.start_request(request_id)

            # Simulate varying response times (0.01s to 0.1s)
            time.sleep(0.001 * (i % 10 + 1))

            self.collector.end_request(
                request_id=request_id, success=True, cache_hit=False
            )

        # Get percentiles
        percentiles = self.collector.get_response_time_percentiles()

        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
        assert percentiles["p50"] > 0.0
        assert percentiles["p95"] >= percentiles["p50"]
        assert percentiles["p99"] >= percentiles["p95"]

    def test_youtube_api_quota_tracking(self):
        """YouTube API quota tracking testi"""
        # Record some API calls
        self.collector.record_youtube_api_call(quota_cost=1)
        self.collector.record_youtube_api_call(quota_cost=5)
        self.collector.record_youtube_api_call(quota_cost=10)

        # Verify quota
        snapshot = self.collector.get_snapshot()
        assert snapshot.youtube_api_quota_used == 16  # 1 + 5 + 10

    def test_youtube_quota_reset(self):
        """YouTube quota reset testi"""
        # Use some quota
        self.collector.record_youtube_api_call(quota_cost=100)
        assert self.collector.get_snapshot().youtube_api_quota_used == 100

        # Reset
        self.collector.reset_youtube_quota()
        assert self.collector.get_snapshot().youtube_api_quota_used == 0

    def test_cache_operations(self):
        """Cache operation tracking testi"""
        self.collector.record_cache_operation("get")
        self.collector.record_cache_operation("set")
        self.collector.record_cache_operation("delete")

        # Verify (Prometheus counter'lar increment edildi)
        # Bu test sadece hata olmadığını doğrular
        assert True

    def test_cache_size_update(self):
        """Cache size update testi"""
        self.collector.update_cache_size(100)
        self.collector.update_cache_size(150)
        self.collector.update_cache_size(200)

        # Verify (Prometheus gauge güncellendi)
        assert True

    def test_get_snapshot(self):
        """Snapshot alma testi"""
        # Simulate some activity
        for i in range(10):
            request_id = f"test-request-{i}"
            self.collector.start_request(request_id)
            time.sleep(0.001)
            self.collector.end_request(
                request_id=request_id,
                success=i < 8,  # 8 success, 2 error
                cache_hit=i < 5,  # 5 hit, 5 miss
            )

        # Get snapshot
        snapshot = self.collector.get_snapshot()

        # Verify snapshot
        assert isinstance(snapshot, MetricSnapshot)
        assert snapshot.total_requests == 10
        assert snapshot.successful_requests == 8
        assert snapshot.failed_requests == 2
        assert snapshot.cache_hits == 5
        assert snapshot.cache_misses == 5
        assert snapshot.cache_hit_rate == 0.5
        assert snapshot.error_rate == 0.2  # 2/10
        assert snapshot.avg_response_time > 0.0

    def test_prometheus_metrics_export(self):
        """Prometheus metrics export testi"""
        # Simulate some activity
        request_id = "test-request-prometheus"
        self.collector.start_request(request_id)
        time.sleep(0.01)
        self.collector.end_request(request_id=request_id, success=True, cache_hit=True)

        # Get Prometheus metrics
        metrics_data = self.collector.get_prometheus_metrics()

        # Verify
        assert isinstance(metrics_data, bytes)
        assert b"video_requests_total" in metrics_data
        assert b"video_response_time_seconds" in metrics_data
        assert b"cache_hit_rate" in metrics_data
        assert b"youtube_api_quota_used" in metrics_data

    def test_metrics_content_type(self):
        """Prometheus content type testi"""
        content_type = self.collector.get_metrics_content_type()
        assert "text/plain" in content_type

    def test_reset_metrics(self):
        """Metrics reset testi"""
        # Add some data
        request_id = "test-request-reset"
        self.collector.start_request(request_id)
        self.collector.end_request(request_id, success=True, cache_hit=True)
        self.collector.record_youtube_api_call(quota_cost=50)

        # Verify data exists
        snapshot_before = self.collector.get_snapshot()
        assert snapshot_before.total_requests > 0

        # Reset
        self.collector.reset_metrics()

        # Verify reset
        snapshot_after = self.collector.get_snapshot()
        assert snapshot_after.cache_hits == 0
        assert snapshot_after.cache_misses == 0
        assert snapshot_after.youtube_api_quota_used == 0
        assert snapshot_after.avg_response_time == 0.0


class TestGlobalMetricsCollector:
    """Global metrics collector singleton testi"""

    def test_get_global_collector(self):
        """Global collector alma testi"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # Same instance (singleton)
        assert collector1 is collector2

    def test_reset_global_collector(self):
        """Global collector reset testi"""
        collector = get_metrics_collector()

        # Add some data
        request_id = "test-global-request"
        collector.start_request(request_id)
        collector.end_request(request_id, success=True, cache_hit=True)

        # Reset
        reset_metrics_collector()

        # Verify reset
        snapshot = collector.get_snapshot()
        assert snapshot.cache_hits == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
