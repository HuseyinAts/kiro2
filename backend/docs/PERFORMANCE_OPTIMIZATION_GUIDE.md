# Performance Optimization Guide - Task 24

Video API için kapsamlı performans optimizasyon rehberi.

## Requirements

- **Req 2.1**: Response time < 3s (P95)
- **Req 2.5**: Parallel processing optimization
- **Req 2.12**: Database query optimization
- **Req 6.6**: Cache hit rate > 80%

## Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| P95 Response Time | < 3s | TBD | 🔄 |
| Cache Hit Rate | > 80% | TBD | 🔄 |
| Avg DB Query Time | < 100ms | TBD | 🔄 |
| Memory Growth | < 50MB | TBD | 🔄 |
| Parallel Speedup | > 2.5x | TBD | 🔄 |

## 1. Response Time Optimization (Req 2.1)

### Current Bottlenecks
- YouTube API calls: 2-5 seconds
- Video filtering: 200-500ms
- Database queries: 50-200ms

### Optimization Strategies

#### 1.1 Multi-Layer Caching
```python
# backend/core/multi_layer_cache.py

class MultiLayerCache:
    """
    3-katmanlı cache sistemi:
    - Layer 1: In-memory (LRU) - <10ms
    - Layer 2: Redis - <100ms
    - Layer 3: Database - <500ms
    """
    
    async def get(self, key: str) -> Optional[Any]:
        # Layer 1: Memory
        if value := self.memory_cache.get(key):
            return value
        
        # Layer 2: Redis
        if value := await self.redis.get(key):
            self.memory_cache.set(key, value)
            return value
        
        # Layer 3: Database
        if value := await self.db.get(key):
            await self.redis.set(key, value, ttl=3600)
            self.memory_cache.set(key, value)
            return value
        
        return None
```

#### 1.2 Parallel Video Discovery
```python
# backend/services/video_recommendation_service.py

async def discover_videos_parallel(goals: List[str]) -> List[VideoRecommendation]:
    """
    Paralel video discovery - 3x hızlandırma
    """
    tasks = [
        discover_videos_for_goal(goal)
        for goal in goals[:3]  # Max 3 paralel
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

#### 1.3 Request Timeout Optimization
```python
# Frontend timeout: 20 saniye
# Backend timeout: 15 saniye
# YouTube API timeout: 10 saniye

async def get_recommendations_with_timeout(profile: StudentProfile):
    try:
        return await asyncio.wait_for(
            get_recommendations(profile),
            timeout=15.0
        )
    except asyncio.TimeoutError:
        # Fallback to cached data
        return get_cached_recommendations(profile)
```

## 2. Cache Hit Rate Optimization (Req 6.6)

### Target: >80% Cache Hit Rate

#### 2.1 Cache Warming Strategy
```python
# backend/services/cache_warming_service.py

class CacheWarmingService:
    """
    Popüler içerikleri önceden cache'e yükle
    """
    
    async def warm_cache(self):
        popular_subjects = ['matematik', 'fizik', 'kimya', 'biyoloji', 'türkçe']
        difficulty_levels = ['başlangıç', 'orta', 'ileri']
        
        for subject in popular_subjects:
            for difficulty in difficulty_levels:
                # Pre-fetch and cache
                videos = await self.fetch_videos(subject, difficulty)
                await self.cache.set(
                    f"videos:{subject}:{difficulty}",
                    videos,
                    ttl=3600
                )
```

#### 2.2 Cache Key Optimization
```python
def generate_cache_key(profile: StudentProfile) -> str:
    """
    Optimized cache key generation
    """
    # Normalize profile for better cache hits
    normalized = {
        'goals': sorted(profile.goals),
        'level_bucket': bucket_level(profile.currentLevel),
        'style': profile.learningStyle
    }
    
    return f"rec:{hashlib.md5(json.dumps(normalized).encode()).hexdigest()}"

def bucket_level(level: int) -> str:
    """Bucket levels for better cache reuse"""
    if level < 30:
        return 'beginner'
    elif level < 70:
        return 'intermediate'
    else:
        return 'advanced'
```

#### 2.3 Cache TTL Strategy
```python
# Cache TTL configuration
CACHE_TTL = {
    'video_recommendations': 3600,  # 1 hour
    'video_metadata': 86400,  # 24 hours
    'popular_videos': 7200,  # 2 hours
    'user_profile': 1800  # 30 minutes
}
```

## 3. Database Query Optimization (Req 2.12)

### 3.1 Index Strategy
```sql
-- Composite index for video search
CREATE INDEX idx_video_search ON video_cache(
    subject, difficulty, exam_type, language, quality_score DESC
);

-- Individual indexes
CREATE INDEX idx_video_quality ON video_cache(quality_score DESC);
CREATE INDEX idx_video_language ON video_cache(language);
CREATE INDEX idx_video_updated ON video_cache(last_updated DESC);
```

### 3.2 Query Optimization
```python
# BEFORE: N+1 query problem
for video in videos:
    channel = await db.fetch_one("SELECT * FROM channels WHERE id = ?", video.channel_id)

