/**
 * useOfflineMode Hook Tests
 * 
 * Unit tests for useOfflineMode React hook
 * 
 * @requires Requirements: 5.19, 10.6, 10.7
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useOfflineMode, useNetworkStatus } from '../useOfflineMode';
import { getNetworkDetector } from '../../services/NetworkDetector';
import { VideoLoadingManager } from '../../services/VideoLoadingManager';

describe('useOfflineMode', () => {
  beforeEach(() => {
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
      configurable: true,
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    const networkDetector = getNetworkDetector();
    networkDetector.resetReconnectionAttempts();
    window.dispatchEvent(new Event('online'));

    // Mock timers
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Hook Initialization', () => {
    it('should initialize with online state', () => {
      const { result } = renderHook(() => useOfflineMode());

      expect(result.current.isOnline).toBe(true);
      expect(result.current.isOffline).toBe(false);
      expect(result.current.showOfflineUI).toBe(false);
    });

    it('should initialize with offline state when navigator is offline', () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
        configurable: true,
      });

      const { result } = renderHook(() => useOfflineMode());

      expect(result.current.isOnline).toBe(false);
      expect(result.current.isOffline).toBe(true);
    });

    it('should accept options', () => {
      const videoLoadingManager = new VideoLoadingManager();
      
      const { result } = renderHook(() => 
        useOfflineMode({
          videoLoadingManager,
          autoRetryOnReconnection: true,
          maxReconnectionAttempts: 10,
          reconnectionDelay: 3000,
        })
      );

      expect(result.current).toBeDefined();
    });
  });

  describe('Network State', () => {
    it('should provide network state', () => {
      const { result } = renderHook(() => useOfflineMode());

      expect(result.current.networkState).toBeDefined();
      expect(result.current.networkState.status).toBe('online');
      expect(result.current.networkState.isOnline).toBe(true);
    });

    it('should update network state on offline event', async () => {
      const { result } = renderHook(() => useOfflineMode());

      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(result.current.isOffline).toBe(true);
        expect(result.current.networkState.status).toBe('offline');
      });
    });

    it('should update network state on online event', async () => {
      const { result } = renderHook(() => useOfflineMode());

      // Go offline first
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(result.current.isOffline).toBe(true);
      });

      // Then go online
      act(() => {
        window.dispatchEvent(new Event('online'));
      });

      await waitFor(() => {
        expect(result.current.isOnline).toBe(true);
      });
    });
  });

  describe('Offline Mode State', () => {
    it('should provide offline mode state', () => {
      const { result } = renderHook(() => useOfflineMode());

      expect(result.current.offlineModeState).toBeDefined();
      expect(result.current.offlineModeState.isOffline).toBe(false);
      expect(result.current.offlineModeState.pendingRequests).toBeDefined();
    });

    it('should show offline UI when offline', async () => {
      const { result } = renderHook(() => useOfflineMode());

      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(result.current.showOfflineUI).toBe(true);
      });
    });

    it('should track offline duration', async () => {
      const { result } = renderHook(() => useOfflineMode());

      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(result.current.isOffline).toBe(true);
      });

      act(() => {
        vi.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(result.current.offlineDuration).toBeGreaterThan(0);
      });
    });
  });

  describe('Pending Requests', () => {
    it('should register pending request', async () => {
      const { result } = renderHook(() => useOfflineMode());

      act(() => {
        result.current.registerPendingRequest('req_123');
      });

      await waitFor(() => {
        expect(result.current.pendingRequestsCount).toBe(1);
      });
    });

    it('should unregister pending request', async () => {
      const { result } = renderHook(() => useOfflineMode());

      act(() => {
        result.current.registerPendingRequest('req_123');
      });

      await waitFor(() => {
        expect(result.current.pendingRequestsCount).toBe(1);
      });

      act(() => {
        result.current.unregisterPendingRequest('req_123');
      });

      await waitFor(() => {
        expect(result.current.pendingRequestsCount).toBe(0);
      });
    });

    it('should track multiple pending requests', async () => {
      const { result } = renderHook(() => useOfflineMode());

      act(() => {
        result.current.registerPendingRequest('req_1');
        result.current.registerPendingRequest('req_2');
        result.current.registerPendingRequest('req_3');
      });

      await waitFor(() => {
        expect(result.current.pendingRequestsCount).toBe(3);
      });
    });
  });

  describe('Actions', () => {
    it('should check connection', async () => {
      // Mock fetch for ping test
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
      });

      const { result } = renderHook(() => useOfflineMode());

      let connectionResult: boolean | undefined;

      await act(async () => {
        connectionResult = await result.current.checkConnection();
      });

      expect(connectionResult).toBe(true);
    });

    it('should retry cancelled requests', async () => {
      const { result } = renderHook(() => useOfflineMode());

      act(() => {
        result.current.registerPendingRequest('req_123');
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(result.current.isOffline).toBe(true);
      });

      act(() => {
        window.dispatchEvent(new Event('online'));
      });

      await waitFor(() => {
        expect(result.current.isOnline).toBe(true);
      });

      act(() => {
        result.current.retryCancelledRequests();
      });

      // Should not throw
      expect(() => result.current.retryCancelledRequests()).not.toThrow();
    });
  });

  describe('Managers Access', () => {
    it('should provide access to NetworkDetector', () => {
      const { result } = renderHook(() => useOfflineMode());

      expect(result.current.networkDetector).toBeDefined();
      expect(result.current.networkDetector.getState).toBeDefined();
    });

    it('should provide access to OfflineModeManager', () => {
      const { result } = renderHook(() => useOfflineMode());

      expect(result.current.offlineModeManager).toBeDefined();
      expect(result.current.offlineModeManager.getState).toBeDefined();
    });
  });

  describe('Derived State', () => {
    it('should provide isSlow flag', () => {
      const { result } = renderHook(() => useOfflineMode());

      expect(result.current.isSlow).toBe(false);
    });

    it('should provide reconnectionInProgress flag', () => {
      const { result } = renderHook(() => useOfflineMode());

      expect(result.current.reconnectionInProgress).toBe(false);
    });
  });

  describe('VideoLoadingManager Integration', () => {
    it('should integrate with VideoLoadingManager', () => {
      const videoLoadingManager = new VideoLoadingManager();
      
      const { result } = renderHook(() => 
        useOfflineMode({ videoLoadingManager })
      );

      expect(result.current).toBeDefined();
    });

    it('should update VideoLoadingManager when provided', () => {
      const videoLoadingManager1 = new VideoLoadingManager();
      const videoLoadingManager2 = new VideoLoadingManager();
      
      const { result, rerender } = renderHook(
        ({ manager }) => useOfflineMode({ videoLoadingManager: manager }),
        { initialProps: { manager: videoLoadingManager1 } }
      );

      expect(result.current).toBeDefined();

      // Update with new manager
      rerender({ manager: videoLoadingManager2 });

      expect(result.current).toBeDefined();
    });
  });

  describe('Hook Cleanup', () => {
    it('should cleanup on unmount', () => {
      const { unmount } = renderHook(() => useOfflineMode());

      // Should not throw
      expect(() => unmount()).not.toThrow();
    });
  });
});

describe('useNetworkStatus', () => {
  beforeEach(() => {
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
      configurable: true,
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    const networkDetector = getNetworkDetector();
    networkDetector.resetReconnectionAttempts();
    window.dispatchEvent(new Event('online'));

    // Mock timers
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Hook Initialization', () => {
    it('should initialize with online status', () => {
      const { result } = renderHook(() => useNetworkStatus());

      expect(result.current.status).toBe('online');
      expect(result.current.isOnline).toBe(true);
      expect(result.current.isOffline).toBe(false);
    });

    it('should initialize with offline status when navigator is offline', () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
        configurable: true,
      });

      const { result } = renderHook(() => useNetworkStatus());

      expect(result.current.status).toBe('offline');
      expect(result.current.isOnline).toBe(false);
      expect(result.current.isOffline).toBe(true);
    });
  });

  describe('Network Status Updates', () => {
    it('should update status on offline event', async () => {
      const { result } = renderHook(() => useNetworkStatus());

      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(result.current.status).toBe('offline');
        expect(result.current.isOffline).toBe(true);
      });
    });

    it('should update status on online event', async () => {
      const { result } = renderHook(() => useNetworkStatus());

      // Go offline first
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(result.current.isOffline).toBe(true);
      });

      // Then go online
      act(() => {
        window.dispatchEvent(new Event('online'));
      });

      await waitFor(() => {
        expect(result.current.status).toBe('online');
        expect(result.current.isOnline).toBe(true);
      });
    });
  });

  describe('Network Information', () => {
    it('should provide network information', () => {
      const { result } = renderHook(() => useNetworkStatus());

      expect(result.current).toHaveProperty('status');
      expect(result.current).toHaveProperty('isOnline');
      expect(result.current).toHaveProperty('isOffline');
      expect(result.current).toHaveProperty('isSlow');
      expect(result.current).toHaveProperty('effectiveType');
      expect(result.current).toHaveProperty('downlink');
      expect(result.current).toHaveProperty('rtt');
      expect(result.current).toHaveProperty('reconnectionAttempts');
    });

    it('should provide isSlow flag', () => {
      const { result } = renderHook(() => useNetworkStatus());

      expect(result.current.isSlow).toBe(false);
    });

    it('should provide reconnectionAttempts', () => {
      const { result } = renderHook(() => useNetworkStatus());

      expect(result.current.reconnectionAttempts).toBe(0);
    });
  });

  describe('Hook Cleanup', () => {
    it('should cleanup on unmount', () => {
      const { unmount } = renderHook(() => useNetworkStatus());

      // Should not throw
      expect(() => unmount()).not.toThrow();
    });
  });
});
