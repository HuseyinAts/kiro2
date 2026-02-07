/**
 * Task 106: AI Chat Assistant Component
 *
 * Enhanced chat interface with image upload, OCR, and step-by-step solutions
 */

import * as React from 'react';
import {  useState, useEffect, useRef  } from 'react';
import './AIChatAssistant.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ============================================================
// Types
// ============================================================

type MessageRole = 'user' | 'assistant' | 'system';
type SessionStatus = 'active' | 'completed' | 'archived';
type SubjectType = 'mathematics' | 'physics' | 'chemistry' | 'biology' | 'turkish' | 'history' | 'geography' | 'english' | 'general';
type ImageProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

interface ChatMessage {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  image_id?: string;
  tokens_used?: number;
  confidence_score?: number;
  user_rating?: number;
  is_helpful?: boolean;
  created_at: string;
}

interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  subject_type: SubjectType;
  status: SessionStatus;
  context: any;
  message_count: number;
  total_tokens: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
}

interface ImageUpload {
  id: string;
  session_id: string;
  file_path: string;
  file_size: number;
  processing_status: ImageProcessingStatus;
  ocr_text?: string;
  ocr_confidence?: number;
  contains_math?: boolean;
  math_latex?: string;
  is_handwritten?: boolean;
  handwriting_quality?: string;
  image_description?: string;
  detected_objects?: any[];
  suggested_subjects?: string[];
}

interface SolutionStep {
  id: string;
  message_id: string;
  step_number: number;
  title: string;
  content: string;
  explanation?: string;
  formula?: string;
  image_url?: string;
}

interface AIChatAssistantProps {
  userId: string;
  initialSubject?: SubjectType;
  showSessionList?: boolean;
}

// ============================================================
// Component
// ============================================================