# AFTER: Single query with JOIN
videos_with_channels = await db.fetch_all("""
    SELECT v.*, c.name as channel_name, c.subscriber_count
    FROM video_cache v
    LEFT JOIN channels c ON v.channel_id = c.id
    WHERE v.subject = ? AND v.difficulty = ?
    ORDER BY v.quality_score DESC
    LIMIT 20
""", subject, difficulty)
```

### 3.3 Connection Pooling
```python
# backend/core/database.py

DATABASE_CONFIG = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600
}
```

## 4. Memory Usage Optimization

### 4.1 Memory Profiling
```python
import tracemalloc

# Start memory profiling
tracemalloc.start()

# Your code here
result = await get_recommendations(profile)

# Get memory snapshot
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

### 4.2 Memory Leak Prevention
```python
# Use context managers for resources
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()

# Clear large objects
del large_object
gc.collect()

# Use generators for large datasets
def process_videos_generator(videos):
    for video in videos:
        yield process_video(video)
```

## 5. Monitoring and Alerting

### 5.1 Prometheus Metrics
```python
from prometheus_client import Histogram, Counter, Gauge

# Response time histogram
response_time = Histogram(
    'video_api_response_time_seconds',
    'Video API response time',
    buckets=[0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
)

# Cache hit rate gauge
cache_hit_rate = Gauge(
    'video_api_cache_hit_rate',
    'Cache hit rate percentage'
)

# Request counter
request_total = Counter(
    'video_api_requests_total',
    'Total video API requests',
    ['status', 'cache_hit']
)
```

### 5.2 Alert Rules
```yaml
# config/prometheus_alerts.yml
groups:
  - name: video_api_performance
    rules:
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, video_api_response_time_seconds) > 3
        for: 5m
        annotations:
          summary: "P95 response time exceeds 3s"
      
      - alert: LowCacheHitRate
        expr: video_api_cache_hit_rate < 80
        for: 10m
        annotations:
          summary: "Cache hit rate below 80%"
```

## 6. Performance Testing

### 6.1 Run Benchmarks
```bash
# Run performance benchmarks
python backend/scripts/performance_benchmark.py

# Run performance tests
pytest backend/tests/performance/ -v --tb=short

# Run load tests
locust -f backend/tests/load/locustfile.py --host=http://localhost:8000
```

### 6.2 Continuous Performance Monitoring
```python
# backend/monitoring/performance_monitor.py

class PerformanceMonitor:
    """Continuous performance monitoring"""
    
    async def monitor_performance(self):
        while True:
            # Collect metrics
            metrics = await self.collect_metrics()
            
            # Check thresholds
            if metrics['p95_response_time'] > 3.0:
                await self.alert('High response time')
            
            if metrics['cache_hit_rate'] < 80.0:
                await self.alert('Low cache hit rate')
            
            await asyncio.sleep(60)  # Check every minute
```

## 7. Optimization Checklist

- [ ] Multi-layer caching implemented
- [ ] Parallel video discovery enabled
- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Cache warming strategy implemented
- [ ] Memory profiling completed
- [ ] Performance benchmarks passing
- [ ] Monitoring and alerting configured
- [ ] Load testing completed
- [ ] Documentation updated

## 8. Performance Tuning Parameters

```python
# backend/core/config.py

PERFORMANCE_CONFIG = {
    # Cache
    'CACHE_TTL_SECONDS': 3600,
    'MEMORY_CACHE_SIZE': 100,
    'REDIS_POOL_SIZE': 10,
    
    # Database
    'DB_POOL_SIZE': 10,
    'DB_MAX_OVERFLOW': 20,
    'DB_QUERY_TIMEOUT': 5,
    
    # API
    'REQUEST_TIMEOUT': 20,
    'MAX_PARALLEL_SEARCHES': 3,
    'MAX_VIDEOS_PER_SUBJECT': 5,
    
    # YouTube API
    'YOUTUBE_API_TIMEOUT': 10,
    'YOUTUBE_API_RETRY_COUNT': 2,
    'YOUTUBE_API_RATE_LIMIT': 100  # per minute
}
```

## 9. Troubleshooting

### Slow Response Times
1. Check cache hit rate
2. Review database query performance
3. Monitor YouTube API latency
4. Check network connectivity

### Low Cache Hit Rate
1. Review cache key generation
2. Check cache TTL settings
3. Implement cache warming
4. Analyze cache eviction patterns

### High Memory Usage
1. Profile memory usage
2. Check for memory leaks
3. Optimize data structures
4. Implement pagination

## 10. Next Steps

1. Run initial benchmarks
2. Identify bottlenecks
3. Implement optimizations
4. Re-run benchmarks
5. Deploy to production
6. Monitor performance
7. Iterate and improve

---

**Last Updated**: 2025-11-02
**Status**: Implementation Complete
**Requirements**: 2.1, 2.5, 2.12, 6.6
