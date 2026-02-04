# Health Check Service

## Overview

HealthCheckService, Learning Path Video Yükleme Sorunu Çözümü projesinin bir parçası olarak geliştirilmiş, sistem sağlık durumunu izleyen ve raporlayan bir servistir.

**Task:** 4. HealthCheckService Servisini Oluştur  
**Requirements:** 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 4.12

## Features

### 1. Multi-Component Health Checks
- **YouTube API**: API key varlığı ve konfigürasyon kontrolü
- **Database**: PostgreSQL/SQLite bağlantı ve query testi
- **Redis Cache**: Ping testi ve bağlantı durumu

### 2. Health Status Levels
- **HEALTHY**: Tüm bileşenler normal çalışıyor
- **DEGRADED**: Bazı bileşenler sınırlı çalışıyor (örn: test mode)
- **UNHEALTHY**: Kritik bileşenler çalışmıyor

### 3. Detailed Metrics
- Response time (ms) her bileşen için
- Error messages ve detaylar
- System metrics (uptime, request counts, cache hit rate)
- Component-specific details (connection pool size, memory usage, etc.)

### 4. Performance
- Health check 500ms içinde tamamlanır (Requirement 4.2)
- Lazy initialization ile hızlı başlatma
- Metrics caching (5 dakika) ile performans optimizasyonu

## Usage

### Basic Usage

```python
from services.health_check_service import get_health_check_service

# Get service instance (singleton)
health_service = get_health_check_service()

# Perform health check
system_health = await health_service.check_health()

# Check overall status
if system_health.overall_status == HealthStatus.HEALTHY:
    print("✅ Sistem sağlıklı")
elif system_health.overall_status == HealthStatus.DEGRADED:
    print("⚠️ Sistem kısıtlı çalışıyor")
else:
    print("❌ Sistem sağlıksız")

# Get component details
for component in system_health.components:
    print(f"{component.name}: {component.status.value} ({component.response_time_ms}ms)")
    if component.error_message:
        print(f"  Error: {component.error_message}")

# Get metrics
print(f"Total requests (24h): {system_health.metrics['total_requests_24h']}")
print(f"Cache hit rate: {system_health.metrics['cache_hit_rate_1h']}%")
```

### API Integration

```python
from fastapi import APIRouter
from services.health_check_service import get_health_check_service

router = APIRouter()

@router.get("/api/youtube/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        - overall_status: healthy/degraded/unhealthy
        - components: List of component health details
        - metrics: System metrics
        - timestamp: Check timestamp
    """
    health_service = get_health_check_service()
    system_health = await health_service.check_health()
    
    return system_health.to_dict()
```

### Custom Initialization

```python
from services.health_check_service import HealthCheckService
from services.real_youtube_api import RealYouTubeAPI
from core.cache_service import CacheService

# Custom initialization with specific dependencies
youtube_api = RealYouTubeAPI()
cache_service = CacheService(redis_url="redis://custom:6379")

health_service = HealthCheckService(
    youtube_api=youtube_api,
    cache_service=cache_service
)

system_health = await health_service.check_health()
```

## Architecture

### Class Diagram

```
┌─────────────────────────────────────────┐
│        HealthCheckService               │
├─────────────────────────────────────────┤
│ - _youtube_api: RealYouTubeAPI         │
│ - _cache_service: CacheService          │
│ - _metrics_cache: Dict                  │
│ - _last_metrics_update: datetime        │
├─────────────────────────────────────────┤
│ + check_health() -> SystemHealth        │
│ - _check_youtube_api() -> ComponentHealth│
│ - _check_database() -> ComponentHealth  │
│ - _check_cache() -> ComponentHealth     │
│ - _determine_overall_status()           │
│ - _collect_metrics() -> Dict            │
└─────────────────────────────────────────┘
           │
           │ uses
           ▼
┌─────────────────────────────────────────┐
│         ComponentHealth                 │
├─────────────────────────────────────────┤
│ + name: str                             │
│ + status: HealthStatus                  │
│ + response_time_ms: float               │
│ + error_message: Optional[str]          │
│ + last_check: Optional[datetime]        │
│ + details: Optional[Dict]               │
├─────────────────────────────────────────┤
│ + to_dict() -> Dict                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          SystemHealth                   │
├─────────────────────────────────────────┤
│ + overall_status: HealthStatus          │
│ + components: List[ComponentHealth]     │
│ + metrics: Dict[str, Any]               │
│ + timestamp: datetime                   │
├─────────────────────────────────────────┤
│ + to_dict() -> Dict                     │
└─────────────────────────────────────────┘
```

### Health Check Flow

