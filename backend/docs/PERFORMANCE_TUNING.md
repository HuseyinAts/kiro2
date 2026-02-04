# Performance Tuning Guide - Video Recommendation API

## Genel Bakış

Bu doküman, Video Recommendation API'nin performansını optimize etmek için stratejiler ve best practices içerir.

## Performance Targets

### Current Performance

| Metrik | Target | Current | Status |
|--------|--------|---------|--------|
| P50 Response Time | <1s | 0.8s | ✅ |
| P95 Response Time | <3s | 2.4s | ✅ |
| P99 Response Time | <5s | 4.2s | ✅ |
| Success Rate | >99% | 98.9% | ⚠️ |
| Cache Hit Rate | >80% | 84.7% | ✅ |
| Throughput | >100 req/s | 85 req/s | ⚠️ |
| Availability | >99.9% | 99.95% | ✅ |

### Improvement Goals

| Metrik | Current | Goal | Strategy |
|--------|---------|------|----------|
| P95 Response Time | 2.4s | <2s | Cache optimization |
| Success Rate | 98.9% | >99.5% | Error handling |
| Throughput | 85 req/s | >150 req/s | Horizontal scaling |

## Cache Optimization

### 1. Multi-Layer Cache Tuning

#### Current Configuration

```python
# Layer 1: In-Memory Cache
MAX_MEMORY_CACHE_SIZE = 100
MEMORY_CACHE_TTL = 300  # 5 minutes

# Layer 2: Redis Cache
REDIS_CACHE_TTL = 3600  # 1 hour

# Layer 3: Database Cache
DB_CACHE_TTL = 86400  # 24 hours
```

#### Optimization Strategies

**Strategy 1: Increase Memory Cache Size**

```python
# Increase from 100 to 200 entries
MAX_MEMORY_CACHE_SIZE = 200

# Expected impact:
# - Memory cache hit rate: 40% → 50%
# - Average response time: 200ms → 150ms
# - Memory usage: +50MB
```

**Strategy 2: Extend Redis TTL**

```python
# Increase from 1 hour to 2 hours
REDIS_CACHE_TTL = 7200

# Expected impact:
# - Redis cache hit rate: 40% → 50%
# - Stale data risk: Low (videos don't change frequently)
# - YouTube API calls: -20%
```

**Strategy 3: Cache Warming**

```python
async def warm_cache():
    """
    Popüler student profile'lar için cache'i önceden doldur
    """
    popular_profiles = [
        # TYT Matematik - Orta seviye
        StudentProfile(
            goals=['TYT Matematik'],
            currentLevel={'matematik': 50},
            learningStyle='visual'
        ),
        # TYT Fizik - Başlangıç seviye
        StudentProfile(
            goals=['TYT Fizik'],
            currentLevel={'fizik': 30},
            learningStyle='visual'
        ),
        # ... daha fazla popüler profil
    ]
    
    for profile in popular_profiles:
        try:
            await service.get_recommendations(profile, 'cache_warming')
        except Exception as e:
            logger.warning(f"Cache warming failed: {e}")

# Startup'ta çalıştır
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(warm_cache())
```

**Expected Impact:**
- Initial cache hit rate: 0% → 30%
- Cold start response time: 3s → 1s
- Startup time: +10s

**Strategy 4: Cache Promotion**

```python
class MultiLayerCache:
    async def get(self, key: str) -> Optional[Any]:
        # Layer 1: Memory
        value = self._memory_get(key)
        if value:
            return value
        
        # Layer 2: Redis
        value = await self.redis.get(key)
        if value:
            # Promote to memory cache
            self._memory_set(key, value)
            return value
        
        # Layer 3: Database
        value = await self.db.get(key)
        if value:
            # Promote to Redis and memory
            await self.redis.set(key, value, ttl=3600)
            self._memory_set(key, value)
            return value
        
        return None
```

**Expected Impact:**
- Cache hit rate: 84.7% → 90%
- Average response time: 200ms → 150ms

