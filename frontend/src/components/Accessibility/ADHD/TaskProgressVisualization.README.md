# Task Progress Visualization Component

## Genel Bakış

`TaskProgressVisualization` bileşeni, DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) tanılı öğrenciler için optimize edilmiş görsel ilerleme göstergesi sağlar. Görevlerin tamamlanma durumunu, alt görevleri ve kilometre taşlarını görsel olarak sunar.

## Requirements

Bu bileşen aşağıdaki gereksinimleri karşılar:

- **REQ-52.46**: Progress bar gösterimi
- **REQ-52.47**: Tamamlanma yüzdesi gösterimi
- **REQ-52.48**: Görsel milestone (kilometre taşı) göstergeleri
- **REQ-52.49**: Renk kodlu ilerleme gösterimi
- **REQ-52.50**: Animasyonlu geçişler

## Task

**Task 90.2**: Görsel ilerleme göstergesi
- Progress bar
- Completion percentage
- Visual milestones

## Özellikler

### 1. Progress Bar (İlerleme Çubuğu)
- Animasyonlu dolum efekti
- Renk kodlu gösterim
- Yüzdelik değer gösterimi
- ARIA etiketleri ile erişilebilirlik

### 2. Alt Görev Takibi
- Tamamlanan/toplam alt görev sayısı
- Görsel onay işareti
- Renk kodlu durum gösterimi

### 3. Kilometre Taşları (Milestones)
- %25, %50, %75, %100 kilometre taşları
- İkon ve renk kodlu gösterim
- Ulaşılan taşlar için animasyon
- Onay işareti gösterimi

### 4. Zaman Takibi
- Tahmini süre
- Geçen süre
- Kalan süre
- Okunabilir format (saat/dakika)

### 5. Animasyonlar
- Progress bar dolum animasyonu
- Shine (parıltı) efekti
- Milestone pulse animasyonu
- Checkmark appear animasyonu

## Kullanım

### Temel Kullanım

```tsx
import { TaskProgressVisualization } from '@/components/Accessibility/ADHD';

function MyComponent() {
  return (
    <TaskProgressVisualization 
      taskId="task-123"
    />
  );
}
```

### Callback ile Kullanım

```tsx
import { TaskProgressVisualization } from '@/components/Accessibility/ADHD';

function MyComponent() {
  const handleRefresh = () => {
    console.log('Görev görüntüleniyor');
    // Görev detay sayfasına yönlendir
  };

  return (
    <TaskProgressVisualization 
      taskId="task-123"
      onRefresh={handleRefresh}
    />
  );
}
```

## Props

| Prop | Tip | Gerekli | Varsayılan | Açıklama |
|------|-----|---------|-----------|----------|
| `taskId` | `string` | ✅ | - | Görev ID'si |
| `onRefresh` | `() => void` | ❌ | - | Yenileme butonu callback'i |

## API Entegrasyonu

Bileşen, backend API'den veri çeker:

```
GET /api/adhd-task-management/tasks/{taskId}/progress
```

### Response Formatı

```typescript
interface ProgressVisualizationData {
  task_id: string;
  title: string;
  progress_percentage: number;
  completed_subtasks: number;
  total_subtasks: number;
  estimated_minutes?: number;
  actual_minutes?: number;
  time_remaining_minutes?: number;
  milestones: Milestone[];
  color: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'blocked';
}

interface Milestone {
  percentage: number;
  label: string;
  reached: boolean;
  icon: string;
  color: string;
}
```

## Durum Yönetimi

### Loading State
- Spinner animasyonu
- "İlerleme yükleniyor..." mesajı

### Error State
- Hata mesajı gösterimi
- "Tekrar Dene" butonu

### Success State
- Tam ilerleme görselleştirmesi
- Tüm bileşenler aktif

## Erişilebilirlik

### ARIA Etiketleri
- `role="progressbar"` - Progress bar için
- `aria-valuenow` - Mevcut ilerleme değeri
- `aria-valuemin` - Minimum değer (0)
- `aria-valuemax` - Maksimum değer (100)
- `aria-label` - Ekran okuyucu açıklamaları

