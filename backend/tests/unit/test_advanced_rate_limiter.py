"""
Unit Tests for Advanced Rate Limiter
Sprint 7: Test Coverage

Tests for Redis-based distributed rate limiting system.
"""

import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.advanced_rate_limiter import (
    _LOGIN_RPM,
    AdvancedRateLimiter,
    RateLimitExceeded,
    UserTier,
    get_rate_limiter,
    resolve_user_tier_for_rate_limit,
)
from models.enums_db import UserRole


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = AsyncMock()
    redis_mock.pipeline = Mock(return_value=AsyncMock())
    redis_mock.zrange = AsyncMock(return_value=[])
    redis_mock.zremrangebyscore = AsyncMock()
    redis_mock.zcard = AsyncMock(return_value=0)
    redis_mock.zadd = AsyncMock()
    redis_mock.expire = AsyncMock()
    redis_mock.delete = AsyncMock()
    return redis_mock


@pytest.fixture
def rate_limiter(mock_redis):
    """Create rate limiter instance with mocked Redis"""
    limiter = AdvancedRateLimiter("redis://localhost:6379/0")
    limiter.redis_client = mock_redis
    return limiter


class TestAdvancedRateLimiter:
    """Test suite for AdvancedRateLimiter"""

    def test_initialization(self):
        """Test rate limiter initialization"""
        limiter = AdvancedRateLimiter("redis://localhost:6379/0")

        assert limiter.redis_url == "redis://localhost:6379/0"
        assert limiter.redis_client is None

        # Check tier limits
        assert UserTier.FREE in limiter.tier_limits
        assert UserTier.PREMIUM in limiter.tier_limits
        assert UserTier.ADMIN in limiter.tier_limits

        # Check FREE tier limits
        assert limiter.tier_limits[UserTier.FREE]["default"] == 60
        assert limiter.tier_limits[UserTier.FREE]["auth"] == 10
        assert limiter.tier_limits[UserTier.FREE]["export"] == 2
        assert limiter.tier_limits[UserTier.FREE]["ai"] == 20

        # Check PREMIUM tier limits
        assert limiter.tier_limits[UserTier.PREMIUM]["default"] == 300
        assert limiter.tier_limits[UserTier.PREMIUM]["ai"] == 100

        # Check ADMIN tier limits
        assert limiter.tier_limits[UserTier.ADMIN]["default"] == 10000

    def test_tier_enum(self):
        """Test UserTier enum values"""
        assert UserTier.FREE.value == "free"
        assert UserTier.PREMIUM.value == "premium"
        assert UserTier.ADMIN.value == "admin"

    def test_resolve_user_tier_enum_admin_and_super_admin(self):
        assert resolve_user_tier_for_rate_limit(UserRole.ADMIN) == UserTier.ADMIN
        assert resolve_user_tier_for_rate_limit(UserRole.SUPER_ADMIN) == UserTier.ADMIN

    def test_resolve_user_tier_string_variants(self):
        assert resolve_user_tier_for_rate_limit("super_admin") == UserTier.ADMIN
        assert resolve_user_tier_for_rate_limit("superadmin") == UserTier.ADMIN

    def test_resolve_user_tier_teacher_premium(self):
        assert resolve_user_tier_for_rate_limit(UserRole.TEACHER) == UserTier.PREMIUM
        assert resolve_user_tier_for_rate_limit("teacher") == UserTier.PREMIUM

    def test_get_rate_limit_key(self, rate_limiter):
        """Test Redis key generation"""
        key = rate_limiter._get_rate_limit_key(
            identifier="user-123", endpoint="/api/v1/test", tier=UserTier.FREE
        )

        assert key == "ratelimit:free:/api/v1/test:user-123"

        # Test with different tier
        key2 = rate_limiter._get_rate_limit_key(
            identifier="192.168.1.1",
            endpoint="/api/v1/auth/login",
            tier=UserTier.PREMIUM,
        )

        assert key2 == "ratelimit:premium:/api/v1/auth/login:192.168.1.1"

    def test_categorize_endpoint(self, rate_limiter):
        """Test endpoint categorization"""
        # Auth endpoints
        assert rate_limiter._categorize_endpoint("/api/v1/auth/login") == "auth"
        assert rate_limiter._categorize_endpoint("/api/v1/auth/register") == "auth"

        # Export endpoints
        assert (
            rate_limiter._categorize_endpoint("/api/v1/kvkk/privacy/export") == "export"
        )
        assert rate_limiter._categorize_endpoint("/api/v1/data/delete") == "export"

        # AI endpoints
        assert rate_limiter._categorize_endpoint("/api/v1/ai/chat") == "ai"
        assert rate_limiter._categorize_endpoint("/api/v1/chat/assistant") == "ai"

        # Default
        assert rate_limiter._categorize_endpoint("/api/v1/users/profile") == "default"
        assert rate_limiter._categorize_endpoint("/api/v1/exams/list") == "default"

    def test_get_tier_limit(self, rate_limiter):
        """Test tier limit retrieval"""
        # FREE tier
        assert rate_limiter._get_tier_limit(UserTier.FREE, "default") == 60
        assert rate_limiter._get_tier_limit(UserTier.FREE, "auth") == 10
        assert rate_limiter._get_tier_limit(UserTier.FREE, "export") == 2
        assert rate_limiter._get_tier_limit(UserTier.FREE, "ai") == 20

        # PREMIUM tier
        assert rate_limiter._get_tier_limit(UserTier.PREMIUM, "default") == 300
        assert rate_limiter._get_tier_limit(UserTier.PREMIUM, "auth") == 30
        assert rate_limiter._get_tier_limit(UserTier.PREMIUM, "ai") == 100

        # ADMIN tier
        assert rate_limiter._get_tier_limit(UserTier.ADMIN, "default") == 10000

        # Non-existent category should return default
        assert rate_limiter._get_tier_limit(UserTier.FREE, "nonexistent") == 60

    def test_endpoint_specific_limits(self, rate_limiter):
        """Test endpoint-specific limit configuration"""
        assert "/api/v1/auth/login" in rate_limiter.endpoint_limits
        # OLCUM (6 Eyl 2026): burada sabit `== 5` yaziyordu ve BAYATTI. Uretim
        # politikasi `_LOGIN_RPM` (env: LOGIN_RATE_LIMIT_PER_MINUTE, varsayilan
        # 300) ve bu deger OLCUME dayali, gerekceli bir karar --
        # core/advanced_rate_limiter.py'deki S229 notu: 300 -> 5 degisikligi
        # gerekcesiz yapilmis, paylasimli NAT arkasindaki ogrencileri 429'a
        # dusurmus (Golden Flow'da 15 test), sonra politikaya geri donulmustu.
        # Ustelik `tests/fast/test_rate_limit_tutarliligi.py` civisi
        # `limit >= 30` sart kosuyor -- yani eski `== 5` beklentisi o civiyle
        # ayni anda GECEMEZDI. Bu celiski fark edilmemisti cunku pytest'in `-x`
        # bayragi suite'i daha erken durduruyordu (bkz. SS10.54).
        # Sabiti tekrarlamak yerine politikaya BAGLANIYORUZ: politika degisirse
        # test kendiliginden dogru kalir, sessizce bayatlamaz.
        assert rate_limiter.endpoint_limits["/api/v1/auth/login"]["limit"] == _LOGIN_RPM
        assert rate_limiter.endpoint_limits["/api/v1/auth/login"]["window"] == 60

        assert "/api/v1/kvkk/privacy/export" in rate_limiter.endpoint_limits
        assert rate_limiter.endpoint_limits["/api/v1/kvkk/privacy/export"]["limit"] == 2
        assert (
            rate_limiter.endpoint_limits["/api/v1/kvkk/privacy/export"]["window"]
            == 3600
        )

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test Redis connection"""
        with patch(
            "core.advanced_rate_limiter.redis.from_url", new_callable=AsyncMock
        ) as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis

            limiter = AdvancedRateLimiter("redis://localhost:6379/0")
            await limiter.connect()

            mock_from_url.assert_called_once_with(
                "redis://localhost:6379/0", encoding="utf-8", decode_responses=True
            )
            assert limiter.redis_client == mock_redis

    @pytest.mark.asyncio
    async def test_disconnect(self, rate_limiter, mock_redis):
        """Test Redis disconnection"""
        await rate_limiter.disconnect()
        mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, rate_limiter, mock_redis):
        """Test rate limit check when under limit"""
        # Setup mock pipeline
        pipeline_mock = AsyncMock()
        pipeline_mock.execute = AsyncMock(
            return_value=[None, 5, None, None]
        )  # 5 current requests
        mock_redis.pipeline.return_value = pipeline_mock

        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user-123", endpoint="/api/v1/test", tier=UserTier.FREE
        )

        assert allowed is True
        assert info["limit"] == 60
        assert info["remaining"] == 54  # 60 - 5 - 1
        assert "reset" in info
        assert info["retry_after"] == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, rate_limiter, mock_redis):
        """Test rate limit check when limit exceeded"""
        # Setup mock pipeline - 60 requests (at limit)
        pipeline_mock = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[None, 60, None, None])
        mock_redis.pipeline.return_value = pipeline_mock

        # Mock zrange for retry_after calculation
        now = time.time()
        mock_redis.zrange = AsyncMock(return_value=[("req", now - 50)])

        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user-123", endpoint="/api/v1/test", tier=UserTier.FREE
        )

        assert allowed is False
        assert info["limit"] == 60
        assert info["remaining"] == 0
        assert info["retry_after"] > 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_endpoint_specific(self, rate_limiter, mock_redis):
        """Test endpoint-specific limit overrides tier limit"""
        pipeline_mock = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[None, 2, None, None])
        mock_redis.pipeline.return_value = pipeline_mock

        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user-123",
            endpoint="/api/v1/auth/login",  # endpoint'e ozel limit: _LOGIN_RPM
            tier=UserTier.FREE,
        )

        assert allowed is True
        # Ayni bayatlik (bkz. yukaridaki test): sabit 5 yerine politikaya bagli.
        # Bu ikinci yer ilkini duzeltene kadar GORUNMUYORDU -- pytest `-x` ile
        # ilk hatada duruyordu, yani tek bir bayat assert arkasindaki borcu da
        # gizliyordu.
        assert info["limit"] == _LOGIN_RPM  # Endpoint-specific, not tier-based (60)
        assert info["window"] == 60

    @pytest.mark.asyncio
    async def test_check_rate_limit_premium_tier(self, rate_limiter, mock_redis):
        """Test PREMIUM tier has higher limits"""
        pipeline_mock = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[None, 100, None, None])
        mock_redis.pipeline.return_value = pipeline_mock

        # FREE tier would be blocked (60 limit)
        allowed_free, info_free = await rate_limiter.check_rate_limit(
            identifier="user-free", endpoint="/api/v1/test", tier=UserTier.FREE
        )

        assert allowed_free is False  # 100 > 60

        # PREMIUM tier should be allowed (300 limit)
        allowed_premium, info_premium = await rate_limiter.check_rate_limit(
            identifier="user-premium", endpoint="/api/v1/test", tier=UserTier.PREMIUM
        )

        assert allowed_premium is True  # 100 < 300
        assert info_premium["limit"] == 300

    @pytest.mark.asyncio
    async def test_reset_rate_limit(self, rate_limiter, mock_redis):
        """Test rate limit reset"""
        await rate_limiter.reset_rate_limit(
            identifier="user-123", endpoint="/api/v1/test", tier=UserTier.FREE
        )

        expected_key = "ratelimit:free:/api/v1/test:user-123"
        mock_redis.delete.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_get_rate_limit_info(self, rate_limiter, mock_redis):
        """Test getting rate limit info without consuming"""
        mock_redis.zcard = AsyncMock(return_value=45)

        info = await rate_limiter.get_rate_limit_info(
            identifier="user-123", endpoint="/api/v1/test", tier=UserTier.FREE
        )

        assert info["limit"] == 60
        assert info["remaining"] == 15  # 60 - 45
        assert "reset" in info
        assert info["window"] == 60

    def test_rate_limit_exceeded_exception(self):
        """Test RateLimitExceeded exception"""
        exc = RateLimitExceeded(retry_after=15, limit=60, window=60)

        assert exc.status_code == 429
        assert exc.detail["error"] == "rate_limit_exceeded"
        assert exc.detail["retry_after"] == 15
        assert exc.detail["limit"] == 60
        assert exc.headers["Retry-After"] == "15"
        assert exc.headers["X-RateLimit-Limit"] == "60"

    def test_get_rate_limiter_singleton(self):
        """Test global rate limiter instance"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        # Should return same instance
        assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_sliding_window_algorithm(self, rate_limiter, mock_redis):
        """Test sliding window algorithm behavior"""
        # Create a pipeline mock to capture calls
        pipeline_instance = AsyncMock()
        pipeline_instance.execute = AsyncMock(return_value=[None, 5, None, None])
        pipeline_instance.zremrangebyscore = Mock()
        pipeline_instance.zcard = Mock()
        pipeline_instance.zadd = Mock()
        pipeline_instance.expire = Mock()

        mock_redis.pipeline.return_value = pipeline_instance

        await rate_limiter.check_rate_limit(
            identifier="user-123", endpoint="/api/v1/test", tier=UserTier.FREE
        )

        # Verify Redis commands were called on the pipeline
        assert pipeline_instance.zremrangebyscore.called
        assert pipeline_instance.zcard.called
        assert pipeline_instance.zadd.called
        assert pipeline_instance.expire.called

    @pytest.mark.asyncio
    async def test_ai_endpoint_category_limits(self, rate_limiter, mock_redis):
        """Test AI endpoints have specific category limits"""
        pipeline_mock = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[None, 19, None, None])
        mock_redis.pipeline.return_value = pipeline_mock

        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user-123", endpoint="/api/v1/ai/chat", tier=UserTier.FREE
        )

        # Endpoint-specific limit for /api/v1/ai/chat is 20
        assert info["limit"] == 20
        assert info["remaining"] == 0  # 20 - 19 - 1 = 0

    @pytest.mark.asyncio
    async def test_export_endpoint_hourly_limit(self, rate_limiter, mock_redis):
        """Test export endpoint has hourly limit (not per minute)"""
        pipeline_mock = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[None, 1, None, None])
        mock_redis.pipeline.return_value = pipeline_mock

        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user-123",
            endpoint="/api/v1/kvkk/privacy/export",
            tier=UserTier.FREE,
        )

        assert allowed is True
        assert info["limit"] == 2  # 2 per hour
        assert info["window"] == 3600  # 1 hour in seconds
        assert info["remaining"] == 0  # 2 - 1 - 1 = 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
