/**
 * ProactiveCoachWidget — Proaktif AI Koçluk
 *
 * Century Tech proaktif müdahale + Squirrel AI davranışsal analiz.
 * FSRS due kartları + weakness-report verilerinden otomatik öneri üretir.
 *
 * Privacy-safe: Kamera/mikrofon YOK, sadece öğrenme verisi.
 * Davranışsal sinyaller: yanlış cevap paterni, oturum süresi, çalışma aralığı.
 */

import { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Typography,
  Chip,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  Psychology,
  Close,
  Replay,
  TrendingDown,
  Timer,
  AutoAwesome,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../ui/GlassCard';
import { ModernButton } from '../ui/ModernButton';
import { apiRequest } from '../../utils/apiHelpers';

interface WeaknessItem {
  topic: string;
  avg_score: number;
  attempts: number;
  trend: 'improving' | 'declining' | 'stable';
  is_weak: boolean;
}

interface CoachSuggestion {
  type: 'review' | 'weakness' | 'burnout' | 'streak';
  title: string;
  message: string;
  icon: React.ReactElement;
  color: string;
  action?: string;
  priority: number; // lower = higher priority
}

interface ProactiveCoachWidgetProps {
  /** Recent wrong answer count (from quiz sessions) */
  recentWrongCount?: number;
  /** Study minutes today */
  studyMinutesToday?: number;
  /** Current streak */
  streak?: number;
  /** FSRS due card count */
  dueCardCount?: number;
  /** Callback when user acts on suggestion */
  onAction?: (type: string) => void;
}

export function ProactiveCoachWidget({
  recentWrongCount = 0,
  studyMinutesToday = 0,
  streak = 0,
  dueCardCount = 0,
  onAction,
}: ProactiveCoachWidgetProps) {
  const [visible, setVisible] = useState(true);
  const [weakTopics, setWeakTopics] = useState<WeaknessItem[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  // Fetch weakness data
  useEffect(() => {
    apiRequest<{ weaknesses: WeaknessItem[] }>('/api/learning-path/weakness-report')
      .then(data => setWeakTopics((data.weaknesses || []).filter(w => w.is_weak)))
      .catch(() => {});
  }, []);

  // Generate suggestions based on behavioral signals
  const suggestions = useMemo(() => {
    const items: CoachSuggestion[] = [];

    // 1. FSRS due cards
    if (dueCardCount > 0) {
      items.push({
        type: 'review',
        title: 'Tekrar Zamanı',
        message: `${dueCardCount} kart tekrar edilmeyi bekliyor. Ebbinghaus unutma eğrisi — bugün tekrar etmezsen yarın %40 daha zor hatırlarsın.`,
        icon: <Replay sx={{ fontSize: 20 }} />,
        color: '#6366f1',
        action: 'review',
        priority: 1,
      });
    }

    // 2. Weak topics declining
    const decliningTopics = weakTopics.filter(w => w.trend === 'declining');
    if (decliningTopics.length > 0) {
      const topic = decliningTopics[0];
      items.push({
        type: 'weakness',
        title: 'Dikkat Gerektiren Konu',
        message: `${topic.topic} konusunda performansın düşüyor (ort. %${topic.avg_score}). 15 dakikalık hızlı bir tekrar büyük fark yaratır.`,
        icon: <TrendingDown sx={{ fontSize: 20 }} />,
        color: '#f59e0b',
        action: 'weakness',
        priority: 2,
      });
    }

    // 3. Burnout detection — too much study without break
    if (studyMinutesToday > 180) {
      items.push({
        type: 'burnout',
        title: 'Mola Zamanı',
        message: `Bugün ${studyMinutesToday} dakika çalıştın — harika! Ama araştırmalar 90 dakikada bir mola vermenin verimliliği %20 artırdığını gösteriyor.`,
        icon: <Timer sx={{ fontSize: 20 }} />,
        color: '#22c55e',
        priority: 3,
      });
    }

    // 4. Streak motivation
    if (streak >= 3 && streak % 5 === 0) {
      items.push({
        type: 'streak',
        title: `${streak} Gün!`,
        message: `${streak} günlük seri — süper tutarlılık! Düzenli çalışma alışkanlığı exam score'u ortalama %15 artırıyor.`,
        icon: <AutoAwesome sx={{ fontSize: 20 }} />,
        color: '#f97316',
        priority: 4,
      });
    }

    // 5. Recent high wrong count → frustration detection
    if (recentWrongCount >= 3) {
      items.push({
        type: 'weakness',
        title: 'Birlikte Çözelim',
        message: `Son sorularda zorlandığını fark ettim. Konuyu birlikte gözden geçirelim — yanlış yapmak öğrenmenin doğal parçası!`,
        icon: <Psychology sx={{ fontSize: 20 }} />,
        color: '#8b5cf6',
        action: 'chat',
        priority: 0, // Highest priority
      });
    }

    return items
      .filter(s => !dismissed.has(s.type + s.title))
      .sort((a, b) => a.priority - b.priority);
  }, [dueCardCount, weakTopics, studyMinutesToday, streak, recentWrongCount, dismissed]);

  const dismissSuggestion = (suggestion: CoachSuggestion) => {
    setDismissed(prev => new Set(prev).add(suggestion.type + suggestion.title));
  };

  if (!visible || suggestions.length === 0) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
      >
        <GlassCard glassIntensity="light" sx={{ mb: 2, position: 'relative' }}>
          <IconButton
            size="small"
            onClick={() => setVisible(false)}
            sx={{ position: 'absolute', top: 8, right: 8 }}
          >
            <Close sx={{ fontSize: 16 }} />
          </IconButton>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
            <Psychology sx={{ fontSize: 22, color: '#6366f1' }} />
            <Typography variant="subtitle2" fontWeight={700}>
              AI Koç Önerileri
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {suggestions.slice(0, 2).map((s) => (
              <Collapse key={s.type + s.title} in>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: `${s.color}08`,
                    borderLeft: `3px solid ${s.color}`,
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 1,
                  }}
                >
                  <Box sx={{ color: s.color, mt: 0.25, flexShrink: 0 }}>
                    {s.icon}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" fontWeight={700} sx={{ mb: 0.25, color: s.color }}>
                      {s.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: s.action ? 1 : 0 }}>
                      {s.message}
                    </Typography>
                    {s.action && (
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <ModernButton
                          variant="glass"
                          onClick={() => {
                            onAction?.(s.action!);
                            dismissSuggestion(s);
                          }}
                          sx={{ height: 28, fontSize: 11, px: 1.5 }}
                        >
                          Hadi Başlayalım
                        </ModernButton>
                        <Chip
                          label="Şimdi değil"
                          size="small"
                          onClick={() => dismissSuggestion(s)}
                          sx={{ cursor: 'pointer', fontSize: 10, height: 22 }}
                        />
                      </Box>
                    )}
                  </Box>
                </Box>
              </Collapse>
            ))}
          </Box>
        </GlassCard>
      </motion.div>
    </AnimatePresence>
  );
}

export default ProactiveCoachWidget;
