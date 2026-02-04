"""
Unit Tests for YouTube Rate Limiting (Task 12)

Tests:
- Rate limiting on /api/youtube/recommendations endpoint
- Rate limiting on /api/youtube/search endpoint
- YouTube API quota tracking
- Rate limit headers
- Rate limit exceeded error handling

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8, 7.9

Author: AI Assistant
Date: 2025-10-30
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from services.youtube_rate_limiter import (
    YouTubeRateLimiter,
    YouTubeQuotaInfo,
    get_youtube_rate_limiter,
)


class TestYouTubeQuotaInfo:
    """Test YouTubeQuotaInfo dataclass"""

    def test_quota_info_initialization(self):
        """Test quota info initialization with defaults"""
        quota_info = YouTubeQuotaInfo()

        assert quota_info.daily_limit == 10000
        assert quota_info.used_quota == 0
        assert quota_info.remaining_quota == 10000
        assert quota_info.reset_time is not None
        assert quota_info.last_updated is not None

    def test_quota_info_custom_values(self):
        """Test quota info with custom values"""
        reset_time = datetime.now() + timedelta(hours=12)
        quota_info = YouTubeQuotaInfo(
            daily_limit=5000,
            used_quota=2000,
            remaining_quota=3000,
            reset_time=reset_time,
        )

        assert quota_info.daily_limit == 5000
        assert quota_info.used_quota == 2000
        assert quota_info.remaining_quota == 3000
        assert quota_info.reset_time == reset_time


class TestYouTubeRateLimiter:
    """Test YouTubeRateLimiter class"""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter instance"""
        return YouTubeRateLimiter()

    @pytest.mark.asyncio
    async def test_initialize_creates_new_quota(self, rate_limiter):
        """Test initialization creates new quota info"""
        with patch("services.youtube_rate_limiter.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            result = await rate_limiter.initialize()

            assert result is True
            assert rate_limiter._quota_info is not None
            assert rate_limiter._quota_info.daily_limit == 10000
            assert rate_limiter._quota_info.used_quota == 0

    @pytest.mark.asyncio
    async def test_initialize_loads_cached_quota(self, rate_limiter):
        """Test initialization loads quota from cache"""
        cached_data = {
            "daily_limit": 10000,
            "used_quota": 5000,
            "remaining_quota": 5000,
            "reset_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "last_updated": datetime.now().isoformat(),
        }

        with patch("services.youtube_rate_limiter.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=cached_data)

            result = await rate_limiter.initialize()

            assert result is True
            assert rate_limiter._quota_info.used_quota == 5000
            assert rate_limiter._quota_info.remaining_quota == 5000

    @pytest.mark.asyncio
    async def test_check_quota_available_sufficient(self, rate_limiter):
        """Test quota check when quota is sufficient"""
        rate_limiter._quota_info = YouTubeQuotaInfo(
            daily_limit=10000, used_quota=1000, remaining_quota=9000
        )

        with patch("services.youtube_rate_limiter.cache_manager"):
            is_available, message = await rate_limiter.check_quota_available("search")

            assert is_available is True
            assert message == "Quota available"

    @pytest.mark.asyncio
    async def test_check_quota_available_insufficient(self, rate_limiter):
        """Test quota check when quota is insufficient"""
        rate_limiter._quota_info = YouTubeQuotaInfo(
            daily_limit=10000, used_quota=9950, remaining_quota=50
        )

        with patch("services.youtube_rate_limiter.cache_manager"):
            is_available, message = await rate_limiter.check_quota_available("search")

            assert is_available is False
            assert "yetersiz" in message.lower()

    @pytest.mark.asyncio
    async def test_consume_quota_search_operation(self, rate_limiter):
        """Test quota consumption for search operation"""
        rate_limiter._quota_info = YouTubeQuotaInfo(
            daily_limit=10000, used_quota=0, remaining_quota=10000
        )

        with patch("services.youtube_rate_limiter.cache_manager") as mock_cache:
            mock_cache.set = AsyncMock()

            result = await rate_limiter.consume_quota("search")

            assert result is True
            assert rate_limiter._quota_info.used_quota == 100  # search costs 100
            assert rate_limiter._quota_info.remaining_quota == 9900

    @pytest.mark.asyncio
    async def test_consume_quota_custom_amount(self, rate_limiter):
        """Test quota consumption with custom amount"""
        rate_limiter._quota_info = YouTubeQuotaInfo(
            daily_limit=10000, used_quota=0, remaining_quota=10000
        )

        with patch("services.youtube_rate_limiter.cache_manager") as mock_cache:
            mock_cache.set = AsyncMock()

            result = await rate_limiter.consume_quota("search", quota_amount=200)

            assert result is True
            assert rate_limiter._quota_info.used_quota == 200
            assert rate_limiter._quota_info.remaining_quota == 9800

    @pytest.mark.asyncio
    async def test_get_quota_info(self, rate_limiter):
        """Test getting quota info"""
        rate_limiter._quota_info = YouTubeQuotaInfo(
            daily_limit=10000, used_quota=3000, remaining_quota=7000
        )

        with patch("services.youtube_rate_limiter.cache_manager"):
            quota_info = await rate_limiter.get_quota_info()

            assert quota_info.daily_limit == 10000
            assert quota_info.used_quota == 3000
            assert quota_info.remaining_quota == 7000

    @pytest.mark.asyncio
    async def test_reset_quota(self, rate_limiter):
        """Test manual quota reset"""
        rate_limiter._quota_info = YouTubeQuotaInfo(
            daily_limit=10000, used_quota=5000, remaining_quota=5000
        )

        with patch("services.youtube_rate_limiter.cache_manager") as mock_cache:
            mock_cache.set = AsyncMock()

            await rate_limiter.reset_quota()

            assert rate_limiter._quota_info.used_quota == 0
            assert rate_limiter._quota_info.remaining_quota == 10000

    @pytest.mark.asyncio
    async def test_quota_reset_on_new_day(self, rate_limiter):
        """Test automatic quota reset when reset time is reached"""
        # Set reset time to past
        past_reset_time = datetime.now() - timedelta(hours=1)
        rate_limiter._quota_info = YouTubeQuotaInfo(
            daily_limit=10000,
            used_quota=9000,
            remaining_quota=1000,
            reset_time=past_reset_time,
        )

        with patch("services.youtube_rate_limiter.cache_manager") as mock_cache:
            mock_cache.set = AsyncMock()

            await rate_limiter._check_quota_reset()

            # Quota should be reset
            assert rate_limiter._quota_info.used_quota == 0
            assert rate_limiter._quota_info.remaining_quota == 10000

    def test_should_use_cache_normal_usage(self, rate_limiter):
        """Test cache decision with normal quota usage"""
        rate_limiter._quota_info = YouTubeQuotaInfo(
            daily_limit=10000, used_quota=5000, remaining_quota=5000  # 50% usage
        )

        should_cache = rate_limiter.should_use_cache()

        # Should not force cache at 50% usage
        assert should_cache is False

    def test_should_use_cache_high_usage(self, rate_limiter):
        """Test cache decision with high quota usage"""
        rate_limiter._quota_info = YouTubeQuotaInfo(
            daily_limit=10000, used_quota=8500, remaining_quota=1500  # 85% usage
        )

        should_cache = rate_limiter.should_use_cache()

        # Should force cache at 85% usage
        assert should_cache is True

    def test_operation_costs(self):
        """Test operation cost constants"""
        assert YouTubeRateLimiter.OPERATION_COSTS["search"] == 100
        assert YouTubeRateLimiter.OPERATION_COSTS["video_details"] == 1
        assert YouTubeRateLimiter.OPERATION_COSTS["channel_details"] == 1

    def test_quota_thresholds(self):
        """Test quota threshold constants"""
        assert YouTubeRateLimiter.QUOTA_WARNING_THRESHOLD == 0.8
        assert YouTubeRateLimiter.QUOTA_CRITICAL_THRESHOLD == 0.95


class TestGetYouTubeRateLimiter:
    """Test get_youtube_rate_limiter singleton function"""

    def test_singleton_returns_same_instance(self):
        """Test that singleton returns the same instance"""
        limiter1 = get_youtube_rate_limiter()
        limiter2 = get_youtube_rate_limiter()

        assert limiter1 is limiter2

    def test_singleton_returns_rate_limiter_instance(self):
        """Test that singleton returns YouTubeRateLimiter instance"""
        limiter = get_youtube_rate_limiter()

        assert isinstance(limiter, YouTubeRateLimiter)


# Integration test (requires running backend)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limiting_integration():
    """
    Integration test for rate limiting on YouTube endpoints

    This test requires a running backend with Redis
    """
    from httpx import AsyncClient
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make multiple requests to trigger rate limit
        responses = []

        for i in range(12):  # 12 requests (limit is 10/min)
            response = await client.post(
                "/api/youtube/recommendations",
                json={
                    "goals": ["TYT Matematik"],
                    "currentLevel": {"matematik": 50},
                    "learningStyle": "visual",
                    "preferences": {},
                },
            )
            responses.append(response)

        # First 10 should succeed (or return 200/500 depending on backend state)
        # 11th and 12th should return 429 (rate limit exceeded)
        rate_limited_responses = [r for r in responses if r.status_code == 429]

        assert (
            len(rate_limited_responses) >= 2
        ), "Rate limiting should trigger after 10 requests"

        # Check rate limit headers
        if rate_limited_responses:
            response = rate_limited_responses[0]
            assert "Retry-After" in response.headers
            assert "X-RateLimit-Limit" in response.headers
