# Offline Mode ve Network Detection

Bu doküman, Learning Path Video Yükleme sisteminde kullanılan offline mode ve network detection özelliklerini açıklar.

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Bileşenler](#bileşenler)
- [Kullanım](#kullanım)
- [API Referansı](#api-referansı)
- [Örnekler](#örnekler)
- [Troubleshooting](#troubleshooting)

## 🎯 Genel Bakış

Offline mode sistemi, kullanıcının internet bağlantısını izler ve bağlantı sorunlarında uygun aksiyonlar alır:

### Özellikler

✅ **Network Status Detection**
- Online/offline durumu tespiti
- Yavaş bağlantı tespiti (slow connection)
- Network quality monitoring (RTT, downlink speed)

✅ **Offline Mode UI**
- Kullanıcı dostu offline banner
- Network durumu göstergesi
- Retry ve dismiss butonları

✅ **Network Reconnection Handling**
- Otomatik reconnection attempts (exponential backoff)
- Auto-retry on reconnection
- Reconnection callback'leri

✅ **Request Cancellation**
- Kullanıcı sayfadan ayrıldığında request iptali
- Pending request tracking
- Beforeunload event handling

✅ **Auto-Retry on Reconnection**
- Network geri geldiğinde otomatik retry
- Cancelled request'leri yeniden deneme
- VideoLoadingManager entegrasyonu

## 🧩 Bileşenler

### 1. NetworkDetector

Network durumunu izleyen ve yöneten servis.

**Dosya:** `frontend/src/services/NetworkDetector.ts`

**Özellikler:**
- Online/offline event listening
- Network quality monitoring (Network Information API)
- Ping test ile bağlantı kontrolü
- Reconnection attempts (exponential backoff)
- State subscription mechanism

**Kullanım:**
```typescript
import { NetworkDetector, getNetworkDetector } from './services/NetworkDetector';

// Singleton instance
const detector = getNetworkDetector();

// Subscribe to network changes
const unsubscribe = detector.subscribe((state) => {
  console.log('Network status:', state.status);
  console.log('Is online:', state.isOnline);
});

// Check connection manually
const isOnline = await detector.checkConnection();

// Cleanup
unsubscribe();
```

### 2. OfflineModeManager

Offline mode UI ve request cancellation'ı yöneten servis.

**Dosya:** `frontend/src/services/OfflineModeManager.ts`

**Özellikler:**
- Offline mode UI management
- Request cancellation on navigation
- Auto-retry on reconnection
- Pending request tracking
- VideoLoadingManager entegrasyonu

**Kullanım:**
```typescript
import { OfflineModeManager, createOfflineModeManager } from './services/OfflineModeManager';
import { getNetworkDetector } from './services/NetworkDetector';

const networkDetector = getNetworkDetector();
const offlineModeManager = createOfflineModeManager(networkDetector);

// Subscribe to state changes
const unsubscribe = offlineModeManager.subscribe((state) => {
  console.log('Offline mode state:', state);
});

// Register pending request
offlineModeManager.registerPendingRequest('request-123');

// Unregister pending request
offlineModeManager.unregisterPendingRequest('request-123');

// Cleanup
unsubscribe();
```

### 3. useOfflineMode Hook

React component'lerinde offline mode kullanımı için hook.

**Dosya:** `frontend/src/hooks/useOfflineMode.ts`

**Özellikler:**
- Network state management
- Offline mode state management
- Request tracking
- Auto-retry on reconnection

**Kullanım:**
```typescript
import { useOfflineMode } from './hooks/useOfflineMode';

function MyComponent() {
  const {
    isOnline,
    isOffline,
    isSlow,
    showOfflineUI,
    networkState,
    offlineModeState,
    retryCancelledRequests,
    registerPendingRequest,
    unregisterPendingRequest,
  } = useOfflineMode({
    videoLoadingManager: videoManager,
    autoRetryOnReconnection: true,
  });

  return (
    <div>
      {showOfflineUI && <OfflineModeUI {...} />}
      <div>Status: {isOnline ? 'Online' : 'Offline'}</div>
    </div>
  );
}
```

### 4. OfflineModeUI Component

Offline mode kullanıcı arayüzü bileşeni.

**Dosya:** `frontend/src/components/OfflineModeUI.tsx`

**Özellikler:**
- Full banner (top of page)
- Compact banner (bottom-right corner)
- Network status indicator
- Retry button
- Dismiss button

**Kullanım:**
```typescript
import { OfflineModeUI, CompactOfflineModeUI } from './components/OfflineModeUI';

// Full banner
<OfflineModeUI
  networkState={networkState}
  offlineModeState={offlineModeState}
  onRetry={retryCancelledRequests}
  onDismiss={() => console.log('Dismissed')}
/>

// Compact banner
<CompactOfflineModeUI
  networkState={networkState}
  offlineModeState={offlineModeState}
  onRetry={retryCancelledRequests}
/>
```

## 📖 Kullanım

### Temel Kullanım

```typescript
import React from 'react';
import { useOfflineMode } from './hooks/useOfflineMode';
import { OfflineModeUI } from './components/OfflineModeUI';

function MyApp() {
  const {
    isOnline,
    showOfflineUI,
    networkState,
    offlineModeState,
    retryCancelledRequests,
  } = useOfflineMode();

  return (
    <div>
      {/* Offline Mode UI */}
      <OfflineModeUI
        networkState={networkState}
        offlineModeState={offlineModeState}
        onRetry={retryCancelledRequests}
      />

      {/* Main Content */}
      <div>
        <h1>My App</h1>
        <p>Status: {isOnline ? 'Online' : 'Offline'}</p>
      </div>
    </div>
  );
}
```

### VideoLoadingManager ile Entegrasyon

```typescript
import React from 'react';
import { useOfflineMode } from './hooks/useOfflineMode';
import { OfflineModeUI } from './components/OfflineModeUI';
import { VideoLoadingManager } from './services/VideoLoadingManager';

function VideoPage() {
  const videoManagerRef = React.useRef<VideoLoadingManager | null>(null);

  // Initialize VideoLoadingManager
  React.useEffect(() => {
    videoManagerRef.current = new VideoLoadingManager('http://localhost:8001', 20000, 2);
  }, []);

  // Use offline mode with VideoLoadingManager
  const {
    isOnline,
    isOffline,
    showOfflineUI,
    networkState,
    offlineModeState,
    retryCancelledRequests,
    registerPendingRequest,
    unregisterPendingRequest,
  } = useOfflineMode({
    videoLoadingManager: videoManagerRef.current || undefined,
    autoRetryOnReconnection: true,
  });

  // Load videos
  const loadVideos = async () => {
    // Check if offline
    if (isOffline) {
      alert('İnternet bağlantısı yok!');
      return;
    }

    const requestId = `video-load-${Date.now()}`;

    try {
      // Register pending request
      registerPendingRequest(requestId);

      // Load videos
      const recommendations = await videoManagerRef.current.loadVideos(profile);

      // Unregister pending request
      unregisterPendingRequest(requestId);
    } catch (error) {
      unregisterPendingRequest(requestId);
      throw error;
    }
  };

  return (
    <div>
      <OfflineModeUI
        networkState={networkState}
        offlineModeState={offlineModeState}
        onRetry={retryCancelledRequests}
      />

      <button onClick={loadVideos} disabled={isOffline}>
        Load Videos
      </button>
    </div>
  );
}
```

## 📚 API Referansı

### NetworkDetector

#### Methods

- `getState(): NetworkState` - Mevcut network durumunu döndürür
- `isOnline(): boolean` - Online durumunu kontrol eder
- `isOffline(): boolean` - Offline durumunu kontrol eder
- `isSlow(): boolean` - Yavaş bağlantı kontrolü
- `getOfflineDuration(): number | null` - Offline süresi (ms)
- `subscribe(callback): () => void` - State değişikliklerine subscribe
- `onReconnection(callback): () => void` - Reconnection event'ine subscribe
- `checkConnection(): Promise<boolean>` - Manuel bağlantı kontrolü
- `resetReconnectionAttempts(): void` - Reconnection attempt'leri sıfırla
- `destroy(): void` - Cleanup

#### NetworkState

```typescript
interface NetworkState {
  status: 'online' | 'offline' | 'slow' | 'unknown';
  isOnline: boolean;
  lastOnlineTime: number | null;
  lastOfflineTime: number | null;
  reconnectionAttempts: number;
  effectiveType?: string; // '4g', '3g', '2g', 'slow-2g'
  downlink?: number; // Mbps
  rtt?: number; // Round-trip time in ms
}
```

### OfflineModeManager

#### Methods

- `getState(): OfflineModeState` - Mevcut offline mode durumunu döndürür
- `isOffline(): boolean` - Offline durumunu kontrol eder
- `shouldShowOfflineUI(): boolean` - Offline UI gösterilmeli mi?
- `getOfflineDuration(): number | null` - Offline süresi (ms)
- `getPendingRequestsCount(): number` - Pending request sayısı
- `subscribe(callback): () => void` - State değişikliklerine subscribe
- `checkConnection(): Promise<boolean>` - Manuel bağlantı kontrolü
- `retryCancelledRequests(): void` - Cancelled request'leri retry et
- `registerPendingRequest(requestId): void` - Pending request kaydet
- `unregisterPendingRequest(requestId): void` - Pending request'i kaldır
- `setVideoLoadingManager(manager): void` - VideoLoadingManager set et
- `destroy(): void` - Cleanup

#### OfflineModeState

```typescript
interface OfflineModeState {
  isOffline: boolean;
  showOfflineUI: boolean;
  offlineDuration: number | null;
  pendingRequests: Set<string>;
  cancelledRequests: Set<string>;
  reconnectionInProgress: boolean;
}
```

### useOfflineMode Hook

#### Options

```typescript
interface UseOfflineModeOptions {
  videoLoadingManager?: VideoLoadingManager;
  autoRetryOnReconnection?: boolean; // Default: true
  maxReconnectionAttempts?: number; // Default: 5
  reconnectionDelay?: number; // Default: 2000ms
}
```

#### Return Value

```typescript
interface UseOfflineModeReturn {
  // Network state
  networkState: NetworkState;
  isOnline: boolean;
  isOffline: boolean;
  isSlow: boolean;
  
  // Offline mode state
  offlineModeState: OfflineModeState;
  showOfflineUI: boolean;
  offlineDuration: number | null;
  pendingRequestsCount: number;
  reconnectionInProgress: boolean;
  
  // Actions
  checkConnection: () => Promise<boolean>;
  retryCancelledRequests: () => void;
  registerPendingRequest: (requestId: string) => void;
  unregisterPendingRequest: (requestId: string) => void;
  
  // Managers
  networkDetector: NetworkDetector;
  offlineModeManager: OfflineModeManager;
}
```

## 💡 Örnekler

Detaylı örnekler için `OfflineMode.example.tsx` dosyasına bakın:

1. **BasicOfflineModeExample** - Basit offline/online durumu
2. **FullOfflineModeExample** - Tam offline mode UI entegrasyonu
3. **CompactOfflineModeExample** - Compact banner kullanımı
4. **VideoLoadingWithOfflineModeExample** - VideoLoadingManager entegrasyonu
5. **AutoRetryExample** - Otomatik retry örneği
6. **RequestCancellationExample** - Request cancellation örneği
7. **SlowConnectionExample** - Yavaş bağlantı uyarısı
8. **CompleteIntegrationExample** - Tam entegrasyon örneği

## 🔧 Troubleshooting

### Problem: Offline UI gösterilmiyor

**Çözüm:**
- `showOfflineUI` state'ini kontrol edin
- `OfflineModeUI` component'inin render edildiğinden emin olun
- Browser console'da network event'lerini kontrol edin

### Problem: Auto-retry çalışmıyor

**Çözüm:**
- `autoRetryOnReconnection: true` olduğundan emin olun
- `VideoLoadingManager` instance'ının doğru set edildiğini kontrol edin
- Reconnection callback'lerinin register edildiğini kontrol edin

### Problem: Request cancellation çalışmıyor

**Çözüm:**
- `registerPendingRequest()` ve `unregisterPendingRequest()` çağrılarını kontrol edin
- `beforeunload` event listener'ının eklendiğinden emin olun
- Browser console'da cancelled request loglarını kontrol edin

### Problem: Yavaş bağlantı tespit edilmiyor

**Çözüm:**
- Browser'ın Network Information API'yi desteklediğinden emin olun
- Fallback ping test'inin çalıştığını kontrol edin
- `networkState.rtt` ve `networkState.effectiveType` değerlerini kontrol edin

## 📝 Requirements

Bu implementasyon aşağıdaki requirement'ları karşılar:

- **Requirement 5.19:** Offline mode desteği ve network bağlantısı geri geldiğinde otomatik sync
- **Requirement 10.6:** Network status izleme (online/offline detection)
- **Requirement 10.7:** Request cancellation (kullanıcı sayfadan ayrılırsa)

## 🚀 Gelecek İyileştirmeler

- [ ] Service Worker entegrasyonu (offline caching)
- [ ] IndexedDB ile offline data storage
- [ ] Background sync API kullanımı
- [ ] Progressive Web App (PWA) özellikleri
- [ ] Offline analytics tracking
- [ ] Network quality based video quality adjustment

## 📄 Lisans

Bu kod Teknofest 2025 Eğitim Eylemci Platformu projesi kapsamında geliştirilmiştir.
