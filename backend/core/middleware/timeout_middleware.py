"""
Timeout Middleware
Path-based timeout configuration for FastAPI endpoints

Different endpoints have different timeout requirements:
- File uploads: 300 seconds (5 minutes)
- Batch operations: 600 seconds (10 minutes)
- LLM/AI operations: 120 seconds (2 minutes)
- Standard requests: 30 seconds
"""

import asyncio
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeouts based on endpoint paths

    Timeout configuration:
    - /api/v1/batch-upload/*: 600s (batch question generation)
    - /api/v1/upload/*: 300s (PDF uploads, file uploads)
    - /api/v1/osym-pdf/upload: 300s (OSYM PDF parsing)
    - /api/v1/chat/*: 120s (LLM chat operations)
    - /api/v1/learning-path/*: 120s (AI learning path generation)
    - /api/v1/rag/*: 90s (RAG operations)
    - Default: 30s (standard requests)
    """

    # Path-based timeout configuration (in seconds)
    TIMEOUT_CONFIG = {
        # Batch operations - very long running
        '/api/v1/batch-upload': 600,
        '/api/v1/batch-generation': 600,
        '/api/celery': 600,

        # File uploads - long running
        '/api/v1/upload': 300,
        '/api/v1/osym-pdf/upload': 300,
        '/api/v1/pdf': 300,

        # LLM/AI operations - medium timeout
        '/api/v1/chat': 120,
        '/api/v1/enhanced-chat': 120,
        '/api/v1/learning-path': 120,
        '/api/v1/learning-path-v2': 120,
        '/api/v1/multi-agent': 120,

        # RAG operations
        '/api/v1/rag': 90,

        # Default timeout for all other endpoints
        'default': 30
    }

    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.default_timeout = kwargs.get('default_timeout', 30)
        logger.info(f"TimeoutMiddleware initialized with default timeout: {self.default_timeout}s")

    def get_timeout_for_path(self, path: str) -> int:
        """
        Determine timeout for a given request path

        Args:
            path: Request path (e.g., "/api/v1/batch-upload/generate")

        Returns:
            Timeout in seconds
        """
        # Check if path matches any configured prefix
        for prefix, timeout in self.TIMEOUT_CONFIG.items():
            if prefix != 'default' and path.startswith(prefix):
                return timeout

        # Return default timeout
        return self.TIMEOUT_CONFIG.get('default', self.default_timeout)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with timeout enforcement
        """
        # Skip timeout for health checks and static files
        if request.url.path in ['/health', '/docs', '/redoc', '/openapi.json']:
            return await call_next(request)

        # Get timeout for this path
        timeout_seconds = self.get_timeout_for_path(request.url.path)

        # Record start time
        start_time = time.time()

        try:
            # Execute request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout_seconds
            )

            # Add timing headers
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            response.headers["X-Timeout-Config"] = str(timeout_seconds)

            # Log slow requests (>50% of timeout)
            if process_time > (timeout_seconds * 0.5):
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {process_time:.2f}s (timeout: {timeout_seconds}s)"
                )

            return response

        except TimeoutError:
            # Request exceeded timeout
            process_time = time.time() - start_time

            logger.error(
                f"Request timeout: {request.method} {request.url.path} "
                f"exceeded {timeout_seconds}s timeout (took {process_time:.2f}s)"
            )

            return JSONResponse(
                status_code=504,  # Gateway Timeout
                content={
                    "detail": f"Request timeout: exceeded {timeout_seconds}s limit",
                    "timeout_seconds": timeout_seconds,
                    "elapsed_seconds": round(process_time, 2),
                    "suggestion": (
                        "Bu işlem uzun sürüyor. "
                        "Lütfen daha küçük batch size kullanın veya "
                        "işlemi parçalara bölün."
                    )
                },
                headers={
                    "X-Timeout-Exceeded": "true",
                    "X-Timeout-Config": str(timeout_seconds),
                    "X-Elapsed-Time": f"{process_time:.3f}"
                }
            )

        except Exception as e:
            # Other errors - log and re-raise
            logger.error(f"Error processing request: {request.method} {request.url.path}: {e!s}")
            raise


def get_timeout_middleware(default_timeout: int = 30):
    """
    Factory function to create TimeoutMiddleware with custom default timeout

    Args:
        default_timeout: Default timeout in seconds for unconfigured paths

    Returns:
        TimeoutMiddleware class configured with default timeout
    """
    class ConfiguredTimeoutMiddleware(TimeoutMiddleware):
        def __init__(self, app):
            super().__init__(app, default_timeout=default_timeout)

    return ConfiguredTimeoutMiddleware


# Export
__all__ = ['TimeoutMiddleware', 'get_timeout_middleware']