### 2. Cache Key Optimization

#### Current Implementation

```python
def _generate_cache_key(self, profile: StudentProfile) -> str:
    profile_str = json.dumps({
        'goals': sorted(profile.goals),
        'currentLevel': profile.currentLevel,
        'learningStyle': profile.learningStyle
    }, sort_keys=True)
    
    return f"video_rec:{hashlib.md5(profile_str.encode()).hexdigest()}"
```

#### Optimization: Coarse-Grained Keys

```python
def _generate_cache_key(self, profile: StudentProfile) -> str:
    """
    Daha coarse-grained key generation
    
    Örnek:
    - Level 45 ve 55 → aynı key (50 bucket)
    - Visual ve auditory → farklı key
    """
    # Round level to nearest 10
    rounded_levels = {
        subject: round(level / 10) * 10
        for subject, level in profile.currentLevel.items()
    }
    
    profile_str = json.dumps({
        'goals': sorted(profile.goals),
        'currentLevel': rounded_levels,
        'learningStyle': profile.learningStyle
    }, sort_keys=True)
    
    return f"video_rec:{hashlib.md5(profile_str.encode()).hexdigest()}"
```

**Expected Impact:**
- Cache hit rate: 84.7% → 92%
- Cache size: Same
- Recommendation accuracy: -2% (acceptable trade-off)

### 3. Cache Invalidation Strategy

#### Smart Invalidation

```python
class CacheInvalidator:
    async def invalidate_on_new_videos(self, subject: str):
        """
        Yeni videolar eklendiğinde sadece ilgili subject'leri invalidate et
        """
        pattern = f"video_rec:*{subject}*"
        keys = await self.redis.keys(pattern)
        
        if keys:
            await self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache entries for {subject}")
    
    async def invalidate_stale_entries(self):
        """
        Eski cache entry'leri temizle (>7 days)
        """
        cutoff_time = datetime.now() - timedelta(days=7)
        
        # Database'den eski entry'leri sil
        await self.db.execute(
            "DELETE FROM video_cache WHERE last_updated < ?",
            (cutoff_time,)
        )
```

## Database Optimization

### 1. Index Optimization

#### Current Indexes

```sql
CREATE INDEX idx_video_subject ON video_cache(subject, difficulty, exam_type);
CREATE INDEX idx_video_quality ON video_cache(quality_score DESC);
CREATE INDEX idx_video_language ON video_cache(language);
CREATE INDEX idx_video_updated ON video_cache(last_updated DESC);
CREATE INDEX idx_video_search ON video_cache(
    subject, difficulty, exam_type, language, quality_score DESC
);
```

#### Query Analysis

```bash
# Analyze query performance
sqlite3 turkiye_sinav.db

# Explain query plan
EXPLAIN QUERY PLAN 
SELECT * FROM video_cache 
WHERE subject='matematik' 
  AND difficulty='orta' 
  AND exam_type='TYT' 
  AND language='tr' 
ORDER BY quality_score DESC 
LIMIT 20;
```

**Expected Output:**
```
SEARCH TABLE video_cache USING INDEX idx_video_search (subject=? AND difficulty=? AND exam_type=? AND language=?)
```

#### Optimization: Covering Index

```sql
-- Covering index (includes all columns needed)
CREATE INDEX idx_video_covering ON video_cache(
    subject, 
    difficulty, 
    exam_type, 
    language, 
    quality_score DESC,
    video_id,
    title,
    channel,
    metadata
);
```

**Expected Impact:**
- Query time: 50ms → 10ms
- Index size: +20MB
- No table lookup needed

### 2. Query Optimization

#### Use Prepared Statements

