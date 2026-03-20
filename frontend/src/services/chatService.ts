import {
  sendChatMessage,
  getSession,
  clearSessions,
  createWebSocketConnection,
} from '../api';

// Enhanced chat API endpoints
const ENHANCED_CHAT_API = '/api/v1/enhanced-chat';
const STREAM_ENDPOINT = '/api/v1/enhanced-chat/stream';
const SESSIONS_ENDPOINT = '/api/v1/enhanced-chat/sessions';
const ATTACHMENT_ENDPOINT = '/api/v1/enhanced-chat/message-with-attachment';

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  agent?: string;
  timestamp: string;
}

export interface ChatSessionInfo {
  id: string;
  title: string;
  subject: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  createdAt: string;
  lastActivity: string;
}

class ChatService {
  private sessionId: string | null = null;
  private messages: ChatMessage[] = [];
  private wsConnection: any = null;
  private messageListeners: Set<(message: ChatMessage) => void> = new Set();
  private connectionListeners: Set<(status: boolean) => void> = new Set();

  getSessionId(): string | null {
    return this.sessionId;
  }

  setSessionId(id: string | null) {
    this.sessionId = id;
    if (id) {
      localStorage.setItem('chatSessionId', id);
    } else {
      localStorage.removeItem('chatSessionId');
    }
  }

  initSession() {
    if (!this.sessionId) {
      this.sessionId = this.generateSessionId();
      localStorage.setItem('chatSessionId', this.sessionId);
    }
    return this.sessionId;
  }

