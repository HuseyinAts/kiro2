"""
Tests for YouTube Error Handlers
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import asyncio
import pytest
from unittest.mock import AsyncMock

from services.youtube_error_handlers import (
    YouTubeAPIErrorHandler,
    ValidationErrorHandler,
    TimeoutHandler,
    QuotaExceededError,
    InvalidAPIKeyError,
    RateLimitError,
    FallbackResponse,
)


class TestYouTubeAPIErrorHandler:
    """YouTubeAPIErrorHandler testleri"""

    @pytest.fixture
    def error_handler(self):
        """Error handler fixture"""
        return YouTubeAPIErrorHandler()

    @pytest.mark.asyncio
    async def test_handle_quota_exceeded_error(self, error_handler):
        """Quota exceeded hatası yönetimi testi"""
        error = QuotaExceededError()
        context = {"subject": "matematik", "topic": "türev"}

        result = await error_handler.handle_api_error(error, context)

        assert isinstance(result, FallbackResponse)
        assert result.source in ["cache", "mock"]

    @pytest.mark.asyncio
    async def test_handle_invalid_api_key_error(self, error_handler):
        """Invalid API key hatası yönetimi testi"""
        error = InvalidAPIKeyError()
        context = {"subject": "fizik"}

        result = await error_handler.handle_api_error(error, context)

        assert isinstance(result, FallbackResponse)
        assert result.source == "mock"
        assert len(result.videos) > 0

    @pytest.mark.asyncio
    async def test_handle_rate_limit_error(self, error_handler):
        """Rate limit hatası yönetimi testi"""
        error = RateLimitError()
        context = {"subject": "kimya"}

        result = await error_handler.handle_api_error(error, context)

        assert isinstance(result, FallbackResponse)
        assert result.source in ["cache", "mock"]

    @pytest.mark.asyncio
    async def test_get_mock_videos(self, error_handler):
        """Mock video alma testi"""
        context = {"subject": "matematik"}

        result = await error_handler.get_mock_videos(context)

        assert isinstance(result, FallbackResponse)
        assert result.source == "mock"
        assert len(result.videos) > 0
        # Matematik ile ilgili video olmalı
        assert any("matematik" in v.get("title", "").lower() for v in result.videos)

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self, error_handler):
        """Retry with backoff başarı testi"""
        mock_func = AsyncMock(return_value="success")

        result = await error_handler.retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_with_backoff_rate_limit(self, error_handler):
        """Retry with backoff rate limit testi"""
        # İlk 2 çağrıda rate limit, 3. çağrıda başarılı
        mock_func = AsyncMock(
            side_effect=[RateLimitError(), RateLimitError(), "success"]
        )

        result = await error_handler.retry_with_backoff(mock_func, max_retries=3)

        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_max_retries(self, error_handler):
        """Retry with backoff max retries testi"""
        mock_func = AsyncMock(side_effect=RateLimitError())

        with pytest.raises(RateLimitError):
            await error_handler.retry_with_backoff(mock_func, max_retries=2)

        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_with_backoff_non_retryable_error(self, error_handler):
        """Retry with backoff non-retryable error testi"""
        mock_func = AsyncMock(side_effect=QuotaExceededError())

        with pytest.raises(QuotaExceededError):
            await error_handler.retry_with_backoff(mock_func)

        # Quota exceeded için retry yapılmamalı
        assert mock_func.call_count == 1


class TestValidationErrorHandler:
    """ValidationErrorHandler testleri"""

    @pytest.fixture
    def error_handler(self):
        """Error handler fixture"""
        return ValidationErrorHandler()

    def test_handle_validation_failure(self, error_handler):
        """Validation failure yönetimi testi"""
        error_handler.handle_validation_failure(
            "video_123", "turkish_filter_failed", {"score": 0.5, "threshold": 0.7}
        )

        stats = error_handler.get_failure_stats()
        assert "turkish_filter_failed" in stats
        assert stats["turkish_filter_failed"] == 1

    def test_handle_multiple_validation_failures(self, error_handler):
        """Çoklu validation failure testi"""
        error_handler.handle_validation_failure("video_1", "turkish_filter_failed")
        error_handler.handle_validation_failure("video_2", "relevance_too_low")
        error_handler.handle_validation_failure("video_3", "turkish_filter_failed")

        stats = error_handler.get_failure_stats()
        assert stats["turkish_filter_failed"] == 2
        assert stats["relevance_too_low"] == 1

    def test_reset_stats(self, error_handler):
        """İstatistik sıfırlama testi"""
        error_handler.handle_validation_failure("video_1", "quality_too_low")
        error_handler.reset_stats()

        stats = error_handler.get_failure_stats()
        assert len(stats) == 0


class TestTimeoutHandler:
    """TimeoutHandler testleri"""

    @pytest.fixture
    def timeout_handler(self):
        """Timeout handler fixture"""
        return TimeoutHandler(default_timeout=1)

    @pytest.mark.asyncio
    async def test_with_timeout_success(self, timeout_handler):
        """Timeout ile başarılı işlem testi"""

        async def fast_operation():
            await asyncio.sleep(0.1)
            return "success"

        result = await timeout_handler.with_timeout(fast_operation(), timeout_seconds=2)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_timeout_timeout(self, timeout_handler):
        """Timeout durumu testi"""

        async def slow_operation():
            await asyncio.sleep(2)  # Reduced from 5s
            return "success"

        result = await timeout_handler.with_timeout(
            slow_operation(), timeout_seconds=0.5, fallback_value="fallback"
        )

        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_with_timeout_and_retry_success(self, timeout_handler):
        """Timeout ve retry ile başarı testi"""
        call_count = 0

        async def operation_with_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                await asyncio.sleep(2)  # İlk çağrıda timeout
            return "success"

        result = await timeout_handler.with_timeout_and_retry(
            operation_with_retry, timeout_seconds=0.5, max_retries=2
        )

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_with_timeout_and_retry_max_retries(self, timeout_handler):
        """Timeout ve retry max retries testi"""

        async def always_timeout():
            await asyncio.sleep(2)  # Reduced from 5s
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await timeout_handler.with_timeout_and_retry(
                always_timeout, timeout_seconds=0.2, max_retries=1
            )


class TestErrorHandlerIntegration:
    """Error handler entegrasyon testleri"""

    @pytest.mark.asyncio
    async def test_full_error_handling_flow(self):
        """Tam error handling akışı testi"""
        youtube_handler = YouTubeAPIErrorHandler()
        validation_handler = ValidationErrorHandler()
        timeout_handler = TimeoutHandler()

        # 1. YouTube API hatası simüle et
        error = QuotaExceededError()
        context = {"subject": "matematik"}

        fallback_response = await youtube_handler.handle_api_error(error, context)
        assert isinstance(fallback_response, FallbackResponse)

        # 2. Validation hatası kaydet
        validation_handler.handle_validation_failure(
            "video_1", "turkish_filter_failed", {"score": 0.5}
        )

        stats = validation_handler.get_failure_stats()
        assert "turkish_filter_failed" in stats

        # 3. Timeout ile işlem yap
        async def quick_operation():
            return "done"

        result = await timeout_handler.with_timeout(
            quick_operation(), timeout_seconds=2
        )
        assert result == "done"
