"""
Advanced Redis-based Rate Limiter
PHASE 2 Sprint 6: Advanced Rate Limiting

Features:
- Distributed rate limiting with Redis
- Endpoint-specific limits
- Tier-based limits (free/premium/admin)
- Rate limit headers (RFC 6585)
- Sliding window algorithm
- IP & User-based limiting
"""
import time
from typing import Optional, Tuple, Dict
from enum import Enum

import redis.asyncio as redis
from fastapi import Request, HTTPException, status
from core.structured_logger import get_logger

logger = get_logger(__name__)


class UserTier(str, Enum):
    """User subscription tiers"""
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception"""
    def __init__(self, retry_after: int, limit: int, window: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                "limit": limit,
                "window": window,
                "retry_after": retry_after
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Window": str(window)
            }
        )


class AdvancedRateLimiter:
    """
    Redis-based distributed rate limiter

    Uses sliding window algorithm for accurate rate limiting.
    Supports multiple tiers and endpoint-specific limits.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize rate limiter

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

        # Default rate limits per tier (requests per minute)
        self.tier_limits = {
            UserTier.FREE: {
                "default": 60,  # 60 requests/minute
                "auth": 10,  # 10 auth requests/minute
                "export": 2,  # 2 exports/minute
                "ai": 20,  # 20 AI requests/minute
            },
            UserTier.PREMIUM: {
                "default": 300,  # 300 requests/minute
                "auth": 30,
                "export": 10,
                "ai": 100,
            },
            UserTier.ADMIN: {
                "default": 10000,  # No practical limit
                "auth": 1000,
                "export": 1000,
                "ai": 1000,
            }
        }

        # Endpoint-specific limits (overrides tier defaults)
        self.endpoint_limits = {
            "/api/v1/auth/login": {"limit": 5, "window": 60},  # 5 per minute
            "/api/v1/auth/register": {"limit": 3, "window": 60},  # 3 per minute
            "/api/v1/kvkk/privacy/export": {"limit": 2, "window": 3600},  # 2 per hour
            "/api/v1/ai/chat": {"limit": 20, "window": 60},  # 20 per minute (free)
        }

    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("rate_limiter_connected", redis_url=self.redis_url)

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("rate_limiter_disconnected")

    def _get_rate_limit_key(
        self,
        identifier: str,
        endpoint: str,
        tier: UserTier
    ) -> str:
        """
        Generate Redis key for rate limit

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint
            tier: User tier

        Returns:
            Redis key string
        """
        return f"ratelimit:{tier.value}:{endpoint}:{identifier}"

    def _get_tier_limit(
        self,
        tier: UserTier,
        endpoint_category: str = "default"
    ) -> int:
        """
        Get rate limit for tier and endpoint category

        Args:
            tier: User tier
            endpoint_category: Endpoint category (default, auth, export, ai)

        Returns:
            Rate limit (requests per window)
        """
        return self.tier_limits[tier].get(
            endpoint_category,
            self.tier_limits[tier]["default"]
        )

    def _categorize_endpoint(self, endpoint: str) -> str:
        """
        Categorize endpoint for rate limiting

        Args:
            endpoint: API endpoint path

        Returns:
            Category string (default, auth, export, ai)
        """
        if "/auth/" in endpoint:
            return "auth"
        elif "/export" in endpoint or "/delete" in endpoint:
            return "export"
        elif "/ai/" in endpoint or "/chat" in endpoint:
            return "ai"
        else:
            return "default"

    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        tier: UserTier = UserTier.FREE,
        window: int = 60  # seconds
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is within rate limit (Sliding Window Algorithm)

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint
            tier: User tier
            window: Time window in seconds

        Returns:
            Tuple of (allowed: bool, info: dict)
            info contains: limit, remaining, reset, retry_after
        """
        if not self.redis_client:
            await self.connect()

        # Check for endpoint-specific limit
        if endpoint in self.endpoint_limits:
            limit = self.endpoint_limits[endpoint]["limit"]
            window = self.endpoint_limits[endpoint]["window"]
        else:
            # Use tier-based limit
            category = self._categorize_endpoint(endpoint)
            limit = self._get_tier_limit(tier, category)

        key = self._get_rate_limit_key(identifier, endpoint, tier)
        now = time.time()
        window_start = now - window

        # Sliding window using Redis sorted set
        pipe = self.redis_client.pipeline()

        # Remove old entries outside window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiry on key
        pipe.expire(key, window + 10)  # Window + 10s buffer

        results = await pipe.execute()
        current_count = results[1]  # Count before adding new request

        # Calculate info
        remaining = max(0, limit - current_count - 1)
        reset = int(now + window)
        retry_after = 0

        if current_count >= limit:
            # Get oldest request in window
            oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_time = oldest[0][1]
                retry_after = int(oldest_time + window - now)

            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                endpoint=endpoint,
                tier=tier.value,
                count=current_count,
                limit=limit
            )

            return False, {
                "limit": limit,
                "remaining": 0,
                "reset": reset,
                "retry_after": max(1, retry_after),
                "window": window
            }

        return True, {
            "limit": limit,
            "remaining": remaining,
            "reset": reset,
            "retry_after": 0,
            "window": window
        }

    async def reset_rate_limit(self, identifier: str, endpoint: str, tier: UserTier):
        """
        Reset rate limit for identifier (admin only)

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint
            tier: User tier
        """
        if not self.redis_client:
            await self.connect()

        key = self._get_rate_limit_key(identifier, endpoint, tier)
        await self.redis_client.delete(key)

        logger.info(
            "rate_limit_reset",
            identifier=identifier,
            endpoint=endpoint,
            tier=tier.value
        )

    async def get_rate_limit_info(
        self,
        identifier: str,
        endpoint: str,
        tier: UserTier = UserTier.FREE
    ) -> Dict[str, int]:
        """
        Get current rate limit status without incrementing

        Args:
            identifier: User ID or IP address
            endpoint: API endpoint
            tier: User tier

        Returns:
            Dict with limit, remaining, reset info
        """
        if not self.redis_client:
            await self.connect()

        # Get limit
        if endpoint in self.endpoint_limits:
            limit = self.endpoint_limits[endpoint]["limit"]
            window = self.endpoint_limits[endpoint]["window"]
        else:
            category = self._categorize_endpoint(endpoint)
            limit = self._get_tier_limit(tier, category)
            window = 60

        key = self._get_rate_limit_key(identifier, endpoint, tier)
        now = time.time()
        window_start = now - window

        # Count requests in window
        await self.redis_client.zremrangebyscore(key, 0, window_start)
        current_count = await self.redis_client.zcard(key)

        remaining = max(0, limit - current_count)
        reset = int(now + window)

        return {
            "limit": limit,
            "remaining": remaining,
            "reset": reset,
            "window": window
        }


# Global rate limiter instance
_rate_limiter: Optional[AdvancedRateLimiter] = None


def get_rate_limiter() -> AdvancedRateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        from core.config import settings
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        _rate_limiter = AdvancedRateLimiter(redis_url)
    return _rate_limiter


async def check_rate_limit(
    request: Request,
    tier: UserTier = UserTier.FREE,
    user_id: Optional[str] = None
) -> Dict[str, int]:
    """
    Check rate limit for request

    Args:
        request: FastAPI request
        tier: User tier
        user_id: User ID (if authenticated)

    Returns:
        Rate limit info dict

    Raises:
        RateLimitExceeded: If rate limit exceeded
    """
    limiter = get_rate_limiter()

    # Use user_id if available, otherwise IP
    identifier = user_id if user_id else request.client.host
    endpoint = request.url.path

    allowed, info = await limiter.check_rate_limit(
        identifier=identifier,
        endpoint=endpoint,
        tier=tier
    )

    if not allowed:
        raise RateLimitExceeded(
            retry_after=info["retry_after"],
            limit=info["limit"],
            window=info["window"]
        )

    return info


__all__ = [
    "AdvancedRateLimiter",
    "UserTier",
    "RateLimitExceeded",
    "get_rate_limiter",
    "check_rate_limit"
]
