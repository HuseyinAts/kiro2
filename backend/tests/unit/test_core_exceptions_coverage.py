"""
Core Exceptions Module Coverage Tests
Goal: Increase core.exceptions coverage from 25% to 70%+
"""

import pytest
from datetime import datetime, timedelta

from core.exceptions import (
    # Base exceptions
    ServiceError,
    ValidationError,
    NotFoundError,
    AuthorizationError,
    DatabaseError,
    ExternalServiceError,
    ConfigurationError,
    BusinessLogicError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    ConcurrencyError,
    IntegrationError,
    MaintenanceError,
    QuotaExceededError,
    SecurityError,
    # Enhanced exceptions
    ErrorSeverity,
    EnhancedServiceError,
    UserError,
    ContentError,
    ExamError,
    LearningError,
    # Utilities
    ErrorChain,
    ErrorFactory,
    # Compatibility
    AdminAuthorizationError,
)


class TestServiceError:
    """Test base ServiceError class"""

    def test_basic_initialization(self):
        """Test ServiceError with message only"""
        error = ServiceError("Test error")
        assert error.message == "Test error"
        assert error.error_code == "SERVICE_ERROR"
        assert error.details == {}

    def test_initialization_with_error_code(self):
        """Test ServiceError with custom error code"""
        error = ServiceError("Test error", error_code="CUSTOM_ERROR")
        assert error.error_code == "CUSTOM_ERROR"

    def test_initialization_with_details(self):
        """Test ServiceError with details"""
        details = {"key": "value", "count": 42}
        error = ServiceError("Test error", details=details)
        assert error.details == details

    def test_string_representation(self):
        """Test ServiceError string representation"""
        error = ServiceError("Test error")
        assert str(error) == "Test error"


class TestValidationError:
    """Test ValidationError class"""

    def test_basic_validation_error(self):
        """Test basic validation error"""
        error = ValidationError("Invalid value")
        assert error.message == "Invalid value"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.field is None

    def test_validation_error_with_field(self):
        """Test validation error with field"""
        error = ValidationError("Invalid email", field="email")
        assert error.field == "email"
        assert error.error_code == "VALIDATION_ERROR"

    def test_validation_error_with_details(self):
        """Test validation error with details"""
        details = {"pattern": "[a-z]+", "actual": "123"}
        error = ValidationError("Invalid format", field="username", details=details)
        assert error.details == details
        assert error.field == "username"


class TestNotFoundError:
    """Test NotFoundError class"""

    def test_basic_not_found_error(self):
        """Test basic not found error"""
        error = NotFoundError("Resource not found")
        assert error.message == "Resource not found"
        assert error.error_code == "NOT_FOUND"

    def test_not_found_with_resource_type(self):
        """Test not found error with resource type"""
        error = NotFoundError("User not found", resource_type="user")
        assert "resource_type" in error.details
        assert error.details["resource_type"] == "user"

    def test_not_found_with_resource_id(self):
        """Test not found error with resource ID"""
        error = NotFoundError("User not found", resource_type="user", resource_id="123")
        assert error.details["resource_type"] == "user"
        assert error.details["resource_id"] == "123"


class TestAuthorizationError:
    """Test AuthorizationError class"""

    def test_basic_authorization_error(self):
        """Test basic authorization error"""
        error = AuthorizationError()
        assert error.message == "Insufficient permissions"
        assert error.error_code == "AUTHORIZATION_ERROR"

    def test_authorization_error_custom_message(self):
        """Test authorization error with custom message"""
        error = AuthorizationError("Admin access required")
        assert error.message == "Admin access required"


class TestDatabaseError:
    """Test DatabaseError class"""

    def test_basic_database_error(self):
        """Test basic database error"""
        error = DatabaseError("Connection failed")
        assert error.message == "Connection failed"
        assert error.error_code == "DATABASE_ERROR"

    def test_database_error_with_operation(self):
        """Test database error with operation"""
        error = DatabaseError("Query failed", operation="INSERT")
        assert error.details["operation"] == "INSERT"


