/**
 * ProductiveFailureFlow — "Çöz-Sonra-Gör" modu (Brilliant productive failure)
 *
 * Akış:
 * 1. Pretest: Konu öğretilmeden ÖNCE 2-3 soru (keşif denemesi)
 * 2. Öğren: Yanlış yapılan konulara kaynak göster
 * 3. Posttest: Aynı soruları tekrar → gelişim göster
 *
 * Bilimsel temel: Kapur 2016 — productive failure, desirable difficulty
 * Growth mindset: Yanlış = "öğrenme fırsatı" çerçeveleme
 */

import { useState, useMemo } from 'react';
import { Box, Typography, Chip, LinearProgress } from '@mui/material';
import { TrendingUp, School, Replay, CheckCircle, Cancel } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../ui/GlassCard';
import { ModernButton } from '../ui/ModernButton';
import { QuizInterface, type QuizConfig } from '../Quiz/QuizInterface';
import modernColors from '../../theme/modern-colors';

type FlowPhase = 'pretest' | 'learn' | 'posttest' | 'results';

interface ProductiveFailureFlowProps {
  /** Quiz config with questions */
  config: QuizConfig;
  /** Node title for context */
  nodeTitle: string;
  /** Callback when flow completes */
  onComplete?: (improvement: number) => void;
  /** Exit handler */
  onExit?: () => void;
}

interface PhaseResult {
  percentage: number;
  correctCount: number;
  incorrectCount: number;
}

