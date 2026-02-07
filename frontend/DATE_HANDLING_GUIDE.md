# Date Handling Guide - KIRO2 Frontend

## Overview

Bu doküman KIRO2 platformunda tarih ve zaman verilerinin nasıl işleneceğini açıklar.

## 🎯 Temel Prensipler

### 1. Backend ↔ Frontend İletişimi

**Backend (FastAPI/Python)**:
- Backend tüm tarihleri **ISO 8601 formatında** döner
- Format: `"2024-06-15T09:00:00Z"` (UTC timezone)
- Python `datetime` objeleri otomatik olarak ISO 8601 string'e çevrilir

**Frontend (React/TypeScript)**:
- TypeScript interface'lerinde tarih alanları **`string` türünde** tanımlanır
- JSDoc ile ISO 8601 formatı belirtilir
- `dayjs` kütüphanesi ile parse edilir

### 2. Date Parsing ve Formatting

#### ✅ DOĞRU Kullanım

```typescript
import { dateUtils } from '@/utils/dateUtils'

// Backend'den gelen tarih
interface ExamSession {
  /** Sınav başlangıç zamanı (ISO 8601: "2024-06-15T09:00:00Z") */
  started_at: string
}

const session: ExamSession = await api.getExamSession()

// Parse ve format
const startTime = dateUtils.format(session.started_at, 'DD/MM/YYYY HH:mm')
// Output: "15/06/2024 09:00"

const relativeTime = dateUtils.fromNow(session.started_at)
// Output: "2 saat önce"
```

#### ❌ YANLIŞ Kullanım

```typescript
// ❌ Date objesi olarak tanımlama
interface ExamSession {
  started_at: Date  // YANLIŞ - Backend string döner!
}

// ❌ Manuel string parsing
const date = new Date(session.started_at.split('T')[0])  // YANLIŞ

// ❌ Locale-dependent formatting
const date = new Date(session.started_at).toLocaleDateString()  // YANLIŞ
```

## 📚 dateUtils API Referansı

### Temel Fonksiyonlar

```typescript
import { dateUtils } from '@/utils/dateUtils'

// 1. Format - Tarihi istenen formatta string'e çevir
dateUtils.format(date, 'DD/MM/YYYY HH:mm')  // "15/06/2024 14:30"
dateUtils.format(date, 'DD MMMM YYYY')      // "15 Haziran 2024"
dateUtils.formatDate(date)                   // "15/06/2024" (shortcut)
dateUtils.formatTime(date)                   // "14:30:00" (shortcut)

// 2. Relative Time - "X önce" formatında
dateUtils.fromNow(date)           // "2 saat önce"
dateUtils.toNow(futureDate)       // "3 gün içinde"
dateUtils.calendar(date)          // "Bugün 14:30", "Dün 10:00", vs.

// 3. Comparison - Tarih karşılaştırma
dateUtils.isBefore(date1, date2)  // boolean
dateUtils.isAfter(date1, date2)   // boolean
dateUtils.isSame(date1, date2)    // boolean
dateUtils.isBetween(date, start, end)  // boolean

// 4. Duration - Süre hesaplama
dateUtils.diff(date1, date2, 'hours')  // number
dateUtils.formatDuration(milliseconds) // "2 saat 30 dakika"

// 5. Date Manipulation
dateUtils.add(date, 7, 'days')         // Dayjs
dateUtils.subtract(date, 2, 'hours')   // Dayjs
dateUtils.startOf(date, 'day')         // Günün başı (00:00:00)
dateUtils.endOf(date, 'day')           // Günün sonu (23:59:59)
```

### Exam-Specific Helpers

```typescript
// Sınav tarihi formatla
const examDate = dateUtils.format(session.started_at, 'DD/MM/YYYY HH:mm')
// "15/06/2024 09:00"

// Kalan süreyi hesapla
const now = dateUtils.now()
const examStart = dateUtils.parseISO(session.started_at)
const remainingMinutes = dateUtils.diff(examStart, now, 'minutes')

// Sınav süresi formatla
const durationSeconds = session.duration_minutes * 60
const formattedDuration = dateUtils.formatDuration(durationSeconds * 1000)
// "135 dakika" veya "2 saat 15 dakika"
```

## 🔍 TypeScript Interface Örnekleri

### Sınav Sistemi

```typescript
export interface ExamSessionResponse {
  session_id: string
  /** Sınav başlangıç zamanı (ISO 8601: "2024-06-15T09:00:00Z") */
  started_at?: string
  /** Sınav bitiş zamanı (ISO 8601: "2024-06-15T11:30:00Z") */
  completed_at?: string
}
```

### Parent Dashboard

```typescript
export interface ChildPerformance {
  child_name: string
  /** Son sınav tarihi (ISO 8601: "2024-06-15T09:00:00Z") */
  last_exam_date?: string
}

export interface ParentNotification {
  message: string
  /** Bildirim oluşturulma zamanı (ISO 8601: "2024-06-15T10:30:00Z") */
  created_at: string
  /** Okunma zamanı (ISO 8601: "2024-06-15T11:00:00Z") */
  read_at?: string
}
```

### Batch Jobs (Admin)

```typescript
interface BatchJob {
  task_id: string
  /** Görev oluşturulma zamanı (ISO 8601: "2024-06-15T10:00:00Z") */
  created_at: string
  /** İşleme başlama zamanı (ISO 8601: "2024-06-15T10:05:00Z") */
  started_at?: string
  /** Tamamlanma zamanı (ISO 8601: "2024-06-15T10:30:00Z") */
  completed_at?: string
}
```

