"""
Async Utility Functions - Asenkron Yardimci Fonksiyonlar

Bu modul, asenkron islemler icin yardimci fonksiyonlar ve context manager'lar saglar.
asyncio.gather, connection pooling ve async context manager'lar icin utility'ler icerir.

Requirements:
    - REQ-1.1: Async context manager for database sessions
    - REQ-1.5: asyncio.gather with return_exceptions=True

Author: KIRO2 Team
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")
R = TypeVar("R")


@dataclass
class AsyncResult:
    """
    Asenkron islem sonucu.

    Basarili veya basarisiz sonuclari tutmak icin kullanilir.
    asyncio.gather ile return_exceptions=True kullanildiginda
    sonuclari daha kolay islemek icin kullanilir.

    Attributes:
        value: Basarili sonuc degeri
        error: Hata durumunda exception
        elapsed_ms: Islem suresi (milisaniye)
        task_name: Gorev adi (debug icin)
    """

    value: Any = None
    error: Exception | None = None
    elapsed_ms: float = 0.0
    task_name: str = ""

    @property
    def success(self) -> bool:
        """Islem basarili mi?"""
        return self.error is None

    def unwrap(self) -> Any:
        """Degeri dondur veya hata firsat."""
        if self.error:
            raise self.error
        return self.value


@dataclass
class GatherResults:
    """
    asyncio.gather sonuclarini yonetir.

    Partial failure handling icin kullanilir.

    Attributes:
        results: Tum sonuclar (basarili ve basarisiz)
        successes: Basarili sonuclar
        failures: Basarisiz sonuclar
    """

    results: list[AsyncResult] = field(default_factory=list)

    @property
    def successes(self) -> list[AsyncResult]:
        """Basarili sonuclari dondur."""
        return [r for r in self.results if r.success]

    @property
    def failures(self) -> list[AsyncResult]:
        """Basarisiz sonuclari dondur."""
        return [r for r in self.results if not r.success]

    @property
    def all_succeeded(self) -> bool:
        """Tum islemler basarili mi?"""
        return len(self.failures) == 0

    @property
    def partial_success(self) -> bool:
        """En az bir basari var mi?"""
        return len(self.successes) > 0

    def values(self) -> list[Any]:
        """Basarili degerleri dondur."""
        return [r.value for r in self.successes]


async def gather_with_results(
    *coroutines: Coroutine[Any, Any, T],
    task_names: list[str] | None = None,
) -> GatherResults:
    """
    Birden fazla coroutine'i paralel calistirir ve sonuclari yonetir.

    asyncio.gather'in return_exceptions=True ile kullanimi yerine
    daha yapi dolu bir sonuc objesi dondurur.

    Args:
        *coroutines: Calistirilacak coroutine'ler
        task_names: Gorev adlari (debug icin)

    Returns:
        GatherResults objesi

    Example:
        >>> results = await gather_with_results(
        ...     fetch_user(1),
        ...     fetch_user(2),
        ...     fetch_user(3),
        ...     task_names=["user_1", "user_2", "user_3"]
        ... )
        >>> if results.partial_success:
        ...     for r in results.successes:
        ...         print(r.value)
    """
    if task_names is None:
        task_names = [f"task_{i}" for i in range(len(coroutines))]

    async def _wrap_coro(coro: Coroutine[Any, Any, T], name: str) -> AsyncResult:
        start = time.perf_counter()
        try:
            value = await coro
            elapsed = (time.perf_counter() - start) * 1000
            return AsyncResult(value=value, elapsed_ms=elapsed, task_name=name)
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning(f"Async task failed: {name} - {e}")
            return AsyncResult(error=e, elapsed_ms=elapsed, task_name=name)

    wrapped = [_wrap_coro(coro, name) for coro, name in zip(coroutines, task_names)]
    results = await asyncio.gather(*wrapped)

    return GatherResults(results=list(results))


async def gather_dict(
    tasks: dict[str, Coroutine[Any, Any, T]],
    return_exceptions: bool = True,
) -> dict[str, T | Exception]:
    """
    Dict olarak verilen coroutine'leri paralel calistirir.

    Args:
        tasks: {key: coroutine} formatinda gorevler
        return_exceptions: True ise hatalar exception yerine deger olarak doner

    Returns:
        {key: result} formatinda sonuclar

    Example:
        >>> results = await gather_dict({
        ...     "user": fetch_user(user_id),
        ...     "posts": fetch_posts(user_id),
        ...     "comments": fetch_comments(user_id),
        ... })
        >>> user = results["user"]
    """
    keys = list(tasks.keys())
    coros = list(tasks.values())

    results = await asyncio.gather(*coros, return_exceptions=return_exceptions)

    return dict(zip(keys, results))


async def run_with_timeout(
    coro: Coroutine[Any, Any, T],
    timeout: float,
    default: T | None = None,
) -> T | None:
    """
    Coroutine'i timeout ile calistirir.

    Args:
        coro: Calistirilacak coroutine
        timeout: Maksimum sure (saniye)
        default: Timeout durumunda dondurulecek deger

    Returns:
        Sonuc veya default deger

    Example:
        >>> result = await run_with_timeout(
        ...     slow_operation(),
        ...     timeout=5.0,
        ...     default=None
        ... )
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except TimeoutError:
        logger.warning(f"Operation timed out after {timeout}s")
        return default


