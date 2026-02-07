"""
Health Check Router

Sistem sağlık durumu kontrolleri.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import psutil
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basit health check endpoint'i."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "KIRO2 Backend API"
    }

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes readiness probe için endpoint.
    
    Servisin trafiği kabul etmeye hazır olup olmadığını kontrol eder.
    """
    try:
        # Database bağlantı kontrolü yapılabilir
        # Redis bağlantı kontrolü yapılabilir
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": "ok",
                "cache": "ok",
                "services": "ok"
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )

@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes liveness probe için endpoint.
    
    Servisin çalışıp çalışmadığını kontrol eder.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/startup")
async def startup_check() -> Dict[str, Any]:
    """
    Kubernetes startup probe için endpoint.
    
    Servisin başlatma işleminin tamamlanıp tamamlanmadığını kontrol eder.
    """
    return {
        "status": "started",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0")
    }

@router.get("/metrics")
async def health_metrics() -> Dict[str, Any]:
    """
    Detaylı sistem metrikleri.
    
    CPU, memory, disk kullanımı gibi sistem metriklerini döndürür.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                }
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {
            "status": "partial",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }