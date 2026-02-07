import {
  Send,
  AttachFile,
  Mic,
  Stop,
  EmojiEmotions,
  Code,
  FormatBold,
  FormatItalic,
} from '@mui/icons-material';
import { IconButton, Tooltip, TextField, Paper } from '@mui/material';
import { motion } from 'framer-motion';
import { useState, useRef, KeyboardEvent } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isLoading?: boolean
  placeholder?: string
}

export function ChatInput({ onSendMessage, isLoading, placeholder }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoiceToggle = () => {
    setIsRecording(!isRecording);
    // Voice recording logic would go here
  };

  const insertFormatting = (format: string) => {
    const input = inputRef.current;
    if (!input) {return;}

    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const selectedText = message.substring(start, end);

    let formattedText = '';
    switch (format) {
      case 'bold':
        formattedText = `**${selectedText || 'metin'}**`;
        break;
      case 'italic':
        formattedText = `*${selectedText || 'metin'}*`;
        break;
      case 'code':
        formattedText = `\`${selectedText || 'kod'}\``;
        break;
      default:
        formattedText = selectedText;
    }

    const newMessage =
      message.substring(0, start) +
      formattedText +
      message.substring(end);

    setMessage(newMessage);
    setTimeout(() => {
      input.focus();
      input.setSelectionRange(
        start + formattedText.length,
        start + formattedText.length,
      );
    }, 0);
  };

  return (
    <Paper
      elevation={3}
      className="p-4 border-t border-gray-200 bg-white"
    >
      <div className="flex flex-col gap-2">
        {/* Formatting Toolbar */}
        <div className="flex items-center gap-1 px-2">
          <Tooltip title="Kalın">
            <IconButton
              size="small"
              onClick={() => insertFormatting('bold')}
            >
              <FormatBold fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="İtalik">
            <IconButton
              size="small"
              onClick={() => insertFormatting('italic')}
            >
              <FormatItalic fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Kod">
            <IconButton
              size="small"
              onClick={() => insertFormatting('code')}
            >
              <Code fontSize="small" />
            </IconButton>
          </Tooltip>

          <div className="w-px h-6 bg-gray-300 mx-1" />

          <Tooltip title="Emoji">
            <IconButton size="small">
              <EmojiEmotions fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Dosya Ekle">
            <IconButton size="small">
              <AttachFile fontSize="small" />
            </IconButton>
          </Tooltip>
        </div>

        {/* Input Area */}
        <div className="flex items-end gap-2">
          <TextField
            ref={inputRef}
            multiline
            maxRows={4}
            fullWidth
            variant="outlined"
            placeholder={placeholder || 'Mesajınızı yazın...'}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            className="flex-1"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '20px',
                backgroundColor: '#f9fafb',
                '&:hover fieldset': {
                  borderColor: '#3b82f6',
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#3b82f6',
                },
              },
            }}
          />

          {/* Voice Button */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Tooltip title={isRecording ? 'Kaydı Durdur' : 'Sesli Mesaj'}>
              <IconButton
                onClick={handleVoiceToggle}
                color={isRecording ? 'error' : 'default'}
                className={isRecording ? 'animate-pulse' : ''}
              >
                {isRecording ? <Stop /> : <Mic />}
              </IconButton>
            </Tooltip>
          </motion.div>

          {/* Send Button */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <IconButton
              onClick={handleSend}
              disabled={!message.trim() || isLoading}
              color="primary"
              className="bg-blue-500 text-white hover:bg-blue-600 disabled:bg-gray-300"
            >
              <Send />
            </IconButton>
          </motion.div>
        </div>

        {/* Character Counter */}
        <div className="flex justify-between items-center px-2">
          <span className="text-xs text-gray-400">
            {message.length} / 4000 karakter
          </span>
          {isLoading && (
            <span className="text-xs text-blue-500 animate-pulse">
              AI yanıt yazıyor...
            </span>
          )}
        </div>
      </div>
    </Paper>
  );
}