/**
 * Task 109.3: Study Room Chat Interface
 *
 * Real-time chat with WebSocket support.
 * Features: text messages, file sharing, reactions, threads, mentions.
 */

import {
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  MoreVert as MoreVertIcon,
  Reply as ReplyIcon,
  ThumbUp as ThumbUpIcon,
  Favorite as FavoriteIcon,
  TagFaces as TagFacesIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Menu,
  MenuItem,
  Divider,
} from '@mui/material';
import axios from 'axios';
import * as React from 'react';
import {  useState, useEffect, useRef  } from 'react';

import { config } from '@/config';
import { dateUtils } from '@/utils/dateUtils';

// ============================================================
// Types
// ============================================================

interface Message {
  id: string;
  room_id: string;
  sender_id: string;
  sender_name: string;
  sender_avatar?: string;
  message_type: 'text' | 'file' | 'image' | 'link' | 'system';
  content: string;
  file_url?: string;
  file_name?: string;
  file_size?: number;
  reply_to_id?: string;
  reply_to_message?: string;
  reply_to_sender?: string;
  mentions?: string[];
  reactions?: MessageReaction[];
  created_at: string;
  edited_at?: string;
  is_edited: boolean;
}

interface MessageReaction {
  emoji: string;
  count: number;
  users: string[];
}

interface ChatInterfaceProps {
  roomId: string;
  currentUserId: string;
  currentUserName: string;
}

