/**
 * OfflineModeUI - Offline mode kullanıcı arayüzü bileşeni
 *
 * Bu bileşen, kullanıcı offline olduğunda gösterilir ve
 * network durumu hakkında bilgi verir.
 *
 * @module OfflineModeUI
 * @requires Requirements: 5.19, 10.6, 10.7
 */

import * as React from 'react';

import { NetworkState } from '../services/NetworkDetector';
import { OfflineModeState } from '../services/OfflineModeManager';

/**
 * OfflineModeUI props
 */
export interface OfflineModeUIProps {
  networkState: NetworkState;
  offlineModeState: OfflineModeState;
  onRetry?: () => void;
  onDismiss?: () => void;
  style?: React.CSSProperties;
}

/**
 * Format duration to human-readable string
 */
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours} saat ${minutes % 60} dakika`;
  } else if (minutes > 0) {
    return `${minutes} dakika ${seconds % 60} saniye`;
  } else {
    return `${seconds} saniye`;
  }
}

/**
 * OfflineModeUI Component
 */
export const OfflineModeUI: React.FC<OfflineModeUIProps> = ({
  networkState,
  offlineModeState,
  onRetry,
  onDismiss,
  style,
}) => {
  // Don't show if online
  if (!offlineModeState.showOfflineUI) {
    return null;
  }

  // Determine message and color based on network status
  const getMessage = (): { icon: string; title: string; message: string; color: string } => {
    if (networkState.status === 'offline') {
      return {
        icon: '🔴',
        title: 'İnternet Bağlantısı Yok',
        message: 'İnternet bağlantınız kesildi. Lütfen bağlantınızı kontrol edin.',
        color: '#dc3545',
      };
    } else if (networkState.status === 'slow') {
      return {
        icon: '⚠️',
        title: 'Yavaş Bağlantı',
        message: 'İnternet bağlantınız yavaş. Videolar yüklenmesi uzun sürebilir.',
        color: '#ffc107',
      };
    } else if (offlineModeState.reconnectionInProgress) {
      return {
        icon: '🔄',
        title: 'Yeniden Bağlanılıyor',
        message: 'İnternet bağlantınız geri geldi. Videolar yeniden yükleniyor...',
        color: '#17a2b8',
      };
    } else {
      return {
        icon: '🔴',
        title: 'Bağlantı Sorunu',
        message: 'Bir bağlantı sorunu oluştu.',
        color: '#dc3545',
      };
    }
  };

  const { icon, title, message, color } = getMessage();

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        backgroundColor: color,
        color: 'white',
        padding: '15px 20px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        animation: 'slideDown 0.3s ease-out',
        ...style,
      }}
    >
      {/* Left side - Icon and message */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px', flex: 1 }}>
        <div style={{ fontSize: '24px' }}>{icon}</div>
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '4px' }}>
            {title}
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>
            {message}
          </div>
          {offlineModeState.offlineDuration && offlineModeState.offlineDuration > 5000 && (
            <div style={{ fontSize: '12px', opacity: 0.8, marginTop: '4px' }}>
              Offline süresi: {formatDuration(offlineModeState.offlineDuration)}
            </div>
          )}
          {networkState.rtt && (
            <div style={{ fontSize: '12px', opacity: 0.8, marginTop: '4px' }}>
              Bağlantı hızı: {networkState.rtt}ms
              {networkState.downlink && ` (${networkState.downlink.toFixed(1)} Mbps)`}
            </div>
          )}
        </div>
      </div>

      {/* Right side - Actions */}
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        {/* Reconnection attempts indicator */}
        {networkState.reconnectionAttempts > 0 && (
          <div
            style={{
              fontSize: '12px',
              padding: '4px 8px',
              backgroundColor: 'rgba(255,255,255,0.2)',
              borderRadius: '12px',
            }}
          >
            Deneme {networkState.reconnectionAttempts}/5
          </div>
        )}

        {/* Retry button */}
        {onRetry && !offlineModeState.reconnectionInProgress && (
          <button
            onClick={onRetry}
            style={{
              padding: '8px 16px',
              backgroundColor: 'white',
              color: color,
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
            }}
          >
            🔄 Tekrar Dene
          </button>
        )}

        {/* Loading spinner for reconnection */}
        {offlineModeState.reconnectionInProgress && (
          <div
            style={{
              width: '20px',
              height: '20px',
              border: '3px solid rgba(255,255,255,0.3)',
              borderTop: '3px solid white',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }}
          />
        )}

        {/* Dismiss button */}
        {onDismiss && (
          <button
            onClick={onDismiss}
            style={{
              padding: '8px',
              backgroundColor: 'transparent',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '18px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.2)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
            title="Kapat"
          >
            ✕
          </button>
        )}
      </div>

      {/* CSS animations */}
      <style>{`
        @keyframes slideDown {
          from {
            transform: translateY(-100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
};

/**
 * Compact OfflineModeUI - Daha küçük banner versiyonu
 */
export const CompactOfflineModeUI: React.FC<OfflineModeUIProps> = ({
  networkState,
  offlineModeState,
  onRetry,
  style,
}) => {
  // Don't show if online
  if (!offlineModeState.showOfflineUI) {
    return null;
  }

  const isOffline = networkState.status === 'offline';
  const isSlow = networkState.status === 'slow';

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 9999,
        backgroundColor: isOffline ? '#dc3545' : '#ffc107',
        color: 'white',
        padding: '12px 16px',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        animation: 'fadeIn 0.3s ease-out',
        maxWidth: '300px',
        ...style,
      }}
    >
      <div style={{ fontSize: '20px' }}>
        {isOffline ? '🔴' : isSlow ? '⚠️' : '🔄'}
      </div>
      <div style={{ flex: 1, fontSize: '14px' }}>
        {isOffline ? 'Bağlantı yok' : isSlow ? 'Yavaş bağlantı' : 'Yeniden bağlanılıyor'}
      </div>
      {onRetry && !offlineModeState.reconnectionInProgress && (
        <button
          onClick={onRetry}
          style={{
            padding: '6px 12px',
            backgroundColor: 'white',
            color: isOffline ? '#dc3545' : '#ffc107',
            border: 'none',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 'bold',
            cursor: 'pointer',
          }}
        >
          Tekrar Dene
        </button>
      )}

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default OfflineModeUI;
