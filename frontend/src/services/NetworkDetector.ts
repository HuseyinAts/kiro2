/**
 * NetworkDetector - Network status detection ve offline mode yönetimi
 *
 * Bu servis, kullanıcının internet bağlantısını izler ve offline/online durumlarını yönetir.
 * Network reconnection handling, auto-retry ve request cancellation sağlar.
 *
 * @module NetworkDetector
 * @requires Requirements: 5.19, 10.6, 10.7
 */

import config from '../config';

/**
 * Network durumu
 */
export type NetworkStatus = 'online' | 'offline' | 'slow' | 'unknown';

/**
 * Network state
 */
export interface NetworkState {
  status: NetworkStatus;
  isOnline: boolean;
  lastOnlineTime: number | null;
  lastOfflineTime: number | null;
  reconnectionAttempts: number;
  effectiveType?: string; // '4g', '3g', '2g', 'slow-2g'
  downlink?: number; // Mbps
  rtt?: number; // Round-trip time in ms
}

/**
 * Network değişiklik callback tipi
 */
export type NetworkChangeCallback = (state: NetworkState) => void;

/**
 * Reconnection callback tipi
 */
export type ReconnectionCallback = () => void | Promise<void>;

/**
 * NetworkDetector - Network durumu izleme ve yönetimi
 *
 * Özellikler:
 * - Online/offline detection
 * - Network quality monitoring (slow connection detection)
 * - Automatic reconnection handling
 * - State subscription mechanism
 * - Auto-retry on reconnection
 * - Request cancellation on offline
 */
export class NetworkDetector {
  private state: NetworkState;
  private subscribers: Set<NetworkChangeCallback> = new Set();
  private reconnectionCallbacks: Set<ReconnectionCallback> = new Set();
  private checkInterval: number | null = null;
  private reconnectionTimeout: number | null = null;
  private maxReconnectionAttempts: number;
  private reconnectionDelay: number;

  /**
   * NetworkDetector constructor
   *
   * @param maxReconnectionAttempts - Maximum reconnection attempts (default: 5)
   * @param reconnectionDelay - Delay between reconnection attempts in ms (default: 2000)
   */
  constructor(
    maxReconnectionAttempts: number = 5,
    reconnectionDelay: number = 2000,
  ) {
    this.maxReconnectionAttempts = maxReconnectionAttempts;
    this.reconnectionDelay = reconnectionDelay;

    // Initialize state
    this.state = {
      status: navigator.onLine ? 'online' : 'offline',
      isOnline: navigator.onLine,
      lastOnlineTime: navigator.onLine ? Date.now() : null,
      lastOfflineTime: navigator.onLine ? null : Date.now(),
      reconnectionAttempts: 0,
    };

    // Start monitoring
    this._startMonitoring();

    // NetworkDetector initialized
  }

  /**
   * Network monitoring'i başlat
   */
  private _startMonitoring(): void {
    // Listen to online/offline events
    window.addEventListener('online', this._handleOnline);
    window.addEventListener('offline', this._handleOffline);

    // Check network quality periodically (every 30 seconds)
    this.checkInterval = window.setInterval(() => {
      this._checkNetworkQuality();
    }, 30000);

    // Initial network quality check
    this._checkNetworkQuality();
  }

  /**
   * Network monitoring'i durdur
   */
  private _stopMonitoring(): void {
    window.removeEventListener('online', this._handleOnline);
    window.removeEventListener('offline', this._handleOffline);

    if (this.checkInterval !== null) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }

    if (this.reconnectionTimeout !== null) {
      clearTimeout(this.reconnectionTimeout);
      this.reconnectionTimeout = null;
    }
  }

  /**
   * Online event handler
   */
  private _handleOnline = (): void => {
    // NetworkDetector: Network online

    this._updateState({
      status: 'online',
      isOnline: true,
      lastOnlineTime: Date.now(),
      reconnectionAttempts: 0,
    });

    // Trigger reconnection callbacks
    this._triggerReconnectionCallbacks();
  };

  /**
   * Offline event handler
   */
  private _handleOffline = (): void => {
    // NetworkDetector: Network offline

    this._updateState({
      status: 'offline',
      isOnline: false,
      lastOfflineTime: Date.now(),
    });

    // Start reconnection attempts
    this._startReconnectionAttempts();
  };

  /**
   * Network kalitesini kontrol et
   */
  private async _checkNetworkQuality(): Promise<void> {
    if (!navigator.onLine) {
      return;
    }

    try {
      // Check if Network Information API is available
      const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

      if (connection) {
        const effectiveType = connection.effectiveType; // '4g', '3g', '2g', 'slow-2g'
        const downlink = connection.downlink; // Mbps
        const rtt = connection.rtt; // Round-trip time in ms

        // Determine if connection is slow
        const isSlow = effectiveType === 'slow-2g' || effectiveType === '2g' || rtt > 1000;

        this._updateState({
          status: isSlow ? 'slow' : 'online',
          effectiveType,
          downlink,
          rtt,
        });

        if (isSlow) {
          console.warn('⚠️ NetworkDetector: Slow connection detected', {
            effectiveType,
            downlink: `${downlink} Mbps`,
            rtt: `${rtt}ms`,
          });
        }
      } else {
        // Fallback: Ping test
        await this._performPingTest();
      }
    } catch (error) {
      console.error('❌ NetworkDetector: Error checking network quality', error);
    }
  }

  /**
   * Ping test ile network kalitesini kontrol et
   */
  private async _performPingTest(): Promise<void> {
    const startTime = Date.now();

    try {
      // Ping backend health endpoint instead of external resource
      const response = await fetch(`${config.api.baseURL}/health`, {
        method: 'GET',
        cache: 'no-cache',
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });

      const rtt = Date.now() - startTime;

      if (response.ok) {
        const isSlow = rtt > 1000; // > 1 second is considered slow

        this._updateState({
          status: isSlow ? 'slow' : 'online',
          rtt,
        });

        if (isSlow) {
          console.warn('⚠️ NetworkDetector: Slow connection detected (ping test)', {
            rtt: `${rtt}ms`,
          });
        }
      }
    } catch (error) {
      // Ping failed - but we're in development, so don't mark as offline
      // Only mark as offline if navigator.onLine is also false
      console.warn('⚠️ NetworkDetector: Ping test failed (backend may be down)', error);

      if (!navigator.onLine) {
        this._updateState({
          status: 'offline',
          isOnline: false,
          lastOfflineTime: Date.now(),
        });
      } else {
        // Backend is down but network is up - keep status as online
        // NetworkDetector: Backend unreachable but network is up
        this._updateState({
          status: 'online',
          isOnline: true,
        });
      }
    }
  }

  /**
   * Reconnection attempts başlat
   */
  private _startReconnectionAttempts(): void {
    if (this.state.reconnectionAttempts >= this.maxReconnectionAttempts) {
      console.warn('⚠️ NetworkDetector: Max reconnection attempts reached');
      return;
    }

    const attempt = this.state.reconnectionAttempts + 1;
    const delay = this.reconnectionDelay * Math.pow(2, attempt - 1); // Exponential backoff

    // NetworkDetector: Reconnection attempt

    this._updateState({
      reconnectionAttempts: attempt,
    });

    this.reconnectionTimeout = window.setTimeout(async () => {
      // Check if we're back online
      if (navigator.onLine) {
        // Verify with ping test
        await this._performPingTest();

        if (this.state.isOnline) {
          // NetworkDetector: Reconnection successful
          this._triggerReconnectionCallbacks();
          return;
        }
      }

      // Still offline - try again
      this._startReconnectionAttempts();
    }, delay);
  }

  /**
   * Reconnection callbacks'i tetikle
   */
  private _triggerReconnectionCallbacks(): void {
    // NetworkDetector: Triggering reconnection callbacks

    this.reconnectionCallbacks.forEach(async (callback) => {
      try {
        await callback();
      } catch (error) {
        console.error('❌ NetworkDetector: Error in reconnection callback', error);
      }
    });
  }

  /**
   * Get current network state
   *
   * @returns NetworkState
   */
  getState(): NetworkState {
    return { ...this.state };
  }

  /**
   * Check if online
   *
   * @returns boolean
   */
  isOnline(): boolean {
    return this.state.isOnline;
  }

  /**
   * Check if offline
   *
   * @returns boolean
   */
  isOffline(): boolean {
    return !this.state.isOnline;
  }

  /**
   * Check if connection is slow
   *
   * @returns boolean
   */
  isSlow(): boolean {
    return this.state.status === 'slow';
  }

  /**
   * Get offline duration in milliseconds
   *
   * @returns number | null
   */
  getOfflineDuration(): number | null {
    if (this.state.isOnline || !this.state.lastOfflineTime) {
      return null;
    }

    return Date.now() - this.state.lastOfflineTime;
  }

  /**
   * Subscribe to network state changes
   *
   * @param callback - Network change callback
   * @returns Unsubscribe function
   */
  subscribe(callback: NetworkChangeCallback): () => void {
    this.subscribers.add(callback);

    // Immediately call with current state
    callback(this.state);

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(callback);
    };
  }

  /**
   * Register reconnection callback (auto-retry on reconnection)
   *
   * @param callback - Reconnection callback
   * @returns Unregister function
   */
  onReconnection(callback: ReconnectionCallback): () => void {
    this.reconnectionCallbacks.add(callback);

    // Return unregister function
    return () => {
      this.reconnectionCallbacks.delete(callback);
    };
  }

  /**
   * Manually trigger reconnection check
   */
  async checkConnection(): Promise<boolean> {
    // NetworkDetector: Manual connection check

    await this._performPingTest();

    return this.state.isOnline;
  }

  /**
   * Reset reconnection attempts
   */
  resetReconnectionAttempts(): void {
    this._updateState({
      reconnectionAttempts: 0,
    });

    if (this.reconnectionTimeout !== null) {
      clearTimeout(this.reconnectionTimeout);
      this.reconnectionTimeout = null;
    }
  }

  /**
   * Cleanup - stop monitoring
   */
  destroy(): void {
    // NetworkDetector: Destroying

    this._stopMonitoring();
    this.subscribers.clear();
    this.reconnectionCallbacks.clear();
  }

  // Private methods

  /**
   * Update state and notify subscribers
   */
  private _updateState(newState: Partial<NetworkState>): void {
    this.state = {
      ...this.state,
      ...newState,
    };

    // Status change logged for debugging
    // previousStatus !== this.state.status

    // Notify all subscribers
    this.subscribers.forEach(callback => {
      try {
        callback(this.state);
      } catch (error) {
        console.error('❌ NetworkDetector: Error in subscriber callback', error);
      }
    });
  }
}

/**
 * Singleton instance for global usage
 */
let globalInstance: NetworkDetector | null = null;

/**
 * Get or create global NetworkDetector instance
 *
 * @returns NetworkDetector
 */
export function getNetworkDetector(): NetworkDetector {
  if (!globalInstance) {
    globalInstance = new NetworkDetector();
  }
  return globalInstance;
}

/**
 * Create new NetworkDetector instance
 *
 * @param maxReconnectionAttempts - Maximum reconnection attempts
 * @param reconnectionDelay - Delay between reconnection attempts in ms
 * @returns NetworkDetector
 */
export function createNetworkDetector(
  maxReconnectionAttempts?: number,
  reconnectionDelay?: number,
): NetworkDetector {
  return new NetworkDetector(maxReconnectionAttempts, reconnectionDelay);
}

export default NetworkDetector;
