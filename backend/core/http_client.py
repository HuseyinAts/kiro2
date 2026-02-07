"""
Async HTTP Client - External API Calls

aiohttp tabanli async HTTP client. Connection pooling, retry logic
ve timeout konfigurasyonu destekler.

Requirements:
    - REQ-1.3: aiohttp ClientSession with connection pooling (limit=100)
    - REQ-1.3: Retry logic with exponential backoff (max 3 retries)
    - REQ-1.3: Timeout configuration (default: 5s, configurable)

Author: KIRO2 Team
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator

import aiohttp
from aiohttp import ClientTimeout, TCPConnector

logger = logging.getLogger(__name__)


class HttpMethod(str, Enum):
    """HTTP metodlari."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class HttpClientConfig:
    """
    HTTP client konfigurasyonu.

    Attributes:
        base_url: Temel URL (opsiyonel)
        timeout: Varsayilan timeout (saniye)
        max_connections: Maksimum connection sayisi
        max_retries: Maksimum retry sayisi
        retry_delay: Ilk retry gecikmesi (saniye)
        retry_backoff: Retry backoff carpani
        headers: Varsayilan header'lar
    """

    base_url: str = ""
    timeout: float = 5.0
    max_connections: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    headers: dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True


@dataclass
class HttpResponse:
    """
    HTTP response wrapper.

    Attributes:
        status: HTTP status code
        headers: Response headers
        body: Response body (bytes)
        text: Response body (string)
        json_data: Parsed JSON (dict/list)
        elapsed_ms: Request suresi (milisaniye)
        url: Request URL
    """

    status: int
    headers: dict[str, str]
    body: bytes
    url: str
    elapsed_ms: float = 0.0

    @property
    def text(self) -> str:
        """Response body as text."""
        return self.body.decode("utf-8", errors="replace")

    @property
    def json_data(self) -> Any:
        """Response body as JSON."""
        import json

        return json.loads(self.body)

    @property
    def ok(self) -> bool:
        """Response basarili mi (2xx)?"""
        return 200 <= self.status < 300


