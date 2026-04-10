"""
KIRO2 app/core/deps.py
CAT/FSRS/DAG/Placement/Estimator dependency koprusu.
"""

from __future__ import annotations

import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import (
    AuthenticatedUser,
    get_current_user,
)
from core.dependencies import (
    get_db as _get_db,
)

logger = logging.getLogger(__name__)

# Singleton fallback Redis client — pool exhaustion'ı önler
_fallback_redis = None


async def get_db() -> AsyncSession:
    async for session in _get_db():
        yield session


async def get_redis():
    """Ham aioredis.Redis client dondurur."""
    global _fallback_redis
    # Oncelik 1: cache_manager ic client (zaten baslangicta initialize ediliyor)
    try:
        from core.cache import cache_manager

        if not cache_manager.enabled:
            await cache_manager.initialize()
        if cache_manager.redis is not None:
            return cache_manager.redis
    except Exception as e:
        logger.warning(
            "cache_manager Redis başlatma hatası — fallback'e geçiliyor: %s", e
        )
    # Oncelik 2: Singleton fallback — her request'te yeni baglanti ACILMAZ
    try:
        import redis.asyncio as aioredis

        if _fallback_redis is None:
            _url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            _fallback_redis = aioredis.from_url(
                _url,
                decode_responses=False,
                max_connections=50,
            )
        return _fallback_redis
    except Exception as e:
        logger.error("Redis fallback başlatma HATASI — Redis kullanılamıyor: %s", e)
    return None


User = AuthenticatedUser
__all__ = ["AuthenticatedUser", "User", "get_current_user", "get_db", "get_redis"]
