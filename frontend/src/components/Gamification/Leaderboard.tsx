/**
 * Leaderboard Component - Task 91
 * Liderlik tablosu gösterimi
 */
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { useLeaderboard, LeaderboardEntry } from '../../hooks/useGamification';
import './Leaderboard.css';

interface LeaderboardProps {
  defaultType?: 'global' | 'weekly' | 'monthly';
  showNearby?: boolean;
  limit?: number;
}

const MEDAL_EMOJIS = ['🥇', '🥈', '🥉'];

export const Leaderboard: React.FC<LeaderboardProps> = ({
  defaultType = 'global',
  showNearby = true,
  limit = 100,
}) => {
  const [leaderboardType, setLeaderboardType] = useState<'global' | 'weekly' | 'monthly'>(defaultType);
  const { leaderboard, loading, error, refresh, getNearbyUsers } = useLeaderboard(leaderboardType);
  const [nearbyUsers, setNearbyUsers] = useState<any>(null);
  const [viewMode, setViewMode] = useState<'full' | 'nearby'>('full');

  useEffect(() => {
    if (showNearby && viewMode === 'nearby') {
      loadNearbyUsers();
    }
  }, [viewMode, showNearby]);

  const loadNearbyUsers = async () => {
    const data = await getNearbyUsers(5);
    setNearbyUsers(data);
  };

  if (loading && leaderboard.length === 0) {
    return (
      <div className="leaderboard loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="leaderboard error">
        <span className="error-icon">⚠️</span>
        <span className="error-message">Liderlik tablosu yüklenemedi</span>
      </div>
    );
  }

  const renderLeaderboardEntry = (entry: LeaderboardEntry, index: number, isCurrentUser = false) => {
    const displayRank = entry.rank || index + 1;
    const medal = displayRank <= 3 ? MEDAL_EMOJIS[displayRank - 1] : null;

    return (
      <div
        key={entry.user_id}
        className={`leaderboard-entry ${displayRank <= 3 ? 'top-three' : ''} ${
          isCurrentUser ? 'current-user' : ''
        }`}
      >
        <div className="entry-rank">
          {medal || `#${displayRank}`}
        </div>

        <div className="entry-avatar">
          {entry.avatar_url ? (
            <img src={entry.avatar_url} alt={entry.username} />
          ) : (
            <div className="avatar-placeholder">
              {entry.username.charAt(0).toUpperCase()}
            </div>
          )}
        </div>

        <div className="entry-info">
          <div className="entry-username">
            {entry.username}
            {isCurrentUser && <span className="you-badge">Sen</span>}
          </div>
          {entry.level && (
            <div className="entry-level">Seviye {entry.level}</div>
          )}
        </div>

        <div className="entry-score">
          <div className="score-value">{entry.score.toLocaleString('tr-TR')}</div>
          <div className="score-label">XP</div>
        </div>
      </div>
    );
  };

  return (
    <div className="leaderboard">
      <div className="leaderboard-header">
        <h3>Liderlik Tablosu</h3>
        <button
          className="refresh-btn"
          onClick={() => refresh()}
          disabled={loading}
          aria-label="Yenile"
        >
          🔄
        </button>
      </div>

      <div className="leaderboard-tabs">
        <button
          className={`tab-btn ${leaderboardType === 'global' ? 'active' : ''}`}
          onClick={() => setLeaderboardType('global')}
        >
          <span className="tab-icon">🌍</span>
          <span className="tab-label">Global</span>
        </button>
        <button
          className={`tab-btn ${leaderboardType === 'weekly' ? 'active' : ''}`}
          onClick={() => setLeaderboardType('weekly')}
        >
          <span className="tab-icon">📅</span>
          <span className="tab-label">Haftalık</span>
        </button>
        <button
          className={`tab-btn ${leaderboardType === 'monthly' ? 'active' : ''}`}
          onClick={() => setLeaderboardType('monthly')}
        >
          <span className="tab-icon">📆</span>
          <span className="tab-label">Aylık</span>
        </button>
      </div>

      {showNearby && (
        <div className="view-mode-toggle">
          <button
            className={`toggle-btn ${viewMode === 'full' ? 'active' : ''}`}
            onClick={() => setViewMode('full')}
          >
            Tüm Sıralama
          </button>
          <button
            className={`toggle-btn ${viewMode === 'nearby' ? 'active' : ''}`}
            onClick={() => setViewMode('nearby')}
          >
            Yakınımdakiler
          </button>
        </div>
      )}

      <div className="leaderboard-content">
        {viewMode === 'full' ? (
          <div className="leaderboard-list">
            {leaderboard.slice(0, limit).map((entry, index) =>
              renderLeaderboardEntry(entry, index),
            )}
            {leaderboard.length === 0 && (
              <div className="no-entries">Henüz kayıt yok</div>
            )}
          </div>
        ) : (
          <div className="nearby-section">
            {nearbyUsers ? (
              <>
                {nearbyUsers.above.length > 0 && (
                  <div className="nearby-group">
                    <div className="nearby-label">Üstünüzdekiler</div>
                    {nearbyUsers.above.map((entry: LeaderboardEntry, index: number) =>
                      renderLeaderboardEntry(entry, index),
                    )}
                  </div>
                )}

                {nearbyUsers.user && (
                  <div className="nearby-group current">
                    <div className="nearby-label">Siz</div>
                    {renderLeaderboardEntry(nearbyUsers.user, 0, true)}
                  </div>
                )}

                {nearbyUsers.below.length > 0 && (
                  <div className="nearby-group">
                    <div className="nearby-label">Altınızdakiler</div>
                    {nearbyUsers.below.map((entry: LeaderboardEntry, index: number) =>
                      renderLeaderboardEntry(entry, index),
                    )}
                  </div>
                )}

                {!nearbyUsers.user && nearbyUsers.above.length === 0 && nearbyUsers.below.length === 0 && (
                  <div className="no-entries">Yakınınızda kimse yok</div>
                )}
              </>
            ) : (
              <div className="spinner-small"></div>
            )}
          </div>
        )}
      </div>

      {loading && leaderboard.length > 0 && (
        <div className="loading-overlay">
          <div className="spinner-small"></div>
        </div>
      )}
    </div>
  );
};

export default Leaderboard;
