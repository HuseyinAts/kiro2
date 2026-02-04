# VideoLoadingUI Component

Video yükleme sürecinin görsel geri bildirimlerini sağlayan React bileşeni.

## Özellikler

✅ **Loading Indicator** - Progress bar + spinner animasyonu  
✅ **Dinamik Mesajlar** - Konu bazlı yükleme mesajları  
✅ **Success State** - Video sayısı ve yükleme süresi ile başarı mesajı  
✅ **Error State** - Kullanıcı dostu hata mesajları ve çözüm önerileri  
✅ **Retry Button** - Otomatik retry logic ile "Tekrar Dene" butonu  
✅ **Fallback Button** - "Örnek Videoları Göster" butonu  
✅ **Loading Time Display** - Yükleme süresini gösterme  
✅ **Smooth Animations** - Fade-in ve scale animasyonları  

## Requirements Coverage

Bu bileşen aşağıdaki gereksinimleri karşılar:

- **Req 3.1**: Dinamik loading mesajları (konu bazlı)
- **Req 3.2**: Loading indicator (progress bar + spinner)
- **Req 3.3**: Success message (video sayısı ile)
- **Req 3.4**: Error message display + retry/fallback butonları
- **Req 3.6**: Loading time display
- **Req 3.7**: Bekleme mesajları (5 saniye+)
- **Req 3.11**: Smooth fade-in animations

## Kullanım

### Basic Usage

```tsx
import { VideoLoadingUI } from './components/VideoLoadingUI';
import { VideoLoadingManager } from './services/VideoLoadingManager';

function MyComponent() {
  const [videoState, setVideoState] = useState<VideoLoadingState>({
    status: 'idle',
    videos: [],
    error: null,
    loadingProgress: 0,
    retryCount: 0,
    requestId: '',
    loadingTime: 0,
  });

  const videoManager = useRef(new VideoLoadingManager());

  useEffect(() => {
    const unsubscribe = videoManager.current.subscribe((state) => {
      setVideoState(state);
    });

    return () => unsubscribe();
  }, []);

  const handleRetry = () => {
    videoManager.current.loadVideos(profile);
  };

  const handleShowFallback = () => {
    // Show fallback videos
  };

  return (
    <VideoLoadingUI
      state={videoState}
      onRetry={handleRetry}
      onShowFallback={handleShowFallback}
    />
  );
}
```

### Props

```typescript
interface VideoLoadingUIProps {
  state: VideoLoadingState;      // Video yükleme durumu
  onRetry?: () => void;           // Retry butonu callback
  onShowFallback?: () => void;    // Fallback butonu callback
  onCancel?: () => void;          // Cancel butonu callback (opsiyonel)
}
```

### State Types

```typescript
type VideoLoadingStatus = 'idle' | 'loading' | 'success' | 'error' | 'fallback';

interface VideoLoadingState {
  status: VideoLoadingStatus;
  videos: SubjectVideos[];
  error: Error | null;
  loadingProgress: number;        // 0-100
  retryCount: number;
  requestId: string;
  loadingTime: number;            // milliseconds
  cacheHit?: boolean;
  errorMessage?: string;
}
```

## State Transitions

```
idle → loading → success
              ↓
            error → (retry) → loading
              ↓
          fallback
```

## UI States

### 1. Loading State

**Görünüm:**
- Spinner animasyonu
- Progress bar (0-100%)
- Dinamik loading mesajı
- Progress durumu ("Bağlantı kuruluyor...", "Videolar aranıyor...", vb.)
- Retry count (varsa)

**Mesaj Örnekleri:**
- "AI size özel videoları buluyor..."
- "AI Matematik konusunda videolar buluyor..."
- "Videolar kalite skoruna göre sıralanıyor..."

### 2. Success State

**Görünüm:**
- ✅ Success icon (scale animasyonu)
- "Videolar Başarıyla Yüklendi!" başlığı
- Toplam video sayısı
- Konu sayısı (birden fazla ise)
- Yükleme süresi
- Cache hit badge (varsa)
- Bilgilendirme mesajı

**Örnek:**
```
✅
Videolar Başarıyla Yüklendi!
45 video bulundu (3 farklı konu)

⏱️ Yükleme süresi: 2.3s  ⚡ Hızlı yükleme (önbellekten)

🎯 Tüm videolar seviyenize ve hedeflerinize uygun olarak seçildi
```

