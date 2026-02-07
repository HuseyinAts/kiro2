"""
API Endpoint Sağlık Doğrulama Sistemi

Bu paket, FastAPI endpoint'lerinin sağlık durumunu sürekli izleyen
ve doğrulayan sistemi içerir.

Modules:
    - models: Pydantic data models
    - discovery: Endpoint otomatik keşif
    - checker: Health check işlemleri
    - sla_monitor: SLA monitoring
    - circuit_breaker: Circuit breaker pattern
    - score_calculator: Health score hesaplama
    - scheduler: Periyodik job scheduling
    - dashboard_api: Dashboard API endpoints
"""

from .discovery import EndpointDiscovery
from .checker import HealthChecker
from .sla_monitor import SLAMonitor
from .circuit_breaker import CircuitBreaker
from .score_calculator import HealthScoreCalculator
from .scheduler import HealthCheckScheduler, get_scheduler
from .models import (
    CircuitState,
    EndpointMetadata,
    HealthCheckResult,
    HealthScore,
    HealthStatus,
    SLAMetrics,
)

__all__ = [
    # Models
    "CircuitState",
    "EndpointMetadata",
    "HealthCheckResult",
    "HealthScore",
    "HealthStatus",
    "SLAMetrics",
    # Services
    "EndpointDiscovery",
    "HealthChecker",
    "SLAMonitor",
    "CircuitBreaker",
    "HealthScoreCalculator",
    "HealthCheckScheduler",
    "get_scheduler",
]
