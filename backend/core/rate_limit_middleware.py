"""
Rate Limit Middleware for FastAPI
PHASE 2 Sprint 6: Advanced Rate Limiting

Applies distributed rate limiting to all API requests.
Adds RFC 6585 compliant headers to responses.
"""
from datetime import datetime

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.advanced_rate_limiter import AdvancedRateLimiter, UserTier, get_rate_limiter
from core.structured_logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI

    Features:
    - Distributed rate limiting with Redis
    - Tier-based limits (FREE/PREMIUM/ADMIN)
    - Endpoint-specific limits
    - RFC 6585 compliant headers
    - Automatic user/IP identification
    """

    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: AdvancedRateLimiter | None = None,
        excluded_paths: list | None = None
    ):
        """
        Initialize rate limit middleware

        Args:
            app: FastAPI application
            rate_limiter: Rate limiter instance (uses global if None)
            excluded_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or get_rate_limiter()

        # Exclude health checks and docs from rate limiting
        self.excluded_paths = excluded_paths or [
            "/health",
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics"
        ]

    def _should_rate_limit(self, path: str) -> bool:
        """Check if path should be rate limited"""
        # Exclude specific paths
        if path in self.excluded_paths:
            return False

        # Exclude paths that start with excluded patterns
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return False

        return True

    def _get_user_tier(self, request: Request) -> UserTier:
        """
        Determine user tier from request

        Priority:
        1. User from auth token (if authenticated)
        2. Default to FREE tier
        """
        # Check if user is authenticated
        user = getattr(request.state, "user", None)

        if not user:
            return UserTier.FREE

        # Check user role/tier
        user_role = getattr(user, "role", None)

        if user_role == "admin" or user_role == "superadmin":
            return UserTier.ADMIN
        if user_role == "premium" or getattr(user, "is_premium", False):
            return UserTier.PREMIUM
        return UserTier.FREE

    def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting

        Priority:
        1. User ID (if authenticated)
        2. IP address (if not authenticated)
        """
        # Try to get user ID from request state
        user = getattr(request.state, "user", None)
        if user:
            user_id = getattr(user, "id", None)
            if user_id:
                return str(user_id)

        # Fallback to IP address
        if request.client:
            return request.client.host

        # Ultimate fallback
        return "unknown"

    def _add_rate_limit_headers(
        self,
        response: Response,
        rate_info: dict
    ) -> None:
        """
        Add RFC 6585 compliant rate limit headers

        Headers:
        - X-RateLimit-Limit: Maximum requests allowed
        - X-RateLimit-Remaining: Requests remaining in window
        - X-RateLimit-Reset: Unix timestamp when limit resets
        - X-RateLimit-Window: Time window in seconds
        """
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
        response.headers["X-RateLimit-Window"] = str(rate_info.get("window", 60))

        # Add retry-after if rate limit exceeded
        if rate_info.get("retry_after", 0) > 0:
            response.headers["Retry-After"] = str(rate_info["retry_after"])

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting

        Flow:
        1. Check if path should be rate limited
        2. Determine user tier
        3. Check rate limit
        4. Add headers to response
        5. Return 429 if exceeded
        """
        path = request.url.path

        # Skip rate limiting for excluded paths
        if not self._should_rate_limit(path):
            return await call_next(request)

        # Get user tier and identifier
        tier = self._get_user_tier(request)
        identifier = self._get_identifier(request)

        try:
            # Check rate limit
            allowed, rate_info = await self.rate_limiter.check_rate_limit(
                identifier=identifier,
                endpoint=path,
                tier=tier
            )

            if not allowed:
                # Rate limit exceeded
                logger.warning(
                    "rate_limit_exceeded",
                    identifier=identifier,
                    endpoint=path,
                    tier=tier.value,
                    limit=rate_info["limit"],
                    retry_after=rate_info["retry_after"]
                )

                # Return 429 Too Many Requests
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Try again in {rate_info['retry_after']} seconds.",
                        "limit": rate_info["limit"],
                        "window": rate_info["window"],
                        "retry_after": rate_info["retry_after"]
                    }
                )

                # Add rate limit headers
                self._add_rate_limit_headers(response, rate_info)

                return response

            # Process request
            response = await call_next(request)

            # Add rate limit headers to successful response
            self._add_rate_limit_headers(response, rate_info)

            return response

        except Exception as e:
            # If rate limiting fails, log error but don't block request
            logger.error(
                "rate_limit_middleware_error",
                identifier=identifier,
                endpoint=path,
                error=str(e)
            )

            # Continue without rate limiting on error
            return await call_next(request)


# Dependency for checking rate limit status
async def get_rate_limit_status(request: Request) -> dict:
    """
    Get rate limit status for current request

    Returns rate limit info without consuming a request.
    Useful for displaying remaining requests to users.
    """
    limiter = get_rate_limiter()

    # Get user tier and identifier (same logic as middleware)
    user = getattr(request.state, "user", None)

    if user:
        user_id = getattr(user, "id", None)
        identifier = str(user_id) if user_id else request.client.host

        user_role = getattr(user, "role", None)
        if user_role == "admin" or user_role == "superadmin":
            tier = UserTier.ADMIN
        elif user_role == "premium" or getattr(user, "is_premium", False):
            tier = UserTier.PREMIUM
        else:
            tier = UserTier.FREE
    else:
        identifier = request.client.host if request.client else "unknown"
        tier = UserTier.FREE

    # Get rate limit info without incrementing
    rate_info = await limiter.get_rate_limit_info(
        identifier=identifier,
        endpoint=request.url.path,
        tier=tier
    )

    return {
        "tier": tier.value,
        "limit": rate_info["limit"],
        "remaining": rate_info["remaining"],
        "reset": rate_info["reset"],
        "reset_datetime": datetime.fromtimestamp(rate_info["reset"]).isoformat(),
        "window": rate_info["window"]
    }


__all__ = [
    "RateLimitMiddleware",
    "get_rate_limit_status"
]
