/**
 * Student Dashboard - Ana Öğrenci Paneli
 *
 * Özellikler:
 * - Öğrenme profili görünümü (64 hibrit kod)
 * - Sınav geçmişi ve performans
 * - Kişiselleştirilmiş içerik önerileri
 * - Günlük çalışma planı
 */

import {
  School as SchoolIcon,
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon,
  Lightbulb as LightbulbIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Avatar,
  Button,
  Alert,
} from '@mui/material';
import * as React from 'react';
import {  useEffect, useState  } from 'react';

// API servisleri
import { examService } from '../../services/examService';
import { learningStyleService } from '../../services/learningStyleService';
import { recommendationService } from '../../services/recommendationService';

// Types
interface StudentProfile {
  student_id: string;
  name: string;
  grade: number;
  hibrit_kod: string;
  vark_profili: {
    visual: number;
    auditory: number;
    reading: number;
    kinesthetic: number;
  };
  felder_silverman_profili: {
    active_reflective: number;
    sensing_intuitive: number;
    visual_verbal: number;
    sequential_global: number;
  };
  guven_seviyesi: number;
}

interface ExamStats {
  total_exams: number;
  avg_net: number;
  best_subject: string;
  weak_subject: string;
  trend: 'up' | 'down' | 'stable';
}

interface Recommendation {
  id: string;
  tip: string;
  title: string;
  source: string;
  duration?: number;
  match_score: number;
}

