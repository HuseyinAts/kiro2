"""
Learning Path Enhanced Logger - P1.9
Error Tracking & Structured Logging for Learning Path Operations

Features:
- Request ID tracking (correlation across services)
- Student context binding
- Path context binding
- Error categorization
- Performance timing
- User journey tracking
"""

import uuid
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextvars import ContextVar
from enum import Enum

from core.structured_logger import get_logger

# ============================================================================
# Context Variables for Request Tracking
# ============================================================================

# Request ID for correlation across logs
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Student ID for user journey tracking
student_id_var: ContextVar[Optional[str]] = ContextVar("student_id", default=None)

# Learning Path ID for operation tracking
path_id_var: ContextVar[Optional[str]] = ContextVar("path_id", default=None)


# ============================================================================
# Error Categories
# ============================================================================


class ErrorCategory(str, Enum):
    """Error categories for better tracking and alerting"""

    # External API errors
    YOUTUBE_API_ERROR = "youtube_api_error"
    LLM_SERVICE_ERROR = "llm_service_error"
    REDIS_ERROR = "redis_error"
    DATABASE_ERROR = "database_error"

    # Business logic errors
    INVALID_INPUT = "invalid_input"
    VALIDATION_ERROR = "validation_error"
    PROFILE_NOT_FOUND = "profile_not_found"
    PATH_NOT_FOUND = "path_not_found"
    QUIZ_NOT_FOUND = "quiz_not_found"

    # Authorization errors
    AUTH_FAILED = "auth_failed"
    PERMISSION_DENIED = "permission_denied"
    OWNERSHIP_VIOLATION = "ownership_violation"

    # System errors
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CACHE_ERROR = "cache_error"

    # AI/ML errors
    AI_AGENT_ERROR = "ai_agent_error"
    RECOMMENDATION_ERROR = "recommendation_error"
    ADAPTATION_ERROR = "adaptation_error"

    # Unknown
    UNKNOWN_ERROR = "unknown_error"


# ============================================================================
# Enhanced Logger Class
# ============================================================================


