"""
Request Tracking Middleware - P1.9
Automatically tracks request IDs and adds context to all logs

Features:
- Generates unique request ID for each request
- Binds request ID to context for all logs
- Adds request ID to response headers
- Tracks request duration
- Logs request/response details
"""

import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.learning_path_logger import (
    get_learning_path_logger,
    request_id_var,
)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track requests with unique IDs

    Adds X-Request-ID header to all requests/responses
    Binds request ID to logging context
    Logs request details and performance
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_learning_path_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with tracking

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with X-Request-ID header
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Bind request ID to context
        request_id_var.set(request_id)

        # Track request start
        start_time = time.time()

        # Log request received
        self.logger.info(
            "request_received",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log request completed
            self.logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_seconds=duration,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log slow requests
            if duration > 5.0:
                self.logger.warning(
                    "slow_request",
                    method=request.method,
                    path=request.url.path,
                    duration_seconds=duration,
                    threshold_seconds=5.0,
                )

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log request error
            self.logger.error(
                "request_failed",
                error=e,
                method=request.method,
                path=request.url.path,
                duration_seconds=duration,
            )

            raise

        finally:
            # Clear context after request
            request_id_var.set(None)
