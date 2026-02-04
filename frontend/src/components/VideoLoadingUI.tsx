/**
 * VideoLoadingUI - Gelişmiş video yükleme UI bileşeni
 * 
 * Bu bileşen, video yükleme sürecinde kullanıcıya zengin geri bildirim sağlar:
 * - Animasyonlu progress bar ve spinner
 * - Dinamik yükleme mesajları (konu bazlı)
 * - Başarı mesajı (video sayısı ile)
 * - Gelişmiş hata gösterimi
 * - Tekrar dene ve fallback butonları
 * - Yükleme süresi gösterimi
 * - Smooth fade-in animasyonları
 * 
 * @module VideoLoadingUI
 * @requires Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.7, 3.11
 */

import React from 'react';
import { VideoLoadingState, SubjectVideos } from '../services/VideoLoadingManager';

/**
 * VideoLoadingUI Props
 */
export interface VideoLoadingUIProps {
  state: VideoLoadingState;
  onRetry?: () => void;
  onShowFallback?: () => void;
  onCancel?: () => void;
  subjects?: string[]; // Yüklenen konular listesi
}

/**
 * Dinamik yükleme mesajları - konu bazlı (Req 3.1)
 */
const LOADING_MESSAGES = [
  { progress: 0, message: '🤖 AI size özel videoları buluyor...' },
  { progress: 20, message: '🔍 YouTube\'da en kaliteli içerikler aranıyor...' },
  { progress: 40, message: '📊 Videolar seviyenize göre filtreleniyor...' },
  { progress: 60, message: '🎯 En alakalı içerikler seçiliyor...' },
  { progress: 80, message: '✨ Kişiselleştirilmiş öneriler hazırlanıyor...' },
  { progress: 95, message: '🎉 Neredeyse hazır!' },
];

/**
 * Konu bazlı dinamik mesaj oluştur
 */
function getSubjectMessage(subjects: string[], progress: number): string {
  if (!subjects || subjects.length === 0) {
    return LOADING_MESSAGES.find(m => progress >= m.progress)?.message || LOADING_MESSAGES[0].message;
  }

  const subject = subjects[Math.floor((progress / 100) * subjects.length)] || subjects[0];
  
  if (progress < 30) {
    return `🔍 AI ${subject} konusunda videolar buluyor...`;
  } else if (progress < 60) {
    return `📊 ${subject} için en kaliteli içerikler seçiliyor...`;
  } else if (progress < 90) {
    return `✨ ${subject} videoları hazırlanıyor...`;
  } else {
    return `🎉 ${subject} videoları neredeyse hazır!`;
  }
}

/**
 * VideoLoadingUI Component
 */
