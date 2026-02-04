# Video API Production Deployment Guide

## Overview

Bu doküman, Learning Path Video Yükleme Sistemi'nin production ortamına deployment sürecini detaylı olarak açıklar.

**Requirements:** 4.9, 4.13

## Deployment Stratejisi

### Rolling Deployment

Zero-downtime deployment için rolling update stratejisi kullanılır:

- **maxSurge: 1** - Güncelleme sırasında 1 ekstra pod oluşturulabilir
- **maxUnavailable: 0** - Hiçbir zaman tüm podlar down olmaz
- **Health Check** - Yeni pod hazır olmadan eski pod terminate edilmez

### Deployment Akışı

```
1. Yeni image build edilir ve registry'e push edilir
2. Kubernetes yeni pod oluşturur (maxSurge: 1)
3. Init container startup health check yapar
4. Startup probe başarılı olana kadar bekler
5. Readiness probe başarılı olunca traffic alır
6. Eski pod terminate edilir
7. Süreç tüm podlar için tekrarlanır
```

## Prerequisites

### 1. Environment Variables

Production secrets'ları hazırlayın:

```bash
# Secret generation
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Required secrets:
- SECRET_KEY
- JWT_SECRET_KEY
- DATABASE_URL
- REDIS_PASSWORD
- YOUTUBE_API_KEY
- SENTRY_DSN
```

### 2. Docker Registry Access

GitHub Container Registry için authentication:

```bash
# GitHub Personal Access Token oluşturun (read:packages permission)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### 3. Kubernetes Cluster

Cluster requirements:
- Kubernetes 1.24+
- Metrics Server (HPA için)
- Ingress Controller (nginx)
- Persistent Volume provisioner
- Secret management (AWS Secrets Manager, HashiCorp Vault, etc.)

## Deployment Steps

### Step 1: Build Docker Image

```bash
# Navigate to project root
cd /path/to/project

# Build image
docker build \
  -f .kiro/specs/learning-path-video-fix/deployment/Dockerfile.video-api \
  -t ghcr.io/turkiye-sinav/video-api:latest \
  -t ghcr.io/turkiye-sinav/video-api:v1.0.0 \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --build-arg VERSION=1.0.0 \
  .

# Test image locally
docker run --rm \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./test.db \
  -e REDIS_URL=redis://localhost:6379/0 \
  -e YOUTUBE_API_KEY=test_key \
  ghcr.io/turkiye-sinav/video-api:latest

# Push to registry
docker push ghcr.io/turkiye-sinav/video-api:latest
docker push ghcr.io/turkiye-sinav/video-api:v1.0.0
```

### Step 2: Configure Secrets

**Option A: Kubernetes Secrets (Basic)**

```bash
# Create namespace
kubectl create namespace video-api

# Create secrets
kubectl create secret generic video-api-secrets \
  --namespace=video-api \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=JWT_SECRET_KEY='your-jwt-secret' \
  --from-literal=DATABASE_URL='postgresql+asyncpg://user:pass@host:5432/db' \
  --from-literal=REDIS_URL='redis://redis-service:6379/0' \
  --from-literal=REDIS_PASSWORD='your-redis-password' \
  --from-literal=YOUTUBE_API_KEY='your-youtube-api-key' \
  --from-literal=SENTRY_DSN='your-sentry-dsn'

# Create image pull secret
kubectl create secret docker-registry ghcr-secret \
  --namespace=video-api \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN
```

**Option B: External Secret Management (Recommended)**

AWS Secrets Manager örneği:

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace

# Create SecretStore
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: video-api
spec:
  provider:
    aws:
      service: SecretsManager
      region: eu-central-1
      auth:
        jwt:
          serviceAccountRef:
            name: video-api-sa
EOF

# Create ExternalSecret
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: video-api-secrets
  namespace: video-api
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: video-api-secrets
    creationPolicy: Owner
  data:
  - secretKey: SECRET_KEY
    remoteRef:
      key: video-api/secret-key
  - secretKey: JWT_SECRET_KEY
    remoteRef:
      key: video-api/jwt-secret-key
  - secretKey: DATABASE_URL
    remoteRef:
      key: video-api/database-url
  - secretKey: YOUTUBE_API_KEY
    remoteRef:
      key: video-api/youtube-api-key
EOF
```

### Step 3: Deploy to Kubernetes

```bash
# Apply deployment manifests
kubectl apply -f .kiro/specs/learning-path-video-fix/deployment/k8s/video-api-deployment.yaml

# Verify deployment
kubectl get deployments -n video-api
kubectl get pods -n video-api
kubectl get services -n video-api
kubectl get hpa -n video-api

# Check pod logs
kubectl logs -f deployment/video-api -n video-api

# Check startup health check
kubectl logs -f deployment/video-api -n video-api -c startup-check
```

### Step 4: Verify Deployment

```bash
# Port forward to test locally
kubectl port-forward -n video-api service/video-api-service 8000:8000

# Test health endpoint
curl http://localhost:8000/api/youtube/health

# Test video recommendations
curl -X POST http://localhost:8000/api/youtube/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "goals": ["Matematik TYT konularını öğrenmek"],
    "currentLevel": {"matematik": 50},
    "learningStyle": "visual",
    "preferences": {"language": "tr"}
  }'

# Check metrics
curl http://localhost:8000/metrics
```

### Step 5: Configure Ingress

```bash
# Create Ingress resource
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: video-api-ingress
  namespace: video-api
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "10"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: video-api-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /api/youtube
        pathType: Prefix
        backend:
          service:
            name: video-api-service
            port:
              number: 8000
EOF
```

## Monitoring Setup

### Prometheus Metrics

