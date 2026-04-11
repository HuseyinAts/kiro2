"""
Cache Metrics API - Sprint 2
Real-time cache performance monitoring and analytics

Provides:
- Multi-layer cache hit/miss rates
- L1/L2 performance breakdown
- Cache size and utilization
- Response time improvements
- Cache invalidation triggers
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from core.dependencies import get_current_admin_user
from core.multi_layer_cache import get_cache_instance
from core.structured_logger import get_logger

router = APIRouter(prefix="/api/v1/cache-metrics", tags=["Cache Monitoring"])
logger = get_logger("cache_metrics_api")


@router.get("/metrics", response_model=dict[str, Any])
async def get_cache_metrics(
    namespace: str = Query(None, description="Filter by cache namespace"),
    _=Depends(get_current_admin_user),
):
    """
    Get real-time cache performance metrics

    Returns comprehensive cache statistics including:
    - **Hit Rates**: L1, L2, and overall hit rates
    - **Performance**: Cache promotions, evictions
    - **Utilization**: Cache size, memory usage
    - **Response Times**: Cached vs uncached comparison

    **Use Cases**:
    - Monitor cache effectiveness
    - Identify performance bottlenecks
    - Optimize cache configuration
    - Debug cache issues

    **Expected Metrics**:
    - Overall hit rate: 70-80% target
    - L1 hit rate: 40-50%
    - L2 hit rate: 30-40%
    - Response time improvement: 20-40x
    """
    try:
        # Get global cache instance
        cache = get_cache_instance()

        if cache is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "success": False,
                    "error": "Cache not initialized",
                    "message": "Multi-layer cache is not available. Check Redis connection.",
                },
            )

        # Get metrics
        metrics = cache.get_metrics()
        l1_stats = cache.get_l1_stats()

        # Calculate response time improvement
        # Assume: L1 cache ~1ms, L2 cache ~10ms, Database ~1000ms
        l1_hit_rate = metrics.get("l1_hits", 0) / max(
            1, metrics.get("l1_hits", 0) + metrics.get("l1_misses", 0)
        )
        l2_hit_rate = metrics.get("l2_hits", 0) / max(
            1, metrics.get("l2_hits", 0) + metrics.get("l2_misses", 0)
        )

        avg_response_time = (
            l1_hit_rate * 1  # L1 hits: 1ms
            + (1 - l1_hit_rate) * l2_hit_rate * 10  # L2 hits: 10ms
            + (1 - l1_hit_rate) * (1 - l2_hit_rate) * 1000  # Database: 1000ms
        )

        performance_improvement = 1000 / max(1, avg_response_time)

        response_data = {
            "success": True,
            "cache_metrics": metrics,
            "l1_statistics": l1_stats,
            "performance_analysis": {
                "average_response_time_ms": round(avg_response_time, 2),
                "performance_improvement": f"{performance_improvement:.1f}x",
                "cache_effectiveness": "excellent"
                if metrics.get("overall_hit_rate", "0%") >= "70%"
                else "good"
                if metrics.get("overall_hit_rate", "0%") >= "50%"
                else "needs_improvement",
            },
            "recommendations": _generate_recommendations(metrics, l1_stats),
        }

        logger.info("cache_metrics_retrieved", namespace=cache.namespace)

        return JSONResponse(status_code=status.HTTP_200_OK, content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("cache_metrics_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/invalidate/{pattern}")
async def invalidate_cache_pattern(pattern: str, _=Depends(get_current_admin_user)):
    """
    Invalidate cache entries matching pattern

    **Pattern Examples**:
    - `exam_performance:*` - All exam performance caches
    - `user:12345:*` - All caches for user 12345
    - `soru_bankasi:*` - All question bank caches

    **Use Cases**:
    - After data updates
    - Manual cache refresh
    - Testing cache behavior
    - Emergency cache clear

    **Security**: Protected endpoint (requires admin role in production)
    """
    try:
        cache = get_cache_instance()

        if cache is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache not initialized",
            )

        # Invalidate matching keys
        deleted_count = await cache.invalidate_pattern(pattern)

        logger.info("cache_invalidated", pattern=pattern, deleted_count=deleted_count)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "pattern": pattern,
                "deleted_count": deleted_count,
                "message": f"Invalidated {deleted_count} cache entries matching pattern '{pattern}'",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("cache_invalidation_error", pattern=pattern, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/clear-all")
async def clear_all_caches(_=Depends(get_current_admin_user)):
    """
    Clear all cache entries (L1 + L2)

    **WARNING**: This will clear ALL caches across all namespaces.
    Use with caution in production.

    **Use Cases**:
    - Development/testing
    - Major data migrations
    - Cache corruption recovery
    - Performance testing baseline

    **Security**: Should be protected in production (admin only)
    """
    try:
        cache = get_cache_instance()

        if cache is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache not initialized",
            )

        await cache.clear_all()

        logger.warning("all_caches_cleared")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "All caches cleared successfully",
                "warning": "This action cleared both L1 (memory) and L2 (Redis) caches",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("cache_clear_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/health")
async def cache_health_check():
    """
    Check cache system health

    Returns:
    - Cache availability (L1 + L2)
    - Connection status
    - Recent errors
    - Performance indicators
    """
    try:
        cache = get_cache_instance()

        if cache is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "healthy": False,
                    "l1_status": "unavailable",
                    "l2_status": "unavailable",
                    "message": "Cache not initialized",
                },
            )

        # Check L1 (always available)
        l1_healthy = cache._l1_cache is not None

        # Check L2 (Redis)
        l2_healthy = cache._redis_enabled and cache._redis is not None

        if l2_healthy:
            try:
                await cache._redis.ping()
            except (ConnectionError, OSError, AttributeError) as e:
                logger.debug(f"Redis ping failed: {e}")
                l2_healthy = False

        overall_healthy = l1_healthy  # System works with L1 only

        return JSONResponse(
            status_code=status.HTTP_200_OK
            if overall_healthy
            else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "healthy": overall_healthy,
                "l1_status": "healthy" if l1_healthy else "unhealthy",
                "l2_status": "healthy" if l2_healthy else "degraded",
                "mode": "full"
                if (l1_healthy and l2_healthy)
                else "degraded"
                if l1_healthy
                else "unavailable",
                "message": "Cache system operational"
                if overall_healthy
                else "Cache system unavailable",
            },
        )

    except Exception as e:
        logger.error("cache_health_check_error", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "healthy": False,
                "error": str(e),
                "message": "Cache health check failed",
            },
        )


def _generate_recommendations(
    metrics: dict[str, Any], l1_stats: dict[str, Any]
) -> list[str]:
    """Generate performance recommendations based on metrics"""
    recommendations = []

    # Parse hit rate percentages
    def parse_rate(rate_str):
        try:
            return float(rate_str.replace("%", ""))
        except (ValueError, AttributeError):
            return 0.0

    overall_hit_rate = parse_rate(metrics.get("overall_hit_rate", "0%"))
    l1_hit_rate = parse_rate(metrics.get("l1_hit_rate", "0%"))

    # Check overall hit rate
    if overall_hit_rate < 50:
        recommendations.append(
            "⚠️ Overall hit rate is low (<50%). Consider increasing cache TTL or reviewing cache key strategy."
        )
    elif overall_hit_rate < 70:
        recommendations.append(
            "✅ Good hit rate (50-70%). Fine-tune TTL values for further improvement."
        )
    else:
        recommendations.append(
            "🎉 Excellent hit rate (>70%). Cache is performing optimally!"
        )

    # Check L1 utilization
    l1_size = metrics.get("l1_size", 0)
    l1_max = metrics.get("l1_max_size", 100)
    l1_utilization = (l1_size / l1_max) * 100

    if l1_utilization > 90:
        recommendations.append(
            f"⚠️ L1 cache is almost full ({l1_utilization:.1f}%). Consider increasing l1_max_size."
        )

    # Check evictions
    evictions = metrics.get("evictions", 0)
    sets = metrics.get("sets", 1)
    eviction_rate = (evictions / max(1, sets)) * 100

    if eviction_rate > 20:
        recommendations.append(
            f"⚠️ High eviction rate ({eviction_rate:.1f}%). Increase L1 cache size or adjust TTL."
        )

    # Check errors
    errors = metrics.get("errors", 0)
    if errors > 10:
        recommendations.append(
            f"❌ Detected {errors} cache errors. Check Redis connection and serialization logic."
        )

    # Check L2 status
    if not metrics.get("l2_enabled", False):
        recommendations.append(
            "⚠️ L2 (Redis) cache is disabled. System is running on L1 (memory) only with reduced performance."
        )

    if not recommendations:
        recommendations.append("✅ All cache metrics look good. No action needed.")

    return recommendations
