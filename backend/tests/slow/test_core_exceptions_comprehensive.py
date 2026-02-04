"""
Comprehensive tests for core.exceptions module
Target: 95%+ coverage for exception handling
"""
import pytest
from unittest.mock import patch, MagicMock
from core.exceptions import (
    TurkishEducationPlatformException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ExternalServiceError,
    ConfigurationError,
    BusinessLogicError,
    ResourceNotFoundError,
    RateLimitError,
    ExamError,
    StudentError,
    TeacherError,
    ParentError,
    ContentError,
    TurkishLanguageError,
)


class TestTurkishEducationPlatformException:
    """Test base exception class"""

    def test_base_exception_initialization(self):
        """Test base exception initialization"""
        exc = TurkishEducationPlatformException("Test message")
        assert str(exc) == "Test message"
        assert exc.args == ("Test message",)

    def test_base_exception_with_details(self):
        """Test base exception with details"""
        details = {"field": "value", "error_code": 123}
        exc = TurkishEducationPlatformException("Test message", details=details)

        assert str(exc) == "Test message"
        assert hasattr(exc, "details")
        assert exc.details == details

    def test_base_exception_without_details(self):
        """Test base exception without details"""
        exc = TurkishEducationPlatformException("Test message")
        assert hasattr(exc, "details")
        assert exc.details is None

    def test_base_exception_inheritance(self):
        """Test that base exception inherits from Exception"""
        exc = TurkishEducationPlatformException("Test")
        assert isinstance(exc, Exception)

    def test_base_exception_empty_message(self):
        """Test base exception with empty message"""
        exc = TurkishEducationPlatformException("")
        assert str(exc) == ""

    def test_base_exception_none_message(self):
        """Test base exception with None message"""
        exc = TurkishEducationPlatformException(None)
        assert str(exc) == "None"


class TestValidationError:
    """Test validation error"""

    def test_validation_error_basic(self):
        """Test basic validation error"""
        exc = ValidationError("Geçersiz veri")
        assert str(exc) == "Geçersiz veri"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_validation_error_with_field(self):
        """Test validation error with field details"""
        details = {"field": "email", "value": "invalid-email"}
        exc = ValidationError("Email formatı geçersiz", details=details)

        assert str(exc) == "Email formatı geçersiz"
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "invalid-email"

    def test_validation_error_multiple_fields(self):
        """Test validation error with multiple field errors"""
        details = {
            "errors": [
                {"field": "name", "message": "İsim gerekli"},
                {"field": "email", "message": "Email geçersiz"},
            ]
        }
        exc = ValidationError("Doğrulama hatası", details=details)

        assert len(exc.details["errors"]) == 2
        assert exc.details["errors"][0]["field"] == "name"

    def test_validation_error_turkish_characters(self):
        """Test validation error with Turkish characters"""
        exc = ValidationError("Türkçe karakter hatası: çğıöşü")
        assert "çğıöşü" in str(exc)


class TestAuthenticationError:
    """Test authentication error"""

    def test_authentication_error_basic(self):
        """Test basic authentication error"""
        exc = AuthenticationError("Kimlik doğrulama başarısız")
        assert str(exc) == "Kimlik doğrulama başarısız"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_authentication_error_with_user_info(self):
        """Test authentication error with user info"""
        details = {"username": "test_user", "attempt_count": 3}
        exc = AuthenticationError("Giriş başarısız", details=details)

        assert exc.details["username"] == "test_user"
        assert exc.details["attempt_count"] == 3

    def test_authentication_error_token_expired(self):
        """Test authentication error for expired token"""
        details = {"reason": "token_expired", "expires_at": "2023-01-01"}
        exc = AuthenticationError("Token süresi dolmuş", details=details)

        assert exc.details["reason"] == "token_expired"

    def test_authentication_error_invalid_credentials(self):
        """Test authentication error for invalid credentials"""
        exc = AuthenticationError("Geçersiz kullanıcı bilgileri")
        assert "Geçersiz" in str(exc)


