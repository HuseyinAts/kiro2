/**
 * KIRO2 Service Worker
 * Advanced caching strategy for Turkish educational content
 */

/// <reference lib="webworker" />

import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { BackgroundSyncPlugin } from 'workbox-background-sync';
import { BroadcastUpdatePlugin } from 'workbox-broadcast-update';

declare const self: ServiceWorkerGlobalScope;

// Precache all static assets
precacheAndRoute(self.__WB_MANIFEST);

// Clean up outdated caches
cleanupOutdatedCaches();

// Cache strategy for API calls
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 60 * 15, // 15 minutes
      }),
      new BroadcastUpdatePlugin(),
    ],
  })
);

// Cache strategy for user data
registerRoute(
  ({ url }) => url.pathname.match(/\/api\/(profile|settings|preferences)/),
  new StaleWhileRevalidate({
    cacheName: 'user-data-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 60 * 30, // 30 minutes
      }),
    ],
  })
);

// Cache strategy for exam content
registerRoute(
  ({ url }) => url.pathname.match(/\/api\/(exams|questions|results)/),
  new NetworkFirst({
    cacheName: 'exam-content-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 200,
        maxAgeSeconds: 60 * 60, // 1 hour
      }),
    ],
  })
);

// Cache strategy for static content (Turkish educational materials)
registerRoute(
  ({ url }) => url.pathname.match(/\/api\/(content|materials|resources)/),
  new StaleWhileRevalidate({
    cacheName: 'educational-content-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 300,
        maxAgeSeconds: 60 * 60 * 24, // 24 hours
      }),
    ],
  })
);

// Cache strategy for images and media
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
      }),
    ],
  })
);

// Cache strategy for fonts (including Turkish character support)
registerRoute(
  ({ request }) => request.destination === 'font',
  new CacheFirst({
    cacheName: 'fonts-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 30,
        maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
      }),
    ],
  })
);

// Cache strategy for Google Fonts (Turkish character support)
registerRoute(
  ({ url }) => url.origin === 'https://fonts.googleapis.com',
  new StaleWhileRevalidate({
    cacheName: 'google-fonts-stylesheets',
  })
);

registerRoute(
  ({ url }) => url.origin === 'https://fonts.gstatic.com',
  new CacheFirst({
    cacheName: 'google-fonts-webfonts',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 30,
        maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
      }),
    ],
  })
);

// Cache strategy for JavaScript and CSS
registerRoute(
  ({ request }) => 
    request.destination === 'script' || 
    request.destination === 'style',
  new StaleWhileRevalidate({
    cacheName: 'static-resources',
  })
);

// Background sync for form submissions
const bgSyncPlugin = new BackgroundSyncPlugin('form-sync-queue', {
  maxRetentionTime: 24 * 60 // Retry for max of 24 Hours (specified in minutes)
});

registerRoute(
  ({ url, request }) => 
    url.pathname.match(/\/api\/(submit|save|update)/) && 
    request.method === 'POST',
  new NetworkFirst({
    cacheName: 'form-submissions',
    plugins: [bgSyncPlugin]
  })
);

// Navigation route (SPA support)
const navigationRoute = new NavigationRoute(
  new StaleWhileRevalidate({
    cacheName: 'navigation-cache',
  })
);

registerRoute(navigationRoute);

// Handle offline scenarios with custom offline page
const OFFLINE_VERSION = 1;
const CACHE_NAME = 'offline-v' + OFFLINE_VERSION;
const OFFLINE_URL = '/offline.html';

// Install event - cache offline page
self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      await cache.add(new Request(OFFLINE_URL, { cache: 'reload' }));
    })()
  );
  
  // Skip waiting to activate immediately
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      // Enable navigation preload if supported
      if ('navigationPreload' in self.registration) {
        await self.registration.navigationPreload.enable();
      }
      
      // Clean up old caches
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })()
  );
  
  // Claim all clients immediately
  self.clients.claim();
});

