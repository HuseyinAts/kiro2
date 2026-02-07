/**
 * PWA Durum Bileşeni
 * Çevrimdışı durum, senkronizasyon ve PWA kurulum bilgilerini gösterir
 */

import * as React from 'react';
import {  useState  } from 'react';

import { usePWA, useNetworkStatus } from '../hooks/usePWA';

interface PWAStatusProps {
  className?: string;
  showDetails?: boolean;
}

export const PWAStatus: React.FC<PWAStatusProps> = ({
  className = '',
  showDetails = false,
}) => {
  const {
    isInstallable,
    isInstalled,
    isOnline,
    syncStatus,
    offlineStats,
    installPWA,
    triggerSync,
    downloadQuestionsForOffline,
    clearOfflineData,
    subscribeToPushNotifications,
  } = usePWA();

  const { connectionType } = useNetworkStatus();
  const [isExpanded, setIsExpanded] = useState(showDetails);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadSubject, setDownloadSubject] = useState('matematik');

  const handleInstallPWA = async () => {
    const success = await installPWA();
    if (success) {
      alert('Uygulama başarıyla kuruldu! Artık ana ekranınızdan erişebilirsiniz.');
    }
  };

  const handleDownloadQuestions = async () => {
    setIsDownloading(true);
    try {
      await downloadQuestionsForOffline(downloadSubject, 100);
      alert(`${downloadSubject} konusu için 100 soru başarıyla indirildi!`);
    } catch {
      alert('Soru indirme başarısız. Lütfen internet bağlantınızı kontrol edin.');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleClearData = async () => {
    if (window.confirm('Tüm çevrimdışı veriler silinecek. Emin misiniz?')) {
      try {
        await clearOfflineData();
        alert('Çevrimdışı veriler başarıyla temizlendi.');
      } catch {
        alert('Veri temizleme başarısız.');
      }
    }
  };

  const handleSubscribeNotifications = async () => {
    const success = await subscribeToPushNotifications();
    if (success) {
      alert('Bildirimler başarıyla etkinleştirildi!');
    } else {
      alert('Bildirim izni gerekli. Lütfen tarayıcı ayarlarından izin verin.');
    }
  };

  const getConnectionIcon = () => {
    if (!isOnline) {return '❌';}

    switch (connectionType) {
      case '4g': return '📶';
      case '3g': return '📶';
      case '2g': return '📱';
      case 'slow-2g': return '🐌';
      default: return '🌐';
    }
  };

  const getConnectionText = () => {
    if (!isOnline) {return 'Çevrimdışı';}

    switch (connectionType) {
      case '4g': return 'Hızlı Bağlantı (4G)';
      case '3g': return 'Orta Hız (3G)';
      case '2g': return 'Yavaş Bağlantı (2G)';
      case 'slow-2g': return 'Çok Yavaş (2G)';
      default: return 'Çevrimiçi';
    }
  };

  return (
    <div className={`pwa-status ${className}`}>
      {/* Kompakt Durum Çubuğu */}
      <div
        className="pwa-status-bar"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 16px',
          background: isOnline ? '#e8f5e8' : '#fff3cd',
          border: `1px solid ${isOnline ? '#28a745' : '#ffc107'}`,
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '14px',
          marginBottom: isExpanded ? '10px' : '0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>{getConnectionIcon()}</span>
          <span>{getConnectionText()}</span>
          {(syncStatus?.pendingItems ?? 0) > 0 && (
            <span style={{
              background: '#dc3545',
              color: 'white',
              padding: '2px 6px',
              borderRadius: '10px',
              fontSize: '12px',
            }}>
              {syncStatus?.pendingItems} bekliyor
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isInstalled && <span title="PWA Kurulu">📱</span>}
          {offlineStats && offlineStats.totalQuestions > 0 && (
            <span title={`${offlineStats.totalQuestions} çevrimdışı soru`}>
              📚 {offlineStats.totalQuestions}
            </span>
          )}
          <span style={{ fontSize: '12px' }}>
            {isExpanded ? '▼' : '▶'}
          </span>
        </div>
      </div>

      {/* Detaylı Panel */}
      {isExpanded && (
        <div
          className="pwa-details"
          style={{
            background: 'white',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '16px',
          }}
        >
          {/* PWA Kurulum */}
          {isInstallable && (
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ margin: '0 0 8px 0', color: '#495057' }}>
                📱 Uygulama Kurulumu
              </h4>
              <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#6c757d' }}>
                Uygulamayı ana ekranınıza ekleyerek daha hızlı erişim sağlayın
              </p>
              <button
                onClick={handleInstallPWA}
                style={{
                  background: '#007bff',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Uygulamayı Kur
              </button>
            </div>
          )}

          {/* Çevrimdışı İstatistikler */}
          {offlineStats && (
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ margin: '0 0 8px 0', color: '#495057' }}>
                📊 Çevrimdışı Veriler
              </h4>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: '8px',
                fontSize: '14px',
              }}>
                <div>
                  <strong>{offlineStats.totalQuestions}</strong>
                  <br />
                  <span style={{ color: '#6c757d' }}>Soru</span>
                </div>
                <div>
                  <strong>{offlineStats.totalExams}</strong>
                  <br />
                  <span style={{ color: '#6c757d' }}>Sınav</span>
                </div>
                <div>
                  <strong>{offlineStats.totalNotes}</strong>
                  <br />
                  <span style={{ color: '#6c757d' }}>Not</span>
                </div>
                <div>
                  <strong>{offlineStats.storageUsed} KB</strong>
                  <br />
                  <span style={{ color: '#6c757d' }}>Depolama</span>
                </div>
              </div>
            </div>
          )}

          {/* Soru İndirme */}
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#495057' }}>
              📥 Çevrimdışı Soru İndirme
            </h4>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <select
                value={downloadSubject}
                onChange={(e) => setDownloadSubject(e.target.value)}
                style={{
                  padding: '6px 8px',
                  border: '1px solid #ced4da',
                  borderRadius: '4px',
                  fontSize: '14px',
                }}
              >
                <option value="matematik">Matematik</option>
                <option value="turkce">Türkçe</option>
                <option value="fen">Fen Bilimleri</option>
                <option value="sosyal">Sosyal Bilgiler</option>
                <option value="fizik">Fizik</option>
                <option value="kimya">Kimya</option>
                <option value="biyoloji">Biyoloji</option>
                <option value="tarih">Tarih</option>
                <option value="cografya">Coğrafya</option>
              </select>
              <button
                onClick={handleDownloadQuestions}
                disabled={!isOnline || isDownloading}
                style={{
                  background: isOnline ? '#28a745' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: isOnline ? 'pointer' : 'not-allowed',
                  fontSize: '14px',
                }}
              >
                {isDownloading ? '⏳ İndiriliyor...' : '📥 100 Soru İndir'}
              </button>
            </div>
          </div>

          {/* Senkronizasyon */}
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#495057' }}>
              🔄 Senkronizasyon
            </h4>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                onClick={triggerSync}
                disabled={!isOnline || syncStatus?.syncInProgress}
                style={{
                  background: isOnline ? '#17a2b8' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: isOnline ? 'pointer' : 'not-allowed',
                  fontSize: '14px',
                }}
              >
                {syncStatus?.syncInProgress ? '⏳ Senkronize ediliyor...' : '🔄 Şimdi Senkronize Et'}
              </button>

              {syncStatus?.lastSync && (
                <span style={{ fontSize: '12px', color: '#6c757d' }}>
                  Son: {new Date(syncStatus.lastSync).toLocaleString('tr-TR')}
                </span>
              )}
            </div>
          </div>

          {/* Bildirimler */}
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#495057' }}>
              🔔 Bildirimler
            </h4>
            <button
              onClick={handleSubscribeNotifications}
              style={{
                background: '#6f42c1',
                color: 'white',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              🔔 Bildirimleri Etkinleştir
            </button>
          </div>

          {/* Veri Yönetimi */}
          <div>
            <h4 style={{ margin: '0 0 8px 0', color: '#495057' }}>
              🗑️ Veri Yönetimi
            </h4>
            <button
              onClick={handleClearData}
              style={{
                background: '#dc3545',
                color: 'white',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              🗑️ Çevrimdışı Verileri Temizle
            </button>
          </div>

          {/* Çevrimdışı Mod Linki */}
          {!isOnline && (
            <div style={{
              marginTop: '16px',
              padding: '12px',
              background: '#fff3cd',
              border: '1px solid #ffc107',
              borderRadius: '4px',
            }}>
              <p style={{ margin: '0 0 8px 0', fontSize: '14px' }}>
                İnternet bağlantınız yok. Çevrimdışı modda çalışmaya devam edebilirsiniz.
              </p>
              <a
                href="/offline-app.html"
                style={{
                  display: 'inline-block',
                  background: '#ffc107',
                  color: '#212529',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  textDecoration: 'none',
                  fontSize: '14px',
                  fontWeight: 'bold',
                }}
              >
                📚 Çevrimdışı Çalışmaya Başla
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Basit PWA Kurulum Butonu
 */
export const PWAInstallButton: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { isInstallable, installPWA } = usePWA();

  if (!isInstallable) {return null;}

  const handleInstall = async () => {
    const success = await installPWA();
    if (success) {
      alert('Uygulama başarıyla kuruldu!');
    }
  };

  return (
    <button
      onClick={handleInstall}
      className={`pwa-install-button ${className}`}
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        background: '#007bff',
        color: 'white',
        border: 'none',
        padding: '12px 20px',
        borderRadius: '25px',
        cursor: 'pointer',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        zIndex: 1000,
        fontSize: '14px',
        fontWeight: 'bold',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}
    >
      📱 Uygulamayı Yükle
    </button>
  );
};

/**
 * Çevrimdışı Durum Göstergesi
 */
export const OfflineIndicator: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { isOnline } = useNetworkStatus();

  if (isOnline) {return null;}

  return (
    <div
      className={`offline-indicator ${className}`}
      style={{
        position: 'fixed',
        top: '0',
        left: '0',
        right: '0',
        background: '#dc3545',
        color: 'white',
        padding: '8px',
        textAlign: 'center',
        fontSize: '14px',
        zIndex: 1001,
      }}
    >
      ❌ İnternet bağlantısı yok - Çevrimdışı modda çalışıyorsunuz
    </div>
  );
};