class TestAuthorizationError:
    """Test authorization error"""

    def test_authorization_error_basic(self):
        """Test basic authorization error"""
        exc = AuthorizationError("Yetki yetersiz")
        assert str(exc) == "Yetki yetersiz"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_authorization_error_with_permission(self):
        """Test authorization error with permission details"""
        details = {
            "required_permission": "admin.write",
            "user_permissions": ["student.read", "student.write"],
        }
        exc = AuthorizationError("İzin verilmeyen işlem", details=details)

        assert exc.details["required_permission"] == "admin.write"
        assert len(exc.details["user_permissions"]) == 2

    def test_authorization_error_role_based(self):
        """Test authorization error for role-based access"""
        details = {"required_role": "teacher", "user_role": "student"}
        exc = AuthorizationError("Öğretmen yetkisi gerekli", details=details)

        assert exc.details["required_role"] == "teacher"
        assert exc.details["user_role"] == "student"


class TestDatabaseError:
    """Test database error"""

    def test_database_error_basic(self):
        """Test basic database error"""
        exc = DatabaseError("Veritabanı bağlantı hatası")
        assert str(exc) == "Veritabanı bağlantı hatası"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_database_error_with_query_info(self):
        """Test database error with query information"""
        details = {
            "query": "SELECT * FROM users WHERE id = ?",
            "parameters": [123],
            "error_code": "SQLITE_CONSTRAINT",
        }
        exc = DatabaseError("Sorgu hatası", details=details)

        assert "SELECT" in exc.details["query"]
        assert exc.details["parameters"][0] == 123

    def test_database_error_connection_timeout(self):
        """Test database error for connection timeout"""
        details = {"timeout_seconds": 30, "operation": "connect"}
        exc = DatabaseError("Bağlantı zaman aşımı", details=details)

        assert exc.details["timeout_seconds"] == 30

    def test_database_error_constraint_violation(self):
        """Test database error for constraint violation"""
        details = {"constraint": "unique_email", "table": "users", "field": "email"}
        exc = DatabaseError("Benzersizlik kısıtlaması ihlali", details=details)

        assert exc.details["constraint"] == "unique_email"


class TestExternalServiceError:
    """Test external service error"""

    def test_external_service_error_basic(self):
        """Test basic external service error"""
        exc = ExternalServiceError("Dış servis hatası")
        assert str(exc) == "Dış servis hatası"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_external_service_error_with_service_info(self):
        """Test external service error with service details"""
        details = {
            "service_name": "OSYM API",
            "endpoint": "/api/v1/exams",
            "status_code": 500,
            "response": "Internal Server Error",
        }
        exc = ExternalServiceError("OSYM API hatası", details=details)

        assert exc.details["service_name"] == "OSYM API"
        assert exc.details["status_code"] == 500

    def test_external_service_error_timeout(self):
        """Test external service error for timeout"""
        details = {
            "service": "YouTube API",
            "timeout_seconds": 10,
            "operation": "search_videos",
        }
        exc = ExternalServiceError("Servis zaman aşımı", details=details)

        assert exc.details["service"] == "YouTube API"

    def test_external_service_error_rate_limit(self):
        """Test external service error for rate limiting"""
        details = {
            "service": "OpenAI API",
            "rate_limit": "100 requests/hour",
            "retry_after": 3600,
        }
        exc = ExternalServiceError("Oran sınırı aşıldı", details=details)

        assert exc.details["retry_after"] == 3600


class TestConfigurationError:
    """Test configuration error"""

    def test_configuration_error_basic(self):
        """Test basic configuration error"""
        exc = ConfigurationError("Konfigürasyon hatası")
        assert str(exc) == "Konfigürasyon hatası"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_configuration_error_missing_setting(self):
        """Test configuration error for missing setting"""
        details = {
            "setting_name": "DATABASE_URL",
            "config_file": "settings.yaml",
            "required": True,
        }
        exc = ConfigurationError("Gerekli ayar eksik", details=details)

        assert exc.details["setting_name"] == "DATABASE_URL"
        assert exc.details["required"] is True

    def test_configuration_error_invalid_value(self):
        """Test configuration error for invalid value"""
        details = {"setting": "PORT", "value": "invalid", "expected_type": "integer"}
        exc = ConfigurationError("Geçersiz ayar değeri", details=details)

        assert exc.details["value"] == "invalid"
        assert exc.details["expected_type"] == "integer"


