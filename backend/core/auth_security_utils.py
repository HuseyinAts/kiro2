"""
KIRO2 Authentication Security Utilities
Comprehensive security utilities for authentication and authorization
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import hashlib
import ipaddress
import logging
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from io import BytesIO
from typing import Any

import bcrypt
import geoip2.database
import geoip2.errors
import pyotp
import qrcode

from core.exceptions import ValidationError
from core.unified_config import get_unified_config

logger = logging.getLogger(__name__)
config = get_unified_config()


class SecurityLevel(Enum):
    """Security level enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Security threat type enumeration"""

    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    CSRF_ATTACK = "csrf_attack"
    BOT_ACTIVITY = "bot_activity"
    SUSPICIOUS_IP = "suspicious_ip"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DEVICE_ANOMALY = "device_anomaly"
    LOCATION_ANOMALY = "location_anomaly"
    TIME_ANOMALY = "time_anomaly"


@dataclass
class SecurityThreat:
    """Security threat information"""

    threat_type: ThreatType
    severity: SecurityLevel
    description: str
    ip_address: str = ""
    user_id: int | None = None
    timestamp: datetime = None
    additional_data: dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class LocationInfo:
    """Geographic location information"""

    country: str = ""
    country_code: str = ""
    city: str = ""
    region: str = ""
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = ""
    is_vpn: bool = False
    is_tor: bool = False
    is_datacenter: bool = False


class PasswordSecurityManager:
    """Advanced password security management"""

    # Common Turkish passwords to check against
    TURKISH_COMMON_PASSWORDS = [
        "123456",
        "password",
        "123456789",
        "12345678",
        "12345",
        "1234567",
        "sifre",
        "şifre",
        "admin",
        "test",
        "user",
        "kullanici",
        "kullanıcı",
        "ankara",
        "istanbul",
        "izmir",
        "türkiye",
        "turkiye",
        "merhaba",
        "selam",
        "aşk",
        "ask",
        "sevgi",
        "güven",
        "guven",
        "dostluk",
        "arkadaş",
        "arkadas",
        "qwerty",
        "asdf",
        "zxcv",
        "qwe123",
    ]

    # Keyboard patterns
    KEYBOARD_PATTERNS = [
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm",
        "1234567890",
        "qwerty",
        "asdfg",
        "zxcvb",
        "123456",
        "098765",
    ]

    @staticmethod
    def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
        """Hash password with bcrypt and return hash and salt"""
        if not password:
            raise ValidationError("Şifre boş olamaz")

        if salt is None:
            # S179 fix (B-P0-12): bcrypt cost env-configurable.
            # Pre-fix hard-coded rounds=12 cost ~300 ms verify, which
            # dominated login latency (Locust p50=1300ms). NIST permits
            # >=10. Default still 12 for safety; deploys with serious
            # latency budget (load test 100+ concurrent students) can
            # set BCRYPT_ROUNDS=10 → ~75 ms verify.
            import os as _os

            try:
                _rounds = int(_os.environ.get("BCRYPT_ROUNDS", "12"))
            except ValueError:
                _rounds = 12
            _rounds = max(10, min(_rounds, 14))  # NIST floor / sane ceiling
            salt = bcrypt.gensalt(rounds=_rounds)

        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8"), salt.decode("utf-8")

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

    @classmethod
    def analyze_password_strength(cls, password: str) -> dict[str, Any]:
        """Comprehensive password strength analysis"""
        if not password:
            return {
                "score": 0,
                "level": SecurityLevel.LOW.value,
                "issues": ["Şifre boş olamaz"],
                "suggestions": ["En az 8 karakter uzunluğunda şifre girin"],
            }

        score = 0
        issues = []
        suggestions = []

        # Length checks
        if len(password) < 8:
            issues.append("En az 8 karakter olmalı")
            suggestions.append("Şifrenizi en az 8 karakter yapın")
        elif len(password) < 12:
            score += 10
            suggestions.append("Daha güvenli olmak için 12+ karakter kullanın")
        else:
            score += 20

        # Character diversity checks
        has_lower = bool(re.search(r"[a-züşğıöçİĞÜÇÖŞ]", password))
        has_upper = bool(re.search(r"[A-ZÜĞIİÇÖŞ]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

        if has_lower:
            score += 15
        else:
            issues.append("Küçük harf içermeli")
            suggestions.append("En az bir küçük harf ekleyin")

        if has_upper:
            score += 15
        else:
            issues.append("Büyük harf içermeli")
            suggestions.append("En az bir büyük harf ekleyin")

        if has_digit:
            score += 15
        else:
            issues.append("Rakam içermeli")
            suggestions.append("En az bir rakam ekleyin")

        if has_special:
            score += 15
        else:
            issues.append("Özel karakter içermeli (!@#$%^&* vb.)")
            suggestions.append("En az bir özel karakter ekleyin")

        # Pattern checks
        if password.lower() in [p.lower() for p in cls.TURKISH_COMMON_PASSWORDS]:
            score -= 30
            issues.append("Yaygın şifre kullanımı")
            suggestions.append("Daha özgün bir şifre seçin")

        # Sequential characters
        if cls._has_sequential_chars(password):
            score -= 20
            issues.append("Ardışık karakterler içeriyor")
            suggestions.append("Ardışık karakterlerden kaçının (123, abc vb.)")

        # Keyboard patterns
        if cls._has_keyboard_pattern(password):
            score -= 20
            issues.append("Klavye düzeni kalıbı içeriyor")
            suggestions.append("Klavye düzeni kalıplarından kaçının (qwerty vb.)")

        # Repeated characters
        if cls._has_repeated_chars(password):
            score -= 15
            issues.append("Tekrarlanan karakterler içeriyor")
            suggestions.append("Aynı karakterleri art arda kullanmayın")

        # Personal info patterns (basic check)
        if cls._contains_personal_info_pattern(password):
            score -= 25
            issues.append("Kişisel bilgi kalıbı içerebilir")
            suggestions.append("Doğum tarihi, isim gibi kişisel bilgileri kullanmayın")

        # Calculate final score
        score = max(0, min(100, score))

        # Determine security level
        if score >= 80:
            level = SecurityLevel.HIGH.value
        elif score >= 60:
            level = SecurityLevel.MEDIUM.value
        else:
            level = SecurityLevel.LOW.value

        return {
            "score": score,
            "level": level,
            "issues": issues,
            "suggestions": suggestions,
            "character_diversity": {
                "has_lowercase": has_lower,
                "has_uppercase": has_upper,
                "has_digits": has_digit,
                "has_special": has_special,
            },
        }

    @staticmethod
    def _has_sequential_chars(password: str) -> bool:
        """Check for sequential characters"""
        sequences = [
            "0123456789",
            "abcdefghijklmnopqrstuvwxyz",
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm",
        ]

        for seq in sequences:
            for i in range(len(seq) - 2):
                if seq[i : i + 3] in password.lower():
                    return True
                if seq[i : i + 3][::-1] in password.lower():  # Reverse sequence
                    return True
        return False

    @classmethod
    def _has_keyboard_pattern(cls, password: str) -> bool:
        """Check for keyboard patterns"""
        for pattern in cls.KEYBOARD_PATTERNS:
            for i in range(len(pattern) - 2):
                if pattern[i : i + 3] in password.lower():
                    return True
        return False

    @staticmethod
    def _has_repeated_chars(password: str) -> bool:
        """Check for repeated characters"""
        return bool(re.search(r"(.)\1{2,}", password))

    @staticmethod
    def _contains_personal_info_pattern(password: str) -> bool:
        """Check for common personal info patterns"""
        # Date patterns
        date_patterns = [
            r"\d{2}[./\-]\d{2}[./\-]\d{4}",  # dd.mm.yyyy
            r"\d{4}[./\-]\d{2}[./\-]\d{2}",  # yyyy.mm.dd
            r"\d{2}\d{2}\d{4}",  # ddmmyyyy
            r"\d{4}\d{2}\d{2}",  # yyyymmdd
            r"\d{2}\d{2}\d{2}",  # ddmmyy
        ]

        for pattern in date_patterns:
            if re.search(pattern, password):
                return True

        # Phone-like patterns
        if re.search(r"\d{10,11}", password):
            return True

        return False

    @staticmethod
    def generate_secure_password(
        length: int = 16, include_turkish: bool = False
    ) -> str:
        """Generate cryptographically secure password"""
        length = max(length, 8)

        # Character sets
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if include_turkish:
            lowercase += "çğıöşü"
            uppercase += "ÇĞIİÖŞÜ"

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


class InputSecurityValidator:
    """Advanced input validation and sanitization"""

    # Turkish character support
    TURKISH_CHARS = "çğıİöşüÇĞÖŞÜ"

    # Validation patterns
    PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "username": rf"^[a-zA-Z0-9_.-{TURKISH_CHARS}]{{3,30}}$",
        "phone_tr": r"^(\+90|0)?[5][0-9]{9}$",  # Turkish mobile
        "tc_no": r"^[1-9][0-9]{10}$",  # Turkish ID number
        "name": rf"^[a-zA-Z\s{TURKISH_CHARS}]{{1,50}}$",
        "text_content": rf"^[a-zA-Z0-9\s.,!?;:()\\-_{TURKISH_CHARS}]*$",
        "url": r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$",
        "slug": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        "hex_color": r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    }

    # Dangerous patterns for security scanning
    SECURITY_PATTERNS = {
        "sql_injection": [
            r"('[^']*'[^']*')|(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)",
            r"(--|#|/\*|\*/)",
            r"(\bOR\b|\bAND\b)\s+['\"]?\d+['\"]?\s*[=<>]",
            r";\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER|EXEC)",
            r"(UNION|SELECT).*FROM",
            r"'[^']*'[^']*'|\"[^\"]*\"[^\"]*\"",
        ],
        "xss": [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"data:.*?base64",
            r"vbscript:",
            r"expression\s*\(",
            r"@import",
        ],
        "path_traversal": [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
            r"\.\.%2f",
            r"\.\.%5c",
        ],
        "command_injection": [
            r"[;&|`$]",
            r"(\|\||&&)",
            r"\$\([^)]+\)",
            r"`[^`]+`",
            r"\\x[0-9a-fA-F]{2}",
            r"\\[0-7]{3}",
        ],
    }

    @classmethod
    def validate_input(
        cls, value: str, pattern_name: str, required: bool = True
    ) -> bool:
        """Validate input against a specific pattern"""
        if not value:
            return not required

        if not isinstance(value, str):
            return False

        if pattern_name not in cls.PATTERNS:
            logger.warning(f"Unknown validation pattern: {pattern_name}")
            return False

        pattern = cls.PATTERNS[pattern_name]
        return bool(re.match(pattern, value, re.IGNORECASE))

    @classmethod
    def scan_for_security_threats(cls, value: str) -> list[SecurityThreat]:
        """Scan input for security threats"""
        threats = []

        if not value or not isinstance(value, str):
            return threats

        # Check for SQL injection
        for pattern in cls.SECURITY_PATTERNS["sql_injection"]:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append(
                    SecurityThreat(
                        threat_type=ThreatType.SQL_INJECTION,
                        severity=SecurityLevel.HIGH,
                        description=f"Potansiyel SQL injection tespit edildi: {pattern}",
                        additional_data={"pattern": pattern, "input": value[:100]},
                    )
                )

        # Check for XSS
        for pattern in cls.SECURITY_PATTERNS["xss"]:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append(
                    SecurityThreat(
                        threat_type=ThreatType.XSS_ATTACK,
                        severity=SecurityLevel.HIGH,
                        description=f"Potansiyel XSS saldırısı tespit edildi: {pattern}",
                        additional_data={"pattern": pattern, "input": value[:100]},
                    )
                )

        # Check for path traversal
        for pattern in cls.SECURITY_PATTERNS["path_traversal"]:
            if re.search(pattern, value, re.IGNORECASE):
                threats.append(
                    SecurityThreat(
                        threat_type=ThreatType.SUSPICIOUS_IP,  # Using as general threat type
                        severity=SecurityLevel.MEDIUM,
                        description=f"Potansiyel path traversal saldırısı: {pattern}",
                        additional_data={"pattern": pattern, "input": value[:100]},
                    )
                )

        # Check for command injection
        for pattern in cls.SECURITY_PATTERNS["command_injection"]:
            if re.search(pattern, value):
                threats.append(
                    SecurityThreat(
                        threat_type=ThreatType.SUSPICIOUS_IP,  # Using as general threat type
                        severity=SecurityLevel.HIGH,
                        description=f"Potansiyel command injection: {pattern}",
                        additional_data={"pattern": pattern, "input": value[:100]},
                    )
                )

        return threats

    @classmethod
    def sanitize_input(cls, value: str, allow_html: bool = False) -> str:
        """Sanitize input string"""
        if not value:
            return ""

        # Remove null bytes
        value = value.replace("\x00", "")

        if not allow_html:
            # HTML escape
            value = value.replace("&", "&amp;")
            value = value.replace("<", "&lt;")
            value = value.replace(">", "&gt;")
            value = value.replace('"', "&quot;")
            value = value.replace("'", "&#x27;")

        # Remove dangerous patterns
        for threat_type, patterns in cls.SECURITY_PATTERNS.items():
            for pattern in patterns:
                value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        return value.strip()

    @classmethod
    def validate_turkish_tc_number(cls, tc_no: str) -> bool:
        """Validate Turkish TC (ID) number"""
        if not tc_no or len(tc_no) != 11 or not tc_no.isdigit():
            return False

        if tc_no[0] == "0":  # TC numbers don't start with 0
            return False

        # TC number algorithm validation
        digits = [int(d) for d in tc_no]

        # Check 10th digit
        odd_sum = sum(digits[i] for i in range(0, 9, 2))  # 1st, 3rd, 5th, 7th, 9th
        even_sum = sum(digits[i] for i in range(1, 8, 2))  # 2nd, 4th, 6th, 8th

        check_10 = (odd_sum * 7 - even_sum) % 10
        if check_10 != digits[9]:
            return False

        # Check 11th digit
        check_11 = sum(digits[:10]) % 10
        if check_11 != digits[10]:
            return False

        return True

    @classmethod
    def validate_turkish_phone(cls, phone: str) -> bool:
        """Validate Turkish phone number"""
        if not phone:
            return False

        # Clean phone number
        phone = re.sub(r"[^\d+]", "", phone)

        # Turkish mobile number patterns
        patterns = [
            r"^(\+90|90)?5[0-9]{9}$",  # Mobile with country code
            r"^05[0-9]{9}$",  # Mobile without country code
        ]

        return any(re.match(pattern, phone) for pattern in patterns)


class IPSecurityManager:
    """IP address security analysis and management"""

    def __init__(self):
        self.trusted_networks = self._load_trusted_networks()
        self.blocked_ips: set[str] = set()
        self.suspicious_ips: set[str] = set()
        self.geo_db_path = None  # Path to GeoIP database if available

    def _load_trusted_networks(self) -> list[ipaddress.IPv4Network]:
        """Load trusted IP networks"""
        # Default trusted networks
        trusted = [
            ipaddress.IPv4Network("127.0.0.0/8"),  # Loopback
            ipaddress.IPv4Network("10.0.0.0/8"),  # Private A
            ipaddress.IPv4Network("172.16.0.0/12"),  # Private B
            ipaddress.IPv4Network("192.168.0.0/16"),  # Private C
        ]

        # Add configured trusted networks
        if hasattr(config.security, "trusted_networks"):
            for network in config.security.trusted_networks:
                try:
                    trusted.append(ipaddress.IPv4Network(network))
                except Exception as e:
                    logger.warning(f"Invalid trusted network: {network}, {e}")

        return trusted

    def is_valid_ip(self, ip_address: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    def is_private_ip(self, ip_address: str) -> bool:
        """Check if IP is in private range"""
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private
        except ValueError:
            return False

    def is_trusted_ip(self, ip_address: str) -> bool:
        """Check if IP is in trusted networks"""
        try:
            ip = ipaddress.ip_address(ip_address)
            return any(ip in network for network in self.trusted_networks)
        except ValueError:
            return False

    def is_blocked_ip(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        return ip_address in self.blocked_ips

    def is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP is marked as suspicious"""
        return ip_address in self.suspicious_ips

    def block_ip(self, ip_address: str, reason: str = "security_violation"):
        """Block IP address"""
        self.blocked_ips.add(ip_address)
        logger.warning(f"IP {ip_address} blocked: {reason}")

    def mark_suspicious(self, ip_address: str, reason: str = "unusual_activity"):
        """Mark IP as suspicious"""
        self.suspicious_ips.add(ip_address)
        logger.info(f"IP {ip_address} marked suspicious: {reason}")

    def get_location_info(self, ip_address: str) -> LocationInfo:
        """Get geographic information for IP address"""
        location = LocationInfo()

        if not self.geo_db_path or self.is_private_ip(ip_address):
            return location

        try:
            with geoip2.database.Reader(self.geo_db_path) as reader:
                response = reader.city(ip_address)

                location.country = response.country.name or ""
                location.country_code = response.country.iso_code or ""
                location.city = response.city.name or ""
                location.region = response.subdivisions.most_specific.name or ""
                location.latitude = float(response.location.latitude or 0)
                location.longitude = float(response.location.longitude or 0)
                location.timezone = response.location.time_zone or ""

        except (geoip2.errors.AddressNotFoundError, FileNotFoundError, Exception) as e:
            logger.debug(f"Could not get location for IP {ip_address}: {e}")

        return location

    def analyze_ip_risk(
        self, ip_address: str, user_history: list[str] = None
    ) -> dict[str, Any]:
        """Analyze IP address risk level"""
        risk_score = 0
        risk_factors = []

        # Basic validations
        if not self.is_valid_ip(ip_address):
            return {
                "risk_level": SecurityLevel.HIGH.value,
                "score": 100,
                "factors": ["Invalid IP format"],
            }

        # Check if blocked
        if self.is_blocked_ip(ip_address):
            risk_score += 50
            risk_factors.append("IP is blocked")

        # Check if suspicious
        if self.is_suspicious_ip(ip_address):
            risk_score += 30
            risk_factors.append("IP marked as suspicious")

        # Check if from known bad ranges (simplified)
        if self._is_from_bad_range(ip_address):
            risk_score += 40
            risk_factors.append("IP from suspicious range")

        # Geographic analysis
        location = self.get_location_info(ip_address)
        if location.country_code and location.country_code not in [
            "TR",
            "US",
            "GB",
            "DE",
            "FR",
        ]:
            # Higher risk for requests from certain countries (configurable)
            risk_score += 20
            risk_factors.append(f"Request from {location.country}")

        # User history analysis
        if user_history:
            unique_countries = set()
            for hist_ip in user_history[-10:]:  # Last 10 IPs
                hist_location = self.get_location_info(hist_ip)
                if hist_location.country_code:
                    unique_countries.add(hist_location.country_code)

            if len(unique_countries) > 3:  # Multiple countries
                risk_score += 25
                risk_factors.append("Multiple countries in recent history")

        # Determine risk level
        if risk_score >= 80:
            risk_level = SecurityLevel.CRITICAL.value
        elif risk_score >= 60:
            risk_level = SecurityLevel.HIGH.value
        elif risk_score >= 40:
            risk_level = SecurityLevel.MEDIUM.value
        else:
            risk_level = SecurityLevel.LOW.value

        return {
            "risk_level": risk_level,
            "score": min(100, risk_score),
            "factors": risk_factors,
            "location": location,
        }

    def _is_from_bad_range(self, ip_address: str) -> bool:
        """Check if IP is from known bad ranges (simplified)"""
        # This is a simplified implementation
        # In production, you would use threat intelligence feeds
        bad_ranges = [
            # Example bad ranges (these are just examples)
            "192.0.2.0/24",  # TEST-NET-1
        ]

        try:
            ip = ipaddress.ip_address(ip_address)
            for range_str in bad_ranges:
                network = ipaddress.ip_network(range_str)
                if ip in network:
                    return True
        except Exception:
            pass

        return False


