/**
 * Focus Mode Component - Odak Modu
 *
 * DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) desteği için odak modu.
 * Dikkat dağıtıcı unsurları minimize ederek tek göreve odaklanmayı sağlar.
 *
 * Requirements: REQ-52.21 - REQ-52.40
 * Task: 89 Focus Mode
 *
 * Features:
 * - Single-task view (sadece aktif görev görünür)
 * - Minimal interface (minimal arayüz)
 * - Notification suppression (bildirimler kapalı)
 * - Distraction hiding (dikkat dağıtıcı unsurları gizleme)
 * - Fullscreen mode (tam ekran modu)
 */

import * as React from 'react';
import {  useState, useEffect, useCallback  } from 'react';
import './FocusMode.css';

interface FocusModeTask {
  id: string;
  title: string;
  description: string;
  estimated_duration_minutes: number;
  priority: 'low' | 'medium' | 'high';
  subject?: string;
}

interface FocusModeSettings {
  hide_sidebar: boolean;
  hide_navigation: boolean;
  hide_notifications: boolean;
  fullscreen_mode: boolean;
  minimal_ui: boolean;
  show_timer: boolean;
  show_progress: boolean;
}

interface FocusModeProps {
  taskId?: string;
  onExit?: () => void;
  initialSettings?: Partial<FocusModeSettings>;
}

