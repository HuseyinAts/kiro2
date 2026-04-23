"""
Security Headers Middleware
TASK 51.6: CSP headers and XSS protection

Implements security headers for protection against common web vulnerabilities:
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME type sniffing
- Man-in-the-Middle attacks
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses

    Implements OWASP recommended security headers for web applications.
    """

    def __init__(self, app, csp_policy: str = None):
        super().__init__(app)
        self.csp_policy = csp_policy or self._default_csp_policy()

    @staticmethod
    def _default_csp_policy() -> str:
        """
        Default Content Security Policy

        Allows:
        - Scripts from self and MathJax CDN
        - Styles from self (inline styles for React)
        - Images from self and data URIs
        - Fonts from self and Google Fonts
        - Connect to self (API calls)
        """
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net https://cdn.mathjax.org; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
            "font-src 'self' fonts.gstatic.com data:; "
            "img-src 'self' data: https:; "
            "media-src 'self' blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response: Response = await call_next(request)

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS filtering in browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Force HTTPS connections (HSTS)
        # max-age=31536000 (1 year), includeSubDomains
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains; preload"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # Referrer policy - protect user privacy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (formerly Feature-Policy)
        # Restrict access to browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # Cross-Origin policies
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        return response


def get_security_headers_middleware(
    csp_policy: str = None,
) -> SecurityHeadersMiddleware:
    """
    Factory function to create security headers middleware

    Args:
        csp_policy: Custom Content Security Policy. If None, uses default.

    Returns:
        Configured SecurityHeadersMiddleware instance

    Usage:
        from fastapi import FastAPI
        from core.security_headers import get_security_headers_middleware

        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
    """

    def middleware_factory(app):
        return SecurityHeadersMiddleware(app, csp_policy=csp_policy)

    return middleware_factory


# CSP policy presets
CSP_POLICIES = {
    "strict": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    ),
    "moderate": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    ),
    "development": (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' *; "
        "style-src 'self' 'unsafe-inline' *; "
        "img-src * data: blob:; "
        "font-src * data:; "
        "connect-src * ws: wss:; "
        "frame-src *"
    ),
}


def get_csp_policy(environment: str = "production") -> str:
    """
    Get CSP policy based on environment

    Args:
        environment: "production", "staging", or "development"

    Returns:
        Appropriate CSP policy string
    """
    if environment == "development":
        return CSP_POLICIES["development"]
    if environment == "staging":
        return CSP_POLICIES["moderate"]
    return CSP_POLICIES["strict"]
