"""
Input Validation ve Sanitization Modülü
Task 23: Security Hardening - Input validation ve sanitization

Bu modül tüm kullanıcı girdilerini doğrular ve temizler.
"""
import re
import html
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, constr, conint
from fastapi import HTTPException, status


class InputValidationError(Exception):
    """Input validation hatası için özel exception"""
    pass


class SecurityValidator:
    """Güvenlik doğrulama ve sanitization sınıfı"""

    # Tehlikeli karakterler ve pattern'ler
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bOR\b.*=.*|1=1|'=')",
        r"(\bUNION\b.*\bSELECT\b)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    # İzin verilen karakterler (whitelist approach)
    ALLOWED_SUBJECT_CHARS = r"^[a-zA-ZçğıöşüÇĞİÖŞÜ0-9\s\-]+$"
    ALLOWED_DIFFICULTY_VALUES = ["başlangıç", "kolay", "orta", "zor", "ileri"]
    ALLOWED_EXAM_TYPES = ["TYT", "AYT", "LGS", "KPSS", "DGS", "ALES"]
    ALLOWED_LEARNING_STYLES = ["visual", "auditory", "kinesthetic", "reading"]

    @staticmethod
    def sanitize_string(value: str, max_length: int = 200) -> str:
        """
        String değeri temizle ve güvenli hale getir.
        Raises InputValidationError if max_length exceeded.
        """
        if not value:
            return ""

        # Null byte kontrolü
        if '\x00' in value:
            raise InputValidationError('String contains null bytes')

        # Trim whitespace
        value = value.strip()

        # Max length kontrolü - raise exception
        if len(value) > max_length:
            raise InputValidationError(f'String exceeds max length of {max_length}')

        # HTML escape (XSS prevention)
        value = html.escape(value)

        # Control characters removal
        value = "".join(char for char in value if ord(char) >= 32 or char in "\n\r\t")

        return value

    @staticmethod
    def validate_no_sql_injection(value: str) -> bool:
        """SQL injection pattern kontrolü"""
        value_upper = value.upper()
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return False
        return True

    @staticmethod
    def validate_no_xss(value: str) -> bool:
        """XSS pattern kontrolü"""
        value_lower = value.lower()
        for pattern in SecurityValidator.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return False
        return True

    @staticmethod
    def validate_subject(subject: str) -> str:
        """Konu adı doğrulama"""
        subject = SecurityValidator.sanitize_string(subject, max_length=100)
        if not re.match(SecurityValidator.ALLOWED_SUBJECT_CHARS, subject):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz konu adı. Sadece harf, rakam, boşluk ve tire kullanılabilir.",
            )
        if not SecurityValidator.validate_no_sql_injection(subject):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Güvenlik nedeniyle istek reddedildi.",
            )
        return subject

    @staticmethod
    def validate_difficulty(difficulty: str) -> str:
        """Zorluk seviyesi doğrulama"""
        difficulty = difficulty.lower().strip()
        if difficulty not in SecurityValidator.ALLOWED_DIFFICULTY_VALUES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz zorluk seviyesi. İzin verilenler: {', '.join(SecurityValidator.ALLOWED_DIFFICULTY_VALUES)}",
            )
        return difficulty

    @staticmethod
    def validate_exam_type(exam_type: str) -> str:
        """Sınav tipi doğrulama"""
        exam_type = exam_type.upper().strip()
        if exam_type not in SecurityValidator.ALLOWED_EXAM_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz sınav tipi. İzin verilenler: {', '.join(SecurityValidator.ALLOWED_EXAM_TYPES)}",
            )
        return exam_type

    @staticmethod
    def validate_learning_style(learning_style: str) -> str:
        """Öğrenme stili doğrulama"""
        learning_style = learning_style.lower().strip()
        if learning_style not in SecurityValidator.ALLOWED_LEARNING_STYLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz öğrenme stili. İzin verilenler: {', '.join(SecurityValidator.ALLOWED_LEARNING_STYLES)}",
            )
        return learning_style

    @staticmethod
    def validate_goals(goals: List[str]) -> List[str]:
        """Hedefler listesi doğrulama"""
        if not goals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="En az bir hedef belirtilmelidir.",
            )
        if len(goals) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maksimum 10 hedef belirtilebilir.",
            )
        validated_goals = []
        for goal in goals:
            goal = SecurityValidator.sanitize_string(goal, max_length=200)
            if not SecurityValidator.validate_no_xss(goal):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Güvenlik nedeniyle istek reddedildi.",
                )
            if not SecurityValidator.validate_no_sql_injection(goal):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Güvenlik nedeniyle istek reddedildi.",
                )
            validated_goals.append(goal)
        return validated_goals

    @staticmethod
    def validate_current_level(current_level: Dict[str, int]) -> Dict[str, int]:
        """Mevcut seviye doğrulama"""
        if not current_level:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="En az bir konu seviyesi belirtilmelidir.",
            )
        if len(current_level) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maksimum 20 konu seviyesi belirtilebilir.",
            )
        validated_level = {}
        for subject, level in current_level.items():
            subject = SecurityValidator.validate_subject(subject)
            if not isinstance(level, int) or level < 0 or level > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Geçersiz seviye değeri: {level}. Seviye 0-100 arası olmalıdır.",
                )
            validated_level[subject] = level
        return validated_level

    # ========== YENİ SANITIZER METODLARI ==========

    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize and validate email address"""
        if not email or not isinstance(email, str):
            raise InputValidationError('Email cannot be empty')
        email = email.strip().lower()
        if ' ' in email:
            raise InputValidationError('Email cannot contain spaces')
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise InputValidationError('Invalid email format')
        local_part = email.split('@')[0]
        if len(local_part) > 64:
            raise InputValidationError('Email local part too long')
        return email

    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize and validate URL - only allow http/https"""
        if not url or not isinstance(url, str):
            raise InputValidationError('Invalid URL: empty or not string')
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            raise InputValidationError(f'Invalid URL scheme: {url}')
        return url

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL - returns bool for backward compatibility"""
        try:
            SecurityValidator.sanitize_url(url)
            return True
        except InputValidationError:
            return False

    @staticmethod
    def sanitize_integer(value, min_value: int = None, max_value: int = None) -> int:
        """Sanitize and validate integer with optional range"""
        try:
            int_val = int(value)
        except (ValueError, TypeError):
            raise InputValidationError(f'Invalid integer: {value}')
        if min_value is not None and int_val < min_value:
            raise InputValidationError(f'Integer {int_val} below minimum {min_value}')
        if max_value is not None and int_val > max_value:
            raise InputValidationError(f'Integer {int_val} above maximum {max_value}')
        return int_val

    @staticmethod
    def validate_integer(value, min_value: int = None, max_value: int = None) -> bool:
        """Validate integer - returns bool for backward compatibility"""
        try:
            SecurityValidator.sanitize_integer(value, min_value, max_value)
            return True
        except InputValidationError:
            return False

    @staticmethod
    def sanitize_float(value) -> float:
        """Sanitize and validate float - reject inf and nan"""
        try:
            float_val = float(value)
        except (ValueError, TypeError):
            raise InputValidationError(f'Invalid float: {value}')
        if float_val != float_val:  # nan check
            raise InputValidationError('Float cannot be NaN')
        if float_val == float('inf') or float_val == float('-inf'):
            raise InputValidationError('Float cannot be infinite')
        return float_val

    @staticmethod
    def validate_float(value) -> bool:
        """Validate float - returns bool for backward compatibility"""
        try:
            SecurityValidator.sanitize_float(value)
            return True
        except InputValidationError:
            return False

    @staticmethod
    def validate_no_null_bytes(value: str) -> bool:
        """Check for null bytes in string"""
        if not isinstance(value, str):
            return True
        if '\x00' in value:
            raise InputValidationError('String contains null bytes')
        return True


# Pydantic modelleri ile enhanced validation

class ValidatedVideoSearchRequest(BaseModel):
    """Doğrulanmış video arama isteği"""

    subject: constr(min_length=1, max_length=100, strip_whitespace=True)
    difficulty: constr(min_length=1, max_length=20, strip_whitespace=True)
    exam_type: constr(min_length=2, max_length=10, strip_whitespace=True)
    max_results: conint(ge=1, le=50) = 20
    search_mode: constr(pattern=r"^(semantic|keyword|hybrid)$") = "semantic"
    custom_query: Optional[constr(max_length=500)] = None

    @field_validator("subject")
    @classmethod
    def validate_subject_field(cls, v):
        return SecurityValidator.validate_subject(v)

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty_field(cls, v):
        return SecurityValidator.validate_difficulty(v)

    @field_validator("exam_type")
    @classmethod
    def validate_exam_type_field(cls, v):
        return SecurityValidator.validate_exam_type(v)

    @field_validator("custom_query")
    @classmethod
    def validate_custom_query_field(cls, v):
        if v:
            v = SecurityValidator.sanitize_string(v, max_length=500)
            if not SecurityValidator.validate_no_xss(v):
                raise ValueError("Güvenlik nedeniyle istek reddedildi.")
            if not SecurityValidator.validate_no_sql_injection(v):
                raise ValueError("Güvenlik nedeniyle istek reddedildi.")
        return v


class ValidatedStudentProfileRequest(BaseModel):
    """Doğrulanmış öğrenci profili isteği"""

    goals: List[constr(min_length=1, max_length=200, strip_whitespace=True)] = Field(
        ..., min_length=1, max_length=10
    )
    currentLevel: Dict[str, conint(ge=0, le=100)]
    learningStyle: constr(min_length=1, max_length=20, strip_whitespace=True)
    preferences: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("goals")
    @classmethod
    def validate_goals_field(cls, v):
        return SecurityValidator.validate_goals(v)

    @field_validator("currentLevel")
    @classmethod
    def validate_current_level_field(cls, v):
        return SecurityValidator.validate_current_level(v)

    @field_validator("learningStyle")
    @classmethod
    def validate_learning_style_field(cls, v):
        return SecurityValidator.validate_learning_style(v)

    @field_validator("preferences")
    @classmethod
    def validate_preferences_field(cls, v):
        if not v:
            return {}
        if len(v) > 20:
            raise ValueError("Maksimum 20 tercih belirtilebilir.")
        sanitized = {}
        for key, value in v.items():
            key = SecurityValidator.sanitize_string(str(key), max_length=50)
            if isinstance(value, str):
                value = SecurityValidator.sanitize_string(value, max_length=200)
            elif isinstance(value, (list, dict)):
                if len(str(value)) > 1000:
                    raise ValueError("Tercih değeri çok büyük.")
            sanitized[key] = value
        return sanitized

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "goals": ["TYT Matematik", "TYT Fizik"],
            "currentLevel": {"matematik": 65, "fizik": 50},
            "learningStyle": "visual",
            "preferences": {
                "video_duration": "medium",
                "channel_preference": ["Tonguç Akademi"],
            },
        }
    })
