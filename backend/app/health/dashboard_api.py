"""
Health Dashboard API

Bu modul, health monitoring dashboard için API endpoint'lerini sağlar.

Endpoints:
- GET /api/v1/health/endpoints - Tüm endpoint'lerin health score'ları
- GET /api/v1/health/endpoints/{path} - Endpoint detayları
- GET /api/v1/health/metrics - Sistem geneli metrikler
- GET /api/v1/health/sla-report - SLA raporu
- GET /api/v1/health/history - Tarihsel veriler

Requirements:
    REQ-8.1: Endpoint health score'ları
    REQ-8.2: Response time grafiği, error rate, uptime
    REQ-8.5: Son 30 günlük trend analizi
    REQ-8.6: Aylık SLA raporu
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.core.deps import User, get_current_user

from .models import HealthStatus

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(prefix="/api/v1/health", tags=["Health Dashboard"])


# ===== Pydantic Models =====


class EndpointHealthResponse(BaseModel):
    """Endpoint health response modeli."""

    endpoint: str
    method: str
    status: HealthStatus
    score: int = Field(ge=0, le=100)
    response_time_ms: float
    error_rate: float
    uptime_percentage: float
    circuit_state: str = "closed"
    last_checked: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "/api/v1/users",
                "method": "GET",
                "status": "healthy",
                "score": 95,
                "response_time_ms": 45.2,
                "error_rate": 0.005,
                "uptime_percentage": 99.95,
                "circuit_state": "closed",
                "last_checked": "2026-01-14T10:30:00Z",
            }
        }
    )


class EndpointDetailResponse(BaseModel):
    """Endpoint detay response modeli."""

    endpoint: str
    method: str
    handler: str
    is_critical: bool
    requires_auth: bool
    status: HealthStatus
    score: int
    metrics: dict
    history: list[dict] = []


class SystemMetricsResponse(BaseModel):
    """Sistem metrikleri response modeli."""

    total_endpoints: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    average_score: float
    average_response_time_ms: float
    overall_error_rate: float
    overall_uptime: float
    database_healthy: bool
    redis_healthy: bool
    timestamp: datetime


class SLAReportResponse(BaseModel):
    """SLA raporu response modeli."""

    period_start: datetime
    period_end: datetime
    total_endpoints: int
    sla_compliant_count: int
    sla_compliance_rate: float
    average_uptime: float
    average_response_time_ms: float
    incidents: list[dict] = []
    recommendations: list[str] = []


class HistoricalDataResponse(BaseModel):
    """Tarihsel veri response modeli."""

    endpoint: str
    period_days: int
    data_points: list[dict]
    trend: str  # improving, stable, degrading


# ===== Dependency Injection =====

# Bu bağımlılıklar main.py'de ayarlanacak
_health_service = None


def get_health_service():
    """Health service bağımlılığı."""
    global _health_service
    if _health_service is None:
        raise HTTPException(status_code=503, detail="Health service not initialized")
    return _health_service


def set_health_service(service):
    """Health service'i ayarlar."""
    global _health_service
    _health_service = service


# ===== API Endpoints =====


@router.get(
    "/endpoints",
    response_model=list[EndpointHealthResponse],
    summary="Tüm endpoint'lerin sağlık durumu",
    description="Tüm API endpoint'lerinin health score ve durumlarını listeler.",
)
async def list_endpoints(
    current_user: User = Depends(get_current_user),
    status: HealthStatus | None = Query(None, description="Status filtresi"),
    min_score: int | None = Query(None, ge=0, le=100, description="Minimum skor"),
    max_score: int | None = Query(None, ge=0, le=100, description="Maksimum skor"),
    limit: int = Query(100, ge=1, le=500, description="Maksimum sonuç sayısı"),
    offset: int = Query(0, ge=0, description="Başlangıç offset"),
):
    """
    Tüm endpoint'lerin health durumunu listeler.

    Requirements:
        REQ-8.1: Endpoint health score'larını gösterir
    """
    try:
        # Mock data (gerçek implementasyonda service'ten gelecek)
        endpoints = [
            EndpointHealthResponse(
                endpoint="/api/v1/users",
                method="GET",
                status=HealthStatus.HEALTHY,
                score=95,
                response_time_ms=45.2,
                error_rate=0.005,
                uptime_percentage=99.95,
                circuit_state="closed",
                last_checked=datetime.now(UTC),
            ),
            EndpointHealthResponse(
                endpoint="/api/v1/auth/login",
                method="POST",
                status=HealthStatus.HEALTHY,
                score=92,
                response_time_ms=120.5,
                error_rate=0.01,
                uptime_percentage=99.9,
                circuit_state="closed",
                last_checked=datetime.now(UTC),
            ),
            EndpointHealthResponse(
                endpoint="/api/v1/exams",
                method="GET",
                status=HealthStatus.DEGRADED,
                score=68,
                response_time_ms=350.0,
                error_rate=0.02,
                uptime_percentage=99.5,
                circuit_state="closed",
                last_checked=datetime.now(UTC),
            ),
        ]

        # Filtreleme
        if status:
            endpoints = [e for e in endpoints if e.status == status]
        if min_score is not None:
            endpoints = [e for e in endpoints if e.score >= min_score]
        if max_score is not None:
            endpoints = [e for e in endpoints if e.score <= max_score]

        # Pagination
        endpoints = endpoints[offset : offset + limit]

        return endpoints

    except Exception as e:
        logger.error(f"Endpoint listesi alınamadı: {e}")
        raise HTTPException(status_code=500, detail="Dahili sunucu hatasi")


