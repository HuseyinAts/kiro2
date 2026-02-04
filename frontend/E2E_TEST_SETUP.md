# E2E Test Setup Guide

Bu doküman, Learning Path video loading E2E testlerini çalıştırmak için gerekli kurulum adımlarını içerir.

## Gereksinimler

- Node.js 18+
- Python 3.11+
- npm veya yarn
- Backend servisi çalışır durumda
- Frontend servisi çalışır durumda

## Kurulum Adımları

### 1. Playwright Kurulumu

```bash
cd frontend
npm install
```

Bu komut `@playwright/test` paketini ve diğer bağımlılıkları kuracaktır.

### 2. Playwright Browsers Kurulumu

```bash
npx playwright install --with-deps
```

Bu komut Chromium, Firefox ve WebKit tarayıcılarını kuracaktır.

### 3. Environment Variables

`.env` dosyasını oluşturun veya güncelleyin:

```bash
VITE_API_URL=http://localhost:8001
VITE_APP_URL=http://localhost:3002
```

### 4. Backend Servisini Başlatın

```bash
cd backend
python -m uvicorn main:app --port 8001
```

Backend'in çalıştığını doğrulayın:
```bash
curl http://localhost:8001/health
```

### 5. Frontend Servisini Başlatın

```bash
cd frontend
npm run dev
```

Frontend'in çalıştığını doğrulayın:
```bash
curl http://localhost:3002
```

## Testleri Çalıştırma

### Otomatik Kurulum ve Test (Önerilen)

**Linux/Mac:**
```bash
chmod +x scripts/run-e2e-tests.sh
./scripts/run-e2e-tests.sh
```

**Windows:**
```cmd
scripts\run-e2e-tests.bat
```

### Manuel Test Çalıştırma

#### Tüm testleri çalıştır
```bash
npm run test:e2e
```

#### UI modunda çalıştır (interaktif)
```bash
npm run test:e2e:ui
```

#### Headed modda çalıştır (tarayıcı görünür)
```bash
npm run test:e2e:headed
```

#### Debug modda çalıştır
```bash
npm run test:e2e:debug
```

#### Belirli bir tarayıcıda çalıştır
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

#### Belirli bir test dosyasını çalıştır
```bash
npx playwright test learning-path-video-loading.spec.ts
```

#### Belirli bir test case'i çalıştır
```bash
npx playwright test -g "should load videos successfully"
```

## Test Raporlarını Görüntüleme

### HTML Raporu
```bash
npm run test:e2e:report
```

Bu komut tarayıcıda interaktif bir rapor açacaktır.

### JSON Raporu
Test sonuçları `test-results/e2e-results.json` dosyasında saklanır.

### Screenshots ve Videos
- Screenshots: `test-results/screenshots/`
- Videos: `test-results/videos/`
- Traces: `test-results/traces/`

## Troubleshooting

### Problem: "Playwright browsers not found"

**Çözüm:**
```bash
npx playwright install --with-deps
```

### Problem: "Backend is not running"

**Çözüm:**
```bash
cd backend
python -m uvicorn main:app --port 8001
```

Backend'in çalıştığını doğrulayın:
```bash
curl http://localhost:8001/health
```

### Problem: "Frontend is not running"

**Çözüm:**
```bash
cd frontend
npm run dev
```

Frontend'in çalıştığını doğrulayın:
```bash
curl http://localhost:3002
```

### Problem: "Test timeout"

**Çözüm:**
1. Network bağlantınızı kontrol edin
2. Backend ve frontend servislerinin çalıştığını doğrulayın
3. Timeout değerlerini artırın (playwright.config.ts)

### Problem: "Selector not found"

**Çözüm:**
1. `data-testid` attribute'larının eklendiğinden emin olun
2. Element'in render olduğunu doğrulayın
3. Selector'ı kontrol edin

### Problem: "Port already in use"

**Çözüm:**
```bash
# Linux/Mac
lsof -ti:8001 | xargs kill -9
lsof -ti:3002 | xargs kill -9

# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

## CI/CD Integration

### GitHub Actions

E2E testleri otomatik olarak GitHub Actions ile çalışır:
- Push to main/develop
- Pull request to main/develop
- Manuel trigger

Workflow dosyası: `.github/workflows/e2e-tests.yml`

### Test Artifacts

CI'da test başarısız olursa, aşağıdaki artifact'ler otomatik olarak yüklenir:
- Playwright report
- Test videos
- Screenshots
- Traces

## Best Practices

### 1. Test İzolasyonu
Her test bağımsız olmalı ve diğer testlerden etkilenmemelidir.

### 2. Mock Kullanımı
Gerçek API'ye bağımlı olmayın, mock'ları kullanın.

### 3. Selector Stratejisi
`data-testid` attribute'larını kullanın:
```html
<div data-testid="video-card">...</div>
```

### 4. Page Object Pattern
Sayfa etkileşimlerini helper class'larda soyutlayın.

### 5. Error Handling
Hata durumlarını test edin ve screenshot alın.

### 6. Performance
Test sürelerini optimize edin, gereksiz beklemelerden kaçının.

## Test Coverage

E2E testler aşağıdaki senaryoları kapsar:

- ✅ Success flow (başarılı video yükleme)
- ✅ Error handling (timeout, server error, network error)
- ✅ Retry logic (otomatik ve manuel retry)
- ✅ User interactions (cancel, fallback, retry)
- ✅ Offline mode (offline detection, cached videos)
- ✅ Performance (load time, UI blocking)
- ✅ Accessibility (ARIA labels, keyboard navigation)
- ✅ Mobile responsiveness (mobile viewport, touch)

## İlgili Dosyalar

- `playwright.config.ts` - Playwright konfigürasyonu
- `src/test/e2e/learning-path-video-loading.spec.ts` - Ana test dosyası
- `src/test/e2e/helpers/video-loading-helpers.ts` - Helper fonksiyonlar
- `src/test/e2e/README.md` - Test dokümantasyonu
- `scripts/run-e2e-tests.sh` - Linux/Mac test runner
- `scripts/run-e2e-tests.bat` - Windows test runner

## Destek

Sorun yaşarsanız:
1. Test raporlarını kontrol edin
2. Screenshots ve videos'ları inceleyin
3. Debug modda çalıştırın
4. GitHub Issues'da sorun açın

## Requirement

Bu testler aşağıdaki requirement'ı karşılar:
- **Requirement 11.5**: E2E test yazma (Playwright ile video yükleme flow'u)

## Lisans

Bu testler Teknofest 2025 Eğitim Eylemci projesi kapsamındadır.
