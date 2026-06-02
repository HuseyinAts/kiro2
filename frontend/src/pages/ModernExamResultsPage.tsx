/**
 * Modern Exam Results Page
 * Glassmorphism ile detaylı sınav sonuçları analizi
 */

import {
  Assessment as AssessmentIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  HelpOutline as EmptyIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Replay as ReplayIcon,
  Home as HomeIcon,
  EmojiEvents as TrophyIcon,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { modernColors } from '../theme/modern-colors';
import { apiRequest } from '../utils/apiHelpers';

interface ExamResult {
  sinav_id: string
  exam_type: string
  subject: string
  question_count: number
  correct_count: number
  wrong_count: number
  empty_count: number
  score: number
  duration: number
  duration_limit: number
  completed_at: string
  questions: Array<{
    question_id: string
    question_text: string
    user_answer: string | null
    correct_answer: string
    is_correct: boolean
    time_spent: number
  }>
  subject_breakdown: Array<{
    subject: string
    correct: number
    wrong: number
    empty: number
    total: number
  }>
}

export const ModernExamResultsPage: React.FC = () => {
  const { sinavId } = useParams<{ sinavId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<ExamResult | null>(null);

  useEffect(() => {
    if (sinavId) {
      fetchExamResults();
    }
  }, [sinavId]);

  const fetchExamResults = async () => {
    try {
      const perfData = await apiRequest(`/api/v1/osym-exam/${sinavId}/performance`);

      let subjectData: any[] = [];
      let sessionData: any = null;
      // allSettled: ders kırılımı (subject-performance) ile oturum bilgisi
      // (session) BAĞIMSIZ alınır. Promise.all idi → session 404'ü tüm bloğu
      // reject edip ders kırılımını siliyordu (D3 bug).
      const [subjRes, sessRes] = await Promise.allSettled([
        apiRequest(`/api/v1/osym-exam/${sinavId}/subject-performance`),
        apiRequest(`/api/v1/osym-exam/${sinavId}/session`),
      ]);
      if (subjRes.status === 'fulfilled' && Array.isArray(subjRes.value)) {
        subjectData = subjRes.value;
      }
      if (sessRes.status === 'fulfilled') {
        sessionData = sessRes.value;
      }

      // Gerçek geçen süreyi hesapla (dakika)
      let durationMinutes = 0;
      if (sessionData?.started_at && sessionData?.completed_at) {
        const start = new Date(sessionData.started_at).getTime();
        const end = new Date(sessionData.completed_at).getTime();
        durationMinutes = Math.round((end - start) / 60000);
      }

      setResult({
        sinav_id: sinavId!,
        exam_type: (sessionData?.exam_type || 'tyt').toUpperCase(),
        subject: '',
        question_count: perfData.total_questions,
        correct_count: perfData.correct_answers,
        wrong_count: perfData.wrong_answers,
        empty_count: perfData.empty_answers,
        score: perfData.raw_score,
        duration: durationMinutes,
        duration_limit: sessionData?.duration_minutes || 0,
        completed_at: sessionData?.completed_at || new Date().toISOString(),
        questions: [],
        subject_breakdown: subjectData.map((s: any) => ({
          subject: s.subject,
          correct: s.correct_answers,
          wrong: s.wrong_answers,
          empty: s.empty_answers,
          total: s.total_questions,
        })),
      });
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  if (!sinavId) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Sınav ID bulunamadı</Alert>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <LinearProgress />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
          Sonuçlar yükleniyor...
        </Typography>
      </Container>
    );
  }

  if (!result) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Sonuçlar yüklenemedi</Alert>
      </Container>
    );
  }

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

  const getScoreMessage = (score: number) => {
    if (score >= 85) {return 'Mükemmel! Harika bir performans sergiledinizyürümeye devam edin!';}
    if (score >= 70) {return 'Çok iyi! Biraz daha çalışarak daha da iyiye gidebilirsiniz.';}
    if (score >= 50) {return 'İyi bir başlangıç! Eksik konularınızı çalışmaya devam edin.';}
    return 'Daha fazla çalışmanız gerekiyor. Pes etmeyin, başarısız olabilirsiniz!';
  };

  const successRate = result.question_count > 0
    ? ((result.correct_count / result.question_count) * 100).toFixed(1)
    : '0.0';
  const avgTimePerQuestion = result.question_count > 0
    ? (result.duration / result.question_count).toFixed(1)
    : '0.0';

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
              background: getScoreGradient(result.score),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2,
            }}
          >
            <AssessmentIcon sx={{ fontSize: 32, color: 'white' }} />
          </Box>

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              background: getScoreGradient(result.score),
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
            }}
          >
            Sınav Sonuçları {getScoreIcon(result.score)}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip label={result.exam_type} size="small" color="primary" />
            <Chip label={result.subject} size="small" variant="outlined" />
            <Typography variant="caption" color="text.secondary">
              {new Date(result.completed_at).toLocaleDateString('tr-TR', {
                day: 'numeric',
                month: 'long',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </Typography>
          </Box>
        </Box>
      </motion.div>

      {/* Ana Skor Kartı */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
      >
        <GlassCard sx={{ mb: 3, textAlign: 'center', py: 4 }}>
          <Box
            sx={{
              width: 120,
              height: 120,
              borderRadius: '50%',
              background: getScoreGradient(result.score),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 2,
            }}
          >
            <Typography variant="h2" fontWeight={700} color="white">
              {result.score}
            </Typography>
          </Box>

          <Typography variant="h6" gutterBottom>{getScoreMessage(result.score)}</Typography>

          <Grid container spacing={2} sx={{ mt: 3 }}>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">Doğru</Typography>
              <Typography variant="h5" fontWeight={600} color="success.main">
                <CheckIcon sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                {result.correct_count}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">Yanlış</Typography>
              <Typography variant="h5" fontWeight={600} color="error.main">
                <CancelIcon sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                {result.wrong_count}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">Boş</Typography>
              <Typography variant="h5" fontWeight={600} color="text.secondary">
                <EmptyIcon sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                {result.empty_count}
              </Typography>
            </Grid>
          </Grid>
        </GlassCard>
      </motion.div>

      {/* İstatistikler */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Başarı Oranı</Typography>
                <TrendingUpIcon sx={{ color: 'success.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{successRate}%</Typography>
              <LinearProgress
                variant="determinate"
                value={parseFloat(successRate)}
                sx={{
                  mt: 1,
                  height: 6,
                  borderRadius: 3,
                  background: 'rgba(0,0,0,0.1)',
                  '& .MuiLinearProgress-bar': {
                    background: getScoreGradient(result.score),
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
            transition={{ delay: 0.25 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Toplam Süre</Typography>
                <SpeedIcon sx={{ color: 'primary.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{result.duration}<Typography variant="caption">dk</Typography></Typography>
              <Typography variant="caption" color="text.secondary">
                {result.duration_limit || result.duration} dakika limit
              </Typography>
            </GlassCard>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Ort. Süre/Soru</Typography>
                <SpeedIcon sx={{ color: 'warning.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{avgTimePerQuestion}<Typography variant="caption">dk</Typography></Typography>
              <Typography variant="caption" color="text.secondary">
                soru başına
              </Typography>
            </GlassCard>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.35 }}
          >
            <GlassCard>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">Toplam Soru</Typography>
                <TrophyIcon sx={{ color: 'error.main' }} />
              </Box>
              <Typography variant="h4" fontWeight={700}>{result.question_count}</Typography>
              <Typography variant="caption" color="text.secondary">
                soru çözüldü
              </Typography>
            </GlassCard>
          </motion.div>
        </Grid>
      </Grid>

      {/* Konu Bazlı Analiz */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <GlassCard sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
            Konu Bazlı Performans
          </Typography>

          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Konu</strong></TableCell>
                <TableCell align="center"><strong>Doğru</strong></TableCell>
                <TableCell align="center"><strong>Yanlış</strong></TableCell>
                <TableCell align="center"><strong>Boş</strong></TableCell>
                <TableCell align="center"><strong>Başarı</strong></TableCell>
                <TableCell><strong>Durum</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {result.subject_breakdown.map((item, index) => {
                const success = item.total > 0 ? ((item.correct / item.total) * 100).toFixed(0) : '0';
                return (
                  <TableRow key={index}>
                    <TableCell>{item.subject}</TableCell>
                    <TableCell align="center">
                      <Chip label={item.correct} size="small" color="success" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label={item.wrong} size="small" color="error" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label={item.empty} size="small" />
                    </TableCell>
                    <TableCell align="center">{success}%</TableCell>
                    <TableCell>
                      <LinearProgress
                        variant="determinate"
                        value={parseFloat(success)}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          background: 'rgba(0,0,0,0.1)',
                          '& .MuiLinearProgress-bar': {
                            background: getScoreGradient(parseFloat(success)),
                          },
                        }}
                      />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </GlassCard>
      </motion.div>

      {/* Aksiyonlar */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <ModernButton
            variant="solid"
            startIcon={<ReplayIcon />}
            onClick={() => navigate('/exam/start')}
            sx={{ background: modernColors.gradients.primary }}
          >
            Yeni Sınav Başlat
          </ModernButton>
          <ModernButton
            variant="outlined"
            startIcon={<HomeIcon />}
            onClick={() => navigate('/dashboard')}
          >
            Ana Sayfaya Dön
          </ModernButton>
        </Box>
      </motion.div>
    </Container>
  );
};

export default ModernExamResultsPage;
