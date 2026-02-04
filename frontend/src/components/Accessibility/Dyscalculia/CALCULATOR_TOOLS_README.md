# Hesap Makinesi ve Araçlar (Calculator and Tools)

## Genel Bakış

Bu modül, diskalkuli (matematik öğrenme güçlüğü) olan öğrenciler için özel olarak tasarlanmış hesap makinesi ve geometri araçlarını içerir. Tüm bileşenler WCAG 2.1 Level AA erişilebilirlik standartlarına uygundur.

**Gereksinimler:** REQ-51.41 - REQ-51.60

## Bileşenler

### 1. ScientificCalculator (Bilimsel Hesap Makinesi)

**Dosyalar:**
- `ScientificCalculator.tsx`
- `ScientificCalculator.css`

**Özellikler:**
- ✅ Temel aritmetik işlemler (+, -, *, /)
- ✅ Bilimsel fonksiyonlar (sin, cos, tan, log, ln, sqrt, pow)
- ✅ Sabitler (π, e)
- ✅ Bellek işlemleri (MC, MR, MS, M+, M-)
- ✅ İşlem geçmişi (son 50 işlem)
- ✅ Derece/Radyan modu
- ✅ Tam klavye desteği
- ✅ Faktöriyel, mutlak değer, ters fonksiyonlar

**Klavye Kısayolları:**
- `0-9`: Sayılar
- `+`, `-`, `*`, `/`: İşlemler
- `Enter` veya `=`: Hesapla
- `Esc`: Temizle
- `Backspace`: Sil
- `.`: Ondalık nokta

**Kullanım:**
```tsx
import { ScientificCalculator } from '@/components/Accessibility/Dyscalculia';

function MyComponent() {
  return <ScientificCalculator />;
}
```

---

### 2. GraphingCalculator (Grafik Hesap Makinesi)

**Dosyalar:**
- `GraphingCalculator.tsx`
- `GraphingCalculator.css`

**Özellikler:**
- ✅ Fonksiyon grafikleri (y = f(x))
- ✅ Birden fazla fonksiyon desteği (farklı renkler)
- ✅ Değer tablosu oluşturma
- ✅ Trace (iz sürme) özelliği
- ✅ Zoom in/out
- ✅ Eksen ayarları (X ve Y aralıkları)
- ✅ Grid görünürlüğü
- ✅ Fonksiyon görünürlük kontrolü

**Desteklenen Fonksiyonlar:**
- Üs alma: `x^2`, `x^3`
- Trigonometrik: `sin(x)`, `cos(x)`, `tan(x)`
- Karekök: `sqrt(x)`
- Mutlak değer: `abs(x)`
- Logaritma: `log(x)`, `ln(x)`
- Sabitler: `pi`, `e`

**Kullanım:**
```tsx
import { GraphingCalculator } from '@/components/Accessibility/Dyscalculia';

function MyComponent() {
  return <GraphingCalculator />;
}
```

**Örnek Fonksiyonlar:**
- `x^2` - Parabol
- `sin(x)` - Sinüs dalgası
- `2*x+1` - Doğrusal fonksiyon
- `sqrt(x)` - Karekök fonksiyonu

---

### 3. GeometryTools (Geometri Araçları)

**Dosyalar:**
- `GeometryTools.tsx`
- `GeometryTools.css`

**Özellikler:**
- ✅ Sanal cetvel (cm ve inch)
- ✅ İletki (açı ölçme, 0-180°)
- ✅ Pergel (daire çizme)
- ✅ Şekil çizim araçları:
  - Çizgi
  - Daire
  - Dikdörtgen
  - Üçgen
  - Çokgen
- ✅ Otomatik ölçüm hesaplama
- ✅ Grid sistemi
- ✅ Geri alma özelliği

**Kullanım:**
```tsx
import { GeometryTools } from '@/components/Accessibility/Dyscalculia';

function MyComponent() {
  return <GeometryTools />;
}
```

**Nasıl Kullanılır:**
- **Cetvel:** Açı ayarlayıcı ile döndürün
- **İletki:** Açı ölçmek için kullanın
- **Çizgi/Dikdörtgen/Daire:** Tıklayıp sürükleyin
- **Üçgen:** 3 nokta tıklayın
- **Çokgen:** Noktaları tıklayın, bitirmek için çift tıklayın

**Ölçümler:**
- Çizgi uzunluğu (cm/inch)
- Daire yarıçapı ve alanı
- Dikdörtgen genişlik, yükseklik ve alan
- Üçgen alanı

---

### 4. FormulaEditor (Formül Editörü)

**Dosyalar:**
- `FormulaEditor.tsx`
- `FormulaEditor.css`

**Özellikler:**
- ✅ LaTeX formatında formül girişi
- ✅ Hızlı ekleme butonları (kesir, üs, karekök, vb.)
- ✅ Formül kütüphanesi (25+ şablon)
- ✅ Kategori filtreleme:
  - Temel
  - Cebir
  - Geometri
  - Trigonometri
  - Kalkülüs
  - Matris
  - İstatistik
