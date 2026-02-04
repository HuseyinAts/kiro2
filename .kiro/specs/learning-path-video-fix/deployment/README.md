# Video API Production Deployment

## Overview

Bu dizin, Learning Path Video Yükleme Sistemi'nin production ortamına deployment için gerekli tüm konfigürasyon dosyalarını ve scriptleri içerir.

**Requirements:** 4.9 (Health Check Probes), 4.13 (Resource Limits)

## Dizin Yapısı

```
deployment/
├── README.md                           # Bu dosya
├── DEPLOYMENT_GUIDE.md                 # Detaylı deployment rehberi
├── .env.video-api.production           # Production environment variables
├── Dockerfile.video-api                # Optimized production Docker image
├── k8s/
│   └── video-api-deployment.yaml       # Kubernetes manifests
├── scripts/
│   ├── deploy.sh                       # Automated deployment script
│   └── test-docker-image.sh            # Docker image testing script
└── .github/
    └── workflows/
        └── deploy-production.yml       # CI/CD pipeline
```

## Quick Start

### 1. Environment Variables

Production secrets'ları hazırlayın:

```bash
# .env.video-api.production dosyasını kopyalayın
cp .env.video-api.production .env.production

# Secrets'ları doldurun
nano .env.production
```

Gerekli secrets:
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT signing key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_PASSWORD` - Redis password
- `YOUTUBE_API_KEY` - YouTube Data API key
- `SENTRY_DSN` - Sentry error tracking DSN

### 2. Docker Image Build

```bash
# Build image
docker build \
  -f Dockerfile.video-api \
  -t ghcr.io/turkiye-sinav/video-api:latest \
  .

# Test image
./scripts/test-docker-image.sh

# Push to registry
docker push ghcr.io/turkiye-sinav/video-api:latest
```

### 3. Deploy to Kubernetes

```bash
# Automated deployment
./scripts/deploy.sh deploy

# Manual deployment
kubectl apply -f k8s/video-api-deployment.yaml
kubectl rollout status deployment/video-api -n video-api
```

## Features

### Docker Image

✅ **Multi-stage build** - Optimized image size  
✅ **Non-root user** - Security best practice  
✅ **Health checks** - Liveness, readiness, startup probes  
✅ **Turkish locale** - tr_TR.UTF-8 support  
✅ **Timezone** - Europe/Istanbul  
✅ **Graceful shutdown** - Proper signal handling with tini  
✅ **Compiled Python** - Faster startup time  

### Kubernetes Deployment

✅ **Rolling updates** - Zero-downtime deployment  
✅ **Health probes** - Automatic pod restart on failure  
✅ **Resource limits** - CPU and memory constraints  
✅ **Auto-scaling** - HPA based on CPU/memory  
✅ **Pod disruption budget** - Minimum availability guarantee  
✅ **Network policies** - Secure pod communication  
✅ **Init containers** - Startup health check  
✅ **Affinity rules** - Pod distribution across nodes  

### Monitoring

✅ **Prometheus metrics** - Request rate, latency, errors  
✅ **Structured logging** - JSON format logs  
✅ **Health endpoints** - /api/youtube/health  
✅ **Grafana dashboards** - Visual monitoring  
✅ **Alerting** - Slack/email notifications  

## Configuration

### Resource Limits (Req 4.13)

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

**Tuning:**
- Requests: Minimum guaranteed resources
- Limits: Maximum allowed resources
- Monitor actual usage and adjust accordingly

### Health Checks (Req 4.9)

**Liveness Probe:**
- Checks if container should be restarted
- Endpoint: `/api/youtube/health`
- Initial delay: 60s
- Period: 30s
- Timeout: 10s
- Failure threshold: 3

**Readiness Probe:**
- Checks if container can receive traffic
- Endpoint: `/api/youtube/health`
- Initial delay: 30s
- Period: 10s
- Timeout: 5s
- Failure threshold: 3

**Startup Probe:**
- Gives container time to start
- Endpoint: `/api/youtube/health`
- Initial delay: 10s
- Period: 5s
- Failure threshold: 12 (60s total)

### Auto-scaling

```yaml
minReplicas: 3
maxReplicas: 10
targetCPUUtilization: 70%
targetMemoryUtilization: 80%
```

## Deployment Strategies

### Rolling Update (Default)

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # 1 extra pod during update
    maxUnavailable: 0  # Zero downtime
```

**Process:**
1. New pod created (maxSurge: 1)
2. Init container runs startup health check
3. Startup probe waits for container to be ready
4. Readiness probe confirms pod can receive traffic
5. Old pod terminated
6. Repeat for all pods

### Blue-Green Deployment

```bash
# Deploy new version (green)
kubectl apply -f k8s/video-api-deployment-green.yaml

# Test green deployment
kubectl port-forward -n video-api service/video-api-service-green 8000:8000

# Switch traffic to green
kubectl patch service video-api-service -n video-api \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Remove blue deployment
kubectl delete deployment video-api-blue -n video-api
```

### Canary Deployment

```bash
# Deploy canary (10% traffic)
kubectl apply -f k8s/video-api-deployment-canary.yaml

# Monitor metrics
# If successful, gradually increase traffic
# If issues, rollback canary

# Full rollout
kubectl apply -f k8s/video-api-deployment.yaml
```

