"""
Sentry Error Tracking Middleware for Kiro2 Platform
Sprint 12: Advanced Error Context and Categorization

Features:
- Automatic error capture
- Performance transaction tracking
- Request/response context
- User context enrichment
- Business operation tagging
- Error categorization
- Breadcrumbs for debugging
"""
import time
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk
from sentry_sdk import start_transaction, configure_scope

logger = logging.getLogger(__name__)


class SentryErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Advanced Sentry Error Tracking Middleware

    Features:
    - Automatic error capture for all requests
    - Performance transaction tracking
    - Request/response metadata
    - User context enrichment
    - Business operation tagging
    - Error categorization
    """

    def __init__(self, app, excluded_paths: list = None):
        """
        Initialize Sentry middleware

        Args:
            app: FastAPI application
            excluded_paths: Paths to exclude from tracking
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with Sentry error tracking

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with error tracking
        """
        # Skip tracking for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Start Sentry transaction for performance monitoring
        transaction_name = f"{request.method} {request.url.path}"

        with start_transaction(op="http.server", name=transaction_name) as transaction:
            # Record request start time
            start_time = time.time()

            # Add request context to Sentry scope
            with configure_scope() as scope:
                try:
                    # Add request attributes
                    self._add_request_context(scope, request)

                    # Add breadcrumb for request start
                    sentry_sdk.add_breadcrumb(
                        message=f"HTTP Request: {request.method} {request.url.path}",
                        category="http",
                        level="info",
                        data={
                            "method": request.method,
                            "url": str(request.url),
                            "client_ip": request.client.host if request.client else "unknown"
                        }
                    )

                    # Process request
                    response = await call_next(request)

                    # Calculate duration
                    duration_ms = (time.time() - start_time) * 1000

                    # Add response attributes
                    self._add_response_context(scope, transaction, response, duration_ms)

                    # Add breadcrumb for successful response
                    sentry_sdk.add_breadcrumb(
                        message=f"HTTP Response: {response.status_code}",
                        category="http",
                        level="info",
                        data={
                            "status_code": response.status_code,
                            "duration_ms": duration_ms
                        }
                    )

                    # Set transaction status
                    if response.status_code >= 500:
                        transaction.set_status("internal_error")
                    elif response.status_code >= 400:
                        transaction.set_status("invalid_argument")
                    else:
                        transaction.set_status("ok")

                    return response

                except Exception as e:
                    # Record exception duration
                    duration_ms = (time.time() - start_time) * 1000

                    # Add error context
                    scope.set_tag("error", True)
                    scope.set_tag("error_type", type(e).__name__)
                    scope.set_extra("request_duration_ms", duration_ms)

                    # Add breadcrumb for error
                    sentry_sdk.add_breadcrumb(
                        message=f"Request failed: {type(e).__name__}",
                        category="error",
                        level="error",
                        data={
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "duration_ms": duration_ms
                        }
                    )

                    # Capture exception in Sentry
                    sentry_sdk.capture_exception(e)

                    # Set transaction status
                    transaction.set_status("internal_error")

                    # Re-raise exception
                    raise

    def _add_request_context(self, scope, request: Request):
        """
        Add request context to Sentry scope

        Args:
            scope: Sentry scope
            request: FastAPI request
        """
        # HTTP request attributes
        scope.set_tag("http.method", request.method)
        scope.set_tag("http.url", str(request.url))
        scope.set_tag("http.path", request.url.path)

        # Client information
        if request.client:
            scope.set_tag("client.ip", request.client.host)

        # User-Agent
        user_agent = request.headers.get("user-agent", "unknown")
        scope.set_tag("user_agent", user_agent[:100])  # Limit length

        # Request ID
        request_id = request.headers.get("x-request-id", "unknown")
        scope.set_tag("request_id", request_id)

        # User context (if authenticated)
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user
            sentry_sdk.set_user({
                "id": str(user.id),
                "username": getattr(user, "username", None),
                "role": getattr(user, "role", None),
            })

            # Add user tags
            scope.set_tag("user.role", user.role)
            if hasattr(user, "is_premium"):
                scope.set_tag("user.is_premium", user.is_premium)

        # Business operation context (if available)
        if hasattr(request.state, "business_operation"):
            scope.set_tag("business.operation", request.state.business_operation)

        # Query parameters (sanitized)
        if request.query_params:
            query_dict = dict(request.query_params)
            # Sanitize sensitive parameters
            for sensitive in ["password", "token", "secret", "api_key"]:
                if sensitive in query_dict:
                    query_dict[sensitive] = "[Filtered]"
            scope.set_context("query_params", query_dict)

    def _add_response_context(self, scope, transaction, response: Response, duration_ms: float):
        """
        Add response context to Sentry scope

        Args:
            scope: Sentry scope
            transaction: Sentry transaction
            response: FastAPI response
            duration_ms: Request duration in milliseconds
        """
        # HTTP response attributes
        scope.set_tag("http.status_code", response.status_code)
        scope.set_extra("response.duration_ms", duration_ms)

        # Response size
        if "content-length" in response.headers:
            scope.set_extra("response.size_bytes", int(response.headers["content-length"]))

        # Performance classification
        if duration_ms < 100:
            performance = "fast"
        elif duration_ms < 500:
            performance = "normal"
        elif duration_ms < 2000:
            performance = "slow"
        else:
            performance = "very_slow"

        scope.set_tag("performance", performance)
        transaction.set_tag("performance", performance)

        # Add span for slow requests
        if duration_ms > 1000:
            scope.set_tag("slow_request", True)


# Business operation decorator
def track_business_operation(operation_name: str):
    """
    Decorator to track business operations in Sentry

    Args:
        operation_name: Name of the business operation

    Example:
        @track_business_operation("exam_submission")
        async def submit_exam(exam_id: str, user_id: str):
            pass
    """
    def decorator(func):
        import functools
        import inspect

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with start_transaction(op="business", name=operation_name) as transaction:
                transaction.set_tag("business.operation", operation_name)

                # Add breadcrumb
                sentry_sdk.add_breadcrumb(
                    message=f"Business operation: {operation_name}",
                    category="business",
                    level="info"
                )

                try:
                    result = await func(*args, **kwargs)
                    transaction.set_status("ok")
                    return result
                except Exception as e:
                    transaction.set_status("internal_error")
                    transaction.set_tag("error", True)
                    transaction.set_tag("error_type", type(e).__name__)
                    sentry_sdk.capture_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with start_transaction(op="business", name=operation_name) as transaction:
                transaction.set_tag("business.operation", operation_name)

                # Add breadcrumb
                sentry_sdk.add_breadcrumb(
                    message=f"Business operation: {operation_name}",
                    category="business",
                    level="info"
                )

                try:
                    result = func(*args, **kwargs)
                    transaction.set_status("ok")
                    return result
                except Exception as e:
                    transaction.set_status("internal_error")
                    transaction.set_tag("error", True)
                    transaction.set_tag("error_type", type(e).__name__)
                    sentry_sdk.capture_exception(e)
                    raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Error category utilities
ERROR_CATEGORIES = {
    # Database errors
    "DatabaseError": "database",
    "IntegrityError": "database",
    "OperationalError": "database",
    "DataError": "database",

    # Network errors
    "ConnectionError": "network",
    "TimeoutError": "network",
    "ConnectTimeout": "network",
    "ReadTimeout": "network",

    # Authentication/Authorization
    "AuthenticationError": "auth",
    "PermissionError": "auth",
    "Unauthorized": "auth",
    "Forbidden": "auth",

    # Validation errors
    "ValidationError": "validation",
    "ValueError": "validation",
    "SchemaError": "validation",

    # HTTP errors
    "HTTPException": "http",
    "RequestException": "http",

    # Business logic errors
    "InsufficientFundsError": "business",
    "ExamNotFoundError": "business",
    "QuestionNotFoundError": "business",

    # Data errors
    "KeyError": "data",
    "TypeError": "data",
    "AttributeError": "data",
    "IndexError": "data",
}


def get_error_category(error: Exception) -> str:
    """
    Get error category for an exception

    Args:
        error: Exception

    Returns:
        Error category string
    """
    error_type = type(error).__name__
    return ERROR_CATEGORIES.get(error_type, "other")


def capture_categorized_error(
    error: Exception,
    user_id: Optional[str] = None,
    operation: Optional[str] = None,
    **extra_context
):
    """
    Capture an error with automatic categorization

    Args:
        error: Exception to capture
        user_id: User ID (if applicable)
        operation: Business operation name
        **extra_context: Additional context
    """
    with configure_scope() as scope:
        # Add error category
        category = get_error_category(error)
        scope.set_tag("error_category", category)

        # Add user context
        if user_id:
            sentry_sdk.set_user({"id": user_id})

        # Add business operation
        if operation:
            scope.set_tag("business.operation", operation)

        # Add extra context
        for key, value in extra_context.items():
            scope.set_extra(key, value)

        # Capture exception
        sentry_sdk.capture_exception(error)


if __name__ == "__main__":
    print("=" * 80)
    print("SENTRY ERROR TRACKING MIDDLEWARE TEST")
    print("=" * 80)
    print("\n[OK] Middleware module loaded successfully")
    print("Features:")
    print("  - Automatic error capture")
    print("  - Performance transaction tracking")
    print("  - Request/response context")
    print("  - User context enrichment")
    print("  - Business operation tagging")
    print("  - Error categorization")
    print("  - Breadcrumbs for debugging")
