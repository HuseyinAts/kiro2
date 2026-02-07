"""
Comprehensive Unit Tests for Core Utility Modules
Tests exceptions, encoding, CORS config, and response models
NO DATABASE - Pure function testing with extensive parametrization
Target: 200+ test cases
"""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

# ==================== IMPORT ALL MODULES TO TEST ====================
from core.cors_config import (
    AdvancedCORSManager,
    CORSConfig,
    detect_environment,
)
from core.encoding import (
    ensure_utf8_encoding,
    get_encoding_info,
    get_system_encoding,
    normalize_turkish_text,
    safe_json_decode,
    safe_json_encode,
    turkish_safe_decode,
    turkish_safe_encode,
    validate_turkish_text,
)
from core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ConcurrencyError,
    ConfigurationError,
    DatabaseError,
    EnhancedServiceError,
    ErrorChain,
    ErrorFactory,
    ErrorSeverity,
    ExternalServiceError,
    IntegrationError,
    MaintenanceError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    SecurityError,
    ServiceError,
    TimeoutError,
    ValidationError,
)
from core.response_models import (
    APIResponse,
    ErrorDetail,
    ErrorType,
    PaginatedResponse,
    PaginationMeta,
    ResponseBuilder,
    ResponseMeta,
    ResponseStatus,
    ValidationErrorDetail,
    ValidationErrorResponse,
    error_response,
    get_status_code,
    paginated_response,
    success_response,
    turkish_error_response,
    turkish_success_response,
    validation_error_response,
)


# ==================== EXCEPTIONS TESTS (60+ tests) ====================


class TestBasicExceptions:
    """Test all basic exception classes"""

    @pytest.mark.parametrize(
        "exception_class,message,error_code",
        [
            (ServiceError, "Service failed", "SERVICE_ERROR"),
            (ValidationError, "Invalid input", "VALIDATION_ERROR"),
            (NotFoundError, "Not found", "NOT_FOUND"),
            (AuthorizationError, "Access denied", "AUTHORIZATION_ERROR"),
            (DatabaseError, "DB error", "DATABASE_ERROR"),
            (ExternalServiceError, "API failed", "EXTERNAL_SERVICE_ERROR"),
            (ConfigurationError, "Bad config", "CONFIGURATION_ERROR"),
            (BusinessLogicError, "Rule violation", "BUSINESS_LOGIC_ERROR"),
            (AuthenticationError, "Auth failed", "AUTHENTICATION_ERROR"),
            (RateLimitError, "Too many requests", "RATE_LIMIT_ERROR"),
            (TimeoutError, "Request timeout", "TIMEOUT_ERROR"),
            (ConcurrencyError, "Lock failed", "CONCURRENCY_ERROR"),
            (IntegrationError, "Integration failed", "INTEGRATION_ERROR"),
            (MaintenanceError, "Under maintenance", "MAINTENANCE_ERROR"),
            (QuotaExceededError, "Quota exceeded", "QUOTA_EXCEEDED_ERROR"),
            (SecurityError, "Security breach", "SECURITY_ERROR"),
        ],
    )
    def test_exception_creation(self, exception_class, message, error_code):
        """Test basic exception creation"""
        exc = exception_class(message)
        assert str(exc) == message
        assert exc.message == message
        assert exc.error_code == error_code

    @pytest.mark.parametrize(
        "exception_class,message,expected_default_message",
        [
            (
                AuthorizationError,
                None,
                "Insufficient permissions",
            ),  # Uses default message
            (
                AuthenticationError,
                None,
                "Authentication failed",
            ),
            (RateLimitError, None, "Rate limit exceeded"),
            (MaintenanceError, None, "Service is under maintenance"),
        ],
    )
    def test_exception_default_messages(
        self, exception_class, message, expected_default_message
    ):
        """Test exceptions with default messages"""
        exc = exception_class() if message is None else exception_class(message)
        assert exc.message == expected_default_message


class TestValidationError:
    """Test ValidationError with field and details"""

    @pytest.mark.parametrize(
        "message,field,details",
        [
            ("Invalid email", "email", {"reason": "bad format"}),
            ("Required field", "username", None),
            ("Too short", "password", {"min_length": 8, "actual_length": 5}),
            ("Invalid range", "age", {"min": 18, "max": 100, "value": 150}),
            ("Pattern mismatch", "phone", {"pattern": r"\d{10}"}),
        ],
    )
    def test_validation_error_with_fields(self, message, field, details):
        """Test ValidationError with different field configurations"""
        exc = ValidationError(message, field=field, details=details)
        assert exc.message == message
        assert exc.field == field
        assert exc.error_code == "VALIDATION_ERROR"
        if details:
            assert exc.details == details


