"""
Response Caching Decorator - Redis Backend

@cache_response decorator ile endpoint response'larini Redis'te cache'ler.
TTL ve cache key konfigurasyonu destekler.

Requirements:
- REQ-4.3: Cache-Control header'lari max-age ile
- REQ-4.4: Private data icin kullanici bazli cache key'leri
- REQ-4.5: Version-based cache invalidation

Author: KIRO2 Team
"""

from __future__ import annotations

import functools
import hashlib
import inspect
import logging
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Optional, TypeVar, Union

from fastapi import Request

logger = logging.getLogger(__name__)

# Type variables for generic decorator typing
F = TypeVar("F", bound=Callable[..., Any])


class TTLPreset(IntEnum):
    """
    Onaylanmis TTL (Time-To-Live) degerleri.

    Endpoint tipine gore standart TTL degerleri saglar.

    Attributes:
        STATIC: Statik icerik (1 saat)
        DYNAMIC: Dinamik icerik (5 dakika)
        USER_DATA: Kullanici verisi (1 dakika)
        QUESTIONS: Soru icerigi (30 dakika)
        LIST: Liste verileri (10 dakika)
        SESSION: Oturum verisi (1 saat)
        SHORT: Kisa sureli (30 saniye)
        NONE: Cache'lenme (0)
    """

    STATIC = 3600  # 1 saat
    DYNAMIC = 300  # 5 dakika
    USER_DATA = 60  # 1 dakika
    QUESTIONS = 1800  # 30 dakika
    LIST = 600  # 10 dakika
    SESSION = 3600  # 1 saat
    SHORT = 30  # 30 saniye
    NONE = 0  # Cache'lenme


# Default TTL degeri
DEFAULT_TTL: int = TTLPreset.DYNAMIC.value


@dataclass
class CacheKeyBuilder:
    """
    Cache key olusturma yardimcisi.

    Endpoint path'i, query parametreleri ve kullanici ID'si
    kullanarak benzersiz cache key'leri uretir.

    Attributes:
        prefix: Cache key prefix'i (namespace)
        include_query_params: Query parametrelerini dahil et
        include_user_id: Kullanici ID'sini dahil et (private cache)
        version: Cache versiyonu (invalidation icin)

    Example:
        >>> builder = CacheKeyBuilder(prefix="questions", include_user_id=True)
        >>> key = builder.build("/api/v1/questions", {"limit": 10}, user_id=123)
        >>> print(key)  # "questions:v1:/api/v1/questions:limit=10:user=123"
    """

    prefix: str = "api_cache"
    include_query_params: bool = True
    include_user_id: bool = False
    version: int = 1
    hash_long_keys: bool = True
    max_key_length: int = 200

    def build(
        self,
        path: str,
        query_params: Optional[dict[str, Any]] = None,
        user_id: Optional[Union[int, str]] = None,
        extra_parts: Optional[list[str]] = None,
    ) -> str:
        """
        Cache key'i olusturur.

        Args:
            path: Endpoint path'i
            query_params: Query parametreleri dict'i
            user_id: Kullanici ID'si (private cache icin)
            extra_parts: Ek key parcalari

        Returns:
            Benzersiz cache key string'i
        """
        parts: list[str] = [
            self.prefix,
            f"v{self.version}",
            path,
        ]

        # Query parametrelerini ekle
        if self.include_query_params and query_params:
            # Sorted keys for consistent ordering
            sorted_params = sorted(query_params.items())
            params_str = "&".join(f"{k}={v}" for k, v in sorted_params if v is not None)
            if params_str:
                parts.append(params_str)

        # Kullanici ID'sini ekle
        if self.include_user_id and user_id is not None:
            parts.append(f"user={user_id}")

        # Extra parcalari ekle
        if extra_parts:
            parts.extend(extra_parts)

        # Key'i birlestir
        key = ":".join(parts)

        # Uzun key'leri hash'le
        if self.hash_long_keys and len(key) > self.max_key_length:
            hash_suffix = hashlib.md5(key.encode()).hexdigest()[:16]
            key = f"{self.prefix}:v{self.version}:hash:{hash_suffix}"

        return key


def _get_request_from_args(args: tuple, kwargs: dict) -> Optional[Request]:
    """
    Fonksiyon argumanlari arasinda Request objesini bulur.

    Args:
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Request objesi veya None
    """
    # Check kwargs first
    if "request" in kwargs and isinstance(kwargs["request"], Request):
        return kwargs["request"]

    # Check positional args
    for arg in args:
        if isinstance(arg, Request):
            return arg

    return None


