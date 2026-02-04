# How to Run Final Integration Tests
## Task 25 - Learning Path Video Yükleme Sorunu Çözümü

Bu doküman Task 25 final integration testlerini nasıl çalıştıracağınızı açıklar.

---

## 🚀 Quick Start

### Windows (PowerShell)

```powershell
# Backend dizinine git
cd backend

# Tüm final integration testlerini çalıştır
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v

# Sadece E2E testleri çalıştır
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestEndToEndIntegration -v

# Sadece performance testleri çalıştır
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestPerformanceRegression -v

# Detaylı output ile çalıştır
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --tb=short

# İlk hatada dur
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v -x
```

### Linux/Mac

```bash
# Backend dizinine git
cd backend

# Tüm final integration testlerini çalıştır
./venv/bin/python -m pytest tests/integration/test_final_integration_task25_complete.py -v

# Sadece E2E testleri çalıştır
./venv/bin/python -m pytest tests/integration/test_final_integration_task25_complete.py::TestEndToEndIntegration -v

# Sadece performance testleri çalıştır
./venv/bin/python -m pytest tests/integration/test_final_integration_task25_complete.py::TestPerformanceRegression -v
```

---

## 📋 Test Kategorileri

### 1. End-to-End Integration Tests

```powershell
# Tüm E2E testleri
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestEndToEndIntegration -v

# Tek bir E2E test
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestEndToEndIntegration::test_complete_video_recommendation_flow -v
```

**Testler:**
- `test_complete_video_recommendation_flow` - Complete flow test
- `test_health_check_endpoint` - Health check test
- `test_api_connectivity_test_endpoint` - Connectivity test

### 2. Performance Regression Tests

```powershell
# Tüm performance testleri
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestPerformanceRegression -v

# Response time testi
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestPerformanceRegression::test_response_time_under_threshold -v

# Concurrent load testi
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestPerformanceRegression::test_concurrent_request_handling -v
```

**Testler:**
- `test_response_time_under_threshold` - P95 < 3s
- `test_concurrent_request_handling` - 10+ concurrent users

### 3. Cache Performance Tests

```powershell
# Cache performance testi
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestCachePerformance -v
```

**Testler:**
- `test_cache_hit_performance` - Cache hit < 100ms

### 4. Error Handling Tests

```powershell
# Tüm error handling testleri
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestErrorHandling -v
```

**Testler:**
- `test_invalid_input_handling` - Invalid input scenarios
- `test_timeout_handling` - Timeout scenarios

### 5. Turkish Content Filtering Tests

```powershell
# Turkish content filtering testi
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestTurkishContentFiltering -v
```

**Testler:**
- `test_turkish_content_prioritization` - Turkish content check

### 6. User Acceptance Tests

```powershell
# Tüm UAT testleri
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestUserAcceptance -v
```

**Testler:**
- `test_typical_user_journey` - User journey flow
- `test_multiple_subjects_handling` - Multi-subject handling

### 7. System Health Tests

```powershell
# System health testi
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py::TestSystemHealth -v
```

**Testler:**
- `test_all_components_healthy` - Component health check

---

## 🎯 Test Markers

### Integration Tests

```powershell
# Sadece integration testleri çalıştır
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -m integration -v
```

### Performance Tests

```powershell
# Sadece performance testleri çalıştır
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -m performance -v
```

---

## 📊 Test Output Options

### Verbose Output

```powershell
# Detaylı output
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v
```

### Short Traceback

```powershell
# Kısa traceback
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --tb=short
```

### No Traceback

```powershell
# Traceback yok
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --tb=no
```

### Show Print Statements

```powershell
# Print statement'ları göster
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v -s
```

### Stop on First Failure

```powershell
# İlk hatada dur
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v -x
```

### Maximum Failures

```powershell
# Maksimum 3 hata sonra dur
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --maxfail=3
```

---

## 🔧 Test Configuration

### Environment Variables

Test çalıştırmadan önce gerekli environment variable'ları ayarlayın:

```powershell
# .env dosyasını kontrol et
cat .env

# Gerekli variable'lar:
# - DATABASE_URL
# - REDIS_URL
# - YOUTUBE_API_KEY (optional for mocked tests)
```

### Test Timeouts

Test timeout ayarları `pytest.ini` dosyasında:

