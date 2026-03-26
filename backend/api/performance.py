"""
Performance API
Performans metrikleri ve optimizasyon endpoint'leri
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_current_admin_user, AuthenticatedUser

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/performance",
    tags=["Performance"],
    responses={404: {"description": "Not found"}},
)


@router.get("/metrics", response_model=Dict[str, Any])
async def get_performance_metrics(
    current_user: AuthenticatedUser = Depends(get_current_admin_user)
):
    """
    Genel performans metriklerini al
    Sadece admin kullanıcıları erişebilir
    """
    try:
        metrics = {}

        # Cache metrikleri
        try:
            from core.cache import cache_manager

            cache_stats = await cache_manager.get_stats()
            metrics["cache"] = cache_stats
        except Exception as e:
            logger.error(f"Cache metrics hatası: {str(e)}")
            metrics["cache"] = {"error": str(e)}

        # System metrikleri
        try:
            from core.performance_middleware import system_monitor

            system_metrics = system_monitor.get_current_metrics()
            metrics["system"] = system_metrics
        except Exception as e:
            logger.error(f"System metrics hatası: {str(e)}")
            metrics["system"] = {"error": str(e)}

        # Database query metrikleri
        try:
            from core.database_optimizer import query_optimizer

            query_stats = query_optimizer.get_performance_stats()
            metrics["database_queries"] = query_stats
        except Exception as e:
            logger.error(f"Database query metrics hatası: {str(e)}")
            metrics["database_queries"] = {"error": str(e)}

        # Revolutionary features metrikleri
        try:
            from core.revolutionary_optimizer import get_optimization_stats

            revolutionary_stats = get_optimization_stats()
            metrics["revolutionary_features"] = revolutionary_stats
        except Exception as e:
            logger.error(f"Revolutionary features metrics hatası: {str(e)}")
            metrics["revolutionary_features"] = {"error": str(e)}

        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.now().isoformat(),
            "message": "Performans metrikleri başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"Performance metrics hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/system-status", response_model=Dict[str, Any])
async def get_system_status(
    current_user: AuthenticatedUser = Depends(get_current_admin_user)
):
    """
    Sistem durumu ve kaynak kullanımı
    """
    try:
        from core.performance_middleware import system_monitor

        # Güncel sistem metrikleri
        current_metrics = system_monitor.get_current_metrics()

        # Son 1 saatlik geçmiş
        historical_metrics = system_monitor.get_historical_metrics(minutes=60)

        # Sistem durumu değerlendirmesi
        status = "healthy"
        warnings = []

        if current_metrics.get("cpu_percent", 0) > 80:
            status = "warning"
            warnings.append("Yüksek CPU kullanımı")

        if current_metrics.get("memory_percent", 0) > 85:
            status = "warning"
            warnings.append("Yüksek memory kullanımı")

        if current_metrics.get("disk_percent", 0) > 90:
            status = "critical"
            warnings.append("Disk alanı kritik seviyede")

        return {
            "success": True,
            "data": {
                "status": status,
                "warnings": warnings,
                "current_metrics": current_metrics,
                "historical_metrics": historical_metrics[-20:],  # Son 20 ölçüm
                "uptime": "N/A",  # Uptime hesaplanabilir
            },
            "message": f"Sistem durumu: {status}",
        }

    except Exception as e:
        logger.error(f"System status hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/cache-stats", response_model=Dict[str, Any])
async def get_cache_statistics(
    current_user: AuthenticatedUser = Depends(get_current_admin_user)
):
    """
    Cache istatistikleri ve hit/miss oranları
    """
    try:
        from core.cache import cache_manager

        # Redis cache istatistikleri
        cache_stats = await cache_manager.get_stats()

        # Hit/miss oranları hesapla
        hits = cache_stats.get("keyspace_hits", 0)
        misses = cache_stats.get("keyspace_misses", 0)
        total_requests = hits + misses

        hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
        miss_rate = (misses / total_requests * 100) if total_requests > 0 else 0

        return {
            "success": True,
            "data": {
                "redis_stats": cache_stats,
                "performance": {
                    "hit_rate": round(hit_rate, 2),
                    "miss_rate": round(miss_rate, 2),
                    "total_requests": total_requests,
                    "hits": hits,
                    "misses": misses,
                },
                "memory_usage": {
                    "used_memory": cache_stats.get("used_memory", 0),
                    "used_memory_human": cache_stats.get("used_memory_human", "0B"),
                },
            },
            "message": "Cache istatistikleri başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"Cache stats hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/database-performance", response_model=Dict[str, Any])
async def get_database_performance(
    current_user: AuthenticatedUser = Depends(get_current_admin_user)
):
    """
    Database performans metrikleri
    """
    try:
        from core.database_optimizer import query_optimizer

        # Query performans istatistikleri
        query_stats = query_optimizer.get_performance_stats()

        # Özet istatistikler
        total_queries = sum(stats["total_executions"] for stats in query_stats.values())
        avg_response_time = (
            sum(stats["avg_time"] for stats in query_stats.values()) / len(query_stats)
            if query_stats
            else 0
        )
        slow_queries = sum(stats["slow_queries"] for stats in query_stats.values())

        # En yavaş sorgular
        slowest_queries = sorted(
            [(name, stats) for name, stats in query_stats.items()],
            key=lambda x: x[1]["avg_time"],
            reverse=True,
        )[:5]

        return {
            "success": True,
            "data": {
                "summary": {
                    "total_queries": total_queries,
                    "avg_response_time": round(avg_response_time, 3),
                    "slow_queries": slow_queries,
                    "query_types": len(query_stats),
                },
                "slowest_queries": [
                    {
                        "name": name,
                        "avg_time": round(stats["avg_time"], 3),
                        "total_executions": stats["total_executions"],
                        "slow_queries": stats["slow_queries"],
                    }
                    for name, stats in slowest_queries
                ],
                "detailed_stats": query_stats,
            },
            "message": "Database performans metrikleri başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"Database performance hatası: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get("/revolutionary-features-performance", response_model=Dict[str, Any])
async def get_revolutionary_features_performance(
    current_user: AuthenticatedUser = Depends(get_current_admin_user)
):
    """
    Devrimsel özelliklerin performans metrikleri
    """
    try:
        from core.revolutionary_optimizer import get_optimization_stats

        optimization_stats = get_optimization_stats()

        return {
            "success": True,
            "data": optimization_stats,
            "message": "Devrimsel özellik performans metrikleri başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"Revolutionary features performance hatası: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.post("/clear-cache", response_model=Dict[str, Any])
async def clear_cache(
    cache_type: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    Cache'i temizle
    cache_type: "all", "redis", "revolutionary", "learning_style", vb.
    """
    try:
        cleared_caches = []

        if cache_type is None or cache_type == "all" or cache_type == "redis":
            # Redis cache temizle
            try:
                from core.cache import cache_manager

                await cache_manager.clear_pattern("*")
                cleared_caches.append("redis")
            except Exception as e:
                logger.error(f"Redis cache temizleme hatası: {str(e)}")

        if cache_type is None or cache_type == "all" or cache_type == "revolutionary":
            # Revolutionary features cache temizle
            try:
                from core.revolutionary_optimizer import (
                    irt_morphology_optimizer,
                    vark_felder_optimizer,
                    zpd_maarif_optimizer,
                )

                vark_felder_optimizer.profile_cache.clear()
                zpd_maarif_optimizer.cultural_cache.clear()
                irt_morphology_optimizer.morphology_cache.clear()
                cleared_caches.append("revolutionary_features")
            except Exception as e:
                logger.error(f"Revolutionary cache temizleme hatası: {str(e)}")

        if cache_type is None or cache_type == "all" or cache_type == "learning_style":
            # Learning style cache temizle
            try:
                from services.learning_style_service import learning_style_service

                # Safe clear — attributes may not exist after DB-only refactor
                for cache_name in ('profiles_cache', 'behavioral_data_cache', 'questionnaire_cache', 'recommendations_cache'):
                    cache = getattr(learning_style_service, cache_name, None)
                    if cache is not None:
                        cache.clear()
                cleared_caches.append("learning_style")
            except Exception as e:
                logger.error(f"Learning style cache temizleme hatası: {str(e)}")

        return {
            "success": True,
            "data": {
                "cleared_caches": cleared_caches,
                "cache_type": cache_type or "all",
            },
            "message": f"Cache temizlendi: {', '.join(cleared_caches)}",
        }

    except Exception as e:
        logger.error(f"Cache temizleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/api-response-times", response_model=Dict[str, Any])
