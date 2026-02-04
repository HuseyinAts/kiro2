# Video Recommendation Monitoring System

## Genel Bakış

Video öneri sistemi için kapsamlı monitoring ve logging altyapısı. Video filtreleme, validation ve performance metriklerini toplar, loglar ve raporlar.

## Özellikler

### 1. Video Filtreleme Metrikleri

- **İşlenen Video Sayısı**: Toplam işlenen video sayısı
- **Filtre Geçiş Oranları**: Her filtre için geçiş/başarısızlık oranları
  - Türkçe filtresi
  - Konu uygunluğu filtresi
  - Erişilebilirlik filtresi
  - Kalite filtresi
- **Ortalama Skorlar**: Her filtre için ortalama skorlar
- **Skor Dağılımları**: Skorların dağılımı (0.0-0.3, 0.3-0.5, 0.5-0.7, 0.7-0.9, 0.9-1.0)

### 2. Validation Başarısızlıkları

- **Başarısızlık Tipleri**: Hangi filtrelerde başarısız olundu
  - `turkish_filter_failed`: Türkçe skoru yetersiz
  - `relevance_too_low`: Konu uygunluğu düşük
  - `accessibility_failed`: Video erişilemiyor
  - `quality_too_low`: Kalite skoru düşük
- **Detaylı Kayıtlar**: Her başarısızlık için video ID, başlık, zaman damgası ve detaylar
- **Son Başarısızlıklar**: En son 10 validation başarısızlığı

### 3. Performance Metrikleri

- **Request Metrikleri**:
  - Toplam request sayısı
  - Başarılı/başarısız request sayısı
  - Başarı oranı
- **Cache Metrikleri**:
  - Cache hit/miss sayısı
  - Cache hit oranı
- **Timing Metrikleri**:
  - Ortalama işlem süresi
  - Min/max işlem süresi
  - Timing dağılımı (<1s, 1-2s, 2-3s, 3-5s, >5s)
- **YouTube API Metrikleri**:
  - Toplam API çağrısı
  - API hataları
  - Quota aşımı sayısı
  - Rate limit sayısı
- **Timeout Sayısı**: Timeout olan operasyon sayısı

### 4. Hata Metrikleri

- **Toplam Hata Sayısı**: Sistemdeki toplam hata sayısı
- **Hata Oranı**: Hata/request oranı
- **Hata Tipleri**: Hata tiplerine göre gruplandırılmış sayılar
- **Son Hatalar**: En son 10 hata kaydı

## Kullanım

### Python Kodu İçinde

```python
from backend.services.video_recommendation_monitoring import (
    get_video_recommendation_monitor
)

# Monitor instance'ını al
monitor = get_video_recommendation_monitor()

# Video işleme logla
monitor.log_video_processed(
    video_id="abc123",
    video_title="Matematik Türev Konu Anlatımı",
    turkish_score=0.85,
    relevance_score=0.75,
    quality_score=0.65,
    final_score=0.75,
    passed_filters=True
)

# Filtre sonucu logla
monitor.log_filter_result(
    filter_type="turkish",
    passed=True,
    score=0.85,
    threshold=0.7
)

# Validation başarısızlığı logla
monitor.log_validation_failure(
    video_id="xyz789",
    failure_type="relevance_too_low",
    details={"score": 0.45, "threshold": 0.6},
    video_title="İngilizce Video"
)

# Request lifecycle logla
start_time = monitor.log_request_start()
# ... işlemler ...
monitor.log_request_end(
    start_time=start_time,
    success=True,
    cache_hit=False,
    video_count=10
)

# YouTube API çağrısı logla
monitor.log_youtube_api_call(success=True)
monitor.log_youtube_quota_exceeded()
monitor.log_youtube_rate_limit()

# Hata logla
monitor.log_error(
    error_type="ValueError",
    error_message="Invalid subject parameter",
    context={"subject": "invalid_subject"}
)

# İstatistikleri al
filter_stats = monitor.get_filter_stats()
performance_stats = monitor.get_performance_stats()
error_stats = monitor.get_error_stats()
comprehensive_report = monitor.get_comprehensive_report()

# Rapor logla
monitor.log_comprehensive_report()

# Metrikleri sıfırla
monitor.reset_metrics()
```

### API Endpoints

#### 1. Kapsamlı İstatistikler

```bash
GET /api/monitoring/video-recommendations/stats
```

Tüm monitoring metriklerini döndürür.