class TestExternalServiceError:
    """Test ExternalServiceError class"""

    def test_basic_external_service_error(self):
        """Test basic external service error"""
        error = ExternalServiceError("API call failed")
        assert error.message == "API call failed"
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"

    def test_external_service_error_with_details(self):
        """Test external service error with service name and status"""
        error = ExternalServiceError(
            "API timeout", service_name="OpenAI", status_code=504
        )
        assert error.details["service_name"] == "OpenAI"
        assert error.details["status_code"] == 504


class TestConfigurationError:
    """Test ConfigurationError class"""

    def test_basic_configuration_error(self):
        """Test basic configuration error"""
        error = ConfigurationError("Invalid config")
        assert error.message == "Invalid config"
        assert error.error_code == "CONFIGURATION_ERROR"

    def test_configuration_error_with_key(self):
        """Test configuration error with config key"""
        error = ConfigurationError("Missing value", config_key="DATABASE_URL")
        assert error.details["config_key"] == "DATABASE_URL"


class TestBusinessLogicError:
    """Test BusinessLogicError class"""

    def test_basic_business_logic_error(self):
        """Test basic business logic error"""
        error = BusinessLogicError("Rule violation")
        assert error.message == "Rule violation"
        assert error.error_code == "BUSINESS_LOGIC_ERROR"

    def test_business_logic_error_with_rule(self):
        """Test business logic error with rule name"""
        error = BusinessLogicError("Age requirement not met", rule="MIN_AGE_18")
        assert error.details["rule"] == "MIN_AGE_18"


class TestAuthenticationError:
    """Test AuthenticationError class"""

    def test_basic_authentication_error(self):
        """Test basic authentication error"""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.error_code == "AUTHENTICATION_ERROR"

    def test_authentication_error_with_token_type(self):
        """Test authentication error with token type"""
        error = AuthenticationError("Token expired", token_type="JWT")
        assert error.details["token_type"] == "JWT"


class TestRateLimitError:
    """Test RateLimitError class"""

    def test_basic_rate_limit_error(self):
        """Test basic rate limit error"""
        error = RateLimitError()
        assert error.message == "Rate limit exceeded"
        assert error.error_code == "RATE_LIMIT_ERROR"

    def test_rate_limit_error_with_limit(self):
        """Test rate limit error with limit"""
        error = RateLimitError("Too many requests", limit=100)
        assert error.details["limit"] == 100

    def test_rate_limit_error_with_reset_time(self):
        """Test rate limit error with reset time"""
        reset_time = datetime.now() + timedelta(minutes=5)
        error = RateLimitError("Rate limited", limit=100, reset_time=reset_time)
        assert "reset_time" in error.details
        assert error.details["limit"] == 100


class TestTimeoutError:
    """Test TimeoutError class"""

    def test_basic_timeout_error(self):
        """Test basic timeout error"""
        error = TimeoutError("Operation timed out")
        assert error.message == "Operation timed out"
        assert error.error_code == "TIMEOUT_ERROR"

    def test_timeout_error_with_seconds(self):
        """Test timeout error with timeout seconds"""
        error = TimeoutError("Connection timeout", timeout_seconds=30.5)
        assert error.details["timeout_seconds"] == 30.5


class TestConcurrencyError:
    """Test ConcurrencyError class"""

    def test_basic_concurrency_error(self):
        """Test basic concurrency error"""
        error = ConcurrencyError("Lock acquisition failed")
        assert error.message == "Lock acquisition failed"
        assert error.error_code == "CONCURRENCY_ERROR"

    def test_concurrency_error_with_resource(self):
        """Test concurrency error with resource"""
        error = ConcurrencyError("Resource locked", resource="user_profile_123")
        assert error.details["resource"] == "user_profile_123"


