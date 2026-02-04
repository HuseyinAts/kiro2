# Production Deployment Guide - Learning Path Video Fix

## Overview

Bu doküman, Learning Path Video Fix özelliğinin production ortamına deployment sürecini detaylı olarak açıklar.

## Deployment Stratejisi

### Rolling Deployment

- **Zero-downtime deployment:** Kullanıcılar kesintisiz hizmet alır
- **Gradual rollout:** Yeni versiyon aşamalı olarak devreye alınır
- **Automatic rollback:** Sorun tespit edilirse otomatik geri alma
- **Health checks:** Her adımda sağlık kontrolü yapılır

### Deployment Flow

```
1. Pre-deployment checks
   ├── kubectl availability
   ├── Namespace verification
   └── Docker image verification

2. Backup current deployment
   └── Save to ./backups/

3. Update deployment
   └── Set new image tag

4. Monitor rollout
   ├── Wait for pods to be ready
   └── Timeout: 5 minutes

5. Health checks
   ├── Pod readiness
   ├── Health endpoint
   └── Component health

6. Smoke tests
   ├── API connectivity
   ├── Recommendations endpoint
   ├── Response time
   └── Error handling

7. Post-deployment verification
   ├── Metrics monitoring
   ├── Log analysis
   └── Performance tracking

8. Success / Rollback
```

## Prerequisites

### Required Tools

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install jq (JSON processor)
sudo apt-get install jq

# Install bc (calculator)
sudo apt-get install bc
```

### Access Requirements

- Kubernetes cluster access (production namespace)
- Docker registry access
- Grafana dashboard access
- Prometheus access
- Appropriate RBAC permissions

### Environment Variables

```bash
# Required
export NAMESPACE=production
export API_BASE_URL=https://api.example.com
export GRAFANA_URL=https://grafana.example.com
export PROMETHEUS_URL=https://prometheus.example.com

# Optional
export ROLLBACK_ENABLED=true
export VERIFICATION_DURATION=300
```

## Deployment Process

### Step 1: Pre-Deployment Checklist

```bash
# 1. Verify all tests pass
cd backend
pytest tests/ -v --cov

# 2. Build Docker image
docker build -t video-api:v1.2.0 .

# 3. Tag image
docker tag video-api:v1.2.0 registry.example.com/video-api:v1.2.0

# 4. Push to registry
docker push registry.example.com/video-api:v1.2.0

# 5. Verify image in registry
docker pull registry.example.com/video-api:v1.2.0

# 6. Review deployment plan
cat deployment/production_deploy.sh

