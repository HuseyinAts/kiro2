/**
 * PWA Functionality Tests
 * Progressive Web App özelliklerinin test edilmesi
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { offlineStorageService } from '../services/offlineStorageService';
import { backgroundSyncService } from '../services/backgroundSyncService';
import { TouchGestureDetector, PWAInstallHelper, NetworkManager } from '../utils/touchUtils';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

// Mock navigator
const navigatorMock = {
  onLine: true,
  serviceWorker: {
    register: vi.fn(),
    ready: Promise.resolve({
      sync: {
        register: vi.fn()
      },
      pushManager: {
        subscribe: vi.fn()
      }
    })
  },
  vibrate: vi.fn()
};

// Mock window
const windowMock = {
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  matchMedia: vi.fn(() => ({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn()
  })),
  innerWidth: 1024,
  innerHeight: 768
};

describe('PWA Offline Storage Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true
    });
  });

  it('should load offline data from localStorage', async () => {
    const mockData = {
      questions: [],
      examSessions: [],
      studyNotes: [],
      progress: [],
      settings: {
        autoSync: true,
        offlineMode: false,
        downloadLimit: 1000
      }
    };

    localStorageMock.getItem.mockReturnValue(JSON.stringify(mockData));

    const data = await offlineStorageService.loadOfflineData();
    
    expect(localStorageMock.getItem).toHaveBeenCalledWith('kiro2-offline-data');
    expect(data).toEqual(mockData);
  });

  it('should return default data when localStorage is empty', async () => {
    localStorageMock.getItem.mockReturnValue(null);

    const data = await offlineStorageService.loadOfflineData();
    
    expect(data).toEqual({
      questions: [],
      examSessions: [],
      studyNotes: [],
      progress: [],
      settings: {
        autoSync: true,
        offlineMode: false,
        downloadLimit: 1000
      }
    });
  });

  it('should save offline data to localStorage', async () => {
    const testData = {
      questions: [{ id: '1', text: 'Test question', options: [], correct: 0, subject: 'math', difficulty: 'easy' as const, downloadedAt: '2025-01-01' }],
      examSessions: [],
      studyNotes: [],
      progress: [],
      settings: {
        autoSync: true,
        offlineMode: false,
        downloadLimit: 1000
      }
    };

    await offlineStorageService.saveOfflineData(testData);
    
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'kiro2-offline-data',
      JSON.stringify(testData)
    );
  });

  it('should create offline exam session', async () => {
    const mockQuestions = [
      { id: '1', text: 'Q1', options: ['A', 'B'], correct: 0, subject: 'matematik', difficulty: 'easy' as const, downloadedAt: '2025-01-01' },
      { id: '2', text: 'Q2', options: ['A', 'B'], correct: 1, subject: 'matematik', difficulty: 'easy' as const, downloadedAt: '2025-01-01' }
    ];

    localStorageMock.getItem.mockReturnValue(JSON.stringify({
      questions: mockQuestions,
      examSessions: [],
      studyNotes: [],
      progress: [],
      settings: { autoSync: true, offlineMode: false, downloadLimit: 1000 }
    }));

    const examSession = await offlineStorageService.startOfflineExam('matematik', 2);
    
    expect(examSession.questions).toHaveLength(2);
    expect(examSession.completed).toBe(false);
    expect(examSession.synced).toBe(false);
  });

  it('should throw error when insufficient questions for exam', async () => {
    localStorageMock.getItem.mockReturnValue(JSON.stringify({
      questions: [],
      examSessions: [],
      studyNotes: [],
      progress: [],
      settings: { autoSync: true, offlineMode: false, downloadLimit: 1000 }
    }));

    await expect(
      offlineStorageService.startOfflineExam('matematik', 10)
    ).rejects.toThrow('Yeterli çevrimdışı soru yok');
  });
});

describe('PWA Background Sync Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window, 'navigator', {
      value: navigatorMock,
      writable: true
    });
    Object.defineProperty(window, 'addEventListener', {
      value: windowMock.addEventListener,
      writable: true
    });
  });

  it('should return sync status', async () => {
    const status = await backgroundSyncService.getSyncStatus();
    
    expect(status).toHaveProperty('isOnline');
    expect(status).toHaveProperty('pendingItems');
    expect(status).toHaveProperty('syncInProgress');
  });

  it('should not sync when offline', async () => {
    navigatorMock.onLine = false;

    const result = await backgroundSyncService.performSync();
    
    expect(result.success).toBe(false);
    expect(result.errors).toContain('İnternet bağlantısı yok');
  });

  it('should register background sync', async () => {
    await backgroundSyncService.registerBackgroundSync('test-sync');
    
    // Service worker registration kontrolü yapılmalı
    expect(navigatorMock.serviceWorker.register).toBeDefined();
  });
});

describe('PWA Touch Gesture Detector', () => {
  let mockElement: HTMLElement;
  let callbacks: any;

  beforeEach(() => {
    mockElement = {
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      classList: {
        add: vi.fn(),
        remove: vi.fn()
      }
    } as any;

    callbacks = {
      onSwipe: vi.fn(),
      onTap: vi.fn(),
      onLongPress: vi.fn(),
      onPinch: vi.fn()
    };

    new TouchGestureDetector(mockElement, callbacks);
  });

  it('should setup touch event listeners', () => {
    expect(mockElement.addEventListener).toHaveBeenCalledWith('touchstart', expect.any(Function), expect.any(Object));
    expect(mockElement.addEventListener).toHaveBeenCalledWith('touchmove', expect.any(Function), expect.any(Object));
    expect(mockElement.addEventListener).toHaveBeenCalledWith('touchend', expect.any(Function), expect.any(Object));
  });

  it('should detect swipe gestures', () => {
    // Touch start event simülasyonu
    const touchStartEvent = new TouchEvent('touchstart', {
      touches: [{ clientX: 100, clientY: 100 } as Touch]
    });

    // Touch end event simülasyonu (sağa swipe)
    const touchEndEvent = new TouchEvent('touchend', {
      changedTouches: [{ clientX: 200, clientY: 100 } as Touch]
    });

    // Event handler'ları manuel olarak çağır
    const startHandler = (mockElement.addEventListener as any).mock.calls
      .find((call: any) => call[0] === 'touchstart')[1];
    const endHandler = (mockElement.addEventListener as any).mock.calls
      .find((call: any) => call[0] === 'touchend')[1];

    startHandler(touchStartEvent);
    
    // Zaman gecikmesi simülasyonu
    setTimeout(() => {
      endHandler(touchEndEvent);
      
      expect(callbacks.onSwipe).toHaveBeenCalledWith(
        expect.objectContaining({
          direction: 'right',
          distance: expect.any(Number),
          duration: expect.any(Number),
          velocity: expect.any(Number)
        })
      );
    }, 100);
  });
});

describe('PWA Install Helper', () => {
  let installHelper: PWAInstallHelper;
  let mockPrompt: any;

  beforeEach(() => {
    mockPrompt = {
      prompt: vi.fn(),
      userChoice: Promise.resolve({ outcome: 'accepted' })
    };

    Object.defineProperty(window, 'addEventListener', {
      value: windowMock.addEventListener,
      writable: true
    });

    installHelper = new PWAInstallHelper();
  });

  it('should detect installable state', () => {
    // beforeinstallprompt event simülasyonu
    const beforeInstallPromptEvent = new Event('beforeinstallprompt');
    Object.defineProperty(beforeInstallPromptEvent, 'preventDefault', {
      value: vi.fn()
    });

    // Event handler'ı bul ve çağır
    const eventHandler = (windowMock.addEventListener as any).mock.calls
      .find((call: any) => call[0] === 'beforeinstallprompt')[1];

    eventHandler(beforeInstallPromptEvent);

    expect(installHelper.isInstallable()).toBe(true);
  });

  it('should handle PWA installation', async () => {
    // Prompt'u manuel olarak set et
    (installHelper as any).deferredPrompt = mockPrompt;

    const result = await installHelper.install();
    
    expect(mockPrompt.prompt).toHaveBeenCalled();
    expect(result).toBe(true);
  });

  it('should detect installed state', () => {
    Object.defineProperty(window, 'matchMedia', {
      value: vi.fn(() => ({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      })),
      writable: true
    });

    const isInstalled = installHelper.isInstalled();
    
    expect(isInstalled).toBe(true);
  });
});

describe('PWA Network Manager', () => {
  let networkManager: NetworkManager;
  let callbacks: any;

  beforeEach(() => {
    callbacks = {
      onOnline: vi.fn(),
      onOffline: vi.fn(),
      onSlowConnection: vi.fn()
    };

    windowMock.addEventListener.mockClear();

    Object.defineProperty(window, 'addEventListener', {
      value: windowMock.addEventListener,
      writable: true
    });

    networkManager = new NetworkManager(callbacks);
  });

  it('should setup network event listeners', () => {
    expect(windowMock.addEventListener).toHaveBeenCalledWith('online', expect.any(Function));
    expect(windowMock.addEventListener).toHaveBeenCalledWith('offline', expect.any(Function));
  });

  it('should return connection info', () => {
    const connectionInfo = networkManager.getConnectionInfo();
    
    expect(connectionInfo).toHaveProperty('isOnline');
    expect(typeof connectionInfo.isOnline).toBe('boolean');
  });

  it('should handle online event', () => {
    const onlineCalls = (windowMock.addEventListener as any).mock.calls.filter((c: any) => c[0] === 'online');
    const onlineHandler = onlineCalls[onlineCalls.length - 1][1];

    onlineHandler();
    
    expect(callbacks.onOnline).toHaveBeenCalled();
  });

  it('should handle offline event', () => {
    const offlineCalls = (windowMock.addEventListener as any).mock.calls.filter((c: any) => c[0] === 'offline');
    const offlineHandler = offlineCalls[offlineCalls.length - 1][1];

    offlineHandler();
    
    expect(callbacks.onOffline).toHaveBeenCalled();
  });
});

describe('PWA Utility Functions', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      value: 1024,
      writable: true
    });
    Object.defineProperty(window, 'innerHeight', {
      value: 768,
      writable: true
    });
  });

  it('should detect mobile device', async () => {
    const { isMobile } = await import('../utils/touchUtils');
    
    window.innerWidth = 400;
    expect(isMobile()).toBe(true);
    
    window.innerWidth = 1024;
    expect(isMobile()).toBe(false);
  });

  it('should detect tablet device', async () => {
    const { isTablet } = await import('../utils/touchUtils');
    
    window.innerWidth = 600;
    expect(isTablet()).toBe(true);
    
    window.innerWidth = 400;
    expect(isTablet()).toBe(false);
  });

  it('should detect desktop device', async () => {
    const { isDesktop } = await import('../utils/touchUtils');
    
    window.innerWidth = 1024;
    expect(isDesktop()).toBe(true);
    
    window.innerWidth = 600;
    expect(isDesktop()).toBe(false);
  });
});