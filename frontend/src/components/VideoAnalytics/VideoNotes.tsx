/**
 * Task 100.3: Video Notes Component
 *
 * Timestamped note-taking during video playback
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';
import './VideoNotes.css';

export interface VideoNote {
  id: string;
  videoId: string;
  timestamp: number;
  content: string;
  isImportant: boolean;
  tags: string[];
  videoCaption?: string;
  createdAt: string;
  updatedAt: string;
}

export interface VideoNotesProps {
  userId: string;
  videoId: string;
  videoSource: string;
  currentTimestamp?: number;
  onSeekToTimestamp?: (timestamp: number) => void;
}

const API_BASE = '/api/v1/video-analytics';

export const VideoNotes: React.FC<VideoNotesProps> = ({
  userId,
  videoId,
  videoSource,
  currentTimestamp = 0,
  onSeekToTimestamp,
}) => {
  const [notes, setNotes] = useState<VideoNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [newNoteContent, setNewNoteContent] = useState('');
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterImportant, setFilterImportant] = useState(false);

  // Load notes
  useEffect(() => {
    loadNotes();
  }, [userId, videoId, videoSource]);

  const loadNotes = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/notes?user_id=${userId}&video_id=${videoId}&video_source=${videoSource}`,
      );
      const data = await response.json();
      setNotes(data.map((n: any) => ({
        id: n.id,
        videoId: n.video_id,
        timestamp: n.timestamp,
        content: n.content,
        isImportant: n.is_important,
        tags: n.tags,
        videoCaption: n.video_caption,
        createdAt: n.created_at,
        updatedAt: n.updated_at,
      })));
    } catch (error) {
      console.error('Failed to load notes:', error);
    } finally {
      setLoading(false);
    }
  };

  const createNote = async () => {
    if (!newNoteContent.trim()) {return;}

    try {
      const response = await fetch(`${API_BASE}/notes?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: videoId,
          video_source: videoSource,
          content: newNoteContent,
          timestamp: currentTimestamp,
          is_important: false,
          tags: [],
        }),
      });

      if (response.ok) {
        setNewNoteContent('');
        await loadNotes();
      }
    } catch (error) {
      console.error('Failed to create note:', error);
    }
  };

  const updateNote = async (noteId: string) => {
    if (!editContent.trim()) {return;}

    try {
      await fetch(`${API_BASE}/notes/${noteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: editContent }),
      });

      setEditingNoteId(null);
      setEditContent('');
      await loadNotes();
    } catch (error) {
      console.error('Failed to update note:', error);
    }
  };

  const deleteNote = async (noteId: string) => {
    if (!confirm('Bu notu silmek istediğinize emin misiniz?')) {return;}

    try {
      await fetch(`${API_BASE}/notes/${noteId}`, { method: 'DELETE' });
      await loadNotes();
    } catch (error) {
      console.error('Failed to delete note:', error);
    }
  };

  const toggleImportant = async (note: VideoNote) => {
    try {
      await fetch(`${API_BASE}/notes/${note.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_important: !note.isImportant }),
      });
      await loadNotes();
    } catch (error) {
      console.error('Failed to toggle importance:', error);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const filteredNotes = notes.filter(note => {
    if (filterImportant && !note.isImportant) {return false;}
    if (searchQuery && !note.content.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div className="video-notes">
      <div className="notes-header">
        <h3>Notlar ({notes.length})</h3>

        <div className="notes-filters">
          <input
            type="text"
            className="search-input"
            placeholder="Notlarda ara..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search notes"
          />

          <label className="filter-important">
            <input
              type="checkbox"
              checked={filterImportant}
              onChange={(e) => setFilterImportant(e.target.checked)}
            />
            Sadece önemli
          </label>
        </div>
      </div>

      <div className="new-note">
        <div className="timestamp-display">
          {formatTime(currentTimestamp)}
        </div>
        <textarea
          className="note-textarea"
          placeholder="Notunuzu buraya yazın..."
          value={newNoteContent}
          onChange={(e) => setNewNoteContent(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
              createNote();
            }
          }}
          aria-label="New note content"
        />
        <button
          className="btn-primary"
          onClick={createNote}
          disabled={!newNoteContent.trim()}
        >
          Not Ekle
        </button>
        <small className="hint">Ctrl+Enter ile kaydet</small>
      </div>

      <div className="notes-list">
        {loading ? (
          <div className="loading">Notlar yükleniyor...</div>
        ) : filteredNotes.length === 0 ? (
          <div className="empty-state">
            {searchQuery || filterImportant
              ? 'Filtreye uygun not bulunamadı'
              : 'Henüz not eklenmemiş'}
          </div>
        ) : (
          filteredNotes.map((note) => (
            <div
              key={note.id}
              className={`note-item ${note.isImportant ? 'important' : ''}`}
            >
              <div className="note-header">
                <button
                  className="timestamp-btn"
                  onClick={() => onSeekToTimestamp?.(note.timestamp)}
                  title="Bu zamana git"
                >
                  {formatTime(note.timestamp)}
                </button>

                <div className="note-actions">
                  <button
                    className="icon-btn"
                    onClick={() => toggleImportant(note)}
                    title={note.isImportant ? 'Önemsiz işaretle' : 'Önemli işaretle'}
                    aria-label={note.isImportant ? 'Mark as unimportant' : 'Mark as important'}
                  >
                    {note.isImportant ? '⭐' : '☆'}
                  </button>

                  <button
                    className="icon-btn"
                    onClick={() => {
                      setEditingNoteId(note.id);
                      setEditContent(note.content);
                    }}
                    title="Düzenle"
                    aria-label="Edit note"
                  >
                    ✏️
                  </button>

                  <button
                    className="icon-btn"
                    onClick={() => deleteNote(note.id)}
                    title="Sil"
                    aria-label="Delete note"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              {editingNoteId === note.id ? (
                <div className="note-edit">
                  <textarea
                    className="note-textarea"
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    autoFocus
                  />
                  <div className="edit-actions">
                    <button
                      className="btn-primary"
                      onClick={() => updateNote(note.id)}
                    >
                      Kaydet
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => {
                        setEditingNoteId(null);
                        setEditContent('');
                      }}
                    >
                      İptal
                    </button>
                  </div>
                </div>
              ) : (
                <div className="note-content">{note.content}</div>
              )}

              {note.videoCaption && (
                <div className="video-caption">
                  <small>Video: &quot;{note.videoCaption}&quot;</small>
                </div>
              )}

              <div className="note-footer">
                <small>{new Date(note.createdAt).toLocaleDateString('tr-TR')}</small>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default VideoNotes;
