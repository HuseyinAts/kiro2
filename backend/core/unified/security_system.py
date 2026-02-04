"""
KIRO2 Unified Security System
Consolidated security solution combining all security functionality
"""

import base64
import hashlib
import html
import logging
import os
import re
import secrets
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Tuple

import bcrypt
from cryptography.fernet import Fernet
from fastapi import Request, Response, status
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security level enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Security threat types"""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    DDOS = "ddos"
    BRUTE_FORCE = "brute_force"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALICIOUS_FILE = "malicious_file"
    BOT_ACTIVITY = "bot_activity"


class SecurityAction(Enum):
    """Security response actions"""

    ALLOW = "allow"
    DENY = "deny"
    RATE_LIMIT = "rate_limit"
    CAPTCHA = "captcha"
    LOG_ONLY = "log_only"
    IP_BAN = "ip_ban"


@dataclass
class SecurityConfig:
    """Unified security configuration"""

    # General security
    security_level: SecurityLevel = SecurityLevel.HIGH
    enable_security_headers: bool = True
    enable_cors: bool = True
    enable_csrf_protection: bool = True

    # Rate limiting
    enable_rate_limiting: bool = True
    requests_per_minute: int = 100
    burst_limit: int = 200
    rate_limit_window: int = 60

    # DDoS protection
    enable_ddos_protection: bool = True
    ddos_threshold: int = 500
    ddos_window: int = 300  # 5 minutes

    # IP filtering
    enable_ip_filtering: bool = True
    max_requests_per_ip: int = 1000
    ip_ban_duration: int = 3600  # 1 hour

    # Input validation
    enable_input_validation: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_json_depth: int = 20

    # Bot detection
    enable_bot_detection: bool = True
    bot_detection_threshold: float = 0.8

    # Encryption
    encryption_key: str | None = None
    hash_algorithm: str = "sha256"

    # CORS settings
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000"])
    cors_methods: list[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE"]
    )
    cors_headers: list[str] = field(default_factory=lambda: ["*"])

    # Security headers
    security_headers: dict[str, str] = field(
        default_factory=lambda: {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        }
    )


@dataclass
class SecurityThreat:
    """Security threat detection"""

    threat_id: str
    threat_type: ThreatType
    severity: SecurityLevel
    source_ip: str
    user_agent: str
    request_path: str
    payload: str | None = None
    detected_at: datetime = field(default_factory=datetime.now)
    action_taken: SecurityAction | None = None
    description: str = ""


@dataclass
class RateLimitEntry:
    """Rate limiting entry"""

    requests: deque = field(default_factory=deque)
    blocked_until: datetime | None = None
    total_requests: int = 0
    total_blocked: int = 0


class SecurityValidator:
    """Input validation and sanitization"""

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\balter\b.*\btable\b)",
        r"(\bexec\b.*\b)",
        r"(\bscript\b.*\>)",
        r"(\b\-\-)",
        r"(\b\/\*.*\*\/)",
        r"(\b0x[0-9a-f]+)",
        r"(\bchar\(.+\))",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<embed[^>]*>",
        r"<object[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"expression\s*\(",
        r"url\s*\(",
        r"@import",
    ]

    @classmethod
    def detect_sql_injection(cls, input_text: str) -> bool:
        """Detect SQL injection attempts"""
        if not input_text:
            return False

        input_lower = input_text.lower()
        return any(
            re.search(pattern, input_lower, re.IGNORECASE)
            for pattern in cls.SQL_INJECTION_PATTERNS
        )

    @classmethod
    def detect_xss(cls, input_text: str) -> bool:
        """Detect XSS attempts"""
        if not input_text:
            return False

        return any(
            re.search(pattern, input_text, re.IGNORECASE)
            for pattern in cls.XSS_PATTERNS
        )

    @classmethod
    def sanitize_input(cls, input_text: str) -> str:
        """Sanitize input text"""
        if not input_text:
            return input_text

        # HTML escape
        sanitized = html.escape(input_text)

        # Remove potential script tags
        sanitized = re.sub(
            r"<script[^>]*>.*?</script>", "", sanitized, flags=re.IGNORECASE | re.DOTALL
        )

        # Remove javascript: protocols
        sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)

        return sanitized

    @classmethod
    def validate_json_depth(
        cls, data: Any, max_depth: int = 20, current_depth: int = 0
    ) -> bool:
        """Validate JSON depth to prevent DoS"""
        if current_depth > max_depth:
            return False

        if isinstance(data, dict):
            return all(
                cls.validate_json_depth(v, max_depth, current_depth + 1)
                for v in data.values()
            )
        if isinstance(data, list):
            return all(
                cls.validate_json_depth(item, max_depth, current_depth + 1)
                for item in data
            )

        return True


class BotDetector:
    """Bot and automated traffic detection"""

    BOT_USER_AGENTS = [
        "bot",
        "crawler",
        "spider",
        "scraper",
        "curl",
        "wget",
        "python",
        "requests",
    ]

    SUSPICIOUS_PATTERNS = [
        r"(.){100,}",  # Very long strings
        r"\d{4,}",  # Long numeric sequences
        r"[a-zA-Z]{50,}",  # Very long alphabetic sequences
    ]

    @classmethod
    def detect_bot(cls, user_agent: str, request_pattern: dict) -> float:
        """Detect bot activity (returns probability 0-1)"""
        score = 0.0

        # Check user agent
        if any(bot_ua in user_agent.lower() for bot_ua in cls.BOT_USER_AGENTS):
            score += 0.5

        # Check request frequency
        if request_pattern.get("frequency", 0) > 10:  # More than 10 requests per second
            score += 0.3

        # Check request patterns
        if request_pattern.get("uniform_timing", False):
            score += 0.2

        # Check for suspicious patterns in requests
        if any(
            re.search(pattern, str(request_pattern))
            for pattern in cls.SUSPICIOUS_PATTERNS
        ):
            score += 0.2

        return min(score, 1.0)


class UnifiedSecurityManager:
    """
    Unified security manager combining all security functionality:
    - Input validation and sanitization
    - Rate limiting and DDoS protection
    - Bot detection and prevention
    - Security monitoring and logging
    - Encryption and hashing
    - CORS and security headers
    - IP filtering and blocking
    """

    def __init__(self, config: SecurityConfig | None = None):
        self.config = config or SecurityConfig()
        self.validator = SecurityValidator()
        self.bot_detector = BotDetector()

        # Security tracking
        self.rate_limits: dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self.blocked_ips: dict[str, datetime] = {}
        self.security_threats: list[SecurityThreat] = []
        self.request_patterns: dict[str, dict] = defaultdict(dict)

        # Encryption
        self.cipher = None
        if self.config.encryption_key:
            self.cipher = Fernet(self.config.encryption_key.encode())

    async def initialize(self) -> None:
        """Initialize security manager"""
        try:
            # Generate encryption key if not provided
            if not self.config.encryption_key:
                self.config.encryption_key = base64.urlsafe_b64encode(
                    os.urandom(32)
                ).decode()
                self.cipher = Fernet(self.config.encryption_key.encode())

            logger.info("Security manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize security manager: {e}")
            raise

    # Input Validation
    def validate_request(
        self, request_data: Any, content_type: str = "application/json"
    ) -> Tuple[bool, list[str]]:
        """Validate incoming request data"""
        errors = []

        if not self.config.enable_input_validation:
            return True, errors

        # Check content size
        if (
            hasattr(request_data, "__len__")
            and len(str(request_data)) > self.config.max_request_size
        ):
            errors.append(f"Request size exceeds limit: {self.config.max_request_size}")

        # Validate JSON depth
        if content_type == "application/json" and isinstance(
            request_data, (dict, list)
        ):
            if not self.validator.validate_json_depth(
                request_data, self.config.max_json_depth
            ):
                errors.append(f"JSON depth exceeds limit: {self.config.max_json_depth}")

        # Check for SQL injection
        if isinstance(request_data, str):
            if self.validator.detect_sql_injection(request_data):
                errors.append("Potential SQL injection detected")
        elif isinstance(request_data, dict):
            for value in request_data.values():
                if isinstance(value, str) and self.validator.detect_sql_injection(
                    value
                ):
                    errors.append("Potential SQL injection detected in request data")
                    break

        # Check for XSS
        if isinstance(request_data, str):
            if self.validator.detect_xss(request_data):
                errors.append("Potential XSS attack detected")
        elif isinstance(request_data, dict):
            for value in request_data.values():
                if isinstance(value, str) and self.validator.detect_xss(value):
                    errors.append("Potential XSS attack detected in request data")
                    break

        return len(errors) == 0, errors

    def sanitize_data(self, data: Any) -> Any:
        """Sanitize input data"""
        if isinstance(data, str):
            return self.validator.sanitize_input(data)
        if isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        return data

    # Rate Limiting
    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        if not self.config.enable_rate_limiting:
            return True

        now = datetime.now()
        rate_entry = self.rate_limits[client_id]

        # Check if client is blocked
        if rate_entry.blocked_until and now < rate_entry.blocked_until:
            return False

        # Clean old requests
        cutoff = now - timedelta(seconds=self.config.rate_limit_window)
        while rate_entry.requests and rate_entry.requests[0] < cutoff:
            rate_entry.requests.popleft()

        # Check rate limit
        if len(rate_entry.requests) >= self.config.requests_per_minute:
            # Block client
            rate_entry.blocked_until = now + timedelta(
                seconds=self.config.rate_limit_window
            )
            rate_entry.total_blocked += 1
            return False

        # Add current request
        rate_entry.requests.append(now)
        rate_entry.total_requests += 1

        return True

    # DDoS Protection
    def check_ddos_protection(self, source_ip: str) -> bool:
        """Check for DDoS attacks"""
        if not self.config.enable_ddos_protection:
            return True

        # Simple DDoS detection based on request frequency
        now = datetime.now()
        ip_pattern = self.request_patterns[source_ip]

        # Count requests in the last window
        requests_in_window = ip_pattern.get("requests_in_window", 0)
        last_request_time = ip_pattern.get("last_request_time", now)

        # Reset counter if window expired
        if (now - last_request_time).total_seconds() > self.config.ddos_window:
            requests_in_window = 0

        requests_in_window += 1
        ip_pattern["requests_in_window"] = requests_in_window
        ip_pattern["last_request_time"] = now

        # Check threshold
        if requests_in_window > self.config.ddos_threshold:
            self.block_ip(source_ip, "DDoS attack detected")
            return False

        return True

    # IP Management
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        if ip_address in self.blocked_ips:
            if datetime.now() < self.blocked_ips[ip_address]:
                return True
            # Unblock expired IP
            del self.blocked_ips[ip_address]
        return False

    def block_ip(
        self, ip_address: str, reason: str = "", duration: int | None = None
    ) -> None:
        """Block IP address"""
        block_duration = duration or self.config.ip_ban_duration
        blocked_until = datetime.now() + timedelta(seconds=block_duration)
        self.blocked_ips[ip_address] = blocked_until

        logger.warning(
            f"IP blocked: {ip_address} - Reason: {reason} - Until: {blocked_until}"
        )

    def unblock_ip(self, ip_address: str) -> bool:
        """Unblock IP address"""
        if ip_address in self.blocked_ips:
            del self.blocked_ips[ip_address]
            logger.info(f"IP unblocked: {ip_address}")
            return True
        return False

    # Bot Detection
    def detect_bot_activity(self, user_agent: str, source_ip: str) -> float:
        """Detect bot activity"""
        if not self.config.enable_bot_detection:
            return 0.0

        # Get request pattern for this IP
        pattern = self.request_patterns.get(source_ip, {})

        # Calculate bot probability
        bot_probability = self.bot_detector.detect_bot(user_agent, pattern)

        # Take action if bot detected
        if bot_probability > self.config.bot_detection_threshold:
            self.log_security_threat(
                ThreatType.BOT_ACTIVITY,
                SecurityLevel.MEDIUM,
                source_ip,
                user_agent,
                "",
                f"Bot detected with probability: {bot_probability}",
            )

        return bot_probability

    # Encryption
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not self.cipher:
            raise ValueError("Encryption not configured")

        return self.cipher.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not self.cipher:
            raise ValueError("Encryption not configured")

        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def hash_data(self, data: str, salt: str | None = None) -> str:
        """Hash data with optional salt"""
        if salt is None:
            salt = secrets.token_hex(16)

        if self.config.hash_algorithm == "bcrypt":
            return bcrypt.hashpw((data + salt).encode(), bcrypt.gensalt()).decode()
        hash_obj = hashlib.new(self.config.hash_algorithm)
        hash_obj.update((data + salt).encode())
        return hash_obj.hexdigest()

    # Security Headers
    def get_security_headers(self) -> dict[str, str]:
        """Get security headers"""
        if not self.config.enable_security_headers:
            return {}

        return self.config.security_headers.copy()

    def get_cors_headers(self, origin: str) -> dict[str, str]:
        """Get CORS headers"""
        if not self.config.enable_cors:
            return {}

        headers = {}

        # Check origin
        if origin in self.config.cors_origins or "*" in self.config.cors_origins:
            headers["Access-Control-Allow-Origin"] = origin

        headers["Access-Control-Allow-Methods"] = ", ".join(self.config.cors_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(self.config.cors_headers)
        headers["Access-Control-Allow-Credentials"] = "true"

        return headers

    # Threat Logging
    def log_security_threat(
        self,
        threat_type: ThreatType,
        severity: SecurityLevel,
        source_ip: str,
        user_agent: str,
        request_path: str,
        description: str = "",
        payload: str | None = None,
    ) -> str:
        """Log security threat"""
        threat_id = str(uuid.uuid4())

        threat = SecurityThreat(
            threat_id=threat_id,
            threat_type=threat_type,
            severity=severity,
            source_ip=source_ip,
            user_agent=user_agent,
            request_path=request_path,
            payload=payload,
            description=description,
        )

        self.security_threats.append(threat)

        # Log to system logger
        logger.warning(
            f"Security threat detected: {threat_type.value} - {severity.value} - {source_ip} - {description}"
        )

        return threat_id

    # Middleware
    async def security_middleware(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Security middleware for FastAPI"""
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        # Check if IP is blocked
        if self.is_ip_blocked(client_ip):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "IP address is blocked"},
            )

        # Check rate limiting
        if not self.check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )

        # Check DDoS protection
        if not self.check_ddos_protection(client_ip):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Service temporarily unavailable"},
            )

        # Detect bot activity
        self.detect_bot_activity(user_agent, client_ip)

        # Process request
        response = await call_next(request)

        # Add security headers
        security_headers = self.get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value

        # Add CORS headers
        origin = request.headers.get("origin")
        if origin:
            cors_headers = self.get_cors_headers(origin)
            for header, value in cors_headers.items():
                response.headers[header] = value

        return response

    # Statistics and Monitoring
    async def get_security_stats(self) -> dict[str, Any]:
        """Get security statistics"""
        now = datetime.now()

        # Count threats by type in last 24 hours
        recent_threats = [
            t
            for t in self.security_threats
            if (now - t.detected_at).total_seconds() < 86400
        ]

        threat_counts = defaultdict(int)
        for threat in recent_threats:
            threat_counts[threat.threat_type.value] += 1

        return {
            "total_threats": len(self.security_threats),
            "recent_threats": len(recent_threats),
            "threat_breakdown": dict(threat_counts),
            "blocked_ips": len(self.blocked_ips),
            "rate_limited_clients": len(
                [r for r in self.rate_limits.values() if r.blocked_until]
            ),
            "timestamp": now.isoformat(),
        }

    async def health_check(self) -> dict[str, Any]:
        """Security system health check"""
        return {
            "security_manager_status": "healthy",
            "rate_limiting_enabled": self.config.enable_rate_limiting,
            "ddos_protection_enabled": self.config.enable_ddos_protection,
            "input_validation_enabled": self.config.enable_input_validation,
            "bot_detection_enabled": self.config.enable_bot_detection,
            "encryption_configured": self.cipher is not None,
            "timestamp": datetime.now().isoformat(),
        }


# Global instance
_security_manager: UnifiedSecurityManager | None = None


def get_security_manager() -> UnifiedSecurityManager:
    """Get global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = UnifiedSecurityManager()
    return _security_manager


# Backward compatibility aliases
SecurityManager = UnifiedSecurityManager
SecurityMiddleware = UnifiedSecurityManager
SecurityEventMonitoring = UnifiedSecurityManager
AuthSecurityUtils = UnifiedSecurityManager
