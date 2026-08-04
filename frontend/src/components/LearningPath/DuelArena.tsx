import { Box, Typography, CircularProgress, Chip } from '@mui/material';
import { CheckCircle } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { DuelQuestion } from './duelReducer';

interface DuelArenaProps {
  question: DuelQuestion;
  selectedAnswer: string | null;
  isSubmitting: boolean;
  onAnswer: (answer: string) => void;
  opponentAnswered: boolean;
  isBot: boolean;
}

export default function DuelArena({
  question,
  selectedAnswer,
  isSubmitting,
  onAnswer,
  opponentAnswered,
  isBot,
}: DuelArenaProps) {
  return (
    <Box>
      <AnimatePresence>
        {opponentAnswered && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Chip
              icon={<CheckCircle sx={{ fontSize: 14 }} />}
              label={isBot ? 'Bot cevapladı' : 'Rakip cevapladı!'}
              size="small"
              sx={{
                mb: 2,
                fontSize: 12,
                fontWeight: 700,
                backgroundColor: 'rgba(245,158,11,0.15)',
                color: '#d97706',
                boxShadow: '0 4px 12px rgba(245,158,11,0.15)',
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <Box
          sx={{
            p: 3,
            mb: 3,
            borderRadius: 4,
            backgroundColor: 'rgba(255,255,255,0.6)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255,255,255,0.8)',
            boxShadow: '0 8px 32px rgba(99,102,241,0.08)',
          }}
        >
          <Chip
            label={question.subject}
            size="small"
            sx={{ mb: 1.5, fontSize: 11, height: 22, fontWeight: 700, backgroundColor: '#e0e7ff', color: '#4f46e5' }}
          />
          <Typography variant="body1" fontWeight={700} sx={{ color: '#1e293b', lineHeight: 1.6 }}>
            {question.content}
          </Typography>
        </Box>
      </motion.div>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {question.options.map((opt, i) => {
          const isSelected = selectedAnswer === opt.key;
          const isDisabled = !!selectedAnswer || isSubmitting;

          return (
            <motion.div
              key={opt.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: i * 0.08, ease: 'easeOut' }}
              whileHover={!isDisabled ? { scale: 1.02, backgroundColor: 'rgba(255,255,255,0.9)' } : {}}
              whileTap={!isDisabled ? { scale: 0.98 } : {}}
              onClick={() => {
                if (!isDisabled) onAnswer(opt.key);
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '14px',
                border: `2px solid ${isSelected ? '#6366f1' : 'rgba(255,255,255,0.6)'}`,
                borderRadius: '16px',
                backgroundColor: isSelected ? 'rgba(99,102,241,0.1)' : 'rgba(255,255,255,0.7)',
                backdropFilter: 'blur(10px)',
                cursor: isDisabled ? 'default' : 'pointer',
                textAlign: 'left',
                width: '100%',
                boxShadow: isSelected ? '0 4px 16px rgba(99,102,241,0.2)' : '0 2px 10px rgba(0,0,0,0.03)',
                opacity: selectedAnswer && !isSelected ? 0.6 : 1,
              }}
            >
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: 14,
                  flexShrink: 0,
                  backgroundColor: isSelected ? '#6366f1' : 'rgba(0,0,0,0.05)',
                  color: isSelected ? '#fff' : 'text.primary',
                  transition: 'all 0.2s',
                }}
              >
                {opt.key}
              </Box>
              <Typography variant="body2" sx={{ flex: 1, fontWeight: 600, color: '#334155', fontSize: '15px' }}>
                {opt.text}
              </Typography>
              {isSubmitting && isSelected && <CircularProgress size={18} sx={{ color: '#6366f1' }} />}
            </motion.div>
          );
        })}
      </Box>
    </Box>
  );
}
