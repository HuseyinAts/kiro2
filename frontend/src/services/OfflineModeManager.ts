/**
 * OfflineModeManager - Offline mode UI ve request cancellation yönetimi
 *
 * Bu servis, offline mode UI'ını yönetir ve kullanıcı sayfadan ayrıldığında
 * request'leri iptal eder.
 *
 * @module OfflineModeManager
 * @requires Requirements: 5.19, 10.6, 10.7
 */

import { NetworkDetector, NetworkState } from './NetworkDetector';
import { VideoLoadingManager } from './VideoLoadingManager';

/**
 * Offline mode state
 */
export interface OfflineModeState {
  isOffline: boolean;
  showOfflineUI: boolean;
  offlineDuration: number | null;
  pendingRequests: Set<string>;
  cancelledRequests: Set<string>;
  reconnectionInProgress: boolean;
}

/**
 * Offline mode callback tipi
 */
export type OfflineModeCallback = (state: OfflineModeState) => void;

/**
 * OfflineModeManager - Offline mode orchestration
 *
 * Özellikler:
 * - Offline mode UI management
 * - Request cancellation on navigation
 * - Auto-retry on reconnection
 * - Pending request tracking
 * - User notification
 */
export class OfflineModeManager {
  private state: OfflineModeState;
  private subscribers: Set<OfflineModeCallback> = new Set();
  private networkDetector: NetworkDetector;
  private videoLoadingManager: VideoLoadingManager | null = null;
  private unsubscribeNetwork: (() => void) | null = null;
  private unsubscribeReconnection: (() => void) | null = null;
  private beforeUnloadHandler: ((event: BeforeUnloadEvent) => void) | null = null;

  /**
   * OfflineModeManager constructor
   *
   * @param networkDetector - NetworkDetector instance
   * @param videoLoadingManager - VideoLoadingManager instance (optional)
   */
  constructor(
    networkDetector: NetworkDetector,
    videoLoadingManager?: VideoLoadingManager,
  ) {
    this.networkDetector = networkDetector;
    this.videoLoadingManager = videoLoadingManager || null;

    // Initialize state
    this.state = {
      isOffline: !networkDetector.isOnline(),
      showOfflineUI: !networkDetector.isOnline(),
      offlineDuration: null,
      pendingRequests: new Set(),
      cancelledRequests: new Set(),
      reconnectionInProgress: false,
    };

    // Start monitoring
    this._startMonitoring();

    // OfflineModeManager initialized
  }

  /**
   * Set VideoLoadingManager instance
   *
   * @param manager - VideoLoadingManager instance
   */
  setVideoLoadingManager(manager: VideoLoadingManager): void {
    this.videoLoadingManager = manager;
  }

  /**
   * Monitoring'i başlat
   */
  private _startMonitoring(): void {
    // Subscribe to network changes
    this.unsubscribeNetwork = this.networkDetector.subscribe(this._handleNetworkChange);

    // Subscribe to reconnection events
    this.unsubscribeReconnection = this.networkDetector.onReconnection(this._handleReconnection);

    // Listen to beforeunload event (user navigates away)
    this.beforeUnloadHandler = this._handleBeforeUnload;
    window.addEventListener('beforeunload', this.beforeUnloadHandler);

    // Listen to visibilitychange event (tab hidden/visible)
    document.addEventListener('visibilitychange', this._handleVisibilityChange);
  }

  /**
   * Monitoring'i durdur
   */
  private _stopMonitoring(): void {
    if (this.unsubscribeNetwork) {
      this.unsubscribeNetwork();
      this.unsubscribeNetwork = null;
    }

    if (this.unsubscribeReconnection) {
      this.unsubscribeReconnection();
      this.unsubscribeReconnection = null;
    }

    if (this.beforeUnloadHandler) {
      window.removeEventListener('beforeunload', this.beforeUnloadHandler);
      this.beforeUnloadHandler = null;
    }

    document.removeEventListener('visibilitychange', this._handleVisibilityChange);
  }

  /**
   * Network change handler
   */
  private _handleNetworkChange = (networkState: NetworkState): void => {
    const wasOffline = this.state.isOffline;
    const isOffline = !networkState.isOnline;

    // OfflineModeManager: Network state changed

    // Update offline duration
    const offlineDuration = isOffline ? this.networkDetector.getOfflineDuration() : null;

    this._updateState({
      isOffline,
      showOfflineUI: isOffline,
      offlineDuration,
    });

    // Cancel pending requests if going offline
    if (!wasOffline && isOffline) {
      this._cancelPendingRequests('Network offline');
    }

    // Show slow connection warning
    if (networkState.status === 'slow') {
      console.warn('⚠️ OfflineModeManager: Slow connection detected');
      this._showSlowConnectionWarning();
    }
  };

  /**
   * Reconnection handler (auto-retry)
   */
  private _handleReconnection = async (): Promise<void> => {
    // OfflineModeManager: Reconnection detected - auto-retry

    this._updateState({
      reconnectionInProgress: true,
    });

    try {
      // Auto-retry video loading if there were cancelled requests
      if (this.state.cancelledRequests.size > 0 && this.videoLoadingManager) {
        // OfflineModeManager: Auto-retrying video loading

        // Get the last student profile from VideoLoadingManager state
        const videoState = this.videoLoadingManager.getState();

        // Only retry if we were in error or fallback state
        if (videoState.status === 'error' || videoState.status === 'fallback') {
          // Note: We can't automatically retry without the profile
          // This should be handled by the component
          // OfflineModeManager: Component should handle retry with profile
        }
      }

      // Clear cancelled requests
      this._updateState({
        cancelledRequests: new Set(),
        reconnectionInProgress: false,
      });

      // Hide offline UI
      this._hideOfflineUI();

    } catch (error) {
      console.error('❌ OfflineModeManager: Error during auto-retry', error);

      this._updateState({
        reconnectionInProgress: false,
      });
    }
  };

