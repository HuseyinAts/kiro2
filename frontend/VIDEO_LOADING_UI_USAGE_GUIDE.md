# VideoLoadingUI - Kullanım Kılavuzu

## 🚀 Hızlı Başlangıç

### 1. Import
```typescript
import { VideoLoadingUI } from '../components/VideoLoadingUI';
import { VideoLoadingManager, VideoLoadingState } from '../services/VideoLoadingManager';
import { VideoErrorHandler } from '../services/VideoErrorHandler';
```

### 2. State Tanımlama
```typescript
const [videoLoadingState, setVideoLoadingState] = useState<VideoLoadingState>({
  status: 'idle',
  videos: [],
  error: null,
  loadingProgress: 0,
  retryCount: 0,
  requestId: '',
  loadingTime: 0,
  cacheHit: false,
  errorMessage: null,
});

const [loadingSubjects, setLoadingSubjects] = useState<string[]>([]);
```

### 3. Manager Initialization
```typescript
const videoManagerRef = useRef<VideoLoadingManager | null>(null);
const videoErrorHandlerRef = useRef<VideoErrorHandler | null>(null);

useEffect(() => {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
  
  // Initialize VideoLoadingManager
  videoManagerRef.current = new VideoLoadingManager(API_BASE_URL, 20000, 2);
  
  // Initialize VideoErrorHandler
  videoErrorHandlerRef.current = new VideoErrorHandler(false, true);
  
  // Subscribe to state changes
  const unsubscribe = videoManagerRef.current.subscribe((state) => {
    setVideoLoadingState(state);
  });
  
  return () => {
    unsubscribe();
  };
}, []);
```

### 4. Video Yükleme
```typescript
const loadVideos = async () => {
  if (!videoManagerRef.current) return;
  
  const studentProfile = {
    goals: ['matematik öğrenme', 'fizik geliştirme'],
    currentLevel: { matematik: 50, fizik: 60 },
    learningStyle: 'visual',
    preferences: { grade: 12, exam_type: 'YKS' }
  };
  
  setLoadingSubjects(['matematik', 'fizik']);
  
  await videoManagerRef.current.loadVideos(studentProfile);
};
```

### 5. Handler Fonksiyonları
```typescript
const handleRetry = async () => {
  if (!videoManagerRef.current) return;
  await videoManagerRef.current.retryLoad();
};

const handleShowFallback = () => {
  // Fallback logic
  console.log('Showing fallback videos...');
};

const handleCancel = () => {
  if (!videoManagerRef.current) return;
  videoManagerRef.current.cancelLoad();
};
```

### 6. UI Kullanımı
```typescript
<VideoLoadingUI
  state={videoLoadingState}
  onRetry={handleRetry}
  onShowFallback={handleShowFallback}
  onCancel={handleCancel}
  subjects={loadingSubjects}
/>
```

## 📋 Props Detayları

### VideoLoadingUIProps
```typescript
interface VideoLoadingUIProps {
  state: VideoLoadingState;        // Zorunlu - Video yükleme durumu
  onRetry?: () => void;            // Opsiyonel - Tekrar dene callback
  onShowFallback?: () => void;     // Opsiyonel - Fallback göster callback
  onCancel?: () => void;           // Opsiyonel - İptal callback
  subjects?: string[];             // Opsiyonel - Yüklenen konular
}
```

### VideoLoadingState
```typescript
interface VideoLoadingState {
  status: 'idle' | 'loading' | 'success' | 'error' | 'fallback';
  videos: SubjectVideos[];         // Yüklenen videolar
  error: Error | null;             // Hata objesi
  loadingProgress: number;         // 0-100 arası ilerleme
  retryCount: number;              // Deneme sayısı
  requestId: string;               // Benzersiz istek ID
  loadingTime: number;             // Yükleme süresi (ms)
  cacheHit: boolean;               // Önbellekten mi yüklendi
  errorMessage: string | null;    // Kullanıcı dostu hata mesajı
}
```

## 🎯 Kullanım Senaryoları

### Senaryo 1: Basit Video Yükleme
```typescript
function MyComponent() {
  const [state, setState] = useState<VideoLoadingState>({
    status: 'idle',
    videos: [],
    error: null,
    loadingProgress: 0,
    retryCount: 0,
    requestId: '',
    loadingTime: 0,
    cacheHit: false,
    errorMessage: null,
  });

  const loadVideos = async () => {
    setState(prev => ({ ...prev, status: 'loading', loadingProgress: 0 }));
    
    try {
      // Simüle edilmiş yükleme
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setState(prev => ({ ...prev, loadingProgress: i }));
      }
      
      setState(prev => ({ 
        ...prev, 
        status: 'success',
        videos: mockVideos,
        loadingTime: 2000
      }));
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        status: 'error',
        error: error as Error,
        errorMessage: 'Video yükleme başarısız'
      }));
    }
  };

  return (
    <div>
      <button onClick={loadVideos}>Videoları Yükle</button>
      <VideoLoadingUI state={state} />
    </div>
  );
}
```

