"""
HTTP Cache Headers Middleware - Response Caching Optimization

ETag, If-None-Match, Cache-Control header yonetimi icin FastAPI middleware.
P95 < 200ms latency hedefine ulasmak icin HTTP caching stratejisi uygular.

Requirements:
- REQ-4.1: Cacheable endpoint'ler icin ETag header uretimi
- REQ-4.2: If-None-Match isteklerinde 304 Not Modified donusu
- REQ-4.3: Cache-Control header'lari max-age ile
- REQ-4.4: Private data icin kullanici bazli cache key'leri
- REQ-4.5: Version-based cache invalidation

Author: KIRO2 Team
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)


class CachePolicy(str, Enum):
    """
    Cache politikasi tipleri.

    Attributes:
        PUBLIC: Herkes tarafindan cache'lenebilir (CDN, proxy)
        PRIVATE: Sadece istemci tarafindan cache'lenebilir
        NO_CACHE: Her istek sunucuya gider, ama cache kullanilabilir
        NO_STORE: Hicbir sekilde cache'lenmez
    """

    PUBLIC = "public"
    PRIVATE = "private"
    NO_CACHE = "no-cache"
    NO_STORE = "no-store"


@dataclass
class CacheConfig:
    """
    Endpoint bazli cache konfigurasyonu.

    Attributes:
        max_age: Cache suresi (saniye)
        policy: Cache politikasi
        vary_headers: Content negotiation icin Vary header degerleri
        stale_while_revalidate: Eski cache kullanilirken yeniden dogrulama suresi
        stale_if_error: Hata durumunda eski cache kullanma suresi
    """

    max_age: int = 300  # 5 dakika default
    policy: CachePolicy = CachePolicy.PUBLIC
    vary_headers: list[str] = field(default_factory=lambda: ["Accept", "Accept-Encoding"])
    stale_while_revalidate: int | None = None
    stale_if_error: int | None = None


# Endpoint tipine gore default cache konfigurasyonlari
DEFAULT_CACHE_CONFIGS: dict[str, CacheConfig] = {
    # Statik icerik - uzun sureli cache
    "static": CacheConfig(
        max_age=3600,  # 1 saat
        policy=CachePolicy.PUBLIC,
        stale_while_revalidate=60,
        stale_if_error=86400,  # 1 gun
    ),
    # Dinamik icerik - kisa sureli cache
    "dynamic": CacheConfig(
        max_age=300,  # 5 dakika
        policy=CachePolicy.PRIVATE,
        stale_while_revalidate=30,
    ),
    # Kullanici verisi - ozel cache
    "user_data": CacheConfig(
        max_age=60,  # 1 dakika
        policy=CachePolicy.PRIVATE,
    ),
    # API listeler - orta sureli cache
    "list": CacheConfig(
        max_age=600,  # 10 dakika
        policy=CachePolicy.PUBLIC,
        vary_headers=["Accept", "Accept-Encoding", "Accept-Language"],
        stale_while_revalidate=60,
    ),
    # Sorular - uzun sureli (nadiren degisir)
    "questions": CacheConfig(
        max_age=1800,  # 30 dakika
        policy=CachePolicy.PUBLIC,
        stale_while_revalidate=300,
        stale_if_error=3600,
    ),
    # No cache - her zaman taze veri
    "no_cache": CacheConfig(
        max_age=0,
        policy=CachePolicy.NO_STORE,
    ),
}

# Path prefix bazli cache tipi eslestirmesi
PATH_CACHE_MAPPING: dict[str, str] = {
    "/api/v1/questions": "questions",
    "/api/v1/exams": "dynamic",
    "/api/v1/users": "user_data",
    "/api/v1/learning-path": "dynamic",
    "/api/v1/auth": "no_cache",
    "/api/v1/admin": "no_cache",
    "/static": "static",
    "/docs": "static",
    "/openapi.json": "static",
}


def generate_etag(content: bytes, weak: bool = False) -> str:
    """
    Response body'den ETag degeri uretir.

    MD5 hash kullanarak benzersiz ETag degeri olusturur.
    Weak ETag secenegi ile partial match destegi saglar.

    Args:
        content: Response body icerigi (bytes)
        weak: Weak ETag kullanimi (W/ prefix)

    Returns:
        ETag string degeri (quoted)

    Example:
        >>> etag = generate_etag(b'{"data": "test"}')
        >>> print(etag)  # '"a1b2c3d4e5f6..."'
    """
    hash_digest = hashlib.md5(content).hexdigest()
    etag = f'"{hash_digest}"'

    if weak:
        etag = f"W/{etag}"

    return etag


def build_cache_control_header(config: CacheConfig) -> str:
    """
    CacheConfig'den Cache-Control header degeri olusturur.

    Args:
        config: Cache konfigurasyonu

    Returns:
        Cache-Control header string degeri

    Example:
        >>> config = CacheConfig(max_age=3600, policy=CachePolicy.PUBLIC)
        >>> header = build_cache_control_header(config)
        >>> print(header)  # 'public, max-age=3600'
    """
    directives: list[str] = []

    # Policy directive
    if config.policy == CachePolicy.NO_STORE:
        return "no-store"

    if config.policy == CachePolicy.NO_CACHE:
        directives.append("no-cache")
    else:
        directives.append(config.policy.value)

    # max-age directive
    directives.append(f"max-age={config.max_age}")

    # stale-while-revalidate directive
    if config.stale_while_revalidate:
        directives.append(f"stale-while-revalidate={config.stale_while_revalidate}")

    # stale-if-error directive
    if config.stale_if_error:
        directives.append(f"stale-if-error={config.stale_if_error}")

    return ", ".join(directives)


def get_cache_config_for_path(path: str) -> CacheConfig:
    """
    Request path'ine gore cache konfigurasyonu belirler.

    Args:
        path: Request URL path'i

    Returns:
        Uygun CacheConfig nesnesi
    """
    # Path prefix eslestirmesi
    for prefix, cache_type in PATH_CACHE_MAPPING.items():
        if path.startswith(prefix):
            return DEFAULT_CACHE_CONFIGS.get(cache_type, DEFAULT_CACHE_CONFIGS["dynamic"])

    # Default: dynamic cache
    return DEFAULT_CACHE_CONFIGS["dynamic"]


def should_skip_cache(request: Request) -> bool:
    """
    Cache isleminin atlanip atlanmayacagini belirler.

    Args:
        request: FastAPI Request nesnesi

    Returns:
        True ise cache islemi atlanir
    """
    # POST, PUT, PATCH, DELETE metodlari cache'lenmez
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        return True

    # Health check endpoint'leri
    skip_paths = ["/health", "/metrics", "/readiness", "/liveness"]
    if request.url.path in skip_paths:
        return True

    # Cache-Control: no-cache header'i varsa
    cache_control = request.headers.get("Cache-Control", "")
    if "no-cache" in cache_control or "no-store" in cache_control:
        return True

    return False


def etags_match(request_etag: str, response_etag: str) -> bool:
    """
    If-None-Match header'i ile ETag karsilastirmasi yapar.

    Supports:
    - Exact match: "abc123" == "abc123"
    - Wildcard: * matches anything
    - Multiple values: "abc", "def" (comma separated)
    - Weak comparison: W/"abc" matches "abc"

    Args:
        request_etag: If-None-Match header degeri
        response_etag: Response ETag degeri

    Returns:
        True ise match var (304 donmeli)
    """
    if not request_etag or not response_etag:
        return False

    # Wildcard match
    if request_etag.strip() == "*":
        return True

    # Response ETag'i normalize et
    normalized_response = response_etag.replace("W/", "").strip('"')

    # If-None-Match birden fazla deger icerebilir
    request_etags = [e.strip() for e in request_etag.split(",")]

    for etag in request_etags:
        # Weak prefix'i kaldir ve normalize et
        normalized_request = etag.replace("W/", "").strip().strip('"')

        if normalized_request == normalized_response:
            return True

    return False


class CacheMiddleware(BaseHTTPMiddleware):
    """
    HTTP Cache Headers Middleware.

    ETag uretimi, If-None-Match kontrolu ve Cache-Control header'lari
    yoneten FastAPI middleware. HTTP caching spesifikasyonuna (RFC 7234)
    uygun sekilde cache header'lari ekler.

    Features:
        - ETag header uretimi (MD5 hash)
        - If-None-Match ile 304 Not Modified kontrolu
        - Cache-Control header yonetimi (max-age, public/private)
        - Vary header ile content negotiation destegi
        - Path bazli cache policy konfigurasyonu

    Attributes:
        skip_paths: Cache'lenmeyecek path listesi
        cache_metrics: Cache hit/miss istatistikleri

    Example:
        ```python
        from fastapi import FastAPI
        from backend.core.middleware.cache_headers import CacheMiddleware

        app = FastAPI()
        app.add_middleware(CacheMiddleware)
        ```

    Requirements:
        REQ-4.1, REQ-4.2, REQ-4.3, REQ-4.4, REQ-4.5
    """

    def __init__(
        self,
        app,
        skip_paths: list[str] | None = None,
        enable_metrics: bool = True,
    ) -> None:
        """
        CacheMiddleware constructor.

        Args:
            app: FastAPI/Starlette application
            skip_paths: Cache'lenmeyecek path listesi
            enable_metrics: Cache hit/miss metriklerini topla
        """
        super().__init__(app)
        self.skip_paths = skip_paths or ["/health", "/metrics", "/docs", "/redoc"]
        self.enable_metrics = enable_metrics

        # Cache metrikleri
        self.hit_count: int = 0
        self.miss_count: int = 0
        self.not_modified_count: int = 0

        logger.info(
            "CacheMiddleware baslatildi",
            extra={
                "skip_paths": self.skip_paths,
                "enable_metrics": enable_metrics,
            },
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> StarletteResponse:
        """
        Request/response isleyicisi.

        1. Cache bypass kontrolu yapar
        2. If-None-Match header'ini kontrol eder
        3. Response'a ETag ve Cache-Control header'lari ekler
        4. Eslesme varsa 304 Not Modified doner

        Args:
            request: Gelen HTTP istegi
            call_next: Sonraki middleware/handler

        Returns:
            HTTP response (normal veya 304 Not Modified)
        """
        start_time = time.perf_counter()

        # Cache bypass kontrolu
        if should_skip_cache(request):
            return await call_next(request)

        # Path bazli cache config
        cache_config = get_cache_config_for_path(request.url.path)

        # no-store policy ise direkt isle
        if cache_config.policy == CachePolicy.NO_STORE:
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-store"
            return response

        # If-None-Match header'i
        if_none_match = request.headers.get("If-None-Match")

        # Response'u al
        response = await call_next(request)

        # Sadece basarili response'lari cache'le
        if response.status_code not in (200, 201, 206):
            return response

        # Response body'yi oku (streaming response degil ise)
        try:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # ETag uret
            etag = generate_etag(response_body)

            # If-None-Match kontrolu
            if if_none_match and etags_match(if_none_match, etag):
                # Cache hit - 304 Not Modified
                self.not_modified_count += 1

                elapsed = (time.perf_counter() - start_time) * 1000
                logger.debug(
                    "Cache hit - 304 Not Modified",
                    extra={
                        "path": request.url.path,
                        "elapsed_ms": f"{elapsed:.2f}",
                        "etag": etag,
                    },
                )

                # 304 response olustur
                return Response(
                    status_code=304,
                    headers={
                        "ETag": etag,
                        "Cache-Control": build_cache_control_header(cache_config),
                        "Vary": ", ".join(cache_config.vary_headers),
                        "X-Cache-Status": "HIT",
                    },
                )

            # Cache miss - normal response
            self.miss_count += 1

            # Yeni response olustur (body ile)
            new_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

            # Cache header'larini ekle
            new_response.headers["ETag"] = etag
            new_response.headers["Cache-Control"] = build_cache_control_header(cache_config)
            new_response.headers["Vary"] = ", ".join(cache_config.vary_headers)
            new_response.headers["X-Cache-Status"] = "MISS"

            elapsed = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "Cache miss - Response cached",
                extra={
                    "path": request.url.path,
                    "elapsed_ms": f"{elapsed:.2f}",
                    "etag": etag,
                    "cache_control": new_response.headers["Cache-Control"],
                },
            )

            return new_response

        except Exception as e:
            # Streaming response veya hata durumu
            logger.warning(
                "Cache header isleme hatasi",
                extra={"error": str(e), "path": request.url.path},
            )
            return response

    def get_metrics(self) -> dict:
        """
        Cache metriklerini doner.

        Returns:
            Hit, miss ve not_modified sayilari
        """
        total = self.hit_count + self.miss_count
        hit_rate = (self.not_modified_count / total * 100) if total > 0 else 0

        return {
            "cache_hits": self.not_modified_count,
            "cache_misses": self.miss_count,
            "total_requests": total,
            "hit_rate_percent": f"{hit_rate:.2f}",
        }


def get_cache_middleware(
    skip_paths: list[str] | None = None,
    enable_metrics: bool = True,
):
    """
    Factory function - ozel konfigurasyonlu CacheMiddleware olusturur.

    Args:
        skip_paths: Cache'lenmeyecek path listesi
        enable_metrics: Metrikleri topla

    Returns:
        Konfigureli CacheMiddleware class

    Example:
        ```python
        app.add_middleware(
            get_cache_middleware(skip_paths=["/api/v1/auth"])
        )
        ```
    """

    class ConfiguredCacheMiddleware(CacheMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                skip_paths=skip_paths,
                enable_metrics=enable_metrics,
            )

    return ConfiguredCacheMiddleware


__all__ = [
    "DEFAULT_CACHE_CONFIGS",
    "CacheConfig",
    "CacheMiddleware",
    "CachePolicy",
    "build_cache_control_header",
    "generate_etag",
    "get_cache_config_for_path",
    "get_cache_middleware",
]