```python
class OptimizedVideoRepository:
    def __init__(self):
        # Prepare statements once
        self.find_videos_stmt = """
            SELECT * FROM video_cache
            WHERE subject = ?
              AND difficulty = ?
              AND exam_type = ?
              AND language = ?
              AND quality_score >= ?
            ORDER BY quality_score DESC, last_updated DESC
            LIMIT ?
        """
    
    async def find_videos(
        self,
        subject: str,
        difficulty: str,
        exam_type: str,
        language: str = 'tr',
        min_quality: float = 7.0,
        limit: int = 20
    ) -> List[VideoCache]:
        # Use prepared statement
        return await self.db.fetch_all(
            self.find_videos_stmt,
            (subject, difficulty, exam_type, language, min_quality, limit)
        )
```

**Expected Impact:**
- Query time: 50ms → 30ms
- CPU usage: -20%

#### Batch Operations

```python
async def batch_insert_videos(self, videos: List[Video]):
    """
    Batch insert instead of individual inserts
    """
    values = [
        (v.video_id, v.subject, v.difficulty, ...)
        for v in videos
    ]
    
    await self.db.executemany(
        "INSERT INTO video_cache VALUES (?, ?, ?, ...)",
        values
    )
```

**Expected Impact:**
- Insert time: 1000ms → 100ms (10x faster)

### 3. Connection Pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Max 10 connections
    max_overflow=20,  # Max 30 total connections
    pool_timeout=30,  # Wait 30s for connection
    pool_recycle=3600,  # Recycle connections after 1 hour
)
```

**Expected Impact:**
- Connection overhead: -50%
- Concurrent request handling: +100%

### 4. Database Vacuum

```bash
# Optimize database file
sqlite3 turkiye_sinav.db "VACUUM;"

# Analyze statistics
sqlite3 turkiye_sinav.db "ANALYZE;"
```

**Expected Impact:**
- Database size: -30%
- Query time: -10%

## Parallel Processing Optimization

### 1. Increase Parallelism

#### Current Configuration

```python
MAX_PARALLEL_SEARCHES = 3
```

#### Optimization

```python
# Increase to 5 parallel searches
MAX_PARALLEL_SEARCHES = 5

# Expected impact:
# - Response time: 2.4s → 1.8s
# - CPU usage: +30%
# - Memory usage: +20%
```

### 2. Async Optimization

#### Use asyncio.gather with return_exceptions

```python
async def discover_videos_parallel(
    goals: List[str],
    profile: StudentProfile
) -> List[VideoRecommendation]:
    """
    Parallel video discovery with error handling
    """
    tasks = [
        discover_videos_for_goal(goal, profile)
        for goal in goals[:MAX_PARALLEL_SEARCHES]
    ]
    
    # Execute in parallel, don't fail on single error
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid_results = [
        r for r in results
        if not isinstance(r, Exception)
    ]
    
    # Log exceptions
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Video discovery failed: {r}")
    
    return valid_results
```

### 3. Thread Pool for Blocking Operations

```python
import concurrent.futures

executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

