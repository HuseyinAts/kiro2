"""
KIRO2 Security Manager
Comprehensive security management for Turkish educational platform
"""

import base64
import html
import ipaddress
import logging
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from urllib.parse import urlparse

import bcrypt
import jwt
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security level enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityConfig:
    """Security configuration"""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    session_timeout_minutes: int = 480  # 8 hours
    csrf_token_expire_minutes: int = 60
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 1000
    trusted_domains: list[str] = None
    encryption_key: str | None = None

    def __post_init__(self):
        if self.trusted_domains is None:
            self.trusted_domains = ["localhost", "127.0.0.1"]
        if self.encryption_key is None:
            self.encryption_key = Fernet.generate_key().decode()


class InputValidator:
    """Secure input validation for Turkish content"""

    # Turkish character patterns
    TURKISH_CHARS = r"çğıİöşüÇĞÖŞÜ"

    # Safe patterns
    PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "username": rf"^[a-zA-Z0-9_{TURKISH_CHARS}]{{3,30}}$",
        "password": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$",
        "name": rf"^[a-zA-Z\s{TURKISH_CHARS}]{{1,50}}$",
        "phone": r"^\+?[1-9]\d{1,14}$",
        "url": r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$",
        "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        "alphanumeric": rf"^[a-zA-Z0-9{TURKISH_CHARS}]+$",
        "numeric": r"^\d+$",
        "text_content": rf"^[a-zA-Z0-9\s.,!?;:()\-_{TURKISH_CHARS}]+$",
    }

    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        r"<script.*?>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript URLs
        r"on\w+\s*=",  # Event handlers
        r"<iframe.*?>.*?</iframe>",  # IFrames
        r"<object.*?>.*?</object>",  # Objects
        r"<embed.*?>",  # Embeds
        r"<link.*?>",  # Link tags
        r"<meta.*?>",  # Meta tags
        r"<form.*?>",  # Form tags
        r"data:.*?base64",  # Data URLs
        r"vbscript:",  # VBScript
        r"expression\s*\(",  # CSS expressions
        r"url\s*\(",  # CSS URLs
        r"@import",  # CSS imports
    ]

    @classmethod
    def validate_input(cls, value: str, pattern_name: str) -> bool:
        """Validate input against pattern"""
        if not value or not isinstance(value, str):
            return False

        if pattern_name not in cls.PATTERNS:
            logger.warning(f"Unknown validation pattern: {pattern_name}")
            return False

        pattern = cls.PATTERNS[pattern_name]
        return bool(re.match(pattern, value))

    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """Sanitize HTML content"""
        if not value:
            return ""

        # HTML escape
        sanitized = html.escape(value)

        # Remove dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized

    @classmethod
    def sanitize_sql(cls, value: str) -> str:
        """Sanitize SQL input (basic prevention)"""
        if not value:
            return ""

        # SQL injection patterns
        sql_patterns = [
            r"'.*?'",  # String literals
            r"--.*",  # SQL comments
            r"/\*.*?\*/",  # Block comments
            r"\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b",
            r"\b(OR|AND)\s+\d+\s*=\s*\d+",  # Always true conditions
            r";\s*$",  # Statement terminators
        ]

        sanitized = value
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized

    @classmethod
    def validate_turkish_content(cls, content: str) -> bool:
        """Validate Turkish text content"""
        if not content:
            return False

        # Check for valid Turkish characters and common punctuation
        allowed_pattern = rf'^[a-zA-Z0-9\s.,!?;:()\-_"{cls.TURKISH_CHARS}]+$'
        return bool(re.match(allowed_pattern, content))

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize file names for Turkish content"""
        if not filename:
            return "file"

        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "", filename)

        # Replace Turkish characters for file system compatibility (optional)
        # turkish_map = {'ç': 'c', 'ğ': 'g', 'ı': 'i', 'İ': 'I', 'ö': 'o', 'ş': 's', 'ü': 'u',
        #                'Ç': 'C', 'Ğ': 'G', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'}
        # for tr_char, en_char in turkish_map.items():
        #     sanitized = sanitized.replace(tr_char, en_char)

        # Limit length
        sanitized = sanitized[:255]

        return sanitized if sanitized else "file"


class PasswordManager:
    """Secure password management with Turkish support"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        if not password:
            raise ValueError("Password cannot be empty")

        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        if not password or not hashed_password:
            return False

        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> dict[str, Any]:
        """Validate password strength with Turkish messages"""
        if not password:
            return {"valid": False, "message": "Şifre boş olamaz", "score": 0}

        issues = []
        score = 0

        # Length check
        if len(password) < 8:
            issues.append("En az 8 karakter olmalı")
        else:
            score += 20

        if len(password) >= 12:
            score += 10

        # Character type checks
        if not re.search(r"[a-z]", password):
            issues.append("En az bir küçük harf içermeli")
        else:
            score += 20

        if not re.search(r"[A-Z]", password):
            issues.append("En az bir büyük harf içermeli")
        else:
            score += 20

        if not re.search(r"\d", password):
            issues.append("En az bir rakam içermeli")
        else:
            score += 20

        if not re.search(r"[@$!%*?&]", password):
            issues.append("En az bir özel karakter içermeli (@$!%*?&)")
        else:
            score += 20

        # Common patterns check - Extended password blacklist
        # SECURITY FIX: Extended with Turkish common passwords
        common_patterns = [
            # English common passwords
            r"123456", r"12345678", r"password", r"password1", r"password123",
            r"qwerty", r"abc123", r"admin", r"admin123", r"user",
            r"test", r"letmein", r"welcome", r"monkey", r"dragon",
            r"master", r"login", r"iloveyou", r"sunshine", r"princess",
            r"football", r"baseball", r"superman", r"trustno1", r"shadow",
            r"qazwsx", r"michael", r"ashley", r"654321", r"11111",
            # Turkish common passwords
            r"sifre", r"sifre123", r"turkiye", r"istanbul", r"ankara",
            r"galatasaray", r"fenerbahce", r"besiktas", r"trabzon",
            r"merhaba", r"sevgi", r"askim", r"12345", r"turk",
            r"teknofest", r"yks", r"tyt", r"ayt", r"egitim",
        ]

        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                issues.append("Yaygın şifre kalıpları kullanmayın")
                score -= 30
                break

        # Sequential characters
        if re.search(r"(.)\1{2,}", password):
            issues.append("Ardışık aynı karakterler kullanmayın")
            score -= 20

        # Keyboard patterns
        keyboard_patterns = ["qwerty", "asdf", "zxcv", "1234", "4321"]
        for pattern in keyboard_patterns:
            if pattern in password.lower():
                issues.append("Klavye düzeni kalıpları kullanmayın")
                score -= 20
                break

        score = max(0, min(100, score))

        return {
            "valid": len(issues) == 0,
            "message": "; ".join(issues) if issues else "Şifre güçlü",
            "score": score,
            "issues": issues,
        }

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate cryptographically secure password"""
        length = max(length, 8)

        # Character sets
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = "@$!%*?&"

        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special),
        ]

        # Fill remaining length
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)

        return "".join(password)


class TokenManager:
    """JWT token management"""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def create_access_token(self, data: dict[str, Any]) -> str:
        """Create JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.config.jwt_access_token_expire_minutes
        )

        payload = {
            **data,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
            "jti": secrets.token_urlsafe(32),  # JWT ID
        }

        return jwt.encode(
            payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm
        )

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.config.jwt_refresh_token_expire_days
        )

        payload = {
            **data,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),
        }

        return jwt.encode(
            payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm
        )

    def verify_token(
        self, token: str, token_type: str = "access"
    ) -> dict[str, Any] | None:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            # Check token type
            if payload.get("type") != token_type:
                logger.warning(
                    f"Invalid token type: expected {token_type}, got {payload.get('type')}"
                )
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def create_csrf_token(self) -> str:
        """Create CSRF token"""
        return secrets.token_urlsafe(32)