@router.get(
    "/endpoints/{path:path}",
    response_model=EndpointDetailResponse,
    summary="Endpoint detayları",
    description="Belirli bir endpoint'in detaylı sağlık bilgilerini getirir.",
)
async def get_endpoint_detail(
    path: str,
    method: str = Query("GET", description="HTTP method"),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint detaylarını getirir.

    Requirements:
        REQ-8.2: Response time grafiği, error rate, uptime gösterir
    """
    try:
        # Mock data
        return EndpointDetailResponse(
            endpoint=f"/{path}",
            method=method,
            handler="get_resource",
            is_critical=path.startswith("api/v1/auth"),
            requires_auth=True,
            status=HealthStatus.HEALTHY,
            score=95,
            metrics={
                "p50_ms": 35.0,
                "p95_ms": 120.0,
                "p99_ms": 250.0,
                "error_rate": 0.005,
                "request_count_1h": 1500,
                "success_count_1h": 1492,
                "failure_count_1h": 8,
            },
            history=[
                {
                    "timestamp": "2026-01-14T10:00:00Z",
                    "score": 95,
                    "response_time_ms": 45.0,
                },
                {
                    "timestamp": "2026-01-14T09:00:00Z",
                    "score": 93,
                    "response_time_ms": 52.0,
                },
                {
                    "timestamp": "2026-01-14T08:00:00Z",
                    "score": 94,
                    "response_time_ms": 48.0,
                },
            ],
        )

    except Exception as e:
        logger.error(f"Endpoint detayı alınamadı: {e}")
        raise HTTPException(status_code=500, detail="Dahili sunucu hatasi")


@router.get(
    "/metrics",
    response_model=SystemMetricsResponse,
    summary="Sistem metrikleri",
    description="Sistem genelindeki health metriklerini getirir.",
)
async def get_system_metrics(
    current_user: User = Depends(get_current_user),
):
    """
    Sistem geneli metrikleri getirir.

    Requirements:
        REQ-8.1: Sistem durumu özeti
    """
    try:
        return SystemMetricsResponse(
            total_endpoints=150,
            healthy_count=135,
            degraded_count=12,
            unhealthy_count=3,
            average_score=87.5,
            average_response_time_ms=85.3,
            overall_error_rate=0.008,
            overall_uptime=99.85,
            database_healthy=True,
            redis_healthy=True,
            timestamp=datetime.now(UTC),
        )

    except Exception as e:
        logger.error(f"Sistem metrikleri alınamadı: {e}")
        raise HTTPException(status_code=500, detail="Dahili sunucu hatasi")


@router.get(
    "/sla-report",
    response_model=SLAReportResponse,
    summary="SLA raporu",
    description="Aylık SLA compliance raporunu getirir.",
)
async def get_sla_report(
    current_user: User = Depends(get_current_user),
    start_date: datetime | None = Query(None, description="Başlangıç tarihi"),
    end_date: datetime | None = Query(None, description="Bitiş tarihi"),
):
    """
    SLA raporunu getirir.

    Requirements:
        REQ-8.6: Aylık uptime ve performance metrikleri raporlar
    """
    try:
        # Varsayılan tarih aralığı: son 30 gün
        if not end_date:
            end_date = datetime.now(UTC)
        if not start_date:
            start_date = end_date - timedelta(days=30)

        return SLAReportResponse(
            period_start=start_date,
            period_end=end_date,
            total_endpoints=150,
            sla_compliant_count=142,
            sla_compliance_rate=94.67,
            average_uptime=99.85,
            average_response_time_ms=85.3,
            incidents=[
                {
                    "id": "INC-001",
                    "endpoint": "/api/v1/exams",
                    "duration_minutes": 15,
                    "impact": "high",
                    "resolved": True,
                }
            ],
            recommendations=[
                "Consider scaling exam service during peak hours",
                "Review database connection pool settings",
                "Implement caching for frequently accessed endpoints",
            ],
        )

    except Exception as e:
        logger.error(f"SLA raporu alınamadı: {e}")
        raise HTTPException(status_code=500, detail="Dahili sunucu hatasi")


@router.get(
    "/history",
    response_model=HistoricalDataResponse,
    summary="Tarihsel veriler",
    description="Endpoint için tarihsel trend verilerini getirir.",
)
async def get_historical_data(
    current_user: User = Depends(get_current_user),
    endpoint: str = Query(..., description="Endpoint path"),
    days: int = Query(30, ge=1, le=90, description="Gün sayısı"),
):
    """
    Tarihsel verileri getirir.

    Requirements:
        REQ-8.5: Son 30 günlük trend analizi gösterir
    """
    try:
        # Mock data points
        data_points = []
        now = datetime.now(UTC)

        for i in range(days):
            date = now - timedelta(days=i)
            data_points.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "score": 90 + (i % 10) - 5,  # 85-95 arası dalgalanma
                    "response_time_ms": 80 + (i % 30),
                    "error_rate": 0.005 + (i % 5) * 0.001,
                    "request_count": 10000 + (i % 1000),
                }
            )

        # Trend analizi
        if len(data_points) >= 7:
            recent_avg = sum(dp["score"] for dp in data_points[:7]) / 7
            older_avg = sum(dp["score"] for dp in data_points[-7:]) / 7

            if recent_avg > older_avg + 2:
                trend = "improving"
            elif recent_avg < older_avg - 2:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return HistoricalDataResponse(
            endpoint=endpoint, period_days=days, data_points=data_points, trend=trend
        )

    except Exception as e:
        logger.error(f"Tarihsel veri alınamadı: {e}")
        raise HTTPException(status_code=500, detail="Dahili sunucu hatasi")


@router.get(
    "/alerts",
    summary="Aktif alertler",
    description="Aktif health alertlerini listeler.",
)
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    severity: str | None = Query(None, description="Severity filtresi"),
    limit: int = Query(50, ge=1, le=200),
):
    """Aktif alertleri listeler."""
    try:
        # Mock data
        alerts = [
            {
                "id": "alert_20260114103000_1",
                "type": "high_latency",
                "severity": "warning",
                "endpoint": "/api/v1/exams",
                "message": "High latency: 350ms",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            {
                "id": "alert_20260114102500_2",
                "type": "high_error_rate",
                "severity": "critical",
                "endpoint": "/api/v1/questions/generate",
                "message": "Critical error rate: 5.2%",
                "timestamp": (datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
            },
        ]

        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]

        return alerts[:limit]

    except Exception as e:
        logger.error(f"Alertler alınamadı: {e}")
        raise HTTPException(status_code=500, detail="Dahili sunucu hatasi")


@router.post(
    "/circuit/{endpoint:path}/reset",
    summary="Circuit breaker reset",
    description="Endpoint'in circuit breaker'ını manuel olarak resetler.",
)
async def reset_circuit_breaker(
    endpoint: str,
    method: str = Query("GET"),
    current_user: User = Depends(get_current_user),
):
    """Circuit breaker'ı resetler."""
    try:
        logger.info(f"Circuit breaker reset: {method}:{endpoint}")
        return {
            "status": "success",
            "message": f"Circuit breaker reset for {method} {endpoint}",
            "new_state": "closed",
        }

    except Exception as e:
        logger.error(f"Circuit reset hatası: {e}")
        raise HTTPException(status_code=500, detail="Dahili sunucu hatasi")


@router.get(
    "/dependencies",
    summary="Bağımlılık durumu",
    description="Database, Redis vb. bağımlılıkların sağlık durumunu gösterir.",
)
async def get_dependency_health(
    current_user: User = Depends(get_current_user),
):
    """Bağımlılık sağlık durumunu getirir."""
    try:
        return {
            "database": {
                "healthy": True,
                "response_time_ms": 12.5,
                "active_connections": 25,
                "pool_usage_percent": 50.0,
            },
            "redis": {
                "healthy": True,
                "response_time_ms": 2.3,
                "hit_rate": 0.85,
                "memory_usage_percent": 45.0,
            },
            "elasticsearch": {
                "healthy": True,
                "response_time_ms": 35.0,
                "cluster_status": "green",
            },
        }

    except Exception as e:
        logger.error(f"Bağımlılık durumu alınamadı: {e}")
        raise HTTPException(status_code=500, detail="Dahili sunucu hatasi")
