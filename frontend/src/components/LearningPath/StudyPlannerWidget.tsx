/**
 * StudyPlannerWidget — YKS Geri Sayım + Haftalık Çalışma Planı
 *
 * Gösterir:
 * - YKS sınavına kalan gün sayısı
 * - Haftalık konu hedefi (kalan konular / kalan hafta)
 * - Simüle skor projeksiyonu
 * - Günlük çalışma süresi hedefi
 *
 * Bilimsel temel: Sistematik çalışma planı sınav kaygısını anlamlı azaltır (PMC).
 * Referans: LearnQ, PrepAI — countdown + study planning
 */

import { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Chip,
  TextField,
} from '@mui/material';
import {
  CalendarToday,
  TrendingUp,
  Speed,
  CheckCircle,
  Schedule,
} from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';
import type { PathNodeData } from './PathNode';

// YKS 2026 varsayılan tarih (Haziran ortası)
const DEFAULT_YKS_DATE = '2026-06-20';
const STORAGE_KEY = 'kiro2_yks_target_date';

interface StudyPlannerWidgetProps {
  pathNodes: PathNodeData[];
  /** Günlük hedef çalışma süresi (dakika) */
  dailyTargetMinutes?: number;
}

export function StudyPlannerWidget({ pathNodes, dailyTargetMinutes = 120 }: StudyPlannerWidgetProps) {
  const [targetDate, setTargetDate] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || DEFAULT_YKS_DATE;
    } catch {
      return DEFAULT_YKS_DATE;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, targetDate);
    } catch {
      // localStorage unavailable
    }
  }, [targetDate]);

  const stats = useMemo(() => {
    const now = new Date();
    const target = new Date(targetDate + 'T00:00:00');
    const diffMs = target.getTime() - now.getTime();
    const daysLeft = Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
    const weeksLeft = Math.max(1, Math.ceil(daysLeft / 7));

    const total = pathNodes.length;
    const completed = pathNodes.filter(n => n.status === 'completed').length;
    const remaining = total - completed;
    const progressPercent = total > 0 ? Math.round((completed / total) * 100) : 0;

    // Haftalık hedef
    const weeklyTarget = remaining > 0 ? Math.ceil(remaining / weeksLeft) : 0;

    // Simüle skor projeksiyonu (basit lineer model)
    // TYT max net ~120, AYT max net ~80
    const maxNet = 120;
    const projectedNet = total > 0 ? Math.round((completed / total) * maxNet) : 0;

    // Günlük çalışma hedefi dakika cinsinden
    const dailyMinutesNeeded = remaining > 0 && daysLeft > 0
      ? Math.round((remaining * 45) / daysLeft) // Her konu ~45dk
      : 0;

    return {
      daysLeft,
      weeksLeft,
      total,
      completed,
      remaining,
      progressPercent,
      weeklyTarget,
      projectedNet,
      dailyMinutesNeeded,
    };
  }, [pathNodes, targetDate]);

  const urgencyColor = stats.daysLeft > 90 ? '#22c55e' : stats.daysLeft > 30 ? '#f59e0b' : '#ef4444';

  return (
    <GlassCard glassIntensity="light" sx={{ mb: 2 }}>
      {/* Header: Geri sayım */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2.5 }}>
        <Box>
          <Typography variant="subtitle2" fontWeight={700} sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
            <CalendarToday sx={{ fontSize: 18, color: urgencyColor }} />
            Sınav Geri Sayımı
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
            <Typography variant="h3" fontWeight={900} sx={{ color: urgencyColor, lineHeight: 1 }}>
              {stats.daysLeft}
            </Typography>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>
              gün kaldı
            </Typography>
          </Box>
        </Box>
        <TextField
          type="date"
          size="small"
          value={targetDate}
          onChange={(e) => setTargetDate(e.target.value)}
          sx={{
            width: 150,
            '& .MuiInputBase-root': { borderRadius: 2, fontSize: 13 },
          }}
          inputProps={{ min: new Date().toISOString().split('T')[0] }}
        />
      </Box>

      {/* İlerleme barı */}
      <Box sx={{ mb: 2.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            Genel İlerleme
          </Typography>
          <Typography variant="caption" fontWeight={700}>
            {stats.completed}/{stats.total} konu
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={stats.progressPercent}
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: 'rgba(0,0,0,0.06)',
            '& .MuiLinearProgress-bar': {
              borderRadius: 4,
              background: `linear-gradient(90deg, ${urgencyColor}, ${stats.progressPercent > 50 ? '#22c55e' : urgencyColor})`,
            },
          }}
        />
      </Box>

      {/* Stat kartları */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1.5 }}>
        {/* Haftalık hedef */}
        <Box sx={{
          p: 1.5,
          borderRadius: 2,
          backgroundColor: 'rgba(99,102,241,0.06)',
          textAlign: 'center',
        }}>
          <Speed sx={{ fontSize: 20, color: '#6366f1', mb: 0.25 }} />
          <Typography variant="h6" fontWeight={800} sx={{ color: '#6366f1' }}>
            {stats.weeklyTarget}
          </Typography>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            konu/hafta hedef
          </Typography>
        </Box>

        {/* Tahmini net */}
        <Box sx={{
          p: 1.5,
          borderRadius: 2,
          backgroundColor: 'rgba(34,197,94,0.06)',
          textAlign: 'center',
        }}>
          <TrendingUp sx={{ fontSize: 20, color: '#22c55e', mb: 0.25 }} />
          <Typography variant="h6" fontWeight={800} sx={{ color: '#22c55e' }}>
            {stats.projectedNet}
          </Typography>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            tahmini net
          </Typography>
        </Box>

        {/* Tamamlanan */}
        <Box sx={{
          p: 1.5,
          borderRadius: 2,
          backgroundColor: 'rgba(16,185,129,0.06)',
          textAlign: 'center',
        }}>
          <CheckCircle sx={{ fontSize: 20, color: '#10b981', mb: 0.25 }} />
          <Typography variant="h6" fontWeight={800} sx={{ color: '#10b981' }}>
            %{stats.progressPercent}
          </Typography>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            tamamlandı
          </Typography>
        </Box>

        {/* Günlük çalışma */}
        <Box sx={{
          p: 1.5,
          borderRadius: 2,
          backgroundColor: 'rgba(245,158,11,0.06)',
          textAlign: 'center',
        }}>
          <Schedule sx={{ fontSize: 20, color: '#f59e0b', mb: 0.25 }} />
          <Typography variant="h6" fontWeight={800} sx={{ color: '#f59e0b' }}>
            {Math.min(stats.dailyMinutesNeeded, dailyTargetMinutes)}dk
          </Typography>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            günlük hedef
          </Typography>
        </Box>
      </Box>

      {/* Uyarı mesajları */}
      {stats.daysLeft <= 30 && stats.remaining > 0 && (
        <Chip
          label={`Son ${stats.daysLeft} gün! ${stats.remaining} konu kaldı.`}
          size="small"
          sx={{
            mt: 1.5,
            width: '100%',
            fontWeight: 700,
            fontSize: 11,
            backgroundColor: '#ef444415',
            color: '#ef4444',
          }}
        />
      )}
    </GlassCard>
  );
}

export default StudyPlannerWidget;
