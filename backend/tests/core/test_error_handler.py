"""
Tests for Error Handler and Custom Exceptions
Learning Path Video Yükleme Sorunu - Error Handling Tests

Requirements: 5.1, 5.2, 5.7, 5.8, 5.9
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from backend.core.error_handler import (
    ErrorHandler,
    ErrorCategory,
    ErrorClassification,
    VideoAPIError,
    YouTubeAPIError,
    CacheError,
    VideoDiscoveryError,
    VideoFilterError,
    VideoTimeoutError,
)
from backend.core.exceptions import (
    ErrorSeverity,
    RateLimitError,
    DatabaseError,
    ExternalServiceError,
)


class TestCustomExceptions:
    """Test custom video API exceptions"""

    def test_video_api_error_creation(self):
        """Test VideoAPIError creation with default values"""
        error = VideoAPIError("Test error")

        assert error.message == "Test error"
        assert error.error_code == "VIDEO_API_ERROR"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.user_message == "Video yükleme sırasında bir hata oluştu"
        assert error.retry_after is None

    def test_youtube_api_error_quota_exceeded(self):
        """Test YouTubeAPIError with quota exceeded"""
        error = YouTubeAPIError(
            message="Quota exceeded", status_code=429, quota_exceeded=True
        )

        assert error.error_code == "YOUTUBE_API_ERROR"
        assert error.severity == ErrorSeverity.HIGH
        assert error.details["quota_exceeded"] is True
        assert error.retry_after == 3600
        assert "kota" in error.user_message.lower()

    def test_youtube_api_error_server_error(self):
        """Test YouTubeAPIError with server error"""
        error = YouTubeAPIError(message="Server error", status_code=503)

        assert error.details["status_code"] == 503
        assert error.severity == ErrorSeverity.MEDIUM

    def test_cache_error_creation(self):
        """Test CacheError creation"""
        error = CacheError(
            message="Cache write failed", operation="write", cache_type="redis"
        )

        assert error.error_code == "CACHE_ERROR"
        assert error.severity == ErrorSeverity.LOW
        assert error.details["operation"] == "write"
        assert error.details["cache_type"] == "redis"

    def test_video_discovery_error(self):
        """Test VideoDiscoveryError creation"""
        error = VideoDiscoveryError(
            message="No videos found", subject="matematik", search_type="semantic"
        )

        assert error.error_code == "VIDEO_DISCOVERY_ERROR"
        assert error.details["subject"] == "matematik"
        assert error.details["search_type"] == "semantic"

    def test_video_timeout_error(self):
        """Test VideoTimeoutError creation"""
        error = VideoTimeoutError(
            message="Operation timeout", timeout_seconds=20.0, operation="video_search"
        )

        assert error.error_code == "VIDEO_TIMEOUT_ERROR"
        assert error.details["timeout_seconds"] == 20.0
        assert error.retry_after == 5


class TestErrorClassification:
    """Test error classification logic"""

    def setup_method(self):
        """Setup test fixtures"""
        self.handler = ErrorHandler()

    def test_classify_youtube_quota_error(self):
        """Test classification of YouTube quota exceeded error"""
        error = YouTubeAPIError(message="Quota exceeded", quota_exceeded=True)

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.QUOTA
        assert classification.severity == ErrorSeverity.CRITICAL
        assert classification.retryable is True
        assert classification.retry_after == 3600
        assert "use_cache" in classification.recovery_actions
        assert classification.log_level == "CRITICAL"

    def test_classify_youtube_rate_limit_error(self):
        """Test classification of YouTube rate limit error"""
        error = YouTubeAPIError(message="Rate limit", status_code=429)

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.RATE_LIMIT
        assert classification.severity == ErrorSeverity.HIGH
        assert classification.retryable is True
        assert classification.retry_after == 60
        assert "wait" in classification.recovery_actions

    def test_classify_youtube_server_error(self):
        """Test classification of YouTube server error"""
        error = YouTubeAPIError(message="Server error", status_code=503)

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.SERVER_ERROR
        assert classification.retryable is True
        assert "retry" in classification.recovery_actions

    def test_classify_cache_error(self):
        """Test classification of cache error"""
        error = CacheError(message="Cache unavailable", operation="read")

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.CACHE
        assert classification.severity == ErrorSeverity.LOW
        assert classification.retryable is True
        assert "skip_cache" in classification.recovery_actions

    def test_classify_timeout_error(self):
        """Test classification of timeout error"""
        error = VideoTimeoutError(message="Timeout", timeout_seconds=20.0)

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.TIMEOUT
        assert classification.retryable is True
        assert "retry" in classification.recovery_actions

    def test_classify_discovery_error(self):
        """Test classification of video discovery error"""
        error = VideoDiscoveryError(message="No videos found", subject="fizik")

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.NOT_FOUND
        assert classification.retryable is True
        assert "fallback" in classification.recovery_actions

    def test_classify_rate_limit_error(self):
        """Test classification of generic rate limit error"""
        error = RateLimitError(message="Rate limit exceeded", limit=100)
        error.details["retry_after"] = 120

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.RATE_LIMIT
        assert classification.retry_after == 120

    def test_classify_database_error(self):
        """Test classification of database error"""
        error = DatabaseError(message="Connection failed", operation="query")

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.DATABASE
        assert classification.severity == ErrorSeverity.HIGH
        assert "notify_admin" in classification.recovery_actions

    def test_classify_connection_error(self):
        """Test classification of connection error"""
        error = ConnectionError("Network unreachable")

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.NETWORK
        assert classification.retryable is True
        assert "check_network" in classification.recovery_actions

    def test_classify_unknown_error(self):
        """Test classification of unknown error"""
        error = ValueError("Unknown error")

        classification = self.handler.classify_error(error)

        assert classification.category == ErrorCategory.UNKNOWN
        assert classification.severity == ErrorSeverity.HIGH
        assert classification.retryable is False


class TestErrorHandler:
    """Test ErrorHandler functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.handler = ErrorHandler()

    def test_handle_error_with_context(self):
        """Test error handling with context"""
        error = VideoAPIError("Test error")
        context = {"user_id": "123", "subject": "matematik"}
        request_id = "req-123"

        classification = self.handler.handle_error(
            error, context=context, request_id=request_id
        )

        assert classification is not None
        # VideoAPIError without specific subtype is classified as UNKNOWN
        assert classification.category == ErrorCategory.UNKNOWN

    def test_get_user_message(self):
        """Test user-friendly message generation"""
        error = YouTubeAPIError(message="API error", quota_exceeded=True)

        user_message = self.handler.get_user_message(error)

        assert "kota" in user_message.lower()
        assert len(user_message) > 0

    def test_should_retry_retryable_error(self):
        """Test retry decision for retryable error"""
        error = VideoTimeoutError(message="Timeout", timeout_seconds=20.0)

        should_retry, retry_after = self.handler.should_retry(error)

        assert should_retry is True
        assert retry_after == 5

    def test_should_retry_non_retryable_error(self):
        """Test retry decision for non-retryable error"""
        error = ValueError("Invalid input")

        should_retry, retry_after = self.handler.should_retry(error)

        assert should_retry is False
        assert retry_after == 0

    def test_get_recovery_actions(self):
        """Test recovery actions retrieval"""
        error = CacheError(message="Cache error", operation="write")

        actions = self.handler.get_recovery_actions(error)

        assert isinstance(actions, list)
        assert len(actions) > 0
        assert "skip_cache" in actions

    def test_error_metrics_tracking(self):
        """Test error metrics collection"""
        # Handle multiple errors
        self.handler.handle_error(VideoAPIError("Error 1"))
        self.handler.handle_error(CacheError("Error 2"))
        self.handler.handle_error(VideoAPIError("Error 3"))

        metrics = self.handler.get_error_metrics()

        assert "error_counts" in metrics
        assert "total_errors" in metrics
        assert metrics["total_errors"] == 3

    def test_error_logging(self):
        """Test error logging functionality"""
        with patch.object(self.handler.logger, "error") as mock_log:
            error = YouTubeAPIError(message="Server error", status_code=500)

            self.handler.handle_error(
                error, context={"test": "context"}, request_id="req-456"
            )

            # Verify logging was called
            assert mock_log.called

    def test_high_severity_error_includes_stack_trace(self):
        """Test that high severity errors include stack trace"""
        with patch.object(self.handler.logger, "error") as mock_log:
            error = DatabaseError(message="Critical DB error", operation="write")

            self.handler.handle_error(error)

            # Verify error was logged
            assert mock_log.called


