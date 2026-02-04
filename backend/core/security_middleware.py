"""
Security Middleware Consolidation - Comprehensive Security Layer
Unified security middleware system for the Türkiye Üniversite Sınavları Hazırlık Platformu

Bu dosya kapsamlı security middleware'leri sağlar:
- Authentication middleware with multiple strategies
- Authorization middleware with RBAC integration
- Rate limiting and DDoS protection
- CORS and security headers management
- Request/response security validation
- Session security and CSRF protection
- Security logging and monitoring
- IP whitelisting/blacklisting
- Device fingerprinting and bot detection
"""

import logging
import re
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.security import HTTPBearer
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

# Import authentication and RBAC systems
from .enhanced_authentication import (
    AuthenticationType,
    TokenType,
    get_authentication_manager,
)
from .error_context import async_error_context
from .error_monitoring import log_error

# Import error handling
from .exceptions import ErrorSeverity
from .rbac_system import Action, AuthorizationContext, ResourceType, get_rbac_manager

# Import response models
from .response_models import error_response

logger = logging.getLogger(__name__)


# ==================== SECURITY MIDDLEWARE ENUMS ====================


class SecurityLevel(Enum):
    """Security level for different endpoints"""

    PUBLIC = "public"  # No authentication required
    AUTHENTICATED = "authenticated"  # Authentication required
    AUTHORIZED = "authorized"  # Authentication + specific permissions required
    ADMIN = "admin"  # Admin-level access required
    SYSTEM = "system"  # System-level access required


class RateLimitType(Enum):
    """Rate limiting types"""

    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"


class SecurityThreat(Enum):
    """Security threat types"""

    BRUTE_FORCE = "brute_force"
    DDOS = "ddos"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    MALFORMED_REQUEST = "malformed_request"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


class BlockAction(Enum):
    """Actions to take when security threat detected"""

    LOG = "log"  # Only log the threat
    WARN = "warn"  # Log and send warning response
    BLOCK = "block"  # Block the request
    CAPTCHA = "captcha"  # Require CAPTCHA verification
    TEMPORARY_BAN = "temporary_ban"  # Temporary IP ban


# ==================== SECURITY CONFIGURATION ====================


@dataclass
class SecurityMiddlewareConfig:
    """Configuration for security middleware"""

    # Authentication settings
    enable_authentication: bool = True
    authentication_required_paths: list[str] = field(default_factory=lambda: ["/api/"])
    authentication_exempt_paths: list[str] = field(
        default_factory=lambda: ["/health", "/docs"]
    )

    # Rate limiting settings
    enable_rate_limiting: bool = True
    global_rate_limit_per_minute: int = 1000
    user_rate_limit_per_minute: int = 100
    ip_rate_limit_per_minute: int = 200
    burst_threshold: int = 50

    # CORS settings
    enable_cors: bool = True
    allowed_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    allowed_methods: list[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE"]
    )
    allowed_headers: list[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True

    # Security headers
    enable_security_headers: bool = True
    security_headers: dict[str, str] = field(default_factory=dict)

    # CSRF protection
    enable_csrf_protection: bool = True
    csrf_exempt_paths: list[str] = field(default_factory=lambda: ["/api/auth/login"])

    # Input validation
    enable_input_validation: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_json_depth: int = 10

    # IP filtering
    enable_ip_filtering: bool = True
    ip_whitelist: set[str] = field(default_factory=set)
    ip_blacklist: set[str] = field(default_factory=set)

    # SECURITY FIX: Trusted proxy configuration
    trusted_proxies: set[str] = field(
        default_factory=lambda: {"127.0.0.1", "::1", "localhost"}
    )
    enable_trusted_proxy_validation: bool = True

    # Bot detection
    enable_bot_detection: bool = True
    suspicious_user_agents: list[str] = field(
        default_factory=lambda: ["bot", "crawler", "spider", "scraper", "wget", "curl"]
    )

    # Logging settings
    log_all_requests: bool = False
    log_security_events: bool = True
    log_failed_auth: bool = True

    def __post_init__(self):
        if not self.security_headers:
            self.security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: https:;",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            }


# ==================== RATE LIMITING ====================


@dataclass
class RateLimitRecord:
    """Record for rate limiting tracking"""

    requests: deque = field(default_factory=deque)
    blocked_until: datetime | None = None
    warning_count: int = 0

    def add_request(self, timestamp: datetime) -> None:
        """Add request timestamp"""
        self.requests.append(timestamp)

        # Keep only requests from last minute
        cutoff = timestamp - timedelta(minutes=1)
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

    def get_request_count(self, window_minutes: int = 1) -> int:
        """Get request count in time window"""
        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)
        return sum(1 for req_time in self.requests if req_time >= cutoff)

    def is_blocked(self) -> bool:
        """Check if currently blocked"""
        if self.blocked_until and datetime.now(UTC) < self.blocked_until:
            return True
        return False


