# Rollback Plan - Learning Path Video Fix

## Overview

Bu doküman, production deployment'ı geri almak için adım adım rollback planını içerir.

## Rollback Senaryoları

### Senaryo 1: Deployment Başarısız (Pods Başlamıyor)

**Belirtiler:**
- Pods `CrashLoopBackOff` durumunda
- Health check başarısız
- Logs'ta kritik hatalar

**Rollback Adımları:**

```bash
# 1. Mevcut durumu kontrol et
kubectl get pods -n production -l app=video-api

# 2. Logs'u incele
kubectl logs -n production deployment/video-api --tail=100

# 3. Önceki versiyona geri dön
kubectl rollout undo deployment/video-api -n production

# 4. Rollback durumunu izle
kubectl rollout status deployment/video-api -n production

# 5. Pods'ların sağlıklı olduğunu doğrula
kubectl get pods -n production -l app=video-api
```

**Beklenen Süre:** 2-3 dakika

---

### Senaryo 2: Yüksek Hata Oranı (Production'da Çalışıyor Ama Hatalar Var)

**Belirtiler:**
- Prometheus alert: `HighErrorRate`
- Grafana dashboard'da error spike
- Kullanıcı şikayetleri

**Rollback Adımları:**

```bash
# 1. Hata oranını kontrol et
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
# Prometheus'ta query: rate(video_requests_total{status="error"}[5m])

# 2. Logs'ta hata detaylarını incele
kubectl logs -n production deployment/video-api --tail=500 | grep ERROR

# 3. Eğer kritik ise, hemen rollback yap
kubectl rollout undo deployment/video-api -n production

# 4. Rollback sonrası hata oranını izle
# Prometheus'ta aynı query'yi tekrar çalıştır

# 5. Grafana dashboard'u kontrol et
# http://localhost:3000/d/video-api-dashboard
```

**Beklenen Süre:** 3-5 dakika

---

### Senaryo 3: Yavaş Yanıt Süresi (Performance Degradation)

**Belirtiler:**
- Prometheus alert: `SlowResponseTime`
- P95 response time > 5 saniye
- Kullanıcılar timeout alıyor

**Rollback Adımları:**

```bash
# 1. Response time metriklerini kontrol et
# Prometheus query: histogram_quantile(0.95, video_response_time_seconds)

# 2. Resource kullanımını kontrol et
kubectl top pods -n production -l app=video-api

# 3. Eğer resource limit'e ulaşılmışsa, scale up dene
kubectl scale deployment/video-api -n production --replicas=5

# 4. 5 dakika bekle ve tekrar kontrol et

# 5. Eğer sorun devam ederse, rollback yap
kubectl rollout undo deployment/video-api -n production

# 6. Rollback sonrası performance'ı izle
```

**Beklenen Süre:** 5-10 dakika

---

### Senaryo 4: Cache Sorunları (Düşük Cache Hit Rate)

**Belirtiler:**
- Prometheus alert: `LowCacheHitRate`
- Cache hit rate < 60%
- Yüksek YouTube API kullanımı

**Rollback Adımları:**

```bash
# 1. Cache metriklerini kontrol et
# Prometheus query: cache_hit_rate

# 2. Redis durumunu kontrol et
kubectl get pods -n production -l app=redis

# 3. Redis logs'unu incele
kubectl logs -n production deployment/redis --tail=100

# 4. Eğer Redis down ise, restart et
kubectl rollout restart deployment/redis -n production

# 5. Eğer sorun devam ederse, video-api'yi rollback yap
kubectl rollout undo deployment/video-api -n production

# 6. Cache'i temizle ve yeniden başlat
kubectl exec -n production deployment/redis -- redis-cli FLUSHALL
```

**Beklenen Süre:** 5-10 dakika

---

### Senaryo 5: YouTube API Quota Aşımı

**Belirtiler:**
- Prometheus alert: `YouTubeQuotaLow`
- Logs'ta "quota exceeded" hataları
- Videolar yüklenmiyor

**Rollback Adımları:**

```bash
# 1. Quota durumunu kontrol et
# Prometheus query: youtube_api_quota_remaining

# 2. Eğer quota bitmişse, cache-only mode'a geç
kubectl set env deployment/video-api -n production \
    YOUTUBE_API_ENABLED=false

# 3. Cache hit rate'i izle
# Prometheus query: cache_hit_rate

# 4. Eğer cache yeterli değilse, rollback yap
kubectl rollout undo deployment/video-api -n production

# 5. Ertesi gün quota reset olduğunda, tekrar enable et
kubectl set env deployment/video-api -n production \
    YOUTUBE_API_ENABLED=true
```

**Beklenen Süre:** Anında (environment variable değişikliği)

---

## Otomatik Rollback

Deployment script'i otomatik rollback içerir:

```bash
# Otomatik rollback şartları:
# 1. Health check başarısız (5 deneme sonrası)
# 2. Smoke tests başarısız
# 3. Rollout timeout (5 dakika)

# Otomatik rollback'i devre dışı bırakmak için:
ROLLBACK_ENABLED=false ./deployment/production_deploy.sh
```

---

## Manuel Rollback

### Belirli Bir Revision'a Geri Dönme