export function ProductiveFailureFlow({
  config,
  nodeTitle,
  onComplete,
  onExit,
}: ProductiveFailureFlowProps) {
  const [phase, setPhase] = useState<FlowPhase>('pretest');
  const [pretestResult, setPretestResult] = useState<PhaseResult | null>(null);
  const [posttestResult, setPosttestResult] = useState<PhaseResult | null>(null);

  // Build quiz config for each phase
  const pretestConfig = useMemo((): QuizConfig => ({
    ...config,
    title: `${nodeTitle} — Önce Dene`,
    description: 'Bu konuyu bilmeden çözmeyi deneyin. Yanlış yapmak normaldir!',
    immediateFeedback: true,
    allowReview: false,
    passingScore: 0, // No passing requirement for pretest
  }), [config, nodeTitle]);

  const posttestConfig = useMemo((): QuizConfig => ({
    ...config,
    title: `${nodeTitle} — Tekrar Dene`,
    description: 'Öğrendiklerinizle tekrar deneyin!',
    immediateFeedback: true,
    allowReview: true,
    showCorrectAnswers: true,
  }), [config, nodeTitle]);

  const improvement = useMemo(() => {
    if (!pretestResult || !posttestResult) return 0;
    return posttestResult.percentage - pretestResult.percentage;
  }, [pretestResult, posttestResult]);

  const handlePretestComplete = (results: { percentage: number; correctCount: number; incorrectCount: number }) => {
    setPretestResult({
      percentage: results.percentage,
      correctCount: results.correctCount,
      incorrectCount: results.incorrectCount,
    });
    setPhase('learn');
  };

  const handlePosttestComplete = (results: { percentage: number; correctCount: number; incorrectCount: number }) => {
    setPosttestResult({
      percentage: results.percentage,
      correctCount: results.correctCount,
      incorrectCount: results.incorrectCount,
    });
    setPhase('results');
    onComplete?.(results.percentage - (pretestResult?.percentage || 0));
  };

  return (
    <Box>
      {/* Phase indicator */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        {(['pretest', 'learn', 'posttest', 'results'] as FlowPhase[]).map((p, i) => {
          const labels = { pretest: 'Dene', learn: 'Öğren', posttest: 'Tekrar', results: 'Sonuç' };
          const isDone = ['pretest', 'learn', 'posttest', 'results'].indexOf(phase) > i;
          const isCurrent = phase === p;
          return (
            <Box key={p} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Chip
                label={`${i + 1}. ${labels[p]}`}
                size="small"
                sx={{
                  fontWeight: 700,
                  fontSize: 11,
                  backgroundColor: isCurrent ? '#6366f120' : isDone ? '#22c55e15' : 'rgba(0,0,0,0.04)',
                  color: isCurrent ? '#6366f1' : isDone ? '#22c55e' : '#94a3b8',
                  borderColor: isCurrent ? '#6366f1' : 'transparent',
                  borderWidth: 1.5,
                  borderStyle: 'solid',
                }}
              />
              {i < 3 && <Box sx={{ width: 16, height: 2, bgcolor: isDone ? '#22c55e' : '#e2e8f0', borderRadius: 1 }} />}
            </Box>
          );
        })}
      </Box>

      <AnimatePresence mode="wait">
        {/* Phase 1: Pretest */}
        {phase === 'pretest' && (
          <motion.div
            key="pretest"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
          >
            <GlassCard glassIntensity="light" sx={{ mb: 2, p: 2, backgroundColor: '#6366f108' }}>
              <Typography variant="body2" fontWeight={600} sx={{ color: '#6366f1' }}>
                Bu konuyu henüz öğrenmediniz — bu normal! Önce ne kadar bildiğinizi görelim.
              </Typography>
            </GlassCard>
            <QuizInterface
              config={pretestConfig}
              onSubmit={handlePretestComplete}
              onExit={onExit}
            />
          </motion.div>
        )}

        {/* Phase 2: Learn */}
        {phase === 'learn' && pretestResult && (
          <motion.div
            key="learn"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
          >
            <GlassCard glassIntensity="medium" elevated>
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <School sx={{ fontSize: 48, color: '#6366f1', mb: 1.5 }} />
                <Typography variant="h5" fontWeight={800} sx={{ mb: 1 }}>
                  Öğrenme Zamanı!
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2.5 }}>
                  Pretest sonucunuz: <strong>%{pretestResult.percentage}</strong>
                  {' '}({pretestResult.correctCount}/{pretestResult.correctCount + pretestResult.incorrectCount} doğru)
                </Typography>

                {pretestResult.incorrectCount > 0 && (
                  <GlassCard glassIntensity="light" sx={{ mb: 3, p: 2, textAlign: 'left' }}>
                    <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1, color: '#f59e0b' }}>
                      Eksik kalan noktalar:
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {pretestResult.incorrectCount} soruda hata yaptınız.
                      Şimdi konuyu öğrenip tekrar deneyin — bu sefer çok daha iyi olacak!
                    </Typography>
                  </GlassCard>
                )}

                <Typography variant="body2" color="text.secondary" sx={{ mb: 3, fontStyle: 'italic' }}>
                  Konuyu öğrendikten sonra aynı soruları tekrar çözeceksiniz.
                  Araştırmalar gösteriyor ki bu yöntem doğrudan öğretimden %40 daha etkili!
                </Typography>

                <ModernButton
                  variant="gradient"
                  gradient={modernColors.gradients.primary}
                  icon={<Replay />}
                  onClick={() => setPhase('posttest')}
                >
                  Öğrendim, Tekrar Deneyelim!
                </ModernButton>
              </Box>
            </GlassCard>
          </motion.div>
        )}

        {/* Phase 3: Posttest */}
        {phase === 'posttest' && (
          <motion.div
            key="posttest"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
          >
            <GlassCard glassIntensity="light" sx={{ mb: 2, p: 2, backgroundColor: '#22c55e08' }}>
              <Typography variant="body2" fontWeight={600} sx={{ color: '#22c55e' }}>
                Şimdi öğrendiklerinizle tekrar deneyin! Gelişiminizi ölçeceğiz.
              </Typography>
            </GlassCard>
            <QuizInterface
              config={posttestConfig}
              onSubmit={handlePosttestComplete}
              onExit={onExit}
            />
          </motion.div>
        )}

        {/* Phase 4: Results — Pretest vs Posttest comparison */}
        {phase === 'results' && pretestResult && posttestResult && (
          <motion.div
            key="results"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <GlassCard glassIntensity="medium" elevated>
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <TrendingUp sx={{ fontSize: 48, color: improvement > 0 ? '#22c55e' : '#f59e0b', mb: 1 }} />
                <Typography variant="h5" fontWeight={800} sx={{ mb: 0.5 }}>
                  {improvement > 0 ? 'Harika Gelişim!' : 'İyi Deneme!'}
                </Typography>

                {/* Comparison bars */}
                <Box sx={{ maxWidth: 360, mx: 'auto', my: 3 }}>
                  {/* Pretest */}
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" fontWeight={600} color="text.secondary">
                        Pretest (Önce)
                      </Typography>
                      <Typography variant="caption" fontWeight={700}>
                        %{pretestResult.percentage}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={pretestResult.percentage}
                      sx={{
                        height: 10,
                        borderRadius: 5,
                        bgcolor: '#fee2e2',
                        '& .MuiLinearProgress-bar': { bgcolor: '#ef4444', borderRadius: 5 },
                      }}
                    />
                  </Box>

                  {/* Posttest */}
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" fontWeight={600} color="text.secondary">
                        Posttest (Sonra)
                      </Typography>
                      <Typography variant="caption" fontWeight={700}>
                        %{posttestResult.percentage}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={posttestResult.percentage}
                      sx={{
                        height: 10,
                        borderRadius: 5,
                        bgcolor: '#dcfce7',
                        '& .MuiLinearProgress-bar': { bgcolor: '#22c55e', borderRadius: 5 },
                      }}
                    />
                  </Box>

                  {/* Improvement */}
                  <Chip
                    icon={improvement > 0 ? <TrendingUp sx={{ fontSize: 16 }} /> : undefined}
                    label={improvement > 0 ? `+${improvement} puan gelişim` : 'Aynı seviye'}
                    sx={{
                      fontWeight: 700,
                      fontSize: 13,
                      backgroundColor: improvement > 0 ? '#22c55e15' : '#f59e0b15',
                      color: improvement > 0 ? '#22c55e' : '#f59e0b',
                    }}
                  />
                </Box>

                {/* Per-question comparison */}
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mb: 3 }}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <Cancel sx={{ fontSize: 16, color: '#ef4444' }} />
                      <Typography variant="caption" fontWeight={600}>Pretest</Typography>
                    </Box>
                    <Typography variant="h6" fontWeight={800}>
                      {pretestResult.correctCount}/{pretestResult.correctCount + pretestResult.incorrectCount}
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <CheckCircle sx={{ fontSize: 16, color: '#22c55e' }} />
                      <Typography variant="caption" fontWeight={600}>Posttest</Typography>
                    </Box>
                    <Typography variant="h6" fontWeight={800}>
                      {posttestResult.correctCount}/{posttestResult.correctCount + posttestResult.incorrectCount}
                    </Typography>
                  </Box>
                </Box>

                <ModernButton
                  variant="gradient"
                  gradient={modernColors.gradients.primary}
                  onClick={onExit}
                >
                  Devam Et
                </ModernButton>
              </Box>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
}

export default ProductiveFailureFlow;