class TestBusinessLogicError:
    """Test business logic error"""

    def test_business_logic_error_basic(self):
        """Test basic business logic error"""
        exc = BusinessLogicError("İş kuralı ihlali")
        assert str(exc) == "İş kuralı ihlali"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_business_logic_error_exam_rules(self):
        """Test business logic error for exam rules"""
        details = {
            "rule": "exam_duration_limit",
            "max_duration": 180,
            "requested_duration": 240,
        }
        exc = BusinessLogicError("Sınav süresi aşıldı", details=details)

        assert exc.details["max_duration"] == 180
        assert exc.details["requested_duration"] == 240

    def test_business_logic_error_enrollment_rules(self):
        """Test business logic error for enrollment rules"""
        details = {
            "student_id": "12345",
            "course_id": "MATH101",
            "max_enrollment": 30,
            "current_enrollment": 30,
        }
        exc = BusinessLogicError("Kurs dolu", details=details)

        assert exc.details["current_enrollment"] == 30


class TestResourceNotFoundError:
    """Test resource not found error"""

    def test_resource_not_found_error_basic(self):
        """Test basic resource not found error"""
        exc = ResourceNotFoundError("Kaynak bulunamadı")
        assert str(exc) == "Kaynak bulunamadı"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_resource_not_found_error_with_resource_info(self):
        """Test resource not found error with resource details"""
        details = {
            "resource_type": "User",
            "resource_id": "12345",
            "search_criteria": {"email": "test@example.com"},
        }
        exc = ResourceNotFoundError("Kullanıcı bulunamadı", details=details)

        assert exc.details["resource_type"] == "User"
        assert exc.details["resource_id"] == "12345"

    def test_resource_not_found_error_exam(self):
        """Test resource not found error for exam"""
        details = {"exam_id": "TYT2023", "student_id": "67890"}
        exc = ResourceNotFoundError("Sınav bulunamadı", details=details)

        assert exc.details["exam_id"] == "TYT2023"


class TestRateLimitError:
    """Test rate limit error"""

    def test_rate_limit_error_basic(self):
        """Test basic rate limit error"""
        exc = RateLimitError("Oran sınırı aşıldı")
        assert str(exc) == "Oran sınırı aşıldı"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_rate_limit_error_with_limit_info(self):
        """Test rate limit error with limit details"""
        details = {
            "limit": 100,
            "window": "1 hour",
            "current_usage": 105,
            "retry_after": 3600,
        }
        exc = RateLimitError("Saatlik sınır aşıldı", details=details)

        assert exc.details["limit"] == 100
        assert exc.details["current_usage"] == 105
        assert exc.details["retry_after"] == 3600

    def test_rate_limit_error_api_specific(self):
        """Test rate limit error for specific API"""
        details = {
            "api_endpoint": "/api/v1/questions",
            "user_id": "user123",
            "reset_time": "2023-12-01T15:00:00Z",
        }
        exc = RateLimitError("API sınırı aşıldı", details=details)

        assert exc.details["api_endpoint"] == "/api/v1/questions"


class TestExamError:
    """Test exam-specific error"""

    def test_exam_error_basic(self):
        """Test basic exam error"""
        exc = ExamError("Sınav hatası")
        assert str(exc) == "Sınav hatası"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_exam_error_submission(self):
        """Test exam error for submission issues"""
        details = {
            "exam_id": "TYT2023",
            "student_id": "12345",
            "error_type": "time_exceeded",
            "remaining_time": -30,
        }
        exc = ExamError("Sınav süresi aşıldı", details=details)

        assert exc.details["error_type"] == "time_exceeded"
        assert exc.details["remaining_time"] == -30

    def test_exam_error_question_loading(self):
        """Test exam error for question loading"""
        details = {
            "question_id": "Q12345",
            "exam_session": "session_789",
            "error": "question_not_found",
        }
        exc = ExamError("Soru yüklenemedi", details=details)

        assert exc.details["question_id"] == "Q12345"