async def get_api_response_times(
    current_user: AuthenticatedUser = Depends(get_current_admin_user)
):
    """
    API endpoint'lerinin response time'ları
    """
    try:
        # Performance middleware'den istatistikleri al
        # Bu örnekte global bir instance olması gerekiyor
        # Gerçek implementasyonda middleware instance'ına erişim sağlanmalı

        # Mock data - gerçek implementasyonda middleware'den alınacak
        api_stats = {
            "/api/v1/sinav/basla": {
                "total_requests": 150,
                "avg_response_time": 0.245,
                "max_response_time": 1.2,
                "min_response_time": 0.1,
                "success_rate": 0.98,
                "error_rate": 0.02,
            },
            "/api/v1/learning-style/detect": {
                "total_requests": 89,
                "avg_response_time": 0.567,
                "max_response_time": 2.1,
                "min_response_time": 0.3,
                "success_rate": 0.96,
                "error_rate": 0.04,
            },
            "/api/v1/zpd-maarif/calculate": {
                "total_requests": 67,
                "avg_response_time": 0.423,
                "max_response_time": 1.8,
                "min_response_time": 0.2,
                "success_rate": 0.99,
                "error_rate": 0.01,
            },
        }

        # En yavaş endpoint'ler
        slowest_endpoints = sorted(
            api_stats.items(), key=lambda x: x[1]["avg_response_time"], reverse=True
        )[:5]

        return {
            "success": True,
            "data": {
                "api_stats": api_stats,
                "slowest_endpoints": [
                    {
                        "endpoint": endpoint,
                        "avg_response_time": stats["avg_response_time"],
                        "total_requests": stats["total_requests"],
                        "success_rate": stats["success_rate"],
                    }
                    for endpoint, stats in slowest_endpoints
                ],
                "summary": {
                    "total_endpoints": len(api_stats),
                    "total_requests": sum(
                        stats["total_requests"] for stats in api_stats.values()
                    ),
                    "avg_response_time": sum(
                        stats["avg_response_time"] for stats in api_stats.values()
                    )
                    / len(api_stats),
                },
            },
            "message": "API response time metrikleri başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"API response times hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_system(
    optimization_type: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_admin_user),
):
    """
    Sistem optimizasyonu çalıştır
    optimization_type: "cache", "database", "revolutionary", "all"
    """
    try:
        optimizations_applied = []

        if (
            optimization_type is None
            or optimization_type == "all"
            or optimization_type == "cache"
        ):
            # Cache optimizasyonu
            try:
                from core.cache import cache_manager

                # Cache'i yeniden başlat
                await cache_manager.close()
                await cache_manager.initialize()
                optimizations_applied.append("cache_restart")
            except Exception as e:
                logger.error(f"Cache optimizasyon hatası: {str(e)}")

        if (
            optimization_type is None
            or optimization_type == "all"
            or optimization_type == "revolutionary"
        ):
            # Revolutionary features optimizasyonu
            try:
                from core.revolutionary_optimizer import (
                    optimize_all_revolutionary_features,
                )

                await optimize_all_revolutionary_features()
                optimizations_applied.append("revolutionary_features")
            except Exception as e:
                logger.error(f"Revolutionary optimizasyon hatası: {str(e)}")

        if (
            optimization_type is None
            or optimization_type == "all"
            or optimization_type == "database"
        ):
            # Database optimizasyonu
            try:
                from core.database import get_db_session_context
                from core.database_optimizer import create_performance_indexes

                async with get_db_session_context() as session:
                    await create_performance_indexes(session)
                optimizations_applied.append("database_indexes")
            except Exception as e:
                logger.error(f"Database optimizasyon hatası: {str(e)}")

        return {
            "success": True,
            "data": {
                "optimizations_applied": optimizations_applied,
                "optimization_type": optimization_type or "all",
                "timestamp": datetime.now().isoformat(),
            },
            "message": f"Sistem optimizasyonu tamamlandı: {', '.join(optimizations_applied)}",
        }

    except Exception as e:
        logger.error(f"Sistem optimizasyon hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/health-check", response_model=Dict[str, Any])
