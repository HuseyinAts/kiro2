/**
 * ProgressDashboard — Geliştirilmiş ilerleme takibi
 *
 * - Son 14 günlük bar chart (localStorage snapshots)
 * - 4 stat kartı (completed, inProgress, available, percentage)
 * - Tahmini tamamlanma tarihi
 * - En çok çalışılan konular
 */

import { useMemo, useEffect, useState } from 'react';
import { Box, Typography, LinearProgress } from '@mui/material';
import { TrendingUp, CalendarMonth, EmojiEvents, Warning } from '@mui/icons-material';
import { GlassCard } from '../../ui/GlassCard';
import modernColors from '../../../theme/modern-colors';
import { PathNodeData } from '../PathNode';
import { apiRequest } from '../../../utils/apiHelpers';

interface ProgressDashboardProps {
  pathNodes: PathNodeData[];
}

interface DailySnapshot {
  date: string; // YYYY-MM-DD
  completed: number;
  total: number;
  percentage: number;
}

const STORAGE_KEY = 'lp_progress_snapshots';
const MAX_DAYS = 14;

function loadSnapshots(): DailySnapshot[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveSnapshot(completed: number, total: number) {
  const today = new Date().toISOString().split('T')[0];
  const snapshots = loadSnapshots();
  const existing = snapshots.findIndex(s => s.date === today);
  const entry: DailySnapshot = {
    date: today,
    completed,
    total,
    percentage: total > 0 ? Math.round((completed / total) * 100) : 0,
  };

  if (existing >= 0) {
    snapshots[existing] = entry;
  } else {
    snapshots.push(entry);
  }

  // Keep last MAX_DAYS
  const trimmed = snapshots.slice(-MAX_DAYS);
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed)); } catch {}
}

interface WeaknessItem {
  topic: string;
  avg_score: number;
  attempts: number;
  trend: 'improving' | 'declining' | 'stable';
  is_weak: boolean;
}

