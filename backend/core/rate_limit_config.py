"""
Rate Limiting Configuration (Task 51.2)
Endpoint-specific rate limits and user-tier limits

Author: Claude
Date: 2025-10-27
"""
from dataclasses import dataclass
from enum import Enum

from core.rate_limiting import RateLimitRule, RateLimitScope, RateLimitStrategy


class UserTier(str, Enum):
    """User subscription tiers"""

    ANONYMOUS = "anonymous"
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"


@dataclass
class EndpointRateLimit:
    """Rate limit configuration for specific endpoint"""

    endpoint: str
    anonymous_limit: int
    free_limit: int
    premium_limit: int
    admin_limit: int
    window: int  # seconds
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    description: str = ""


# Endpoint-specific rate limits
ENDPOINT_RATE_LIMITS = [
    # Authentication endpoints (strict limits to prevent brute force)
    EndpointRateLimit(
        endpoint="/api/v1/auth/login",
        anonymous_limit=5,
        free_limit=5,
        premium_limit=5,
        admin_limit=20,
        window=60,  # 1 minute
        strategy=RateLimitStrategy.FIXED_WINDOW,
        description="Login attempts - strict to prevent brute force",
    ),
    EndpointRateLimit(
        endpoint="/api/v1/auth/register",
        anonymous_limit=3,
        free_limit=3,
        premium_limit=3,
        admin_limit=10,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.FIXED_WINDOW,
        description="Registration - strict to prevent spam accounts",
    ),
    EndpointRateLimit(
        endpoint="/api/v1/auth/reset-password",
        anonymous_limit=3,
        free_limit=3,
        premium_limit=5,
        admin_limit=10,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.TOKEN_BUCKET,
        description="Password reset requests",
    ),
    EndpointRateLimit(
        endpoint="/api/v1/auth/verify-email",
        anonymous_limit=5,
        free_limit=5,
        premium_limit=10,
        admin_limit=20,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.FIXED_WINDOW,
        description="Email verification attempts",
    ),
    # Exam endpoints
    EndpointRateLimit(
        endpoint="/api/v1/exam/submit",
        anonymous_limit=0,  # Not allowed for anonymous
        free_limit=10,
        premium_limit=50,
        admin_limit=100,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Exam submission - prevent spam",
    ),
    EndpointRateLimit(
        endpoint="/api/v1/exam/start",
        anonymous_limit=0,
        free_limit=20,
        premium_limit=100,
        admin_limit=200,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Exam start requests",
    ),
    EndpointRateLimit(
        endpoint="/api/v1/exam/questions",
        anonymous_limit=0,
        free_limit=100,
        premium_limit=500,
        admin_limit=1000,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Question fetching",
    ),
    # Chat endpoints
    EndpointRateLimit(
        endpoint="/api/v1/chat/message",
        anonymous_limit=0,
        free_limit=30,
        premium_limit=100,
        admin_limit=200,
        window=60,  # 1 minute
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Chat messages",
    ),
    EndpointRateLimit(
        endpoint="/api/v1/chat/history",
        anonymous_limit=0,
        free_limit=50,
        premium_limit=200,
        admin_limit=500,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Chat history fetching",
    ),
    # Search endpoints
    EndpointRateLimit(
        endpoint="/api/v1/search",
        anonymous_limit=10,
        free_limit=50,
        premium_limit=200,
        admin_limit=500,
        window=60,  # 1 minute
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Content search requests",
    ),
    EndpointRateLimit(
        endpoint="/api/v1/search/questions",
        anonymous_limit=10,
        free_limit=50,
        premium_limit=200,
        admin_limit=500,
        window=60,  # 1 minute
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Question search",
    ),
    # Content endpoints
    EndpointRateLimit(
        endpoint="/api/v1/content/video",
        anonymous_limit=5,
        free_limit=30,
        premium_limit=100,
        admin_limit=200,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Video content fetching",
    ),
    EndpointRateLimit(
        endpoint="/api/v1/content/khan",
        anonymous_limit=5,
        free_limit=30,
        premium_limit=100,
        admin_limit=200,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Khan Academy content",
    ),
    EndpointRateLimit(
        endpoint="/api/v1/content/eba",
        anonymous_limit=5,
        free_limit=30,
        premium_limit=100,
        admin_limit=200,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="EBA TV content",
    ),
    # Admin endpoints (very strict for non-admins)
    EndpointRateLimit(
        endpoint="/api/v1/admin",
        anonymous_limit=0,
        free_limit=0,
        premium_limit=0,
        admin_limit=100,
        window=60,  # 1 minute
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Admin operations",
    ),
    # Analytics endpoints
    EndpointRateLimit(
        endpoint="/api/v1/analytics",
        anonymous_limit=0,
        free_limit=20,
        premium_limit=100,
        admin_limit=500,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="Analytics data fetching",
    ),
    # API key endpoints
    EndpointRateLimit(
        endpoint="/api/v1/api-keys/create",
        anonymous_limit=0,
        free_limit=5,
        premium_limit=20,
        admin_limit=100,
        window=86400,  # 1 day
        strategy=RateLimitStrategy.FIXED_WINDOW,
        description="API key creation - strict to prevent abuse",
    ),
    # File upload endpoints
    EndpointRateLimit(
        endpoint="/api/v1/upload",
        anonymous_limit=0,
        free_limit=10,
        premium_limit=50,
        admin_limit=200,
        window=3600,  # 1 hour
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="File uploads",
    ),
    # YouTube video recommendations endpoint (Task 12)
    EndpointRateLimit(
        endpoint="/api/youtube/recommendations",
        anonymous_limit=5,  # 5 req/min for anonymous users
        free_limit=10,  # 10 req/min for free users
        premium_limit=30,  # 30 req/min for premium users
        admin_limit=100,  # 100 req/min for admins
        window=60,  # 1 minute
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="YouTube video recommendations - protect YouTube API quota",
    ),
    # YouTube search endpoint (Task 12)
    EndpointRateLimit(
        endpoint="/api/youtube/search",
        anonymous_limit=5,
        free_limit=10,
        premium_limit=30,
        admin_limit=100,
        window=60,  # 1 minute
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        description="YouTube video search - protect YouTube API quota",
    ),
]

