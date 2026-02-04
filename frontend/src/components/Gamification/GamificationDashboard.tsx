/**
 * GamificationDashboard Component - Task 91
 * Tüm oyunlaştırma özelliklerini tek bir dashboard'da gösteren ana component
 */
import React from 'react';
import { useGamificationStats } from '../../hooks/useGamification';
import PointsDisplay from './PointsDisplay';
import LevelDisplay from './LevelDisplay';
import BadgeCollection from './BadgeCollection';
import Leaderboard from './Leaderboard';
import './GamificationDashboard.css';

interface GamificationDashboardProps {
  layout?: 'grid' | 'tabs';
}

export const GamificationDashboard: React.FC<GamificationDashboardProps> = ({
  layout = 'grid'
}) => {
  const { stats, loading, error } = useGamificationStats();
  const [activeTab, setActiveTab] = React.useState<'overview' | 'badges' | 'leaderboard'>('overview');

  if (loading && !stats) {
    return (
      <div className="gamification-dashboard loading">
        <div className="spinner-large"></div>
        <p>Oyunlaştırma verileri yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="gamification-dashboard error">
        <span className="error-icon">⚠️</span>
        <h3>Bir hata oluştu</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (layout === 'tabs') {
    return (
      <div className="gamification-dashboard tabs-layout">
        <div className="dashboard-header">
          <h2>Oyunlaştırma</h2>
          <div className="quick-stats">
            <div className="quick-stat">
              <span className="stat-icon">⭐</span>
              <span className="stat-value">{stats?.points.toLocaleString('tr-TR')}</span>
              <span className="stat-label">Puan</span>
            </div>
            <div className="quick-stat">
              <span className="stat-icon">⚡</span>
              <span className="stat-value">{stats?.level}</span>
              <span className="stat-label">Seviye</span>
            </div>
            <div className="quick-stat">
              <span className="stat-icon">🏅</span>
              <span className="stat-value">{stats?.total_badges}</span>
              <span className="stat-label">Rozet</span>
            </div>
          </div>
        </div>

        <div className="dashboard-tabs">
          <button
            className={`dashboard-tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <span className="tab-icon">📊</span>
            <span className="tab-label">Genel Bakış</span>
          </button>
          <button
            className={`dashboard-tab ${activeTab === 'badges' ? 'active' : ''}`}
            onClick={() => setActiveTab('badges')}
          >
            <span className="tab-icon">🏅</span>
            <span className="tab-label">Rozetler</span>
          </button>
          <button
            className={`dashboard-tab ${activeTab === 'leaderboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('leaderboard')}
          >
            <span className="tab-icon">🏆</span>
            <span className="tab-label">Liderlik Tablosu</span>
          </button>
        </div>

        <div className="dashboard-content">
          {activeTab === 'overview' && (
            <div className="overview-grid">
              <div className="overview-section">
                <PointsDisplay showHistory={true} />
              </div>
              <div className="overview-section">
                <LevelDisplay showMilestones={true} />
              </div>
              {stats && stats.recent_achievements.length > 0 && (
                <div className="overview-section recent-achievements">
                  <h3>Son Başarılar</h3>
                  <div className="achievements-list">
                    {stats.recent_achievements.map((badge) => (
                      <div key={badge.badge_id} className="achievement-item">
                        <span className="achievement-icon">{badge.icon}</span>
                        <div className="achievement-info">
                          <div className="achievement-name">{badge.name}</div>
                          <div className="achievement-date">
                            {badge.earned_at &&
                              new Date(badge.earned_at).toLocaleDateString('tr-TR')}
                          </div>
                        </div>
                        <div className="achievement-points">+{badge.points}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'badges' && <BadgeCollection showProgress={true} />}

          {activeTab === 'leaderboard' && <Leaderboard showNearby={true} limit={50} />}
        </div>
      </div>
    );
  }

  // Grid layout
  return (
    <div className="gamification-dashboard grid-layout">
      <div className="dashboard-header">
        <h2>Oyunlaştırma Dashboard</h2>
        <p className="dashboard-subtitle">
          Başarılarını takip et, rozetler kazan ve liderlik tablosunda yüksel!
        </p>
      </div>

      <div className="dashboard-grid">
        <div className="grid-item points-section">
          <PointsDisplay showHistory={true} />
        </div>

        <div className="grid-item level-section">
          <LevelDisplay showMilestones={true} />
        </div>

        <div className="grid-item badges-section">
          <BadgeCollection showProgress={true} />
        </div>

        <div className="grid-item leaderboard-section">
          <Leaderboard showNearby={true} limit={10} />
        </div>

        {stats && stats.recent_achievements.length > 0 && (
          <div className="grid-item achievements-section">
            <div className="section-card">
              <h3>Son Başarılar 🎉</h3>
              <div className="achievements-grid">
                {stats.recent_achievements.map((badge) => (
                  <div key={badge.badge_id} className="achievement-card">
                    <div className="achievement-icon-large">{badge.icon}</div>
                    <div className="achievement-name">{badge.name}</div>
                    <div className="achievement-rarity">{badge.rarity}</div>
                    <div className="achievement-points">+{badge.points} puan</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {stats && stats.leaderboard_rank && (
          <div className="grid-item rank-section">
            <div className="section-card rank-card">
              <h3>Sıralamanız</h3>
              <div className="rank-display">
                <div className="rank-number">#{stats.leaderboard_rank.rank}</div>
                <div className="rank-info">
                  <div className="rank-percentile">
                    Top {Math.round(100 - stats.leaderboard_rank.percentile)}%
                  </div>
                  <div className="rank-total">
                    {stats.leaderboard_rank.total_users.toLocaleString('tr-TR')} kullanıcı arasında
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GamificationDashboard;