const FocusMode: React.FC<FocusModeProps> = ({
  taskId,
  onExit,
  initialSettings = {},
}) => {
  const [isActive, setIsActive] = useState(false);
  const [currentTask, setCurrentTask] = useState<FocusModeTask | null>(null);
  const [settings, setSettings] = useState<FocusModeSettings>({
    hide_sidebar: true,
    hide_navigation: true,
    hide_notifications: true,
    fullscreen_mode: false,
    minimal_ui: true,
    show_timer: true,
    show_progress: true,
    ...initialSettings,
  });
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch current task
  const fetchTask = useCallback(async () => {
    if (!taskId) {return;}

    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/adhd-support/focus-mode/task/${taskId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Görev bilgileri alınamadı');
      }

      const data = await response.json();
      setCurrentTask(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu');
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  // Activate focus mode
  const activateFocusMode = useCallback(async () => {
    try {
      // Apply UI changes
      if (settings.hide_sidebar) {
        document.body.classList.add('focus-mode-hide-sidebar');
      }
      if (settings.hide_navigation) {
        document.body.classList.add('focus-mode-hide-navigation');
      }
      if (settings.hide_notifications) {
        document.body.classList.add('focus-mode-hide-notifications');
      }
      if (settings.minimal_ui) {
        document.body.classList.add('focus-mode-minimal-ui');
      }
      if (settings.fullscreen_mode && document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen();
      }

      document.body.classList.add('focus-mode-active');
      setIsActive(true);

      // Send activation event to backend
      await fetch('/api/v1/adhd-support/focus-mode/activate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          task_id: taskId,
          settings,
        }),
      });
    } catch (err) {
      console.error('Focus mode activation error:', err);
      setError('Odak modu etkinleştirilemedi');
    }
  }, [taskId, settings]);

  // Deactivate focus mode
  const deactivateFocusMode = useCallback(async () => {
    try {
      // Remove UI changes
      document.body.classList.remove(
        'focus-mode-active',
        'focus-mode-hide-sidebar',
        'focus-mode-hide-navigation',
        'focus-mode-hide-notifications',
        'focus-mode-minimal-ui',
      );

      if (document.fullscreenElement) {
        await document.exitFullscreen();
      }

      setIsActive(false);

      // Send deactivation event to backend
      await fetch('/api/v1/adhd-support/focus-mode/deactivate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          task_id: taskId,
          elapsed_seconds: elapsedSeconds,
        }),
      });

      if (onExit) {
        onExit();
      }
    } catch (err) {
      console.error('Focus mode deactivation error:', err);
    }
  }, [taskId, elapsedSeconds, onExit]);

  // Timer effect
  useEffect(() => {
    if (!isActive) {return;}

    const interval = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive]);

  // Fetch task on mount
  useEffect(() => {
    if (taskId) {
      fetchTask();
    }
  }, [taskId, fetchTask]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // ESC to exit focus mode
      if (e.key === 'Escape' && isActive) {
        deactivateFocusMode();
      }
      // F11 to toggle fullscreen
      if (e.key === 'F11') {
        e.preventDefault();
        setSettings(prev => ({
          ...prev,
          fullscreen_mode: !prev.fullscreen_mode,
        }));
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isActive, deactivateFocusMode]);

  // Format time display
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate progress percentage
  const getProgressPercentage = (): number => {
    if (!currentTask || !currentTask.estimated_duration_minutes) {return 0;}
    const estimatedSeconds = currentTask.estimated_duration_minutes * 60;
    return Math.min((elapsedSeconds / estimatedSeconds) * 100, 100);
  };

  // Get priority color
  const getPriorityColor = (priority: string): string => {
    const colors = {
      low: '#4CAF50',
      medium: '#FF9800',
      high: '#F44336',
    };
    return colors[priority as keyof typeof colors] || '#2196F3';
  };

  if (!isActive) {
    return (
      <div className="focus-mode-setup">
        <div className="setup-container">
          <div className="setup-header">
            <h2>🎯 Odak Modu</h2>
            <p>Dikkat dağıtıcı unsurları kaldırarak tek göreve odaklanın</p>
          </div>

          {isLoading && (
            <div className="loading-state" role="status">
              <div className="spinner"></div>
              <p>Görev yükleniyor...</p>
            </div>
          )}

          {error && (
            <div className="error-state" role="alert">
              <span className="error-icon">⚠️</span>
              <p>{error}</p>
            </div>
          )}

          {currentTask && (
            <div className="task-preview">
              <h3>{currentTask.title}</h3>
              {currentTask.description && (
                <p className="task-description">{currentTask.description}</p>
              )}
              {currentTask.estimated_duration_minutes && (
                <div className="task-duration">
                  <span className="duration-icon">⏱️</span>
                  <span>{currentTask.estimated_duration_minutes} dakika</span>
                </div>
              )}
              {currentTask.priority && (
                <div
                  className="task-priority"
                  style={{ borderColor: getPriorityColor(currentTask.priority) }}
                >
                  <span
                    className="priority-dot"
                    style={{ backgroundColor: getPriorityColor(currentTask.priority) }}
                  ></span>
                  <span>
                    {currentTask.priority === 'high' ? 'Yüksek' :
                     currentTask.priority === 'medium' ? 'Orta' : 'Düşük'} Öncelik
                  </span>
                </div>
              )}
            </div>
          )}

          <div className="settings-panel">
            <h3>Ayarlar</h3>
            <div className="settings-grid">
              <label className="setting-item">
                <input
                  type="checkbox"
                  checked={settings.hide_sidebar}
                  onChange={(e) => setSettings(prev => ({ ...prev, hide_sidebar: e.target.checked }))}
                />
                <span>Kenar çubuğunu gizle</span>
              </label>

              <label className="setting-item">
                <input
                  type="checkbox"
                  checked={settings.hide_navigation}
                  onChange={(e) => setSettings(prev => ({ ...prev, hide_navigation: e.target.checked }))}
                />
                <span>Navigasyonu gizle</span>
              </label>

              <label className="setting-item">
                <input
                  type="checkbox"
                  checked={settings.hide_notifications}
                  onChange={(e) => setSettings(prev => ({ ...prev, hide_notifications: e.target.checked }))}
                />
                <span>Bildirimleri kapat</span>
              </label>

              <label className="setting-item">
                <input
                  type="checkbox"
                  checked={settings.fullscreen_mode}
                  onChange={(e) => setSettings(prev => ({ ...prev, fullscreen_mode: e.target.checked }))}
                />
                <span>Tam ekran modu</span>
              </label>

              <label className="setting-item">
                <input
                  type="checkbox"
                  checked={settings.minimal_ui}
                  onChange={(e) => setSettings(prev => ({ ...prev, minimal_ui: e.target.checked }))}
                />
                <span>Minimal arayüz</span>
              </label>

              <label className="setting-item">
                <input
                  type="checkbox"
                  checked={settings.show_timer}
                  onChange={(e) => setSettings(prev => ({ ...prev, show_timer: e.target.checked }))}
                />
                <span>Zamanlayıcıyı göster</span>
              </label>
            </div>
          </div>

          <div className="setup-actions">
            <button
              className="btn-activate"
              onClick={activateFocusMode}
              disabled={!currentTask}
            >
              🎯 Odak Modunu Başlat
            </button>
            {onExit && (
              <button className="btn-cancel" onClick={onExit}>
                İptal
              </button>
            )}
          </div>

          <div className="keyboard-shortcuts">
            <p><kbd>ESC</kbd> Odak modundan çık</p>
            <p><kbd>F11</kbd> Tam ekran aç/kapat</p>
          </div>
        </div>
      </div>
    );
  }

  // Active focus mode view
  return (
    <div
      className="focus-mode-active-view"
      role="main"
      aria-label="Odak modu aktif"
    >
      {/* Minimal Header */}
      {!settings.minimal_ui && (
        <div className="focus-header">
          <div className="focus-title">
            <span className="focus-icon">🎯</span>
            <span>Odak Modu</span>
          </div>
          <button
            className="btn-exit"
            onClick={deactivateFocusMode}
            aria-label="Odak modundan çık"
          >
            <span aria-hidden="true">✕</span>
          </button>
        </div>
      )}

      {/* Main Task Display */}
      <div className="focus-task-container">
        {currentTask && (
          <div className="focus-task">
            <h1 className="task-title">{currentTask.title}</h1>

            {currentTask.description && (
              <p className="task-description">{currentTask.description}</p>
            )}

            {currentTask.subject && (
              <div className="task-subject">
                <span className="subject-icon">📚</span>
                <span>{currentTask.subject}</span>
              </div>
            )}

            {/* Timer Display */}
            {settings.show_timer && (
              <div className="focus-timer">
                <div className="timer-display">
                  <span className="timer-icon" aria-hidden="true">⏱️</span>
                  <span className="timer-value" aria-live="polite">
                    {formatTime(elapsedSeconds)}
                  </span>
                </div>
                {currentTask.estimated_duration_minutes && (
                  <div className="timer-estimate">
                    Hedef: {currentTask.estimated_duration_minutes} dakika
                  </div>
                )}
              </div>
            )}

            {/* Progress Bar */}
            {settings.show_progress && currentTask.estimated_duration_minutes && (
              <div className="focus-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${getProgressPercentage()}%`,
                      backgroundColor: getPriorityColor(currentTask.priority || 'medium'),
                    }}
                    role="progressbar"
                    aria-valuenow={getProgressPercentage()}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`İlerleme: yüzde ${getProgressPercentage().toFixed(0)}`}
                  ></div>
                </div>
                <div className="progress-label">
                  {getProgressPercentage().toFixed(0)}% Tamamlandı
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Minimal Exit Button (always visible) */}
      {settings.minimal_ui && (
        <button
          className="btn-exit-minimal"
          onClick={deactivateFocusMode}
          aria-label="Odak modundan çık (ESC)"
          title="Odak modundan çık (ESC)"
        >
          <span aria-hidden="true">✕</span>
        </button>
      )}

      {/* Screen Reader Status */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        Odak modu aktif.
        {currentTask && `Görev: ${currentTask.title}.`}
        Geçen süre: {formatTime(elapsedSeconds)}.
        {currentTask?.estimated_duration_minutes &&
          ` İlerleme: yüzde ${getProgressPercentage().toFixed(0)}.`}
        Çıkmak için ESC tuşuna basın.
      </div>
    </div>
  );
};

export default FocusMode;
