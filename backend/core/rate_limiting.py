"""
Rate Limiting Middleware
Advanced rate limiting with Redis backend, multiple strategies, and DDoS protection
"""
import ipaddress
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import redis
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from core.config import get_settings
from core.structured_logger import get_logger


class RateLimitStrategy(str, Enum):
    """Rate limiting stratejileri"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(str, Enum):
    """Rate limiting kapsamları"""

    IP = "ip"
    USER = "user"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    GLOBAL = "global"


@dataclass
class RateLimitRule:
    """Rate limiting kuralı"""

    scope: RateLimitScope
    strategy: RateLimitStrategy
    limit: int  # Request sayısı
    window: int  # Zaman penceresi (saniye)
    burst_limit: int | None = None  # Burst limit (token bucket için)
    endpoints: list[str] | None = None  # Hangi endpoint'ler için geçerli
    excluded_ips: list[str] | None = None  # Hariç tutulan IP'ler
    user_roles: list[str] | None = None  # Hangi roller için geçerli


@dataclass
class TokenBucket:
    """Token bucket data structure"""

    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.time)

    def consume(self, tokens: int = 1) -> bool:
        """Token tüket"""
        now = time.time()

        # Token'ları yenile
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now

        # Token tüket
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False


@dataclass
class SlidingWindow:
    """Sliding window data structure"""

    window_size: int
    limit: int
    requests: deque = field(default_factory=deque)

    def add_request(self) -> bool:
        """Request ekle"""
        now = time.time()

        # Eski request'leri temizle
        while self.requests and now - self.requests[0] > self.window_size:
            self.requests.popleft()

        # Limit kontrolü
        if len(self.requests) >= self.limit:
            return False

        self.requests.append(now)
        return True


class DDoSDetector:
    """DDoS saldırı tespiti"""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis_client = redis_client
        self.suspicious_patterns = defaultdict(list)
        self.blocked_ips: set[str] = set()

        # DDoS tespit parametreleri
        self.burst_threshold = 100  # 1 dakikada 100+ request
        self.sustained_threshold = 1000  # 10 dakikada 1000+ request
        self.unique_endpoint_threshold = 50  # 1 dakikada 50+ farklı endpoint

    def analyze_request(self, ip: str, endpoint: str, user_agent: str) -> bool:
        """Request'i analiz et ve DDoS olup olmadığını belirle"""
        now = time.time()

        # IP zaten bloklu mu?
        if ip in self.blocked_ips:
            return False

        # Redis'ten veri oku
        if self.redis_client:
            return self._analyze_with_redis(ip, endpoint, user_agent, now)
        return self._analyze_in_memory(ip, endpoint, user_agent, now)

    def _analyze_with_redis(
        self, ip: str, endpoint: str, user_agent: str, now: float
    ) -> bool:
        """Redis ile DDoS analizi"""
        pipe = self.redis_client.pipeline()

        # 1 dakikalık burst kontrolü
        burst_key = f"ddos:burst:{ip}:{int(now // 60)}"
        pipe.incr(burst_key)
        pipe.expire(burst_key, 60)

        # 10 dakikalık sustained kontrolü
        sustained_key = f"ddos:sustained:{ip}:{int(now // 600)}"
        pipe.incr(sustained_key)
        pipe.expire(sustained_key, 600)

        # Endpoint çeşitliliği kontrolü
        endpoint_key = f"ddos:endpoints:{ip}:{int(now // 60)}"
        pipe.sadd(endpoint_key, endpoint)
        pipe.expire(endpoint_key, 60)

        results = pipe.execute()

        burst_count = results[0]
        sustained_count = results[2]

        # Endpoint sayısını al
        endpoint_count = self.redis_client.scard(endpoint_key)

        # DDoS tespiti
        if (
            burst_count > self.burst_threshold
            or sustained_count > self.sustained_threshold
            or endpoint_count > self.unique_endpoint_threshold
        ):
            self._block_ip(ip, "DDoS pattern detected")
            return False

        return True

    def _analyze_in_memory(
        self, ip: str, endpoint: str, user_agent: str, now: float
    ) -> bool:
        """In-memory DDoS analizi"""
        # Eski record'ları temizle
        cutoff_time = now - 600  # 10 dakika
        self.suspicious_patterns[ip] = [
            record
            for record in self.suspicious_patterns[ip]
            if record["timestamp"] > cutoff_time
        ]

        # Yeni record ekle
        self.suspicious_patterns[ip].append(
            {"timestamp": now, "endpoint": endpoint, "user_agent": user_agent}
        )

        records = self.suspicious_patterns[ip]

        # Burst kontrolü (1 dakika)
        recent_records = [r for r in records if now - r["timestamp"] <= 60]
        if len(recent_records) > self.burst_threshold:
            self._block_ip(ip, "Burst threshold exceeded")
            return False

        # Sustained kontrolü (10 dakika)
        if len(records) > self.sustained_threshold:
            self._block_ip(ip, "Sustained threshold exceeded")
            return False

        # Endpoint çeşitliliği kontrolü
        unique_endpoints = set(r["endpoint"] for r in recent_records)
        if len(unique_endpoints) > self.unique_endpoint_threshold:
            self._block_ip(ip, "Too many unique endpoints")
            return False

        return True

    def _block_ip(self, ip: str, reason: str):
        """IP'yi blokla"""
        self.blocked_ips.add(ip)

        # Redis'e kaydet
        if self.redis_client:
            block_key = f"ddos:blocked:{ip}"
            self.redis_client.setex(block_key, 3600, reason)  # 1 saat blok

        logger = get_logger("ddos_detector")
        logger.warning(f"IP blocked: {ip} - Reason: {reason}")

    def is_blocked(self, ip: str) -> bool:
        """IP bloklu mu kontrol et"""
        if ip in self.blocked_ips:
            return True

        if self.redis_client:
            return self.redis_client.exists(f"ddos:blocked:{ip}")

        return False


