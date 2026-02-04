# End-to-End Platform Testing Guide

## Genel Bakış

Bu test suite, Türkiye Üniversite Sınavları Hazırlık Platformu'nun tüm bileşenlerinin birlikte çalışmasını test eden kapsamlı entegrasyon testlerini içerir.

## Test Kategorileri

### 1. Tam Sınav Workflow Testleri
**Dosya**: `test_end_to_end_platform.py::TestFullExamWorkflow`

- ✅ TYT sınav workflow'u (başlatma → sorular → cevaplama → sonuçlar → analiz)
- ✅ Performans analizi ve zayıf konu tespiti
- ✅ Adaptif öğrenme önerileri

**Çalıştırma**:
```bash
pytest backend/tests/integration/test_end_to_end_platform.py::TestFullExamWorkflow -v
```

### 2. Tam Öğrenci Yolculuğu Testleri
**Dosya**: `test_end_to_end_platform.py::TestFullStudentJourney`

- ✅ Kayıt (Registration)
- ✅ Giriş (Login)
- ✅ Profil oluşturma
- ✅ Öğrenme stili tespiti
- ✅ Sınav başlatma ve tamamlama
- ✅ Sonuçlar ve performans analizi
- ✅ Kişiselleştirilmiş öneriler
- ✅ İçerik önerileri
- ✅ Öğrenme yolu oluşturma

**Çalıştırma**:
```bash
pytest backend/tests/integration/test_end_to_end_platform.py::TestFullStudentJourney::test_complete_student_journey -v -s
```

**Requirements Karşılama**: 1.1-1.6 (Sınav sistemi), 4.1-4.5 (Adaptif öğrenme)

### 3. Öğretmen-Öğrenci-Veli Workflow Testleri
**Dosya**: `test_end_to_end_platform.py::TestTeacherStudentParentWorkflow`

- ✅ Öğretmen, öğrenci ve veli kayıt/giriş
- ✅ Veli-öğrenci bağlantısı
- ✅ Öğretmen sınıf oluşturma
- ✅ Öğrenciyi sınıfa ekleme
- ✅ Ödev oluşturma ve atama
- ✅ Öğrenci ödev tamamlama
- ✅ Öğretmen performans raporu
- ✅ Veli haftalık rapor
- ✅ Veli-öğretmen iletişimi

**Çalıştırma**:
```bash
pytest backend/tests/integration/test_end_to_end_platform.py::TestTeacherStudentParentWorkflow::test_teacher_student_parent_interaction -v -s
```

**Requirements Karşılama**: 6.1-6.5 (Öğretmen ve veli takip sistemi)

### 4. Çoklu Kullanıcı Eşzamanlı Testler
**Dosya**: `test_end_to_end_platform.py::TestMultiUserConcurrentScenarios`

- ✅ 1000+ eşzamanlı sınav oturumu
- ✅ Batch processing ile yük dağıtımı
- ✅ Başarı oranı ve performans metrikleri
- ✅ Hata yönetimi ve exception handling

**Çalıştırma**:
```bash
pytest backend/tests/integration/test_end_to_end_platform.py::TestMultiUserConcurrentScenarios::test_concurrent_exam_sessions_1000_users -v -s
```

**Requirements Karşılama**: 7.2 (100K+ eşzamanlı kullanıcı)

### 5. WebSocket Gerçek Zamanlı İletişim Testleri
**Dosya**: `test_end_to_end_platform.py::TestWebSocketRealTimeCommunication`

- ✅ WebSocket bağlantı yönetimi
- ✅ Multi-agent koordinasyon
- ✅ Gerçek zamanlı mesajlaşma
- ✅ Agent senkronizasyonu

**Çalıştırma**:
```bash
pytest backend/tests/integration/test_end_to_end_platform.py::TestWebSocketRealTimeCommunication::test_websocket_agent_coordination -v -s
```

**Requirements Karşılama**: 11.1-11.6 (Gerçek zamanlı iletişim ve koordinasyon)

