import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { 
  Send, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Settings, 
  History, 
  Trash2,
  CheckCircle,
  AlertCircle,
  Wifi,
  WifiOff,
  MessageSquare,
  Bot,
  User,
  Lightbulb,
  BookOpen,
  Target,
  Zap
} from 'lucide-react';
import { Message, Agent } from '../../types';
import chatService, { ChatMessage } from '../../services/chatService';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useTurkishLanguageCorrection } from '../../hooks/useTurkishLanguageCorrection';

interface TurkishChatInterfaceProps {
  studentId: string;
  sessionId?: string;
  subject?: string;
  onMessageSent?: (message: string) => void;
  onAgentResponse?: (response: ChatMessage) => void;
  className?: string;
}

interface ChatSettings {
  enableVoice: boolean;
  enableBionicReading: boolean;
  enableLanguageCorrection: boolean;
  responseMode: 'simple' | 'detailed' | 'adaptive';
  fontSize: 'small' | 'medium' | 'large';
  theme: 'light' | 'dark';
}

interface LanguageCorrection {
  original: string;
  corrected: string;
  suggestions: string[];
  confidence: number;
}

// Speech-to-text conversion helper
async function convertSpeechToText(audioBlob: Blob): Promise<string> {
  try {
    // Create FormData to send audio file
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    formData.append('language', 'tr-TR'); // Turkish language

    // Send to backend speech-to-text endpoint
    const response = await fetch('/api/v1/speech-to-text', {
      method: 'POST',
      body: formData,
      signal: AbortSignal.timeout(30000) // 30 second timeout
    });

    if (!response.ok) {
      throw new Error(`STT service error: ${response.status}`);
    }

    const data = await response.json();

    // Return transcription text
    return data.transcription || data.text || '';
  } catch (error) {
    console.error('Speech-to-text conversion failed:', error);
    throw error;
  }
}