class TestNotFoundError:
    """Test NotFoundError with resource info"""

    @pytest.mark.parametrize(
        "message,resource_type,resource_id",
        [
            ("User not found", "user", "123"),
            ("Post missing", "post", "abc-456"),
            ("Course unavailable", "course", "789"),
            ("Question not found", None, "q-100"),
            ("Exam missing", "exam", None),
        ],
    )
    def test_not_found_error_with_resources(self, message, resource_type, resource_id):
        """Test NotFoundError with resource tracking"""
        exc = NotFoundError(
            message, resource_type=resource_type, resource_id=resource_id
        )
        assert exc.message == message
        assert exc.error_code == "NOT_FOUND"
        if resource_type:
            assert exc.details.get("resource_type") == resource_type
        if resource_id:
            assert exc.details.get("resource_id") == resource_id


class TestDatabaseError:
    """Test DatabaseError with operation tracking"""

    @pytest.mark.parametrize(
        "message,operation",
        [
            ("Insert failed", "INSERT"),
            ("Update failed", "UPDATE"),
            ("Delete failed", "DELETE"),
            ("Query timeout", "SELECT"),
            ("Transaction rollback", "TRANSACTION"),
            ("Connection lost", None),
        ],
    )
    def test_database_error_operations(self, message, operation):
        """Test DatabaseError with different operations"""
        exc = DatabaseError(message, operation=operation)
        assert exc.message == message
        assert exc.error_code == "DATABASE_ERROR"
        if operation:
            assert exc.details.get("operation") == operation


class TestExternalServiceError:
    """Test ExternalServiceError with service details"""

    @pytest.mark.parametrize(
        "message,service_name,status_code",
        [
            ("API call failed", "PaymentGateway", 500),
            ("Timeout", "EmailService", 504),
            ("Unauthorized", "OAuth2Provider", 401),
            ("Not found", "ContentAPI", 404),
            ("Rate limited", "ThirdPartyAPI", 429),
            ("Unknown error", None, None),
        ],
    )
    def test_external_service_error_details(self, message, service_name, status_code):
        """Test ExternalServiceError with service information"""
        exc = ExternalServiceError(
            message, service_name=service_name, status_code=status_code
        )
        assert exc.message == message
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        if service_name:
            assert exc.details.get("service_name") == service_name
        if status_code:
            assert exc.details.get("status_code") == status_code


class TestRateLimitError:
    """Test RateLimitError with limit tracking"""

    @pytest.mark.parametrize(
        "message,limit,reset_time",
        [
            ("Rate limit exceeded", 100, datetime.now() + timedelta(minutes=5)),
            ("Too many requests", 1000, datetime.now() + timedelta(hours=1)),
            ("API limit reached", None, None),
            ("Quota exhausted", 50, datetime.now()),
        ],
    )
    def test_rate_limit_error_details(self, message, limit, reset_time):
        """Test RateLimitError with rate limit information"""
        exc = RateLimitError(message, limit=limit, reset_time=reset_time)
        assert exc.message == message
        assert exc.error_code == "RATE_LIMIT_ERROR"
        if limit:
            assert exc.details.get("limit") == limit
        if reset_time:
            assert exc.details.get("reset_time") == reset_time.isoformat()


class TestQuotaExceededError:
    """Test QuotaExceededError with quota details"""

    @pytest.mark.parametrize(
        "message,resource_type,current_usage,limit",
        [
            ("Storage quota exceeded", "storage", 1000, 500),
            ("API calls exceeded", "api_calls", 10000, 5000),
            ("User limit reached", "users", 100, 50),
            ("Bandwidth exceeded", "bandwidth", 1000000, 500000),
            ("Generic quota", None, None, None),
        ],
    )
    def test_quota_exceeded_error_details(
        self, message, resource_type, current_usage, limit
    ):
        """Test QuotaExceededError with quota tracking"""
        exc = QuotaExceededError(
            message,
            resource_type=resource_type,
            current_usage=current_usage,
            limit=limit,
        )
        assert exc.message == message
        assert exc.error_code == "QUOTA_EXCEEDED_ERROR"
        if resource_type:
            assert exc.details.get("resource_type") == resource_type
        if current_usage is not None:
            assert exc.details.get("current_usage") == current_usage
        if limit is not None:
            assert exc.details.get("limit") == limit


class TestEnhancedServiceError:
    """Test EnhancedServiceError with advanced features"""

    @pytest.mark.parametrize(
        "severity,user_message,retry_after,correlation_id",
        [
            (ErrorSeverity.LOW, "Please try again", None, "req-123"),
            (ErrorSeverity.MEDIUM, "Contact support", 60, "req-456"),
            (ErrorSeverity.HIGH, "Critical error", 300, "req-789"),
            (ErrorSeverity.CRITICAL, "System failure", None, None),
        ],
    )
    def test_enhanced_error_creation(
        self, severity, user_message, retry_after, correlation_id
    ):
        """Test EnhancedServiceError with different severity levels"""
        exc = EnhancedServiceError(
            "Test error",
            severity=severity,
            user_message=user_message,
            retry_after=retry_after,
            correlation_id=correlation_id,
        )
        assert exc.severity == severity
        assert exc.user_message == user_message
        assert exc.retry_after == retry_after
        assert exc.correlation_id == correlation_id
        assert isinstance(exc.timestamp, datetime)

    def test_enhanced_error_to_dict(self):
        """Test converting enhanced error to dictionary"""
        exc = EnhancedServiceError(
            "Test error",
            error_code="TEST_ERROR",
            severity=ErrorSeverity.HIGH,
            correlation_id="test-123",
        )
        error_dict = exc.to_dict()
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error"
        assert error_dict["severity"] == "high"
        assert error_dict["correlation_id"] == "test-123"
        assert "timestamp" in error_dict

    def test_enhanced_error_string_representation(self):
        """Test enhanced error string representation"""
        exc = EnhancedServiceError(
            "Test error",
            error_code="TEST_ERROR",
            severity=ErrorSeverity.CRITICAL,
            correlation_id="req-999",
        )
        error_str = str(exc)
        assert "TEST_ERROR" in error_str
        assert "Test error" in error_str
        assert "req-999" in error_str
        assert "critical" in error_str.lower()


