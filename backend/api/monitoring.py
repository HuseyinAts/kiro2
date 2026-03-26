"""
Monitoring API Endpoints
Performance metrics, health checks, system status
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth_dependencies import require_role
from core.database import get_db_session
from core.performance_monitor import performance_monitor
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])
logger = get_logger("monitoring_api")


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Comprehensive health check endpoint
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "1.0.0",
            "services": {},
        }

        # Database health check
        try:
            async with get_db_session() as db:
                await db.execute("SELECT 1")
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {e!s}"
            health_status["status"] = "degraded"

        # Redis health check
        try:
            from core.cache import cache_manager

            if await cache_manager.ping():
                health_status["services"]["redis"] = "healthy"
            else:
                health_status["services"]["redis"] = "unhealthy: no response"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {e!s}"
            health_status["status"] = "degraded"

        # Elasticsearch health check
        try:
            from core.elasticsearch_service import elasticsearch_service

            if await elasticsearch_service.ping():
                health_status["services"]["elasticsearch"] = "healthy"
            else:
                health_status["services"]["elasticsearch"] = "unhealthy: no response"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["services"]["elasticsearch"] = f"unhealthy: {e!s}"
            health_status["status"] = "degraded"

        # Performance monitor health
        health_status["services"]["performance_monitor"] = (
            "healthy" if performance_monitor.is_monitoring else "stopped"
        )

        logger.info(
            "Health check performed",
            extra_data={
                "status": health_status["status"],
                "services": health_status["services"],
            },
        )

        return {
            "success": True,
            "data": health_status,
            "message": "Health check completed",
        }

    except Exception as e:
        logger.error("Health check failed", exception=e)
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/performance/api")
async def get_api_performance(
    hours: int = Query(1, ge=1, le=24, description="Hours to analyze"),
    _: None = Depends(require_role("ADMIN")),
) -> dict[str, Any]:
    """
    Get API performance metrics
    """
    try:
        summary = performance_monitor.get_api_performance_summary(hours)

        logger.info("API performance metrics requested", extra_data={"hours": hours})

        return {
            "success": True,
            "data": summary,
            "message": f"API performance metrics for last {hours} hours",
        }

    except Exception as e:
        logger.error("Failed to get API performance metrics", exception=e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve API performance metrics"
        )


@router.get("/performance/database")
async def get_database_performance(
    hours: int = Query(1, ge=1, le=24, description="Hours to analyze"),
    _: None = Depends(require_role("ADMIN")),
) -> dict[str, Any]:
    """
    Get database performance metrics
    """
    try:
        summary = performance_monitor.get_db_performance_summary(hours)

        logger.info(
            "Database performance metrics requested", extra_data={"hours": hours}
        )

        return {
            "success": True,
            "data": summary,
            "message": f"Database performance metrics for last {hours} hours",
        }

    except Exception as e:
        logger.error("Failed to get database performance metrics", exception=e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve database performance metrics"
        )


@router.get("/performance/system")
async def get_system_performance(
    hours: int = Query(1, ge=1, le=24, description="Hours to analyze"),
    _: None = Depends(require_role("ADMIN")),
) -> dict[str, Any]:
    """
    Get system performance metrics
    """
    try:
        summary = performance_monitor.get_system_performance_summary(hours)

        logger.info("System performance metrics requested", extra_data={"hours": hours})

        return {
            "success": True,
            "data": summary,
            "message": f"System performance metrics for last {hours} hours",
        }

    except Exception as e:
        logger.error("Failed to get system performance metrics", exception=e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve system performance metrics"
        )


@router.get("/performance/summary")
async def get_performance_summary(
    hours: int = Query(1, ge=1, le=24, description="Hours to analyze"),
    _: None = Depends(require_role("ADMIN")),
) -> dict[str, Any]:
    """
    Get comprehensive performance summary
    """
    try:
        api_summary = performance_monitor.get_api_performance_summary(hours)
        db_summary = performance_monitor.get_db_performance_summary(hours)
        system_summary = performance_monitor.get_system_performance_summary(hours)

        summary = {
            "time_period_hours": hours,
            "timestamp": datetime.now(UTC).isoformat(),
            "api_performance": api_summary,
            "database_performance": db_summary,
            "system_performance": system_summary,
        }

        logger.info(
            "Comprehensive performance summary requested", extra_data={"hours": hours}
        )

        return {
            "success": True,
            "data": summary,
            "message": f"Comprehensive performance summary for last {hours} hours",
        }

    except Exception as e:
        logger.error("Failed to get performance summary", exception=e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve performance summary"
        )


@router.get("/metrics/prometheus")
async def get_prometheus_metrics(_: None = Depends(require_role("ADMIN"))) -> str:
    """
    Get metrics in Prometheus format
    """
    try:
        metrics = performance_monitor.export_metrics_to_prometheus()

        logger.info("Prometheus metrics exported")

        return metrics

    except Exception as e:
        logger.error("Failed to export Prometheus metrics", exception=e)
        raise HTTPException(
            status_code=500, detail="Failed to export Prometheus metrics"
        )


@router.get("/bottlenecks")
async def detect_performance_bottlenecks(
    hours: int = Query(1, ge=1, le=24, description="Hours to analyze"),
    _: None = Depends(require_role("ADMIN")),
) -> dict[str, Any]:
    """
    Detect performance bottlenecks
    """
    try:
        bottlenecks = []

        # API bottlenecks
        api_summary = performance_monitor.get_api_performance_summary(hours)
        if isinstance(api_summary, dict) and "avg_response_time_ms" in api_summary:
            if api_summary["avg_response_time_ms"] > 500:
                bottlenecks.append(
                    {
                        "type": "api_performance",
                        "severity": "high"
                        if api_summary["avg_response_time_ms"] > 1000
                        else "medium",
                        "description": f"Average API response time is {api_summary['avg_response_time_ms']:.2f}ms",
                        "recommendation": "Consider optimizing slow endpoints or adding caching",
                    }
                )

        # Database bottlenecks
        db_summary = performance_monitor.get_db_performance_summary(hours)
        if isinstance(db_summary, dict) and "avg_execution_time_ms" in db_summary:
            if db_summary["avg_execution_time_ms"] > 200:
                bottlenecks.append(
                    {
                        "type": "database_performance",
                        "severity": "high"
                        if db_summary["avg_execution_time_ms"] > 500
                        else "medium",
                        "description": f"Average database query time is {db_summary['avg_execution_time_ms']:.2f}ms",
                        "recommendation": "Consider adding database indexes or optimizing queries",
                    }
                )

        # System bottlenecks
        system_summary = performance_monitor.get_system_performance_summary(hours)
        if isinstance(system_summary, dict):
            cpu_avg = system_summary.get("cpu", {}).get("avg_percent", 0)
            memory_avg = system_summary.get("memory", {}).get("avg_percent", 0)

            if cpu_avg > 70:
                bottlenecks.append(
                    {
                        "type": "cpu_usage",
                        "severity": "high" if cpu_avg > 85 else "medium",
                        "description": f"Average CPU usage is {cpu_avg:.1f}%",
                        "recommendation": "Consider scaling up or optimizing CPU-intensive operations",
                    }
                )

            if memory_avg > 80:
                bottlenecks.append(
                    {
                        "type": "memory_usage",
                        "severity": "high" if memory_avg > 90 else "medium",
                        "description": f"Average memory usage is {memory_avg:.1f}%",
                        "recommendation": "Consider increasing memory or optimizing memory usage",
                    }
                )

        logger.info(
            "Performance bottleneck analysis completed",
            extra_data={"hours": hours, "bottlenecks_found": len(bottlenecks)},
        )

        return {
            "success": True,
            "data": {
                "bottlenecks": bottlenecks,
                "analysis_period_hours": hours,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            "message": f"Found {len(bottlenecks)} potential bottlenecks",
        }

    except Exception as e:
        logger.error("Failed to detect performance bottlenecks", exception=e)
        raise HTTPException(
            status_code=500, detail="Failed to detect performance bottlenecks"
        )


@router.post("/monitoring/start")
async def start_monitoring(
    interval_seconds: int = Query(
        30, ge=10, le=300, description="Monitoring interval in seconds"
    ),
    _: None = Depends(require_role("ADMIN")),
) -> dict[str, Any]:
    """
    Start performance monitoring
    """
    try:
        if performance_monitor.is_monitoring:
            return {
                "success": True,
                "message": "Performance monitoring is already running",
            }

        await performance_monitor.start_monitoring(interval_seconds)

        logger.info(
            "Performance monitoring started via API",
            extra_data={"interval_seconds": interval_seconds},
        )

        return {
            "success": True,
            "message": f"Performance monitoring started with {interval_seconds}s interval",
        }

    except Exception as e:
        logger.error("Failed to start performance monitoring", exception=e)
        raise HTTPException(
            status_code=500, detail="Failed to start performance monitoring"
        )


@router.post("/monitoring/stop")
async def stop_monitoring(_: None = Depends(require_role("ADMIN"))) -> dict[str, Any]:
    """
    Stop performance monitoring
    """
    try:
        if not performance_monitor.is_monitoring:
            return {"success": True, "message": "Performance monitoring is not running"}

        await performance_monitor.stop_monitoring()

        logger.info("Performance monitoring stopped via API")

        return {"success": True, "message": "Performance monitoring stopped"}

    except Exception as e:
        logger.error("Failed to stop performance monitoring", exception=e)
        raise HTTPException(
            status_code=500, detail="Failed to stop performance monitoring"
        )


@router.get("/logs/analysis")
async def analyze_logs(
    hours: int = Query(1, ge=1, le=24, description="Hours to analyze"),
    log_level: str | None = Query(None, description="Filter by log level"),
    _: None = Depends(require_role("ADMIN")),
) -> dict[str, Any]:
    """
    Analyze application logs for patterns and issues
    """
    try:
        from core.logging_config import LogAnalyzer

        # Analyze error patterns
        error_analysis = LogAnalyzer.analyze_error_patterns("logs/errors.log")

        # Analyze performance patterns
        performance_analysis = LogAnalyzer.analyze_performance_metrics("logs/api.log")

        analysis = {
            "time_period_hours": hours,
            "timestamp": datetime.now(UTC).isoformat(),
            "error_analysis": error_analysis,
            "performance_analysis": performance_analysis,
        }

        logger.info(
            "Log analysis completed",
            extra_data={"hours": hours, "log_level": log_level},
        )

        return {
            "success": True,
            "data": analysis,
            "message": f"Log analysis for last {hours} hours completed",
        }

    except Exception as e:
        logger.error("Failed to analyze logs", exception=e)
        raise HTTPException(status_code=500, detail="Failed to analyze logs")


@router.get("/token-projection")
async def get_token_projection(
    _: None = Depends(require_role("ADMIN")),
) -> dict[str, Any]:
    """
    Token usage projection — stub endpoint.
    Frontend: TokenOptimizationDashboard.tsx
    """
    return {
        "success": True,
        "data": {
            "current_usage": 0,
            "projected_monthly": 0,
            "budget_remaining": 100,
            "trend": "stable",
        },
        "message": "Token projection stub — not yet implemented",
    }