async def retry_async(
    coro_func: Callable[P, Coroutine[Any, Any, T]],
    *args: P.args,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: P.kwargs,
) -> T:
    """
    Asenkron fonksiyonu retry mekanizmasi ile calistirir.

    Exponential backoff stratejisi kullanir.

    Args:
        coro_func: Calistirilacak async fonksiyon
        *args: Fonksiyon argumanlari
        max_retries: Maksimum deneme sayisi
        delay: Ilk bekleme suresi (saniye)
        backoff: Backoff carpani
        exceptions: Yakalanacak exception turleri
        **kwargs: Fonksiyon keyword argumanlari

    Returns:
        Fonksiyon sonucu

    Raises:
        Exception: Max retry asildiginda son hata

    Example:
        >>> result = await retry_async(
        ...     fetch_data,
        ...     url="https://api.example.com",
        ...     max_retries=3,
        ...     delay=1.0,
        ...     backoff=2.0
        ... )
    """
    last_error: Exception | None = None
    current_delay = delay

    for attempt in range(max_retries):
        try:
            return await coro_func(*args, **kwargs)
        except exceptions as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Retry attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Waiting {current_delay:.1f}s"
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(f"All {max_retries} attempts failed: {e}")

    if last_error:
        raise last_error
    raise RuntimeError("Unexpected retry failure")