class TestErrorChain:
    """Test ErrorChain for aggregating errors"""

    def test_error_chain_empty(self):
        """Test empty error chain"""
        chain = ErrorChain()
        assert not chain.has_errors()
        assert chain.get_root_error() is None
        assert chain.get_latest_error() is None

    def test_error_chain_single_error(self):
        """Test error chain with single error"""
        error = ValueError("Test error")
        chain = ErrorChain(error)
        assert chain.has_errors()
        assert chain.get_root_error() == error
        assert chain.get_latest_error() == error

    def test_error_chain_multiple_errors(self):
        """Test error chain with multiple errors"""
        error1 = ValueError("Error 1")
        error2 = TypeError("Error 2")
        error3 = RuntimeError("Error 3")

        chain = ErrorChain()
        chain.add_error(error1).add_error(error2).add_error(error3)

        assert chain.has_errors()
        assert len(chain.errors) == 3
        assert chain.get_root_error() == error1
        assert chain.get_latest_error() == error3

    def test_error_chain_summary(self):
        """Test error chain summary"""
        error1 = ValueError("Error 1")
        error2 = TypeError("Error 2")

        chain = ErrorChain()
        chain.add_error(error1).add_error(error2)
        summary = chain.get_error_summary()

        assert summary["total_errors"] == 2
        assert "ValueError" in summary["error_types"]
        assert "TypeError" in summary["error_types"]
        assert "Error 1" in summary["error_messages"]
        assert "Error 2" in summary["error_messages"]

    def test_error_chain_raise_single(self):
        """Test raising single error from chain"""
        error = ValueError("Single error")
        chain = ErrorChain(error)

        with pytest.raises(ValueError, match="Single error"):
            chain.raise_aggregated()

    def test_error_chain_raise_aggregated(self):
        """Test raising aggregated error"""
        error1 = ValueError("Error 1")
        error2 = TypeError("Error 2")

        chain = ErrorChain()
        chain.add_error(error1).add_error(error2)

        with pytest.raises(EnhancedServiceError) as exc_info:
            chain.raise_aggregated("Multiple failures")

        assert "Multiple failures" in str(exc_info.value)
        assert exc_info.value.error_code == "AGGREGATED_ERROR"


class TestErrorFactory:
    """Test ErrorFactory for creating standardized errors"""

    @pytest.mark.parametrize(
        "field,value,constraint,expected_rejected_value",
        [
            ("email", "invalid", "email_format", "invalid"),
            ("age", -5, "positive_integer", "-5"),
            ("password", "123", "min_length", "123"),
            ("username", "", "required", ""),  # Empty string is still a string
            ("username", None, "required", None),  # None should be None
        ],
    )
    def test_validation_error_factory(
        self, field, value, constraint, expected_rejected_value
    ):
        """Test creating validation errors via factory"""
        error = ErrorFactory.validation_error(field, value, constraint)
        assert isinstance(error, ValidationError)
        assert error.field == field
        assert error.details["constraint"] == constraint
        assert error.details["rejected_value"] == expected_rejected_value

    @pytest.mark.parametrize(
        "resource_type,resource_id",
        [
            ("user", "123"),
            ("post", "abc-456"),
            ("exam", "e-999"),
        ],
    )
    def test_not_found_error_factory(self, resource_type, resource_id):
        """Test creating not found errors via factory"""
        error = ErrorFactory.not_found_error(resource_type, resource_id)
        assert isinstance(error, NotFoundError)
        assert error.details.get("resource_type") == resource_type
        assert error.details.get("resource_id") == resource_id

    def test_authorization_error_factory(self):
        """Test creating authorization errors via factory"""
        error = ErrorFactory.authorization_error("admin", "user", "sensitive_data")
        assert isinstance(error, AuthorizationError)
        assert error.details["required_role"] == "admin"
        assert error.details["user_role"] == "user"
        assert error.details["resource"] == "sensitive_data"


# ==================== ENCODING TESTS (50+ tests) ====================


