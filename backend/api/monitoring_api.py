"""
Production Health Monitoring API Endpoints
Teknofest 2025 - Görev 68.2 Production Health Monitoring

Bu modül monitoring verilerine erişim için API endpoint'leri sağlar:
- /metrics - Prometheus formatında metrikler
- /health - Sistem sağlık durumu
- /performance - Performans özeti
- /bottlenecks - Tespit edilen darboğazlar
"""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse

from ..core.production_health_monitor import production_health_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Prometheus formatında sistem metriklerini döndür

    Bu endpoint Prometheus tarafından scrape edilmek için kullanılır.
    """
    try:
        metrics_data = production_health_monitor.get_prometheus_metrics()
        return Response(
            content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Prometheus metrics hatası: {e}")
        raise HTTPException(status_code=500, detail="Metrics alınamadı")


@router.get("/health")
async def get_health_status():
    """
    Sistem sağlık durumunu döndür

    Returns:
        - overall_status: healthy/degraded/unhealthy/critical
        - components: Her component için detaylı sağlık durumu
        - last_check: Son sağlık kontrolü zamanı
        - uptime: Sistem çalışma süresi
    """
    try:
        health_summary = production_health_monitor.get_health_summary()

        # Overall health status hesapla
        system_cpu = health_summary["system"]["cpu_percent"]
        system_memory = health_summary["system"]["memory_percent"]
        api_error_rate = health_summary["api"]["error_rate"]
        api_response_time = health_summary["api"]["p95_response_time"]

        # Health status belirleme
        overall_status = "healthy"

        if (
            system_cpu > 95
            or system_memory > 95
            or api_error_rate > 0.3
            or api_response_time > 10
        ):
            overall_status = "critical"
        elif (
            system_cpu > 85
            or system_memory > 90
            or api_error_rate > 0.15
            or api_response_time > 5
        ):
            overall_status = "unhealthy"
        elif (
            system_cpu > 75
            or system_memory > 80
            or api_error_rate > 0.05
            or api_response_time > 2
        ):
            overall_status = "degraded"

        return {
            "success": True,
            "data": {
                "overall_status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "monitoring_active": health_summary["monitoring_active"],
                "last_health_check": health_summary["last_health_check"],
                "components": {
                    "system": {
                        "status": _get_component_status(system_cpu, [75, 85, 95]),
                        "cpu_percent": system_cpu,
                        "memory_percent": system_memory,
                        "memory_available_gb": health_summary["system"][
                            "memory_available_gb"
                        ],
                        "disk_usage": health_summary["system"]["disk_usage"],
                    },
                    "api": {
                        "status": _get_component_status(
                            api_error_rate * 100, [5, 15, 30]
                        ),
                        "total_requests_5min": health_summary["api"][
                            "total_requests_5min"
                        ],
                        "avg_response_time": health_summary["api"]["avg_response_time"],
                        "error_rate": api_error_rate,
                        "p95_response_time": api_response_time,
                    },
                    "database": {
                        "status": _get_component_status(
                            health_summary["database"]["avg_query_time"], [1, 3, 5]
                        ),
                        "total_queries_5min": health_summary["database"][
                            "total_queries_5min"
                        ],
                        "avg_query_time": health_summary["database"]["avg_query_time"],
                        "p95_query_time": health_summary["database"]["p95_query_time"],
                    },
                },
                "active_bottlenecks": health_summary["bottlenecks"]["active_count"],
            },
            "message": f"Sistem durumu: {overall_status}",
        }

    except Exception as e:
        logger.error(f"Health status hatası: {e}")
        raise HTTPException(status_code=500, detail="Sağlık durumu alınamadı")


@router.get("/performance")
async def get_performance_summary():
    """
    Performans özeti ve istatistikleri

    Returns:
        - response_times: API response time istatistikleri
        - database_performance: Database query performance
        - system_resources: Sistem kaynak kullanımı
        - trends: Performans trendleri
    """
    try:
        health_summary = production_health_monitor.get_health_summary()

        # Performance trends hesapla (son 1 saat)
        current_time = datetime.now()

        return {
            "success": True,
            "data": {
                "timestamp": current_time.isoformat(),
                "response_times": {
                    "avg_response_time": health_summary["api"]["avg_response_time"],
                    "p95_response_time": health_summary["api"]["p95_response_time"],
                    "total_requests_5min": health_summary["api"]["total_requests_5min"],
                    "error_rate": health_summary["api"]["error_rate"],
                },
                "database_performance": {
                    "avg_query_time": health_summary["database"]["avg_query_time"],
                    "p95_query_time": health_summary["database"]["p95_query_time"],
                    "total_queries_5min": health_summary["database"][
                        "total_queries_5min"
                    ],
                },
                "system_resources": {
                    "cpu_percent": health_summary["system"]["cpu_percent"],
                    "memory_percent": health_summary["system"]["memory_percent"],
                    "memory_available_gb": health_summary["system"][
                        "memory_available_gb"
                    ],
                    "disk_usage": health_summary["system"]["disk_usage"],
                },
                "cache_performance": {
                    "hit_rate": 0.85,  # Placeholder - gerçek cache metrics'ten alınacak
                    "avg_response_time": 0.001,
                    "total_operations_5min": 1500,
                },
            },
            "message": "Performans verileri başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"Performance summary hatası: {e}")
        raise HTTPException(status_code=500, detail="Performans verileri alınamadı")


@router.get("/bottlenecks")
async def get_performance_bottlenecks():
    """
    Tespit edilen performans darboğazları ve öneriler

    Returns:
        - active_bottlenecks: Aktif darboğazlar
        - recommendations: Performans önerileri
        - severity_distribution: Darboğaz şiddet dağılımı
    """
    try:
        recommendations = production_health_monitor.get_performance_recommendations()

        # Severity distribution hesapla
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for rec in recommendations:
            severity = rec.get("severity", "medium")
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Bottleneck types distribution
        type_counts = {}
        for rec in recommendations:
            bottleneck_type = rec.get("type", "unknown")
            type_counts[bottleneck_type] = type_counts.get(bottleneck_type, 0) + 1

        return {
            "success": True,
            "data": {
                "timestamp": datetime.now().isoformat(),
                "active_bottlenecks": len(recommendations),
                "recommendations": recommendations,
                "severity_distribution": severity_counts,
                "type_distribution": type_counts,
                "summary": {
                    "critical_issues": severity_counts["critical"],
                    "high_priority": severity_counts["high"],
                    "total_issues": len(recommendations),
                },
            },
            "message": f"{len(recommendations)} performans önerisi bulundu",
        }

    except Exception as e:
        logger.error(f"Bottlenecks hatası: {e}")
        raise HTTPException(status_code=500, detail="Darboğaz verileri alınamadı")


@router.get("/system-info")
async def get_system_info():
    """
    Detaylı sistem bilgileri

    Returns:
        - hardware: Donanım bilgileri
        - software: Yazılım bilgileri
        - network: Network bilgileri
        - processes: Süreç bilgileri
    """
    try:
        import platform

        import psutil

        # CPU bilgileri
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else None,
            "current_frequency": psutil.cpu_freq().current
            if psutil.cpu_freq()
            else None,
            "cpu_usage_per_core": psutil.cpu_percent(percpu=True, interval=1),
        }

        # Memory bilgileri
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "percentage": memory.percent,
        }

        # Disk bilgileri
        disk_info = {}
        for partition in psutil.disk_partitions():
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                disk_info[partition.mountpoint] = {
                    "total_gb": partition_usage.total / (1024**3),
                    "used_gb": partition_usage.used / (1024**3),
                    "free_gb": partition_usage.free / (1024**3),
                    "percentage": (partition_usage.used / partition_usage.total) * 100,
                    "filesystem": partition.fstype,
                }
            except (PermissionError, OSError):
                continue

        # Network bilgileri
        network = psutil.net_io_counters()
        network_info = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv,
        }

        # Platform bilgileri
        platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

        return {
            "success": True,
            "data": {
                "timestamp": datetime.now().isoformat(),
                "hardware": {
                    "cpu": cpu_info,
                    "memory": memory_info,
                    "disk": disk_info,
                    "network": network_info,
                },
                "software": {
                    "platform": platform_info,
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                },
                "processes": {
                    "total_processes": len(psutil.pids()),
                    "running_processes": len(
                        [p for p in psutil.process_iter() if p.status() == "running"]
                    ),
                },
            },
            "message": "Sistem bilgileri başarıyla alındı",
        }

    except Exception as e:
        logger.error(f"System info hatası: {e}")
        raise HTTPException(status_code=500, detail="Sistem bilgileri alınamadı")


@router.post("/start-monitoring")
async def start_monitoring():
    """Monitoring sistemini başlat"""
    try:
        if production_health_monitor.monitoring_active:
            return {
                "success": True,
                "data": {"status": "already_running"},
                "message": "Monitoring zaten aktif",
            }

        await production_health_monitor.start_monitoring()

        return {
            "success": True,
            "data": {"status": "started", "timestamp": datetime.now().isoformat()},
            "message": "Monitoring başarıyla başlatıldı",
        }

    except Exception as e:
        logger.error(f"Start monitoring hatası: {e}")
        raise HTTPException(status_code=500, detail="Monitoring başlatılamadı")


@router.post("/stop-monitoring")
async def stop_monitoring():
    """Monitoring sistemini durdur"""
    try:
        if not production_health_monitor.monitoring_active:
            return {
                "success": True,
                "data": {"status": "already_stopped"},
                "message": "Monitoring zaten durmuş",
            }

        await production_health_monitor.stop_monitoring()

        return {
            "success": True,
            "data": {"status": "stopped", "timestamp": datetime.now().isoformat()},
            "message": "Monitoring başarıyla durduruldu",
        }

    except Exception as e:
        logger.error(f"Stop monitoring hatası: {e}")
        raise HTTPException(status_code=500, detail="Monitoring durdurulamadı")


def _get_component_status(value: float, thresholds: List[float]) -> str:
    """Component sağlık durumunu hesapla"""
    if len(thresholds) != 3:
        return "healthy"

    medium, high, critical = thresholds

    if value >= critical:
        return "critical"
    elif value >= high:
        return "unhealthy"
    elif value >= medium:
        return "degraded"
    else:
        return "healthy"
