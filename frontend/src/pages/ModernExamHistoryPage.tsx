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

// Mirrors backend ExamSessionResponse (backend/api/sinav.py) exactly — that
// endpoint has no subject/score/correct_count/wrong_count/empty_count fields,
// so this page only shows what /my-exams genuinely returns. The detailed
// per-exam score breakdown lives on ModernExamResultsPage ("Sonuçları
// Görüntüle"), which fetches it from /performance + /subject-performance.
type ExamStatus = 'not_started' | 'in_progress' | 'completed' | 'abandoned' | 'expired';

interface Exam {
  session_id: string
  exam_type: string
  status: ExamStatus
  total_questions: number
  duration_minutes: number
  started_at: string | null
  completed_at: string | null
}

const STATUS_LABEL: Record<ExamStatus, string> = {
  not_started: 'Başlanmadı',
  in_progress: 'Devam Ediyor',
  completed: 'Tamamlandı',
  abandoned: 'Yarım Bırakıldı',
  expired: 'Süresi Doldu',
};

const STATUS_COLOR: Record<ExamStatus, 'default' | 'success' | 'warning' | 'error'> = {
  not_started: 'default',
  in_progress: 'warning',
  completed: 'success',
  abandoned: 'error',
  expired: 'error',
};

export const ModernExamHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [exams, setExams] = useState<Exam[]>([]);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    fetchExamHistory();
  }, []);

  const fetchExamHistory = async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const response = await fetch('/api/v1/osym-exam/my-exams', {
        credentials: 'include',
      });
      if (!response.ok) {throw new Error('Sınav geçmişi alınamadı');}
      const data: Exam[] = await response.json();
      setExams(data);
    } catch {
      setExams([]);
      setFetchError('Sınav geçmişi yüklenirken bir hata oluştu. Lütfen tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  };

  const completedExams = exams.filter(e => e.status === 'completed');
  const inProgressExams = exams.filter(e => e.status === 'in_progress');
  const totalQuestions = exams.reduce((sum, e) => sum + (e.total_questions || 0), 0);

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
              <Typography variant="h4" fontWeight={700}>{exams.length}</Typography>
              <Typography variant="caption" color="text.secondary">kayıtlı oturum</Typography>
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
                <Typography variant="body2" color="text.secondary">Tamamlanan</Typography>
                <TrophyIcon sx={{ color: 'warning.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{completedExams.length}</Typography>
              <Typography variant="caption" color="text.secondary">sınav</Typography>
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
                <Typography variant="body2" color="text.secondary">Devam Eden</Typography>
                <ScheduleIcon sx={{ color: 'info.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{inProgressExams.length}</Typography>
              <Typography variant="caption" color="text.secondary">sınav</Typography>
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
                <Typography variant="body2" color="text.secondary">Toplam Soru</Typography>
                <GraphIcon sx={{ color: 'error.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{totalQuestions}</Typography>
              <Typography variant="caption" color="text.secondary">tüm oturumlarda</Typography>
            </GlassCard>
          </motion.div>
        </Grid>
      </Grid>

      {fetchError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setFetchError(null)}>
          {fetchError}
        </Alert>
      )}

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
            !fetchError && (
              <Alert severity="info">
                Henüz sınav geçmişiniz bulunmuyor. Yeni bir sınav başlatın!
              </Alert>
            )
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {filteredExams.map((exam, index) => {
                const displayDate = exam.completed_at || exam.started_at;
                return (
                <motion.div
                  key={exam.session_id}
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
                      {/* Durum */}
                      <Grid item xs={12} sm={2}>
                        <Box sx={{ textAlign: 'center' }}>
                          {exam.status === 'completed' ? (
                            <CheckIcon sx={{ fontSize: 40, color: 'success.main' }} />
                          ) : exam.status === 'in_progress' ? (
                            <ScheduleIcon sx={{ fontSize: 40, color: 'warning.main' }} />
                          ) : (
                            <CancelIcon sx={{ fontSize: 40, color: 'error.main' }} />
                          )}
                          <Chip
                            label={STATUS_LABEL[exam.status]}
                            size="small"
                            color={STATUS_COLOR[exam.status]}
                            sx={{ mt: 0.5, display: 'block' }}
                          />
                        </Box>
                      </Grid>

                      {/* Detaylar */}
                      <Grid item xs={12} sm={6}>
                        <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                          <Chip label={exam.exam_type} size="small" color="primary" />
                        </Box>
                        {displayDate && (
                          <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <ScheduleIcon sx={{ fontSize: 16 }} />
                            {new Date(displayDate).toLocaleDateString('tr-TR', {
                              day: 'numeric',
                              month: 'long',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </Typography>
                        )}
                        <Typography variant="caption" color="text.secondary">
                          Süre: {exam.duration_minutes} dk
                        </Typography>
                      </Grid>

                      {/* İstatistikler */}
                      <Grid item xs={12} sm={2}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="caption" color="text.secondary">Sorular</Typography>
                          <Typography variant="h6" fontWeight={600}>{exam.total_questions}</Typography>
                        </Box>
                      </Grid>

                      {/* Aksiyon */}
                      <Grid item xs={12} sm={2}>
                        <ModernButton
                          fullWidth
                          variant="outlined"
                          size="small"
                          startIcon={<ViewIcon />}
                          onClick={() => navigate(
                            exam.status === 'in_progress'
                              ? `/exam/${exam.session_id}`
                              : `/exam/${exam.session_id}/results`,
                          )}
                        >
                          {exam.status === 'in_progress' ? 'Devam Et' : 'Görüntüle'}
                        </ModernButton>
                      </Grid>
                    </Grid>
                  </GlassCard>
                </motion.div>
                );
              })}
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