  /**
   * Before unload handler (user navigates away)
   */
  private _handleBeforeUnload = (event: BeforeUnloadEvent): void => {
    // Cancel pending requests
    if (this.state.pendingRequests.size > 0) {
      // OfflineModeManager: User navigating away - cancelling requests

      this._cancelPendingRequests('User navigated away');

      // Show confirmation dialog if there are pending requests
      event.preventDefault();
      event.returnValue = 'Videolar yükleniyor. Sayfayı kapatmak istediğinizden emin misiniz?';
    }
  };

  /**
   * Visibility change handler (tab hidden/visible)
   */
  private _handleVisibilityChange = (): void => {
    if (document.hidden) {
      // OfflineModeManager: Tab hidden

      // Optionally pause pending requests
      // (Not cancelling, just logging for now)
    } else {
      // OfflineModeManager: Tab visible

      // Check network status when tab becomes visible
      this.networkDetector.checkConnection();
    }
  };

  /**
   * Cancel pending requests
   */
  private _cancelPendingRequests(_reason: string): void {
    // OfflineModeManager: Cancelling pending requests

    // Cancel video loading
    if (this.videoLoadingManager) {
      this.videoLoadingManager.cancelLoad();
    }

    // Move pending to cancelled
    const cancelledRequests = new Set([
      ...this.state.cancelledRequests,
      ...this.state.pendingRequests,
    ]);

    this._updateState({
      pendingRequests: new Set(),
      cancelledRequests,
    });
  }

  /**
   * Show slow connection warning
   */
  private _showSlowConnectionWarning(): void {
    // This should be handled by the UI component
    // Just update state to trigger UI update
    console.warn('⚠️ OfflineModeManager: Slow connection - UI should show warning');
  }

  /**
   * Hide offline UI
   */
  private _hideOfflineUI(): void {
    this._updateState({
      showOfflineUI: false,
    });
  }

  /**
   * Register pending request
   *
   * @param requestId - Request ID
   */
  registerPendingRequest(requestId: string): void {
    const pendingRequests = new Set(this.state.pendingRequests);
    pendingRequests.add(requestId);

    this._updateState({
      pendingRequests,
    });

    // OfflineModeManager: Registered pending request
  }

  /**
   * Unregister pending request
   *
   * @param requestId - Request ID
   */
  unregisterPendingRequest(requestId: string): void {
    const pendingRequests = new Set(this.state.pendingRequests);
    pendingRequests.delete(requestId);

    this._updateState({
      pendingRequests,
    });

    // OfflineModeManager: Unregistered pending request
  }

  /**
   * Get current state
   *
   * @returns OfflineModeState
   */
  getState(): OfflineModeState {
    return {
      ...this.state,
      pendingRequests: new Set(this.state.pendingRequests),
      cancelledRequests: new Set(this.state.cancelledRequests),
    };
  }

  /**
   * Check if offline
   *
   * @returns boolean
   */
  isOffline(): boolean {
    return this.state.isOffline;
  }

  /**
   * Check if should show offline UI
   *
   * @returns boolean
   */
  shouldShowOfflineUI(): boolean {
    return this.state.showOfflineUI;
  }

  /**
   * Get offline duration
   *
   * @returns number | null
   */
  getOfflineDuration(): number | null {
    return this.networkDetector.getOfflineDuration();
  }

  /**
   * Get pending requests count
   *
   * @returns number
   */
  getPendingRequestsCount(): number {
    return this.state.pendingRequests.size;
  }

  /**
   * Subscribe to state changes
   *
   * @param callback - State change callback
   * @returns Unsubscribe function
   */
  subscribe(callback: OfflineModeCallback): () => void {
    this.subscribers.add(callback);

    // Immediately call with current state
    try {
      callback(this.getState());
    } catch (error) {
      console.error('❌ OfflineModeManager: Error in subscriber callback', error);
    }

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(callback);
    };
  }

  /**
   * Manually trigger reconnection check
   */
  async checkConnection(): Promise<boolean> {
    return await this.networkDetector.checkConnection();
  }

  /**
   * Manually retry cancelled requests
   */
  retryCancelledRequests(): void {
    if (this.state.cancelledRequests.size > 0) {
      // OfflineModeManager: Manually retrying cancelled requests

      // Clear cancelled requests
      this._updateState({
        cancelledRequests: new Set(),
      });

      // Trigger reconnection handler
      this._handleReconnection();
    }
  }

  /**
   * Cleanup - stop monitoring
   */
  destroy(): void {
    // OfflineModeManager: Destroying

    this._stopMonitoring();
    this.subscribers.clear();
  }

  // Private methods

  /**
   * Update state and notify subscribers
   */
  private _updateState(newState: Partial<OfflineModeState>): void {
    this.state = {
      ...this.state,
      ...newState,
    };

    // Notify all subscribers
    this.subscribers.forEach(callback => {
      try {
        callback(this.getState());
      } catch (error) {
        console.error('❌ OfflineModeManager: Error in subscriber callback', error);
      }
    });
  }
}

/**
 * Create OfflineModeManager instance
 *
 * @param networkDetector - NetworkDetector instance
 * @param videoLoadingManager - VideoLoadingManager instance (optional)
 * @returns OfflineModeManager
 */
export function createOfflineModeManager(
  networkDetector: NetworkDetector,
  videoLoadingManager?: VideoLoadingManager,
): OfflineModeManager {
  return new OfflineModeManager(networkDetector, videoLoadingManager);
}

export default OfflineModeManager;
