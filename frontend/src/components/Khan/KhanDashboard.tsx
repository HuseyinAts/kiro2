/**
 * Task 98: Khan Academy Dashboard Component
 * OAuth connection, content browsing, progress tracking, badges
 */

import React, { useState, useEffect } from 'react';
import './KhanDashboard.css';

export interface KhanContent {
  content_id: string;
  title: string;
  description?: string;
  content_type: string;
  subject: string;
  duration_seconds?: number;
  thumbnail_url?: string;
  difficulty_level?: string;
}

export interface KhanProgress {
  content_id: string;
  content_title: string;
  energy_points: int;
  proficiency_level?: string;
  video_completed: boolean;
}

export interface KhanBadge {
  badge_id: string;
  badge_name: string;
  badge_category: string;
  icon_url?: string;
  earned_at: string;
}

export interface KhanDashboardProps {
  apiBaseUrl?: string;
}

export const KhanDashboard: React.FC<KhanDashboardProps> = ({
  apiBaseUrl = '/api/v1/khan'
}) => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [contents, setContents] = useState<KhanContent[]>([]);
  const [progress, setProgress] = useState<KhanProgress[]>([]);
  const [badges, setBadges] = useState<KhanBadge[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'content' | 'progress' | 'badges'>('content');

  useEffect(() => {
    checkConnectionStatus();
  }, []);

  useEffect(() => {
    if (isConnected && activeTab === 'content') {
      fetchContent();
    } else if (isConnected && activeTab === 'progress') {
      fetchProgress();
      fetchAnalytics();
    } else if (isConnected && activeTab === 'badges') {
      fetchBadges();
    }
  }, [isConnected, activeTab]);

  const checkConnectionStatus = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/oauth/status`);
      const data = await response.json();
      setIsConnected(data.connected);
    } catch (err) {
      console.error('Failed to check OAuth status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const redirectUri = `${window.location.origin}/khan/callback`;
      const response = await fetch(`${apiBaseUrl}/oauth/connect?redirect_uri=${encodeURIComponent(redirectUri)}`);
      const data = await response.json();

      // Redirect to Khan Academy OAuth
      window.location.href = data.authorization_url;
    } catch (err) {
      console.error('Failed to initiate OAuth:', err);
      alert('Khan Academy bağlantısı başarısız oldu');
    }
  };

  const fetchContent = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/content?page=1&page_size=20`);
      const data = await response.json();
      setContents(data);
    } catch (err) {
      console.error('Failed to fetch content:', err);
    }
  };

  const fetchProgress = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/progress`);
      const data = await response.json();
      setProgress(data);
    } catch (err) {
      console.error('Failed to fetch progress:', err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/progress/analytics`);
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  };

  const fetchBadges = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/badges`);
      const data = await response.json();
      setBadges(data);
    } catch (err) {
      console.error('Failed to fetch badges:', err);
    }
  };

  const handleSyncProgress = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/progress/sync`, { method: 'POST' });
      const data = await response.json();
      alert(data.message);
      fetchProgress();
      fetchAnalytics();
    } catch (err) {
      console.error('Failed to sync progress:', err);
      alert('Senkronizasyon başarısız');
    }
  };

  const handleSyncBadges = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/badges/sync`, { method: 'POST' });
      const data = await response.json();
      alert(data.message);
      fetchBadges();
    } catch (err) {
      console.error('Failed to sync badges:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="khan-dashboard loading">
        <div className="spinner"></div>
        <p>Yükleniyor...</p>
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="khan-dashboard not-connected">
        <div className="connect-card">
          <img src="/khan-academy-logo.png" alt="Khan Academy" className="khan-logo" />
          <h2>Khan Academy ile Bağlan</h2>
          <p>Khan Academy hesabınızı bağlayarak binlerce Türkçe eğitim içeriğine erişin</p>
          <ul className="benefits-list">
            <li>✅ Türkçe matematik, fen, bilgisayar bilimleri videoları</li>
            <li>✅ İnteraktif alıştırmalar ve projeler</li>
            <li>✅ İlerleme takibi ve senkronizasyon</li>
            <li>✅ Rozetler ve başarı sertifikaları</li>
          </ul>
          <button onClick={handleConnect} className="connect-button">
            Khan Academy ile Bağlan
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="khan-dashboard connected">
      <div className="dashboard-header">
        <h1>Khan Academy</h1>
        <div className="connection-status">
          <span className="status-indicator connected"></span>
          <span>Bağlı</span>
        </div>
      </div>

      {/* Analytics Summary */}
      {analytics && (
        <div className="analytics-summary">
          <div className="stat-card">
            <div className="stat-value">{analytics.total_energy_points}</div>
            <div className="stat-label">Enerji Puanı</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{analytics.completed_videos}</div>
            <div className="stat-label">Tamamlanan Video</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{analytics.mastered_exercises}</div>
            <div className="stat-label">Ustalaşılan Alıştırma</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{analytics.total_content_accessed}</div>
            <div className="stat-label">Toplam İçerik</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'content' ? 'active' : ''}`}
          onClick={() => setActiveTab('content')}
        >
          İçerikler
        </button>
        <button
          className={`tab ${activeTab === 'progress' ? 'active' : ''}`}
          onClick={() => setActiveTab('progress')}
        >
          İlerleme
        </button>
        <button
          className={`tab ${activeTab === 'badges' ? 'active' : ''}`}
          onClick={() => setActiveTab('badges')}
        >
          Rozetler
        </button>
      </div>

      {/* Content Tab */}
      {activeTab === 'content' && (
        <div className="content-grid">
          {contents.map((content) => (
            <div key={content.content_id} className="content-card">
              {content.thumbnail_url && (
                <img src={content.thumbnail_url} alt={content.title} className="content-thumbnail" />
              )}
              <div className="content-info">
                <h3>{content.title}</h3>
                <div className="content-meta">
                  <span className="badge">{content.subject}</span>
                  <span className="badge">{content.content_type}</span>
                  {content.difficulty_level && (
                    <span className="badge">{content.difficulty_level}</span>
                  )}
                </div>
                {content.description && (
                  <p className="content-description">{content.description}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Progress Tab */}
      {activeTab === 'progress' && (
        <div className="progress-section">
          <div className="section-header">
            <h2>İlerleme Durumu</h2>
            <button onClick={handleSyncProgress} className="sync-button">
              Senkronize Et
            </button>
          </div>
          <div className="progress-list">
            {progress.map((item) => (
              <div key={item.content_id} className="progress-card">
                <h3>{item.content_title}</h3>
                <div className="progress-stats">
                  <span>Enerji Puanı: {item.energy_points}</span>
                  {item.proficiency_level && (
                    <span className={`proficiency ${item.proficiency_level}`}>
                      {item.proficiency_level}
                    </span>
                  )}
                  {item.video_completed && (
                    <span className="completed">✓ Tamamlandı</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Badges Tab */}
      {activeTab === 'badges' && (
        <div className="badges-section">
          <div className="section-header">
            <h2>Kazanılan Rozetler</h2>
            <button onClick={handleSyncBadges} className="sync-button">
              Senkronize Et
            </button>
          </div>
          <div className="badges-grid">
            {badges.map((badge) => (
              <div key={badge.badge_id} className="badge-card">
                {badge.icon_url && (
                  <img src={badge.icon_url} alt={badge.badge_name} className="badge-icon" />
                )}
                <h3>{badge.badge_name}</h3>
                <span className="badge-category">{badge.badge_category}</span>
                <span className="badge-date">
                  {new Date(badge.earned_at).toLocaleDateString('tr-TR')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default KhanDashboard;
