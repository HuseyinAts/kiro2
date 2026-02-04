# VideoLoadingManager Integration Guide

Bu doküman, VideoLoadingManager'ın main.tsx'e nasıl entegre edileceğini açıklar.

## 📋 Genel Bakış

VideoLoadingManager (Task 13) tamamlandı ve kullanıma hazır. Bu servis, Learning Path sayfasında video yükleme işlemlerini merkezi olarak yönetir.

## 🎯 Entegrasyon Adımları

### 1. Import VideoLoadingManager

`frontend/src/main.tsx` dosyasının başına ekleyin:

```typescript
import { 
  getVideoLoadingManager, 
  VideoLoadingState,
  StudentProfile 
} from './services/VideoLoadingManager';
```

### 2. Component State'e Ekleyin

LearningPathPage component'inde state ekleyin:

```typescript
const LearningPathPage = () => {
  // Mevcut state'ler...
  const [currentStep, setCurrentStep] = React.useState('welcome');
  const [studentProfile, setStudentProfile] = React.useState({...});
  
  // YENİ: VideoLoadingManager state
  const [videoLoadingState, setVideoLoadingState] = React.useState<VideoLoadingState | null>(null);
  const [videoManager] = React.useState(() => getVideoLoadingManager());
  
  // ... rest of component
}
```

### 3. Subscribe to State Changes

useEffect ile state değişikliklerini dinleyin:

```typescript
React.useEffect(() => {
  // Subscribe to video loading state changes
  const unsubscribe = videoManager.subscribe((state) => {
    setVideoLoadingState(state);
    
    // Update UI based on state
    if (state.status === 'loading') {
      console.log(`Loading progress: ${state.loadingProgress}%`);
    } else if (state.status === 'success') {
      console.log(`Videos loaded in ${state.loadingTime}ms`);
    } else if (state.status === 'error') {
      console.error('Error loading videos:', state.errorMessage);
    }
  });

  // Cleanup on unmount
  return () => {
    unsubscribe();
    videoManager.cancelLoad(); // Cancel any ongoing requests
  };
}, [videoManager]);
```

### 4. Replace Existing Video Loading Logic

Mevcut video yükleme kodunu (satır ~1366-1450) değiştirin:

**ÖNCE (Eski Kod):**
```typescript
// Old code with manual fetch
const response = await fetch(`${API_BASE_URL}/api/youtube/recommendations`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(defaultProfile),
  signal: controller.signal
});
```

**SONRA (Yeni Kod):**
```typescript
// New code with VideoLoadingManager
try {
  const videos = await videoManager.loadVideos(defaultProfile);
  
  // Success - display videos
  displayVideos(videos);
  
} catch (error) {
  // Error - check state for fallback
  const state = videoManager.getState();
  
  if (state.status === 'fallback') {
    // Show fallback videos
    displayFallbackVideos(FALLBACK_VIDEOS);
  } else {
    // Show error message
    showErrorMessage(state.errorMessage);
  }
}
```

### 5. Update UI Based on State

Loading indicator'ı güncelleyin:

