"""
Base Tool Handler
Abstract base class with caching logic for all NLP tools

Supports both JPype (direct Java bridge) and HTTP backend modes.
JPype is tried first if available, with automatic HTTP fallback.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

import httpx

from ..config import get_config, ZemberekConfig
from ..cache.redis_cache import ZemberekCache

if TYPE_CHECKING:
    from ..bridge import ZemberekJPypeBridge

logger = logging.getLogger(__name__)


class BaseToolHandler(ABC):
    """
    Base class for all Zemberek NLP tool handlers.

    Supports dual-mode operation:
    - JPype: Direct Java library access (primary, faster)
    - HTTP: External Zemberek service (fallback)
    """

    # Tool name - override in subclass
    tool_name: str = "base"

    def __init__(
        self,
        http_client: Optional[httpx.AsyncClient] = None,
        cache: Optional[ZemberekCache] = None,
        config: Optional[ZemberekConfig] = None,
        bridge: Optional["ZemberekJPypeBridge"] = None,
    ):
        """
        Initialize tool handler.

        Args:
            http_client: Async HTTP client for backend calls (optional if using JPype only)
            cache: Optional Redis cache instance
            config: Optional configuration (uses global if None)
            bridge: Optional JPype bridge instance
        """
        self.client = http_client
        self.cache = cache
        self.config = config or get_config()
        self.bridge = bridge

        # Determine if JPype should be used
        self._use_jpype = (
            self.config.use_jpype
            and bridge is not None
            and bridge.is_initialized
        )

    def set_bridge(self, bridge: "ZemberekJPypeBridge") -> None:
        """
        Set JPype bridge instance.

        Args:
            bridge: Initialized JPype bridge
        """
        self.bridge = bridge
        self._use_jpype = (
            self.config.use_jpype
            and bridge is not None
            and bridge.is_initialized
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute tool with caching.

        Tries JPype first if available, falls back to HTTP on failure.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            Tool result dictionary
        """
        start_time = time.perf_counter()

        # Generate cache key input
        cache_input = self._get_cache_input(**kwargs)

        # Check cache
        if self.cache and self.cache.is_connected and cache_input:
            cached_result = await self.cache.get_cached(self.tool_name, cache_input)
            if cached_result:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                cached_result["cached"] = True
                cached_result["latency_ms"] = round(elapsed_ms, 2)
                logger.debug(
                    f"[{self.tool_name}] Cache hit, latency: {elapsed_ms:.2f}ms"
                )
                return cached_result

        # Try JPype first, then HTTP fallback
        result = await self._execute_with_fallback(**kwargs)

        # Calculate latency
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        result["cached"] = False
        result["latency_ms"] = round(elapsed_ms, 2)

        # Cache result
        if self.cache and self.cache.is_connected and cache_input:
            await self.cache.set_cached(self.tool_name, cache_input, result)

        logger.debug(f"[{self.tool_name}] Call completed, latency: {elapsed_ms:.2f}ms")

        return result

    async def _execute_with_fallback(self, **kwargs) -> Dict[str, Any]:
        """
        Execute with JPype->HTTP fallback pattern.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            Tool result dictionary
        """
        # Try JPype if available
        if self._use_jpype:
            try:
                result = await self._call_jpype(**kwargs)
                result["backend"] = "jpype"
                return result
            except Exception as e:
                logger.warning(
                    f"[{self.tool_name}] JPype call failed, falling back to HTTP: {e}"
                )

        # Fall back to HTTP
        try:
            result = await self._call_backend(**kwargs)
            result["backend"] = "http"
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"[{self.tool_name}] HTTP error: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"[{self.tool_name}] Request error: {e}")
            raise

    async def _call_jpype(self, **kwargs) -> Dict[str, Any]:
        """
        Call Zemberek via JPype bridge.

        Override in subclass to implement tool-specific JPype logic.
        Default implementation raises NotImplementedError.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            Tool result dictionary (without cached/latency_ms/backend fields)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement _call_jpype()"
        )

    @abstractmethod
    async def _call_backend(self, **kwargs) -> Dict[str, Any]:
        """
        Call HTTP backend to perform operation.

        Override in subclass to implement tool-specific logic.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            Tool result dictionary (without cached/latency_ms/backend fields)
        """
        pass

    def _get_cache_input(self, **kwargs) -> Optional[str]:
        """
        Get cache input string from arguments

        Override in subclass if needed.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            Cache input string or None if caching not applicable
        """
        # Default: use 'text' argument if present
        return kwargs.get("text")

    async def _post(
        self, endpoint: str, json_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make POST request to HTTP backend

        Args:
            endpoint: API endpoint (e.g., "/analyze")
            json_data: Request body

        Returns:
            Response JSON
        """
        url = f"{self.config.zemberek_url}{endpoint}"
        response = await self.client.post(
            url, json=json_data, timeout=self.config.http_timeout
        )
        response.raise_for_status()
        return response.json()

    async def _get(self, endpoint: str) -> Dict[str, Any]:
        """
        Make GET request to HTTP backend

        Args:
            endpoint: API endpoint (e.g., "/health")

        Returns:
            Response JSON
        """
        url = f"{self.config.zemberek_url}{endpoint}"
        response = await self.client.get(url, timeout=self.config.http_timeout)
        response.raise_for_status()
        return response.json()