class TestStudentError:
    """Test student-specific error"""

    def test_student_error_basic(self):
        """Test basic student error"""
        exc = StudentError("Öğrenci hatası")
        assert str(exc) == "Öğrenci hatası"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_student_error_enrollment(self):
        """Test student error for enrollment"""
        details = {
            "student_id": "S12345",
            "course_id": "MATH101",
            "error_reason": "prerequisite_not_met",
            "required_courses": ["MATH100"],
        }
        exc = StudentError("Ön koşul eksik", details=details)

        assert exc.details["error_reason"] == "prerequisite_not_met"
        assert "MATH100" in exc.details["required_courses"]

    def test_student_error_grade_calculation(self):
        """Test student error for grade calculation"""
        details = {
            "student_id": "S67890",
            "exam_scores": [85, 90, 78],
            "error": "invalid_score_range",
        }
        exc = StudentError("Not hesaplama hatası", details=details)

        assert len(exc.details["exam_scores"]) == 3


class TestTeacherError:
    """Test teacher-specific error"""

    def test_teacher_error_basic(self):
        """Test basic teacher error"""
        exc = TeacherError("Öğretmen hatası")
        assert str(exc) == "Öğretmen hatası"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_teacher_error_class_assignment(self):
        """Test teacher error for class assignment"""
        details = {
            "teacher_id": "T12345",
            "class_id": "CLASS_A",
            "max_classes": 5,
            "current_classes": 5,
        }
        exc = TeacherError("Sınıf sınırı aşıldı", details=details)

        assert exc.details["max_classes"] == 5
        assert exc.details["current_classes"] == 5

    def test_teacher_error_subject_qualification(self):
        """Test teacher error for subject qualification"""
        details = {
            "teacher_id": "T67890",
            "requested_subject": "Physics",
            "qualified_subjects": ["Mathematics", "Chemistry"],
        }
        exc = TeacherError("Alan yetkinliği yetersiz", details=details)

        assert exc.details["requested_subject"] == "Physics"
        assert "Mathematics" in exc.details["qualified_subjects"]


class TestParentError:
    """Test parent-specific error"""

    def test_parent_error_basic(self):
        """Test basic parent error"""
        exc = ParentError("Veli hatası")
        assert str(exc) == "Veli hatası"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_parent_error_child_access(self):
        """Test parent error for child access"""
        details = {
            "parent_id": "P12345",
            "student_id": "S67890",
            "relationship": "guardian",
            "verified": False,
        }
        exc = ParentError("Öğrenci erişim yetkisi yok", details=details)

        assert exc.details["relationship"] == "guardian"
        assert exc.details["verified"] is False

    def test_parent_error_multiple_children(self):
        """Test parent error for multiple children management"""
        details = {
            "parent_id": "P11111",
            "children": ["S1", "S2", "S3"],
            "max_children": 2,
        }
        exc = ParentError("Çocuk sayısı sınırı aşıldı", details=details)

        assert len(exc.details["children"]) == 3
        assert exc.details["max_children"] == 2


class TestContentError:
    """Test content-specific error"""

    def test_content_error_basic(self):
        """Test basic content error"""
        exc = ContentError("İçerik hatası")
        assert str(exc) == "İçerik hatası"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_content_error_upload(self):
        """Test content error for upload issues"""
        details = {
            "file_name": "matematik_soru.pdf",
            "file_size": 10485760,  # 10MB
            "max_size": 5242880,  # 5MB
            "error_type": "file_too_large",
        }
        exc = ContentError("Dosya boyutu çok büyük", details=details)

        assert exc.details["file_size"] > exc.details["max_size"]

    def test_content_error_format(self):
        """Test content error for format issues"""
        details = {
            "content_type": "question",
            "expected_format": "JSON",
            "received_format": "XML",
            "validation_errors": ["missing_answer_key", "invalid_difficulty"],
        }
        exc = ContentError("İçerik formatı geçersiz", details=details)

        assert exc.details["expected_format"] == "JSON"
        assert len(exc.details["validation_errors"]) == 2