class LearningPathLogger:
    """
    Enhanced logger for Learning Path operations with context tracking

    Features:
    - Automatic request ID generation and tracking
    - Student context binding
    - Path context binding
    - Error categorization
    - Performance timing
    - User journey tracking
    """

    def __init__(self, name: str):
        """
        Initialize Learning Path logger

        Args:
            name: Logger name (typically __name__)
        """
        self.base_logger = get_logger(name)
        self.name = name

    def _get_context(self) -> Dict[str, Any]:
        """
        Get current context from context variables

        Returns:
            Dictionary with request_id, student_id, path_id if available
        """
        context = {}

        request_id = request_id_var.get()
        if request_id:
            context["request_id"] = request_id

        student_id = student_id_var.get()
        if student_id:
            context["student_id"] = student_id

        path_id = path_id_var.get()
        if path_id:
            context["path_id"] = path_id

        return context

    def bind_request(self, request_id: Optional[str] = None) -> str:
        """
        Bind request ID to context

        Args:
            request_id: Optional request ID (generated if not provided)

        Returns:
            Request ID that was set
        """
        if request_id is None:
            request_id = str(uuid.uuid4())

        request_id_var.set(request_id)
        return request_id

    def bind_student(self, student_id: str):
        """
        Bind student ID to context

        Args:
            student_id: Student ID
        """
        student_id_var.set(student_id)

    def bind_path(self, path_id: str):
        """
        Bind learning path ID to context

        Args:
            path_id: Learning path ID
        """
        path_id_var.set(path_id)

    def clear_context(self):
        """Clear all context variables"""
        request_id_var.set(None)
        student_id_var.set(None)
        path_id_var.set(None)

    # ========================================================================
    # Standard Logging Methods (with automatic context)
    # ========================================================================

    def info(self, event: str, **kwargs):
        """
        Log info event with automatic context

        Args:
            event: Event name
            **kwargs: Additional structured data
        """
        context = self._get_context()
        self.base_logger.info(event, **context, **kwargs)

    def warning(self, event: str, **kwargs):
        """Log warning event with automatic context"""
        context = self._get_context()
        self.base_logger.warning(event, **context, **kwargs)

    def error(
        self,
        event: str,
        error: Optional[Exception] = None,
        error_category: Optional[ErrorCategory] = None,
        **kwargs,
    ):
        """
        Log error event with categorization

        Args:
            event: Event name
            error: Exception object
            error_category: Error category for tracking
            **kwargs: Additional structured data
        """
        context = self._get_context()

        # Add error details
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)

        if error_category:
            kwargs["error_category"] = error_category.value
        else:
            kwargs["error_category"] = ErrorCategory.UNKNOWN_ERROR.value

        self.base_logger.error(event, **context, **kwargs)

    def debug(self, event: str, **kwargs):
        """Log debug event with automatic context"""
        context = self._get_context()
        self.base_logger.debug(event, **context, **kwargs)

    # ========================================================================
    # Learning Path Specific Methods
    # ========================================================================

    def log_path_creation_start(self, student_id: str, subject: str, difficulty: str):
        """
        Log start of learning path creation

        Args:
            student_id: Student ID
            subject: Subject
            difficulty: Difficulty level
        """
        self.bind_student(student_id)

        self.info(
            "learning_path_creation_started",
            subject=subject,
            difficulty=difficulty,
            operation="create_path",
        )

    def log_path_creation_success(
        self,
        path_id: str,
        duration_seconds: float,
        module_count: int,
        resource_count: int,
    ):
        """
        Log successful path creation

        Args:
            path_id: Created path ID
            duration_seconds: Time taken
            module_count: Number of modules
            resource_count: Number of resources
        """
        self.bind_path(path_id)

        self.info(
            "learning_path_creation_success",
            duration_seconds=duration_seconds,
            module_count=module_count,
            resource_count=resource_count,
            operation="create_path",
        )

    def log_path_creation_failure(
        self, error: Exception, duration_seconds: float, error_category: ErrorCategory
    ):
        """
        Log failed path creation

        Args:
            error: Exception that occurred
            duration_seconds: Time taken before failure
            error_category: Category of error
        """
        self.error(
            "learning_path_creation_failed",
            error=error,
            error_category=error_category,
            duration_seconds=duration_seconds,
            operation="create_path",
        )

    def log_resource_search(
        self,
        subject: str,
        difficulty: Optional[str],
        result_count: int,
        duration_seconds: float,
        source: str,  # "cache" or "api"
    ):
        """
        Log resource search operation

        Args:
            subject: Subject searched
            difficulty: Difficulty level
            result_count: Number of results
            duration_seconds: Time taken
            source: Cache hit or API call
        """
        self.info(
            "resource_search_completed",
            subject=subject,
            difficulty=difficulty,
            result_count=result_count,
            duration_seconds=duration_seconds,
            source=source,
            operation="resource_search",
        )

    def log_quiz_submission(
        self,
        quiz_id: str,
        score: int,
        passed: bool,
        duration_seconds: Optional[float] = None,
    ):
        """
        Log quiz submission

        Args:
            quiz_id: Quiz ID
            score: Score achieved
            passed: Whether quiz was passed
            duration_seconds: Time spent on quiz
        """
        self.info(
            "quiz_submitted",
            quiz_id=quiz_id,
            score=score,
            passed=passed,
            duration_seconds=duration_seconds,
            operation="quiz_submit",
        )

    def log_progress_update(
        self, path_id: str, node_id: str, progress_percent: int, completed: bool
    ):
        """
        Log progress update

        Args:
            path_id: Learning path ID
            node_id: Node/topic ID
            progress_percent: Progress percentage
            completed: Whether node is completed
        """
        self.bind_path(path_id)

        self.info(
            "progress_updated",
            node_id=node_id,
            progress_percent=progress_percent,
            completed=completed,
            operation="progress_update",
        )

    def log_cache_operation(
        self,
        operation: str,  # "get", "set", "invalidate"
        cache_type: str,  # "path", "resources", "quiz", etc.
        hit: Optional[bool] = None,
        ttl: Optional[int] = None,
    ):
        """
        Log cache operation

        Args:
            operation: Cache operation type
            cache_type: Type of cached data
            hit: Whether cache hit (for get operations)
            ttl: TTL in seconds (for set operations)
        """
        self.debug(
            f"cache_{operation}",
            cache_type=cache_type,
            hit=hit,
            ttl=ttl,
            operation="cache",
        )

    def log_auth_event(
        self,
        event_type: str,  # "login", "token_validate", "permission_check"
        success: bool,
        user_role: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """
        Log authentication/authorization event

        Args:
            event_type: Type of auth event
            success: Whether auth succeeded
            user_role: User role
            reason: Failure reason (if failed)
        """
        if success:
            self.info(
                f"auth_{event_type}_success", user_role=user_role, operation="auth"
            )
        else:
            self.warning(
                f"auth_{event_type}_failed",
                user_role=user_role,
                reason=reason,
                operation="auth",
            )

    def log_circuit_breaker_event(
        self,
        breaker_name: str,
        state: str,  # "open", "closed", "half_open"
        failure_count: Optional[int] = None,
    ):
        """
        Log circuit breaker state change

        Args:
            breaker_name: Name of circuit breaker
            state: New state
            failure_count: Number of failures (if opening)
        """
        self.warning(
            f"circuit_breaker_{state}",
            breaker_name=breaker_name,
            failure_count=failure_count,
            operation="circuit_breaker",
        )

    # ========================================================================
    # Performance Timing
    # ========================================================================

    def log_performance(
        self,
        operation: str,
        duration_seconds: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log performance metrics

        Args:
            operation: Operation name
            duration_seconds: Time taken
            success: Whether operation succeeded
            metadata: Additional metadata
        """
        log_data = {
            "operation": operation,
            "duration_seconds": duration_seconds,
            "success": success,
        }

        if metadata:
            log_data.update(metadata)

        if duration_seconds > 10:
            # Slow operation
            self.warning("slow_operation", **log_data)
        else:
            self.debug("operation_completed", **log_data)


# ============================================================================
# Decorator for Automatic Context and Timing
# ============================================================================


def track_operation(
    operation_name: str, error_category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR
):
    """
    Decorator to automatically track operation performance and errors

    Args:
        operation_name: Name of operation
        error_category: Default error category if exception occurs

    Usage:
        @track_operation("create_learning_path", ErrorCategory.AI_AGENT_ERROR)
        async def create_path(student_id: str, subject: str):
            # Your code here
            pass
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = LearningPathLogger(func.__module__)
            start_time = time.time()

            # Generate request ID if not exists
            if request_id_var.get() is None:
                logger.bind_request()

            try:
                logger.debug(f"{operation_name}_started", function=func.__name__)

                result = await func(*args, **kwargs)

                duration = time.time() - start_time
                logger.log_performance(
                    operation=operation_name, duration_seconds=duration, success=True
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"{operation_name}_failed",
                    error=e,
                    error_category=error_category,
                    function=func.__name__,
                )

                logger.log_performance(
                    operation=operation_name,
                    duration_seconds=duration,
                    success=False,
                    metadata={"error_type": type(e).__name__},
                )

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = LearningPathLogger(func.__module__)
            start_time = time.time()

            # Generate request ID if not exists
            if request_id_var.get() is None:
                logger.bind_request()

            try:
                logger.debug(f"{operation_name}_started", function=func.__name__)

                result = func(*args, **kwargs)

                duration = time.time() - start_time
                logger.log_performance(
                    operation=operation_name, duration_seconds=duration, success=True
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"{operation_name}_failed",
                    error=e,
                    error_category=error_category,
                    function=func.__name__,
                )

                logger.log_performance(
                    operation=operation_name,
                    duration_seconds=duration,
                    success=False,
                    metadata={"error_type": type(e).__name__},
                )

                raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# Singleton Instance
# ============================================================================

_logger_instances: Dict[str, LearningPathLogger] = {}


def get_learning_path_logger(name: str) -> LearningPathLogger:
    """
    Get Learning Path logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        LearningPathLogger instance
    """
    if name not in _logger_instances:
        _logger_instances[name] = LearningPathLogger(name)

    return _logger_instances[name]