class TestIntegrationError:
    """Test IntegrationError class"""

    def test_basic_integration_error(self):
        """Test basic integration error"""
        error = IntegrationError("Integration failed")
        assert error.message == "Integration failed"
        assert error.error_code == "INTEGRATION_ERROR"

    def test_integration_error_with_details(self):
        """Test integration error with system name and code"""
        error = IntegrationError(
            "Payment gateway error", system_name="Stripe", error_code="card_declined"
        )
        assert error.details["system_name"] == "Stripe"
        assert error.details["integration_error_code"] == "card_declined"


class TestMaintenanceError:
    """Test MaintenanceError class"""

    def test_basic_maintenance_error(self):
        """Test basic maintenance error"""
        error = MaintenanceError()
        assert error.message == "Service is under maintenance"
        assert error.error_code == "MAINTENANCE_ERROR"

    def test_maintenance_error_with_duration(self):
        """Test maintenance error with estimated duration"""
        error = MaintenanceError(
            "System upgrade in progress", estimated_duration="2 hours"
        )
        assert error.details["estimated_duration"] == "2 hours"


class TestQuotaExceededError:
    """Test QuotaExceededError class"""

    def test_basic_quota_exceeded_error(self):
        """Test basic quota exceeded error"""
        error = QuotaExceededError("Storage quota exceeded")
        assert error.message == "Storage quota exceeded"
        assert error.error_code == "QUOTA_EXCEEDED_ERROR"

    def test_quota_exceeded_error_with_details(self):
        """Test quota exceeded error with all details"""
        error = QuotaExceededError(
            "API quota exceeded",
            resource_type="api_calls",
            current_usage=1500,
            limit=1000,
        )
        assert error.details["resource_type"] == "api_calls"
        assert error.details["current_usage"] == 1500
        assert error.details["limit"] == 1000


class TestSecurityError:
    """Test SecurityError class"""

    def test_basic_security_error(self):
        """Test basic security error"""
        error = SecurityError("Security violation")
        assert error.message == "Security violation"
        assert error.error_code == "SECURITY_ERROR"

    def test_security_error_with_context(self):
        """Test security error with security context"""
        error = SecurityError(
            "SQL injection attempt",
            security_context="database_query",
            threat_level="high",
        )
        assert error.details["security_context"] == "database_query"
        assert error.details["threat_level"] == "high"


class TestErrorSeverity:
    """Test ErrorSeverity enum"""

    def test_severity_levels(self):
        """Test all severity levels exist"""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"


class TestEnhancedServiceError:
    """Test EnhancedServiceError class"""

    def test_basic_enhanced_error(self):
        """Test basic enhanced service error"""
        error = EnhancedServiceError("Enhanced error")
        assert error.message == "Enhanced error"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.user_message == "Enhanced error"

    def test_enhanced_error_with_all_params(self):
        """Test enhanced error with all parameters"""
        error = EnhancedServiceError(
            "Internal error",
            error_code="CUSTOM_ERROR",
            details={"key": "value"},
            severity=ErrorSeverity.CRITICAL,
            user_message="Something went wrong",
            retry_after=60,
            correlation_id="req-123",
        )
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.user_message == "Something went wrong"
        assert error.retry_after == 60
        assert error.correlation_id == "req-123"
        assert error.timestamp is not None

    def test_enhanced_error_to_dict(self):
        """Test enhanced error to_dict method"""
        error = EnhancedServiceError(
            "Test error",
            error_code="TEST_ERROR",
            severity=ErrorSeverity.HIGH,
            correlation_id="req-456",
        )
        error_dict = error.to_dict()

        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error"
        assert error_dict["severity"] == "high"
        assert error_dict["correlation_id"] == "req-456"
        assert "timestamp" in error_dict
        assert "source_location" in error_dict

    def test_enhanced_error_str_representation(self):
        """Test enhanced error string representation"""
        error = EnhancedServiceError(
            "Test error",
            error_code="TEST_ERROR",
            severity=ErrorSeverity.CRITICAL,
            correlation_id="req-789",
        )
        error_str = str(error)

        assert "TEST_ERROR" in error_str
        assert "Test error" in error_str
        assert "req-789" in error_str
        assert "critical" in error_str.lower()

    def test_enhanced_error_with_previous_error(self):
        """Test enhanced error chaining with previous error"""
        original = ValueError("Original error")
        error = EnhancedServiceError("Wrapped error", previous_error=original)
        assert error.previous_error == original
        assert error.stack_trace is not None


