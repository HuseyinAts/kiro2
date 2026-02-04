# Video API Load Testing

Bu dizin, Video API için Locust tabanlı yük testlerini içerir.

## Gereksinimler

```bash
pip install locust
```

## Test Dosyaları

### 1. `load_test_video_api.py`
Video öneri API'si için özel yük testi (Requirement 11.3)

**Test Senaryoları:**
- `VideoAPIUser`: Normal kullanıcı davranışı (100 concurrent user)
  - Video önerileri alma (ana senaryo)
  - Retry logic ile video önerileri
  - Health check
  - API connectivity test
  - Farklı profiller ile cache test
  
- `VideoAPIStressUser`: Stress test senaryosu
  - Hızlı ardışık istekler (rate limiting testi)

**Kapsanan Requirements:**
- Requirement 11.3: 100 concurrent user load test
- Requirement 2.1: P95 response time < 3000ms
- Requirement 4.2: Health check < 500ms
- Requirement 7.1, 7.2: Rate limiting

### 2. `locustfile.py`
Genel platform yük testi (tüm API'ler)

### 3. `test_100k_concurrent_users.py`
100K+ kullanıcı simülasyonu (extrapolation ile)

## Kullanım

### Web UI ile (Önerilen)

```bash
# Video API load test
locust -f backend/tests/load/load_test_video_api.py --host http://localhost:8000

# Tarayıcıda http://localhost:8089 adresini açın
# Kullanıcı sayısı: 100
# Spawn rate: 10 (saniyede 10 kullanıcı ekle)
```

### Headless Mode (CI/CD için)

```bash
# 100 kullanıcı, 5 dakika süre
locust -f backend/tests/load/load_test_video_api.py \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --host http://localhost:8000 \
  --headless

# Sonuçları CSV'ye kaydet
locust -f backend/tests/load/load_test_video_api.py \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --host http://localhost:8000 \
  --headless \
  --csv=results/video_api_load_test
```

### Farklı Yük Seviyeleri

```bash
# Düşük yük (10 kullanıcı)
locust -f backend/tests/load/load_test_video_api.py --users 10 --spawn-rate 2 --host http://localhost:8000

# Orta yük (50 kullanıcı)
locust -f backend/tests/load/load_test_video_api.py --users 50 --spawn-rate 5 --host http://localhost:8000

# Yüksek yük (100 kullanıcı) - Requirement 11.3
locust -f backend/tests/load/load_test_video_api.py --users 100 --spawn-rate 10 --host http://localhost:8000

# Stress test (200 kullanıcı)
locust -f backend/tests/load/load_test_video_api.py --users 200 --spawn-rate 20 --host http://localhost:8000
```

### Distributed Load Testing (Çok Makine)

Master node:
```bash
locust -f backend/tests/load/load_test_video_api.py --master --host http://localhost:8000
```

Worker nodes (her makinede):
```bash
locust -f backend/tests/load/load_test_video_api.py --worker --master-host=<master-ip>
```

## Test Metrikleri

Load test sonunda aşağıdaki metrikler raporlanır:

### Temel Metrikler
- **Total Requests**: Toplam istek sayısı
- **Total Failures**: Başarısız istek sayısı
- **Failure Rate**: Hata oranı (%)
- **Requests per Second (RPS)**: Saniyedeki istek sayısı

### Response Time Metrikleri
- **Average**: Ortalama yanıt süresi
- **Median (P50)**: Medyan yanıt süresi
- **P95**: 95. yüzdelik yanıt süresi (Requirement 2.1: < 3000ms)
- **P99**: 99. yüzdelik yanıt süresi
- **Maximum**: Maksimum yanıt süresi

### Endpoint-Specific Metrikleri
- `/api/youtube/recommendations`: Video öneri endpoint'i
- `/api/youtube/health`: Health check endpoint'i (Requirement 4.2: < 500ms)
- `/api/youtube/test`: API connectivity test

## Performance Thresholds

Test otomatik olarak aşağıdaki threshold'ları kontrol eder:

| Metric | Threshold | Requirement |
|--------|-----------|-------------|
| P95 Response Time | < 3000ms | Requirement 2.1 |
| Health Check P95 | < 500ms | Requirement 4.2 |
| Success Rate | > 95% | General |
| Concurrent Users | 100 | Requirement 11.3 |

Threshold'lar aşılırsa test FAILED olarak işaretlenir ve exit code 1 döner.

## Test Sonuçları

### Başarılı Test Örneği

```
======================================================================
PERFORMANCE ANALYSIS - VIDEO API
======================================================================
Total Requests:              15,234
Total Failures:              123
Failure Rate:                0.81%
Requests per Second:         50.78
----------------------------------------------------------------------
Response Times:
  Average:                   1,245ms
  Median (P50):              987ms
  95th Percentile (P95):     2,456ms
  99th Percentile (P99):     2,987ms
  Maximum:                   3,456ms
======================================================================

REQUIREMENT VALIDATION:
----------------------------------------------------------------------
✓ Requirement 11.3: 100 concurrent user load test - COMPLETED
✓ Requirement 2.1: P95 response time < 3000ms - PASSED (2456ms)
✓ Requirement 4.2: Health check < 500ms - PASSED (234ms)
✓ Success Rate > 95% - PASSED (99.19%)
======================================================================

✅ ALL REQUIREMENTS MET - TEST PASSED
```

## Troubleshooting

### Backend Başlatma

Load test çalıştırmadan önce backend'in çalıştığından emin olun:

```bash
cd backend
python main.py
```

### Connection Refused Hatası

```
Error: Connection refused
```

**Çözüm:** Backend'in çalıştığını ve doğru portta (8000) dinlediğini kontrol edin.

### Rate Limit Hataları

```
429 Too Many Requests
```

**Beklenen Durum:** Rate limiting çalışıyor demektir. Test bu durumu handle eder.

### Timeout Hataları

```
504 Gateway Timeout
```

**Çözüm:** 
- Backend'in yeterli kaynağa sahip olduğunu kontrol edin
- Cache'in çalıştığını doğrulayın
- YouTube API quota'sını kontrol edin

## CI/CD Entegrasyonu

### GitHub Actions Örneği

```yaml
name: Load Test

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Her gece 02:00

jobs:
  load-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install locust
      
      - name: Start backend
        run: |
          cd backend
          python main.py &
          sleep 10
      
      - name: Run load test
        run: |
          locust -f backend/tests/load/load_test_video_api.py \
            --users 100 \
            --spawn-rate 10 \
            --run-time 5m \
            --host http://localhost:8000 \
            --headless \
            --csv=results/load_test
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: results/
```

## Best Practices

1. **Gerçekçi Test Verileri**: Test'te kullanılan öğrenci profilleri gerçek kullanım senaryolarını yansıtmalı

2. **Kademeli Yük Artışı**: Spawn rate'i düşük tutarak sisteme kademeli yük verin

3. **Monitoring**: Load test sırasında sistem metriklerini (CPU, memory, network) izleyin

4. **Cache Warming**: İlk birkaç istek cache miss olacağından, test öncesi cache'i warm-up edin

5. **Realistic Wait Times**: Kullanıcılar arası bekleme süreleri gerçekçi olmalı (1-3 saniye)

6. **Error Handling**: Test'in hata durumlarını gracefully handle ettiğinden emin olun

7. **Cleanup**: Test sonrası oluşturulan test verilerini temizleyin

## İleri Seviye Kullanım

### Custom Metrics

```python
from locust import events

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    # Custom metric tracking
    if "cache_hit" in name:
        # Track cache hit rate
        pass
```

### Distributed Testing

Çok makine ile yük testi için:

```bash
# Master (1 makine)
locust -f load_test_video_api.py --master --expect-workers=4

# Workers (4 makine)
locust -f load_test_video_api.py --worker --master-host=<master-ip>
```

### Performance Profiling

```bash
# Python profiler ile
python -m cProfile -o profile.stats backend/tests/load/load_test_video_api.py

# Sonuçları görüntüle
python -m pstats profile.stats
```

## Kaynaklar

- [Locust Documentation](https://docs.locust.io/)
- [Load Testing Best Practices](https://docs.locust.io/en/stable/writing-a-locustfile.html)
- [Distributed Load Testing](https://docs.locust.io/en/stable/running-distributed.html)
