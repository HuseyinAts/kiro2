"""
KIRO2 app/core/deps.py
CAT/FSRS/DAG/Placement/Estimator dependency koprusu.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import (
    AuthenticatedUser,
    get_current_user,
)
from core.dependencies import (
    get_db as _get_db,
)


async def get_db() -> AsyncSession:
    async for session in _get_db():
        yield session


async def get_redis():
    """Ham aioredis.Redis client dondurur."""
    # Oncelik 1: cache_manager ic client (zaten baslangicta initialize ediliyor)
    try:
        from core.cache import cache_manager

        if not cache_manager.enabled:
            await cache_manager.initialize()
        if cache_manager.redis is not None:
            return cache_manager.redis
    except Exception:
        pass
    # Oncelik 2: Dogrudan baglanti
    try:
        import os

        import redis.asyncio as aioredis

        _url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return aioredis.from_url(_url, decode_responses=False)
    except Exception:
        pass
    return None


User = AuthenticatedUser
__all__ = ["AuthenticatedUser", "User", "get_current_user", "get_db", "get_redis"]
