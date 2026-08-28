import clsx from 'clsx';
import * as React from 'react';
import {  useState, useRef, useEffect, useCallback, useMemo  } from 'react';

import { Message, Agent } from './types';

interface ChatProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  isLoading: boolean
  currentAgent?: Agent
}

export function Chat({ messages, onSendMessage, isLoading, currentAgent }: ChatProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive - optimized with debouncing
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [messages]);

  // Memoized submit handler for performance
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  }, [input, isLoading, onSendMessage]);

  // Memoized message formatter to avoid re-renders
  const formatMessage = useCallback((content: string) => {
    // Simple formatting: preserve line breaks and basic markdown
    return content.split('\n').map((line, i) => (
      <span key={i}>
        {line}
        {i < content.split('\n').length - 1 && <br />}
      </span>
    ));
  }, []);

  // Memoized quick action buttons
  const quickActions = useMemo(() => [
    { text: 'Öğrenme planı oluştur', icon: '📚' },
    { text: 'Quiz oluştur', icon: '❓' },
    { text: 'Sınav stratejileri', icon: '📝' },
    { text: 'Flashcard oluştur', icon: '🎴' },
  ], []);

  // Memoized agent info to prevent unnecessary re-renders
  const agentInfo = useMemo(() => {
    if (!currentAgent) {return null;}

    return (
      <div className="flex items-center space-x-3">
        <span className="text-2xl">{currentAgent.icon}</span>
        <div>
          <h2 className="font-semibold text-gray-800">{currentAgent.name}</h2>
          <p className="text-sm text-gray-600">{currentAgent.description}</p>
        </div>
      </div>
    );
  }, [currentAgent]);

  return (
    <div className="flex flex-col h-full">
      {/* Header - Optimized with memoized agent info */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        {agentInfo}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-6xl mb-4">💬</div>
            <p className="text-lg">Merhaba! Size nasıl yardımcı olabilirim?</p>
            <p className="text-sm mt-2">Bir soru sorarak başlayabilirsiniz.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageBubble
              key={`${message.timestamp}-${index}`} // Better key for performance
              message={message}
              formatMessage={formatMessage}
            />
          ))
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex space-x-4">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Mesajınızı yazın..."
            disabled={isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? '⏳' : '📤'} Gönder
          </button>
        </div>

        {/* Optimized Quick Actions */}
        <div className="mt-2 flex flex-wrap gap-2">
          {quickActions.map((action) => (
            <QuickActionButton
              key={action.text}
              text={action.text}
              icon={action.icon}
              onClick={() => setInput(action.text)}
            />
          ))}
        </div>

        {/* Legal Disclaimer */}
        <div className="text-[10px] text-gray-400 mt-3 p-1 text-center">
          ⚠️ Yapay zeka asistanı hata yapabilir. Üretilen akademik çözümleri daima MEB ders kitapları veya öğretmenleriniz ile teyit ediniz.
        </div>
      </form>
    </div>
  );
}

// Memoized MessageBubble component for better performance
const MessageBubble = React.memo(({ message, formatMessage }: {
  message: Message
  formatMessage: (content: string) => React.ReactNode
}) => {
  const agentLabel = useMemo(() => {
    if (message.role !== 'agent' || !message.agent) {return null;}

    const labels = {
      'learning': '📚 Öğrenme Yolu',
      'study': '💡 Çalışma Arkadaşı',
      'exam': '📝 Sınav Uzmanı',
    };

    return labels[message.agent as keyof typeof labels];
  }, [message.agent, message.role]);

  return (
    <div
      className={clsx(
        'flex',
        message.role === 'user' ? 'justify-end' : 'justify-start',
      )}
    >
      <div
        className={clsx(
          'max-w-2xl rounded-lg px-4 py-3',
          message.role === 'user'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-800',
        )}
      >
        {agentLabel && (
          <div className="text-xs opacity-75 mb-1">
            {agentLabel}
          </div>
        )}
        <div className="whitespace-pre-wrap">
          {formatMessage(message.content)}
        </div>
        <div className={clsx(
          'text-xs mt-2',
          message.role === 'user' ? 'text-blue-100' : 'text-gray-500',
        )}>
          {new Date(message.timestamp).toLocaleTimeString('tr-TR')}
        </div>
      </div>
    </div>
  );
});

// Memoized QuickActionButton component
const QuickActionButton = React.memo(({ text, icon, onClick }: {
  text: string
  icon: string
  onClick: () => void
}) => (
  <button
    type="button"
    onClick={onClick}
    className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
  >
    {icon} {text.replace(/oluştur|stratejileri/, '').trim()}
  </button>
));