class TestUserError:
    """Test UserError class"""

    def test_basic_user_error(self):
        """Test basic user error"""
        error = UserError("User operation failed")
        assert error.message == "User operation failed"
        assert error.error_code == "USER_ERROR"

    def test_user_error_with_details(self):
        """Test user error with user details"""
        error = UserError(
            "Invalid user action", user_id="user123", user_action="delete_account"
        )
        assert error.details["user_id"] == "user123"
        assert error.details["user_action"] == "delete_account"


class TestContentError:
    """Test ContentError class"""

    def test_basic_content_error(self):
        """Test basic content error"""
        error = ContentError("Content processing failed")
        assert error.message == "Content processing failed"
        assert error.error_code == "CONTENT_ERROR"

    def test_content_error_with_details(self):
        """Test content error with content details"""
        error = ContentError(
            "Content not available",
            content_id="content456",
            content_type="video",
            operation="fetch",
        )
        assert error.details["content_id"] == "content456"
        assert error.details["content_type"] == "video"
        assert error.details["operation"] == "fetch"


class TestExamError:
    """Test ExamError class"""

    def test_basic_exam_error(self):
        """Test basic exam error"""
        error = ExamError("Exam submission failed")
        assert error.message == "Exam submission failed"
        assert error.error_code == "EXAM_ERROR"

    def test_exam_error_with_details(self):
        """Test exam error with exam details"""
        error = ExamError(
            "Invalid exam state",
            exam_id="exam789",
            question_id="q42",
            exam_state="completed",
        )
        assert error.details["exam_id"] == "exam789"
        assert error.details["question_id"] == "q42"
        assert error.details["exam_state"] == "completed"


class TestLearningError:
    """Test LearningError class"""

    def test_basic_learning_error(self):
        """Test basic learning error"""
        error = LearningError("Analytics calculation failed")
        assert error.message == "Analytics calculation failed"
        assert error.error_code == "LEARNING_ERROR"

    def test_learning_error_with_details(self):
        """Test learning error with learning details"""
        error = LearningError(
            "Style detection failed",
            user_id="user999",
            learning_context="math_practice",
            analytics_type="learning_style",
        )
        assert error.details["user_id"] == "user999"
        assert error.details["learning_context"] == "math_practice"
        assert error.details["analytics_type"] == "learning_style"


class TestErrorChain:
    """Test ErrorChain utility class"""

    def test_empty_error_chain(self):
        """Test empty error chain"""
        chain = ErrorChain()
        assert not chain.has_errors()
        assert chain.get_root_error() is None
        assert chain.get_latest_error() is None

    def test_error_chain_with_root(self):
        """Test error chain initialized with root error"""
        root_error = ValueError("Root error")
        chain = ErrorChain(root_error)
        assert chain.has_errors()
        assert chain.get_root_error() == root_error

    def test_add_error_to_chain(self):
        """Test adding errors to chain"""
        chain = ErrorChain()
        error1 = ValueError("Error 1")
        error2 = TypeError("Error 2")

        chain.add_error(error1).add_error(error2)

        assert len(chain.errors) == 2
        assert chain.get_root_error() == error1
        assert chain.get_latest_error() == error2

    def test_error_chain_summary(self):
        """Test error chain summary"""
        chain = ErrorChain()
        chain.add_error(ValueError("Value error"))
        chain.add_error(TypeError("Type error"))
        chain.correlation_id = "chain-123"

        summary = chain.get_error_summary()

        assert summary["total_errors"] == 2
        assert "ValueError" in summary["error_types"]
        assert "TypeError" in summary["error_types"]
        assert summary["correlation_id"] == "chain-123"

    def test_raise_aggregated_single_error(self):
        """Test raising aggregated error with single error"""
        chain = ErrorChain()
        original_error = ValueError("Single error")
        chain.add_error(original_error)

        with pytest.raises(ValueError) as exc_info:
            chain.raise_aggregated()

        assert exc_info.value == original_error

    def test_raise_aggregated_multiple_errors(self):
        """Test raising aggregated error with multiple errors"""
        chain = ErrorChain()
        chain.add_error(ValueError("Error 1"))
        chain.add_error(TypeError("Error 2"))
        chain.correlation_id = "agg-456"

        with pytest.raises(EnhancedServiceError) as exc_info:
            chain.raise_aggregated("Multiple failures")

        error = exc_info.value
        assert error.error_code == "AGGREGATED_ERROR"
        assert error.severity == ErrorSeverity.HIGH
        assert error.correlation_id == "agg-456"
        assert error.details["error_count"] == 2

    def test_raise_aggregated_no_errors(self):
        """Test raise_aggregated with no errors (should not raise)"""
        chain = ErrorChain()
        chain.raise_aggregated()  # Should not raise