### 6. Offline-Online Senkronizasyon Testleri
**Dosya**: `test_end_to_end_platform.py::TestOfflineOnlineSynchronization`

- ✅ Offline içerik paketi indirme
- ✅ Offline sınav tamamlama
- ✅ Online senkronizasyon
- ✅ Sonuç doğrulama
- ✅ Progress senkronizasyonu
- ✅ Conflict resolution
- ✅ İçerik önbellekleme

**Çalıştırma**:
```bash
pytest backend/tests/integration/test_end_to_end_platform.py::TestOfflineOnlineSynchronization -v -s
```

**Requirements Karşılama**: 8.1-8.5 (PWA ve offline çalışma)

### 7. Performance Yük Testleri
**Dosya**: `test_end_to_end_platform.py::TestPerformanceLoadTesting`

#### 7.1. 10K Kullanıcı Yük Simülasyonu (100K için extrapolation)
- ✅ 10,000 gerçek kullanıcı testi
- ✅ 100,000 kullanıcı için extrapolation
- ✅ Throughput ve yanıt süresi metrikleri
- ✅ Memory ve CPU kullanımı

**Çalıştırma**:
```bash
pytest backend/tests/integration/test_end_to_end_platform.py::TestPerformanceLoadTesting::test_high_load_simulation_10k_users -v -s
```

#### 7.2. Stres Testi - Yanıt Süresi Analizi
- ✅ Farklı yük seviyelerinde test (100, 500, 1K, 2K, 5K)
- ✅ p50, p95, p99 yanıt süreleri
- ✅ Requirement 7.1: p95 < 200ms kontrolü

**Çalıştırma**:
```bash
pytest backend/tests/integration/test_end_to_end_platform.py::TestPerformanceLoadTesting::test_stress_test_response_time -v -s
```

#### 7.3. Sürekli Yük Stabilitesi Testi
- ✅ 5 dakika sürekli yük
- ✅ Uptime hesaplama
- ✅ Requirement 7.3: %99.9 uptime kontrolü

**Çalıştırma**:
```bash
pytest backend/tests/integration/test_end_to_end_platform.py::TestPerformanceLoadTesting::test_sustained_load_stability -v -s
```

**Requirements Karşılama**: 7.1 (p95 < 200ms), 7.2 (100K+ kullanıcı), 7.3 (%99.9 uptime)

## 100K+ Concurrent Users Load Testing

### Büyük Ölçekli Yük Testleri
**Dosya**: `backend/tests/load/test_100k_concurrent_users.py`

#### Test 1: 100K Kullanıcı Simülasyonu (Extrapolated)
- 10K gerçek kullanıcı + 100K extrapolation
- Batch processing ile kaynak optimizasyonu
- Detaylı metrik toplama

**Çalıştırma**:
```bash
pytest backend/tests/load/test_100k_concurrent_users.py::Test100KConcurrentUsers::test_100k_user_simulation_extrapolated -v -s -m slow
```

#### Test 2: Yük Altında Yanıt Süresi
- 100, 500, 1K, 5K, 10K yük seviyeleri
- p95 yanıt süresi analizi
- Requirement 7.1 doğrulama

**Çalıştırma**:
```bash
pytest backend/tests/load/test_100k_concurrent_users.py::Test100KConcurrentUsers::test_response_time_under_load -v -s -m slow
```

#### Test 3: Sürekli Yüksek Yük
- 10 dakika sürekli yük
- %99.9 uptime doğrulama
- Requirement 7.3 kontrolü

**Çalıştırma**:
```bash
pytest backend/tests/load/test_100k_concurrent_users.py::Test100KConcurrentUsers::test_sustained_high_load -v -s -m slow
```

#### Test 4: Otomatik Ölçeklendirme Simülasyonu
- Kademeli yük artışı (100 → 5K)
- Ölçeklendirme stabilitesi
- Requirement 7.6 doğrulama

