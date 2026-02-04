# Video Recommendation System - Architecture

## System Overview

Video Recommendation System, öğrencilere kişiselleştirilmiş YouTube eğitim videoları öneren, yüksek performanslı ve güvenilir bir servistir. Sistem, Türkçe içerik filtreleme, MEB müfredatı uyumluluğu ve zorluk seviyesi eşleştirmesi ile kaliteli öneriler sunar.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Learning Path Page (main.tsx)                           │  │
│  │  - Video Loading State Management                        │  │
│  │  - Error Handling & Retry Logic                          │  │
│  │  - User Feedback & Progress Indicators                   │  │
│  │  - Offline Mode & Network Detection                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST /api/youtube/recommendations
                              │ (20s timeout, retry logic)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Startup Health Check                                    │  │
│  │  - Database connectivity verification                    │  │
│  │  - Redis cache availability check                        │  │
│  │  - YouTube API connection test                           │  │
│  │  - CORS configuration validation                         │  │
│  │  - Structured logging initialization                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Layer (youtube_routes.py)                           │  │
│  │  - Request Validation                                    │  │
│  │  - Rate Limiting & Throttling                            │  │
│  │  - Health Check Endpoints                                │  │
│  │  - Circuit Breaker Protection                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Service Layer                                           │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  VideoRecommendationService                        │ │  │
│  │  │  - Orchestrates video discovery                    │ │  │
│  │  │  - Multi-layer cache management                    │ │  │
│  │  │  - Parallel video search execution                 │ │  │
│  │  │  - Request ID tracking                             │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  TurkishContentFilter                              │ │  │
│  │  │  - Multi-signal language detection                │ │  │
│  │  │  - MEB curriculum-based relevance scoring         │ │  │
│  │  │  - Adaptive difficulty matching                   │ │  │
│  │  │  - Subject taxonomy categorization                │ │  │
│  │  │  - Trusted channel verification                   │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  HealthCheckService                                │ │  │
│  │  │  - Component health monitoring                     │ │  │
│  │  │  - System metrics collection                       │ │  │
│  │  │  - Startup validation                              │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Layer                                              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │  │
│  │  │   Redis    │  │  SQLite    │  │  YouTube Data API  │ │  │
│  │  │   Cache    │  │  Database  │  │       v3           │ │  │
│  │  │ (Multi-    │  │ (Indexed)  │  │  (Rate Limited)    │ │  │
│  │  │  Layer)    │  │            │  │                    │ │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Frontend Layer

#### VideoLoadingManager
**Sorumluluk:** Merkezi video yükleme state management

**Özellikler:**
- State management (idle, loading, success, error, fallback)
- Request lifecycle yönetimi
- Retry logic (exponential backoff)
- Request cancellation (AbortController)
- Progress tracking

**State Machine:**
```
idle → loading → success
              → error → retry → loading
                     → fallback
```

#### NetworkStatusManager
**Sorumluluk:** Ağ durumu izleme ve offline mode

**Özellikler:**
- Online/offline detection
- Connection quality monitoring
- Auto-retry on reconnection
- Offline data caching

#### VideoErrorHandler
**Sorumluluk:** Hata yönetimi ve kullanıcı geri bildirimi

**Özellikler:**
- Error classification
- User-friendly messages
- Retry decision logic
- Error logging (Sentry)

### 2. Backend API Layer

#### youtube_routes.py
**Sorumluluk:** HTTP endpoint'leri ve request handling

**Endpoints:**
- `POST /api/youtube/recommendations` - Video önerileri
- `GET /api/youtube/health` - Sağlık kontrolü
- `GET /api/youtube/test` - API erişilebilirlik testi

**Middleware:**
- CORS handling
- Rate limiting (SlowAPI)
- Request validation (Pydantic)
- Error handling
- Structured logging

### 3. Service Layer

#### VideoRecommendationService
**Sorumluluk:** Video öneri orchestration

**İş Akışı:**
1. Cache key generation (student profile hash)
2. Multi-layer cache lookup
3. Cache miss → Parallel video discovery
4. Turkish content filtering
5. Quality scoring and ranking
6. Cache update
7. Metrics recording

**Optimizasyonlar:**
- Parallel video search (asyncio.gather)
- Multi-layer caching
- Request deduplication
- Response compression

#### TurkishContentFilter
**Sorumluluk:** Türkçe içerik doğrulama ve filtreleme

**Filtreleme Kriterleri:**
1. **Language Detection (Multi-Signal)**
   - Title language detection (langdetect)
   - Description language detection
   - Turkish character presence (ç, ğ, ı, ö, ş, ü)
   - Trusted Turkish channel verification

2. **Relevance Scoring (MEB Curriculum)**
   - Subject keyword matching
   - Sub-topic keyword matching
   - Semantic similarity
   - Taxonomy-based categorization