class TestErrorHandlerIntegration:
    """Integration tests for error handler"""

    def setup_method(self):
        """Setup test fixtures"""
        self.handler = ErrorHandler()

    def test_full_error_handling_flow(self):
        """Test complete error handling flow"""
        # Create error
        error = YouTubeAPIError(
            message="API quota exceeded", status_code=429, quota_exceeded=True
        )

        # Handle error
        classification = self.handler.handle_error(
            error,
            context={"subject": "matematik", "user_id": "123"},
            request_id="req-789",
        )

        # Verify classification
        assert classification.category == ErrorCategory.QUOTA
        assert classification.severity == ErrorSeverity.CRITICAL

        # Get user message
        user_message = self.handler.get_user_message(error)
        assert len(user_message) > 0

        # Check retry decision
        should_retry, retry_after = self.handler.should_retry(error)
        assert should_retry is True
        assert retry_after > 0

        # Get recovery actions
        actions = self.handler.get_recovery_actions(error)
        assert "use_cache" in actions

        # Check metrics
        metrics = self.handler.get_error_metrics()
        assert metrics["total_errors"] > 0

    def test_error_chain_handling(self):
        """Test handling of multiple related errors"""
        errors = [
            VideoTimeoutError("Timeout 1", timeout_seconds=10.0),
            VideoTimeoutError("Timeout 2", timeout_seconds=20.0),
            YouTubeAPIError("API error", status_code=503),
        ]

        for error in errors:
            self.handler.handle_error(error)

        metrics = self.handler.get_error_metrics()
        assert metrics["total_errors"] == 3

    def test_concurrent_error_handling(self):
        """Test error handling under concurrent load"""

        async def handle_error_async(error):
            return self.handler.handle_error(error)

        async def run_concurrent_tests():
            errors = [VideoAPIError(f"Error {i}") for i in range(10)]

            tasks = [handle_error_async(error) for error in errors]
            results = await asyncio.gather(*tasks)

            return results

        # Run concurrent error handling
        results = asyncio.run(run_concurrent_tests())

        assert len(results) == 10
        assert all(isinstance(r, ErrorClassification) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