```typescript
// Loading state UI
{videoLoadingState?.status === 'loading' && (
  <div style={{ padding: '20px', textAlign: 'center' }}>
    <h3>🤖 AI size özel videoları buluyor...</h3>
    
    {/* Progress bar */}
    <div style={{ 
      width: '100%', 
      backgroundColor: '#e9ecef', 
      borderRadius: '10px',
      height: '20px',
      overflow: 'hidden',
      marginTop: '15px'
    }}>
      <div style={{ 
        width: `${videoLoadingState.loadingProgress}%`, 
        backgroundColor: '#6f42c1',
        height: '100%',
        transition: 'width 0.3s ease'
      }} />
    </div>
    
    <p style={{ marginTop: '10px', color: '#666' }}>
      {videoLoadingState.loadingProgress}% tamamlandı
    </p>
    
    {/* Cancel button */}
    <button 
      onClick={() => videoManager.cancelLoad()}
      style={{
        marginTop: '15px',
        padding: '10px 20px',
        backgroundColor: '#dc3545',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer'
      }}
    >
      ❌ İptal Et
    </button>
  </div>
)}

// Success state UI
{videoLoadingState?.status === 'success' && (
  <div style={{ padding: '20px', textAlign: 'center' }}>
    <h3>✅ Videolar Hazır!</h3>
    <p>
      {videoLoadingState.videos.length} kategori, 
      {videoLoadingState.videos.reduce((sum, cat) => sum + cat.videos.length, 0)} video
    </p>
    <p style={{ fontSize: '14px', color: '#666' }}>
      Yükleme süresi: {videoLoadingState.loadingTime}ms
      {videoLoadingState.cacheHit && ' (Cache\'den)'}
    </p>
  </div>
)}

// Error state UI
{videoLoadingState?.status === 'error' && (
  <div style={{ padding: '20px', textAlign: 'center' }}>
    <h3>❌ Hata Oluştu</h3>
    <p>{videoLoadingState.errorMessage}</p>
    <button 
      onClick={() => videoManager.retryLoad(studentProfile)}
      style={{
        marginTop: '15px',
        padding: '10px 20px',
        backgroundColor: '#ffc107',
        color: '#212529',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer'
      }}
    >
      🔄 Tekrar Dene
    </button>
  </div>
)}

// Fallback state UI
{videoLoadingState?.status === 'fallback' && (
  <div style={{ padding: '20px', textAlign: 'center' }}>
    <h3>⚠️ Örnek Videolar Gösteriliyor</h3>
    <p>{videoLoadingState.errorMessage}</p>
    <button 
      onClick={() => videoManager.retryLoad(studentProfile)}
      style={{
        marginTop: '15px',
        padding: '10px 20px',
        backgroundColor: '#17a2b8',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer'
      }}
    >
      🔄 Tekrar Dene
    </button>
  </div>
)}
```

## 🔧 Complete Integration Example

İşte tam entegrasyon örneği:

```typescript
const LearningPathPage = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = React.useState('welcome');
  const [studentProfile, setStudentProfile] = React.useState({
    goals: [],
    currentLevel: {},
    learningStyle: '',
    preferences: {}
  });
  
  // VideoLoadingManager integration
  const [videoLoadingState, setVideoLoadingState] = React.useState<VideoLoadingState | null>(null);
  const [videoManager] = React.useState(() => getVideoLoadingManager());

  // Subscribe to state changes
  React.useEffect(() => {
    const unsubscribe = videoManager.subscribe(setVideoLoadingState);
    return () => {
      unsubscribe();
      videoManager.cancelLoad();
    };
  }, [videoManager]);

  // Load videos function
  const handleLoadVideos = async () => {
    try {
      // Prepare profile
      const profile: StudentProfile = {
        goals: studentProfile.goals.length > 0 ? studentProfile.goals : ['TYT'],
        currentLevel: Object.keys(studentProfile.currentLevel).length > 0 
          ? studentProfile.currentLevel 
          : { matematik: 5, fizik: 4 },
        learningStyle: studentProfile.learningStyle || 'visual',
        preferences: studentProfile.preferences || {}
      };

      // Load videos
      const videos = await videoManager.loadVideos(profile);

      // Open popup with videos
      openVideoPopup(videos);

    } catch (error) {
      console.error('Error loading videos:', error);
      
      // Check if we should show fallback
      const state = videoManager.getState();
      if (state.status === 'fallback') {
        openVideoPopup(FALLBACK_VIDEOS, state.errorMessage);
      }
    }
  };

  // Retry function
  const handleRetry = async () => {
    try {
      const profile: StudentProfile = {
        goals: studentProfile.goals,
        currentLevel: studentProfile.currentLevel,
        learningStyle: studentProfile.learningStyle,
        preferences: studentProfile.preferences
      };

      const videos = await videoManager.retryLoad(profile);
      openVideoPopup(videos);

    } catch (error) {
      console.error('Retry failed:', error);
    }
  };

  // Rest of component...
  return (
    <div>
      {/* Your existing UI */}
      
      {/* Video loading UI */}
      {videoLoadingState && (
        <VideoLoadingUI 
          state={videoLoadingState}
          onRetry={handleRetry}
          onCancel={() => videoManager.cancelLoad()}
        />
      )}
    </div>
  );
};
```