def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
    """
    Async fonksiyonlar icin retry decorator.

    Args:
        max_retries: Maksimum deneme sayisi
        delay: Ilk bekleme suresi
        backoff: Backoff carpani
        exceptions: Yakalanacak exception turleri

    Returns:
        Decorated async function

    Example:
        >>> @async_retry(max_retries=3, delay=1.0)
        ... async def fetch_user(user_id: int):
        ...     return await api.get_user(user_id)
    """

    def decorator(
        func: Callable[P, Coroutine[Any, Any, T]]
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await retry_async(
                func,
                *args,
                max_retries=max_retries,
                delay=delay,
                backoff=backoff,
                exceptions=exceptions,
                **kwargs,
            )

        return wrapper

    return decorator


@asynccontextmanager
async def async_timer(name: str = "operation") -> AsyncGenerator[None, None]:
    """
    Async islem suresi olcumu icin context manager.

    Args:
        name: Islem adi (log icin)

    Yields:
        None

    Example:
        >>> async with async_timer("database_query"):
        ...     result = await db.execute(query)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"{name} completed in {elapsed:.2f}ms")


@asynccontextmanager
async def semaphore_context(
    semaphore: asyncio.Semaphore,
    timeout: float | None = None,
) -> AsyncGenerator[None, None]:
    """
    Semaphore ile rate limiting icin context manager.

    Args:
        semaphore: asyncio.Semaphore instance
        timeout: Maksimum bekleme suresi

    Yields:
        None

    Raises:
        asyncio.TimeoutError: Timeout asildiginda

    Example:
        >>> semaphore = asyncio.Semaphore(10)
        >>> async with semaphore_context(semaphore, timeout=5.0):
        ...     await process_item()
    """
    if timeout:
        await asyncio.wait_for(semaphore.acquire(), timeout=timeout)
    else:
        await semaphore.acquire()
    try:
        yield
    finally:
        semaphore.release()


class AsyncPool:
    """
    Async worker pool - concurrent islem sinirlandirmasi.

    Belirli sayida concurrent islem calistirmak icin kullanilir.

    Attributes:
        max_workers: Maksimum concurrent islem sayisi
        semaphore: Dahili semaphore

    Example:
        >>> pool = AsyncPool(max_workers=10)
        >>> async with pool:
        ...     tasks = [pool.submit(process_item, item) for item in items]
        ...     results = await asyncio.gather(*tasks)
    """

    def __init__(self, max_workers: int = 10):
        """
        AsyncPool baslatici.

        Args:
            max_workers: Maksimum concurrent islem sayisi
        """
        self.max_workers = max_workers
        self._semaphore: asyncio.Semaphore | None = None

    async def __aenter__(self) -> AsyncPool:
        """Context manager giris."""
        self._semaphore = asyncio.Semaphore(self.max_workers)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager cikis."""
        self._semaphore = None

    async def submit(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Coroutine'i pool'a gonder.

        Args:
            coro_func: Async fonksiyon
            *args: Fonksiyon argumanlari
            **kwargs: Fonksiyon keyword argumanlari

        Returns:
            Fonksiyon sonucu
        """
        if self._semaphore is None:
            raise RuntimeError("AsyncPool must be used as context manager")

        async with semaphore_context(self._semaphore):
            return await coro_func(*args, **kwargs)

    async def map(
        self,
        coro_func: Callable[[T], Coroutine[Any, Any, R]],
        items: list[T],
    ) -> list[R]:
        """
        Func'i tum itemlara uygula (paralel).

        Args:
            coro_func: Uygulanacak async fonksiyon
            items: Islenecek itemlar

        Returns:
            Sonuclar listesi

        Example:
            >>> async with AsyncPool(max_workers=5) as pool:
            ...     results = await pool.map(fetch_user, user_ids)
        """
        if self._semaphore is None:
            raise RuntimeError("AsyncPool must be used as context manager")

        tasks = [self.submit(coro_func, item) for item in items]
        return await asyncio.gather(*tasks)


async def batch_process(
    items: list[T],
    processor: Callable[[T], Coroutine[Any, Any, R]],
    batch_size: int = 10,
    delay_between_batches: float = 0.0,
) -> list[R]:
    """
    Itemlari batch'ler halinde isler.

    Buyuk veri setleri icin memory-efficient isleme saglar.

    Args:
        items: Islenecek itemlar
        processor: Her item icin calistirilacak async fonksiyon
        batch_size: Batch boyutu
        delay_between_batches: Batch'ler arasi bekleme (saniye)

    Returns:
        Tum sonuclar

    Example:
        >>> results = await batch_process(
        ...     items=user_ids,
        ...     processor=fetch_user,
        ...     batch_size=100,
        ...     delay_between_batches=0.1
        ... )
    """
    results: list[R] = []

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        batch_results = await asyncio.gather(*[processor(item) for item in batch])
        results.extend(batch_results)

        if delay_between_batches > 0 and i + batch_size < len(items):
            await asyncio.sleep(delay_between_batches)

    return results


def async_cached(
    ttl: float = 60.0,
    maxsize: int = 128,
) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
    """
    Async fonksiyonlar icin in-memory cache decorator.

    Simple TTL-based caching. Redis gerektirmez.

    Args:
        ttl: Cache suresi (saniye)
        maxsize: Maksimum cache boyutu

    Returns:
        Decorated async function

    Example:
        >>> @async_cached(ttl=60.0)
        ... async def get_user(user_id: int):
        ...     return await db.fetch_user(user_id)
    """
    cache: dict[str, tuple[Any, float]] = {}

    def decorator(
        func: Callable[P, Coroutine[Any, Any, T]]
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Cache key olustur
            key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"

            # Cache kontrolu
            if key in cache:
                value, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Cache hit: {func.__name__}")
                    return value
                del cache[key]

            # Fonksiyonu calistir
            result = await func(*args, **kwargs)

            # Cache'e ekle
            if len(cache) >= maxsize:
                # En eski entry'yi sil (simple LRU)
                oldest_key = min(cache, key=lambda k: cache[k][1])
                del cache[oldest_key]

            cache[key] = (result, time.time())
            return result

        return wrapper

    return decorator


__all__ = [
    "AsyncPool",
    "AsyncResult",
    "GatherResults",
    "async_cached",
    "async_retry",
    "async_timer",
    "batch_process",
    "gather_dict",
    "gather_with_results",
    "retry_async",
    "run_with_timeout",
    "semaphore_context",
]
