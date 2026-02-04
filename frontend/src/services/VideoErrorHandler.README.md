# VideoErrorHandler - Video Yükleme Hata Yönetimi

## Genel Bakış

`VideoErrorHandler`, Learning Path sayfasında video yükleme sırasında oluşan hataları yönetmek için tasarlanmış kapsamlı bir hata yönetim servisidir. Hataları sınıflandırır, kullanıcı dostu Türkçe mesajlar üretir ve retry kararları verir.

## Özellikler

- ✅ **Hata Sınıflandırma**: Timeout, network, server, CORS, rate limit, validation
- ✅ **Kullanıcı Dostu Mesajlar**: Türkçe, emoji'li, anlaşılır mesajlar
- ✅ **Retry Kararı**: Hangi hataların tekrar denenmesi gerektiğini belirler
- ✅ **Structured Logging**: Console ve Sentry entegrasyonu
- ✅ **Context Tracking**: Request ID, endpoint, retry count takibi
- ✅ **TypeScript Support**: Tam tip güvenliği

## Kurulum

```typescript
import { VideoErrorHandler, getVideoErrorHandler } from '@/services/VideoErrorHandler';

// Singleton instance kullanımı (önerilen)
const errorHandler = getVideoErrorHandler();

// Veya yeni instance oluşturma
const customHandler = new VideoErrorHandler(
  true,  // Sentry logging aktif
  true   // Console logging aktif
);
```

## Temel Kullanım

### 1. Basit Hata İşleme

```typescript
import { getVideoErrorHandler } from '@/services/VideoErrorHandler';

const errorHandler = getVideoErrorHandler();

try {
  const response = await fetch('/api/youtube/recommendations', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
  
  if (!response.ok) {
    throw new Error(`Backend error: ${response.status}`);
  }
} catch (error) {
  // Hatayı işle
  const videoError = errorHandler.handleError(error, {
    requestId: 'req_123',
    endpoint: '/api/youtube/recommendations',
    retryCount: 0,
  });
  
  // Kullanıcıya mesaj göster
  console.log(videoError.userMessage);
  // "🔧 Sunucu hatası oluştu. Lütfen birkaç dakika sonra tekrar deneyin."
  
  // Retry kararı ver
  if (errorHandler.shouldRetry(videoError)) {
    // Tekrar dene
    console.log('Retrying...');
  }
}
```

### 2. VideoLoadingManager ile Entegrasyon

```typescript
import { VideoLoadingManager } from '@/services/VideoLoadingManager';
import { getVideoErrorHandler } from '@/services/VideoErrorHandler';

const loadingManager = new VideoLoadingManager();
const errorHandler = getVideoErrorHandler();

try {
  const videos = await loadingManager.loadVideos(profile);
  console.log('Videos loaded:', videos);
} catch (error) {
  const videoError = errorHandler.handleError(error, {
    requestId: loadingManager.getState().requestId,
    retryCount: loadingManager.getState().retryCount,
  });
  
  // UI'da hata mesajı göster
  setErrorMessage(videoError.userMessage);
  
  // Retry butonu göster
  setShowRetryButton(videoError.retryable);
}
```

### 3. Helper Functions

```typescript
import { getQuickErrorMessage, isRetryableError } from '@/services/VideoErrorHandler';

// Hızlı mesaj alma
try {
  // ... API call
} catch (error) {
  const message = getQuickErrorMessage(error);
  alert(message);
}

// Retry kontrolü
try {
  // ... API call
} catch (error) {
  if (isRetryableError(error)) {
    setTimeout(() => retry(), 2000);
  }
}
```

## Hata Tipleri

### 1. Timeout (`timeout`)
- **Neden**: İstek zaman aşımına uğradı
- **Retryable**: ✅ Evet
- **Mesaj**: "⏰ İstek zaman aşımına uğradı. Lütfen tekrar deneyin."
- **Aksiyon**: `retry`

```typescript
const error = new Error('Request timeout');
error.name = 'AbortError';
```

### 2. Network (`network`)
- **Neden**: İnternet bağlantı hatası
- **Retryable**: ✅ Evet
- **Mesaj**: "🌐 İnternet bağlantınızı kontrol edin ve tekrar deneyin."
- **Aksiyon**: `retry`

```typescript
const error = new Error('Failed to fetch');
error.name = 'TypeError';
```

