# Monitoring Quick Reference Guide
**Teknofest 2025 - Video API Monitoring**

## 🚀 Başlangıç Komutları

```bash
# Monitoring stack'i başlat
./start-monitoring.sh  # Linux/Mac
start-monitoring.bat   # Windows

# Manuel başlatma
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Durumu kontrol et
docker-compose -f docker-compose.monitoring.yml ps

# Logları izle
docker-compose -f docker-compose.monitoring.yml logs -f

# Durdur
docker-compose -f docker-compose.monitoring.yml down

# Durdur ve verileri sil
docker-compose -f docker-compose.monitoring.yml down -v
```

## 📊 Hızlı Erişim URL'leri

| Servis | URL | Credentials |
|--------|-----|-------------|
| Grafana | http://localhost:3000 | admin / teknofest2025 |
| Prometheus | http://localhost:9090 | - |
| Alertmanager | http://localhost:9093 | - |
| Backend Metrics | http://localhost:8000/metrics | - |
| Prometheus Exporter | http://localhost:9091/metrics | - |

## 🔍 Prometheus Queries (PromQL)

### Request Metrics

```promql
# Toplam istek sayısı (son 5 dakika)
sum(rate(video_requests_total[5m]))

# Başarılı istek oranı
sum(rate(video_requests_total{status="success"}[5m])) / sum(rate(video_requests_total[5m])) * 100

# Hata oranı
sum(rate(video_errors_total[5m])) / sum(rate(video_requests_total[5m])) * 100

# Aktif istek sayısı
active_video_requests
```

### Response Time Metrics

```promql
# P50 response time
histogram_quantile(0.50, sum(rate(video_response_time_seconds_bucket[5m])) by (le))

# P95 response time
histogram_quantile(0.95, sum(rate(video_response_time_seconds_bucket[5m])) by (le))

# P99 response time
histogram_quantile(0.99, sum(rate(video_response_time_seconds_bucket[5m])) by (le))

# Ortalama response time
rate(video_response_time_seconds_sum[5m]) / rate(video_response_time_seconds_count[5m])
```

### Cache Metrics

```promql
# Cache hit rate
cache_hit_rate

# Cache boyutu
cache_size_entries

# Cache operations (son 5 dakika)
sum(rate(cache_operations_total[5m])) by (operation)

# Cache hit/miss oranı
sum(rate(cache_operations_total{operation="get"}[5m])) by (operation)
```

### YouTube API Metrics

```promql
# Quota kullanımı
youtube_api_quota_used

# Quota kullanım yüzdesi
(youtube_api_quota_used / youtube_api_quota_limit) * 100

# Kalan quota
youtube_api_quota_limit - youtube_api_quota_used
```

## 🔔 Alert Durumları

### Prometheus'ta Alert'leri Görüntüle

```bash
# Tüm alert'ler
curl http://localhost:9090/api/v1/rules | jq

# Aktif alert'ler
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'
```

### Alertmanager'da Alert'leri Görüntüle

```bash
# Tüm alert'ler
curl http://localhost:9093/api/v1/alerts | jq

# Silence'ları listele
curl http://localhost:9093/api/v1/silences | jq
```

### Alert Silence Oluştur

```bash
# 1 saatlik silence
curl -X POST http://localhost:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {
        "name": "alertname",
        "value": "HighVideoAPIErrorRate",
        "isRegex": false
      }
    ],
    "startsAt": "2025-11-03T10:00:00Z",
    "endsAt": "2025-11-03T11:00:00Z",
    "createdBy": "admin",
    "comment": "Maintenance window"
  }'
```

## 📈 Grafana Shortcuts

| Kısayol | Açıklama |
|---------|----------|
| `d` + `h` | Dashboard home |
| `d` + `s` | Dashboard settings |
| `d` + `k` | Kiosk mode |
| `Ctrl/Cmd + S` | Dashboard kaydet |
| `Ctrl/Cmd + H` | Yardım menüsü |
| `t` + `z` | Zoom out time range |
| `t` + `←` | Time range backward |
| `t` + `→` | Time range forward |

## 🔧 Troubleshooting Commands

### Container Durumunu Kontrol Et

```bash
# Tüm container'ları listele
docker ps -a | grep teknofest

# Belirli bir container'ın loglarını görüntüle
docker logs teknofest-prometheus
docker logs teknofest-grafana
docker logs teknofest-alertmanager

# Container içine gir
docker exec -it teknofest-prometheus sh
docker exec -it teknofest-grafana bash
```

### Prometheus Konfigürasyonunu Test Et

