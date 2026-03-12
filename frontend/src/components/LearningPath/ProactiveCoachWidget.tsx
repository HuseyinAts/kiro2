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
  CircularProgress,
} from '@mui/material';
import {
  Psychology,
  Close,
  Replay,
  TrendingDown,
  Timer,
  AutoAwesome,
  WarningAmber,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../ui/GlassCard';
import { ModernButton } from '../ui/ModernButton';
import { apiRequest } from '../../utils/apiHelpers';

// ---------------------------------------------------------------------------
// Types matching backend Pydantic schemas
// ---------------------------------------------------------------------------

interface WeaknessItem {
  topic: string;
  avg_score: number;
  attempts: number;
  trend: 'improving' | 'declining' | 'stable';
  is_weak: boolean;
}

/** Matches backend CoachingSuggestionItem */
interface ApiCoachingSuggestion {
  id: string;
  type: string;
  title: string;
  message: string;
  priority: number;
  action_url: string;
}

/** Matches backend BurnoutCheckResponse */
interface BurnoutCheckResponse {
  is_at_risk: boolean;
  signals: string[];
  recommendation: string;
}

/** Internal display model */
interface CoachSuggestion {
  /** Backend suggestion id — present for API items, undefined for local items */
  apiId?: string;
  type: 'review' | 'weakness' | 'burnout' | 'streak';
  title: string;
  message: string;
  icon: React.ReactElement;
  color: string;
  action?: string;
  priority: number; // lower = higher priority
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Map suggestion type string to display icon */
function iconForType(type: string): React.ReactElement {
  switch (type) {
    case 'review':  return <Replay sx={{ fontSize: 20 }} />;
    case 'burnout': return <Timer sx={{ fontSize: 20 }} />;
    case 'streak':  return <AutoAwesome sx={{ fontSize: 20 }} />;
    case 'weakness':
    default:        return <Psychology sx={{ fontSize: 20 }} />;
  }
}

/** Map suggestion type string to accent color */
function colorForType(type: string): string {
  switch (type) {
    case 'review':  return '#6366f1';
    case 'burnout': return '#22c55e';
    case 'streak':  return '#f97316';
    case 'weakness':
    default:        return '#f59e0b';
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

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
  const [loading, setLoading] = useState(true);

  const [apiSuggestions, setApiSuggestions] = useState<CoachSuggestion[]>([]);
  const [burnout, setBurnout] = useState<BurnoutCheckResponse | null>(null);

  // Fetch weakness data + coaching suggestions + burnout check on mount
  useEffect(() => {
    // Weakness report (best-effort — ignore 404/500)
    apiRequest<{ weaknesses: WeaknessItem[] }>('/api/learning-path/weakness-report')
      .then(data => setWeakTopics((data.weaknesses || []).filter(w => w.is_weak)))
      .catch(() => {});

    // Burnout check
    apiRequest<BurnoutCheckResponse>('/api/v1/coaching/burnout-check')
      .then(data => setBurnout(data))
      .catch(() => {});

    // Backend coaching suggestions — the primary data source
    setLoading(true);
    apiRequest<ApiCoachingSuggestion[]>('/api/v1/coaching/suggestions')
      .then(items => {
        const mapped: CoachSuggestion[] = (items || []).map(item => ({
          apiId: item.id,
          type: item.type as CoachSuggestion['type'],
          title: item.title,
          message: item.message,
          icon: iconForType(item.type),
          color: colorForType(item.type),
          // action_url from backend doubles as the local action key
          action: item.action_url || undefined,
          priority: item.priority,
        }));
        setApiSuggestions(mapped);
      })
      .catch(() => {
        // Silently fall back to local signal-based suggestions
      })
      .finally(() => setLoading(false));
  }, []);

  // Generate suggestions based on local behavioral signals
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

    // 3. Burnout detection — from API or prop fallback
    const burnoutFromApi = burnout?.is_at_risk;
    const burnoutFromProp = studyMinutesToday > 180;
    if (burnoutFromApi || burnoutFromProp) {
      const msg = burnout?.recommendation
        ?? `Bugün ${studyMinutesToday} dakika çalıştın — harika! Ama araştırmalar 90 dakikada bir mola vermenin verimliliği %20 artırdığını gösteriyor.`;
      items.push({
        type: 'burnout',
        title: 'Mola Zamanı',
        message: msg,
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
        message: 'Son sorularda zorlandığını fark ettim. Konuyu birlikte gözden geçirelim — yanlış yapmak öğrenmenin doğal parçası!',
        icon: <Psychology sx={{ fontSize: 20 }} />,
        color: '#8b5cf6',
        action: 'chat',
        priority: 0, // Highest priority
      });
    }

    // 6. Merge backend API suggestions (deduplicate by type+title)
    const localKeys = new Set(items.map(s => s.type + s.title));
    for (const apiS of apiSuggestions) {
      if (!localKeys.has(apiS.type + apiS.title)) {
        items.push(apiS);
      }
    }

    return items
      .filter(s => !dismissed.has(s.type + s.title))
      .sort((a, b) => a.priority - b.priority);
  }, [dueCardCount, weakTopics, studyMinutesToday, streak, recentWrongCount, dismissed, apiSuggestions, burnout]);

  // ---------------------------------------------------------------------------
  // Interaction handlers — use /interact endpoint for API items, signals for
  // locally-generated items so the coaching engine gets accurate feedback.
  // ---------------------------------------------------------------------------

  const postInteract = (suggestion: CoachSuggestion, action: 'clicked' | 'dismissed') => {
    if (suggestion.apiId) {
      // API suggestion — use the proper interact endpoint
      apiRequest(
        `/api/v1/coaching/suggestions/${suggestion.apiId}/interact`,
        {
          method: 'POST',
          body: JSON.stringify({ action }),
        },
      ).catch(() => {});
    } else {
      // Local signal-based suggestion — record a session_duration proxy
      // (value 1 = acted, 0 = dismissed) so the backend has some signal
      apiRequest('/api/v1/coaching/signals', {
        method: 'POST',
        body: JSON.stringify({
          signal_type: 'session_duration',
          value: action === 'clicked' ? 1 : 0,
        }),
      }).catch(() => {});
    }
  };

  const dismissSuggestion = (suggestion: CoachSuggestion) => {
    setDismissed(prev => new Set(prev).add(suggestion.type + suggestion.title));
    postInteract(suggestion, 'dismissed');
  };

  const handleAction = (suggestion: CoachSuggestion) => {
    if (suggestion.action) { onAction?.(suggestion.action); }
    postInteract(suggestion, 'clicked');
    // Remove from view after acting
    setDismissed(prev => new Set(prev).add(suggestion.type + suggestion.title));
  };

  // Show nothing while loading and there are no local signals yet
  if (!visible) { return null; }
  if (loading && suggestions.length === 0) {
    return (
      <GlassCard glassIntensity="light" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1.5, p: 2 }}>
        <CircularProgress size={18} thickness={5} sx={{ color: '#6366f1', flexShrink: 0 }} />
        <Typography variant="caption" color="text.secondary">
          AI koç önerileri yükleniyor…
        </Typography>
      </GlassCard>
    );
  }
  if (suggestions.length === 0) { return null; }

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

          {/* Burnout signals banner — shown when backend detects risk */}
          {burnout?.is_at_risk && burnout.signals.length > 0 && (
            <Box
              sx={{
                mb: 1.5,
                p: 1,
                borderRadius: 1.5,
                bgcolor: '#22c55e10',
                border: '1px solid #22c55e30',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 0.75,
              }}
            >
              <WarningAmber sx={{ fontSize: 16, color: '#22c55e', mt: 0.1, flexShrink: 0 }} />
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  <strong style={{ color: '#22c55e' }}>Davranışsal sinyal analizi:</strong>{' '}
                  {burnout.signals.join(' · ')}
                </Typography>
              </Box>
            </Box>
          )}

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
                          onClick={() => handleAction(s)}
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
