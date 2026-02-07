/**
 * Task Progress Visualization Component
 *
 * Görsel ilerleme göstergesi - DEHB desteği için görev ilerlemesini görselleştirir
 *
 * Requirements: REQ-52.46 - REQ-52.50
 * - REQ-52.46: Progress bar gösterimi
 * - REQ-52.47: Tamamlanma yüzdesi
 * - REQ-52.48: Görsel milestone göstergeleri
 * - REQ-52.49: Renk kodlu ilerleme
 * - REQ-52.50: Animasyonlu geçişler
 *
 * Task: 90.2 Görsel ilerleme göstergesi
 */

import * as React from 'react';
import {  useEffect, useState  } from 'react';
import './TaskProgressVisualization.css';

interface Milestone {
  percentage: number;
  label: string;
  reached: boolean;
  icon: string;
  color: string;
}

interface ProgressVisualizationData {
  task_id: string;
  title: string;
  progress_percentage: number;
  completed_subtasks: number;
  total_subtasks: number;
  estimated_minutes?: number;
  actual_minutes?: number;
  time_remaining_minutes?: number;
  milestones: Milestone[];
  color: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'blocked';
}

interface TaskProgressVisualizationProps {
  taskId: string;
  onRefresh?: () => void;
}

export const TaskProgressVisualization: React.FC<TaskProgressVisualizationProps> = ({
  taskId,
  onRefresh,
}) => {
  const [progressData, setProgressData] = useState<ProgressVisualizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    fetchProgressData();
  }, [taskId]);

  // Animate progress bar
  useEffect(() => {
    if (progressData) {
      const timer = setTimeout(() => {
        setAnimatedProgress(progressData.progress_percentage);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [progressData]);

  const fetchProgressData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/adhd-task-management/tasks/${taskId}/progress`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('İlerleme verileri yüklenemedi');
      }

      const data = await response.json();
      setProgressData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const getStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
      'not_started': 'Başlanmadı',
      'in_progress': 'Devam Ediyor',
      'completed': 'Tamamlandı',
      'blocked': 'Engellenmiş',
    };
    return statusMap[status] || status;
  };

  const getStatusColor = (status: string): string => {
    const colorMap: Record<string, string> = {
      'not_started': '#9E9E9E',
      'in_progress': '#2196F3',
      'completed': '#4CAF50',
      'blocked': '#F44336',
    };
    return colorMap[status] || '#9E9E9E';
  };

  const getStatusIcon = (status: string): string => {
    const iconMap: Record<string, string> = {
      'not_started': '⏸️',
      'in_progress': '▶️',
      'completed': '✅',
      'blocked': '🚫',
    };
    return iconMap[status] || '❓';
  };

  const formatTime = (minutes?: number): string => {
    if (!minutes) {return '-';}
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours} saat ${mins} dakika`;
    }
    return `${mins} dakika`;
  };

  if (loading) {
    return (
      <div className="task-progress-loading">
        <div
          className="spinner"
          role="status"
          aria-label="İlerleme yükleniyor"
        ></div>
        <p>İlerleme yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="task-progress-error" role="alert">
        <p className="error-message">
          <span role="img" aria-label="Hata">❌</span> {error}
        </p>
        <button
          onClick={fetchProgressData}
          className="retry-button"
          aria-label="İlerleme verilerini tekrar yükle"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  if (!progressData) {
    return null;
  }

  return (
    <div className="task-progress-visualization">
      {/* Live region for screen readers - WCAG 4.1.3 */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {`Görev ilerleme yüzdesi: ${Math.round(progressData.progress_percentage)}%`}
      </div>

      {/* Header */}
      <div className="progress-header">
        <h2 className="task-title">{progressData.title}</h2>
        <div
          className="status-badge"
          style={{ backgroundColor: getStatusColor(progressData.status) }}
          role="status"
          aria-label={`Görev durumu: ${getStatusText(progressData.status)}`}
        >
          <span className="status-icon" aria-hidden="true">
            {getStatusIcon(progressData.status)}
          </span>
          {getStatusText(progressData.status)}
        </div>
      </div>

      {/* Main Progress Bar - REQ-52.46 */}
      <div className="progress-section">
        <div className="progress-info">
          <span className="progress-label">Genel İlerleme</span>
          <span
            className="progress-percentage"
            style={{ color: progressData.color }}
          >
            {Math.round(progressData.progress_percentage)}%
          </span>
        </div>

        <div className="progress-bar-container">
          <div
            className="progress-bar-fill"
            style={{
              width: `${animatedProgress}%`,
              backgroundColor: progressData.color,
            }}
            role="progressbar"
            aria-valuenow={progressData.progress_percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Görev ilerleme yüzdesi: ${Math.round(progressData.progress_percentage)}%`}
          >
            <div className="progress-bar-shine"></div>
          </div>
        </div>
      </div>

      {/* Subtasks Progress - REQ-52.47 */}
      <div className="subtasks-section">
        <div className="subtasks-info">
          <span
            className="subtasks-icon"
            role="img"
            aria-label="Tamamlandı işareti"
          >
            ✓
          </span>
          <span className="subtasks-text">
            <strong>{progressData.completed_subtasks}</strong> / {progressData.total_subtasks} alt görev tamamlandı
          </span>
        </div>
      </div>

      {/* Milestones - REQ-52.48 */}
      <div className="milestones-section">
        <h3 className="milestones-title">Kilometre Taşları</h3>
        <div className="milestones-container" role="list">
          {progressData.milestones.map((milestone, index) => (
            <div
              key={index}
              className={`milestone ${milestone.reached ? 'reached' : 'unreached'}`}
              style={{
                borderColor: milestone.reached ? milestone.color : '#E0E0E0',
              }}
              role="listitem"
            >
              <div
                className="milestone-icon"
                style={{
                  backgroundColor: milestone.reached ? milestone.color : '#F5F5F5',
                  color: milestone.reached ? '#FFFFFF' : '#9E9E9E',
                }}
                role="img"
                aria-label={`${milestone.label} kilometre taşı ${milestone.reached ? 'tamamlandı' : 'henüz ulaşılmadı'}`}
              >
                {milestone.icon}
              </div>
              <div className="milestone-info">
                <span className="milestone-percentage">{milestone.percentage}%</span>
                <span className="milestone-label">{milestone.label}</span>
              </div>
              {milestone.reached && (
                <div
                  className="milestone-checkmark"
                  role="img"
                  aria-label="Tamamlandı"
                >
                  ✓
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Time Tracking */}
      {progressData.estimated_minutes && (
        <div className="time-section">
          <h3 className="time-title">Zaman Takibi</h3>
          <div className="time-grid">
            <div className="time-item">
              <span className="time-label">Tahmini Süre</span>
              <span className="time-value">{formatTime(progressData.estimated_minutes)}</span>
            </div>
            <div className="time-item">
              <span className="time-label">Geçen Süre</span>
              <span className="time-value">{formatTime(progressData.actual_minutes)}</span>
            </div>
            {progressData.time_remaining_minutes !== undefined && (
              <div className="time-item">
                <span className="time-label">Kalan Süre</span>
                <span className="time-value time-remaining">
                  {formatTime(progressData.time_remaining_minutes)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="progress-actions">
        <button
          onClick={fetchProgressData}
          className="refresh-button"
          aria-label="İlerlemeyi yenile"
        >
          🔄 Yenile
        </button>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="custom-action-button"
          >
            Görevi Görüntüle
          </button>
        )}
      </div>
    </div>
  );
};

export default TaskProgressVisualization;