### 3. Server (`server`)
- **Neden**: Sunucu hatası (5xx)
- **Retryable**: ✅ Evet (503 hariç)
- **Mesaj**: "🔧 Sunucu hatası oluştu. Lütfen birkaç dakika sonra tekrar deneyin."
- **Aksiyon**: `retry`

```typescript
const error = new Error('Backend error: 500 Internal Server Error');
```

### 4. CORS (`cors`)
- **Neden**: CORS politika hatası
- **Retryable**: ❌ Hayır
- **Mesaj**: "🔒 Bağlantı güvenlik hatası oluştu. Lütfen sistem yöneticisi ile iletişime geçin."
- **Aksiyon**: `contact_admin`

```typescript
const error = new Error('CORS policy blocked');
```

### 5. Rate Limit (`rate_limit`)
- **Neden**: Çok fazla istek
- **Retryable**: ❌ Hayır
- **Mesaj**: "⚡ Çok fazla istek gönderildi. Lütfen 1-2 dakika bekleyip tekrar deneyin."
- **Aksiyon**: `wait_and_retry`

```typescript
const error = new Error('Backend error: 429 Too Many Requests');
```

### 6. Validation (`validation`)
- **Neden**: Veri doğrulama hatası (4xx)
- **Retryable**: ❌ Hayır
- **Mesaj**: "📝 Gönderilen veri geçersiz. Lütfen bilgilerinizi kontrol edin."
- **Aksiyon**: `check_input`

```typescript
const error = new Error('Backend error: 400 Bad Request');
```

### 7. Unknown (`unknown`)
- **Neden**: Bilinmeyen hata
- **Retryable**: ✅ Evet (bir kez)
- **Mesaj**: "❓ Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin."
- **Aksiyon**: `retry`

## API Referansı

### VideoErrorHandler Class

#### Constructor

```typescript
constructor(
  sentryEnabled: boolean = false,
  consoleLoggingEnabled: boolean = true
)
```

#### Methods

##### handleError()
```typescript
handleError(error: unknown, context?: ErrorContext): VideoError
```
Hatayı işler ve VideoError nesnesine dönüştürür.

##### getUserMessage()
```typescript
getUserMessage(error: VideoError): string
```
Kullanıcı dostu hata mesajını döndürür.

##### shouldRetry()
```typescript
shouldRetry(error: VideoError): boolean
```
Hatanın tekrar denenebilir olup olmadığını kontrol eder.

##### logError()
```typescript
logError(error: VideoError, context?: ErrorContext): void
```
Hatayı console ve Sentry'ye loglar.

##### handleMultipleErrors()
```typescript
handleMultipleErrors(errors: unknown[], context?: ErrorContext): VideoError[]
```
Birden fazla hatayı toplu işler.

##### getErrorStats()
```typescript
getErrorStats(errors: VideoError[]): Record<string, number>
```
Hata istatistiklerini döndürür.

### Interfaces

#### VideoError
```typescript
interface VideoError {
  type: VideoErrorType;
  message: string;
  userMessage: string;
  retryable: boolean;
  statusCode?: number;
  details?: Record<string, any>;
  timestamp: Date;
  requestId?: string;
  suggestedAction?: string;
}
```

#### ErrorContext
```typescript
interface ErrorContext {
  requestId?: string;
  endpoint?: string;
  profile?: Record<string, any>;
  retryCount?: number;
  loadingTime?: number;
  metadata?: Record<string, any>;
}
```

## Örnekler

### React Component ile Kullanım

```typescript
import React, { useState } from 'react';
import { VideoLoadingManager } from '@/services/VideoLoadingManager';
import { getVideoErrorHandler } from '@/services/VideoErrorHandler';

function VideoRecommendations() {
  const [error, setError] = useState<string | null>(null);
  const [showRetry, setShowRetry] = useState(false);
  
  const loadingManager = new VideoLoadingManager();
  const errorHandler = getVideoErrorHandler();
  
  const loadVideos = async () => {
    try {
      setError(null);
      const videos = await loadingManager.loadVideos(profile);
      // Success handling
    } catch (err) {
      const videoError = errorHandler.handleError(err, {
        requestId: loadingManager.getState().requestId,
        retryCount: loadingManager.getState().retryCount,
      });
      
      setError(videoError.userMessage);
      setShowRetry(videoError.retryable);
    }
  };
  
  return (
    <div>
      {error && (
        <div className="error-message">
          <p>{error}</p>
          {showRetry && (
            <button onClick={loadVideos}>🔄 Tekrar Dene</button>
          )}
        </div>
      )}
    </div>
  );
}
```

