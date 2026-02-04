# Performance Testing Quick Start Guide

Video API için hızlı performans testi başlangıç rehberi.

## Hızlı Başlangıç

### 1. Performance Benchmark Çalıştır

```bash
# Backend dizinine git
cd backend

# Benchmark'ı çalıştır
python scripts/performance_benchmark.py
```

**Çıktı**: `backend/reports/performance_benchmark_YYYYMMDD_HHMMSS.json`

### 2. Performance Report Oluştur

```bash
# Report generator'ı çalıştır
python scripts/generate_performance_report.py
```

**Çıktılar**:
- `backend/reports/performance_analysis_YYYYMMDD_HHMMSS.json`
- `backend/reports/performance_analysis_YYYYMMDD_HHMMSS.md`

### 3. Performance Tests Çalıştır

```bash
# Tüm performance testleri
pytest tests/performance/ -v -m performance

# Sadece response time testi
pytest tests/performance/test_video_api_performance.py::TestVideoAPIPerformance::test_response_time_benchmark -v

# Sadece cache testi
pytest tests/performance/test_video_api_performance.py::TestVideoAPIPerformance::test_cache_hit_rate_optimization -v
```

### 4. Load Testing Çalıştır

```bash
# Locust'u başlat
locust -f tests/load/locustfile_video_api.py --host=http://localhost:8000

# Web UI'ı aç: http://localhost:8089
# Users: 100
# Spawn rate: 10/s
# Duration: 10 minutes
```

## Performance Targets

| Metric | Target | Test |
|--------|--------|------|
| P95 Response Time | < 3s | `test_response_time_benchmark` |
| Cache Hit Rate | > 80% | `test_cache_hit_rate_optimization` |
| Avg DB Query | < 100ms | `test_database_query_optimization` |
| Memory Growth | < 50MB | `test_memory_usage_optimization` |
| Parallel Speedup | > 2.5x | `test_parallel_processing_performance` |

## Örnek Çıktılar

### Benchmark Output

```
============================================================
PERFORMANCE BENCHMARK - Video API
============================================================
Started at: 2025-11-02T10:30:00

[1/5] Response Time Benchmark
------------------------------------------------------------
  Progress: 20/100 requests
  Progress: 40/100 requests
  Progress: 60/100 requests
  Progress: 80/100 requests
  Progress: 100/100 requests

  Results:
    Average:  150.5ms
    Median:   145.2ms
    P95:      280.3ms (target: <3000ms)
    P99:      350.1ms
    Min:      95.2ms
    Max:      420.8ms
    Status:   ✓ PASS

[2/5] Cache Performance Benchmark
------------------------------------------------------------
  Progress: 200/1000 requests (hit rate: 75.0%)
  Progress: 400/1000 requests (hit rate: 80.5%)
  Progress: 600/1000 requests (hit rate: 82.3%)
  Progress: 800/1000 requests (hit rate: 83.8%)
  Progress: 1000/1000 requests (hit rate: 85.0%)

  Results:
    Total Requests: 1000
    Cache Hits:     850
    Cache Misses:   150
    Hit Rate:       85.0% (target: >80%)
    Status:         ✓ PASS

...

============================================================
BENCHMARK COMPLETE
============================================================

Summary:
  Total Benchmarks: 5
  Passed:           5
  Failed:           0
  Pass Rate:        100.0%
  Overall Status:   PASS
```

### Performance Report Output

```
================================================================================
PERFORMANCE ANALYSIS REPORT
================================================================================
Generated: 2025-11-02T10:35:00

BENCHMARK RESULTS
--------------------------------------------------------------------------------

✓ Response Time: PASS
    average_ms: 150.50
    median_ms: 145.20
    p95_ms: 280.30
    target_p95_ms: 3000.00
    margin_ms: 2719.70
    margin_percent: 90.66

✓ Cache Performance: PASS
    hit_rate_percent: 85.00
    target_percent: 80.00
    margin_percent: 5.00

✓ Database Queries: PASS
    avg_ms: 25.30
    target_ms: 100.00
    margin_ms: 74.70

✓ Memory Usage: PASS
    growth_mb: 12.50
    target_mb: 50.00
    margin_mb: 37.50

✓ Parallel Processing: PASS
    speedup: 2.95
    target_speedup: 2.50
    efficiency_percent: 98.33

--------------------------------------------------------------------------------
OVERALL ANALYSIS
--------------------------------------------------------------------------------
Total Benchmarks: 5
Passed:           5
Failed:           0
Pass Rate:        100.0%
Overall Status:   PASS

================================================================================
```

## Troubleshooting

### Python Bulunamadı

```bash
# Python yolunu kontrol et
where python

# Veya python3 kullan
python3 scripts/performance_benchmark.py
```

### Pytest Bulunamadı

```bash
# Virtual environment'ı aktif et
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Pytest'i yükle
pip install pytest pytest-asyncio psutil
```

### Locust Bulunamadı

```bash
# Locust'u yükle
pip install locust

# Versiyonu kontrol et
locust --version
```

## Detaylı Dokümantasyon

Daha fazla bilgi için:
- **Optimization Guide**: `backend/docs/PERFORMANCE_OPTIMIZATION_GUIDE.md`
- **Completion Report**: `backend/TASK_24_PERFORMANCE_OPTIMIZATION_COMPLETE.md`
- **Test Code**: `backend/tests/performance/test_video_api_performance.py`

## Monitoring

### Prometheus Metrics

```bash
# Metrics endpoint
curl http://localhost:8000/metrics

# Örnek metrikler:
# video_api_response_time_seconds
# video_api_cache_hit_rate
# video_api_requests_total
```

### Grafana Dashboard

```bash
# Grafana'yı başlat
docker-compose up grafana

# Dashboard: http://localhost:3000
# Import: config/grafana_video_dashboard.json
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/performance-tests.yml
name: Performance Tests

on: [push, pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Performance Tests
        run: |
          cd backend
          pytest tests/performance/ -v -m performance
```

## Support

Sorular için:
- **Documentation**: `backend/docs/`
- **Issues**: GitHub Issues
- **Contact**: Development Team

---

**Last Updated**: 2 Kasım 2025