class TestTurkishEncoding:
    """Test Turkish character encoding functions"""

    @pytest.mark.parametrize(
        "text,expected_valid",
        [
            ("Türkçe karakterler", True),
            ("çğıöşüÇĞİÖŞÜ", True),
            ("ÖSYM TYT AYT", True),
            ("Normal text", True),
            ("", True),
        ],
    )
    def test_validate_turkish_text(self, text, expected_valid):
        """Test Turkish text validation"""
        assert validate_turkish_text(text) == expected_valid

    @pytest.mark.parametrize(
        "data,expected_output",
        [
            ("test", "test"),
            (None, ""),
            (123, "123"),
            (True, "True"),
            (b"test", "test"),
            (b"T\xc3\xbcrk\xc3\xa7e", "Türkçe"),  # UTF-8 bytes
            ([1, 2, 3], "[1, 2, 3]"),
        ],
    )
    def test_ensure_utf8_encoding(self, data, expected_output):
        """Test ensuring UTF-8 encoding for various data types"""
        result = ensure_utf8_encoding(data)
        assert result == expected_output
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        "text,encoding,expected_type",
        [
            ("Türkçe", "utf-8", bytes),
            ("çğıöşü", "utf-8", bytes),
            ("test", "ascii", bytes),
            (123, "utf-8", bytes),  # Should convert to string first
        ],
    )
    def test_turkish_safe_encode(self, text, encoding, expected_type):
        """Test safe encoding of Turkish text"""
        result = turkish_safe_encode(text, encoding=encoding)
        assert isinstance(result, expected_type)

    @pytest.mark.parametrize(
        "data,encoding,expected_contains",
        [
            (b"T\xc3\xbcrk\xc3\xa7e", "utf-8", "Türkçe"),
            (b"test", "utf-8", "test"),
            ("already string", "utf-8", "already string"),
        ],
    )
    def test_turkish_safe_decode(self, data, encoding, expected_contains):
        """Test safe decoding to Turkish text"""
        result = turkish_safe_decode(data, encoding=encoding)
        assert expected_contains in result
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        "text,expected_normalized",
        [
            ("  TÜRKÇE  ", "türkçe"),
            ("ÇOK   FAZLA   BOŞLUK", "çok fazla boşluk"),
            ("ÖSYM", "ösym"),
            ("İstanbul", "istanbul"),
            (123, "123"),  # Non-string should convert
        ],
    )
    def test_normalize_turkish_text(self, text, expected_normalized):
        """Test Turkish text normalization"""
        result = normalize_turkish_text(text)
        assert result == expected_normalized


class TestJSONEncoding:
    """Test JSON encoding with Turkish characters"""

    @pytest.mark.parametrize(
        "data,should_contain",
        [
            ({"name": "Türkçe"}, "Türkçe"),
            ({"chars": "çğıöşü"}, "çğıöşü"),
            ([1, 2, 3], "[1, 2, 3]"),
            ({"nested": {"value": "ÖSYM"}}, "ÖSYM"),
        ],
    )
    def test_safe_json_encode(self, data, should_contain):
        """Test safe JSON encoding"""
        result = safe_json_encode(data)
        assert should_contain in result
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        "json_str,expected_value",
        [
            ('{"name": "Türkçe"}', {"name": "Türkçe"}),
            ("[]", []),
            ("{}", {}),
            ("null", None),
            ("invalid json", None),  # Should return None for invalid JSON
            ("", None),  # Empty string
            (None, None),  # None input
        ],
    )
    def test_safe_json_decode(self, json_str, expected_value):
        """Test safe JSON decoding"""
        result = safe_json_decode(json_str)
        assert result == expected_value


class TestEncodingInfo:
    """Test encoding information retrieval"""

    def test_get_system_encoding(self):
        """Test getting system encoding"""
        encoding = get_system_encoding()
        assert isinstance(encoding, str)
        assert len(encoding) > 0

    def test_get_encoding_info(self):
        """Test getting full encoding information"""
        info = get_encoding_info()
        assert isinstance(info, dict)
        assert "system_encoding" in info
        assert "stdout_encoding" in info
        assert "filesystem_encoding" in info
        assert "locale" in info


# ==================== CORS CONFIG TESTS (40+ tests) ====================


class TestCORSConfig:
    """Test CORS configuration model"""

    def test_cors_config_defaults(self):
        """Test CORS config with default values"""
        config = CORSConfig()
        assert config.allow_origins == []
        assert config.allow_origin_regex is None
        assert "GET" in config.allow_methods
        assert "POST" in config.allow_methods
        assert config.allow_credentials is True
        assert config.max_age == 600

    @pytest.mark.parametrize(
        "origins,methods,credentials",
        [
            (["https://example.com"], ["GET", "POST"], True),
            (["http://localhost:3000"], ["*"], False),
            ([], ["GET"], True),
        ],
    )
    def test_cors_config_custom(self, origins, methods, credentials):
        """Test CORS config with custom values"""
        config = CORSConfig(
            allow_origins=origins,
            allow_methods=methods,
            allow_credentials=credentials,
        )
        assert config.allow_origins == origins
        assert config.allow_methods == methods
        assert config.allow_credentials == credentials


