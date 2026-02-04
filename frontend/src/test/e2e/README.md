# E2E Tests - Learning Path Video Loading

Bu dizin, Learning Path video yükleme özelliği için End-to-End (E2E) testlerini içerir.

## Test Kapsamı

### 1. Success Flow (Başarılı Akış)
- ✅ Videoların 3 saniye içinde yüklenmesi
- ✅ Loading indicator ve progress gösterimi
- ✅ Video kartlarının görüntülenmesi
- ✅ Cache hit indicator

### 2. Error Handling (Hata Yönetimi)
- ✅ Timeout hatası
- ✅ 500 sunucu hatası
- ✅ Network hatası
- ✅ CORS hatası

### 3. Retry Logic (Yeniden Deneme)
- ✅ Otomatik retry
- ✅ Manuel retry
- ✅ Exponential backoff
- ✅ Retry count gösterimi

### 4. User Interactions (Kullanıcı Etkileşimleri)
- ✅ Video yüklemeyi iptal etme
- ✅ Fallback videoları gösterme
- ✅ Personalized ve fallback arasında geçiş
- ✅ Video izleme takibi

### 5. Offline Mode (Çevrimdışı Mod)
- ✅ Offline durumu algılama
- ✅ Cached videoları gösterme
- ✅ Bağlantı geri geldiğinde otomatik retry
- ✅ Network kalite göstergesi

### 6. Performance (Performans)
- ✅ Performance budget kontrolü
- ✅ UI blocking kontrolü
- ✅ Concurrent request yönetimi

### 7. Accessibility (Erişilebilirlik)
- ✅ ARIA labels
- ✅ Keyboard navigation
- ✅ Screen reader announcements

### 8. Mobile Responsiveness (Mobil Uyumluluk)
- ✅ Mobile viewport
- ✅ Touch interactions

## Testleri Çalıştırma

### Tüm testleri çalıştır
```bash
npm run test:e2e
```

### UI modunda çalıştır (interaktif)
```bash
npm run test:e2e:ui
```

### Headed modda çalıştır (tarayıcı görünür)
```bash
npm run test:e2e:headed
```

### Debug modda çalıştır
```bash
npm run test:e2e:debug
```

### Sadece belirli bir test dosyasını çalıştır
```bash
npx playwright test learning-path-video-loading.spec.ts
```

### Sadece belirli bir tarayıcıda çalıştır
```bash
npx playwright test --project=chromium
```

### Test raporunu görüntüle
```bash
npm run test:e2e:report
```

## Test Yapısı

```
src/test/e2e/
├── learning-path-video-loading.spec.ts  # Ana test dosyası
├── helpers/
│   └── video-loading-helpers.ts         # Test yardımcı fonksiyonları
└── README.md                             # Bu dosya
```

## Helper Fonksiyonlar

### VideoLoadingMocks
API yanıtlarını mock'lamak için kullanılır:

```typescript
const mocks = new VideoLoadingMocks(page);

// Başarılı yanıt
await mocks.mockSuccess();

// Cached yanıt
await mocks.mockCached();

// Timeout
await mocks.mockTimeout();

// Server error
await mocks.mockServerError();

// Network error
await mocks.mockNetworkError();
```

### LearningPathPage
Page Object Pattern kullanarak sayfa etkileşimleri:

```typescript
const learningPath = new LearningPathPage(page);

// Sayfaya git
await learningPath.navigate();

// Öğrenme yolu oluştur
await learningPath.clickCreateLearningPath();

// Başarı durumunu bekle
await learningPath.waitForSuccess();

// Video kartlarını al
const cards = learningPath.getVideoCards();
```

### TestUtils
Genel test yardımcı fonksiyonları:

```typescript
// Performance ölçümü
const duration = await TestUtils.measurePerformance(page, async () => {
  await learningPath.clickCreateLearningPath();
  await learningPath.waitForSuccess();
});

// Yavaş network simülasyonu
await TestUtils.simulateSlowNetwork(page);

// Offline simülasyonu
await TestUtils.simulateOffline(page);
```

## Mock Data

Test için kullanılan mock data `helpers/video-loading-helpers.ts` dosyasında tanımlıdır:

- `mockVideoData.success`: Başarılı video yanıtı
- `mockVideoData.cached`: Cache'den gelen yanıt
- `mockVideoData.empty`: Boş sonuç

## Environment Variables

Testler için gerekli environment variables:

```bash
VITE_API_URL=http://localhost:8001
VITE_APP_URL=http://localhost:3002
```

## CI/CD Integration

GitHub Actions veya diğer CI/CD sistemlerinde çalıştırmak için:

```yaml
- name: Install Playwright Browsers
  run: npx playwright install --with-deps

- name: Run E2E Tests
  run: npm run test:e2e

- name: Upload Test Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Debugging

### Test başarısız olduğunda:

1. **Screenshot'ları kontrol et**: `test-results/screenshots/`
2. **Video kayıtlarını izle**: `test-results/videos/`
3. **Trace'i incele**: `playwright show-trace trace.zip`
4. **Debug modda çalıştır**: `npm run test:e2e:debug`

### Console logları yakalama:

```typescript
const logs = TestUtils.setupConsoleCapture(page);
// Test çalıştır
console.log('Console logs:', logs);
```

### Network isteklerini yakalama:

```typescript
const requests = TestUtils.setupNetworkCapture(page);
// Test çalıştır
console.log('Network requests:', requests);
```

## Best Practices

1. **Test İzolasyonu**: Her test bağımsız olmalı
2. **Mock Kullanımı**: Gerçek API'ye bağımlı olmayın
3. **Timeout Yönetimi**: Uygun timeout değerleri kullanın
4. **Selector Stratejisi**: `data-testid` kullanın
5. **Page Object Pattern**: Sayfa etkileşimlerini soyutlayın
6. **Error Handling**: Hata durumlarını test edin
7. **Performance**: Test sürelerini optimize edin

## Troubleshooting

### Test çalışmıyor
- Playwright browsers kurulu mu? `npx playwright install`
- Frontend çalışıyor mu? `npm run dev`
- Port doğru mu? `.env` dosyasını kontrol et

### Test timeout oluyor
- Network yavaş olabilir
- Timeout değerlerini artırın
- Mock'ları kullanın

### Selector bulunamıyor
- `data-testid` attribute'ları eklenmiş mi?
- Selector doğru mu?
- Element render olmuş mu?

## Requirements

Bu testler aşağıdaki requirement'ı karşılar:

- **Requirement 11.5**: E2E test yazma (Playwright ile video yükleme flow'u)

## İlgili Dosyalar

- `frontend/src/services/VideoLoadingManager.ts` - Video yükleme servisi
- `frontend/src/hooks/useOfflineMode.ts` - Offline mode hook
- `frontend/src/main.tsx` - Learning Path sayfası
- `backend/api/youtube_routes.py` - Video API endpoint'leri

## Katkıda Bulunma

Yeni test senaryoları eklerken:

1. Test'i uygun describe bloğuna ekleyin
2. Açıklayıcı test isimleri kullanın
3. Helper fonksiyonları kullanın
4. Mock data kullanın
5. README'yi güncelleyin

## Lisans

Bu testler Teknofest 2025 Eğitim Eylemci projesi kapsamındadır.
