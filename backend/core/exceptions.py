"""
Centralized Exception Hierarchy
Comprehensive exception system for standardized error handling
"""

import traceback
from datetime import datetime
from enum import Enum
from typing import Any


class ServiceError(Exception):
    """Base service exception"""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "SERVICE_ERROR"
        self.details = details or {}


class ValidationError(ServiceError):
    """Validation error exception"""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class NotFoundError(ServiceError):
    """Resource not found exception"""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(message, "NOT_FOUND", details)


class AuthorizationError(ServiceError):
    """Authorization error exception"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class DatabaseError(ServiceError):
    """Database operation error exception"""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        # ``details`` ServiceError'un zaten kabul ettigi parametredir; bu sinif onu
        # daraltmisti ve 22 cagri yeri onu gonderdigi icin TypeError firliyordu.
        # ``operation`` once yazilir, acikca verilen ``details`` uzerine yazabilir.
        birlesik: dict[str, Any] = {"operation": operation} if operation else {}
        if details:
            birlesik.update(details)
        super().__init__(message, "DATABASE_ERROR", birlesik)


class ExternalServiceError(ServiceError):
    """External service error exception"""

    def __init__(
        self,
        message: str,
        service_name: str | None = None,
        status_code: int | None = None,
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        if status_code:
            details["status_code"] = status_code

        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class ConfigurationError(ServiceError):
    """Configuration error exception"""

    def __init__(self, message: str, config_key: str | None = None):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, "CONFIGURATION_ERROR", details)


class BusinessLogicError(ServiceError):
    """Business logic error exception"""

    def __init__(self, message: str, rule: str | None = None):
        details = {"rule": rule} if rule else {}
        super().__init__(message, "BUSINESS_LOGIC_ERROR", details)


class AuthenticationError(ServiceError):
    """Authentication error exception"""

    def __init__(
        self, message: str = "Authentication failed", token_type: str | None = None
    ):
        details = {"token_type": token_type} if token_type else {}
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class RateLimitError(ServiceError):
    """Rate limit exceeded exception"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: int | None = None,
        reset_time: datetime | None = None,
    ):
        details = {}
        if limit:
            details["limit"] = limit
        if reset_time:
            details["reset_time"] = reset_time.isoformat()
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class TimeoutError(ServiceError):
    """Operation timeout exception"""

    def __init__(self, message: str, timeout_seconds: float | None = None):
        details = {"timeout_seconds": timeout_seconds} if timeout_seconds else {}
        super().__init__(message, "TIMEOUT_ERROR", details)


class ConcurrencyError(ServiceError):
    """Concurrency/locking error exception"""

    def __init__(self, message: str, resource: str | None = None):
        details = {"resource": resource} if resource else {}
        super().__init__(message, "CONCURRENCY_ERROR", details)


class IntegrationError(ServiceError):
    """System integration error exception"""

    def __init__(
        self,
        message: str,
        system_name: str | None = None,
        error_code: str | None = None,
    ):
        details = {}
        if system_name:
            details["system_name"] = system_name
        if error_code:
            details["integration_error_code"] = error_code
        super().__init__(message, "INTEGRATION_ERROR", details)


class MaintenanceError(ServiceError):
    """Service under maintenance exception"""

    def __init__(
        self,
        message: str = "Service is under maintenance",
        estimated_duration: str | None = None,
    ):
        details = (
            {"estimated_duration": estimated_duration} if estimated_duration else {}
        )
        super().__init__(message, "MAINTENANCE_ERROR", details)


class QuotaExceededError(ServiceError):
    """Resource quota exceeded exception"""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        current_usage: int | None = None,
        limit: int | None = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if current_usage is not None:
            details["current_usage"] = current_usage
        if limit is not None:
            details["limit"] = limit
        super().__init__(message, "QUOTA_EXCEEDED_ERROR", details)


