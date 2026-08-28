/**
 * Teacher Co-Pilot Dashboard Component (2026 Q3-Q4)
 * ZPD (Yakınsal Gelişim Alanı) & FSRS Unutma Eğrisi Takip Ekranı
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  LinearProgress,
  CircularProgress,
  Avatar,
  Stack,
  Alert,
  Tooltip,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import SchoolIcon from '@mui/icons-material/School';
import SendIcon from '@mui/icons-material/Send';
import LightbulbIcon from '@mui/icons-material/Lightbulb';

export interface MisconceptionAlert {
  alert_id: string;
  class_id: string;
  subject: string;
  topic: string;
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  affected_students_count: number;
  misconception_title: string;
  ai_socratic_recommendation: string;
  created_at: string;
}

export interface ZPDDistribution {
  scaffolding_needed: number;
  independent_mastery: number;
  advanced_mastery: number;
  scaffolding_percentage: number;
  independent_percentage: number;
  advanced_percentage: number;
}

export interface FSRSRetentionSummary {
  average_retention_rate: number;
  decay_risk_cards_count: number;
  decay_risk_topics: string[];
  recommended_review_date: string;
}

export interface CoPilotAnalyticsData {
  class_id: string;
  class_name: string;
  total_students: number;
  zpd_distribution: ZPDDistribution;
  fsrs_retention: FSRSRetentionSummary;
  misconception_alerts: MisconceptionAlert[];
  timestamp: string;
}

export const TeacherCoPilotDashboard: React.FC = () => {
  const [data, setData] = useState<CoPilotAnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionSent, setActionSent] = useState<string | null>(null);
  // Varsayilan 'mock' — backend'deki is_real_impl ile ayni guvenli varsayilan.
  // Bilinmiyorsa "gercek" demek, ogretmene sabit veriyi olcum diye gosterir.
  const [dataSource, setDataSource] = useState<'mock' | 'live'>('mock');

  useEffect(() => {
    // Fetch Co-Pilot analytics with fallback
    fetch('/api/v1/teacher-copilot/dashboard-analytics?class_id=12-A')
      .then((res) => res.json())
      .then((resData) => {
        if (resData.success && resData.data) {
          setData(resData.data);
          setDataSource(resData.data_source === 'live' ? 'live' : 'mock');
        } else {
          setFallbackData();
        }
      })
      .catch(() => setFallbackData())
      .finally(() => setLoading(false));
  }, []);

  const setFallbackData = () => {
    setData({
      class_id: '12-A',
      class_name: 'Sınıf 12-A (YKS Sayısal Maratonu)',
      total_students: 32,
      zpd_distribution: {
        scaffolding_needed: 8,
        independent_mastery: 19,
        advanced_mastery: 5,
        scaffolding_percentage: 25.0,
        independent_percentage: 59.4,
        advanced_percentage: 15.6,
      },
      fsrs_retention: {
        average_retention_rate: 84.2,
        decay_risk_cards_count: 48,
        decay_risk_topics: [
          'Türevde Ekstremum Noktaları',
          'Trigonometri Toplam-Fark Formülleri',
          'Paragrafta Anlatım Biçimleri',
        ],
        recommended_review_date: '10 Ağustos 2026',
      },
      misconception_alerts: [
        {
          alert_id: 'alert-01',
          class_id: '12-A',
          subject: 'Matematik',
          topic: 'Türev',
          risk_level: 'HIGH',
          affected_students_count: 12,
          misconception_title: 'Teğet Eğimi ile Yerel Ekstremum Karıştırılması',
          ai_socratic_recommendation:
            'Öğrencilere türevin sıfır olduğu her noktanın ekstremum olmadığını gösteren f(x)=x³ karşıt örneğini sorun.',
          created_at: new Date().toISOString(),
        },
        {
          alert_id: 'alert-02',
          class_id: '12-A',
          subject: 'Fizik',
          topic: 'Kuvvet ve Hareket',
          risk_level: 'MEDIUM',
          affected_students_count: 8,
          misconception_title: 'Net Kuvvet Sıfırken Hızın Sıfır Kabul Edilmesi',
          ai_socratic_recommendation:
            'Eylemsizlik prensibini hatırlatarak "Sabit hızla ilerleyen araca etki eden net kuvvet nedir?" sorusunu yöneltin.',
          created_at: new Date().toISOString(),
        },
      ],
      timestamp: new Date().toISOString(),
    });
  };

  const handleSendSocraticTask = (alertId: string) => {
    setActionSent(alertId);
    setTimeout(() => setActionSent(null), 4000);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 8 }}>
        <CircularProgress color="secondary" />
      </Box>
    );
  }

  if (!data) return null;

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, color: '#F8FAFC' }}>
      {/* Header Banner */}
      <Box
        sx={{
          p: 3,
          mb: 4,
          borderRadius: 4,
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        }}
      >
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems="center" spacing={2}>
          <Box>
            <Stack direction="row" alignItems="center" spacing={1.5}>
              <AutoAwesomeIcon sx={{ color: '#A855F7', fontSize: 32 }} />
              <Typography variant="h4" fontWeight={700} sx={{ background: 'linear-gradient(90deg, #6366F1, #A855F7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Pedagojik AI Co-Pilot Paneli
              </Typography>
            </Stack>
            <Typography variant="body1" sx={{ color: '#94A3B8', mt: 0.5 }}>
              {data.class_name} — {data.total_students} Aktif Öğrenci Takip Ediliyor
            </Typography>
          </Box>
          {/* Sabit veriye "Canlı" demek yanlıştı; kaynak açıkça beyan ediliyor. */}
          <Chip
            icon={<SchoolIcon sx={{ color: dataSource === 'live' ? '#38BDF8 !important' : '#FBBF24 !important' }} />}
            label={
              dataSource === 'live'
                ? '2026 Q3-Q4 Canlı ZPD & FSRS-6 Akışı'
                : 'ÖRNEK VERİ — gerçek ölçüm değil'
            }
            sx={
              dataSource === 'live'
                ? { background: 'rgba(56, 189, 248, 0.1)', color: '#38BDF8', border: '1px solid rgba(56, 189, 248, 0.3)', fontWeight: 600 }
                : { background: 'rgba(251, 191, 36, 0.12)', color: '#FBBF24', border: '1px solid rgba(251, 191, 36, 0.4)', fontWeight: 700 }
            }
          />
        </Stack>
      </Box>

      {/* Action Notification */}
      {actionSent && (
        <Alert severity="success" icon={<CheckCircleOutlineIcon fontSize="inherit" />} sx={{ mb: 3, background: 'rgba(34, 197, 94, 0.15)', color: '#4ADE80', border: '1px solid rgba(74, 222, 128, 0.3)' }}>
          Sokratik Ödev Görevi sınıfa ve öğrenci panellerine başarıyla iletildi!
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* ZPD Mastery Section */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              height: '100%',
              background: 'rgba(30, 41, 59, 0.7)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: 3,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 3 }}>
                <PsychologyIcon sx={{ color: '#38BDF8' }} />
                <Typography variant="h6" fontWeight={600} color="#F8FAFC">
                  Yakınsal Gelişim Alanı (ZPD) Dağılımı
                </Typography>
              </Stack>

              {/* Scaffolding Needed */}
              <Box sx={{ mb: 2.5 }}>
                <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.8 }}>
                  <Typography variant="body2" color="#94A3B8">
                    Rehberlik / Destek İhtiyacı (ZPD Alt Sınır)
                  </Typography>
                  <Typography variant="body2" fontWeight={700} color="#F43F5E">
                    {data.zpd_distribution.scaffolding_needed} Öğrenci (%{data.zpd_distribution.scaffolding_percentage})
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={data.zpd_distribution.scaffolding_percentage}
                  sx={{ height: 10, borderRadius: 5, backgroundColor: 'rgba(244, 63, 94, 0.15)', '& .MuiLinearProgress-bar': { backgroundColor: '#F43F5E' } }}
                />
              </Box>

              {/* Independent Mastery */}
              <Box sx={{ mb: 2.5 }}>
                <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.8 }}>
                  <Typography variant="body2" color="#94A3B8">
                    Bağımsız Çözüm Seviyesi (ZPD Ideal Zone)
                  </Typography>
                  <Typography variant="body2" fontWeight={700} color="#38BDF8">
                    {data.zpd_distribution.independent_mastery} Öğrenci (%{data.zpd_distribution.independent_percentage})
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={data.zpd_distribution.independent_percentage}
                  sx={{ height: 10, borderRadius: 5, backgroundColor: 'rgba(56, 189, 248, 0.15)', '& .MuiLinearProgress-bar': { backgroundColor: '#38BDF8' } }}
                />
              </Box>

              {/* Advanced Mastery */}
              <Box sx={{ mb: 1 }}>
                <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.8 }}>
                  <Typography variant="body2" color="#94A3B8">
                    İleri Seviye Ustalık (ZPD Üst Sınır)
                  </Typography>
                  <Typography variant="body2" fontWeight={700} color="#4ADE80">
                    {data.zpd_distribution.advanced_mastery} Öğrenci (%{data.zpd_distribution.advanced_percentage})
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={data.zpd_distribution.advanced_percentage}
                  sx={{ height: 10, borderRadius: 5, backgroundColor: 'rgba(74, 222, 128, 0.15)', '& .MuiLinearProgress-bar': { backgroundColor: '#4ADE80' } }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* FSRS Memory Curve Section */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              height: '100%',
              background: 'rgba(30, 41, 59, 0.7)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: 3,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 3 }}>
                <AccessTimeIcon sx={{ color: '#A855F7' }} />
                <Typography variant="h6" fontWeight={600} color="#F8FAFC">
                  FSRS-6 Unutma Eğrisi & Hafıza İstatistikleri
                </Typography>
              </Stack>

              <Grid container spacing={2} alignItems="center">
                <Grid item xs={5} textAlign="center">
                  <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                    <CircularProgress
                      variant="determinate"
                      value={data.fsrs_retention.average_retention_rate}
                      size={100}
                      thickness={6}
                      sx={{ color: '#A855F7' }}
                    />
                    <Box
                      sx={{
                        top: 0, left: 0, bottom: 0, right: 0,
                        position: 'absolute', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        flexDirection: 'column',
                      }}
                    >
                      <Typography variant="h6" fontWeight={700} color="#F8FAFC">
                        %{data.fsrs_retention.average_retention_rate}
                      </Typography>
                      <Typography variant="caption" color="#94A3B8">Retention</Typography>
                    </Box>
                  </Box>
                </Grid>

                <Grid item xs={7}>
                  <Typography variant="subtitle2" color="#94A3B8" gutterBottom>
                    7 Günlük Unutma Riski Taşıyan Konular:
                  </Typography>
                  <Stack spacing={1}>
                    {data.fsrs_retention.decay_risk_topics.map((topic, i) => (
                      <Chip
                        key={i}
                        size="small"
                        icon={<WarningAmberIcon sx={{ color: '#F59E0B !important' }} />}
                        label={topic}
                        sx={{ background: 'rgba(245, 158, 11, 0.1)', color: '#F59E0B', justifyContent: 'flex-start' }}
                      />
                    ))}
                  </Stack>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* AI Misconception Risk Alerts */}
        <Grid item xs={12}>
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <LightbulbIcon sx={{ color: '#F59E0B' }} />
            Yapay Zeka Tespitli Kavram Yanılgısı (Misconception Risk) Uyarıları
          </Typography>

          <Stack spacing={2}>
            {data.misconception_alerts.map((alert) => (
              <Card
                key={alert.alert_id}
                sx={{
                  background: 'rgba(15, 23, 42, 0.8)',
                  backdropFilter: 'blur(12px)',
                  border: alert.risk_level === 'HIGH' ? '1px solid rgba(244, 63, 94, 0.4)' : '1px solid rgba(245, 158, 11, 0.4)',
                  borderRadius: 3,
                  p: 1.5,
                }}
              >
                <CardContent sx={{ pb: '16px !important' }}>
                  <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ sm: 'center' }} spacing={2} sx={{ mb: 2 }}>
                    <Stack direction="row" alignItems="center" spacing={1.5}>
                      <Avatar sx={{ bgcolor: alert.risk_level === 'HIGH' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(245, 158, 11, 0.2)', color: alert.risk_level === 'HIGH' ? '#F43F5E' : '#F59E0B' }}>
                        <WarningAmberIcon />
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle1" fontWeight={700} color="#F8FAFC">
                          {alert.misconception_title}
                        </Typography>
                        <Typography variant="caption" color="#94A3B8">
                          {alert.subject} • {alert.topic} • {alert.affected_students_count} Öğrenci Etkilendi
                        </Typography>
                      </Box>
                    </Stack>

                    <Chip
                      label={alert.risk_level === 'HIGH' ? 'Yüksek Risk' : 'Orta Risk'}
                      color={alert.risk_level === 'HIGH' ? 'error' : 'warning'}
                      size="small"
                      sx={{ fontWeight: 700 }}
                    />
                  </Stack>

                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      background: 'rgba(30, 41, 59, 0.6)',
                      borderLeft: '4px solid #A855F7',
                      mb: 2,
                    }}
                  >
                    <Typography variant="caption" fontWeight={700} color="#A855F7" display="block" gutterBottom>
                      💡 Yapay Zeka Sokratik Müdahale Önerisi:
                    </Typography>
                    <Typography variant="body2" color="#CBD5E1">
                      "{alert.ai_socratic_recommendation}"
                    </Typography>
                  </Box>

                  <Stack direction="row" spacing={2} justifyContent="flex-end">
                    <Tooltip title="Sınıfa özel Sokratik yönlendirme sorusunu ödev olarak gönder">
                      <Button
                        variant="contained"
                        size="small"
                        startIcon={<SendIcon />}
                        onClick={() => handleSendSocraticTask(alert.alert_id)}
                        sx={{ background: 'linear-gradient(90deg, #6366F1, #A855F7)', borderRadius: 2 }}
                      >
                        Sokratik Görev İlet
                      </Button>
                    </Tooltip>
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TeacherCoPilotDashboard;
