# API Response Time Optimization Guide

KIRO2 Platform API performans optimizasyon rehberi.

## Genel Bakış

Bu dokümantasyon, API response time optimizasyonu için uygulanan
tüm teknikleri ve yapılandırmaları açıklar.

## Optimizasyon Teknikleri

### 1. Response Compression

GZip middleware ile response sıkıştırma.

**Yapılandırma:**
- Minimum size: 1000 bytes (1KB)
- Compression level: 6 (balance)
- Excluded content types: images, videos, already compressed

**Kullanım:**
```python
# Otomatik - middleware'de yapılandırılmış
# application.py'de aktif

# Manuel kontrol için header:
# Accept-Encoding: gzip
```

**Beklenen Sonuç:**
- JSON payload'lar için >= 60% boyut azalması
- Response headers: `Content-Encoding: gzip`

### 2. HTTP Caching

ETag ve Cache-Control headers ile HTTP caching.

**Yapılandırma:**
```python
# Endpoint tipine göre cache policy:
# - static: max-age=3600 (1 saat)
# - dynamic: max-age=300 (5 dakika)
# - user_data: max-age=60, private
# - questions: max-age=1800 (30 dakika)
# - no_cache: no-store
```

**Headers:**
```
ETag: "abc123..."
Cache-Control: public, max-age=300
Vary: Accept, Accept-Encoding
```

**304 Not Modified:**
```
Request:
  If-None-Match: "abc123..."

Response (if unchanged):
  Status: 304 Not Modified
  ETag: "abc123..."
```

### 3. Request Batching

Birden fazla işlemi tek request'te yapma.

**Endpoint:**
```
POST /api/v1/batch
```

**Request Body:**
```json
{
  "operations": [
    {
      "type": "get_questions",
      "params": {"ids": ["q1", "q2", "q3"]},
      "id": "op1"
    },
    {
      "type": "submit_answers",
      "params": {"exam_id": "e1", "answers": [...]},
      "id": "op2"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {"operation_id": "op1", "success": true, "data": {...}},
    {"operation_id": "op2", "success": true, "data": {...}}
  ],
  "summary": {
    "total": 2,
    "success": 2,
    "failure": 0,
    "elapsed_ms": 45.23
  }
}
```

**Limits:**
- Max 10 operations per batch
- Partial failure handling enabled

### 4. Payload Optimization

#### orjson Serialization
3-10x faster JSON serialization.

```python
from core.json_utils import ORJSONResponse

@app.get("/items", response_class=ORJSONResponse)
async def get_items():
    return {"items": [...]}
```

#### Sparse Fieldsets
İstenen field'ları seçme.

```
GET /api/v1/questions?fields=id,content,difficulty
```

#### Null Value Exclusion
None değerleri response'dan çıkarma.

```python
# exclude_none=True (default)
# {"name": "test", "description": null} -> {"name": "test"}
```

#### Depth Limiting
Nested object derinliğini sınırlama.

```python
from core.depth_limiter import depth_limited_response

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await fetch_user_with_relations(user_id)
    return depth_limited_response(user, max_depth=4)
```

### 5. Database Query Optimization

#### Cursor-Based Pagination
```python
from repositories.cursor_pagination import CursorPaginator

paginator = CursorPaginator(Question)
page = await paginator.paginate(
    session=db,
    limit=20,
    cursor=request.query_params.get("cursor")
)

# Response:
# {
#   "items": [...],
#   "pagination": {
#     "next_cursor": "...",
#     "has_next": true
#   }
# }
```

#### Query Caching
```python
from core.cache.query_cache import cached_query

@cached_query("questions:{subject}:page{page}", ttl=600)
async def get_questions(subject: str, page: int = 1):
    return await db.fetch_questions(subject, page)
```

#### Eager Loading
```python
from sqlalchemy.orm import selectinload

query = select(Question).options(
    selectinload(Question.options),
    selectinload(Question.tags)
)
```

### 6. Middleware Stack

Optimized middleware ordering (fastest first):

1. **Timing** - Request süre ölçümü
2. **CORS** - Cross-origin handling
3. **Cache Headers** - ETag, If-None-Match
4. **Compression** - GZip response

## Performance Targets

| Metric | Target | Description |
|--------|--------|-------------|
| P50 Latency | < 100ms | Median response time |
| P95 Latency | < 200ms | 95th percentile |
| P99 Latency | < 500ms | 99th percentile |
| Throughput | >= 1000 req/sec | Requests per second |
| Error Rate | < 1% | Server errors |

## Monitoring

### Prometheus Metrics

```
GET /metrics

# HELP http_request_latency_seconds HTTP request latency
# TYPE http_request_latency_seconds histogram
http_request_latency_seconds_bucket{endpoint="/api/v1/questions",method="GET",le="0.1"} 950
http_request_latency_seconds_bucket{endpoint="/api/v1/questions",method="GET",le="0.2"} 990
```

### Response Headers

```
X-Response-Time: 45.23ms
X-Cache-Status: HIT|MISS
X-Compression-Ratio: 65.2%
```

### Alerting

P95 > 200ms durumunda alert tetiklenir.

```python
from core.monitoring.alerts import get_alert_manager

alert_manager = get_alert_manager()
alert_manager.check_latency(endpoint, p95_ms=250.0)
```

## Troubleshooting

### Slow Requests (> 200ms)

1. Check timing middleware logs
2. Analyze database query performance
3. Verify cache hit rates
4. Review N+1 query issues

### High Cache Miss Rate

1. Review cache TTL settings
2. Check cache key consistency
3. Verify cache warming

### Compression Not Working

1. Check Accept-Encoding header
2. Verify content type is compressible
3. Check minimum size threshold

## Related Documentation

- [Async Operations Guide](./async-guide.md)
- [Monitoring Setup](./monitoring-setup.md)
- [Database Optimization](./database-optimization.md)
