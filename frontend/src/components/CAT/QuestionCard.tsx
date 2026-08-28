import { useState, useEffect, useRef } from 'react';
import {
  Box, Typography, Button, LinearProgress,
  Chip, Stack, useTheme
} from '@mui/material';
import { CheckCircle, Cancel, HelpOutline } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../ui/GlassCard';
import modernColors from '../../theme/modern-colors';

interface QuestionCardProps {
  stem: string;
  options: Record<string, string>;
  onAnswer: (key: string, ms: number) => void;
  disabled?: boolean;
  feedback?: { selected: string; is_correct: boolean; correct_option: string | null } | null;
  questionNumber?: number;
  totalQuestions?: number;
  theta?: number;
  phase?: string;
}

const cardVariants = {
  hidden: { opacity: 0, y: 30, scale: 0.98 },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1, 
    transition: { 
      type: 'spring', 
      damping: 25, 
      stiffness: 300,
      staggerChildren: 0.1 
    } 
  },
  exit: { opacity: 0, scale: 0.95, transition: { duration: 0.2 } }
};

const childVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.4 } }
};

export function QuestionCard({
  stem, options, onAnswer, disabled = false,
  feedback, questionNumber, totalQuestions, theta, phase,
}: QuestionCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const startTime = useRef(Date.now());
  const theme = useTheme();

  useEffect(() => {
    setSelected(null);
    startTime.current = Date.now();
  }, [stem]);

  const handleSelect = (key: string) => {
    if (disabled || selected) return;
    setSelected(key);
    onAnswer(key, Date.now() - startTime.current);
  };

  const getColor = (key: string) => {
    if (!feedback) return selected === key ? modernColors.primary[500] : 'transparent';
    if (key === feedback.correct_option) return modernColors.success[500];
    if (key === feedback.selected && !feedback.is_correct) return modernColors.error[500];
    return 'transparent';
  };

  const getTextColor = (key: string) => {
    if (!feedback && selected === key) return '#fff';
    if (feedback && (key === feedback.correct_option || (key === feedback.selected && !feedback.is_correct))) return '#fff';
    return theme.palette.text.primary;
  };

  const progress = totalQuestions && questionNumber ? (questionNumber / totalQuestions) * 100 : 0;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={stem}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
        style={{ width: '100%', maxWidth: 800, margin: '0 auto' }}
      >
        <GlassCard 
          glassIntensity="medium" 
          elevated 
          sx={{ p: { xs: 3, md: 5 }, borderRadius: 4, overflow: 'hidden', position: 'relative' }}
        >
          {/* Top Progress Bar */}
          {totalQuestions && (
            <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0 }}>
              <LinearProgress 
                variant="determinate" 
                value={progress} 
                sx={{ 
                  height: 4, 
                  backgroundColor: 'rgba(255,255,255,0.1)',
                  '& .MuiLinearProgress-bar': {
                    background: modernColors.gradients.primary
                  }
                }} 
              />
            </Box>
          )}

          <motion.div variants={childVariants}>
            {questionNumber && (
              <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3} mt={1}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box 
                    sx={{ 
                      width: 32, height: 32, borderRadius: '50%', 
                      background: modernColors.gradients.primary,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: 'white', fontWeight: 800, fontSize: '0.9rem'
                    }}
                  >
                    {questionNumber}
                  </Box>
                  <Typography variant="subtitle2" color="text.secondary" fontWeight={600}>
                    SORU
                  </Typography>
                </Box>

                <Stack direction="row" spacing={1.5}>
                  {theta !== undefined && (
                    <Chip 
                      size="small" 
                      label={`Yetenek (θ): ${theta.toFixed(2)}`} 
                      sx={{ background: 'rgba(255,255,255,0.1)', color: 'white', fontWeight: 600, border: '1px solid rgba(255,255,255,0.2)' }} 
                    />
                  )}
                  {phase && (
                    <Chip 
                      size="small"
                      label={phase === 'warm_up' ? '🔥 Kalibrasyon' : '🎯 Adaptif Test'}
                      sx={{ 
                        background: phase === 'warm_up' ? modernColors.gradients.sunset : modernColors.gradients.ocean, 
                        color: 'white', fontWeight: 600 
                      }}
                    />
                  )}
                </Stack>
              </Stack>
            )}

            <Typography 
              variant="h6" 
              fontWeight={500} 
              mb={4} 
              sx={{ 
                lineHeight: 1.7, 
                color: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.95)' : 'rgba(0,0,0,0.85)',
                fontSize: { xs: '1.1rem', md: '1.25rem' }
              }}
            >
              {stem}
            </Typography>
          </motion.div>

          <Stack spacing={2}>
            {Object.entries(options).map(([key, text], index) => {
              const bgColor = getColor(key);
              const txtColor = getTextColor(key);
              const isSelected = selected === key || feedback?.selected === key;
              const isCorrect = feedback?.correct_option === key;
              const isWrong = feedback?.selected === key && !feedback.is_correct;

              return (
                <motion.div variants={childVariants} key={key} custom={index}>
                  <Button
                    onClick={() => handleSelect(key)}
                    disabled={disabled || !!selected}
                    fullWidth
                    sx={{
                      justifyContent: 'flex-start',
                      textAlign: 'left',
                      py: 2, px: 3,
                      borderRadius: 3,
                      textTransform: 'none',
                      backgroundColor: bgColor,
                      color: txtColor,
                      border: `1px solid ${isSelected || isCorrect ? bgColor : 'rgba(156, 163, 175, 0.3)'}`,
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      '&:hover': {
                        backgroundColor: !selected ? 'rgba(255,255,255,0.05)' : bgColor,
                        borderColor: !selected ? modernColors.primary[400] : bgColor,
                        transform: !selected ? 'translateY(-2px)' : 'none',
                        boxShadow: !selected ? '0 10px 20px -10px rgba(0,0,0,0.2)' : 'none'
                      },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <Box 
                        sx={{ 
                          width: 32, height: 32, borderRadius: 2, 
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          backgroundColor: isSelected || isCorrect ? 'rgba(255,255,255,0.2)' : 'rgba(156, 163, 175, 0.15)',
                          color: 'inherit',
                          fontWeight: 700, mr: 2, flexShrink: 0
                        }}
                      >
                        {key}
                      </Box>
                      <Typography variant="body1" fontWeight={isSelected || isCorrect ? 600 : 400} sx={{ flexGrow: 1 }}>
                        {text}
                      </Typography>
                      
                      {/* Icons for feedback */}
                      {feedback && (
                        <Box sx={{ ml: 2, display: 'flex', alignItems: 'center' }}>
                          {isCorrect && (
                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring' }}>
                              <CheckCircle sx={{ color: '#fff', fontSize: 28 }} />
                            </motion.div>
                          )}
                          {isWrong && (
                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring' }}>
                              <Cancel sx={{ color: '#fff', fontSize: 28 }} />
                            </motion.div>
                          )}
                        </Box>
                      )}
                    </Box>
                  </Button>
                </motion.div>
              );
            })}
          </Stack>

          <AnimatePresence>
            {feedback && (
              <motion.div
                initial={{ opacity: 0, height: 0, y: 20 }}
                animate={{ opacity: 1, height: 'auto', y: 0 }}
                transition={{ type: 'spring', damping: 20, stiffness: 200, delay: 0.3 }}
              >
                <Box 
                  mt={4} p={3} borderRadius={3}
                  sx={{ 
                    background: feedback.is_correct ? modernColors.gradients.success : modernColors.gradients.fire,
                    color: 'white',
                    boxShadow: '0 10px 30px -10px rgba(0,0,0,0.3)',
                    display: 'flex', alignItems: 'flex-start', gap: 2
                  }}
                >
                  {feedback.is_correct ? <CheckCircle fontSize="large" /> : <HelpOutline fontSize="large" />}
                  <Box>
                    <Typography variant="h6" fontWeight={800} mb={0.5}>
                      {feedback.is_correct ? 'Harika İş!' : 'Gözden Kaçan Bir Şeyler Var'}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      {feedback.is_correct
                        ? 'Doğru cevabı buldun. Yapay zeka motorumuz yetenek seviyeni (Theta) buna göre güncelledi.'
                        : `Doğru cevap ${feedback.correct_option} olmalıydı. İlgili konuyu tekrar etmeni öneririz.`}
                    </Typography>
                  </Box>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </GlassCard>
      </motion.div>
    </AnimatePresence>
  );
}