export const AIChatAssistant: React.FC<AIChatAssistantProps> = ({
  userId,
  initialSubject = 'general',
  showSessionList = true,
}) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Message input
  const [messageInput, setMessageInput] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [uploadedImage, setUploadedImage] = useState<ImageUpload | null>(null);

  // New session form
  const [showNewSessionForm, setShowNewSessionForm] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState('');
  const [newSessionSubject, setNewSessionSubject] = useState<SubjectType>(initialSubject);

  // UI state
  const [isSending, setIsSending] = useState(false);
  const [isProcessingImage, setIsProcessingImage] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSessions();
  }, [userId]);

  useEffect(() => {
    if (currentSession) {
      fetchMessages(currentSession.id);
    }
  }, [currentSession]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/chat/sessions?user_id=${userId}&limit=50`);
      if (!response.ok) {throw new Error('Failed to fetch sessions');}
      const data = await response.json();
      setSessions(data);

      // Auto-select first active session
      if (data.length > 0 && !currentSession) {
        const activeSession = data.find((s: ChatSession) => s.status === 'active') || data[0];
        setCurrentSession(activeSession);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
    }
  };

  const fetchMessages = async (sessionId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}/messages`);
      if (!response.ok) {throw new Error('Failed to fetch messages');}
      const data = await response.json();
      setMessages(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newSessionTitle.trim()) {
      alert('Lütfen oturum başlığı girin');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/chat/sessions?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newSessionTitle,
          subject_type: newSessionSubject,
        }),
      });

      if (!response.ok) {throw new Error('Failed to create session');}
      const newSession = await response.json();

      setSessions([newSession, ...sessions]);
      setCurrentSession(newSession);
      setShowNewSessionForm(false);
      setNewSessionTitle('');
      setNewSessionSubject(initialSubject);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Oturum oluşturulamadı');
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {return;}

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Lütfen geçerli bir resim dosyası seçin');
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      alert('Dosya boyutu 10MB\'dan küçük olmalıdır');
      return;
    }

    setSelectedImage(file);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleImageUpload = async () => {
    if (!selectedImage || !currentSession) {return;}

    setIsProcessingImage(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedImage);

      const response = await fetch(
        `${API_BASE}/api/chat/sessions/${currentSession.id}/upload?user_id=${userId}`,
        {
          method: 'POST',
          body: formData,
        },
      );

      if (!response.ok) {throw new Error('Failed to upload image');}
      const imageData = await response.json();

      setUploadedImage(imageData);

      // Clear selection
      setSelectedImage(null);
      setImagePreview(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Resim yüklenemedi');
    } finally {
      setIsProcessingImage(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!messageInput.trim() && !uploadedImage) {
      return;
    }

    if (!currentSession) {
      alert('Lütfen önce bir oturum oluşturun');
      return;
    }

    setIsSending(true);
    setError(null);

    try {
      const requestBody: any = {
        content: messageInput.trim() || 'Resimde ne görüyorsun?',
      };

      if (uploadedImage) {
        requestBody.image_id = uploadedImage.id;
      }

      const response = await fetch(
        `${API_BASE}/api/chat/sessions/${currentSession.id}/messages?user_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        },
      );

      if (!response.ok) {throw new Error('Failed to send message');}
      const result = await response.json();

      // Add both user message and assistant response
      setMessages([...messages, result.user_message, result.assistant_message]);

      // Clear input and image
      setMessageInput('');
      setUploadedImage(null);

      // Update session
      fetchSessions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Mesaj gönderilemedi');
    } finally {
      setIsSending(false);
    }
  };

  const handleRateMessage = async (messageId: string, rating: number) => {
    if (!currentSession) {return;}

    try {
      const response = await fetch(
        `${API_BASE}/api/chat/messages/${messageId}/rate?user_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rating }),
        },
      );

      if (response.ok) {
        // Update message rating in UI
        setMessages(messages.map(msg =>
          msg.id === messageId ? { ...msg, user_rating: rating } : msg,
        ));
      }
    } catch (err) {
      console.error('Failed to rate message:', err);
    }
  };

  const handleClearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setUploadedImage(null);
  };

  return (
    <div className="ai-chat-assistant">
      {/* Sessions Sidebar */}
      {showSessionList && (
        <div className="sessions-sidebar">
          <div className="sidebar-header">
            <h3>Sohbetler</h3>
            <button
              className="btn-new-session"
              onClick={() => setShowNewSessionForm(!showNewSessionForm)}
            >
              + Yeni
            </button>
          </div>

          {showNewSessionForm && (
            <div className="new-session-form">
              <form onSubmit={handleCreateSession}>
                <input
                  type="text"
                  placeholder="Oturum başlığı"
                  value={newSessionTitle}
                  onChange={(e) => setNewSessionTitle(e.target.value)}
                  required
                />
                <select
                  value={newSessionSubject}
                  onChange={(e) => setNewSessionSubject(e.target.value as SubjectType)}
                >
                  <option value="general">Genel</option>
                  <option value="mathematics">Matematik</option>
                  <option value="physics">Fizik</option>
                  <option value="chemistry">Kimya</option>
                  <option value="biology">Biyoloji</option>
                  <option value="turkish">Türkçe</option>
                  <option value="history">Tarih</option>
                  <option value="geography">Coğrafya</option>
                  <option value="english">İngilizce</option>
                </select>
                <button type="submit" className="btn-create">Oluştur</button>
              </form>
            </div>
          )}

          <div className="sessions-list">
            {sessions.map(session => (
              <div
                key={session.id}
                className={`session-item ${currentSession?.id === session.id ? 'active' : ''}`}
                onClick={() => setCurrentSession(session)}
              >
                <div className="session-title">{session.title}</div>
                <div className="session-meta">
                  <span className="subject-badge">{getSubjectLabel(session.subject_type)}</span>
                  <span className="message-count">{session.message_count} mesaj</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat Area */}
      <div className="chat-area">
        {currentSession ? (
          <>
            {/* Chat Header */}
            <div className="chat-header">
              <div className="session-info">
                <h2>{currentSession.title}</h2>
                <div className="session-stats">
                  <span className="subject-badge">{getSubjectLabel(currentSession.subject_type)}</span>
                  <span className="token-count">{currentSession.total_tokens} token</span>
                  {currentSession.total_cost > 0 && (
                    <span className="cost">₺{currentSession.total_cost.toFixed(4)}</span>
                  )}
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="messages-container">
              {loading && <div className="loading">Mesajlar yükleniyor...</div>}

              {messages.map(message => (
                <div key={message.id} className={`message ${message.role}`}>
                  <div className="message-content">
                    {message.content}

                    {message.confidence_score && (
                      <div className="confidence-badge">
                        Güven: {(message.confidence_score * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>

                  {message.role === 'assistant' && (
                    <div className="message-actions">
                      <div className="rating-stars">
                        {[1, 2, 3, 4, 5].map(rating => (
                          <span
                            key={rating}
                            className={`star ${message.user_rating && rating <= message.user_rating ? 'filled' : ''}`}
                            onClick={() => handleRateMessage(message.id, rating)}
                          >
                            ⭐
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="message-time">
                    {formatMessageTime(message.created_at)}
                  </div>
                </div>
              ))}

              {error && <div className="error-message">{error}</div>}

              <div ref={messagesEndRef} />
            </div>

            {/* Image Upload Area */}
            {(selectedImage || uploadedImage) && (
              <div className="image-upload-area">
                {imagePreview && (
                  <div className="image-preview">
                    <img src={imagePreview} alt="Preview" />
                    <button className="btn-clear-image" onClick={handleClearImage}>
                      ✕
                    </button>
                    {!isProcessingImage && (
                      <button className="btn-upload-image" onClick={handleImageUpload}>
                        📤 Yükle ve İşle
                      </button>
                    )}
                  </div>
                )}

                {isProcessingImage && (
                  <div className="processing-indicator">
                    🔄 Resim işleniyor (OCR, el yazısı tanıma, formül çıkarma)...
                  </div>
                )}

                {uploadedImage && uploadedImage.processing_status === 'completed' && (
                  <div className="ocr-results">
                    <h4>📝 OCR Sonuçları</h4>

                    {uploadedImage.ocr_text && (
                      <div className="ocr-text">
                        <strong>Çıkarılan Metin:</strong>
                        <p>{uploadedImage.ocr_text}</p>
                        {uploadedImage.ocr_confidence && (
                          <span className="confidence">
                            Güven: {(uploadedImage.ocr_confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                    )}

                    {uploadedImage.is_handwritten && (
                      <div className="handwriting-info">
                        ✍️ El yazısı tespit edildi ({uploadedImage.handwriting_quality})
                      </div>
                    )}

                    {uploadedImage.contains_math && uploadedImage.math_latex && (
                      <div className="math-formula">
                        <strong>🔢 Matematik Formülü (LaTeX):</strong>
                        <code>{uploadedImage.math_latex}</code>
                      </div>
                    )}

                    {uploadedImage.suggested_subjects && uploadedImage.suggested_subjects.length > 0 && (
                      <div className="suggested-subjects">
                        <strong>📚 Önerilen Konular:</strong>
                        {uploadedImage.suggested_subjects.map(subject => (
                          <span key={subject} className="subject-tag">{subject}</span>
                        ))}
                      </div>
                    )}

                    <button className="btn-clear-image" onClick={handleClearImage}>
                      🗑️ Temizle
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Input Area */}
            <div className="input-area">
              <form onSubmit={handleSendMessage} className="message-form">
                <label htmlFor="image-input" className="btn-attach">
                  📎
                  <input
                    id="image-input"
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    style={{ display: 'none' }}
                  />
                </label>

                <input
                  type="text"
                  className="message-input"
                  placeholder="Sorunuzu yazın veya resim yükleyin..."
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  disabled={isSending}
                />

                <button
                  type="submit"
                  className="btn-send"
                  disabled={isSending || (!messageInput.trim() && !uploadedImage)}
                >
                  {isSending ? '📤...' : '📤 Gönder'}
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="no-session">
            <h2>Sohbet Başlatın</h2>
            <p>Sol taraftan bir oturum seçin veya yeni bir oturum oluşturun</p>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================
// Utility Functions
// ============================================================

function getSubjectLabel(subject: SubjectType): string {
  const labels: Record<SubjectType, string> = {
    general: 'Genel',
    mathematics: 'Matematik',
    physics: 'Fizik',
    chemistry: 'Kimya',
    biology: 'Biyoloji',
    turkish: 'Türkçe',
    history: 'Tarih',
    geography: 'Coğrafya',
    english: 'İngilizce',
  };
  return labels[subject] || subject;
}

function formatMessageTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));

  if (diffMins < 1) {return 'Şimdi';}
  if (diffMins < 60) {return `${diffMins} dk önce`;}
  if (diffMins < 1440) {return `${Math.floor(diffMins / 60)} saat önce`;}

  return date.toLocaleDateString('tr-TR', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export type {
  AIChatAssistantProps,
  ChatMessage,
  ChatSession,
  ImageUpload,
  SolutionStep,
  MessageRole,
  SessionStatus,
  SubjectType,
  ImageProcessingStatus,
};