class TestTurkishLanguageError:
    """Test Turkish language-specific error"""

    def test_turkish_language_error_basic(self):
        """Test basic Turkish language error"""
        exc = TurkishLanguageError("Türkçe dil hatası")
        assert str(exc) == "Türkçe dil hatası"
        assert isinstance(exc, TurkishEducationPlatformException)

    def test_turkish_language_error_encoding(self):
        """Test Turkish language error for encoding issues"""
        details = {
            "text": "çğıöşü ÇĞIÖŞÜ",
            "encoding_error": "UnicodeEncodeError",
            "problematic_chars": ["ğ", "ı", "ş"],
        }
        exc = TurkishLanguageError("Karakter kodlama hatası", details=details)

        assert "çğıöşü" in exc.details["text"]
        assert "ğ" in exc.details["problematic_chars"]

    def test_turkish_language_error_morphology(self):
        """Test Turkish language error for morphological analysis"""
        details = {
            "word": "gidiyordum",
            "analysis_error": "stem_not_found",
            "suggested_stems": ["git", "gid"],
        }
        exc = TurkishLanguageError("Morfolojik analiz hatası", details=details)

        assert exc.details["word"] == "gidiyordum"
        assert "git" in exc.details["suggested_stems"]


class TestExceptionIntegration:
    """Integration tests for exception handling"""

    def test_exception_inheritance_chain(self):
        """Test that all custom exceptions inherit properly"""
        exceptions_to_test = [
            ValidationError,
            AuthenticationError,
            AuthorizationError,
            DatabaseError,
            ExternalServiceError,
            ConfigurationError,
            BusinessLogicError,
            ResourceNotFoundError,
            RateLimitError,
            ExamError,
            StudentError,
            TeacherError,
            ParentError,
            ContentError,
            TurkishLanguageError,
        ]

        for exc_class in exceptions_to_test:
            exc = exc_class("Test message")
            assert isinstance(exc, TurkishEducationPlatformException)
            assert isinstance(exc, Exception)

    def test_exception_with_nested_details(self):
        """Test exception with complex nested details"""
        details = {
            "user": {
                "id": "12345",
                "role": "student",
                "permissions": ["read", "write"],
            },
            "request": {
                "method": "POST",
                "endpoint": "/api/exams",
                "timestamp": "2023-12-01T10:00:00Z",
            },
            "error_context": {
                "validation_errors": [
                    {"field": "duration", "message": "Must be positive"},
                    {"field": "questions", "message": "At least 10 required"},
                ]
            },
        }

        exc = ValidationError("Karmaşık doğrulama hatası", details=details)

        assert exc.details["user"]["id"] == "12345"
        assert len(exc.details["error_context"]["validation_errors"]) == 2

    def test_exception_str_representation_with_details(self):
        """Test string representation of exceptions with details"""
        details = {"field": "email", "value": "invalid"}
        exc = ValidationError("Email geçersiz", details=details)

        # String representation should show the message
        assert str(exc) == "Email geçersiz"
        # Details should be accessible separately
        assert exc.details is not None

    def test_exception_serialization_compatibility(self):
        """Test that exceptions can be used in logging/serialization contexts"""
        import json

        details = {"error_code": 400, "timestamp": "2023-12-01"}
        exc = ValidationError("Serileştirme testi", details=details)

        # Should be able to create a dict representation
        exc_dict = {
            "message": str(exc),
            "type": exc.__class__.__name__,
            "details": exc.details,
        }

        # Should be JSON serializable
        json_str = json.dumps(exc_dict)
        assert "Serileştirme testi" in json_str

    def test_exception_with_turkish_content_in_details(self):
        """Test exceptions with Turkish content in details"""
        details = {
            "mesaj": "Türkçe hata mesajı",
            "alan": "öğrenci_numarası",
            "değer": "geçersiz_numara",
            "açıklama": "Öğrenci numarası sayısal olmalıdır",
        }

        exc = ValidationError("Türkçe içerik hatası", details=details)

        assert "Türkçe" in exc.details["mesaj"]
        assert "öğrenci_numarası" == exc.details["alan"]
        assert "açıklama" in exc.details


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
