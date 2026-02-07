"""
API Endpoint Sağlık Doğrulama Sistemi - Pydantic Modelleri

Bu modül, health check sistemi için gerekli tüm Pydantic modellerini tanımlar.
Python 3.13+ type hints kullanılarak yazılmıştır.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HealthStatus(str, Enum):
    """
    Endpoint sağlık durumu enum'u.
    
    Attributes:
        HEALTHY: Endpoint sağlıklı çalışıyor (P95 < 200ms, error rate < 1%)
        DEGRADED: Endpoint kısmi çalışma durumunda (P95 200-500ms)
        UNHEALTHY: Endpoint sağlıksız (P95 > 500ms veya error rate > 5%)
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CircuitState(str, Enum):
    """
    Circuit breaker durumu enum'u.
    
    Attributes:
        CLOSED: Circuit kapalı, normal işlem devam ediyor
        OPEN: Circuit açık, tüm istekler reddediliyor
        HALF_OPEN: Circuit yarı açık, test istekleri kabul ediliyor
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class EndpointMetadata(BaseModel):
    """
    Endpoint metadata bilgilerini tutan model.
    
    Attributes:
        path: Endpoint path'i (örn: /api/v1/users)
        method: HTTP method (GET, POST, PUT, DELETE, vb.)
        handler: Handler fonksiyon adı
        requires_auth: Authentication gerekip gerekmediği
        is_critical: Kritik endpoint olup olmadığı
        expected_status_codes: Beklenen başarılı status code'lar
    """
    path: str = Field(..., description="Endpoint path'i")
    method: str = Field(..., description="HTTP method")
    handler: str = Field(..., description="Handler fonksiyon adı")
    requires_auth: bool = Field(default=False, description="Authentication gereksinimi")
    is_critical: bool = Field(default=False, description="Kritik endpoint işareti")
    expected_status_codes: List[int] = Field(
        default=[200, 201, 204],
        description="Beklenen başarılı status code'lar"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "path": "/api/v1/users",
                "method": "GET",
                "handler": "get_users",
                "requires_auth": True,
                "is_critical": True,
                "expected_status_codes": [200]
            }
        }
    )


class HealthCheckResult(BaseModel):
    """
    Health check sonuç modeli.
    
    Attributes:
        endpoint: Kontrol edilen endpoint path'i
        status: Sağlık durumu
        response_time_ms: Yanıt süresi (milisaniye)
        status_code: HTTP status code
        error_message: Hata mesajı (varsa)
        timestamp: Kontrol zamanı
        circuit_state: Circuit breaker durumu
    """
    endpoint: str = Field(..., description="Endpoint path'i")
    status: HealthStatus = Field(..., description="Sağlık durumu")
    response_time_ms: float = Field(..., description="Yanıt süresi (ms)")
    status_code: int = Field(..., description="HTTP status code")
    error_message: Optional[str] = Field(None, description="Hata mesajı")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Kontrol zamanı")
    circuit_state: CircuitState = Field(default=CircuitState.CLOSED, description="Circuit breaker durumu")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "/api/v1/users",
                "status": "healthy",
                "response_time_ms": 45.2,
                "status_code": 200,
                "error_message": None,
                "timestamp": "2026-01-14T10:30:00Z",
                "circuit_state": "closed"
            }
        }
    )


class HealthScore(BaseModel):
    """
    Endpoint sağlık skoru modeli.
    
    Health score 0-100 arası bir değerdir ve şu ağırlıklarla hesaplanır:
    - Response Time: %40
    - Error Rate: %30
    - Uptime: %20
    - Dependency Health: %10
    
    Attributes:
        endpoint: Endpoint path'i
        score: Toplam sağlık skoru (0-100)
        response_time_score: Yanıt süresi skoru
        error_rate_score: Hata oranı skoru
        uptime_score: Uptime skoru
        dependency_score: Bağımlılık sağlık skoru
        timestamp: Hesaplama zamanı
    """
    endpoint: str = Field(..., description="Endpoint path'i")
    score: int = Field(..., ge=0, le=100, description="Toplam sağlık skoru (0-100)")
    response_time_score: float = Field(..., ge=0, le=100, description="Yanıt süresi skoru")
    error_rate_score: float = Field(..., ge=0, le=100, description="Hata oranı skoru")
    uptime_score: float = Field(..., ge=0, le=100, description="Uptime skoru")
    dependency_score: float = Field(..., ge=0, le=100, description="Bağımlılık skoru")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Hesaplama zamanı")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "/api/v1/users",
                "score": 95,
                "response_time_score": 100.0,
                "error_rate_score": 95.0,
                "uptime_score": 99.9,
                "dependency_score": 85.0,
                "timestamp": "2026-01-14T10:30:00Z"
            }
        }
    )


class SLATarget(BaseModel):
    """
    SLA hedef değerleri modeli.

    Attributes:
        target_uptime: Hedef uptime yüzdesi (varsayılan %99)
        target_response_time_ms: Hedef P95 yanıt süresi (ms)
        target_error_rate: Hedef maksimum hata oranı (%)
    """
    target_uptime: float = Field(default=99.0, ge=0.0, le=100.0, description="Hedef uptime yüzdesi")
    target_response_time_ms: float = Field(default=200.0, ge=0.0, description="Hedef P95 yanıt süresi (ms)")
    target_error_rate: float = Field(default=1.0, ge=0.0, le=100.0, description="Hedef maksimum hata oranı (%)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "target_uptime": 99.9,
                "target_response_time_ms": 200.0,
                "target_error_rate": 1.0
            }
        }
    )


class SLAComplianceReport(BaseModel):
    """
    SLA uyumluluk raporu modeli.

    Attributes:
        endpoint: Endpoint path'i
        uptime_percentage: Gerçekleşen uptime yüzdesi
        p95_response_time_ms: Gerçekleşen P95 yanıt süresi
        error_rate: Gerçekleşen hata oranı
        is_compliant: SLA'ya uygunluk durumu
    """
    endpoint: str = Field(..., description="Endpoint path'i")
    uptime_percentage: float = Field(..., ge=0.0, le=100.0, description="Gerçekleşen uptime yüzdesi")
    p95_response_time_ms: float = Field(default=0.0, ge=0.0, description="Gerçekleşen P95 yanıt süresi")
    error_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="Gerçekleşen hata oranı")
    is_compliant: bool = Field(default=True, description="SLA uygunluk durumu")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "/api/v1/users",
                "uptime_percentage": 99.95,
                "p95_response_time_ms": 150.0,
                "error_rate": 0.5,
                "is_compliant": True
            }
        }
    )


class SLAMetrics(BaseModel):
    """
    SLA metrikleri modeli.

    Attributes:
        endpoint: Endpoint path'i
        p50_ms: 50. persentil yanıt süresi (ms)
        p95_ms: 95. persentil yanıt süresi (ms)
        p99_ms: 99. persentil yanıt süresi (ms)
        error_rate: Hata oranı (0.0-1.0)
        uptime_percentage: Uptime yüzdesi (0.0-100.0)
        sla_compliant: SLA'ya uygunluk durumu
    """
    endpoint: str = Field(..., description="Endpoint path'i")
    p50_ms: float = Field(..., description="P50 yanıt süresi (ms)")
    p95_ms: float = Field(..., description="P95 yanıt süresi (ms)")
    p99_ms: float = Field(..., description="P99 yanıt süresi (ms)")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Hata oranı")
    uptime_percentage: float = Field(..., ge=0.0, le=100.0, description="Uptime yüzdesi")
    sla_compliant: bool = Field(..., description="SLA uygunluk durumu")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "/api/v1/users",
                "p50_ms": 45.2,
                "p95_ms": 180.5,
                "p99_ms": 450.0,
                "error_rate": 0.005,
                "uptime_percentage": 99.95,
                "sla_compliant": True
            }
        }
    )