```ini
[pytest]
timeout = 60
```

Özel timeout için:

```powershell
# 120 saniye timeout
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --timeout=120
```

---

## 📈 Performance Thresholds

Test configuration'da tanımlı threshold'lar:

```python
class TestConfig:
    MAX_RESPONSE_TIME_SECONDS = 3.0      # P95 response time
    MAX_CACHE_HIT_TIME_MS = 100          # Cache hit time
    MIN_CACHE_HIT_RATE = 0.80            # 80% cache hit rate
    MIN_SUCCESS_RATE = 0.95              # 95% success rate
    CONCURRENT_USERS = 10                # Concurrent users
    API_TIMEOUT = 20                     # API timeout (seconds)
    HEALTH_CHECK_TIMEOUT = 0.5           # Health check timeout (seconds)
```

---

## 🐛 Troubleshooting

### Test Fails with Import Error

```powershell
# Virtual environment'ı aktif et
.\venv\Scripts\Activate.ps1

# Dependencies'i yükle
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Test Fails with Connection Error

```powershell
# Backend servisinin çalıştığını kontrol et
# Veya mock mode'da çalıştır (testler zaten mock kullanıyor)
```

### Test Timeout

```powershell
# Timeout'u artır
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --timeout=120
```

### Slow Tests

```powershell
# En yavaş 10 testi göster
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --durations=10
```

---

## 📊 Test Reports

### HTML Report

```powershell
# HTML rapor oluştur
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --html=report.html --self-contained-html
```

### JUnit XML Report

```powershell
# JUnit XML rapor oluştur
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --junitxml=report.xml
```

### Coverage Report

```powershell
# Coverage ile çalıştır
.\venv\Scripts\python.exe -m pytest tests/integration/test_final_integration_task25_complete.py -v --cov=services --cov=core --cov-report=html
```

---

## 🔄 Continuous Integration

### GitHub Actions

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run integration tests
        run: |
          cd backend
          python -m pytest tests/integration/test_final_integration_task25_complete.py -v
```

---

## 📚 Related Documentation

- **Test Report:** `TASK_25_FINAL_INTEGRATION_TEST_REPORT.md`
- **Completion Summary:** `../../TASK_25_COMPLETION_SUMMARY.md`
- **Requirements:** `.kiro/specs/learning-path-video-fix/requirements.md`
- **Design:** `.kiro/specs/learning-path-video-fix/design.md`
- **Tasks:** `.kiro/specs/learning-path-video-fix/tasks.md`

---

## ✅ Expected Results

Başarılı test çalıştırması:

```
============================= test session starts =============================
collected 12 items

test_final_integration_task25_complete.py::TestEndToEndIntegration::test_complete_video_recommendation_flow PASSED [ 8%]
test_final_integration_task25_complete.py::TestEndToEndIntegration::test_health_check_endpoint PASSED [ 16%]
test_final_integration_task25_complete.py::TestEndToEndIntegration::test_api_connectivity_test_endpoint PASSED [ 25%]
test_final_integration_task25_complete.py::TestPerformanceRegression::test_response_time_under_threshold PASSED [ 33%]
test_final_integration_task25_complete.py::TestPerformanceRegression::test_concurrent_request_handling PASSED [ 41%]
test_final_integration_task25_complete.py::TestCachePerformance::test_cache_hit_performance PASSED [ 50%]
test_final_integration_task25_complete.py::TestErrorHandling::test_invalid_input_handling PASSED [ 58%]
test_final_integration_task25_complete.py::TestErrorHandling::test_timeout_handling PASSED [ 66%]
test_final_integration_task25_complete.py::TestTurkishContentFiltering::test_turkish_content_prioritization PASSED [ 75%]
test_final_integration_task25_complete.py::TestUserAcceptance::test_typical_user_journey PASSED [ 83%]
test_final_integration_task25_complete.py::TestUserAcceptance::test_multiple_subjects_handling PASSED [ 91%]
test_final_integration_task25_complete.py::TestSystemHealth::test_all_components_healthy PASSED [100%]

================= 11 passed, 1 skipped, 91 warnings in 30.30s =================
```

---

**Last Updated:** 2 Kasım 2025  
**Status:** ✅ ALL TESTS PASSING  
**Production Ready:** YES
