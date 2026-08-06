/**
 * NetworkDetector Tests
 *
 * Unit tests for NetworkDetector service
 *
 * @requires Requirements: 5.19, 10.6, 10.7
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { NetworkDetector, NetworkState, getNetworkDetector, createNetworkDetector } from '../NetworkDetector';

describe('NetworkDetector', () => {
  let detector: NetworkDetector;

  beforeEach(() => {
    // Create detector instance
    detector = new NetworkDetector(5, 2000);

    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });

    // Mock timers
    vi.useFakeTimers();
  });

  afterEach(() => {
    detector.destroy();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Constructor', () => {
    it('should initialize with online state', () => {
      const state = detector.getState();

      expect(state.status).toBe('online');
      expect(state.isOnline).toBe(true);
      expect(state.reconnectionAttempts).toBe(0);
    });

    it('should initialize with offline state when navigator is offline', () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      const offlineDetector = new NetworkDetector();
      const state = offlineDetector.getState();

      expect(state.status).toBe('offline');
      expect(state.isOnline).toBe(false);

      offlineDetector.destroy();
    });

    it('should accept custom configuration', () => {
      const customDetector = new NetworkDetector(10, 5000);
      expect(customDetector).toBeDefined();
      customDetector.destroy();
    });
  });

  describe('State Management', () => {
    it('should return current state', () => {
      const state = detector.getState();

      expect(state).toHaveProperty('status');
      expect(state).toHaveProperty('isOnline');
      expect(state).toHaveProperty('lastOnlineTime');
      expect(state).toHaveProperty('lastOfflineTime');
      expect(state).toHaveProperty('reconnectionAttempts');
    });

    it('should notify subscribers on state change', () => {
      const callback = vi.fn();

      detector.subscribe(callback);

      // Trigger online event
      window.dispatchEvent(new Event('online'));

      expect(callback).toHaveBeenCalled();
    });

    it('should allow unsubscribing', () => {
      const callback = vi.fn();

      const unsubscribe = detector.subscribe(callback);
      unsubscribe();

      // Trigger online event
      window.dispatchEvent(new Event('online'));

      // Callback should not be called after unsubscribe
      expect(callback).toHaveBeenCalledTimes(1); // Only initial call
    });
  });

  describe('Online/Offline Detection', () => {
    it('should detect online event', () => {
      const callback = vi.fn();
      detector.subscribe(callback);

      // Trigger online event
      window.dispatchEvent(new Event('online'));

      const state = detector.getState();
      expect(state.isOnline).toBe(true);
      expect(state.status).toBe('online');
    });

    it('should detect offline event', () => {
      const callback = vi.fn();
      detector.subscribe(callback);

      // Trigger offline event
      window.dispatchEvent(new Event('offline'));

      const state = detector.getState();
      expect(state.isOnline).toBe(false);
      expect(state.status).toBe('offline');
    });

    it('should update lastOnlineTime on online event', () => {
      const beforeTime = Date.now();

      window.dispatchEvent(new Event('online'));

      const state = detector.getState();
      expect(state.lastOnlineTime).toBeGreaterThanOrEqual(beforeTime);
    });

    it('should update lastOfflineTime on offline event', () => {
      const beforeTime = Date.now();

      window.dispatchEvent(new Event('offline'));

      const state = detector.getState();
      expect(state.lastOfflineTime).toBeGreaterThanOrEqual(beforeTime);
    });
  });

  describe('Helper Methods', () => {
    it('should check if online', () => {
      expect(detector.isOnline()).toBe(true);

      window.dispatchEvent(new Event('offline'));

      expect(detector.isOnline()).toBe(false);
    });

    it('should check if offline', () => {
      expect(detector.isOffline()).toBe(false);

      window.dispatchEvent(new Event('offline'));

      expect(detector.isOffline()).toBe(true);
    });

    it('should check if connection is slow', () => {
      expect(detector.isSlow()).toBe(false);
    });

    it('should get offline duration', () => {
      expect(detector.getOfflineDuration()).toBeNull();

      window.dispatchEvent(new Event('offline'));
      vi.advanceTimersByTime(5000);

      const duration = detector.getOfflineDuration();
      expect(duration).toBeGreaterThan(0);
    });

    it('should return null offline duration when online', () => {
      window.dispatchEvent(new Event('online'));

      expect(detector.getOfflineDuration()).toBeNull();
    });
  });

  describe('Reconnection Callbacks', () => {
    it('should register reconnection callback', () => {
      const callback = vi.fn();

      const unregister = detector.onReconnection(callback);

      expect(unregister).toBeInstanceOf(Function);
    });

    it('should trigger reconnection callbacks on reconnection', () => {
      const callback = vi.fn();

      detector.onReconnection(callback);

      // Go offline then online
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));

      expect(callback).toHaveBeenCalled();
    });

    it('should allow unregistering reconnection callback', () => {
      const callback = vi.fn();

      const unregister = detector.onReconnection(callback);
      unregister();

      // Go offline then online
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));

      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('Manual Connection Check', () => {
    it('should perform manual connection check', async () => {
      // Mock fetch for ping test
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
      });

      const result = await detector.checkConnection();

      expect(result).toBe(true);
    });

    it('should handle failed connection check', async () => {
      // Mock fetch failure
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

      // Mock navigator.onLine to be false so the fallback doesn't treat it as a backend-only failure
      navigator.onLine = false;

      const result = await detector.checkConnection();

      expect(result).toBe(false);

      navigator.onLine = true;
    });
  });

  describe('Reconnection Attempts', () => {
    it('should reset reconnection attempts', () => {
      // Trigger offline
      window.dispatchEvent(new Event('offline'));

      // Manually set reconnection attempts
      const state = detector.getState();
      expect(state.reconnectionAttempts).toBeGreaterThanOrEqual(0);

      detector.resetReconnectionAttempts();

      const newState = detector.getState();
      expect(newState.reconnectionAttempts).toBe(0);
    });
  });

  describe('Cleanup', () => {
    it('should cleanup on destroy', () => {
      const callback = vi.fn();
      detector.subscribe(callback);

      detector.destroy();

      // Trigger event after destroy
      window.dispatchEvent(new Event('online'));

      // Callback should not be called after destroy
      expect(callback).toHaveBeenCalledTimes(1); // Only initial call
    });
  });

  describe('Singleton Pattern', () => {
    it('should return same instance from getNetworkDetector', () => {
      const instance1 = getNetworkDetector();
      const instance2 = getNetworkDetector();

      expect(instance1).toBe(instance2);
    });

    it('should create new instance from createNetworkDetector', () => {
      const instance1 = createNetworkDetector();
      const instance2 = createNetworkDetector();

      expect(instance1).not.toBe(instance2);

      instance1.destroy();
      instance2.destroy();
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid online/offline changes', () => {
      const callback = vi.fn();
      detector.subscribe(callback);

      // Rapid changes
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));

      expect(callback).toHaveBeenCalled();
      expect(detector.isOnline()).toBe(true);
    });

    it('should handle multiple subscribers', () => {
      const callback1 = vi.fn();
      const callback2 = vi.fn();
      const callback3 = vi.fn();

      detector.subscribe(callback1);
      detector.subscribe(callback2);
      detector.subscribe(callback3);

      window.dispatchEvent(new Event('online'));

      expect(callback1).toHaveBeenCalled();
      expect(callback2).toHaveBeenCalled();
      expect(callback3).toHaveBeenCalled();
    });

    it('should handle subscriber errors gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const errorCallback = () => {
        throw new Error('Subscriber error');
      };
      const normalCallback = vi.fn();

      detector.subscribe(errorCallback);
      detector.subscribe(normalCallback);

      // Should not throw
      expect(() => {
        window.dispatchEvent(new Event('online'));
      }).not.toThrow();

      consoleSpy.mockRestore();
      expect(normalCallback).toHaveBeenCalled();
    });
  });
});
