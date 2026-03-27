"""
Security Headers Middleware (Task 51.6)
Comprehensive HTTP security headers including CSP

Author: Claude
Date: 2025-10-27
"""
import secrets
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from core.structured_logger import get_logger

logger = get_logger("security_headers_middleware")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security Headers Middleware (Task 51.6)

    Adds comprehensive HTTP security headers:
    - Content-Security-Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - Strict-Transport-Security (HSTS)
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(
        self,
        app,
        enable_csp: bool = True,
        csp_report_only: bool = False,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        enable_nonce: bool = True,
    ):
        super().__init__(app)
        self.enable_csp = enable_csp
        self.csp_report_only = csp_report_only
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.enable_nonce = enable_nonce

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate CSP nonce for this request
        nonce = secrets.token_urlsafe(16) if self.enable_nonce else None

        # Store nonce in request state for templates to access
        if nonce:
            request.state.csp_nonce = nonce

        # Process request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response, nonce)

        return response

    def _add_security_headers(self, response: Response, nonce: Optional[str] = None):
        """Add all security headers to response"""

        # Content-Security-Policy (CSP)
        if self.enable_csp:
            csp_header = self._build_csp_header(nonce)
            header_name = (
                "Content-Security-Policy-Report-Only"
                if self.csp_report_only
                else "Content-Security-Policy"
            )
            response.headers[header_name] = csp_header

        # X-Frame-Options (prevent clickjacking)
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options (prevent MIME sniffing)
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection (legacy XSS protection for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security (HSTS) - enforce HTTPS
        if self.enable_hsts:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Referrer-Policy (control referer header)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (control browser features)
        response.headers["Permissions-Policy"] = self._build_permissions_policy()

        # X-Permitted-Cross-Domain-Policies (control cross-domain policies)
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

    def _build_csp_header(self, nonce: Optional[str] = None) -> str:
        """
        Build Content-Security-Policy header (Task 51.6)

        CSP prevents XSS attacks by restricting resource loading sources
        """
        nonce_directive = f" 'nonce-{nonce}'" if nonce else ""

        # CSP directives
        csp_directives = {
            # Default policy: only allow from same origin
            "default-src": "'self'",
            # Scripts: allow from self, CDNs, and with nonce
            "script-src": f"'self' 'unsafe-inline'{nonce_directive} https://cdn.jsdelivr.net https://unpkg.com",
            # Styles: allow from self, CDNs, and inline styles with nonce
            "style-src": f"'self' 'unsafe-inline'{nonce_directive} https://fonts.googleapis.com https://cdn.jsdelivr.net",
            # Images: allow from self, data URIs, and external sources
            "img-src": "'self' data: https: blob:",
            # Fonts: allow from self and font CDNs
            "font-src": "'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net",
            # AJAX, WebSocket, EventSource connections
            "connect-src": "'self' https://api.openai.com https://api.anthropic.com",
            # Frames: deny by default (same as X-Frame-Options)
            "frame-src": "'none'",
            # Form submission: only to same origin
            "form-action": "'self'",
            # Block mixed content (HTTP resources on HTTPS pages)
            "upgrade-insecure-requests": "",
            # Base URI restriction
            "base-uri": "'self'",
            # Object/embed restrictions (Flash, etc.)
            "object-src": "'none'",
            # Media sources (audio/video)
            "media-src": "'self' https://www.youtube.com https://player.vimeo.com blob:",
            # Worker sources (Web Workers, Service Workers)
            "worker-src": "'self' blob:",
            # Manifest sources (PWA manifest)
            "manifest-src": "'self'",
            # Report violations to this endpoint
            # "report-uri": "/api/v1/security/csp-report",
            # "report-to": "csp-endpoint",
        }

        # Build CSP string
        csp_parts = []
        for directive, value in csp_directives.items():
            if value:
                csp_parts.append(f"{directive} {value}")
            else:
                csp_parts.append(directive)

        csp_header = "; ".join(csp_parts)

        return csp_header

    def _build_permissions_policy(self) -> str:
        """
        Build Permissions-Policy header

        Controls which browser features and APIs can be used
        """
        permissions = {
            # Disable features not needed
            "geolocation": "()",  # Disable geolocation
            "microphone": "()",  # Disable microphone
            "camera": "()",  # Disable camera
            "payment": "()",  # Disable payment API
            "usb": "()",  # Disable USB API
            "magnetometer": "()",  # Disable magnetometer
            "gyroscope": "()",  # Disable gyroscope
            "accelerometer": "()",  # Disable accelerometer
            # Allow fullscreen from same origin
            "fullscreen": "(self)",
            # Allow picture-in-picture
            "picture-in-picture": "(self)",
        }

        permission_parts = [
            f"{feature}={policy}" for feature, policy in permissions.items()
        ]

        return ", ".join(permission_parts)


class CSPReportingMiddleware(BaseHTTPMiddleware):
    """
    CSP Reporting Middleware

    Logs CSP violations for monitoring and debugging
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check if this is a CSP violation report
        if (
            request.url.path == "/api/v1/security/csp-report"
            and request.method == "POST"
        ):
            try:
                report = await request.json()
                logger.warning(
                    "[CSP] Content Security Policy violation reported",
                    extra_data={
                        "violated_directive": report.get("violated-directive"),
                        "blocked_uri": report.get("blocked-uri"),
                        "document_uri": report.get("document-uri"),
                        "referrer": report.get("referrer"),
                        "status_code": report.get("status-code"),
                    },
                )

                return Response(status_code=204)  # No content

            except Exception as e:
                logger.error(f"[CSP] Failed to process CSP report: {e}")
                return Response(status_code=400)

        return await call_next(request)
