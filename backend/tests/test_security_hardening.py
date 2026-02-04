"""
Security Hardening Tests
Task 23: Security Hardening - Test suite

Bu test suite tüm güvenlik önlemlerini test eder.
"""
import pytest
from fastapi import HTTPException
from core.input_validation import SecurityValidator, ValidatedStudentProfileRequest
from core.sql_injection_prevention import SQLInjectionPrevention, SafeQueryBuilder
from core.xss_prevention import XSSPrevention
from core.cors_security import validate_origin


class TestInputValidation:
    """Input validation tests"""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        result = SecurityValidator.sanitize_string("  Hello World  ")
        assert result == "Hello World"

    def test_sanitize_string_html_escape(self):
        """Test HTML escaping"""
        result = SecurityValidator.sanitize_string("<script>alert('XSS')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_string_max_length(self):
        """Test max length enforcement"""
        long_string = "a" * 300
        result = SecurityValidator.sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_validate_subject_valid(self):
        """Test valid subject validation"""
        result = SecurityValidator.validate_subject("Matematik")
        assert result == "Matematik"

    def test_validate_subject_turkish_chars(self):
        """Test Turkish characters in subject"""
        result = SecurityValidator.validate_subject("Türkçe")
        assert result == "Türkçe"

    def test_validate_subject_invalid_chars(self):
        """Test invalid characters in subject"""
        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_subject("Matematik<script>")
        assert exc_info.value.status_code == 400

    def test_validate_difficulty_valid(self):
        """Test valid difficulty validation"""
        result = SecurityValidator.validate_difficulty("orta")
        assert result == "orta"

    def test_validate_difficulty_invalid(self):
        """Test invalid difficulty validation"""
        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_difficulty("invalid")
        assert exc_info.value.status_code == 400

    def test_validate_exam_type_valid(self):
        """Test valid exam type validation"""
        result = SecurityValidator.validate_exam_type("TYT")
        assert result == "TYT"

    def test_validate_exam_type_invalid(self):
        """Test invalid exam type validation"""
        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_exam_type("INVALID")
        assert exc_info.value.status_code == 400

    def test_validate_goals_valid(self):
        """Test valid goals validation"""
        goals = ["TYT Matematik", "TYT Fizik"]
        result = SecurityValidator.validate_goals(goals)
        assert len(result) == 2

    def test_validate_goals_empty(self):
        """Test empty goals validation"""
        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_goals([])
        assert exc_info.value.status_code == 400

    def test_validate_goals_too_many(self):
        """Test too many goals validation"""
        goals = [f"Goal {i}" for i in range(15)]
        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_goals(goals)
        assert exc_info.value.status_code == 400

    def test_validate_current_level_valid(self):
        """Test valid current level validation"""
        level = {"matematik": 50, "fizik": 70}
        result = SecurityValidator.validate_current_level(level)
        assert result == level

    def test_validate_current_level_invalid_range(self):
        """Test invalid level range"""
        level = {"matematik": 150}
        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_current_level(level)
        assert exc_info.value.status_code == 400

    def test_validate_no_sql_injection_safe(self):
        """Test safe string (no SQL injection)"""
        result = SecurityValidator.validate_no_sql_injection("matematik")
        assert result is True

    def test_validate_no_sql_injection_dangerous(self):
        """Test dangerous SQL injection pattern"""
        result = SecurityValidator.validate_no_sql_injection("matematik' OR '1'='1")
        assert result is False

    def test_validate_no_xss_safe(self):
        """Test safe string (no XSS)"""
        result = SecurityValidator.validate_no_xss("Normal text")
        assert result is True

    def test_validate_no_xss_dangerous(self):
        """Test dangerous XSS pattern"""
        result = SecurityValidator.validate_no_xss("<script>alert('XSS')</script>")
        assert result is False


class TestSQLInjectionPrevention:
    """SQL injection prevention tests"""

    def test_is_safe_identifier_valid(self):
        """Test valid identifier"""
        assert SQLInjectionPrevention.is_safe_identifier("video_cache") is True
        assert SQLInjectionPrevention.is_safe_identifier("subject") is True

    def test_is_safe_identifier_invalid(self):
        """Test invalid identifier"""
        assert SQLInjectionPrevention.is_safe_identifier("video-cache") is False
        assert SQLInjectionPrevention.is_safe_identifier("SELECT") is False
        assert SQLInjectionPrevention.is_safe_identifier("1table") is False

    def test_validate_query_params_safe(self):
        """Test safe query params"""
        params = {"subject": "matematik", "difficulty": "orta"}
        result = SQLInjectionPrevention.validate_query_params(params)
        assert result == params

    def test_validate_query_params_sql_injection(self):
        """Test SQL injection in params"""
        params = {"subject": "matematik' OR '1'='1"}
        with pytest.raises(HTTPException) as exc_info:
            SQLInjectionPrevention.validate_query_params(params)
        assert exc_info.value.status_code == 400

    def test_build_safe_query_basic(self):
        """Test basic safe query building"""
        query, params = SQLInjectionPrevention.build_safe_query(
            base_query="SELECT * FROM video_cache",
            filters={"subject": "matematik"},
            limit=20,
        )

        assert "SELECT * FROM video_cache" in query
        assert "WHERE subject = :param_subject" in query
        assert "LIMIT :limit_value" in query
        assert params["param_subject"] == "matematik"
        assert params["limit_value"] == 20

    def test_build_safe_query_invalid_column(self):
        """Test invalid column name"""
        with pytest.raises(HTTPException) as exc_info:
            SQLInjectionPrevention.build_safe_query(
                base_query="SELECT * FROM video_cache",
                order_by="subject; DROP TABLE users; --",
            )
        assert exc_info.value.status_code == 400

    def test_safe_query_builder(self):
        """Test SafeQueryBuilder"""
        builder = SafeQueryBuilder("video_cache")
        builder.where(subject="matematik", difficulty="orta")
        builder.order_by("quality_score")
        builder.limit(20)

        query, params = builder.build()

        assert "SELECT * FROM video_cache" in query
        assert "WHERE" in query
        assert "ORDER BY quality_score" in query
        assert "LIMIT" in query

    def test_safe_query_builder_invalid_table(self):
        """Test invalid table name"""
        with pytest.raises(HTTPException) as exc_info:
            SafeQueryBuilder("video_cache; DROP TABLE users; --")
        assert exc_info.value.status_code == 400


class TestXSSPrevention:
    """XSS prevention tests"""

    def test_escape_html_basic(self):
        """Test basic HTML escaping"""
        result = XSSPrevention.escape_html("<script>alert('XSS')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_remove_dangerous_tags(self):
        """Test dangerous tag removal"""
        html = "<div>Safe</div><script>alert('XSS')</script><p>More safe</p>"
        result = XSSPrevention.remove_dangerous_tags(html)
        assert "<script>" not in result
        assert "<div>Safe</div>" in result

    def test_remove_dangerous_attributes(self):
        """Test dangerous attribute removal"""
        html = "<div onclick=\"alert('XSS')\">Click me</div>"
        result = XSSPrevention.remove_dangerous_attributes(html)
        assert "onclick" not in result

    def test_remove_dangerous_protocols(self):
        """Test dangerous protocol removal"""
        assert XSSPrevention.remove_dangerous_protocols("javascript:alert('XSS')") == ""
        assert (
            XSSPrevention.remove_dangerous_protocols("https://example.com")
            == "https://example.com"
        )

    def test_sanitize_text_no_html(self):
        """Test text sanitization without HTML"""
        result = XSSPrevention.sanitize_text(
            "<script>alert('XSS')</script>", allow_html=False
        )
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_text_with_html(self):
        """Test text sanitization with HTML allowed"""
        result = XSSPrevention.sanitize_text(
            "<div>Safe</div><script>alert('XSS')</script>", allow_html=True
        )
        assert "<div>Safe</div>" in result
        assert "<script>" not in result

    def test_sanitize_dict(self):
        """Test dictionary sanitization"""
        data = {"title": "<script>alert('XSS')</script>", "description": "Normal text"}
        result = XSSPrevention.sanitize_dict(data)
        assert "<script>" not in result["title"]
        assert result["description"] == "Normal text"

    def test_sanitize_list(self):
        """Test list sanitization"""
        data = ["<script>alert('XSS')</script>", "Normal text"]
        result = XSSPrevention.sanitize_list(data)
        assert "<script>" not in result[0]
        assert result[1] == "Normal text"


class TestCORSSecurity:
    """CORS security tests"""

    def test_validate_origin_allowed_development(self):
        """Test allowed development origin"""
        # Mock environment
        import os

        os.environ["ENVIRONMENT"] = "development"

        assert validate_origin("http://localhost:3001") is True
        assert validate_origin("http://localhost:3000") is True

    def test_validate_origin_not_allowed(self):
        """Test not allowed origin"""
        import os

        os.environ["ENVIRONMENT"] = "development"

        assert validate_origin("https://evil.com") is False

    def test_validate_origin_production(self):
        """Test production origin validation"""
        import os

        os.environ["ENVIRONMENT"] = "production"

        assert validate_origin("https://kiro2.app") is True
        assert validate_origin("http://localhost:3001") is False


class TestPydanticValidation:
    """Pydantic model validation tests"""

    def test_validated_student_profile_valid(self):
        """Test valid student profile"""
        data = {
            "goals": ["TYT Matematik", "TYT Fizik"],
            "currentLevel": {"matematik": 50, "fizik": 70},
            "learningStyle": "visual",
            "preferences": {},
        }

        profile = ValidatedStudentProfileRequest(**data)
        assert len(profile.goals) == 2
        assert profile.currentLevel["matematik"] == 50

    def test_validated_student_profile_invalid_goals(self):
        """Test invalid goals"""
        data = {
            "goals": [],  # Empty goals
            "currentLevel": {"matematik": 50},
            "learningStyle": "visual",
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            ValidatedStudentProfileRequest(**data)

    def test_validated_student_profile_invalid_level(self):
        """Test invalid level"""
        data = {
            "goals": ["TYT Matematik"],
            "currentLevel": {"matematik": 150},  # Out of range
            "learningStyle": "visual",
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            ValidatedStudentProfileRequest(**data)

    def test_validated_student_profile_invalid_learning_style(self):
        """Test invalid learning style"""
        data = {
            "goals": ["TYT Matematik"],
            "currentLevel": {"matematik": 50},
            "learningStyle": "invalid",  # Not in whitelist
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            ValidatedStudentProfileRequest(**data)


# Integration tests
class TestSecurityIntegration:
    """Integration tests for security measures"""

    def test_full_validation_pipeline(self):
        """Test full validation pipeline"""
        # Simulate user input
        user_input = {
            "goals": ["  TYT Matematik  ", "TYT Fizik"],
            "currentLevel": {"matematik": 50, "fizik": 70},
            "learningStyle": "visual",
            "preferences": {"video_duration": "medium"},
        }

        # Validate with Pydantic
        profile = ValidatedStudentProfileRequest(**user_input)

        # Check sanitization
        assert profile.goals[0] == "TYT Matematik"  # Trimmed
        assert profile.currentLevel["matematik"] == 50

    def test_sql_injection_prevention_pipeline(self):
        """Test SQL injection prevention pipeline"""
        # Simulate malicious input
        malicious_subject = "matematik' OR '1'='1"

        # Validation should fail
        with pytest.raises(HTTPException):
            SecurityValidator.validate_subject(malicious_subject)

    def test_xss_prevention_pipeline(self):
        """Test XSS prevention pipeline"""
        # Simulate malicious input
        malicious_goal = "<script>alert('XSS')</script>"

        # Sanitization should escape
        sanitized = SecurityValidator.sanitize_string(malicious_goal)
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