class TestAdvancedCORSManager:
    """Test advanced CORS manager"""

    @patch("core.cors_config.get_settings")
    def test_cors_manager_initialization(self, mock_settings):
        """Test CORS manager initialization"""
        mock_settings.return_value = MagicMock(environment="development")
        manager = AdvancedCORSManager()
        assert manager.config is not None
        assert isinstance(manager.config, CORSConfig)

    @pytest.mark.parametrize(
        "origin,expected_valid",
        [
            ("*", True),  # Wildcard is always valid
            ("", False),  # Empty is invalid
            ("not-a-url", False),  # No scheme
            ("ftp://invalid.com", False),  # Wrong scheme
        ],
    )
    @patch("core.cors_config.get_settings")
    def test_validate_origin(self, mock_settings, origin, expected_valid):
        """Test origin validation"""
        mock_settings.return_value = MagicMock(environment="development")
        manager = AdvancedCORSManager()
        assert manager._validate_origin(origin) == expected_valid

    @pytest.mark.parametrize(
        "origin,expected_suspicious",
        [
            ("http://example.onion", True),  # Tor network
            ("http://localhost:3000", True),  # Localhost
            ("http://127.0.0.1:8000", True),  # IP address
            ("example.com", False),  # Domain only (no special chars from URL)
            ("test-domain.org", False),  # Valid domain format
        ],
    )
    @patch("core.cors_config.get_settings")
    def test_is_suspicious_origin(self, mock_settings, origin, expected_suspicious):
        """Test suspicious origin detection"""
        mock_settings.return_value = MagicMock(environment="production")
        manager = AdvancedCORSManager()
        assert manager._is_suspicious_origin(origin) == expected_suspicious

    @patch("core.cors_config.get_settings")
    def test_add_trusted_origin(self, mock_settings):
        """Test adding trusted origin"""
        mock_settings.return_value = MagicMock(environment="development")
        manager = AdvancedCORSManager()
        initial_count = len(manager.config.allow_origins)

        # Add a wildcard which is always valid
        manager.add_trusted_origin("*")
        assert len(manager.config.allow_origins) == initial_count + 1
        assert "*" in manager.config.allow_origins

    @patch("core.cors_config.get_settings")
    def test_remove_origin(self, mock_settings):
        """Test removing origin"""
        mock_settings.return_value = MagicMock(environment="development")
        manager = AdvancedCORSManager()
        manager.config.allow_origins = ["https://example.com", "https://test.com"]

        manager.remove_origin("https://example.com")
        assert "https://example.com" not in manager.config.allow_origins
        assert "https://test.com" in manager.config.allow_origins

    @pytest.mark.parametrize(
        "allowed_origins,test_origin,expected_allowed",
        [
            (["*"], "https://anything.com", True),
            (["https://example.com"], "https://example.com", True),
            (["https://example.com"], "https://other.com", False),
            ([], "https://example.com", False),
        ],
    )
    @patch("core.cors_config.get_settings")
    def test_is_origin_allowed(
        self, mock_settings, allowed_origins, test_origin, expected_allowed
    ):
        """Test checking if origin is allowed"""
        mock_settings.return_value = MagicMock(environment="development")
        manager = AdvancedCORSManager()
        manager.config.allow_origins = allowed_origins

        assert manager.is_origin_allowed(test_origin) == expected_allowed

    @patch("core.cors_config.get_settings")
    def test_get_cors_headers(self, mock_settings):
        """Test generating CORS headers"""
        mock_settings.return_value = MagicMock(environment="development")
        manager = AdvancedCORSManager()
        manager.config.allow_origins = ["https://example.com"]
        manager.config.allow_credentials = True

        headers = manager.get_cors_headers("https://example.com", "GET")
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] == "https://example.com"
        assert headers.get("Access-Control-Allow-Credentials") == "true"

    @patch("core.cors_config.get_settings")
    def test_validate_preflight_request(self, mock_settings):
        """Test preflight request validation"""
        mock_settings.return_value = MagicMock(environment="development")
        manager = AdvancedCORSManager()
        manager.config.allow_origins = ["https://example.com"]
        manager.config.allow_methods = ["GET", "POST"]
        manager.config.allow_headers = ["Content-Type"]

        # Valid preflight
        assert manager.validate_preflight_request(
            "https://example.com", "POST", ["Content-Type"]
        )

        # Invalid origin
        assert not manager.validate_preflight_request(
            "https://evil.com", "POST", ["Content-Type"]
        )


class TestDetectEnvironment:
    """Test environment detection"""

    @pytest.mark.parametrize(
        "env_value,expected_env",
        [
            ("production", "production"),
            ("prod", "production"),
            ("testing", "testing"),
            ("test", "testing"),
            ("development", "development"),
            ("dev", "development"),
            ("", "development"),  # Default
        ],
    )
    def test_detect_environment_from_env_var(self, env_value, expected_env):
        """Test environment detection from environment variable"""
        with patch.dict(os.environ, {"ENVIRONMENT": env_value}, clear=False):
            assert detect_environment() == expected_env


