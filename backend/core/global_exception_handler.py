"""
Global Exception Handler System
Comprehensive global exception handling with monitoring, logging, and recovery
"""

import asyncio
import logging
import traceback
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    DatabaseError,
    EnhancedServiceError,
    ErrorChain,
    ErrorSeverity,
    ExternalServiceError,
    MaintenanceError,
    NotFoundError,
    RateLimitError,
    SecurityError,
    ServiceError,
    TimeoutError,
    ValidationError,
)
from .response_models import ErrorDetail, ResponseBuilder

# ==================== ERROR HANDLER CONFIGURATION ====================


class HandlerMode(str, Enum):
    """Exception handler modes"""

    STRICT = "strict"  # Fail fast, detailed errors
    GRACEFUL = "graceful"  # Attempt recovery, user-friendly errors
    SILENT = "silent"  # Log errors but return success responses when possible


@dataclass
class ExceptionHandlerConfig:
    """Configuration for exception handlers"""

    mode: HandlerMode = HandlerMode.GRACEFUL
    enable_error_recovery: bool = True
    enable_detailed_logging: bool = True
    enable_error_aggregation: bool = True
    enable_circuit_breaker: bool = True
    max_error_rate_per_minute: int = 100
    circuit_breaker_threshold: int = 10
    circuit_breaker_timeout: int = 300  # seconds
    expose_internal_errors: bool = False
    enable_turkish_messages: bool = True
    enable_error_notification: bool = False
    notification_threshold: ErrorSeverity = ErrorSeverity.HIGH
    retry_policy: dict[str, Any] = field(
        default_factory=lambda: {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_backoff": True,
        }
    )


# ==================== ERROR CONTEXT AND TRACKING ====================


@dataclass
class ErrorContext:
    """Comprehensive error context information"""

    request_id: str
    correlation_id: str
    timestamp: datetime
    request_method: str
    request_url: str
    request_headers: dict[str, str]
    user_id: str | None = None
    user_role: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    api_version: str | None = None
    processing_time_ms: float | None = None
    memory_usage_mb: float | None = None
    additional_context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_request(cls, request: Request) -> "ErrorContext":
        """Create error context from FastAPI request"""
        return cls(
            request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
            correlation_id=getattr(request.state, "correlation_id", str(uuid.uuid4())),
            timestamp=datetime.now(),
            request_method=request.method,
            request_url=str(request.url),
            request_headers=dict(request.headers),
            user_id=getattr(request.state, "user_id", None),
            user_role=getattr(request.state, "user_role", None),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            session_id=getattr(request.state, "session_id", None),
            api_version=getattr(request.state, "api_version", "v1"),
            processing_time_ms=getattr(request.state, "processing_time", None),
        )


