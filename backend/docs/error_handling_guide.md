# Error Handling ve Circuit Breaker Pattern - Kullanım Kılavuzu

## Genel Bakış

Learning Path Video Yükleme sistemi için kapsamlı hata yönetimi ve circuit breaker pattern implementasyonu.

**Dosya:** `backend/core/error_handler.py`

**Requirements:** 5.1, 5.2, 5.7, 5.8, 5.9, 5.18

## Özel Exception Sınıfları

### VideoAPIError (Base Class)
Tüm video API hatalarının temel sınıfı.

```python
from core.error_handler import VideoAPIError

raise VideoAPIError(
    message="Video yükleme başarısız",
    severity=ErrorSeverity.MEDIUM,
    user_message="Videolar şu anda yüklenemiyor"
)
```

### YouTubeAPIError
YouTube API'ye özel hatalar.

```python
from core.error_handler import YouTubeAPIError

# Rate limit hatası
raise YouTubeAPIError(
    message="YouTube API rate limit exceeded",
    status_code=429,
    quota_exceeded=False
)

# Quota hatası
raise YouTubeAPIError(
    message="YouTube API quota exceeded",
    quota_exceeded=True
)
```

### CacheError
Cache işlem hataları.

```python
from core.error_handler import CacheError

raise CacheError(
    message="Redis cache unavailable",
    operation="get",
    cache_type="redis"
)
```

### VideoDiscoveryError
Video bulma işlemi hataları.

```python
from core.error_handler import VideoDiscoveryError

raise VideoDiscoveryError(
    message="No videos found for subject",
    subject="matematik",
    search_type="semantic"
)
```

### VideoTimeoutError
Timeout hataları.

```python
from core.error_handler import VideoTimeoutError

raise VideoTimeoutError(
    message="Video search timeout",
    timeout_seconds=10.0,
    operation="search"
)
```

## ErrorHandler Kullanımı

### Temel Kullanım

```python
from core.error_handler import ErrorHandler

handler = ErrorHandler()

try:
    # Risky operation
    result = await search_videos()
except Exception as error:
    # Hatayı sınıflandır ve işle
    classification = handler.handle_error(
        error=error,
        context={"subject": "matematik", "user_id": "123"},
        request_id="req-456"
    )
    
    # Kullanıcı mesajı al
    user_message = classification.user_message
    
    # Retry kararı
    if classification.retryable:
        await asyncio.sleep(classification.retry_after)
        # Retry logic
```

### Hata Sınıflandırma

```python
# Hatayı sınıflandır
classification = handler.classify_error(error)

print(f"Category: {classification.category}")  # ErrorCategory.TIMEOUT
print(f"Severity: {classification.severity}")  # ErrorSeverity.MEDIUM
print(f"Retryable: {classification.retryable}")  # True
print(f"Retry after: {classification.retry_after} seconds")  # 5
print(f"User message: {classification.user_message}")
print(f"Recovery actions: {classification.recovery_actions}")
```

### Kullanıcı Mesajı Alma

```python
# Kullanıcı dostu mesaj al
user_message = handler.get_user_message(error)
# "Video yükleme zaman aşımına uğradı. Lütfen tekrar deneyin."
```

### Retry Kararı

```python
# Retry yapılmalı mı?
should_retry, retry_after = handler.should_retry(error)

if should_retry:
    await asyncio.sleep(retry_after)
    # Retry operation
```

### Recovery Actions

```python
# Önerilen recovery aksiyonları
actions = handler.get_recovery_actions(error)
# ['retry', 'use_cache', 'fallback']

for action in actions:
    if action == 'use_cache':
        result = await get_from_cache()
    elif action == 'fallback':
        result = get_fallback_videos()
```

### Error Metrics

```python
# Hata metriklerini al
metrics = handler.get_error_metrics()

print(f"Total errors: {metrics['total_errors']}")
print(f"Error counts: {metrics['error_counts']}")
print(f"Last errors: {metrics['last_errors']}")
```

## CircuitBreaker Kullanımı

### Temel Kullanım

```python
from core.error_handler import CircuitBreaker, CircuitBreakerConfig

# Circuit breaker oluştur
config = CircuitBreakerConfig(
    failure_threshold=5,      # 5 hata sonrası aç
    success_threshold=2,      # 2 başarı sonrası kapat
    timeout=60,               # 60 saniye sonra half-open
    half_open_max_calls=3     # Half-open'da max 3 çağrı
)

breaker = CircuitBreaker(
    name="youtube-api",
    config=config
)

# Fonksiyonu circuit breaker ile çağır
try:
    result = await breaker.call(
        search_youtube_videos,
        subject="matematik",
        max_results=10
    )
except CircuitBreakerOpenError as e:
    # Circuit açık, fallback kullan
    result = get_cached_videos()
```

### Circuit State Kontrolü

```python
from core.error_handler import CircuitState

# Mevcut durumu kontrol et
if breaker.state == CircuitState.CLOSED:
    # Normal operation
    pass
elif breaker.state == CircuitState.OPEN:
    # Circuit açık, fallback kullan
    pass
elif breaker.state == CircuitState.HALF_OPEN:
    # Test ediliyor
    pass
```

### Circuit Breaker İstatistikleri