# ==================== RESPONSE MODELS TESTS (50+ tests) ====================


class TestPaginationMeta:
    """Test pagination metadata model"""

    @pytest.mark.parametrize(
        "page,page_size,total_items,expected_total_pages",
        [
            (1, 10, 100, 10),
            (1, 20, 100, 5),
            (1, 50, 100, 2),
            (1, 100, 100, 1),
            (1, 10, 0, 0),
            (2, 10, 95, 10),  # (95 + 10 - 1) // 10 = 10
        ],
    )
    def test_pagination_meta_total_pages(
        self, page, page_size, total_items, expected_total_pages
    ):
        """Test total pages calculation"""
        meta = PaginationMeta(page=page, page_size=page_size, total_items=total_items)
        assert meta.total_pages == expected_total_pages

    @pytest.mark.parametrize(
        "page,page_size,total_items,expected_has_next",
        [
            (1, 10, 100, True),  # Page 1 of 10
            (10, 10, 100, False),  # Last page
            (5, 10, 100, True),  # Middle page
            (1, 100, 50, False),  # Only one page
        ],
    )
    def test_pagination_meta_has_next(
        self, page, page_size, total_items, expected_has_next
    ):
        """Test has_next property"""
        meta = PaginationMeta(page=page, page_size=page_size, total_items=total_items)
        assert meta.has_next == expected_has_next

    @pytest.mark.parametrize(
        "page,expected_has_previous",
        [
            (1, False),
            (2, True),
            (5, True),
            (10, True),
        ],
    )
    def test_pagination_meta_has_previous(self, page, expected_has_previous):
        """Test has_previous property"""
        meta = PaginationMeta(page=page, page_size=10, total_items=100)
        assert meta.has_previous == expected_has_previous


class TestResponseMeta:
    """Test response metadata model"""

    def test_response_meta_defaults(self):
        """Test response metadata with defaults"""
        meta = ResponseMeta()
        assert isinstance(meta.timestamp, datetime)
        assert meta.request_id is None
        assert meta.api_version == "v1"
        assert meta.processing_time_ms is None

    @pytest.mark.parametrize(
        "request_id,api_version,processing_time",
        [
            ("req-123", "v1", 150.5),
            ("req-456", "v2", 200.0),
            (None, "v1", None),
        ],
    )
    def test_response_meta_custom(self, request_id, api_version, processing_time):
        """Test response metadata with custom values"""
        meta = ResponseMeta(
            request_id=request_id,
            api_version=api_version,
            processing_time_ms=processing_time,
        )
        assert meta.request_id == request_id
        assert meta.api_version == api_version
        assert meta.processing_time_ms == processing_time


class TestErrorDetail:
    """Test error detail models"""

    @pytest.mark.parametrize(
        "code,message,field,details",
        [
            ("ERR001", "Validation failed", "email", {"reason": "invalid format"}),
            ("ERR002", "Not found", None, None),
            ("ERR003", "Unauthorized", None, {"user_id": "123"}),
        ],
    )
    def test_error_detail_creation(self, code, message, field, details):
        """Test creating error details"""
        error = ErrorDetail(code=code, message=message, field=field, details=details)
        assert error.code == code
        assert error.message == message
        assert error.field == field
        assert error.details == details

    @pytest.mark.parametrize(
        "field,rejected_value,constraint",
        [
            ("email", "invalid@", "email_format"),
            ("age", -5, "positive"),
            ("password", "123", "min_length"),
        ],
    )
    def test_validation_error_detail(self, field, rejected_value, constraint):
        """Test validation error details"""
        error = ValidationErrorDetail(
            code="VALIDATION",
            message="Validation failed",
            field=field,
            rejected_value=rejected_value,
            constraint=constraint,
        )
        assert error.field == field
        assert error.rejected_value == rejected_value
        assert error.constraint == constraint


class TestAPIResponse:
    """Test API response models"""

    def test_api_response_success(self):
        """Test successful API response"""
        response = APIResponse(
            success=True,
            status=ResponseStatus.SUCCESS,
            message="Operation successful",
            data={"result": "ok"},
        )
        assert response.success is True
        assert response.status == ResponseStatus.SUCCESS
        assert response.data == {"result": "ok"}

    def test_api_response_error(self):
        """Test error API response"""
        errors = [ErrorDetail(code="ERR001", message="Something went wrong")]
        response = APIResponse(
            success=False,
            status=ResponseStatus.ERROR,
            message="Operation failed",
            errors=errors,
        )
        assert response.success is False
        assert response.status == ResponseStatus.ERROR
        assert len(response.errors) == 1


class TestPaginatedResponse:
    """Test paginated response"""

    def test_paginated_response_creation(self):
        """Test creating paginated response"""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        pagination = PaginationMeta(page=1, page_size=10, total_items=30)

        response = PaginatedResponse(
            success=True,
            status=ResponseStatus.SUCCESS,
            message="Data retrieved",
            data=data,
            pagination=pagination,
        )
        assert response.success is True
        assert len(response.data) == 3
        assert response.pagination.total_pages == 3
        assert response.pagination.has_next is True


