/**
 * BadgeCollection Component - Task 91
 * Rozet koleksiyonu ve ilerleme gösterimi
 */
import React, { useState, useMemo } from 'react';
import { useBadges, Badge, BadgeProgress } from '../../hooks/useGamification';
import './BadgeCollection.css';

interface BadgeCollectionProps {
  showProgress?: boolean;
  filterByCategory?: string;
  compact?: boolean;
}

const RARITY_COLORS = {
  common: '#94a3b8',
  uncommon: '#22c55e',
  rare: '#3b82f6',
  epic: '#a855f7',
  legendary: '#f59e0b'
};

const CATEGORY_ICONS: Record<string, string> = {
  achievement: '🎯',
  milestone: '🏆',
  streak: '🔥',
  mastery: '⭐',
  special: '💎',
  seasonal: '🎃'
};

export const BadgeCollection: React.FC<BadgeCollectionProps> = ({
  showProgress = true,
  filterByCategory,
  compact = false
}) => {
  const { allBadges, earnedBadges, badgeProgress, loading, error } = useBadges();
  const [selectedBadge, setSelectedBadge] = useState<Badge | BadgeProgress | null>(null);
  const [filterRarity, setFilterRarity] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'earned' | 'all' | 'progress'>('earned');

  const filteredBadges = useMemo(() => {
    let badges: (Badge | BadgeProgress)[] = [];

    if (viewMode === 'earned') {
      badges = earnedBadges;
    } else if (viewMode === 'all') {
      badges = allBadges;
    } else {
      badges = badgeProgress;
    }

    if (filterByCategory) {
      badges = badges.filter(b => b.category === filterByCategory);
    }

    if (filterRarity !== 'all') {
      badges = badges.filter(b => b.rarity === filterRarity);
    }

    return badges;
  }, [viewMode, earnedBadges, allBadges, badgeProgress, filterByCategory, filterRarity]);

  const stats = useMemo(() => {
    const byRarity: Record<string, number> = {};
    earnedBadges.forEach(badge => {
      byRarity[badge.rarity] = (byRarity[badge.rarity] || 0) + 1;
    });

    return {
      total: earnedBadges.length,
      available: allBadges.length,
      byRarity
    };
  }, [earnedBadges, allBadges]);

  if (loading && earnedBadges.length === 0) {
    return (
      <div className="badge-collection loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="badge-collection error">
        <span className="error-icon">⚠️</span>
        <span className="error-message">Rozetler yüklenemedi</span>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="badge-collection compact">
        <span className="badge-count-icon">🏅</span>
        <span className="badge-count">{stats.total}/{stats.available}</span>
      </div>
    );
  }

  return (
    <div className="badge-collection">
      <div className="badge-header">
        <h3>Rozet Koleksiyonu</h3>
        <div className="badge-stats-compact">
          <span className="stat-badge">
            <span className="stat-icon">🏅</span>
            <span className="stat-value">{stats.total}/{stats.available}</span>
          </span>
        </div>
      </div>

      <div className="badge-filters">
        <div className="view-mode-buttons">
          <button
            className={`view-mode-btn ${viewMode === 'earned' ? 'active' : ''}`}
            onClick={() => setViewMode('earned')}
          >
            Kazanılanlar ({earnedBadges.length})
          </button>
          <button
            className={`view-mode-btn ${viewMode === 'all' ? 'active' : ''}`}
            onClick={() => setViewMode('all')}
          >
            Tümü ({allBadges.length})
          </button>
          {showProgress && (
            <button
              className={`view-mode-btn ${viewMode === 'progress' ? 'active' : ''}`}
              onClick={() => setViewMode('progress')}
            >
              İlerleme ({badgeProgress.length})
            </button>
          )}
        </div>

        <div className="rarity-filter">
          <select
            value={filterRarity}
            onChange={(e) => setFilterRarity(e.target.value)}
            className="rarity-select"
          >
            <option value="all">Tüm Nadirlikler</option>
            <option value="common">Yaygın</option>
            <option value="uncommon">Nadir</option>
            <option value="rare">Çok Nadir</option>
            <option value="epic">Epik</option>
            <option value="legendary">Efsanevi</option>
          </select>
        </div>
      </div>

      <div className="badge-grid">
        {filteredBadges.length === 0 ? (
          <div className="no-badges">
            {viewMode === 'earned' ? 'Henüz rozet kazanmadınız' : 'Rozet bulunamadı'}
          </div>
        ) : (
          filteredBadges.map((badge) => (
            <div
              key={badge.badge_id}
              className={`badge-card ${badge.rarity} ${
                'earned_at' in badge ? 'earned' : ''
              }`}
              onClick={() => setSelectedBadge(badge)}
              style={{ borderColor: RARITY_COLORS[badge.rarity] }}
            >
              <div className="badge-icon">{badge.icon}</div>
              <div className="badge-name">{badge.name}</div>
              <div className="badge-category">
                {CATEGORY_ICONS[badge.category] || '📌'} {badge.category}
              </div>
              <div className="badge-points">+{badge.points} puan</div>

              {viewMode === 'progress' && 'progress_percentage' in badge && (
                <div className="badge-progress-bar">
                  <div
                    className="badge-progress-fill"
                    style={{
                      width: `${badge.progress_percentage}%`,
                      background: RARITY_COLORS[badge.rarity]
                    }}
                  ></div>
                  <span className="badge-progress-text">
                    {Math.round(badge.progress_percentage)}%
                  </span>
                </div>
              )}

              {/* 'earned_at' in badge && badge.earned_at && (
                <div className="badge-earned-date">
                  {new Date(badge.earned_at).toLocaleDateString('tr-TR')}
                </div>
              ) */}
            </div>
          ))
        )}
      </div>

      {selectedBadge && (
        <div className="badge-modal-overlay" onClick={() => setSelectedBadge(null)}>
          <div className="badge-modal" onClick={(e) => e.stopPropagation()}>
            <button
              className="modal-close"
              onClick={() => setSelectedBadge(null)}
              aria-label="Kapat"
            >
              ✕
            </button>

            <div
              className="modal-badge-icon"
              style={{ color: RARITY_COLORS[selectedBadge.rarity] }}
            >
              {selectedBadge.icon}
            </div>

            <h2 className="modal-badge-name">{selectedBadge.name}</h2>

            <div
              className="modal-rarity-badge"
              style={{ background: RARITY_COLORS[selectedBadge.rarity] }}
            >
              {selectedBadge.rarity.toUpperCase()}
            </div>

            <p className="modal-badge-description">{selectedBadge.description}</p>

            <div className="modal-badge-info">
              <div className="modal-info-item">
                <span className="modal-info-label">Kategori:</span>
                <span className="modal-info-value">
                  {CATEGORY_ICONS[selectedBadge.category] || '📌'} {selectedBadge.category}
                </span>
              </div>
              <div className="modal-info-item">
                <span className="modal-info-label">Puan:</span>
                <span className="modal-info-value">+{selectedBadge.points}</span>
              </div>
              {'earned_at' in selectedBadge && selectedBadge.earned_at && (
                <div className="modal-info-item">
                  <span className="modal-info-label">Kazanma Tarihi:</span>
                  <span className="modal-info-value">
                    {new Date(selectedBadge.earned_at).toLocaleDateString('tr-TR', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </span>
                </div>
              )}
            </div>

            {viewMode === 'progress' && 'progress_percentage' in selectedBadge && (
              <div className="modal-progress">
                <h3>İlerleme</h3>
                <div className="modal-progress-bar">
                  <div
                    className="modal-progress-fill"
                    style={{
                      width: `${selectedBadge.progress_percentage}%`,
                      background: RARITY_COLORS[selectedBadge.rarity]
                    }}
                  ></div>
                </div>
                <div className="modal-progress-text">
                  {Math.round(selectedBadge.progress_percentage)}% tamamlandı
                </div>

                {selectedBadge.criteria && (
                  <div className="modal-criteria">
                    <h4>Kriterler</h4>
                    <ul>
                      {Object.entries(selectedBadge.criteria).map(([key, value]) => (
                        <li key={key}>
                          {key}: {value}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BadgeCollection;
