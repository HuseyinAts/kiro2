"""
Response Format Middleware
Automatic response formatting and standardization middleware
"""

import json
import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse

from .response_models import (
    TURKISH_MESSAGES,
    ErrorDetail,
    ErrorType,
    ResponseBuilder,
    ResponseMeta,
    ResponseStatus,
    get_status_code,
)
from .unified_config import get_unified_config


class ResponseFormatterMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically format all API responses into standardized format
    """

    def __init__(
        self,
        app,
        enable_auto_formatting: bool = True,
        include_server_info: bool = False,
        turkish_messages: bool = True,
        excluded_paths: list | None = None,
    ):
        super().__init__(app)
        self.enable_auto_formatting = enable_auto_formatting
        self.include_server_info = include_server_info
        self.turkish_messages = turkish_messages
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/health",
            "/health/",
            "/metrics",
            "/static",
        ]
        self.config = get_unified_config()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StarletteResponse:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time for processing time calculation
        start_time = time.time()

        try:
            # Call the actual endpoint
            response = await call_next(request)

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000

            # Skip formatting for excluded paths
            if self._should_skip_formatting(request.url.path):
                return response

            # Skip formatting if auto formatting is disabled
            if not self.enable_auto_formatting:
                return response

            # Format the response
            formatted_response = await self._format_response(
                request, response, request_id, processing_time
            )

            return formatted_response

        except HTTPException as e:
            # Handle FastAPI HTTPExceptions
            processing_time = (time.time() - start_time) * 1000
            return await self._format_http_exception(e, request_id, processing_time)

        except Exception as e:
            # Handle unexpected exceptions
            processing_time = (time.time() - start_time) * 1000
            return await self._format_internal_error(e, request_id, processing_time)

    def _should_skip_formatting(self, path: str) -> bool:
        """Check if path should skip response formatting"""
        return any(excluded in path for excluded in self.excluded_paths)

    async def _format_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        processing_time: float,
    ) -> JSONResponse:
        """Format successful response into standardized format"""

        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Try to parse JSON response
        try:
            if body:
                original_data = json.loads(body.decode())
            else:
                original_data = None
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Non-JSON response, wrap as string
            original_data = body.decode() if body else None

        # Check if response is already in our standard format
        if (
            isinstance(original_data, dict)
            and "success" in original_data
            and "status" in original_data
            and "message" in original_data
        ):
            # Already formatted, just add metadata if missing
            if "meta" not in original_data or not isinstance(
                original_data["meta"], dict
            ):
                original_data["meta"] = self._create_response_meta(
                    request_id, processing_time
                ).dict()
            else:
                # Update existing meta
                original_data["meta"].update(
                    {"request_id": request_id, "processing_time_ms": processing_time}
                )

            return JSONResponse(content=original_data, status_code=response.status_code)

        # Format into standardized response
        success_message = (
            self._get_message("success")
            if self.turkish_messages
            else "Operation completed successfully"
        )

        formatted_response = (
            ResponseBuilder()
            .success(success_message)
            .with_data(original_data)
            .with_meta(
                request_id=request_id,
                processing_time_ms=processing_time,
                api_version=self.config.app_version,
                server_info=self._get_server_info()
                if self.include_server_info
                else None,
            )
            .build()
        )

        return JSONResponse(
            content=formatted_response.dict(exclude_none=True),
            status_code=response.status_code,
        )

    async def _format_http_exception(
        self, exc: HTTPException, request_id: str, processing_time: float
    ) -> JSONResponse:
        """Format HTTPException into standardized error response"""

        # Determine error type based on status code
        error_type = self._get_error_type_from_status(exc.status_code)

        # Create error detail
        error_detail = ErrorDetail(code=error_type.value, message=str(exc.detail))

        # Get appropriate message
        if self.turkish_messages:
            message = self._get_turkish_error_message(exc.status_code, str(exc.detail))
        else:
            message = "Request failed"

        # Build error response
        error_response = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=request_id,
                processing_time_ms=processing_time,
                api_version=self.config.app_version,
                server_info=self._get_server_info()
                if self.include_server_info
                else None,
            )
            .build()
        )

        return JSONResponse(
            content=error_response.dict(exclude_none=True), status_code=exc.status_code
        )

    async def _format_internal_error(
        self, exc: Exception, request_id: str, processing_time: float
    ) -> JSONResponse:
        """Format internal server error into standardized response"""

        error_detail = ErrorDetail(
            code=ErrorType.INTERNAL_SERVER_ERROR.value,
            message="Internal server error occurred"
            if not self.config.debug
            else str(exc),
            details={"exception_type": type(exc).__name__}
            if self.config.debug
            else None,
        )

        message = (
            self._get_message("internal_error")
            if self.turkish_messages
            else "Internal server error"
        )

        error_response = (
            ResponseBuilder()
            .error(message)
            .with_errors([error_detail])
            .with_meta(
                request_id=request_id,
                processing_time_ms=processing_time,
                api_version=self.config.app_version,
                server_info=self._get_server_info()
                if self.include_server_info
                else None,
            )
            .build()
        )

        return JSONResponse(
            content=error_response.dict(exclude_none=True), status_code=500
        )

    def _create_response_meta(
        self, request_id: str, processing_time: float
    ) -> ResponseMeta:
        """Create response metadata"""
        return ResponseMeta(
            timestamp=datetime.now(),
            request_id=request_id,
            api_version=self.config.app_version,
            processing_time_ms=processing_time,
            server_info=self._get_server_info() if self.include_server_info else None,
        )

    def _get_server_info(self) -> dict[str, Any]:
        """Get server information for response metadata"""
        return {
            "environment": self.config.environment.value,
            "server_host": self.config.server.host,
            "server_port": self.config.server.port,
            "debug_mode": self.config.debug,
        }

    def _get_error_type_from_status(self, status_code: int) -> ErrorType:
        """Map HTTP status code to error type"""
        mapping = {
            400: ErrorType.VALIDATION_ERROR,
            401: ErrorType.AUTHENTICATION_ERROR,
            403: ErrorType.AUTHORIZATION_ERROR,
            404: ErrorType.NOT_FOUND_ERROR,
            422: ErrorType.BUSINESS_LOGIC_ERROR,
            429: ErrorType.RATE_LIMIT_ERROR,
            500: ErrorType.INTERNAL_SERVER_ERROR,
            502: ErrorType.EXTERNAL_SERVICE_ERROR,
            503: ErrorType.MAINTENANCE_ERROR,
        }
        return mapping.get(status_code, ErrorType.INTERNAL_SERVER_ERROR)

    def _get_message(self, key: str) -> str:
        """Get localized message"""
        return TURKISH_MESSAGES.get(key, "İşlem tamamlandı")

    def _get_turkish_error_message(self, status_code: int, detail: str) -> str:
        """Get appropriate Turkish error message based on status code"""
        message_mapping = {
            400: "validation_error",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            422: "validation_error",
            429: "rate_limit_exceeded",
            500: "internal_error",
            502: "external_service_error",
            503: "service_unavailable",
        }

        message_key = message_mapping.get(status_code, "error")
        message = self._get_message(message_key)

        # If detail contains Turkish text, use it
        if any(turkish_char in detail.lower() for turkish_char in "çğıöşü"):
            return detail

        return message


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request tracing and logging
    """

    def __init__(self, app, enable_logging: bool = True):
        super().__init__(app)
        self.enable_logging = enable_logging
        self.config = get_unified_config()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StarletteResponse:
        # Skip tracing for health checks and static files
        if self._should_skip_tracing(request.url.path):
            return await call_next(request)

        start_time = time.time()
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        # Log request
        if self.enable_logging:
            self._log_request(request, request_id)

        try:
            response = await call_next(request)

            # Log response
            if self.enable_logging:
                self._log_response(request, response, request_id, start_time)

            return response

        except Exception as e:
            # Log error
            if self.enable_logging:
                self._log_error(request, e, request_id, start_time)
            raise

    def _should_skip_tracing(self, path: str) -> bool:
        """Check if path should skip tracing"""
        skip_paths = ["/health", "/metrics", "/favicon.ico", "/static"]
        return any(skip_path in path for skip_path in skip_paths)

    def _log_request(self, request: Request, request_id: str):
        """Log incoming request"""
        import logging

        logger = logging.getLogger("api.request")

        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "content_type": request.headers.get("content-type"),
            },
        )

    def _log_response(
        self, request: Request, response: Response, request_id: str, start_time: float
    ):
        """Log response"""
        import logging

        logger = logging.getLogger("api.response")

        processing_time = (time.time() - start_time) * 1000

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "processing_time_ms": processing_time,
            },
        )

    def _log_error(
        self, request: Request, error: Exception, request_id: str, start_time: float
    ):
        """Log error"""
        import logging

        logger = logging.getLogger("api.error")

        processing_time = (time.time() - start_time) * 1000

        logger.error(
            "Request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "processing_time_ms": processing_time,
            },
            exc_info=True,
        )


class CORSResponseMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with response formatting integration
    """

    def __init__(
        self,
        app,
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
        allow_credentials: bool = False,
    ):
        super().__init__(app)
        self.config = get_unified_config()

        self.allow_origins = allow_origins or self.config.server.allowed_origins
        self.allow_methods = allow_methods or [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
            "PATCH",
        ]
        self.allow_headers = allow_headers or [
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "X-API-Version",
            "Accept-Language",
        ]
        self.allow_credentials = allow_credentials

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StarletteResponse:
        # Handle preflight requests
        if request.method == "OPTIONS":
            return self._create_preflight_response()

        # Process request
        response = await call_next(request)

        # Add CORS headers
        self._add_cors_headers(response, request)

        return response

    def _create_preflight_response(self) -> JSONResponse:
        """Create preflight response for OPTIONS requests"""
        response = JSONResponse(content={"message": "CORS preflight"})
        response.headers.update(self._get_cors_headers())
        return response

    def _add_cors_headers(self, response: Response, request: Request):
        """Add CORS headers to response"""
        cors_headers = self._get_cors_headers()

        # Check if origin is allowed
        origin = request.headers.get("origin")
        if origin and (self._is_origin_allowed(origin) or "*" in self.allow_origins):
            cors_headers["Access-Control-Allow-Origin"] = origin

        response.headers.update(cors_headers)

    def _get_cors_headers(self) -> dict[str, str]:
        """Get CORS headers"""
        return {
            "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allow_headers),
            "Access-Control-Allow-Credentials": str(self.allow_credentials).lower(),
            "Access-Control-Max-Age": "86400",  # 24 hours
        }

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in allowed origins list"""
        return origin in self.allow_origins


