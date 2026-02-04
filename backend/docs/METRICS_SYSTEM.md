# Video API Metrics Collection System

## Overview

Kapsamlı Prometheus tabanlı metrics collection sistemi. Video API'nin performansını, cache verimliliğini, YouTube API quota kullanımını ve hata oranlarını gerçek zamanlı izler.

**Requirements:** 4.4, 4.10, 4.14, 5.12

## Features

### 📊 Toplanan Metrikler

1. **video_requests_total** (Counter)
   - Toplam video isteği sayısı
   - Labels: `status` (success/error), `cache_status` (hit/miss)

2. **video_response_time_seconds** (Histogram)
   - Video yanıt süresi (saniye)
   - Percentile'lar: P50, P95, P99
   - Buckets: 0.1s, 0.5s, 1s, 2s, 3s, 5s, 10s, 20s, 30s

3. **cache_hit_rate** (Gauge)
   - Cache hit oranı (0-1 arası)
   - Hedef: >0.8 (80%+)

4. **youtube_api_quota_used** (Gauge)
   - YouTube API quota kullanımı
   - Günlük limit: 10,000

5. **video_errors_total** (Counter)
   - Toplam hata sayısı
   - Labels: `error_type`, `endpoint`

6. **active_video_requests** (Gauge)
   - Aktif istek sayısı

7. **cache_operations_total** (Counter)
   - Cache operasyonları
   - Labels: `operation` (get/set/delete/clear)

8. **cache_size_entries** (Gauge)
   - Cache'deki entry sayısı

## API Endpoints

### 1. Prometheus Metrics Endpoint

```http
GET /api/youtube/metrics/prometheus
```

**Response:** Prometheus text format

```
# HELP video_requests_total Total number of video recommendation requests
# TYPE video_requests_total counter
video_requests_total{cache_status="hit",status="success"} 1450.0
video_requests_total{cache_status="miss",status="success"} 320.0
...
```

**Kullanım:**
- Prometheus scraper tarafından otomatik olarak çekilir
- Grafana dashboard'larında görselleştirilir

### 2. Metrics Snapshot Endpoint

```http
GET /api/youtube/metrics/snapshot
```

**Response:** JSON format

```json
{
  "timestamp": "2025-10-30T15:30:00",
  "total_requests": 1770,
  "successful_requests": 1680,
  "failed_requests": 90,
  "cache_hits": 1450,
  "cache_misses": 320,
  "avg_response_time": 1.234,
  "p50_response_time": 0.987,
  "p95_response_time": 2.456,
  "p99_response_time": 4.123,
  "youtube_api_quota_used": 450,
  "error_rate": 0.051,
  "cache_hit_rate": 0.819
}
```

**Kullanım:**
- Dashboard'lar için JSON data
- Monitoring sistemleri için API entegrasyonu

## Usage

### Python Code Integration

```python
from core.metrics_collector import get_metrics_collector

# Get global metrics collector
metrics_collector = get_metrics_collector()

# Track a request
request_id = "unique-request-id"

# Start tracking
metrics_collector.start_request(request_id, endpoint='/api/youtube/recommendations')

try:
    # Your business logic here
    result = await process_video_request()
    
    # End tracking (success)
    metrics_collector.end_request(
        request_id=request_id,
        success=True,
        cache_hit=True,  # or False
        endpoint='/api/youtube/recommendations'
    )
    
except Exception as e:
    # Record error
    metrics_collector.record_error(
        request_id=request_id,
        error_type=type(e).__name__,
        endpoint='/api/youtube/recommendations'
    )
    
    # End tracking (failure)
    metrics_collector.end_request(
        request_id=request_id,
        success=False,
        cache_hit=False,
        endpoint='/api/youtube/recommendations'
    )
```

### YouTube API Quota Tracking

```python
# Record YouTube API call
metrics_collector.record_youtube_api_call(quota_cost=1)

# Search operation costs 100 units
metrics_collector.record_youtube_api_call(quota_cost=100)

# Reset quota (daily reset)
metrics_collector.reset_youtube_quota()
```

### Cache Operations Tracking

```python
# Track cache operations
metrics_collector.record_cache_operation('get')
metrics_collector.record_cache_operation('set')
metrics_collector.record_cache_operation('delete')

# Update cache size
metrics_collector.update_cache_size(150)
```

### Get Metrics Snapshot

```python
# Get current metrics snapshot
snapshot = metrics_collector.get_snapshot()

print(f"Total requests: {snapshot.total_requests}")
print(f"Cache hit rate: {snapshot.cache_hit_rate:.2%}")
print(f"Avg response time: {snapshot.avg_response_time:.3f}s")
print(f"P95 response time: {snapshot.p95_response_time:.3f}s")
```

