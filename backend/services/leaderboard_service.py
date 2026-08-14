import logging
import os
from datetime import UTC, datetime
from typing import Any

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LeaderboardService:
    """
    Redis-based real-time leaderboard service.
    Handles weekly leagues using Redis Sorted Sets (ZSET).
    """

    def __init__(self, redis_url: str | None = None):
        self._redis_url = redis_url or os.getenv(
            "REDIS_URL", "redis://localhost:6379/0"
        )
        self._redis: redis.Redis | None = None
        if REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(self._redis_url, decode_responses=True)
                logger.info("LeaderboardService connected to Redis")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis for Leaderboard: {e}")
                self._redis = None

    async def add_xp(
        self, user_id: str, xp_amount: int, league_name: str = "bronze"
    ) -> int:
        """
        Adds XP to the user in the specified weekly league.
        """
        if not self._redis:
            logger.warning("Redis is not available. Skipping XP add to leaderboard.")
            return 0

        current_year_week = datetime.now(UTC).strftime("%Y-%V")
        key = f"leaderboard:{league_name}:{current_year_week}"

        # ZINCRBY key increment member
        new_score = await self._redis.zincrby(key, xp_amount, user_id)
        return int(new_score)

    async def get_top_users(
        self, league_name: str = "bronze", top_n: int = 10
    ) -> list[dict[str, Any]]:
        """
        Gets the top N users from the specified weekly league.
        """
        if not self._redis:
            return []

        current_year_week = datetime.now(UTC).strftime("%Y-%V")
        key = f"leaderboard:{league_name}:{current_year_week}"

        # ZREVRANGE with scores
        # Returns [(user_id, score), ...]
        results = await self._redis.zrevrange(key, 0, top_n - 1, withscores=True)

        leaderboard = []
        for rank, (user_id, score) in enumerate(results, start=1):
            leaderboard.append({"rank": rank, "user_id": user_id, "score": int(score)})

        return leaderboard

    async def get_user_rank(
        self, user_id: str, league_name: str = "bronze"
    ) -> int | None:
        """
        Gets the current rank of a user in a league.
        """
        if not self._redis:
            return None

        current_year_week = datetime.now(UTC).strftime("%Y-%V")
        key = f"leaderboard:{league_name}:{current_year_week}"

        rank = await self._redis.zrevrank(key, user_id)
        if rank is not None:
            return int(rank) + 1  # 0-indexed in Redis
        return None


leaderboard_service = LeaderboardService()