### Klavye Navigasyonu
- Tab ile butonlar arasında gezinme
- Enter/Space ile buton aktivasyonu
- Focus göstergeleri

### Yüksek Kontrast Modu
- Sınır kalınlıkları artırılır
- Renkler daha belirgin hale gelir

### Azaltılmış Hareket Modu
- Animasyonlar devre dışı bırakılır
- Geçişler kaldırılır
- Statik gösterim

## Responsive Tasarım

### Desktop (> 768px)
- 4 sütunlu milestone grid
- Tam genişlik progress bar
- Yan yana zaman gösterimi

### Mobile (≤ 768px)
- 2 sütunlu milestone grid
- Tam genişlik progress bar
- Dikey zaman gösterimi
- Küçültülmüş fontlar

## Renk Kodlama

### Durum Renkleri
- **Başlanmadı**: Gri (#9E9E9E)
- **Devam Ediyor**: Mavi (#2196F3)
- **Tamamlandı**: Yeşil (#4CAF50)
- **Engellenmiş**: Kırmızı (#F44336)

### Milestone Renkleri
- **%25 (Başlangıç)**: Yeşil (#4CAF50)
- **%50 (Yarı Yol)**: Mavi (#2196F3)
- **%75 (Son Çeyrek)**: Turuncu (#FF9800)
- **%100 (Tamamlandı)**: Yeşil (#4CAF50)

## Performans

### Optimizasyonlar
- Lazy loading için React.lazy kullanımı
- Memoization ile gereksiz render'ları önleme
- CSS animasyonları (GPU hızlandırmalı)
- Debounced API çağrıları

### Animasyon Performansı
- `transform` ve `opacity` kullanımı (GPU)
- `will-change` özelliği
- `requestAnimationFrame` kullanımı

## Test

### Unit Tests
```bash
npm test TaskProgressVisualization.test.tsx
```

### Integration Tests
```bash
npm test TaskProgressVisualization.integration.test.tsx
```

### E2E Tests
```bash
npm run e2e:test -- --spec=task-progress.spec.ts
```

## Örnek Senaryolar

### Senaryo 1: Yeni Başlayan Görev
```tsx
// Progress: 0%
// Completed: 0/5
// Status: not_started
<TaskProgressVisualization taskId="new-task" />
```

### Senaryo 2: Devam Eden Görev
```tsx
// Progress: 60%
// Completed: 3/5
// Status: in_progress
<TaskProgressVisualization taskId="ongoing-task" />
```

### Senaryo 3: Tamamlanan Görev
```tsx
// Progress: 100%
// Completed: 5/5
// Status: completed
<TaskProgressVisualization taskId="completed-task" />
```

## Sorun Giderme

### API Hatası
**Sorun**: "İlerleme verileri yüklenemedi" hatası
**Çözüm**: 
- Token'ın geçerli olduğundan emin olun
- Backend API'nin çalıştığını kontrol edin
- Network sekmesinde 401/403 hatalarını kontrol edin

### Animasyon Çalışmıyor
**Sorun**: Progress bar animasyonu görünmüyor
**Çözüm**:
- CSS dosyasının import edildiğinden emin olun
- `prefers-reduced-motion` ayarını kontrol edin
- Browser developer tools'da CSS'i inceleyin

### Milestone Gösterilmiyor
**Sorun**: Kilometre taşları görünmüyor
**Çözüm**:
- API response'unda `milestones` array'inin olduğundan emin olun
- Console'da hata mesajlarını kontrol edin
- Grid layout'un responsive olduğunu doğrulayın

## İlgili Bileşenler

- `VisualTimer` - Pomodoro zamanlayıcı
- `FocusMode` - Dikkat modu
- `TaskDecomposition` - Görev bölme

## Kaynaklar

- [ADHD Support Documentation](./README.md)
- [WCAG Compliance Report](./WCAG_COMPLIANCE_REPORT.md)
- [Backend API Documentation](../../../backend/api/README_ADHD_SUPPORT.md)

## Lisans

Bu bileşen Teknofest 2025 Eğitim Eylemci Platformu'nun bir parçasıdır.
