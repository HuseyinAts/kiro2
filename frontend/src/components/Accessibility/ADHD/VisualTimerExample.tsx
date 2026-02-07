/**
 * Visual Timer Example - Görsel Zamanlayıcı Örnek Kullanım
 *
 * VisualTimer bileşeninin nasıl kullanılacağını gösteren örnek component.
 *
 * Requirements: REQ-52.6 - REQ-52.10
 * Task: 88.2 Görsel zamanlayıcı
 */

import * as React from 'react';
import {  useState  } from 'react';

import VisualTimer from './VisualTimer';

const VisualTimerExample: React.FC = () => {
  const [sessionId, _setSessionId] = useState<string>('demo-session-123');
  const [size, setSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [showNotification, setShowNotification] = useState<boolean>(false);

  const handleTimerEnd = () => {
    setShowNotification(true);

    // Bildirimi 3 saniye sonra gizle
    setTimeout(() => {
      setShowNotification(false);
    }, 3000);

    // Gerçek uygulamada:
    // - Ses çal
    // - Browser notification göster
    // - Sonraki oturumu başlat
    console.log('⏰ Pomodoro oturumu tamamlandı!');
  };

  const handleSizeChange = (newSize: 'small' | 'medium' | 'large') => {
    setSize(newSize);
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '2rem' }}>
        Görsel Zamanlayıcı Demo
      </h1>

      {/* Size Selector */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: '1rem',
        marginBottom: '2rem',
      }}>
        <button
          onClick={() => handleSizeChange('small')}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: size === 'small' ? '#4299e1' : '#e2e8f0',
            color: size === 'small' ? 'white' : '#2d3748',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            fontWeight: size === 'small' ? 'bold' : 'normal',
          }}
        >
          Küçük
        </button>
        <button
          onClick={() => handleSizeChange('medium')}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: size === 'medium' ? '#4299e1' : '#e2e8f0',
            color: size === 'medium' ? 'white' : '#2d3748',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            fontWeight: size === 'medium' ? 'bold' : 'normal',
          }}
        >
          Orta
        </button>
        <button
          onClick={() => handleSizeChange('large')}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: size === 'large' ? '#4299e1' : '#e2e8f0',
            color: size === 'large' ? 'white' : '#2d3748',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            fontWeight: size === 'large' ? 'bold' : 'normal',
          }}
        >
          Büyük
        </button>
      </div>

      {/* Notification */}
      {showNotification && (
        <div
          style={{
            position: 'fixed',
            top: '2rem',
            right: '2rem',
            backgroundColor: '#48bb78',
            color: 'white',
            padding: '1rem 1.5rem',
            borderRadius: '0.5rem',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            zIndex: 1000,
            animation: 'slideIn 0.3s ease-out',
          }}
          role="alert"
        >
          🎉 Pomodoro oturumu tamamlandı!
        </div>
      )}

      {/* Visual Timer */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        marginBottom: '2rem',
      }}>
        <VisualTimer
          sessionId={sessionId}
          size={size}
          onTimerEnd={handleTimerEnd}
          showControls={true}
        />
      </div>

      {/* Info Panel */}
      <div style={{
        backgroundColor: '#f7fafc',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        marginTop: '2rem',
      }}>
        <h3 style={{ marginTop: 0 }}>ℹ️ Bilgi</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li>
            <strong>Session ID:</strong> {sessionId}
          </li>
          <li>
            <strong>Boyut:</strong> {size}
          </li>
          <li>
            <strong>Özellikler:</strong>
            <ul>
              <li>✅ Gerçek zamanlı countdown</li>
              <li>✅ Progress ring (ilerleme halkası)</li>
              <li>✅ Kalan süre gösterimi</li>
              <li>✅ Oturum tipi göstergesi</li>
              <li>✅ Renk kodlu gösterim</li>
              <li>✅ Aktif/Duraklatıldı durumu</li>
            </ul>
          </li>
        </ul>
      </div>

      {/* Usage Example */}
      <div style={{
        backgroundColor: '#2d3748',
        color: '#f7fafc',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        marginTop: '2rem',
        fontFamily: 'monospace',
        fontSize: '0.875rem',
        overflow: 'auto',
      }}>
        <h3 style={{ marginTop: 0, color: '#f7fafc' }}>📝 Kullanım Örneği</h3>
        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
{`import { VisualTimer } from '@/components/Accessibility/ADHD';

function PomodoroPage() {
  const handleTimerEnd = () => {
    console.log('Timer tamamlandı!');
  };

  return (
    <VisualTimer 
      sessionId="session-123"
      size="medium"
      onTimerEnd={handleTimerEnd}
    />
  );
}`}
        </pre>
      </div>

      {/* Requirements */}
      <div style={{
        backgroundColor: '#edf2f7',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        marginTop: '2rem',
      }}>
        <h3 style={{ marginTop: 0 }}>✅ Requirements (REQ-52.6 - REQ-52.10)</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li>
            <strong>REQ-52.6:</strong> Görsel countdown gösterimi ✅
          </li>
          <li>
            <strong>REQ-52.7:</strong> Progress ring gösterimi ✅
          </li>
          <li>
            <strong>REQ-52.8:</strong> Kalan süre gösterimi ✅
          </li>
          <li>
            <strong>REQ-52.9:</strong> Oturum tipi gösterimi ✅
          </li>
          <li>
            <strong>REQ-52.10:</strong> Renk kodlu gösterim ✅
          </li>
        </ul>
      </div>

      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default VisualTimerExample;