### Senaryo 2: Retry Logic ile
```typescript
function MyComponent() {
  const [state, setState] = useState<VideoLoadingState>({...});
  const [retryCount, setRetryCount] = useState(0);

  const loadVideos = async () => {
    setState(prev => ({ 
      ...prev, 
      status: 'loading',
      retryCount: retryCount
    }));
    
    try {
      const response = await fetch('/api/videos');
      const data = await response.json();
      
      setState(prev => ({ 
        ...prev, 
        status: 'success',
        videos: data.videos
      }));
      
      setRetryCount(0); // Reset on success
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        status: 'error',
        error: error as Error
      }));
    }
  };

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    loadVideos();
  };

  return (
    <VideoLoadingUI 
      state={state} 
      onRetry={handleRetry}
    />
  );
}
```

### Senaryo 3: Konu Bazlı Yükleme
```typescript
function MyComponent() {
  const [state, setState] = useState<VideoLoadingState>({...});
  const [subjects, setSubjects] = useState<string[]>([]);

  const loadVideosForSubjects = async (subjectList: string[]) => {
    setSubjects(subjectList);
    setState(prev => ({ ...prev, status: 'loading' }));
    
    // Her konu için video yükle
    for (let i = 0; i < subjectList.length; i++) {
      const progress = ((i + 1) / subjectList.length) * 100;
      setState(prev => ({ ...prev, loadingProgress: progress }));
      
      await loadVideosForSubject(subjectList[i]);
    }
    
    setState(prev => ({ ...prev, status: 'success' }));
  };

  return (
    <VideoLoadingUI 
      state={state}
      subjects={subjects}
    />
  );
}
```

### Senaryo 4: Timeout Handling
```typescript
function MyComponent() {
  const [state, setState] = useState<VideoLoadingState>({...});
  const timeoutRef = useRef<NodeJS.Timeout>();

  const loadVideosWithTimeout = async () => {
    setState(prev => ({ ...prev, status: 'loading' }));
    
    // 20 saniye timeout
    timeoutRef.current = setTimeout(() => {
      setState(prev => ({ 
        ...prev, 
        status: 'fallback',
        errorMessage: 'Videoları 20 saniye içinde yükleyemedik'
      }));
    }, 20000);
    
    try {
      const videos = await fetchVideos();
      clearTimeout(timeoutRef.current);
      
      setState(prev => ({ 
        ...prev, 
        status: 'success',
        videos: videos
      }));
    } catch (error) {
      clearTimeout(timeoutRef.current);
      setState(prev => ({ 
        ...prev, 
        status: 'error',
        error: error as Error
      }));
    }
  };

  return (
    <VideoLoadingUI 
      state={state}
      onRetry={loadVideosWithTimeout}
      onShowFallback={() => showFallbackVideos()}
    />
  );
}
```

## 🎨 Özelleştirme

### Custom Styling
```typescript
// VideoLoadingUI bileşeni inline styles kullanıyor
// Özelleştirmek için wrapper div ekleyin:

<div className="custom-video-loading">
  <VideoLoadingUI state={state} />
</div>

// CSS:
.custom-video-loading {
  max-width: 800px;
  margin: 0 auto;
}

.custom-video-loading > div {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}
```

### Custom Messages
```typescript
// Kendi mesajlarınızı eklemek için subjects prop'unu kullanın:

const customSubjects = [
  'Matematik - Türev',
  'Fizik - Hareket',
  'Kimya - Atom'
];

<VideoLoadingUI 
  state={state}
  subjects={customSubjects}
/>

// Mesajlar otomatik olarak:
// "🔍 AI Matematik - Türev konusunda videolar buluyor..."
```

## 🐛 Hata Ayıklama

### Console Logging
```typescript
// VideoErrorHandler ile hata loglama:
const errorHandler = new VideoErrorHandler(false, true); // console enabled

errorHandler.logError(error, {
  component: 'MyComponent',
  action: 'loadVideos',
  subjects: subjects,
  retryCount: retryCount
});
```

### State Debugging
```typescript
// State değişikliklerini izleme:
useEffect(() => {
  console.log('VideoLoadingState changed:', videoLoadingState);
}, [videoLoadingState]);
```

