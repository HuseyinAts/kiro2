"""
Unit Tests for Rate Limit Middleware
Sprint 7: Test Coverage

Tests for FastAPI rate limiting middleware.
"""
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request, Response

from core.advanced_rate_limiter import AdvancedRateLimiter, UserTier
from core.rate_limit_middleware import RateLimitMiddleware, get_rate_limit_status


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter"""
    limiter = Mock(spec=AdvancedRateLimiter)
    limiter.check_rate_limit = AsyncMock(return_value=(True, {
        "limit": 60,
        "remaining": 45,
        "reset": 1699876543,
        "retry_after": 0,
        "window": 60
    }))
    limiter.get_rate_limit_info = AsyncMock(return_value={
        "limit": 60,
        "remaining": 45,
        "reset": 1699876543,
        "window": 60
    })
    return limiter


@pytest.fixture
def mock_request():
    """Mock FastAPI request"""
    request = Mock(spec=Request)
    request.url = Mock()
    request.url.path = "/api/v1/test"
    request.client = Mock()
    request.client.host = "192.168.1.1"
    request.state = Mock()
    request.state.user = None
    return request


@pytest.fixture
def mock_app():
    """Mock ASGI app"""
    async def app(scope, receive, send):
        pass
    return app


@pytest.fixture
def middleware(mock_app, mock_rate_limiter):
    """Create middleware instance"""
    return RateLimitMiddleware(mock_app, rate_limiter=mock_rate_limiter)


class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware"""

    def test_initialization(self, mock_app, mock_rate_limiter):
        """Test middleware initialization"""
        middleware = RateLimitMiddleware(mock_app, rate_limiter=mock_rate_limiter)

        assert middleware.rate_limiter == mock_rate_limiter
        assert "/health" in middleware.excluded_paths
        assert "/docs" in middleware.excluded_paths
        assert "/metrics" in middleware.excluded_paths

    def test_initialization_with_custom_excluded_paths(self, mock_app):
        """Test middleware with custom excluded paths"""
        custom_paths = ["/custom", "/admin/health"]
        middleware = RateLimitMiddleware(
            mock_app,
            excluded_paths=custom_paths
        )

        assert middleware.excluded_paths == custom_paths

    def test_should_rate_limit_excluded_paths(self, middleware):
        """Test that excluded paths are not rate limited"""
        assert middleware._should_rate_limit("/health") is False
        assert middleware._should_rate_limit("/api/v1/health") is False
        assert middleware._should_rate_limit("/docs") is False
        assert middleware._should_rate_limit("/redoc") is False
        assert middleware._should_rate_limit("/openapi.json") is False
        assert middleware._should_rate_limit("/metrics") is False

    def test_should_rate_limit_included_paths(self, middleware):
        """Test that normal paths are rate limited"""
        assert middleware._should_rate_limit("/api/v1/users") is True
        assert middleware._should_rate_limit("/api/v1/auth/login") is True
        assert middleware._should_rate_limit("/api/v1/exams/list") is True

    def test_get_user_tier_no_user(self, middleware, mock_request):
        """Test tier detection for unauthenticated requests"""
        mock_request.state.user = None

        tier = middleware._get_user_tier(mock_request)

        assert tier == UserTier.FREE

    def test_get_user_tier_free_user(self, middleware, mock_request):
        """Test tier detection for FREE user"""
        mock_user = Mock()
        mock_user.role = "student"
        mock_user.is_premium = False
        mock_request.state.user = mock_user

        tier = middleware._get_user_tier(mock_request)

        assert tier == UserTier.FREE

    def test_get_user_tier_premium_user(self, middleware, mock_request):
        """Test tier detection for PREMIUM user"""
        mock_user = Mock()
        mock_user.role = "student"
        mock_user.is_premium = True
        mock_request.state.user = mock_user

        tier = middleware._get_user_tier(mock_request)

        assert tier == UserTier.PREMIUM

    def test_get_user_tier_admin_user(self, middleware, mock_request):
        """Test tier detection for ADMIN user"""
        mock_user = Mock()
        mock_user.role = "admin"
        mock_request.state.user = mock_user

        tier = middleware._get_user_tier(mock_request)

        assert tier == UserTier.ADMIN

    def test_get_user_tier_superadmin_user(self, middleware, mock_request):
        """Test tier detection for superadmin user"""
        mock_user = Mock()
        mock_user.role = "superadmin"
        mock_request.state.user = mock_user

        tier = middleware._get_user_tier(mock_request)

        assert tier == UserTier.ADMIN

    def test_get_user_tier_super_admin_slug(self, middleware, mock_request):
        """Canonical super_admin string maps to ADMIN tier"""
        mock_user = Mock()
        mock_user.role = "super_admin"
        mock_request.state.user = mock_user

        assert middleware._get_user_tier(mock_request) == UserTier.ADMIN

    def test_get_user_tier_teacher_premium(self, middleware, mock_request):
        mock_user = Mock()
        mock_user.role = "teacher"
        mock_user.is_premium = False
        mock_request.state.user = mock_user

        assert middleware._get_user_tier(mock_request) == UserTier.PREMIUM

    def test_get_identifier_authenticated(self, middleware, mock_request):
        """Test identifier for authenticated user"""
        mock_user = Mock()
        mock_user.id = "user-uuid-1234"
        mock_request.state.user = mock_user

        identifier = middleware._get_identifier(mock_request)

        assert identifier == "user-uuid-1234"

    def test_get_identifier_unauthenticated(self, middleware, mock_request):
        """Test identifier for unauthenticated user (uses IP)"""
        mock_request.state.user = None
        mock_request.client.host = "192.168.1.100"

        identifier = middleware._get_identifier(mock_request)

        assert identifier == "192.168.1.100"

    def test_get_identifier_no_client(self, middleware, mock_request):
        """Test identifier when no client info available"""
        mock_request.state.user = None
        mock_request.client = None

        identifier = middleware._get_identifier(mock_request)

        assert identifier == "unknown"

    def test_add_rate_limit_headers(self, middleware):
        """Test adding rate limit headers to response"""
        response = Response()
        rate_info = {
            "limit": 60,
            "remaining": 45,
            "reset": 1699876543,
            "window": 60,
            "retry_after": 0
        }

        middleware._add_rate_limit_headers(response, rate_info)

        assert response.headers["X-RateLimit-Limit"] == "60"
        assert response.headers["X-RateLimit-Remaining"] == "45"
        assert response.headers["X-RateLimit-Reset"] == "1699876543"
        assert response.headers["X-RateLimit-Window"] == "60"

    def test_add_rate_limit_headers_with_retry_after(self, middleware):
        """Test adding Retry-After header when rate limited"""
        response = Response()
        rate_info = {
            "limit": 60,
            "remaining": 0,
            "reset": 1699876543,
            "window": 60,
            "retry_after": 15
        }

        middleware._add_rate_limit_headers(response, rate_info)

        assert response.headers["Retry-After"] == "15"
        assert response.headers["X-RateLimit-Remaining"] == "0"

    @pytest.mark.asyncio
    async def test_dispatch_excluded_path(self, middleware, mock_request):
        """Test that excluded paths bypass rate limiting"""
        mock_request.url.path = "/health"

        call_next = AsyncMock(return_value=Response(status_code=200))

        response = await middleware.dispatch(mock_request, call_next)

        # Should call next without checking rate limit
        call_next.assert_called_once_with(mock_request)
        assert response.status_code == 200

        # Rate limiter should NOT be called
        middleware.rate_limiter.check_rate_limit.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_allowed(self, middleware, mock_request, mock_rate_limiter):
        """Test dispatch when request is allowed"""
        mock_request.url.path = "/api/v1/test"
        mock_request.state.user = None

        # Mock successful rate limit check
        mock_rate_limiter.check_rate_limit.return_value = (True, {
            "limit": 60,
            "remaining": 45,
            "reset": 1699876543,
            "window": 60,
            "retry_after": 0
        })

        call_next = AsyncMock(return_value=Response(status_code=200))

        response = await middleware.dispatch(mock_request, call_next)

        # Should proceed and add headers
        call_next.assert_called_once_with(mock_request)
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_rate_limited(self, middleware, mock_request, mock_rate_limiter):
        """Test dispatch when rate limit exceeded"""
        mock_request.url.path = "/api/v1/test"

        # Mock rate limit exceeded
        mock_rate_limiter.check_rate_limit.return_value = (False, {
            "limit": 60,
            "remaining": 0,
            "reset": 1699876543,
            "window": 60,
            "retry_after": 15
        })

        call_next = AsyncMock(return_value=Response(status_code=200))

        response = await middleware.dispatch(mock_request, call_next)

        # Should return 429 without calling next
        call_next.assert_not_called()
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "15"

        # Check response body
        # Response is JSONResponse, need to decode
        assert b"rate_limit_exceeded" in response.body

    @pytest.mark.asyncio
    async def test_dispatch_premium_user(self, middleware, mock_request, mock_rate_limiter):
        """Test dispatch with premium user gets higher limits"""
        mock_user = Mock()
        mock_user.id = "premium-user"
        mock_user.role = "student"
        mock_user.is_premium = True
        mock_request.state.user = mock_user

        mock_rate_limiter.check_rate_limit.return_value = (True, {
            "limit": 300,  # PREMIUM limit
            "remaining": 250,
            "reset": 1699876543,
            "window": 60,
            "retry_after": 0
        })

        call_next = AsyncMock(return_value=Response(status_code=200))

        await middleware.dispatch(mock_request, call_next)

        # Verify rate limiter was called with PREMIUM tier
        mock_rate_limiter.check_rate_limit.assert_called_once()
        call_args = mock_rate_limiter.check_rate_limit.call_args
        assert call_args.kwargs["tier"] == UserTier.PREMIUM

    @pytest.mark.asyncio
    async def test_dispatch_error_handling(self, middleware, mock_request, mock_rate_limiter):
        """Test graceful error handling (fail-open)"""
        # Simulate rate limiter failure
        mock_rate_limiter.check_rate_limit.side_effect = Exception("Redis connection error")

        call_next = AsyncMock(return_value=Response(status_code=200))

        response = await middleware.dispatch(mock_request, call_next)

        # Should continue despite error (fail-open)
        call_next.assert_called_once_with(mock_request)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_rate_limit_status_authenticated(self, mock_rate_limiter):
        """Test get_rate_limit_status for authenticated user"""
        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"

        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.role = "student"
        mock_user.is_premium = False
        mock_request.state.user = mock_user

        with patch("core.rate_limit_middleware.get_rate_limiter", return_value=mock_rate_limiter):
            status = await get_rate_limit_status(mock_request)

            assert status["tier"] == "free"
            assert status["limit"] == 60
            assert status["remaining"] == 45
            assert "reset_datetime" in status

    @pytest.mark.asyncio
    async def test_get_rate_limit_status_unauthenticated(self, mock_rate_limiter):
        """Test get_rate_limit_status for unauthenticated user"""
        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state.user = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        with patch("core.rate_limit_middleware.get_rate_limiter", return_value=mock_rate_limiter):
            status = await get_rate_limit_status(mock_request)

            assert status["tier"] == "free"
            # Should call get_rate_limit_info with IP address
            mock_rate_limiter.get_rate_limit_info.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
