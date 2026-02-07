"""
KIRO2 Middleware Pipeline
Comprehensive middleware system for API request/response processing
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

import asyncio
import base64
import gzip
import json
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from enum import Enum
from http import HTTPMethod
from typing import Any

from core.cache_system_integration import get_unified_cache_system
from core.structured_logging import LogCategory, get_logger
from core.unified_api_gateway import APIRequest, APIResponse
from core.unified_config import get_unified_config
from core.unified_event_bus import EventPriority, EventType, publish_event

config = get_unified_config()
logger = get_logger(__name__, LogCategory.API)


class MiddlewareType(Enum):
    """Types of middleware"""

    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    CACHING = "caching"
    RATE_LIMITING = "rate_limiting"
    COMPRESSION = "compression"
    LOGGING = "logging"
    METRICS = "metrics"
    CORS = "cors"
    TURKISH_LOCALIZATION = "turkish_localization"
    EXAM_CONTEXT = "exam_context"


class MiddlewarePriority(Enum):
    """Middleware execution priorities"""

    CRITICAL = 0  # Security, CORS
    HIGH = 100  # Authentication, Authorization
    NORMAL = 500  # Validation, Caching
    LOW = 800  # Logging, Metrics
    LOWEST = 1000  # Response transformation


@dataclass
class MiddlewareConfig:
    """Middleware configuration"""

    name: str
    middleware_type: MiddlewareType
    priority: int
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)
    applies_to_routes: set[str] | None = None
    excludes_routes: set[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationRule:
    """Request validation rule"""

    field: str
    required: bool = False
    type: type = str
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    allowed_values: list[Any] | None = None
    custom_validator: Callable | None = None
    error_message: str = "Validation failed"
    error_message_tr: str = "Doğrulama başarısız"


@dataclass
class RateLimitRule:
    """Rate limiting rule"""

    requests_per_minute: int
    burst_limit: int = None
    per_user: bool = True
    per_ip: bool = False
    window_size: int = 60  # seconds
    block_duration: int = 300  # seconds when limit exceeded


class SecurityMiddleware:
    """Security headers and protection middleware"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.blocked_ips: set[str] = set()
        self.blocked_user_agents: set[str] = set()
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process security middleware"""
        try:
            # Check IP blocking
            if request.client_ip in self.blocked_ips:
                return self._create_security_error(
                    "IP blocked", "IP adresi engellenmiş"
                )

            # Check user agent blocking
            if request.user_agent in self.blocked_user_agents:
                return self._create_security_error(
                    "User agent blocked", "Kullanıcı aracısı engellenmiş"
                )

            # Validate request size
            max_size = self.config.get("max_request_size", 10 * 1024 * 1024)  # 10MB
            if self._get_request_size(request) > max_size:
                return self._create_security_error(
                    "Request too large", "İstek çok büyük"
                )

            # Check for suspicious patterns
            if self._has_suspicious_patterns(request):
                logger.warning(
                    f"Suspicious request detected from {request.client_ip}",
                    extra={"request_id": request.id, "user_agent": request.user_agent},
                )

                # Publish security event
                await publish_event(
                    EventType.SECURITY_ALERT,
                    {
                        "type": "suspicious_request",
                        "client_ip": request.client_ip,
                        "user_agent": request.user_agent,
                        "path": request.path,
                    },
                    priority=EventPriority.HIGH,
                )

            # Process request
            response = await next_handler(request)

            # Add security headers
            for header, value in self.security_headers.items():
                response.add_header(header, value)

            # Add Turkish security headers
            response.add_header("X-Security-Policy", "KIRO2-Turkish-Exam-Platform")

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return self._create_security_error(
                "Security check failed", "Güvenlik kontrolü başarısız"
            )

    def _get_request_size(self, request: APIRequest) -> int:
        """Calculate request size"""
        size = len(json.dumps(request.headers))
        if request.body:
            size += len(json.dumps(request.body))
        return size

    def _has_suspicious_patterns(self, request: APIRequest) -> bool:
        """Check for suspicious request patterns"""
        suspicious_patterns = [
            r"<script.*?>.*?</script>",  # XSS
            r"union.*select",  # SQL injection
            r"drop.*table",  # SQL injection
            r"\.\.\/",  # Path traversal
            r"eval\(",  # Code injection
        ]

        # Check all request data
        check_data = [
            request.path,
            str(request.query_params),
            json.dumps(request.body) if request.body else "",
        ]

        for data in check_data:
            for pattern in suspicious_patterns:
                if re.search(pattern, data.lower()):
                    return True

        return False

    def _create_security_error(self, error: str, error_tr: str) -> APIResponse:
        """Create security error response"""
        return APIResponse(
            request_id=str(uuid.uuid4()),
            status_code=403,
            headers={"Content-Type": "application/json"},
            body={
                "error": "Forbidden",
                "detail": error,
                "error_tr": "Erişim Engellendi",
                "detail_tr": error_tr,
            },
            processing_time_ms=1.0,
        )


class RequestValidationMiddleware:
    """Request validation middleware"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.validation_rules: dict[str, list[ValidationRule]] = {}
        self.global_rules: list[ValidationRule] = []

        # Default validation rules for Turkish exam platform
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default validation rules"""
        # Global rules for all requests
        self.global_rules = [
            ValidationRule(
                field="user_id",
                type=int,
                error_message="Invalid user ID",
                error_message_tr="Geçersiz kullanıcı ID",
            )
        ]

        # Route-specific rules
        self.validation_rules["/auth/login"] = [
            ValidationRule(
                field="email",
                required=True,
                pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                error_message="Invalid email format",
                error_message_tr="Geçersiz email formatı",
            ),
            ValidationRule(
                field="password",
                required=True,
                min_length=8,
                error_message="Password must be at least 8 characters",
                error_message_tr="Şifre en az 8 karakter olmalıdır",
            ),
        ]

        self.validation_rules["/exams/tyt/start"] = [
            ValidationRule(
                field="session_type",
                required=True,
                allowed_values=["practice", "simulation", "real"],
                error_message="Invalid session type",
                error_message_tr="Geçersiz oturum türü",
            ),
            ValidationRule(
                field="duration_minutes",
                type=int,
                error_message="Duration must be a valid number",
                error_message_tr="Süre geçerli bir sayı olmalıdır",
            ),
        ]

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process validation middleware"""
        try:
            # Validate request
            validation_errors = await self._validate_request(request)

            if validation_errors:
                return APIResponse(
                    request_id=request.id,
                    status_code=400,
                    headers={"Content-Type": "application/json"},
                    body={
                        "error": "Validation Failed",
                        "detail": "Request validation failed",
                        "error_tr": "Doğrulama Başarısız",
                        "detail_tr": "İstek doğrulaması başarısız",
                        "validation_errors": validation_errors,
                    },
                    processing_time_ms=5.0,
                )

            return await next_handler(request)

        except Exception as e:
            logger.error(f"Validation middleware error: {e}")
            return APIResponse(
                request_id=request.id,
                status_code=500,
                headers={"Content-Type": "application/json"},
                body={
                    "error": "Validation Error",
                    "detail": str(e),
                    "error_tr": "Doğrulama Hatası",
                    "detail_tr": str(e),
                },
                processing_time_ms=1.0,
            )

    async def _validate_request(self, request: APIRequest) -> list[dict[str, str]]:
        """Validate request against rules"""
        errors = []

        # Get validation rules for this route
        route_rules = self.validation_rules.get(request.path, [])
        all_rules = self.global_rules + route_rules

        # Combine all request data
        request_data = {}
        if request.body:
            request_data.update(request.body)
        request_data.update(request.query_params)

        # Check headers for user_id
        if request.user_id:
            request_data["user_id"] = request.user_id

        # Apply validation rules
        for rule in all_rules:
            error = await self._apply_rule(rule, request_data)
            if error:
                errors.append(error)

        return errors

    async def _apply_rule(
        self, rule: ValidationRule, data: dict[str, Any]
    ) -> dict[str, str] | None:
        """Apply single validation rule"""
        value = data.get(rule.field)

        # Check required
        if rule.required and (value is None or value == ""):
            return {
                "field": rule.field,
                "error": f"{rule.field} is required",
                "error_tr": f"{rule.field} gereklidir",
            }

        # If field is not present and not required, skip validation
        if value is None:
            return None

        # Type validation
        if not isinstance(value, rule.type):
            try:
                value = rule.type(value)  # Try to convert
            except (ValueError, TypeError):
                return {
                    "field": rule.field,
                    "error": f"{rule.field} must be of type {rule.type.__name__}",
                    "error_tr": f"{rule.field} {rule.type.__name__} tipinde olmalıdır",
                }

        # String validations
        if isinstance(value, str):
            if rule.min_length and len(value) < rule.min_length:
                return {
                    "field": rule.field,
                    "error": f"{rule.field} must be at least {rule.min_length} characters",
                    "error_tr": f"{rule.field} en az {rule.min_length} karakter olmalıdır",
                }

            if rule.max_length and len(value) > rule.max_length:
                return {
                    "field": rule.field,
                    "error": f"{rule.field} must be at most {rule.max_length} characters",
                    "error_tr": f"{rule.field} en fazla {rule.max_length} karakter olmalıdır",
                }

            if rule.pattern and not re.match(rule.pattern, value):
                return {
                    "field": rule.field,
                    "error": rule.error_message,
                    "error_tr": rule.error_message_tr,
                }

        # Allowed values validation
        if rule.allowed_values and value not in rule.allowed_values:
            return {
                "field": rule.field,
                "error": f"{rule.field} must be one of: {', '.join(map(str, rule.allowed_values))}",
                "error_tr": f"{rule.field} şunlardan biri olmalıdır: {', '.join(map(str, rule.allowed_values))}",
            }

        # Custom validator
        if rule.custom_validator:
            try:
                is_valid = (
                    await rule.custom_validator(value)
                    if asyncio.iscoroutinefunction(rule.custom_validator)
                    else rule.custom_validator(value)
                )
                if not is_valid:
                    return {
                        "field": rule.field,
                        "error": rule.error_message,
                        "error_tr": rule.error_message_tr,
                    }
            except Exception as e:
                return {
                    "field": rule.field,
                    "error": f"Validation error: {e}",
                    "error_tr": f"Doğrulama hatası: {e}",
                }

        return None