# Utility functions for manual response formatting
def format_success_response(
    data: Any = None,
    message: str = None,
    status_code: int = 200,
    request_id: str = None,
    turkish: bool = True,
) -> JSONResponse:
    """Manually format a success response"""

    if message is None:
        message = (
            TURKISH_MESSAGES["success"]
            if turkish
            else "Operation completed successfully"
        )

    response_data = (
        ResponseBuilder()
        .success(message)
        .with_data(data)
        .with_meta(
            request_id=request_id or str(uuid.uuid4()),
            api_version=get_unified_config().app_version,
        )
        .build()
    )

    return JSONResponse(
        content=response_data.dict(exclude_none=True), status_code=status_code
    )


def format_error_response(
    message: str = None,
    error_type: ErrorType = ErrorType.INTERNAL_SERVER_ERROR,
    details: dict[str, Any] = None,
    request_id: str = None,
    turkish: bool = True,
) -> JSONResponse:
    """Manually format an error response"""

    if message is None:
        message = TURKISH_MESSAGES["error"] if turkish else "An error occurred"

    error_detail = ErrorDetail(code=error_type.value, message=message, details=details)

    response_data = (
        ResponseBuilder()
        .error(message)
        .with_errors([error_detail])
        .with_meta(
            request_id=request_id or str(uuid.uuid4()),
            api_version=get_unified_config().app_version,
        )
        .build()
    )

    status_code = get_status_code(ResponseStatus.ERROR, error_type)

    return JSONResponse(
        content=response_data.dict(exclude_none=True), status_code=status_code
    )
