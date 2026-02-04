# Video API Monitoring ve Alerting Kurulum Rehberi

## Genel Bakış

Learning Path Video Yükleme sistemi için kapsamlı monitoring ve alerting altyapısı. Bu doküman, Prometheus, Grafana ve Alertmanager kullanarak video API'sinin izlenmesi ve sorunların otomatik tespiti için gerekli kurulum adımlarını içerir.

**Task:** 19 - Monitoring ve Alerting Kur  
**Requirements:** 4.5, 4.11, 5.4, 5.12

## Bileşenler

### 1. Prometheus Metrics
- **Dosya:** `backend/monitoring/prometheus_exporter.py`
- **Port:** 9091
- **Metrikler:**
  - Video API request rate, response time, error rate
  - Cache hit/miss rate
  - Health check status
  - Turkish content filter scores
  - Component health status

### 2. Prometheus Alert Rules
- **Dosya:** `backend/config/prometheus_video_alerts.yml`
- **Alert Grupları:**
  - `video_api_performance`: API performans alertleri
  - `video_cache_performance`: Cache performans alertleri
  - `video_health_checks`: Health check alertleri
  - `video_content_quality`: İçerik kalitesi alertleri
  - `video_system_resources`: Sistem kaynak alertleri
  - `video_user_experience`: Kullanıcı deneyimi alertleri

### 3. Grafana Dashboard
- **Dosya:** `backend/config/grafana_video_dashboard.json`
- **Paneller:**
  - Request rate ve response time grafikleri
  - Error rate ve cache hit rate göstergeleri
  - Component health status
  - Turkish content filter score dağılımı
  - Active alerts tablosu