class RateLimitingMiddleware:
    """Rate limiting middleware"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.request_counts: dict[str, dict[str, Any]] = {}
        self.blocked_clients: dict[str, datetime] = {}
        self.rate_limits: dict[str, RateLimitRule] = {}

        # Setup default rate limits
        self._setup_default_limits()

    def _setup_default_limits(self):
        """Setup default rate limits for Turkish exam platform"""
        # Authentication endpoints - stricter limits
        self.rate_limits["/auth/login"] = RateLimitRule(
            requests_per_minute=10,
            burst_limit=5,
            per_ip=True,
            block_duration=900,  # 15 minutes
        )

        # Exam endpoints - moderate limits to prevent abuse
        self.rate_limits["/exams/tyt/start"] = RateLimitRule(
            requests_per_minute=5, per_user=True
        )

        self.rate_limits["/exams/ayt/start"] = RateLimitRule(
            requests_per_minute=5, per_user=True
        )

        # API endpoints - generous limits
        self.rate_limits["default"] = RateLimitRule(
            requests_per_minute=100, burst_limit=200, per_user=True
        )

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process rate limiting middleware"""
        try:
            # Get rate limit rule for this route
            rule = self.rate_limits.get(request.path, self.rate_limits["default"])

            # Generate client key
            client_key = self._get_client_key(request, rule)

            # Check if client is blocked
            if self._is_blocked(client_key):
                return self._create_rate_limit_error(
                    "Client blocked", "İstemci engellenmiş"
                )

            # Check rate limit
            if not await self._check_rate_limit(client_key, rule):
                # Block client if limit exceeded
                self.blocked_clients[client_key] = datetime.now(UTC) + timedelta(
                    seconds=rule.block_duration
                )

                logger.warning(
                    f"Rate limit exceeded for {client_key}",
                    extra={"request_id": request.id, "path": request.path},
                )

                # Publish rate limit event
                await publish_event(
                    EventType.SECURITY_ALERT,
                    {
                        "type": "rate_limit_exceeded",
                        "client_key": client_key,
                        "path": request.path,
                        "rule": rule.__dict__,
                    },
                    priority=EventPriority.HIGH,
                )

                return self._create_rate_limit_error(
                    "Rate limit exceeded",
                    f"İstek limiti aşıldı. {rule.block_duration} saniye sonra tekrar deneyin.",
                )

            # Process request
            response = await next_handler(request)

            # Add rate limit headers
            remaining = await self._get_remaining_requests(client_key, rule)
            response.add_header("X-RateLimit-Limit", str(rule.requests_per_minute))
            response.add_header("X-RateLimit-Remaining", str(remaining))
            response.add_header(
                "X-RateLimit-Reset", str(self._get_reset_time(client_key, rule))
            )

            return response

        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            return await next_handler(request)

    def _get_client_key(self, request: APIRequest, rule: RateLimitRule) -> str:
        """Generate client key for rate limiting"""
        if rule.per_user and request.user_id:
            return f"user_{request.user_id}"
        if rule.per_ip:
            return f"ip_{request.client_ip}"
        return (
            f"user_{request.user_id}" if request.user_id else f"ip_{request.client_ip}"
        )

    def _is_blocked(self, client_key: str) -> bool:
        """Check if client is currently blocked"""
        if client_key in self.blocked_clients:
            if datetime.now(UTC) < self.blocked_clients[client_key]:
                return True
            # Unblock client
            del self.blocked_clients[client_key]
        return False

    async def _check_rate_limit(self, client_key: str, rule: RateLimitRule) -> bool:
        """Check if request is within rate limit"""
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=rule.window_size)

        # Initialize client data if not exists
        if client_key not in self.request_counts:
            self.request_counts[client_key] = {"requests": [], "last_reset": now}

        client_data = self.request_counts[client_key]

        # Clean old requests outside window
        client_data["requests"] = [
            req_time for req_time in client_data["requests"] if req_time > window_start
        ]

        # Check rate limit
        current_count = len(client_data["requests"])

        if current_count >= rule.requests_per_minute:
            return False

        # Check burst limit
        if rule.burst_limit:
            recent_requests = [
                req_time
                for req_time in client_data["requests"]
                if req_time > now - timedelta(seconds=10)  # Last 10 seconds
            ]
            if len(recent_requests) >= rule.burst_limit:
                return False

        # Record this request
        client_data["requests"].append(now)

        return True

    async def _get_remaining_requests(
        self, client_key: str, rule: RateLimitRule
    ) -> int:
        """Get remaining requests for client"""
        if client_key not in self.request_counts:
            return rule.requests_per_minute

        current_count = len(self.request_counts[client_key]["requests"])
        return max(0, rule.requests_per_minute - current_count)

    def _get_reset_time(self, client_key: str, rule: RateLimitRule) -> int:
        """Get reset time for rate limit window"""
        now = datetime.now(UTC)
        reset_time = now + timedelta(seconds=rule.window_size)
        return int(reset_time.timestamp())

    def _create_rate_limit_error(self, error: str, error_tr: str) -> APIResponse:
        """Create rate limit error response"""
        return APIResponse(
            request_id=str(uuid.uuid4()),
            status_code=429,
            headers={"Content-Type": "application/json", "Retry-After": "300"},
            body={
                "error": "Rate Limit Exceeded",
                "detail": error,
                "error_tr": "İstek Limiti Aşıldı",
                "detail_tr": error_tr,
            },
            processing_time_ms=1.0,
        )


