# Video Recommendation API - Troubleshooting Guide

## Genel Bakış

Bu doküman, Video Recommendation API ile ilgili yaygın sorunları ve çözümlerini içerir.

## İçindekiler

- [Hızlı Tanı](#hızlı-tanı)
- [Yaygın Sorunlar](#yaygın-sorunlar)
- [Performans Sorunları](#performans-sorunları)
- [Bağlantı Sorunları](#bağlantı-sorunları)
- [Cache Sorunları](#cache-sorunları)
- [Hata Kodları](#hata-kodları)
- [Monitoring ve Debugging](#monitoring-ve-debugging)
- [Destek](#destek)

## Hızlı Tanı

### 1. Sağlık Kontrolü

İlk olarak servis sağlığını kontrol edin:

```bash
curl http://localhost:8000/api/youtube/health
```

**Beklenen Yanıt:**
```json
{
  "status": "healthy",
  "components": [...]
}
```

**Sorunlu Yanıt:**
```json
{
  "status": "unhealthy",
  "components": [
    {
      "name": "YouTube API",
      "status": "unhealthy",
      "error_message": "API key invalid"
    }
  ]
}
```

### 2. API Erişilebilirlik Testi

Backend'in erişilebilir olduğunu doğrulayın:

```bash
curl http://localhost:8000/api/youtube/test
```

**Beklenen Yanıt:**
```json
{
  "status": "ok",
  "message": "YouTube API service is reachable"
}
```

### 3. Log Kontrolü

Backend loglarını kontrol edin:

```bash
# Docker
docker logs backend-container

# Local
tail -f backend/app.log

# Kubernetes
kubectl logs -f deployment/video-api
```

## Yaygın Sorunlar

### Sorun 1: "Videoları 10 saniye içinde yükleyemedik"

**Semptomlar:**
- Frontend timeout hatası
- Fallback videolar gösteriliyor
- Kişiselleştirilmiş videolar yüklenmiyor

**Olası Nedenler:**

#### 1.1 Backend Servisi Çalışmıyor

**Tanı:**
```bash
# Backend process kontrolü
ps aux | grep uvicorn

# Port kontrolü
netstat -an | grep 8000
```

**Çözüm:**
```bash
# Backend'i başlat
cd backend
uvicorn main:app --reload --port 8000
```

#### 1.2 YouTube API Key Geçersiz

**Tanı:**
```bash
# Health check
curl http://localhost:8000/api/youtube/health

# Log kontrolü
grep "YouTube API" backend/app.log
```

**Çözüm:**
```bash
# .env dosyasını kontrol et
cat backend/.env | grep YOUTUBE_API_KEY

# Yeni API key al
# https://console.cloud.google.com/apis/credentials

# .env dosyasını güncelle
echo "YOUTUBE_API_KEY=your_new_key" >> backend/.env

# Backend'i yeniden başlat
```

#### 1.3 CORS Hatası

**Tanı:**
```javascript
// Browser console
// Error: CORS policy: No 'Access-Control-Allow-Origin' header
```

**Çözüm:**
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Frontend URL'ini ekle
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 1.4 Database Bağlantı Hatası

**Tanı:**
```bash
# Database dosyası var mı?
ls -la backend/turkiye_sinav.db

# Log kontrolü
grep "Database" backend/app.log
```

**Çözüm:**
```bash
# Database'i oluştur
cd backend
python init_db.py

# Permissions kontrolü
chmod 644 turkiye_sinav.db
```

#### 1.5 Redis Cache Erişilemiyor

**Tanı:**
```bash
# Redis çalışıyor mu?
redis-cli ping
# Beklenen: PONG

# Health check
curl http://localhost:8000/api/youtube/health | jq '.components[] | select(.name=="Redis Cache")'
```

**Çözüm:**
```bash
# Redis'i başlat
redis-server

# Docker ile
docker run -d -p 6379:6379 redis:alpine

# Kubernetes ile
kubectl apply -f k8s/redis-deployment.yaml
```

### Sorun 2: Yavaş Yanıt Süresi (>3 saniye)

**Semptomlar:**
- Video yükleme 3 saniyeden uzun sürüyor
- Kullanıcı deneyimi kötü
- Timeout riski

**Olası Nedenler:**

#### 2.1 Cache Hit Rate Düşük

**Tanı:**
```bash
# Metrics kontrolü
curl http://localhost:8000/metrics | grep cache_hit_rate

# Health check
curl http://localhost:8000/api/youtube/health | jq '.metrics.cache_hit_rate_1h'
```

**Beklenen:** >0.80 (80%)  
**Sorunlu:** <0.60 (60%)

**Çözüm:**
```python
# Cache TTL'i artır
# backend/services/video_recommendation_service.py
await self.cache.set(
    cache_key,
    recommendations,
    ttl=7200  # 1 saat → 2 saat
)

# Cache warming stratejisi ekle
async def warm_cache():
    popular_profiles = get_popular_student_profiles()
    for profile in popular_profiles:
        await service.get_recommendations(profile)
```

#### 2.2 Database Query Yavaş

**Tanı:**
```bash
# Query performance analizi
sqlite3 backend/turkiye_sinav.db
> EXPLAIN QUERY PLAN SELECT * FROM video_cache WHERE subject='matematik';
```

**Çözüm:**
```sql
-- Index'leri kontrol et
SELECT name FROM sqlite_master WHERE type='index';

-- Eksik index'leri ekle
CREATE INDEX IF NOT EXISTS idx_video_search 
ON video_cache(subject, difficulty, exam_type, language, quality_score DESC);

-- Vacuum yap (optimize)
VACUUM;
```

#### 2.3 Paralel Arama Çalışmıyor

**Tanı:**
```python
# Log kontrolü
grep "parallel" backend/app.log

# Response time breakdown
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/youtube/recommendations
```

**Çözüm:**
```python
# backend/services/video_recommendation_service.py
# asyncio.gather kullanıldığından emin ol
results = await asyncio.gather(*tasks, return_exceptions=True)

# Max parallel searches'i artır
MAX_PARALLEL_SEARCHES = 5  # 3 → 5
```

### Sorun 3: Rate Limit Hatası (429)

**Semptomlar:**
- "Too Many Requests" hatası
- Kullanıcı istekleri reddediliyor

**Tanı:**
```bash
# Rate limit headers kontrolü
curl -I http://localhost:8000/api/youtube/recommendations

# Beklenen headers:
# X-RateLimit-Limit: 10
# X-RateLimit-Remaining: 7
# X-RateLimit-Reset: 1698840000
```

**Çözüm:**

#### 3.1 Geçici Çözüm (Development)
```python
# backend/api/youtube_routes.py
# Rate limit'i artır
@limiter.limit("30/minute")  # 10 → 30
async def get_recommendations():
    pass
```

#### 3.2 Kalıcı Çözüm (Production)
```python
# Authenticated user'lara daha yüksek limit
@limiter.limit("10/minute", key_func=get_ip_address)
@limiter.limit("30/minute", key_func=get_user_id)
async def get_recommendations():
    pass
```

### Sorun 4: Türkçe Olmayan Videolar Geliyor

**Semptomlar:**
- İngilizce veya başka dilde videolar
- Türkçe filtre çalışmıyor

**Tanı:**
```bash
# Video response kontrolü
curl -X POST http://localhost:8000/api/youtube/recommendations \
  -H "Content-Type: application/json" \
  -d '{"goals":["TYT Matematik"],"currentLevel":{"matematik":50},"learningStyle":"visual"}' \
  | jq '.[] | .videos[] | {title, language_score}'
```

**Beklenen:** `language_score > 0.8`

**Çözüm:**
```python
# backend/services/turkish_content_filter.py
# Language score threshold'u artır
MIN_LANGUAGE_SCORE = 0.9  # 0.8 → 0.9

# Trusted Turkish channels listesini genişlet
TRUSTED_TURKISH_CHANNELS = [
    'tonguç akademi',
    'matematik öğretmeni',
    # ... daha fazla kanal ekle
]

# Turkish character detection'ı güçlendir
def _calculate_turkish_char_ratio(self, text: str) -> float:
    if not text:
        return 0.0
    
    turkish_count = sum(1 for c in text if c in self.TURKISH_CHARS)
    total_alpha = sum(1 for c in text if c.isalpha())
    
    if total_alpha == 0:
        return 0.0
    
    # Bonus'u artır
    return min(1.0, turkish_count / total_alpha * 10)  # 5 → 10
```

### Sorun 5: Circuit Breaker Açık (503)

**Semptomlar:**
- "Service Unavailable" hatası
- YouTube API'ye istek gitmiyor
- Sadece cache'den veri geliyor

**Tanı:**
```bash
# Circuit breaker state kontrolü
curl http://localhost:8000/metrics | grep circuit_breaker_state

# Log kontrolü
grep "circuit breaker" backend/app.log
```

**Çözüm:**

#### 5.1 Manuel Reset
```python
# backend/core/circuit_breaker.py
# Circuit breaker'ı manuel reset et
circuit_breaker.reset()
```

#### 5.2 Otomatik Recovery Bekle
```bash
# 60 saniye sonra otomatik olarak HALF_OPEN state'e geçer
# 2 başarılı istek sonrası CLOSED state'e döner
```

#### 5.3 Root Cause Analizi
```bash
# YouTube API neden başarısız?
curl "https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key=YOUR_API_KEY"

# Quota kontrolü
# https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
```

## Performans Sorunları

### Yüksek Memory Kullanımı

**Tanı:**
```bash
# Memory kullanımı
ps aux | grep uvicorn

# Docker
docker stats backend-container

# Kubernetes
kubectl top pod -l app=video-api
```

**Çözüm:**
```python
# In-memory cache size'ı azalt
MAX_MEMORY_CACHE_SIZE = 50  # 100 → 50

# Garbage collection'ı optimize et
import gc
gc.collect()

# Memory profiling
import tracemalloc
tracemalloc.start()
```

### Yüksek CPU Kullanımı

**Tanı:**
```bash
# CPU kullanımı
top -p $(pgrep -f uvicorn)

# Profiling
python -m cProfile -o profile.stats backend/main.py
```

**Çözüm:**
```python
# Worker sayısını artır
uvicorn main:app --workers 4

# Async operations'ı optimize et
# Blocking operations'ı thread pool'a taşı
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_function)
```

## Bağlantı Sorunları

### Frontend Backend'e Bağlanamıyor

**Tanı:**
```bash
# Network connectivity
ping localhost

# Port açık mı?
telnet localhost 8000

# Firewall kontrolü
sudo iptables -L
```

**Çözüm:**
```bash
# Backend'in doğru port'ta çalıştığından emin ol
netstat -an | grep 8000

# Frontend API_BASE_URL kontrolü
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000

# CORS ayarlarını kontrol et
# backend/main.py
```

### Database Lock Hatası

**Tanı:**
```bash
# Log kontrolü
grep "database is locked" backend/app.log
```

**Çözüm:**
```python
# Connection timeout'u artır
DATABASE_URL = "sqlite:///./turkiye_sinav.db?timeout=30"

# Write-Ahead Logging (WAL) mode
import sqlite3
conn = sqlite3.connect('turkiye_sinav.db')
conn.execute('PRAGMA journal_mode=WAL')

# PostgreSQL'e migrate et (production için)
DATABASE_URL = "postgresql://user:pass@localhost/dbname"
```

## Cache Sorunları

### Redis Connection Error

**Tanı:**
```bash
# Redis çalışıyor mu?
redis-cli ping

# Connection string kontrolü
echo $REDIS_URL
```

**Çözüm:**
```bash
# Redis'i başlat
redis-server

# Connection string'i düzelt
export REDIS_URL=redis://localhost:6379/0

# Redis password varsa
export REDIS_URL=redis://:password@localhost:6379/0
```

### Cache Invalidation Sorunu

**Tanı:**
```bash
# Cache içeriğini kontrol et
redis-cli KEYS "video_rec:*"

# Specific key kontrolü
redis-cli GET "video_rec:abc123"
```

**Çözüm:**
```bash
# Tüm cache'i temizle
redis-cli FLUSHDB

# Specific pattern'i temizle
redis-cli --scan --pattern "video_rec:*" | xargs redis-cli DEL

# TTL'i kontrol et
redis-cli TTL "video_rec:abc123"
```

## Hata Kodları

### HTTP Status Codes

| Kod | Açıklama | Çözüm |
|-----|----------|--------|
| 400 | Bad Request - Geçersiz istek | Request body'yi kontrol et |
| 401 | Unauthorized - Yetkilendirme gerekli | API key veya token ekle |
| 403 | Forbidden - Erişim yasak | Permissions kontrolü |
| 404 | Not Found - Endpoint bulunamadı | URL'yi kontrol et |
| 429 | Too Many Requests - Rate limit | Bekle ve tekrar dene |
| 500 | Internal Server Error - Sunucu hatası | Logları kontrol et |
| 503 | Service Unavailable - Servis kullanılamıyor | Health check yap |
| 504 | Gateway Timeout - Zaman aşımı | Timeout'u artır |

### Application Error Codes

| Error Type | Açıklama | Çözüm |
|-----------|----------|--------|
| `ValidationError` | Geçersiz input | Request parametrelerini düzelt |
| `CacheError` | Cache işlem hatası | Redis bağlantısını kontrol et |
| `YouTubeAPIError` | YouTube API hatası | API key ve quota kontrol et |
| `DatabaseError` | Database hatası | Database bağlantısını kontrol et |
| `TimeoutError` | İstek zaman aşımı | Timeout'u artır veya optimize et |
| `CircuitBreakerOpen` | Circuit breaker açık | Root cause'u çöz, bekle |
| `RateLimitError` | Rate limit aşıldı | Bekle veya limit artır |

## Monitoring ve Debugging

### Structured Logging

**Log Formatı:**
```json
{
  "timestamp": "2024-11-01T10:30:00Z",
  "level": "ERROR",
  "event": "video_request_error",
  "request_id": "req_abc123",
  "error_type": "YouTubeAPIError",
  "error_message": "API quota exceeded",
  "stack_trace": "...",
  "context": {
    "user_id": "user_123",
    "goals": ["TYT Matematik"]
  }
}
```

**Log Arama:**
```bash
# Specific request ID
grep "req_abc123" backend/app.log

# Error logs
grep '"level":"ERROR"' backend/app.log | jq

# Specific error type
grep "YouTubeAPIError" backend/app.log

# Time range
grep "2024-11-01T10:" backend/app.log
```

### Prometheus Metrics

**Metrics Endpoint:**
```bash
curl http://localhost:8000/metrics
```

**Önemli Metrikler:**
```
# Request rate
rate(video_requests_total[5m])

# Error rate
rate(video_requests_total{status="error"}[5m]) / rate(video_requests_total[5m])

# Response time (P95)
histogram_quantile(0.95, video_response_time_seconds)

# Cache hit rate
cache_hit_rate

# YouTube API quota
youtube_api_quota_remaining
```

### Grafana Dashboards

**Dashboard URL:** http://grafana.example.com/d/video-api

**Paneller:**
- Request Rate (req/s)
- Error Rate (%)
- Response Time (P50, P95, P99)
- Cache Hit Rate (%)
- YouTube API Quota
- Circuit Breaker State

### Debug Mode

**Development:**
```bash
# Debug mode ile başlat
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug

# Verbose logging
export PYTHONVERBOSE=1
```

**Request Tracing:**
```python
# Request ID ile trace et
import uuid

request_id = str(uuid.uuid4())
logger.info("request_start", request_id=request_id)

# Her log'da request_id kullan
logger.info("cache_lookup", request_id=request_id, cache_key=key)
logger.info("api_call", request_id=request_id, endpoint=endpoint)
logger.info("request_complete", request_id=request_id, duration_ms=duration)
```

## Destek

### Self-Service Resources

1. **Documentation**
   - [API Documentation](./VIDEO_API.md)
   - [Architecture](./ARCHITECTURE.md)
   - [Developer Setup](./DEVELOPER_SETUP.md)
   - [Performance Tuning](./PERFORMANCE_TUNING.md)

2. **Monitoring**
   - Grafana: http://grafana.example.com
   - Prometheus: http://prometheus.example.com
   - Logs: http://kibana.example.com

3. **Status Page**
   - https://status.teknofest-egitim.com

### Contact Support

**Email:** support@teknofest-egitim.com

**Slack Channels:**
- #video-api-support (Genel sorular)
- #video-api-incidents (Acil durumlar)
- #video-api-dev (Geliştirici soruları)

**GitHub Issues:**
- https://github.com/teknofest-2025-egitim-eylemci/issues

**On-Call (Acil Durumlar):**
- PagerDuty: +90 XXX XXX XX XX
- Email: oncall@teknofest-egitim.com

### Incident Reporting

**Acil Durum Prosedürü:**

1. **Assess Severity**
   - P0: Servis tamamen down
   - P1: Kritik özellik çalışmıyor
   - P2: Performans sorunu
   - P3: Minor bug

2. **Create Incident**
   - Slack: `/incident create` in #video-api-incidents
   - PagerDuty: Otomatik alert
   - Email: oncall@teknofest-egitim.com

3. **Gather Information**
   - Error messages
   - Request IDs
   - Timestamps
   - Affected users
   - Reproduction steps

4. **Follow Up**
   - Incident timeline
   - Root cause analysis
   - Action items
   - Post-mortem

## Checklist: Sorun Giderme Adımları

Bir sorunla karşılaştığınızda, sırasıyla şu adımları izleyin:

- [ ] Health check endpoint'ini kontrol et
- [ ] Backend loglarını incele
- [ ] Metrics'leri kontrol et (Grafana)
- [ ] Database bağlantısını test et
- [ ] Redis bağlantısını test et
- [ ] YouTube API key'i doğrula
- [ ] CORS ayarlarını kontrol et
- [ ] Rate limit durumunu kontrol et
- [ ] Circuit breaker state'ini kontrol et
- [ ] Cache hit rate'i kontrol et
- [ ] Network connectivity'yi test et
- [ ] Environment variables'ı doğrula
- [ ] Recent deployments'ı kontrol et
- [ ] Known issues'ı kontrol et
- [ ] Destek ekibine ulaş

## Sık Sorulan Sorular (FAQ)

**S: Video önerileri neden bazen yavaş?**  
C: Cache miss olduğunda YouTube API'ye istek gider, bu 2-5 saniye sürebilir. Cache hit rate'i artırmak için cache TTL'i uzatabilir veya cache warming stratejisi uygulayabilirsiniz.

**S: Neden bazı videolar Türkçe değil?**  
C: Language detection %100 doğru değildir. MIN_LANGUAGE_SCORE threshold'unu artırarak veya TRUSTED_TURKISH_CHANNELS listesini genişleterek filtrelemeyi güçlendirebilirsiniz.

**S: Rate limit'e neden takılıyorum?**  
C: Anonymous kullanıcılar için dakikada 10 istek limiti vardır. Authenticated kullanıcılar için limit 30'dur. Production'da bu limitler artırılabilir.

**S: Circuit breaker neden açıldı?**  
C: YouTube API 5 kez üst üste başarısız olduğunda circuit breaker açılır. 60 saniye sonra otomatik olarak test moduna geçer. Root cause'u (API key, quota, network) çözmeniz gerekir.

**S: Cache nasıl temizlenir?**  
C: `redis-cli FLUSHDB` komutu ile tüm cache temizlenebilir. Specific pattern için `redis-cli --scan --pattern "video_rec:*" | xargs redis-cli DEL` kullanın.

**S: Loglar nerede?**  
C: Backend logları `backend/app.log` dosyasında. Docker için `docker logs backend-container`, Kubernetes için `kubectl logs -f deployment/video-api`.

**S: Metrics nasıl görüntülenir?**  
C: Prometheus metrics: `http://localhost:8000/metrics`, Grafana dashboard: http://grafana.example.com/d/video-api

**S: Production'da sorun nasıl raporlanır?**  
C: Slack #video-api-incidents kanalında `/incident create` komutu ile veya oncall@teknofest-egitim.com email'ine.