// Fetch event - serve offline page when needed
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      (async () => {
        try {
          // Try network first
          const preloadResponse = await event.preloadResponse;
          if (preloadResponse) {
            return preloadResponse;
          }

          const networkResponse = await fetch(event.request);
          return networkResponse;
        } catch (error) {
          // Network failed, serve offline page
          console.log('Fetch failed; returning offline page instead.', error);
          
          const cache = await caches.open(CACHE_NAME);
          const cachedResponse = await cache.match(OFFLINE_URL);
          return cachedResponse;
        }
      })()
    );
  }
});

// Handle background sync events
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  // Implement background sync logic for Turkish educational platform
  console.log('Background sync triggered');
  
  try {
    // Sync user progress
    await syncUserProgress();
    
    // Sync exam results
    await syncExamResults();
    
    // Sync learning analytics
    await syncLearningAnalytics();
    
    console.log('Background sync completed successfully');
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

async function syncUserProgress() {
  // Sync user learning progress to server
  const progressData = await getStoredProgressData();
  if (progressData.length > 0) {
    try {
      await fetch('/api/sync/progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(progressData),
      });
      
      // Clear synced data from local storage
      await clearStoredProgressData();
    } catch (error) {
      console.error('Failed to sync progress data:', error);
    }
  }
}

async function syncExamResults() {
  // Sync exam results to server
  const examResults = await getStoredExamResults();
  if (examResults.length > 0) {
    try {
      await fetch('/api/sync/exam-results', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(examResults),
      });
      
      // Clear synced data from local storage
      await clearStoredExamResults();
    } catch (error) {
      console.error('Failed to sync exam results:', error);
    }
  }
}

async function syncLearningAnalytics() {
  // Sync learning analytics to server
  const analyticsData = await getStoredAnalyticsData();
  if (analyticsData.length > 0) {
    try {
      await fetch('/api/sync/analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(analyticsData),
      });
      
      // Clear synced data from local storage
      await clearStoredAnalyticsData();
    } catch (error) {
      console.error('Failed to sync analytics data:', error);
    }
  }
}

// Helper functions for local storage management
async function getStoredProgressData(): Promise<any[]> {
  return new Promise((resolve) => {
    const data = localStorage.getItem('offline-progress-data');
    resolve(data ? JSON.parse(data) : []);
  });
}

async function clearStoredProgressData(): Promise<void> {
  localStorage.removeItem('offline-progress-data');
}

async function getStoredExamResults(): Promise<any[]> {
  return new Promise((resolve) => {
    const data = localStorage.getItem('offline-exam-results');
    resolve(data ? JSON.parse(data) : []);
  });
}

async function clearStoredExamResults(): Promise<void> {
  localStorage.removeItem('offline-exam-results');
}

async function getStoredAnalyticsData(): Promise<any[]> {
  return new Promise((resolve) => {
    const data = localStorage.getItem('offline-analytics-data');
    resolve(data ? JSON.parse(data) : []);
  });
}

async function clearStoredAnalyticsData(): Promise<void> {
  localStorage.removeItem('offline-analytics-data');
}

// Handle push notifications
self.addEventListener('push', (event) => {
  if (event.data) {
    const options = {
      body: event.data.text(),
      icon: '/images/icon-192x192.png',
      badge: '/images/badge-72x72.png',
      vibrate: [100, 50, 100],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: 1
      },
      actions: [
        {
          action: 'explore',
          title: 'İncele',
          icon: '/images/checkmark.png'
        },
        {
          action: 'close',
          title: 'Kapat',
          icon: '/images/xmark.png'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification('KIRO2 Bildirimi', options)
    );
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'explore') {
    // Open the app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Performance monitoring
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'PERFORMANCE_MEASURE') {
    // Log performance metrics
    console.log('Performance metric received:', event.data.metric);
  }
});

// Export for TypeScript
export {};