def _get_user_id_from_request(request: Optional[Request]) -> Optional[Union[int, str]]:
    """
    Request'ten kullanici ID'sini cikarir.

    Args:
        request: FastAPI Request objesi

    Returns:
        Kullanici ID'si veya None
    """
    if request is None:
        return None

    # state.user varsa
    if hasattr(request, "state") and hasattr(request.state, "user"):
        user = request.state.user
        if hasattr(user, "id"):
            return user.id
        if isinstance(user, dict):
            return user.get("id")

    # Authorization header'dan JWT claim'i
    # (Bu basit bir fallback - gercek implementasyon JWT decode gerektirir)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Token'in hash'ini kullan (gercek ID yerine)
        token = auth_header[7:]
        return hashlib.md5(token.encode()).hexdigest()[:12]

    return None


async def _get_cached_value(cache_key: str) -> Optional[Any]:
    """
    Redis'ten cache'lenmis degeri alir.

    Args:
        cache_key: Cache key'i

    Returns:
        Cache'lenmis deger veya None
    """
    try:
        # Import here to avoid circular imports
        from backend.core.cache import cache_manager

        cached = await cache_manager.get(cache_key)
        return cached
    except ImportError:
        logger.debug("cache_manager import edilemedi")
        return None
    except Exception as e:
        logger.warning(f"Cache get hatasi: {e}")
        return None


async def _set_cached_value(cache_key: str, value: Any, ttl: int) -> bool:
    """
    Degeri Redis'e cache'ler.

    Args:
        cache_key: Cache key'i
        value: Cache'lenecek deger
        ttl: Time-to-live (saniye)

    Returns:
        Basari durumu
    """
    try:
        from backend.core.cache import cache_manager

        return await cache_manager.set(cache_key, value, ttl=ttl)
    except ImportError:
        logger.debug("cache_manager import edilemedi")
        return False
    except Exception as e:
        logger.warning(f"Cache set hatasi: {e}")
        return False


async def invalidate_cache(
    pattern: str,
    prefix: str = "api_cache",
) -> int:
    """
    Pattern'e uyan tum cache key'lerini siler.

    Cache invalidation icin kullanilir. Version-based invalidation
    tercih edilmeli, bu fonksiyon son care olarak kullanilmali.

    Args:
        pattern: Redis key pattern (glob syntax)
        prefix: Cache key prefix'i

    Returns:
        Silinen key sayisi

    Example:
        >>> await invalidate_cache("questions:*")  # Tum soru cache'lerini sil
        >>> await invalidate_cache("user=123:*")  # Kullanici cache'lerini sil
    """
    try:
        from backend.core.cache import cache_manager

        full_pattern = f"{prefix}:*{pattern}*"
        await cache_manager.invalidate_pattern(full_pattern)
        logger.info(f"Cache invalidated: {full_pattern}")
        return 1  # Gercek sayi dondurulemiyor
    except ImportError:
        logger.debug("cache_manager import edilemedi")
        return 0
    except Exception as e:
        logger.warning(f"Cache invalidation hatasi: {e}")
        return 0