const StudentDashboard: React.FC = () => {
  // State
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [examStats, setExamStats] = useState<ExamStats | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Veri yükleme
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Öğrenci ID'sini session'dan al (gerçek uygulamada)
      const studentId = localStorage.getItem('student_id') || 'demo_student_123';

      // Paralel veri yükleme
      const [profileData, statsData, recsData] = await Promise.all([
        learningStyleService.detectLearningStyle(studentId),
        examService.getStudentStats() as Promise<unknown>,
        recommendationService.getRecommendations(studentId),
      ]);

      // Safely convert to StudentProfile - add missing required fields
      setProfile({ name: 'Student', ...profileData } as StudentProfile);
      setExamStats(statsData as ExamStats);
      setRecommendations(recsData.slice(0, 5)); // İlk 5 öneri

    } catch (err) {
      console.error('Dashboard veri yükleme hatası:', err);
      setError('Veriler yüklenirken bir hata oluştu. Lütfen tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  };

  // Hibrit kod renklendirme
  const getHibridKodColor = (kod: string): string => {
    const varkPart = kod.charAt(0);
    const colorMap: Record<string, string> = {
      'V': '#2196f3', // Mavi - Visual
      'A': '#f44336', // Kırmızı - Auditory
      'R': '#4caf50', // Yeşil - Reading
      'K': '#ff9800',  // Turuncu - Kinesthetic
    };
    return colorMap[varkPart] || '#757575';
  };

  // VARK skorları görselleştirme
  const renderVarkScores = () => {
    if (!profile) {return null;}

    const { vark_profili } = profile;
    const scores = [
      { label: 'Görsel', value: vark_profili.visual, color: '#2196f3' },
      { label: 'İşitsel', value: vark_profili.auditory, color: '#f44336' },
      { label: 'Okuma', value: vark_profili.reading, color: '#4caf50' },
      { label: 'Kinestetik', value: vark_profili.kinesthetic, color: '#ff9800' },
    ];

    return (
      <Box>
        {scores.map((score) => (
          <Box key={score.label} sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2">{score.label}</Typography>
              <Typography variant="body2" fontWeight="bold">
                {(score.value * 100).toFixed(0)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={score.value * 100}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: '#e0e0e0',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: score.color,
                  borderRadius: 4,
                },
              }}
            />
          </Box>
        ))}
      </Box>
    );
  };

  // Yükleniyor ekranı
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h5" gutterBottom>
            Dashboard yükleniyor...
          </Typography>
          <LinearProgress sx={{ mt: 2, maxWidth: 300, mx: 'auto' }} />
        </Box>
      </Container>
    );
  }

  // Hata ekranı
  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
        <Button
          variant="contained"
          onClick={loadDashboardData}
          sx={{ mt: 2 }}
        >
          Tekrar Dene
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Başlık */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Hoş Geldin, {profile?.name || 'Öğrenci'}! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Günlük çalışma planın ve önerilerinin bir arada
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Sol Kolon - Profil ve Performans */}
        <Grid item xs={12} md={4}>
          {/* Öğrenme Profili */}
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar
                sx={{
                  width: 60,
                  height: 60,
                  bgcolor: getHibridKodColor(profile?.hibrit_kod || 'V-ASVS'),
                  mr: 2,
                }}
              >
                <SchoolIcon fontSize="large" />
              </Avatar>
              <Box>
                <Typography variant="h6" fontWeight="bold">
                  Öğrenme Profilin
                </Typography>
                <Chip
                  label={profile?.hibrit_kod || 'V-ASVS'}
                  size="small"
                  sx={{
                    backgroundColor: getHibridKodColor(profile?.hibrit_kod || 'V-ASVS'),
                    color: 'white',
                    fontWeight: 'bold',
                  }}
                />
              </Box>
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Senin için en uygun öğrenme stilini tespit ettik!
            </Typography>

            {renderVarkScores()}

            <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Güven Seviyesi
              </Typography>
              <Typography variant="h6" fontWeight="bold">
                {((profile?.guven_seviyesi || 0.82) * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Paper>

          {/* Sınav İstatistikleri */}
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Sınav Performansın
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Toplam Sınav
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                {examStats?.total_exams || 0}
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Ortalama Net
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="h4" fontWeight="bold" sx={{ mr: 1 }}>
                  {examStats?.avg_net?.toFixed(1) || '0.0'}
                </Typography>
                {examStats?.trend === 'up' && (
                  <TrendingUpIcon color="success" />
                )}
              </Box>
            </Box>

            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                icon={<TrendingUpIcon />}
                label={`En İyi: ${examStats?.best_subject || 'Matematik'}`}
                color="success"
                size="small"
              />
              <Chip
                label={`Çalışılacak: ${examStats?.weak_subject || 'Fizik'}`}
                color="warning"
                size="small"
              />
            </Box>
          </Paper>
        </Grid>

        {/* Sağ Kolon - Öneriler ve Planlama */}
        <Grid item xs={12} md={8}>
          {/* Bugünkü Plan */}
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CalendarIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" fontWeight="bold">
                Bugünkü Çalışma Planın
              </Typography>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Hedef Süre
                    </Typography>
                    <Typography variant="h5" fontWeight="bold">
                      3 saat
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Konu Sayısı
                    </Typography>
                    <Typography variant="h5" fontWeight="bold">
                      4 konu
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Hedef Net
                    </Typography>
                    <Typography variant="h5" fontWeight="bold">
                      25 net
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>

          {/* Kişiselleştirilmiş Öneriler */}
          <Paper elevation={3} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <LightbulbIcon sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="h6" fontWeight="bold">
                Senin İçin Öneriler
              </Typography>
            </Box>

            {recommendations.length > 0 ? (
              <Grid container spacing={2}>
                {recommendations.map((rec) => (
                  <Grid item xs={12} key={rec.id}>
                    <Card variant="outlined" sx={{
                      '&:hover': {
                        boxShadow: 3,
                        cursor: 'pointer',
                      },
                    }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                              {rec.title}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              {rec.source} • {rec.tip}
                            </Typography>
                            {rec.duration && (
                              <Chip
                                label={`${rec.duration} dakika`}
                                size="small"
                                sx={{ mt: 1 }}
                              />
                            )}
                          </Box>
                          <Chip
                            label={`${(rec.match_score * 100).toFixed(0)}% uyum`}
                            color="primary"
                            size="small"
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Alert severity="info">
                Henüz önerin yok. Biraz daha çalışma yaptıkça sana özel öneriler göreceğiz!
              </Alert>
            )}

            <Button
              variant="outlined"
              fullWidth
              sx={{ mt: 2 }}
              startIcon={<AssignmentIcon />}
            >
              Tüm Önerileri Gör
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default StudentDashboard;