class SecurityError(ServiceError):
    """Security-related error exception"""

    def __init__(
        self,
        message: str,
        security_context: str | None = None,
        threat_level: str | None = "low",
    ):
        details = {}
        if security_context:
            details["security_context"] = security_context
        if threat_level:
            details["threat_level"] = threat_level
        super().__init__(message, "SECURITY_ERROR", details)


# ==================== ERROR SEVERITY LEVELS ====================


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ==================== ENHANCED SERVICE ERROR BASE CLASS ====================


class EnhancedServiceError(ServiceError):
    """Enhanced service error with additional context and tracing"""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: str | None = None,
        retry_after: int | None = None,
        correlation_id: str | None = None,
        source_location: dict[str, Any] | None = None,
        previous_error: Exception | None = None,
    ):
        super().__init__(message, error_code, details)

        self.severity = severity
        self.user_message = user_message or message  # User-friendly message
        self.retry_after = retry_after  # Seconds before retry is allowed
        self.correlation_id = correlation_id  # For request tracing
        self.timestamp = datetime.now()
        self.source_location = source_location or self._get_source_location()
        self.previous_error = previous_error
        self.stack_trace = traceback.format_exc() if previous_error else None

    def _get_source_location(self) -> dict[str, Any]:
        """Get source code location where error occurred"""
        try:
            import inspect

            frame = inspect.currentframe()
            if frame and frame.f_back and frame.f_back.f_back:
                caller_frame = frame.f_back.f_back
                return {
                    "file": caller_frame.f_code.co_filename,
                    "function": caller_frame.f_code.co_name,
                    "line": caller_frame.f_lineno,
                }
        except Exception:
            pass
        return {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "correlation_id": self.correlation_id,
            "source_location": self.source_location,
            "retry_after": self.retry_after,
            "stack_trace": self.stack_trace,
            "previous_error": str(self.previous_error) if self.previous_error else None,
        }

    def __str__(self) -> str:
        """String representation with enhanced context"""
        base_str = f"[{self.error_code}] {self.message}"
        if self.correlation_id:
            base_str += f" (ID: {self.correlation_id})"
        if self.severity != ErrorSeverity.MEDIUM:
            base_str += f" [Severity: {self.severity.value}]"
        return base_str


# ==================== BUSINESS-SPECIFIC EXCEPTIONS ====================


class UserError(EnhancedServiceError):
    """User-related error exception"""

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        user_action: str | None = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if user_id:
            details["user_id"] = user_id
        if user_action:
            details["user_action"] = user_action
        kwargs["details"] = details
        super().__init__(message, "USER_ERROR", **kwargs)


