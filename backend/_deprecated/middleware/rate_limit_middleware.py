"""
Enhanced Rate Limit Middleware (Task 51.2)
Tier-based rate limiting with endpoint-specific limits

Author: Claude
Date: 2025-10-27
"""
import json
import time

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from core.rate_limit_config import (
    UserTier,
    get_rate_limit_for_endpoint,
    get_user_tier_from_roles,
)
from core.rate_limiting import (
    AdvancedRateLimiter,
    RateLimitRule,
    RateLimitScope,
    RateLimitStrategy,
)
from core.structured_logger import get_logger

logger = get_logger("enhanced_rate_limit_middleware")


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enhanced rate limiting middleware (Task 51.2)

    Features:
    - User tier-based limits (Anonymous, Free, Premium, Admin)
    - Endpoint-specific rate limits
    - Redis ZSET-based sliding window
    - Comprehensive rate limit headers
    - Turkish error messages
    """

    def __init__(self, app, rate_limiter: AdvancedRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            # Extract user information
            user_id, user_tier, roles = self._extract_user_info(request)

            # Get endpoint
            endpoint = str(request.url.path)

            # Get rate limit for this endpoint and user tier
            limit, window = get_rate_limit_for_endpoint(endpoint, user_tier)

            # Check if endpoint is blocked for this tier
            if limit == 0:
                logger.warning(
                    f"Access denied for {user_tier.value} to {endpoint}",
                    extra_data={"user_id": user_id, "tier": user_tier.value},
                )

                error_response = {
                    "error": "Access denied",
                    "message": "Bu endpoint için yetkiniz bulunmamaktadır. Lütfen premium hesaba geçin veya giriş yapın.",
                    "required_tier": "premium"
                    if user_tier == UserTier.FREE
                    else "authenticated",
                }

                return Response(
                    content=json.dumps(error_response),
                    status_code=status.HTTP_403_FORBIDDEN,
                    headers={"Content-Type": "application/json"},
                )

            # Create dynamic rate limit rule for this request
            scope = (
                RateLimitScope.IP
                if user_tier == UserTier.ANONYMOUS
                else RateLimitScope.USER
            )
            rule = RateLimitRule(
                scope=scope,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit=limit,
                window=window,
                endpoints=[endpoint],
            )

            # Get identifier
            ip = self.rate_limiter._get_client_ip(request)
            identifier = self.rate_limiter._get_identifier(scope, ip, user_id, endpoint)

            # Check rate limit using the rule
            is_allowed = self.rate_limiter._check_rule(
                rule, request, ip, user_id, endpoint
            )

            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded: {user_tier.value} user on {endpoint}",
                    extra_data={
                        "user_id": user_id,
                        "tier": user_tier.value,
                        "endpoint": endpoint,
                        "ip": ip,
                    },
                )

                # Get rate limit info
                rate_limit_info = self.rate_limiter.get_rate_limit_info(
                    identifier, rule
                )
                retry_after = (
                    rate_limit_info.get("reset", time.time() + window) - time.time()
                )
                retry_after = max(1, int(retry_after))

                error_response = {
                    "error": "Rate limit exceeded",
                    "message": f"Çok fazla istek gönderdiniz. Lütfen {retry_after} saniye sonra tekrar deneyin.",
                    "retry_after": retry_after,
                    "limit": limit,
                    "window": window,
                    "user_tier": user_tier.value,
                    "upgrade_message": (
                        "Premium hesaba geçerek daha yüksek limit alabilirsiniz."
                        if user_tier in [UserTier.ANONYMOUS, UserTier.FREE]
                        else None
                    ),
                }

                return Response(
                    content=json.dumps(error_response),
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={
                        "Content-Type": "application/json",
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(
                            int(rate_limit_info.get("reset", time.time() + window))
                        ),
                        "X-RateLimit-Window": str(window),
                        "X-User-Tier": user_tier.value,
                    },
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            rate_limit_info = self.rate_limiter.get_rate_limit_info(identifier, rule)

            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(
                rate_limit_info.get("remaining", limit)
            )
            response.headers["X-RateLimit-Window"] = str(window)
            response.headers["X-User-Tier"] = user_tier.value

            if "reset" in rate_limit_info:
                response.headers["X-RateLimit-Reset"] = str(
                    int(rate_limit_info["reset"])
                )

            return response

        except Exception as e:
            logger.error(f"Rate limiting error: {e!s}", extra_data={"error": str(e)})
            # Fail-open: allow request on error
            return await call_next(request)

    def _extract_user_info(
        self, request: Request
    ) -> tuple[str | None, UserTier, list | None]:
        """
        Extract user information from request

        Returns:
            Tuple of (user_id, user_tier, roles)
        """
        user_id = None
        roles = None
        is_premium = False

        # Try to extract from JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from core.jwt_auth import jwt_manager

                token = auth_header.split(" ")[1]
                payload = jwt_manager.verify_token(token)

                user_id = payload.sub
                roles = getattr(payload, "roles", None)

                # Check if premium (could be from JWT claim or database)
                is_premium = getattr(payload, "is_premium", False)

            except Exception as e:
                logger.debug(f"Failed to extract user info from token: {e}")

        # Determine user tier
        user_tier = get_user_tier_from_roles(roles, is_premium)

        return user_id, user_tier, roles
