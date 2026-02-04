# Quick Reference - Production Deployment

## 🚀 Quick Deploy

```bash
# 1. Build and push image
docker build -t video-api:v1.2.0 .
docker push registry.example.com/video-api:v1.2.0

# 2. Deploy
cd backend/deployment
chmod +x *.sh
./production_deploy.sh v1.2.0

# 3. Verify
./post_deployment_verification.sh
```

## 🔄 Quick Rollback

```bash
# Automatic (if deployment fails)
# - Script will rollback automatically

# Manual
kubectl rollout undo deployment/video-api -n production
kubectl rollout status deployment/video-api -n production
```

## 📊 Quick Monitoring

```bash
# Grafana Dashboard
kubectl port-forward -n monitoring svc/grafana 3000:3000
# http://localhost:3000/d/video-api-dashboard

# Prometheus Alerts
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# http://localhost:9090/alerts

# Logs
kubectl logs -f deployment/video-api -n production
```

## 🔍 Quick Troubleshooting

```bash
# Check pod status
kubectl get pods -n production -l app=video-api

# Check logs
kubectl logs -n production deployment/video-api --tail=100

# Check health
curl https://api.example.com/api/youtube/health

# Scale up
kubectl scale deployment/video-api -n production --replicas=5

# Restart
kubectl rollout restart deployment/video-api -n production
```

## 📋 Quick Checklist

### Pre-Deployment
- [ ] All tests pass
- [ ] Docker image built and pushed
- [ ] Team notified
- [ ] Backup plan ready

### During Deployment
- [ ] Monitor rollout status
- [ ] Watch pod logs
- [ ] Check health endpoint
- [ ] Run smoke tests

### Post-Deployment
- [ ] Verify all checks pass
- [ ] Monitor for 24 hours
- [ ] Check Grafana dashboard
- [ ] Review Prometheus alerts
- [ ] Update documentation

## 🚨 Emergency Contacts

| Role | Contact |
|------|---------|
| On-Call Engineer | +90 XXX XXX XX XX |
| DevOps Lead | devops-lead@example.com |
| Slack | #incidents |

## 📈 Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Availability | 99.9% | < 99.9% |
| P95 Response Time | < 3s | > 3s |
| Error Rate | < 1% | > 5% |
| Cache Hit Rate | > 80% | < 60% |

## 🔗 Quick Links

- [Full Deployment Guide](./README.md)
- [Rollback Plan](./rollback_plan.md)
- [Grafana Dashboard](./monitoring/grafana_dashboard.json)
- [Prometheus Alerts](./monitoring/prometheus_alerts.yml)

## 💡 Common Commands

```bash
# View deployment history
kubectl rollout history deployment/video-api -n production

# Pause rollout
kubectl rollout pause deployment/video-api -n production

# Resume rollout
kubectl rollout resume deployment/video-api -n production

# Check resource usage
kubectl top pods -n production -l app=video-api

# Get pod details
kubectl describe pods -n production -l app=video-api

# Execute command in pod
kubectl exec -it -n production deployment/video-api -- /bin/bash

# Port forward for local testing
kubectl port-forward -n production deployment/video-api 8000:8000
```

## 🎯 Success Criteria

✅ All pods running and ready  
✅ Health endpoint returns "healthy"  
✅ Smoke tests pass  
✅ Response time < 3s  
✅ Error rate < 1%  
✅ Cache hit rate > 80%  
✅ No critical alerts firing  

---

**Need Help?** Check [README.md](./README.md) or contact DevOps team.