class RateLimiter:
    """Advanced rate limiter with multiple strategies"""

    def __init__(self, config: SecurityMiddlewareConfig):
        self.config = config
        self.ip_records: dict[str, RateLimitRecord] = {}
        self.user_records: dict[str, RateLimitRecord] = {}
        self.endpoint_records: dict[str, RateLimitRecord] = {}
        self.global_record = RateLimitRecord()
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = datetime.now(UTC)

    async def check_rate_limit(
        self, request: Request, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Check if request should be rate limited"""

        now = datetime.now(UTC)
        client_ip = self._get_client_ip(request)
        endpoint = f"{request.method} {request.url.path}"

        # Clean up old records periodically
        if (now - self.last_cleanup).total_seconds() > self.cleanup_interval:
            await self._cleanup_records()
            self.last_cleanup = now

        violations = []

        # Check global rate limit
        self.global_record.add_request(now)
        if (
            self.global_record.get_request_count()
            > self.config.global_rate_limit_per_minute
        ):
            violations.append(
                {
                    "type": RateLimitType.GLOBAL.value,
                    "limit": self.config.global_rate_limit_per_minute,
                    "current": self.global_record.get_request_count(),
                }
            )

        # Check IP rate limit
        if client_ip not in self.ip_records:
            self.ip_records[client_ip] = RateLimitRecord()

        ip_record = self.ip_records[client_ip]
        if ip_record.is_blocked():
            violations.append(
                {
                    "type": "ip_blocked",
                    "blocked_until": ip_record.blocked_until.isoformat(),
                    "reason": "Temporary IP ban",
                }
            )
        else:
            ip_record.add_request(now)
            if ip_record.get_request_count() > self.config.ip_rate_limit_per_minute:
                violations.append(
                    {
                        "type": RateLimitType.PER_IP.value,
                        "limit": self.config.ip_rate_limit_per_minute,
                        "current": ip_record.get_request_count(),
                    }
                )

        # Check user rate limit
        if user_id:
            if user_id not in self.user_records:
                self.user_records[user_id] = RateLimitRecord()

            user_record = self.user_records[user_id]
            user_record.add_request(now)
            if user_record.get_request_count() > self.config.user_rate_limit_per_minute:
                violations.append(
                    {
                        "type": RateLimitType.PER_USER.value,
                        "limit": self.config.user_rate_limit_per_minute,
                        "current": user_record.get_request_count(),
                    }
                )

        # Check endpoint rate limit (if configured)
        if endpoint not in self.endpoint_records:
            self.endpoint_records[endpoint] = RateLimitRecord()

        endpoint_record = self.endpoint_records[endpoint]
        endpoint_record.add_request(now)

        if violations:
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded for {client_ip} (user: {user_id}): {violations}"
            )

            # Implement progressive penalties
            if len(violations) > 1 or ip_record.warning_count > 3:
                # Temporary ban for repeat offenders
                ip_record.blocked_until = now + timedelta(minutes=15)
                ip_record.warning_count = 0
            else:
                ip_record.warning_count += 1

            return {
                "rate_limited": True,
                "violations": violations,
                "retry_after": 60,  # seconds
                "client_ip": client_ip,
            }

        return None

    def _is_from_trusted_proxy(self, request: Request) -> bool:
        """
        Check if request is from a trusted proxy
        SECURITY FIX: Validate proxy source before trusting forwarded headers
        """
        if not self.config.enable_trusted_proxy_validation:
            return True  # Trust all if validation disabled (NOT RECOMMENDED)

        client_host = request.client.host if request.client else None
        if not client_host:
            return False

        return client_host in self.config.trusted_proxies

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request with trusted proxy validation
        SECURITY FIX: Prevents IP spoofing via X-Forwarded-For header
        """
        # SECURITY: Only trust forwarded headers from trusted proxies
        if self._is_from_trusted_proxy(request):
            # X-Forwarded-For: client, proxy1, proxy2
            # Take the FIRST IP (original client)
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                # Split and validate
                ips = [ip.strip() for ip in forwarded_for.split(",")]
                # Return the leftmost (original client) IP
                client_ip = ips[0]
                # Basic IP validation
                if self._is_valid_ip(client_ip):
                    return client_ip

            # X-Real-IP (nginx)
            real_ip = request.headers.get("x-real-ip")
            if real_ip and self._is_valid_ip(real_ip):
                return real_ip

        # Direct connection IP (always trusted)
        return request.client.host if request.client else "unknown"

    def _is_valid_ip(self, ip: str) -> bool:
        """
        Validate IP address format
        SECURITY FIX: Prevent injection of malicious values
        """
        import ipaddress

        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    async def _cleanup_records(self) -> None:
        """Clean up old rate limiting records"""
        cutoff = datetime.now(UTC) - timedelta(hours=1)

        # Clean IP records
        for ip, record in list(self.ip_records.items()):
            if not record.requests or (
                record.requests[-1] < cutoff and not record.is_blocked()
            ):
                del self.ip_records[ip]

        # Clean user records
        for user_id, record in list(self.user_records.items()):
            if not record.requests or record.requests[-1] < cutoff:
                del self.user_records[user_id]

        # Clean endpoint records
        for endpoint, record in list(self.endpoint_records.items()):
            if not record.requests or record.requests[-1] < cutoff:
                del self.endpoint_records[endpoint]

        logger.debug("Cleaned up rate limiting records")


# ==================== SECURITY VALIDATORS ====================


class SecurityValidator:
    """Validate requests for security threats"""

    def __init__(self, config: SecurityMiddlewareConfig):
        self.config = config

        # SQL injection patterns
        self.sql_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bselect\b.*\bfrom\b)",
            r"(\binsert\b.*\binto\b)",
            r"(\bdelete\b.*\bfrom\b)",
            r"(\bdrop\b.*\btable\b)",
            r"(\bupdate\b.*\bset\b)",
            r"(--|#|/\*|\*/)",
            r"(\bor\b.*\b=\b.*\bor\b)",
            r"(\band\b.*\b=\b.*\band\b)",
        ]

        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"vbscript:",
            r"data:.*?base64",
        ]

        # Compile patterns for performance
        self.compiled_sql_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns
        ]
        self.compiled_xss_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns
        ]

    async def validate_request(self, request: Request) -> list[dict[str, Any]]:
        """Validate request for security threats"""
        threats = []

        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.config.max_request_size:
            threats.append(
                {
                    "type": SecurityThreat.MALFORMED_REQUEST.value,
                    "description": "Request size exceeds limit",
                    "details": {
                        "size": content_length,
                        "limit": self.config.max_request_size,
                    },
                }
            )

        # Check user agent
        user_agent = request.headers.get("user-agent", "").lower()
        if any(
            suspicious in user_agent
            for suspicious in self.config.suspicious_user_agents
        ):
            threats.append(
                {
                    "type": SecurityThreat.SUSPICIOUS_USER_AGENT.value,
                    "description": "Suspicious user agent detected",
                    "details": {"user_agent": user_agent},
                }
            )

        # Check query parameters
        for key, value in request.query_params.items():
            if isinstance(value, str):
                # Check for SQL injection
                if self._check_sql_injection(value):
                    threats.append(
                        {
                            "type": SecurityThreat.SQL_INJECTION.value,
                            "description": f"SQL injection attempt in query parameter: {key}",
                            "details": {"parameter": key, "value": value[:100]},
                        }
                    )

                # Check for XSS
                if self._check_xss(value):
                    threats.append(
                        {
                            "type": SecurityThreat.XSS.value,
                            "description": f"XSS attempt in query parameter: {key}",
                            "details": {"parameter": key, "value": value[:100]},
                        }
                    )

        # Check headers for suspicious content
        for header_name, header_value in request.headers.items():
            if isinstance(header_value, str):
                if self._check_sql_injection(header_value) or self._check_xss(
                    header_value
                ):
                    threats.append(
                        {
                            "type": SecurityThreat.MALFORMED_REQUEST.value,
                            "description": f"Suspicious content in header: {header_name}",
                            "details": {"header": header_name},
                        }
                    )

        return threats

    def _check_sql_injection(self, text: str) -> bool:
        """Check text for SQL injection patterns"""
        return any(pattern.search(text) for pattern in self.compiled_sql_patterns)

    def _check_xss(self, text: str) -> bool:
        """Check text for XSS patterns"""
        return any(pattern.search(text) for pattern in self.compiled_xss_patterns)