**Response:**
```json
{
  "success": true,
  "data": {
    "monitoring_info": {
      "start_time": "2025-01-18T10:00:00",
      "uptime_seconds": 3600,
      "uptime_hours": 1.0
    },
    "filter_stats": {
      "total_videos_processed": 150,
      "filters": {
        "turkish": {
          "passed": 120,
          "failed": 30,
          "pass_rate": 0.8
        },
        ...
      },
      "average_scores": {
        "turkish": 0.82,
        "relevance": 0.75,
        "quality": 0.68,
        "final": 0.76
      }
    },
    "performance_stats": {...},
    "error_stats": {...}
  }
}
```

#### 2. Filtre İstatistikleri

```bash
GET /api/monitoring/video-recommendations/filter-stats
```

Sadece filtre metriklerini döndürür.

#### 3. Validation Başarısızlıkları

```bash
GET /api/monitoring/video-recommendations/validation-failures
```

Validation başarısızlıklarını döndürür.

#### 4. Performance İstatistikleri

```bash
GET /api/monitoring/video-recommendations/performance
```

Performance metriklerini döndürür.

#### 5. Hata İstatistikleri

```bash
GET /api/monitoring/video-recommendations/errors
```

Hata metriklerini döndürür.

#### 6. Sistem Sağlık Durumu

```bash
GET /api/monitoring/video-recommendations/health
```

Sistem sağlık durumunu kontrol eder.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",  // "healthy", "degraded"
    "total_requests": 100,
    "success_rate": 0.95,
    "error_rate": 0.05,
    "avg_processing_time": 2.5,
    "cache_hit_rate": 0.7,
    "issues": []
  }
}
```

**Sağlık Durumu Kriterleri:**
- `healthy`: Tüm metrikler normal
- `degraded`: Aşağıdaki durumlardan biri varsa:
  - Başarı oranı < %90
  - Hata oranı > %10
  - Ortalama işlem süresi > 5 saniye
  - YouTube API quota aşıldı

#### 7. Metrikleri Sıfırla

```bash
POST /api/monitoring/video-recommendations/reset-metrics
```

Tüm monitoring metriklerini sıfırlar.

## Entegrasyon

### Enhanced Resource Recommendation Engine

Monitoring sistemi otomatik olarak `EnhancedResourceRecommendationEngine` ile entegre edilmiştir:

```python
from backend.services.enhanced_resource_recommendation_engine import (
    get_enhanced_recommendation_engine
)

engine = await get_enhanced_recommendation_engine()

# Monitoring otomatik olarak çalışır
videos = await engine.get_recommended_videos(
    subject="matematik",
    topic="türev",
    difficulty="orta",
    max_results=10
)

# Monitoring istatistiklerini al
stats = engine.get_monitoring_stats()

# Monitoring raporu logla
engine.log_monitoring_report()
```

## Log Formatı

### Video İşleme

```
INFO: Video processed: Matematik Türev Konu Anlatımı... (T:0.85, R:0.75, Q:0.65, F:0.75) - PASSED
DEBUG: Video filtered: İngilizce Video... (T:0.45, R:0.60, Q:0.50)
```

### Filtre Sonuçları

```
DEBUG: TURKISH filter: PASSED (score: 0.85, threshold: 0.70)
DEBUG: RELEVANCE filter: FAILED (score: 0.55, threshold: 0.60)
```

### Validation Başarısızlıkları

```
WARNING: Validation failure: turkish_filter_failed for video abc123 (Test Video...) - {'score': 0.5, 'threshold': 0.7}
```

### Request Lifecycle

```
INFO: Request completed: SUCCESS - CACHE_MISS - 2.35s - 10 videos
INFO: Request completed: SUCCESS - CACHE_HIT - 0.05s - 10 videos
```

### YouTube API

```
ERROR: YouTube API quota exceeded
WARNING: YouTube API rate limit hit
```

### Hatalar

```
ERROR: Error: ValueError - Invalid subject parameter (context: {'subject': 'invalid_subject'})
```

### Kapsamlı Rapor

```
================================================================================
VIDEO RECOMMENDATION MONITORING REPORT
================================================================================
Uptime: 2.50 hours

Total videos processed: 250
Filter pass rates:
  Turkish: 85.0% (213/250)
  Relevance: 78.0% (195/250)
  Accessibility: 92.0% (230/250)
  Quality: 88.0% (220/250)

Average scores:
  Turkish: 0.820
  Relevance: 0.750
  Quality: 0.680
  Final: 0.750

