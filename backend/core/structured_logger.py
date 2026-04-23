"""
Structured Logger for Application
Enhanced with structlog for better observability and performance monitoring
"""

import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

import structlog
from structlog.types import EventDict, Processor

# ==================== CONFIGURATION ====================


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to all log entries"""
    event_dict.setdefault("app", "kiro2-backend")
    event_dict.setdefault("environment", os.getenv("ENVIRONMENT", "production"))
    return event_dict


def censor_sensitive_data(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """Censor sensitive information from logs"""
    sensitive_keys = {
        "password",
        "token",
        "secret",
        "api_key",
        "authorization",
        "credit_card",
        "ssn",
        "private_key",
        "şifre",
        "parola",
    }

    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = "***REDACTED***"

    return event_dict


def setup_structlog(
    level: str = "INFO", json_logs: bool = None, dev_mode: bool = None
) -> None:
    """
    Configure structlog for the application

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Output JSON format (None = auto-detect from env)
        dev_mode: Enable development mode (None = auto-detect from env)
    """
    # Auto-detect settings from environment
    if json_logs is None:
        json_logs = os.getenv("LOG_FORMAT", "json").lower() == "json"

    if dev_mode is None:
        dev_mode = os.getenv("ENVIRONMENT", "production").lower() in [
            "development",
            "dev",
            "local",
        ]

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    # Build processor chain
    processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        censor_sensitive_data,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Windows compatibility: disable colors on Windows to avoid [Errno 22]
    import platform
    is_windows = platform.system() == "Windows"

    if dev_mode:
        # Development: Colored console output (disabled on Windows)
        processors.append(structlog.dev.ConsoleRenderer(colors=not is_windows))
    # Production: JSON output
    elif json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=False))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# ==================== LOGGER CLASS ====================


class StructuredLogger:
    """
    Enhanced structured logger with structlog

    Backward compatible with old API while providing new structlog features
    """

    def __init__(self, name: str, level: str = "INFO"):
        self.name = name
        self.level = level
        self.logger = structlog.get_logger(name)
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs) -> "StructuredLogger":
        """Bind context that will be included in all subsequent logs"""
        self._context.update(kwargs)
        self.logger = self.logger.bind(**kwargs)
        return self

    def unbind(self, *keys) -> "StructuredLogger":
        """Remove context keys"""
        for key in keys:
            self._context.pop(key, None)
        self.logger = structlog.get_logger(self.name)
        if self._context:
            self.logger = self.logger.bind(**self._context)
        return self

    def info(self, message: str, extra: dict[str, Any] | None = None, **kwargs):
        """
        Log info message

        Args:
            message: Event name/message
            extra: Backward compatible extra dict
            **kwargs: Additional structured data
        """
        if extra:
            kwargs.update(extra)
        self.logger.info(message, **kwargs)

    def error(self, message: str, extra: dict[str, Any] | None = None, **kwargs):
        """Log error message"""
        if extra:
            kwargs.update(extra)
        self.logger.error(message, **kwargs)

    def warning(self, message: str, extra: dict[str, Any] | None = None, **kwargs):
        """Log warning message"""
        if extra:
            kwargs.update(extra)
        self.logger.warning(message, **kwargs)

    def debug(self, message: str, extra: dict[str, Any] | None = None, **kwargs):
        """Log debug message"""
        if extra:
            kwargs.update(extra)
        self.logger.debug(message, **kwargs)

    def critical(self, message: str, extra: dict[str, Any] | None = None, **kwargs):
        """Log critical message"""
        if extra:
            kwargs.update(extra)
        self.logger.critical(message, **kwargs)

    def exception(
        self,
        message: str,
        extra: dict[str, Any] | None = None,
        exc_info: bool = True,
        **kwargs,
    ):
        """Log exception with traceback"""
        if extra:
            kwargs.update(extra)
        self.logger.exception(message, exc_info=exc_info, **kwargs)

    # ==================== CONVENIENCE METHODS ====================

    def log_request(
        self,
        request_id: str,
        endpoint: str,
        method: str = "POST",
        profile: dict[str, Any] | None = None,
        **kwargs,
    ):
        """
        Log API request with structured data

        Args:
            request_id: Unique request identifier
            endpoint: API endpoint path
            method: HTTP method
            profile: Student profile or request payload
            **kwargs: Additional context

        Example:
            logger.log_request(
                request_id="abc-123",
                endpoint="/api/youtube/recommendations",
                method="POST",
                profile={"goals": ["TYT Matematik"], "currentLevel": {"matematik": 50}}
            )
        """
        log_data = {
            "request_id": request_id,
            "endpoint": endpoint,
            "method": method,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if profile:
            log_data["profile"] = profile

        log_data.update(kwargs)

        self.info("api_request_started", **log_data)

    def log_response(
        self,
        request_id: str,
        endpoint: str,
        status: int,
        response_time: float,
        cache_hit: bool | None = None,
        **kwargs,
    ):
        """
        Log API response with timing and cache information

        Args:
            request_id: Unique request identifier
            endpoint: API endpoint path
            status: HTTP status code
            response_time: Response time in milliseconds
            cache_hit: Whether response was served from cache
            **kwargs: Additional context (e.g., video_count, error_message)

        Example:
            logger.log_response(
                request_id="abc-123",
                endpoint="/api/youtube/recommendations",
                status=200,
                response_time=1234.5,
                cache_hit=True,
                video_count=15
            )
        """
        log_data = {
            "request_id": request_id,
            "endpoint": endpoint,
            "status": status,
            "response_time": response_time,
            "response_time_ms": response_time,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if cache_hit is not None:
            log_data["cache_hit"] = cache_hit

        log_data.update(kwargs)

        # Log as info for success, warning for client errors, error for server errors
        if status < 400:
            self.info("api_response_success", **log_data)
        elif status < 500:
            self.warning("api_response_client_error", **log_data)
        else:
            self.error("api_response_server_error", **log_data)

    def log_error_context(
        self,
        error_type: str,
        error_message: str,
        context: str,
        request_id: str | None = None,
        stack_trace: str | None = None,
        **kwargs,
    ):
        """
        Log error with full context and stack trace

        Args:
            error_type: Type of error (e.g., "VideoAPIError", "CacheError")
            error_message: Error message
            context: Context where error occurred
            request_id: Optional unique request ID
            stack_trace: Optional stack trace string
            **kwargs: Additional context data

        Example:
            logger.log_error_context(
                error_type="YouTubeAPIError",
                error_message="Rate limit exceeded",
                context="video_discovery",
                request_id="abc-123",
                stack_trace=traceback.format_exc(),
                quota_remaining=0
            )
        """
        log_data = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if request_id:
            log_data["request_id"] = request_id

        if stack_trace:
            log_data["stack_trace"] = stack_trace

        log_data.update(kwargs)

        self.error("error_with_context", **log_data)


# ==================== COMMON PATTERNS ====================


def log_exam_event(
    logger: StructuredLogger,
    event_type: str,
    sinav_id: int,
    ogrenci_id: int,
    sinav_tipi: str | None = None,
    **kwargs,
):
    """
    Log exam-related events with consistent structure

    Example:
        log_exam_event(
            logger,
            "sinav_olusturuldu",
            sinav_id=123,
            ogrenci_id=456,
            sinav_tipi="tyt",
            soru_sayisi=40
        )
    """
    logger.info(
        event_type,
        sinav_id=sinav_id,
        ogrenci_id=ogrenci_id,
        sinav_tipi=sinav_tipi,
        timestamp=datetime.now(UTC).isoformat(),
        **kwargs,
    )


def log_api_request(
    logger: StructuredLogger,
    method: str,
    path: str,
    user_id: int | None = None,
    request_id: str | None = None,
    **kwargs,
):
    """
    Log API request with consistent structure

    Args:
        logger: StructuredLogger instance
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path
        user_id: Optional user ID
        request_id: Optional unique request ID for tracing
        **kwargs: Additional context (e.g., profile, query_params)

    Example:
        log_api_request(
            logger,
            method="POST",
            path="/api/youtube/recommendations",
            request_id="abc-123",
            profile={"goals": ["TYT Matematik"]}
        )
    """
    logger.info(
        "api_request",
        method=method,
        path=path,
        endpoint=path,  # Alias for compatibility
        user_id=user_id,
        request_id=request_id,
        timestamp=datetime.now(UTC).isoformat(),
        **kwargs,
    )


def log_api_response(
    logger: StructuredLogger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: str | None = None,
    cache_hit: bool | None = None,
    **kwargs,
):
    """
    Log API response with timing and cache information

    Args:
        logger: StructuredLogger instance
        method: HTTP method
        path: API endpoint path
        status_code: HTTP status code
        duration_ms: Response time in milliseconds
        request_id: Optional unique request ID for tracing
        cache_hit: Whether response was served from cache
        **kwargs: Additional context

    Example:
        log_api_response(
            logger,
            method="POST",
            path="/api/youtube/recommendations",
            status_code=200,
            duration_ms=1234.5,
            request_id="abc-123",
            cache_hit=True,
            video_count=15
        )
    """
    log_data = {
        "method": method,
        "path": path,
        "endpoint": path,  # Alias for compatibility
        "status": status_code,
        "status_code": status_code,
        "response_time": duration_ms,
        "response_time_ms": duration_ms,
        "duration_ms": duration_ms,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    if request_id:
        log_data["request_id"] = request_id

    if cache_hit is not None:
        log_data["cache_hit"] = cache_hit

    log_data.update(kwargs)

    logger.info("api_response", **log_data)


def log_database_query(
    logger: StructuredLogger, operation: str, table: str, duration_ms: float, **kwargs
):
    """Log database query performance"""
    logger.debug(
        "database_query",
        operation=operation,
        table=table,
        duration_ms=duration_ms,
        **kwargs,
    )


def log_cache_operation(
    logger: StructuredLogger,
    operation: str,
    cache_key: str,
    hit: bool | None = None,
    **kwargs,
):
    """Log cache operations"""
    logger.debug(
        "cache_operation", operation=operation, cache_key=cache_key, hit=hit, **kwargs
    )


def log_error_with_context(
    logger: StructuredLogger,
    error: Exception,
    context: str,
    request_id: str | None = None,
    include_stack_trace: bool = True,
    **kwargs,
):
    """
    Log error with rich context and stack trace

    Args:
        logger: StructuredLogger instance
        error: Exception object
        context: Context description (e.g., "video_discovery", "cache_operation")
        request_id: Optional unique request ID for tracing
        include_stack_trace: Whether to include full stack trace
        **kwargs: Additional context data

    Example:
        try:
            # some operation
        except Exception as e:
            log_error_with_context(
                logger,
                error=e,
                context="video_recommendation_service",
                request_id="abc-123",
                student_profile=profile
            )
    """
    import traceback

    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    if request_id:
        error_data["request_id"] = request_id

    if include_stack_trace:
        error_data["stack_trace"] = traceback.format_exc()

    error_data.update(kwargs)

    logger.error("error_occurred", **error_data)


# ==================== PUBLIC API ====================


def get_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """
    Get structured logger instance

    Args:
        name: Logger name (typically __name__)
        level: Log level

    Returns:
        StructuredLogger instance

    Example:
        logger = get_logger(__name__)
        logger.info("user_login", user_id=123, success=True)
    """
    return StructuredLogger(name, level)


def get_structured_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """Alias for get_logger - backward compatibility"""
    return get_logger(name, level)


# ==================== INITIALIZATION ====================

# Initialize structlog on module import
try:
    setup_structlog(
        level=os.getenv("LOG_LEVEL", "INFO"),
        json_logs=None,  # Auto-detect
        dev_mode=None,  # Auto-detect
    )
except Exception:
    # Fallback to basic configuration if structlog setup fails
    logging.basicConfig(level=logging.INFO)


# Default application logger
app_logger = get_logger("app")


# ==================== EXPORTS ====================

__all__ = [
    # Core classes
    "StructuredLogger",
    # Factory functions
    "get_logger",
    "get_structured_logger",
    "setup_structlog",
    # Helper functions
    "log_exam_event",
    "log_api_request",
    "log_api_response",
    "log_database_query",
    "log_cache_operation",
    "log_error_with_context",
    # Default logger
    "app_logger",
]
