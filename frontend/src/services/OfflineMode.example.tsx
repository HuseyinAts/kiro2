/**
 * OfflineMode Integration Example
 * 
 * Bu dosya, offline mode ve network detection özelliklerinin
 * nasıl kullanılacağını gösteren örnek implementasyonlar içerir.
 * 
 * @module OfflineMode.example
 */

import React from 'react';
import { useOfflineMode, useNetworkStatus } from '../hooks/useOfflineMode';
import { OfflineModeUI, CompactOfflineModeUI } from '../components/OfflineModeUI';
import { VideoLoadingManager } from './VideoLoadingManager';

/**
 * Example 1: Basic Offline Mode Integration
 * 
 * En basit kullanım - sadece offline/online durumunu göster
 */
export const BasicOfflineModeExample: React.FC = () => {
  const { isOnline, isOffline, isSlow } = useNetworkStatus();

  return (
    <div>
      <h2>Network Status</h2>
      <div>
        Status: {isOnline ? '🟢 Online' : '🔴 Offline'}
        {isSlow && ' ⚠️ Slow Connection'}
      </div>
    </div>
  );
};

/**
 * Example 2: Full Offline Mode with UI Banner
 * 
 * Offline mode UI banner ile tam entegrasyon
 */
export const FullOfflineModeExample: React.FC = () => {
  const {
    isOnline,
    showOfflineUI,
    networkState,
    offlineModeState,
    retryCancelledRequests,
  } = useOfflineMode();

  return (
    <div>
      {/* Offline Mode UI Banner */}
      <OfflineModeUI
        networkState={networkState}
        offlineModeState={offlineModeState}
        onRetry={retryCancelledRequests}
        onDismiss={() => console.log('Banner dismissed')}
      />

      {/* Main Content */}
      <div style={{ padding: '20px' }}>
        <h1>My App</h1>
        <p>Network Status: {isOnline ? 'Online' : 'Offline'}</p>
      </div>
    </div>
  );
};

/**
 * Example 3: Compact Offline Mode UI
 * 
 * Daha küçük, sağ alt köşede gösterilen banner
 */
export const CompactOfflineModeExample: React.FC = () => {
  const {
    networkState,
    offlineModeState,
    retryCancelledRequests,
  } = useOfflineMode();

  return (
    <div>
      {/* Compact Offline Mode UI */}
      <CompactOfflineModeUI
        networkState={networkState}
        offlineModeState={offlineModeState}
        onRetry={retryCancelledRequests}
      />

      {/* Main Content */}
      <div style={{ padding: '20px' }}>
        <h1>My App</h1>
        <p>Content here...</p>
      </div>
    </div>
  );
};

/**
 * Example 4: Video Loading with Offline Mode
 * 
 * VideoLoadingManager ile offline mode entegrasyonu
 */
