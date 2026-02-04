# Optik Form (Bubble Sheet) Arayüzü

## Genel Bakış

Bu implementasyon, ÖSYM sınavlarında kullanılan optik form (bubble sheet) görünümünü sağlar. Öğrenciler, gerçek sınav deneyimine benzer şekilde cevaplarını daire içinde işaretleyebilirler.

## Gereksinim Karşılama

### REQ-1.1: TYT Sınav Formatı
- ✅ 120 soru, 120 dakika formatı desteklenir
- ✅ ÖSYM uyumlu optik form görünümü
- ✅ A, B, C, D, E seçenekleri

### REQ-1.6: Otomatik Kaydetme
- ✅ Her cevap değişikliğinde otomatik kaydetme tetiklenir
- ✅ 30 saniyede bir toplu kaydetme
- ✅ Bağlantı kesildiğinde veri kaybı önlenir

## Bileşenler

### 1. BubbleSheetInterface

Tek bir soru için optik form görünümü sağlar.

**Props:**
```typescript
interface BubbleSheetInterfaceProps {
  questionNumber: number          // Soru numarası
  options: string[]               // Seçenekler (örn: ['A', 'B', 'C', 'D', 'E'])
  selectedAnswer: string | null   // Seçili cevap
  onAnswerSelect: (answer: string) => void  // Cevap seçim callback
  disabled?: boolean              // Devre dışı bırakma
  showFeedback?: boolean          // Geri bildirim gösterme
  correctAnswer?: string          // Doğru cevap (feedback için)
  size?: 'small' | 'medium' | 'large'  // Bubble boyutu
}
```

**Özellikler:**
- ✅ Bubble tıklama ile cevap işaretleme
- ✅ Seçili bubble'a tekrar tıklayarak işareti kaldırma
- ✅ Görsel geri bildirim (animasyonlar, renkler)
- ✅ Klavye erişilebilirliği (Tab, Enter, Space)
- ✅ Responsive tasarım
- ✅ WCAG 2.1 Level AA uyumlu

**Kullanım:**
```tsx
import BubbleSheetInterface from './components/Exam/BubbleSheetInterface'

<BubbleSheetInterface
  questionNumber={1}
  options={['A', 'B', 'C', 'D', 'E']}
  selectedAnswer={selectedAnswer}
  onAnswerSelect={(answer) => setSelectedAnswer(answer)}
  size="medium"
/>
```

### 2. BubbleSheetPanel

Çoklu soru için tam sayfa optik form görünümü sağlar.

**Props:**
```typescript
interface BubbleSheetPanelProps {
  questions: Question[]           // Soru listesi
  answers: Record<string, string> // Cevaplar (questionId -> answer)
  onAnswerChange: (questionId: string, answer: string) => void
  currentQuestionIndex?: number   // Mevcut soru index'i
  onQuestionNavigate?: (index: number) => void  // Soru navigasyon callback
  disabled?: boolean              // Devre dışı bırakma
  showSubjects?: boolean          // Konuları gösterme
  columns?: 1 | 2 | 3 | 4        // Kolon sayısı
  size?: 'small' | 'medium' | 'large'  // Bubble boyutu
}
```

**Özellikler:**
- ✅ Tüm soruları tek sayfada gösterme
- ✅ Konulara göre gruplama
- ✅ İstatistik gösterimi (cevaplanan, boş, tamamlanma yüzdesi)
- ✅ Grid ve liste görünümü
- ✅ Boş soruları vurgulama
- ✅ Soru navigasyonu
- ✅ Bilgi dialog'u

**Kullanım:**
```tsx
import BubbleSheetPanel from './components/Exam/BubbleSheetPanel'

<BubbleSheetPanel
  questions={questions}
  answers={answers}
  onAnswerChange={(questionId, answer) => handleAnswerChange(questionId, answer)}
  currentQuestionIndex={currentIndex}
  onQuestionNavigate={(index) => setCurrentIndex(index)}
  showSubjects={true}
  columns={2}
  size="medium"
/>
```

## Görsel Geri Bildirim

### Bubble Durumları

1. **Boş (Unselected)**
   - Beyaz arka plan
   - Gri kenarlık
   - Hover efekti: Açık mavi arka plan

2. **Seçili (Selected)**
   - Mavi arka plan
   - Koyu mavi kenarlık
   - Beyaz metin
   - İçinde dolu daire ikonu
   - Gölge efekti

3. **Doğru Cevap (Correct - Feedback Mode)**
   - Yeşil arka plan
   - Koyu yeşil kenarlık
   - Beyaz metin
   - Başarı ikonu

4. **Yanlış Cevap (Wrong - Feedback Mode)**
   - Kırmızı arka plan
   - Koyu kırmızı kenarlık
   - Beyaz metin
   - Hata ikonu

### Animasyonlar

- **Seçim Animasyonu**: Bubble tıklandığında scale(1.2) animasyonu
- **Hover Animasyonu**: Mouse üzerine geldiğinde scale(1.05)
- **İşaret Animasyonu**: Seçili işareti fade-in/fade-out ile görünür

## Klavye Erişilebilirliği

### Desteklenen Tuşlar