- ✅ Formül kaydetme ve yükleme
- ✅ LocalStorage entegrasyonu
- ✅ LaTeX komutları rehberi

**Kullanım:**
```tsx
import { FormulaEditor } from '@/components/Accessibility/Dyscalculia';

function MyComponent() {
  return <FormulaEditor />;
}
```

**Örnek LaTeX Komutları:**
- `\frac{a}{b}` - Kesir
- `x^{n}` - Üs
- `\sqrt{x}` - Karekök
- `\sum_{i=1}^{n}` - Toplam
- `\int_{a}^{b}` - İntegral
- `\alpha, \beta, \theta` - Yunan harfleri

**Popüler Formül Şablonları:**
- İkinci derece denklem: `ax^2 + bx + c = 0`
- Çözüm formülü: `x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}`
- Pisagor teoremi: `a^2 + b^2 = c^2`
- Daire alanı: `A = \pi r^2`

---

## Erişilebilirlik Özellikleri

Tüm bileşenler aşağıdaki erişilebilirlik özelliklerini içerir:

### WCAG 2.1 Level AA Uyumluluğu
- ✅ Klavye navigasyonu (Tab, Enter, Space, Arrow keys)
- ✅ ARIA etiketleri ve roller
- ✅ Yüksek kontrast desteği
- ✅ Ekran okuyucu uyumluluğu
- ✅ Focus göstergeleri (3px sarı outline)
- ✅ Anlamlı hata mesajları

### Görsel Tasarım
- ✅ Minimum 4.5:1 kontrast oranı
- ✅ Büyük, tıklanabilir hedefler (minimum 44x44px)
- ✅ Net, okunabilir fontlar
- ✅ Renk körü dostu renk paleti

### Responsive Tasarım
- ✅ Mobil cihaz desteği (320px+)
- ✅ Tablet optimizasyonu
- ✅ Desktop tam özellik desteği

### Karanlık Mod
- ✅ Otomatik karanlık mod algılama
- ✅ Yüksek kontrast karanlık tema
- ✅ Göz yorgunluğunu azaltma

### Azaltılmış Hareket
- ✅ `prefers-reduced-motion` desteği
- ✅ Animasyonları devre dışı bırakma
- ✅ Statik geçişler

---

## Teknik Detaylar

### Teknoloji Stack
- **React 18+** - UI framework
- **TypeScript** - Type safety
- **CSS3** - Styling (CSS Grid, Flexbox)
- **HTML5 Canvas** - Grafik çizimi (GraphingCalculator, GeometryTools)

### Tarayıcı Desteği
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Performans
- ⚡ Hafif bileşenler (< 50KB her biri)
- ⚡ Lazy loading desteği
- ⚡ Optimize edilmiş render döngüleri
- ⚡ LocalStorage caching

---

## Test Edilmiş Senaryolar

### Fonksiyonel Testler
- ✅ Tüm hesap makinesi işlemleri
- ✅ Grafik çizimi ve zoom
- ✅ Geometri araçları ile şekil çizimi
- ✅ Formül kaydetme ve yükleme

### Erişilebilirlik Testler
- ✅ NVDA ekran okuyucu (Windows)
- ✅ JAWS ekran okuyucu (Windows)
- ✅ VoiceOver (macOS, iOS)
- ✅ TalkBack (Android)
- ✅ Klavye-only navigasyon

### Cihaz Testleri
- ✅ iPhone (Safari)
- ✅ Android (Chrome)
- ✅ iPad (Safari)
- ✅ Windows (Chrome, Edge, Firefox)
- ✅ macOS (Safari, Chrome)

---

## Gelecek Geliştirmeler

### Planlanan Özellikler
- [ ] MathJax/KaTeX entegrasyonu (FormulaEditor için gerçek LaTeX render)
- [ ] 3D geometri araçları
- [ ] Grafik hesap makinesinde türev/integral hesaplama
- [ ] Formül paylaşma özelliği
- [ ] Sesli komut desteği
- [ ] Dokunmatik ekran jestleri

### Bilinen Sınırlamalar
- FormulaEditor şu anda LaTeX kodunu text olarak gösteriyor (MathJax entegrasyonu gerekli)
- GraphingCalculator karmaşık fonksiyonlarda performans düşüşü olabilir
- GeometryTools 3D şekilleri desteklemiyor

---

## Katkıda Bulunma

Bu bileşenleri geliştirmek için:

1. Yeni özellik eklerken erişilebilirlik standartlarına uyun
2. WCAG 2.1 Level AA gereksinimlerini kontrol edin
3. Tüm bileşenlerde klavye navigasyonunu test edin
4. Responsive tasarımı doğrulayın
5. Ekran okuyucu uyumluluğunu test edin

---

## Lisans

Bu bileşenler Teknofest 2025 Eğitim Eylemci Platformu'nun bir parçasıdır.

---

## İletişim

Sorularınız için:
- GitHub Issues
- Proje dokümantasyonu
- Geliştirici ekibi

---

**Son Güncelleme:** 24 Ekim 2025
**Versiyon:** 1.0.0
**Durum:** ✅ Production Ready