export const VideoLoadingWithOfflineModeExample: React.FC = () => {
  const videoManagerRef = React.useRef<VideoLoadingManager | null>(null);

  // Initialize VideoLoadingManager
  React.useEffect(() => {
    const API_BASE_URL = 'http://localhost:8001';
    videoManagerRef.current = new VideoLoadingManager(API_BASE_URL, 20000, 2);
  }, []);

  // Use offline mode with VideoLoadingManager
  const {
    isOnline,
    isOffline,
    showOfflineUI,
    networkState,
    offlineModeState,
    retryCancelledRequests,
    registerPendingRequest,
    unregisterPendingRequest,
  } = useOfflineMode({
    videoLoadingManager: videoManagerRef.current || undefined,
    autoRetryOnReconnection: true,
  });

  // Load videos function
  const loadVideos = async () => {
    // Check if offline
    if (isOffline) {
      alert('İnternet bağlantısı yok. Lütfen bağlantınızı kontrol edin.');
      return;
    }

    if (!videoManagerRef.current) {
      console.error('VideoLoadingManager not initialized');
      return;
    }

    // Generate request ID
    const requestId = `video-load-${Date.now()}`;

    try {
      // Register pending request
      registerPendingRequest(requestId);

      // Load videos
      const profile = {
        goals: ['TYT Matematik'],
        currentLevel: { matematik: 5 },
        learningStyle: 'visual',
        preferences: {},
      };

      const recommendations = await videoManagerRef.current.loadVideos(profile);

      console.log('Videos loaded:', recommendations);

      // Unregister pending request
      unregisterPendingRequest(requestId);
    } catch (error) {
      console.error('Error loading videos:', error);

      // Unregister pending request
      unregisterPendingRequest(requestId);
    }
  };

  return (
    <div>
      {/* Offline Mode UI */}
      <OfflineModeUI
        networkState={networkState}
        offlineModeState={offlineModeState}
        onRetry={retryCancelledRequests}
      />

      {/* Main Content */}
      <div style={{ padding: '20px' }}>
        <h1>Video Library</h1>
        <button
          onClick={loadVideos}
          disabled={isOffline}
          style={{
            padding: '10px 20px',
            backgroundColor: isOffline ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: isOffline ? 'not-allowed' : 'pointer',
          }}
        >
          {isOffline ? '🔴 Offline - Cannot Load' : '📺 Load Videos'}
        </button>

        {offlineModeState.pendingRequests.size > 0 && (
          <div style={{ marginTop: '10px', color: '#666' }}>
            Loading... ({offlineModeState.pendingRequests.size} pending requests)
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Example 5: Auto-Retry on Reconnection
 * 
 * Network yeniden bağlandığında otomatik retry
 */
export const AutoRetryExample: React.FC = () => {
  const [lastAttempt, setLastAttempt] = React.useState<Date | null>(null);
  const [attemptCount, setAttemptCount] = React.useState(0);

  const {
    isOnline,
    networkState,
    offlineModeState,
    retryCancelledRequests,
  } = useOfflineMode({
    autoRetryOnReconnection: true,
    maxReconnectionAttempts: 5,
    reconnectionDelay: 2000,
  });

  // Monitor reconnection attempts
  React.useEffect(() => {
    if (offlineModeState.reconnectionInProgress) {
      setLastAttempt(new Date());
      setAttemptCount(prev => prev + 1);
    }
  }, [offlineModeState.reconnectionInProgress]);

  return (
    <div style={{ padding: '20px' }}>
      <h1>Auto-Retry Example</h1>

      <div style={{ marginBottom: '20px' }}>
        <h3>Network Status</h3>
        <p>Status: {isOnline ? '🟢 Online' : '🔴 Offline'}</p>
        <p>Reconnection Attempts: {networkState.reconnectionAttempts}/5</p>
        {offlineModeState.reconnectionInProgress && (
          <p>🔄 Reconnecting...</p>
        )}
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Attempt History</h3>
        <p>Total Attempts: {attemptCount}</p>
        {lastAttempt && (
          <p>Last Attempt: {lastAttempt.toLocaleTimeString()}</p>
        )}
      </div>

      <button
        onClick={retryCancelledRequests}
        style={{
          padding: '10px 20px',
          backgroundColor: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
        }}
      >
        🔄 Manual Retry
      </button>
    </div>
  );
};

/**
 * Example 6: Request Cancellation on Navigation
 * 
 * Kullanıcı sayfadan ayrıldığında request'leri iptal et
 */
export const RequestCancellationExample: React.FC = () => {
  const {
    offlineModeState,
    registerPendingRequest,
    unregisterPendingRequest,
  } = useOfflineMode();

  const [isLoading, setIsLoading] = React.useState(false);

  const startLongRunningRequest = async () => {
    const requestId = `long-request-${Date.now()}`;

    try {
      setIsLoading(true);
      registerPendingRequest(requestId);

      // Simulate long-running request
      await new Promise((resolve) => setTimeout(resolve, 10000));

      console.log('Request completed');
      unregisterPendingRequest(requestId);
      setIsLoading(false);
    } catch (error) {
      console.error('Request failed:', error);
      unregisterPendingRequest(requestId);
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Request Cancellation Example</h1>

      <div style={{ marginBottom: '20px' }}>
        <p>Pending Requests: {offlineModeState.pendingRequests.size}</p>
        <p>Cancelled Requests: {offlineModeState.cancelledRequests.size}</p>
      </div>

      <button
        onClick={startLongRunningRequest}
        disabled={isLoading}
        style={{
          padding: '10px 20px',
          backgroundColor: isLoading ? '#ccc' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: isLoading ? 'not-allowed' : 'pointer',
        }}
      >
        {isLoading ? '⏳ Loading...' : '🚀 Start Long Request'}
      </button>

      <p style={{ marginTop: '10px', color: '#666', fontSize: '14px' }}>
        💡 Try navigating away or going offline while the request is running.
        The request will be automatically cancelled.
      </p>
    </div>
  );
};

/**
 * Example 7: Slow Connection Warning
 * 
 * Yavaş bağlantı uyarısı göster
 */
export const SlowConnectionExample: React.FC = () => {
  const { isSlow, networkState } = useNetworkStatus();

  return (
    <div style={{ padding: '20px' }}>
      <h1>Slow Connection Example</h1>

      {isSlow && (
        <div
          style={{
            padding: '15px',
            backgroundColor: '#fff3cd',
            border: '1px solid #ffc107',
            borderRadius: '6px',
            marginBottom: '20px',
          }}
        >
          <strong>⚠️ Yavaş Bağlantı Tespit Edildi</strong>
          <p style={{ margin: '5px 0 0 0', fontSize: '14px' }}>
            İnternet bağlantınız yavaş. Videolar yüklenmesi uzun sürebilir.
          </p>
          {networkState.rtt && (
            <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#666' }}>
              Bağlantı hızı: {networkState.rtt}ms
              {networkState.downlink && ` (${networkState.downlink.toFixed(1)} Mbps)`}
            </p>
          )}
        </div>
      )}

      <div>
        <h3>Network Details</h3>
        <ul>
          <li>Status: {networkState.status}</li>
          <li>Effective Type: {networkState.effectiveType || 'Unknown'}</li>
          <li>RTT: {networkState.rtt ? `${networkState.rtt}ms` : 'Unknown'}</li>
          <li>Downlink: {networkState.downlink ? `${networkState.downlink.toFixed(1)} Mbps` : 'Unknown'}</li>
        </ul>
      </div>
    </div>
  );
};

/**
 * Example 8: Complete Integration
 * 
 * Tüm özellikleri içeren tam entegrasyon örneği
 */
export const CompleteIntegrationExample: React.FC = () => {
  const videoManagerRef = React.useRef<VideoLoadingManager | null>(null);
  const [videos, setVideos] = React.useState<any[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);

  // Initialize VideoLoadingManager
  React.useEffect(() => {
    const API_BASE_URL = 'http://localhost:8001';
    videoManagerRef.current = new VideoLoadingManager(API_BASE_URL, 20000, 2);
  }, []);

  // Use offline mode
  const {
    isOnline,
    isOffline,
    isSlow,
    showOfflineUI,
    networkState,
    offlineModeState,
    retryCancelledRequests,
    registerPendingRequest,
    unregisterPendingRequest,
  } = useOfflineMode({
    videoLoadingManager: videoManagerRef.current || undefined,
    autoRetryOnReconnection: true,
  });

  // Load videos
  const loadVideos = async () => {
    if (isOffline) {
      alert('İnternet bağlantısı yok. Lütfen bağlantınızı kontrol edin.');
      return;
    }

    if (!videoManagerRef.current) return;

    const requestId = `video-load-${Date.now()}`;

    try {
      setIsLoading(true);
      registerPendingRequest(requestId);

      const profile = {
        goals: ['TYT Matematik'],
        currentLevel: { matematik: 5 },
        learningStyle: 'visual',
        preferences: {},
      };

      const recommendations = await videoManagerRef.current.loadVideos(profile);
      setVideos(recommendations);

      unregisterPendingRequest(requestId);
      setIsLoading(false);
    } catch (error) {
      console.error('Error loading videos:', error);
      unregisterPendingRequest(requestId);
      setIsLoading(false);
    }
  };

  return (
    <div>
      {/* Offline Mode UI */}
      <OfflineModeUI
        networkState={networkState}
        offlineModeState={offlineModeState}
        onRetry={() => {
          retryCancelledRequests();
          if (videos.length === 0) {
            loadVideos();
          }
        }}
      />

      {/* Main Content */}
      <div style={{ padding: '20px' }}>
        <h1>Complete Integration Example</h1>

        {/* Network Status */}
        <div
          style={{
            padding: '15px',
            backgroundColor: isOnline ? '#d4edda' : '#f8d7da',
            border: `1px solid ${isOnline ? '#c3e6cb' : '#f5c6cb'}`,
            borderRadius: '6px',
            marginBottom: '20px',
          }}
        >
          <strong>
            {isOnline ? '🟢 Online' : '🔴 Offline'}
            {isSlow && ' ⚠️ Slow Connection'}
          </strong>
          <p style={{ margin: '5px 0 0 0', fontSize: '14px' }}>
            Pending Requests: {offlineModeState.pendingRequests.size}
          </p>
        </div>

        {/* Load Videos Button */}
        <button
          onClick={loadVideos}
          disabled={isOffline || isLoading}
          style={{
            padding: '12px 24px',
            backgroundColor: isOffline || isLoading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: isOffline || isLoading ? 'not-allowed' : 'pointer',
            fontSize: '16px',
            marginBottom: '20px',
          }}
        >
          {isLoading ? '⏳ Loading...' : isOffline ? '🔴 Offline' : '📺 Load Videos'}
        </button>

        {/* Videos List */}
        {videos.length > 0 && (
          <div>
            <h2>Videos ({videos.length})</h2>
            <ul>
              {videos.map((category, index) => (
                <li key={index}>
                  <strong>{category.subject_exam}</strong>: {category.videos.length} videos
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompleteIntegrationExample;