### 3. Error State

**Görünüm:**
- ❌ Error icon
- "Video Yükleme Hatası" başlığı
- Kullanıcı dostu hata mesajı
- Retry count (varsa)
- "Tekrar Dene" butonu (retry mümkünse)
- "Örnek Videoları Göster" butonu
- Sorun giderme önerileri

**Hata Mesajları:**
- "İstek zaman aşımına uğradı. Lütfen tekrar deneyin."
- "İnternet bağlantınızı kontrol edin."
- "Video servisi şu anda erişilebilir değil."
- "Çok fazla istek gönderildi. Lütfen biraz bekleyin."

### 4. Fallback State

**Görünüm:**
- ⚠️ Warning icon
- "Kişiselleştirilmiş Videolar Yüklenemedi" başlığı
- Açıklama mesajı
- "Örnek Videoları Göster" butonu
- Bilgilendirme notu

## Animations

### CSS Animations

```css
@keyframes spin {
  /* Spinner rotation */
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes fadeIn {
  /* Smooth fade-in */
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  /* Success icon scale */
  from {
    transform: scale(0.5);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
```

### Animation Timing

- **Fade-in**: 0.3s ease-in (loading, error, fallback)
- **Success fade-in**: 0.5s ease-in
- **Success icon scale**: 0.5s ease-out
- **Spinner rotation**: 1s linear infinite
- **Progress bar**: 0.3s ease (width transition)
- **Button hover**: 0.2s ease (all properties)

## Styling

### Color Palette

- **Primary**: #007bff (buttons, progress bar)
- **Success**: #28a745 (success state)
- **Error**: #dc3545 (error state)
- **Warning**: #ffc107 (fallback state)
- **Info**: #17a2b8 (cache hit badge)
- **Gray**: #6c757d (fallback button)
- **Light**: #f8f9fa (backgrounds)
- **Dark**: #333 (text)

### Typography

- **Heading**: 20-22px, font-weight: 600
- **Body**: 14-16px, line-height: 1.6
- **Small**: 12-13px
- **Icon**: 48px

### Spacing

- **Container padding**: 30-40px
- **Element margin**: 10-20px
- **Button padding**: 12-14px vertical, 24-28px horizontal
- **Gap**: 15-20px

## Integration with VideoLoadingManager

VideoLoadingUI, VideoLoadingManager ile tam entegre çalışır:

```tsx
// 1. VideoLoadingManager oluştur
const videoManager = new VideoLoadingManager(
  'http://localhost:8001',  // API base URL
  20000,                     // 20s timeout
  2                          // 2 max retries
);

// 2. State değişikliklerini dinle
videoManager.subscribe((state) => {
  setVideoState(state);
});

// 3. Video yükleme başlat
await videoManager.loadVideos(profile);

// 4. UI otomatik olarak state'e göre güncellenir
<VideoLoadingUI state={videoState} ... />
```

## Accessibility

- ✅ Semantic HTML kullanımı
- ✅ Yeterli renk kontrastı (WCAG AA)
- ✅ Keyboard navigation (button focus states)
- ✅ Screen reader friendly (anlamlı metinler)
- ✅ Loading state announcements

## Performance

- ✅ Minimal re-renders (React.memo kullanımı önerilir)
- ✅ CSS animations (GPU accelerated)
- ✅ Lazy loading (animations on demand)
- ✅ Optimized state updates

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Testing

Test dosyası: `VideoLoadingUI.test.tsx`

```bash
npm test VideoLoadingUI
```

## Examples

Detaylı kullanım örnekleri için:
- `VideoLoadingUI.example.tsx` dosyasına bakın

## Changelog

### v1.0.0 (2025-11-03)
- ✅ Initial release
- ✅ Loading, success, error, fallback states
- ✅ Smooth animations
- ✅ Retry and fallback buttons
- ✅ Dynamic loading messages
- ✅ Loading time display
- ✅ Cache hit indicator

## License

MIT

## Author

KIRO2 Development Team

## Related

- `VideoLoadingManager.ts` - Video yükleme logic
- `VideoErrorHandler.ts` - Error handling
- `useOfflineMode.ts` - Offline mode hook
