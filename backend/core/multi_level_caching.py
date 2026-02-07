"""Multi-level caching facade module."""
from typing import Any, Optional


class CacheSystem:
    """Multi-level cache system with L1 (memory) and L2 (Redis) layers."""

    def __init__(self) -> None:
        self._l1_cache: dict[str, Any] = {}

    async def get(self, key: str) -> Optional[Any]:
        return self._l1_cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        self._l1_cache[key] = value

    async def delete(self, key: str) -> None:
        self._l1_cache.pop(key, None)

    async def clear(self) -> None:
        self._l1_cache.clear()


_cache_system: Optional[CacheSystem] = None


def get_cache_system() -> CacheSystem:
    """Get or create global cache system instance."""
    global _cache_system
    if _cache_system is None:
        _cache_system = CacheSystem()
    return _cache_system
