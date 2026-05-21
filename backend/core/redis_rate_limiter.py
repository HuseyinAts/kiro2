"""Redis-backed unified rate limiter (Quality Hardening Task 7 / S179).

Replaces the legacy in-process ``_rate_buckets: defaultdict(...)`` in
``backend/api/auth.py:75-89`` and the parallel implementation in
``core/auth_rate_limiting.py``. Pre-fix consequences:

- Multi-worker (uvicorn ``--workers N``) effectively multiplied the
  limit Nx because each worker had its own bucket.
- Restart wiped the bucket immediately.
- No way to share quota between API + Celery worker.

The Redis ZSET sliding-window algorithm gives:

- Distributed quota (any worker enforces the same bucket).
- Restart-safe (Redis persists).
- Cheap: each `check` is one ZRANGEBYSCORE + one ZADD + one EXPIRE.

If Redis is unreachable we **fail open by default** (log + allow). This
is the right call for KIRO2: false 429s during a Redis outage are worse
than 60s of un-limited login traffic. Override with
``RATE_LIMIT_FAIL_CLOSED=true`` for high-security deploys.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitDecision:
    """Result of a rate-limit check.

    Returned instead of raising — middleware/handler converts to a
    JSONResponse / HTTPException at the right architectural layer
    (see ``.claude/rules/middleware.md``).
    """

    allowed: bool
    remaining: int
    retry_after_sec: int
    bucket: str


class RedisRateLimiter:
    """Sliding-window rate limiter, Redis-backed.

    Usage:
        limiter = await get_rate_limiter()
        decision = await limiter.check(bucket="login", identifier=ip, limit=30, window=60)
        if not decision.allowed:
            return JSONResponse(429, ...)
    """

    def __init__(self, redis_client) -> None:
        self.redis = redis_client
        self.fail_closed = os.environ.get("RATE_LIMIT_FAIL_CLOSED", "").lower() in (
            "1",
            "true",
            "yes",
        )

    async def check(
        self,
        *,
        bucket: str,
        identifier: str,
        limit: int,
        window: int,
    ) -> RateLimitDecision:
        """Check if `identifier` is allowed in `bucket` (limit/window).

        Args:
            bucket: scope name (e.g. ``"login"``, ``"award_xp"``).
            identifier: per-bucket key (usually client IP or user id).
            limit: max events allowed in ``window`` seconds.
            window: window length in seconds.
        """
        key = f"ratelimit:{bucket}:{identifier}"
        now = time.time()
        threshold = now - window
        try:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, threshold)
            pipe.zcard(key)
            pipe.zadd(key, {f"{now}:{os.urandom(4).hex()}": now})
            pipe.expire(key, window + 5)
            _, count_before_add, _, _ = await pipe.execute()
            count = int(count_before_add) + 1  # incl. the one we just added
            if count > limit:
                # Roll back the add so we don't penalize next call's window.
                await self.redis.zremrangebyscore(key, now, now)
                return RateLimitDecision(
                    allowed=False,
                    remaining=0,
                    retry_after_sec=window,
                    bucket=bucket,
                )
            return RateLimitDecision(
                allowed=True,
                remaining=max(0, limit - count),
                retry_after_sec=0,
                bucket=bucket,
            )
        except Exception:
            logger.warning(
                "RateLimit Redis check failed bucket=%s — fail %s",
                bucket,
                "closed" if self.fail_closed else "open",
                exc_info=True,
            )
            if self.fail_closed:
                return RateLimitDecision(
                    allowed=False,
                    remaining=0,
                    retry_after_sec=window,
                    bucket=bucket,
                )
            return RateLimitDecision(
                allowed=True,
                remaining=limit,
                retry_after_sec=0,
                bucket=bucket,
            )


_INSTANCE: RedisRateLimiter | None = None


async def get_rate_limiter() -> RedisRateLimiter | None:
    """Return a shared RedisRateLimiter, or None if Redis unavailable."""
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE
    try:
        import redis.asyncio as aioredis

        url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        client = aioredis.from_url(
            url,
            decode_responses=False,
            max_connections=20,
            health_check_interval=30,
        )
        await client.ping()
        _INSTANCE = RedisRateLimiter(client)
        return _INSTANCE
    except Exception:
        logger.warning(
            "Redis rate limiter unavailable — caller fallback", exc_info=True
        )
        return None
