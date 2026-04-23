"""
Authentication Rate Limiting
SECURITY FIX: Prevent brute force attacks on auth endpoints
"""

import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from .structured_logger import get_logger

logger = get_logger("auth_rate_limit")


@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""

    max_attempts: int  # Maximum attempts
    window_seconds: int  # Time window in seconds
    block_duration: int  # Block duration in seconds after limit exceeded


class AuthRateLimiter:
    """
    Rate limiter for authentication endpoints

    Features:
    - Per-IP rate limiting
    - Per-username rate limiting
    - Configurable limits per endpoint
    - Automatic blocking after limit exceeded
    - Failed attempt tracking
    """

    def __init__(self):
        # Rate limit rules per endpoint
        self.rules: dict[str, RateLimitRule] = {
            # Login: 5 attempts per minute
            "/api/v1/auth/login": RateLimitRule(
                max_attempts=5, window_seconds=60, block_duration=300  # 5 minutes block
            ),
            "/api/v1/auth/giris": RateLimitRule(
                max_attempts=5, window_seconds=60, block_duration=300
            ),
            # Register: 3 attempts per minute
            "/api/v1/auth/register": RateLimitRule(
                max_attempts=3,
                window_seconds=60,
                block_duration=600,  # 10 minutes block
            ),
            "/api/v1/auth/kayit": RateLimitRule(
                max_attempts=3, window_seconds=60, block_duration=600
            ),
            # Password reset: 3 attempts per hour
            "/api/v1/auth/password-reset": RateLimitRule(
                max_attempts=3,
                window_seconds=3600,
                block_duration=1800,  # 30 minutes block
            ),
            "/api/v1/auth/sifre-sifirlama": RateLimitRule(
                max_attempts=3, window_seconds=3600, block_duration=1800
            ),
            # Token refresh: 10 attempts per minute
            "/api/v1/auth/refresh": RateLimitRule(
                max_attempts=10, window_seconds=60, block_duration=300
            ),
        }

        # Tracking structures
        # {identifier: [(timestamp, success/fail), ...]}
        self.attempts: dict[str, list] = defaultdict(list)
        # {identifier: block_until_timestamp}
        self.blocked: dict[str, float] = {}

    def _get_identifier(self, request: Request, username: str | None = None) -> str:
        """
        Get unique identifier for rate limiting

        Combines IP + username (if available) for better tracking
        """
        ip = request.client.host if request.client else "unknown"
        if username:
            return f"{ip}:{username}"
        return ip

    def _clean_old_attempts(self, identifier: str, window_seconds: int):
        """Remove attempts outside the time window"""
        if identifier not in self.attempts:
            return

        now = time.time()
        cutoff = now - window_seconds

        # Keep only recent attempts
        self.attempts[identifier] = [
            (ts, success) for ts, success in self.attempts[identifier] if ts > cutoff
        ]

    def _is_blocked(self, identifier: str) -> tuple[bool, int | None]:
        """
        Check if identifier is blocked

        Returns:
            (is_blocked, remaining_seconds)
        """
        if identifier not in self.blocked:
            return False, None

        block_until = self.blocked[identifier]
        now = time.time()

        if now < block_until:
            remaining = int(block_until - now)
            return True, remaining
        # Block expired, remove it
        del self.blocked[identifier]
        return False, None

    def check_rate_limit(
        self, request: Request, endpoint: str, username: str | None = None
    ) -> None:
        """
        Check rate limit for request

        Args:
            request: FastAPI request
            endpoint: Endpoint path
            username: Username (if available from request body)

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Check if endpoint has rate limit rule
        if endpoint not in self.rules:
            return

        rule = self.rules[endpoint]
        identifier = self._get_identifier(request, username)

        # Check if blocked
        is_blocked, remaining = self._is_blocked(identifier)
        if is_blocked:
            logger.warning(
                "Blocked authentication attempt",
                extra_data={
                    "identifier": identifier,
                    "endpoint": endpoint,
                    "remaining_seconds": remaining,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many attempts. Please try again in {remaining} seconds.",
            )

        # Clean old attempts
        self._clean_old_attempts(identifier, rule.window_seconds)

        # Count recent attempts
        recent_attempts = len(self.attempts[identifier])

        # Check if limit exceeded
        if recent_attempts >= rule.max_attempts:
            # Block the identifier
            block_until = time.time() + rule.block_duration
            self.blocked[identifier] = block_until

            logger.error(
                "Rate limit exceeded - blocking user",
                extra_data={
                    "identifier": identifier,
                    "endpoint": endpoint,
                    "attempts": recent_attempts,
                    "max_attempts": rule.max_attempts,
                    "block_duration": rule.block_duration,
                },
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many attempts. Blocked for {rule.block_duration // 60} minutes.",
            )

        # Record this attempt (will be marked as success/fail later)
        self.attempts[identifier].append((time.time(), None))

    def record_attempt(
        self,
        request: Request,
        endpoint: str,
        success: bool,
        username: str | None = None,
    ):
        """
        Record authentication attempt result

        Args:
            request: FastAPI request
            endpoint: Endpoint path
            success: Whether attempt was successful
            username: Username
        """
        if endpoint not in self.rules:
            return

        identifier = self._get_identifier(request, username)

        # Update last attempt status
        if self.attempts.get(identifier):
            last_attempt = self.attempts[identifier][-1]
            # Update the None status with actual result
            self.attempts[identifier][-1] = (last_attempt[0], success)

        # If successful, clear failed attempts (reset window)
        if success and identifier in self.attempts:
            self.attempts[identifier] = []
            if identifier in self.blocked:
                del self.blocked[identifier]

        logger.info(
            "Auth attempt recorded",
            extra_data={
                "identifier": identifier,
                "endpoint": endpoint,
                "success": success,
                "username": username,
            },
        )

    def get_stats(self, identifier: str) -> dict:
        """Get rate limit stats for identifier"""
        is_blocked, remaining = self._is_blocked(identifier)
        return {
            "is_blocked": is_blocked,
            "block_remaining_seconds": remaining,
            "recent_attempts": len(self.attempts.get(identifier, [])),
        }


# Global rate limiter instance
auth_rate_limiter = AuthRateLimiter()


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic auth rate limiting

    Add to FastAPI app:
        app.add_middleware(AuthRateLimitMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        # Check if this is an auth endpoint
        path = request.url.path

        if any(
            auth_path in path
            for auth_path in [
                "/auth/login",
                "/auth/giris",
                "/auth/register",
                "/auth/kayit",
                "/auth/password-reset",
                "/auth/sifre-sifirlama",
            ]
        ):
            # Extract username from request body if available
            username = None
            if request.method == "POST":
                try:
                    # Try to get username from form or JSON body
                    # (without consuming the body stream)
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        # For JSON, we'll check after processing
                        pass
                except (KeyError, AttributeError) as e:
                    logger.debug(f"Content type check failed: {e}")

            # Check rate limit BEFORE processing request
            try:
                auth_rate_limiter.check_rate_limit(request, path, username)
            except HTTPException as e:
                # Return rate limit error immediately
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=e.status_code, content={"detail": e.detail}
                )

        # Process request
        response = await call_next(request)

        # Record attempt result if auth endpoint
        if any(
            auth_path in path
            for auth_path in [
                "/auth/login",
                "/auth/giris",
                "/auth/register",
                "/auth/kayit",
            ]
        ):
            # Successful if status code is 200/201
            success = 200 <= response.status_code < 300
            auth_rate_limiter.record_attempt(request, path, success)

        return response


# Utility function for manual rate limit checking
async def check_auth_rate_limit(
    request: Request, endpoint: str, username: str | None = None
):
    """
    Manually check auth rate limit

    Usage in route:
        @router.post("/login")
        async def login(request: Request, credentials: LoginCredentials):
            await check_auth_rate_limit(request, "/api/v1/auth/login", credentials.username)
            # ... rest of login logic
    """
    auth_rate_limiter.check_rate_limit(request, endpoint, username)


async def record_auth_attempt(
    request: Request, endpoint: str, success: bool, username: str | None = None
):
    """
    Manually record auth attempt

    Usage in route:
        try:
            user = await authenticate(username, password)
            await record_auth_attempt(request, "/api/v1/auth/login", True, username)
            return user
        except AuthError:
            await record_auth_attempt(request, "/api/v1/auth/login", False, username)
            raise
    """
    auth_rate_limiter.record_attempt(request, endpoint, success, username)
