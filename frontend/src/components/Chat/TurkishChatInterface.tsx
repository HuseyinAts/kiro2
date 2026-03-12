/**
 * Turkish Chat Interface - MUI + Glassmorphism Design
 * Proje tasarim sistemiyle uyumlu modern chat arayuzu
 */

import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Warning as WarningIcon,
  MenuBook as MenuBookIcon,
  Quiz as QuizIcon,
  Lightbulb as LightbulbIcon,
  Summarize as SummarizeIcon,
  DeleteOutline as DeleteIcon,
  Add as AddIcon,
  History as HistoryIcon,
  AttachFile as AttachFileIcon,
  Close as CloseIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  InsertDriveFile as FileIcon,
  Functions as FormulasIcon,
  Route as StepsIcon,
  EmojiEvents as StrategyIcon,
  ErrorOutline as MistakeIcon,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Paper,
  CircularProgress,
  Menu,
  MenuItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Tooltip,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

import { modernColors } from '../../theme/modern-colors';
import chatService, { ChatMessage, ChatSessionInfo } from '../../services/chatService';

interface TurkishChatInterfaceProps {
  studentId: string;
  sessionId?: string;
  subject?: string;
  onMessageSent?: (message: string) => void;
  onAgentResponse?: (response: ChatMessage) => void;
  className?: string;
}

// Quick action definitions (F20: "Ne Soracağımı Bilmiyorum" conversation starters)
const QUICK_ACTIONS = [
  { text: 'Konu acikla', icon: <MenuBookIcon sx={{ fontSize: 16 }} />, prompt: 'Bu konuyu detayli olarak aciklar misin?' },
  { text: 'Soru sor', icon: <QuizIcon sx={{ fontSize: 16 }} />, prompt: 'Bu konu hakkinda bana soru sorabilir misin?' },
  { text: 'Ornek ver', icon: <LightbulbIcon sx={{ fontSize: 16 }} />, prompt: 'Bu konuya ornek verebilir misin?' },
  { text: 'Ozet cikar', icon: <SummarizeIcon sx={{ fontSize: 16 }} />, prompt: 'Bu konunun ozetini cikarabilir misin?' },
];

// Extended starters shown only in empty state — helps students who don't know what to ask
const CONVERSATION_STARTERS = [
  { text: 'Yaygın yanılgılar', icon: <MistakeIcon sx={{ fontSize: 16 }} />, prompt: 'Bu konudaki en yaygın 3 yanılgı nedir? Öğrenciler genelde neyi yanlış anlıyor?' },
  { text: 'Basitçe anlat', icon: <LightbulbIcon sx={{ fontSize: 16 }} />, prompt: 'Bu konuyu en basit şekilde, günlük hayattan örneklerle anlat.' },
  { text: 'Pratik soru sor', icon: <QuizIcon sx={{ fontSize: 16 }} />, prompt: 'Bana bu konudan bir pratik soru sor, sonra çözümünü adım adım kontrol edelim.' },
  { text: 'Formül hatırlatıcı', icon: <FormulasIcon sx={{ fontSize: 16 }} />, prompt: 'Bu konudaki tüm önemli formülleri ve ne zaman kullanılacaklarını listele.' },
  { text: 'Adım adım çözüm', icon: <StepsIcon sx={{ fontSize: 16 }} />, prompt: 'Tipik bir YKS sorusunu adım adım çözelim. Her adımda neden o işlemi yaptığımızı açıkla.' },
  { text: 'Sınav stratejisi', icon: <StrategyIcon sx={{ fontSize: 16 }} />, prompt: 'Bu konu sınavda nasıl çıkıyor? Hangi soru tiplerini beklemeliyim ve nasıl yaklaşmalıyım?' },
];

