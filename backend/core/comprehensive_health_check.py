"""
Comprehensive Health Check System
RELIABILITY FIX: Production-ready health monitoring with Kubernetes support
"""

import asyncio
import shutil
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .structured_logger import get_logger

logger = get_logger("health_check")


class HealthStatus(Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Individual component health"""

    name: str
    status: HealthStatus
    healthy: bool
    response_time_ms: float
    message: str | None = None
    details: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class SystemHealth:
    """Overall system health"""

    status: HealthStatus
    timestamp: str
    response_time_ms: float
    components: list[ComponentHealth]
    summary: dict[str, int]
    readiness: bool  # Kubernetes readiness
    liveness: bool  # Kubernetes liveness


class HealthChecker:
    """
    Comprehensive health check system

    Features:
    - Database health (connection, pool, query performance)
    - Redis health (persistence, memory, replication)
    - Elasticsearch health (cluster status)
    - Disk space monitoring
    - Memory usage monitoring
    - Kubernetes readiness/liveness probes
    """

    def __init__(self):
        self.critical_services = ["database"]
        self.optional_services = ["redis", "elasticsearch", "llm_service"]

    async def check_all(self, session: AsyncSession = None) -> SystemHealth:
        """
        Run comprehensive health checks

        Args:
            session: Database session (optional)

        Returns:
            SystemHealth with all component statuses
        """
        start_time = time.time()
        components = []

        # Run health checks in parallel with per-check timeout (5s max)
        check_timeout = 5.0
        tasks = [
            asyncio.wait_for(
                self._check_database(session)
                if session
                else self._check_database_standalone(),
                timeout=check_timeout,
            ),
            asyncio.wait_for(self._check_redis(), timeout=check_timeout),
            asyncio.wait_for(self._check_elasticsearch(), timeout=check_timeout),
            self._check_disk_space(),
            self._check_memory(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        check_names = ["database", "redis", "elasticsearch", "disk_space", "memory"]
        for i, result in enumerate(results):
            name = check_names[i] if i < len(check_names) else "unknown"
            if isinstance(result, asyncio.TimeoutError):
                components.append(
                    ComponentHealth(
                        name=name,
                        status=HealthStatus.UNKNOWN,
                        healthy=name not in self.critical_services,
                        response_time_ms=check_timeout * 1000,
                        message=f"{name} check timed out ({check_timeout}s)",
                    )
                )
            elif isinstance(result, Exception):
                components.append(
                    ComponentHealth(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        healthy=name not in self.critical_services,
                        response_time_ms=0,
                        error=str(result),
                    )
                )
            elif isinstance(result, ComponentHealth):
                components.append(result)

        # Calculate overall status
        critical_healthy = all(
            c.healthy for c in components if c.name in self.critical_services
        )

        all_healthy = all(c.healthy for c in components)

        if all_healthy:
            overall_status = HealthStatus.HEALTHY
        elif critical_healthy:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNHEALTHY

        # Summary
        summary = {
            "total": len(components),
            "healthy": sum(1 for c in components if c.healthy),
            "unhealthy": sum(1 for c in components if not c.healthy),
            "critical_healthy": sum(
                1 for c in components if c.name in self.critical_services and c.healthy
            ),
        }

        # Kubernetes probes
        readiness = critical_healthy  # Ready to serve traffic if critical services ok
        liveness = any(c.healthy for c in components)  # Alive if any service responds

        total_time = (time.time() - start_time) * 1000

        return SystemHealth(
            status=overall_status,
            timestamp=datetime.now(UTC).isoformat(),
            response_time_ms=round(total_time, 2),
            components=components,
            summary=summary,
            readiness=readiness,
            liveness=liveness,
        )

    async def _check_database(self, session: AsyncSession) -> ComponentHealth:
        """Check database health with connection pool metrics"""
        start_time = time.time()

        try:
            # Simple query
            result = await session.execute(text("SELECT 1 as health_check"))
            row = result.scalar()

            if row != 1:
                raise Exception("Database query returned unexpected result")

            # Connection pool stats
            pool_stats = {}
            try:
                pool = session.get_bind().pool
                pool_stats = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                }
            except Exception as e:
                logger.debug(f"Could not get pool stats: {e}")

            # Table count (optional)
            try:
                table_result = await session.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                )
                table_count = table_result.scalar()
                pool_stats["tables"] = table_count
            except Exception as e:
                logger.debug(f"Could not get table count: {e}")

            duration_ms = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                healthy=True,
                response_time_ms=round(duration_ms, 2),
                message="Database connection successful",
                details={"connection_pool": pool_stats},
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")

            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                healthy=False,
                response_time_ms=round(duration_ms, 2),
                error=str(e),
            )

    async def _check_database_standalone(self) -> ComponentHealth:
        """Check database without session (for standalone checks)"""
        start_time = time.time()

        try:
            from core.database import get_db_session_context

            async with get_db_session_context() as session:
                return await self._check_database(session)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                healthy=False,
                response_time_ms=round(duration_ms, 2),
                error=str(e),
            )

    async def _check_redis(self) -> ComponentHealth:
        """Check Redis health with persistence and memory metrics"""
        start_time = time.time()

        try:
            from core.redis_monitoring import redis_monitor

            health = await redis_monitor.check_health()

            duration_ms = (time.time() - start_time) * 1000

            if health.is_healthy:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    response_time_ms=round(duration_ms, 2),
                    message="Redis operational",
                    details=health.metrics,
                )
            return ComponentHealth(
                name="redis",
                status=HealthStatus.DEGRADED,
                healthy=True,  # Non-critical
                response_time_ms=round(duration_ms, 2),
                message=f"Redis issues: {', '.join(health.issues)}",
                details=health.metrics,
            )

        except ImportError:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNKNOWN,
                healthy=True,  # Non-critical
                response_time_ms=0,
                message="Redis monitoring not available",
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                healthy=True,  # Non-critical
                response_time_ms=round(duration_ms, 2),
                error=str(e),
            )

    async def _check_elasticsearch(self) -> ComponentHealth:
        """Check Elasticsearch cluster health"""
        start_time = time.time()

        try:
            from core.elasticsearch_client import get_elasticsearch_client
            
            es_wrapper = get_elasticsearch_client()
            await es_wrapper._ensure_connected()
            es = es_wrapper._client
            
            try:
                health = await es.cluster.health(request_timeout=2.0)
            except Exception:
                pass

            duration_ms = (time.time() - start_time) * 1000
            cluster_status = health.get("status", "unknown")

            status_map = {
                "green": HealthStatus.HEALTHY,
                "yellow": HealthStatus.DEGRADED,
                "red": HealthStatus.UNHEALTHY,
            }

            return ComponentHealth(
                name="elasticsearch",
                status=status_map.get(cluster_status, HealthStatus.UNKNOWN),
                healthy=True,  # Non-critical
                response_time_ms=round(duration_ms, 2),
                message=f"Cluster status: {cluster_status}",
                details={
                    "cluster_name": health.get("cluster_name"),
                    "number_of_nodes": health.get("number_of_nodes"),
                    "active_shards": health.get("active_shards"),
                },
            )

        except ImportError:
            return ComponentHealth(
                name="elasticsearch",
                status=HealthStatus.UNKNOWN,
                healthy=True,  # Non-critical
                response_time_ms=0,
                message="Elasticsearch not configured",
            )
        except (ConnectionRefusedError, ConnectionError, OSError):
            duration_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="elasticsearch",
                status=HealthStatus.UNKNOWN,
                healthy=True,  # Non-critical
                response_time_ms=round(duration_ms, 2),
                message="Elasticsearch unavailable",
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="elasticsearch",
                status=HealthStatus.UNHEALTHY,
                healthy=True,  # Non-critical
                response_time_ms=round(duration_ms, 2),
                error=str(e),
            )

    async def _check_disk_space(self) -> ComponentHealth:
        """Check disk space availability"""
        start_time = time.time()

        try:
            # Get disk usage for current directory
            disk = shutil.disk_usage("/")
            total_gb = disk.total / (1024**3)
            used_gb = disk.used / (1024**3)
            free_gb = disk.free / (1024**3)
            usage_percent = (disk.used / disk.total) * 100

            duration_ms = (time.time() - start_time) * 1000

            # Determine status based on usage
            if usage_percent < 80:
                status = HealthStatus.HEALTHY
                healthy = True
                message = f"Disk usage: {usage_percent:.1f}%"
            elif usage_percent < 90:
                status = HealthStatus.DEGRADED
                healthy = True
                message = f"High disk usage: {usage_percent:.1f}%"
            else:
                status = HealthStatus.UNHEALTHY
                healthy = False
                message = f"Critical disk usage: {usage_percent:.1f}%"

            return ComponentHealth(
                name="disk_space",
                status=status,
                healthy=healthy,
                response_time_ms=round(duration_ms, 2),
                message=message,
                details={
                    "total_gb": round(total_gb, 2),
                    "used_gb": round(used_gb, 2),
                    "free_gb": round(free_gb, 2),
                    "usage_percent": round(usage_percent, 2),
                },
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                healthy=True,
                response_time_ms=round(duration_ms, 2),
                error=str(e),
            )

    async def _check_memory(self) -> ComponentHealth:
        """Check system memory usage"""
        start_time = time.time()

        try:
            import psutil

            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            available_gb = memory.available / (1024**3)
            total_gb = memory.total / (1024**3)

            duration_ms = (time.time() - start_time) * 1000

            # Determine status
            if usage_percent < 80:
                status = HealthStatus.HEALTHY
                healthy = True
                message = f"Memory usage: {usage_percent:.1f}%"
            elif usage_percent < 90:
                status = HealthStatus.DEGRADED
                healthy = True
                message = f"High memory usage: {usage_percent:.1f}%"
            else:
                status = HealthStatus.UNHEALTHY
                healthy = False
                message = f"Critical memory usage: {usage_percent:.1f}%"

            return ComponentHealth(
                name="memory",
                status=status,
                healthy=healthy,
                response_time_ms=round(duration_ms, 2),
                message=message,
                details={
                    "total_gb": round(total_gb, 2),
                    "available_gb": round(available_gb, 2),
                    "usage_percent": round(usage_percent, 2),
                },
            )

        except ImportError:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                healthy=True,
                response_time_ms=0,
                message="psutil not installed",
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                healthy=True,
                response_time_ms=round(duration_ms, 2),
                error=str(e),
            )


# Global health checker instance
health_checker = HealthChecker()


# Helper functions for different health check types
async def kubernetes_readiness_probe() -> bool:
    """
    Kubernetes readiness probe

    Returns True if application is ready to serve traffic

    Usage in K8s:
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
    """
    try:
        health = await health_checker.check_all()
        return health.readiness
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return False


async def kubernetes_liveness_probe() -> bool:
    """
    Kubernetes liveness probe

    Returns True if application is alive (should not be restarted)

    Usage in K8s:
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
    """
    try:
        health = await health_checker.check_all()
        return health.liveness
    except Exception as e:
        logger.error(f"Liveness probe failed: {e}")
        return False


async def kubernetes_startup_probe() -> bool:
    """
    Kubernetes startup probe

    Returns True once application has started successfully

    Usage in K8s:
        startupProbe:
          httpGet:
            path: /health/startup
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 10
          failureThreshold: 30
    """
    try:
        from core.database import get_db_session_context

        # Check if critical services are up
        async with get_db_session_context() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Startup probe failed: {e}")
        return False
