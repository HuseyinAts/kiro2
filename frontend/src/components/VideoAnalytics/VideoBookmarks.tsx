/**
 * Task 100.4: Video Bookmarks Component
 *
 * Bookmark key moments in videos for quick navigation
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';
import './VideoBookmarks.css';

export interface VideoBookmark {
  id: string;
  userId: string;
  videoId: string;
  timestamp: number;
  title: string;
  description?: string;
  bookmarkType: 'manual' | 'key_moment' | 'auto_generated';
  isPublic: boolean;
  shareCount: number;
  createdAt: string;
}

export interface VideoBookmarksProps {
  userId: string;
  videoId: string;
  videoSource: string;
  currentTimestamp?: number;
  onSeekToTimestamp?: (timestamp: number) => void;
  includePublic?: boolean;
}

const API_BASE = '/api/v1/video-analytics';

export const VideoBookmarks: React.FC<VideoBookmarksProps> = ({
  userId,
  videoId,
  videoSource,
  currentTimestamp = 0,
  onSeekToTimestamp,
  includePublic = false,
}) => {
  const [bookmarks, setBookmarks] = useState<VideoBookmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newIsPublic, setNewIsPublic] = useState(false);

  useEffect(() => {
    loadBookmarks();
  }, [userId, videoId, videoSource, includePublic]);

  const loadBookmarks = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/bookmarks?user_id=${userId}&video_id=${videoId}&video_source=${videoSource}&include_public=${includePublic}`,
      );
      const data = await response.json();
      setBookmarks(data.map((b: any) => ({
        id: b.id,
        userId: b.user_id,
        videoId: b.video_id,
        timestamp: b.timestamp,
        title: b.title,
        description: b.description,
        bookmarkType: b.bookmark_type,
        isPublic: b.is_public,
        shareCount: b.share_count,
        createdAt: b.created_at,
      })));
    } catch (error) {
      console.error('Failed to load bookmarks:', error);
    } finally {
      setLoading(false);
    }
  };

  const createBookmark = async () => {
    if (!newTitle.trim()) {return;}

    try {
      await fetch(`${API_BASE}/bookmarks?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: videoId,
          video_source: videoSource,
          timestamp: currentTimestamp,
          title: newTitle,
          description: newDescription || null,
          bookmark_type: 'manual',
          is_public: newIsPublic,
        }),
      });

      setNewTitle('');
      setNewDescription('');
      setNewIsPublic(false);
      setShowAddModal(false);
      await loadBookmarks();
    } catch (error) {
      console.error('Failed to create bookmark:', error);
    }
  };

  const deleteBookmark = async (bookmarkId: string) => {
    if (!confirm('Bu yer imini silmek istediğinize emin misiniz?')) {return;}

    try {
      await fetch(`${API_BASE}/bookmarks/${bookmarkId}`, { method: 'DELETE' });
      await loadBookmarks();
    } catch (error) {
      console.error('Failed to delete bookmark:', error);
    }
  };

  const shareBookmark = async (bookmarkId: string) => {
    try {
      await fetch(`${API_BASE}/bookmarks/${bookmarkId}/share`, {
        method: 'POST',
      });
      await loadBookmarks();
    } catch (error) {
      console.error('Failed to share bookmark:', error);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getBookmarkIcon = (type: string): string => {
    switch (type) {
      case 'key_moment':
        return '⭐';
      case 'auto_generated':
        return '🤖';
      default:
        return '🔖';
    }
  };

  return (
    <div className="video-bookmarks">
      <div className="bookmarks-header">
        <h3>Yer İmleri ({bookmarks.length})</h3>
        <button
          className="btn-add-bookmark"
          onClick={() => setShowAddModal(true)}
        >
          + Yer İmi Ekle
        </button>
      </div>

      {showAddModal && (
        <div className="bookmark-modal">
          <div className="modal-content">
            <h4>Yeni Yer İmi</h4>
            <div className="timestamp-info">
              Zaman: {formatTime(currentTimestamp)}
            </div>

            <input
              type="text"
              className="input-title"
              placeholder="Başlık (zorunlu)"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              autoFocus
              aria-label="Bookmark title"
            />

            <textarea
              className="input-description"
              placeholder="Açıklama (opsiyonel)"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              aria-label="Bookmark description"
            />

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={newIsPublic}
                onChange={(e) => setNewIsPublic(e.target.checked)}
              />
              Herkese açık (diğer kullanıcılar görebilir)
            </label>

            <div className="modal-actions">
              <button
                className="btn-primary"
                onClick={createBookmark}
                disabled={!newTitle.trim()}
              >
                Kaydet
              </button>
              <button
                className="btn-secondary"
                onClick={() => {
                  setShowAddModal(false);
                  setNewTitle('');
                  setNewDescription('');
                  setNewIsPublic(false);
                }}
              >
                İptal
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="bookmarks-list">
        {loading ? (
          <div className="loading">Yer imleri yükleniyor...</div>
        ) : bookmarks.length === 0 ? (
          <div className="empty-state">Henüz yer imi eklenmemiş</div>
        ) : (
          bookmarks.map((bookmark) => {
            const isOwnBookmark = bookmark.userId === userId;
            return (
              <div
                key={bookmark.id}
                className={`bookmark-item ${bookmark.bookmarkType}`}
              >
                <div className="bookmark-header">
                  <span className="bookmark-icon">
                    {getBookmarkIcon(bookmark.bookmarkType)}
                  </span>

                  <button
                    className="bookmark-timestamp"
                    onClick={() => onSeekToTimestamp?.(bookmark.timestamp)}
                    title="Bu zamana git"
                  >
                    {formatTime(bookmark.timestamp)}
                  </button>

                  {bookmark.isPublic && (
                    <span className="public-badge" title="Herkese açık">
                      🌐
                    </span>
                  )}

                  {!isOwnBookmark && (
                    <span className="shared-badge" title="Paylaşılan">
                      👤
                    </span>
                  )}
                </div>

                <div className="bookmark-title">{bookmark.title}</div>

                {bookmark.description && (
                  <div className="bookmark-description">
                    {bookmark.description}
                  </div>
                )}

                <div className="bookmark-footer">
                  <small>
                    {new Date(bookmark.createdAt).toLocaleDateString('tr-TR')}
                  </small>

                  {bookmark.shareCount > 0 && (
                    <small className="share-count">
                      {bookmark.shareCount} paylaşım
                    </small>
                  )}

                  {isOwnBookmark && (
                    <div className="bookmark-actions">
                      <button
                        className="action-btn"
                        onClick={() => shareBookmark(bookmark.id)}
                        title="Paylaş"
                      >
                        📤
                      </button>
                      <button
                        className="action-btn"
                        onClick={() => deleteBookmark(bookmark.id)}
                        title="Sil"
                      >
                        🗑️
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default VideoBookmarks;