class AdvancedRateLimiter:
    """Gelişmiş rate limiter"""

    def __init__(self, redis_url: str | None = None):
        self.rules: list[RateLimitRule] = []
        self.token_buckets: dict[str, TokenBucket] = {}
        self.sliding_windows: dict[str, SlidingWindow] = {}
        self.fixed_windows: dict[str, dict] = defaultdict(dict)

        # Redis bağlantısı
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
            except:
                self.redis_client = None

        # DDoS detector
        self.ddos_detector = DDoSDetector(self.redis_client)

        # Logger
        self.logger = get_logger("rate_limiter")

    def add_rule(self, rule: RateLimitRule):
        """Rate limiting kuralı ekle"""
        self.rules.append(rule)

    def check_rate_limit(self, request: Request, user_id: str | None = None) -> bool:
        """Rate limit kontrolü"""
        ip = self._get_client_ip(request)
        endpoint = str(request.url.path)
        user_agent = request.headers.get("user-agent", "")

        # DDoS kontrolü
        if not self.ddos_detector.analyze_request(ip, endpoint, user_agent):
            return False

        # Her kural için kontrol
        for rule in self.rules:
            if not self._check_rule(rule, request, ip, user_id, endpoint):
                return False

        return True

    def _check_rule(
        self,
        rule: RateLimitRule,
        request: Request,
        ip: str,
        user_id: str | None,
        endpoint: str,
    ) -> bool:
        """Belirli bir kural için rate limit kontrolü"""
        # Endpoint filtresi
        if rule.endpoints and endpoint not in rule.endpoints:
            return True

        # IP hariç tutma
        if rule.excluded_ips and ip in rule.excluded_ips:
            return True

        # Identifier oluştur
        identifier = self._get_identifier(rule.scope, ip, user_id, endpoint)

        # Strateji'ye göre kontrol
        if rule.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(identifier, rule)
        if rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(identifier, rule)
        if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(identifier, rule)
        if rule.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return self._check_leaky_bucket(identifier, rule)

        return True

    def _check_fixed_window(self, identifier: str, rule: RateLimitRule) -> bool:
        """Fixed window rate limiting"""
        now = time.time()
        window_start = int(now // rule.window) * rule.window

        if self.redis_client:
            key = f"rate_limit:fixed:{identifier}:{window_start}"
            current = self.redis_client.incr(key)
            self.redis_client.expire(key, rule.window)
            return current <= rule.limit
        # In-memory implementation
        if identifier not in self.fixed_windows:
            self.fixed_windows[identifier] = {}

        if window_start not in self.fixed_windows[identifier]:
            self.fixed_windows[identifier][window_start] = 0

        # Eski window'ları temizle
        old_windows = [
            w for w in self.fixed_windows[identifier] if w < window_start - rule.window
        ]
        for w in old_windows:
            del self.fixed_windows[identifier][w]

        self.fixed_windows[identifier][window_start] += 1
        return self.fixed_windows[identifier][window_start] <= rule.limit

    def _check_sliding_window(self, identifier: str, rule: RateLimitRule) -> bool:
        """Sliding window rate limiting with Redis ZSET (Task 51.2)"""
        if self.redis_client:
            return self._check_sliding_window_redis(identifier, rule)

        # Fallback to in-memory implementation
        if identifier not in self.sliding_windows:
            self.sliding_windows[identifier] = SlidingWindow(rule.window, rule.limit)

        return self.sliding_windows[identifier].add_request()

    def _check_sliding_window_redis(self, identifier: str, rule: RateLimitRule) -> bool:
        """
        Redis ZSET-based sliding window rate limiting (Task 51.2)

        Uses sorted set with timestamps as scores for accurate sliding window
        """
        import uuid

        now = time.time()
        window_start = now - rule.window
        key = f"rate_limit:sliding:{identifier}"

        pipe = self.redis_client.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        pipe.zcard(key)

        # Execute pipeline
        results = pipe.execute()
        request_count = results[1]

        # Check if under limit
        if request_count < rule.limit:
            # Add current request with timestamp as score
            request_id = str(uuid.uuid4())
            self.redis_client.zadd(key, {request_id: now})

            # Set expiry to window + buffer
            self.redis_client.expire(key, rule.window + 60)

            return True

        return False

    def _check_token_bucket(self, identifier: str, rule: RateLimitRule) -> bool:
        """Token bucket rate limiting"""
        if identifier not in self.token_buckets:
            capacity = rule.burst_limit or rule.limit
            refill_rate = rule.limit / rule.window
            self.token_buckets[identifier] = TokenBucket(
                capacity, capacity, refill_rate
            )

        return self.token_buckets[identifier].consume()

    def _check_leaky_bucket(self, identifier: str, rule: RateLimitRule) -> bool:
        """Leaky bucket rate limiting (simplified as sliding window)"""
        return self._check_sliding_window(identifier, rule)

    def _get_identifier(
        self, scope: RateLimitScope, ip: str, user_id: str | None, endpoint: str
    ) -> str:
        """Rate limiting identifier oluştur"""
        if scope == RateLimitScope.IP:
            return f"ip:{ip}"
        if scope == RateLimitScope.USER and user_id:
            return f"user:{user_id}"
        if scope == RateLimitScope.ENDPOINT:
            return f"endpoint:{endpoint}:{ip}"
        if scope == RateLimitScope.GLOBAL:
            return "global"
        return f"ip:{ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Client IP adresini al"""
        # X-Forwarded-For header'ını kontrol et
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # İlk IP'yi al (original client)
            ip = forwarded_for.split(",")[0].strip()
            try:
                # IP'nin geçerli olduğunu kontrol et
                ipaddress.ip_address(ip)
                return ip
            except:
                pass

        # X-Real-IP header'ını kontrol et
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            try:
                ipaddress.ip_address(real_ip)
                return real_ip
            except:
                pass

        # Client IP'yi al
        client_ip = request.client.host if request.client else "unknown"
        return client_ip

    def get_rate_limit_info(
        self, identifier: str, rule: RateLimitRule
    ) -> dict[str, Any]:
        """Rate limit bilgilerini al"""
        if rule.strategy == RateLimitStrategy.FIXED_WINDOW:
            now = time.time()
            window_start = int(now // rule.window) * rule.window

            if self.redis_client:
                key = f"rate_limit:fixed:{identifier}:{window_start}"
                used = self.redis_client.get(key) or 0
                used = int(used)
            else:
                used = self.fixed_windows.get(identifier, {}).get(window_start, 0)

            remaining = max(0, rule.limit - used)
            reset_time = window_start + rule.window

            return {
                "limit": rule.limit,
                "remaining": remaining,
                "used": used,
                "reset": reset_time,
            }

        if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            bucket = self.token_buckets.get(identifier)
            if bucket:
                return {
                    "limit": rule.limit,
                    "remaining": int(bucket.tokens),
                    "capacity": bucket.capacity,
                }

        return {"limit": rule.limit, "remaining": rule.limit}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, app, rate_limiter: AdvancedRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.logger = get_logger("rate_limit_middleware")

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Rate limit kontrolü
        try:
            # User ID'yi token'dan al (varsa)
            user_id = None
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # JWT token'dan user_id çıkar (optional)
                try:
                    from core.jwt_auth import jwt_manager

                    token = auth_header.split(" ")[1]
                    payload = jwt_manager.verify_token(token)
                    user_id = payload.sub
                except:
                    pass

            # Rate limit kontrolü
            if not self.rate_limiter.check_rate_limit(request, user_id):
                self.logger.warning(
                    f"Rate limit exceeded for {request.client.host} - {request.url.path}",
                    extra_data={"user_id": user_id, "endpoint": str(request.url.path)},
                )

                # Get rate limit info for better error message
                ip = self.rate_limiter._get_client_ip(request)
                primary_rule = (
                    self.rate_limiter.rules[0] if self.rate_limiter.rules else None
                )

                if primary_rule:
                    identifier = self.rate_limiter._get_identifier(
                        primary_rule.scope, ip, user_id, str(request.url.path)
                    )
                    rate_limit_info = self.rate_limiter.get_rate_limit_info(
                        identifier, primary_rule
                    )
                    retry_after = (
                        rate_limit_info.get("reset", time.time() + 60) - time.time()
                    )
                    retry_after = max(1, int(retry_after))
                else:
                    retry_after = 60

                import json

                error_response = {
                    "error": "Rate limit exceeded",
                    "message": f"Çok fazla istek gönderdiniz. Lütfen {retry_after} saniye sonra tekrar deneyin.",
                    "retry_after": retry_after,
                    "limit": rate_limit_info.get("limit", 0) if primary_rule else 0,
                    "window": primary_rule.window if primary_rule else 60,
                }

                return Response(
                    content=json.dumps(error_response),
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={
                        "Content-Type": "application/json",
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(error_response["limit"]),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            # Request'i işle
            response = await call_next(request)

            # Rate limit header'larını ekle
            # İlk kuraldan bilgi al (genel rate limit)
            if self.rate_limiter.rules:
                primary_rule = self.rate_limiter.rules[0]
                ip = self.rate_limiter._get_client_ip(request)
                identifier = self.rate_limiter._get_identifier(
                    primary_rule.scope, ip, user_id, str(request.url.path)
                )
                rate_limit_info = self.rate_limiter.get_rate_limit_info(
                    identifier, primary_rule
                )

                response.headers["X-RateLimit-Limit"] = str(
                    rate_limit_info.get("limit", 0)
                )
                response.headers["X-RateLimit-Remaining"] = str(
                    rate_limit_info.get("remaining", 0)
                )
                if "reset" in rate_limit_info:
                    response.headers["X-RateLimit-Reset"] = str(
                        int(rate_limit_info["reset"])
                    )

            return response

        except Exception as e:
            self.logger.error(f"Rate limiting error: {e!s}")
            # Hata durumunda request'i geçir (fail-open)
            return await call_next(request)


# Default rate limiting rules
def get_default_rate_limit_rules() -> list[RateLimitRule]:
    """Default rate limiting kuralları"""
    return [
        # Global rate limiting
        RateLimitRule(
            scope=RateLimitScope.IP,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            limit=1000,  # 1000 request per 10 minutes
            window=600,
        ),
        # API endpoint rate limiting
        RateLimitRule(
            scope=RateLimitScope.IP,
            strategy=RateLimitStrategy.FIXED_WINDOW,
            limit=100,  # 100 request per minute
            window=60,
            endpoints=["/api/auth/login", "/api/auth/register"],
        ),
        # Strict rate limiting for sensitive endpoints
        RateLimitRule(
            scope=RateLimitScope.IP,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            limit=5,  # 5 request per minute
            window=60,
            burst_limit=10,
            endpoints=["/api/auth/reset-password", "/api/auth/verify-email"],
        ),
        # User-based rate limiting
        RateLimitRule(
            scope=RateLimitScope.USER,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            limit=10000,  # 10000 request per hour for logged in users
            window=3600,
        ),
    ]


# Global rate limiter instance
def create_rate_limiter() -> AdvancedRateLimiter:
    """Rate limiter oluştur"""
    settings = get_settings()
    redis_url = getattr(settings, "redis_url", None)

    rate_limiter = AdvancedRateLimiter(redis_url)

    # Default kuralları ekle
    for rule in get_default_rate_limit_rules():
        rate_limiter.add_rule(rule)

    return rate_limiter


# Global instance
rate_limiter = create_rate_limiter()


def get_rate_limiter() -> AdvancedRateLimiter:
    """Rate limiter instance'ını döndür"""
    return rate_limiter