### 4. Alertmanager
- **Dosya:** `monitoring/alertmanager/alertmanager.yml`
- **Notification Channels:**
  - Slack (#backend-youtube-api, #backend-critical, #backend-health)
  - Email (backend-team@teknofest-egitim.com)

## Kurulum Adımları

### 1. Prometheus Kurulumu

```bash
# Prometheus config dosyasını güncelle
# backend/config/prometheus.yml

scrape_configs:
  - job_name: 'video-api'
    static_configs:
      - targets: ['localhost:9091']
    scrape_interval: 15s
    scrape_timeout: 10s

# Alert rules'u ekle
rule_files:
  - 'prometheus_video_alerts.yml'
```

### 2. Prometheus Exporter'ı Başlat

```bash
# Backend içinde
cd backend

# Prometheus exporter'ı başlat
python -m monitoring.prometheus_exporter

# Veya servis olarak
python -m monitoring.prometheus_exporter --service
```

### 3. Health Check Monitoring'i Başlat

```python
# Backend main.py içinde

from monitoring.health_check_monitor import start_health_monitoring
from services.health_check_service import HealthCheckService

# Startup event
@app.on_event("startup")
async def startup_event():
    # Health check service oluştur
    health_check_service = HealthCheckService(
        youtube_api=youtube_api,
        database=database,
        cache=cache,
        metrics=metrics_collector
    )
    
    # Health check monitoring başlat (30 saniye interval)
    await start_health_monitoring(
        health_check_service=health_check_service,
        check_interval=30
    )
    
    logger.info("Health check monitoring started")
```

### 4. Grafana Dashboard'u İçe Aktar

```bash
# Grafana UI'da:
# 1. Dashboards > Import
# 2. Upload JSON file: backend/config/grafana_video_dashboard.json
# 3. Datasource olarak Prometheus'u seç
# 4. Import'a tıkla
```

### 5. Alertmanager Konfigürasyonu

```bash
# Environment variables ayarla
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export SMTP_USERNAME="alerts@teknofest-egitim.com"
export SMTP_PASSWORD="your-smtp-password"

# Alertmanager'ı başlat
alertmanager --config.file=monitoring/alertmanager/alertmanager.yml
```

## Alert Kuralları

### Kritik Alertler (Immediate Notification)

#### 1. HighVideoAPIErrorRate
- **Koşul:** Error rate > %5 (5 dakika boyunca)
- **Severity:** Critical
- **Açıklama:** Video API'de yüksek hata oranı
- **Aksiyon:** 
  - Backend loglarını kontrol et
  - YouTube API quota'sını kontrol et
  - Database bağlantısını kontrol et

#### 2. VerySlowVideoAPIResponse
- **Koşul:** P95 response time > 10 saniye (2 dakika boyunca)
- **Severity:** Critical
- **Açıklama:** Video API çok yavaş, kullanıcılar timeout alıyor
- **Aksiyon:**
  - Cache hit rate'i kontrol et
  - YouTube API response time'ı kontrol et
  - Database query performance'ı kontrol et

#### 3. VideoAPIServiceUnhealthy
- **Koşul:** Overall health status = 0 (3 dakika boyunca)
- **Severity:** Critical
- **Açıklama:** Video API servisi sağlıksız
- **Aksiyon:**
  - Health check endpoint'ini manuel çağır
  - Component status'lerini kontrol et
  - Servisi restart et

#### 4. VeryLowVideoCacheHitRate
- **Koşul:** Cache hit rate < %40 (5 dakika boyunca)
- **Severity:** Critical
- **Açıklama:** Cache sistemi çalışmıyor
- **Aksiyon:**
  - Redis bağlantısını kontrol et
  - Cache key generation'ı kontrol et
  - Redis memory kullanımını kontrol et

### Warning Alertleri

#### 1. SlowVideoAPIResponse
- **Koşul:** P95 response time > 3 saniye (5 dakika boyunca)
- **Severity:** Warning
- **Açıklama:** Video API hedef süreyi aşıyor
- **Aksiyon:**
  - Performance metriklerini incele
  - Slow query'leri kontrol et
  - Cache stratejisini optimize et

#### 2. LowVideoCacheHitRate
- **Koşul:** Cache hit rate < %60 (10 dakika boyunca)
- **Severity:** Warning
- **Açıklama:** Cache hit rate hedefin altında
- **Aksiyon:**
  - Cache TTL'i kontrol et
  - Cache key distribution'ı analiz et
  - Cache warming stratejisi uygula

#### 3. LowTurkishContentScore
- **Koşul:** Median Turkish score < %70 (10 dakika boyunca)
- **Severity:** Warning
- **Açıklama:** Türkçe içerik filtreleme zayıf
- **Aksiyon:**
  - Video source'ları kontrol et
  - Language detection algoritmasını gözden geçir
  - Trusted channel listesini güncelle

## Grafana Dashboard Kullanımı

### Ana Metrikler

1. **Video API Request Rate**
   - Total requests/sec
   - Success rate (200)
   - Server errors (5xx)
   - Timeouts (504)

2. **Response Time (P50, P95, P99)**
   - Hedef: P95 < 3 saniye
   - Critical threshold: P95 > 10 saniye

3. **Error Rate**
   - Hedef: < %2
   - Warning: > %2
   - Critical: > %5

4. **Cache Hit Rate**
   - Hedef: > %80
   - Warning: < %60
   - Critical: < %40

5. **Overall Health Status**
   - Green: Healthy (1)
   - Red: Unhealthy (0)

### Dashboard Filtreleri

- **Subject:** Matematik, Fizik, Kimya, vb.
- **Learning Style:** Visual-Active, Auditory-Reflective, vb.
- **Time Range:** Last 1h, 6h, 24h, 7d

### Alert Annotations

Dashboard üzerinde firing alert'ler kırmızı çizgi olarak gösterilir. Alert'e tıklayarak detayları görebilirsiniz.

## Troubleshooting

### Problem: Metrics görünmüyor

**Çözüm:**
```bash
# Prometheus exporter çalışıyor mu?
curl http://localhost:9091/metrics

# Prometheus scraping yapıyor mu?
# Prometheus UI > Status > Targets
# video-api job'ı UP olmalı
```

### Problem: Alert'ler firing olmuyor

**Çözüm:**
```bash
# Prometheus alert rules yüklendi mi?
# Prometheus UI > Alerts
# Video API alert'leri görünmeli

# Alertmanager'a alert gidiyor mu?
# Alertmanager UI > Alerts
```

### Problem: Slack notification gelmiyor

**Çözüm:**
```bash
# Slack webhook URL doğru mu?
echo $SLACK_WEBHOOK_URL

# Alertmanager config'i doğru mu?
alertmanager --config.file=monitoring/alertmanager/alertmanager.yml --config.check

# Test notification gönder
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test alert from Alertmanager"}'
```

### Problem: Health check monitoring çalışmıyor

**Çözüm:**
```python
# Health check monitor status'ü kontrol et
from monitoring.health_check_monitor import get_health_monitor

monitor = get_health_monitor()
if monitor:
    status = monitor.get_status()
    print(f"Running: {status['running']}")
    print(f"Last check: {status['last_check_time']}")
    print(f"Consecutive failures: {status['consecutive_failures']}")
```

## Metrik Örnekleri

### Video API Request Rate
```promql
# Total request rate
rate(kiro_api_requests_total{endpoint="/api/youtube/recommendations"}[5m])

# Success rate
rate(kiro_api_requests_total{endpoint="/api/youtube/recommendations", status="200"}[5m])

# Error rate percentage
(rate(kiro_api_requests_total{endpoint="/api/youtube/recommendations", status=~"5.."}[5m]) / rate(kiro_api_requests_total{endpoint="/api/youtube/recommendations"}[5m])) * 100
```

### Response Time Percentiles
```promql
# P50
histogram_quantile(0.50, rate(kiro_api_request_duration_seconds_bucket{endpoint="/api/youtube/recommendations"}[5m]))

# P95
histogram_quantile(0.95, rate(kiro_api_request_duration_seconds_bucket{endpoint="/api/youtube/recommendations"}[5m]))

# P99
histogram_quantile(0.99, rate(kiro_api_request_duration_seconds_bucket{endpoint="/api/youtube/recommendations"}[5m]))
```

### Cache Hit Rate
```promql
(rate(kiro_cache_hits_total{cache_type="video_recommendations"}[10m]) / (rate(kiro_cache_hits_total{cache_type="video_recommendations"}[10m]) + rate(kiro_cache_misses_total{cache_type="video_recommendations"}[10m]))) * 100
```

### Health Check Status
```promql
# Overall health
health_check_overall_status

# Component health
health_check_component_status{component="youtube_api"}
health_check_component_status{component="database"}
health_check_component_status{component="redis_cache"}
```

## Best Practices

### 1. Alert Fatigue'den Kaçının
- Sadece actionable alert'ler tanımlayın
- Threshold'ları gerçekçi ayarlayın
- Alert inhibition rules kullanın

### 2. Runbook'lar Hazırlayın
- Her alert için troubleshooting adımları
- Escalation prosedürü
- Rollback planı

### 3. Dashboard'ları Düzenli Güncelleyin
- Yeni metrikler ekleyin
- Kullanılmayan panelleri kaldırın
- Team feedback'ine göre optimize edin

### 4. Alert Routing'i Optimize Edin
- Critical alert'ler için ayrı channel
- Component-specific routing
- On-call rotation

### 5. Metrics Retention
- Prometheus: 15 gün
- Long-term storage: Thanos/Cortex
- Aggregated metrics: 90 gün

## İlgili Dökümanlar

- [Health Check Service](./HEALTH_CHECK_SERVICE.md)
- [Prometheus Exporter](./PROMETHEUS_EXPORTER.md)
- [Video API Architecture](./VIDEO_API_ARCHITECTURE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING_GUIDE.md)

## Destek

Sorularınız için:
- Slack: #backend-monitoring
- Email: backend-team@teknofest-egitim.com
- On-call: backend-oncall@teknofest-egitim.com