export const TurkishChatInterface: React.FC<TurkishChatInterfaceProps> = ({
  studentId,
  sessionId,
  subject = 'genel',
  onMessageSent,
  onAgentResponse,
  className = ''
}) => {
  // State management
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [languageCorrections, setLanguageCorrections] = useState<LanguageCorrection[]>([]);
  
  // Settings state
  const [settings, setSettings] = useState<ChatSettings>({
    enableVoice: false,
    enableBionicReading: false,
    enableLanguageCorrection: true,
    responseMode: 'adaptive',
    fontSize: 'medium',
    theme: 'light'
  });

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  // Custom hooks
  const { 
    isConnected, 
    connectionStatus, 
    sendMessage: sendWebSocketMessage,
    lastMessage 
  } = useWebSocket(studentId, sessionId);

  const {
    checkText,
    suggestions,
    isChecking
  } = useTurkishLanguageCorrection();

  // Load messages on component mount
  useEffect(() => {
    const loadMessages = async () => {
      try {
        const storedMessages = chatService.loadMessagesFromLocalStorage();
        setMessages(storedMessages);
        
        if (sessionId) {
          const sessionMessages = await chatService.loadSession(sessionId);
          setMessages(sessionMessages);
        }
      } catch (error) {
        console.error('Mesajlar yüklenirken hata:', error);
      }
    };

    loadMessages();
  }, [sessionId]);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      setMessages(prev => [...prev, lastMessage]);
      setIsLoading(false);
      onAgentResponse?.(lastMessage);
    }
  }, [lastMessage, onAgentResponse]);

  // Auto-scroll to bottom
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages]);

  // Language correction effect
  useEffect(() => {
    if (settings.enableLanguageCorrection && input.trim().length > 10) {
      const timeoutId = setTimeout(() => {
        checkText(input);
      }, 1000);

      return () => clearTimeout(timeoutId);
    }
  }, [input, settings.enableLanguageCorrection, checkText]);

  // Handle message submission
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;

    const messageText = input.trim();
    setInput('');
    setIsLoading(true);

    try {
      // Add user message immediately
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: messageText,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, userMessage]);
      onMessageSent?.(messageText);

      // Send via WebSocket if connected, otherwise use HTTP
      if (isConnected) {
        sendWebSocketMessage('turkish_nlp', messageText);
      } else {
        const response = await chatService.sendMessage('turkish_nlp', messageText);
        setMessages(prev => [...prev, response]);
        setIsLoading(false);
        onAgentResponse?.(response);
      }

    } catch (error) {
      console.error('Mesaj gönderilirken hata:', error);
      setIsLoading(false);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: 'Üzgünüm, mesajınızı işleyemedim. Lütfen tekrar deneyin.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }, [input, isLoading, isConnected, sendWebSocketMessage, onMessageSent, onAgentResponse]);

  // Voice recording handlers
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const audioChunks: Blob[] = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

        try {
          // Send audio to speech-to-text service
          const transcription = await convertSpeechToText(audioBlob);

          if (transcription) {
            // Set the transcribed text as input
            setInput(transcription);

            // Optionally auto-send the message
            if (settings.enableVoice) {
              // Create a temporary message event
              handleSendMessage();
            }
          }
        } catch (error) {
          console.error('Ses-metin dönüştürme hatası:', error);
          // Show error message to user
          const errorMsg: ChatMessage = {
            id: `error-${Date.now()}`,
            role: 'system',
            content: 'Ses kaydı metne dönüştürülemedi. Lütfen tekrar deneyin.',
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMsg]);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Ses kaydı başlatılamadı:', error);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  }, [isRecording]);

  // Quick action buttons
  const quickActions = useMemo(() => [
    { 
      text: 'Konu açıkla', 
      icon: <BookOpen className="w-4 h-4" />,
      prompt: 'Bu konuyu detaylı olarak açıklar mısın?'
    },
    { 
      text: 'Soru sor', 
      icon: <Target className="w-4 h-4" />,
      prompt: 'Bu konu hakkında bana soru sorabilir misin?'
    },
    { 
      text: 'Örnek ver', 
      icon: <Lightbulb className="w-4 h-4" />,
      prompt: 'Bu konuya örnek verebilir misin?'
    },
    { 
      text: 'Özet çıkar', 
      icon: <Zap className="w-4 h-4" />,
      prompt: 'Bu konunun özetini çıkarabilir misin?'
    }
  ], []);

  // Clear chat history
  const clearHistory = useCallback(async () => {
    try {
      await chatService.clearAllSessions();
      setMessages([]);
    } catch (error) {
      console.error('Geçmiş temizlenirken hata:', error);
    }
  }, []);

  // Apply language correction
  const applyCorrection = useCallback((correction: LanguageCorrection) => {
    setInput(correction.corrected);
    setLanguageCorrections(prev => prev.filter(c => c.original !== correction.original));
  }, []);

  // Format message content with Bionic Reading if enabled
  const formatMessageContent = useCallback((content: string) => {
    if (settings.enableBionicReading) {
      // Simple Bionic Reading implementation for Turkish
      return content.split(' ').map((word, index) => {
        if (word.length > 3) {
          const boldLength = Math.ceil(word.length * 0.4);
          return (
            <span key={index}>
              <strong>{word.slice(0, boldLength)}</strong>
              {word.slice(boldLength)}
              {' '}
            </span>
          );
        }
        return <span key={index}>{word} </span>;
      });
    }
    
    return content.split('\n').map((line, i) => (
      <span key={i}>
        {line}
        {i < content.split('\n').length - 1 && <br />}
      </span>
    ));
  }, [settings.enableBionicReading]);

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-full">
            <Bot className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-800">Türkçe AI Asistan</h2>
            <p className="text-sm text-gray-600">
              {subject} • {isConnected ? 'Bağlı' : 'Bağlantı kesildi'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Connection status */}
          <div className="flex items-center space-x-1">
            {isConnected ? (
              <Wifi className="w-4 h-4 text-green-500" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-500" />
            )}
          </div>
          
          {/* Settings button */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
          
          {/* History button */}
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
          >
            <History className="w-5 h-5" />
          </button>
          
          {/* Clear history button */}
          <button
            onClick={clearHistory}
            className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Language corrections */}
      {settings.enableLanguageCorrection && suggestions.length > 0 && (
        <div className="p-3 bg-yellow-50 border-b border-yellow-200">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-yellow-800 font-medium">Dil düzeltme önerileri:</p>
              <div className="mt-1 space-y-1">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => applyCorrection(suggestion)}
                    className="text-xs bg-yellow-100 hover:bg-yellow-200 text-yellow-800 px-2 py-1 rounded transition-colors"
                  >
                    {suggestion.corrected}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-6xl mb-4">💬</div>
            <p className="text-lg font-medium">Merhaba! Size nasıl yardımcı olabilirim?</p>
            <p className="text-sm mt-2">Türkçe sorularınızı sorabilir, konuları açıklamamı isteyebilirsiniz.</p>
            
            {/* Quick actions for empty state */}
            <div className="mt-6 grid grid-cols-2 gap-3 max-w-md mx-auto">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => setInput(action.prompt)}
                  className="flex items-center space-x-2 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-left"
                >
                  {action.icon}
                  <span className="text-sm font-medium">{action.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageBubble
              key={`${message.id}-${index}`}
              message={message}
              formatContent={formatMessageContent}
              settings={settings}
            />
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-xs">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-xs text-gray-500">Yazıyor...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4 bg-gray-50">
        {/* Quick actions */}
        <div className="mb-3 flex flex-wrap gap-2">
          {quickActions.map((action, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setInput(action.prompt)}
              className="flex items-center space-x-1 text-xs px-3 py-1.5 bg-white hover:bg-gray-100 border border-gray-200 rounded-full transition-colors"
            >
              {action.icon}
              <span>{action.text}</span>
            </button>
          ))}
        </div>
        
        <div className="flex items-end space-x-3">
          {/* Text input */}
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Mesajınızı Türkçe yazın..."
              disabled={isLoading}
              rows={1}
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 resize-none"
              style={{ minHeight: '48px', maxHeight: '120px' }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            
            {/* Language checking indicator */}
            {isChecking && (
              <div className="absolute right-3 top-3">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}
          </div>
          
          {/* Voice recording button */}
          {settings.enableVoice && (
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              className={`p-3 rounded-lg transition-colors ${
                isRecording 
                  ? 'bg-red-500 text-white hover:bg-red-600' 
                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
              }`}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>
          )}
          
          {/* Send button */}
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        
        {/* Input hints */}
        <div className="mt-2 text-xs text-gray-500">
          <span>Enter ile gönder • Shift+Enter ile yeni satır</span>
          {settings.enableLanguageCorrection && (
            <span className="ml-2">• Dil düzeltme aktif</span>
          )}
        </div>
      </form>
    </div>
  );
};

// Message bubble component
interface MessageBubbleProps {
  message: ChatMessage;
  formatContent: (content: string) => React.ReactNode;
  settings: ChatSettings;
}

const MessageBubble: React.FC<MessageBubbleProps> = React.memo(({ 
  message, 
  formatContent, 
  settings 
}) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex items-start space-x-3 max-w-2xl ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser 
            ? 'bg-blue-500' 
            : isSystem 
              ? 'bg-gray-400' 
              : 'bg-green-500'
        }`}>
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : isSystem ? (
            <AlertCircle className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </div>
        
        {/* Message content */}
        <div className={`rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-blue-500 text-white'
            : isSystem
              ? 'bg-gray-100 text-gray-700 border border-gray-200'
              : 'bg-gray-100 text-gray-800'
        }`}>
          {/* Agent label */}
          {!isUser && !isSystem && message.agent && (
            <div className="text-xs opacity-75 mb-1 font-medium">
              🤖 {message.agent === 'turkish_nlp' ? 'Türkçe AI Asistan' : message.agent}
            </div>
          )}
          
          {/* Message text */}
          <div className={`whitespace-pre-wrap ${settings.fontSize === 'small' ? 'text-sm' : settings.fontSize === 'large' ? 'text-lg' : 'text-base'}`}>
            {formatContent(message.content)}
          </div>
          
          {/* Timestamp */}
          <div className={`text-xs mt-2 opacity-75 ${
            isUser ? 'text-blue-100' : 'text-gray-500'
          }`}>
            {new Date(message.timestamp).toLocaleTimeString('tr-TR', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        </div>
      </div>
    </div>
  );
});

MessageBubble.displayName = 'MessageBubble';

export default TurkishChatInterface;