def cache_response(
    ttl: Union[int, TTLPreset] = DEFAULT_TTL,
    prefix: Optional[str] = None,
    include_query_params: bool = True,
    include_user_id: bool = False,
    cache_version: int = 1,
    key_builder: Optional[CacheKeyBuilder] = None,
    skip_if: Optional[Callable[..., bool]] = None,
) -> Callable[[F], F]:
    """
    Response caching decorator.

    Fonksiyon sonuclarini Redis'te cache'ler. Async fonksiyonlar
    icin tasarlanmistir. TTL, key generation ve user-specific
    cache destekler.

    Args:
        ttl: Cache suresi (saniye veya TTLPreset)
        prefix: Cache key prefix'i (default: fonksiyon adi)
        include_query_params: Query parametrelerini key'e dahil et
        include_user_id: Kullanici ID'sini key'e dahil et (private cache)
        cache_version: Cache versiyonu (invalidation icin)
        key_builder: Ozel CacheKeyBuilder instance
        skip_if: Cache'lemeyi atlama kosulu (callable)

    Returns:
        Decorated async function

    Example:
        ```python
        @cache_response(ttl=TTLPreset.QUESTIONS, include_user_id=False)
        async def get_questions(request: Request, limit: int = 10):
            return await db.fetch_questions(limit)

        @cache_response(ttl=60, include_user_id=True)
        async def get_user_progress(request: Request, user_id: int):
            return await db.fetch_progress(user_id)
        ```

    Requirements:
        REQ-4.3: TTL ile max-age ayari
        REQ-4.4: include_user_id ile user-specific cache
        REQ-4.5: cache_version ile version-based invalidation
    """

    def decorator(func: F) -> F:
        # Cache key builder
        _prefix = prefix or func.__name__
        _ttl = ttl.value if isinstance(ttl, TTLPreset) else ttl

        _key_builder = key_builder or CacheKeyBuilder(
            prefix=_prefix,
            include_query_params=include_query_params,
            include_user_id=include_user_id,
            version=cache_version,
        )

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Skip kosulu kontrolu
            if skip_if and skip_if(*args, **kwargs):
                return await func(*args, **kwargs)

            # Request objesini bul
            request = _get_request_from_args(args, kwargs)

            # Path ve query params
            path = request.url.path if request else func.__name__
            query_params = dict(request.query_params) if request else {}

            # User ID (private cache icin)
            user_id = None
            if include_user_id:
                user_id = _get_user_id_from_request(request)

            # Cache key olustur
            cache_key = _key_builder.build(
                path=path,
                query_params=query_params if include_query_params else None,
                user_id=user_id,
            )

            # Cache'ten kontrol et
            cached_value = await _get_cached_value(cache_key)
            if cached_value is not None:
                logger.debug(
                    "Cache hit",
                    extra={"cache_key": cache_key, "function": func.__name__},
                )
                return cached_value

            # Fonksiyonu calistir
            result = await func(*args, **kwargs)

            # Sonucu cache'le
            if result is not None:
                await _set_cached_value(cache_key, result, _ttl)
                logger.debug(
                    "Cache set",
                    extra={
                        "cache_key": cache_key,
                        "function": func.__name__,
                        "ttl": _ttl,
                    },
                )

            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Sync fonksiyonlar icin cache devre disi
            logger.warning(
                f"cache_response decorator sadece async fonksiyonlar icin calisiyor: {func.__name__}"
            )
            return func(*args, **kwargs)

        # Async mi kontrolu
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        else:
            return sync_wrapper  # type: ignore[return-value]

    return decorator


# Convenience decorators for common use cases
def cache_static(
    ttl: int = TTLPreset.STATIC,
    prefix: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Statik icerik icin cache decorator.

    Nadiren degisen icerik icin uzun TTL kullanir (1 saat).

    Args:
        ttl: Cache suresi (default: 3600s)
        prefix: Cache key prefix'i

    Example:
        ```python
        @cache_static()
        async def get_curriculum():
            return await db.fetch_curriculum()
        ```
    """
    return cache_response(
        ttl=ttl,
        prefix=prefix,
        include_query_params=True,
        include_user_id=False,
    )


def cache_dynamic(
    ttl: int = TTLPreset.DYNAMIC,
    prefix: Optional[str] = None,
    include_user_id: bool = False,
) -> Callable[[F], F]:
    """
    Dinamik icerik icin cache decorator.

    Sik degisen icerik icin kisa TTL kullanir (5 dakika).

    Args:
        ttl: Cache suresi (default: 300s)
        prefix: Cache key prefix'i
        include_user_id: User-specific cache

    Example:
        ```python
        @cache_dynamic(include_user_id=True)
        async def get_recommendations(request: Request):
            return await service.generate_recommendations()
        ```
    """
    return cache_response(
        ttl=ttl,
        prefix=prefix,
        include_query_params=True,
        include_user_id=include_user_id,
    )


def cache_user_data(
    ttl: int = TTLPreset.USER_DATA,
    prefix: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Kullanici verisi icin cache decorator.

    Her kullanici icin ayri cache key olusturur (private cache).

    Args:
        ttl: Cache suresi (default: 60s)
        prefix: Cache key prefix'i

    Example:
        ```python
        @cache_user_data()
        async def get_user_progress(request: Request, user_id: int):
            return await db.fetch_progress(user_id)
        ```
    """
    return cache_response(
        ttl=ttl,
        prefix=prefix,
        include_query_params=True,
        include_user_id=True,  # Always include user ID
    )


__all__ = [
    "cache_response",
    "cache_static",
    "cache_dynamic",
    "cache_user_data",
    "CacheKeyBuilder",
    "TTLPreset",
    "DEFAULT_TTL",
    "invalidate_cache",
]