## 📊 Benefits of Integration

### Before (Manual Fetch)
- ❌ No centralized state management
- ❌ No automatic retry
- ❌ No progress tracking
- ❌ Manual error handling
- ❌ No request cancellation
- ❌ Hardcoded timeout

### After (VideoLoadingManager)
- ✅ Centralized state management
- ✅ Automatic retry with exponential backoff
- ✅ Progress tracking (0-100%)
- ✅ Comprehensive error handling
- ✅ Request cancellation support
- ✅ Configurable timeout
- ✅ Cache hit/miss tracking
- ✅ User-friendly error messages
- ✅ Request ID tracking
- ✅ Loading time measurement

## 🧪 Testing Integration

### Manual Testing Steps

1. **Test Successful Load:**
   - Open Learning Path page
   - Click "Video Kütüphanesini Aç"
   - Verify videos load successfully
   - Check loading progress updates
   - Verify success message

2. **Test Timeout:**
   - Disconnect backend
   - Try loading videos
   - Verify timeout after 20 seconds
   - Check fallback videos shown
   - Verify error message

3. **Test Retry:**
   - Cause an error
   - Click "Tekrar Dene"
   - Verify retry with backoff
   - Check success after retry

4. **Test Cancel:**
   - Start loading videos
   - Click "İptal Et"
   - Verify request cancelled
   - Check state reset

5. **Test Progress:**
   - Start loading videos
   - Watch progress bar
   - Verify smooth updates (10% → 30% → 70% → 100%)

### Automated Testing

```typescript
// Add to your test suite
describe('LearningPathPage with VideoLoadingManager', () => {
  it('should load videos successfully', async () => {
    render(<LearningPathPage />);
    
    // Click load button
    fireEvent.click(screen.getByText('Video Kütüphanesini Aç'));
    
    // Wait for loading
    expect(screen.getByText(/AI size özel videoları buluyor/)).toBeInTheDocument();
    
    // Wait for success
    await waitFor(() => {
      expect(screen.getByText(/Videolar Hazır/)).toBeInTheDocument();
    });
  });
});
```

## 🔍 Debugging

### Enable Debug Logging

VideoLoadingManager otomatik olarak console'a log yazar:

```
📤 VideoLoadingManager: Starting API call
✅ VideoLoadingManager: Videos loaded successfully
❌ VideoLoadingManager: Error loading videos
🔄 VideoLoadingManager: Retrying (attempt 1/2)
⏰ VideoLoadingManager: Request timeout
🛑 VideoLoadingManager: Cancelling request
```

### Check State

```typescript
// Get current state
const state = videoManager.getState();
console.log('Current state:', state);

// Check specific properties
console.log('Status:', state.status);
console.log('Progress:', state.loadingProgress);
console.log('Error:', state.error);
console.log('Videos:', state.videos);
```

## 📝 Migration Checklist

- [ ] Import VideoLoadingManager
- [ ] Add state variables
- [ ] Subscribe to state changes
- [ ] Replace fetch logic with videoManager.loadVideos()
- [ ] Update loading UI
- [ ] Update success UI
- [ ] Update error UI
- [ ] Add retry button
- [ ] Add cancel button
- [ ] Test successful load
- [ ] Test timeout scenario
- [ ] Test retry logic
- [ ] Test cancel functionality
- [ ] Test progress tracking
- [ ] Remove old fetch code
- [ ] Update error messages
- [ ] Test in production

## 🚀 Next Steps

After integration:

1. **Task 14:** Implement VideoErrorHandler
2. **Task 15:** UI improvements (animations, better messages)
3. **Task 16:** Offline mode and network detection
4. **Task 17-18:** Add comprehensive tests
5. **Task 19:** Setup monitoring and alerting

## 📞 Support

Sorularınız için:
- Documentation: `VideoLoadingManager.README.md`
- Examples: `VideoLoadingManager.example.tsx`
- Tests: `__tests__/VideoLoadingManager.test.ts`

---

**Integration Guide Version:** 1.0  
**Last Updated:** 30 Ekim 2025  
**Status:** Ready for Integration