  async sendMessage(agent: string, message: string): Promise<ChatMessage> {
    const sessionId = this.initSession();

    try {
      const response = await sendChatMessage(agent, message, sessionId);

      const chatMessage: ChatMessage = {
        id: this.generateMessageId(),
        role: 'agent',
        content: response.response,
        agent: response.agent,
        timestamp: response.timestamp,
      };

      this.addMessage({
        id: this.generateMessageId(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      });

      this.addMessage(chatMessage);

      // Update session_id if backend returned one
      if (response.session_id) {
        this.setSessionId(response.session_id);
      }

      return chatMessage;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  /**
   * Send message with SSE streaming — tokens arrive in real-time.
   */
  async sendMessageStreaming(
    message: string,
    onToken: (accumulated: string) => void,
    options?: { subject?: string; teachingMode?: string },
  ): Promise<ChatMessage> {
    this.initSession();

    let accumulated = '';

    const response = await fetch(STREAM_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        student_id: 'current',
        message,
        session_id: this.sessionId,
        subject: options?.subject || '',
        teaching_mode: options?.teachingMode || 'direct',
      }),
    });

    if (!response.ok) {
      throw new Error(`Stream error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6).trim();
        if (payload === '[DONE]') break;
        try {
          const parsed = JSON.parse(payload);
          // Capture session_id from first SSE event (backend sends it)
          if (parsed.session_id && !parsed.content) {
            this.setSessionId(parsed.session_id);
            continue;
          }
          if (parsed.content) {
            accumulated += parsed.content;
            onToken(accumulated);
          }
        } catch {
          // skip malformed SSE line
        }
      }
    }

    const chatMessage: ChatMessage = {
      id: this.generateMessageId(),
      role: 'agent',
      content: accumulated,
      agent: 'turkish_nlp',
      timestamp: new Date().toISOString(),
    };

    // Don't re-add to local state — handleSubmit manages state directly
    // Just persist to localStorage as backup
    this.addMessage({
      id: this.generateMessageId(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    });
    this.addMessage(chatMessage);

    return chatMessage;
  }

  /**
   * Send message with file or URL attachment.
   */
  async sendMessageWithAttachment(
    options: {
      file?: File;
      url?: string;
      message?: string;
      subject?: string;
      teachingMode?: string;
    },
  ): Promise<{ message: string; attachmentType: string; sessionId?: string }> {
    this.initSession();

    const formData = new FormData();
    if (options.file) formData.append('file', options.file);
    if (options.url) formData.append('url', options.url);
    formData.append('message', options.message || '');
    formData.append('subject', options.subject || '');
    formData.append('session_id', this.sessionId || '');
    formData.append('teaching_mode', options.teachingMode || 'direct');

    const response = await fetch(ATTACHMENT_ENDPOINT, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Attachment error: ${response.status}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.error || 'Dosya isleme hatasi');
    }

    if (result.session_id) {
      this.setSessionId(result.session_id);
    }

    return {
      message: result.data.message,
      attachmentType: result.data.attachment_type,
      sessionId: result.session_id,
    };
  }

  /**
   * List user's chat sessions from DB.
   */
  async listSessions(): Promise<ChatSessionInfo[]> {
    try {
      const response = await fetch(SESSIONS_ENDPOINT, {
        credentials: 'include',
      });
      if (!response.ok) return [];
      const result = await response.json();
      return result.sessions || [];
    } catch {
      return [];
    }
  }

  /**
   * Load a session's messages from DB.
   */
  async loadSessionFromDB(sessionId: string): Promise<ChatMessage[]> {
    try {
      const response = await fetch(`${SESSIONS_ENDPOINT}/${sessionId}/messages`, {
        credentials: 'include',
      });
      if (!response.ok) return [];
      const result = await response.json();
      const messages: ChatMessage[] = (result.messages || []).map((msg: any) => ({
        id: msg.id || this.generateMessageId(),
        role: msg.role,
        content: msg.content,
        agent: msg.agent,
        timestamp: msg.timestamp,
      }));
      this.sessionId = sessionId;
      this.messages = messages;
      localStorage.setItem('chatSessionId', sessionId);
      this.saveMessagesToLocalStorage();
      return messages;
    } catch (error) {
      console.error('loadSessionFromDB error:', error);
      return [];
    }
  }

  /**
   * Start a new chat session (clear current state).
   */
  startNewSession() {
    this.sessionId = null;
    this.messages = [];
    localStorage.removeItem('chatSessionId');
    localStorage.removeItem('chatMessages');
  }

  async sendEnhancedMessage(
    studentId: string,
    message: string,
    options: {
      subject?: string;
      sessionId?: string;
      responseMode?: 'simple' | 'detailed' | 'adaptive';
      includeBionic?: boolean;
      contextData?: Record<string, any>;
    } = {},
  ): Promise<ChatMessage> {
    try {
      const response = await fetch(`${ENHANCED_CHAT_API}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_id: studentId,
          message: message,
          subject: options.subject || 'genel',
          session_id: options.sessionId || this.sessionId,
          response_mode: options.responseMode || 'adaptive',
          include_bionic: options.includeBionic || false,
          context_data: options.contextData,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || 'Enhanced chat request failed');
      }

      // Update session_id from backend
      if (result.session_id || result.data?.session_id) {
        this.setSessionId(result.session_id || result.data.session_id);
      }

      const chatMessage: ChatMessage = {
        id: result.data.response_id,
        role: 'agent',
        content: result.data.message,
        agent: 'turkish_nlp',
        timestamp: new Date().toISOString(),
      };

      this.addMessage({
        id: this.generateMessageId(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      });

      this.addMessage(chatMessage);

      return chatMessage;
    } catch (error) {
      console.error('Enhanced chat error:', error);
      throw error;
    }
  }

