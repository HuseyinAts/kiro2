"""
DDoS Protection with SlowAPI Integration
Advanced DDoS prevention with multiple protection layers

Features:
- SlowAPI integration for FastAPI
- IP-based rate limiting
- Adaptive throttling
- Distributed rate limiting with Redis
- Request pattern analysis
- Automatic IP blocking
- Whitelist/Blacklist management
"""
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import redis
from fastapi import FastAPI, HTTPException, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from core.config import get_settings
from core.structured_logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ==================== SLOWAPI CONFIGURATION ====================


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key based on request

    Priority:
    1. User ID (if authenticated)
    2. API Key (if provided)
    3. IP Address (default)
    """
    # Check for authenticated user
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.get('id', 'unknown')}"

    # Check for API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:16]}"  # Hash prefix for security

    # Default to IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get first IP from X-Forwarded-For
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    return f"ip:{ip}"


# Initialize SlowAPI limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["1000/hour", "200/minute"],  # Default global limits
    storage_uri=settings.redis_url if hasattr(settings, "redis_url") else "memory://",
    strategy="fixed-window",  # Valid strategies: fixed-window, moving-window
    headers_enabled=True,  # Add X-RateLimit-* headers
)


# ==================== ADAPTIVE RATE LIMITING ====================


@dataclass
class AdaptiveRateLimitConfig:
    """Adaptive rate limit configuration"""

    normal_rpm: int = 200  # Requests per minute (normal)
    suspicious_rpm: int = 100  # Requests per minute (suspicious)
    attack_rpm: int = 20  # Requests per minute (under attack)

    normal_rph: int = 1000  # Requests per hour (normal)
    suspicious_rph: int = 500  # Requests per hour (suspicious)
    attack_rph: int = 100  # Requests per hour (under attack)

    # Thresholds
    suspicious_threshold: int = 150  # Requests in 1 min to be suspicious
    attack_threshold: int = 300  # Requests in 1 min to trigger attack mode


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts limits based on traffic patterns
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        config: AdaptiveRateLimitConfig | None = None,
    ):
        self.redis = redis_client
        self.config = config or AdaptiveRateLimitConfig()
        self.mode = "normal"  # normal, suspicious, attack
        self.mode_changed_at = time.time()

    def get_current_limits(self, ip: str) -> dict[str, int]:
        """Get current rate limits based on mode"""
        if self.mode == "attack":
            return {"rpm": self.config.attack_rpm, "rph": self.config.attack_rph}
        if self.mode == "suspicious":
            return {
                "rpm": self.config.suspicious_rpm,
                "rph": self.config.suspicious_rph,
            }
        return {"rpm": self.config.normal_rpm, "rph": self.config.normal_rph}

    def analyze_traffic(self):
        """Analyze global traffic and adjust mode"""
        if not self.redis:
            return

        try:
            now = time.time()
            minute_key = f"traffic:global:{int(now // 60)}"

            # Get requests in last minute
            requests_last_minute = int(self.redis.get(minute_key) or 0)

            # Adjust mode based on traffic
            if requests_last_minute > self.config.attack_threshold:
                if self.mode != "attack":
                    self.mode = "attack"
                    self.mode_changed_at = now
                    logger.warning(
                        f"[DDoS PROTECTION] Switched to ATTACK mode - {requests_last_minute} req/min"
                    )
            elif requests_last_minute > self.config.suspicious_threshold:
                if self.mode == "normal":
                    self.mode = "suspicious"
                    self.mode_changed_at = now
                    logger.warning(
                        f"[DDoS PROTECTION] Switched to SUSPICIOUS mode - {requests_last_minute} req/min"
                    )
            # Cool down period: stay in protective mode for at least 5 minutes
            elif self.mode != "normal" and (now - self.mode_changed_at) > 300:
                self.mode = "normal"
                logger.info("[DDoS PROTECTION] Returned to NORMAL mode")

        except Exception as e:
            logger.error(f"Traffic analysis error: {e}")


# ==================== IP BLACKLIST/WHITELIST ====================


class IPAccessControl:
    """IP-based access control"""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client
        self.whitelist: set[str] = set()
        self.blacklist: set[str] = set()
        self.temp_blacklist: dict[str, float] = {}  # IP -> expiry time

        # Load from environment/config
        self._load_static_lists()

    def _load_static_lists(self):
        """Load static whitelist/blacklist"""
        # Add trusted IPs to whitelist
        self.whitelist.add("127.0.0.1")
        self.whitelist.add("::1")

        # You can add more from environment variables
        # whitelist_env = os.getenv("IP_WHITELIST", "")
        # if whitelist_env:
        #     self.whitelist.update(whitelist_env.split(","))

    def is_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        if ip in self.whitelist:
            return True

        if self.redis:
            return self.redis.sismember("ip:whitelist", ip)

        return False

    def is_blacklisted(self, ip: str) -> bool:
        """Check if IP is blacklisted"""
        # Check permanent blacklist
        if ip in self.blacklist:
            return True

        if self.redis:
            if self.redis.sismember("ip:blacklist:permanent", ip):
                return True

            # Check temporary blacklist
            ttl = self.redis.ttl(f"ip:blacklist:temp:{ip}")
            if ttl > 0:
                return True

        # Check in-memory temp blacklist
        if ip in self.temp_blacklist:
            if time.time() < self.temp_blacklist[ip]:
                return True
            del self.temp_blacklist[ip]

        return False

    def block_ip(
        self, ip: str, duration: int | None = None, reason: str = "DDoS protection"
    ):
        """
        Block IP address

        Args:
            ip: IP address to block
            duration: Block duration in seconds (None = permanent)
            reason: Reason for blocking
        """
        logger.warning(f"[DDoS PROTECTION] Blocking IP {ip}: {reason}")

        if duration is None:
            # Permanent block
            self.blacklist.add(ip)
            if self.redis:
                self.redis.sadd("ip:blacklist:permanent", ip)
        else:
            # Temporary block
            expiry = time.time() + duration
            self.temp_blacklist[ip] = expiry

            if self.redis:
                key = f"ip:blacklist:temp:{ip}"
                self.redis.setex(key, duration, reason)

    def unblock_ip(self, ip: str):
        """Unblock IP address"""
        logger.info(f"[DDoS PROTECTION] Unblocking IP {ip}")

        self.blacklist.discard(ip)
        self.temp_blacklist.pop(ip, None)

        if self.redis:
            self.redis.srem("ip:blacklist:permanent", ip)
            self.redis.delete(f"ip:blacklist:temp:{ip}")


# ==================== REQUEST PATTERN ANALYSIS ====================


class RequestPatternAnalyzer:
    """Analyze request patterns for anomaly detection"""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client
        self.patterns: dict[str, list[dict]] = defaultdict(list)

    def analyze(self, request: Request, ip: str) -> dict[str, Any]:
        """
        Analyze request for suspicious patterns

        Returns:
            dict with suspicion score and details
        """
        suspicion_score = 0
        reasons = []

        # Pattern 1: Missing or suspicious User-Agent
        user_agent = request.headers.get("User-Agent", "")
        if not user_agent:
            suspicion_score += 20
            reasons.append("Missing User-Agent")
        elif len(user_agent) < 10:
            suspicion_score += 15
            reasons.append("Suspicious User-Agent")

        # Pattern 2: Unusual request method
        if request.method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]:
            suspicion_score += 30
            reasons.append("Unusual HTTP method")

        # Pattern 3: No Referer for POST requests (potential CSRF)
        if request.method == "POST":
            referer = request.headers.get("Referer", "")
            if not referer:
                suspicion_score += 10
                reasons.append("Missing Referer on POST")

        # Pattern 4: Rapid endpoint scanning
        endpoint = str(request.url.path)
        recent_endpoints = self._get_recent_endpoints(ip)
        unique_endpoints = len(set(recent_endpoints))

        if unique_endpoints > 20:  # 20+ different endpoints in short time
            suspicion_score += 25
            reasons.append(f"Endpoint scanning ({unique_endpoints} endpoints)")

        # Pattern 5: SQL injection or XSS in query params
        query_string = str(request.url.query)
        if self._contains_attack_patterns(query_string):
            suspicion_score += 50
            reasons.append("Attack patterns in query string")

        return {
            "score": suspicion_score,
            "reasons": reasons,
            "is_suspicious": suspicion_score >= 30,
            "is_attack": suspicion_score >= 60,
        }

    def _get_recent_endpoints(self, ip: str) -> list[str]:
        """Get recently accessed endpoints for IP"""
        if self.redis:
            key = f"pattern:endpoints:{ip}"
            return [e.decode() for e in self.redis.lrange(key, 0, -1)]
        return self.patterns.get(ip, [])

    def _contains_attack_patterns(self, text: str) -> bool:
        """Check for common attack patterns"""
        attack_patterns = [
            "union select",
            "drop table",
            "<script",
            "javascript:",
            "../",
            "etc/passwd",
            "cmd.exe",
        ]
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in attack_patterns)


# ==================== DDOS PROTECTION MIDDLEWARE ====================


class DDoSProtectionMiddleware:
    """
    Comprehensive DDoS protection middleware

    Combines:
    - IP blacklist/whitelist
    - Adaptive rate limiting
    - Request pattern analysis
    - Automatic blocking
    """

    def __init__(
        self,
        app: FastAPI,
        redis_client: redis.Redis | None = None,
        enable_adaptive: bool = True,
        enable_pattern_analysis: bool = True,
    ):
        self.app = app
        self.redis = redis_client

        self.ip_control = IPAccessControl(redis_client)
        self.adaptive_limiter = (
            AdaptiveRateLimiter(redis_client) if enable_adaptive else None
        )
        self.pattern_analyzer = (
            RequestPatternAnalyzer(redis_client) if enable_pattern_analysis else None
        )

        self.last_traffic_analysis = time.time()

    async def __call__(self, request: Request, call_next):
        """Process request with DDoS protection"""
        # Get client IP
        ip = get_remote_address(request)

        # Check whitelist (bypass all checks)
        if self.ip_control.is_whitelisted(ip):
            return await call_next(request)

        # Check blacklist
        if self.ip_control.is_blacklisted(ip):
            logger.warning(f"[DDoS PROTECTION] Blocked blacklisted IP: {ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # Adaptive traffic analysis (every 10 seconds)
        now = time.time()
        if self.adaptive_limiter and (now - self.last_traffic_analysis) > 10:
            self.adaptive_limiter.analyze_traffic()
            self.last_traffic_analysis = now

        # Pattern analysis
        if self.pattern_analyzer:
            analysis = self.pattern_analyzer.analyze(request, ip)

            if analysis["is_attack"]:
                # High suspicion - block immediately
                self.ip_control.block_ip(
                    ip, duration=3600, reason=", ".join(analysis["reasons"])
                )
                logger.error(
                    f"[DDoS PROTECTION] Blocked attack from {ip}",
                    extra_data={"analysis": analysis},
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Suspicious activity detected",
                )

            if analysis["is_suspicious"]:
                # Moderate suspicion - log and monitor
                logger.warning(
                    f"[DDoS PROTECTION] Suspicious request from {ip}",
                    extra_data={"analysis": analysis},
                )

        # Continue with request
        return await call_next(request)


# ==================== HELPER FUNCTIONS ====================


def setup_ddos_protection(
    app: FastAPI,
    redis_url: str | None = None,
    enable_slowapi: bool = True,
    enable_adaptive: bool = True,
    enable_pattern_analysis: bool = True,
) -> dict[str, Any]:
    """
    Setup comprehensive DDoS protection

    Args:
        app: FastAPI application
        redis_url: Redis connection URL
        enable_slowapi: Enable SlowAPI integration
        enable_adaptive: Enable adaptive rate limiting
        enable_pattern_analysis: Enable pattern analysis

    Returns:
        Dictionary with protection components
    """
    # Setup Redis connection
    redis_client = None
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url, decode_responses=False)
            redis_client.ping()
            logger.info("[DDoS PROTECTION] Redis connection established")
        except Exception as e:
            logger.error(f"[DDoS PROTECTION] Redis connection failed: {e}")

    # Setup SlowAPI
    if enable_slowapi:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        logger.info("[DDoS PROTECTION] SlowAPI configured")

    # Setup DDoS middleware
    middleware = DDoSProtectionMiddleware(
        app,
        redis_client=redis_client,
        enable_adaptive=enable_adaptive,
        enable_pattern_analysis=enable_pattern_analysis,
    )

    logger.info(
        "[DDoS PROTECTION] Protection enabled",
        extra_data={
            "slowapi": enable_slowapi,
            "adaptive": enable_adaptive,
            "pattern_analysis": enable_pattern_analysis,
            "redis": redis_client is not None,
        },
    )

    return {
        "limiter": limiter if enable_slowapi else None,
        "middleware": middleware,
        "redis": redis_client,
        "ip_control": middleware.ip_control,
    }


# ==================== DECORATORS ====================


def rate_limit(limit: str):
    """
    Rate limit decorator for routes

    Usage:
        @app.get("/api/endpoint")
        @rate_limit("10/minute")
        async def endpoint():
            ...
    """
    return limiter.limit(limit)


# ==================== EXPORT ====================

__all__ = [
    "AdaptiveRateLimiter",
    "DDoSProtectionMiddleware",
    "IPAccessControl",
    "RequestPatternAnalyzer",
    "get_rate_limit_key",
    "limiter",
    "rate_limit",
    "setup_ddos_protection",
]
