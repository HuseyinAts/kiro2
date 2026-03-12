/**
 * DuelMode — 1v1 Düello Modu (Elendin rekabetçi model)
 *
 * Frontend-only implementation with AI bot opponent.
 * When backend WS endpoint is ready, swap bot logic for real-time sync.
 *
 * SDT ilişkilenirlik: g=1.776 (meta-analysis)
 * Rekabetçi zorluklar: %30 performans iyileşmesi
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Chip,
  Avatar,
} from '@mui/material';
import {
  EmojiEvents,
  Person,
  SmartToy,
  Timer,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../ui/GlassCard';
import { ModernButton } from '../ui/ModernButton';
import type { Question } from '../Quiz/QuizInterface';
import modernColors from '../../theme/modern-colors';

type DuelPhase = 'matching' | 'playing' | 'results';

interface DuelModeProps {
  questions: Question[];
  /** Subject for context */
  subject: string;
  onComplete?: (won: boolean, playerScore: number) => void;
  onExit?: () => void;
}

interface PlayerState {
  score: number;
  answeredCount: number;
  correctCount: number;
}

export function DuelMode({ questions, subject, onComplete, onExit }: DuelModeProps) {
  const [phase, setPhase] = useState<DuelPhase>('matching');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [player, setPlayer] = useState<PlayerState>({ score: 0, answeredCount: 0, correctCount: 0 });
  const [bot, setBot] = useState<PlayerState>({ score: 0, answeredCount: 0, correctCount: 0 });
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [timeLeft, setTimeLeft] = useState(15); // 15s per question
  const botTimerRef = useRef<ReturnType<typeof setTimeout>>();

  const currentQuestion = questions[currentIndex];
  const totalQuestions = questions.length;

  // Matching phase — simulate finding opponent
  useEffect(() => {
    if (phase !== 'matching') return;
    const timer = setTimeout(() => setPhase('playing'), 2500);
    return () => clearTimeout(timer);
  }, [phase]);

  // Question timer
  useEffect(() => {
    if (phase !== 'playing' || showFeedback) return;
    if (timeLeft <= 0) {
      handleAnswer(null); // Time's up
      return;
    }
    const timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [phase, timeLeft, showFeedback]);

  // Bot answers with delay (simulates opponent)
  useEffect(() => {
    if (phase !== 'playing' || showFeedback) return;

    // Bot answers 2-8 seconds after question appears
    const delay = 2000 + Math.random() * 6000;
    botTimerRef.current = setTimeout(() => {
      // Bot correctness: ~65% (slight challenge but beatable)
      const isCorrect = Math.random() < 0.65;
      setBot(prev => ({
        score: prev.score + (isCorrect ? 10 : 0),
        answeredCount: prev.answeredCount + 1,
        correctCount: prev.correctCount + (isCorrect ? 1 : 0),
      }));
    }, delay);

    return () => {
      if (botTimerRef.current) clearTimeout(botTimerRef.current);
    };
  }, [currentIndex, phase, showFeedback]);

  const handleAnswer = useCallback((answer: string | null) => {
    if (showFeedback) return;

    setSelectedAnswer(answer);
    const isCorrect = answer === currentQuestion?.correctAnswer;

    setPlayer(prev => ({
      score: prev.score + (isCorrect ? 10 : 0),
      answeredCount: prev.answeredCount + 1,
      correctCount: prev.correctCount + (isCorrect ? 1 : 0),
    }));

    setShowFeedback(true);

    // Move to next question after feedback
    setTimeout(() => {
      if (currentIndex < totalQuestions - 1) {
        setCurrentIndex(prev => prev + 1);
        setSelectedAnswer(null);
        setShowFeedback(false);
        setTimeLeft(15);
      } else {
        setPhase('results');
      }
    }, 1500);
  }, [showFeedback, currentQuestion, currentIndex, totalQuestions]);

  // Matching screen
  if (phase === 'matching') {
    return (
      <GlassCard glassIntensity="medium" elevated>
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <SmartToy sx={{ fontSize: 64, color: '#6366f1' }} />
          </motion.div>
          <Typography variant="h5" fontWeight={800} sx={{ mt: 2, mb: 1 }}>
            Rakip Aranıyor...
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {subject} konusunda senin seviyende bir rakip eşleştiriliyor
          </Typography>
          <LinearProgress sx={{ maxWidth: 200, mx: 'auto', borderRadius: 2 }} />
        </Box>
      </GlassCard>
    );
  }

  // Trigger callback when results phase is reached (NOT in render body)
  const won = player.score > bot.score;
  useEffect(() => {
    if (phase === 'results') {
      onComplete?.(won, player.score);
    }
  }, [phase]); // eslint-disable-line react-hooks/exhaustive-deps

  // Results screen
  if (phase === 'results') {
    const tied = player.score === bot.score;

    return (
      <GlassCard glassIntensity="medium" elevated>
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <EmojiEvents sx={{ fontSize: 56, color: won ? '#f59e0b' : '#94a3b8', mb: 1 }} />
          <Typography variant="h4" fontWeight={900} sx={{ mb: 0.5, color: won ? '#22c55e' : tied ? '#f59e0b' : '#ef4444' }}>
            {won ? 'Kazandın!' : tied ? 'Berabere!' : 'Kaybettin'}
          </Typography>

          {/* Score comparison */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 4, my: 3 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: '#6366f1', width: 48, height: 48, mx: 'auto', mb: 1 }}>
                <Person />
              </Avatar>
              <Typography variant="h5" fontWeight={800}>{player.score}</Typography>
              <Typography variant="caption" color="text.secondary">
                {player.correctCount}/{totalQuestions} doğru
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="h6" fontWeight={700} color="text.secondary">VS</Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: '#ef4444', width: 48, height: 48, mx: 'auto', mb: 1 }}>
                <SmartToy />
              </Avatar>
              <Typography variant="h5" fontWeight={800}>{bot.score}</Typography>
              <Typography variant="caption" color="text.secondary">
                {bot.correctCount}/{totalQuestions} doğru
              </Typography>
            </Box>
          </Box>

          <Chip
            label={won ? '+30 puan' : '+10 puan'}
            sx={{
              fontWeight: 700,
              fontSize: 13,
              bgcolor: won ? '#22c55e15' : '#f59e0b15',
              color: won ? '#22c55e' : '#f59e0b',
              mb: 3,
            }}
          />

          <Box sx={{ display: 'flex', gap: 1.5, justifyContent: 'center' }}>
            <ModernButton variant="gradient" gradient={modernColors.gradients.primary} onClick={onExit}>
              Kapat
            </ModernButton>
          </Box>
        </Box>
      </GlassCard>
    );
  }

  // Playing screen
  return (
    <Box>
      {/* Score header */}
      <GlassCard glassIntensity="light" sx={{ mb: 2, p: 1.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ bgcolor: '#6366f1', width: 32, height: 32 }}><Person sx={{ fontSize: 18 }} /></Avatar>
            <Typography variant="body2" fontWeight={700}>{player.score}</Typography>
          </Box>
          <Chip
            icon={<Timer sx={{ fontSize: 14 }} />}
            label={`${timeLeft}s`}
            size="small"
            color={timeLeft <= 5 ? 'error' : 'default'}
            sx={{ fontWeight: 700 }}
          />
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" fontWeight={700}>{bot.score}</Typography>
            <Avatar sx={{ bgcolor: '#ef4444', width: 32, height: 32 }}><SmartToy sx={{ fontSize: 18 }} /></Avatar>
          </Box>
        </Box>
        <LinearProgress
          variant="determinate"
          value={((currentIndex + 1) / totalQuestions) * 100}
          sx={{ mt: 1, height: 4, borderRadius: 2 }}
        />
      </GlassCard>

      {/* Question */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentIndex}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.2 }}
        >
          <GlassCard glassIntensity="medium" sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ mb: 1, display: 'block' }}>
              Soru {currentIndex + 1}/{totalQuestions}
            </Typography>
            <Typography variant="body1" fontWeight={600} sx={{ mb: 2 }}>
              {currentQuestion.question}
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {currentQuestion.options?.map((option, i) => {
                const isSelected = selectedAnswer === option;
                const isCorrect = option === currentQuestion.correctAnswer;
                const showResult = showFeedback;

                return (
                  <Box
                    key={i}
                    onClick={() => !showFeedback && handleAnswer(option)}
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      cursor: showFeedback ? 'default' : 'pointer',
                      borderWidth: 2,
                      borderStyle: 'solid',
                      borderColor: showResult
                        ? isCorrect ? '#22c55e' : isSelected ? '#ef4444' : 'transparent'
                        : isSelected ? '#6366f1' : 'rgba(0,0,0,0.08)',
                      bgcolor: showResult
                        ? isCorrect ? '#22c55e10' : isSelected ? '#ef444410' : 'transparent'
                        : isSelected ? '#6366f110' : 'transparent',
                      transition: 'all 0.2s',
                      '&:hover': !showFeedback ? { bgcolor: '#6366f108', borderColor: '#6366f1' } : {},
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    {showResult && isCorrect && <CheckCircle sx={{ fontSize: 18, color: '#22c55e' }} />}
                    {showResult && isSelected && !isCorrect && <Cancel sx={{ fontSize: 18, color: '#ef4444' }} />}
                    <Typography variant="body2" fontWeight={isSelected ? 700 : 400}>
                      {option}
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          </GlassCard>
        </motion.div>
      </AnimatePresence>
    </Box>
  );
}

export default DuelMode;
