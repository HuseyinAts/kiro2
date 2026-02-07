/**
 * Dashboard Component with Error Handling
 * Production-ready örnek: Error handling + Retry logic + User feedback
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { getDashboardStats, getExamHistory } from '@/api';
import config from '@/config';
import { useErrorHandler, AppError, ErrorType } from '@/utils/errorHandler';

interface DashboardData {
  stats: any;
  examHistory: any[];
}

export const DashboardWithErrorHandling: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<AppError | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const { handleError, getUserMessage, isRecoverable } = useErrorHandler();

  const loadDashboard = async (isRetry = false) => {
    if (!isRetry) {
      setLoading(true);
    }
    setError(null);

    try {
      // Parallel API calls
      const [stats, examHistory] = await Promise.all([
        getDashboardStats(),
        getExamHistory(10),
      ]);

      setData({ stats, examHistory });
      setRetryCount(0); // Reset retry count on success

      // Log success (only in production)
      if (config.isProduction && config.features.analytics) {
        console.log('Dashboard loaded successfully');
      }
    } catch (err) {
      const appError = handleError(err, 'loadDashboard');
      setError(appError);

      // Auto-retry for network errors
      if (isRecoverable(appError) && retryCount < 3) {
        const delay = Math.pow(2, retryCount) * 1000; // Exponential backoff
        console.log(`Retrying in ${delay}ms... (Attempt ${retryCount + 1}/3)`);

        setTimeout(() => {
          setRetryCount((prev) => prev + 1);
          loadDashboard(true);
        }, delay);
      }
    } finally {
      if (!isRetry) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // Render loading state
  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner" />
        <p>Dashboard yükleniyor...</p>
        {config.isDevelopment && <p className="debug">API URL: {config.api.baseURL}</p>}
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className={`dashboard-error error-${error.type}`}>
        <div className="error-icon">⚠️</div>
        <h3>Dashboard Yüklenemedi</h3>
        <p className="error-message">{getUserMessage(error)}</p>

        {/* Error-specific actions */}
        {error.type === ErrorType.NETWORK && (
          <div className="error-actions">
            <p className="hint">İnternet bağlantınızı kontrol edin</p>
            <button onClick={() => loadDashboard()}>Tekrar Dene</button>
          </div>
        )}

        {error.type === ErrorType.AUTH && (
          <div className="error-actions">
            <p className="hint">Oturumunuz sona ermiş olabilir</p>
            <button onClick={() => (window.location.href = '/login')}>
              Tekrar Giriş Yap
            </button>
          </div>
        )}

        {error.type === ErrorType.SERVER && (
          <div className="error-actions">
            <p className="hint">Sunucu geçici olarak kullanılamıyor</p>
            <button onClick={() => loadDashboard()}>Tekrar Dene</button>
          </div>
        )}

        {/* Show retry status */}
        {isRecoverable(error) && retryCount > 0 && (
          <p className="retry-status">
            Otomatik yeniden deneme: {retryCount}/3
          </p>
        )}

        {/* Debug info (development only) */}
        {config.isDevelopment && error.details && (
          <details className="error-details">
            <summary>Teknik Detaylar (Development)</summary>
            <pre>{JSON.stringify(error.details, null, 2)}</pre>
            <p>Status: {error.status}</p>
            <p>Timestamp: {error.timestamp?.toISOString()}</p>
          </details>
        )}
      </div>
    );
  }

  // Render success state
  return (
    <div className="dashboard-success">
      <h2>Dashboard</h2>

      {/* Stats Section */}
      <div className="stats-section">
        <h3>İstatistikler</h3>
        {data?.stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Toplam Sınav</span>
              <span className="stat-value">{data.stats.total_exams || 0}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Ortalama Puan</span>
              <span className="stat-value">{data.stats.average_score || 0}</span>
            </div>
          </div>
        )}
      </div>

      {/* Exam History Section */}
      <div className="exam-history-section">
        <h3>Sınav Geçmişi</h3>
        {data?.examHistory && data.examHistory.length > 0 ? (
          <ul className="exam-list">
            {data.examHistory.map((exam, index) => (
              <li key={exam.id || index} className="exam-item">
                <span>{exam.exam_type}</span>
                <span>{exam.score}</span>
                <span>{new Date(exam.date).toLocaleDateString('tr-TR')}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="no-data">Henüz sınav kaydı yok</p>
        )}
      </div>

      {/* Refresh Button */}
      <button onClick={() => loadDashboard()} className="refresh-button">
        Yenile
      </button>

      {/* Environment Badge (development only) */}
      {config.isDevelopment && (
        <div className="dev-badge">
          <span>Environment: {config.app.env}</span>
          <span>API: {config.api.baseURL}</span>
          <span>Test Mode: {config.isTest ? 'Yes' : 'No'}</span>
        </div>
      )}
    </div>
  );
};

export default DashboardWithErrorHandling;