```bash
# Create ServiceMonitor for Prometheus Operator
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: video-api-metrics
  namespace: video-api
  labels:
    app.kubernetes.io/name: video-api
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: video-api
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF
```

### Grafana Dashboard

Import dashboard from `monitoring/grafana/dashboards/video-api-dashboard.json`

Key metrics:
- Request rate (requests/second)
- Response time (P50, P95, P99)
- Error rate (%)
- Cache hit rate (%)
- YouTube API quota usage
- Pod CPU/Memory usage

### Alerting Rules

```yaml
# Prometheus AlertManager rules
groups:
- name: video-api
  interval: 30s
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} (threshold: 5%)"
  
  - alert: SlowResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 3
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Slow response time detected"
      description: "P95 response time is {{ $value }}s (threshold: 3s)"
  
  - alert: LowCacheHitRate
    expr: cache_hit_rate < 0.8
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Low cache hit rate"
      description: "Cache hit rate is {{ $value }} (threshold: 80%)"
```

## Rollback Procedure

### Quick Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/video-api -n video-api

# Rollback to specific revision
kubectl rollout history deployment/video-api -n video-api
kubectl rollout undo deployment/video-api -n video-api --to-revision=2

# Check rollback status
kubectl rollout status deployment/video-api -n video-api
```

### Manual Rollback

```bash
# Update image to previous version
kubectl set image deployment/video-api \
  video-api=ghcr.io/turkiye-sinav/video-api:v0.9.0 \
  -n video-api

# Or edit deployment directly
kubectl edit deployment/video-api -n video-api
```

## Scaling

### Manual Scaling

```bash
# Scale up
kubectl scale deployment/video-api --replicas=5 -n video-api

# Scale down
kubectl scale deployment/video-api --replicas=2 -n video-api
```

### Auto-scaling (HPA)

HPA otomatik olarak CPU ve memory kullanımına göre scale eder:

```bash
# Check HPA status
kubectl get hpa -n video-api
kubectl describe hpa video-api-hpa -n video-api

# Update HPA thresholds
kubectl edit hpa video-api-hpa -n video-api
```

## Resource Limits

### Current Limits (Req 4.13)

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Tuning Guidelines

**CPU:**
- Requests: Minimum CPU needed for normal operation
- Limits: Maximum CPU during peak load
- Recommendation: Monitor actual usage and adjust

**Memory:**
- Requests: Minimum memory for application + cache
- Limits: Maximum memory including cache warming
- Recommendation: Set limits 2x requests for cache flexibility

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
# Check health endpoint directly
kubectl exec -it <pod-name> -n video-api -- curl http://localhost:8000/api/youtube/health

# Check dependencies
kubectl exec -it <pod-name> -n video-api -- curl http://postgres-service:5432
kubectl exec -it <pod-name> -n video-api -- redis-cli -h redis-service ping
```

### High Memory Usage

```bash
# Check memory usage
kubectl top pods -n video-api

# Check cache size
kubectl exec -it <pod-name> -n video-api -- \
  python -c "from core.multi_layer_cache import get_cache_stats; print(get_cache_stats())"

# Restart pod to clear cache
kubectl delete pod <pod-name> -n video-api
```

### Slow Response Time

```bash
# Check metrics
kubectl port-forward -n video-api service/video-api-service 9090:9090
curl http://localhost:9090/metrics | grep http_request_duration

# Check database connections
kubectl exec -it <pod-name> -n video-api -- \
  python -c "from database import get_pool_stats; print(get_pool_stats())"

# Check YouTube API quota
kubectl logs <pod-name> -n video-api | grep "quota"
```

## Maintenance

### Database Migrations

```bash
# Run migrations
kubectl exec -it deployment/video-api -n video-api -- \
  alembic upgrade head

# Rollback migration
kubectl exec -it deployment/video-api -n video-api -- \
  alembic downgrade -1
```

### Cache Warming

```bash
# Warm cache manually
kubectl exec -it deployment/video-api -n video-api -- \
  python -c "from services.video_recommendation_service import warm_cache; warm_cache()"
```

### Log Rotation

Logs are stored in emptyDir volumes and automatically cleaned on pod restart.

For persistent logs, configure log aggregation (ELK, Loki, etc.)

## Security Checklist

- [ ] Secrets stored in external secret management
- [ ] Image pull secrets configured
- [ ] Non-root user in container
- [ ] Read-only root filesystem (where possible)
- [ ] Network policies configured
- [ ] RBAC roles configured
- [ ] Pod security policies/standards applied
- [ ] TLS/SSL certificates configured
- [ ] API rate limiting enabled
- [ ] CORS properly configured

## Performance Checklist

- [ ] Resource requests/limits configured
- [ ] HPA configured and tested
- [ ] Cache warming enabled
- [ ] Database connection pooling optimized
- [ ] Health checks tuned
- [ ] Metrics collection enabled
- [ ] Logging optimized (not too verbose)
- [ ] Pod anti-affinity configured

## Compliance Checklist

- [ ] Turkish locale configured
- [ ] Timezone set to Europe/Istanbul
- [ ] MEB curriculum taxonomy loaded
- [ ] Trusted Turkish channels configured
- [ ] KVKK compliance verified
- [ ] Data retention policies configured

## Support

For issues or questions:
- Check logs: `kubectl logs -f deployment/video-api -n video-api`
- Check metrics: Grafana dashboard
- Check alerts: AlertManager
- Contact: DevOps team

## References

- Kubernetes Documentation: https://kubernetes.io/docs/
- Prometheus Operator: https://prometheus-operator.dev/
- External Secrets: https://external-secrets.io/
- NGINX Ingress: https://kubernetes.github.io/ingress-nginx/
