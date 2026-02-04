# Video API Monitoring Dashboard Setup
**Teknofest 2025 - Eğitim Eylemci Projesi**

Bu doküman Video API için Prometheus + Grafana monitoring altyapısının kurulum ve kullanım kılavuzudur.

## 📊 Genel Bakış

Monitoring stack şu bileşenlerden oluşur:

- **Prometheus**: Metrics toplama ve depolama
- **Grafana**: Metrics görselleştirme ve dashboard
- **Alertmanager**: Alert yönetimi ve bildirimler
- **Node Exporter**: Sistem metrikleri
- **Redis Exporter**: Cache metrikleri
- **Postgres Exporter**: Database metrikleri

## 🚀 Hızlı Başlangıç

### 1. Monitoring Stack'i Başlat

```bash
# Monitoring dizinine git
cd monitoring

# Docker Compose ile başlat
docker-compose -f docker-compose.monitoring.yml up -d

# Logları kontrol et
docker-compose -f docker-compose.monitoring.yml logs -f
```

### 2. Servislere Erişim

- **Grafana**: http://localhost:3000
  - Kullanıcı: `admin`
  - Şifre: `teknofest2025`
  
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 3. Dashboard'u Aç

1. Grafana'ya giriş yap
2. Sol menüden **Dashboards** → **Browse** seç
3. **Video API** klasörünü aç
4. **Video API Monitoring Dashboard** seçeneğini tıkla

## 📈 Dashboard Panelleri

### Request Metrics
- **Video API Request Rate**: Saniye başına istek sayısı (success/error)
- **Response Time (P50, P95, P99)**: Yanıt süresi percentile'ları
- **Active Requests**: Anlık aktif istek sayısı
- **Total Requests (24h)**: Son 24 saatteki toplam istek

### Cache Metrics
- **Cache Hit Rate**: Cache isabet oranı (hedef: >%80)
- **Cache Size**: Cache'deki entry sayısı
- **Cache Operations**: Cache operasyon hızı (get/set/delete)

### Performance Metrics
- **Success Rate**: Başarılı istek oranı (hedef: >%99)
- **Error Rate**: Hata oranı ve tipleri
- **Avg Response Time (1h)**: Son 1 saatin ortalama yanıt süresi

### YouTube API Metrics
- **YouTube API Quota Usage**: Günlük quota kullanımı (gauge)

## 🔔 Alert Kuralları

### Video API Alerts

#### HighVideoAPIErrorRate (Critical)
- **Koşul**: Hata oranı >%5
- **Süre**: 5 dakika
- **Aksiyon**: Acil müdahale gerekli

#### SlowVideoAPIResponse (Warning)
- **Koşul**: P95 yanıt süresi >3 saniye
- **Süre**: 10 dakika
- **Aksiyon**: Performance optimization

#### VerySlowVideoAPIResponse (Critical)
- **Koşul**: P95 yanıt süresi >10 saniye
- **Süre**: 5 dakika
- **Aksiyon**: Acil müdahale gerekli

#### YouTubeAPIQuotaWarning (Warning)
- **Koşul**: Quota kullanımı >%80
- **Aksiyon**: Cache kullanımını artır

#### YouTubeAPIQuotaCritical (Critical)
- **Koşul**: Quota kullanımı >%95
- **Aksiyon**: Acil önlem gerekli

### Cache Alerts

#### LowCacheHitRate (Warning)
- **Koşul**: Cache hit rate <%60
- **Süre**: 15 dakika
- **Aksiyon**: Cache stratejisini gözden geçir

#### VeryLowCacheHitRate (Critical)
- **Koşul**: Cache hit rate <%40
- **Süre**: 10 dakika
- **Aksiyon**: Cache sistemi kontrol et

#### CacheFull (Critical)
- **Koşul**: Cache size ≥10,000 entries
- **Aksiyon**: Eviction policy kontrol et

### Health Check Alerts

#### VideoAPIServiceDown (Critical)
- **Koşul**: Service 2 dakikadır yanıt vermiyor
- **Aksiyon**: Acil müdahale gerekli

#### DatabaseConnectionIssues (Critical)
- **Koşul**: Database bağlantısı yok
- **Aksiyon**: Database kontrol et

#### HighMemoryUsage (Warning)
- **Koşul**: Memory kullanımı >%85
- **Aksiyon**: Memory leak kontrol et