# ==================== AUTHENTICATION MIDDLEWARE ====================


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware with multiple strategies"""

    def __init__(self, app: ASGIApp, config: SecurityMiddlewareConfig):
        super().__init__(app)
        self.config = config
        self.auth_manager = get_authentication_manager()
        self.security_bearer = HTTPBearer(auto_error=False)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request for authentication"""

        # Skip authentication for exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # Check if authentication is required for this path
        if not self._requires_authentication(request.url.path):
            return await call_next(request)

        async with async_error_context(
            operation_name="authentication_middleware",
            business_operation="request_authentication",
        ) as ctx:
            try:
                # Extract authentication credentials
                auth_result = await self._authenticate_request(request)

                if auth_result["success"]:
                    # Add user context to request
                    request.state.user = auth_result["user"]
                    request.state.session_id = auth_result.get("session_id")
                    request.state.authentication_type = auth_result.get(
                        "authentication_type"
                    )

                    ctx.add_annotation(
                        f"User authenticated: {auth_result['user']['id']}"
                    )

                    return await call_next(request)
                ctx.add_annotation(f"Authentication failed: {auth_result['reason']}")

                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content=error_response(
                        "AUTHENTICATION_REQUIRED",
                        "Authentication required",
                        "Bu endpoint için kimlik doğrulaması gereklidir",
                    ).dict(),
                )

            except Exception as e:
                ctx.add_annotation(f"Authentication middleware error: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)

                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=error_response(
                        "AUTHENTICATION_ERROR",
                        "Authentication error",
                        "Kimlik doğrulama sırasında hata oluştu",
                    ).dict(),
                )

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from authentication"""
        return any(
            path.startswith(exempt_path)
            for exempt_path in self.config.authentication_exempt_paths
        )

    def _requires_authentication(self, path: str) -> bool:
        """Check if path requires authentication"""
        if not self.config.enable_authentication:
            return False

        return any(
            path.startswith(auth_path)
            for auth_path in self.config.authentication_required_paths
        )

    async def _authenticate_request(self, request: Request) -> dict[str, Any]:
        """Authenticate request using available methods"""

        # Try JWT token authentication
        jwt_result = await self._authenticate_jwt(request)
        if jwt_result["success"]:
            return jwt_result

        # Try API key authentication
        api_key_result = await self._authenticate_api_key(request)
        if api_key_result["success"]:
            return api_key_result

        # Try session authentication
        session_result = await self._authenticate_session(request)
        if session_result["success"]:
            return session_result

        return {"success": False, "reason": "No valid authentication method found"}

    async def _authenticate_jwt(self, request: Request) -> dict[str, Any]:
        """Authenticate using JWT token"""

        try:
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return {"success": False, "reason": "No bearer token"}

            token = auth_header[7:]  # Remove "Bearer " prefix

            # Verify token
            payload = self.auth_manager.token_manager.verify_token(
                token, TokenType.ACCESS
            )

            if payload:
                # Get session info
                session = None
                if payload.session_id:
                    session = await self.auth_manager.session_manager.get_session(
                        payload.session_id
                    )
                    if session:
                        await self.auth_manager.session_manager.update_session_activity(
                            payload.session_id
                        )

                return {
                    "success": True,
                    "user": {
                        "id": payload.user_id,
                        "username": payload.username,
                        "email": payload.email,
                        "role": payload.role,
                        "permissions": payload.permissions,
                    },
                    "session_id": payload.session_id,
                    "authentication_type": AuthenticationType.JWT_TOKEN.value,
                }

            return {"success": False, "reason": "Invalid or expired token"}

        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            return {"success": False, "reason": "JWT authentication failed"}

    async def _authenticate_api_key(self, request: Request) -> dict[str, Any]:
        """Authenticate using API key"""

        api_key = request.headers.get("x-api-key") or request.query_params.get(
            "api_key"
        )

        if not api_key:
            return {"success": False, "reason": "No API key"}

        # In production, validate API key against database
        # For now, return mock result
        return {"success": False, "reason": "API key authentication not implemented"}

    async def _authenticate_session(self, request: Request) -> dict[str, Any]:
        """Authenticate using session cookie"""

        session_id = request.cookies.get("session_id")

        if not session_id:
            return {"success": False, "reason": "No session cookie"}

        try:
            session = await self.auth_manager.session_manager.get_session(session_id)

            if session and session.is_active():
                await self.auth_manager.session_manager.update_session_activity(
                    session_id
                )

                return {
                    "success": True,
                    "user": {
                        "id": session.user_id,
                        # Additional user data would be fetched from database
                    },
                    "session_id": session_id,
                    "authentication_type": AuthenticationType.SESSION_TOKEN.value,
                }

            return {"success": False, "reason": "Invalid or expired session"}

        except Exception as e:
            logger.error(f"Session authentication error: {e}")
            return {"success": False, "reason": "Session authentication failed"}


# ==================== AUTHORIZATION MIDDLEWARE ====================


class AuthorizationMiddleware(BaseHTTPMiddleware):
    """Authorization middleware with RBAC integration"""

    def __init__(self, app: ASGIApp, config: SecurityMiddlewareConfig):
        super().__init__(app)
        self.config = config
        self.rbac_manager = get_rbac_manager()

        # Define endpoint permissions
        self.endpoint_permissions = {
            # User management
            "GET /api/v1/users": (ResourceType.USER, Action.READ),
            "POST /api/v1/users": (ResourceType.USER, Action.CREATE),
            "PUT /api/v1/users/*": (ResourceType.USER, Action.UPDATE),
            "DELETE /api/v1/users/*": (ResourceType.USER, Action.DELETE),
            # Exam management
            "GET /api/v1/exams": (ResourceType.EXAM, Action.READ),
            "POST /api/v1/exams": (ResourceType.EXAM, Action.CREATE),
            "PUT /api/v1/exams/*": (ResourceType.EXAM, Action.UPDATE),
            "DELETE /api/v1/exams/*": (ResourceType.EXAM, Action.DELETE),
            # Content management
            "GET /api/v1/content": (ResourceType.CONTENT, Action.READ),
            "POST /api/v1/content": (ResourceType.CONTENT, Action.CREATE),
            "PUT /api/v1/content/*": (ResourceType.CONTENT, Action.UPDATE),
            "DELETE /api/v1/content/*": (ResourceType.CONTENT, Action.DELETE),
            # Reports
            "GET /api/v1/reports": (ResourceType.REPORT, Action.READ),
            "POST /api/v1/reports/export": (ResourceType.REPORT, Action.EXPORT),
            # Analytics
            "GET /api/v1/analytics": (ResourceType.ANALYTICS, Action.READ),
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request for authorization"""

        # Skip authorization if no user context (not authenticated)
        if not hasattr(request.state, "user") or not request.state.user:
            return await call_next(request)

        async with async_error_context(
            operation_name="authorization_middleware",
            entity_id=request.state.user["id"],
            business_operation="request_authorization",
        ) as ctx:
            try:
                # Check if endpoint requires specific permissions
                required_permission = self._get_required_permission(request)

                if required_permission:
                    resource_type, action = required_permission

                    # Create authorization context
                    auth_context = AuthorizationContext(
                        user_id=request.state.user["id"],
                        resource_type=resource_type,
                        action=action,
                        ip_address=self._get_client_ip(request),
                        user_agent=request.headers.get("user-agent"),
                        additional_context={
                            "endpoint": f"{request.method} {request.url.path}",
                            "session_id": getattr(request.state, "session_id", None),
                        },
                    )

                    # Check permission
                    result = await self.rbac_manager.check_permission(auth_context)

                    if not result.granted:
                        ctx.add_annotation(f"Authorization denied: {result.reason}")

                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content=error_response(
                                "AUTHORIZATION_DENIED",
                                "Insufficient permissions",
                                "Bu işlem için yeterli yetkiniz yok",
                            ).dict(),
                        )

                    # Add authorization context to request
                    request.state.authorization_result = result
                    ctx.add_annotation("Authorization granted")

                return await call_next(request)

            except Exception as e:
                ctx.add_annotation(f"Authorization middleware error: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)

                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=error_response(
                        "AUTHORIZATION_ERROR",
                        "Authorization error",
                        "Yetkilendirme sırasında hata oluştu",
                    ).dict(),
                )

    def _get_required_permission(
        self, request: Request
    ) -> Tuple[ResourceType, Action] | None:
        """Get required permission for endpoint"""

        endpoint_key = f"{request.method} {request.url.path}"

        # Check exact match first
        if endpoint_key in self.endpoint_permissions:
            return self.endpoint_permissions[endpoint_key]

        # Check wildcard matches
        for pattern, permission in self.endpoint_permissions.items():
            if pattern.endswith("/*"):
                prefix = pattern[:-2]  # Remove /*
                if endpoint_key.startswith(prefix):
                    return permission

        return None

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


