"""
Version Redirect Middleware

Redirects legacy versionless API paths to /api/v1/ equivalents.
Provides backward compatibility during router prefix standardization.

Example: /api/learning-path/my-profile → /api/v1/learning-path/my-profile

This middleware should be removed after all clients migrate to /api/v1/ URLs.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

# Legacy versionless prefixes that should redirect to /api/v1/
# Format: old_prefix → new_prefix (all without trailing slash)
LEGACY_PREFIXES: list[tuple[str, str]] = [
    ("/api/learning-path", "/api/v1/learning-path"),
    ("/api/chat", "/api/v1/chat"),
    ("/api/realms", "/api/v1/realms"),
    ("/api/bilge-alp", "/api/v1/bilge-alp"),
    ("/api/teachers", "/api/v1/teachers"),
    ("/api/manipulatives", "/api/v1/manipulatives"),
    ("/api/youtube", "/api/v1/youtube"),
    ("/api/adhd-support", "/api/v1/adhd-support"),
    ("/api/study-rooms", "/api/v1/study-rooms"),
    ("/api/batch", "/api/v1/batch"),
    ("/api/config", "/api/v1/config"),
    ("/api/department-info", "/api/v1/department-info"),
    ("/api/live-sessions", "/api/v1/live-sessions"),
    ("/api/ocr", "/api/v1/ocr"),
    ("/api/pdf", "/api/v1/pdf"),
    ("/api/preference-simulation", "/api/v1/preference-simulation"),
    ("/api/quality-gates", "/api/v1/quality-gates"),
    ("/api/questions/hybrid", "/api/v1/questions/hybrid"),
    ("/api/reviews", "/api/v1/reviews"),
    ("/api/sentry-demo", "/api/v1/sentry-demo"),
    ("/api/tracing-demo", "/api/v1/tracing-demo"),
    ("/api/university-advisory", "/api/v1/university-advisory"),
    ("/api/university-info", "/api/v1/university-info"),
    ("/api/video-analytics", "/api/v1/video-analytics"),
    ("/api/vision", "/api/v1/vision"),
    ("/api/zemberek", "/api/v1/zemberek"),
    ("/api/errors", "/api/v1/errors"),
    ("/api/analytics", "/api/v1/analytics"),
    # Prefix-less routes
    ("/search", "/api/v1/search"),
    ("/validation", "/api/v1/validation"),
    ("/yolo", "/api/v1/yolo"),
    ("/question-parser", "/api/v1/question-parser"),
]

# Sort by longest prefix first to avoid partial matches
LEGACY_PREFIXES.sort(key=lambda x: len(x[0]), reverse=True)


class VersionRedirectMiddleware(BaseHTTPMiddleware):
    """Redirects legacy versionless API paths to /api/v1/ equivalents."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Fast path: /api/v1/ trafigi icin 32 kural dongusunu atla
        if path.startswith("/api/v1/"):
            return await call_next(request)

        for old_prefix, new_prefix in LEGACY_PREFIXES:
            if path == old_prefix or path.startswith(old_prefix + "/"):
                new_path = new_prefix + path[len(old_prefix) :]
                query = str(request.url.query)
                redirect_url = new_path + ("?" + query if query else "")
                return RedirectResponse(
                    url=redirect_url,
                    status_code=307,  # Preserve HTTP method (POST, PUT, etc.)
                )

        return await call_next(request)