class EncryptionManager:
    """Data encryption and decryption"""

    def __init__(self, encryption_key: str):
        self.fernet = Fernet(encryption_key.encode())

    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not data:
            return ""

        encrypted = self.fernet.encrypt(data.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted).decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return ""

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return ""

    def encrypt_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Encrypt sensitive fields in data"""
        sensitive_fields = [
            "password",
            "email",
            "phone",
            "address",
            "ssn",
            "credit_card",
        ]

        encrypted_data = data.copy()
        for field in sensitive_fields:
            if encrypted_data.get(field):
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))

        return encrypted_data


class SecurityAuditor:
    """Security audit and monitoring"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.security_events = []

    def log_security_event(
        self,
        event_type: str,
        severity: SecurityLevel,
        description: str,
        user_id: int | None = None,
        ip_address: str | None = None,
        additional_data: dict[str, Any] | None = None,
    ):
        """Log security event"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "severity": severity.value,
            "description": description,
            "user_id": user_id,
            "ip_address": ip_address,
            "additional_data": additional_data or {},
        }

        self.security_events.append(event)

        # Log to logger based on severity
        if severity == SecurityLevel.CRITICAL:
            logger.critical(f"SECURITY ALERT: {description}")
        elif severity == SecurityLevel.HIGH:
            logger.error(f"SECURITY WARNING: {description}")
        elif severity == SecurityLevel.MEDIUM:
            logger.warning(f"SECURITY NOTICE: {description}")
        else:
            logger.info(f"SECURITY INFO: {description}")

    def detect_suspicious_activity(
        self, user_id: int, ip_address: str, action: str
    ) -> bool:
        """Detect suspicious activity patterns"""
        recent_events = [
            event
            for event in self.security_events
            if event["user_id"] == user_id
            and datetime.fromisoformat(event["timestamp"])
            > datetime.now(timezone.utc) - timedelta(hours=1)
        ]

        # Multiple failed login attempts
        failed_logins = len(
            [event for event in recent_events if event["event_type"] == "failed_login"]
        )

        if failed_logins >= self.config.max_login_attempts:
            self.log_security_event(
                "account_lockout",
                SecurityLevel.HIGH,
                f"Account locked due to {failed_logins} failed login attempts",
                user_id=user_id,
                ip_address=ip_address,
            )
            return True

        # Rapid requests
        rapid_requests = len(
            [
                event
                for event in recent_events
                if datetime.fromisoformat(event["timestamp"])
                > datetime.now(timezone.utc) - timedelta(minutes=1)
            ]
        )

        if rapid_requests > self.config.rate_limit_per_minute:
            self.log_security_event(
                "rate_limit_exceeded",
                SecurityLevel.MEDIUM,
                f"Rate limit exceeded: {rapid_requests} requests in 1 minute",
                user_id=user_id,
                ip_address=ip_address,
            )
            return True

        return False

    def validate_ip_address(self, ip_address: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    def is_trusted_domain(self, domain: str) -> bool:
        """Check if domain is trusted"""
        return domain.lower() in [d.lower() for d in self.config.trusted_domains]

    def validate_referrer(self, referrer: str) -> bool:
        """Validate HTTP referrer"""
        if not referrer:
            return True  # Allow empty referrer

        try:
            parsed = urlparse(referrer)
            return self.is_trusted_domain(parsed.netloc)
        except Exception:
            return False

    def get_security_report(self, hours: int = 24) -> dict[str, Any]:
        """Generate security report"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_events = [
            event
            for event in self.security_events
            if datetime.fromisoformat(event["timestamp"]) > cutoff
        ]

        report = {
            "total_events": len(recent_events),
            "events_by_severity": {},
            "events_by_type": {},
            "unique_users": set(),
            "unique_ips": set(),
            "critical_events": [],
        }

        for event in recent_events:
            # Count by severity
            severity = event["severity"]
            report["events_by_severity"][severity] = (
                report["events_by_severity"].get(severity, 0) + 1
            )

            # Count by type
            event_type = event["event_type"]
            report["events_by_type"][event_type] = (
                report["events_by_type"].get(event_type, 0) + 1
            )

            # Collect unique users and IPs
            if event["user_id"]:
                report["unique_users"].add(event["user_id"])
            if event["ip_address"]:
                report["unique_ips"].add(event["ip_address"])

            # Collect critical events
            if event["severity"] == SecurityLevel.CRITICAL.value:
                report["critical_events"].append(event)

        # Convert sets to counts
        report["unique_users"] = len(report["unique_users"])
        report["unique_ips"] = len(report["unique_ips"])

        return report


