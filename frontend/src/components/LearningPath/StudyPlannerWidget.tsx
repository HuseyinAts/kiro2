/**
 * StudyPlannerWidget — YKS Geri Sayım + Haftalık Çalışma Planı
 *
 * Gösterir:
 * - YKS sınavına kalan gün sayısı
 * - Haftalık konu hedefi (kalan konular / kalan hafta)
 * - IRT tabanlı Monte Carlo skor projeksiyonu (backend API)
 * - Günlük çalışma süresi hedefi
 *
 * Bilimsel temel: Sistematik çalışma planı sınav kaygısını anlamlı azaltır (PMC).
 * Referans: LearnQ, PrepAI — countdown + study planning
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Chip,
  TextField,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  CalendarToday,
  TrendingUp,
  Speed,
  CheckCircle,
  Schedule,
} from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';
import { apiRequest } from '../../utils/apiHelpers';
import type { PathNodeData } from './PathNode';

// YKS 2026 varsayılan tarih (Haziran ortası)
const DEFAULT_YKS_DATE = '2026-06-20';
const STORAGE_KEY = 'kiro2_yks_target_date';

interface StudyPlannerWidgetProps {
  pathNodes: PathNodeData[];
  /** Günlük hedef çalışma süresi (dakika) */
  dailyTargetMinutes?: number;
}

// Matches backend StudyPlanResponse
interface WeekGoalItem {
  week_number: number;
  topics: string[];
  target_questions: number;
  completed_questions: number;
  accuracy: number | null;
  is_current: boolean;
}

interface PlanData {
  plan_id: string | number;
  yks_date: string;
  days_left: number;
  total_weeks: number;
  current_week: number;
  weekly_hours: number;
  total_target_questions: number;
  total_completed_questions: number;
  overall_completion_rate: number;
  weeks: WeekGoalItem[];
}

// Matches backend ScoreProjectionResponse
interface ScoreProjection {
  projected_net: number;
  confidence_interval: number[];
  trend: string;
  simulation_runs: number;
}

// Matches backend WeeklyReportResponse
interface WeeklyReport {
  week_number: number;
  target_questions: number;
  completed_questions: number;
  completion_rate: number;
  topics: string[];
  days_remaining_in_week: number;
  daily_target_to_catch_up: number;
  on_track: boolean;
}