class ContentError(EnhancedServiceError):
    """Content management error exception"""

    def __init__(
        self,
        message: str,
        content_id: str | None = None,
        content_type: str | None = None,
        operation: str | None = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if content_id:
            details["content_id"] = content_id
        if content_type:
            details["content_type"] = content_type
        if operation:
            details["operation"] = operation
        kwargs["details"] = details
        super().__init__(message, "CONTENT_ERROR", **kwargs)


class ExamError(EnhancedServiceError):
    """Exam-related error exception"""

    def __init__(
        self,
        message: str,
        exam_id: str | None = None,
        question_id: str | None = None,
        exam_state: str | None = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if exam_id:
            details["exam_id"] = exam_id
        if question_id:
            details["question_id"] = question_id
        if exam_state:
            details["exam_state"] = exam_state
        kwargs["details"] = details
        super().__init__(message, "EXAM_ERROR", **kwargs)


class LearningError(EnhancedServiceError):
    """Learning and analytics error exception"""

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        learning_context: str | None = None,
        analytics_type: str | None = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if user_id:
            details["user_id"] = user_id
        if learning_context:
            details["learning_context"] = learning_context
        if analytics_type:
            details["analytics_type"] = analytics_type
        kwargs["details"] = details
        super().__init__(message, "LEARNING_ERROR", **kwargs)


# ==================== ERROR CHAINS AND AGGREGATION ====================


class ErrorChain:
    """Utility for chaining and aggregating errors"""

    def __init__(self, root_error: Exception | None = None):
        self.errors: list[Exception] = []
        self.correlation_id = None
        if root_error:
            self.add_error(root_error)

    def add_error(self, error: Exception) -> "ErrorChain":
        """Add error to the chain"""
        self.errors.append(error)
        return self

    def has_errors(self) -> bool:
        """Check if chain has any errors"""
        return len(self.errors) > 0

    def get_root_error(self) -> Exception | None:
        """Get the first/root error"""
        return self.errors[0] if self.errors else None

    def get_latest_error(self) -> Exception | None:
        """Get the most recent error"""
        return self.errors[-1] if self.errors else None

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of all errors in chain"""
        return {
            "total_errors": len(self.errors),
            "error_types": [type(err).__name__ for err in self.errors],
            "error_messages": [str(err) for err in self.errors],
            "correlation_id": self.correlation_id,
            "first_error_time": getattr(self.errors[0], "timestamp", None)
            if self.errors
            else None,
            "last_error_time": getattr(self.errors[-1], "timestamp", None)
            if self.errors
            else None,
        }

    def raise_aggregated(self, message: str = "Multiple errors occurred") -> None:
        """Raise an aggregated error containing all errors in chain"""
        if not self.errors:
            return

        if len(self.errors) == 1:
            raise self.errors[0]

        # Create aggregated error
        details = {
            "error_count": len(self.errors),
            "error_chain": self.get_error_summary(),
        }

        raise EnhancedServiceError(
            message=message,
            error_code="AGGREGATED_ERROR",
            details=details,
            severity=ErrorSeverity.HIGH,
            correlation_id=self.correlation_id,
            previous_error=self.get_latest_error(),
        )


# ==================== ERROR FACTORIES ====================


class ErrorFactory:
    """Factory for creating standardized errors"""

    @staticmethod
    def validation_error(
        field: str, value: Any, constraint: str, message: str | None = None
    ) -> ValidationError:
        """Create standardized validation error"""
        message = message or f"Validation failed for field '{field}'"
        details = {
            "field": field,
            "rejected_value": str(value) if value is not None else None,
            "constraint": constraint,
        }
        return ValidationError(message, field=field, details=details)

    @staticmethod
    def not_found_error(
        resource_type: str, resource_id: str, message: str | None = None
    ) -> NotFoundError:
        """Create standardized not found error"""
        message = (
            message or f"{resource_type.title()} with ID '{resource_id}' not found"
        )
        return NotFoundError(
            message, resource_type=resource_type, resource_id=resource_id
        )

    @staticmethod
    def authorization_error(
        required_role: str,
        user_role: str,
        resource: str | None = None,
        message: str | None = None,
    ) -> AuthorizationError:
        """Create standardized authorization error"""
        message = (
            message
            or f"Access denied. Required role: {required_role}, user role: {user_role}"
        )
        error = AuthorizationError(message)
        error.details.update(
            {
                "required_role": required_role,
                "user_role": user_role,
                "resource": resource,
            }
        )
        return error

    @staticmethod
    def database_error(
        operation: str,
        table: str | None = None,
        original_error: Exception | None = None,
        message: str | None = None,
    ) -> DatabaseError:
        """Create standardized database error"""
        message = message or f"Database operation '{operation}' failed"
        error = DatabaseError(message, operation=operation)
        if table:
            error.details["table"] = table
        if original_error:
            error.details["original_error"] = str(original_error)
        return error

    @staticmethod
    def business_logic_error(
        rule_name: str,
        context: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> BusinessLogicError:
        """Create standardized business logic error"""
        message = message or f"Business rule violation: {rule_name}"
        error = BusinessLogicError(message, rule=rule_name)
        if context:
            error.details.update(context)
        return error


# ==================== COMPATIBILITY ALIASES ====================

# Keep existing aliases for backward compatibility
AdminAuthorizationError = AuthorizationError