## Prometheus Configuration

### prometheus.yml

```yaml
scrape_configs:
  - job_name: 'video_api'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/youtube/metrics/prometheus'
```

## Grafana Dashboard

### Key Panels

1. **Request Rate**
   - Query: `rate(video_requests_total[5m])`
   - Visualization: Graph

2. **Success Rate**
   - Query: `sum(rate(video_requests_total{status="success"}[5m])) / sum(rate(video_requests_total[5m]))`
   - Visualization: Gauge (0-100%)

3. **Response Time (P95)**
   - Query: `histogram_quantile(0.95, rate(video_response_time_seconds_bucket[5m]))`
   - Visualization: Graph

4. **Cache Hit Rate**
   - Query: `cache_hit_rate`
   - Visualization: Gauge (0-100%)

5. **YouTube API Quota**
   - Query: `youtube_api_quota_used`
   - Visualization: Gauge with threshold (warning at 80%)

6. **Error Rate**
   - Query: `rate(video_errors_total[5m])`
   - Visualization: Graph

## Alerting Rules

### Prometheus Alerts

```yaml
groups:
  - name: video_api_alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(video_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      # Slow response time
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(video_response_time_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time detected"
          description: "P95 response time is {{ $value }}s"
      
      # Low cache hit rate
      - alert: LowCacheHitRate
        expr: cache_hit_rate < 0.6
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"
      
      # YouTube API quota warning
      - alert: YouTubeQuotaHigh
        expr: youtube_api_quota_used > 8000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "YouTube API quota is high"
          description: "Quota used: {{ $value }} / 10000"
```

## Performance Targets

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| P95 Response Time | < 3s | > 5s | > 10s |
| Cache Hit Rate | > 80% | < 60% | < 40% |
| Error Rate | < 1% | > 5% | > 10% |
| YouTube Quota | < 8000/day | > 8000 | > 9500 |
| Success Rate | > 99% | < 95% | < 90% |

## Troubleshooting

### High Error Rate

1. Check error types:
   ```python
   snapshot = metrics_collector.get_snapshot()
   print(f"Error rate: {snapshot.error_rate:.2%}")
   ```

2. Review logs for error patterns
3. Check external service health (YouTube API, cache, database)

### Low Cache Hit Rate

1. Check cache configuration
2. Verify cache TTL settings
3. Review cache key generation logic
4. Monitor cache size and eviction

### Slow Response Time

1. Check P95/P99 percentiles
2. Identify slow endpoints
3. Review database query performance
4. Check YouTube API response times

### YouTube Quota Exhaustion

1. Monitor quota usage:
   ```python
   snapshot = metrics_collector.get_snapshot()
   quota_percentage = (snapshot.youtube_api_quota_used / 10000) * 100
   print(f"Quota: {quota_percentage:.1f}%")
   ```

2. Increase cache hit rate
3. Implement request throttling
4. Consider quota increase from Google

## Testing

### Run Tests

```bash
cd backend
pytest tests/test_metrics_collector.py -v
```

### Run Example

```bash
cd backend
python examples/metrics_example.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Video API Endpoint                        │
│                  (/api/youtube/recommendations)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    MetricsCollector                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  start_request()                                       │ │
│  │  end_request()                                         │ │
│  │  record_error()                                        │ │
│  │  record_youtube_api_call()                             │ │
│  │  record_cache_operation()                              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Prometheus Client                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Counter, Gauge, Histogram                             │ │
│  │  Registry                                              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Metrics Endpoints                               │
│  - /api/youtube/metrics/prometheus (Prometheus format)      │
│  - /api/youtube/metrics/snapshot (JSON format)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         Monitoring & Visualization                           │
│  - Prometheus (scraping & storage)                           │
│  - Grafana (dashboards)                                      │
│  - Alertmanager (alerts)                                     │
└─────────────────────────────────────────────────────────────┘
```

## Best Practices

1. **Always track requests:**
   - Call `start_request()` at the beginning
   - Call `end_request()` in finally block

2. **Record errors:**
   - Use specific error types
   - Include context in error messages

3. **Monitor quota:**
   - Track YouTube API calls
   - Set up alerts at 80% usage

4. **Cache operations:**
   - Track all cache operations
   - Monitor cache size

5. **Regular monitoring:**
   - Check metrics daily
   - Review trends weekly
   - Optimize based on data

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [YouTube Data API Quota](https://developers.google.com/youtube/v3/getting-started#quota)
