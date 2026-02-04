/**
 * useOfflineMode - React hook for offline mode management
 * 
 * Bu hook, offline mode ve network detection'ı React component'lerinde
 * kullanmak için bir interface sağlar.
 * 
 * @module useOfflineMode
 * @requires Requirements: 5.19, 10.6, 10.7
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { NetworkDetector, NetworkState, getNetworkDetector } from '../services/NetworkDetector';
import { OfflineModeManager, OfflineModeState, createOfflineModeManager } from '../services/OfflineModeManager';
import { VideoLoadingManager } from '../services/VideoLoadingManager';

/**
 * useOfflineMode hook return type
 */
export interface UseOfflineModeReturn {
  // Network state
  networkState: NetworkState;
  isOnline: boolean;
  isOffline: boolean;
  isSlow: boolean;
  
  // Offline mode state
  offlineModeState: OfflineModeState;
  showOfflineUI: boolean;
  offlineDuration: number | null;
  pendingRequestsCount: number;
  reconnectionInProgress: boolean;
  
  // Actions
  checkConnection: () => Promise<boolean>;
  retryCancelledRequests: () => void;
  registerPendingRequest: (requestId: string) => void;
  unregisterPendingRequest: (requestId: string) => void;
  
  // Managers (for advanced usage)
  networkDetector: NetworkDetector;
  offlineModeManager: OfflineModeManager;
}

/**
 * useOfflineMode hook options
 */
export interface UseOfflineModeOptions {
  videoLoadingManager?: VideoLoadingManager;
  autoRetryOnReconnection?: boolean;
  maxReconnectionAttempts?: number;
  reconnectionDelay?: number;
}

/**
 * useOfflineMode - React hook for offline mode management
 * 
 * @param options - Hook options
 * @returns UseOfflineModeReturn
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const {
 *     isOnline,
 *     showOfflineUI,
 *     networkState,
 *     offlineModeState,
 *     checkConnection,
 *     retryCancelledRequests,
 *   } = useOfflineMode();
 * 
 *   return (
 *     <div>
 *       {showOfflineUI && (
 *         <OfflineModeUI
 *           networkState={networkState}
 *           offlineModeState={offlineModeState}
 *           onRetry={retryCancelledRequests}
 *         />
 *       )}
 *       <div>Status: {isOnline ? 'Online' : 'Offline'}</div>
 *     </div>
 *   );
 * }
 * ```
 */
export function useOfflineMode(options: UseOfflineModeOptions = {}): UseOfflineModeReturn {
  const {
    videoLoadingManager,
    autoRetryOnReconnection = true,
    maxReconnectionAttempts = 5,
    reconnectionDelay = 2000,
  } = options;

  // Create or get singleton instances
  const networkDetectorRef = useRef<NetworkDetector | null>(null);
  const offlineModeManagerRef = useRef<OfflineModeManager | null>(null);

  // Initialize managers
  if (!networkDetectorRef.current) {
    networkDetectorRef.current = getNetworkDetector();
  }

  if (!offlineModeManagerRef.current) {
    offlineModeManagerRef.current = createOfflineModeManager(
      networkDetectorRef.current,
      videoLoadingManager
    );
  }

  const networkDetector = networkDetectorRef.current;
  const offlineModeManager = offlineModeManagerRef.current;

  // State
  const [networkState, setNetworkState] = useState<NetworkState>(networkDetector.getState());
  const [offlineModeState, setOfflineModeState] = useState<OfflineModeState>(offlineModeManager.getState());

  // Subscribe to network changes
  useEffect(() => {
    const unsubscribeNetwork = networkDetector.subscribe((state) => {
      setNetworkState(state);
    });

    const unsubscribeOfflineMode = offlineModeManager.subscribe((state) => {
      setOfflineModeState(state);
    });

    return () => {
      unsubscribeNetwork();
      unsubscribeOfflineMode();
    };
  }, [networkDetector, offlineModeManager]);

  // Update VideoLoadingManager if provided
  useEffect(() => {
    if (videoLoadingManager) {
      offlineModeManager.setVideoLoadingManager(videoLoadingManager);
    }
  }, [videoLoadingManager, offlineModeManager]);

  // Actions
  const checkConnection = useCallback(async (): Promise<boolean> => {
    return await offlineModeManager.checkConnection();
  }, [offlineModeManager]);

  const retryCancelledRequests = useCallback(() => {
    offlineModeManager.retryCancelledRequests();
  }, [offlineModeManager]);

  const registerPendingRequest = useCallback((requestId: string) => {
    offlineModeManager.registerPendingRequest(requestId);
  }, [offlineModeManager]);

  const unregisterPendingRequest = useCallback((requestId: string) => {
    offlineModeManager.unregisterPendingRequest(requestId);
  }, [offlineModeManager]);

  // Derived state
  const isOnline = networkState.isOnline;
  const isOffline = !networkState.isOnline;
  const isSlow = networkState.status === 'slow';
  const showOfflineUI = offlineModeState.showOfflineUI;
  const offlineDuration = offlineModeState.offlineDuration;
  const pendingRequestsCount = offlineModeState.pendingRequests.size;
  const reconnectionInProgress = offlineModeState.reconnectionInProgress;

  return {
    // Network state
    networkState,
    isOnline,
    isOffline,
    isSlow,
    
    // Offline mode state
    offlineModeState,
    showOfflineUI,
    offlineDuration,
    pendingRequestsCount,
    reconnectionInProgress,
    
    // Actions
    checkConnection,
    retryCancelledRequests,
    registerPendingRequest,
    unregisterPendingRequest,
    
    // Managers
    networkDetector,
    offlineModeManager,
  };
}

/**
 * useNetworkStatus - Simplified hook for just network status
 * 
 * @returns Network status information
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { isOnline, isSlow, status } = useNetworkStatus();
 * 
 *   return <div>Network: {status}</div>;
 * }
 * ```
 */
export function useNetworkStatus() {
  const networkDetector = getNetworkDetector();
  const [networkState, setNetworkState] = useState<NetworkState>(networkDetector.getState());

  useEffect(() => {
    const unsubscribe = networkDetector.subscribe((state) => {
      setNetworkState(state);
    });

    return unsubscribe;
  }, [networkDetector]);

  return {
    status: networkState.status,
    isOnline: networkState.isOnline,
    isOffline: !networkState.isOnline,
    isSlow: networkState.status === 'slow',
    effectiveType: networkState.effectiveType,
    downlink: networkState.downlink,
    rtt: networkState.rtt,
    reconnectionAttempts: networkState.reconnectionAttempts,
  };
}

export default useOfflineMode;