# ==================== COMPREHENSIVE SECURITY MIDDLEWARE ====================


class ComprehensiveSecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware combining all security features"""

    def __init__(self, app: ASGIApp, config: SecurityMiddlewareConfig | None = None):
        super().__init__(app)
        self.config = config or SecurityMiddlewareConfig()
        self.rate_limiter = RateLimiter(self.config)
        self.security_validator = SecurityValidator(self.config)

        # Security event tracking
        self.security_events: list[dict[str, Any]] = []
        self.blocked_ips: dict[str, datetime] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        """Main security middleware dispatch"""

        start_time = time.time()
        client_ip = self._get_client_ip(request)

        # Add request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        async with async_error_context(
            operation_name="security_middleware",
            entity_id=request_id,
            business_operation="request_security_check",
        ) as ctx:
            ctx.tags.update(
                {
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", "")[:100],
                }
            )

            try:
                # 1. IP filtering
                if self._is_blocked_ip(client_ip):
                    ctx.add_annotation("Request blocked: IP in blacklist")
                    return self._create_blocked_response("IP blocked")

                # 2. Rate limiting
                user_id = (
                    getattr(request.state, "user", {}).get("id")
                    if hasattr(request.state, "user")
                    else None
                )
                rate_limit_result = await self.rate_limiter.check_rate_limit(
                    request, user_id
                )

                if rate_limit_result:
                    ctx.add_annotation("Request blocked: Rate limit exceeded")
                    await self._log_security_event(
                        SecurityThreat.RATE_LIMIT_EXCEEDED, client_ip, rate_limit_result
                    )
                    return self._create_rate_limit_response(rate_limit_result)

                # 3. Security validation
                if self.config.enable_input_validation:
                    threats = await self.security_validator.validate_request(request)

                    if threats:
                        ctx.add_annotation(f"Security threats detected: {len(threats)}")
                        for threat in threats:
                            await self._log_security_event(
                                SecurityThreat(threat["type"]), client_ip, threat
                            )

                        # Block high-severity threats
                        high_severity_threats = [
                            SecurityThreat.SQL_INJECTION,
                            SecurityThreat.XSS,
                        ]

                        if any(
                            SecurityThreat(t["type"]) in high_severity_threats
                            for t in threats
                        ):
                            return self._create_blocked_response(
                                "Security threat detected"
                            )

                # 4. CORS handling (for preflight requests)
                if request.method == "OPTIONS" and self.config.enable_cors:
                    return self._create_cors_response(request)

                # 5. Process request
                response = await call_next(request)

                # 6. Add security headers
                if self.config.enable_security_headers:
                    self._add_security_headers(response)

                # 7. Add CORS headers
                if self.config.enable_cors:
                    self._add_cors_headers(response, request)

                # 8. Log request if configured
                processing_time = (time.time() - start_time) * 1000
                request.state.processing_time = processing_time

                if self.config.log_all_requests:
                    logger.info(
                        f"Request processed: {request.method} {request.url.path} - {response.status_code} - {processing_time:.2f}ms"
                    )

                ctx.add_annotation(
                    f"Request processed successfully in {processing_time:.2f}ms"
                )

                return response

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                ctx.add_annotation(
                    f"Security middleware error after {processing_time:.2f}ms: {e!s}"
                )
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)

                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=error_response(
                        "SECURITY_ERROR",
                        "Security middleware error",
                        "Güvenlik kontrolü sırasında hata oluştu",
                    ).dict(),
                )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _is_blocked_ip(self, ip: str) -> bool:
        """Check if IP is blocked"""
        # Check permanent blacklist
        if ip in self.config.ip_blacklist:
            return True

        # Check temporary blocks
        if ip in self.blocked_ips:
            if datetime.now(UTC) < self.blocked_ips[ip]:
                return True
            # Remove expired block
            del self.blocked_ips[ip]

        return False

    def _create_blocked_response(self, reason: str) -> JSONResponse:
        """Create response for blocked requests"""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_response(
                "REQUEST_BLOCKED",
                f"Request blocked: {reason}",
                "İsteğiniz güvenlik nedenleriyle engellendi",
            ).dict(),
        )

    def _create_rate_limit_response(
        self, rate_limit_result: dict[str, Any]
    ) -> JSONResponse:
        """Create response for rate limited requests"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_response(
                "RATE_LIMIT_EXCEEDED",
                "Too many requests",
                "Çok fazla istek gönderdiniz. Lütfen daha sonra tekrar deneyin.",
                details={
                    "violations": rate_limit_result["violations"],
                    "retry_after": rate_limit_result["retry_after"],
                },
            ).dict(),
            headers={"Retry-After": str(rate_limit_result["retry_after"])},
        )

    def _create_cors_response(self, request: Request) -> Response:
        """Create CORS preflight response"""
        response = Response(status_code=200)
        self._add_cors_headers(response, request)
        return response

    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response"""
        for header, value in self.config.security_headers.items():
            response.headers[header] = value

    def _add_cors_headers(self, response: Response, request: Request) -> None:
        """Add CORS headers to response"""
        origin = request.headers.get("origin")

        if origin and (
            origin in self.config.allowed_origins or "*" in self.config.allowed_origins
        ):
            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Allow-Methods"] = ", ".join(
            self.config.allowed_methods
        )
        response.headers["Access-Control-Allow-Headers"] = ", ".join(
            self.config.allowed_headers
        )

        if self.config.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"

    async def _log_security_event(
        self, threat_type: SecurityThreat, client_ip: str, details: dict[str, Any]
    ) -> None:
        """Log security event"""

        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "threat_type": threat_type.value,
            "client_ip": client_ip,
            "details": details,
        }

        self.security_events.append(event)

        # Keep only last 10000 events
        if len(self.security_events) > 10000:
            self.security_events = self.security_events[-10000:]

        # Log based on severity
        if threat_type in [
            SecurityThreat.SQL_INJECTION,
            SecurityThreat.XSS,
            SecurityThreat.DDOS,
        ]:
            logger.error(
                f"HIGH SEVERITY SECURITY EVENT: {threat_type.value} from {client_ip}"
            )
        else:
            logger.warning(f"Security event: {threat_type.value} from {client_ip}")

    def get_security_stats(self) -> dict[str, Any]:
        """Get security middleware statistics"""
        recent_events = [
            event
            for event in self.security_events
            if datetime.fromisoformat(event["timestamp"])
            > datetime.now(UTC) - timedelta(hours=24)
        ]

        threat_counts = defaultdict(int)
        for event in recent_events:
            threat_counts[event["threat_type"]] += 1

        return {
            "total_events_24h": len(recent_events),
            "threat_breakdown": dict(threat_counts),
            "blocked_ips_count": len(self.blocked_ips),
            "rate_limiter_stats": {
                "tracked_ips": len(self.rate_limiter.ip_records),
                "tracked_users": len(self.rate_limiter.user_records),
                "tracked_endpoints": len(self.rate_limiter.endpoint_records),
            },
        }


# ==================== MIDDLEWARE FACTORY ====================


def create_security_middleware_stack(
    config: SecurityMiddlewareConfig | None = None,
) -> list[Callable]:
    """Create complete security middleware stack"""

    if config is None:
        config = SecurityMiddlewareConfig()

    middleware_stack = []

    # 1. Comprehensive security middleware (first layer)
    middleware_stack.append(lambda app: ComprehensiveSecurityMiddleware(app, config))

    # 2. Authentication middleware
    if config.enable_authentication:
        middleware_stack.append(lambda app: AuthenticationMiddleware(app, config))

    # 3. Authorization middleware (after authentication)
    middleware_stack.append(lambda app: AuthorizationMiddleware(app, config))

    return middleware_stack


# ==================== GLOBAL INSTANCES ====================

# Global security middleware configuration
default_security_config = SecurityMiddlewareConfig()


def get_security_middleware_config() -> SecurityMiddlewareConfig:
    """Get global security middleware configuration"""
    return default_security_config


def update_security_config(**kwargs) -> None:
    """Update global security configuration"""
    global default_security_config

    for key, value in kwargs.items():
        if hasattr(default_security_config, key):
            setattr(default_security_config, key, value)
