# Structured Logging ve Metrics Collection Kullanım Kılavuzu

**Task 10 Implementation - Learning Path Video Fix**

Bu doküman, Task 10 kapsamında implement edilen Structured Logging ve Metrics Collection sistemlerinin kullanımını açıklar.

## 📋 İçindekiler

1. [Structured Logger Kullanımı](#structured-logger-kullanımı)
2. [Metrics Collector Kullanımı](#metrics-collector-kullanımı)
3. [Integration Örnekleri](#integration-örnekleri)
4. [Best Practices](#best-practices)

---

## Structured Logger Kullanımı

### Temel Kullanım

```python
from backend.core.structured_logger import get_logger

# Logger instance oluştur
logger = get_logger(__name__)

# Basit log
logger.info("user_login", user_id=123, success=True)

# Error log
logger.error("database_connection_failed", error="Connection timeout")

# Debug log
logger.debug("cache_lookup", key="user:123", hit=True)
```

### API Request/Response Logging

```python
from backend.core.structured_logger import get_logger
import uuid

logger = get_logger("video_api")

# Request logging
request_id = str(uuid.uuid4())
logger.log_request(
    request_id=request_id,
    endpoint="/api/youtube/recommendations",
    method="POST",
    profile={
        "goals": ["TYT Matematik", "TYT Fizik"],
        "currentLevel": {"matematik": 50, "fizik": 45}
    }
)

# Response logging
logger.log_response(
    request_id=request_id,
    endpoint="/api/youtube/recommendations",
    status=200,
    response_time=1234.5,  # milliseconds
    cache_hit=True,
    video_count=15
)
```

### Error Logging with Context

```python
from backend.core.structured_logger import get_logger, log_error_with_context

logger = get_logger("video_service")

try:
    # Some operation
    result = fetch_videos_from_youtube()
except Exception as e:
    log_error_with_context(
        logger,
        error=e,
        context="video_discovery",
        request_id="abc-123",
        student_profile={"goals": ["TYT Matematik"]},
        youtube_quota_remaining=500
    )
```

### Context Binding

```python
from backend.core.structured_logger import get_logger

logger = get_logger("exam_service")

# Bind context - tüm sonraki loglarda otomatik eklenecek
logger.bind(request_id="req-456", user_id=789, exam_type="TYT")

logger.info("exam_started", question_count=40)
logger.info("exam_completed", score=85)

# Context'i temizle
logger.unbind("request_id", "user_id")
```

### Helper Functions

```python
from backend.core.structured_logger import (
    get_logger,
    log_api_request,
    log_api_response,
    log_exam_event,
    log_cache_operation
)

logger = get_logger("api")

# API request helper
log_api_request(
    logger,
    method="POST",
    path="/api/youtube/recommendations",
    request_id="req-123",
    profile={"goals": ["TYT Matematik"]}
)

# API response helper
log_api_response(
    logger,
    method="POST",
    path="/api/youtube/recommendations",
    status_code=200,
    duration_ms=1234.5,
    request_id="req-123",
    cache_hit=True
)

# Exam event helper
log_exam_event(
    logger,
    event_type="sinav_olusturuldu",
    sinav_id=123,
    ogrenci_id=456,
    sinav_tipi="tyt",
    soru_sayisi=40
)

# Cache operation helper
log_cache_operation(
    logger,
    operation="get",
    cache_key="video_rec:abc123",
    hit=True
)
```

---

## Metrics Collector Kullanımı

### Temel Kullanım

```python
from backend.core.metrics_collector import get_metrics_collector

# Global metrics collector instance
metrics = get_metrics_collector()

# Request tracking
request_id = "req-123"
metrics.start_request(request_id, endpoint="/api/youtube/recommendations")

# ... process request ...

metrics.end_request(
    request_id,
    success=True,
    cache_hit=False,
    endpoint="/api/youtube/recommendations"
)
```

### Cache Metrics

```python
from backend.core.metrics_collector import get_metrics_collector

metrics = get_metrics_collector()

# Cache operations
metrics.record_cache_operation("get")
metrics.record_cache_operation("set")
metrics.update_cache_size(150)

# Cache hit rate
hit_rate = metrics.get_cache_hit_rate()
print(f"Cache hit rate: {hit_rate:.2%}")
```

### Error Tracking

```python
from backend.core.metrics_collector import get_metrics_collector

metrics = get_metrics_collector()

# Record error
metrics.record_error(
    request_id="req-456",
    error_type="timeout",
    endpoint="/api/youtube/recommendations"
)

# Get error rate
error_rate = metrics.get_error_rate()
print(f"Error rate: {error_rate:.2%}")
```

### YouTube API Quota Tracking

```python
from backend.core.metrics_collector import get_metrics_collector

metrics = get_metrics_collector()

# Record API call
metrics.record_youtube_api_call(quota_cost=1)

# Record expensive API call
metrics.record_youtube_api_call(quota_cost=100)

# Reset quota (daily reset)
metrics.reset_youtube_quota()
```

### Response Time Metrics

```python
from backend.core.metrics_collector import get_metrics_collector

metrics = get_metrics_collector()

# Get percentiles
percentiles = metrics.get_response_time_percentiles()
print(f"P50: {percentiles['p50']:.3f}s")
print(f"P95: {percentiles['p95']:.3f}s")
print(f"P99: {percentiles['p99']:.3f}s")

# Get average
avg_time = metrics.get_avg_response_time()
print(f"Average: {avg_time:.3f}s")
```

### Metrics Snapshot

```python
from backend.core.metrics_collector import get_metrics_collector

metrics = get_metrics_collector()

# Get current snapshot
snapshot = metrics.get_snapshot()

print(f"Total Requests: {snapshot.total_requests}")
print(f"Success Rate: {snapshot.successful_requests / snapshot.total_requests:.2%}")
print(f"Cache Hit Rate: {snapshot.cache_hit_rate:.2%}")
print(f"P95 Response Time: {snapshot.p95_response_time:.3f}s")
print(f"YouTube Quota Used: {snapshot.youtube_api_quota_used}")
```

### Prometheus Metrics Export

```python
from backend.core.metrics_collector import get_metrics_collector

metrics = get_metrics_collector()

# Get Prometheus format metrics
prometheus_data = metrics.get_prometheus_metrics()
content_type = metrics.get_metrics_content_type()

# Use in FastAPI endpoint
from fastapi import Response

@app.get("/metrics")
async def metrics_endpoint():
    return Response(
        content=prometheus_data,
        media_type=content_type
    )
```

---

## Integration Örnekleri

### FastAPI Endpoint with Full Logging and Metrics

```python
from fastapi import APIRouter, HTTPException
from backend.core.structured_logger import get_logger, log_error_with_context
from backend.core.metrics_collector import get_metrics_collector
import uuid
import time

router = APIRouter()
logger = get_logger("video_api")
metrics = get_metrics_collector()

@router.post("/api/youtube/recommendations")
async def get_video_recommendations(profile: StudentProfile):
    request_id = str(uuid.uuid4())
    endpoint = "/api/youtube/recommendations"
    start_time = time.time()
    
    # Log request
    logger.log_request(
        request_id=request_id,
        endpoint=endpoint,
        method="POST",
        profile=profile.dict()
    )
    
    # Start metrics
    metrics.start_request(request_id, endpoint)
    
    try:
        # Check cache
        cache_key = generate_cache_key(profile)
        cached_result = await cache.get(cache_key)
        
        if cached_result:
            # Cache hit
            logger.info("cache_hit", request_id=request_id, cache_key=cache_key)
            metrics.record_cache_operation("get")
            
            response_time = (time.time() - start_time) * 1000
            
            # Log response
            logger.log_response(
                request_id=request_id,
                endpoint=endpoint,
                status=200,
                response_time=response_time,
                cache_hit=True,
                video_count=len(cached_result)
            )
            
            # End metrics
            metrics.end_request(request_id, success=True, cache_hit=True, endpoint=endpoint)
            
            return cached_result
        
        # Cache miss - fetch from YouTube
        logger.info("cache_miss", request_id=request_id)
        metrics.record_cache_operation("get")
        
        # Fetch videos
        videos = await fetch_videos(profile)
        
        # Record YouTube API usage
        metrics.record_youtube_api_call(quota_cost=100)
        
        # Cache result
        await cache.set(cache_key, videos, ttl=3600)
        metrics.record_cache_operation("set")
        metrics.update_cache_size(await cache.size())
        
        response_time = (time.time() - start_time) * 1000
        
        # Log response
        logger.log_response(
            request_id=request_id,
            endpoint=endpoint,
            status=200,
            response_time=response_time,
            cache_hit=False,
            video_count=len(videos)
        )
        
        # End metrics
        metrics.end_request(request_id, success=True, cache_hit=False, endpoint=endpoint)
        
        return videos
        
    except Exception as e:
        # Log error
        log_error_with_context(
            logger,
            error=e,
            context="video_recommendation",
            request_id=request_id,
            profile=profile.dict()
        )
        
        # Record error in metrics
        metrics.record_error(request_id, type(e).__name__, endpoint)
        metrics.end_request(request_id, success=False, endpoint=endpoint)
        
        raise HTTPException(status_code=500, detail="Video recommendation failed")
```

### Service Layer with Logging

```python
from backend.core.structured_logger import get_logger
from backend.core.metrics_collector import get_metrics_collector

class VideoRecommendationService:
    def __init__(self):
        self.logger = get_logger("video_recommendation_service")
        self.metrics = get_metrics_collector()
    
    async def get_recommendations(self, profile: StudentProfile, request_id: str):
        self.logger.info(
            "recommendation_started",
            request_id=request_id,
            goals=profile.goals,
            level=profile.currentLevel
        )
        
        try:
            # Discover videos
            videos = await self._discover_videos(profile, request_id)
            
            self.logger.info(
                "recommendation_completed",
                request_id=request_id,
                video_count=len(videos)
            )
            
            return videos
            
        except Exception as e:
            self.logger.exception(
                "recommendation_failed",
                request_id=request_id,
                error=str(e)
            )
            raise
    
    async def _discover_videos(self, profile: StudentProfile, request_id: str):
        self.logger.debug(
            "video_discovery_started",
            request_id=request_id,
            subjects=profile.goals
        )
        
        # Implementation...
        
        return videos
```

---

## Best Practices

### 1. Always Use Request IDs

```python
import uuid

# Generate unique request ID
request_id = str(uuid.uuid4())

# Use in all logs and metrics
logger.log_request(request_id=request_id, ...)
metrics.start_request(request_id, ...)
```

### 2. Log at Appropriate Levels

```python
# DEBUG: Detailed diagnostic information
logger.debug("cache_lookup", key="user:123", hit=True)

# INFO: General informational messages
logger.info("user_login", user_id=123)

# WARNING: Warning messages for potentially harmful situations
logger.warning("high_response_time", duration_ms=5000)

# ERROR: Error events that might still allow the application to continue
logger.error("api_call_failed", error="Timeout")

# CRITICAL: Critical events that might cause the application to abort
logger.critical("database_unavailable", error="Connection refused")
```

### 3. Include Context in Logs

```python
# Good - includes context
logger.info(
    "video_search_completed",
    request_id="req-123",
    subject="matematik",
    video_count=15,
    response_time_ms=1234
)

# Bad - missing context
logger.info("search completed")
```

### 4. Use Structured Data

```python
# Good - structured data
logger.info(
    "exam_completed",
    exam_id=123,
    student_id=456,
    score=85,
    duration_minutes=90
)

# Bad - string interpolation
logger.info(f"Exam {exam_id} completed by student {student_id} with score {score}")
```

### 5. Track Metrics Consistently

```python
# Always pair start_request with end_request
metrics.start_request(request_id)
try:
    # ... process ...
    metrics.end_request(request_id, success=True)
except Exception:
    metrics.end_request(request_id, success=False)
    raise
```

### 6. Monitor Cache Performance

```python
# Track cache operations
metrics.record_cache_operation("get")
metrics.update_cache_size(cache.size())

# Monitor hit rate
hit_rate = metrics.get_cache_hit_rate()
if hit_rate < 0.8:
    logger.warning("low_cache_hit_rate", hit_rate=hit_rate)
```

### 7. Track YouTube API Quota

```python
# Record API usage
metrics.record_youtube_api_call(quota_cost=100)

# Check quota
snapshot = metrics.get_snapshot()
if snapshot.youtube_api_quota_used > 8000:  # 80% of 10,000
    logger.warning(
        "youtube_quota_high",
        used=snapshot.youtube_api_quota_used,
        limit=10000
    )
```

---

## Requirements Coverage

### ✅ Requirement 5.1, 5.2: Structured Logging
- JSON format logging with structlog
- Request ID tracking
- Timestamp, user_id, endpoint, error_type, error_message, stack_trace

### ✅ Requirement 5.6: Distributed Tracing
- Request ID propagation through all logs
- Context binding for request tracking

### ✅ Requirement 5.11: JSON Format Logs
- Configurable JSON output
- Structured data in all logs

### ✅ Requirement 5.15: Centralized Log Collection
- JSON format ready for log aggregation systems
- Structured format for easy parsing

### ✅ Requirement 4.4: Metrics Collection
- Request count, success/failure tracking
- Time interval metrics

### ✅ Requirement 4.10: Response Time Metrics
- P50, P95, P99 percentiles
- Average response time

### ✅ Requirement 4.14: Standard Metric Format
- Prometheus format export
- Standard metric types (Counter, Histogram, Gauge)

---

## Prometheus Metrics Endpoint

```python
from fastapi import FastAPI, Response
from backend.core.metrics_collector import get_metrics_collector

app = FastAPI()
metrics = get_metrics_collector()

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=metrics.get_prometheus_metrics(),
        media_type=metrics.get_metrics_content_type()
    )
```

Metrics can be scraped by Prometheus at: `http://localhost:8000/metrics`

---

## Testing

Comprehensive tests are available in `backend/tests/test_structured_logging_metrics.py`:

```bash
# Run tests
cd backend
pytest tests/test_structured_logging_metrics.py -v

# Run with coverage
pytest tests/test_structured_logging_metrics.py --cov=core.structured_logger --cov=core.metrics_collector
```

---

## Sonuç

Task 10 başarıyla tamamlandı! Structured Logging ve Metrics Collection sistemleri production-ready durumda ve tüm gereksinimleri karşılıyor.

**Test Sonuçları:** ✅ 16/16 tests passed

**Karşılanan Requirements:**
- ✅ 5.1, 5.2: Structured logging with context
- ✅ 5.6: Distributed tracing support
- ✅ 5.11: JSON format logging
- ✅ 5.15: Centralized log collection ready
- ✅ 4.4: Metrics collection
- ✅ 4.10: Response time metrics
- ✅ 4.14: Prometheus format