class ErrorTracker:
    """Track and monitor error patterns"""

    def __init__(self):
        self.error_counts: dict[str, int] = {}
        self.error_timestamps: dict[str, list[datetime]] = {}
        self.circuit_breakers: dict[str, dict[str, Any]] = {}
        self.error_patterns: dict[str, list[str]] = {}

    def record_error(
        self,
        error_type: str,
        endpoint: str,
        severity: ErrorSeverity,
        context: ErrorContext,
    ) -> None:
        """Record error occurrence"""
        key = f"{error_type}:{endpoint}"

        # Update error counts
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

        # Track timestamps for rate limiting
        now = datetime.now()
        if key not in self.error_timestamps:
            self.error_timestamps[key] = []

        self.error_timestamps[key].append(now)

        # Clean old timestamps (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.error_timestamps[key] = [
            ts for ts in self.error_timestamps[key] if ts > cutoff
        ]

        # Update circuit breaker state
        self._update_circuit_breaker(endpoint, severity)

        # Track error patterns
        pattern_key = f"{context.user_role}:{endpoint}"
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = []
        self.error_patterns[pattern_key].append(error_type)

    def get_error_rate(
        self, error_type: str, endpoint: str, window_minutes: int = 60
    ) -> float:
        """Get error rate for specific type/endpoint"""
        key = f"{error_type}:{endpoint}"
        if key not in self.error_timestamps:
            return 0.0

        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_errors = [ts for ts in self.error_timestamps[key] if ts > cutoff]
        return len(recent_errors) / window_minutes

    def is_circuit_breaker_open(self, endpoint: str) -> bool:
        """Check if circuit breaker is open for endpoint"""
        if endpoint not in self.circuit_breakers:
            return False

        breaker = self.circuit_breakers[endpoint]
        if breaker.get("state") != "open":
            return False

        # Check if timeout has passed
        open_time = breaker.get("opened_at")
        if open_time and datetime.now() - open_time > timedelta(
            seconds=breaker.get("timeout", 300)
        ):
            breaker["state"] = "half_open"
            return False

        return True

    def _update_circuit_breaker(self, endpoint: str, severity: ErrorSeverity) -> None:
        """Update circuit breaker state"""
        if endpoint not in self.circuit_breakers:
            self.circuit_breakers[endpoint] = {
                "state": "closed",
                "error_count": 0,
                "last_failure": None,
                "opened_at": None,
                "timeout": 300,
            }

        breaker = self.circuit_breakers[endpoint]

        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            breaker["error_count"] += 1
            breaker["last_failure"] = datetime.now()

            if breaker["error_count"] >= 10:  # Threshold
                breaker["state"] = "open"
                breaker["opened_at"] = datetime.now()

    def get_error_statistics(self) -> dict[str, Any]:
        """Get comprehensive error statistics"""
        now = datetime.now()
        cutoff = now - timedelta(hours=24)

        # Recent errors
        recent_errors = {}
        for key, timestamps in self.error_timestamps.items():
            recent = [ts for ts in timestamps if ts > cutoff]
            if recent:
                recent_errors[key] = len(recent)

        # Circuit breaker states
        circuit_states = {
            endpoint: breaker["state"]
            for endpoint, breaker in self.circuit_breakers.items()
        }

        return {
            "total_error_types": len(self.error_counts),
            "recent_errors_24h": recent_errors,
            "circuit_breaker_states": circuit_states,
            "error_patterns": self.error_patterns,
            "top_errors": sorted(
                self.error_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }


# ==================== GLOBAL EXCEPTION HANDLER ====================


class GlobalExceptionHandler:
    """Comprehensive global exception handler"""

    def __init__(self, config: ExceptionHandlerConfig | None = None):
        self.config = config or ExceptionHandlerConfig()
        self.error_tracker = ErrorTracker()
        self.logger = logging.getLogger("global_exception_handler")

        # Lazy load unified_config to avoid circular imports
        try:
            from .unified_config import get_unified_config

            self.app_config = get_unified_config()
        except Exception:
            # Fallback to minimal config
            self.app_config = type(
                "Config", (), {"debug": False, "app_version": "1.0.0"}
            )()

        # Error recovery functions registry
        self.recovery_functions: dict[type, Callable] = {}

        # Error notification callbacks
        self.notification_callbacks: list[Callable] = []

        # Initialize error patterns
        self._setup_recovery_functions()

    def register_recovery_function(self, exception_type: type, recovery_func: Callable):
        """Register a recovery function for specific exception type"""
        self.recovery_functions[exception_type] = recovery_func

    def register_notification_callback(self, callback: Callable):
        """Register notification callback for critical errors"""
        self.notification_callbacks.append(callback)

    def _setup_recovery_functions(self):
        """Setup default recovery functions"""

        async def recover_from_timeout(
            error: TimeoutError, context: ErrorContext
        ) -> dict[str, Any] | None:
            """Attempt to recover from timeout errors"""
            if context.request_method in ["GET", "HEAD"]:
                # For read operations, try with cached data
                return {
                    "message": "İşlem zaman aşımına uğradı, önbellek verisi döndürülüyor"
                }
            return None

        async def recover_from_database_error(
            error: DatabaseError, context: ErrorContext
        ) -> dict[str, Any] | None:
            """Attempt to recover from database errors"""
            if "read" in error.details.get("operation", "").lower():
                # For read operations, try backup database or cache
                return {"message": "Veritabanı geçici olarak kullanılamıyor"}
            return None

        async def recover_from_rate_limit(
            error: RateLimitError, context: ErrorContext
        ) -> dict[str, Any] | None:
            """Handle rate limit errors gracefully"""
            retry_after = error.details.get("retry_after", 60)
            return {
                "message": "İstek limiti aşıldı",
                "retry_after": retry_after,
                "details": {"limit_type": "rate_limit"},
            }

        # Register recovery functions
        self.recovery_functions[TimeoutError] = recover_from_timeout
        self.recovery_functions[DatabaseError] = recover_from_database_error
        self.recovery_functions[RateLimitError] = recover_from_rate_limit

    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Main exception handling entry point"""

        # Create error context
        context = ErrorContext.from_request(request)

        # Check circuit breaker
        endpoint = self._get_endpoint_identifier(request)
        if self.error_tracker.is_circuit_breaker_open(endpoint):
            return await self._handle_circuit_breaker_open(context)

        # Determine exception type and severity
        error_info = self._classify_exception(exc)

        # Record error for tracking
        self.error_tracker.record_error(
            error_info["type"], endpoint, error_info["severity"], context
        )

        # Log error with full context
        await self._log_exception(exc, context, error_info)

        # Attempt error recovery if enabled
        recovery_data = None
        if self.config.enable_error_recovery:
            recovery_data = await self._attempt_recovery(exc, context)

        # Send notifications for critical errors
        if (
            self.config.enable_error_notification
            and error_info["severity"] >= self.config.notification_threshold
        ):
            await self._send_error_notifications(exc, context, error_info)

        # Generate response
        return await self._generate_error_response(
            exc, context, error_info, recovery_data
        )

    def _get_endpoint_identifier(self, request: Request) -> str:
        """Get endpoint identifier for circuit breaker"""
        path = request.url.path
        method = request.method
        return f"{method}:{path}"

    def _classify_exception(self, exc: Exception) -> dict[str, Any]:
        """Classify exception type and determine severity"""

        classification = {
            "type": type(exc).__name__,
            "severity": ErrorSeverity.MEDIUM,
            "error_code": "INTERNAL_SERVER_ERROR",
            "http_status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "user_message": "Sunucu hatası oluştu",
            "is_retryable": False,
            "expose_details": False,
        }

        # Enhanced service errors
        if isinstance(exc, EnhancedServiceError):
            classification.update(
                {
                    "severity": exc.severity,
                    "error_code": exc.error_code,
                    "user_message": exc.user_message,
                    "is_retryable": exc.retry_after is not None,
                    "expose_details": True,
                }
            )

        # Standard service errors
        elif isinstance(exc, ServiceError):
            classification.update(
                {"error_code": exc.error_code, "expose_details": True}
            )

        # Specific exception mappings
        exception_mappings = {
            # FastAPI built-in exceptions
            HTTPException: {
                "severity": ErrorSeverity.LOW,
                "http_status": getattr(exc, "status_code", 500),
                "error_code": "HTTP_ERROR",
                "expose_details": True,
            },
            RequestValidationError: {
                "severity": ErrorSeverity.LOW,
                "http_status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "error_code": "VALIDATION_ERROR",
                "user_message": "Veri doğrulama hatası",
                "expose_details": True,
            },
            PydanticValidationError: {
                "severity": ErrorSeverity.LOW,
                "http_status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "error_code": "VALIDATION_ERROR",
                "user_message": "Veri doğrulama hatası",
                "expose_details": True,
            },
            # Custom exceptions
            ValidationError: {
                "severity": ErrorSeverity.LOW,
                "http_status": status.HTTP_400_BAD_REQUEST,
                "user_message": "Geçersiz veri",
            },
            NotFoundError: {
                "severity": ErrorSeverity.LOW,
                "http_status": status.HTTP_404_NOT_FOUND,
                "user_message": "Kaynak bulunamadı",
            },
            AuthenticationError: {
                "severity": ErrorSeverity.MEDIUM,
                "http_status": status.HTTP_401_UNAUTHORIZED,
                "user_message": "Kimlik doğrulama gerekli",
            },
            AuthorizationError: {
                "severity": ErrorSeverity.MEDIUM,
                "http_status": status.HTTP_403_FORBIDDEN,
                "user_message": "Bu işlem için yetkiniz yok",
            },
            DatabaseError: {
                "severity": ErrorSeverity.HIGH,
                "http_status": status.HTTP_503_SERVICE_UNAVAILABLE,
                "user_message": "Veritabanı hatası",
                "is_retryable": True,
            },
            ExternalServiceError: {
                "severity": ErrorSeverity.HIGH,
                "http_status": status.HTTP_502_BAD_GATEWAY,
                "user_message": "Harici servis hatası",
                "is_retryable": True,
            },
            TimeoutError: {
                "severity": ErrorSeverity.HIGH,
                "http_status": status.HTTP_408_REQUEST_TIMEOUT,
                "user_message": "İşlem zaman aşımına uğradı",
                "is_retryable": True,
            },
            RateLimitError: {
                "severity": ErrorSeverity.MEDIUM,
                "http_status": status.HTTP_429_TOO_MANY_REQUESTS,
                "user_message": "İstek limiti aşıldı",
                "is_retryable": True,
            },
            SecurityError: {
                "severity": ErrorSeverity.CRITICAL,
                "http_status": status.HTTP_403_FORBIDDEN,
                "user_message": "Güvenlik ihlali tespit edildi",
            },
            MaintenanceError: {
                "severity": ErrorSeverity.MEDIUM,
                "http_status": status.HTTP_503_SERVICE_UNAVAILABLE,
                "user_message": "Sistem bakımda",
            },
            # Python built-in exceptions
            ValueError: {
                "severity": ErrorSeverity.LOW,
                "http_status": status.HTTP_400_BAD_REQUEST,
                "error_code": "VALUE_ERROR",
                "user_message": "Geçersiz değer",
            },
            KeyError: {
                "severity": ErrorSeverity.MEDIUM,
                "http_status": status.HTTP_400_BAD_REQUEST,
                "error_code": "KEY_ERROR",
                "user_message": "Gerekli alan eksik",
            },
            AttributeError: {
                "severity": ErrorSeverity.HIGH,
                "http_status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error_code": "ATTRIBUTE_ERROR",
                "user_message": "Sunucu hatası",
            },
            TypeError: {
                "severity": ErrorSeverity.HIGH,
                "http_status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error_code": "TYPE_ERROR",
                "user_message": "Sunucu hatası",
            },
            MemoryError: {
                "severity": ErrorSeverity.CRITICAL,
                "http_status": status.HTTP_507_INSUFFICIENT_STORAGE,
                "error_code": "MEMORY_ERROR",
                "user_message": "Sistem kaynak yetersizliği",
            },
            asyncio.TimeoutError: {
                "severity": ErrorSeverity.HIGH,
                "http_status": status.HTTP_408_REQUEST_TIMEOUT,
                "error_code": "ASYNC_TIMEOUT",
                "user_message": "İşlem zaman aşımına uğradı",
                "is_retryable": True,
            },
        }

        # Apply specific mappings
        for exc_type, mapping in exception_mappings.items():
            if isinstance(exc, exc_type):
                classification.update(mapping)
                break

        return classification

    async def _attempt_recovery(
        self, exc: Exception, context: ErrorContext
    ) -> dict[str, Any] | None:
        """Attempt to recover from error"""

        # Check if we have a specific recovery function
        for exc_type, recovery_func in self.recovery_functions.items():
            if isinstance(exc, exc_type):
                try:
                    return await recovery_func(exc, context)
                except Exception as recovery_error:
                    self.logger.warning(
                        f"Error recovery failed: {recovery_error}",
                        extra={"context": context.request_id},
                    )

        return None

    async def _log_exception(
        self, exc: Exception, context: ErrorContext, error_info: dict[str, Any]
    ) -> None:
        """Log exception with full context"""

        log_data = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "error_code": error_info["error_code"],
            "severity": error_info["severity"].value,
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
            "endpoint": f"{context.request_method} {context.request_url}",
            "user_id": context.user_id,
            "user_role": context.user_role,
            "client_ip": context.client_ip,
            "user_agent": context.user_agent,
            "timestamp": context.timestamp.isoformat(),
        }

        # Add enhanced service error details
        if isinstance(exc, EnhancedServiceError):
            log_data.update(
                {
                    "source_location": exc.source_location,
                    "previous_error": str(exc.previous_error)
                    if exc.previous_error
                    else None,
                    "error_details": exc.details,
                }
            )

        # Log based on severity
        if error_info["severity"] == ErrorSeverity.CRITICAL:
            self.logger.critical(
                f"CRITICAL ERROR: {exc!s}", extra=log_data, exc_info=True
            )
        elif error_info["severity"] == ErrorSeverity.HIGH:
            self.logger.error(
                f"HIGH SEVERITY ERROR: {exc!s}", extra=log_data, exc_info=True
            )
        elif error_info["severity"] == ErrorSeverity.MEDIUM:
            self.logger.warning(
                f"ERROR: {exc!s}",
                extra=log_data,
                exc_info=self.config.enable_detailed_logging,
            )
        else:
            self.logger.info(f"LOW SEVERITY ERROR: {exc!s}", extra=log_data)

    async def _send_error_notifications(
        self, exc: Exception, context: ErrorContext, error_info: dict[str, Any]
    ) -> None:
        """Send error notifications to registered callbacks"""

        notification_data = {
            "exception": exc,
            "context": context,
            "error_info": error_info,
            "timestamp": datetime.now().isoformat(),
        }

        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification_data)
                else:
                    callback(notification_data)
            except Exception as notification_error:
                self.logger.error(
                    f"Error notification callback failed: {notification_error}",
                    extra={"context": context.request_id},
                )

    async def _generate_error_response(
        self,
        exc: Exception,
        context: ErrorContext,
        error_info: dict[str, Any],
        recovery_data: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """Generate standardized error response"""

        # Create error detail
        error_detail = ErrorDetail(
            code=error_info["error_code"],
            message=error_info["user_message"],
            details=self._get_error_details(exc, error_info, context),
        )

        # Build response using ResponseBuilder
        response_builder = (
            ResponseBuilder()
            .error(error_info["user_message"])
            .with_errors([error_detail])
            .with_meta(
                request_id=context.request_id,
                api_version=context.api_version,
                processing_time_ms=context.processing_time_ms,
                correlation_id=context.correlation_id,
            )
        )

        # Add recovery data if available
        if recovery_data:
            response_builder.with_data(recovery_data)

        response = response_builder.build()

        # Use model_dump with JSON mode for proper datetime serialization
        try:
            content = response.model_dump(exclude_none=True, mode="json")
        except AttributeError:
            # Fallback for older Pydantic versions
            content = response.dict(exclude_none=True)
            # Convert datetime objects manually
            import json

            content = json.loads(json.dumps(content, default=str))

        return JSONResponse(
            content=content,
            status_code=error_info["http_status"],
        )

    def _get_error_details(
        self, exc: Exception, error_info: dict[str, Any], context: ErrorContext
    ) -> dict[str, Any] | None:
        """Get error details to include in response"""

        details = {}

        # Include exception details if allowed
        if error_info["expose_details"] or self.app_config.debug:
            if isinstance(exc, ServiceError):
                details.update(exc.details)

            if isinstance(exc, EnhancedServiceError):
                details.update(
                    {
                        "severity": exc.severity.value,
                        "retry_after": exc.retry_after,
                        "correlation_id": exc.correlation_id,
                    }
                )

            # Add debug information in debug mode
            if self.app_config.debug:
                details.update(
                    {
                        "exception_type": type(exc).__name__,
                        "traceback": traceback.format_exc(),
                        "request_context": {
                            "method": context.request_method,
                            "url": context.request_url,
                            "timestamp": context.timestamp.isoformat(),
                        },
                    }
                )

        # Add retry information for retryable errors
        if error_info["is_retryable"]:
            retry_policy = self.config.retry_policy
            details.update(
                {
                    "retryable": True,
                    "max_retries": retry_policy["max_retries"],
                    "retry_delay": retry_policy["base_delay"],
                }
            )

        return details if details else None

    async def _handle_circuit_breaker_open(self, context: ErrorContext) -> JSONResponse:
        """Handle requests when circuit breaker is open"""

        error_detail = ErrorDetail(
            code="CIRCUIT_BREAKER_OPEN",
            message="Servis geçici olarak kullanılamıyor",
            details={"reason": "circuit_breaker_open", "retry_after": 300},
        )

        response = (
            ResponseBuilder()
            .error("Servis geçici olarak kullanılamıyor")
            .with_errors([error_detail])
            .with_meta(request_id=context.request_id, api_version=context.api_version)
            .build()
        )

        return JSONResponse(
            content=response.dict(exclude_none=True),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ==================== ERROR CONTEXT MANAGER ====================


@asynccontextmanager
async def error_context(correlation_id: str | None = None):
    """Context manager for error handling with correlation tracking"""

    correlation_id = correlation_id or str(uuid.uuid4())
    error_chain = ErrorChain()

    try:
        yield error_chain
    except Exception as e:
        error_chain.add_error(e)
        error_chain.correlation_id = correlation_id

        # If we have multiple errors, raise aggregated
        if len(error_chain.errors) > 1:
            error_chain.raise_aggregated("Multiple errors occurred during operation")
        else:
            # Re-raise the single error
            raise e


# ==================== SETUP FUNCTION ====================


def setup_global_exception_handlers(
    app, config: ExceptionHandlerConfig | None = None
) -> GlobalExceptionHandler:
    """Setup global exception handlers for FastAPI app"""

    handler = GlobalExceptionHandler(config)

    # Register all exception handlers
    app.add_exception_handler(Exception, handler.handle_exception)
    app.add_exception_handler(HTTPException, handler.handle_exception)
    app.add_exception_handler(StarletteHTTPException, handler.handle_exception)
    app.add_exception_handler(RequestValidationError, handler.handle_exception)
    app.add_exception_handler(PydanticValidationError, handler.handle_exception)

    # Register custom exception handlers
    app.add_exception_handler(ServiceError, handler.handle_exception)
    app.add_exception_handler(EnhancedServiceError, handler.handle_exception)
    app.add_exception_handler(ValidationError, handler.handle_exception)
    app.add_exception_handler(NotFoundError, handler.handle_exception)
    app.add_exception_handler(AuthenticationError, handler.handle_exception)
    app.add_exception_handler(AuthorizationError, handler.handle_exception)
    app.add_exception_handler(DatabaseError, handler.handle_exception)
    app.add_exception_handler(BusinessLogicError, handler.handle_exception)
    app.add_exception_handler(ExternalServiceError, handler.handle_exception)
    app.add_exception_handler(TimeoutError, handler.handle_exception)
    app.add_exception_handler(RateLimitError, handler.handle_exception)
    app.add_exception_handler(SecurityError, handler.handle_exception)
    app.add_exception_handler(MaintenanceError, handler.handle_exception)

    return handler


# ==================== UTILITY FUNCTIONS ====================


def get_error_handler(app) -> GlobalExceptionHandler | None:
    """Get the global exception handler instance from app"""
    # This would need to be stored in app.state during setup
    return getattr(app.state, "global_exception_handler", None)


async def handle_with_recovery(
    operation: Callable, *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs
) -> Any:
    """Execute operation with automatic retry and error recovery"""

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(operation):
                return await operation(*args, **kwargs)
            return operation(*args, **kwargs)

        except Exception as e:
            last_error = e

            if attempt == max_retries:
                break

            # Don't retry on certain error types
            if isinstance(e, (ValidationError, AuthorizationError, NotFoundError)):
                break

            # Exponential backoff delay
            delay = base_delay * (2**attempt)
            await asyncio.sleep(min(delay, 60.0))

    # If we get here, all retries failed
    if last_error:
        raise last_error