3. **Difficulty Matching**
   - Student level analysis
   - Video difficulty estimation
   - ±1 level tolerance
   - Adaptive progression

**Scoring Formula:**
```
overall_score = (language_score * 0.3) + 
                (relevance_score * 0.5) + 
                (difficulty_match * 0.2)
```

**Pass Threshold:** 0.7 overall score

#### HealthCheckService
**Sorumluluk:** Sistem sağlık izleme

**Kontroller:**
- YouTube API connectivity
- Database connectivity
- Redis cache availability
- System metrics collection

**Startup Health Check:**
- Tüm kritik bağımlılıkları doğrula
- Başarısız servisleri WARNING seviyesinde logla
- Kısmi işlevsellik ile başlamaya izin ver
- Metrics'e raporla

### 4. Data Layer

#### Multi-Layer Cache

```
┌─────────────────────────────────────────────────────────┐
│                    Cache Layers                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Layer 1: In-Memory Cache (LRU)                         │
│  - Size: 100 entries                                     │
│  - TTL: 5 minutes                                        │
│  - Hit rate: ~40%                                        │
│  - Response time: <10ms                                  │
│                                                           │
│  Layer 2: Redis Cache                                    │
│  - Size: 10,000 entries                                  │
│  - TTL: 1 hour                                           │
│  - Hit rate: ~40%                                        │
│  - Response time: <100ms                                 │
│                                                           │
│  Layer 3: Database Cache                                 │
│  - Size: Unlimited                                       │
│  - TTL: 24 hours                                         │
│  - Hit rate: ~15%                                        │
│  - Response time: <500ms                                 │
│                                                           │
│  Layer 4: YouTube API (Cache Miss)                       │
│  - Hit rate: ~5%                                         │
│  - Response time: 2-5 seconds                            │
│                                                           │
└─────────────────────────────────────────────────────────┘

Total Cache Hit Rate: ~95%
Average Response Time: <200ms
```

**Cache Promotion Strategy:**
- Redis hit → Promote to memory cache
- Database hit → Promote to Redis cache
- YouTube API hit → Write to all cache layers

**Cache Invalidation:**
- TTL-based expiration
- Manual invalidation on content update
- LRU eviction on capacity limit

#### Database Schema

```sql
-- Video cache table
CREATE TABLE video_cache (
    id INTEGER PRIMARY KEY,
    video_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    exam_type TEXT NOT NULL,
    language TEXT NOT NULL,
    quality_score REAL NOT NULL,
    relevance_score REAL NOT NULL,
    language_score REAL NOT NULL,
    difficulty_match REAL NOT NULL,
    overall_score REAL NOT NULL,
    metadata TEXT NOT NULL,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast lookup
CREATE INDEX idx_video_subject ON video_cache(
    subject, difficulty, exam_type
);
CREATE INDEX idx_video_quality ON video_cache(quality_score DESC);
CREATE INDEX idx_video_language ON video_cache(language);
CREATE INDEX idx_video_updated ON video_cache(last_updated DESC);

-- Composite index for common queries
CREATE INDEX idx_video_search ON video_cache(
    subject, difficulty, exam_type, language, quality_score DESC
);
```

## Request Flow

### Successful Request Flow

```
1. User opens Learning Path page
   ↓
2. Frontend: Initialize VideoLoadingManager
   ↓
3. Frontend: Show loading indicator
   ↓
4. Frontend: POST /api/youtube/recommendations
   - Timeout: 20 seconds
   - Retry: 2 attempts with exponential backoff
   ↓
5. Backend: Receive request
   ↓
6. Backend: Generate request_id, log request
   ↓
7. Backend: Check rate limit
   ↓
8. Backend: Check cache (Layer 1: Memory)
   ↓
9a. Cache HIT (40% of requests)
   ↓
   Return cached videos (<10ms)
   ↓
   Go to step 16
   
9b. Cache MISS
   ↓
10. Backend: Check cache (Layer 2: Redis)
   ↓
11a. Cache HIT (40% of requests)
   ↓
   Promote to memory cache
   Return cached videos (<100ms)
   ↓
   Go to step 16

11b. Cache MISS
   ↓
12. Backend: VideoRecommendationService.get_recommendations()
   ↓
13. For each goal (parallel execution):
    ↓
    13a. AdvancedYouTubeSearch.search_videos()
    ↓
    13b. SemanticYouTubeSearch.search_videos()
    ↓
    13c. Merge and deduplicate results
    ↓
    13d. TurkishContentFilter.filter_videos()
         - Language detection (>0.8 score)
         - Relevance scoring (>0.7 score)
         - Difficulty matching (±1 level)
    ↓
    13e. Sort by overall_score
    ↓
    13f. Take top 5 videos per subject
    ↓
14. Backend: Aggregate all results
    ↓
15. Backend: Cache results (all layers)
    ↓
16. Backend: Log metrics (response time, cache status)
    ↓
17. Backend: Return response
    - Status: 200 OK
    - Body: { recommendations: [...], total_count: X }
    ↓
18. Frontend: Receive response
    ↓
19. Frontend: Update UI with videos
    - Show success message
    - Display video cards
    - Enable video playback
    ↓
20. Frontend: Log success metrics
```

