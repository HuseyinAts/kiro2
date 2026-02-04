/**
 * Task 97.3: EBA Video Browser Component
 * Browse and filter EBA videos by subject, grade level, topic
 */

import React, { useState, useEffect } from 'react';
import './EBAVideoBrowser.css';

export interface EBAVideo {
  video_id: string;
  title: string;
  description?: string;
  duration_seconds: number;
  thumbnail_url?: string;
  subject: string;
  grade_level: string;
  topic?: string;
  quality: string;
  view_count: number;
}

export interface EBAVideoBrowserProps {
  apiBaseUrl?: string;
  onVideoSelect?: (video: EBAVideo) => void;
}

export const EBAVideoBrowser: React.FC<EBAVideoBrowserProps> = ({
  apiBaseUrl = '/api/v1/eba',
  onVideoSelect
}) => {
  // State
  const [videos, setVideos] = useState<EBAVideo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [selectedGrade, setSelectedGrade] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(1);

  // Taxonomy
  const [taxonomy, setTaxonomy] = useState<Record<string, string[]>>({});

  // Fetch taxonomy on mount
  useEffect(() => {
    fetchTaxonomy();
  }, []);

  // Fetch videos when filters change
  useEffect(() => {
    fetchVideos();
  }, [selectedSubject, selectedGrade, searchQuery, page]);

  const fetchTaxonomy = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/taxonomy/subjects`);
      if (!response.ok) throw new Error('Failed to fetch taxonomy');

      const data = await response.json();
      setTaxonomy(data);
    } catch (err) {
      console.error('[EBA BROWSER] Failed to fetch taxonomy:', err);
    }
  };

  const fetchVideos = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();

      if (selectedSubject) params.append('subject', selectedSubject);
      if (selectedGrade) params.append('grade_level', selectedGrade);
      if (searchQuery) params.append('search', searchQuery);
      params.append('page', page.toString());
      params.append('page_size', '20');

      const response = await fetch(`${apiBaseUrl}/videos?${params}`);

      if (!response.ok) throw new Error('Failed to fetch videos');

      const data = await response.json();
      setVideos(data);

    } catch (err) {
      console.error('[EBA BROWSER] Failed to fetch videos:', err);
      setError('Videolar yüklenemedi. Lütfen tekrar deneyin.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatSubject = (subject: string): string => {
    const subjectNames: Record<string, string> = {
      'matematik': 'Matematik',
      'fizik': 'Fizik',
      'kimya': 'Kimya',
      'biyoloji': 'Biyoloji',
      'turkce': 'Türkçe',
      'tarih': 'Tarih',
      'cografya': 'Coğrafya'
    };
    return subjectNames[subject] || subject;
  };

  const formatGradeLevel = (grade: string): string => {
    const gradeNames: Record<string, string> = {
      'ortaokul_5': '5. Sınıf',
      'ortaokul_6': '6. Sınıf',
      'ortaokul_7': '7. Sınıf',
      'ortaokul_8': '8. Sınıf',
      'lise_9': '9. Sınıf',
      'lise_10': '10. Sınıf',
      'lise_11': '11. Sınıf',
      'lise_12': '12. Sınıf'
    };
    return gradeNames[grade] || grade;
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchVideos();
  };

  const handleReset = () => {
    setSelectedSubject('');
    setSelectedGrade('');
    setSearchQuery('');
    setPage(1);
  };

  return (
    <div className="eba-video-browser">
      <div className="browser-header">
        <h1 className="browser-title">
          <img src="/eba-logo.png" alt="EBA" className="eba-logo-header" />
          EBA TV Eğitim Videoları
        </h1>
        <p className="browser-subtitle">
          MEB onaylı binlerce eğitim videosu
        </p>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <form onSubmit={handleSearch} className="filters-form">
          <div className="filter-group">
            <label htmlFor="subject-filter">Ders</label>
            <select
              id="subject-filter"
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="filter-select"
            >
              <option value="">Tüm Dersler</option>
              <option value="matematik">Matematik</option>
              <option value="fizik">Fizik</option>
              <option value="kimya">Kimya</option>
              <option value="biyoloji">Biyoloji</option>
              <option value="turkce">Türkçe</option>
              <option value="tarih">Tarih</option>
              <option value="cografya">Coğrafya</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="grade-filter">Sınıf Seviyesi</label>
            <select
              id="grade-filter"
              value={selectedGrade}
              onChange={(e) => setSelectedGrade(e.target.value)}
              className="filter-select"
            >
              <option value="">Tüm Seviyeler</option>
              <optgroup label="Ortaokul">
                <option value="ortaokul_5">5. Sınıf</option>
                <option value="ortaokul_6">6. Sınıf</option>
                <option value="ortaokul_7">7. Sınıf</option>
                <option value="ortaokul_8">8. Sınıf</option>
              </optgroup>
              <optgroup label="Lise">
                <option value="lise_9">9. Sınıf</option>
                <option value="lise_10">10. Sınıf</option>
                <option value="lise_11">11. Sınıf</option>
                <option value="lise_12">12. Sınıf</option>
              </optgroup>
            </select>
          </div>

          <div className="filter-group search-group">
            <label htmlFor="search-input">Ara</label>
            <div className="search-input-wrapper">
              <input
                id="search-input"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Video ara..."
                className="search-input"
              />
              <button type="submit" className="search-button">
                🔍
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={handleReset}
            className="reset-button"
          >
            Filtreleri Temizle
          </button>
        </form>
      </div>

      {/* Video Grid */}
      {isLoading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Videolar yükleniyor...</p>
        </div>
      ) : error ? (
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button onClick={fetchVideos}>Tekrar Dene</button>
        </div>
      ) : videos.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📹</div>
          <p>Video bulunamadı.</p>
          <p className="empty-subtitle">Farklı filtreler deneyin.</p>
        </div>
      ) : (
        <>
          <div className="results-header">
            <p className="results-count">
              {videos.length} video bulundu
            </p>
          </div>

          <div className="video-grid">
            {videos.map((video) => (
              <div
                key={video.video_id}
                className="video-card"
                onClick={() => onVideoSelect?.(video)}
                role="button"
                tabIndex={0}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') onVideoSelect?.(video);
                }}
              >
                <div className="video-thumbnail">
                  {video.thumbnail_url ? (
                    <img src={video.thumbnail_url} alt={video.title} />
                  ) : (
                    <div className="thumbnail-placeholder">
                      <span className="play-icon">▶</span>
                    </div>
                  )}
                  <div className="duration-badge">
                    {formatDuration(video.duration_seconds)}
                  </div>
                  <div className="quality-badge">{video.quality}</div>
                </div>

                <div className="video-info-card">
                  <h3 className="video-title-card">{video.title}</h3>

                  <div className="video-meta-card">
                    <span className="subject-badge">
                      {formatSubject(video.subject)}
                    </span>
                    <span className="grade-badge">
                      {formatGradeLevel(video.grade_level)}
                    </span>
                  </div>

                  {video.topic && (
                    <p className="video-topic">{video.topic}</p>
                  )}

                  <div className="video-stats">
                    <span className="view-count">
                      👁️ {video.view_count.toLocaleString()} izlenme
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="pagination-button"
            >
              ← Önceki
            </button>

            <span className="page-number">Sayfa {page}</span>

            <button
              onClick={() => setPage(page + 1)}
              disabled={videos.length < 20}
              className="pagination-button"
            >
              Sonraki →
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default EBAVideoBrowser;