- **Tab**: Bubble'lar arasında gezinme
- **Shift + Tab**: Geriye doğru gezinme
- **Enter**: Seçili bubble'ı işaretleme/işareti kaldırma
- **Space**: Seçili bubble'ı işaretleme/işareti kaldırma
- **Escape**: Dialog'ları kapatma

### ARIA Özellikleri

```html
<div role="radiogroup" aria-label="Soru 1 cevap seçenekleri">
  <div role="radio" aria-checked="true" aria-label="Şık A" tabindex="0">
    A
  </div>
  <!-- Diğer seçenekler -->
</div>
```

## Responsive Tasarım

### Breakpoint'ler

- **Mobile (< 600px)**: Tek kolon, küçük bubble'lar
- **Tablet (600px - 960px)**: 2 kolon, orta bubble'lar
- **Desktop (> 960px)**: 2-4 kolon, büyük bubble'lar

### Touch Optimizasyonu

- Minimum 48x48px dokunma alanı
- Bubble'lar arası yeterli boşluk
- Kaydırma desteği
- Pinch-to-zoom devre dışı

## Performans Optimizasyonu

### Render Optimizasyonu

```tsx
// useMemo ile hesaplanan değerler
const stats = useMemo(() => {
  // İstatistik hesaplamaları
}, [questions, answers])

// useCallback ile memoize edilmiş fonksiyonlar
const handleAnswerChange = useCallback((questionId, answer) => {
  // Cevap değiştirme
}, [])
```

### Lazy Loading

```tsx
// Büyük soru listeleri için virtualization
import { FixedSizeList } from 'react-window'

<FixedSizeList
  height={600}
  itemCount={questions.length}
  itemSize={80}
>
  {({ index, style }) => (
    <div style={style}>
      <BubbleSheetInterface {...questions[index]} />
    </div>
  )}
</FixedSizeList>
```

## Entegrasyon

### Mevcut OSYMExamInterface'e Entegrasyon

```tsx
import BubbleSheetInterface from './BubbleSheetInterface'

// OSYMExamInterface.tsx içinde
const [viewMode, setViewMode] = useState<'standard' | 'bubble'>('standard')

// Render kısmında
{viewMode === 'bubble' ? (
  <BubbleSheetInterface
    questionNumber={currentQuestion.number}
    options={['A', 'B', 'C', 'D', 'E']}
    selectedAnswer={answers[currentQuestion.id]}
    onAnswerSelect={(answer) => handleAnswerSave(answer)}
  />
) : (
  // Mevcut RadioGroup implementasyonu
)}
```

### Otomatik Kaydetme Entegrasyonu

```tsx
import useAutoSave from '../../hooks/useAutoSave'

const autoSave = useAutoSave({
  sessionId,
  enabled: true,
  interval: 30000, // 30 saniye
  onSave: (success, error) => {
    if (success) {
      setSaveStatus('saved')
    } else {
      setSaveStatus('error')
    }
  }
})

// Cevap değiştiğinde
const handleAnswerSelect = (answer: string) => {
  // Optimistic update
  setAnswers(prev => ({ ...prev, [questionId]: answer }))
  
  // Otomatik kaydetme kuyruğuna ekle
  autoSave.queueSave({
    question_id: questionId,
    selected_answer: answer
  })
}
```

## Test Coverage

### Unit Tests

```bash
npm test -- BubbleSheetInterface.test.tsx
```

**Test Senaryoları:**
- ✅ Temel render
- ✅ Cevap işaretleme (mark)
- ✅ İşareti kaldırma (unmark)
- ✅ Görsel geri bildirim
- ✅ Klavye erişilebilirliği
- ✅ Disabled durumu
- ✅ Boyut seçenekleri
- ✅ Çoklu soru paneli
- ✅ İstatistik hesaplama
- ✅ Görünüm modu değiştirme

### Integration Tests

```bash
npm test -- ExamIntegration.test.tsx
```

**Test Senaryoları:**
- ✅ Sınav başlatma ve optik form görünümü
- ✅ Cevap kaydetme ve otomatik kaydetme
- ✅ Soru navigasyonu
- ✅ Sınav tamamlama

## Tarayıcı Desteği

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile Safari (iOS 14+)
- ✅ Chrome Mobile (Android 10+)

## Bilinen Sınırlamalar

1. **Çok Fazla Soru**: 1000+ soru için virtualization gerekebilir
2. **Eski Tarayıcılar**: IE11 desteklenmez
3. **Düşük Bant Genişliği**: Animasyonlar yavaşlayabilir

## Gelecek Geliştirmeler

- [ ] Sürükle-bırak ile cevap işaretleme
- [ ] Ses geri bildirimi (accessibility)
- [ ] Çoklu seçim desteği (bazı sınav tipleri için)
- [ ] Optik form yazdırma özelliği
- [ ] Offline mod için IndexedDB entegrasyonu
- [ ] Gerçek zamanlı senkronizasyon (WebSocket)

## Katkıda Bulunma

Lütfen değişikliklerinizi yapmadan önce testleri çalıştırın:

```bash
npm test
npm run lint
npm run type-check
```

## Lisans

Bu proje Teknofest 2025 Eğitim Eylemci Platformu'nun bir parçasıdır.

## İletişim

Sorularınız için: [email protected]

---

**Son Güncelleme**: 21 Ekim 2025
**Versiyon**: 1.0.0
**Durum**: ✅ Production Ready