### Error Flow

```
ERROR SCENARIOS:

1. Timeout (20s)
   ↓
   Frontend: Show fallback videos
   Frontend: Offer retry option
   Frontend: Log timeout error

2. 500 Internal Server Error
   ↓
   Backend: Log error with stack trace
   Backend: Record error metrics
   Frontend: Show user-friendly message
   Frontend: Offer retry option

3. Network Error
   ↓
   Frontend: Check network connectivity
   Frontend: Show offline message
   Frontend: Auto-retry on reconnection

4. CORS Error
   ↓
   Backend: Add CORS headers
   Frontend: Log to Sentry
   Frontend: Contact admin

5. Rate Limit (429)
   ↓
   Backend: Return retry_after
   Frontend: Wait and auto-retry
   Frontend: Show waiting message

6. Circuit Breaker Open (503)
   ↓
   Backend: Return cached data
   Backend: Log circuit breaker status
   Frontend: Show degraded service message
```

## Startup Sequence

```
1. Backend Application Start
   ↓
2. Initialize Configuration
   - Load environment variables
   - Validate API keys
   - Set CORS origins
   ↓
3. Initialize Structured Logging
   - Configure JSON format
   - Set log levels
   ↓
4. Health Check: Database
   - Test connection
   - Verify schema
   - Log result (INFO/WARNING)
   ↓
5. Health Check: Redis Cache
   - Test connection
   - Verify read/write
   - Log result (INFO/WARNING)
   ↓
6. Health Check: YouTube API
   - Test API key validity
   - Check quota availability
   - Log result (INFO/WARNING)
   ↓
7. Initialize Services
   - VideoRecommendationService
   - TurkishContentFilter
   - HealthCheckService
   ↓
8. Register API Routes
   - /api/youtube/recommendations
   - /api/youtube/health
   - /api/youtube/test
   ↓
9. Start Metrics Collection
   - Prometheus endpoint
   - Initial metrics
   ↓
10. Application Ready
    - Log startup summary
    - Report to metrics
    - Accept requests

Note: Kritik servis başarısız olsa bile uygulama başlar,
ancak WARNING seviyesinde log kaydedilir ve metrics'e raporlanır.
```

## Reliability Patterns

### Circuit Breaker

**Purpose:** Başarısız servisleri geçici olarak devre dışı bırakarak cascading failure'ları önler.

**States:**
- **CLOSED:** Normal operation, istekler geçer
- **OPEN:** Servis başarısız, istekler reddedilir
- **HALF_OPEN:** Test mode, sınırlı istekler geçer

**Configuration:**
- Failure threshold: 5 başarısız istek
- Timeout: 60 saniye
- Success threshold (half-open): 2 başarılı istek

**Flow:**
```
CLOSED → (5 failures) → OPEN → (60s timeout) → HALF_OPEN
                                                    ↓
                                    (2 successes) → CLOSED
                                    (1 failure) → OPEN
```

### Retry Logic

**Strategy:** Exponential backoff with jitter

**Configuration:**
- Max retries: 2
- Base delay: 1 second
- Backoff multiplier: 2
- Max delay: 10 seconds

**Retryable Errors:**
- Timeout errors
- Network errors
- 5xx server errors
- Cache errors

**Non-Retryable Errors:**
- 4xx client errors (except 429)
- Validation errors
- Authentication errors

### Graceful Degradation

**Fallback Strategy:**

1. **Primary:** YouTube API + Full filtering
2. **Fallback 1:** Cached data (recent)
3. **Fallback 2:** Database cache (older)
4. **Fallback 3:** Static example videos

**Degradation Levels:**
- **Level 0:** Full functionality
- **Level 1:** Cache-only mode (no new videos)
- **Level 2:** Database-only mode (no Redis)
- **Level 3:** Static content mode

## Performance Optimization

### Parallel Processing

**Video Discovery:**
- Multiple goals processed in parallel (asyncio.gather)
- Maximum 3 parallel searches
- Exception handling per search

**Performance Gain:** 3x faster than sequential

### Database Optimization

**Indexing:**
- Composite index on (subject, difficulty, exam_type, language, quality_score)
- Individual indexes on frequently queried fields
- Covering indexes for common queries

**Query Optimization:**
- Prepared statements
- Connection pooling
- Query result caching

