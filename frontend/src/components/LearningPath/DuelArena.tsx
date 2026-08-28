import { Box, Typography, CircularProgress, Chip } from '@mui/material';
import { CheckCircle, Insights } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { DuelQuestion } from './duelReducer';
import modernColors from '../../theme/modern-colors';

interface DuelArenaProps {
  question: DuelQuestion;
  selectedAnswer: string | null;
  isSubmitting: boolean;
  onAnswer: (answer: string) => void;
  opponentAnswered: boolean;
  isBot: boolean;
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring', damping: 20, stiffness: 200 } }
};

export default function DuelArena({
  question,
  selectedAnswer,
  isSubmitting,
  onAnswer,
  opponentAnswered,
  isBot,
}: DuelArenaProps) {
  return (
    <Box sx={{ position: 'relative', width: '100%', maxWidth: 700, mx: 'auto' }}>
      <AnimatePresence>
        {opponentAnswered && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: -20 }}
            style={{ position: 'absolute', top: -15, right: 10, zIndex: 10 }}
          >
            <Chip
              icon={<CheckCircle sx={{ fontSize: 16 }} />}
              label={isBot ? 'Bot hazır' : 'Rakip cevapladı!'}
              size="small"
              sx={{
                fontWeight: 800,
                backgroundColor: modernColors.gradients.sunset,
                color: 'white',
                boxShadow: '0 8px 16px rgba(245,158,11,0.3)',
                border: '1px solid rgba(255,255,255,0.2)',
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          visible: { transition: { staggerChildren: 0.1 } }
        }}
      >
        <motion.div variants={itemVariants}>
          <Box
            sx={{
              p: 4,
              mb: 4,
              borderRadius: 4,
              background: 'linear-gradient(145deg, rgba(255,255,255,0.9), rgba(255,255,255,0.5))',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.8)',
              boxShadow: '0 20px 40px rgba(0,0,0,0.05), inset 0 2px 4px rgba(255,255,255,0.8)',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            {/* Subtle glow effect behind question */}
            <Box sx={{ position: 'absolute', top: -50, right: -50, width: 150, height: 150, background: modernColors.primary[200], filter: 'blur(60px)', opacity: 0.5, borderRadius: '50%' }} />

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
              <Insights sx={{ color: modernColors.primary[500], fontSize: 20 }} />
              <Typography variant="overline" fontWeight={800} sx={{ color: modernColors.primary[600], letterSpacing: 1.2 }}>
                {question.subject}
              </Typography>
            </Box>
            
            <Typography variant="h6" fontWeight={600} sx={{ color: '#1e293b', lineHeight: 1.6, position: 'relative', zIndex: 1 }}>
              {question.content}
            </Typography>
          </Box>
        </motion.div>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {question.options.map((opt) => {
            const isSelected = selectedAnswer === opt.key;
            const isDisabled = !!selectedAnswer || isSubmitting;

            return (
              <motion.div
                variants={itemVariants}
                key={opt.key}
                whileHover={!isDisabled ? { scale: 1.02, x: 5 } : {}}
                whileTap={!isDisabled ? { scale: 0.98 } : {}}
                onClick={() => {
                  if (!isDisabled) onAnswer(opt.key);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  padding: '16px 20px',
                  border: `2px solid ${isSelected ? modernColors.primary[500] : 'rgba(255,255,255,0.8)'}`,
                  borderRadius: '20px',
                  background: isSelected ? modernColors.gradients.primary : 'rgba(255,255,255,0.6)',
                  backdropFilter: 'blur(10px)',
                  cursor: isDisabled ? 'default' : 'pointer',
                  textAlign: 'left',
                  width: '100%',
                  boxShadow: isSelected ? '0 10px 25px rgba(99,102,241,0.4)' : '0 4px 15px rgba(0,0,0,0.03)',
                  opacity: selectedAnswer && !isSelected ? 0.4 : 1,
                  color: isSelected ? 'white' : '#334155',
                  transition: 'background 0.3s ease, opacity 0.3s ease',
                }}
              >
                <Box
                  sx={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 800,
                    fontSize: 16,
                    flexShrink: 0,
                    background: isSelected ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.04)',
                    color: isSelected ? '#fff' : modernColors.primary[600],
                    boxShadow: isSelected ? 'inset 0 2px 4px rgba(255,255,255,0.3)' : 'none'
                  }}
                >
                  {opt.key}
                </Box>
                <Typography variant="body1" sx={{ flex: 1, fontWeight: isSelected ? 700 : 500, fontSize: '1rem' }}>
                  {opt.text}
                </Typography>
                {isSubmitting && isSelected && (
                  <motion.div initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }}>
                    <CircularProgress size={20} sx={{ color: 'white' }} />
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </Box>
      </motion.div>
    </Box>
  );
}
