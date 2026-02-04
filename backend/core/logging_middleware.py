"""
Logging Middleware for FastAPI
Request/Response logging functionality
"""
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/Response logging middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url}")

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {response.status_code} "
            f"Time: {process_time:.3f}s "
            f"Path: {request.url.path}"
        )

        return response


def setup_logging_middleware(app) -> None:
    """Setup logging middleware for FastAPI app"""
    app.add_middleware(LoggingMiddleware)
    logger.info("Logging middleware setup completed")