**Performance Gain:** 10x faster queries

### Response Compression

**Strategy:**
- Gzip compression for responses >1KB
- Content-Encoding header
- Automatic decompression on client

**Performance Gain:** 70% bandwidth reduction

## Security

### Rate Limiting

**Tiers:**
- Anonymous: 10 req/min per IP
- Authenticated: 30 req/min per user
- YouTube API: Adaptive based on quota

**Implementation:** SlowAPI middleware

### Input Validation

**Strategy:**
- Pydantic models for request validation
- Field-level validators
- Input sanitization
- Max length limits

### CORS Policy

**Allowed Origins:**
- `http://localhost:3000` (dev)
- `http://localhost:3001` (dev)
- Production frontend URL (env var)

**Allowed Methods:** GET, POST, OPTIONS

**Allowed Headers:** Content-Type, Authorization

## Monitoring & Observability

### Metrics (Prometheus)

**Request Metrics:**
- `video_requests_total{status, cache_hit}`
- `video_response_time_seconds` (histogram)
- `video_errors_total{error_type}`

**Cache Metrics:**
- `cache_hit_rate` (gauge)
- `cache_size{layer}` (gauge)
- `cache_evictions_total{layer}`

**System Metrics:**
- `youtube_api_quota_remaining`
- `circuit_breaker_state{service}`
- `active_requests` (gauge)

### Logging (Structured)

**Format:** JSON (structlog)

**Log Levels:**
- DEBUG: Detailed debugging info
- INFO: Normal operations
- WARNING: Degraded service
- ERROR: Errors requiring attention
- CRITICAL: System failures

**Context Fields:**
- `request_id`: Unique request identifier
- `user_id`: User identifier (if authenticated)
- `endpoint`: API endpoint
- `response_time_ms`: Response time
- `cache_hit`: Cache hit/miss

### Alerting

**Alert Rules:**
- High error rate (>5% for 5 minutes)
- Slow response time (P95 >3s for 5 minutes)
- Low cache hit rate (<60% for 10 minutes)
- YouTube API quota low (<1000 remaining)
- Circuit breaker open

**Notification Channels:**
- Slack: #video-api-alerts
- Email: oncall@teknofest-egitim.com
- PagerDuty: Critical alerts

## Deployment

### Infrastructure

**Platform:** Kubernetes

**Resources:**
- CPU: 500m request, 1000m limit
- Memory: 512Mi request, 1Gi limit
- Replicas: 3 (production)

**Probes:**
- Liveness: `/api/youtube/health` (30s initial delay)
- Readiness: `/api/youtube/health` (5s initial delay)

### Deployment Strategy

**Type:** Rolling update

**Configuration:**
- Max surge: 1
- Max unavailable: 0
- Zero-downtime deployment

**Rollback:** Automatic on health check failure

### Environment Variables

```bash
# API Keys
YOUTUBE_API_KEY=your_api_key_here

# Database
DATABASE_URL=sqlite:///./turkiye_sinav.db

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
FRONTEND_URL=http://localhost:3001

# Performance
CACHE_TTL_SECONDS=3600
MAX_PARALLEL_SEARCHES=3
REQUEST_TIMEOUT_SECONDS=20

# Quality Thresholds
MIN_RELEVANCE_SCORE=0.7
MIN_LANGUAGE_SCORE=0.8
MIN_QUALITY_SCORE=7.0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_AUTHENTICATED=30
```

## Scalability

### Horizontal Scaling

**Current:** 3 replicas

**Auto-scaling:**
- Target CPU: 70%
- Min replicas: 3
- Max replicas: 10

### Vertical Scaling

**Current:** 512Mi memory, 500m CPU

**Limits:** 1Gi memory, 1000m CPU

### Database Scaling

**Current:** SQLite (single file)

**Future:** PostgreSQL with read replicas

### Cache Scaling

**Current:** Single Redis instance

**Future:** Redis Cluster with sharding

## Future Enhancements

### Short-term (1-3 months)
- [ ] JWT authentication
- [ ] User-specific caching
- [ ] A/B testing framework
- [ ] Advanced analytics
- [ ] Video quality prediction ML model

### Medium-term (3-6 months)
- [ ] PostgreSQL migration
- [ ] Redis Cluster
- [ ] GraphQL API
- [ ] Real-time recommendations
- [ ] Video transcript analysis

### Long-term (6-12 months)
- [ ] Microservices architecture
- [ ] Event-driven architecture
- [ ] Machine learning pipeline
- [ ] Multi-region deployment
- [ ] CDN integration

## References

- [API Documentation](./VIDEO_API.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Developer Setup Guide](./DEVELOPER_SETUP.md)
- [Performance Tuning Guide](./PERFORMANCE_TUNING.md)
