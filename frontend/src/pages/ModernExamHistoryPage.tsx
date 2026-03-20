/**
 * Modern Exam History Page
 * Glassmorphism ile sınav geçmişi görüntüleme
 */

import {
  History as HistoryIcon,
  EmojiEvents as TrophyIcon,
  Visibility as ViewIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Schedule as ScheduleIcon,
  AutoGraph as GraphIcon,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Tab,
  Tabs,
  Divider,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import { useNavigate } from 'react-router-dom';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { modernColors } from '../theme/modern-colors';

interface Exam {
  sinav_id: string
  exam_type: string
  subject: string
  question_count: number
  correct_count: number
  wrong_count: number
  empty_count: number
  score: number
  duration: number
  completed_at: string
  status: 'completed' | 'in_progress' | 'abandoned'
}

export const ModernExamHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [exams, setExams] = useState<Exam[]>([]);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    fetchExamHistory();
  }, []);

  const fetchExamHistory = async () => {
    try {
      const response = await fetch('/api/v1/osym-exam/my-exams', {
        credentials: 'include',
      });
      if (!response.ok) {throw new Error();}
      const data = await response.json();
      setExams(data.exams || []);
    } catch {
      // Mock data
      setExams([
        {
          sinav_id: '1',
          exam_type: 'TYT',
          subject: 'Matematik',
          question_count: 40,
          correct_count: 32,
          wrong_count: 5,
          empty_count: 3,
          score: 85,
          duration: 65,
          completed_at: '2025-11-21T10:30:00',
          status: 'completed',
        },
        {
          sinav_id: '2',
          exam_type: 'AYT',
          subject: 'Fizik',
          question_count: 30,
          correct_count: 22,
          wrong_count: 6,
          empty_count: 2,
          score: 75,
          duration: 52,
          completed_at: '2025-11-20T15:45:00',
          status: 'completed',
        },
        {
          sinav_id: '3',
          exam_type: 'TYT',
          subject: 'Türkçe',
          question_count: 40,
          correct_count: 28,
          wrong_count: 8,
          empty_count: 4,
          score: 70,
          duration: 72,
          completed_at: '2025-11-19T14:20:00',
          status: 'completed',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getScoreGradient = (score: number): string => {
    if (score >= 85) {return modernColors.gradients.success;}
    if (score >= 70) {return modernColors.gradients.primary;}
    if (score >= 50) {return modernColors.gradients.warning;}
    return modernColors.gradients.error;
  };

  const getScoreIcon = (score: number) => {
    if (score >= 85) {return '🏆';}
    if (score >= 70) {return '🎯';}
    if (score >= 50) {return '📈';}
    return '💪';
  };

  const completedExams = exams.filter(e => e.status === 'completed');
  const avgScore = completedExams.length > 0
    ? completedExams.reduce((sum, e) => sum + e.score, 0) / completedExams.length
    : 0;

  const totalQuestions = completedExams.reduce((sum, e) => sum + e.question_count, 0);
  const totalCorrect = completedExams.reduce((sum, e) => sum + e.correct_count, 0);

  const filteredExams = tabValue === 0
    ? exams
    : exams.filter(e => e.status === (tabValue === 1 ? 'completed' : 'in_progress'));

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: '16px',
              background: modernColors.gradients.ocean,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2,
            }}
          >
            <HistoryIcon sx={{ fontSize: 32, color: 'white' }} />
          </Box>

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              background: modernColors.gradients.ocean,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
            }}
          >
            Sınav Geçmişi
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Geçmiş sınavlarınızı inceleyin ve performansınızı analiz edin
          </Typography>
        </Box>
      </motion.div>

      {/* İstatistik Kartları */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Toplam Sınav</Typography>
                <HistoryIcon sx={{ color: 'primary.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{completedExams.length}</Typography>
              <Typography variant="caption" color="text.secondary">tamamlandı</Typography>
            </GlassCard>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.15 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Ortalama Puan</Typography>
                <TrophyIcon sx={{ color: 'warning.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{avgScore.toFixed(0)}</Typography>
              <LinearProgress
                variant="determinate"
                value={avgScore}
                sx={{
                  mt: 1,
                  height: 6,
                  borderRadius: 3,
                  background: 'rgba(0,0,0,0.1)',
                  '& .MuiLinearProgress-bar': {
                    background: getScoreGradient(avgScore),
                  },
                }}
              />
            </GlassCard>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Doğru Cevap</Typography>
                <CheckIcon sx={{ color: 'success.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{totalCorrect}</Typography>
              <Typography variant="caption" color="text.secondary">
                / {totalQuestions} soru ({totalQuestions > 0 ? ((totalCorrect / totalQuestions) * 100).toFixed(0) : 0}%)
              </Typography>
            </GlassCard>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.25 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">En Yüksek Puan</Typography>
                <GraphIcon sx={{ color: 'error.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>
                {completedExams.length > 0 ? Math.max(...completedExams.map(e => e.score)) : 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">şimdiye kadarki</Typography>
            </GlassCard>
          </motion.div>
        </Grid>
      </Grid>

      {/* Sınav Listesi */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <GlassCard>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 3 }}>
            <Tab label="Tüm Sınavlar" />
            <Tab label="Tamamlananlar" />
            <Tab label="Devam Edenler" />
          </Tabs>

          <Divider sx={{ mb: 3 }} />

          {loading ? (
            <Box sx={{ py: 4 }}>
              <LinearProgress />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
                Sınavlar yükleniyor...
              </Typography>
            </Box>
          ) : filteredExams.length === 0 ? (
            <Alert severity="info">
              Henüz sınav geçmişiniz bulunmuyor. Yeni bir sınav başlatın!
            </Alert>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {filteredExams.map((exam, index) => (
                <motion.div
                  key={exam.sinav_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + index * 0.05 }}
                >
                  <GlassCard
                    sx={{
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4,
                        transition: 'all 0.3s',
                      },
                    }}
                  >
                    <Grid container spacing={2} alignItems="center">
                      {/* Skor */}
                      <Grid item xs={12} sm={2}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Box
                            sx={{
                              width: 72,
                              height: 72,
                              borderRadius: '50%',
                              background: getScoreGradient(exam.score),
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              justifyContent: 'center',
                              mx: 'auto',
                              mb: 1,
                            }}
                          >
                            <Typography variant="h5" fontWeight={700} color="white">
                              {exam.score}
                            </Typography>
                          </Box>
                          <Typography variant="caption">{getScoreIcon(exam.score)}</Typography>
                        </Box>
                      </Grid>

                      {/* Detaylar */}
                      <Grid item xs={12} sm={6}>
                        <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                          <Chip label={exam.exam_type} size="small" color="primary" />
                          <Chip label={exam.subject} size="small" variant="outlined" />
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ScheduleIcon sx={{ fontSize: 16 }} />
                          {new Date(exam.completed_at).toLocaleDateString('tr-TR', {
                            day: 'numeric',
                            month: 'long',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                          <Typography variant="caption" color="success.main">
                            <CheckIcon sx={{ fontSize: 14, verticalAlign: 'middle' }} /> {exam.correct_count} Doğru
                          </Typography>
                          <Typography variant="caption" color="error.main">
                            <CancelIcon sx={{ fontSize: 14, verticalAlign: 'middle' }} /> {exam.wrong_count} Yanlış
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {exam.empty_count} Boş
                          </Typography>
                        </Box>
                      </Grid>

                      {/* İstatistikler */}
                      <Grid item xs={12} sm={2}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="caption" color="text.secondary">Sorular</Typography>
                          <Typography variant="h6" fontWeight={600}>{exam.question_count}</Typography>
                        </Box>
                      </Grid>

                      {/* Aksiyon */}
                      <Grid item xs={12} sm={2}>
                        <ModernButton
                          fullWidth
                          variant="outlined"
                          size="small"
                          startIcon={<ViewIcon />}
                          onClick={() => navigate(`/exam/${exam.sinav_id}/results`)}
                        >
                          Görüntüle
                        </ModernButton>
                      </Grid>
                    </Grid>
                  </GlassCard>
                </motion.div>
              ))}
            </Box>
          )}
        </GlassCard>
      </motion.div>

      {/* Yeni Sınav Başlat */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <ModernButton
            variant="solid"
            size="large"
            onClick={() => navigate('/exam/start')}
            sx={{
              background: modernColors.gradients.primary,
              px: 6,
            }}
          >
            Yeni Sınav Başlat
          </ModernButton>
        </Box>
      </motion.div>
    </Container>
  );
};

export default ModernExamHistoryPage;