## 🔧 Konfigürasyon

### Prometheus Konfigürasyonu

Prometheus konfigürasyonu `prometheus/prometheus.yml` dosyasında:

```yaml
scrape_configs:
  - job_name: 'video_api'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Alert Konfigürasyonu

Alert kuralları `prometheus/alerts/` dizininde:
- `video_api_alerts.yml`: Video API alert kuralları
- `cache_alerts.yml`: Cache alert kuralları
- `health_alerts.yml`: Health check alert kuralları

### Alertmanager Konfigürasyonu

Alertmanager konfigürasyonu `alertmanager/alertmanager.yml` dosyasında.

**Slack Entegrasyonu için:**

```bash
# .env dosyasına ekle
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Email Entegrasyonu için:**

```bash
# .env dosyasına ekle
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 📊 Metrics Endpoint'leri

### Backend Metrics
```bash
# Video API metrics
curl http://localhost:8000/metrics

# Örnek metrikler:
# - video_requests_total
# - video_response_time_seconds
# - cache_hit_rate
# - youtube_api_quota_used
# - video_errors_total
# - active_video_requests
```

### Prometheus Exporter Metrics
```bash
# Custom platform metrics
curl http://localhost:9091/metrics

# Örnek metrikler:
# - kiro_video_recommendations_total
# - kiro_learning_style_detections_total
# - kiro_api_requests_total
```

## 🔍 Troubleshooting

### Prometheus Hedeflere Ulaşamıyor

```bash
# Prometheus targets kontrol et
curl http://localhost:9090/api/v1/targets

# Backend servisinin çalıştığını kontrol et
curl http://localhost:8000/metrics

# Network bağlantısını kontrol et
docker network inspect teknofest_backend
```

### Grafana Dashboard Görünmüyor

```bash
# Grafana loglarını kontrol et
docker logs teknofest-grafana

# Dashboard provisioning kontrol et
docker exec teknofest-grafana ls -la /etc/grafana/provisioning/dashboards

# Datasource kontrol et
curl -u admin:teknofest2025 http://localhost:3000/api/datasources
```

### Alert'ler Çalışmıyor

```bash
# Alertmanager durumunu kontrol et
curl http://localhost:9093/api/v1/status

# Alert kurallarını kontrol et
curl http://localhost:9090/api/v1/rules

# Alertmanager loglarını kontrol et
docker logs teknofest-alertmanager
```

## 📝 Best Practices

### 1. Alert Fatigue'den Kaçının
- Sadece actionable alert'ler tanımlayın
- Threshold'ları gerçekçi belirleyin
- Alert'leri severity'ye göre gruplandırın

### 2. Dashboard Organizasyonu
- İlgili metrikleri gruplandırın
- Önemli metrikleri üstte gösterin
- Time range'i ihtiyaca göre ayarlayın

### 3. Retention Policy
- Prometheus: 30 gün (disk alanına göre ayarlayın)
- Grafana: Snapshot'lar alın
- Alertmanager: Resolved alert'leri temizleyin

### 4. Performance Optimization
- Scrape interval'ı optimize edin
- Gereksiz metrikleri disable edin
- Query'leri optimize edin

## 🔐 Güvenlik

### Production Deployment için:

1. **Grafana şifresini değiştirin:**
```yaml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
```

2. **Prometheus'u koruyun:**
```yaml
command:
  - '--web.enable-admin-api=false'
  - '--web.enable-lifecycle=false'
```

3. **Network izolasyonu:**
```yaml
networks:
  monitoring:
    internal: true  # External erişimi kapat
```

4. **TLS/SSL ekleyin:**
```yaml
environment:
  - GF_SERVER_PROTOCOL=https
  - GF_SERVER_CERT_FILE=/etc/grafana/ssl/cert.pem
  - GF_SERVER_CERT_KEY=/etc/grafana/ssl/key.pem
```

## 📚 Ek Kaynaklar

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)

## 🆘 Destek

Sorun yaşarsanız:
1. Logları kontrol edin
2. Troubleshooting bölümüne bakın
3. GitHub Issues'da sorun açın
4. DevOps ekibine ulaşın: devops@teknofest.com

---

**Son Güncelleme**: 3 Kasım 2025
**Versiyon**: 1.0.0
**Gereksinimler**: Requirements 4.14, 5.15