export function StudyPlannerWidget({ pathNodes, dailyTargetMinutes = 120 }: StudyPlannerWidgetProps) {
  const [targetDate, setTargetDate] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || DEFAULT_YKS_DATE;
    } catch {
      return DEFAULT_YKS_DATE;
    }
  });

  const [planData, setPlanData] = useState<PlanData | null>(null);
  const [projection, setProjection] = useState<ScoreProjection | null>(null);
  const [weeklyReport, setWeeklyReport] = useState<WeeklyReport | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(true);
  const [loadingProjection, setLoadingProjection] = useState(false);
  const [savingDate, setSavingDate] = useState(false);

  // Fetch all plan data on mount
  useEffect(() => {
    let cancelled = false;

    async function fetchPlanData() {
      setLoadingPlan(true);
      try {
        const data = await apiRequest<PlanData>('/api/v1/study-plan/current');
        if (cancelled) {return;}
        setPlanData(data);
        if (data.yks_date) {
          setTargetDate(data.yks_date);
          try { localStorage.setItem(STORAGE_KEY, data.yks_date); } catch { /* noop */ }
        }
      } catch {
        // No active plan yet — component still works with local date + pathNodes
      } finally {
        if (!cancelled) {setLoadingPlan(false);}
      }
    }

    fetchPlanData();
    return () => { cancelled = true; };
  }, []);

  // Fetch score projection separately (slower endpoint — Monte Carlo)
  useEffect(() => {
    let cancelled = false;

    async function fetchProjection() {
      setLoadingProjection(true);
      try {
        const data = await apiRequest<ScoreProjection>('/api/v1/study-plan/projection');
        if (!cancelled) {setProjection(data);}
      } catch {
        // Fall back to local estimate — handled in stats useMemo
      } finally {
        if (!cancelled) {setLoadingProjection(false);}
      }
    }

    fetchProjection();
    return () => { cancelled = true; };
  }, []);

  // Fetch weekly report
  useEffect(() => {
    let cancelled = false;

    async function fetchWeeklyReport() {
      try {
        const data = await apiRequest<WeeklyReport>('/api/v1/study-plan/weekly-report');
        if (!cancelled) {setWeeklyReport(data);}
      } catch {
        // No active plan — silently ignore
      }
    }

    fetchWeeklyReport();
    return () => { cancelled = true; };
  }, []);

  // Save date: POST to create/update plan, also persist in localStorage
  const handleDateChange = useCallback(async (newDate: string) => {
    setTargetDate(newDate);
    try { localStorage.setItem(STORAGE_KEY, newDate); } catch { /* noop */ }

    setSavingDate(true);
    try {
      const created = await apiRequest<PlanData>('/api/v1/study-plan/', {
        method: 'POST',
        body: JSON.stringify({ yks_date: newDate, weekly_hours: planData?.weekly_hours ?? 20 }),
      });
      setPlanData(created);

      // Refresh projection and weekly report after plan change
      const [proj, report] = await Promise.allSettled([
        apiRequest<ScoreProjection>('/api/v1/study-plan/projection'),
        apiRequest<WeeklyReport>('/api/v1/study-plan/weekly-report'),
      ]);
      if (proj.status === 'fulfilled') {setProjection(proj.value);}
      if (report.status === 'fulfilled') {setWeeklyReport(report.value);}
    } catch {
      // Keep UI in consistent state — date already updated locally
    } finally {
      setSavingDate(false);
    }
  }, [planData?.weekly_hours]);

  // Update current week progress via PATCH
  const handleUpdateWeeklyProgress = useCallback(async (
    weekNumber: number,
    completedQuestions: number,
  ) => {
    try {
      await apiRequest(`/api/v1/study-plan/weekly/${weekNumber}`, {
        method: 'PATCH',
        body: JSON.stringify({ completed_questions: completedQuestions }),
      });
      // Refetch plan to get updated totals
      const updated = await apiRequest<PlanData>('/api/v1/study-plan/current');
      setPlanData(updated);
    } catch {
      // Silently ignore — UI remains unchanged
    }
  }, []);

  // Derived stats — prefer backend data, fall back to local computation from pathNodes
  const stats = useMemo(() => {
    const now = new Date();
    const target = new Date(targetDate + 'T00:00:00');
    const diffMs = target.getTime() - now.getTime();
    const daysLeft = planData?.days_left ?? Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
    const weeksLeft = Math.max(1, Math.ceil(daysLeft / 7));

    // Use backend totals when plan exists, else derive from pathNodes
    const total = planData
      ? planData.total_target_questions || pathNodes.length
      : pathNodes.length;
    const completed = planData
      ? planData.total_completed_questions
      : pathNodes.filter(n => n.status === 'completed').length;
    const remaining = Math.max(0, total - completed);
    const progressPercent = planData
      ? Math.round(planData.overall_completion_rate * 100)
      : (total > 0 ? Math.round((completed / total) * 100) : 0);

    // Weekly topics target from pathNodes (backend gives question counts, not topic counts)
    const totalTopics = pathNodes.length;
    const completedTopics = pathNodes.filter(n => n.status === 'completed').length;
    const remainingTopics = totalTopics - completedTopics;
    const weeklyTopicTarget = remainingTopics > 0 ? Math.ceil(remainingTopics / weeksLeft) : 0;

    // Score projection: prefer IRT Monte Carlo from API, fall back to linear estimate
    const projectedNet = projection
      ? Math.round(projection.projected_net)
      : (totalTopics > 0 ? Math.round((completedTopics / totalTopics) * 120) : 0);

    // Daily minutes from weekly report or local calculation
    const dailyMinutesNeeded = weeklyReport?.daily_target_to_catch_up
      ? weeklyReport.daily_target_to_catch_up * 5 // rough: questions * 5 min each
      : (remaining > 0 && daysLeft > 0 ? Math.round((remaining * 5) / daysLeft) : 0);

    return {
      daysLeft,
      weeksLeft,
      total,
      completed,
      remaining,
      progressPercent,
      weeklyTopicTarget,
      projectedNet,
      dailyMinutesNeeded,
      completedTopics,
      totalTopics,
      remainingTopics,
    };
  }, [pathNodes, targetDate, planData, projection, weeklyReport]);

  // Current week info from plan
  const currentWeek = useMemo(() => {
    if (!planData?.weeks) {return null;}
    return planData.weeks.find(w => w.is_current) ?? null;
  }, [planData]);

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
            {loadingPlan ? (
              <CircularProgress size={28} sx={{ color: urgencyColor }} />
            ) : (
              <Typography variant="h3" fontWeight={900} sx={{ color: urgencyColor, lineHeight: 1 }}>
                {stats.daysLeft}
              </Typography>
            )}
            <Typography variant="body2" color="text.secondary" fontWeight={600}>
              gün kaldı
            </Typography>
          </Box>
        </Box>
        <Tooltip title={savingDate ? 'Kaydediliyor...' : 'YKS tarihini ayarla'}>
          <Box sx={{ position: 'relative' }}>
            <TextField
              type="date"
              size="small"
              value={targetDate}
              onChange={(e) => handleDateChange(e.target.value)}
              disabled={savingDate}
              sx={{
                width: 150,
                '& .MuiInputBase-root': { borderRadius: 2, fontSize: 13 },
              }}
              inputProps={{ min: new Date().toISOString().split('T')[0] }}
            />
            {savingDate && (
              <CircularProgress
                size={16}
                sx={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)' }}
              />
            )}
          </Box>
        </Tooltip>
      </Box>

      {/* İlerleme barı */}
      <Box sx={{ mb: 2.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            Genel İlerleme
          </Typography>
          <Typography variant="caption" fontWeight={700}>
            {stats.completedTopics}/{stats.totalTopics} konu
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
            {stats.weeklyTopicTarget}
          </Typography>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            konu/hafta hedef
          </Typography>
        </Box>

        {/* Tahmini net — IRT Monte Carlo or linear fallback */}
        <Tooltip
          title={
            projection
              ? `IRT Monte Carlo (${projection.simulation_runs} sim): %90 güven aralığı ${projection.confidence_interval[0]?.toFixed(1)}–${projection.confidence_interval[1]?.toFixed(1)}`
              : 'Tahmini net (basit lineer model)'
          }
        >
          <Box sx={{
            p: 1.5,
            borderRadius: 2,
            backgroundColor: 'rgba(34,197,94,0.06)',
            textAlign: 'center',
            cursor: 'help',
          }}>
            {loadingProjection ? (
              <CircularProgress size={20} sx={{ color: '#22c55e', mb: 0.25 }} />
            ) : (
              <TrendingUp sx={{ fontSize: 20, color: '#22c55e', mb: 0.25 }} />
            )}
            <Typography variant="h6" fontWeight={800} sx={{ color: '#22c55e' }}>
              {loadingProjection ? '—' : stats.projectedNet}
            </Typography>
            <Typography variant="caption" color="text.secondary" fontWeight={600}>
              tahmini net{projection ? ' (IRT)' : ''}
            </Typography>
          </Box>
        </Tooltip>

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

      {/* Bu hafta özeti (backend verisi varsa) */}
      {weeklyReport && (
        <Box sx={{
          mt: 1.5,
          p: 1.5,
          borderRadius: 2,
          backgroundColor: weeklyReport.on_track
            ? 'rgba(34,197,94,0.06)'
            : 'rgba(245,158,11,0.06)',
          border: `1px solid ${weeklyReport.on_track ? 'rgba(34,197,94,0.2)' : 'rgba(245,158,11,0.2)'}`,
        }}>
          <Typography variant="caption" fontWeight={700} color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            Bu Hafta ({weeklyReport.week_number}. hafta)
          </Typography>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              {weeklyReport.completed_questions} / {weeklyReport.target_questions} soru
            </Typography>
            <Chip
              label={weeklyReport.on_track ? 'Yolunda' : `Günde ${weeklyReport.daily_target_to_catch_up} soru`}
              size="small"
              sx={{
                fontWeight: 700,
                fontSize: 10,
                height: 20,
                backgroundColor: weeklyReport.on_track
                  ? 'rgba(34,197,94,0.15)'
                  : 'rgba(245,158,11,0.15)',
                color: weeklyReport.on_track ? '#22c55e' : '#f59e0b',
              }}
            />
          </Box>
          <LinearProgress
            variant="determinate"
            value={Math.min(100, Math.round(weeklyReport.completion_rate * 100))}
            sx={{
              mt: 0.75,
              height: 4,
              borderRadius: 2,
              bgcolor: 'rgba(0,0,0,0.06)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 2,
                backgroundColor: weeklyReport.on_track ? '#22c55e' : '#f59e0b',
              },
            }}
          />
        </Box>
      )}

      {/* Mevcut hafta konuları (plan varsa) */}
      {currentWeek && currentWeek.topics.length > 0 && (
        <Box sx={{ mt: 1.5 }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            Bu haftanın konuları
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {currentWeek.topics.slice(0, 4).map((topic, i) => (
              <Chip
                key={i}
                label={topic}
                size="small"
                sx={{
                  fontSize: 10,
                  height: 20,
                  backgroundColor: 'rgba(99,102,241,0.08)',
                  color: '#6366f1',
                  fontWeight: 600,
                }}
              />
            ))}
            {currentWeek.topics.length > 4 && (
              <Chip
                label={`+${currentWeek.topics.length - 4}`}
                size="small"
                sx={{ fontSize: 10, height: 20, fontWeight: 600 }}
              />
            )}
          </Box>
        </Box>
      )}

      {/* Haftalık ilerleme güncelle butonu (plan ve mevcut hafta varsa) */}
      {currentWeek && (
        <Box
          component="button"
          onClick={() => {
            const newCount = (currentWeek.completed_questions ?? 0) + 1;
            handleUpdateWeeklyProgress(currentWeek.week_number, newCount);
          }}
          sx={{
            display: 'none', // Gizli — dışarıdan tetiklenebilir, internal use only
          }}
          aria-hidden
        />
      )}

      {/* Uyarı mesajları */}
      {stats.daysLeft <= 30 && stats.remainingTopics > 0 && (
        <Chip
          label={`Son ${stats.daysLeft} gün! ${stats.remainingTopics} konu kaldı.`}
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

      {/* Plan trend bilgisi */}
      {projection?.trend && projection.trend !== 'stable' && (
        <Chip
          label={
            projection.trend === 'improving'
              ? 'Performansın yükseliyor!'
              : projection.trend === 'declining'
                ? 'Performansın düşüyor, çalışmayı artır'
                : projection.trend
          }
          size="small"
          sx={{
            mt: 1,
            width: '100%',
            fontWeight: 700,
            fontSize: 11,
            backgroundColor: projection.trend === 'improving'
              ? 'rgba(34,197,94,0.12)'
              : 'rgba(239,68,68,0.12)',
            color: projection.trend === 'improving' ? '#22c55e' : '#ef4444',
          }}
        />
      )}
    </GlassCard>
  );
}

export default StudyPlannerWidget;