class SecurityManager:
    """Main security manager class"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager(config)
        self.encryption_manager = EncryptionManager(config.encryption_key)
        self.auditor = SecurityAuditor(config)
        self.validator = InputValidator()

    def authenticate_user(
        self, username_or_email: str, password: str, ip_address: str
    ) -> dict[str, Any] | None:
        """Authenticate user with security checks"""
        # Validate inputs
        if not self.validator.validate_input(
            username_or_email, "email"
        ) and not self.validator.validate_input(username_or_email, "username"):
            self.auditor.log_security_event(
                "invalid_credentials_format",
                SecurityLevel.LOW,
                "Invalid username/email format",
                ip_address=ip_address,
            )
            return None

        # Check for suspicious activity
        # Note: This would typically involve checking the database for user_id
        # For now, we'll simulate it
        if self.auditor.detect_suspicious_activity(0, ip_address, "login"):
            return None

        # Here you would check credentials against the database
        # For this example, we'll simulate a successful authentication

        user_data = {
            "user_id": 1,
            "username": username_or_email,
            "role": "student",
            "permissions": ["read", "write"],
        }

        # Create tokens
        access_token = self.token_manager.create_access_token(user_data)
        refresh_token = self.token_manager.create_refresh_token(
            {"user_id": user_data["user_id"]}
        )

        # Log successful authentication
        self.auditor.log_security_event(
            "successful_login",
            SecurityLevel.LOW,
            f"User {username_or_email} logged in successfully",
            user_id=user_data["user_id"],
            ip_address=ip_address,
        )

        return {
            "user": user_data,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def validate_request_security(
        self, request_data: dict[str, Any], ip_address: str, referrer: str = None
    ) -> dict[str, Any]:
        """Validate request security"""
        issues = []

        # Validate IP address
        if not self.auditor.validate_ip_address(ip_address):
            issues.append("Invalid IP address format")

        # Validate referrer
        if referrer and not self.auditor.validate_referrer(referrer):
            issues.append("Untrusted referrer domain")

        # Validate input data
        for key, value in request_data.items():
            if isinstance(value, str):
                # Check for XSS attempts
                if any(
                    pattern in value.lower()
                    for pattern in ["<script", "javascript:", "on"]
                ):
                    issues.append(f"Potential XSS in field: {key}")

                # Check for SQL injection attempts
                sql_keywords = [
                    "union",
                    "select",
                    "insert",
                    "drop",
                    "delete",
                    "--",
                    "/*",
                ]
                if any(keyword in value.lower() for keyword in sql_keywords):
                    issues.append(f"Potential SQL injection in field: {key}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "security_level": SecurityLevel.HIGH if issues else SecurityLevel.LOW,
        }

    def create_secure_session(self, user_id: int) -> dict[str, Any]:
        """Create secure session"""
        session_id = secrets.token_urlsafe(32)
        csrf_token = self.token_manager.create_csrf_token()

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "csrf_token": csrf_token,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(minutes=self.config.session_timeout_minutes)
            ).isoformat(),
        }

        return session_data

    def get_security_headers(self) -> dict[str, str]:
        """Get security headers for responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }


# Global security manager instance
security_manager: SecurityManager | None = None


def get_security_manager() -> SecurityManager:
    """Get global security manager instance"""
    global security_manager

    if security_manager is None:
        config = SecurityConfig(
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32)),
            encryption_key=os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode()),
        )
        security_manager = SecurityManager(config)

    return security_manager


# Usage examples
async def secure_login_example():
    """Example of secure login process"""
    sm = get_security_manager()

    # Authenticate user
    result = sm.authenticate_user(
        username_or_email="user@example.com",
        password="SecurePass123!",
        ip_address="192.168.1.100",
    )

    if result:
        print("Authentication successful!")
        print(f"Access token: {result['access_token'][:20]}...")
    else:
        print("Authentication failed!")


async def validate_user_input_example():
    """Example of input validation"""
    sm = get_security_manager()

    # Test password strength
    password_check = sm.password_manager.validate_password_strength("WeakPass")
    print(f"Password strength: {password_check}")

    # Validate Turkish content
    turkish_text = "Merhaba dünya! Bu Türkçe bir içeriktir."
    is_valid = sm.validator.validate_turkish_content(turkish_text)
    print(f"Turkish content valid: {is_valid}")

    # Sanitize HTML
    html_content = "<script>alert('xss')</script>Güvenli içerik"
    sanitized = sm.validator.sanitize_html(html_content)
    print(f"Sanitized HTML: {sanitized}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(secure_login_example())
    asyncio.run(validate_user_input_example())
