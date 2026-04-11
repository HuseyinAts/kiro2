"""
CSRF (Cross-Site Request Forgery) Protection
SECURITY FIX: Double-submit cookie pattern implementation
"""

import hmac
import secrets

from fastapi import Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from core.config import settings


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware using Double-Submit Cookie Pattern

    How it works:
    1. Server generates CSRF token and sets it as httponly cookie
    2. Frontend reads token from cookie and includes in X-CSRF-Token header
    3. Server validates both cookie and header match

    This prevents CSRF attacks because:
    - Attacker cannot read the cookie (httponly)
    - Attacker cannot set custom headers in cross-origin requests
    """

    def __init__(
        self,
        app,
        secret_key: str | None = None,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        safe_methods: set = None,
        exempt_paths: list = None,
    ):
        super().__init__(app)
        self.secret_key = secret_key or settings.secret_key
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.safe_methods = safe_methods or {"GET", "HEAD", "OPTIONS", "TRACE"}
        self.exempt_paths = exempt_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/kayit",
            "/api/auth/register",  # Registration endpoint for development
            "/api/auth/login",  # Login endpoint
            "/health",
            "/api/v1/chat",  # Chat endpoints for development
            "/api/chat",  # Alternative chat endpoints
        ]

    def _generate_csrf_token(self) -> str:
        """Generate a new CSRF token"""
        return secrets.token_urlsafe(32)

    def _validate_csrf_token(self, cookie_token: str, header_token: str) -> bool:
        """Validate CSRF token (constant-time comparison)"""
        if not cookie_token or not header_token:
            return False

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(cookie_token, header_token)

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from CSRF protection"""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with CSRF protection"""

        # FIX 2026-04-01: environment bazli bypass kaldirildi.
        # Onceki kod: if settings.environment == "development": return
        # Bu, production'da da CSRF'i tamamen devre disi birakiyordu.
        # Simdi CSRF kontrolu sadece exempt_paths config'e gore calisir.
        # Phase 2: /api/v1/ exempt_paths'tan kaldirildiginda gercek CSRF aktif olur.

        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            response = await call_next(request)
            # Set CSRF token cookie for subsequent requests
            if self.cookie_name not in request.cookies:
                csrf_token = self._generate_csrf_token()
                response.set_cookie(
                    key=self.cookie_name,
                    value=csrf_token,
                    httponly=True,
                    secure=settings.environment == "production",
                    samesite="strict",
                    max_age=3600 * 24,  # 24 hours
                )
            return response

        # Skip CSRF check for exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # Session 147 (GF99): Bearer-authenticated API clients cannot be
        # CSRF'd (they don't auto-send cookies cross-site and attackers
        # can't read the header back), so bypass CSRF for Authorization
        # header-based requests. Cookie-authed browsers still go through
        # the double-submit check below.
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return await call_next(request)

        # Validate CSRF token for state-changing methods
        cookie_token = request.cookies.get(self.cookie_name)
        header_token = request.headers.get(self.header_name)

        if not self._validate_csrf_token(cookie_token, header_token):
            # Session 147 (GF99): `raise HTTPException` inside middleware
            # dispatch escapes through the middleware stack as an
            # ExceptionGroup and surfaces as a generic 500 — FastAPI's
            # HTTPException handler only catches exceptions raised from
            # route handlers, not from middleware. Return a JSONResponse
            # directly so the 403 reaches the client intact.
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "CSRF token validation failed. Invalid or missing token.",
                },
            )

        # Token valid, process request
        response = await call_next(request)

        # Rotate CSRF token after successful state-changing request
        new_csrf_token = self._generate_csrf_token()
        response.set_cookie(
            key=self.cookie_name,
            value=new_csrf_token,
            httponly=True,
            secure=settings.environment == "production",
            samesite="strict",
            max_age=3600 * 24,  # 24 hours
        )

        return response


async def get_csrf_token(request: Request) -> str:
    """
    Dependency to get current CSRF token
    Usage: token = Depends(get_csrf_token)
    """
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        # Generate new token if not exists
        csrf_token = secrets.token_urlsafe(32)
    return csrf_token


async def validate_csrf_token(
    request: Request, x_csrf_token: str | None = Header(None, alias="X-CSRF-Token")
) -> bool:
    """
    Dependency to validate CSRF token
    Usage: validated = Depends(validate_csrf_token)

    Raises:
        HTTPException: If CSRF validation fails
    """
    cookie_token = request.cookies.get("csrf_token")

    if not cookie_token or not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing"
        )

    if not hmac.compare_digest(cookie_token, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token validation failed"
        )

    return True


def setup_csrf_protection(app, **kwargs):
    """
    Setup CSRF protection middleware

    Args:
        app: FastAPI application
        **kwargs: Additional configuration for CSRFProtectionMiddleware

    Example:
        from core.csrf_protection import setup_csrf_protection
        setup_csrf_protection(app, exempt_paths=["/api/webhook"])
    """
    csrf_middleware = CSRFProtectionMiddleware(app, **kwargs)
    app.add_middleware(CSRFProtectionMiddleware, **kwargs)
    return csrf_middleware
