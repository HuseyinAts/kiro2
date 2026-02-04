# Diskalkuli Desteği - Görsel Matematik Temsilleri

Diskalkuli (matematik öğrenme güçlüğü) yaşayan öğrenciler için özel olarak tasarlanmış interaktif görsel matematik araçları.

## 📋 Gereksinimler

Bu modül aşağıdaki gereksinimleri karşılar:
- **REQ-51.1 - REQ-51.5**: Sayı Blokları (Base-10 Sistemi)
- **REQ-51.6 - REQ-51.10**: Kesir Çubukları
- **REQ-51.11 - REQ-51.15**: 3D Geometrik Şekiller
- **REQ-51.16 - REQ-51.20**: Grafik Çizim Aracı

## 🎯 Özellikler

### 1. NumberBlocks (Sayı Blokları)
Base-10 blok sistemi ile sayıları görselleştirme:
- ✅ Binler, yüzler, onlar, birler basamakları
- ✅ Farklı renk ve boyutlarda bloklar
- ✅ Drag & drop ile interaktif manipülasyon
- ✅ Toplama/çıkarma animasyonları
- ✅ Otomatik blok temsili

```tsx
import { NumberBlocks } from '@/components/Accessibility/Dyscalculia';

<NumberBlocks 
  initialValue={1234}
  maxValue={9999}
  showAnimation={true}
  onValueChange={(value) => console.log(value)}
/>
```

### 2. FractionBars (Kesir Çubukları)
Kesir kavramını görselleştirme:
- ✅ Renkli kesir çubukları
- ✅ Denk kesir görselleştirme
- ✅ İki kesri karşılaştırma
- ✅ Kesir işlemleri (toplama, çıkarma, çarpma, bölme)
- ✅ Gerçek zamanlı ondalık değer gösterimi

```tsx
import { FractionBars } from '@/components/Accessibility/Dyscalculia';

<FractionBars 
  initialFraction={{ numerator: 1, denominator: 2 }}
  showEquivalent={true}
  showComparison={true}
/>
```

### 3. GeometricShapes3D (3D Geometrik Şekiller)
3D şekilleri görselleştirme ve manipülasyon:
- ✅ Küp, küre, silindir, koni, piramit
- ✅ 360 derece rotasyon (mouse ile sürükleme)
- ✅ Otomatik döndürme modu
- ✅ Hacim ve yüzey alanı hesaplamaları
- ✅ Şekil açılımı (net) gösterimi

```tsx
import { GeometricShapes3D } from '@/components/Accessibility/Dyscalculia';

<GeometricShapes3D 
  initialShape="cube"
  initialSize={100}
  showMeasurements={true}
  showNet={true}
/>
```

### 4. GraphPlotter (Grafik Çizim)
İnteraktif fonksiyon grafik çizimi:
- ✅ Gerçek zamanlı grafik çizimi
- ✅ Zoom ve pan özellikleri
- ✅ Nokta seçimi ve koordinat gösterimi
- ✅ Renkli kodlanmış eksenler (X: kırmızı, Y: mavi)
- ✅ Yaygın fonksiyonlar için hızlı seçim

```tsx
import { GraphPlotter } from '@/components/Accessibility/Dyscalculia';

<GraphPlotter 
  initialFunction="x^2"
  xMin={-10}
  xMax={10}
  yMin={-10}
  yMax={10}
/>
```

## 🎨 Desteklenen Fonksiyonlar (GraphPlotter)

- **Temel**: `x`, `x^2`, `x^3`
- **Karekök**: `sqrt(x)`
- **Trigonometrik**: `sin(x)`, `cos(x)`, `tan(x)`
- **Üstel**: `exp(x)`, `log(x)`
- **Sabitler**: `pi`, `e`
- **Operatörler**: `+`, `-`, `*`, `/`, `^`

## 🎯 Kullanım Senaryoları

### Senaryo 1: Basamak Değeri Öğretimi
```tsx
<NumberBlocks 
  initialValue={0}
  showAnimation={true}
  onValueChange={(value) => {
    console.log(`Öğrenci ${value} sayısını oluşturdu`);
  }}
/>
```

### Senaryo 2: Kesir Karşılaştırma
```tsx
<FractionBars 
  initialFraction={{ numerator: 1, denominator: 2 }}
  showEquivalent={true}
  showComparison={true}
/>
```

### Senaryo 3: 3D Geometri Keşfi
```tsx
<GeometricShapes3D 
  initialShape="pyramid"
  showMeasurements={true}
  showNet={true}
/>
```

### Senaryo 4: Fonksiyon Analizi
```tsx
<GraphPlotter 
  initialFunction="sin(x)"
  onFunctionChange={(func) => {
    console.log(`Yeni fonksiyon: ${func}`);
  }}
/>
```

## ♿ Erişilebilirlik

Tüm component'ler WCAG 2.1 Level AA standartlarına uygundur:

- ✅ Klavye navigasyonu desteği
- ✅ ARIA etiketleri
- ✅ Ekran okuyucu uyumluluğu
- ✅ Yüksek kontrast mod desteği
- ✅ Focus göstergeleri
- ✅ Responsive tasarım

## 🎨 Renk Kodlama

### NumberBlocks
- **Binler**: Kırmızı (#FF6B6B) - 120px
- **Yüzler**: Turkuaz (#4ECDC4) - 90px
- **Onlar**: Sarı (#FFE66D) - 60px
- **Birler**: Yeşil (#95E1D3) - 30px

### GraphPlotter
- **X Ekseni**: Kırmızı (#FF6B6B)
- **Y Ekseni**: Mavi (#2196F3)
- **Fonksiyon**: Yeşil (#4CAF50)

## 📱 Responsive Tasarım

Tüm component'ler mobil cihazlarda optimize edilmiştir:
- Tablet: 768px - 1024px
- Mobil: < 768px
- Desktop: > 1024px

## 🧪 Test Edilmiş Tarayıcılar

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 📊 Performans

- **3D Render**: < 16ms (60 FPS)
- **Grafik Çizimi**: < 100ms
- **Animasyon**: Smooth 60 FPS
- **İnteraktif Yanıt**: < 50ms

## 🔧 Teknoloji Stack

- **React**: 18+
- **TypeScript**: 5+
- **CSS3**: Transforms, Animations
- **Canvas API**: Grafik çizimi için
- **CSS 3D Transforms**: 3D şekiller için

## 📝 Notlar

- 3D şekiller için Three.js entegrasyonu gelecekte eklenebilir
- Grafik çizim için daha gelişmiş matematik kütüphaneleri (Math.js) eklenebilir
- Tüm component'ler bağımsız olarak kullanılabilir
- Props ile tam özelleştirme desteği

## 🤝 Katkıda Bulunma

Bu component'leri geliştirmek için:
1. Yeni özellik ekleyin
2. Test coverage'ı artırın
3. Erişilebilirlik iyileştirmeleri yapın
4. Performans optimizasyonları ekleyin

## 📄 Lisans

Bu proje Teknofest 2025 Eğitim Eylemci Platformu kapsamında geliştirilmiştir.

## 🔗 İlgili Dökümanlar

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Diskalkuli Hakkında](https://www.understood.org/en/articles/what-is-dyscalculia)
- [Görsel Matematik Öğretimi](https://www.nctm.org/visual-mathematics/)