Total requests: 50
Success rate: 96.0%
Cache hit rate: 65.0%
Avg processing time: 2.45s

YouTube API calls: 25
YouTube API errors: 1
Quota exceeded: 0
Rate limits: 0

Total errors: 2
Error rate: 4.00%
================================================================================
```

## Metrik Limitleri

- **Validation Failures**: Son 1000 başarısızlık saklanır
- **Recent Errors**: Son 100 hata saklanır
- **Score Distributions**: 5 bucket (0.0-0.3, 0.3-0.5, 0.5-0.7, 0.7-0.9, 0.9-1.0)
- **Timing Distribution**: 5 bucket (<1s, 1-2s, 2-3s, 3-5s, >5s)

## Thread Safety

Tüm monitoring operasyonları thread-safe'tir. `threading.Lock` kullanılarak concurrent access korunur.

## Best Practices

1. **Düzenli Raporlama**: Belirli aralıklarla (örn. her saat) `log_comprehensive_report()` çağırın
2. **Metrik Sıfırlama**: Uzun süreli çalışmalarda periyodik olarak metrikleri sıfırlayın
3. **Sağlık Kontrolü**: Health endpoint'ini monitoring sistemlerine entegre edin
4. **Hata Takibi**: Yüksek hata oranlarında alarm oluşturun
5. **Performance İzleme**: Ortalama işlem süresini takip edin (hedef: <5s)
6. **Cache Optimizasyonu**: Cache hit rate'i izleyin (hedef: >60%)

## Örnek Dashboard Metrikleri

Monitoring dashboard'u için önerilen metrikler:

1. **Ana Metrikler**:
   - Toplam request sayısı
   - Başarı oranı
   - Ortalama işlem süresi
   - Cache hit rate

2. **Filtre Metrikleri**:
   - Her filtre için geçiş oranı
   - Ortalama skorlar
   - Skor dağılımları (grafik)

3. **Hata Metrikleri**:
   - Toplam hata sayısı
   - Hata oranı
   - Hata tipleri (pie chart)
   - Son hatalar (tablo)

4. **YouTube API Metrikleri**:
   - API çağrı sayısı
   - API hata oranı
   - Quota durumu
   - Rate limit sayısı

5. **Validation Metrikleri**:
   - Başarısızlık tipleri (bar chart)
   - Son başarısızlıklar (tablo)

## Troubleshooting

### Yüksek Hata Oranı

```python
# Hata detaylarını incele
error_stats = monitor.get_error_stats()
print(error_stats['errors_by_type'])
print(error_stats['recent_errors'])
```

### Düşük Filtre Geçiş Oranı

```python
# Filtre istatistiklerini incele
filter_stats = monitor.get_filter_stats()
for filter_name, stats in filter_stats['filters'].items():
    if stats['pass_rate'] < 0.5:
        print(f"Low pass rate for {filter_name}: {stats['pass_rate']:.1%}")
```

### Yavaş İşlem Süresi

```python
# Timing dağılımını incele
perf_stats = monitor.get_performance_stats()
timing_dist = perf_stats['timing']['distribution']
slow_requests = timing_dist['>5s']
print(f"Slow requests (>5s): {slow_requests}")
```

### YouTube API Sorunları

```python
# YouTube API metriklerini incele
perf_stats = monitor.get_performance_stats()
youtube_stats = perf_stats['youtube_api']
if youtube_stats['quota_exceeded'] > 0:
    print("YouTube API quota exceeded!")
if youtube_stats['error_rate'] > 0.1:
    print(f"High YouTube API error rate: {youtube_stats['error_rate']:.1%}")
```

## Geliştirme

### Yeni Metrik Ekleme

1. İlgili dataclass'a yeni field ekle (`FilterMetrics`, `PerformanceMetrics`, vb.)
2. `VideoRecommendationMonitor` class'ına log metodu ekle
3. İlgili `get_*_stats()` metodunu güncelle
4. Test ekle

### Yeni Filtre Tipi Ekleme

```python
# log_filter_result metodunu güncelle
def log_filter_result(self, filter_type: str, passed: bool, ...):
    with self._lock:
        if filter_type == "new_filter":
            if passed:
                self.filter_metrics.new_filter_passed += 1
            else:
                self.filter_metrics.new_filter_failed += 1
        # ...
```

## Lisans

Teknofest 2025 - Eğitim Eylemci Projesi
