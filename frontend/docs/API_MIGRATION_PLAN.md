# API Migration Plan: api.ts → modernApiClient.ts

**Hedef:** Legacy `api.ts` (fetch-based) → Modern `modernApiClient.ts` (Axios-based)

**Durum:** 2025-11-17
**Öncelik:** P1 (High Priority)
**Tahmini Süre:** 2-3 gün

---

## 📊 MEVCUT DURUM ANALİZİ

### API Clients Karşılaştırması

| Özellik | api.ts (Legacy) | modernApiClient.ts | apiClient.ts |
|---------|-----------------|-------------------|--------------|
| **HTTP Library** | fetch (native) | Axios | Axios |
| **Kullanım** | 63 dosya | 5 dosya | 20+ dosya |
| **Token Yönetimi** | Manuel | Otomatik | Otomatik + Refresh |
| **Cache** | ApiCache class | In-memory Map | ❌ |
| **Retry Logic** | withRetry helper | Built-in | ❌ |
| **Rate Limiting** | RateLimiter class | ❌ | ❌ |
| **Request Deduplication** | ❌ | ✅ | ❌ |
| **Performance Tracking** | ❌ | ✅ | ❌ |
| **Type Safety** | Partial | Full | Full |

### Fonksiyon Sayıları

```
api.ts: 80+ fonksiyon
├─ Learning Path: 5
├─ RAG: 13
├─ Student Dashboard: 12
├─ Learning Style: 10
├─ YouTube: 4
├─ Performance: 7
├─ OSYM Questions: 10+
└─ Other: 20+
```

---

## 🎯 MİGRATION STRATEJİSİ

### Faz 1: Altyapı Hazırlığı (1 gün)

**Hedef:** modernApiClient.ts'i api.ts ile uyumlu hale getir

**Yapılacaklar:**

1. ✅ **Base URL standardizasyonu** - COMPLETED
   - Config import eklendi
   - Port tutarsızlığı düzeltildi

2. **modernApiClient'e eksik özellikler ekle:**
   ```typescript
   // Rate limiting desteği
   class ModernApiClient {
     private rateLimiter = new RateLimiter(10, 100);

     async get<T>(url: string, config?: RequestConfig) {
       return this.rateLimiter.execute(() => this.client.get<T>(url, config));
     }
   }
   ```

3. **Wrapper API oluştur:**
   ```typescript
   // api.modern.ts - Uyumluluk katmanı
   import { apiClient } from './modernApiClient';

   // Backward compatibility wrappers
   export async function sendChatMessage(agent: string, message: string) {
     return apiClient.post('/api/chat', { agent, message });
   }
   ```

### Faz 2: Kademeli Migration (1 gün)

**Hedef:** Kritik modülleri önce migrate et

**Migration Sırası:**

1. **Learning Path API** (öncelik: yüksek)
   - `createStudentProfile` ✅ (token eklendi)
   - `assessKnowledge` ✅
   - `createLearningPath` ✅
   - `searchResources` ✅
   - `adaptLearningPath` ✅

2. **Student Dashboard API**
   - `getDashboardStats`
   - `getExamHistory`
   - `getPerformanceTrend`
   - `getGoals` / `createGoal` / `updateGoal`

3. **YouTube & RAG API**
   - `searchYouTubeVideos`
   - `getYouTubeRecommendations`
   - `hybridSearchRAG`
   - `multiQuerySearchRAG`

4. **Diğer Modüller**
   - Learning Style
   - Performance Metrics
   - OSYM Questions

### Faz 3: Test & Doğrulama (0.5 gün)

**Yapılacaklar:**

1. **Unit Tests:**
   ```typescript
   // api.modern.test.ts
   describe('Modern API Client Migration', () => {
     it('should handle auth token automatically', async () => {
       const result = await getDashboardStats();
       expect(result).toBeDefined();
     });

     it('should cache GET requests', async () => {
       const result1 = await getAgents();
       const result2 = await getAgents(); // Should hit cache
       expect(result1).toEqual(result2);
     });
   });
   ```

2. **Integration Tests:**
   - Login flow
   - Token refresh
   - API error handling
   - Rate limiting

3. **Performance Tests:**
   - Response time comparison
   - Cache hit rate
   - Request deduplication

### Faz 4: Cleanup (0.5 gün)

**Yapılacaklar:**

1. **api.ts deprecation:**
   ```typescript
   /**
    * @deprecated Use modernApiClient instead
    * This file will be removed in v2.0.0
    */
   export async function sendChatMessage(...) {
     console.warn('sendChatMessage is deprecated. Use modernApiClient.post() instead.');
     return modernApiClient.post('/api/chat', ...);
   }
   ```