### Retry Logic ile Kullanım

```typescript
import { getVideoErrorHandler } from '@/services/VideoErrorHandler';

const errorHandler = getVideoErrorHandler();
const MAX_RETRIES = 3;

async function loadVideosWithRetry(profile: StudentProfile, retryCount = 0) {
  try {
    const response = await fetch('/api/youtube/recommendations', {
      method: 'POST',
      body: JSON.stringify(profile),
    });
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    const videoError = errorHandler.handleError(error, {
      retryCount,
      endpoint: '/api/youtube/recommendations',
    });
    
    // Retry kararı
    if (videoError.retryable && retryCount < MAX_RETRIES) {
      // Exponential backoff
      const delay = Math.min(1000 * Math.pow(2, retryCount), 5000);
      console.log(`Retrying in ${delay}ms...`);
      
      await new Promise(resolve => setTimeout(resolve, delay));
      return loadVideosWithRetry(profile, retryCount + 1);
    }
    
    // Max retries reached or not retryable
    throw videoError;
  }
}
```

### Error Statistics

```typescript
import { getVideoErrorHandler } from '@/services/VideoErrorHandler';

const errorHandler = getVideoErrorHandler();
const errors: VideoError[] = [];

// Collect errors
try {
  // ... API calls
} catch (error) {
  errors.push(errorHandler.handleError(error));
}

// Get statistics
const stats = errorHandler.getErrorStats(errors);
console.log('Error Statistics:', stats);
// { timeout: 5, network: 2, server: 1 }
```

## Best Practices

1. **Singleton Kullanımı**: Global instance için `getVideoErrorHandler()` kullanın
2. **Context Bilgisi**: Her zaman `requestId` ve `retryCount` ekleyin
3. **Retry Logic**: Exponential backoff kullanın
4. **User Feedback**: Kullanıcıya her zaman net mesaj gösterin
5. **Logging**: Production'da Sentry'yi aktif edin
6. **Error Boundaries**: React Error Boundary ile birlikte kullanın

## Testing

```typescript
import { describe, it, expect } from 'vitest';
import { VideoErrorHandler } from '@/services/VideoErrorHandler';

describe('VideoErrorHandler', () => {
  it('should classify timeout errors', () => {
    const handler = new VideoErrorHandler(false, false);
    const error = new Error('Timeout');
    error.name = 'AbortError';
    
    const videoError = handler.handleError(error);
    
    expect(videoError.type).toBe('timeout');
    expect(videoError.retryable).toBe(true);
  });
});
```

## Troubleshooting

### Sentry Entegrasyonu Çalışmıyor
```typescript
// Sentry SDK'nın yüklü olduğundan emin olun
import * as Sentry from '@sentry/react';

// VideoErrorHandler'ı Sentry ile başlatın
const handler = new VideoErrorHandler(true, true);
```

### Console'da Log Görünmüyor
```typescript
// Console logging'in aktif olduğundan emin olun
const handler = new VideoErrorHandler(false, true); // İkinci parametre true
```

### Retry Çalışmıyor
```typescript
// Hatanın retryable olduğunu kontrol edin
const videoError = handler.handleError(error);
console.log('Retryable:', videoError.retryable);
console.log('Suggested Action:', videoError.suggestedAction);
```

## İlgili Dosyalar

- `VideoLoadingManager.ts` - Video yükleme state management
- `VideoLoadingManager.test.ts` - VideoLoadingManager testleri
- `VideoErrorHandler.test.ts` - VideoErrorHandler testleri

## Requirements

Bu servis aşağıdaki requirement'ları karşılar:
- **1.2**: API hatalarını structured logging ile kaydetme
- **1.3**: Kullanıcı dostu hata mesajları
- **3.4**: Hata durumlarında retry ve fallback seçenekleri
- **3.10**: Hata mesajlarını kullanıcı dostu dilde açıklama
- **5.3**: Frontend hata durumlarını error tracking servisi ile raporlama
- **10.4**: Error recovery UI sağlama
- **10.6**: Network status izleme

## Lisans

MIT
