/**
 * Visual Timer Component - Görsel Zamanlayıcı
 *
 * DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) desteği için görsel zamanlayıcı.
 * Pomodoro oturumları için gerçek zamanlı countdown, progress ring ve kalan süre gösterimi.
 *
 * Requirements: REQ-52.6 - REQ-52.10
 * Task: 88.2 Görsel zamanlayıcı
 *
 * Features:
 * - Visual countdown (görsel geri sayım)
 * - Progress ring (ilerleme halkası)
 * - Time remaining display (kalan süre gösterimi)
 * - Session type indicator (oturum tipi göstergesi)
 * - Color-coded by session type (oturum tipine göre renk kodlu)
 */

import * as React from 'react';
import {  useEffect, useState  } from 'react';
import './VisualTimer.css';

interface VisualTimerData {
  session_id: string;
  remaining_seconds: number;
  total_seconds: number;
  progress_percentage: number;
  time_display: string;
  is_active: boolean;
  session_type: 'work' | 'short_break' | 'long_break';
  color_scheme: {
    primary: string;
    secondary: string;
    background: string;
  };
}

interface VisualTimerProps {
  sessionId: string;
  onTimerEnd?: () => void;
  size?: 'small' | 'medium' | 'large';
  showControls?: boolean;
}

const VisualTimer: React.FC<VisualTimerProps> = ({
  sessionId,
  onTimerEnd,
  size = 'medium',
  showControls: _showControls = true,
}) => {
  const [timerData, setTimerData] = useState<VisualTimerData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Size configurations
  const sizeConfig = {
    small: { radius: 60, strokeWidth: 8, fontSize: '1.5rem' },
    medium: { radius: 100, strokeWidth: 12, fontSize: '2.5rem' },
    large: { radius: 140, strokeWidth: 16, fontSize: '3.5rem' },
  };

  const config = sizeConfig[size];
  const circumference = 2 * Math.PI * config.radius;

  // Fetch timer data
  const fetchTimerData = async () => {
    try {
      const response = await fetch(`/api/adhd-support/timer/visual/${sessionId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Zamanlayıcı verileri alınamadı');
      }

      const data = await response.json();
      setTimerData(data);
      setError(null);

      // Check if timer ended
      if (data.remaining_seconds === 0 && onTimerEnd) {
        onTimerEnd();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu');
    } finally {
      setIsLoading(false);
    }
  };

  // Poll timer data every second
  useEffect(() => {
    fetchTimerData();
    const interval = setInterval(fetchTimerData, 1000);

    return () => clearInterval(interval);
  }, [sessionId]);

  // Calculate stroke dash offset for progress ring
  const getStrokeDashOffset = () => {
    if (!timerData) {return circumference;}
    const progress = timerData.progress_percentage / 100;
    return circumference * (1 - progress);
  };

  // Format time display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Get session type label in Turkish
  const getSessionTypeLabel = (type: string): string => {
    const labels = {
      work: 'Çalışma',
      short_break: 'Kısa Mola',
      long_break: 'Uzun Mola',
    };
    return labels[type as keyof typeof labels] || type;
  };

  // Get session type emoji
  const getSessionTypeEmoji = (type: string): string => {
    const emojis = {
      work: '💪',
      short_break: '☕',
      long_break: '🌟',
    };
    return emojis[type as keyof typeof emojis] || '⏱️';
  };

  if (isLoading) {
    return (
      <div className="visual-timer-loading" role="status" aria-live="polite">
        <div className="spinner" aria-hidden="true"></div>
        <span className="sr-only">Zamanlayıcı yükleniyor...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="visual-timer-error" role="alert">
        <span className="error-icon" aria-hidden="true">⚠️</span>
        <p>{error}</p>
      </div>
    );
  }

  if (!timerData) {
    return null;
  }

  const svgSize = (config.radius + config.strokeWidth) * 2;

  return (
    <div
      className={`visual-timer visual-timer-${size}`}
      style={{ backgroundColor: timerData.color_scheme.background }}
      role="timer"
      aria-label={`${getSessionTypeLabel(timerData.session_type)} zamanlayıcısı`}
      aria-live="polite"
      aria-atomic="true"
    >
      {/* Session Type Header */}
      <div className="timer-header">
        <span className="session-emoji" aria-hidden="true">
          {getSessionTypeEmoji(timerData.session_type)}
        </span>
        <h3 className="session-type">
          {getSessionTypeLabel(timerData.session_type)}
        </h3>
      </div>

      {/* Progress Ring SVG */}
      <div className="timer-ring-container">
        <svg
          width={svgSize}
          height={svgSize}
          className="timer-ring"
          role="img"
          aria-label={`İlerleme: yüzde ${timerData.progress_percentage.toFixed(0)}`}
          focusable="false"
        >
          {/* Background circle */}
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={config.radius}
            fill="none"
            stroke={timerData.color_scheme.secondary}
            strokeWidth={config.strokeWidth}
            opacity="0.3"
          />

          {/* Progress circle */}
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={config.radius}
            fill="none"
            stroke={timerData.color_scheme.primary}
            strokeWidth={config.strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={getStrokeDashOffset()}
            strokeLinecap="round"
            transform={`rotate(-90 ${svgSize / 2} ${svgSize / 2})`}
            className="progress-ring"
          />
        </svg>

        {/* Time Display (centered over ring) */}
        <div
          className="time-display"
          style={{ fontSize: config.fontSize }}
          aria-label={`Kalan süre: ${Math.floor(timerData.remaining_seconds / 60)} dakika ${timerData.remaining_seconds % 60} saniye`}
        >
          <span className="time-text" aria-hidden="true">
            {formatTime(timerData.remaining_seconds)}
          </span>
        </div>
      </div>

      {/* Progress Percentage */}
      <div className="timer-info">
        <div className="progress-percentage">
          <span className="percentage-value">
            {timerData.progress_percentage.toFixed(0)}%
          </span>
          <span className="percentage-label">Tamamlandı</span>
        </div>

        {/* Status Indicator */}
        <div className="status-indicator">
          <span
            className={`status-dot ${timerData.is_active ? 'active' : 'paused'}`}
            aria-hidden="true"
          ></span>
          <span className="status-text">
            {timerData.is_active ? 'Aktif' : 'Duraklatıldı'}
          </span>
        </div>
      </div>

      {/* Screen Reader Only - Detailed Status */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {getSessionTypeLabel(timerData.session_type)} oturumu.
        Kalan süre: {Math.floor(timerData.remaining_seconds / 60)} dakika {timerData.remaining_seconds % 60} saniye.
        İlerleme: yüzde {timerData.progress_percentage.toFixed(0)}.
        Durum: {timerData.is_active ? 'Aktif' : 'Duraklatıldı'}.
      </div>
    </div>
  );
};

export default VisualTimer;
