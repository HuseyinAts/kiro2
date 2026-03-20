/**
 * AdaptiveFeedbackPanel — Post-quiz feedback with weakness detection + path adaptation
 *
 * Shown after quiz completion:
 * - Score summary
 * - Weak topics detected (from /weakness-report)
 * - Suggested extra resources for weak topics
 * - Path adaptation notification
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Warning,
  CheckCircle,
  TrendingDown,
  TrendingUp,
  AutoAwesome,
  Close,
} from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';
import { ModernButton } from '../ui/ModernButton';
import { apiRequest } from '../../utils/apiHelpers';
import modernColors from '../../theme/modern-colors';

interface WeaknessItem {
  topic: string;
  avg_score: number;
  attempts: number;
  trend: 'improving' | 'declining' | 'stable';
  is_weak: boolean;
}

interface AdaptiveFeedbackPanelProps {
  quizScore: number;
  totalQuestions: number;
  correctCount: number;
  passed: boolean;
  onClose: () => void;
  onAdaptPath?: () => void;
}

export function AdaptiveFeedbackPanel({
  quizScore: _quizScore,
  totalQuestions,
  correctCount,
  passed,
  onClose,
  onAdaptPath,
}: AdaptiveFeedbackPanelProps) {
  const [weaknesses, setWeaknesses] = useState<WeaknessItem[]>([]);
  const [isAdapting, setIsAdapting] = useState(false);
  const [adapted, setAdapted] = useState(false);

  useEffect(() => {
    apiRequest<{ weaknesses: WeaknessItem[] }>('/api/learning-path/weakness-report')
      .then(data => setWeaknesses((data.weaknesses || []).filter(w => w.is_weak)))
      .catch(() => {});
  }, []);

  const handleAdapt = async () => {
    setIsAdapting(true);
    try {
      // Delegate adaptation to parent — parent has studentId + path context
      // Parent's onAdaptPath calls reload() which re-fetches the adapted path
      onAdaptPath?.();
      setAdapted(true);
    } catch {
      // Adaptation not critical
    } finally {
      setIsAdapting(false);
    }
  };

  const percentage = totalQuestions > 0 ? Math.round((correctCount / totalQuestions) * 100) : 0;

  return (
    <GlassCard glassIntensity="medium" elevated sx={{ position: 'relative' }}>
      <ModernButton
        variant="glass"
        icon={<Close />}
        onClick={onClose}
        sx={{ position: 'absolute', top: 12, right: 12, minWidth: 'auto', p: 0.5 }}
      />

      {/* Score Summary */}
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        {passed ? (
          <CheckCircle sx={{ fontSize: 48, color: '#22c55e', mb: 1 }} />
        ) : (
          <Warning sx={{ fontSize: 48, color: '#f59e0b', mb: 1 }} />
        )}
        <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
          {passed ? 'Tebrikler!' : 'Devam Et!'}
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 900, color: passed ? '#22c55e' : '#f59e0b' }}>
          {percentage}%
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {correctCount}/{totalQuestions} doğru
        </Typography>
      </Box>

      {/* Weakness Report */}
      {weaknesses.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5, display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TrendingDown sx={{ color: '#ef4444', fontSize: 18 }} />
            Güçlendirilmesi Gereken Konular
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {weaknesses.slice(0, 4).map((w) => (
              <Box key={w.topic} sx={{ p: 1.5, borderRadius: 1.5, backgroundColor: 'rgba(239,68,68,0.04)' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                  <Typography variant="body2" fontWeight={600}>{w.topic}</Typography>
                  <Chip
                    size="small"
                    icon={w.trend === 'improving' ? <TrendingUp sx={{ fontSize: 14 }} /> : undefined}
                    label={w.trend === 'improving' ? 'İyileşiyor' : w.trend === 'declining' ? 'Kötüleşiyor' : 'Sabit'}
                    sx={{
                      height: 20,
                      fontSize: 10,
                      fontWeight: 700,
                      color: w.trend === 'improving' ? '#22c55e' : w.trend === 'declining' ? '#ef4444' : '#94a3b8',
                      backgroundColor: w.trend === 'improving' ? '#22c55e10' : w.trend === 'declining' ? '#ef444410' : '#94a3b810',
                    }}
                  />
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={w.avg_score}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    bgcolor: 'rgba(239,68,68,0.1)',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: w.avg_score < 40 ? '#ef4444' : '#f59e0b',
                      borderRadius: 3,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.25 }}>
                  Ort. %{w.avg_score} · {w.attempts} deneme
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {/* Adapt Path CTA */}
      {!passed && weaknesses.length > 0 && !adapted && (
        <ModernButton
          variant="gradient"
          gradient={modernColors.gradients.primary}
          icon={<AutoAwesome />}
          onClick={handleAdapt}
          disabled={isAdapting}
          fullWidth
        >
          {isAdapting ? 'Yol uyarlanıyor...' : 'Öğrenme Yolumu Güncelle'}
        </ModernButton>
      )}

      {adapted && (
        <Box sx={{ textAlign: 'center', p: 1.5, borderRadius: 2, backgroundColor: '#22c55e10' }}>
          <Typography variant="body2" sx={{ fontWeight: 600, color: '#22c55e' }}>
            Öğrenme yolunuz zayıf noktalarınıza göre güncellendi!
          </Typography>
        </Box>
      )}
    </GlassCard>
  );
}

export default AdaptiveFeedbackPanel;
