/**
 * NodeChatPanel — Inline AI chat for a learning path node
 *
 * Uses SSE streaming via chatService.sendMessageStreaming()
 * Shows suggested questions + message history + input
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  IconButton,
  Chip,
  CircularProgress,
} from '@mui/material';
import { Send, SmartToy } from '@mui/icons-material';
import chatService from '../../services/chatService';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface NodeChatPanelProps {
  nodeTitle: string;
  nodeDescription: string;
}

const SUGGESTED_QUESTIONS = [
  'Bu konuyu açıkla',
  'Neden bu sırada?',
  'Çalışma önerileri',
  'Örnek soru sor',
];

export function NodeChatPanel({ nodeTitle, nodeDescription: _nodeDescription }: NodeChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) {return;}

    const userMessage = text.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    // Add placeholder for streaming response
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    try {
      const contextMessage = `[Konu: ${nodeTitle}] ${userMessage}`;
      await chatService.sendMessageStreaming(
        contextMessage,
        (accumulated) => {
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: 'assistant', content: accumulated };
            return updated;
          });
        },
        { subject: nodeTitle.split(' ')[0]?.toLowerCase() || 'matematik' },
      );
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Yanıt alınamadı. Lütfen tekrar deneyin.',
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, nodeTitle]);

  return (
    <Box>
      {/* Suggested questions — only show when no messages yet */}
      {messages.length === 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
          {SUGGESTED_QUESTIONS.map((q) => (
            <Chip
              key={q}
              label={q}
              size="small"
              variant="outlined"
              onClick={() => sendMessage(q)}
              sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'rgba(99,102,241,0.08)' } }}
            />
          ))}
        </Box>
      )}

      {/* Messages */}
      {messages.length > 0 && (
        <Box sx={{ maxHeight: 280, overflowY: 'auto', mb: 1.5, display: 'flex', flexDirection: 'column', gap: 1 }}>
          {messages.map((msg, i) => (
            <Box
              key={i}
              sx={{
                display: 'flex',
                gap: 1,
                alignItems: 'flex-start',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              {msg.role === 'assistant' && (
                <SmartToy sx={{ fontSize: 20, color: '#6366f1', mt: 0.5, flexShrink: 0 }} />
              )}
              <Box
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  maxWidth: '85%',
                  backgroundColor: msg.role === 'user' ? '#6366f1' : 'grey.100',
                  color: msg.role === 'user' ? 'white' : 'text.primary',
                }}
              >
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>
                  {msg.content || (isLoading ? '...' : '')}
                </Typography>
              </Box>
            </Box>
          ))}
          <div ref={messagesEndRef} />
        </Box>
      )}

      {/* Input */}
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          size="small"
          fullWidth
          placeholder={`${nodeTitle} hakkında sor...`}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage(input);
            }
          }}
          disabled={isLoading}
          sx={{ '& .MuiInputBase-root': { borderRadius: 2 } }}
        />
        <IconButton
          color="primary"
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || isLoading}
        >
          {isLoading ? <CircularProgress size={20} /> : <Send />}
        </IconButton>
      </Box>
    </Box>
  );
}

export default NodeChatPanel;
