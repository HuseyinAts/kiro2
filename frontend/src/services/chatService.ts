import {
  sendChatMessage,
  getSession,
  clearSessions,
  createWebSocketConnection,
} from '../api';

// Enhanced chat API endpoints
const ENHANCED_CHAT_API = '/api/enhanced-chat';

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  agent?: string;
  timestamp: string;
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

      return chatMessage;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
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

      const chatMessage: ChatMessage = {
        id: result.data.response_id,
        role: 'agent',
        content: result.data.message,
        agent: 'turkish_nlp',
        timestamp: new Date().toISOString(),
      };

      // Add user message
      this.addMessage({
        id: this.generateMessageId(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      });

      // Add agent response
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

      return text; // Fallback to original text
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