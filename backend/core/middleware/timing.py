"""
Timing Middleware - API Response Time Optimization

Bu modül, request timing tracking, slow request logging ve
percentile hesaplama için middleware sağlar.

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-6.2, REQ-6.5
"""

import logging
import statistics
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


@dataclass
class EndpointStats:
    """
    Endpoint için istatistikler.

    Attributes:
        endpoint: API endpoint path
        method: HTTP method
        timings: Son N request'in timing değerleri (ms)
        request_count: Toplam request sayısı
        error_count: Hata sayısı (5xx)
        last_updated: Son güncelleme zamanı
    """
    endpoint: str
    method: str
    timings: deque = field(default_factory=lambda: deque(maxlen=1000))
    request_count: int = 0
    error_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def add_timing(self, duration_ms: float, is_error: bool = False) -> None:
        """Timing ekler."""
        self.timings.append(duration_ms)
        self.request_count += 1
        if is_error:
            self.error_count += 1
        self.last_updated = datetime.now(UTC)

    def get_percentile(self, p: float) -> float:
        """P-th percentile hesaplar."""
        if not self.timings:
            return 0.0
        sorted_timings = sorted(self.timings)
        idx = int(len(sorted_timings) * p / 100)
        return sorted_timings[min(idx, len(sorted_timings) - 1)]

    @property
    def p50(self) -> float:
        """P50 (median) döndürür."""
        return self.get_percentile(50)

    @property
    def p95(self) -> float:
        """P95 döndürür."""
        return self.get_percentile(95)

    @property
    def p99(self) -> float:
        """P99 döndürür."""
        return self.get_percentile(99)

    @property
    def avg(self) -> float:
        """Ortalama döndürür."""
        if not self.timings:
            return 0.0
        return statistics.mean(self.timings)

    def to_dict(self) -> dict:
        """Dictionary'e dönüştürür."""
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "p50_ms": round(self.p50, 2),
            "p95_ms": round(self.p95, 2),
            "p99_ms": round(self.p99, 2),
            "avg_ms": round(self.avg, 2),
            "last_updated": self.last_updated.isoformat()
        }


class TimingStatsManager:
    """
    Timing istatistikleri yöneticisi.

    Tüm endpoint'ler için timing stats tutar ve percentile hesaplar.

    Attributes:
        slow_threshold_ms: Slow request threshold (ms)
        stats: Endpoint stats dictionary

    Example:
        manager = TimingStatsManager(slow_threshold_ms=200)
        manager.record("/api/users", "GET", 150.5)
        stats = manager.get_stats("/api/users", "GET")
    """

    def __init__(self, slow_threshold_ms: float = 200.0):
        """
        TimingStatsManager başlatır.

        Args:
            slow_threshold_ms: Slow request threshold (milliseconds)
        """
        self.slow_threshold_ms = slow_threshold_ms
        self._stats: dict[str, EndpointStats] = {}

        logger.info(f"TimingStatsManager initialized: slow_threshold={slow_threshold_ms}ms")

    def _get_key(self, endpoint: str, method: str) -> str:
        """Stats key oluşturur."""
        return f"{method}:{endpoint}"

    def record(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int = 200
    ) -> None:
        """
        Request timing kaydeder.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            duration_ms: Request duration (milliseconds)
            status_code: HTTP status code
        """
        key = self._get_key(endpoint, method)

        if key not in self._stats:
            self._stats[key] = EndpointStats(endpoint=endpoint, method=method)

        is_error = status_code >= 500
        self._stats[key].add_timing(duration_ms, is_error)

        # Log slow requests
        if duration_ms > self.slow_threshold_ms:
            logger.warning(
                f"Slow request: {method} {endpoint} took {duration_ms:.2f}ms "
                f"(threshold: {self.slow_threshold_ms}ms, status: {status_code})"
            )

    def get_stats(self, endpoint: str, method: str) -> EndpointStats | None:
        """
        Endpoint stats döndürür.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Returns:
            EndpointStats veya None
        """
        key = self._get_key(endpoint, method)
        return self._stats.get(key)

    def get_all_stats(self) -> list[dict]:
        """Tüm endpoint stats'larını döndürür."""
        return [stats.to_dict() for stats in self._stats.values()]

    def get_slow_endpoints(self, threshold_ms: float | None = None) -> list[dict]:
        """
        Slow endpoint'leri döndürür.

        Args:
            threshold_ms: Custom threshold (default: self.slow_threshold_ms)

        Returns:
            P95 > threshold olan endpoint'ler
        """
        threshold = threshold_ms or self.slow_threshold_ms
        slow = []
        for stats in self._stats.values():
            if stats.p95 > threshold:
                slow.append(stats.to_dict())
        return sorted(slow, key=lambda x: x["p95_ms"], reverse=True)

    def clear(self) -> None:
        """Tüm stats'ları temizler."""
        self._stats.clear()
        logger.info("Timing stats cleared")


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Request timing middleware.

    Her request için X-Response-Time header ekler ve timing stats toplar.

    Attributes:
        stats_manager: TimingStatsManager instance
        exclude_paths: Timing'den hariç tutulacak path'ler

    Example:
        app.add_middleware(
            TimingMiddleware,
            stats_manager=TimingStatsManager(),
            exclude_paths=["/health", "/metrics"]
        )
    """

    def __init__(
        self,
        app,
        stats_manager: TimingStatsManager | None = None,
        exclude_paths: list[str] | None = None
    ):
        """
        TimingMiddleware başlatır.

        Args:
            app: ASGI application
            stats_manager: TimingStatsManager (default: global instance)
            exclude_paths: Hariç tutulacak path'ler
        """
        super().__init__(app)
        self.stats_manager = stats_manager or get_timing_stats_manager()
        self.exclude_paths = set(exclude_paths or ["/health", "/metrics", "/favicon.ico"])

        logger.info(f"TimingMiddleware initialized: exclude_paths={self.exclude_paths}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Request'i işler ve timing ekler.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response with X-Response-Time header
        """
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Record start time
        start_time = time.perf_counter()

        # Process request
        try:
            response = await call_next(request)
        except Exception:
            # Record error timing
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.stats_manager.record(
                endpoint=request.url.path,
                method=request.method,
                duration_ms=duration_ms,
                status_code=500
            )
            raise

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add X-Response-Time header (milliseconds)
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Record timing
        self.stats_manager.record(
            endpoint=request.url.path,
            method=request.method,
            duration_ms=duration_ms,
            status_code=response.status_code
        )

        return response