# Global rate limits (applied to all endpoints)
GLOBAL_RATE_LIMITS = {
    UserTier.ANONYMOUS: {"limit": 100, "window": 60},  # 100 req/min
    UserTier.FREE: {"limit": 100, "window": 60},  # 100 req/min
    UserTier.PREMIUM: {"limit": 200, "window": 60},  # 200 req/min
    UserTier.ADMIN: {"limit": 500, "window": 60},  # 500 req/min
}


def get_rate_limit_for_endpoint(endpoint: str, user_tier: UserTier) -> tuple[int, int]:
    """
    Get rate limit for specific endpoint and user tier

    Args:
        endpoint: API endpoint path
        user_tier: User's subscription tier

    Returns:
        Tuple of (limit, window in seconds)
    """
    # Find matching endpoint configuration
    for config in ENDPOINT_RATE_LIMITS:
        if endpoint.startswith(config.endpoint):
            limit = {
                UserTier.ANONYMOUS: config.anonymous_limit,
                UserTier.FREE: config.free_limit,
                UserTier.PREMIUM: config.premium_limit,
                UserTier.ADMIN: config.admin_limit,
            }.get(user_tier, config.free_limit)

            return (limit, config.window)

    # Fall back to global rate limits
    global_config = GLOBAL_RATE_LIMITS.get(user_tier, GLOBAL_RATE_LIMITS[UserTier.FREE])
    return (global_config["limit"], global_config["window"])


def get_user_tier_from_roles(
    roles: list[str] | None, is_premium: bool = False
) -> UserTier:
    """
    Determine user tier from roles

    Args:
        roles: List of user roles
        is_premium: Whether user has premium subscription

    Returns:
        UserTier enum
    """
    if not roles:
        return UserTier.ANONYMOUS

    if "admin" in roles or "superadmin" in roles:
        return UserTier.ADMIN

    if is_premium:
        return UserTier.PREMIUM

    return UserTier.FREE


def create_rate_limit_rules() -> list[RateLimitRule]:
    """
    Create comprehensive rate limit rules (Task 51.2)

    Returns:
        List of RateLimitRule objects
    """
    rules = []

    # Global rate limits for each user tier
    for tier, config in GLOBAL_RATE_LIMITS.items():
        scope = RateLimitScope.IP if tier == UserTier.ANONYMOUS else RateLimitScope.USER
        rules.append(
            RateLimitRule(
                scope=scope,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit=config["limit"],
                window=config["window"],
            )
        )

    # Endpoint-specific limits
    for endpoint_config in ENDPOINT_RATE_LIMITS:
        # Create rule for each tier
        for tier in UserTier:
            limit = {
                UserTier.ANONYMOUS: endpoint_config.anonymous_limit,
                UserTier.FREE: endpoint_config.free_limit,
                UserTier.PREMIUM: endpoint_config.premium_limit,
                UserTier.ADMIN: endpoint_config.admin_limit,
            }[tier]

            if limit > 0:  # Only create rule if limit exists
                scope = (
                    RateLimitScope.IP
                    if tier == UserTier.ANONYMOUS
                    else RateLimitScope.ENDPOINT
                )
                rules.append(
                    RateLimitRule(
                        scope=scope,
                        strategy=endpoint_config.strategy,
                        limit=limit,
                        window=endpoint_config.window,
                        endpoints=[endpoint_config.endpoint],
                    )
                )

    return rules