class AsyncHttpClient:
    """
    Async HTTP client with connection pooling and retry logic.

    aiohttp tabanli, high-performance HTTP client.

    Attributes:
        config: Client konfigurasyonu
        session: aiohttp ClientSession

    Example:
        >>> async with AsyncHttpClient() as client:
        ...     response = await client.get("https://api.example.com/users")
        ...     users = response.json_data
    """

    def __init__(self, config: HttpClientConfig | None = None):
        """
        AsyncHttpClient baslatici.

        Args:
            config: Client konfigurasyonu (opsiyonel)
        """
        self.config = config or HttpClientConfig()
        self._session: aiohttp.ClientSession | None = None
        self._connector: TCPConnector | None = None

    async def __aenter__(self) -> "AsyncHttpClient":
        """Context manager giris - session olustur."""
        await self._create_session()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager cikis - session kapat."""
        await self.close()

    async def _create_session(self) -> None:
        """aiohttp session olustur."""
        if self._session is not None:
            return

        # Connection pooling icin TCPConnector
        self._connector = TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=min(self.config.max_connections, 30),
            ttl_dns_cache=300,  # DNS cache 5 dakika
            ssl=self.config.verify_ssl,
        )

        # Timeout konfigurasyonu
        timeout = ClientTimeout(
            total=self.config.timeout * 3,  # Total timeout
            connect=self.config.timeout,  # Connection timeout
            sock_read=self.config.timeout * 2,  # Read timeout
        )

        # Session olustur
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            headers=self.config.headers,
        )

        logger.info(
            f"HTTP client session created: max_connections={self.config.max_connections}, "
            f"timeout={self.config.timeout}s"
        )

    async def close(self) -> None:
        """Session ve connector'i kapat."""
        if self._session:
            await self._session.close()
            self._session = None
        if self._connector:
            await self._connector.close()
            self._connector = None
        logger.debug("HTTP client session closed")

    def _build_url(self, url: str) -> str:
        """URL olustur (base_url varsa birlesitir)."""
        if url.startswith(("http://", "https://")):
            return url
        return f"{self.config.base_url.rstrip('/')}/{url.lstrip('/')}"

    async def _request_with_retry(
        self,
        method: HttpMethod,
        url: str,
        **kwargs: Any,
    ) -> HttpResponse:
        """
        HTTP istegi retry mekanizmasi ile gonder.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: aiohttp request argumanlari

        Returns:
            HttpResponse

        Raises:
            aiohttp.ClientError: Tum retry'lar basarisiz olursa
        """
        if self._session is None:
            await self._create_session()

        assert self._session is not None

        full_url = self._build_url(url)
        last_error: Exception | None = None
        delay = self.config.retry_delay

        for attempt in range(self.config.max_retries):
            start_time = time.perf_counter()

            try:
                async with self._session.request(
                    method.value, full_url, **kwargs
                ) as response:
                    body = await response.read()
                    elapsed_ms = (time.perf_counter() - start_time) * 1000

                    # Log request
                    logger.debug(
                        f"HTTP {method.value} {full_url} -> {response.status} "
                        f"({elapsed_ms:.2f}ms)"
                    )

                    return HttpResponse(
                        status=response.status,
                        headers=dict(response.headers),
                        body=body,
                        url=str(response.url),
                        elapsed_ms=elapsed_ms,
                    )

            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
            ) as e:
                last_error = e
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                logger.warning(
                    f"HTTP {method.value} {full_url} failed (attempt {attempt + 1}/"
                    f"{self.config.max_retries}): {e} ({elapsed_ms:.2f}ms)"
                )

                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= self.config.retry_backoff

        # Tum retry'lar basarisiz
        logger.error(
            f"HTTP {method.value} {full_url} failed after "
            f"{self.config.max_retries} attempts"
        )

        if last_error:
            raise last_error
        raise aiohttp.ClientError(f"Request failed: {full_url}")

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        """
        HTTP GET istegi.

        Args:
            url: Request URL
            params: Query parametreleri
            headers: Ek header'lar
            timeout: Custom timeout (saniye)

        Returns:
            HttpResponse
        """
        kwargs: dict[str, Any] = {}
        if params:
            kwargs["params"] = params
        if headers:
            kwargs["headers"] = headers
        if timeout:
            kwargs["timeout"] = ClientTimeout(total=timeout)

        return await self._request_with_retry(HttpMethod.GET, url, **kwargs)

    async def post(
        self,
        url: str,
        json: dict[str, Any] | list[Any] | None = None,
        data: dict[str, Any] | bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        """
        HTTP POST istegi.

        Args:
            url: Request URL
            json: JSON body (dict/list)
            data: Form data veya raw bytes
            headers: Ek header'lar
            timeout: Custom timeout

        Returns:
            HttpResponse
        """
        kwargs: dict[str, Any] = {}
        if json is not None:
            kwargs["json"] = json
        if data is not None:
            kwargs["data"] = data
        if headers:
            kwargs["headers"] = headers
        if timeout:
            kwargs["timeout"] = ClientTimeout(total=timeout)

        return await self._request_with_retry(HttpMethod.POST, url, **kwargs)

    async def put(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        """
        HTTP PUT istegi.

        Args:
            url: Request URL
            json: JSON body
            data: Form data veya raw bytes
            headers: Ek header'lar
            timeout: Custom timeout

        Returns:
            HttpResponse
        """
        kwargs: dict[str, Any] = {}
        if json is not None:
            kwargs["json"] = json
        if data is not None:
            kwargs["data"] = data
        if headers:
            kwargs["headers"] = headers
        if timeout:
            kwargs["timeout"] = ClientTimeout(total=timeout)

        return await self._request_with_retry(HttpMethod.PUT, url, **kwargs)

    async def patch(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        """
        HTTP PATCH istegi.

        Args:
            url: Request URL
            json: JSON body
            headers: Ek header'lar
            timeout: Custom timeout

        Returns:
            HttpResponse
        """
        kwargs: dict[str, Any] = {}
        if json is not None:
            kwargs["json"] = json
        if headers:
            kwargs["headers"] = headers
        if timeout:
            kwargs["timeout"] = ClientTimeout(total=timeout)

        return await self._request_with_retry(HttpMethod.PATCH, url, **kwargs)

    async def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        """
        HTTP DELETE istegi.

        Args:
            url: Request URL
            headers: Ek header'lar
            timeout: Custom timeout

        Returns:
            HttpResponse
        """
        kwargs: dict[str, Any] = {}
        if headers:
            kwargs["headers"] = headers
        if timeout:
            kwargs["timeout"] = ClientTimeout(total=timeout)

        return await self._request_with_retry(HttpMethod.DELETE, url, **kwargs)

    async def head(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        """
        HTTP HEAD istegi (sadece header'lari al).

        Args:
            url: Request URL
            headers: Ek header'lar
            timeout: Custom timeout

        Returns:
            HttpResponse
        """
        kwargs: dict[str, Any] = {}
        if headers:
            kwargs["headers"] = headers
        if timeout:
            kwargs["timeout"] = ClientTimeout(total=timeout)

        return await self._request_with_retry(HttpMethod.HEAD, url, **kwargs)


# Global client instance (lazy initialization)
_global_client: AsyncHttpClient | None = None


async def get_http_client() -> AsyncHttpClient:
    """
    Global HTTP client instance dondur.

    Lazy initialization ile singleton pattern.

    Returns:
        AsyncHttpClient instance
    """
    global _global_client

    if _global_client is None:
        _global_client = AsyncHttpClient()
        await _global_client._create_session()

    return _global_client


async def close_http_client() -> None:
    """Global HTTP client'i kapat."""
    global _global_client

    if _global_client is not None:
        await _global_client.close()
        _global_client = None


@asynccontextmanager
async def http_client(
    config: HttpClientConfig | None = None,
) -> AsyncGenerator[AsyncHttpClient, None]:
    """
    HTTP client context manager.

    Args:
        config: Client konfigurasyonu

    Yields:
        AsyncHttpClient instance

    Example:
        >>> async with http_client() as client:
        ...     response = await client.get("https://api.example.com/data")
    """
    client = AsyncHttpClient(config)
    try:
        await client._create_session()
        yield client
    finally:
        await client.close()


__all__ = [
    "AsyncHttpClient",
    "HttpClientConfig",
    "HttpMethod",
    "HttpResponse",
    "close_http_client",
    "get_http_client",
    "http_client",
]