class CORSPreflightCache:
    """
    CORS preflight response cache.

    OPTIONS request'leri için response cache tutar (24h TTL).

    Attributes:
        ttl_seconds: Cache TTL (saniye)
        cache: Origin -> cached response

    Example:
        cache = CORSPreflightCache(ttl_seconds=86400)  # 24h
        cached = cache.get(origin="https://example.com")
    """

    def __init__(self, ttl_seconds: int = 86400):
        """
        CORSPreflightCache başlatır.

        Args:
            ttl_seconds: Cache TTL (default: 24 hours)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[dict, datetime]] = {}

        logger.info(f"CORSPreflightCache initialized: TTL={ttl_seconds}s")

    def get(self, origin: str) -> dict | None:
        """
        Cached preflight response döndürür.

        Args:
            origin: Request origin

        Returns:
            Cached headers veya None
        """
        if origin not in self._cache:
            return None

        headers, cached_at = self._cache[origin]

        # Check expiration
        if datetime.now(UTC) - cached_at > timedelta(seconds=self.ttl_seconds):
            del self._cache[origin]
            return None

        return headers

    def set(self, origin: str, headers: dict) -> None:
        """
        Preflight response cache'ler.

        Args:
            origin: Request origin
            headers: CORS headers
        """
        self._cache[origin] = (headers, datetime.now(UTC))

    def clear(self) -> None:
        """Cache'i temizler."""
        self._cache.clear()


class JWTTokenCache:
    """
    JWT token validation cache.

    Validate edilmiş token'ları cache'ler.

    Attributes:
        default_ttl: Default TTL (saniye)
        cache: Token hash -> (user_data, expiry)

    Example:
        cache = JWTTokenCache(default_ttl=300)
        cache.set(token_hash="abc123", user_data={"user_id": 1})
        user = cache.get(token_hash="abc123")
    """

    def __init__(self, default_ttl: int = 300):
        """
        JWTTokenCache başlatır.

        Args:
            default_ttl: Default cache TTL (saniye)
        """
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[dict, datetime]] = {}
        self._max_size = 10000

        logger.info(f"JWTTokenCache initialized: default_ttl={default_ttl}s")

    def _hash_token(self, token: str) -> str:
        """Token'ı hash'ler."""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()[:32]

    def get(self, token: str) -> dict | None:
        """
        Cached user data döndürür.

        Args:
            token: JWT token

        Returns:
            User data veya None
        """
        token_hash = self._hash_token(token)

        if token_hash not in self._cache:
            return None

        user_data, expiry = self._cache[token_hash]

        if datetime.now(UTC) > expiry:
            del self._cache[token_hash]
            return None

        return user_data

    def set(self, token: str, user_data: dict, ttl: int | None = None) -> None:
        """
        Token validation sonucunu cache'ler.

        Args:
            token: JWT token
            user_data: Validated user data
            ttl: Custom TTL (default: self.default_ttl)
        """
        # Evict if cache is full
        if len(self._cache) >= self._max_size:
            self._evict_expired()

        token_hash = self._hash_token(token)
        expiry = datetime.now(UTC) + timedelta(seconds=ttl or self.default_ttl)
        self._cache[token_hash] = (user_data, expiry)

    def invalidate(self, token: str) -> None:
        """Token'ı cache'den kaldırır."""
        token_hash = self._hash_token(token)
        self._cache.pop(token_hash, None)

    def _evict_expired(self) -> None:
        """Expired entry'leri temizler."""
        now = datetime.now(UTC)
        expired = [k for k, (_, exp) in self._cache.items() if now > exp]
        for key in expired:
            del self._cache[key]

    def clear(self) -> None:
        """Cache'i temizler."""
        self._cache.clear()


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

_timing_stats_manager: TimingStatsManager | None = None


def get_timing_stats_manager() -> TimingStatsManager:
    """Global TimingStatsManager instance döndürür."""
    global _timing_stats_manager
    if _timing_stats_manager is None:
        _timing_stats_manager = TimingStatsManager()
    return _timing_stats_manager