class TwoFactorAuthManager:
    """Two-Factor Authentication management"""

    def __init__(self):
        self.issuer_name = "KIRO2 Platform"

    def generate_secret(self) -> str:
        """Generate TOTP secret"""
        return pyotp.random_base32()

    def generate_qr_code(self, secret: str, username: str, email: str) -> bytes:
        """Generate QR code for TOTP setup"""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=email, issuer_name=self.issuer_name
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """Verify TOTP token"""
        if not secret or not token:
            return False

        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False

    def generate_backup_codes(self, count: int = 8) -> list[str]:
        """Generate backup codes for 2FA"""
        codes = []
        for _ in range(count):
            # Generate 8-digit codes
            code = f"{secrets.randbelow(100000000):08d}"
            codes.append(code)
        return codes

    def hash_backup_code(self, code: str) -> str:
        """Hash backup code for storage"""
        return hashlib.sha256(code.encode()).hexdigest()

    def verify_backup_code(self, code: str, hashed_codes: list[str]) -> bool:
        """Verify backup code against stored hashes"""
        if not code:
            return False

        code_hash = self.hash_backup_code(code)
        return code_hash in hashed_codes


class SecurityHeaderManager:
    """Security headers management"""

    @staticmethod
    def get_security_headers() -> dict[str, str]:
        """Get comprehensive security headers"""
        return {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            # XSS protection
            "X-XSS-Protection": "1; mode=block",
            # HTTPS enforcement
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
                "font-src 'self' fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Permissions policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "accelerometer=(), "
                "gyroscope=()"
            ),
            # Prevent caching of sensitive content
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }

    @staticmethod
    def get_cors_headers(
        allowed_origins: list[str] = None, allowed_methods: list[str] = None
    ) -> dict[str, str]:
        """Get CORS headers"""
        if allowed_origins is None:
            allowed_origins = ["http://localhost:3000", "https://kiro2.com"]

        if allowed_methods is None:
            allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

        return {
            "Access-Control-Allow-Origin": ", ".join(allowed_origins),
            "Access-Control-Allow-Methods": ", ".join(allowed_methods),
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, X-CSRF-Token",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }


# Global utility instances
password_manager = PasswordSecurityManager()
input_validator = InputSecurityValidator()
ip_manager = IPSecurityManager()
twofa_manager = TwoFactorAuthManager()
header_manager = SecurityHeaderManager()


# Utility functions
def validate_password_strength(password: str) -> dict[str, Any]:
    """Validate password strength"""
    return password_manager.analyze_password_strength(password)


def scan_input_security(
    input_data: dict[str, Any], ip_address: str = ""
) -> list[SecurityThreat]:
    """Scan input data for security threats"""
    threats = []

    for field_name, field_value in input_data.items():
        if isinstance(field_value, str):
            field_threats = input_validator.scan_for_security_threats(field_value)
            for threat in field_threats:
                threat.additional_data["field"] = field_name
                threat.ip_address = ip_address
                threats.append(threat)

    return threats


def analyze_request_security(
    ip_address: str,
    user_agent: str,
    input_data: dict[str, Any] = None,
    user_history: list[str] = None,
) -> dict[str, Any]:
    """Comprehensive request security analysis"""

    analysis = {
        "risk_level": SecurityLevel.LOW.value,
        "risk_score": 0,
        "threats": [],
        "ip_analysis": {},
        "input_threats": [],
        "recommendations": [],
    }

    # IP analysis
    ip_analysis = ip_manager.analyze_ip_risk(ip_address, user_history)
    analysis["ip_analysis"] = ip_analysis
    analysis["risk_score"] += ip_analysis["score"] * 0.4  # 40% weight

    # Input security scan
    if input_data:
        input_threats = scan_input_security(input_data, ip_address)
        analysis["input_threats"] = [
            {
                "type": threat.threat_type.value,
                "severity": threat.severity.value,
                "description": threat.description,
            }
            for threat in input_threats
        ]

        # Add threat score
        if input_threats:
            threat_score = max(
                (
                    (t.severity == SecurityLevel.HIGH and 40)
                    or (t.severity == SecurityLevel.MEDIUM and 25)
                    or 15
                )
                for t in input_threats
            )
            analysis["risk_score"] += threat_score

    # User agent analysis (basic)
    if user_agent:
        if len(user_agent) < 20 or "bot" in user_agent.lower():
            analysis["risk_score"] += 20
            analysis["threats"].append("Suspicious user agent")

    # Final risk level
    if analysis["risk_score"] >= 80:
        analysis["risk_level"] = SecurityLevel.CRITICAL.value
        analysis["recommendations"].append("Block request immediately")
    elif analysis["risk_score"] >= 60:
        analysis["risk_level"] = SecurityLevel.HIGH.value
        analysis["recommendations"].append("Require additional authentication")
    elif analysis["risk_score"] >= 40:
        analysis["risk_level"] = SecurityLevel.MEDIUM.value
        analysis["recommendations"].append("Monitor closely")

    return analysis