  async getChatHistory(studentId: string, sessionId?: string, limit: number = 20): Promise<ChatMessage[]> {
    try {
      const params = new URLSearchParams({
        student_id: studentId,
        limit: limit.toString(),
      });

      if (sessionId) {
        params.append('session_id', sessionId);
      }

      const response = await fetch(`${ENHANCED_CHAT_API}/history?${params}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        return result.data.history.map((msg: any) => ({
          id: msg.id || this.generateMessageId(),
          role: msg.role,
          content: msg.content,
          agent: msg.agent,
          timestamp: msg.timestamp,
        }));
      }

      return [];
    } catch (error) {
      console.error('Get chat history error:', error);
      return [];
    }
  }

  async applyBionicReading(text: string): Promise<string> {
    try {
      const response = await fetch(`${ENHANCED_CHAT_API}/bionic-reading`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        return result.data.bionic_text;
      }

      return text;
    } catch (error) {
      console.error('Bionic reading error:', error);
      return text;
    }
  }

  async loadSession(sessionId?: string) {
    const id = sessionId || this.sessionId;
    if (!id) {
      throw new Error('No session ID provided');
    }

    try {
      const session = await getSession(id);
      this.messages = session.messages.map((msg: any, index: number) => ({
        id: `msg-${index}`,
        role: msg.role,
        content: msg.content,
        agent: msg.agent,
        timestamp: msg.timestamp,
      }));
      return this.messages;
    } catch (error) {
      console.error('Error loading session:', error);
      throw error;
    }
  }

  async clearAllSessions() {
    try {
      await clearSessions();
      this.messages = [];
      this.sessionId = null;
      localStorage.removeItem('chatSessionId');
      return true;
    } catch (error) {
      console.error('Error clearing sessions:', error);
      throw error;
    }
  }

  connectWebSocket() {
    if (this.wsConnection) {
      console.warn('WebSocket already connected');
      return;
    }

    this.wsConnection = createWebSocketConnection({
      onMessage: (data) => this.handleWebSocketMessage(data),
      onError: (error) => this.handleWebSocketError(error),
    });

    if (this.wsConnection) {
      this.notifyConnectionListeners(true);
    }
  }

  disconnectWebSocket() {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
      this.notifyConnectionListeners(false);
    }
  }

  sendWebSocketMessage(agent: string, message: string) {
    if (!this.wsConnection) {
      console.error('WebSocket not connected');
      throw new Error('WebSocket connection not established');
    }

    this.wsConnection.send({
      agent,
      message,
      session_id: this.initSession(),
    });

    this.addMessage({
      id: this.generateMessageId(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    });
  }

  private handleWebSocketMessage(data: any) {
    if (data.type === 'response') {
      const message: ChatMessage = {
        id: this.generateMessageId(),
        role: 'agent',
        content: data.content,
        agent: data.agent,
        timestamp: data.timestamp,
      };

      this.addMessage(message);
      this.notifyMessageListeners(message);
    } else if (data.type === 'error') {
      console.error('WebSocket error message:', data.content);
    }
  }

  private handleWebSocketError(error: any) {
    console.error('WebSocket connection error:', error);
    this.notifyConnectionListeners(false);
  }

  onMessage(listener: (message: ChatMessage) => void) {
    this.messageListeners.add(listener);
    return () => this.messageListeners.delete(listener);
  }

  onConnectionChange(listener: (status: boolean) => void) {
    this.connectionListeners.add(listener);
    return () => this.connectionListeners.delete(listener);
  }

  private notifyMessageListeners(message: ChatMessage) {
    this.messageListeners.forEach(listener => listener(message));
  }

  private notifyConnectionListeners(status: boolean) {
    this.connectionListeners.forEach(listener => listener(status));
  }

  private addMessage(message: ChatMessage) {
    this.messages.push(message);
    this.saveMessagesToLocalStorage();
  }

  private saveMessagesToLocalStorage() {
    localStorage.setItem('chatMessages', JSON.stringify(this.messages));
  }

  loadMessagesFromLocalStorage() {
    const stored = localStorage.getItem('chatMessages');
    if (stored) {
      try {
        this.messages = JSON.parse(stored);
      } catch (error) {
        console.error('Error loading messages from localStorage:', error);
      }
    }

    const sessionId = localStorage.getItem('chatSessionId');
    if (sessionId) {
      this.sessionId = sessionId;
    }

    return this.messages;
  }

  getMessages(): ChatMessage[] {
    return this.messages;
  }

  clearMessages() {
    this.messages = [];
    localStorage.removeItem('chatMessages');
  }

  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateMessageId(): string {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  isWebSocketConnected(): boolean {
    return this.wsConnection !== null;
  }
}

export default new ChatService();
