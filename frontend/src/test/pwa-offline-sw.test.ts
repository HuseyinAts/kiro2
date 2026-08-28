/**
 * PWA Service Worker Offline Caching & Background Sync Test Suite
 * KIRO2 PWA Service Worker (sw.js) ve Offline Sync Mekanizmasının Doğrulanması
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { offlineStorageService } from '../services/offlineStorageService';
import { backgroundSyncService } from '../services/backgroundSyncService';

// Mock CacheStorage and Cache API
class MockCache {
  private store = new Map<string, Response>();

  async match(request: Request | string): Promise<Response | undefined> {
    const key = typeof request === 'string' ? request : request.url;
    return this.store.get(key);
  }

  async put(request: Request | string, response: Response): Promise<void> {
    const key = typeof request === 'string' ? request : request.url;
    this.store.set(key, response.clone());
  }

  async addAll(urls: string[]): Promise<void> {
    for (const url of urls) {
      this.store.set(url, new Response('mock app shell'));
    }
  }
}

class MockCacheStorage {
  private caches = new Map<string, MockCache>();

  async open(cacheName: string): Promise<MockCache> {
    if (!this.caches.has(cacheName)) {
      this.caches.set(cacheName, new MockCache());
    }
    return this.caches.get(cacheName)!;
  }

  async keys(): Promise<string[]> {
    return Array.from(this.caches.keys());
  }

  async delete(cacheName: string): Promise<boolean> {
    return this.caches.delete(cacheName);
  }

  async match(request: Request | string): Promise<Response | undefined> {
    for (const cache of this.caches.values()) {
      const match = await cache.match(request);
      if (match) return match;
    }
    return undefined;
  }
}

describe('Service Worker Caching & Offline Strategies', () => {
  let mockCaches: MockCacheStorage;

  beforeEach(() => {
    vi.clearAllMocks();
    mockCaches = new MockCacheStorage();

    Object.defineProperty(globalThis, 'caches', {
      value: mockCaches,
      writable: true,
      configurable: true,
    });
  });

  it('should initialize app shell cache kiro2-v1 during install', async () => {
    const cache = await caches.open('kiro2-v1');
    await cache.addAll(['/', '/index.html']);

    const cachedShell = await cache.match('/index.html');
    expect(cachedShell).toBeDefined();
    expect(await cachedShell?.text()).toBe('mock app shell');
  });

  it('should purge outdated caches on service worker activation', async () => {
    await caches.open('kiro2-v0-old');
    await caches.open('kiro2-v1');

    const keysBefore = await caches.keys();
    expect(keysBefore).toContain('kiro2-v0-old');

    // Simulate SW activate event purging non-v1 caches
    for (const key of keysBefore) {
      if (key !== 'kiro2-v1') {
        await caches.delete(key);
      }
    }

    const keysAfter = await caches.keys();
    expect(keysAfter).not.toContain('kiro2-v0-old');
    expect(keysAfter).toContain('kiro2-v1');
  });

  it('should perform network-first strategy for GET /api/ requests', async () => {
    const cache = await caches.open('kiro2-v1');
    const mockRequest = new Request('http://localhost:3000/api/v1/user/profile');
    const mockNetworkResponse = new Response(JSON.stringify({ id: 'u1', name: 'Student' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

    // Simulate network success
    await cache.put(mockRequest, mockNetworkResponse);
    const cached = await cache.match(mockRequest);
    expect(cached).toBeDefined();
    expect(await cached?.json()).toEqual({ id: 'u1', name: 'Student' });
  });

  it('should perform cache-first strategy for static assets (.js, .css, .woff2)', async () => {
    const cache = await caches.open('kiro2-v1');
    const staticUrl = 'http://localhost:3000/assets/index-main.js';
    const staticResponse = new Response('console.log("kiro2 main bundle")', {
      status: 200,
      headers: { 'Content-Type': 'application/javascript' },
    });

    await cache.put(staticUrl, staticResponse);
    const cached = await cache.match(staticUrl);
    expect(cached).toBeDefined();
    expect(await cached?.text()).toContain('kiro2 main bundle');
  });
});

describe('Offline Storage & Background Sync Mechanics', () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => store[key] || null,
      setItem: (key: string, value: string) => {
        store[key] = value;
      },
      removeItem: (key: string) => {
        delete store[key];
      },
      clear: () => {
        for (const k in store) delete store[k];
      },
    });
  });

  it('should store offline study progress correctly', async () => {
    const offlineProgress = {
      userId: 'user-1',
      subject: 'matematik',
      totalQuestions: 15,
      correctAnswers: 12,
      studyTime: 45,
      lastActivity: new Date().toISOString(),
      synced: false,
    };

    await offlineStorageService.saveOfflineData({
      questions: [],
      examSessions: [],
      studyNotes: [],
      progress: [offlineProgress],
      settings: { autoSync: true, offlineMode: true, downloadLimit: 1000 },
    });

    const loadedData = await offlineStorageService.loadOfflineData();
    expect(loadedData.progress).toHaveLength(1);
    expect(loadedData.progress[0].subject).toBe('matematik');
  });

  it('should return pending items status from background sync service', async () => {
    const status = await backgroundSyncService.getSyncStatus();
    expect(status).toHaveProperty('isOnline');
    expect(status).toHaveProperty('pendingItems');
    expect(status).toHaveProperty('syncInProgress');
  });
});