```python
# İstatistikleri al
stats = breaker.get_stats()

print(f"State: {stats.state}")
print(f"Total calls: {stats.total_calls}")
print(f"Total failures: {stats.total_failures}")
print(f"Total successes: {stats.total_successes}")
print(f"Failure count: {stats.failure_count}")
print(f"Last failure: {stats.last_failure_time}")
```

### Circuit Breaker Reset

```python
# Circuit breaker'ı sıfırla
breaker.reset()
```

## Örnek Senaryolar

### Senaryo 1: YouTube API ile Video Arama

```python
from core.error_handler import (
    ErrorHandler,
    CircuitBreaker,
    CircuitBreakerConfig,
    YouTubeAPIError
)

# Setup
handler = ErrorHandler()
breaker = CircuitBreaker(
    "youtube-api",
    CircuitBreakerConfig(failure_threshold=3, timeout=60)
)

async def search_videos_with_protection(subject: str):
    """Circuit breaker ve error handling ile video arama"""
    try:
        # Circuit breaker ile çağır
        videos = await breaker.call(
            youtube_api.search,
            subject=subject
        )
        return videos
        
    except CircuitBreakerOpenError as e:
        # Circuit açık, cache kullan
        handler.logger.warning(f"Circuit open, using cache: {e}")
        return await get_cached_videos(subject)
        
    except YouTubeAPIError as e:
        # YouTube API hatası
        classification = handler.handle_error(e)
        
        if classification.retryable:
            # Retry
            await asyncio.sleep(classification.retry_after)
            return await get_cached_videos(subject)
        else:
            # Fallback
            return get_fallback_videos(subject)
            
    except Exception as e:
        # Beklenmeyen hata
        classification = handler.handle_error(e)
        return get_fallback_videos(subject)
```

### Senaryo 2: Cache ile Fallback

```python
async def get_videos_with_fallback(subject: str):
    """Multi-layer fallback stratejisi"""
    try:
        # 1. Try primary source
        return await breaker.call(youtube_api.search, subject)
        
    except CircuitBreakerOpenError:
        # 2. Try cache
        try:
            cached = await cache.get(f"videos:{subject}")
            if cached:
                return cached
        except CacheError as e:
            handler.logger.warning(f"Cache error: {e}")
        
        # 3. Fallback to static videos
        return get_fallback_videos(subject)
```

### Senaryo 3: Retry Logic

```python
async def search_with_retry(subject: str, max_retries: int = 3):
    """Exponential backoff ile retry"""
    for attempt in range(max_retries):
        try:
            return await breaker.call(youtube_api.search, subject)
            
        except Exception as e:
            classification = handler.handle_error(e)
            
            if not classification.retryable or attempt == max_retries - 1:
                # Son deneme veya retry yapılamaz
                raise
            
            # Exponential backoff
            wait_time = classification.retry_after * (2 ** attempt)
            handler.logger.info(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
            await asyncio.sleep(wait_time)
```

## Error Categories

| Category | Description | Retryable | Typical Retry After |
|----------|-------------|-----------|---------------------|
| NETWORK | Network connectivity issues | Yes | 10s |
| TIMEOUT | Operation timeout | Yes | 5s |
| RATE_LIMIT | Rate limiting | Yes | 60s |
| QUOTA | API quota exceeded | Yes | 3600s |
| AUTHENTICATION | Auth failures | No | - |
| AUTHORIZATION | Permission issues | No | - |
| VALIDATION | Input validation | No | - |
| NOT_FOUND | Resource not found | Yes | 10s |
| SERVER_ERROR | Server-side errors | Yes | 30s |
| CLIENT_ERROR | Client-side errors | No | - |
| CACHE | Cache errors | Yes | 5s |
| DATABASE | Database errors | Yes | 10s |
| UNKNOWN | Unknown errors | No | - |

## Error Severity Levels

| Severity | Description | Action |
|----------|-------------|--------|
| LOW | Minor issues, system functional | Log, continue |
| MEDIUM | Moderate issues, degraded service | Log, retry, fallback |
| HIGH | Serious issues, service impacted | Log, alert, fallback |
| CRITICAL | Critical issues, service down | Log, alert, emergency fallback |

## Best Practices

1. **Her zaman ErrorHandler kullan**: Tüm hataları ErrorHandler üzerinden işle
2. **Circuit Breaker ile koruma**: External servisleri circuit breaker ile koru
3. **Fallback stratejisi**: Her zaman fallback seçeneği hazırla
4. **User-friendly mesajlar**: Kullanıcıya teknik detay verme
5. **Structured logging**: Hataları context ile logla
6. **Metrics toplama**: Error metrics'i izle ve analiz et
7. **Retry logic**: Exponential backoff kullan
8. **Circuit breaker tuning**: Threshold'ları production verilerine göre ayarla

## Testing

Verification test dosyası: `backend/test_error_handler_verification.py`

```bash
# Testleri çalıştır
python test_error_handler_verification.py
```

## Requirements Mapping

- **5.1**: Structured logging with error context
- **5.2**: User-friendly error messages
- **5.7**: Error classification logic
- **5.8**: Recovery action determination
- **5.9**: Error recovery strategies (retry, fallback)
- **5.18**: Circuit breaker pattern for graceful degradation