class CompressionMiddleware:
    """Response compression middleware"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.min_size = config.get("min_size", 1000)  # Minimum size to compress
        self.compression_level = config.get("compression_level", 6)

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process compression middleware"""
        try:
            # Check if client accepts compression
            accept_encoding = request.headers.get("Accept-Encoding", "").lower()
            supports_gzip = "gzip" in accept_encoding

            response = await next_handler(request)

            # Compress response if conditions are met
            if (
                supports_gzip
                and response.body
                and self._should_compress(response)
                and self._get_response_size(response) >= self.min_size
            ):
                compressed_body = await self._compress_response_body(response.body)

                if compressed_body and len(compressed_body) < self._get_response_size(
                    response
                ):
                    response.body = {
                        "compressed_data": base64.b64encode(compressed_body).decode(
                            "utf-8"
                        )
                    }
                    response.add_header("Content-Encoding", "gzip")
                    response.add_header("X-Compressed", "true")

                    logger.debug(f"Response compressed for request {request.id}")

            return response

        except Exception as e:
            logger.error(f"Compression middleware error: {e}")
            return await next_handler(request)

    def _should_compress(self, response: APIResponse) -> bool:
        """Check if response should be compressed"""
        content_type = response.headers.get("Content-Type", "")

        # Don't compress already compressed content
        if "gzip" in response.headers.get("Content-Encoding", ""):
            return False

        # Compress text-based content
        compressible_types = [
            "application/json",
            "text/html",
            "text/plain",
            "text/css",
            "application/javascript",
            "text/xml",
        ]

        return any(ctype in content_type for ctype in compressible_types)

    def _get_response_size(self, response: APIResponse) -> int:
        """Get response body size"""
        if not response.body:
            return 0
        return len(json.dumps(response.body).encode("utf-8"))

    async def _compress_response_body(self, body: dict[str, Any]) -> bytes:
        """Compress response body"""
        try:
            json_data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            return gzip.compress(json_data, compresslevel=self.compression_level)
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return b""


