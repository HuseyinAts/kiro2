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
          <School sx={{ fontSize: 48, color: '#6366f1', mb: 2 }} />
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

  if (!data) return null;

  const progressPercent = data.totalTopics > 0
    ? Math.round((data.completedTopics / data.totalTopics) * 100)
    : 0;

  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #fff7ed 100%)',
      py: 4,
    }}>
      <Container maxWidth="md">
        {/* Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Box sx={{
            width: 64,
            height: 64,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
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
            <Box sx={{ p: 2, borderRadius: 2, bgcolor: '#f97316' + '10', textAlign: 'center' }}>
              <LocalFireDepartment sx={{ fontSize: 28, color: '#f97316', mb: 0.5 }} />
              <Typography variant="h5" fontWeight={800} sx={{ color: '#f97316' }}>
                {data.streak}
              </Typography>
              <Typography variant="caption" fontWeight={600} color="text.secondary">
                günlük seri
              </Typography>
            </Box>

            {/* Today study */}
            <Box sx={{ p: 2, borderRadius: 2, bgcolor: '#3b82f6' + '10', textAlign: 'center' }}>
              <Timer sx={{ fontSize: 28, color: '#3b82f6', mb: 0.5 }} />
              <Typography variant="h5" fontWeight={800} sx={{ color: '#3b82f6' }}>
                {data.todayStudyMinutes} dk
              </Typography>
              <Typography variant="caption" fontWeight={600} color="text.secondary">
                bugün çalışma
              </Typography>
            </Box>

            {/* Completed */}
            <Box sx={{ p: 2, borderRadius: 2, bgcolor: '#22c55e' + '10', textAlign: 'center' }}>
              <CheckCircle sx={{ fontSize: 28, color: '#22c55e', mb: 0.5 }} />
              <Typography variant="h5" fontWeight={800} sx={{ color: '#22c55e' }}>
                {data.completedTopics}
              </Typography>
              <Typography variant="caption" fontWeight={600} color="text.secondary">
                tamamlanan konu
              </Typography>
            </Box>

            {/* Progress */}
            <Box sx={{ p: 2, borderRadius: 2, bgcolor: '#8b5cf6' + '10', textAlign: 'center' }}>
              <TrendingUp sx={{ fontSize: 28, color: '#8b5cf6', mb: 0.5 }} />
              <Typography variant="h5" fontWeight={800} sx={{ color: '#8b5cf6' }}>
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
              <Warning sx={{ color: '#f59e0b' }} />
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
                        color: w.trend === 'improving' ? '#22c55e' : w.trend === 'declining' ? '#ef4444' : '#94a3b8',
                        bgcolor: w.trend === 'improving' ? '#22c55e10' : w.trend === 'declining' ? '#ef444410' : '#94a3b810',
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
              <CalendarToday sx={{ color: '#3b82f6' }} />
              Son Quiz Sonuçları
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {data.recentQuizScores.map((score, i) => (
                <Chip
                  key={i}
                  label={`%${score}`}
                  sx={{
                    fontWeight: 700,
                    bgcolor: score >= 70 ? '#22c55e15' : score >= 50 ? '#f59e0b15' : '#ef444415',
                    color: score >= 70 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444',
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
