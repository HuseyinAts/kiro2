# Production Deployment Guide - Video Recommendation System
## Türkiye Üniversite Sınavları Hazırlık Platformu

Bu doküman, video öneri sisteminin production ortamına deploy edilmesi için gerekli tüm adımları içermektedir.

## İçindekiler

1. [Ön Hazırlık](#ön-hazırlık)
2. [Environment Variables](#environment-variables)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Rolling Deployment Stratejisi](#rolling-deployment-stratejisi)
6. [Rollback Planı](#rollback-planı)
7. [Production Monitoring](#production-monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Ön Hazırlık

### 1. Sistem Gereksinimleri

**Minimum Gereksinimler:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB SSD
- Network: 100 Mbps

**Önerilen Gereksinimler (Production):**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB SSD
- Network: 1 Gbps

### 2. Bağımlılıklar

```bash
# Docker & Docker Compose
docker --version  # >= 24.0.0
docker-compose --version  # >= 2.20.0

# Kubernetes (opsiyonel)
kubectl version --client  # >= 1.28.0
helm version  # >= 3.12.0

# Python (local development)
python --version  # >= 3.11.0
```

### 3. API Keys ve Secrets

Aşağıdaki API key'leri temin edin:

- **YouTube Data API v3**: https://console.cloud.google.com/apis/credentials
- **OpenAI API**: https://platform.openai.com/api-keys
- **HuggingFace API**: https://huggingface.co/settings/tokens
- **Sentry DSN**: https://sentry.io/settings/projects/

**Güvenlik Uyarısı:** API key'leri asla git repository'ye commit etmeyin!

---

## Environment Variables

### 1. Production Environment Dosyası Oluşturma

```bash
# .env.production dosyasını oluştur
cp .env.example .env.production
```

### 2. Kritik Değişkenler

`.env.production` dosyasında aşağıdaki değişkenleri mutlaka güncelleyin:

```bash
# ===== GENEL AYARLAR =====
NODE_ENV=production
DEBUG=false
SECRET_KEY=<GENERATE_SECURE_32_CHAR_KEY>
JWT_SECRET_KEY=<GENERATE_SECURE_32_CHAR_KEY>

# Güvenli key oluşturma:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ===== VERİTABANI =====
DATABASE_URL=postgresql+asyncpg://username:password@postgres-host:5432/turkiye_sinav_db
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100

# ===== CACHE =====
REDIS_URL=redis://:password@redis-host:6379/0
REDIS_PASSWORD=<STRONG_REDIS_PASSWORD>
VIDEO_CACHE_TTL=3600
VIDEO_CACHE_MAX_SIZE=1000
VIDEO_CACHE_MEMORY_LIMIT=100

# ===== YOUTUBE API =====
YOUTUBE_API_KEY=<YOUR_YOUTUBE_API_KEY>
YOUTUBE_QUOTA_LIMIT=10000
YOUTUBE_API_TIMEOUT=30
YOUTUBE_MAX_RESULTS_PER_REQUEST=50
YOUTUBE_CACHE_TTL=3600

# ===== MONITORING =====
SENTRY_DSN=<YOUR_SENTRY_DSN>
PROMETHEUS_GATEWAY_URL=http://prometheus:9090
VIDEO_API_METRICS_ENABLED=true
VIDEO_API_LATENCY_THRESHOLD_MS=3000
VIDEO_CACHE_HIT_RATE_THRESHOLD=0.80

# ===== CORS =====
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# ===== RATE LIMITING =====
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
```

### 3. Environment Variables Validation

Deploy öncesi environment variables'ı doğrulayın:

```bash
# Validation script çalıştır
python backend/scripts/validate_env.py --env production

# Beklenen çıktı:
# ✓ All required environment variables are set
# ✓ Database connection successful
# ✓ Redis connection successful
# ✓ YouTube API key valid
# ✓ All secrets are properly configured
```

---

## Docker Deployment

### 1. Docker Image Build

```bash
# Backend image build
cd backend
docker build -f Dockerfile.production -t turkiye-sinav-backend:latest .

# Image boyutunu kontrol et (< 500MB olmalı)
docker images turkiye-sinav-backend:latest

# Image'i test et
docker run --rm turkiye-sinav-backend:latest python -c "import main; print('OK')"
```

### 2. Docker Image Optimization

**Dockerfile.production** zaten optimize edilmiş durumda:
- ✅ Multi-stage build (builder + production)
- ✅ Minimal base image (python:3.11-slim-bullseye)
- ✅ Non-root user (kiro2)
- ✅ Health check included
- ✅ Turkish locale support
- ✅ Security hardening

**Image boyutu:** ~450MB (optimized)

### 3. Docker Compose Production Deployment

```bash
# Production compose file ile deploy
docker-compose -f docker-compose.production.yml up -d

# Servislerin durumunu kontrol et
docker-compose -f docker-compose.production.yml ps

# Logları izle
docker-compose -f docker-compose.production.yml logs -f backend1

# Health check
curl http://localhost/api/youtube/health
```

### 4. Docker Compose Servisler

Production deployment 3 backend replica içerir:
- **backend1, backend2, backend3**: Load balanced backend instances
- **nginx**: Reverse proxy & load balancer
- **postgres**: PostgreSQL database
- **redis**: Cache & session store
- **elasticsearch**: Search engine
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboard
- **celery-worker**: Background tasks
- **celery-beat**: Scheduled tasks

---

## Kubernetes Deployment

### 1. Namespace Oluşturma

```bash
# Namespace oluştur
kubectl create namespace turkiye-sinav-platform

# Namespace'i default olarak ayarla
kubectl config set-context --current --namespace=turkiye-sinav-platform
```

### 2. Secrets Oluşturma

```bash
# Database secret
kubectl create secret generic turkiye-sinav-secrets \
  --from-literal=database-url="postgresql+asyncpg://user:pass@postgres:5432/db" \
  --from-literal=secret-key="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  --from-literal=jwt-secret-key="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  --from-literal=openai-api-key="sk-..." \
  --from-literal=youtube-api-key="AIza..." \
  --namespace=turkiye-sinav-platform

# Redis password
kubectl create secret generic redis-secret \
  --from-literal=password="$(openssl rand -base64 32)" \
  --namespace=turkiye-sinav-platform

# Docker registry secret (GitHub Container Registry)
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<GITHUB_USERNAME> \
  --docker-password=<GITHUB_TOKEN> \
  --namespace=turkiye-sinav-platform
```

### 3. ConfigMap Oluşturma

```bash
# Application config
kubectl create configmap turkiye-sinav-config \
  --from-literal=REDIS_HOST=redis-service \
  --from-literal=REDIS_PORT=6379 \
  --from-literal=REDIS_DB=0 \
  --from-literal=ELASTICSEARCH_HOST=elasticsearch-service \
  --from-literal=ELASTICSEARCH_PORT=9200 \
  --from-literal=VIDEO_CACHE_TTL=3600 \
  --from-literal=VIDEO_CACHE_MAX_SIZE=1000 \
  --from-literal=LOG_LEVEL=INFO \
  --namespace=turkiye-sinav-platform
```

### 4. Persistent Volumes

```bash
# PVC'leri oluştur
kubectl apply -f k8s/pvc.yaml

# PVC durumunu kontrol et
kubectl get pvc -n turkiye-sinav-platform
```

### 5. StatefulSets (Database, Redis, Elasticsearch)

```bash
# StatefulSets deploy et
kubectl apply -f k8s/statefulset.yaml

# StatefulSet durumunu kontrol et
kubectl get statefulset -n turkiye-sinav-platform

# Pod'ların hazır olmasını bekle
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=database --timeout=300s
```

### 6. Application Deployment

```bash
# Deployment'ları uygula
kubectl apply -f k8s/deployment.yaml

# Deployment durumunu kontrol et
kubectl get deployments -n turkiye-sinav-platform

# Pod'ları listele
kubectl get pods -n turkiye-sinav-platform

# Deployment rollout durumunu izle
kubectl rollout status deployment/turkiye-sinav-app -n turkiye-sinav-platform
```

### 7. Services

```bash
# Service'leri oluştur
kubectl apply -f k8s/service.yaml

# Service'leri listele
kubectl get services -n turkiye-sinav-platform

# LoadBalancer external IP'yi al
kubectl get service turkiye-sinav-nginx-service -n turkiye-sinav-platform
```

### 8. Horizontal Pod Autoscaler (HPA)

```bash
# HPA'yı uygula
kubectl apply -f k8s/hpa.yaml

# HPA durumunu kontrol et
kubectl get hpa -n turkiye-sinav-platform

# HPA detaylarını görüntüle
kubectl describe hpa turkiye-sinav-app-hpa -n turkiye-sinav-platform
```

**HPA Konfigürasyonu:**
- Min replicas: 3
- Max replicas: 10
- Target CPU: 70%
- Target Memory: 80%

---

## Rolling Deployment Stratejisi

### 1. Rolling Update Konfigürasyonu

Kubernetes deployment'ımız zaten rolling update stratejisi kullanıyor:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Aynı anda 1 yeni pod ekle
    maxUnavailable: 0  # Hiçbir pod down olmasın (zero downtime)
```

### 2. Deployment Adımları

```bash
# 1. Yeni image'i build et ve push et
docker build -f backend/Dockerfile.production -t ghcr.io/org/turkiye-sinav-backend:v1.2.0 .
docker push ghcr.io/org/turkiye-sinav-backend:v1.2.0

# 2. Kubernetes deployment'ı güncelle
kubectl set image deployment/turkiye-sinav-app \
  app=ghcr.io/org/turkiye-sinav-backend:v1.2.0 \
  -n turkiye-sinav-platform

# 3. Rollout durumunu izle
kubectl rollout status deployment/turkiye-sinav-app -n turkiye-sinav-platform

# 4. Rollout history'yi görüntüle
kubectl rollout history deployment/turkiye-sinav-app -n turkiye-sinav-platform
```

### 3. Canary Deployment (Opsiyonel)

Canary deployment için Flagger veya Argo Rollouts kullanabilirsiniz:

```bash
# Flagger ile canary deployment
kubectl apply -f k8s/canary.yaml

# Canary durumunu izle
kubectl get canary -n turkiye-sinav-platform
```

### 4. Blue-Green Deployment (Opsiyonel)

```bash
# Green environment deploy et
kubectl apply -f k8s/deployment-green.yaml

# Traffic'i green'e yönlendir
kubectl patch service turkiye-sinav-app-service \
  -p '{"spec":{"selector":{"version":"green"}}}' \
  -n turkiye-sinav-platform
```

---

## Rollback Planı

### 1. Otomatik Rollback

Kubernetes otomatik olarak başarısız deployment'ları rollback eder:

```yaml
spec:
  progressDeadlineSeconds: 600  # 10 dakika içinde başarısız olursa rollback
  minReadySeconds: 30           # Pod'un 30 saniye hazır olması gerekir
```

### 2. Manuel Rollback

```bash
# Son deployment'a rollback
kubectl rollout undo deployment/turkiye-sinav-app -n turkiye-sinav-platform

# Belirli bir revision'a rollback
kubectl rollout undo deployment/turkiye-sinav-app --to-revision=2 -n turkiye-sinav-platform

# Rollback durumunu izle
kubectl rollout status deployment/turkiye-sinav-app -n turkiye-sinav-platform
```

### 3. Docker Compose Rollback

```bash
# Önceki image'e geri dön
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --force-recreate

# Veya belirli bir tag kullan
docker tag turkiye-sinav-backend:v1.1.0 turkiye-sinav-backend:latest
docker-compose -f docker-compose.production.yml up -d
```

### 4. Database Rollback

```bash
# Database migration rollback (Alembic)
docker exec -it turkiye_sinav_backend alembic downgrade -1

# Veya belirli bir revision'a
docker exec -it turkiye_sinav_backend alembic downgrade <revision_id>
```

### 5. Rollback Checklist

- [ ] Deployment başarısız oldu mu? (kubectl get pods)
- [ ] Health check'ler fail ediyor mu? (curl /health)
- [ ] Error rate arttı mı? (Grafana dashboard)
- [ ] Latency arttı mı? (Prometheus metrics)
- [ ] Database migration başarısız oldu mu?
- [ ] Cache invalidation gerekli mi?
- [ ] Rollback sonrası smoke test yap

---

## Production Monitoring

### 1. Health Check Endpoints

```bash
# Application health
curl https://api.yourdomain.com/health

# Beklenen response:
{
  "status": "healthy",
  "version": "1.2.0",
  "timestamp": "2025-11-03T10:30:00Z",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "youtube_api": "healthy"
  }
}

# Video API health
curl https://api.yourdomain.com/api/youtube/health

# Beklenen response:
{
  "status": "healthy",
  "components": {
    "youtube_api": {
      "status": "healthy",
      "quota_remaining": 8500,
      "response_time_ms": 120
    },
    "cache": {
      "status": "healthy",
      "hit_rate": 0.85,
      "size": 450
    },
    "database": {
      "status": "healthy",
      "connection_pool": {
        "active": 15,
        "idle": 35
      }
    }
  },
  "metrics": {
    "uptime_seconds": 86400,
    "total_requests": 125000,
    "error_rate": 0.002,
    "avg_response_time_ms": 450
  }
}
```

### 2. Prometheus Metrics

```bash
# Metrics endpoint
curl https://api.yourdomain.com/metrics

# Key metrics:
# - video_requests_total
# - video_response_time_seconds
# - video_cache_hit_rate
# - youtube_api_quota_remaining
# - video_errors_total
```

### 3. Grafana Dashboards

Grafana'ya erişim: https://grafana.yourdomain.com

**Dashboard'lar:**
1. **Video API Overview**
   - Request rate
   - Response time (P50, P95, P99)
   - Error rate
   - Cache hit rate

2. **System Health**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network traffic

3. **Database Performance**
   - Query latency
   - Connection pool
   - Slow queries

4. **Cache Performance**
   - Redis hit rate
   - Memory usage
   - Eviction rate

### 4. Alerting Rules

**Critical Alerts (PagerDuty):**
- Video API error rate > 5%
- Video API P95 latency > 5 seconds
- Cache hit rate < 70%
- YouTube API quota < 10%
- Database connection pool exhausted

**Warning Alerts (Slack):**
- Video API error rate > 2%
- Video API P95 latency > 3 seconds
- Cache hit rate < 80%
- YouTube API quota < 20%

### 5. Log Aggregation

```bash
# Kubernetes logs
kubectl logs -f deployment/turkiye-sinav-app -n turkiye-sinav-platform

# Structured logs (JSON format)
kubectl logs deployment/turkiye-sinav-app -n turkiye-sinav-platform | jq '.'

# Filter by request_id
kubectl logs deployment/turkiye-sinav-app -n turkiye-sinav-platform | jq 'select(.request_id=="abc123")'

# Filter by error
kubectl logs deployment/turkiye-sinav-app -n turkiye-sinav-platform | jq 'select(.level=="ERROR")'
```

### 6. Monitoring Checklist

**Daily:**
- [ ] Check Grafana dashboards
- [ ] Review error logs
- [ ] Check cache hit rate (target: >80%)
- [ ] Verify YouTube API quota usage

**Weekly:**
- [ ] Review performance trends
- [ ] Analyze slow queries
- [ ] Check disk space
- [ ] Review security logs

**Monthly:**
- [ ] Capacity planning review
- [ ] Cost optimization review
- [ ] Security audit
- [ ] Disaster recovery drill

---

## Troubleshooting

### 1. Video Yükleme Başarısız

**Semptomlar:**
- Frontend'de "Videoları yükleyemedik" hatası
- Timeout errors
- 500 Internal Server Error

**Diagnostic Steps:**

```bash
# 1. Health check
curl https://api.yourdomain.com/api/youtube/health

# 2. Backend logs
kubectl logs -f deployment/turkiye-sinav-app -n turkiye-sinav-platform | grep "video"

# 3. YouTube API quota
# Grafana'da youtube_api_quota_remaining metric'ini kontrol et

# 4. Cache durumu
redis-cli -h redis-service -a <password> INFO stats

# 5. Database connection
kubectl exec -it deployment/turkiye-sinav-app -n turkiye-sinav-platform -- \
  python -c "from database import engine; print(engine.pool.status())"
```

**Çözümler:**

1. **YouTube API Quota Bitti:**
   ```bash
   # Cache'i agresif kullan
   kubectl set env deployment/turkiye-sinav-app VIDEO_CACHE_TTL=7200
   ```

2. **Redis Bağlantı Sorunu:**
   ```bash
   # Redis'i restart et
   kubectl rollout restart statefulset/redis -n turkiye-sinav-platform
   ```

3. **Database Connection Pool Exhausted:**
   ```bash
   # Pool size'ı artır
   kubectl set env deployment/turkiye-sinav-app DB_POOL_SIZE=100
   ```

### 2. Yüksek Latency

**Semptomlar:**
- Video yükleme 5+ saniye sürüyor
- P95 latency > 3 saniye

**Diagnostic Steps:**

```bash
# 1. Response time metrics
curl https://api.yourdomain.com/metrics | grep video_response_time

# 2. Slow query logs
kubectl logs deployment/turkiye-sinav-app -n turkiye-sinav-platform | grep "slow_query"

# 3. Cache hit rate
curl https://api.yourdomain.com/api/youtube/health | jq '.components.cache.hit_rate'
```

**Çözümler:**

1. **Cache Hit Rate Düşük:**
   ```bash
   # Cache TTL'i artır
   kubectl set env deployment/turkiye-sinav-app VIDEO_CACHE_TTL=7200
   
   # Cache size'ı artır
   kubectl set env deployment/turkiye-sinav-app VIDEO_CACHE_MAX_SIZE=2000
   ```

2. **Database Slow Queries:**
   ```bash
   # Index'leri kontrol et
   kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
     psql -U postgres -d turkiye_sinav_db -c "SELECT * FROM pg_stat_user_indexes;"
   ```

3. **YouTube API Yavaş:**
   ```bash
   # Timeout'u artır
   kubectl set env deployment/turkiye-sinav-app YOUTUBE_API_TIMEOUT=45
   ```

### 3. Memory Leak

**Semptomlar:**
- Pod memory usage sürekli artıyor
- OOMKilled errors

**Diagnostic Steps:**

```bash
# 1. Memory usage
kubectl top pods -n turkiye-sinav-platform

# 2. Memory profiling
kubectl exec -it deployment/turkiye-sinav-app -n turkiye-sinav-platform -- \
  python -m memory_profiler main.py
```

**Çözümler:**

1. **Memory Limit Artır:**
   ```bash
   kubectl set resources deployment/turkiye-sinav-app \
     --limits=memory=4Gi \
     -n turkiye-sinav-platform
   ```

2. **Pod'u Restart Et:**
   ```bash
   kubectl rollout restart deployment/turkiye-sinav-app -n turkiye-sinav-platform
   ```

### 4. High Error Rate

**Semptomlar:**
- Error rate > 5%
- Sentry'de çok sayıda error

**Diagnostic Steps:**

```bash
# 1. Error logs
kubectl logs deployment/turkiye-sinav-app -n turkiye-sinav-platform | grep "ERROR"

# 2. Error metrics
curl https://api.yourdomain.com/metrics | grep video_errors_total

# 3. Sentry dashboard
# https://sentry.io/organizations/your-org/issues/
```

**Çözümler:**

1. **Circuit Breaker Açık:**
   ```bash
   # Circuit breaker'ı reset et
   redis-cli -h redis-service -a <password> DEL circuit_breaker:youtube_api
   ```

2. **Rate Limiting:**
   ```bash
   # Rate limit'i artır
   kubectl set env deployment/turkiye-sinav-app RATE_LIMIT_REQUESTS=2000
   ```

---

## Post-Deployment Verification

### 1. Smoke Tests

```bash
# Health check
curl https://api.yourdomain.com/health

# Video recommendations
curl -X POST https://api.yourdomain.com/api/youtube/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "goals": ["Matematik TYT"],
    "currentLevel": {"matematik": 50},
    "learningStyle": "visual"
  }'

# Cache test
curl https://api.yourdomain.com/api/youtube/health | jq '.components.cache'
```

### 2. Load Test

```bash
# Locust load test
cd backend/tests/load
locust -f locustfile.py --host=https://api.yourdomain.com --users=100 --spawn-rate=10
```

### 3. Monitoring Verification

- [ ] Grafana dashboards görünüyor mu?
- [ ] Prometheus metrics toplanıyor mu?
- [ ] Alerting rules aktif mi?
- [ ] Sentry errors raporlanıyor mu?

---

## Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] Secrets created
- [ ] Database migrations ready
- [ ] Docker images built and tested
- [ ] Backup taken
- [ ] Rollback plan documented
- [ ] Team notified

### Deployment
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Deploy to production
- [ ] Monitor rollout progress
- [ ] Verify health checks
- [ ] Run smoke tests on production

### Post-Deployment
- [ ] Verify all services healthy
- [ ] Check metrics and logs
- [ ] Run load tests
- [ ] Monitor for 1 hour
- [ ] Update documentation
- [ ] Notify team of completion

---

## Support & Escalation

**On-Call Engineer:** +90 XXX XXX XX XX
**Slack Channel:** #turkiye-sinav-production
**PagerDuty:** https://turkiye-sinav.pagerduty.com
**Runbook:** https://wiki.company.com/turkiye-sinav/runbook

---

**Son Güncelleme:** 3 Kasım 2025
**Versiyon:** 1.0.0
**Hazırlayan:** DevOps Team
