"""
Tests for Video Recommendation Monitoring Service
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import pytest
import time
from services.video_recommendation_monitoring import (
    VideoRecommendationMonitor,
    FilterMetrics,
    ValidationFailure,
    PerformanceMetrics,
    ErrorMetrics,
)


def test_monitor_initialization():
    """Test monitor initialization"""
    monitor = VideoRecommendationMonitor()

    assert monitor.filter_metrics.total_videos_processed == 0
    assert monitor.performance_metrics.total_requests == 0
    assert monitor.error_metrics.total_errors == 0
    assert len(monitor.validation_failures) == 0


def test_log_video_processed():
    """Test video processing logging"""
    monitor = VideoRecommendationMonitor()

    # Log bir video
    monitor.log_video_processed(
        video_id="test123",
        video_title="Test Video",
        turkish_score=0.85,
        relevance_score=0.75,
        quality_score=0.65,
        final_score=0.75,
        passed_filters=True,
    )

    assert monitor.filter_metrics.total_videos_processed == 1
    assert monitor.filter_metrics.avg_turkish_score == 0.85
    assert monitor.filter_metrics.avg_relevance_score == 0.75
    assert monitor.filter_metrics.avg_quality_score == 0.65
    assert monitor.filter_metrics.avg_final_score == 0.75


def test_log_filter_result():
    """Test filter result logging"""
    monitor = VideoRecommendationMonitor()

    # Turkish filter - passed
    monitor.log_filter_result("turkish", passed=True, score=0.8, threshold=0.7)
    assert monitor.filter_metrics.turkish_filter_passed == 1
    assert monitor.filter_metrics.turkish_filter_failed == 0

    # Turkish filter - failed
    monitor.log_filter_result("turkish", passed=False, score=0.6, threshold=0.7)
    assert monitor.filter_metrics.turkish_filter_passed == 1
    assert monitor.filter_metrics.turkish_filter_failed == 1

    # Relevance filter
    monitor.log_filter_result("relevance", passed=True, score=0.7, threshold=0.6)
    assert monitor.filter_metrics.relevance_filter_passed == 1

    # Accessibility filter
    monitor.log_filter_result("accessibility", passed=True)
    assert monitor.filter_metrics.accessibility_filter_passed == 1

    # Quality filter
    monitor.log_filter_result("quality", passed=False, score=0.2, threshold=0.3)
    assert monitor.filter_metrics.quality_filter_failed == 1


def test_log_validation_failure():
    """Test validation failure logging"""
    monitor = VideoRecommendationMonitor()

    monitor.log_validation_failure(
        video_id="test123",
        failure_type="turkish_filter_failed",
        details={"score": 0.5, "threshold": 0.7},
        video_title="Test Video",
    )

    assert len(monitor.validation_failures) == 1
    failure = monitor.validation_failures[0]
    assert failure.video_id == "test123"
    assert failure.failure_type == "turkish_filter_failed"
    assert failure.video_title == "Test Video"


def test_log_request_lifecycle():
    """Test request lifecycle logging"""
    monitor = VideoRecommendationMonitor()

    # Start request
    start_time = monitor.log_request_start()
    assert monitor.performance_metrics.total_requests == 1

    # Simulate some processing
    time.sleep(0.1)

    # End request
    monitor.log_request_end(
        start_time=start_time, success=True, cache_hit=False, video_count=5
    )

    assert monitor.performance_metrics.successful_requests == 1
    assert monitor.performance_metrics.cache_misses == 1
    assert monitor.performance_metrics.avg_processing_time > 0


def test_log_youtube_api_calls():
    """Test YouTube API call logging"""
    monitor = VideoRecommendationMonitor()

    # Successful call
    monitor.log_youtube_api_call(success=True)
    assert monitor.performance_metrics.youtube_api_calls == 1
    assert monitor.performance_metrics.youtube_api_errors == 0

    # Failed call
    monitor.log_youtube_api_call(success=False)
    assert monitor.performance_metrics.youtube_api_calls == 2
    assert monitor.performance_metrics.youtube_api_errors == 1

    # Quota exceeded
    monitor.log_youtube_quota_exceeded()
    assert monitor.performance_metrics.youtube_quota_exceeded_count == 1

    # Rate limit
    monitor.log_youtube_rate_limit()
    assert monitor.performance_metrics.youtube_rate_limit_count == 1


def test_log_error():
    """Test error logging"""
    monitor = VideoRecommendationMonitor()

    monitor.log_error(
        error_type="ValueError",
        error_message="Invalid input",
        context={"param": "subject"},
    )

    assert monitor.error_metrics.total_errors == 1
    assert monitor.error_metrics.error_types["ValueError"] == 1
    assert len(monitor.error_metrics.recent_errors) == 1


def test_get_filter_stats():
    """Test getting filter statistics"""
    monitor = VideoRecommendationMonitor()

    # Log some filter results
    monitor.log_filter_result("turkish", passed=True, score=0.8, threshold=0.7)
    monitor.log_filter_result("turkish", passed=False, score=0.6, threshold=0.7)
    monitor.log_filter_result("relevance", passed=True, score=0.7, threshold=0.6)

    stats = monitor.get_filter_stats()

    assert stats["filters"]["turkish"]["passed"] == 1
    assert stats["filters"]["turkish"]["failed"] == 1
    assert stats["filters"]["relevance"]["passed"] == 1


def test_get_performance_stats():
    """Test getting performance statistics"""
    monitor = VideoRecommendationMonitor()

    # Log some requests
    start_time = monitor.log_request_start()
    time.sleep(0.05)
    monitor.log_request_end(start_time, success=True, cache_hit=True, video_count=5)

    start_time = monitor.log_request_start()
    time.sleep(0.05)
    monitor.log_request_end(start_time, success=False, cache_hit=False, video_count=0)

    stats = monitor.get_performance_stats()

    assert stats["requests"]["total"] == 2
    assert stats["requests"]["successful"] == 1
    assert stats["requests"]["failed"] == 1
    assert stats["cache"]["hits"] == 1
    assert stats["cache"]["misses"] == 1


def test_get_comprehensive_report():
    """Test getting comprehensive monitoring report"""
    monitor = VideoRecommendationMonitor()

    # Log some data
    monitor.log_video_processed("v1", "Video 1", 0.8, 0.7, 0.6, 0.7, True)
    monitor.log_filter_result("turkish", passed=True, score=0.8, threshold=0.7)

    start_time = monitor.log_request_start()
    time.sleep(0.05)
    monitor.log_request_end(start_time, success=True, cache_hit=False, video_count=1)

    report = monitor.get_comprehensive_report()

    assert "monitoring_info" in report
    assert "filter_stats" in report
    assert "validation_failures" in report
    assert "performance_stats" in report
    assert "error_stats" in report

    assert report["monitoring_info"]["uptime_seconds"] > 0
    assert report["filter_stats"]["total_videos_processed"] == 1
    assert report["performance_stats"]["requests"]["total"] == 1


def test_reset_metrics():
    """Test resetting all metrics"""
    monitor = VideoRecommendationMonitor()

    # Log some data
    monitor.log_video_processed("v1", "Video 1", 0.8, 0.7, 0.6, 0.7, True)
    monitor.log_filter_result("turkish", passed=True, score=0.8, threshold=0.7)
    monitor.log_error("TestError", "Test error message")

    assert monitor.filter_metrics.total_videos_processed == 1
    assert monitor.error_metrics.total_errors == 1

    # Reset
    monitor.reset_metrics()

    assert monitor.filter_metrics.total_videos_processed == 0
    assert monitor.error_metrics.total_errors == 0
    assert len(monitor.validation_failures) == 0


def test_score_distribution():
    """Test score distribution tracking"""
    monitor = VideoRecommendationMonitor()

    # Log videos with different scores
    monitor.log_video_processed("v1", "Video 1", 0.2, 0.4, 0.6, 0.4, True)
    monitor.log_video_processed("v2", "Video 2", 0.5, 0.6, 0.8, 0.6, True)
    monitor.log_video_processed("v3", "Video 3", 0.9, 0.9, 0.95, 0.9, True)

    stats = monitor.get_filter_stats()

    # Check distributions exist
    assert "0.0-0.3" in stats["score_distributions"]["turkish"]
    assert "0.5-0.7" in stats["score_distributions"]["relevance"]
    assert "0.9-1.0" in stats["score_distributions"]["quality"]


def test_timing_distribution():
    """Test request timing distribution"""
    monitor = VideoRecommendationMonitor()

    # Fast request (<1s)
    start_time = monitor.log_request_start()
    time.sleep(0.05)
    monitor.log_request_end(start_time, success=True, cache_hit=False, video_count=1)

    # Medium request (1-2s)
    start_time = monitor.log_request_start()
    time.sleep(0.05)  # Simulated
    monitor.log_request_end(start_time, success=True, cache_hit=False, video_count=1)

    stats = monitor.get_performance_stats()

    assert stats["timing"]["distribution"]["<1s"] == 2


def test_validation_failure_limit():
    """Test validation failure storage limit"""
    monitor = VideoRecommendationMonitor()
    monitor.max_validation_failures = 10

    # Log more than the limit
    for i in range(15):
        monitor.log_validation_failure(
            video_id=f"video_{i}", failure_type="test_failure", details={"index": i}
        )

    # Should only keep the last 10
    assert len(monitor.validation_failures) == 10
    assert monitor.validation_failures[0].details["index"] == 5
    assert monitor.validation_failures[-1].details["index"] == 14


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
