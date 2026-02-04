# Video API Deployment - Quick Reference Card

## 🚀 Quick Deploy

```bash
# 1. Build & Test
docker build -f Dockerfile.video-api -t ghcr.io/turkiye-sinav/video-api:latest .
./scripts/test-docker-image.sh

# 2. Push
docker push ghcr.io/turkiye-sinav/video-api:latest

# 3. Deploy
./scripts/deploy.sh deploy

# 4. Verify
kubectl get pods -n video-api -w
```

## 📋 Essential Commands

### Deployment
```bash
# Deploy
kubectl apply -f k8s/video-api-deployment.yaml

# Check status
kubectl rollout status deployment/video-api -n video-api

# Rollback
kubectl rollout undo deployment/video-api -n video-api
```

### Monitoring
```bash
# Logs
kubectl logs -f deployment/video-api -n video-api

# Metrics
kubectl top pods -n video-api

# Health check
kubectl exec -it <pod> -n video-api -- curl http://localhost:8000/api/youtube/health
```

### Scaling
```bash
# Manual scale
kubectl scale deployment/video-api --replicas=5 -n video-api

# Check HPA
kubectl get hpa -n video-api
```

### Troubleshooting
```bash
# Describe pod
kubectl describe pod <pod-name> -n video-api

# Events
kubectl get events -n video-api --sort-by='.lastTimestamp'

# Port forward
kubectl port-forward -n video-api service/video-api-service 8000:8000
```

## 🔧 Configuration

### Environment Variables
```bash
# Required secrets
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
JWT_SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_PASSWORD=<redis-password>
YOUTUBE_API_KEY=<youtube-api-key>
SENTRY_DSN=<sentry-dsn>
```

### Resource Limits
```yaml
requests:
  memory: "512Mi"
  cpu: "250m"
limits:
  memory: "2Gi"
  cpu: "1000m"
```

### Health Checks
- **Liveness:** 60s initial, 30s period, 10s timeout
- **Readiness:** 30s initial, 10s period, 5s timeout
- **Startup:** 10s initial, 5s period, 12 failures (60s)

## 📊 Monitoring URLs

- **Grafana:** http://grafana.yourdomain.com
- **Prometheus:** http://prometheus.yourdomain.com
- **Sentry:** https://sentry.io/your-project

## 🔐 Security Checklist

- [ ] Secrets in external secret management
- [ ] Non-root user configured
- [ ] Network policies applied
- [ ] TLS/SSL configured
- [ ] Rate limiting enabled
- [ ] CORS configured
- [ ] Image scanned for vulnerabilities

## 📈 Performance Targets

- **Response Time:** P95 < 3s
- **Cache Hit Rate:** > 80%
- **Error Rate:** < 1%
- **Uptime:** > 99.9%

## 🆘 Emergency Contacts

- **DevOps:** devops@yourdomain.com
- **On-call:** +90 XXX XXX XX XX
- **Slack:** #video-api-alerts

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [README](README.md)
- [Task Summary](TASK_21_COMPLETION_SUMMARY.md)