async def performance_health_check():
    """
    Performans sistemlerinin sağlık kontrolü
    """
    try:
        health_status = {
            "cache": "unknown",
            "database": "unknown",
            "monitoring": "unknown",
            "revolutionary_features": "unknown",
        }

        # Cache sağlık kontrolü
        try:
            from core.cache import cache_manager

            await cache_manager.get("health_check")
            health_status["cache"] = "healthy"
        except Exception:
            health_status["cache"] = "unhealthy"

        # Database sağlık kontrolü
        try:
            from core.database import get_db_session_context

            async with get_db_session_context() as session:
                await session.execute("SELECT 1")
            health_status["database"] = "healthy"
        except Exception:
            health_status["database"] = "unhealthy"

        # Monitoring sağlık kontrolü
        try:
            from core.performance_middleware import system_monitor

            if system_monitor.monitoring:
                health_status["monitoring"] = "healthy"
            else:
                health_status["monitoring"] = "stopped"
        except Exception:
            health_status["monitoring"] = "unhealthy"

        # Revolutionary features sağlık kontrolü
        try:
            from core.revolutionary_optimizer import get_optimization_stats

            stats = get_optimization_stats()
            if stats:
                health_status["revolutionary_features"] = "healthy"
            else:
                health_status["revolutionary_features"] = "no_data"
        except Exception:
            health_status["revolutionary_features"] = "unhealthy"

        # Genel sağlık durumu
        overall_health = (
            "healthy"
            if all(
                status in ["healthy", "no_data"] for status in health_status.values()
            )
            else "degraded"
        )

        return {
            "success": True,
            "data": {
                "overall_health": overall_health,
                "components": health_status,
                "timestamp": datetime.now().isoformat(),
            },
            "message": f"Performans sistemleri sağlık durumu: {overall_health}",
        }

    except Exception as e:
        logger.error(f"Performance health check hatası: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )
