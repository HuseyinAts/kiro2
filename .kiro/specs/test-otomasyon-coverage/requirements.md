# Requirements Document - Test Otomasyonu ve Coverage Doğrulama Sistemi

## Introduction

Bu spec, Boris Cherny'nin verification feedback loops prensibine göre tasarlanmış test otomasyonu ve coverage doğrulama sistemini tanımlar. Sistem, her kod değişikliği sonrası otomatik test çalıştırma ve %80+ test coverage garantisi sağlar. Bu yaklaşım kod kalitesini %200-300 artırır ve regression bug'larını %95 oranında önler.

## Glossary

- **Test Coverage**: Kodun test edilen kısmının yüzdesi
- **pytest**: Python test framework'ü
- **pytest-cov**: Coverage ölçüm plugin'i
- **PreCommit Hook**: Commit öncesi otomatik çalışan hook
- **PostToolUse Hook**: Kod yazma sonrası otomatik çalışan hook
- **Unit Test**: Birim test (fonksiyon/method seviyesi)
- **Integration Test**: Entegrasyon testi (servis/API seviyesi)
- **E2E Test**: Uçtan uca test (kullanıcı senaryosu)
- **Coverage Threshold**: Minimum kabul edilebilir coverage oranı (%80)

## Requirements

### Requirement 1: Otomatik Test Çalıştırma

**User Story:** As a developer, I want her kod değişikliğinden sonra testlerin otomatik çalışmasını, so that regression bug'larını hemen tespit edeyim.

#### Acceptance Criteria

1. **REQ-1.1** WHEN bir Python dosyası değiştirildiğinde, THE PostToolUse Hook SHALL ilgili testleri otomatik çalıştırır
2. **REQ-1.2** WHEN test çalıştırıldığında, THE System SHALL pytest -x --tb=short komutunu kullanır
3. **REQ-1.3** WHEN test başarısız olduğunda, THE System SHALL ilk hatada durur ve detaylı traceback gösterir
4. **REQ-1.4** WHEN test başarılı olduğunda, THE System SHALL yeşil onay mesajı gösterir
5. **REQ-1.5** WHEN test süresi 30 saniyeyi aştığında, THE System SHALL uyarı verir
6. **REQ-1.6** IF test bulunamazsa, THEN THE System SHALL test yazılması gerektiğini uyarır

---

### Requirement 2: Coverage Ölçümü ve Raporlama

**User Story:** As a tech lead, I want her modülün test coverage'ını görmek, so that düşük coverage'lı alanları tespit edeyim.

#### Acceptance Criteria

1. **REQ-2.1** WHEN testler çalıştırıldığında, THE Coverage System SHALL pytest-cov ile coverage ölçer
2. **REQ-2.2** WHEN coverage ölçüldüğünde, THE System SHALL satır bazlı coverage hesaplar
3. **REQ-2.3** WHEN coverage raporu oluşturulduğunda, THE System SHALL modül bazlı breakdown gösterir
4. **REQ-2.4** WHEN coverage %80'in altında olduğunda, THE System SHALL kırmızı uyarı verir
5. **REQ-2.5** WHEN coverage raporu kaydedildiğinde, THE System SHALL HTML rapor oluşturur
6. **REQ-2.6** WHEN trend analizi yapıldığında, THE System SHALL coverage değişimini grafikle gösterir

---

### Requirement 3: PreCommit Hook Entegrasyonu

**User Story:** As a developer, I want commit yapmadan önce testlerin geçtiğinden emin olmak, so that broken code commit etmeyeyim.

#### Acceptance Criteria

1. **REQ-3.1** WHEN git commit yapıldığında, THE PreCommit Hook SHALL otomatik olarak tetiklenir
2. **REQ-3.2** WHEN hook tetiklendiğinde, THE Hook SHALL değişen dosyaların testlerini çalıştırır
3. **REQ-3.3** WHEN testler başarısız olduğunda, THE Hook SHALL commit'i engeller
4. **REQ-3.4** WHEN coverage %80'in altında olduğunda, THE Hook SHALL commit'i engeller
5. **REQ-3.5** WHEN linting hatası olduğunda, THE Hook SHALL commit'i engeller
6. **REQ-3.6** IF tüm kontroller geçerse, THEN THE Hook SHALL commit'e izin verir

---

### Requirement 4: Test Kategorileri ve Organizasyon

**User Story:** As a QA engineer, I want testlerin kategorize edilmesini, so that sadece ilgili testleri çalıştırabilirim.

#### Acceptance Criteria

1. **REQ-4.1** WHEN testler organize edildiğinde, THE System SHALL tests/unit/ dizininde unit testleri tutar
2. **REQ-4.2** WHEN testler organize edildiğinde, THE System SHALL tests/integration/ dizininde integration testleri tutar
3. **REQ-4.3** WHEN testler organize edildiğinde, THE System SHALL tests/e2e/ dizininde E2E testleri tutar
4. **REQ-4.4** WHEN pytest marker kullanıldığında, THE System SHALL @pytest.mark.unit, @pytest.mark.integration marker'larını destekler
5. **REQ-4.5** WHEN hızlı test çalıştırılmak istendiğinde, THE System SHALL pytest -m unit komutunu kullanır
6. **REQ-4.6** WHEN tam test suite çalıştırıldığında, THE System SHALL tüm kategorileri sırayla çalıştırır

---

### Requirement 5: Paralel Test Çalıştırma

**User Story:** As a developer, I want testlerin hızlı çalışmasını, so that development akışım yavaşlamasın.

#### Acceptance Criteria

1. **REQ-5.1** WHEN çok sayıda test çalıştırıldığında, THE System SHALL pytest-xdist kullanarak paralel çalıştırır
2. **REQ-5.2** WHEN paralel çalıştırma yapıldığında, THE System SHALL CPU core sayısına göre worker sayısı belirler
3. **REQ-5.3** WHEN worker sayısı belirlendiğinde, THE System SHALL maksimum (CPU_COUNT - 1) worker kullanır
4. **REQ-5.4** WHEN testler paralel çalıştığında, THE System SHALL test isolation sağlar
5. **REQ-5.5** WHEN paralel test tamamlandığında, THE System SHALL sonuçları birleştirir
6. **REQ-5.6** IF paralel çalıştırma hatası olursa, THEN THE System SHALL sequential mode'a geçer

---

### Requirement 6: Test Fixture Yönetimi

**User Story:** As a developer, I want test fixture'larını merkezi yönetmek, so that test setup kodunu tekrar yazmayayım.

#### Acceptance Criteria

1. **REQ-6.1** WHEN fixture tanımlandığında, THE System SHALL tests/conftest.py dosyasında merkezi fixture tutar
2. **REQ-6.2** WHEN database fixture kullanıldığında, THE System SHALL her test için temiz database oluşturur
3. **REQ-6.3** WHEN API client fixture kullanıldığında, THE System SHALL test client instance sağlar
4. **REQ-6.4** WHEN mock fixture kullanıldığında, THE System SHALL external service'leri mock'lar
5. **REQ-6.5** WHEN fixture scope belirlendiğinde, THE System SHALL function/class/module/session scope'larını destekler
6. **REQ-6.6** WHEN fixture cleanup gerektiğinde, THE System SHALL yield pattern kullanarak cleanup yapar

---

### Requirement 7: Flaky Test Tespiti

**User Story:** As a QA engineer, I want kararsız testleri tespit etmek, so that güvenilir test suite'im olsun.

#### Acceptance Criteria

1. **REQ-7.1** WHEN bir test bazen geçip bazen başarısız olduğunda, THE Flaky Detector SHALL testi flaky olarak işaretler
2. **REQ-7.2** WHEN flaky test tespit edildiğinde, THE Detector SHALL son 10 çalıştırmayı analiz eder
3. **REQ-7.3** WHEN başarı oranı %50-95 arasında olduğunda, THE Detector SHALL testi flaky kategorisine alır
4. **REQ-7.4** WHEN flaky test raporu oluşturulduğunda, THE Detector SHALL olası nedenleri listeler (timing, race condition, external dependency)
5. **REQ-7.5** WHEN flaky test bulunduğunda, THE Detector SHALL yöneticiye bildirim gönderir
6. **REQ-6.6** IF flaky test sayısı 5'i aşarsa, THEN THE Detector SHALL kritik uyarı verir

---

### Requirement 8: Coverage Threshold Enforcement

**User Story:** As a tech lead, I want minimum coverage standardını zorlamak, so that kod kalitesi düşmesin.

#### Acceptance Criteria

1. **REQ-8.1** WHEN coverage kontrol edildiğinde, THE Threshold Enforcer SHALL global threshold'u %80 olarak uygular
2. **REQ-8.2** WHEN yeni dosya eklendiğinde, THE Enforcer SHALL yeni dosya için %90 threshold ister
3. **REQ-8.3** WHEN kritik modül kontrol edildiğinde, THE Enforcer SHALL core/ ve services/ için %95 threshold ister
4. **REQ-8.4** WHEN threshold ihlali tespit edildiğinde, THE Enforcer SHALL detaylı rapor oluşturur
5. **REQ-8.5** WHEN CI/CD pipeline çalıştığında, THE Enforcer SHALL threshold ihlalinde build'i başarısız yapar
6. **REQ-8.6** IF legacy kod için exception gerekirse, THEN THE Enforcer SHALL .coveragerc dosyasında exclude pattern destekler

---

## Bağımlılıklar

- **pytest**: Test framework
- **pytest-cov**: Coverage plugin
- **pytest-xdist**: Paralel test çalıştırma
- **pytest-asyncio**: Async test desteği
- **coverage**: Coverage ölçüm kütüphanesi
- **pre-commit**: Git hook yönetimi
- **GitHub Actions**: CI/CD entegrasyonu

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 1 hafta
**Beklenen Coverage:** %80+ (şu an %60)

## Test Automation Flow

```
1. Kod Değişikliği
   ↓
2. PostToolUse Hook Tetiklendi
   ↓
3. İlgili Testler Belirlendi
   ├─ Unit Tests (tests/unit/)
   ├─ Integration Tests (tests/integration/)
   └─ E2E Tests (tests/e2e/)
   ↓
4. Paralel Test Çalıştırma
   ├─ Worker 1: Unit Tests
   ├─ Worker 2: Integration Tests
   └─ Worker 3: E2E Tests
   ↓
5. Coverage Ölçümü
   ├─ Satır Coverage
   ├─ Branch Coverage
   └─ Modül Coverage
   ↓
6. Threshold Kontrolü
   ├─ Global: >= %80
   ├─ New Files: >= %90
   └─ Core Modules: >= %95
   ↓
7. Flaky Test Analizi
   ↓
8. Rapor Oluşturma
   ├─ Terminal Output
   ├─ HTML Report
   └─ Coverage Badge
   ↓
9. Tüm Kontroller Geçti?
   ├─ EVET → Commit İzni ✓
   └─ HAYIR → Commit Engellendi ✗
```

## Success Metrics

1. **Test Coverage:** >= %80 (global), >= %95 (core modules)
2. **Test Execution Time:** < 2 dakika (unit), < 5 dakika (full suite)
3. **Flaky Test Oranı:** < %2
4. **Regression Bug Önleme:** >= %95
5. **CI/CD Success Rate:** >= %98