**Çalıştırma**:
```bash
pytest backend/tests/load/test_100k_concurrent_users.py::Test100KConcurrentUsers::test_auto_scaling_simulation -v -s -m slow
```

## Tüm Testleri Çalıştırma

### Hızlı Testler (Integration)
```bash
pytest backend/tests/integration/test_end_to_end_platform.py -v
```

### Yavaş Testler (Load Testing)
```bash
pytest backend/tests/load/test_100k_concurrent_users.py -v -s -m slow
```

### Tüm End-to-End Testler
```bash
pytest backend/tests/integration/test_end_to_end_platform.py backend/tests/load/test_100k_concurrent_users.py -v -s
```

### Belirli Bir Test Kategorisi
```bash
# Sadece student journey testleri
pytest backend/tests/integration/test_end_to_end_platform.py::TestFullStudentJourney -v

# Sadece teacher-student-parent workflow
pytest backend/tests/integration/test_end_to_end_platform.py::TestTeacherStudentParentWorkflow -v

# Sadece offline-online sync
pytest backend/tests/integration/test_end_to_end_platform.py::TestOfflineOnlineSynchronization -v
```

## Test Gereksinimleri

### Sistem Gereksinimleri
- Python 3.9+
- PostgreSQL veya SQLite (test database)
- Redis (cache için)
- Minimum 8GB RAM (10K+ kullanıcı testleri için)
- Minimum 4 CPU cores

### Python Paketleri
```bash
pip install pytest pytest-asyncio aiohttp psutil websockets
```

### Ortam Değişkenleri
```bash
# .env.test dosyası
DATABASE_URL=postgresql+asyncpg://testuser:test123@localhost:5433/testdb
REDIS_URL=redis://localhost:6379/0
USE_TEST_DB=true
TESTING=true
```

## Test Metrikleri ve Başarı Kriterleri

### Başarı Oranları
- ✅ Minimum %80 başarı oranı (tüm testler)
- ✅ Maksimum %5 exception oranı

### Yanıt Süreleri
- ✅ p95 < 200ms (düşük-orta yük)
- ✅ Ortalama < 5000ms (yüksek yük)

### Uptime
- ✅ %99.9 uptime (sürekli yük testleri)

### Kaynak Kullanımı
- ✅ Memory artışı < 2GB (10K kullanıcı)
- ✅ CPU kullanımı stabil

## Sorun Giderme

### Test Başarısız Olursa

1. **Database bağlantı hatası**:
   ```bash
   # PostgreSQL'in çalıştığından emin olun
   docker-compose up -d postgres
   ```

2. **Redis bağlantı hatası**:
   ```bash
   # Redis'in çalıştığından emin olun
   docker-compose up -d redis
   ```

3. **Timeout hataları**:
   - Test timeout değerlerini artırın
   - Sistem kaynaklarını kontrol edin
   - Concurrent limit değerlerini azaltın

4. **Memory hataları**:
   - Batch size değerlerini azaltın
   - Test kullanıcı sayısını azaltın
   - Sistem RAM'ini artırın

## CI/CD Entegrasyonu

### GitHub Actions
```yaml
name: End-to-End Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      - name: Run integration tests
        run: pytest backend/tests/integration/test_end_to_end_platform.py -v
      - name: Run load tests (sample)
        run: pytest backend/tests/load/test_100k_concurrent_users.py::Test100KConcurrentUsers::test_response_time_under_load -v -s
```

## Raporlama

### HTML Rapor Oluşturma
```bash
pytest backend/tests/integration/test_end_to_end_platform.py --html=report.html --self-contained-html
```

### JSON Rapor Oluşturma
```bash
pytest backend/tests/integration/test_end_to_end_platform.py --json-report --json-report-file=report.json
```

## İletişim ve Destek

Test suite ile ilgili sorularınız için:
- GitHub Issues: [proje-repo]/issues
- Email: support@turkiye-sinav-platformu.com

## Lisans

Bu test suite, Türkiye Üniversite Sınavları Hazırlık Platformu'nun bir parçasıdır.
