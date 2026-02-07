/**
 * PointsDisplay Component - Task 91
 * Kullanıcı puan gösterimi ve geçmişi
 */
import * as React from 'react';
import {  useState  } from 'react';

import { usePoints } from '../../hooks/useGamification';
import './PointsDisplay.css';

interface PointsDisplayProps {
  showHistory?: boolean;
  compact?: boolean;
}

export const PointsDisplay: React.FC<PointsDisplayProps> = ({
  showHistory = false,
  compact = false,
}) => {
  const { points, loading, error, getHistory } = usePoints();
  const [history, setHistory] = useState<any[]>([]);
  const [historyVisible, setHistoryVisible] = useState(false);

  const handleShowHistory = async () => {
    if (!historyVisible) {
      const data = await getHistory(20);
      setHistory(data);
    }
    setHistoryVisible(!historyVisible);
  };

  if (loading && points === 0) {
    return (
      <div className="points-display loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="points-display error">
        <span className="error-icon">⚠️</span>
        <span className="error-message">Puan yüklenemedi</span>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="points-display compact">
        <span className="points-icon">⭐</span>
        <span className="points-value">{points.toLocaleString('tr-TR')}</span>
      </div>
    );
  }

  return (
    <div className="points-display">
      <div className="points-header">
        <h3>Puanlarım</h3>
        {showHistory && (
          <button
            className="history-toggle"
            onClick={handleShowHistory}
            aria-label="Puan geçmişini göster"
          >
            <span>{historyVisible ? '📊' : '📜'}</span>
            <span>{historyVisible ? 'Geçmişi Gizle' : 'Geçmişi Göster'}</span>
          </button>
        )}
      </div>

      <div className="points-main">
        <div className="points-icon-large">⭐</div>
        <div className="points-info">
          <div className="points-value-large">
            {points.toLocaleString('tr-TR')}
          </div>
          <div className="points-label">Toplam Puan</div>
        </div>
      </div>

      {historyVisible && (
        <div className="points-history">
          <h4>Son İşlemler</h4>
          <div className="history-list">
            {history.length === 0 ? (
              <div className="no-history">Henüz işlem yok</div>
            ) : (
              history.map((transaction, index) => (
                <div key={transaction.id || index} className="history-item">
                  <div className="history-reason">
                    <span className="history-icon">
                      {transaction.points > 0 ? '🎯' : '💸'}
                    </span>
                    <span className="history-text">{transaction.reason}</span>
                  </div>
                  <div className="history-details">
                    <span className={`history-points ${transaction.points > 0 ? 'positive' : 'negative'}`}>
                      {transaction.points > 0 ? '+' : ''}{transaction.points}
                    </span>
                    <span className="history-date">
                      {new Date(transaction.timestamp).toLocaleDateString('tr-TR', {
                        day: 'numeric',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {loading && (
        <div className="points-loading-overlay">
          <div className="spinner-small"></div>
        </div>
      )}
    </div>
  );
};

export default PointsDisplay;