2. **Update imports:**
   ```bash
   # Find all imports
   grep -r "from.*api'" src/

   # Replace with modernApiClient
   sed -i "s/from '.*\/api'/from '.*\/modernApiClient'/g" src/**/*.ts
   ```

3. **Remove legacy code:**
   - ApiCache class → Use modernApiClient's cache
   - RateLimiter → Integrate into modernApiClient
   - withRetry helper → Use Axios retry

---

## 📋 IMPLEMENTATION CHECKLIST

### Hazırlık
- [x] Base URL standardizasyonu
- [x] Config centralization
- [x] Token injection helper (getAuthHeaders)
- [ ] modernApiClient rate limiting
- [ ] modernApiClient backward compatibility layer

### Migration
- [x] Learning Path API (5/5 fonksiyon)
- [ ] Student Dashboard API (0/12 fonksiyon)
- [ ] YouTube API (0/4 fonksiyon)
- [ ] RAG API (0/13 fonksiyon)
- [ ] Learning Style API (0/10 fonksiyon)
- [ ] Performance API (0/7 fonksiyon)
- [ ] OSYM Questions API (0/10 fonksiyon)

### Test & Doğrulama
- [ ] Unit tests (0/10)
- [ ] Integration tests (0/5)
- [ ] Performance tests (0/3)
- [ ] Load tests (0/2)

### Cleanup
- [ ] Deprecation warnings
- [ ] Import updates (0/63 dosya)
- [ ] Legacy code removal
- [ ] Documentation update

---

## 🚀 ÖRNEK MİGRATION

### Önce (api.ts):

```typescript
export async function getDashboardStats() {
  const response = await fetch(`${API_BASE_URL}/api/v1/student-dashboard/istatistikler`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    },
    signal: AbortSignal.timeout(config.api.timeout),
  })

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to get dashboard stats')
  }

  return response.json()
}
```

### Sonra (modernApiClient.ts):

```typescript
export async function getDashboardStats() {
  const response = await apiClient.get<DashboardStats>(
    '/api/v1/student-dashboard/istatistikler',
    { cache: true, retries: 3 }
  );

  return response.data;
}
```

**İyileştirmeler:**
- ✅ Otomatik token injection
- ✅ Otomatik error handling
- ✅ Cache support
- ✅ Retry logic
- ✅ Type safety
- ✅ Daha az kod (8 satır → 4 satır)

---

## ⚠️ RİSKLER VE ÇÖZÜMLERİ

### Risk 1: Breaking Changes
**Çözüm:** Backward compatibility layer (api.modern.ts)

### Risk 2: Performance Regression
**Çözüm:** A/B testing, performance metrics

### Risk 3: Cache Invalidation Sorunları
**Çözüm:** TTL ayarları, manual cache clear

### Risk 4: Token Refresh Race Conditions
**Çözüm:** Token refresh queue (apiClient.ts'de zaten var)

---

## 📈 BEKLENTİLER

### Performans İyileştirmeleri
- ⚡ Response time: %20-30 azalma (cache sayesinde)
- 📦 Bundle size: %10 azalma (kod optimize edilmesi)
- 🔄 Request deduplication: %40 azalma (duplicate requests)
- 💾 Network usage: %50 azalma (cache + deduplication)

### Code Quality
- 📝 Kod satırı: 1454 → ~800 (-%45)
- 🎯 Type safety: %70 → %100
- 🧪 Test coverage: %30 → %80
- 🐛 Error handling: Inconsistent → Consistent

### Developer Experience
- ⚙️ Daha az boilerplate
- 🔧 Merkezi configuration
- 🚀 Auto token refresh
- 📊 Performance tracking

---

## 🔄 ROLLBACK PLANI

Eğer migration başarısız olursa:

1. **Immediate Rollback:**
   ```bash
   git revert <migration-commit>
   ```

2. **Gradual Rollback:**
   - Yeni API'yi disable et
   - Legacy API'ye fallback
   - Hataları fix et, tekrar dene

3. **Feature Flag:**
   ```typescript
   const USE_MODERN_API = import.meta.env.VITE_USE_MODERN_API === 'true';

   export const apiClient = USE_MODERN_API ? modernApiClient : legacyApiClient;
   ```

---

## 📚 KAYNAKLAR

- [Axios Documentation](https://axios-http.com/)
- [Fetch vs Axios Comparison](https://blog.logrocket.com/axios-vs-fetch-best-http-requests/)
- [API Client Best Practices](https://kentcdodds.com/blog/replace-axios-with-a-simple-custom-fetch-wrapper)

---

**Next Steps:**
1. Review bu migration planını
2. Faz 1'i başlat (altyapı hazırlığı)
3. Learning Path migration'ı complete et
4. Diğer modüllere geç

**Estimated Completion:** 2-3 gün
**Risk Level:** Medium
**Impact:** High (Better performance, maintainability, DX)
