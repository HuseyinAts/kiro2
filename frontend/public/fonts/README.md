# Disleksi Dostu Fontlar

Bu dizin, disleksi desteği için özel fontları içerir.

## Gerekli Fontlar

### 1. OpenDyslexic (Açık Kaynak)
- **Lisans**: Creative Commons Attribution 3.0 Unported
- **İndirme**: https://opendyslexic.org/
- **Dosyalar**:
  - `OpenDyslexic-Regular.woff2`
  - `OpenDyslexic-Bold.woff2`
  - `OpenDyslexic-Italic.woff2`
  - `OpenDyslexic-BoldItalic.woff2`

### 2. Dyslexie (Ticari Lisans)
- **Lisans**: Ticari lisans gereklidir
- **Web Sitesi**: https://www.dyslexiefont.com/
- **Dosyalar**:
  - `Dyslexie-Regular.woff2`
  - `Dyslexie-Bold.woff2`

## Kurulum Talimatları

### OpenDyslexic Kurulumu

1. OpenDyslexic web sitesinden fontları indirin
2. TTF dosyalarını WOFF2 formatına dönüştürün (https://cloudconvert.com/ttf-to-woff2)
3. Dönüştürülen dosyaları bu dizine kopyalayın

### Dyslexie Kurulumu

1. Dyslexie lisansı satın alın (eğitim kurumları için indirim mevcut)
2. Lisanslı font dosyalarını indirin
3. Web font formatında (WOFF2) dosyaları bu dizine kopyalayın

## Font Yükleme Performansı

- **Hedef**: 500ms içinde font yükleme (REQ-50.1)
- **Format**: WOFF2 (en iyi sıkıştırma ve tarayıcı desteği)
- **Fallback**: System fonts (Arial, Verdana, Comic Sans MS)

## Kullanım

Fontlar `useDyslexiaSettings` hook'u tarafından otomatik olarak yüklenir:

```typescript
import { useDyslexiaSettings } from '@/hooks/useDyslexiaSettings';

const { settings, fontsLoaded } = useDyslexiaSettings();
```

## Test

Font yükleme durumunu test etmek için:

```bash
# Tarayıcı konsolunda
document.fonts.check('16px OpenDyslexic')
document.fonts.check('16px Dyslexie')
```

## Alternatif Fontlar

Eğer OpenDyslexic veya Dyslexie mevcut değilse, sistem otomatik olarak şu fontlara geri döner:

1. **Verdana**: Geniş harf aralığı, net görünüm
2. **Arial**: Yaygın kullanım, iyi okunabilirlik
3. **Comic Sans MS**: Disleksi dostu alternatif
4. **System Font**: Cihazın varsayılan fontu

## Lisans Uyarısı

⚠️ **Önemli**: Dyslexie fontu ticari bir üründür. Production ortamında kullanmadan önce geçerli bir lisans satın alınmalıdır.

OpenDyslexic açık kaynak ve ücretsizdir, ancak Creative Commons Attribution lisansı gerektirir.

## Kaynaklar

- [OpenDyslexic GitHub](https://github.com/antijingoist/opendyslexic)
- [Dyslexie Font](https://www.dyslexiefont.com/)
- [Web Font Best Practices](https://web.dev/font-best-practices/)
- [WOFF2 Browser Support](https://caniuse.com/woff2)
