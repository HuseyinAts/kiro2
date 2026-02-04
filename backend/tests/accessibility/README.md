# Accessibility and Compliance Testing Suite

**Task 45: Accessibility and Compliance Testing**

Bu test suite, Türkiye Üniversite Sınavları Hazırlık Platformu'nun erişilebilirlik ve uyumluluk standartlarına uygunluğunu kapsamlı bir şekilde test eder.

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Test Modülleri](#test-modülleri)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Test Kapsamı](#test-kapsamı)
- [Raporlama](#raporlama)
- [Standartlar](#standartlar)

## 🎯 Genel Bakış

Bu test suite, aşağıdaki erişilebilirlik standartlarına uyumluluğu test eder:

- ✅ **WCAG 2.1 Level AA** - Web Content Accessibility Guidelines
- ✅ **Ekran Okuyucu Uyumluluğu** - NVDA, JAWS, VoiceOver, TalkBack
- ✅ **Klavye Erişilebilirliği** - Tam klavye navigasyonu
- ✅ **Türkçe Dil Desteği** - UTF-8 encoding ve Türkçe karakterler

### Requirements

- **9.1**: Görsel içerik için alternatif metin
- **9.2**: Matematiksel formüller için ekran okuyucu uyumluluğu
- **9.3**: Video içerik için altyazı ve transkript
- **9.4**: Klavye ile tam navigasyon
- **9.5**: WCAG 2.1 Level AA uyumluluğu
- **7.4**: Türkçe karakter encoding (UTF-8)

## 📦 Test Modülleri

### 1. WCAG 2.1 Level AA Compliance (`test_wcag_compliance.py`)

WCAG 2.1 Level AA standartlarına otomatik uyumluluk testleri.

**Test Edilen Kılavuzlar:**
- 1.1.1 - Non-text Content (Alt text)
- 1.4.3 - Contrast (Minimum) (4.5:1 kontrast oranı)
- 2.1.1 - Keyboard (Klavye erişilebilirliği)
- 2.4.2 - Page Titled (Sayfa başlıkları)
- 3.1.1 - Language of Page (Dil tanımı)
- 4.1.2 - Name, Role, Value (ARIA etiketleri)
- Ve daha fazlası...

**Örnek Kullanım:**
```python
from test_wcag_compliance import WCAGComplianceChecker

checker = WCAGComplianceChecker()
result = checker.check_guideline("1.1.1", html_content)
report = checker.generate_compliance_report()
```

### 2. Screen Reader Compatibility (`test_screen_reader_compatibility.py`)

Ekran okuyucu uyumluluğu testleri.

**Test Edilen Özellikler:**
- ARIA live regions (Dinamik içerik güncellemeleri)
- Form field descriptions (Form alanı açıklamaları)
- Heading structure (Başlık hiyerarşisi)
- Landmark regions (Sayfa yapısı)
- Button and link labels (Buton ve link etiketleri)
- Table accessibility (Tablo erişilebilirliği)
- Math formula accessibility (Matematik formül erişilebilirliği)
- Status messages (Durum mesajları)

**Desteklenen Ekran Okuyucular:**
- NVDA (Windows)
- JAWS (Windows)
- VoiceOver (macOS/iOS)
- TalkBack (Android)

### 3. Keyboard Navigation (`test_keyboard_navigation.py`)

Klavye navigasyon testleri.

**Test Edilen Özellikler:**
- Tab order (Tab sırası)
- No keyboard trap (Klavye tuzağı yok)
- Focus indicators (Odak göstergeleri)
- Skip links (İçeriğe atla linkleri)
- Interactive elements (İnteraktif elementler)
- Form keyboard navigation (Form klavye navigasyonu)
- Modal keyboard interaction (Modal klavye etkileşimi)
- Custom controls (Özel kontroller)

**Desteklenen Klavye Kısayolları:**
- `Tab` - Sonraki elemente geç
- `Shift+Tab` - Önceki elemente geç
- `Enter` - Aktif elementi etkinleştir
- `Space` - Checkbox/radio seç
- `Arrow Keys` - Radio group, dropdown navigasyonu
- `Escape` - Modal/dialog kapat
- `Home/End` - İlk/son elemente git

### 4. Turkish Character Encoding (`test_turkish_encoding.py`)

Türkçe karakter encoding doğrulama testleri.

**Test Edilen Alanlar:**
- UTF-8 encoding (Temel encoding)
- HTML meta charset (HTML charset tanımı)
- Database encoding (Veritabanı encoding)
- API response encoding (API yanıt encoding)
- URL encoding (URL encoding)
- File system encoding (Dosya sistemi encoding)
- Form data encoding (Form data encoding)
- Console output encoding (Console çıktı encoding)

**Test Edilen Türkçe Karakterler:**
- Küçük harfler: ç, ğ, ı, ö, ş, ü
- Büyük harfler: Ç, Ğ, İ, Ö, Ş, Ü

## 🚀 Kurulum

### Gereksinimler

```bash
pip install pytest pytest-asyncio
```

### Test Dosyalarını İndirme

Test dosyaları `backend/tests/accessibility/` dizininde bulunur:

```
backend/tests/accessibility/
├── __init__.py
├── test_wcag_compliance.py
├── test_screen_reader_compatibility.py
├── test_keyboard_navigation.py
├── test_turkish_encoding.py
├── run_accessibility_tests.py
└── README.md
```

## 💻 Kullanım

### Tüm Testleri Çalıştırma

```bash
# Basit çalıştırma
python backend/tests/accessibility/run_accessibility_tests.py

# Verbose mode
python backend/tests/accessibility/run_accessibility_tests.py --verbose

# JSON rapor formatı
python backend/tests/accessibility/run_accessibility_tests.py --report-format json
```

### Tek Bir Modülü Çalıştırma

```bash
# WCAG compliance testleri
pytest backend/tests/accessibility/test_wcag_compliance.py -v

# Ekran okuyucu testleri
pytest backend/tests/accessibility/test_screen_reader_compatibility.py -v

# Klavye navigasyon testleri
pytest backend/tests/accessibility/test_keyboard_navigation.py -v

# Türkçe encoding testleri
pytest backend/tests/accessibility/test_turkish_encoding.py -v
```

### Belirli Bir Testi Çalıştırma

```bash
# WCAG 1.1.1 (Alt text) testi
pytest backend/tests/accessibility/test_wcag_compliance.py::test_wcag_1_1_1_non_text_content -v

# Klavye tab order testi
pytest backend/tests/accessibility/test_keyboard_navigation.py::test_tab_order_logical -v
```

## 📊 Test Kapsamı

### WCAG 2.1 Level AA Testleri

| Kılavuz | Seviye | Test Durumu | Açıklama |
|---------|--------|-------------|----------|
| 1.1.1 | A | ✅ | Non-text Content (Alt text) |
| 1.4.3 | AA | ✅ | Contrast (Minimum) |
| 2.1.1 | A | ✅ | Keyboard |
| 2.1.2 | A | ✅ | No Keyboard Trap |
| 2.4.1 | A | ✅ | Bypass Blocks |
| 2.4.2 | A | ✅ | Page Titled |
| 2.4.3 | A | ✅ | Focus Order |
| 2.4.7 | AA | ✅ | Focus Visible |
| 3.1.1 | A | ✅ | Language of Page |
| 3.1.2 | AA | ✅ | Language of Parts |
| 4.1.2 | A | ✅ | Name, Role, Value |
| 4.1.3 | AA | ✅ | Status Messages |

### Ekran Okuyucu Testleri

| Test | Durum | Açıklama |
|------|-------|----------|
| ARIA Live Regions | ✅ | Dinamik içerik güncellemeleri |
| Form Field Descriptions | ✅ | Form alanı etiketleri |
| Heading Structure | ✅ | Başlık hiyerarşisi |
| Landmark Regions | ✅ | Sayfa yapısı navigasyonu |
| Button/Link Labels | ✅ | Buton ve link etiketleri |
| Table Accessibility | ✅ | Tablo erişilebilirliği |
| Math Formula | ✅ | Matematik formül erişilebilirliği |
| Status Messages | ✅ | Durum mesajları |

### Klavye Navigasyon Testleri

| Test | Durum | Açıklama |
|------|-------|----------|
| Tab Order | ✅ | Mantıklı tab sırası |
| No Keyboard Trap | ✅ | Klavye tuzağı yok |
| Focus Indicators | ✅ | Görünür odak göstergeleri |
| Skip Links | ✅ | İçeriğe atla linkleri |
| Interactive Elements | ✅ | Tüm elementler erişilebilir |
| Form Navigation | ✅ | Form klavye navigasyonu |
| Modal Interaction | ✅ | Modal klavye etkileşimi |
| Custom Controls | ✅ | Özel kontrol desteği |

### Türkçe Encoding Testleri

| Test | Durum | Açıklama |
|------|-------|----------|
| UTF-8 Encoding | ✅ | Temel UTF-8 encoding |
| HTML Meta Charset | ✅ | HTML charset tanımı |
| Database Encoding | ✅ | Veritabanı UTF-8 |
| API Response | ✅ | API yanıt encoding |
| URL Encoding | ✅ | URL percent-encoding |
| File System | ✅ | Dosya adı encoding |
| Form Data | ✅ | Form data encoding |
| Console Output | ✅ | Console çıktı encoding |

## 📈 Raporlama

### Rapor Formatları

#### 1. Text Raporu (Varsayılan)

```bash
python run_accessibility_tests.py
```

Çıktı: `accessibility_report_YYYYMMDD_HHMMSS.txt`

Örnek rapor:
```
================================================================================
ACCESSIBILITY TEST SUITE - FINAL REPORT
================================================================================

Test Tarihi: 2025-10-04T15:30:00

Toplam Test: 45
Başarılı: 43 ✓
Başarısız: 2 ✗
Atlanan: 0 ⊘

Başarı Oranı: 95.6%

--------------------------------------------------------------------------------
Modül Bazında Sonuçlar:
--------------------------------------------------------------------------------

test_wcag_compliance.py: ✓ BAŞARILI
  Toplam: 12, Başarılı: 12, Başarısız: 0

test_screen_reader_compatibility.py: ✓ BAŞARILI
  Toplam: 11, Başarılı: 11, Başarısız: 0

test_keyboard_navigation.py: ✗ BAŞARISIZ
  Toplam: 10, Başarılı: 8, Başarısız: 2

test_turkish_encoding.py: ✓ BAŞARILI
  Toplam: 12, Başarılı: 12, Başarısız: 0

================================================================================
WCAG 2.1 Level AA Uyumluluk Durumu
================================================================================

✓ Platform WCAG 2.1 Level AA standartlarına UYUMLU

================================================================================
```

#### 2. JSON Raporu

```bash
python run_accessibility_tests.py --report-format json
```

Çıktı: `accessibility_report_YYYYMMDD_HHMMSS.json`

### Rapor İçeriği

Her rapor şunları içerir:
- Toplam test sayısı
- Başarılı/başarısız/atlanan test sayıları
- Modül bazında detaylı sonuçlar
- WCAG 2.1 Level AA uyumluluk durumu
- Ekran okuyucu uyumluluk durumu
- Klavye erişilebilirlik durumu
- Türkçe karakter destek durumu
- Başarısız testler için öneriler

## 📚 Standartlar ve Referanslar

### WCAG 2.1 Guidelines

- [WCAG 2.1 Official Documentation](https://www.w3.org/WAI/WCAG21/quickref/)
- [Understanding WCAG 2.1](https://www.w3.org/WAI/WCAG21/Understanding/)
- [How to Meet WCAG (Quick Reference)](https://www.w3.org/WAI/WCAG21/quickref/)

### ARIA Specifications

- [WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)

### Ekran Okuyucu Kaynakları

- [NVDA User Guide](https://www.nvaccess.org/files/nvda/documentation/userGuide.html)
- [JAWS Documentation](https://www.freedomscientific.com/training/jaws/)
- [VoiceOver User Guide](https://support.apple.com/guide/voiceover/welcome/mac)

### Türkçe Dil Desteği

- [UTF-8 Encoding](https://en.wikipedia.org/wiki/UTF-8)
- [Turkish Alphabet](https://en.wikipedia.org/wiki/Turkish_alphabet)

## 🔧 Sorun Giderme

### Test Başarısız Olursa

1. **WCAG Testleri Başarısız:**
   - HTML içeriğini kontrol edin
   - Alt text'lerin mevcut olduğundan emin olun
   - Kontrast oranlarını kontrol edin
   - ARIA etiketlerini ekleyin

2. **Ekran Okuyucu Testleri Başarısız:**
   - ARIA live regions ekleyin
   - Form field labels ekleyin
   - Heading hiyerarşisini düzeltin
   - Landmark regions ekleyin

3. **Klavye Navigasyon Testleri Başarısız:**
   - Tab order'ı kontrol edin
   - Focus indicators ekleyin
   - Skip links ekleyin
   - Modal keyboard trap'i düzeltin

4. **Türkçe Encoding Testleri Başarısız:**
   - UTF-8 encoding kullanın
   - HTML meta charset ekleyin
   - Veritabanı charset'ini kontrol edin
   - API response encoding'ini düzeltin

### Yaygın Hatalar

#### 1. Missing Alt Text
```html
<!-- Yanlış -->
<img src="exam.jpg">

<!-- Doğru -->
<img src="exam.jpg" alt="TYT Matematik Sınavı">
```

#### 2. Poor Contrast
```css
/* Yanlış - 2.5:1 kontrast */
color: #999999;
background: #FFFFFF;

/* Doğru - 4.5:1+ kontrast */
color: #666666;
background: #FFFFFF;
```

#### 3. Missing ARIA Labels
```html
<!-- Yanlış -->
<button onclick="submit()">→</button>

<!-- Doğru -->
<button onclick="submit()" aria-label="Sonraki soru">→</button>
```

#### 4. Keyboard Trap
```javascript
// Yanlış - Modal'dan çıkış yok
modal.addEventListener('keydown', (e) => {
  e.preventDefault();
});

// Doğru - Escape ile çıkış
modal.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal();
  }
});
```

## 🎯 Hedefler ve Metrikler

### Minimum Gereksinimler

- ✅ WCAG 2.1 Level AA: **100% uyumluluk**
- ✅ Ekran Okuyucu: **85%+ uyumluluk**
- ✅ Klavye Navigasyon: **90%+ uyumluluk**
- ✅ Türkçe Encoding: **95%+ uyumluluk**

### Başarı Kriterleri

Platformun erişilebilir sayılması için:
- Tüm WCAG 2.1 Level AA testleri geçmeli
- Ekran okuyucu testlerinin en az %85'i geçmeli
- Klavye navigasyon testlerinin en az %90'ı geçmeli
- Türkçe encoding testlerinin en az %95'i geçmeli

## 📝 Katkıda Bulunma

Yeni erişilebilirlik testleri eklemek için:

1. İlgili test modülüne yeni test fonksiyonu ekleyin
2. Test fonksiyonunu `@pytest.mark.asyncio` ile işaretleyin
3. Açıklayıcı docstring ekleyin
4. Test'i çalıştırın ve doğrulayın
5. Dokümantasyonu güncelleyin

## 📞 Destek

Sorularınız için:
- GitHub Issues: [Proje Repository]
- Email: [Destek Email]
- Dokümantasyon: Bu README dosyası

## 📄 Lisans

Bu test suite, Teknofest 2025 Eğitim Eylemci Platformu'nun bir parçasıdır.

---

**Son Güncelleme:** 04 Ekim 2025  
**Versiyon:** 1.0.0  
**Task:** 45 - Accessibility and Compliance Testing