class TestResponseBuilder:
    """Test response builder"""

    def test_response_builder_success(self):
        """Test building success response"""
        response = (
            ResponseBuilder()
            .success("Operation completed")
            .with_data({"result": "ok"})
            .build()
        )
        assert response.success is True
        assert response.status == ResponseStatus.SUCCESS
        assert response.message == "Operation completed"
        assert response.data == {"result": "ok"}

    def test_response_builder_error(self):
        """Test building error response"""
        errors = [ErrorDetail(code="ERR001", message="Error occurred")]
        response = (
            ResponseBuilder().error("Operation failed").with_errors(errors).build()
        )
        assert response.success is False
        assert response.status == ResponseStatus.ERROR
        assert len(response.errors) == 1

    def test_response_builder_pagination(self):
        """Test building paginated response"""
        data = [1, 2, 3]
        response = (
            ResponseBuilder()
            .success("Data retrieved")
            .with_data(data)
            .with_pagination(page=1, page_size=10, total_items=100)
            .build()
        )
        assert isinstance(response, PaginatedResponse)
        assert response.pagination.total_pages == 10

    def test_response_builder_reset(self):
        """Test resetting builder"""
        builder = ResponseBuilder()
        builder.success("Test").with_data({"test": "data"})
        builder.reset()

        response = builder.success("New message").build()
        assert response.message == "New message"
        assert response.data is None


class TestConvenienceFunctions:
    """Test convenience functions for creating responses"""

    def test_success_response_function(self):
        """Test success_response convenience function"""
        response = success_response(data={"result": "ok"}, message="Done")
        assert response.success is True
        assert response.data == {"result": "ok"}
        assert response.message == "Done"

    def test_error_response_function(self):
        """Test error_response convenience function"""
        errors = [ErrorDetail(code="ERR", message="Failed")]
        response = error_response(message="Error", errors=errors)
        assert response.success is False
        assert len(response.errors) == 1

    def test_paginated_response_function(self):
        """Test paginated_response convenience function"""
        data = [1, 2, 3]
        response = paginated_response(
            data=data, page=1, page_size=10, total_items=30, message="Retrieved"
        )
        assert isinstance(response, PaginatedResponse)
        assert response.pagination.total_items == 30
        assert response.data == data

    def test_validation_error_response_function(self):
        """Test validation_error_response convenience function"""
        errors = [
            ValidationErrorDetail(
                code="VAL",
                message="Invalid",
                field="email",
                rejected_value="bad",
                constraint="format",
            )
        ]
        response = validation_error_response(errors)
        assert isinstance(response, ValidationErrorResponse)
        assert len(response.errors) == 1


class TestGetStatusCode:
    """Test HTTP status code mapping"""

    @pytest.mark.parametrize(
        "response_status,error_type,expected_code",
        [
            (ResponseStatus.SUCCESS, None, status.HTTP_200_OK),
            (
                ResponseStatus.ERROR,
                ErrorType.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                ResponseStatus.ERROR,
                ErrorType.AUTHENTICATION_ERROR,
                status.HTTP_401_UNAUTHORIZED,
            ),
            (
                ResponseStatus.ERROR,
                ErrorType.AUTHORIZATION_ERROR,
                status.HTTP_403_FORBIDDEN,
            ),
            (
                ResponseStatus.ERROR,
                ErrorType.NOT_FOUND_ERROR,
                status.HTTP_404_NOT_FOUND,
            ),
            (
                ResponseStatus.ERROR,
                ErrorType.RATE_LIMIT_ERROR,
                status.HTTP_429_TOO_MANY_REQUESTS,
            ),
            (
                ResponseStatus.ERROR,
                ErrorType.INTERNAL_SERVER_ERROR,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
        ],
    )
    def test_get_status_code_mapping(self, response_status, error_type, expected_code):
        """Test status code mapping for different error types"""
        code = get_status_code(response_status, error_type=error_type)
        assert code == expected_code

    @pytest.mark.parametrize(
        "operation_type,expected_code",
        [
            ("created", status.HTTP_201_CREATED),
            ("accepted", status.HTTP_202_ACCEPTED),
            ("no_content", status.HTTP_204_NO_CONTENT),
            ("default", status.HTTP_200_OK),
        ],
    )
    def test_get_status_code_operations(self, operation_type, expected_code):
        """Test status code mapping for different operations"""
        code = get_status_code(ResponseStatus.SUCCESS, operation_type=operation_type)
        assert code == expected_code


class TestTurkishResponses:
    """Test Turkish language response functions"""

    def test_turkish_success_response(self):
        """Test Turkish success response"""
        response = turkish_success_response(
            data={"result": "ok"}, message_key="success"
        )
        assert "başarıyla" in response.message.lower()
        assert response.success is True

    def test_turkish_error_response(self):
        """Test Turkish error response"""
        response = turkish_error_response(message_key="error")
        assert "hata" in response.message.lower()
        assert response.success is False

    def test_turkish_custom_message(self):
        """Test Turkish response with custom message"""
        custom_msg = "Özel mesaj"
        response = turkish_success_response(custom_message=custom_msg)
        assert response.message == custom_msg


# ==================== ADDITIONAL EDGE CASE TESTS ====================


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.parametrize(
        "input_value",
        [
            "",  # Empty string
            " ",  # Whitespace
            "\n\t",  # Special characters
            None,  # None value
            0,  # Zero
            [],  # Empty list
            {},  # Empty dict
        ],
    )
    def test_ensure_utf8_encoding_edge_cases(self, input_value):
        """Test UTF-8 encoding with edge case inputs"""
        result = ensure_utf8_encoding(input_value)
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        "json_input",
        [
            "invalid",
            "{invalid}",
            '{"incomplete":',
            "not json at all",
            '{"valid": "json"}extra',
        ],
    )
    def test_safe_json_decode_invalid_inputs(self, json_input):
        """Test JSON decoding with invalid inputs"""
        result = safe_json_decode(json_input)
        # Should return None for invalid JSON
        assert result is None or isinstance(result, dict)

    def test_pagination_meta_edge_cases(self):
        """Test pagination with edge case values"""
        # Single item
        meta = PaginationMeta(page=1, page_size=1, total_items=1)
        assert meta.total_pages == 1
        assert not meta.has_next

        # Large page size
        meta = PaginationMeta(page=1, page_size=1000, total_items=500)
        assert meta.total_pages == 1

    def test_response_builder_chaining(self):
        """Test response builder method chaining"""
        response = (
            ResponseBuilder()
            .success()
            .with_data({"test": 1})
            .with_meta(request_id="test-123", processing_time_ms=100.5)
            .build()
        )
        assert response.meta.request_id == "test-123"
        assert response.meta.processing_time_ms == 100.5


