"""
Middleware modulu - API optimizasyonu icin middleware'ler.

Bu modul asagidaki middleware'leri icerir:
- TimeoutMiddleware: Endpoint bazli timeout yonetimi
- CacheMiddleware: HTTP cache header yonetimi (ETag, Cache-Control)
- GZipMiddleware: Gzip response sikistirma (REQ-2.1, REQ-2.2, REQ-2.3, REQ-2.6)
"""

from core.middleware.timeout_middleware import TimeoutMiddleware, get_timeout_middleware
from core.middleware.cache_headers import CacheMiddleware, CachePolicy
from core.middleware.compression import (
    GZipMiddleware,
    get_gzip_middleware,
    EXCLUDED_CONTENT_TYPES,
    COMPRESSIBLE_CONTENT_TYPES,
)
from core.middleware.timing import (
    TimingMiddleware,
    EndpointStats,
    TimingStatsManager,
    CORSPreflightCache,
    JWTTokenCache,
    get_timing_stats_manager,
)

__all__ = [
    # Timeout middleware
    "TimeoutMiddleware",
    "get_timeout_middleware",
    # Cache middleware
    "CacheMiddleware",
    "CachePolicy",
    # Compression middleware (Task 2.1.1)
    "GZipMiddleware",
    "get_gzip_middleware",
    "EXCLUDED_CONTENT_TYPES",
    "COMPRESSIBLE_CONTENT_TYPES",
    # Timing middleware (Task 6.1.2)
    "TimingMiddleware",
    "EndpointStats",
    "TimingStatsManager",
    "CORSPreflightCache",
    "JWTTokenCache",
    "get_timing_stats_manager",
]