## 🎨 UI Gösterim Örnekleri

### Exam Timer Display

```tsx
import { dateUtils } from '@/utils/dateUtils'

function ExamTimer({ session }: { session: ExamSessionResponse }) {
  const startTime = session.started_at
    ? dateUtils.format(session.started_at, 'HH:mm')
    : 'Başlamadı'

  const elapsedTime = session.started_at
    ? dateUtils.fromNow(session.started_at)
    : 'Beklemede'

  return (
    <div>
      <span>Başlangıç: {startTime}</span>
      <span>Geçen: {elapsedTime}</span>
    </div>
  )
}
```

### Parent Notification List

```tsx
function NotificationItem({ notification }: { notification: ParentNotification }) {
  const timeAgo = dateUtils.fromNow(notification.created_at)

  return (
    <div>
      <p>{notification.message}</p>
      <small>{timeAgo}</small>
    </div>
  )
}
```

### Batch Job Progress

```tsx
function BatchJobRow({ job }: { job: BatchJob }) {
  const createdAt = dateUtils.formatDateWithDay(job.created_at)
  const duration = job.started_at && job.completed_at
    ? dateUtils.formatDistance(job.started_at, job.completed_at)
    : 'İşlemde'

  return (
    <tr>
      <td>{job.task_id}</td>
      <td>{createdAt}</td>
      <td>{duration}</td>
    </tr>
  )
}
```

## 🛡️ Type Safety Checklist

### ✅ Yeni Interface Oluştururken

- [ ] Tarih alanları `string` türünde mi?
- [ ] JSDoc ile ISO 8601 formatı belirtildi mi?
- [ ] Örnek format verildi mi? (`"2024-06-15T09:00:00Z"`)
- [ ] Optional alanlar `?` ile işaretlendi mi?

### ✅ API Response Kullanırken

- [ ] Backend'den gelen tarih direkt gösterilmiyor mu?
- [ ] `dateUtils` ile parse ediliyor mu?
- [ ] Türkçe locale kullanılıyor mu?
- [ ] Timezone farkı dikkate alındı mı?

### ✅ Testing

```typescript
import { dateUtils } from '@/utils/dateUtils'

describe('Date handling', () => {
  it('should parse ISO 8601 dates', () => {
    const isoDate = '2024-06-15T09:00:00Z'
    const formatted = dateUtils.format(isoDate, 'DD/MM/YYYY')
    expect(formatted).toBe('15/06/2024')
  })

  it('should handle null/undefined dates', () => {
    expect(dateUtils.format(null, 'DD/MM/YYYY')).toBe('')
    expect(dateUtils.format(undefined, 'DD/MM/YYYY')).toBe('')
  })
})
```

## 📖 Format Tokens Referansı

### dayjs Format Tokens

```
YY     → 24
YYYY   → 2024
M      → 6 (Haziran)
MM     → 06
MMM    → Haz
MMMM   → Haziran
D      → 15
DD     → 15
d      → 6 (Cumartesi)
dd     → Ct
ddd    → Cts
dddd   → Cumartesi
H      → 9
HH     → 09
h      → 9 (12-saat)
hh     → 09 (12-saat)
m      → 0
mm     → 00
s      → 0
ss     → 00
A      → AM/PM
```

### Yaygın Formatlar

```typescript
'DD/MM/YYYY'           → "15/06/2024"
'DD MMMM YYYY'         → "15 Haziran 2024"
'DD/MM/YYYY HH:mm'     → "15/06/2024 09:00"
'DD MMMM YYYY HH:mm'   → "15 Haziran 2024 09:00"
'HH:mm'                → "09:00"
'DD MMMM YYYY, dddd'   → "15 Haziran 2024, Cumartesi"
```

## 🚨 Yaygın Hatalar ve Çözümleri

### Hata 1: "Invalid Date" Hatası

```typescript
// ❌ YANLIŞ
const date = new Date('15/06/2024')  // Invalid Date (Amerikan formatı bekler)

// ✅ DOĞRU
const date = dateUtils.parseISO('2024-06-15T09:00:00Z')
```

### Hata 2: Timezone Sorunları

```typescript
// ❌ YANLIŞ - Local timezone kullanır
const local = new Date().toLocaleString()  // "15.06.2024 12:00:00"

// ✅ DOĞRU - Backend'den gelen ISO string kullan
const utc = dateUtils.formatISO(dateUtils.now())  // "2024-06-15T09:00:00Z"
```

### Hata 3: Type Mismatch

```typescript
// ❌ YANLIŞ
interface Session {
  started_at: Date  // Backend string döner!
}

// ✅ DOĞRU
interface Session {
  /** Başlangıç zamanı (ISO 8601: "2024-06-15T09:00:00Z") */
  started_at: string
}
```

## 🔗 Kaynaklar

- [dayjs Documentation](https://day.js.org/docs/en/installation/installation)
- [ISO 8601 Standard](https://en.wikipedia.org/wiki/ISO_8601)
- [FastAPI Date Handling](https://fastapi.tiangolo.com/tutorial/encoder/)

## 📝 Son Güncelleme

Bu doküman backend-frontend tarih type uyumsuzluğu düzeltmesi kapsamında oluşturulmuştur.

**Güncellenme Tarihi**: 2024-11-17
**İlgili Dosyalar**:
- `frontend/src/utils/dateUtils.ts`
- `frontend/src/services/examService.ts`
- `frontend/src/services/parentService.ts`
- `frontend/src/components/Admin/BatchQueueMonitor.tsx`