### Network Debugging
```typescript
// VideoLoadingManager network isteklerini loglar:
videoManagerRef.current = new VideoLoadingManager(
  API_BASE_URL,
  20000,  // timeout
  2,      // max retries
  true    // debug mode
);
```

## ⚡ Performance İpuçları

### 1. Memoization
```typescript
const handleRetry = useCallback(async () => {
  if (!videoManagerRef.current) return;
  await videoManagerRef.current.retryLoad();
}, []);

const handleCancel = useCallback(() => {
  if (!videoManagerRef.current) return;
  videoManagerRef.current.cancelLoad();
}, []);
```

### 2. Lazy Loading
```typescript
// VideoLoadingUI'yi lazy load edin:
const VideoLoadingUI = lazy(() => import('../components/VideoLoadingUI'));

<Suspense fallback={<CircularProgress />}>
  <VideoLoadingUI state={state} />
</Suspense>
```

### 3. State Batching
```typescript
// Birden fazla state güncellemesini batch edin:
setState(prev => ({
  ...prev,
  status: 'success',
  videos: data.videos,
  loadingTime: Date.now() - startTime,
  cacheHit: data.fromCache
}));
```

## 🧪 Testing

### Unit Test Örneği
```typescript
import { render, screen } from '@testing-library/react';
import { VideoLoadingUI } from './VideoLoadingUI';

describe('VideoLoadingUI', () => {
  it('shows loading state', () => {
    const state: VideoLoadingState = {
      status: 'loading',
      videos: [],
      error: null,
      loadingProgress: 50,
      retryCount: 0,
      requestId: 'test-123',
      loadingTime: 5000,
      cacheHit: false,
      errorMessage: null,
    };

    render(<VideoLoadingUI state={state} subjects={['matematik']} />);
    
    expect(screen.getByText(/matematik konusunda videolar buluyor/i)).toBeInTheDocument();
    expect(screen.getByText('%50')).toBeInTheDocument();
  });

  it('shows success state', () => {
    const state: VideoLoadingState = {
      status: 'success',
      videos: mockVideos,
      error: null,
      loadingProgress: 100,
      retryCount: 0,
      requestId: 'test-123',
      loadingTime: 2300,
      cacheHit: false,
      errorMessage: null,
    };

    render(<VideoLoadingUI state={state} />);
    
    expect(screen.getByText(/Videolar Başarıyla Yüklendi/i)).toBeInTheDocument();
    expect(screen.getByText(/45 adet/i)).toBeInTheDocument();
  });
});
```

### Integration Test Örneği
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('VideoLoadingUI Integration', () => {
  it('handles retry flow', async () => {
    const mockRetry = jest.fn();
    
    const state: VideoLoadingState = {
      status: 'error',
      videos: [],
      error: new Error('Network error'),
      loadingProgress: 0,
      retryCount: 1,
      requestId: 'test-123',
      loadingTime: 0,
      cacheHit: false,
      errorMessage: 'İnternet bağlantısı hatası',
    };

    render(<VideoLoadingUI state={state} onRetry={mockRetry} />);
    
    const retryButton = screen.getByText(/Tekrar Dene/i);
    await userEvent.click(retryButton);
    
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });
});
```

## 📚 İlgili Dökümanlar

- [VideoLoadingManager README](../services/VideoLoadingManager.README.md)
- [VideoErrorHandler README](../services/VideoErrorHandler.README.md)
- [VideoLoadingUI Implementation Summary](./VideoLoadingUI.IMPLEMENTATION_SUMMARY.md)
- [Task 15 Completion Report](./TASK_15_UI_IMPROVEMENTS_COMPLETE.md)

## 🆘 Sık Sorulan Sorular

### S: VideoLoadingUI neden render olmuyor?
**C:** State'in `status` değerini kontrol edin. `idle` durumunda UI render olmaz.

### S: Progress bar neden güncellenmiyor?
**C:** `loadingProgress` değerini 0-100 arası güncelleyin. State subscription'ın çalıştığından emin olun.

### S: Animasyonlar neden çalışmıyor?
**C:** CSS keyframes tanımlı mı kontrol edin. Inline styles içinde `<style>` tag'i var.

### S: Retry butonu neden çalışmıyor?
**C:** `onRetry` prop'unu geçtiğinizden emin olun. Callback fonksiyonu tanımlı olmalı.

### S: Konu bazlı mesajlar neden görünmüyor?
**C:** `subjects` prop'unu geçin. Boş array geçerseniz genel mesajlar gösterilir.

---

**Hazırlayan**: Kiro AI Assistant
**Tarih**: 3 Kasım 2025
**Versiyon**: 1.0.0
