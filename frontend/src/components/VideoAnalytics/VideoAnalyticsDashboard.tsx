/**
 * Task 100: Video Analytics Dashboard
 *
 * Comprehensive analytics dashboard showing watch time,
 * completion rates, engagement metrics, and trends
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';
import './VideoAnalyticsDashboard.css';

export interface AnalyticsSummary {
  userId: string;
  periodType: 'daily' | 'weekly' | 'monthly';
  periodStart: string;
  periodEnd: string;
  totalVideosWatched: number;
  totalWatchTime: number;
  totalVideosCompleted: number;
  averageCompletionRate: number;
  totalNotes: number;
  totalBookmarks: number;
  averagePlaybackSpeed: number;
  sourceBreakdown: Record<string, number>;
  subjectBreakdown: Record<string, number>;
}

export interface VideoAnalyticsDashboardProps {
  userId: string;
}

const API_BASE = '/api/v1/video-analytics';

export const VideoAnalyticsDashboard: React.FC<VideoAnalyticsDashboardProps> = ({
  userId,
}) => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0],
  );

  useEffect(() => {
    loadSummary();
  }, [userId, selectedDate]);

  const loadSummary = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/summary/daily?user_id=${userId}&date=${selectedDate}`,
      );
      const data = await response.json();
      setSummary({
        userId: data.user_id,
        periodType: data.period_type,
        periodStart: data.period_start,
        periodEnd: data.period_end,
        totalVideosWatched: data.total_videos_watched,
        totalWatchTime: data.total_watch_time,
        totalVideosCompleted: data.total_videos_completed,
        averageCompletionRate: data.average_completion_rate,
        totalNotes: data.total_notes,
        totalBookmarks: data.total_bookmarks,
        averagePlaybackSpeed: data.average_playback_speed,
        sourceBreakdown: data.source_breakdown,
        subjectBreakdown: data.subject_breakdown,
      });
    } catch (error) {
      console.error('Failed to load summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);

    if (hours > 0) {
      return `${hours}s ${mins}dk`;
    }
    return `${mins}dk`;
  };

  const getCompletionColor = (rate: number): string => {
    if (rate >= 80) {return '#10b981';}
    if (rate >= 60) {return '#f59e0b';}
    return '#ef4444';
  };

  return (
    <div className="video-analytics-dashboard">
      <div className="dashboard-header">
        <h2>Video İzleme Analitikleri</h2>

        <div className="date-selector">
          <label htmlFor="analytics-date">Tarih:</label>
          <input
            id="analytics-date"
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            max={new Date().toISOString().split('T')[0]}
            aria-label="Select date for analytics"
          />
        </div>
      </div>

      {loading ? (
        <div className="loading-state">Analitikler yükleniyor...</div>
      ) : !summary || summary.totalVideosWatched === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <p>Bu tarih için video izleme verisi bulunamadı</p>
        </div>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">📹</div>
              <div className="stat-content">
                <div className="stat-value">{summary.totalVideosWatched}</div>
                <div className="stat-label">İzlenen Video</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-content">
                <div className="stat-value">
                  {formatDuration(summary.totalWatchTime)}
                </div>
                <div className="stat-label">Toplam İzleme Süresi</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">✅</div>
              <div className="stat-content">
                <div className="stat-value">{summary.totalVideosCompleted}</div>
                <div className="stat-label">Tamamlanan Video</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">📈</div>
              <div className="stat-content">
                <div
                  className="stat-value"
                  style={{ color: getCompletionColor(summary.averageCompletionRate) }}
                >
                  {summary.averageCompletionRate.toFixed(1)}%
                </div>
                <div className="stat-label">Ortalama Tamamlama</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">📝</div>
              <div className="stat-content">
                <div className="stat-value">{summary.totalNotes}</div>
                <div className="stat-label">Not Alındı</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">🔖</div>
              <div className="stat-content">
                <div className="stat-value">{summary.totalBookmarks}</div>
                <div className="stat-label">Yer İmi Eklendi</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">⚡</div>
              <div className="stat-content">
                <div className="stat-value">
                  {summary.averagePlaybackSpeed.toFixed(2)}x
                </div>
                <div className="stat-label">Ortalama Hız</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">🎯</div>
              <div className="stat-content">
                <div className="stat-value">
                  {summary.totalVideosCompleted > 0
                    ? ((summary.totalVideosCompleted / summary.totalVideosWatched) * 100).toFixed(0)
                    : 0}%
                </div>
                <div className="stat-label">Tamamlama Oranı</div>
              </div>
            </div>
          </div>

          {/* Source Breakdown */}
          {Object.keys(summary.sourceBreakdown).length > 0 && (
            <div className="breakdown-section">
              <h3>Kaynak Dağılımı</h3>
              <div className="breakdown-grid">
                {Object.entries(summary.sourceBreakdown).map(([source, count]) => (
                  <div key={source} className="breakdown-item">
                    <div className="breakdown-label">
                      {getSourceName(source)}
                    </div>
                    <div className="breakdown-bar">
                      <div
                        className="breakdown-bar-fill"
                        style={{
                          width: `${(count / summary.totalVideosWatched) * 100}%`,
                          background: getSourceColor(source),
                        }}
                      />
                    </div>
                    <div className="breakdown-value">{count} video</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Subject Breakdown */}
          {Object.keys(summary.subjectBreakdown).length > 0 && (
            <div className="breakdown-section">
              <h3>Ders Dağılımı</h3>
              <div className="breakdown-grid">
                {Object.entries(summary.subjectBreakdown).map(([subject, count]) => (
                  <div key={subject} className="breakdown-item">
                    <div className="breakdown-label">{subject}</div>
                    <div className="breakdown-bar">
                      <div
                        className="breakdown-bar-fill"
                        style={{
                          width: `${(count / summary.totalVideosWatched) * 100}%`,
                        }}
                      />
                    </div>
                    <div className="breakdown-value">{count} video</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Insights */}
          <div className="insights-section">
            <h3>İçgörüler</h3>
            <div className="insights-grid">
              {summary.averageCompletionRate >= 80 && (
                <div className="insight-card success">
                  <div className="insight-icon">🎉</div>
                  <div className="insight-text">
                    Harika! Videoları %{summary.averageCompletionRate.toFixed(0)} oranında
                    tamamlıyorsunuz.
                  </div>
                </div>
              )}

              {summary.averagePlaybackSpeed > 1.5 && (
                <div className="insight-card info">
                  <div className="insight-icon">⚡</div>
                  <div className="insight-text">
                    Videoları {summary.averagePlaybackSpeed.toFixed(2)}x hızda izliyorsunuz.
                    Hızlı öğrenen!
                  </div>
                </div>
              )}

              {summary.totalNotes > 10 && (
                <div className="insight-card success">
                  <div className="insight-icon">📝</div>
                  <div className="insight-text">
                    {summary.totalNotes} not aldınız. Aktif öğrenme!
                  </div>
                </div>
              )}

              {summary.totalVideosCompleted === 0 && summary.totalVideosWatched > 0 && (
                <div className="insight-card warning">
                  <div className="insight-icon">⚠️</div>
                  <div className="insight-text">
                    Bugün hiç video tamamlamadınız. Videoları sonuna kadar izlemeyi deneyin!
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Helper functions
function getSourceName(source: string): string {
  const names: Record<string, string> = {
    youtube: 'YouTube',
    eba: 'EBA TV',
    khan: 'Khan Academy',
    vimeo: 'Vimeo',
  };
  return names[source] || source;
}

function getSourceColor(source: string): string {
  const colors: Record<string, string> = {
    youtube: '#ff0000',
    eba: '#10b981',
    khan: '#14b8a6',
    vimeo: '#06b6d4',
  };
  return colors[source] || '#6b7280';
}

export default VideoAnalyticsDashboard;