class CachingMiddleware:
    """Response caching middleware"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_system = None
        self.default_ttl = config.get("default_ttl", 300)  # 5 minutes

        # Routes that should not be cached
        self.no_cache_routes = {
            "/auth/login",
            "/auth/logout",
            "/exams/tyt/start",
            "/exams/ayt/start",
        }

    async def _get_cache_system(self):
        """Get cache system instance"""
        if not self.cache_system:
            self.cache_system = await get_unified_cache_system()
        return self.cache_system

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process caching middleware"""
        try:
            # Skip caching for non-cacheable routes
            if request.path in self.no_cache_routes or request.method != HTTPMethod.GET:
                return await next_handler(request)

            # Get route config for cache TTL
            route_config = request.metadata.get("route_config")
            cache_ttl = route_config.cache_ttl if route_config else self.default_ttl

            if not cache_ttl:
                return await next_handler(request)

            cache_system = await self._get_cache_system()
            cache_key = f"api_response:{request.get_cache_key()}"

            # Try to get cached response
            cached_response = await cache_system.cache_system.get(cache_key)
            if cached_response:
                cached_response["cached"] = True
                cached_response["from_middleware"] = "caching"

                logger.debug(f"Cache hit for request {request.id}")
                return APIResponse(**cached_response)

            # Process request
            response = await next_handler(request)

            # Cache successful responses
            if response.is_success() and response.body:
                cache_data = {
                    "request_id": response.request_id,
                    "status_code": response.status_code,
                    "headers": response.headers,
                    "body": response.body,
                    "processing_time_ms": response.processing_time_ms,
                    "timestamp": response.timestamp,
                }

                await cache_system.cache_system.set(
                    cache_key, cache_data, ttl=cache_ttl
                )

                logger.debug(
                    f"Response cached for request {request.id} (TTL: {cache_ttl}s)"
                )

            return response

        except Exception as e:
            logger.error(f"Caching middleware error: {e}")
            return await next_handler(request)