class TestErrorFactory:
    """Test ErrorFactory utility class"""

    def test_validation_error_factory(self):
        """Test validation error factory"""
        error = ErrorFactory.validation_error(
            field="email", value="invalid", constraint="email_format"
        )
        assert isinstance(error, ValidationError)
        assert error.field == "email"
        assert error.details["field"] == "email"
        assert error.details["rejected_value"] == "invalid"
        assert error.details["constraint"] == "email_format"

    def test_validation_error_factory_custom_message(self):
        """Test validation error factory with custom message"""
        error = ErrorFactory.validation_error(
            field="age",
            value=-5,
            constraint="min_value",
            message="Age must be positive",
        )
        assert error.message == "Age must be positive"

    def test_not_found_error_factory(self):
        """Test not found error factory"""
        error = ErrorFactory.not_found_error(resource_type="user", resource_id="123")
        assert isinstance(error, NotFoundError)
        assert "User with ID '123' not found" in error.message

    def test_authorization_error_factory(self):
        """Test authorization error factory"""
        error = ErrorFactory.authorization_error(
            required_role="admin", user_role="student", resource="user_management"
        )
        assert isinstance(error, AuthorizationError)
        assert "admin" in error.message
        assert error.details["required_role"] == "admin"
        assert error.details["user_role"] == "student"
        assert error.details["resource"] == "user_management"

    def test_database_error_factory(self):
        """Test database error factory"""
        original = Exception("Connection lost")
        error = ErrorFactory.database_error(
            operation="SELECT", table="users", original_error=original
        )
        assert isinstance(error, DatabaseError)
        assert error.details["operation"] == "SELECT"
        assert error.details["table"] == "users"
        assert "Connection lost" in error.details["original_error"]

    def test_business_logic_error_factory(self):
        """Test business logic error factory"""
        error = ErrorFactory.business_logic_error(
            rule_name="MAX_LOGIN_ATTEMPTS", context={"attempts": 5, "max_allowed": 3}
        )
        assert isinstance(error, BusinessLogicError)
        assert error.details["rule"] == "MAX_LOGIN_ATTEMPTS"
        assert error.details["attempts"] == 5
        assert error.details["max_allowed"] == 3


class TestCompatibilityAliases:
    """Test backward compatibility aliases"""

    def test_admin_authorization_error_alias(self):
        """Test AdminAuthorizationError is alias for AuthorizationError"""
        assert AdminAuthorizationError is AuthorizationError


class TestEnhancedServiceErrorSourceLocation:
    """Test EnhancedServiceError source location tracking"""

    def test_source_location_captured(self):
        """Test that source location is captured"""
        error = EnhancedServiceError("Test error")
        assert "source_location" in error.to_dict()

    def test_custom_source_location(self):
        """Test custom source location"""
        custom_location = {
            "file": "/app/service.py",
            "function": "process_data",
            "line": 42,
        }
        error = EnhancedServiceError("Test error", source_location=custom_location)
        assert error.source_location == custom_location