```bash
# Konfigürasyon syntax kontrolü
docker exec teknofest-prometheus promtool check config /etc/prometheus/prometheus.yml

# Alert kurallarını kontrol et
docker exec teknofest-prometheus promtool check rules /etc/prometheus/alerts/*.yml

# Konfigürasyonu reload et (restart gerekmez)
curl -X POST http://localhost:9090/-/reload
```

### Grafana Datasource Test Et

```bash
# Datasource'ları listele
curl -u admin:teknofest2025 http://localhost:3000/api/datasources

# Datasource test et
curl -u admin:teknofest2025 http://localhost:3000/api/datasources/1/health
```

### Metrics Endpoint'lerini Test Et

```bash
# Backend metrics
curl http://localhost:8000/metrics | grep video_

# Prometheus exporter metrics
curl http://localhost:9091/metrics | grep kiro_

# Redis metrics
curl http://localhost:9121/metrics | grep redis_

# Postgres metrics
curl http://localhost:9187/metrics | grep pg_
```

## 📊 Dashboard Customization

### Yeni Panel Ekle

1. Dashboard'u aç
2. Sağ üstten **Add panel** tıkla
3. **Add a new panel** seç
4. Query ekle (PromQL)
5. Visualization type seç (Graph, Stat, Gauge, etc.)
6. Panel ayarlarını düzenle
7. **Apply** tıkla

### Panel Query Örnekleri

```promql
# Request rate by status
sum(rate(video_requests_total[5m])) by (status)

# Error rate percentage
(sum(rate(video_errors_total[5m])) / sum(rate(video_requests_total[5m]))) * 100

# Cache hit rate trend
avg_over_time(cache_hit_rate[1h])

# Top 5 error types
topk(5, sum(rate(video_errors_total[5m])) by (error_type))
```

## 🎯 Performance Tuning

### Prometheus Retention Ayarla

```yaml
# docker-compose.monitoring.yml
command:
  - '--storage.tsdb.retention.time=30d'  # 30 gün
  - '--storage.tsdb.retention.size=10GB'  # veya 10GB
```

### Scrape Interval Optimize Et

```yaml
# prometheus.yml
global:
  scrape_interval: 15s  # Daha az sık scrape
  
scrape_configs:
  - job_name: 'video_api'
    scrape_interval: 10s  # Kritik metrikler için daha sık
```

### Grafana Query Cache

```yaml
# Grafana environment variables
- GF_DATAPROXY_TIMEOUT=60
- GF_DATAPROXY_MAX_IDLE_CONNECTIONS=100
```

## 🔐 Security Best Practices

### Grafana Şifresini Değiştir

```bash
# Docker container içinde
docker exec -it teknofest-grafana grafana-cli admin reset-admin-password newpassword

# Veya environment variable ile
GF_SECURITY_ADMIN_PASSWORD=yeni_sifre
```

### Prometheus Basic Auth Ekle

```yaml
# prometheus.yml
basic_auth:
  username: admin
  password: secure_password
```

### TLS/SSL Ekle

```yaml
# Grafana için
environment:
  - GF_SERVER_PROTOCOL=https
  - GF_SERVER_CERT_FILE=/etc/grafana/ssl/cert.pem
  - GF_SERVER_CERT_KEY=/etc/grafana/ssl/key.pem
```

## 📝 Backup & Restore

### Grafana Dashboard Backup

```bash
# Dashboard export
curl -u admin:teknofest2025 \
  http://localhost:3000/api/dashboards/uid/video-api \
  | jq '.dashboard' > backup_dashboard.json

# Dashboard import
curl -u admin:teknofest2025 \
  -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @backup_dashboard.json
```

### Prometheus Data Backup

```bash
# Snapshot oluştur
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Data directory backup
docker cp teknofest-prometheus:/prometheus ./prometheus-backup
```

## 🆘 Emergency Procedures

### Yüksek Hata Oranı

1. Dashboard'u kontrol et
2. Error type'ları analiz et
3. Backend loglarını incele
4. Gerekirse servisi restart et

```bash
# Backend restart
docker restart teknofest-backend

# Metrics kontrol
curl http://localhost:8000/metrics | grep error
```

### Cache Problemi

1. Cache hit rate'i kontrol et
2. Redis bağlantısını test et
3. Cache size'ı kontrol et

```bash
# Redis kontrol
docker exec -it teknofest-redis redis-cli ping

# Cache metrics
curl http://localhost:8000/metrics | grep cache
```

### Quota Aşımı

1. YouTube API quota'yı kontrol et
2. Cache kullanımını artır
3. Rate limiting ayarla

```bash
# Quota metrics
curl http://localhost:8000/metrics | grep youtube_api_quota
```

---

**Son Güncelleme**: 3 Kasım 2025
**Versiyon**: 1.0.0
