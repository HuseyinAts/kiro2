# Design Document - API Endpoint Sağlık Doğrulama Sistemi

## Overview

API Endpoint Sağlık Doğrulama Sistemi, tüm FastAPI endpoint'lerinin sağlık durumunu sürekli izleyen ve doğrulayan sistemdir. Boris Cherny'nin verification feedback loops prensibi uygulanarak API güvenilirliği %99.9'a çıkarılır ve downtime %95 azaltılır.

**Temel Özellikler:**
- Otomatik endpoint discovery
- Sürekli health check (30 saniye interval)
- Response time SLA monitoring (P95 < 200ms)
- Circuit breaker pattern
- Database ve Redis health monitoring
- PostDeploy verification hooks
- Real-time health dashboard
- Threshold-based alerting

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                           │
│              (All Registered Endpoints)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Endpoint Discovery System                           │
│    (Scans FastAPI routes, extracts metadata)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Health Check Scheduler                              │
│         (APScheduler - runs every 30 seconds)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Endpoint    │  │  Database    │  │   Redis      │
│Health Checker│  │Health Checker│  │Health Checker│
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              SLA Monitor + Circuit Breaker                       │
│    (P95 < 200ms check, 5 failures → OPEN circuit)               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Health Score Calculator                             │
│  (Response Time: 40%, Error Rate: 30%, Uptime: 20%, Deps: 10%)  │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    Redis     │  │  PostgreSQL  │  │   Alerting   │
│   (Cache)    │  │  (History)   │  │(Slack/Email) │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Component Architecture

```
backend/
├── app/
│   ├── health/
│   │   ├── __init__.py
│   │   ├── discovery.py              # Endpoint discovery
│   │   ├── checker.py                # Health check logic
│   │   ├── circuit_breaker.py        # Circuit breaker pattern
│   │   ├── sla_monitor.py            # SLA monitoring
│   │   ├── score_calculator.py       # Health score calculation
│   │   └── scheduler.py              # APScheduler setup
│   ├── health/dependencies/
│   │   ├── __init__.py
│   │   ├── database_health.py        # PostgreSQL health
│   │   └── redis_health.py           # Redis health
│   ├── health/hooks/
│   │   ├── __init__.py
│   │   └── postdeploy_hook.py        # PostDeploy verification
│   ├── health/alerting/
│   │   ├── __init__.py
│   │   ├── alert_manager.py          # Alert logic
│   │   └── notifiers.py              # Slack, Email, SMS
│   └── api/v1/
│       └── health_dashboard.py       # Dashboard API
├── tests/
│   └── health/
│       ├── test_discovery.py
│       ├── test_checker.py
│       ├── test_circuit_breaker.py
│       └── test_sla_monitor.py
└── requirements_health.txt
```

## Data Models

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class EndpointMetadata(BaseModel):
    path: str
    method: str
    handler: str
    requires_auth: bool
    is_critical: bool
    expected_status_codes: List[int] = [200, 201, 204]

class HealthCheckResult(BaseModel):
    endpoint: str
    status: HealthStatus
    response_time_ms: float
    status_code: int
    error_message: Optional[str] = None
    timestamp: datetime
    circuit_state: CircuitState

class HealthScore(BaseModel):
    endpoint: str
    score: int = Field(ge=0, le=100)
    response_time_score: float
    error_rate_score: float
    uptime_score: float
    dependency_score: float
    timestamp: datetime

class SLAMetrics(BaseModel):
    endpoint: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    error_rate: float
    uptime_percentage: float
    sla_compliant: bool
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: Endpoint Discovery Completeness
*For any* registered FastAPI endpoint, *it SHALL be discovered and monitored.*

**Validates: Requirements REQ-1.1, REQ-1.2, REQ-1.3**

### Property 2: Circuit Breaker State Transition
*For any* endpoint with 5 consecutive failures, *circuit SHALL transition to OPEN state.*

**Validates: Requirements REQ-4.1, REQ-4.2**

### Property 3: SLA Compliance Detection
*For any* endpoint with P95 > 200ms, *it SHALL be marked as degraded or unhealthy.*

**Validates: Requirements REQ-3.2, REQ-3.3, REQ-3.4**

### Property 4: Health Score Bounds
*For any* endpoint, *health score SHALL be between 0 and 100.*

**Validates: Requirements REQ-8.1**

### Property 5: Alert Triggering
*For any* critical endpoint failure, *alert SHALL be sent within 5 seconds.*

**Validates: Requirements REQ-2.6, REQ-8.4**

## Testing Strategy

### Unit Tests
- Test endpoint discovery logic
- Test circuit breaker state transitions
- Test SLA threshold calculations
- Test health score formula

### Property-Based Tests
- Generate random endpoint responses
- Verify circuit breaker behavior
- Verify SLA compliance detection
- Verify health score calculation

### Integration Tests
- Test full health check cycle
- Test PostDeploy hook execution
- Test alerting system
- Test dashboard API

**Test Configuration**: Minimum 100 iterations per property test

## Health Score Calculation

```python
def calculate_health_score(
    response_time_p95: float,
    error_rate: float,
    uptime: float,
    dependency_health: float
) -> int:
    # Response Time Score (40%)
    if response_time_p95 < 200:
        rt_score = 100
    elif response_time_p95 < 500:
        rt_score = 70
    else:
        rt_score = 30
    
    # Error Rate Score (30%)
    if error_rate < 0.01:
        er_score = 100
    elif error_rate < 0.05:
        er_score = 70
    else:
        er_score = 30
    
    # Uptime Score (20%)
    uptime_score = uptime * 100
    
    # Dependency Score (10%)
    dep_score = dependency_health * 100
    
    # Weighted average
    total_score = (
        rt_score * 0.4 +
        er_score * 0.3 +
        uptime_score * 0.2 +
        dep_score * 0.1
    )
    
    return int(total_score)
```

## Circuit Breaker State Machine

```
CLOSED (Normal Operation)
   │
   │ 5 consecutive failures
   ▼
OPEN (Reject all requests)
   │
   │ 30 seconds timeout
   ▼
HALF_OPEN (Test with 1 request)
   │
   ├─ Success → CLOSED
   └─ Failure → OPEN
```

## Monitoring and Alerting

### Alert Levels
- **INFO**: Health score 70-100
- **WARNING**: Health score 50-69
- **CRITICAL**: Health score 0-49

### Alert Channels
- Slack webhook for team notifications
- Email for critical alerts
- SMS for on-call engineers (critical only)

### Alert Throttling
- Max 1 alert per endpoint per 5 minutes
- Aggregate multiple endpoint failures into single alert
