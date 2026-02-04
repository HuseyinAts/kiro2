# Production Deployment - Quick Reference
## Video Recommendation System

Bu doküman, production deployment için hızlı referans komutlarını içerir.

## 🚀 Quick Deploy

### Docker Compose (5 dakika)

```bash
# 1. Environment setup
cp .env.example .env.production
# Edit .env.production

# 2. Deploy
docker-compose -f docker-compose.production.yml up -d

# 3. Verify
curl http://localhost/health
```

### Kubernetes (10 dakika)

```bash
# 1. Create namespace
kubectl create namespace turkiye-sinav-platform

# 2. Create secrets
kubectl create secret generic turkiye-sinav-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=secret-key="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  --from-literal=youtube-api-key="AIza..." \
  -n turkiye-sinav-platform

# 3. Deploy
kubectl apply -f k8s/statefulset.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 4. Verify
kubectl get pods -n turkiye-sinav-platform
curl https://api.yourdomain.com/health
```

---

## 🔄 Rollback (2 dakika)

### Kubernetes

```bash
# Quick rollback
kubectl rollout undo deployment/turkiye-sinav-app -n turkiye-sinav-platform

# Verify
kubectl rollout status deployment/turkiye-sinav-app -n turkiye-sinav-platform
curl https://api.yourdomain.com/health
```

### Docker Compose

```bash
# Rollback
docker-compose -f docker-compose.production.yml down
docker tag turkiye-sinav-backend:v1.1.0 turkiye-sinav-backend:latest
docker-compose -f docker-compose.production.yml up -d

# Verify
curl http://localhost/health
```

---

## 📊 Health Check

```bash
# Application health
curl https://api.yourdomain.com/health

# Video API health
curl https://api.yourdomain.com/api/youtube/health | jq '.'

# Expected output:
{
  "status": "healthy",
  "components": {
    "youtube_api": {"status": "healthy", "quota_remaining": 8500},
    "cache": {"status": "healthy", "hit_rate": 0.85},
    "database": {"status": "healthy"}
  }
}
```

---

## 🔍 Monitoring

### Quick Metrics

```bash
# Error rate (should be < 2%)
curl https://api.yourdomain.com/metrics | grep video_errors_total

# Cache hit rate (should be > 80%)
curl https://api.yourdomain.com/api/youtube/health | jq '.components.cache.hit_rate'

# YouTube API quota (should be > 20%)
curl https://api.yourdomain.com/api/youtube/health | jq '.components.youtube_api.quota_remaining'
```

### Dashboards

- **Grafana:** https://grafana.yourdomain.com
- **Prometheus:** https://prometheus.yourdomain.com
- **Sentry:** https://sentry.io/organizations/your-org

---

## 🐛 Troubleshooting

### Video Yükleme Başarısız

```bash
# 1. Check logs
kubectl logs -f deployment/turkiye-sinav-app -n turkiye-sinav-platform | grep "video"

# 2. Check YouTube API quota
curl https://api.yourdomain.com/api/youtube/health | jq '.components.youtube_api.quota_remaining'

# 3. Check cache
redis-cli -h redis-service INFO stats

# 4. Restart if needed
kubectl rollout restart deployment/turkiye-sinav-app -n turkiye-sinav-platform
```

### High Latency

```bash
# 1. Check response time
curl https://api.yourdomain.com/metrics | grep video_response_time

# 2. Check cache hit rate
curl https://api.yourdomain.com/api/youtube/health | jq '.components.cache.hit_rate'

# 3. Increase cache TTL
kubectl set env deployment/turkiye-sinav-app VIDEO_CACHE_TTL=7200 -n turkiye-sinav-platform
```

### High Error Rate

```bash
# 1. Check error logs
kubectl logs deployment/turkiye-sinav-app -n turkiye-sinav-platform | grep "ERROR"

# 2. Check Sentry
# Visit: https://sentry.io/organizations/your-org/issues/

# 3. Rollback if critical
kubectl rollout undo deployment/turkiye-sinav-app -n turkiye-sinav-platform
```

---

## 📞 Emergency Contacts

**On-Call Engineer:** +90 XXX XXX XX XX
**Slack:** #turkiye-sinav-production
**PagerDuty:** https://turkiye-sinav.pagerduty.com

---

## 📚 Full Documentation

- **Deployment Guide:** `backend/docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Rollback Plan:** `backend/docs/ROLLBACK_PLAN.md`
- **Monitoring Checklist:** `backend/docs/PRODUCTION_MONITORING_CHECKLIST.md`
- **Docker Optimization:** `backend/docs/DOCKER_OPTIMIZATION_GUIDE.md`

---

**Son Güncelleme:** 3 Kasım 2025
