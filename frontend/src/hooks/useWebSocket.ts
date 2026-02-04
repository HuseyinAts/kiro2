import { useState, useEffect, useRef, useCallback } from 'react';
import { ChatMessage } from '../services/chatService';
import config from '../config';

interface WebSocketMessage {
  type: 'message' | 'response' | 'error' | 'status' | 'typing';
  agent?: string;
  content?: string;
  data?: any;
  timestamp?: string;
  session_id?: string;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  sendMessage: (agent: string, message: string) => void;
  lastMessage: ChatMessage | null;
  error: string | null;
  reconnect: () => void;
}

export const useWebSocket = (
  studentId: string,
  sessionId?: string
): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<ChatMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3 seconds

  // Get WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    // Use config for WebSocket URL
    const baseUrl = config.api.wsURL;

    return `${baseUrl}/ws/chat/${studentId}${sessionId ? `?session_id=${sessionId}` : ''}`;
  }, [studentId, sessionId]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnectionStatus('connecting');
    setError(null);

    try {
      const wsUrl = getWebSocketUrl();
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket bağlantısı kuruldu');
        setIsConnected(true);
        setConnectionStatus('connected');
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Send initial connection message
        ws.send(JSON.stringify({
          type: 'connect',
          student_id: studentId,
          session_id: sessionId,
          timestamp: new Date().toISOString()
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          
          switch (data.type) {
            case 'response':
              if (data.content && data.agent) {
                const message: ChatMessage = {
                  id: `ws-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                  role: 'agent',
                  content: data.content,
                  agent: data.agent,
                  timestamp: data.timestamp || new Date().toISOString()
                };
                setLastMessage(message);
              }
              break;
              
            case 'error':
              console.error('WebSocket hatası:', data.content);
              setError(data.content || 'Bilinmeyen hata');
              break;
              
            case 'status':
              console.log('WebSocket durum:', data.data);
              break;
              
            case 'typing':
              // Handle typing indicator
              console.log('Agent yazıyor...');
              break;
              
            default:
              console.log('Bilinmeyen WebSocket mesajı:', data);
          }
        } catch (error) {
          console.error('WebSocket mesajı parse edilemedi:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket bağlantısı kapandı:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Auto-reconnect if not intentionally closed
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Yeniden bağlanma denemesi ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay * reconnectAttemptsRef.current);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket hatası:', error);
        setConnectionStatus('error');
        setError('Bağlantı hatası oluştu');
      };

    } catch (error) {
      console.error('WebSocket bağlantısı kurulamadı:', error);
      setConnectionStatus('error');
      setError('Bağlantı kurulamadı');
    }
  }, [getWebSocketUrl, studentId, sessionId]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
    reconnectAttemptsRef.current = 0;
  }, []);

  // Send message via WebSocket
  const sendMessage = useCallback((agent: string, message: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket bağlantısı yok');
      setError('Bağlantı yok');
      return;
    }

    try {
      const messageData = {
        type: 'message',
        agent,
        message,
        student_id: studentId,
        session_id: sessionId,
        timestamp: new Date().toISOString()
      };

      wsRef.current.send(JSON.stringify(messageData));
      setError(null);
    } catch (error) {
      console.error('Mesaj gönderilemedi:', error);
      setError('Mesaj gönderilemedi');
    }
  }, [studentId, sessionId]);

  // Reconnect function
  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      reconnectAttemptsRef.current = 0;
      connect();
    }, 1000);
  }, [connect, disconnect]);

  // Initialize connection on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Handle page visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && !isConnected) {
        // Page became visible and we're not connected, try to reconnect
        reconnect();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isConnected, reconnect]);

  // Handle online/offline events
  useEffect(() => {
    const handleOnline = () => {
      if (!isConnected) {
        reconnect();
      }
    };

    const handleOffline = () => {
      setError('İnternet bağlantısı kesildi');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isConnected, reconnect]);

  return {
    isConnected,
    connectionStatus,
    sendMessage,
    lastMessage,
    error,
    reconnect
  };
};