export const TurkishChatInterface: React.FC<TurkishChatInterfaceProps> = ({
  studentId: _studentId,
  sessionId,
  subject = 'genel',
  onMessageSent,
  onAgentResponse,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [teachingMode, setTeachingMode] = useState<'direct' | 'socratic'>('direct');
  const [attachment, setAttachment] = useState<File | null>(null);
  const [attachmentPreview, setAttachmentPreview] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSessionInfo[]>([]);
  const [sessionMenuAnchor, setSessionMenuAnchor] = useState<null | HTMLElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load messages on mount — try DB first, fallback to localStorage
  useEffect(() => {
    const load = async () => {
      // Try restoring from DB if we have a session_id
      const savedId = sessionId || localStorage.getItem('chatSessionId');
      if (savedId) {
        const dbMessages = await chatService.loadSessionFromDB(savedId);
        if (dbMessages.length > 0) {
          setMessages(dbMessages);
          return;
        }
      }
      // Fallback to localStorage
      const stored = chatService.loadMessagesFromLocalStorage();
      setMessages(stored);
    };
    load();
  }, [sessionId]);

  // Load session list
  const refreshSessions = useCallback(async () => {
    const list = await chatService.listSessions();
    setSessions(list);
  }, []);

  const handleNewChat = useCallback(() => {
    chatService.startNewSession();
    setMessages([]);
    setSessionMenuAnchor(null);
  }, []);

  const handleLoadSession = useCallback(async (sid: string) => {
    setSessionMenuAnchor(null);
    const dbMessages = await chatService.loadSessionFromDB(sid);
    setMessages(dbMessages);
  }, []);

  // Auto-scroll
  useEffect(() => {
    const t = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    return () => clearTimeout(t);
  }, [messages]);

  // Submit handler
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();
    // If attachment present, use attachment handler instead
    if (attachment) {
      await handleSubmitWithAttachment();
      return;
    }
    if (!input.trim() || isLoading) return;

    const text = input.trim();
    setInput('');
    setIsLoading(true);

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    onMessageSent?.(text);

    // Create a placeholder bot message for streaming
    const botMsgId = `bot-${Date.now()}`;
    const botPlaceholder: ChatMessage = {
      id: botMsgId,
      role: 'agent',
      content: '',
      agent: 'turkish_nlp',
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, botPlaceholder]);

    try {
      await chatService.sendMessageStreaming(text, (accumulated) => {
        // Update the bot message content as tokens arrive
        setMessages(prev =>
          prev.map(msg => msg.id === botMsgId ? { ...msg, content: accumulated } : msg),
        );
      }, { subject, teachingMode });
      // Get final message for callback
      setMessages(prev => {
        const final = prev.find(m => m.id === botMsgId);
        if (final) onAgentResponse?.(final);
        return prev;
      });
    } catch (error) {
      console.error('Mesaj gonderilemedi:', error);
      // Replace placeholder with error
      setMessages(prev =>
        prev.map(msg => msg.id === botMsgId ? {
          ...msg,
          role: 'system' as const,
          content: 'Mesajinizi isleyemedim. Lutfen tekrar deneyin.',
        } : msg),
      );
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, onMessageSent, onAgentResponse]);

  const clearHistory = useCallback(async () => {
    await chatService.clearAllSessions().catch(console.error);
    setMessages([]);
  }, []);

  // --- Attachment handlers ---
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      alert('Dosya boyutu 10MB\'yi asamaz.');
      return;
    }
    setAttachment(file);
    // Generate preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (ev) => setAttachmentPreview(ev.target?.result as string);
      reader.readAsDataURL(file);
    } else {
      setAttachmentPreview(null);
    }
    // Reset file input
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  const clearAttachment = useCallback(() => {
    setAttachment(null);
    setAttachmentPreview(null);
  }, []);

  const handleSubmitWithAttachment = useCallback(async () => {
    if (!attachment || isLoading) return;
    const text = input.trim();
    setInput('');
    setIsLoading(true);

    // Show user message with attachment info
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: `${attachment.type.startsWith('image/') ? '🖼️' : '📄'} ${attachment.name}${text ? `\n${text}` : ''}`,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    clearAttachment();

    // Bot placeholder
    const botMsgId = `bot-${Date.now()}`;
    setMessages(prev => [...prev, {
      id: botMsgId, role: 'agent', content: 'Dosya analiz ediliyor...', agent: 'turkish_nlp', timestamp: new Date().toISOString(),
    }]);

    try {
      const result = await chatService.sendMessageWithAttachment({
        file: attachment,
        message: text,
        subject,
        teachingMode,
      });
      setMessages(prev =>
        prev.map(msg => msg.id === botMsgId ? { ...msg, content: result.message } : msg),
      );
    } catch (error: any) {
      setMessages(prev =>
        prev.map(msg => msg.id === botMsgId ? {
          ...msg, role: 'system' as const, content: `Hata: ${error.message || 'Dosya islenemedi.'}`,
        } : msg),
      );
    } finally {
      setIsLoading(false);
    }
  }, [attachment, input, isLoading, subject, teachingMode, clearAttachment]);

  const quickActions = useMemo(() => QUICK_ACTIONS, []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 3,
          py: 2,
          borderBottom: '1px solid',
          borderColor: 'divider',
          background: `linear-gradient(135deg, ${modernColors.primary[50]}, ${modernColors.secondary[50]})`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Avatar
            sx={{
              width: 40,
              height: 40,
              background: modernColors.gradients.purple,
            }}
          >
            <BotIcon sx={{ fontSize: 24 }} />
          </Avatar>
          <Box>
            <Typography variant="subtitle1" fontWeight={600}>
              AI Egitim Asistani
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {subject} konusunda yardimci
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Tooltip title={teachingMode === 'socratic'
            ? 'Sokratik: Cevap vermez, soru sorarak ogretir'
            : 'Dogrudan: Cevabi aciklayarak verir'}>
            <Chip
              label={teachingMode === 'socratic' ? 'Sokratik' : 'Dogrudan'}
              onClick={() => setTeachingMode(prev => prev === 'direct' ? 'socratic' : 'direct')}
              color={teachingMode === 'socratic' ? 'secondary' : 'default'}
              variant={teachingMode === 'socratic' ? 'filled' : 'outlined'}
              size="small"
              sx={{ mr: 1 }}
            />
          </Tooltip>
          <Tooltip title="Yeni Sohbet">
            <IconButton size="small" onClick={handleNewChat} sx={{ color: 'text.secondary' }}>
              <AddIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Gecmis Sohbetler">
            <IconButton
              size="small"
              onClick={(e) => { setSessionMenuAnchor(e.currentTarget); refreshSessions(); }}
              sx={{ color: 'text.secondary' }}
            >
              <HistoryIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Sohbeti Temizle">
            <IconButton size="small" onClick={clearHistory} sx={{ color: 'text.secondary', '&:hover': { color: 'error.main' } }}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>

          {/* Session history dropdown */}
          <Menu
            anchorEl={sessionMenuAnchor}
            open={Boolean(sessionMenuAnchor)}
            onClose={() => setSessionMenuAnchor(null)}
            PaperProps={{
              sx: { maxHeight: 320, width: 280, borderRadius: 2 },
            }}
          >
            <MenuItem onClick={handleNewChat}>
              <ListItemIcon><AddIcon fontSize="small" /></ListItemIcon>
              <ListItemText primary="Yeni Sohbet" />
            </MenuItem>
            <Divider />
            {sessions.length === 0 ? (
              <MenuItem disabled>
                <ListItemText primary="Gecmis sohbet yok" secondary="Mesaj gonderin, otomatik kaydedilir" />
              </MenuItem>
            ) : (
              sessions.map((s) => (
                <MenuItem
                  key={s.id}
                  onClick={() => handleLoadSession(s.id)}
                  selected={chatService.getSessionId() === s.id}
                >
                  <ListItemText
                    primary={s.title || 'Sohbet'}
                    secondary={`${s.message_count} mesaj`}
                    primaryTypographyProps={{ noWrap: true, fontSize: '0.875rem' }}
                    secondaryTypographyProps={{ fontSize: '0.75rem' }}
                  />
                </MenuItem>
              ))
            )}
          </Menu>
        </Box>
      </Box>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          px: 3,
          py: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {messages.length === 0 ? (
          <EmptyState quickActions={quickActions} onAction={setInput} />
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={`${msg.id}-${i}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <MessageBubble message={msg} />
              </motion.div>
            ))}
          </AnimatePresence>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, pl: 6 }}>
              <Paper
                elevation={0}
                sx={{
                  px: 2.5,
                  py: 1.5,
                  borderRadius: '16px',
                  background: 'rgba(255,255,255,0.9)',
                  backdropFilter: 'blur(10px)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <CircularProgress size={16} thickness={5} />
                <Typography variant="caption" color="text.secondary">
                  Yaziyor...
                </Typography>
              </Paper>
            </Box>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          px: 3,
          py: 2,
          borderTop: '1px solid',
          borderColor: 'divider',
          background: 'rgba(255,255,255,0.7)',
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Quick actions */}
        <Box sx={{ display: 'flex', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
          {quickActions.map((action, i) => (
            <Chip
              key={i}
              icon={action.icon}
              label={action.text}
              size="small"
              variant="outlined"
              onClick={() => setInput(action.prompt)}
              sx={{
                borderRadius: '20px',
                borderColor: modernColors.primary[200],
                '&:hover': {
                  background: modernColors.primary[50],
                  borderColor: modernColors.primary[400],
                },
              }}
            />
          ))}
        </Box>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          hidden
          accept="image/*,.pdf,.txt,.doc,.docx"
          onChange={handleFileSelect}
        />

        {/* Attachment preview */}
        {attachment && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              px: 2,
              py: 1,
              mb: 1,
              borderRadius: '12px',
              background: modernColors.primary[50],
              border: `1px solid ${modernColors.primary[200]}`,
            }}
          >
            {attachment.type.startsWith('image/') ? (
              <>
                {attachmentPreview && (
                  <Box
                    component="img"
                    src={attachmentPreview}
                    alt="preview"
                    sx={{ width: 40, height: 40, borderRadius: '8px', objectFit: 'cover' }}
                  />
                )}
                <ImageIcon sx={{ fontSize: 18, color: modernColors.primary[600] }} />
              </>
            ) : attachment.type === 'application/pdf' ? (
              <PdfIcon sx={{ fontSize: 18, color: '#e53935' }} />
            ) : (
              <FileIcon sx={{ fontSize: 18, color: modernColors.primary[600] }} />
            )}
            <Typography variant="body2" sx={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {attachment.name}
            </Typography>
            <IconButton size="small" onClick={clearAttachment}>
              <CloseIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Box>
        )}

        {/* Input + Send */}
        <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-end' }}>
          <Tooltip title="Dosya ekle (resim, PDF, metin)">
            <IconButton
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              sx={{
                width: 40,
                height: 40,
                flexShrink: 0,
                color: attachment ? modernColors.primary[600] : 'text.secondary',
              }}
            >
              <AttachFileIcon />
            </IconButton>
          </Tooltip>
          <TextField
            multiline
            maxRows={4}
            fullWidth
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Mesajinizi yazin..."
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '16px',
                background: 'rgba(255,255,255,0.95)',
                '&.Mui-focused': {
                  boxShadow: `0 0 0 2px ${modernColors.primary[200]}`,
                },
              },
            }}
          />
          <IconButton
            type="submit"
            disabled={!(input.trim() || attachment) || isLoading}
            sx={{
              width: 48,
              height: 48,
              background: modernColors.gradients.primary,
              color: 'white',
              flexShrink: 0,
              '&:hover': { opacity: 0.9, background: modernColors.gradients.primary },
              '&.Mui-disabled': { background: 'action.disabledBackground', color: 'action.disabled' },
            }}
          >
            <SendIcon />
          </IconButton>
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Enter ile gonder &bull; Shift+Enter ile yeni satir
        </Typography>
      </Box>
    </Box>
  );
};

// --- Empty State ---
interface EmptyStateProps {
  quickActions: typeof QUICK_ACTIONS;
  onAction: (prompt: string) => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({ quickActions, onAction }) => (
  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, py: 4 }}>
    <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.4 }}>
      <Box
        sx={{
          width: 80,
          height: 80,
          borderRadius: '24px',
          background: modernColors.gradients.purple,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 3,
          boxShadow: '0 8px 32px rgba(168, 85, 247, 0.3)',
        }}
      >
        <BotIcon sx={{ fontSize: 48, color: 'white' }} />
      </Box>
    </motion.div>

    <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
      Merhaba! Size nasil yardimci olabilirim?
    </Typography>
    <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center', maxWidth: 400 }}>
      TYT/AYT konularinda sorularinizi sorabilir, konu aciklamasi isteyebilirsiniz.
    </Typography>

    {/* Quick actions — general */}
    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5, maxWidth: 420, width: '100%' }}>
      {quickActions.map((action, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 + i * 0.05 }}
        >
          <Paper
            elevation={0}
            onClick={() => onAction(action.prompt)}
            sx={{
              p: 2,
              borderRadius: '12px',
              cursor: 'pointer',
              border: '1px solid',
              borderColor: 'divider',
              background: 'rgba(255,255,255,0.8)',
              backdropFilter: 'blur(8px)',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              transition: 'all 0.2s',
              '&:hover': {
                borderColor: modernColors.primary[300],
                background: modernColors.primary[50],
                transform: 'translateY(-2px)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
              },
            }}
          >
            {action.icon}
            <Typography variant="body2" fontWeight={500}>{action.text}</Typography>
          </Paper>
        </motion.div>
      ))}
    </Box>

    {/* F20: "Ne soracağımı bilmiyorum" conversation starters */}
    <Typography variant="caption" color="text.secondary" sx={{ mt: 3, mb: 1.5, fontWeight: 600 }}>
      Ne soracağını bilmiyor musun? Bunları dene:
    </Typography>
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, maxWidth: 420, justifyContent: 'center' }}>
      {CONVERSATION_STARTERS.map((starter, i) => (
        <motion.div
          key={`starter-${i}`}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 + i * 0.05 }}
        >
          <Chip
            icon={starter.icon}
            label={starter.text}
            size="small"
            variant="outlined"
            onClick={() => onAction(starter.prompt)}
            sx={{
              borderRadius: '20px',
              borderColor: modernColors.primary[200],
              fontWeight: 500,
              '&:hover': {
                background: modernColors.primary[50],
                borderColor: modernColors.primary[400],
              },
            }}
          />
        </motion.div>
      ))}
    </Box>
  </Box>
);

// --- Message Bubble ---
interface MessageBubbleProps {
  message: ChatMessage;
}

const MessageBubble: React.FC<MessageBubbleProps> = React.memo(({ message }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  const avatarBg = isUser
    ? modernColors.gradients.primary
    : isSystem
      ? modernColors.warning[400]
      : modernColors.gradients.purple;

  const avatarIcon = isUser
    ? <PersonIcon sx={{ fontSize: 18 }} />
    : isSystem
      ? <WarningIcon sx={{ fontSize: 18 }} />
      : <BotIcon sx={{ fontSize: 18 }} />;

  return (
    <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 1.5,
          maxWidth: '75%',
          flexDirection: isUser ? 'row-reverse' : 'row',
        }}
      >
        <Avatar sx={{ width: 36, height: 36, background: avatarBg, flexShrink: 0 }}>
          {avatarIcon}
        </Avatar>

        <Paper
          elevation={0}
          sx={{
            px: 2.5,
            py: 1.5,
            borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            background: isUser
              ? modernColors.gradients.primary
              : isSystem
                ? `${modernColors.warning[50]}`
                : 'rgba(255,255,255,0.9)',
            color: isUser ? 'white' : 'text.primary',
            backdropFilter: !isUser ? 'blur(10px)' : undefined,
            border: !isUser && !isSystem ? '1px solid' : undefined,
            borderColor: !isUser && !isSystem ? 'divider' : undefined,
          }}
        >
          {/* Agent label */}
          {!isUser && !isSystem && message.agent && (
            <Typography variant="caption" sx={{ opacity: 0.7, fontWeight: 600, display: 'block', mb: 0.5 }}>
              AI Asistan
            </Typography>
          )}

          {/* Content */}
          {isUser ? (
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
              {message.content}
            </Typography>
          ) : (
            <Box
              sx={{
                fontSize: '0.875rem',
                lineHeight: 1.7,
                '& p': { m: 0, mb: 1 },
                '& p:last-child': { mb: 0 },
                '& ul, & ol': { pl: 2.5, my: 0.5 },
                '& li': { mb: 0.25 },
                '& h3, & h4': { fontSize: '0.95rem', fontWeight: 600, mt: 1.5, mb: 0.5 },
                '& strong': { fontWeight: 600 },
                '& code': {
                  bgcolor: isSystem ? 'rgba(0,0,0,0.06)' : 'grey.100',
                  px: 0.5,
                  borderRadius: 0.5,
                  fontSize: '0.85em',
                  fontFamily: 'monospace',
                },
                '& pre': {
                  bgcolor: isSystem ? 'rgba(0,0,0,0.06)' : 'grey.100',
                  p: 1.5,
                  borderRadius: 1,
                  overflow: 'auto',
                  '& code': { bgcolor: 'transparent', p: 0 },
                },
                '& blockquote': {
                  borderLeft: '3px solid',
                  borderColor: 'divider',
                  pl: 1.5,
                  ml: 0,
                  fontStyle: 'italic',
                  opacity: 0.85,
                },
              }}
            >
              <ReactMarkdown
                remarkPlugins={[remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  code({ inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter style={oneLight} language={match[1]} PreTag="div" {...props}>
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>{children}</code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </Box>
          )}

          {/* Timestamp */}
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              mt: 1,
              opacity: 0.6,
              color: isUser ? 'rgba(255,255,255,0.8)' : 'text.secondary',
              textAlign: isUser ? 'right' : 'left',
            }}
          >
            {new Date(message.timestamp).toLocaleTimeString('tr-TR', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
});

MessageBubble.displayName = 'MessageBubble';

export default TurkishChatInterface;