```bash
# 1. Revision history'yi listele
kubectl rollout history deployment/video-api -n production

# 2. Belirli bir revision'ın detaylarını gör
kubectl rollout history deployment/video-api -n production --revision=3

# 3. Belirli bir revision'a geri dön
kubectl rollout undo deployment/video-api -n production --to-revision=3

# 4. Rollback durumunu izle
kubectl rollout status deployment/video-api -n production
```

### Backup'tan Restore Etme

```bash
# 1. Backup dosyasını bul
ls -lh ./deployment/backups/

# 2. Backup'ı uygula
kubectl apply -f ./deployment/backups/deployment-backup-20250102-143000.yaml

# 3. Pods'ların başladığını doğrula
kubectl get pods -n production -l app=video-api
```

---

## Rollback Sonrası Doğrulama

### 1. Health Check

```bash
# Health endpoint'i test et
kubectl port-forward -n production deployment/video-api 8000:8000 &
curl http://localhost:8000/api/youtube/health

# Beklenen response:
# {
#   "status": "healthy",
#   "components": [...],
#   "timestamp": "..."
# }
```

### 2. Smoke Tests

```bash
# Smoke tests'i çalıştır
API_BASE_URL=http://localhost:8000 ./deployment/smoke_tests.sh

# Tüm testler geçmeli
```

### 3. Metrics Kontrolü

```bash
# Prometheus'ta kontrol edilecek metrikler:
# - video_requests_total (request rate normal mi?)
# - video_response_time_seconds (response time düzeldi mi?)
# - cache_hit_rate (cache çalışıyor mu?)
# - error_rate (hata oranı düştü mü?)
```

### 4. Logs İncelemesi

```bash
# Son 100 log satırını incele
kubectl logs -n production deployment/video-api --tail=100

# Hata loglarını filtrele
kubectl logs -n production deployment/video-api --tail=500 | grep ERROR

# Belirli bir request ID'yi takip et
kubectl logs -n production deployment/video-api --tail=1000 | grep "request_id=abc123"
```

---

## Rollback Checklist

- [ ] Rollback nedeni dokümante edildi
- [ ] Rollback komutu çalıştırıldı
- [ ] Rollback durumu izlendi (kubectl rollout status)
- [ ] Pods sağlıklı durumda (kubectl get pods)
- [ ] Health check başarılı
- [ ] Smoke tests geçti
- [ ] Metrics normal seviyede
- [ ] Logs'ta kritik hata yok
- [ ] Kullanıcı şikayetleri azaldı
- [ ] Incident raporu oluşturuldu
- [ ] Post-mortem toplantısı planlandı

---

## İletişim

### Rollback Sırasında Bilgilendirilecek Kişiler

1. **Development Team Lead**
   - Email: dev-lead@example.com
   - Slack: @dev-lead

2. **DevOps Team**
   - Email: devops@example.com
   - Slack: #devops-alerts

3. **Product Manager**
   - Email: pm@example.com
   - Slack: @product-manager

4. **Customer Support**
   - Email: support@example.com
   - Slack: #customer-support

### Rollback Bildirimi Template

```
🚨 PRODUCTION ROLLBACK ALERT 🚨

Service: Video API (Learning Path)
Environment: Production
Timestamp: [YYYY-MM-DD HH:MM:SS]
Reason: [Kısa açıklama]
Rollback Status: [In Progress / Completed]
Impact: [Kullanıcı etkisi]
ETA: [Tahmini çözüm süresi]

Actions Taken:
- [Adım 1]
- [Adım 2]

Next Steps:
- [Sonraki adım 1]
- [Sonraki adım 2]

Incident Commander: [İsim]
```

---

## Post-Rollback Actions

### 1. Root Cause Analysis

```markdown
# Incident Report Template

## Incident Summary
- Date/Time: 
- Duration: 
- Impact: 
- Severity: 

## Timeline
- [HH:MM] Deployment started
- [HH:MM] Issue detected
- [HH:MM] Rollback initiated
- [HH:MM] Service restored

## Root Cause
[Detaylı açıklama]

## Resolution
[Nasıl çözüldü]

## Prevention
[Gelecekte nasıl önlenebilir]

## Action Items
- [ ] Action 1 (Owner: X, Due: Y)
- [ ] Action 2 (Owner: X, Due: Y)
```

### 2. Monitoring İyileştirmeleri

- Yeni alert kuralları ekle
- Dashboard'ları güncelle
- Log aggregation iyileştir

### 3. Testing İyileştirmeleri

- Eksik test case'leri ekle
- Load test senaryolarını güncelle
- Smoke test coverage artır

---

## Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| On-Call Engineer | [Name] | [Phone] | [Email] |
| DevOps Lead | [Name] | [Phone] | [Email] |
| CTO | [Name] | [Phone] | [Email] |

---

## Rollback SLA

- **Detection Time:** < 5 dakika (monitoring alerts)
- **Decision Time:** < 10 dakika (incident commander)
- **Rollback Execution:** < 5 dakika (automated)
- **Verification Time:** < 10 dakika (smoke tests)
- **Total MTTR:** < 30 dakika

---

## Lessons Learned

Her rollback sonrası:

1. **Post-mortem meeting** düzenle (24 saat içinde)
2. **Incident report** yaz ve paylaş
3. **Action items** belirle ve takip et
4. **Runbook** güncelle
5. **Team** ile bilgi paylaş

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-02 | DevOps Team | Initial version |