export const VideoLoadingUI: React.FC<VideoLoadingUIProps> = ({
  state,
  onRetry,
  onShowFallback,
  onCancel,
  subjects = [],
}) => {
  // Loading state (Req 3.1, 3.2)
  if (state.status === 'loading') {
    const message = getSubjectMessage(subjects, state.loadingProgress);
    const elapsedSeconds = Math.floor(state.loadingTime / 1000);

    return (
      <section
        role="status"
        aria-live="polite"
        aria-atomic="true"
        aria-label="Video yükleme durumu"
        lang="tr"
        style={{
          backgroundColor: 'white',
          padding: '60px 40px',
          borderRadius: '12px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
          marginBottom: '30px',
          textAlign: 'center',
          animation: 'fadeIn 0.3s ease-in',
        }}
      >
        {/* Animated spinner (Req 3.2) - WCAG: Decorative, hidden from screen readers */}
        <div
          role="img"
          aria-label="Yükleniyor"
          style={{
            width: '80px',
            height: '80px',
            margin: '0 auto 30px',
            border: '6px solid #f3f3f3',
            borderTop: '6px solid #6f42c1',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />

        {/* Dynamic loading message (Req 3.1) - WCAG: Proper heading */}
        <h2
          id="loading-message"
          style={{
            color: '#333',
            marginBottom: '20px',
            fontSize: '24px',
            animation: 'pulse 2s ease-in-out infinite',
          }}
        >
          {message}
        </h2>

        {/* Progress bar (Req 3.2) - WCAG: Accessible progressbar */}
        <div
          role="progressbar"
          aria-valuenow={state.loadingProgress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-labelledby="loading-message"
          aria-label={`Video yükleme ilerlemesi: yüzde ${state.loadingProgress}`}
          style={{
            width: '100%',
            maxWidth: '400px',
            height: '12px',
            backgroundColor: '#e9ecef',
            borderRadius: '20px',
            margin: '0 auto 20px',
            overflow: 'hidden',
            boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)',
          }}
        >
          <div
            style={{
              width: `${state.loadingProgress}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #6f42c1, #8e44ad)',
              borderRadius: '20px',
              transition: 'width 0.3s ease',
              boxShadow: '0 0 10px rgba(111, 66, 193, 0.5)',
            }}
          />
        </div>

        {/* Progress percentage - WCAG: Better contrast */}
        <p
          style={{
            color: '#6f42c1',
            fontSize: '18px',
            fontWeight: 'bold',
            marginBottom: '10px',
          }}
          aria-live="polite"
        >
          <span aria-hidden="true">%</span>
          <span>{state.loadingProgress}</span>
        </p>

        {/* Loading time display (Req 3.6) - WCAG: Better contrast and emoji handling */}
        {elapsedSeconds > 0 && (
          <p
            style={{
              color: '#595959',
              fontSize: '14px',
              marginBottom: '20px',
            }}
          >
            <span role="img" aria-label="Zaman">⏱️</span> Geçen süre: {elapsedSeconds} saniye
          </p>
        )}

        {/* Warning message after 5 seconds (Req 3.7) - WCAG: Accessible alert */}
        {elapsedSeconds >= 5 && (
          <aside
            role="status"
            aria-live="polite"
            style={{
              backgroundColor: '#fff3cd',
              border: '1px solid #ffc107',
              borderRadius: '8px',
              padding: '15px',
              marginTop: '20px',
              animation: 'fadeIn 0.3s ease-in',
            }}
          >
            <p
              style={{
                color: '#856404',
                fontSize: '14px',
                margin: 0,
              }}
            >
              <span role="img" aria-label="Bekleme">⏳</span> Videolar yükleniyor, lütfen bekleyin...
            </p>
          </aside>
        )}

        {/* Retry count indicator - WCAG: Better contrast */}
        {state.retryCount > 0 && (
          <p
            style={{
              color: '#595959',
              fontSize: '12px',
              marginTop: '15px',
            }}
            aria-live="polite"
          >
            <span role="img" aria-label="Yeniden deneme">🔄</span> Deneme {state.retryCount + 1}
          </p>
        )}

        {/* Cancel button (Req 3.8) - WCAG: Accessible button with focus indicator */}
        {onCancel && (
          <button
            onClick={onCancel}
            type="button"
            aria-label="Video yüklemeyi iptal et"
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              backgroundColor: '#f8f9fa',
              color: '#495057',
              border: '2px solid #dee2e6',
              borderRadius: '8px',
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = '#e9ecef';
              e.currentTarget.style.borderColor = '#adb5bd';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = '#f8f9fa';
              e.currentTarget.style.borderColor = '#dee2e6';
            }}
            onFocus={(e) => {
              e.currentTarget.style.outline = '3px solid #6f42c1';
              e.currentTarget.style.outlineOffset = '2px';
            }}
            onBlur={(e) => {
              e.currentTarget.style.outline = 'none';
            }}
          >
            <span aria-hidden="true">❌</span> İptal Et
          </button>
        )}

        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
          }
          
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
          }
          
          /* WCAG: Reduced motion support */
          @media (prefers-reduced-motion: reduce) {
            * {
              animation-duration: 0.01ms !important;
              animation-iteration-count: 1 !important;
              transition-duration: 0.01ms !important;
            }
          }
        `}</style>
      </section>
    );
  }

  // Success state (Req 3.3)
  if (state.status === 'success') {
    const totalVideos = state.videos.reduce((sum, cat) => sum + (cat.videos?.length || 0), 0);
    const loadingTimeSeconds = (state.loadingTime / 1000).toFixed(1);

    return (
      <section
        role="status"
        aria-live="polite"
        aria-atomic="true"
        aria-label="Video yükleme başarılı"
        lang="tr"
        style={{
          backgroundColor: 'white',
          padding: '40px',
          borderRadius: '12px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
          marginBottom: '30px',
          textAlign: 'center',
          animation: 'fadeIn 0.5s ease-in',
          border: '2px solid #28a745',
        }}
      >
        {/* Success icon - WCAG: Meaningful emoji */}
        <div
          role="img"
          aria-label="Başarılı"
          style={{
            fontSize: '64px',
            marginBottom: '20px',
            animation: 'bounceIn 0.6s ease-out',
          }}
        >
          ✅
        </div>

        {/* Success message with video count (Req 3.3) */}
        <h2
          style={{
            color: '#28a745',
            marginBottom: '15px',
            fontSize: '28px',
          }}
        >
          <span role="img" aria-label="Kutlama">🎉</span> Videolar Başarıyla Yüklendi!
        </h2>

        <p
          style={{
            color: '#333',
            fontSize: '18px',
            marginBottom: '10px',
          }}
        >
          <strong>{totalVideos} adet</strong> kişiselleştirilmiş video bulundu
        </p>

        {/* Loading time display (Req 3.6) - WCAG: Better contrast */}
        <p
          style={{
            color: '#595959',
            fontSize: '14px',
            marginBottom: '20px',
          }}
        >
          <span role="img" aria-label="Hızlı">⚡</span> Yükleme süresi: {loadingTimeSeconds} saniye
        </p>

        {/* Cache hit indicator - WCAG: Better contrast */}
        {state.cacheHit && (
          <div
            role="status"
            style={{
              display: 'inline-block',
              backgroundColor: '#d4edda',
              border: '1px solid #c3e6cb',
              borderRadius: '20px',
              padding: '8px 16px',
              fontSize: '12px',
              color: '#155724',
              marginTop: '10px',
            }}
          >
            <span role="img" aria-label="Roket">🚀</span> Hızlı yükleme (önbellekten)
          </div>
        )}

        <style>{`
          @keyframes bounceIn {
            0% { transform: scale(0); opacity: 0; }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); opacity: 1; }
          }
        `}</style>
      </section>
    );
  }

  // Error state (Req 3.4, 3.10)
  if (state.status === 'error' || state.status === 'fallback') {
    const isFallback = state.status === 'fallback';
    const errorMessage = state.errorMessage || state.error?.message || 'Bilinmeyen hata oluştu';

    return (
      <section
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        aria-label={isFallback ? 'Zaman aşımı uyarısı' : 'Hata mesajı'}
        lang="tr"
        style={{
          backgroundColor: 'white',
          padding: '40px',
          borderRadius: '12px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
          marginBottom: '30px',
          textAlign: 'center',
          animation: 'fadeIn 0.3s ease-in',
          border: `2px solid ${isFallback ? '#ffc107' : '#dc3545'}`,
        }}
      >
        {/* Error icon - WCAG: Meaningful emoji */}
        <div
          role="img"
          aria-label={isFallback ? 'Uyarı' : 'Hata'}
          style={{
            fontSize: '64px',
            marginBottom: '20px',
          }}
        >
          {isFallback ? '⚠️' : '❌'}
        </div>

        {/* Error title */}
        <h2
          style={{
            color: isFallback ? '#856404' : '#dc3545',
            marginBottom: '15px',
            fontSize: '24px',
          }}
        >
          {isFallback ? (
            <>
              <span role="img" aria-label="Zaman">⏱️</span> Zaman Aşımı
            </>
          ) : (
            <>
              <span role="img" aria-label="Hata">❌</span> Hata Oluştu
            </>
          )}
        </h2>

        {/* User-friendly error message (Req 3.10) - WCAG: Better contrast */}
        <p
          style={{
            color: '#495057',
            fontSize: '16px',
            marginBottom: '20px',
            lineHeight: '1.6',
          }}
        >
          {errorMessage}
        </p>

        {/* Retry count - WCAG: Better contrast */}
        {state.retryCount > 0 && (
          <p
            style={{
              color: '#595959',
              fontSize: '14px',
              marginBottom: '20px',
            }}
            aria-live="polite"
          >
            <span role="img" aria-label="Yeniden deneme">🔄</span> {state.retryCount} kez denendi
          </p>
        )}

        {/* Action buttons */}
        <div
          style={{
            display: 'flex',
            gap: '15px',
            justifyContent: 'center',
            flexWrap: 'wrap',
          }}
        >
          {/* Retry button (Req 3.4) - WCAG: Accessible button with focus */}
          {onRetry && (
            <button
              onClick={onRetry}
              type="button"
              aria-label="Videoları tekrar yüklemeyi dene"
              style={{
                padding: '12px 24px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 8px rgba(0,123,255,0.3)',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = '#0056b3';
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,123,255,0.4)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = '#007bff';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,123,255,0.3)';
              }}
              onFocus={(e) => {
                e.currentTarget.style.outline = '3px solid #0056b3';
                e.currentTarget.style.outlineOffset = '2px';
              }}
              onBlur={(e) => {
                e.currentTarget.style.outline = 'none';
              }}
            >
              <span aria-hidden="true">🔄</span> Tekrar Dene
            </button>
          )}

          {/* Show fallback button (Req 3.4) - WCAG: Accessible button with focus */}
          {onShowFallback && (
            <button
              onClick={onShowFallback}
              type="button"
              aria-label="Örnek videoları göster"
              style={{
                padding: '12px 24px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 8px rgba(40,167,69,0.3)',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = '#1e7e34';
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(40,167,69,0.4)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = '#28a745';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(40,167,69,0.3)';
              }}
              onFocus={(e) => {
                e.currentTarget.style.outline = '3px solid #1e7e34';
                e.currentTarget.style.outlineOffset = '2px';
              }}
              onBlur={(e) => {
                e.currentTarget.style.outline = 'none';
              }}
            >
              <span aria-hidden="true">📺</span> Örnek Videoları Göster
            </button>
          )}
        </div>

        {/* Additional help text - WCAG: Better contrast and semantic structure */}
        <aside
          aria-label="Sorun giderme önerileri"
          style={{
            marginTop: '30px',
            padding: '15px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #dee2e6',
          }}
        >
          <p
            style={{
              color: '#495057',
              fontSize: '14px',
              margin: 0,
              lineHeight: '1.6',
            }}
          >
            <span role="img" aria-label="Öneri">💡</span> <strong>Sorun devam ederse:</strong><br />
            • İnternet bağlantınızı kontrol edin<br />
            • Sayfayı yenileyin<br />
            • Birkaç dakika sonra tekrar deneyin
          </p>
        </aside>
      </section>
    );
  }

  // Idle state - no UI needed
  return null;
};

export default VideoLoadingUI;
