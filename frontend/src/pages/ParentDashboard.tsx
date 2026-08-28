/**
 * ParentDashboard — Veli Takip Sayfası
 *
 * Read-only dashboard: Öğrenci çalışma süresi, quiz sonuçları,
 * zayıf konular, streak bilgisi.
 *
 * Doping Hafıza + Century Tech çift dashboard modeli.
 * Türk pazarında veli ilgisi = retention artışı.
 */

import { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  LinearProgress,
  Chip,
  Alert,
} from '@mui/material';
import {
  School,
  Timer,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  LocalFireDepartment,
  CalendarToday,
  Warning,
} from '@mui/icons-material';
import { GlassCard } from '../components/ui/GlassCard';
import { apiRequest } from '../utils/apiHelpers';

interface WeaknessItem {
  topic: string;
  avg_score: number;
  attempts: number;
  trend: 'improving' | 'declining' | 'stable';
  is_weak: boolean;
}

interface ParentData {
  studentName: string;
  streak: number;
  totalStudyMinutes: number;
  todayStudyMinutes: number;
  completedTopics: number;
  totalTopics: number;
  weaknesses: WeaknessItem[];
  recentQuizScores: number[];
}

export function ParentDashboard() {
  const [data, setData] = useState<ParentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        // Fetch from multiple endpoints in parallel
        const [weaknessRes, streakRes] = await Promise.allSettled([
          apiRequest<{ weaknesses: WeaknessItem[] }>('/api/v1/learning-path/weakness-report'),
          apiRequest<{ daily_streak: number }>('/api/v1/learning-path/streak'),
        ]);

        const weaknesses = weaknessRes.status === 'fulfilled'
          ? (weaknessRes.value.weaknesses || []).filter(w => w.is_weak)
          : [];
        const streak = streakRes.status === 'fulfilled'
          ? streakRes.value.daily_streak || 0
          : 0;

        setData({
          studentName: 'Öğrenci',
          streak,
          totalStudyMinutes: 0, // Would come from study-session API
          todayStudyMinutes: 0,
          completedTopics: 0,
          totalTopics: 0,
          weaknesses,
          recentQuizScores: [],
        });
      } catch (err) {
        setError('Veriler yüklenemedi. Lütfen tekrar deneyin.');
        console.error('Parent dashboard error:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Box sx={{ textAlign: 'center' }}>
          <School sx={{ fontSize: 48, color: 'var(--k-coral)', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">Yükleniyor...</Typography>
          <LinearProgress sx={{ mt: 2, width: 200 }} />
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="sm" sx={{ py: 8 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!data) {return null;}

  const progressPercent = data.totalTopics > 0
    ? Math.round((data.completedTopics / data.totalTopics) * 100)
    : 0;

  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'var(--k-surface)',
      py: 4,
    }}>
      <Container maxWidth="md">
        {/* Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Box sx={{
            width: 64,
            height: 64,
            borderRadius: 3,
            background: 'var(--k-coral)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 2,
          }}>
            <School sx={{ fontSize: 36, color: 'white' }} />
          </Box>
          <Typography variant="h4" fontWeight={900} sx={{ mb: 0.5 }}>
            Veli Takip Paneli
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {data.studentName} — KIRO2 YKS Hazırlık
          </Typography>
        </Box>

        {/* Summary Card */}
        <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
            {/* Streak */}
            <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'color-mix(in srgb, var(--k-coral) 10%, transparent)', textAlign: 'center' }}>
              <LocalFireDepartment sx={{ fontSize: 28, color: 'var(--k-coral)', mb: 0.5 }} />
              <Typography variant="h5" fontWeight={800} sx={{ color: 'var(--k-coral)' }}>
                {data.streak}
              </Typography>
              <Typography variant="caption" fontWeight={600} color="text.secondary">
                günlük seri
              </Typography>
            </Box>

            {/* Today study */}
            <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'color-mix(in srgb, var(--k-text) 10%, transparent)', textAlign: 'center' }}>
              <Timer sx={{ fontSize: 28, color: 'var(--k-text)', mb: 0.5 }} />
              <Typography variant="h5" fontWeight={800} sx={{ color: 'var(--k-text)' }}>
                {data.todayStudyMinutes} dk
              </Typography>
              <Typography variant="caption" fontWeight={600} color="text.secondary">
                bugün çalışma
              </Typography>
            </Box>

            {/* Completed */}
            <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'color-mix(in srgb, var(--k-success) 10%, transparent)', textAlign: 'center' }}>
              <CheckCircle sx={{ fontSize: 28, color: 'var(--k-success)', mb: 0.5 }} />
              <Typography variant="h5" fontWeight={800} sx={{ color: 'var(--k-success)' }}>
                {data.completedTopics}
              </Typography>
              <Typography variant="caption" fontWeight={600} color="text.secondary">
                tamamlanan konu
              </Typography>
            </Box>

            {/* Progress */}
            <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'color-mix(in srgb, var(--k-coral-2) 10%, transparent)', textAlign: 'center' }}>
              <TrendingUp sx={{ fontSize: 28, color: 'var(--k-coral-2)', mb: 0.5 }} />
              <Typography variant="h5" fontWeight={800} sx={{ color: 'var(--k-coral-2)' }}>
                %{progressPercent}
              </Typography>
              <Typography variant="caption" fontWeight={600} color="text.secondary">
                genel ilerleme
              </Typography>
            </Box>
          </Box>
        </GlassCard>

        {/* Weakness Report */}
        {data.weaknesses.length > 0 && (
          <GlassCard glassIntensity="light" sx={{ mb: 3 }}>
            <Typography variant="subtitle1" fontWeight={700} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Warning sx={{ color: 'var(--k-risk)' }} />
              Güçlendirilmesi Gereken Konular
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {data.weaknesses.slice(0, 5).map(w => (
                <Box key={w.topic} sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(239,68,68,0.04)' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                    <Typography variant="body2" fontWeight={600}>{w.topic}</Typography>
                    <Chip
                      size="small"
                      icon={w.trend === 'improving' ? <TrendingUp sx={{ fontSize: 14 }} /> : <TrendingDown sx={{ fontSize: 14 }} />}
                      label={w.trend === 'improving' ? 'İyileşiyor' : w.trend === 'declining' ? 'Kötüleşiyor' : 'Sabit'}
                      sx={{
                        height: 22,
                        fontSize: 10,
                        fontWeight: 700,
                        color: w.trend === 'improving' ? 'var(--k-success)' : w.trend === 'declining' ? 'var(--k-risk)' : 'var(--k-text-muted)',
                        bgcolor: w.trend === 'improving' ? 'color-mix(in srgb, var(--k-success) 10%, transparent)' : w.trend === 'declining' ? 'color-mix(in srgb, var(--k-risk) 10%, transparent)' : 'color-mix(in srgb, var(--k-text-muted) 10%, transparent)',
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
                        bgcolor: w.avg_score < 40 ? 'var(--k-risk)' : 'var(--k-warning)',
                        borderRadius: 3,
                      },
                    }}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.25 }}>
                    Ortalama: %{w.avg_score} · {w.attempts} deneme
                  </Typography>
                </Box>
              ))}
            </Box>

            {/* Actionable suggestion — Century Tech style */}
            {data.weaknesses[0] && (
              <Alert severity="info" sx={{ mt: 2, borderRadius: 2 }}>
                <Typography variant="body2" fontWeight={600}>
                  Öneri: Bu hafta en çok zorlandığı konu: <strong>{data.weaknesses[0].topic}</strong>.
                  Günde 15 dk ek çalışma ile önemli gelişim sağlanabilir.
                </Typography>
              </Alert>
            )}
          </GlassCard>
        )}

        {/* Recent Quiz Scores */}
        {data.recentQuizScores.length > 0 && (
          <GlassCard glassIntensity="light" sx={{ mb: 3 }}>
            <Typography variant="subtitle1" fontWeight={700} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <CalendarToday sx={{ color: 'var(--k-text)' }} />
              Son Quiz Sonuçları
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {data.recentQuizScores.map((score, i) => (
                <Chip
                  key={i}
                  label={`%${score}`}
                  sx={{
                    fontWeight: 700,
                    bgcolor: score >= 70 ? 'color-mix(in srgb, var(--k-success) 15%, transparent)' : score >= 50 ? 'color-mix(in srgb, var(--k-warning) 15%, transparent)' : 'color-mix(in srgb, var(--k-risk) 15%, transparent)',
                    color: score >= 70 ? 'var(--k-success)' : score >= 50 ? 'var(--k-warning)' : 'var(--k-risk)',
                  }}
                />
              ))}
            </Box>
          </GlassCard>
        )}

        {/* Footer */}
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="caption" color="text.secondary">
            KIRO2 — Kişiselleştirilmiş YKS Hazırlık Platformu
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default ParentDashboard;