// ============================================================
// Component
// ============================================================

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  roomId,
  currentUserId,
  currentUserName: _currentUserName,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [replyTo, setReplyTo] = useState<Message | null>(null);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch messages
  useEffect(() => {
    fetchMessages();
    connectWebSocket();

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [roomId]);

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`/api/v1/study-rooms/${roomId}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const connectWebSocket = () => {
    // WebSocket URL - from config
    const wsUrl = `${config.api.wsURL}/ws/study-rooms/${roomId}/chat`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [...prev, message]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) {return;}

    try {
      const messageData = {
        content: newMessage,
        message_type: 'text',
        reply_to_id: replyTo?.id,
      };

      // Send via HTTP for reliability
      await axios.post(`/api/v1/study-rooms/${roomId}/messages`, messageData);

      // Also send via WebSocket for real-time update
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(JSON.stringify(messageData));
      }

      setNewMessage('');
      setReplyTo(null);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {return;}

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('room_id', roomId);

      const response = await axios.post(`/api/v1/study-rooms/${roomId}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const messageData = {
        content: file.name,
        message_type: file.type.startsWith('image/') ? 'image' : 'file',
        file_url: response.data.file_url,
        file_name: file.name,
        file_size: file.size,
      };

      await axios.post(`/api/v1/study-rooms/${roomId}/messages`, messageData);

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleReaction = async (messageId: string, emoji: string) => {
    try {
      await axios.post(`/api/v1/study-rooms/${roomId}/messages/${messageId}/reaction`, {
        emoji,
      });

      // Update local state
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === messageId) {
            const reactions = msg.reactions || [];
            const existingReaction = reactions.find((r) => r.emoji === emoji);

            if (existingReaction) {
              // Toggle reaction
              if (existingReaction.users.includes(currentUserId)) {
                existingReaction.count--;
                existingReaction.users = existingReaction.users.filter((u) => u !== currentUserId);
              } else {
                existingReaction.count++;
                existingReaction.users.push(currentUserId);
              }
            } else {
              reactions.push({
                emoji,
                count: 1,
                users: [currentUserId],
              });
            }

            return { ...msg, reactions };
          }
          return msg;
        }),
      );
    } catch (error) {
      console.error('Error adding reaction:', error);
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    try {
      await axios.delete(`/api/v1/study-rooms/${roomId}/messages/${messageId}`);
      setMessages((prev) => prev.filter((msg) => msg.id !== messageId));
      setAnchorEl(null);
    } catch (error) {
      console.error('Error deleting message:', error);
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, message: Message) => {
    setAnchorEl(event.currentTarget);
    setSelectedMessage(message);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedMessage(null);
  };

  const renderMessage = (message: Message) => {
    const isOwnMessage = message.sender_id === currentUserId;
    const isSystemMessage = message.message_type === 'system';

    if (isSystemMessage) {
      return (
        <Box key={message.id} sx={{ textAlign: 'center', my: 2 }}>
          <Chip label={message.content} size="small" sx={{ bgcolor: 'action.hover' }} />
        </Box>
      );
    }

    return (
      <Box
        key={message.id}
        sx={{
          display: 'flex',
          flexDirection: isOwnMessage ? 'row-reverse' : 'row',
          mb: 2,
          gap: 1,
        }}
      >
        {/* Avatar */}
        <Avatar
          src={message.sender_avatar}
          alt={message.sender_name}
          sx={{ width: 32, height: 32 }}
        >
          {message.sender_name.charAt(0).toUpperCase()}
        </Avatar>

        {/* Message Content */}
        <Box sx={{ maxWidth: '70%' }}>
          {/* Sender Name and Time */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              mb: 0.5,
              flexDirection: isOwnMessage ? 'row-reverse' : 'row',
            }}
          >
            <Typography variant="caption" fontWeight="bold">
              {message.sender_name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {dateUtils.fromNow(message.created_at)}
            </Typography>
            {message.is_edited && (
              <Typography variant="caption" color="text.secondary" fontStyle="italic">
                (düzenlendi)
              </Typography>
            )}
          </Box>

          {/* Reply To */}
          {message.reply_to_message && (
            <Paper
              sx={{
                p: 1,
                mb: 0.5,
                bgcolor: 'action.hover',
                borderLeft: '3px solid',
                borderColor: 'primary.main',
              }}
            >
              <Typography variant="caption" color="text.secondary" display="block">
                <ReplyIcon sx={{ fontSize: 12, mr: 0.5 }} />
                {message.reply_to_sender}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {message.reply_to_message}
              </Typography>
            </Paper>
          )}

          {/* Message Bubble */}
          <Paper
            sx={{
              p: 1.5,
              bgcolor: isOwnMessage ? 'primary.main' : 'background.paper',
              color: isOwnMessage ? 'primary.contrastText' : 'text.primary',
              borderRadius: 2,
              position: 'relative',
            }}
          >
            {/* Message Type: Text */}
            {message.message_type === 'text' && (
              <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                {message.content}
              </Typography>
            )}

            {/* Message Type: Image */}
            {message.message_type === 'image' && (
              <Box>
                <img
                  src={message.file_url}
                  alt={message.file_name}
                  style={{ maxWidth: '100%', borderRadius: 8 }}
                />
                {message.content && (
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {message.content}
                  </Typography>
                )}
              </Box>
            )}

            {/* Message Type: File */}
            {message.message_type === 'file' && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AttachFileIcon fontSize="small" />
                <Box>
                  <Typography variant="body2">{message.file_name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {(message.file_size! / 1024 / 1024).toFixed(2)} MB
                  </Typography>
                </Box>
              </Box>
            )}

            {/* Message Type: Link */}
            {message.message_type === 'link' && (
              <Box>
                <LinkIcon fontSize="small" sx={{ mr: 1 }} />
                <a href={message.content} target="_blank" rel="noopener noreferrer">
                  {message.content}
                </a>
              </Box>
            )}

            {/* Message Menu */}
            <IconButton
              size="small"
              onClick={(e) => handleMenuOpen(e, message)}
              aria-label="more"
              sx={{
                position: 'absolute',
                top: 4,
                right: 4,
                opacity: 0.5,
                '&:hover': { opacity: 1 },
              }}
            >
              <MoreVertIcon fontSize="small" />
            </IconButton>
          </Paper>

          {/* Reactions */}
          {message.reactions && message.reactions.length > 0 && (
            <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
              {message.reactions.map((reaction) => (
                <Chip
                  key={reaction.emoji}
                  label={`${reaction.emoji} ${reaction.count}`}
                  size="small"
                  onClick={() => handleReaction(message.id, reaction.emoji)}
                  sx={{
                    height: 24,
                    bgcolor: reaction.users.includes(currentUserId)
                      ? 'primary.light'
                      : 'action.hover',
                  }}
                />
              ))}
            </Box>
          )}
        </Box>
      </Box>
    );
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Messages Container */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          bgcolor: 'background.default',
        }}
      >
        {messages.length === 0 ? (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <Typography color="text.secondary">
              Henüz mesaj yok. İlk mesajı sen gönder! 💬
            </Typography>
          </Box>
        ) : (
          messages.map((message) => renderMessage(message))
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Reply Preview */}
      {replyTo && (
        <Paper sx={{ p: 1, m: 1, bgcolor: 'action.hover', display: 'flex', alignItems: 'center' }}>
          <ReplyIcon sx={{ mr: 1 }} />
          <Box sx={{ flex: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {replyTo.sender_name} kişisine yanıt veriyorsunuz
            </Typography>
            <Typography variant="body2" noWrap>
              {replyTo.content}
            </Typography>
          </Box>
          <IconButton size="small" onClick={() => setReplyTo(null)}>
            ✕
          </IconButton>
        </Paper>
      )}

      {/* Message Input */}
      <Paper sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            onChange={handleFileUpload}
            accept="image/*,.pdf,.doc,.docx,.txt"
          />
          <IconButton onClick={() => fileInputRef.current?.click()} aria-label="attach">
            <AttachFileIcon />
          </IconButton>

          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Mesajınızı yazın..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            variant="outlined"
            size="small"
          />

          <IconButton color="primary" onClick={handleSendMessage} disabled={!newMessage.trim()} aria-label="send">
            <SendIcon />
          </IconButton>
        </Box>
      </Paper>

      {/* Message Context Menu */}
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem
          onClick={() => {
            setReplyTo(selectedMessage);
            handleMenuClose();
          }}
        >
          <ReplyIcon sx={{ mr: 1 }} fontSize="small" />
          Yanıtla
        </MenuItem>
        <MenuItem onClick={() => handleReaction(selectedMessage?.id || '', '👍')}>
          <ThumbUpIcon sx={{ mr: 1 }} fontSize="small" />
          Beğen
        </MenuItem>
        <MenuItem onClick={() => handleReaction(selectedMessage?.id || '', '❤️')}>
          <FavoriteIcon sx={{ mr: 1 }} fontSize="small" />
          Kalp
        </MenuItem>
        <MenuItem onClick={() => handleReaction(selectedMessage?.id || '', '😂')}>
          <TagFacesIcon sx={{ mr: 1 }} fontSize="small" />
          Gül
        </MenuItem>
        {selectedMessage?.sender_id === currentUserId && (
          <>
            <Divider />
            <MenuItem
              onClick={() => handleDeleteMessage(selectedMessage?.id || '')}
              sx={{ color: 'error.main' }}
            >
              Sil
            </MenuItem>
          </>
        )}
      </Menu>
    </Box>
  );
};

export default ChatInterface;
