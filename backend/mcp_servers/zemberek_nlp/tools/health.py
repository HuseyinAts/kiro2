"""
Health Check Tool (REQ-8.6)
Zemberek server saglik kontrolu

Supports both JPype (direct Zemberek access) and HTTP backend.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

from .base import BaseToolHandler

logger = logging.getLogger(__name__)

# Server start time for uptime calculation
_start_time = datetime.now()


class HealthHandler(BaseToolHandler):
    """Health check tool handler"""

    tool_name = "health"

    async def _call_jpype(self, **kwargs) -> Dict[str, Any]:
        """
        Check health using JPype bridge.

        Returns:
            HealthResult as dictionary
        """
        if not self.bridge:
            raise RuntimeError("JPype bridge not initialized")

        # Get bridge health
        bridge_health = self.bridge.get_health()

        # Check Redis
        redis_available = await self._check_redis()

        # Get cache hit rate
        cache_hit_rate = await self._get_cache_hit_rate()

        # Calculate uptime
        uptime_seconds = (datetime.now() - _start_time).total_seconds()

        # Determine overall status
        jpype_initialized = bridge_health.get("initialized", False)
        jvm_started = bridge_health.get("jvm_started", False)

        if jpype_initialized and jvm_started:
            status = "healthy"
        elif jvm_started:
            status = "degraded"
        else:
            status = "unhealthy"

        # Build error message if any
        error_message = None
        if not jvm_started:
            error_message = "JVM not started"
        elif not jpype_initialized:
            error_message = "JPype bridge not fully initialized"

        return {
            "status": status,
            "backend_mode": "jpype",
            "jpype_initialized": jpype_initialized,
            "jvm_started": jvm_started,
            "zemberek_available": jpype_initialized,
            "redis_available": redis_available,
            "components": bridge_health.get("components", {}),
            "version": "1.0.0",
            "uptime_seconds": round(uptime_seconds, 2),
            "cache_hit_rate": cache_hit_rate,
            "error_message": error_message,
        }

    async def _call_backend(self, **kwargs) -> Dict[str, Any]:
        """
        Check health of all Zemberek components

        Returns:
            HealthResult as dictionary
        """
        # Check HTTP backend
        http_available = await self._check_http_backend()

        # Check Zemberek availability (via HTTP backend)
        zemberek_available = False
        if http_available:
            zemberek_available = await self._check_zemberek()

        # Check Redis
        redis_available = await self._check_redis()

        # Get cache hit rate
        cache_hit_rate = await self._get_cache_hit_rate()

        # Calculate uptime
        uptime_seconds = (datetime.now() - _start_time).total_seconds()

        # Determine overall status
        if http_available and zemberek_available:
            status = "healthy"
        elif http_available:
            status = "degraded"
        else:
            status = "unhealthy"

        # Build error message if any
        error_message = None
        if not http_available:
            error_message = "HTTP backend unavailable"
        elif not zemberek_available:
            error_message = "Zemberek library not available in backend"

        return {
            "status": status,
            "zemberek_available": zemberek_available,
            "redis_available": redis_available,
            "http_backend_available": http_available,
            "version": "1.0.0",
            "uptime_seconds": round(uptime_seconds, 2),
            "cache_hit_rate": cache_hit_rate,
            "error_message": error_message,
        }

    async def _check_http_backend(self) -> bool:
        """Check if HTTP backend is reachable"""
        try:
            response = await self._get("/health")
            return response.get("status") in ("healthy", "degraded")
        except Exception as e:
            logger.warning(f"[Health] HTTP backend check failed: {e}")
            return False

    async def _check_zemberek(self) -> bool:
        """Check if Zemberek is available via HTTP backend"""
        try:
            response = await self._get("/health")
            return response.get("zemberek_available", False)
        except Exception:
            return False

    async def _check_redis(self) -> bool:
        """Check if Redis is connected"""
        if self.cache and self.cache.is_connected:
            return True
        return False

    async def _get_cache_hit_rate(self) -> Optional[float]:
        """Get cache hit rate from stats"""
        if self.cache and self.cache.is_connected:
            return round(self.cache.stats.hit_rate, 4)
        return None

    def _get_cache_input(self, **kwargs) -> Optional[str]:
        """Health check results should not be cached"""
        return None
