# Plan: Frontend PWA Offline Sync & SW Caching Testleri

## Kapsam ve Amaç
KIRO2 PWA (Progressive Web App) altyapısının offline çalışma modunun, Service Worker (sw.js) önbellekleme stratejilerinin (network-first, cache-first, queue-fallback) ve IndexedDB tabanlı arka plan senkronizasyonunun (Background Sync) doğruluk testlerinin yazılması ve %100 test yeşillemesinin sağlanması.

## Bileşenler ve Test Kapsamı

1. **`frontend/src/test/pwa-offline-sw.test.ts` (Yeni Kapsamlı PWA SW Testi):**
   - **Service Worker Önbellekleme Stratejileri:**
     - `/api/*` GET isteklerinde Network-first önbellekleme ve offline fallback doğrulaması.
     - Statik varlıklarda (`.js`, `.css`, fontlar) Cache-first stratejisi.
     - `/api/*` POST isteklerinde offline durumda IndexedDB kuyruğuna ekleme (202 Accepted dönme).
   - **Service Worker Yaşam Döngüsü (Lifecycle & Versioning):**
     - `install` olayı esnasında `kiro2-v1` önbelleğine app shell (`/`, `/index.html`) yükleme.
     - `activate` olayı esnasında eski versiyon önbellek temizleme (`caches.delete`).
   - **Arka Plan Senkronizasyonu (Background Sync Replay):**
     - `sync` olayında IndexedDB kuyruğundaki kaydetmelerin sırayla sunucuya gönderilmesi ve silinmesi.

2. **`frontend/src/services/offlineStorageService.ts` & `backgroundSyncService.ts` Doğrulaması:**
   - Offline sınav/kart çözümlerinin yerel depolamaya (LocalStorage / IndexedDB) yazılması ve online olunduğunda otomatik senkronizasyonu.

3. **Kod Kalitesi ve Tip Doğrulaması:**
   - `npm run type-check` (0 Hata).
   - `npx vitest run src/test/pwa-offline-sw.test.ts src/test/pwa.test.ts` (%100 PASS).