class TurkishLocalizationMiddleware:
    """Turkish localization middleware"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.translations = self._load_translations()

    def _load_translations(self) -> dict[str, dict[str, str]]:
        """Load Turkish translations"""
        return {
            "common": {
                "success": "başarılı",
                "failed": "başarısız",
                "error": "hata",
                "loading": "yükleniyor",
                "please_wait": "lütfen bekleyin",
                "invalid": "geçersiz",
                "required": "gerekli",
                "not_found": "bulunamadı",
            },
            "exam": {
                "exam_started": "sınav başlatıldı",
                "exam_completed": "sınav tamamlandı",
                "time_remaining": "kalan süre",
                "question": "soru",
                "answer": "cevap",
                "score": "puan",
                "ranking": "sıralama",
            },
            "auth": {
                "login_successful": "giriş başarılı",
                "logout_successful": "çıkış başarılı",
                "invalid_credentials": "geçersiz kimlik bilgileri",
                "session_expired": "oturum süresi doldu",
            },
        }

    async def __call__(
        self, request: APIRequest, next_handler: Callable
    ) -> APIResponse:
        """Process Turkish localization middleware"""
        try:
            # Set request locale information
            request.metadata["locale"] = "tr-TR"
            request.metadata["timezone"] = "Europe/Istanbul"

            response = await next_handler(request)

            # Add Turkish localization to response
            if response.body:
                response = await self._localize_response(response, request)

            # Add localization headers
            response.add_header("Content-Language", "tr-TR")
            response.add_header("X-Locale", "turkish")
            response.add_header("X-Timezone", "Europe/Istanbul")

            return response

        except Exception as e:
            logger.error(f"Turkish localization middleware error: {e}")
            return await next_handler(request)

    async def _localize_response(
        self, response: APIResponse, request: APIRequest
    ) -> APIResponse:
        """Add Turkish translations to response"""
        try:
            if not isinstance(response.body, dict):
                return response

            # Add Turkish timestamp format
            if "timestamp" in response.body:
                try:
                    dt = datetime.fromisoformat(
                        response.body["timestamp"].replace("Z", "+00:00")
                    )
                    istanbul_tz = timezone(timedelta(hours=3))  # Turkey timezone
                    local_dt = dt.astimezone(istanbul_tz)
                    response.body["timestamp_tr"] = local_dt.strftime("%d.%m.%Y %H:%M")
                except Exception:
                    pass

            # Add route-specific Turkish content
            route_type = (
                request.route_type.value if hasattr(request, "route_type") else ""
            )

            if route_type == "yks_info":
                response.body[
                    "platform_name"
                ] = "KIRO2 - Türkiye Üniversite Sınavları Hazırlık Platformu"

            # Add Turkish success/error messages if not present
            if "message" in response.body and "message_tr" not in response.body:
                response.body["message_tr"] = self._translate_message(
                    response.body["message"]
                )

            return response

        except Exception as e:
            logger.error(f"Response localization error: {e}")
            return response

    def _translate_message(self, message: str) -> str:
        """Simple message translation"""
        message_lower = message.lower()

        # Check all translation categories
        for category, translations in self.translations.items():
            for en_key, tr_value in translations.items():
                if en_key in message_lower:
                    return message.replace(en_key, tr_value)

        return message  # Return original if no translation found


# Middleware factory functions


def create_security_middleware(config: dict[str, Any] = None) -> SecurityMiddleware:
    """Create security middleware instance"""
    config = config or {}
    return SecurityMiddleware(config)


def create_validation_middleware(
    config: dict[str, Any] = None
) -> RequestValidationMiddleware:
    """Create request validation middleware instance"""
    config = config or {}
    return RequestValidationMiddleware(config)


def create_rate_limiting_middleware(
    config: dict[str, Any] = None
) -> RateLimitingMiddleware:
    """Create rate limiting middleware instance"""
    config = config or {}
    return RateLimitingMiddleware(config)


def create_compression_middleware(
    config: dict[str, Any] = None
) -> CompressionMiddleware:
    """Create compression middleware instance"""
    config = config or {}
    return CompressionMiddleware(config)


def create_caching_middleware(config: dict[str, Any] = None) -> CachingMiddleware:
    """Create caching middleware instance"""
    config = config or {}
    return CachingMiddleware(config)


def create_turkish_localization_middleware(
    config: dict[str, Any] = None
) -> TurkishLocalizationMiddleware:
    """Create Turkish localization middleware instance"""
    config = config or {}
    return TurkishLocalizationMiddleware(config)


# Middleware configuration helpers


def get_default_middleware_stack() -> list[tuple[str, Callable, int]]:
    """Get default middleware stack with priorities"""
    return [
        ("security", create_security_middleware(), MiddlewarePriority.CRITICAL.value),
        (
            "rate_limiting",
            create_rate_limiting_middleware(),
            MiddlewarePriority.HIGH.value,
        ),
        ("validation", create_validation_middleware(), MiddlewarePriority.NORMAL.value),
        ("caching", create_caching_middleware(), MiddlewarePriority.NORMAL.value),
        ("compression", create_compression_middleware(), MiddlewarePriority.LOW.value),
        (
            "turkish_localization",
            create_turkish_localization_middleware(),
            MiddlewarePriority.LOWEST.value,
        ),
    ]


def configure_middleware_for_route(route_type: str) -> list[str]:
    """Get middleware configuration for specific route type"""
    route_middleware = {
        "auth": ["security", "rate_limiting", "validation", "turkish_localization"],
        "tyt_exam": ["security", "rate_limiting", "validation", "turkish_localization"],
        "ayt_exam": ["security", "rate_limiting", "validation", "turkish_localization"],
        "yks_info": ["security", "caching", "compression", "turkish_localization"],
        "practice_tests": ["security", "validation", "caching", "turkish_localization"],
        "user_profile": ["security", "validation", "caching", "turkish_localization"],
        "health": ["security"],
        "default": [
            "security",
            "rate_limiting",
            "validation",
            "caching",
            "compression",
            "turkish_localization",
        ],
    }

    return route_middleware.get(route_type, route_middleware["default"])
