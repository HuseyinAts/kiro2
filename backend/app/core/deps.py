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
    # Oncelik 1: main.get_redis() — kendi fallback zincirine sahip
    try:
        import main as _main

        if hasattr(_main, "get_redis"):
            client = await _main.get_redis()
            if client is not None:
                return client
    except Exception:
        pass
    # Oncelik 2: cache_manager ic client
    try:
        from core.cache import cache_manager

        if not cache_manager.enabled:
            await cache_manager.initialize()
        if cache_manager.redis is not None:
            return cache_manager.redis
    except Exception:
        pass
    # Oncelik 3: Dogrudan baglanti
    try:
        import os

        import redis.asyncio as aioredis

        _url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = aioredis.from_url(_url, decode_responses=False)
        return client
    except Exception:
        pass
    return None


User = AuthenticatedUser
__all__ = ["AuthenticatedUser", "User", "get_current_user", "get_db", "get_redis"]