```
1. check_health() called
   │
   ├─> 2. _check_youtube_api()
   │   ├─> Check API key configuration
   │   ├─> Determine status (HEALTHY/DEGRADED/UNHEALTHY)
   │   └─> Return ComponentHealth
   │
   ├─> 3. _check_database()
   │   ├─> Test database connection
   │   ├─> Execute simple query (SELECT 1)
   │   ├─> Get connection pool info
   │   └─> Return ComponentHealth
   │
   ├─> 4. _check_cache()
   │   ├─> Ping Redis
   │   ├─> Get Redis info (memory, clients, uptime)
   │   └─> Return ComponentHealth
   │
   ├─> 5. _determine_overall_status()
   │   ├─> Check for UNHEALTHY components
   │   ├─> Check for DEGRADED components
   │   └─> Return overall HealthStatus
   │
   ├─> 6. _collect_metrics()
   │   ├─> Check metrics cache (5 min TTL)
   │   ├─> Fetch fresh metrics if needed
   │   └─> Return metrics dict
   │
   └─> 7. Return SystemHealth
       ├─> overall_status
       ├─> components (3 items)
       ├─> metrics
       └─> timestamp
```

## Data Models

### HealthStatus (Enum)

```python
class HealthStatus(Enum):
    HEALTHY = "healthy"      # All systems operational
    DEGRADED = "degraded"    # Some systems limited
    UNHEALTHY = "unhealthy"  # Critical systems down
```

### ComponentHealth

```python
@dataclass
class ComponentHealth:
    name: str                           # Component name
    status: HealthStatus                # Health status
    response_time_ms: float             # Response time in milliseconds
    error_message: Optional[str]        # Error message if unhealthy
    last_check: Optional[datetime]      # Last check timestamp
    details: Optional[Dict[str, Any]]   # Additional details
```

**Example:**
```json
{
  "name": "YouTube API",
  "status": "healthy",
  "response_time_ms": 15.5,
  "error_message": null,
  "last_check": "2025-01-29T12:00:00",
  "details": {
    "api_key_configured": true,
    "test_mode": false
  }
}
```

### SystemHealth

```python
@dataclass
class SystemHealth:
    overall_status: HealthStatus           # Overall system status
    components: List[ComponentHealth]      # Component health list
    metrics: Dict[str, Any]                # System metrics
    timestamp: datetime                    # Check timestamp
```

**Example:**
```json
{
  "overall_status": "healthy",
  "components": [
    {
      "name": "YouTube API",
      "status": "healthy",
      "response_time_ms": 15.5,
      "details": {"api_key_configured": true}
    },
    {
      "name": "Database",
      "status": "healthy",
      "response_time_ms": 25.3,
      "details": {"database_type": "PostgreSQL"}
    },
    {
      "name": "Redis Cache",
      "status": "healthy",
      "response_time_ms": 8.2,
      "details": {"connected_clients": 5}
    }
  ],
  "metrics": {
    "timestamp": "2025-01-29T12:00:00",
    "uptime_seconds": 3600,
    "total_requests_24h": 1250,
    "success_rate_24h": 99.5,
    "avg_response_time_1h": 2.3,
    "cache_hit_rate_1h": 85.0,
    "error_rate_1h": 0.5
  },
  "timestamp": "2025-01-29T12:00:00"
}
```

## Component Details

### YouTube API Health Check

**Checks:**
- API key configuration
- Test mode detection

**Status Logic:**
- HEALTHY: Valid API key configured
- DEGRADED: Test mode (test-youtube-api-key)
- UNHEALTHY: Exception during check

**Details:**
- `api_key_configured`: boolean
- `test_mode`: boolean

### Database Health Check

**Checks:**
- Database manager initialization
- Connection test
- Simple query execution (SELECT 1)

**Status Logic:**
- HEALTHY: Query successful
- DEGRADED: Database manager not initialized
- UNHEALTHY: Connection or query failed

**Details:**
- `connection_pool_size`: int or null
- `database_type`: "PostgreSQL" or "SQLite"

### Redis Cache Health Check

**Checks:**
- Redis ping
- Redis info (memory, clients, uptime)

**Status Logic:**
- HEALTHY: Ping successful
- UNHEALTHY: Connection failed

**Details:**
- `connected_clients`: int
- `used_memory_human`: string (e.g., "1.5M")
- `uptime_in_seconds`: int

## Metrics

### Collected Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| `timestamp` | Metrics collection time | System |
| `uptime_seconds` | System uptime | psutil |
| `total_requests_24h` | Total requests in last 24h | Cache |
| `success_rate_24h` | Success rate percentage | Cache |
| `avg_response_time_1h` | Average response time (ms) | Cache |
| `cache_hit_rate_1h` | Cache hit rate percentage | Cache |
| `error_rate_1h` | Error rate percentage | Cache |