export function ProgressDashboard({ pathNodes }: ProgressDashboardProps) {
  // B3: Weakness data
  const [weaknesses, setWeaknesses] = useState<WeaknessItem[]>([]);
  useEffect(() => {
    apiRequest<{ weaknesses: WeaknessItem[] }>('/api/learning-path/weakness-report')
      .then(data => setWeaknesses(data.weaknesses || []))
      .catch(() => {});
  }, []);
  const completed = pathNodes.filter(n => n.status === 'completed').length;
  const inProgress = pathNodes.filter(n => n.status === 'current').length;
  const available = pathNodes.filter(n => n.status === 'available').length;
  const total = pathNodes.length;
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

  // Save today's snapshot
  useEffect(() => {
    if (total > 0) {saveSnapshot(completed, total);}
  }, [completed, total]);

  const snapshots = useMemo(() => loadSnapshots(), [completed]);

  // Estimated completion date
  const estimatedDate = useMemo(() => {
    if (snapshots.length < 2 || completed >= total) {return null;}
    const first = snapshots[0];
    const last = snapshots[snapshots.length - 1];
    const daysBetween = Math.max(1, Math.round(
      (new Date(last.date).getTime() - new Date(first.date).getTime()) / 86400000,
    ));
    const progressMade = last.completed - first.completed;
    if (progressMade <= 0) {return null;}
    const remaining = total - completed;
    const daysNeeded = Math.ceil((remaining / progressMade) * daysBetween);
    const target = new Date();
    target.setDate(target.getDate() + daysNeeded);
    return target.toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' });
  }, [snapshots, completed, total]);

  // Completed topics for "most studied" list
  const completedTopics = useMemo(
    () => pathNodes.filter(n => n.status === 'completed').map(n => n.title).slice(0, 5),
    [pathNodes],
  );

  // Chart max for bar scaling
  const chartMax = useMemo(
    () => Math.max(1, ...snapshots.map(s => s.completed)),
    [snapshots],
  );

  return (
    <GlassCard glassIntensity="light">
      <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
        İlerleme İstatistikleri
      </Typography>

      {/* Stat Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 4 }}>
        <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.success}>
          <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>{completed}</Typography>
          <Typography variant="body2" color="text.secondary">Tamamlanan Modül</Typography>
        </GlassCard>
        <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.primary}>
          <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>{inProgress}</Typography>
          <Typography variant="body2" color="text.secondary">Devam Eden</Typography>
        </GlassCard>
        <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.ocean}>
          <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>{available}</Typography>
          <Typography variant="body2" color="text.secondary">Erişilebilir</Typography>
        </GlassCard>
        <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.warning}>
          <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>{percentage}%</Typography>
          <Typography variant="body2" color="text.secondary">Tamamlanma Oranı</Typography>
        </GlassCard>
      </Box>

      {/* 14-day Progress Chart */}
      {snapshots.length > 1 && (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <TrendingUp sx={{ color: '#3b82f6' }} />
            <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>Son {snapshots.length} Günlük Trend</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 0.5, height: 120 }}>
            {snapshots.map((snap) => {
              const barHeight = Math.max(4, (snap.completed / chartMax) * 100);
              return (
                <Box key={snap.date} sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                  <Typography variant="caption" sx={{ fontSize: 10, fontWeight: 600 }}>
                    {snap.completed}
                  </Typography>
                  <Box
                    sx={{
                      width: '100%',
                      maxWidth: 32,
                      height: `${barHeight}%`,
                      minHeight: 4,
                      borderRadius: '4px 4px 0 0',
                      background: modernColors.gradients.primary,
                      transition: 'height 0.3s ease',
                    }}
                  />
                  <Typography variant="caption" sx={{ fontSize: 9, color: 'text.secondary' }}>
                    {snap.date.slice(8)}
                  </Typography>
                </Box>
              );
            })}
          </Box>
        </Box>
      )}

      {/* Estimated completion + Completed topics */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
        {estimatedDate && (
          <GlassCard glassIntensity="light">
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <CalendarMonth sx={{ color: '#8b5cf6' }} />
              <Box>
                <Typography variant="caption" color="text.secondary">Tahmini Tamamlanma</Typography>
                <Typography variant="body1" sx={{ fontWeight: 700 }}>{estimatedDate}</Typography>
              </Box>
            </Box>
          </GlassCard>
        )}

        {completedTopics.length > 0 && (
          <GlassCard glassIntensity="light">
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
              <EmojiEvents sx={{ color: '#f59e0b', mt: 0.3 }} />
              <Box>
                <Typography variant="caption" color="text.secondary">Tamamlanan Konular</Typography>
                {completedTopics.map((topic, i) => (
                  <Typography key={i} variant="body2" sx={{ fontWeight: 500 }}>{topic}</Typography>
                ))}
              </Box>
            </Box>
          </GlassCard>
        )}
      </Box>

      {/* B3: Weakness Report */}
      {weaknesses.filter(w => w.is_weak).length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Warning sx={{ color: '#ef4444' }} />
            <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>Zayıf Noktalar</Typography>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {weaknesses.filter(w => w.is_weak).map((w) => (
              <GlassCard key={w.topic} glassIntensity="light">
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{w.topic}</Typography>
                  <Typography variant="caption" sx={{
                    fontWeight: 700,
                    color: w.trend === 'improving' ? '#22c55e' : w.trend === 'declining' ? '#ef4444' : '#94a3b8',
                  }}>
                    {w.trend === 'improving' ? 'İyileşiyor' : w.trend === 'declining' ? 'Kötüleşiyor' : 'Sabit'}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={w.avg_score}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    bgcolor: 'rgba(239,68,68,0.1)',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: w.avg_score < 40 ? '#ef4444' : '#f59e0b',
                      borderRadius: 4,
                    },
                  }}
                />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    Ort. %{w.avg_score}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {w.attempts} deneme
                  </Typography>
                </Box>
              </GlassCard>
            ))}
          </Box>
        </Box>
      )}
    </GlassCard>
  );
}
