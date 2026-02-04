# Production Monitoring Checklist
## Video Recommendation System - Türkiye Üniversite Sınavları Hazırlık Platformu

Bu doküman, production ortamında video öneri sisteminin sağlığını ve performansını izlemek için günlük, haftalık ve aylık kontrol listelerini içermektedir.

## İçindekiler

1. [Günlük Kontroller](#günlük-kontroller)
2. [Haftalık Kontroller](#haftalık-kontroller)
3. [Aylık Kontroller](#aylık-kontroller)
4. [Kritik Metrikler](#kritik-metrikler)
5. [Alert Thresholds](#alert-thresholds)
6. [Dashboard Links](#dashboard-links)
7. [Incident Response](#incident-response)

---

## Günlük Kontroller

### Sabah Kontrolü (09:00)

#### 1. System Health Overview

**Grafana Dashboard:** [System Health Overview](https://grafana.yourdomain.com/d/system-health)

- [ ] **Uptime:** Tüm servisler çalışıyor mu?
  - Backend pods: 3/3 Running
  - Database: Healthy
  - Redis: Healthy
  - Elasticsearch: Healthy

- [ ] **Error Rate:** < 2%
  - Video API error rate
  - Overall application error rate
  - Database error rate

- [ ] **Response Time:** P95 < 3 saniye
  - Video recommendations endpoint
  - Health check endpoint
  - Database queries

**Komutlar:**
```bash
# Pod durumu
kubectl get pods -n turkiye-sinav-platform

# Health check
curl https://api.yourdomain.com/health
curl https://api.yourdomain.com/api/youtube/health

# Error rate (son 1 saat)
curl https://api.yourdomain.com/metrics | grep video_errors_total
```

#### 2. Video API Metrics

**Grafana Dashboard:** [Video API Dashboard](https://grafana.yourdomain.com/d/video-api)

- [ ] **Request Volume:** Normal range içinde mi?
  - Son 24 saat: 10,000 - 50,000 requests
  - Peak hours (14:00-22:00): 2,000 - 5,000 req/hour

- [ ] **Cache Hit Rate:** > 80%
  - Redis cache hit rate
  - In-memory cache hit rate
  - Overall cache effectiveness

- [ ] **YouTube API Quota:** > 20% kaldı mı?
  - Daily quota: 10,000
  - Current usage: < 8,000
  - Quota reset time: 00:00 UTC

**Komutlar:**
```bash
# Cache hit rate
curl https://api.yourdomain.com/api/youtube/health | jq '.components.cache.hit_rate'

# YouTube API quota
curl https://api.yourdomain.com/api/youtube/health | jq '.components.youtube_api.quota_remaining'

# Request volume (Prometheus)
curl https://prometheus.yourdomain.com/api/v1/query?query=rate(video_requests_total[1h])
```

#### 3. Database Performance

**Grafana Dashboard:** [Database Performance](https://grafana.yourdomain.com/d/database)

- [ ] **Connection Pool:** Healthy
  - Active connections: < 40 (max 50)
  - Idle connections: > 10
  - No connection timeouts

- [ ] **Query Performance:** Normal
  - Slow queries (>1s): < 10 per hour
  - Average query time: < 100ms
  - No deadlocks

- [ ] **Disk Space:** > 20% free
  - Database volume: < 80% used
  - WAL archive: < 70% used

**Komutlar:**
```bash
# Connection pool status
kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
  psql -U postgres -d turkiye_sinav_db -c "SELECT * FROM pg_stat_activity;"

# Slow queries
kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
  psql -U postgres -d turkiye_sinav_db -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Disk space
kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- df -h
```

#### 4. Cache Performance

**Grafana Dashboard:** [Cache Performance](https://grafana.yourdomain.com/d/cache)

- [ ] **Redis Health:** Operational
  - Memory usage: < 80%
  - Eviction rate: < 100 keys/min
  - Connected clients: < 100

- [ ] **Cache Effectiveness:** Good
  - Hit rate: > 80%
  - Miss rate: < 20%
  - Average response time: < 10ms

**Komutlar:**
```bash
# Redis info
kubectl exec -it statefulset/redis-0 -n turkiye-sinav-platform -- \
  redis-cli -a <password> INFO stats

# Cache hit rate
kubectl exec -it statefulset/redis-0 -n turkiye-sinav-platform -- \
  redis-cli -a <password> INFO stats | grep keyspace_hits
```

#### 5. Error Logs Review

**Sentry Dashboard:** [Error Tracking](https://sentry.io/organizations/your-org/issues/)

- [ ] **New Errors:** Yeni error pattern var mı?
  - Unhandled exceptions
  - API errors
  - Database errors

- [ ] **Error Frequency:** Artış var mı?
  - Compare with yesterday
  - Check for spikes

- [ ] **Critical Errors:** P0/P1 error var mı?
  - Data corruption
  - Security issues
  - Service outages

**Komutlar:**
```bash
# Recent errors (son 1 saat)
kubectl logs -n turkiye-sinav-platform deployment/turkiye-sinav-app --since=1h | grep "ERROR"

# Error count by type
kubectl logs -n turkiye-sinav-platform deployment/turkiye-sinav-app --since=1h | grep "ERROR" | awk '{print $5}' | sort | uniq -c | sort -rn
```

---

### Akşam Kontrolü (18:00)

#### 1. Peak Hour Performance

- [ ] **Response Time:** Peak saatlerde normal mi?
  - P95 latency: < 3s
  - P99 latency: < 5s

- [ ] **Error Rate:** Peak saatlerde artış var mı?
  - Should remain < 2%

- [ ] **Resource Usage:** Yeterli mi?
  - CPU: < 70%
  - Memory: < 80%
  - Disk I/O: Normal

#### 2. Daily Summary

- [ ] **Total Requests:** Beklenen range içinde mi?
- [ ] **Unique Users:** Normal aktivite mi?
- [ ] **Cache Performance:** Hedeflere ulaşıldı mı?
- [ ] **YouTube API Quota:** Günlük limit içinde mi?

**Komutlar:**
```bash
# Daily summary
curl https://api.yourdomain.com/api/youtube/health | jq '.metrics'

# Resource usage
kubectl top pods -n turkiye-sinav-platform
kubectl top nodes
```

---

## Haftalık Kontroller

### Pazartesi Sabahı (09:00)

#### 1. Weekly Performance Review

**Grafana Dashboard:** [Weekly Performance](https://grafana.yourdomain.com/d/weekly-performance)

- [ ] **Trend Analysis:** Son hafta trendleri
  - Request volume trend
  - Error rate trend
  - Latency trend
  - Cache hit rate trend

- [ ] **Capacity Planning:** Kaynak kullanımı
  - CPU usage trend
  - Memory usage trend
  - Disk usage trend
  - Network bandwidth

- [ ] **Cost Analysis:** Maliyet optimizasyonu
  - YouTube API quota usage
  - Cloud resource costs
  - Database storage costs

#### 2. Database Maintenance

- [ ] **Vacuum & Analyze:** Database optimization
  ```bash
  kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
    psql -U postgres -d turkiye_sinav_db -c "VACUUM ANALYZE;"
  ```

- [ ] **Index Health:** Index'ler optimize mi?
  ```bash
  kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
    psql -U postgres -d turkiye_sinav_db -c "SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;"
  ```

- [ ] **Bloat Check:** Table/index bloat var mı?
  ```bash
  kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
    psql -U postgres -d turkiye_sinav_db -f /scripts/check_bloat.sql
  ```

#### 3. Cache Optimization

- [ ] **Cache Key Analysis:** Hangi key'ler en çok kullanılıyor?
  ```bash
  kubectl exec -it statefulset/redis-0 -n turkiye-sinav-platform -- \
    redis-cli -a <password> --bigkeys
  ```

- [ ] **Eviction Policy:** Eviction rate normal mi?
  ```bash
  kubectl exec -it statefulset/redis-0 -n turkiye-sinav-platform -- \
    redis-cli -a <password> INFO stats | grep evicted_keys
  ```

- [ ] **Memory Fragmentation:** Fragmentation ratio < 1.5
  ```bash
  kubectl exec -it statefulset/redis-0 -n turkiye-sinav-platform -- \
    redis-cli -a <password> INFO memory | grep mem_fragmentation_ratio
  ```

#### 4. Security Review

- [ ] **Failed Login Attempts:** Brute force attack var mı?
- [ ] **Suspicious API Calls:** Rate limit violations
- [ ] **SSL Certificate:** Expiry date kontrol
- [ ] **Dependency Updates:** Security patches var mı?

**Komutlar:**
```bash
# Failed login attempts
kubectl logs -n turkiye-sinav-platform deployment/turkiye-sinav-app --since=7d | grep "authentication_failed"

# Rate limit violations
kubectl logs -n turkiye-sinav-platform deployment/turkiye-sinav-app --since=7d | grep "rate_limit_exceeded"

# SSL certificate expiry
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

#### 5. Backup Verification

- [ ] **Database Backups:** Son 7 gün backup'ları mevcut mu?
  ```bash
  ls -lh backups/postgres/ | tail -7
  ```

- [ ] **Backup Integrity:** Backup'lar restore edilebilir mi?
  ```bash
  # Test restore (staging environment)
  ./scripts/test_restore.sh backups/postgres/latest.sql
  ```

- [ ] **Backup Size:** Beklenmedik artış var mı?
  ```bash
  du -sh backups/postgres/* | tail -7
  ```

---

## Aylık Kontroller

### Ayın İlk Pazartesi (09:00)

#### 1. Monthly Performance Report

- [ ] **SLA Compliance:** SLA hedeflerine ulaşıldı mı?
  - Uptime: > 99.9%
  - P95 latency: < 3s
  - Error rate: < 2%

- [ ] **User Metrics:** Kullanıcı aktivitesi
  - Total users
  - Active users
  - User retention

- [ ] **Business Metrics:** İş metrikleri
  - Video recommendations served
  - Cache hit rate
  - YouTube API quota usage

#### 2. Capacity Planning

- [ ] **Resource Forecast:** 3 aylık projeksiyon
  - CPU requirements
  - Memory requirements
  - Storage requirements
  - Network bandwidth

- [ ] **Scaling Plan:** Ölçeklendirme gerekli mi?
  - Horizontal scaling (more pods)
  - Vertical scaling (bigger pods)
  - Database scaling

- [ ] **Cost Optimization:** Maliyet optimizasyonu
  - Unused resources
  - Over-provisioned resources
  - Reserved instances

#### 3. Security Audit

- [ ] **Vulnerability Scan:** Security vulnerabilities
  ```bash
  # Trivy container scan
  trivy image ghcr.io/org/turkiye-sinav-backend:latest
  ```

- [ ] **Dependency Audit:** Outdated dependencies
  ```bash
  # Python dependencies
  pip list --outdated
  
  # Security vulnerabilities
  safety check
  ```

- [ ] **Access Review:** User access kontrolü
  - Kubernetes RBAC
  - Database users
  - API keys

#### 4. Disaster Recovery Drill

- [ ] **Backup Restore Test:** Full restore test
  ```bash
  # Staging environment'ta full restore
  ./scripts/disaster_recovery_drill.sh
  ```

- [ ] **Failover Test:** Failover senaryosu
  - Database failover
  - Redis failover
  - Multi-region failover (if applicable)

- [ ] **RTO/RPO Verification:** Recovery time/point objectives
  - RTO: < 1 hour
  - RPO: < 15 minutes

#### 5. Documentation Update

- [ ] **Runbook Update:** Runbook güncel mi?
- [ ] **Architecture Diagram:** Diagram güncel mi?
- [ ] **API Documentation:** API docs güncel mi?
- [ ] **Monitoring Dashboard:** Dashboard'lar güncel mi?

---

## Kritik Metrikler

### Video API Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Request Rate | 1000-5000/hour | >6000/hour | >8000/hour |
| Error Rate | <2% | 2-5% | >5% |
| P95 Latency | <3s | 3-5s | >5s |
| P99 Latency | <5s | 5-10s | >10s |
| Cache Hit Rate | >80% | 70-80% | <70% |
| YouTube API Quota | >20% | 10-20% | <10% |

### System Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| CPU Usage | <70% | 70-85% | >85% |
| Memory Usage | <80% | 80-90% | >90% |
| Disk Usage | <80% | 80-90% | >90% |
| Network Bandwidth | <70% | 70-85% | >85% |

### Database Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Connection Pool | <40/50 | 40-45/50 | >45/50 |
| Query Latency | <100ms | 100-500ms | >500ms |
| Slow Queries | <10/hour | 10-50/hour | >50/hour |
| Replication Lag | <1s | 1-5s | >5s |

### Cache Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Hit Rate | >80% | 70-80% | <70% |
| Memory Usage | <80% | 80-90% | >90% |
| Eviction Rate | <100/min | 100-500/min | >500/min |
| Response Time | <10ms | 10-50ms | >50ms |

---

## Alert Thresholds

### P0 - Critical (Immediate Response)

**PagerDuty:** Immediate notification
**Response Time:** 0-5 minutes

- Video API error rate > 10%
- Video API P95 latency > 10s
- Health check failure (3 consecutive)
- Database connection failure
- Redis connection failure
- Pod crash loop (5 restarts in 5 min)
- Disk space > 95%

### P1 - High (Urgent Response)

**PagerDuty:** Notification within 15 minutes
**Response Time:** 5-15 minutes

- Video API error rate > 5%
- Video API P95 latency > 5s
- Cache hit rate < 50%
- YouTube API quota < 10%
- CPU usage > 85%
- Memory usage > 90%
- Database slow queries > 50/hour

### P2 - Medium (Normal Response)

**Slack:** Notification
**Response Time:** 15-60 minutes

- Video API error rate > 2%
- Video API P95 latency > 3s
- Cache hit rate < 70%
- YouTube API quota < 20%
- CPU usage > 70%
- Memory usage > 80%
- Database slow queries > 10/hour

### P3 - Low (Informational)

**Slack:** Notification
**Response Time:** Best effort

- Video API error rate > 1%
- Cache hit rate < 80%
- YouTube API quota < 30%
- Unusual traffic patterns
- Minor performance degradation

---

## Dashboard Links

### Grafana Dashboards

1. **System Health Overview**
   - URL: https://grafana.yourdomain.com/d/system-health
   - Refresh: 30s
   - Time range: Last 24 hours

2. **Video API Dashboard**
   - URL: https://grafana.yourdomain.com/d/video-api
   - Refresh: 10s
   - Time range: Last 6 hours

3. **Database Performance**
   - URL: https://grafana.yourdomain.com/d/database
   - Refresh: 1m
   - Time range: Last 24 hours

4. **Cache Performance**
   - URL: https://grafana.yourdomain.com/d/cache
   - Refresh: 30s
   - Time range: Last 6 hours

5. **Infrastructure Metrics**
   - URL: https://grafana.yourdomain.com/d/infrastructure
   - Refresh: 1m
   - Time range: Last 24 hours

### Prometheus Queries

**Video API Request Rate:**
```promql
rate(video_requests_total[5m])
```

**Video API Error Rate:**
```promql
rate(video_errors_total[5m]) / rate(video_requests_total[5m])
```

**Video API P95 Latency:**
```promql
histogram_quantile(0.95, rate(video_response_time_seconds_bucket[5m]))
```

**Cache Hit Rate:**
```promql
rate(video_cache_hits_total[5m]) / rate(video_cache_requests_total[5m])
```

**YouTube API Quota Remaining:**
```promql
youtube_api_quota_remaining
```

---

## Incident Response

### Incident Severity Levels

**P0 - Critical:**
- Service completely down
- Data loss or corruption
- Security breach
- Response: Immediate (0-5 min)

**P1 - High:**
- Major feature broken
- Significant performance degradation
- High error rate
- Response: Urgent (5-15 min)

**P2 - Medium:**
- Minor feature broken
- Moderate performance degradation
- Elevated error rate
- Response: Normal (15-60 min)

**P3 - Low:**
- Cosmetic issues
- Minor performance issues
- Low error rate
- Response: Best effort

### Incident Response Process

1. **Detect:** Alert triggered or user report
2. **Acknowledge:** On-call engineer acknowledges
3. **Assess:** Determine severity and impact
4. **Communicate:** Notify team and stakeholders
5. **Mitigate:** Implement immediate fix or rollback
6. **Resolve:** Verify issue is resolved
7. **Document:** Create incident report
8. **Post-Mortem:** Schedule post-mortem meeting

### Communication Templates

**Incident Start (Slack):**
```
🚨 INCIDENT: [P0/P1/P2] Video API Down
Status: Investigating
Impact: Users cannot load video recommendations
Started: 2025-11-03 10:30 UTC
On-Call: @engineer
Updates: Every 15 minutes
```

**Incident Update:**
```
📊 UPDATE: [P0/P1/P2] Video API Down
Status: Identified - YouTube API quota exhausted
Action: Switching to cache-only mode
ETA: 5 minutes
Next Update: 10:50 UTC
```

**Incident Resolved:**
```
✅ RESOLVED: [P0/P1/P2] Video API Down
Status: Resolved
Duration: 20 minutes
Root Cause: YouTube API quota exhausted
Fix: Implemented cache-only fallback
Post-Mortem: Scheduled for 2025-11-04 14:00
```

---

## Monitoring Tools

### Required Tools

1. **Grafana:** Metrics visualization
   - URL: https://grafana.yourdomain.com
   - Login: SSO

2. **Prometheus:** Metrics collection
   - URL: https://prometheus.yourdomain.com
   - Login: Basic auth

3. **Sentry:** Error tracking
   - URL: https://sentry.io/organizations/your-org
   - Login: SSO

4. **PagerDuty:** Incident management
   - URL: https://turkiye-sinav.pagerduty.com
   - Mobile app: Required for on-call

5. **Kubernetes Dashboard:** Cluster management
   - URL: https://k8s.yourdomain.com
   - Login: kubectl proxy

### Optional Tools

1. **Datadog:** APM and monitoring
2. **New Relic:** Application performance
3. **Elastic APM:** Distributed tracing
4. **Jaeger:** Distributed tracing

---

## Checklist Summary

### Daily (2x per day)
- [ ] System health check
- [ ] Error logs review
- [ ] Performance metrics
- [ ] Cache performance
- [ ] Database health

### Weekly (1x per week)
- [ ] Performance trend analysis
- [ ] Database maintenance
- [ ] Cache optimization
- [ ] Security review
- [ ] Backup verification

### Monthly (1x per month)
- [ ] Performance report
- [ ] Capacity planning
- [ ] Security audit
- [ ] Disaster recovery drill
- [ ] Documentation update

---

**Son Güncelleme:** 3 Kasım 2025
**Versiyon:** 1.0.0
**Hazırlayan:** DevOps Team