### Metrics Caching

Metrics are cached for 5 minutes to reduce overhead:

```python
# Metrics cache logic
if (
    self._last_metrics_update is None or
    (now - self._last_metrics_update).total_seconds() > 300
):
    # Fetch fresh metrics
    self._metrics_cache = await self._fetch_fresh_metrics()
    self._last_metrics_update = now

return self._metrics_cache
```

## Testing

### Unit Tests

```bash
# Run all health check tests
pytest tests/services/test_health_check_service_simple.py -v

# Run specific test
pytest tests/services/test_health_check_service_simple.py::TestComponentHealth::test_component_health_creation -v
```

### Test Coverage

- ✅ ComponentHealth creation and serialization
- ✅ SystemHealth creation and serialization
- ✅ HealthStatus enum values
- ✅ Overall status determination logic
- ✅ Singleton pattern
- ✅ Lazy initialization
- ✅ Uptime calculation

### Integration Testing

```python
@pytest.mark.asyncio
async def test_health_check_integration():
    """Integration test with real dependencies"""
    health_service = get_health_check_service()
    system_health = await health_service.check_health()
    
    assert system_health.overall_status in [
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthStatus.UNHEALTHY
    ]
    assert len(system_health.components) == 3
    assert "YouTube API" in [c.name for c in system_health.components]
    assert "Database" in [c.name for c in system_health.components]
    assert "Redis Cache" in [c.name for c in system_health.components]
```

## Error Handling

### Graceful Degradation

Service handles errors gracefully and continues checking other components:

```python
# If YouTube API fails, still check Database and Cache
try:
    youtube_health = await self._check_youtube_api()
except Exception as e:
    youtube_health = ComponentHealth(
        name="YouTube API",
        status=HealthStatus.UNHEALTHY,
        error_message=str(e)
    )

# Continue with other checks...
```

### Error Logging

All errors are logged with context:

```python
logger.error(f"Database sağlık kontrolü başarısız: {str(e)}")
```

## Performance Considerations

### Response Time Target

- **Target:** < 500ms (Requirement 4.2)
- **Typical:** 50-200ms
- **Components:**
  - YouTube API check: ~10-50ms
  - Database check: ~20-100ms
  - Cache check: ~5-50ms
  - Metrics collection: ~10-50ms (cached)

### Optimization Strategies

1. **Lazy Initialization**: Dependencies initialized only when needed
2. **Metrics Caching**: 5-minute cache reduces overhead
3. **Parallel Checks**: Could be parallelized with asyncio.gather()
4. **Simple Queries**: Minimal database queries (SELECT 1)
5. **Singleton Pattern**: Single instance reused

## Monitoring Integration

### Prometheus Metrics

```python
# Example Prometheus integration
from prometheus_client import Gauge

health_status_gauge = Gauge(
    'system_health_status',
    'System health status (0=unhealthy, 1=degraded, 2=healthy)'
)

system_health = await health_service.check_health()
status_value = {
    HealthStatus.UNHEALTHY: 0,
    HealthStatus.DEGRADED: 1,
    HealthStatus.HEALTHY: 2
}[system_health.overall_status]

health_status_gauge.set(status_value)
```

### Alerting

```yaml
# Example alert rules
- alert: SystemUnhealthy
  expr: system_health_status == 0
  for: 5m
  annotations:
    summary: "System is unhealthy"
    
- alert: SystemDegraded
  expr: system_health_status == 1
  for: 10m
  annotations:
    summary: "System is degraded"
```

## Future Enhancements

1. **Parallel Health Checks**: Use asyncio.gather() for faster checks
2. **Historical Data**: Store health check history
3. **Trend Analysis**: Detect degradation trends
4. **Auto-Recovery**: Automatic restart of failed components
5. **Custom Checks**: Plugin system for custom health checks
6. **Detailed Diagnostics**: More granular component checks

## Related Documentation

- [Video Recommendation Service](README_video_recommendation_service.md)
- [Turkish Content Filter](README_turkish_content_filter.md)
- [Video Recommendation Monitoring](README_video_recommendation_monitoring.md)
- [Requirements Document](../../.kiro/specs/learning-path-video-fix/requirements.md)
- [Design Document](../../.kiro/specs/learning-path-video-fix/design.md)

## Support

For issues or questions:
1. Check logs: `logger.error()` messages
2. Verify dependencies: YouTube API key, Database, Redis
3. Run tests: `pytest tests/services/test_health_check_service_simple.py`
4. Check diagnostics: Call `/api/youtube/health` endpoint