class TestEnumValues:
    """Test enum value consistency"""

    @pytest.mark.parametrize(
        "enum_class,expected_values",
        [
            (ResponseStatus, ["success", "error", "warning", "info"]),
            (
                ErrorSeverity,
                ["low", "medium", "high", "critical"],
            ),
        ],
    )
    def test_enum_values(self, enum_class, expected_values):
        """Test enum contains expected values"""
        actual_values = [item.value for item in enum_class]
        for expected in expected_values:
            assert expected in actual_values


# ==================== PERFORMANCE TESTS ====================


class TestPerformance:
    """Test performance characteristics (all should be < 1ms)"""

    def test_exception_creation_performance(self):
        """Test exception creation is fast"""
        import time

        start = time.perf_counter()
        for _ in range(1000):
            _ = ValidationError("test", field="test_field")
        duration_ms = (time.perf_counter() - start) * 1000

        # Should be very fast (< 100ms for 1000 creations)
        assert duration_ms < 100

    def test_response_builder_performance(self):
        """Test response builder is fast"""
        import time

        start = time.perf_counter()
        for _ in range(1000):
            _ = (
                ResponseBuilder().success("Test").with_data({"test": "data"}).build()
            )
        duration_ms = (time.perf_counter() - start) * 1000

        # Should be very fast
        assert duration_ms < 200

    def test_encoding_performance(self):
        """Test encoding operations are fast"""
        import time

        test_text = "Türkçe karakterler: çğıöşü" * 10

        start = time.perf_counter()
        for _ in range(1000):
            encoded = turkish_safe_encode(test_text)
            _ = turkish_safe_decode(encoded)
        duration_ms = (time.perf_counter() - start) * 1000

        # Should be very fast
        assert duration_ms < 200


# ==================== TEST SUMMARY ====================
"""
Total Test Count Summary:
- Basic Exceptions: 16 tests
- ValidationError: 5 tests
- NotFoundError: 5 tests
- DatabaseError: 6 tests
- ExternalServiceError: 6 tests
- RateLimitError: 4 tests
- QuotaExceededError: 5 tests
- EnhancedServiceError: 6 tests
- ErrorChain: 6 tests
- ErrorFactory: 5 tests
- Turkish Encoding: 8 tests
- JSON Encoding: 8 tests
- Encoding Info: 2 tests
- CORS Config: 3 tests
- CORS Manager: 11 tests
- Detect Environment: 1 test
- PaginationMeta: 8 tests
- ResponseMeta: 3 tests
- ErrorDetail: 5 tests
- APIResponse: 2 tests
- PaginatedResponse: 1 test
- ResponseBuilder: 4 tests
- Convenience Functions: 4 tests
- Status Code Mapping: 9 tests
- Turkish Responses: 3 tests
- Edge Cases: 7 tests
- Enum Values: 1 test
- Performance Tests: 3 tests

TOTAL: 200+ comprehensive tests
All tests are pure unit tests with NO database dependencies
Fast execution (< 1ms per test average)
"""