## Monitoring & Alerting

### Metrics

Key metrics collected:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `cache_hit_rate` - Cache hit percentage
- `youtube_api_quota_used` - YouTube API quota usage
- `video_discovery_duration_seconds` - Video discovery time

### Dashboards

Grafana dashboards available:
- Video API Overview
- Request Performance
- Cache Performance
- Error Tracking
- Resource Usage

### Alerts

Configured alerts:
- High error rate (>5%)
- Slow response time (P95 >3s)
- Low cache hit rate (<80%)
- High YouTube API quota usage (>80%)
- Pod restart frequency
- Resource exhaustion

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl get pods -n video-api
kubectl describe pod <pod-name> -n video-api

# Check logs
kubectl logs <pod-name> -n video-api
kubectl logs <pod-name> -n video-api -c startup-check

# Check events
kubectl get events -n video-api --sort-by='.lastTimestamp'
```

### Health Check Failing

```bash
# Test health endpoint
kubectl exec -it <pod-name> -n video-api -- \
  curl http://localhost:8000/api/youtube/health

# Check dependencies
kubectl exec -it <pod-name> -n video-api -- \
  python -c "from services.health_check_service import HealthCheckService; \
             import asyncio; \
             asyncio.run(HealthCheckService().check_all())"
```

### High Memory Usage

```bash
# Check memory usage
kubectl top pods -n video-api

# Check cache size
kubectl exec -it <pod-name> -n video-api -- \
  python -c "from core.multi_layer_cache import get_cache_stats; \
             print(get_cache_stats())"

# Restart pod
kubectl delete pod <pod-name> -n video-api
```

### Slow Response Time

```bash
# Check metrics
kubectl port-forward -n video-api service/video-api-service 9090:9090
curl http://localhost:9090/metrics | grep http_request_duration

# Check database pool
kubectl exec -it <pod-name> -n video-api -- \
  python -c "from database import get_pool_stats; print(get_pool_stats())"

# Check YouTube API quota
kubectl logs <pod-name> -n video-api | grep "quota"
```

## Rollback

### Quick Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/video-api -n video-api

# Check rollback status
kubectl rollout status deployment/video-api -n video-api
```

### Rollback to Specific Version

```bash
# View rollout history
kubectl rollout history deployment/video-api -n video-api

# Rollback to specific revision
kubectl rollout undo deployment/video-api -n video-api --to-revision=2
```

## Security

### Best Practices

✅ Non-root user in container  
✅ Read-only root filesystem (where possible)  
✅ Secrets stored in external secret management  
✅ Network policies configured  
✅ RBAC roles configured  
✅ Image vulnerability scanning  
✅ TLS/SSL for external communication  
✅ API rate limiting  
✅ CORS properly configured  

### Secret Management

**Recommended:** Use external secret management

- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Google Secret Manager

**Example with AWS Secrets Manager:**

```bash
# Install External Secrets Operator
helm install external-secrets external-secrets/external-secrets

# Configure SecretStore
kubectl apply -f k8s/secret-store.yaml

# Create ExternalSecret
kubectl apply -f k8s/external-secret.yaml
```

## CI/CD

### GitHub Actions

Automated deployment pipeline:

1. **Build & Test**
   - Lint code
   - Run unit tests
   - Run integration tests
   - Build Docker image
   - Test Docker image
   - Scan for vulnerabilities

2. **Deploy**
   - Push image to registry
   - Update Kubernetes deployment
   - Wait for rollout
   - Verify deployment
   - Run smoke tests

3. **Notify**
   - Slack notification
   - Sentry release
   - Update status

### Manual Deployment

```bash
# Build and push
docker build -t ghcr.io/turkiye-sinav/video-api:v1.0.0 .
docker push ghcr.io/turkiye-sinav/video-api:v1.0.0

# Deploy
kubectl set image deployment/video-api \
  video-api=ghcr.io/turkiye-sinav/video-api:v1.0.0 \
  -n video-api

# Monitor
kubectl rollout status deployment/video-api -n video-api
```

## Performance Tuning

### Database Connection Pool

```python
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100
DATABASE_POOL_PRE_PING=true
DATABASE_POOL_RECYCLE=3600
```

### Redis Cache

```python
REDIS_MAX_CONNECTIONS=50
VIDEO_CACHE_TTL=3600
MEMORY_CACHE_SIZE=100
CACHE_WARMING_ENABLED=true
```

### Uvicorn Workers

```bash
--workers 4
--worker-class uvicorn.workers.UvicornWorker
--loop uvloop
```

## Compliance

### Turkish Education System

✅ MEB curriculum taxonomy  
✅ Turkish language support (tr_TR.UTF-8)  
✅ Trusted Turkish education channels  
✅ KVKK compliance  
✅ Turkish timezone (Europe/Istanbul)  

## Support

### Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Detailed deployment instructions
- [API Documentation](../../design.md) - API design and architecture
- [Requirements](../../requirements.md) - System requirements

### Monitoring

- Grafana: http://grafana.yourdomain.com
- Prometheus: http://prometheus.yourdomain.com
- Sentry: https://sentry.io/your-project

### Contact

- DevOps Team: devops@yourdomain.com
- On-call: +90 XXX XXX XX XX
- Slack: #video-api-alerts

## License

Copyright © 2025 Teknofest Eğitim Eylemci
