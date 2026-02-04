"""
Monitoring API Endpoints
Video öneri sistemi monitoring metriklerini expose eder
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from services.enhanced_resource_recommendation_engine import (
    get_enhanced_recommendation_engine,
)
from services.video_recommendation_monitoring import (
    get_video_recommendation_monitor,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/video-recommendations/stats")
async def get_video_recommendation_stats() -> Dict[str, Any]:
    """
    Video öneri sistemi istatistiklerini al

    Returns:
        Kapsamlı monitoring metrikleri
    """
    try:
        monitor = get_video_recommendation_monitor()
        stats = monitor.get_comprehensive_report()

        return {
            "success": True,
            "data": stats,
            "message": "Video recommendation stats retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Error getting video recommendation stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monitoring istatistikleri alınamadı: {str(e)}",
        )


@router.get("/video-recommendations/filter-stats")
async def get_filter_stats() -> Dict[str, Any]:
    """
    Video filtreleme istatistiklerini al

    Returns:
        Filtre metrikleri
    """
    try:
        monitor = get_video_recommendation_monitor()
        stats = monitor.get_filter_stats()

        return {
            "success": True,
            "data": stats,
            "message": "Filter stats retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Error getting filter stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Filtre istatistikleri alınamadı: {str(e)}",
        )


@router.get("/video-recommendations/validation-failures")
async def get_validation_failures() -> Dict[str, Any]:
    """
    Validation başarısızlıklarını al

    Returns:
        Validation başarısızlık metrikleri
    """
    try:
        monitor = get_video_recommendation_monitor()
        stats = monitor.get_validation_failure_stats()

        return {
            "success": True,
            "data": stats,
            "message": "Validation failures retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Error getting validation failures: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation başarısızlıkları alınamadı: {str(e)}",
        )


@router.get("/video-recommendations/performance")
async def get_performance_stats() -> Dict[str, Any]:
    """
    Performance istatistiklerini al

    Returns:
        Performance metrikleri
    """
    try:
        monitor = get_video_recommendation_monitor()
        stats = monitor.get_performance_stats()

        return {
            "success": True,
            "data": stats,
            "message": "Performance stats retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Performance istatistikleri alınamadı: {str(e)}",
        )


@router.get("/video-recommendations/errors")
async def get_error_stats() -> Dict[str, Any]:
    """
    Hata istatistiklerini al

    Returns:
        Hata metrikleri
    """
    try:
        monitor = get_video_recommendation_monitor()
        stats = monitor.get_error_stats()

        return {
            "success": True,
            "data": stats,
            "message": "Error stats retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Error getting error stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hata istatistikleri alınamadı: {str(e)}",
        )


@router.post("/video-recommendations/reset-metrics")
async def reset_monitoring_metrics() -> Dict[str, Any]:
    """
    Monitoring metriklerini sıfırla

    Returns:
        Başarı mesajı
    """
    try:
        monitor = get_video_recommendation_monitor()
        monitor.reset_metrics()

        logger.info("Video recommendation monitoring metrics reset")

        return {
            "success": True,
            "data": None,
            "message": "Monitoring metrikleri sıfırlandı",
        }
    except Exception as e:
        logger.error(f"Error resetting monitoring metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monitoring metrikleri sıfırlanamadı: {str(e)}",
        )


@router.get("/video-recommendations/health")
async def get_system_health() -> Dict[str, Any]:
    """
    Sistem sağlık durumunu kontrol et

    Returns:
        Sistem sağlık metrikleri
    """
    try:
        monitor = get_video_recommendation_monitor()
        perf_stats = monitor.get_performance_stats()
        error_stats = monitor.get_error_stats()

        # Sağlık durumu hesapla
        total_requests = perf_stats["requests"]["total"]
        success_rate = perf_stats["requests"]["success_rate"]
        error_rate = error_stats["error_rate"]
        avg_processing_time = perf_stats["timing"]["avg_processing_time"]

        # Health status belirleme
        health_status = "healthy"
        issues = []

        if total_requests > 0:
            if success_rate < 0.9:
                health_status = "degraded"
                issues.append(f"Düşük başarı oranı: {success_rate:.1%}")

            if error_rate > 0.1:
                health_status = "degraded"
                issues.append(f"Yüksek hata oranı: {error_rate:.1%}")

            if avg_processing_time > 5.0:
                health_status = "degraded"
                issues.append(f"Yavaş işlem süresi: {avg_processing_time:.2f}s")

            if perf_stats["youtube_api"]["quota_exceeded"] > 0:
                health_status = "degraded"
                issues.append("YouTube API quota aşıldı")

        return {
            "success": True,
            "data": {
                "status": health_status,
                "total_requests": total_requests,
                "success_rate": success_rate,
                "error_rate": error_rate,
                "avg_processing_time": avg_processing_time,
                "cache_hit_rate": perf_stats["cache"]["hit_rate"],
                "issues": issues,
            },
            "message": f"Sistem durumu: {health_status}",
        }
    except Exception as e:
        logger.error(f"Error checking system health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sistem sağlık durumu kontrol edilemedi: {str(e)}",
        )
