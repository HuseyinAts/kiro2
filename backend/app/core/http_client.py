"""
Async HTTP Client - External API Calls

aiohttp ile optimize edilmiş external API çağrıları için HTTP client.
Connection pooling, retry logic, timeout yönetimi içerir.

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-1.3
"""

import asyncio
import logging
from typing import Any, Optional, Dict
from contextlib import asynccontextmanager

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector

logger = logging.getLogger(__name__)


class AsyncHTTPClient:
    """
    Async HTTP client with connection pooling and retry logic.
    
    Features:
    - Connection pooling (limit=100 concurrent connections)
    - Automatic retry with exponential backoff (max 3 retries)
    - Configurable timeouts (default: 5s)
    - Request/response logging
    
    Requirements: REQ-1.3
    """
    
    def __init__(
        self,
        timeout: float = 5.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        connection_limit: int = 100
    ):
        """
        HTTP client initialize eder.
        
        Args:
            timeout: Request timeout (saniye)
            max_retries: Maksimum retry sayısı
            retry_delay: İlk retry arası bekleme (saniye)
            retry_backoff: Her retry'da delay çarpanı
            connection_limit: Maksimum concurrent connection sayısı
        """
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        
        # Connection pooling configuration
        self.connector = TCPConnector(
            limit=connection_limit,  # Max concurrent connections
            limit_per_host=30,  # Max connections per host
            ttl_dns_cache=300,  # DNS cache TTL (5 minutes)
            enable_cleanup_closed=True  # Clean up closed connections
        )
        
        self._session: Optional[ClientSession] = None
        
        logger.info(
            f"AsyncHTTPClient initialized: timeout={timeout}s, "
            f"max_retries={max_retries}, connection_limit={connection_limit}"
        )
    
    async def _ensure_session(self) -> ClientSession:
        """Session yoksa oluşturur."""
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                connector=self.connector,
                timeout=self.timeout
            )
            logger.debug("New aiohttp ClientSession created")
        return self._session
    
    async def close(self) -> None:
        """HTTP client'ı kapatır ve kaynakları temizler."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("AsyncHTTPClient closed")
    
    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> aiohttp.ClientResponse:
        """
        HTTP request yapar (retry logic ile).
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: aiohttp request parametreleri
            
        Returns:
            aiohttp.ClientResponse
            
        Raises:
            aiohttp.ClientError: Request başarısız olursa
        """
        session = await self._ensure_session()
        current_delay = self.retry_delay
        last_exception: Optional[Exception] = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"HTTP {method} {url} (attempt {attempt}/{self.max_retries})")
                
                async with session.request(method, url, **kwargs) as response:
                    # Log response
                    logger.debug(
                        f"HTTP {method} {url} -> {response.status} "
                        f"({response.content_length or 0} bytes)"
                    )
                    
                    # Raise for 4xx/5xx status codes
                    response.raise_for_status()
                    
                    return response
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(
                        f"HTTP {method} {url} failed after {self.max_retries} attempts: {e}"
                    )
                    raise
                
                # Retry only on specific errors
                if isinstance(e, aiohttp.ClientResponseError) and 400 <= e.status < 500:
                    # Don't retry client errors (4xx)
                    logger.error(f"HTTP {method} {url} -> {e.status} (client error, no retry)")
                    raise
                
                logger.warning(
                    f"HTTP {method} {url} failed (attempt {attempt}/{self.max_retries}): {e}. "
                    f"Retrying in {current_delay}s..."
                )
                
                await asyncio.sleep(current_delay)
                current_delay *= self.retry_backoff
        
        # Bu noktaya ulaşılmamalı
        if last_exception:
            raise last_exception
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        HTTP GET request yapar.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            **kwargs: Ek aiohttp parametreleri
            
        Returns:
            JSON response dict
            
        Example:
            data = await client.get("https://api.example.com/users", params={"page": 1})
        """
        response = await self._make_request(
            "GET",
            url,
            params=params,
            headers=headers,
            **kwargs
        )
        return await response.json()
    
    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        HTTP POST request yapar.
        
        Args:
            url: Request URL
            json: JSON request body
            data: Form data
            headers: Request headers
            **kwargs: Ek aiohttp parametreleri
            
        Returns:
            JSON response dict
            
        Example:
            result = await client.post(
                "https://api.example.com/users",
                json={"name": "John", "email": "john@example.com"}
            )
        """
        response = await self._make_request(
            "POST",
            url,
            json=json,
            data=data,
            headers=headers,
            **kwargs
        )
        return await response.json()
    
    async def put(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """HTTP PUT request yapar."""
        response = await self._make_request(
            "PUT",
            url,
            json=json,
            headers=headers,
            **kwargs
        )
        return await response.json()
    
    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """HTTP DELETE request yapar."""
        response = await self._make_request(
            "DELETE",
            url,
            headers=headers,
            **kwargs
        )
        return await response.json()
    
    @asynccontextmanager
    async def stream_get(self, url: str, **kwargs: Any):
        """
        Streaming GET request için context manager.
        
        Args:
            url: Request URL
            **kwargs: aiohttp parametreleri
            
        Yields:
            aiohttp.ClientResponse (streaming)
            
        Example:
            async with client.stream_get("https://example.com/large-file") as response:
                async for chunk in response.content.iter_chunked(8192):
                    process(chunk)
        """
        session = await self._ensure_session()
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            yield response


# Global HTTP client instance
_http_client: Optional[AsyncHTTPClient] = None


def get_http_client() -> AsyncHTTPClient:
    """
    Global HTTP client instance döndürür.
    
    Returns:
        AsyncHTTPClient instance
        
    Example:
        client = get_http_client()
        data = await client.get("https://api.example.com/data")
    """
    global _http_client
    if _http_client is None:
        _http_client = AsyncHTTPClient()
    return _http_client


async def close_http_client() -> None:
    """Global HTTP client'ı kapatır."""
    global _http_client
    if _http_client is not None:
        await _http_client.close()
        _http_client = None
