/**
 * OfflineModeManager Tests
 *
 * Unit tests for OfflineModeManager service
 *
 * @requires Requirements: 5.19, 10.6, 10.7
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { OfflineModeManager, OfflineModeState, createOfflineModeManager } from '../OfflineModeManager';
import { NetworkDetector } from '../NetworkDetector';
import { VideoLoadingManager } from '../VideoLoadingManager';

describe('OfflineModeManager', () => {
  let manager: OfflineModeManager;
  let networkDetector: NetworkDetector;
  let videoLoadingManager: VideoLoadingManager;

  beforeEach(() => {
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    });

    // Create instances
    networkDetector = new NetworkDetector(5, 2000);
    videoLoadingManager = new VideoLoadingManager('http://localhost:8001', 5000, 2);
    manager = new OfflineModeManager(networkDetector, videoLoadingManager);

    // Mock timers
    vi.useFakeTimers();
  });

  afterEach(() => {
    manager.destroy();
    networkDetector.destroy();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Constructor', () => {
    it('should initialize with online state', () => {
      const state = manager.getState();

      expect(state.isOffline).toBe(false);
      expect(state.showOfflineUI).toBe(false);
      expect(state.pendingRequests.size).toBe(0);
      expect(state.cancelledRequests.size).toBe(0);
    });

    it('should initialize with offline state when network is offline', () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      const offlineNetworkDetector = new NetworkDetector();
      const offlineManager = new OfflineModeManager(offlineNetworkDetector);
      const state = offlineManager.getState();

      expect(state.isOffline).toBe(true);
      expect(state.showOfflineUI).toBe(true);

      offlineManager.destroy();
      offlineNetworkDetector.destroy();
    });

    it('should work without VideoLoadingManager', () => {
      const managerWithoutVideo = new OfflineModeManager(networkDetector);
      expect(managerWithoutVideo).toBeDefined();
      managerWithoutVideo.destroy();
    });
  });

  describe('State Management', () => {
    it('should return current state', () => {
      const state = manager.getState();

      expect(state).toHaveProperty('isOffline');
      expect(state).toHaveProperty('showOfflineUI');
      expect(state).toHaveProperty('offlineDuration');
      expect(state).toHaveProperty('pendingRequests');
      expect(state).toHaveProperty('cancelledRequests');
      expect(state).toHaveProperty('reconnectionInProgress');
    });

    it('should notify subscribers on state change', () => {
      const callback = vi.fn();

      manager.subscribe(callback);

      // Trigger offline
      window.dispatchEvent(new Event('offline'));

      expect(callback).toHaveBeenCalled();
    });

    it('should allow unsubscribing', () => {
      const callback = vi.fn();

      const unsubscribe = manager.subscribe(callback);
      unsubscribe();

      // Trigger offline
      window.dispatchEvent(new Event('offline'));

      // Callback should not be called after unsubscribe
      expect(callback).toHaveBeenCalledTimes(1); // Only initial call
    });
  });

  describe('Network State Changes', () => {
    it('should update state when going offline', () => {
      window.dispatchEvent(new Event('offline'));

      const state = manager.getState();
      expect(state.isOffline).toBe(true);
      expect(state.showOfflineUI).toBe(true);
    });

    it('should update state when going online', () => {
      // Go offline first
      window.dispatchEvent(new Event('offline'));

      // Then go online
      window.dispatchEvent(new Event('online'));

      const state = manager.getState();
      expect(state.isOffline).toBe(false);
    });

    it('should update offline duration', () => {
      const now = 1000000;
      vi.setSystemTime(now);
      window.dispatchEvent(new Event('offline'));
      vi.setSystemTime(now + 5000);

      const duration = manager.getOfflineDuration();
      expect(duration).toBeGreaterThan(0);
    });
  });

  describe('Pending Requests', () => {
    it('should register pending request', () => {
      manager.registerPendingRequest('req_123');

      const state = manager.getState();
      expect(state.pendingRequests.has('req_123')).toBe(true);
      expect(manager.getPendingRequestsCount()).toBe(1);
    });

    it('should unregister pending request', () => {
      manager.registerPendingRequest('req_123');
      manager.unregisterPendingRequest('req_123');

      const state = manager.getState();
      expect(state.pendingRequests.has('req_123')).toBe(false);
      expect(manager.getPendingRequestsCount()).toBe(0);
    });

    it('should cancel pending requests when going offline', () => {
      manager.registerPendingRequest('req_123');
      manager.registerPendingRequest('req_456');

      window.dispatchEvent(new Event('offline'));

      const state = manager.getState();
      expect(state.pendingRequests.size).toBe(0);
      expect(state.cancelledRequests.size).toBe(2);
    });
  });

  describe('Helper Methods', () => {
    it('should check if offline', () => {
      expect(manager.isOffline()).toBe(false);

      window.dispatchEvent(new Event('offline'));

      expect(manager.isOffline()).toBe(true);
    });

    it('should check if should show offline UI', () => {
      expect(manager.shouldShowOfflineUI()).toBe(false);

      window.dispatchEvent(new Event('offline'));

      expect(manager.shouldShowOfflineUI()).toBe(true);
    });

    it('should get offline duration', () => {
      expect(manager.getOfflineDuration()).toBeNull();

      const now = 1000000;
      vi.setSystemTime(now);
      window.dispatchEvent(new Event('offline'));
      vi.setSystemTime(now + 3000);

      const duration = manager.getOfflineDuration();
      expect(duration).toBeGreaterThan(0);
    });

    it('should get pending requests count', () => {
      expect(manager.getPendingRequestsCount()).toBe(0);

      manager.registerPendingRequest('req_1');
      manager.registerPendingRequest('req_2');

      expect(manager.getPendingRequestsCount()).toBe(2);
    });
  });

  describe('Manual Connection Check', () => {
    it('should perform manual connection check', async () => {
      // Mock fetch for ping test
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
      });

      const result = await manager.checkConnection();

      expect(result).toBe(true);
    });
  });

  describe('Retry Cancelled Requests', () => {
    it('should retry cancelled requests', () => {
      manager.registerPendingRequest('req_123');

      // Go offline to cancel requests
      window.dispatchEvent(new Event('offline'));

      const state = manager.getState();
      expect(state.cancelledRequests.size).toBe(1);

      // Go online
      window.dispatchEvent(new Event('online'));

      // Manually retry
      manager.retryCancelledRequests();

      const newState = manager.getState();
      expect(newState.cancelledRequests.size).toBe(0);
    });

    it('should not retry if no cancelled requests', () => {
      manager.retryCancelledRequests();

      const state = manager.getState();
      expect(state.cancelledRequests.size).toBe(0);
    });
  });

  describe('VideoLoadingManager Integration', () => {
    it('should set VideoLoadingManager', () => {
      const newVideoManager = new VideoLoadingManager();

      manager.setVideoLoadingManager(newVideoManager);

      // Should not throw
      expect(() => manager.setVideoLoadingManager(newVideoManager)).not.toThrow();
    });

    it('should cancel video loading when going offline', () => {
      const cancelSpy = vi.spyOn(videoLoadingManager, 'cancelLoad');

      manager.registerPendingRequest('req_123');
      window.dispatchEvent(new Event('offline'));

      expect(cancelSpy).toHaveBeenCalled();
    });
  });

  describe('Before Unload Handler', () => {
    it('should handle beforeunload event with pending requests', () => {
      manager.registerPendingRequest('req_123');

      const event = new Event('beforeunload') as BeforeUnloadEvent;
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault');

      window.dispatchEvent(event);

      expect(preventDefaultSpy).toHaveBeenCalled();
      expect(manager.getState().cancelledRequests.has('req_123')).toBe(true);
    });
  });

  describe('Cleanup', () => {
    it('should cleanup on destroy', () => {
      const callback = vi.fn();
      manager.subscribe(callback);

      manager.destroy();

      // Trigger event after destroy
      window.dispatchEvent(new Event('offline'));

      // Callback should not be called after destroy
      expect(callback).toHaveBeenCalledTimes(1); // Only initial call
    });
  });

  describe('Factory Function', () => {
    it('should create instance from factory', () => {
      const instance = createOfflineModeManager(networkDetector, videoLoadingManager);

      expect(instance).toBeInstanceOf(OfflineModeManager);

      instance.destroy();
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid online/offline changes', () => {
      const callback = vi.fn();
      manager.subscribe(callback);

      // Rapid changes
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));

      expect(callback).toHaveBeenCalled();
      expect(manager.isOffline()).toBe(false);
    });

    it('should handle multiple pending requests', () => {
      for (let i = 0; i < 10; i++) {
        manager.registerPendingRequest(`req_${i}`);
      }

      expect(manager.getPendingRequestsCount()).toBe(10);

      window.dispatchEvent(new Event('offline'));

      const state = manager.getState();
      expect(state.pendingRequests.size).toBe(0);
      expect(state.cancelledRequests.size).toBe(10);
    });

    it('should handle subscriber errors gracefully', () => {
      const errorCallback = vi.fn(() => {
        throw new Error('Subscriber error');
      });
      const normalCallback = vi.fn();

      manager.subscribe(errorCallback);
      manager.subscribe(normalCallback);

      // Should not throw
      expect(() => {
        window.dispatchEvent(new Event('offline'));
      }).not.toThrow();

      expect(normalCallback).toHaveBeenCalled();
    });
  });
});