async def blocking_operation():
    """
    Run blocking operation in thread pool
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        sync_blocking_function
    )
    return result
```

## Response Optimization

### 1. Response Compression

```python
from fastapi.responses import Response
import gzip

@router.post("/recommendations")
async def get_recommendations(
    request: StudentProfileRequest,
    response: Response
):
    recommendations = await service.get_recommendations(request)
    
    # Serialize
    json_data = json.dumps(recommendations)
    
    # Compress if large (>1KB)
    if len(json_data) > 1024:
        compressed = gzip.compress(json_data.encode())
        response.headers["Content-Encoding"] = "gzip"
        return Response(
            content=compressed,
            media_type="application/json"
        )
    
    return recommendations
```

**Expected Impact:**
- Response size: -70%
- Transfer time: -60%
- CPU usage: +5%

### 2. Response Pagination

```python
@router.post("/recommendations")
async def get_recommendations(
    request: StudentProfileRequest,
    page: int = 1,
    page_size: int = 20
):
    """
    Paginated response
    """
    all_recommendations = await service.get_recommendations(request)
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_recommendations[start:end]
    
    return {
        "data": paginated,
        "page": page,
        "page_size": page_size,
        "total": len(all_recommendations),
        "has_next": end < len(all_recommendations)
    }
```

### 3. Field Selection

```python
@router.post("/recommendations")
async def get_recommendations(
    request: StudentProfileRequest,
    fields: Optional[List[str]] = None
):
    """
    Return only requested fields
    """
    recommendations = await service.get_recommendations(request)
    
    if fields:
        # Filter fields
        filtered = [
            {k: v for k, v in rec.items() if k in fields}
            for rec in recommendations
        ]
        return filtered
    
    return recommendations
```

## Rate Limiting Optimization

### 1. Adaptive Rate Limiting

```python
class AdaptiveRateLimiter:
    def __init__(self):
        self.base_limit = 10  # req/min
        self.max_limit = 100
        self.current_load = 0
    
    def get_limit(self, user_type: str) -> int:
        """
        Adjust rate limit based on system load
        """
        if self.current_load < 0.5:
            # Low load: Allow more requests
            return self.max_limit
        elif self.current_load < 0.8:
            # Medium load: Normal limit
            return self.base_limit * 2
        else:
            # High load: Strict limit
            return self.base_limit
    
    async def update_load(self):
        """
        Update current system load
        """
        # CPU usage, memory usage, active requests, etc.
        self.current_load = await get_system_load()
```

### 2. Token Bucket Algorithm

```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def _refill(self):
        """
        Refill tokens based on time elapsed
        """
        now = time.time()
        elapsed = now - self.last_refill
        
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        
        self.last_refill = now
```

## YouTube API Optimization

### 1. Quota Management

```python
class YouTubeQuotaManager:
    def __init__(self):
        self.daily_quota = 10000
        self.used_quota = 0
        self.quota_reset_time = None
    
    async def check_quota(self, cost: int) -> bool:
        """
        Check if enough quota available
        """
        if self.used_quota + cost > self.daily_quota:
            # Quota exceeded, use cache only
            logger.warning("YouTube API quota exceeded, using cache only")
            return False
        
        return True
    
    async def consume_quota(self, cost: int):
        """
        Consume quota
        """
        self.used_quota += cost
        
        # Log quota usage
        remaining = self.daily_quota - self.used_quota
        logger.info(f"YouTube API quota: {remaining} remaining")
        
        # Alert if low
        if remaining < 1000:
            await send_alert("YouTube API quota running low")
```

### 2. Request Batching

```python
async def batch_youtube_requests(video_ids: List[str]) -> List[Video]:
    """
    Batch multiple video requests into one API call
    """
    # YouTube API allows up to 50 IDs per request
    batch_size = 50
    
    results = []
    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i+batch_size]
        
        # Single API call for batch
        response = await youtube_api.videos().list(
            part='snippet,statistics',
            id=','.join(batch)
        ).execute()
        
        results.extend(response['items'])
    
    return results
```

**Expected Impact:**
- API calls: -80%
- Quota usage: -80%
- Response time: -50%

## Monitoring and Profiling

### 1. Performance Profiling

```python
import cProfile
import pstats

# Profile function
profiler = cProfile.Profile()
profiler.enable()

# Run function
await service.get_recommendations(profile)

profiler.disable()

# Print stats
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### 2. Memory Profiling

```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Run function
await service.get_recommendations(profile)

# Get memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

# Stop tracing
tracemalloc.stop()
```

### 3. Request Tracing

```python
import time

class RequestTracer:
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.spans = []
    
    def start_span(self, name: str):
        """Start timing a span"""
        return Span(name, self)
    
    def add_span(self, name: str, duration_ms: float):
        """Add completed span"""
        self.spans.append({
            'name': name,
            'duration_ms': duration_ms
        })
    
    def get_trace(self):
        """Get full trace"""
        return {
            'request_id': self.request_id,
            'total_duration_ms': sum(s['duration_ms'] for s in self.spans),
            'spans': self.spans
        }

class Span:
    def __init__(self, name: str, tracer: RequestTracer):
        self.name = name
        self.tracer = tracer
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        duration_ms = (time.time() - self.start_time) * 1000
        self.tracer.add_span(self.name, duration_ms)

# Usage
tracer = RequestTracer(request_id)

with tracer.start_span('cache_lookup'):
    await cache.get(key)

with tracer.start_span('video_discovery'):
    await discover_videos()

with tracer.start_span('filtering'):
    await filter_videos()

# Log trace
logger.info("request_trace", **tracer.get_trace())
```

## Load Testing

### 1. Locust Load Test

```python
# load_test.py
from locust import HttpUser, task, between

class VideoAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_recommendations(self):
        """Most common task"""
        self.client.post(
            "/api/youtube/recommendations",
            json={
                "goals": ["TYT Matematik"],
                "currentLevel": {"matematik": 50},
                "learningStyle": "visual"
            }
        )
    
    @task(1)
    def health_check(self):
        """Less frequent task"""
        self.client.get("/api/youtube/health")

# Run: locust -f load_test.py --host=http://localhost:8000
```

### 2. Load Test Scenarios

**Scenario 1: Normal Load**
```bash
locust -f load_test.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m
```

**Scenario 2: Peak Load**
```bash
locust -f load_test.py \
  --host=http://localhost:8000 \
  --users 200 \
  --spawn-rate 20 \
  --run-time 10m
```

**Scenario 3: Stress Test**
```bash
locust -f load_test.py \
  --host=http://localhost:8000 \
  --users 500 \
  --spawn-rate 50 \
  --run-time 15m
```

### 3. Performance Benchmarks

```bash
# Apache Bench
ab -n 1000 -c 10 -p request.json -T application/json \
  http://localhost:8000/api/youtube/recommendations

# wrk
wrk -t4 -c100 -d30s --latency \
  -s post.lua \
  http://localhost:8000/api/youtube/recommendations
```

## Horizontal Scaling

### 1. Multiple Workers

```bash
# Uvicorn with multiple workers
uvicorn main:app --workers 4 --port 8000

# Gunicorn with Uvicorn workers
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 2. Load Balancer

```nginx
# nginx.conf
upstream backend {
    least_conn;  # Load balancing method
    
    server backend1:8000 weight=1;
    server backend2:8000 weight=1;
    server backend3:8000 weight=1;
}

server {
    listen 80;
    
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Kubernetes Auto-Scaling

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: video-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: video-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Performance Checklist

### Before Deployment

- [ ] Load testing completed (50, 100, 200 users)
- [ ] Cache hit rate >80%
- [ ] P95 response time <3s
- [ ] Database indexes optimized
- [ ] Connection pooling configured
- [ ] Response compression enabled
- [ ] Rate limiting configured
- [ ] Monitoring and alerting setup
- [ ] Error handling tested
- [ ] Circuit breaker tested

### After Deployment

- [ ] Monitor metrics for 24 hours
- [ ] Check error rate (<1%)
- [ ] Verify cache hit rate (>80%)
- [ ] Review slow queries
- [ ] Check memory usage
- [ ] Verify auto-scaling works
- [ ] Test failover scenarios
- [ ] Review logs for issues

## Conclusion

Performance optimization is an ongoing process. Continuously monitor metrics, identify bottlenecks, and apply optimizations incrementally. Always measure the impact of changes and be prepared to rollback if needed.

**Key Takeaways:**
1. Cache aggressively (multi-layer strategy)
2. Optimize database queries (indexes, prepared statements)
3. Use parallel processing (asyncio.gather)
4. Compress responses (gzip)
5. Monitor and profile regularly
6. Scale horizontally when needed

**Next Steps:**
1. Implement cache warming
2. Optimize database indexes
3. Increase parallelism
4. Setup load testing pipeline
5. Configure auto-scaling
