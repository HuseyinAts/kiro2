"""
Redis Monitoring & Health Check
RELIABILITY FIX: Monitor Redis persistence and data integrity
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime

import redis.asyncio as aioredis

from .structured_logger import get_logger

logger = get_logger("redis_monitoring")


@dataclass
class RedisPersistenceStatus:
    """Redis persistence status"""

    aof_enabled: bool
    aof_last_write_status: str
    aof_current_size: int
    aof_base_size: int
    rdb_last_save_time: datetime
    rdb_last_save_status: str
    rdb_changes_since_last_save: int
    loading: bool
    total_keys: int


@dataclass
class RedisHealthStatus:
    """Redis health check result"""

    is_healthy: bool
    persistence_ok: bool
    memory_ok: bool
    replication_ok: bool
    issues: list
    metrics: dict


class RedisMonitor:
    """
    Redis monitoring and health checking

    Features:
    - Persistence status monitoring
    - Data integrity checks
    - Memory usage tracking
    - Backup verification
    - Automatic alerts
    """

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client: aioredis.Redis | None = None

    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def get_persistence_status(self) -> RedisPersistenceStatus:
        """
        Get Redis persistence status

        Returns:
            RedisPersistenceStatus with AOF and RDB info
        """
        await self.connect()

        info = await self.redis_client.info("persistence")

        # AOF status
        aof_enabled = info.get("aof_enabled", 0) == 1
        aof_last_write_status = info.get("aof_last_write_status", "unknown")
        aof_current_size = info.get("aof_current_size", 0)
        aof_base_size = info.get("aof_base_size", 0)

        # RDB status
        rdb_last_save_time = datetime.fromtimestamp(info.get("rdb_last_save_time", 0))
        rdb_last_save_status = info.get("rdb_last_bgsave_status", "unknown")
        rdb_changes = info.get("rdb_changes_since_last_save", 0)

        # Loading status
        loading = info.get("loading", 0) == 1

        # Total keys
        dbsize = await self.redis_client.dbsize()

        return RedisPersistenceStatus(
            aof_enabled=aof_enabled,
            aof_last_write_status=aof_last_write_status,
            aof_current_size=aof_current_size,
            aof_base_size=aof_base_size,
            rdb_last_save_time=rdb_last_save_time,
            rdb_last_save_status=rdb_last_save_status,
            rdb_changes_since_last_save=rdb_changes,
            loading=loading,
            total_keys=dbsize,
        )

    async def check_health(self) -> RedisHealthStatus:
        """
        Comprehensive Redis health check

        Returns:
            RedisHealthStatus with detailed health info
        """
        await self.connect()

        is_healthy = True
        issues = []
        metrics = {}

        try:
            # 1. Ping check
            ping_result = await self.redis_client.ping()
            if not ping_result:
                is_healthy = False
                issues.append("Redis PING failed")

            # 2. Persistence check
            persistence = await self.get_persistence_status()
            metrics["persistence"] = {
                "aof_enabled": persistence.aof_enabled,
                "aof_status": persistence.aof_last_write_status,
                "rdb_status": persistence.rdb_last_save_status,
                "total_keys": persistence.total_keys,
            }

            persistence_ok = True
            if not persistence.aof_enabled:
                issues.append("AOF persistence is disabled")
                persistence_ok = False

            if persistence.aof_last_write_status != "ok":
                issues.append(f"AOF write status: {persistence.aof_last_write_status}")
                persistence_ok = False
                is_healthy = False

            if persistence.rdb_last_save_status != "ok":
                issues.append(f"RDB save status: {persistence.rdb_last_save_status}")
                persistence_ok = False
                is_healthy = False

            # 3. Memory check
            memory_info = await self.redis_client.info("memory")
            used_memory = memory_info.get("used_memory", 0)
            max_memory = memory_info.get("maxmemory", 0)

            memory_ok = True
            if max_memory > 0:
                memory_usage_percent = (used_memory / max_memory) * 100
                metrics["memory"] = {
                    "used_mb": used_memory / (1024 * 1024),
                    "max_mb": max_memory / (1024 * 1024),
                    "usage_percent": memory_usage_percent,
                }

                if memory_usage_percent > 90:
                    issues.append(f"High memory usage: {memory_usage_percent:.1f}%")
                    memory_ok = False
                    is_healthy = False
            else:
                metrics["memory"] = {
                    "used_mb": used_memory / (1024 * 1024),
                    "max_mb": "unlimited",
                    "usage_percent": 0,
                }

            # 4. Replication check (if configured)
            replication_info = await self.redis_client.info("replication")
            role = replication_info.get("role", "master")
            connected_slaves = replication_info.get("connected_slaves", 0)

            metrics["replication"] = {
                "role": role,
                "connected_slaves": connected_slaves,
            }

            replication_ok = True
            if role == "master" and connected_slaves == 0:
                # This is expected for single-instance setup
                replication_ok = True
            elif role == "slave":
                master_link_status = replication_info.get("master_link_status", "down")
                if master_link_status != "up":
                    issues.append(f"Master link status: {master_link_status}")
                    replication_ok = False
                    is_healthy = False

            # 5. Stats
            stats_info = await self.redis_client.info("stats")
            metrics["stats"] = {
                "total_connections_received": stats_info.get(
                    "total_connections_received", 0
                ),
                "total_commands_processed": stats_info.get(
                    "total_commands_processed", 0
                ),
                "rejected_connections": stats_info.get("rejected_connections", 0),
                "expired_keys": stats_info.get("expired_keys", 0),
                "evicted_keys": stats_info.get("evicted_keys", 0),
            }

            # Check for concerning stats
            if stats_info.get("rejected_connections", 0) > 0:
                issues.append(
                    f"Rejected connections: {stats_info['rejected_connections']}"
                )

            if stats_info.get("evicted_keys", 0) > 1000:
                issues.append(f"High key evictions: {stats_info['evicted_keys']}")

            return RedisHealthStatus(
                is_healthy=is_healthy,
                persistence_ok=persistence_ok,
                memory_ok=memory_ok,
                replication_ok=replication_ok,
                issues=issues,
                metrics=metrics,
            )

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return RedisHealthStatus(
                is_healthy=False,
                persistence_ok=False,
                memory_ok=False,
                replication_ok=False,
                issues=[f"Health check error: {e!s}"],
                metrics={},
            )

    async def verify_data_integrity(self, sample_size: int = 100) -> bool:
        """
        Verify data integrity by checking sample keys

        Args:
            sample_size: Number of keys to sample

        Returns:
            True if all sampled keys are valid
        """
        await self.connect()

        try:
            # Get random keys
            keys = await self.redis_client.randomkey()
            if not keys:
                logger.info("No keys to verify")
                return True

            # Sample random keys
            corrupted = 0
            for _ in range(min(sample_size, await self.redis_client.dbsize())):
                key = await self.redis_client.randomkey()
                if key:
                    # Try to access the key
                    try:
                        await self.redis_client.get(key)
                    except Exception as e:
                        logger.error(f"Corrupted key detected: {key} - {e}")
                        corrupted += 1

            if corrupted > 0:
                logger.error(
                    f"Data integrity check failed: {corrupted}/{sample_size} keys corrupted"
                )
                return False

            logger.info(f"Data integrity check passed: {sample_size} keys verified")
            return True

        except Exception as e:
            logger.error(f"Data integrity check error: {e}")
            return False

    async def trigger_backup(self) -> bool:
        """
        Trigger Redis BGSAVE (background save)

        Returns:
            True if backup triggered successfully
        """
        await self.connect()

        try:
            result = await self.redis_client.bgsave()
            logger.info("Redis BGSAVE triggered")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger BGSAVE: {e}")
            return False

    async def get_backup_status(self) -> dict:
        """
        Get last backup status

        Returns:
            Dictionary with backup info
        """
        await self.connect()

        info = await self.redis_client.info("persistence")

        last_save_time = datetime.fromtimestamp(info.get("rdb_last_save_time", 0))
        time_since_save = (datetime.now() - last_save_time).total_seconds()

        return {
            "last_save_time": last_save_time.isoformat(),
            "seconds_since_last_save": int(time_since_save),
            "last_save_status": info.get("rdb_last_bgsave_status", "unknown"),
            "changes_since_last_save": info.get("rdb_changes_since_last_save", 0),
            "save_in_progress": info.get("rdb_bgsave_in_progress", 0) == 1,
        }


# Global monitor instance
redis_monitor = RedisMonitor()


# Health check endpoint helper
async def redis_health_check() -> dict:
    """
    Redis health check for /health endpoint

    Returns:
        Health check result dictionary
    """
    try:
        status = await redis_monitor.check_health()

        return {
            "status": "healthy" if status.is_healthy else "unhealthy",
            "persistence": "ok" if status.persistence_ok else "error",
            "memory": "ok" if status.memory_ok else "warning",
            "replication": "ok" if status.replication_ok else "error",
            "issues": status.issues,
            "metrics": status.metrics,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# Periodic monitoring task
async def periodic_redis_monitoring(interval_seconds: int = 300):
    """
    Periodic Redis monitoring task

    Args:
        interval_seconds: Check interval in seconds (default: 5 minutes)
    """
    while True:
        try:
            # Health check
            health = await redis_monitor.check_health()

            if not health.is_healthy:
                logger.error(
                    "Redis health check failed",
                    extra_data={"issues": health.issues, "metrics": health.metrics},
                )
            else:
                logger.info(
                    "Redis health check passed", extra_data={"metrics": health.metrics}
                )

            # Data integrity check (every hour)
            if interval_seconds >= 3600:
                integrity_ok = await redis_monitor.verify_data_integrity()
                if not integrity_ok:
                    logger.error("Redis data integrity check failed")

            # Backup status check
            backup_status = await redis_monitor.get_backup_status()
            if backup_status["seconds_since_last_save"] > 7200:  # 2 hours
                logger.warning("Redis backup is overdue", extra_data=backup_status)

        except Exception as e:
            logger.error(f"Redis monitoring error: {e}")

        await asyncio.sleep(interval_seconds)