# 7. Notify team
# Send notification to #deployments Slack channel
```

### Step 2: Execute Deployment

```bash
# Make scripts executable
chmod +x deployment/*.sh

# Run deployment script
./deployment/production_deploy.sh v1.2.0

# Monitor deployment
watch kubectl get pods -n production -l app=video-api
```

### Step 3: Monitor Deployment

```bash
# Watch rollout status
kubectl rollout status deployment/video-api -n production

# Check pod logs
kubectl logs -f deployment/video-api -n production

# Check events
kubectl get events -n production --sort-by='.lastTimestamp'
```

### Step 4: Run Post-Deployment Verification

```bash
# Run comprehensive verification
./deployment/post_deployment_verification.sh

# Expected output:
# ✓ All checks passed
# ✓ System is healthy
# ✓ Performance within SLO
```

### Step 5: Monitor for 24 Hours

```bash
# Access Grafana dashboard
kubectl port-forward -n monitoring svc/grafana 3000:3000
# Open: http://localhost:3000/d/video-api-dashboard

# Check Prometheus alerts
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Open: http://localhost:9090/alerts

# Monitor logs
kubectl logs -f deployment/video-api -n production | grep ERROR
```

## Rollback Procedures

### Automatic Rollback

Deployment script otomatik olarak rollback yapar eğer:
- Health check başarısız olursa (5 deneme sonrası)
- Smoke tests başarısız olursa
- Rollout timeout olursa (5 dakika)

### Manual Rollback

```bash
# 1. Önceki versiyona geri dön
kubectl rollout undo deployment/video-api -n production

# 2. Rollback durumunu izle
kubectl rollout status deployment/video-api -n production

# 3. Pods'ların sağlıklı olduğunu doğrula
kubectl get pods -n production -l app=video-api

# 4. Health check yap
curl https://api.example.com/api/youtube/health

# 5. Smoke tests çalıştır
./deployment/smoke_tests.sh
```

### Rollback to Specific Revision

```bash
# Revision history'yi listele
kubectl rollout history deployment/video-api -n production

# Belirli bir revision'a geri dön
kubectl rollout undo deployment/video-api -n production --to-revision=3
```

Detaylı rollback prosedürleri için: [rollback_plan.md](./rollback_plan.md)

## Monitoring & Alerting

### Grafana Dashboard

**URL:** http://grafana.example.com/d/video-api-dashboard

**Panels:**
- Request Rate (by status, cache hit)
- Response Time (P50, P95, P99)
- Error Rate
- Cache Hit Rate
- YouTube API Quota
- System Health Status
- Active Pods
- Request Success Rate
- Top Error Types
- Request Volume by Subject

### Prometheus Alerts

**Critical Alerts:**
- `CriticalErrorRate`: Error rate > 10%
- `VerySlowResponseTime`: P95 > 5s
- `ServiceDown`: Service not responding
- `YouTubeQuotaCritical`: Quota < 500

**Warning Alerts:**
- `HighErrorRate`: Error rate > 5%
- `SlowResponseTime`: P95 > 3s
- `LowCacheHitRate`: Cache hit rate < 60%
- `YouTubeQuotaLow`: Quota < 2000

**SLO Alerts:**
- `SLOAvailabilityBreach`: Availability < 99.9%
- `SLOResponseTimeBreach`: P95 > 3s
- `SLOCacheHitRateBreach`: Cache hit rate < 80%

### Alert Configuration

```bash
# Apply Prometheus alert rules
kubectl apply -f deployment/monitoring/prometheus_alerts.yml

# Verify alerts are loaded
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Open: http://localhost:9090/alerts
```

### Grafana Dashboard Setup

```bash
# Import dashboard
curl -X POST http://grafana.example.com/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @deployment/monitoring/grafana_dashboard.json
```

## Smoke Tests

### Running Smoke Tests

```bash
# Set API base URL
export API_BASE_URL=https://api.example.com

# Run smoke tests
./deployment/smoke_tests.sh

# Expected output:
# ✓ API reachable
# ✓ Health endpoint responds
# ✓ Recommendations endpoint responds
# ✓ Response time < 5s
# ✓ Error handling works
# ✓ CORS headers present
```

### Smoke Test Coverage

1. **API Connectivity:** Verifies API is reachable
2. **Health Check:** Verifies health endpoint and status
3. **Video Recommendations:** Tests main functionality
4. **Response Time:** Ensures performance is acceptable
5. **Error Handling:** Validates error responses
6. **CORS Headers:** Checks cross-origin support
7. **Rate Limiting:** Verifies rate limiting is active

## Post-Deployment Verification

### Verification Checklist

- [ ] All pods are running and ready
- [ ] No pod restarts in last 5 minutes
- [ ] Health endpoint returns "healthy"
- [ ] All components (Database, Redis, YouTube API) are healthy
- [ ] Smoke tests pass
- [ ] Response time < 3s (P95)
- [ ] Error rate < 1%
- [ ] Cache hit rate > 80%
- [ ] No critical errors in logs
- [ ] Grafana dashboard shows normal metrics
- [ ] No Prometheus alerts firing

### Verification Script

```bash
# Run comprehensive verification
./deployment/post_deployment_verification.sh

# This will:
# 1. Check Kubernetes resources
# 2. Verify health checks
# 3. Run functional tests
# 4. Monitor metrics for 5 minutes
# 5. Analyze logs
# 6. Generate summary report
```

## Troubleshooting

### Common Issues

#### Issue 1: Pods Not Starting

**Symptoms:**
- Pods in `CrashLoopBackOff` or `ImagePullBackOff`
- Deployment not progressing

**Solutions:**
```bash
# Check pod status
kubectl describe pods -n production -l app=video-api

# Check logs
kubectl logs -n production deployment/video-api --tail=100

# Common fixes:
# - Verify image exists in registry
# - Check resource limits
# - Verify environment variables
# - Check secrets and configmaps
```

#### Issue 2: High Error Rate

**Symptoms:**
- Prometheus alert: `HighErrorRate`
- Users reporting errors

**Solutions:**
```bash
# Check error logs
kubectl logs -n production deployment/video-api --tail=500 | grep ERROR

# Check external dependencies
kubectl get pods -n production -l app=redis
kubectl get pods -n production -l app=database

# Rollback if needed
kubectl rollout undo deployment/video-api -n production
```

#### Issue 3: Slow Response Time

**Symptoms:**
- Prometheus alert: `SlowResponseTime`
- Users experiencing timeouts

**Solutions:**
```bash
# Check resource usage
kubectl top pods -n production -l app=video-api

# Check cache hit rate
# Should be > 80%

# Scale up if needed
kubectl scale deployment/video-api -n production --replicas=5

# Check database performance
# Look for slow queries
```

#### Issue 4: Low Cache Hit Rate

**Symptoms:**
- Prometheus alert: `LowCacheHitRate`
- High YouTube API usage

**Solutions:**
```bash
# Check Redis status
kubectl get pods -n production -l app=redis

# Check Redis logs
kubectl logs -n production deployment/redis

# Restart Redis if needed
kubectl rollout restart deployment/redis -n production

# Clear cache and warm up
kubectl exec -n production deployment/redis -- redis-cli FLUSHALL
```

## Performance Tuning

### Scaling

```bash
# Horizontal scaling
kubectl scale deployment/video-api -n production --replicas=5

# Autoscaling
kubectl autoscale deployment/video-api -n production \
  --min=3 --max=10 --cpu-percent=70
```

### Resource Limits

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Cache Configuration

```bash
# Increase cache TTL
kubectl set env deployment/video-api -n production \
  CACHE_TTL_SECONDS=7200

# Increase cache size
kubectl set env deployment/video-api -n production \
  MAX_CACHE_SIZE=200
```

## Security Considerations

### Secrets Management

```bash
# Create secrets
kubectl create secret generic video-api-secrets -n production \
  --from-literal=youtube-api-key=$YOUTUBE_API_KEY \
  --from-literal=database-password=$DB_PASSWORD

# Update deployment to use secrets
kubectl set env deployment/video-api -n production \
  --from=secret/video-api-secrets
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: video-api-network-policy
spec:
  podSelector:
    matchLabels:
      app: video-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
```

## Maintenance

### Regular Tasks

**Daily:**
- Check Grafana dashboard
- Review Prometheus alerts
- Check error logs

**Weekly:**
- Review performance metrics
- Analyze cache hit rate trends
- Check YouTube API quota usage
- Review and update documentation

**Monthly:**
- Performance optimization review
- Security updates
- Dependency updates
- Disaster recovery drill

### Backup Strategy

```bash
# Backup deployment configuration
kubectl get deployment video-api -n production -o yaml > backup.yaml

# Backup configmaps
kubectl get configmap -n production -o yaml > configmaps-backup.yaml

# Backup secrets (encrypted)
kubectl get secrets -n production -o yaml > secrets-backup.yaml.enc
```

## Contact Information

### On-Call Rotation

| Day | Engineer | Phone | Email |
|-----|----------|-------|-------|
| Mon-Tue | Engineer A | +90 XXX XXX XX XX | engineer-a@example.com |
| Wed-Thu | Engineer B | +90 XXX XXX XX XX | engineer-b@example.com |
| Fri-Sun | Engineer C | +90 XXX XXX XX XX | engineer-c@example.com |

### Escalation Path

1. **Level 1:** On-call engineer
2. **Level 2:** DevOps lead
3. **Level 3:** CTO

### Communication Channels

- **Slack:** #deployments, #incidents, #devops
- **Email:** devops@example.com
- **PagerDuty:** video-api-production

## References

- [Rollback Plan](./rollback_plan.md)
- [Grafana Dashboard](./monitoring/grafana_dashboard.json)
- [Prometheus Alerts](./monitoring/prometheus_alerts.yml)
- [Architecture Design](../.kiro/specs/learning-path-video-fix/design.md)
- [Requirements](../.kiro/specs/learning-path-video-fix/requirements.md)

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-02 | DevOps Team | Initial deployment guide |

---

**Last Updated:** 2025-01-02  
**Maintained By:** DevOps Team  
**Review Cycle:** Monthly
