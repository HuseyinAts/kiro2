# Rollback Plan - Video Recommendation System
## Türkiye Üniversite Sınavları Hazırlık Platformu

Bu doküman, production deployment'ında sorun çıkması durumunda hızlı ve güvenli rollback yapılması için detaylı prosedürleri içermektedir.

## İçindekiler

1. [Rollback Kriterleri](#rollback-kriterleri)
2. [Rollback Tipleri](#rollback-tipleri)
3. [Kubernetes Rollback](#kubernetes-rollback)
4. [Docker Compose Rollback](#docker-compose-rollback)
5. [Database Rollback](#database-rollback)
6. [Cache Invalidation](#cache-invalidation)
7. [Emergency Procedures](#emergency-procedures)
8. [Post-Rollback Verification](#post-rollback-verification)

---

## Rollback Kriterleri

### Otomatik Rollback Tetikleyicileri

Aşağıdaki durumlardan biri gerçekleşirse **OTOMATIK ROLLBACK** başlatılır:

1. **Error Rate > 10%** (5 dakika boyunca)
2. **P95 Latency > 10 saniye** (5 dakika boyunca)
3. **Health Check Failure** (3 ardışık başarısızlık)
4. **Pod Crash Loop** (5 dakika içinde 3 restart)
5. **Database Connection Failure** (1 dakika boyunca)

### Manuel Rollback Kriterleri

Aşağıdaki durumlardan biri gerçekleşirse **MANUEL ROLLBACK** değerlendirilmelidir:

1. **Error Rate > 5%** (10 dakika boyunca)
2. **P95 Latency > 5 saniye** (10 dakika boyunca)
3. **Cache Hit Rate < 50%** (sürekli)
4. **YouTube API Quota Exhausted** (beklenmedik şekilde)
5. **Memory Leak** (memory usage sürekli artıyor)
6. **Critical Bug** (data corruption, security issue)

### Rollback Karar Matrisi

| Severity | Error Rate | Latency | Action | Timeline |
|----------|-----------|---------|--------|----------|
| P0 - Critical | >10% | >10s | Immediate Rollback | 0-5 min |
| P1 - High | 5-10% | 5-10s | Evaluate & Rollback | 5-15 min |
| P2 - Medium | 2-5% | 3-5s | Monitor & Decide | 15-30 min |
| P3 - Low | <2% | <3s | Monitor Only | N/A |

---

## Rollback Tipleri

### 1. Application Rollback (En Yaygın)

**Süre:** 2-5 dakika
**Etki:** Minimal downtime (rolling update ile zero downtime)
**Kapsam:** Backend application code

### 2. Database Rollback

**Süre:** 5-30 dakika (migration complexity'e bağlı)
**Etki:** Downtime gerekebilir
**Kapsam:** Database schema ve data

### 3. Full Stack Rollback

**Süre:** 10-20 dakika
**Etki:** Tüm servisler etkilenir
**Kapsam:** Application + Database + Cache

### 4. Partial Rollback (Canary)

**Süre:** 1-2 dakika
**Etki:** Sadece canary traffic etkilenir
**Kapsam:** Canary deployment pods

---

## Kubernetes Rollback

### 1. Hızlı Rollback (Son Deployment)

```bash
# ADIM 1: Mevcut durumu kontrol et
kubectl get deployments -n turkiye-sinav-platform
kubectl get pods -n turkiye-sinav-platform

# ADIM 2: Rollback başlat
kubectl rollout undo deployment/turkiye-sinav-app -n turkiye-sinav-platform

# ADIM 3: Rollback durumunu izle
kubectl rollout status deployment/turkiye-sinav-app -n turkiye-sinav-platform

# ADIM 4: Pod'ların sağlıklı olduğunu doğrula
kubectl get pods -n turkiye-sinav-platform -w

# Beklenen süre: 2-3 dakika
```

### 2. Belirli Revision'a Rollback

```bash
# ADIM 1: Rollout history'yi görüntüle
kubectl rollout history deployment/turkiye-sinav-app -n turkiye-sinav-platform

# Çıktı örneği:
# REVISION  CHANGE-CAUSE
# 1         Initial deployment
# 2         Update to v1.1.0
# 3         Update to v1.2.0 (CURRENT)

# ADIM 2: Belirli revision'ın detaylarını gör
kubectl rollout history deployment/turkiye-sinav-app --revision=2 -n turkiye-sinav-platform

# ADIM 3: Belirli revision'a rollback
kubectl rollout undo deployment/turkiye-sinav-app --to-revision=2 -n turkiye-sinav-platform

# ADIM 4: Rollback durumunu izle
kubectl rollout status deployment/turkiye-sinav-app -n turkiye-sinav-platform
```

### 3. Tüm Servisleri Rollback

```bash
# Backend
kubectl rollout undo deployment/turkiye-sinav-app -n turkiye-sinav-platform

# Celery Worker
kubectl rollout undo deployment/turkiye-sinav-worker -n turkiye-sinav-platform

# Celery Beat
kubectl rollout undo deployment/turkiye-sinav-scheduler -n turkiye-sinav-platform

# Nginx (gerekirse)
kubectl rollout undo deployment/turkiye-sinav-nginx -n turkiye-sinav-platform

# Tüm rollback'lerin tamamlanmasını bekle
kubectl wait --for=condition=available --timeout=300s \
  deployment/turkiye-sinav-app \
  deployment/turkiye-sinav-worker \
  deployment/turkiye-sinav-scheduler \
  -n turkiye-sinav-platform
```

### 4. Rollback Verification

```bash
# Pod'ların durumunu kontrol et
kubectl get pods -n turkiye-sinav-platform

# Tüm pod'lar Running ve Ready olmalı
# NAME                                    READY   STATUS    RESTARTS   AGE
# turkiye-sinav-app-7d8f9c5b6d-abc12     1/1     Running   0          2m
# turkiye-sinav-app-7d8f9c5b6d-def34     1/1     Running   0          2m
# turkiye-sinav-app-7d8f9c5b6d-ghi56     1/1     Running   0          2m

# Health check
kubectl exec -it deployment/turkiye-sinav-app -n turkiye-sinav-platform -- \
  curl -f http://localhost:8000/health

# Logs kontrol
kubectl logs -f deployment/turkiye-sinav-app -n turkiye-sinav-platform --tail=50
```

---

## Docker Compose Rollback

### 1. Image Tag Rollback

```bash
# ADIM 1: Mevcut container'ları durdur
docker-compose -f docker-compose.production.yml down

# ADIM 2: Önceki image tag'ini kullan
# .env.production dosyasını düzenle:
# IMAGE_TAG=v1.1.0  # Önceki stable version

# ADIM 3: Container'ları yeniden başlat
docker-compose -f docker-compose.production.yml up -d

# ADIM 4: Container'ların sağlıklı olduğunu doğrula
docker-compose -f docker-compose.production.yml ps

# Beklenen süre: 3-5 dakika
```

### 2. Volume Backup'tan Restore

```bash
# ADIM 1: Container'ları durdur
docker-compose -f docker-compose.production.yml down

# ADIM 2: Volume'leri backup'tan restore et
docker run --rm -v postgres-data:/data -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/postgres-data-backup-2025-11-02.tar.gz"

docker run --rm -v redis-data:/data -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/redis-data-backup-2025-11-02.tar.gz"

# ADIM 3: Container'ları başlat
docker-compose -f docker-compose.production.yml up -d

# ADIM 4: Data integrity kontrol
docker exec -it turkiye_sinav_postgres psql -U postgres -d turkiye_sinav_db -c "SELECT COUNT(*) FROM users;"
```

### 3. Full Stack Rollback

```bash
# ADIM 1: Tüm servisleri durdur
docker-compose -f docker-compose.production.yml down -v

# ADIM 2: Backup'tan restore et (script)
./scripts/restore_from_backup.sh 2025-11-02

# ADIM 3: Önceki docker-compose.yml kullan
git checkout v1.1.0 -- docker-compose.production.yml

# ADIM 4: Servisleri başlat
docker-compose -f docker-compose.production.yml up -d

# ADIM 5: Health check
curl http://localhost/health
```

---

## Database Rollback

### 1. Alembic Migration Rollback

```bash
# ADIM 1: Mevcut migration durumunu kontrol et
docker exec -it turkiye_sinav_backend alembic current

# ADIM 2: Migration history'yi görüntüle
docker exec -it turkiye_sinav_backend alembic history

# ADIM 3: Bir migration geri al
docker exec -it turkiye_sinav_backend alembic downgrade -1

# ADIM 4: Belirli bir revision'a geri al
docker exec -it turkiye_sinav_backend alembic downgrade <revision_id>

# ADIM 5: Migration durumunu doğrula
docker exec -it turkiye_sinav_backend alembic current

# Beklenen süre: 1-10 dakika (migration complexity'e bağlı)
```

### 2. Database Backup'tan Restore

```bash
# ADIM 1: Database backup listesini görüntüle
ls -lh backups/postgres/

# ADIM 2: Application'ı durdur (data corruption önlemek için)
kubectl scale deployment/turkiye-sinav-app --replicas=0 -n turkiye-sinav-platform

# ADIM 3: Database'i backup'tan restore et
kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
  psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS turkiye_sinav_db;"

kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
  psql -U postgres -d postgres -c "CREATE DATABASE turkiye_sinav_db;"

kubectl cp backups/postgres/turkiye_sinav_db-2025-11-02.sql \
  turkiye-sinav-platform/postgres-0:/tmp/restore.sql

kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
  psql -U postgres -d turkiye_sinav_db -f /tmp/restore.sql

# ADIM 4: Data integrity kontrol
kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
  psql -U postgres -d turkiye_sinav_db -c "SELECT COUNT(*) FROM users;"

# ADIM 5: Application'ı yeniden başlat
kubectl scale deployment/turkiye-sinav-app --replicas=3 -n turkiye-sinav-platform

# Beklenen süre: 10-30 dakika (database size'a bağlı)
```

### 3. Point-in-Time Recovery (PITR)

```bash
# PostgreSQL PITR kullanarak belirli bir zamana geri dön
# Not: Bu özellik için PostgreSQL'in WAL archiving aktif olmalı

# ADIM 1: Recovery config oluştur
cat > recovery.conf <<EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2025-11-03 10:30:00'
recovery_target_action = 'promote'
EOF

# ADIM 2: PostgreSQL'i recovery mode'da başlat
kubectl cp recovery.conf turkiye-sinav-platform/postgres-0:/var/lib/postgresql/data/

kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
  pg_ctl restart -D /var/lib/postgresql/data

# ADIM 3: Recovery tamamlanmasını bekle
kubectl logs -f statefulset/postgres-0 -n turkiye-sinav-platform | grep "recovery"

# Beklenen süre: 15-60 dakika (WAL size'a bağlı)
```

---

## Cache Invalidation

### 1. Redis Cache Temizleme

```bash
# ADIM 1: Video cache'i temizle
kubectl exec -it statefulset/redis-0 -n turkiye-sinav-platform -- \
  redis-cli -a <password> --scan --pattern "video_rec:*" | xargs redis-cli -a <password> DEL

# ADIM 2: Tüm cache'i temizle (dikkatli kullan!)
kubectl exec -it statefulset/redis-0 -n turkiye-sinav-platform -- \
  redis-cli -a <password> FLUSHDB

# ADIM 3: Cache durumunu kontrol et
kubectl exec -it statefulset/redis-0 -n turkiye-sinav-platform -- \
  redis-cli -a <password> INFO stats
```

### 2. Application Cache Restart

```bash
# In-memory cache'i temizlemek için pod'ları restart et
kubectl rollout restart deployment/turkiye-sinav-app -n turkiye-sinav-platform

# Restart durumunu izle
kubectl rollout status deployment/turkiye-sinav-app -n turkiye-sinav-platform
```

---

## Emergency Procedures

### 1. Acil Durdurma (Emergency Stop)

**Ne zaman kullanılır:** Data corruption, security breach, critical bug

```bash
# ADIM 1: Tüm traffic'i durdur
kubectl scale deployment/turkiye-sinav-app --replicas=0 -n turkiye-sinav-platform

# ADIM 2: LoadBalancer'ı devre dışı bırak
kubectl patch service turkiye-sinav-nginx-service \
  -p '{"spec":{"type":"ClusterIP"}}' \
  -n turkiye-sinav-platform

# ADIM 3: Maintenance page göster
kubectl apply -f k8s/maintenance-page.yaml

# ADIM 4: Team'i bilgilendir
# Slack: #turkiye-sinav-production
# PagerDuty: Incident oluştur
```

### 2. Maintenance Mode

```bash
# ADIM 1: Maintenance ConfigMap oluştur
kubectl create configmap maintenance-mode \
  --from-literal=enabled=true \
  --from-literal=message="Sistem bakımda. 30 dakika içinde geri döneceğiz." \
  -n turkiye-sinav-platform

# ADIM 2: Application'ı maintenance mode'a al
kubectl set env deployment/turkiye-sinav-app \
  MAINTENANCE_MODE=true \
  -n turkiye-sinav-platform

# ADIM 3: Maintenance page deploy et
kubectl apply -f k8s/maintenance-page.yaml
```

### 3. Partial Rollback (Canary)

```bash
# ADIM 1: Canary deployment'ı durdur
kubectl patch canary turkiye-sinav-app \
  -p '{"spec":{"analysis":{"threshold":0}}}' \
  -n turkiye-sinav-platform

# ADIM 2: Tüm traffic'i stable version'a yönlendir
kubectl patch canary turkiye-sinav-app \
  -p '{"spec":{"canaryAnalysis":{"stepWeight":0}}}' \
  -n turkiye-sinav-platform

# ADIM 3: Canary pod'ları sil
kubectl delete pods -l version=canary -n turkiye-sinav-platform
```

---

## Post-Rollback Verification

### 1. Health Check

```bash
# Application health
curl https://api.yourdomain.com/health

# Video API health
curl https://api.yourdomain.com/api/youtube/health

# Database health
kubectl exec -it statefulset/postgres-0 -n turkiye-sinav-platform -- \
  pg_isready -U postgres

# Redis health
kubectl exec -it statefulset/redis-0 -n turkiye-sinav-platform -- \
  redis-cli -a <password> PING
```

### 2. Smoke Tests

```bash
# Video recommendations test
curl -X POST https://api.yourdomain.com/api/youtube/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "goals": ["Matematik TYT"],
    "currentLevel": {"matematik": 50},
    "learningStyle": "visual"
  }'

# Cache test
curl https://api.yourdomain.com/api/youtube/health | jq '.components.cache.hit_rate'

# Database test
curl https://api.yourdomain.com/api/users/me -H "Authorization: Bearer <token>"
```

### 3. Metrics Verification

```bash
# Error rate (should be < 2%)
curl https://api.yourdomain.com/metrics | grep video_errors_total

# Latency (P95 should be < 3s)
curl https://api.yourdomain.com/metrics | grep video_response_time_seconds

# Cache hit rate (should be > 80%)
curl https://api.yourdomain.com/api/youtube/health | jq '.components.cache.hit_rate'
```

### 4. Load Test

```bash
# Hafif load test (10 concurrent users)
cd backend/tests/load
locust -f locustfile.py --host=https://api.yourdomain.com --users=10 --spawn-rate=2 --run-time=5m --headless

# Sonuçları kontrol et:
# - Request success rate > 98%
# - P95 latency < 3s
# - No errors
```

---

## Rollback Checklist

### Pre-Rollback
- [ ] Rollback kararı onaylandı (Tech Lead / CTO)
- [ ] Rollback nedeni dokümante edildi
- [ ] Backup alındı (database, volumes)
- [ ] Team bilgilendirildi (Slack, PagerDuty)
- [ ] Maintenance window planlandı (gerekirse)

### During Rollback
- [ ] Rollback başlatıldı
- [ ] Rollback progress izleniyor
- [ ] Logs kontrol ediliyor
- [ ] Metrics izleniyor
- [ ] Team'e status update veriliyor

### Post-Rollback
- [ ] Health check'ler başarılı
- [ ] Smoke tests başarılı
- [ ] Metrics normal
- [ ] Load test başarılı
- [ ] Incident report oluşturuldu
- [ ] Post-mortem planlandı
- [ ] Team bilgilendirildi (rollback tamamlandı)

---

## Rollback Decision Tree

```
Deployment başarısız mı?
├─ Evet
│  ├─ Error rate > 10%? → IMMEDIATE ROLLBACK (P0)
│  ├─ Health check fail? → IMMEDIATE ROLLBACK (P0)
│  ├─ Pod crash loop? → IMMEDIATE ROLLBACK (P0)
│  ├─ Error rate 5-10%? → EVALUATE & ROLLBACK (P1)
│  ├─ Latency > 5s? → EVALUATE & ROLLBACK (P1)
│  └─ Error rate 2-5%? → MONITOR & DECIDE (P2)
└─ Hayır
   └─ Deployment başarılı, monitoring devam et
```

---

## Contact & Escalation

**Rollback Authority:**
- Tech Lead: +90 XXX XXX XX XX
- DevOps Lead: +90 XXX XXX XX XX
- CTO: +90 XXX XXX XX XX

**Communication Channels:**
- Slack: #turkiye-sinav-production
- PagerDuty: https://turkiye-sinav.pagerduty.com
- Incident Management: https://jira.company.com/incidents

**Escalation Path:**
1. On-Call Engineer (0-5 min)
2. Tech Lead (5-15 min)
3. DevOps Lead (15-30 min)
4. CTO (30+ min)

---

## Rollback Scripts

### Automated Rollback Script

```bash
#!/bin/bash
# rollback.sh - Automated rollback script

set -e

NAMESPACE="turkiye-sinav-platform"
DEPLOYMENT="turkiye-sinav-app"
REVISION="${1:-}"

echo "🔄 Starting rollback process..."

if [ -z "$REVISION" ]; then
  echo "📋 Rolling back to previous revision..."
  kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
else
  echo "📋 Rolling back to revision $REVISION..."
  kubectl rollout undo deployment/$DEPLOYMENT --to-revision=$REVISION -n $NAMESPACE
fi

echo "⏳ Waiting for rollback to complete..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=5m

echo "✅ Rollback completed!"

echo "🔍 Running health checks..."
kubectl exec -it deployment/$DEPLOYMENT -n $NAMESPACE -- curl -f http://localhost:8000/health

echo "✅ Health checks passed!"

echo "📊 Current deployment status:"
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=$DEPLOYMENT

echo "🎉 Rollback successful!"
```

**Kullanım:**
```bash
# Son revision'a rollback
./scripts/rollback.sh

# Belirli revision'a rollback
./scripts/rollback.sh 2
```

---

**Son Güncelleme:** 3 Kasım 2025
**Versiyon:** 1.0.0
**Hazırlayan:** DevOps Team
