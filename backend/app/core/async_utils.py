"""
Async Utility Functions - API Response Time Optimization

Bu modül, async/await pattern'leri için yardımcı fonksiyonlar ve context manager'lar sağlar.
Database session yönetimi, connection pooling ve async işlemler için utilities içerir.

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-1.1
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, TypeVar, Callable, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@asynccontextmanager
async def async_timeout(seconds: float) -> AsyncGenerator[None, None]:
    """
    Async işlemler için timeout context manager.
    
    Args:
        seconds: Timeout süresi (saniye)
        
    Yields:
        None
        
    Raises:
        asyncio.TimeoutError: Timeout aşıldığında
        
    Example:
        async with async_timeout(5.0):
            await long_running_operation()
    """
    try:
        async with asyncio.timeout(seconds):
            yield
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out after {seconds} seconds")
        raise


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Async fonksiyonlar için retry decorator.
    
    Args:
        max_attempts: Maksimum deneme sayısı
        delay: İlk deneme arası bekleme süresi (saniye)
        backoff: Her denemede delay çarpanı (exponential backoff)
        exceptions: Yakalanacak exception türleri
        
    Returns:
        Decorated async function
        
    Example:
        @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
        async def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Optional[Exception] = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # Bu noktaya ulaşılmamalı ama type checker için
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


async def gather_with_concurrency(
    n: int,
    *tasks: Callable,
    return_exceptions: bool = True
) -> list:
    """
    Belirli sayıda concurrent task ile asyncio.gather çalıştırır.
    
    Args:
        n: Maksimum concurrent task sayısı
        *tasks: Çalıştırılacak async fonksiyonlar
        return_exceptions: Exception'ları liste içinde döndür (True) veya raise et (False)
        
    Returns:
        Task sonuçlarının listesi
        
    Example:
        results = await gather_with_concurrency(
            5,
            fetch_user(1),
            fetch_user(2),
            fetch_user(3),
            return_exceptions=True
        )
    """
    semaphore = asyncio.Semaphore(n)
    
    async def sem_task(task: Callable) -> Any:
        async with semaphore:
            return await task
    
    return await asyncio.gather(
        *[sem_task(task) for task in tasks],
        return_exceptions=return_exceptions
    )


class AsyncConnectionPool:
    """
    Generic async connection pool manager.
    
    Attributes:
        pool_size: Maksimum connection sayısı
        max_overflow: Pool dolu olduğunda ek connection sayısı
        timeout: Connection alma timeout'u (saniye)
    """
    
    def __init__(
        self,
        pool_size: int = 20,
        max_overflow: int = 10,
        timeout: float = 30.0
    ):
        """
        Connection pool initialize eder.
        
        Args:
            pool_size: Maksimum connection sayısı
            max_overflow: Pool dolu olduğunda ek connection sayısı
            timeout: Connection alma timeout'u (saniye)
        """
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(pool_size + max_overflow)
        self._active_connections = 0
        
        logger.info(
            f"AsyncConnectionPool initialized: pool_size={pool_size}, "
            f"max_overflow={max_overflow}, timeout={timeout}s"
        )
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[None, None]:
        """
        Connection pool'dan connection alır.
        
        Yields:
            None (connection context)
            
        Raises:
            asyncio.TimeoutError: Timeout aşıldığında
            
        Example:
            async with pool.acquire():
                # Connection kullan
                pass
        """
        try:
            async with asyncio.timeout(self.timeout):
                async with self._semaphore:
                    self._active_connections += 1
                    logger.debug(f"Connection acquired. Active: {self._active_connections}")
                    try:
                        yield
                    finally:
                        self._active_connections -= 1
                        logger.debug(f"Connection released. Active: {self._active_connections}")
        except asyncio.TimeoutError:
            logger.error(f"Failed to acquire connection within {self.timeout}s")
            raise
    
    @property
    def active_connections(self) -> int:
        """Aktif connection sayısını döndürür."""
        return self._active_connections
    
    @property
    def available_connections(self) -> int:
        """Kullanılabilir connection sayısını döndürür."""
        return (self.pool_size + self.max_overflow) - self._active_connections


async def run_in_threadpool(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """
    Blocking fonksiyonu thread pool'da async olarak çalıştırır.
    
    Args:
        func: Çalıştırılacak blocking fonksiyon
        *args: Fonksiyon argümanları
        **kwargs: Fonksiyon keyword argümanları
        
    Returns:
        Fonksiyon sonucu
        
    Example:
        result = await run_in_threadpool(blocking_function, arg1, arg2)
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


class AsyncBatchProcessor:
    """
    Async batch processing için utility class.
    
    Attributes:
        batch_size: Her batch'teki item sayısı
        max_concurrent: Maksimum concurrent batch sayısı
    """
    
    def __init__(self, batch_size: int = 10, max_concurrent: int = 5):
        """
        Batch processor initialize eder.
        
        Args:
            batch_size: Her batch'teki item sayısı
            max_concurrent: Maksimum concurrent batch sayısı
        """
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        logger.info(
            f"AsyncBatchProcessor initialized: batch_size={batch_size}, "
            f"max_concurrent={max_concurrent}"
        )
    
    async def process_items(
        self,
        items: list[T],
        processor: Callable[[list[T]], Any]
    ) -> list[Any]:
        """
        Item'ları batch'ler halinde işler.
        
        Args:
            items: İşlenecek item listesi
            processor: Batch işleyici async fonksiyon
            
        Returns:
            İşlenmiş sonuçların listesi
            
        Example:
            async def process_batch(batch):
                return await db.insert_many(batch)
            
            results = await processor.process_items(items, process_batch)
        """
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        logger.info(f"Processing {len(items)} items in {len(batches)} batches")
        
        results = await gather_with_concurrency(
            self.max_concurrent,
            *[processor(batch) for batch in batches],
            return_exceptions=True
        )
        
        # Flatten results
        flattened = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")
                continue
            if isinstance(result, list):
                flattened.extend(result)
            else:
                flattened.append(result)
        
        logger.info(f"Batch processing complete. Processed {len(flattened)} items")
        return flattened
