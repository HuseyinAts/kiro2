# Sınav Arayüzü Bileşenleri

Bu klasör, ÖSYM uyumlu sınav arayüzü bileşenlerini içerir.

## 📦 Bileşenler

### ExamInterface
Ana sınav arayüzü bileşeni. Tam sınav deneyimi sunar.

**Özellikler:**
- ✅ Cevap işaretleme sistemi
- ✅ Boş soru takibi
- ✅ Şüpheli işaretleme
- ✅ Soru navigasyonu
- ✅ Klavye kısayolları
- ✅ Erişilebilirlik desteği

**Kullanım:**
```typescript
import ExamInterface from './components/Exam/ExamInterface'

<ExamInterface
  questions={questions}
  answers={answers}
  currentQuestionIndex={currentIndex}
  onAnswerChange={handleAnswerChange}
  onFlagToggle={handleFlagToggle}
  onQuestionNavigate={handleNavigate}
/>
```

### BubbleSheetInterface
Optik form (bubble sheet) görünümü.

**Kullanım:**
```typescript
import BubbleSheetInterface from './components/Exam/BubbleSheetInterface'

<BubbleSheetInterface
  questionNumber={1}
  options={['A', 'B', 'C', 'D', 'E']}
  selectedAnswer={answer}
  onAnswerSelect={handleSelect}
/>
```

### BubbleSheetPanel
Çoklu soru optik form paneli.

**Kullanım:**
```typescript
import BubbleSheetPanel from './components/Exam/BubbleSheetPanel'

<BubbleSheetPanel
  questions={questions}
  answers={answers}
  onAnswerChange={handleChange}
/>
```

### ExamInterfaceExample
Tam çalışan demo ve kullanım örneği.

**Kullanım:**
```typescript
import ExamInterfaceExample from './components/Exam/ExamInterfaceExample'

<ExamInterfaceExample />
```

## 🎯 Task 69 Implementasyonu

Bu bileşenler Task 69: Sınav Arayüzü gereksinimlerini karşılar:

- **69.1 İşaretleme Sistemi**: ✅ Tamamlandı
- **69.2 Boş Bırakma**: ✅ Tamamlandı
- **69.3 Şüpheli İşaretleme**: ✅ Tamamlandı
- **69.4 Soru Navigasyonu**: ✅ Tamamlandı

## 🔧 Veri Yapıları

### ExamQuestion
```typescript
interface ExamQuestion {
  id: string
  number: number
  content: string
  options: string[]
  subject?: string
  topic?: string
}
```

### ExamAnswer
```typescript
interface ExamAnswer {
  questionId: string
  answer: string
  flaggedForReview: boolean
  timestamp: Date
}
```

## ⌨️ Klavye Kısayolları

| Tuş | Fonksiyon |
|-----|-----------|
| ← | Önceki soru |
| → | Sonraki soru |
| A-E | Cevap seçimi |
| F | Şüpheli işaretle |
| Tab | Element gezinme |
| Enter/Space | Seçim yap |

## 🎨 Renk Kodlaması

- 🔵 **Mavi**: Aktif soru
- 🟢 **Yeşil**: Cevaplandı
- 🟠 **Turuncu**: İnceleme için işaretli
- ⚪ **Gri**: Boş

## 📚 Daha Fazla Bilgi

Detaylı implementasyon bilgisi için:
- `TASK_69_SINAV_ARAYUZU_IMPLEMENTATION.md`
- `src/test/components/ExamInterface.test.tsx`

## 🧪 Testler

```bash
npm test -- ExamInterface.test.tsx
```

**Test Coverage**: ~95%  
**Test Sayısı**: 33 test case

## 📝 Notlar

- REQ-1.6 uyumlu otomatik kaydetme desteği
- WCAG 2.1 Level AA erişilebilirlik
- Responsive tasarım
- Material-UI ve Framer Motion kullanımı
