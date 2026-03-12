/**
 * KIRO2 Service Worker — F10 PWA Offline Mode
 *
 * Strategies:
 *   /api/*        — Network-first (fresh data preferred; cache as fallback)
 *   Static assets — Cache-first (JS, CSS, fonts, images)
 *   Background sync — Queue failed POST /api/* for retry when online
 */

const CACHE_NAME = 'kiro2-v1';
const OFFLINE_QUEUE = 'kiro2-offline-queue';

const STATIC_EXTENSIONS = ['.js', '.css', '.woff', '.woff2', '.ttf', '.png', '.jpg', '.svg', '.ico'];

// ---------------------------------------------------------------------------
// Install — pre-cache the app shell
// ---------------------------------------------------------------------------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      cache.addAll(['/', '/index.html'])
    ).then(() => self.skipWaiting())
  );
});

// ---------------------------------------------------------------------------
// Activate — claim clients and remove old caches
// ---------------------------------------------------------------------------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ---------------------------------------------------------------------------
// Fetch — route by request type
// ---------------------------------------------------------------------------
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only intercept same-origin and known external requests
  if (request.method !== 'GET' && request.method !== 'POST') return;

  const isApi = url.pathname.startsWith('/api/');
  const isStatic = STATIC_EXTENSIONS.some((ext) => url.pathname.endsWith(ext));

  if (isApi && request.method === 'GET') {
    event.respondWith(networkFirst(request));
  } else if (isApi && request.method === 'POST') {
    event.respondWith(networkWithQueueFallback(request));
  } else if (isStatic) {
    event.respondWith(cacheFirst(request));
  } else {
    // HTML navigation — network-first with offline fallback
    event.respondWith(networkFirst(request));
  }
});

// ---------------------------------------------------------------------------
// Background sync — replay queued POST requests
// ---------------------------------------------------------------------------
self.addEventListener('sync', (event) => {
  if (event.tag === OFFLINE_QUEUE) {
    event.waitUntil(replayQueue());
  }
});

// ---------------------------------------------------------------------------
// Strategy helpers
// ---------------------------------------------------------------------------

/** Network-first: try network, fall back to cache. */
async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await cache.match(request);
    return cached || offlineFallback(request);
  }
}

/** Cache-first: serve from cache, update in background. */
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch {
    return offlineFallback(request);
  }
}

/** Network with queue fallback for POST requests. */
async function networkWithQueueFallback(request) {
  try {
    return await fetch(request);
  } catch {
    await enqueueRequest(request);
    return new Response(
      JSON.stringify({ queued: true, message: 'Offline — request queued for sync' }),
      { status: 202, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

/** Minimal offline fallback response. */
function offlineFallback(request) {
  const accept = request.headers.get('Accept') || '';
  if (accept.includes('text/html')) {
    return caches.match('/index.html');
  }
  return new Response(
    JSON.stringify({ error: 'offline', message: 'No network connection' }),
    { status: 503, headers: { 'Content-Type': 'application/json' } }
  );
}

// ---------------------------------------------------------------------------
// Queue helpers (IndexedDB-based, minimal implementation)
// ---------------------------------------------------------------------------

async function enqueueRequest(request) {
  try {
    const body = await request.clone().text();
    const entry = {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      body,
      timestamp: Date.now(),
    };
    const db = await openQueueDb();
    const tx = db.transaction('queue', 'readwrite');
    tx.objectStore('queue').add(entry);
    await tx.complete;
    self.registration.sync.register(OFFLINE_QUEUE).catch(() => {});
  } catch (e) {
    // Silent — do not break the app if queuing fails
  }
}

async function replayQueue() {
  const db = await openQueueDb();
  const tx = db.transaction('queue', 'readwrite');
  const store = tx.objectStore('queue');
  const all = await store.getAll();
  for (const entry of all) {
    try {
      await fetch(entry.url, {
        method: entry.method,
        headers: entry.headers,
        body: entry.body || undefined,
      });
      store.delete(entry.id);
    } catch {
      // Will retry on next sync event
    }
  }
}

function openQueueDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('kiro2-sw-queue', 1);
    req.onupgradeneeded = (e) => {
      e.target.result.createObjectStore('queue', { keyPath: 'id', autoIncrement: true });
    };
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = (e) => reject(e.target.error);
  });
}
