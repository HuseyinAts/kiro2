/**
 * Modern Sınav Sonuçları
 * Glassmorphism tasarım ile detaylı performans analizi
 */

import {
  Assessment,
  CheckCircle,
  Cancel,
  Timer,
  Star,
  School,
  Refresh,
  Download,
  Insights,
  EmojiEvents,
} from '@mui/icons-material';
import {
  Box,
  Container,
  Typography,
  Grid,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { advancedReportsService } from '../../services/advancedReportsService';
import { examService } from '../../services/examService';
import { SinavSonucu, performanceToSinavSonucu } from '../../types';
import { StaggerContainer, StaggerItem } from '@/components/Animations/PageTransition';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { ModernLoader } from '@/components/ui/ModernLoader';
import modernColors from '@/theme/modern-colors';

interface ModernExamResultsProps {
  sessionId: string
  onRetake?: () => void
}

export const ModernExamResults: React.FC<ModernExamResultsProps> = ({ sessionId, onRetake }) => {
  const [sonuc, setSonuc] = useState<SinavSonucu | null>(null);
  const [_gelismisRapor, setGelismisRapor] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [_activeTab, _setActiveTab] = useState(0);
  const [pdfGenerating, setPdfGenerating] = useState(false);

  useEffect(() => {
    loadResults();
  }, [sessionId]);

  const loadResults = async () => {
    try {
      setLoading(true);
      setError(null);

      const [sonucData, gelismisRaporData] = await Promise.allSettled([
        examService.getExamResult(sessionId),
        advancedReportsService.getAdvancedExamReport(sessionId),
      ]);

      if (sonucData.status === 'fulfilled') {
        // Convert PerformanceResponse to SinavSonucu
        const convertedSonuc = performanceToSinavSonucu(sonucData.value, sessionId);
        setSonuc(convertedSonuc);
      } else {
        throw new Error('Sınav sonucu yüklenemedi');
      }

      if (gelismisRaporData.status === 'fulfilled') {
        setGelismisRapor(gelismisRaporData.value);
      }
    } catch (err: any) {
      setError(err.message || 'Sonuçlar yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePDF = async () => {
    try {
      setPdfGenerating(true);
      const result = await advancedReportsService.generatePDFReport(sessionId);

      setTimeout(async () => {
        const blob = await advancedReportsService.downloadPDFReport(result.pdf_filename);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = result.pdf_filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 3000);
    } catch (err) {
      console.error('PDF oluşturma hatası:', err);
    } finally {
      setPdfGenerating(false);
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.primary,
        }}
      >
        <ModernLoader message="Sonuçlar analiz ediliyor..." size="large" />
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.primary,
          p: 2,
        }}
      >
        <GlassCard glassIntensity="medium" elevated>
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="h6">Hata</Typography>
            <Typography>{error}</Typography>
          </Alert>
          <ModernButton variant="gradient" gradient={modernColors.gradients.primary} onClick={loadResults}>
            Tekrar Dene
          </ModernButton>
        </GlassCard>
      </Box>
    );
  }

  if (!sonuc) {
    return null;
  }

  const getPerformanceGradient = (score: number): string => {
    if (score >= 80) {return modernColors.gradients.success;}
    if (score >= 60) {return modernColors.gradients.warning;}
    return modernColors.gradients.error;
  };

  const totalQuestions = sonuc.toplam_soru || 0;
  const correctAnswers = sonuc.dogru_sayisi || 0;
  const wrongAnswers = sonuc.yanlis_sayisi || 0;
  const emptyAnswers = sonuc.bos_sayisi || 0;
  const scorePercentage = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.lightBlue,
        py: 4,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Animated Background */}
      <motion.div
        style={{
          position: 'absolute',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.1)',
          top: '-200px',
          right: '-150px',
          filter: 'blur(80px)',
        }}
        animate={{
          scale: [1, 1.2, 1],
          rotate: [0, 90, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
        <StaggerContainer>
          {/* Header */}
          <StaggerItem>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 10 }}
              >
                <Box
                  sx={{
                    width: 120,
                    height: 120,
                    borderRadius: '30px',
                    background: getPerformanceGradient(scorePercentage),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto',
                    boxShadow: modernColors.shadow.modern,
                    color: 'white',
                  }}
                >
                  <EmojiEvents sx={{ fontSize: 64 }} />
                </Box>
              </motion.div>

              <Typography
                variant="h3"
                sx={{
                  fontWeight: 800,
                  mt: 3,
                  background: getPerformanceGradient(scorePercentage),
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Tebrikler!
              </Typography>
              <Typography variant="h5" color="text.secondary" sx={{ mt: 1 }}>
                {sonuc.sinav_tipi} Sınavını Tamamladınız
              </Typography>
            </Box>
          </StaggerItem>

          {/* Score Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<Star sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.warning}
                  hoverable
                >
                  <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {Math.round(scorePercentage)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Başarı Yüzdesi
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<CheckCircle sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.success}
                  hoverable
                >
                  <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {correctAnswers}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Doğru Cevap
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<Cancel sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.error}
                  hoverable
                >
                  <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {wrongAnswers}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Yanlış Cevap
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<Timer sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.ocean}
                  hoverable
                >
                  <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {emptyAnswers}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Boş Soru
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* Overall Performance */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard
                  title="Genel Performans"
                  gradient={getPerformanceGradient(scorePercentage)}
                  elevated
                >
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Başarı Oranı</Typography>
                      <Typography variant="body2" fontWeight={700}>
                        %{Math.round(scorePercentage)}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={scorePercentage}
                      sx={{
                        height: 12,
                        borderRadius: 6,
                        backgroundColor: modernColors.glass.black.light,
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 6,
                          background: getPerformanceGradient(scorePercentage),
                        },
                      }}
                    />
                  </Box>

                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Box sx={{ textAlign: 'center', p: 2, background: modernColors.glass.white.light, borderRadius: '12px' }}>
                        <Typography variant="h5" fontWeight={800} color="success.main">
                          {correctAnswers}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Doğru
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Box sx={{ textAlign: 'center', p: 2, background: modernColors.glass.white.light, borderRadius: '12px' }}>
                        <Typography variant="h5" fontWeight={800} color="error.main">
                          {wrongAnswers}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Yanlış
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Box sx={{ textAlign: 'center', p: 2, background: modernColors.glass.white.light, borderRadius: '12px' }}>
                        <Typography variant="h5" fontWeight={800} color="warning.main">
                          {emptyAnswers}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Boş
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard title="Hızlı İstatistikler" gradient={modernColors.gradients.ocean} elevated>
                  <List>
                    <ListItem sx={{ background: modernColors.glass.white.light, borderRadius: '8px', mb: 1 }}>
                      <ListItemIcon>
                        <Assessment sx={{ color: 'primary.main' }} />
                      </ListItemIcon>
                      <ListItemText
                        primary="Toplam Soru"
                        secondary={totalQuestions}
                      />
                    </ListItem>

                    <ListItem sx={{ background: modernColors.glass.white.light, borderRadius: '8px', mb: 1 }}>
                      <ListItemIcon>
                        <Star sx={{ color: 'warning.main' }} />
                      </ListItemIcon>
                      <ListItemText
                        primary="Ham Puan"
                        secondary={sonuc.ham_puan?.toFixed(2) || 'N/A'}
                      />
                    </ListItem>

                    <ListItem sx={{ background: modernColors.glass.white.light, borderRadius: '8px' }}>
                      <ListItemIcon>
                        <School sx={{ color: 'success.main' }} />
                      </ListItemIcon>
                      <ListItemText
                        primary="Sınav Tipi"
                        secondary={sonuc.sinav_tipi}
                      />
                    </ListItem>
                  </List>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* Actions */}
          <StaggerItem>
            <GlassCard elevated sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                <ModernButton
                  variant="gradient"
                  gradient={modernColors.gradients.primary}
                  icon={<Download />}
                  onClick={handleGeneratePDF}
                  loading={pdfGenerating}
                >
                  PDF İndir
                </ModernButton>

                <ModernButton
                  variant="gradient"
                  gradient={modernColors.gradients.ocean}
                  icon={<Insights />}
                >
                  Detaylı Analiz
                </ModernButton>

                {onRetake && (
                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.success}
                    icon={<Refresh />}
                    onClick={onRetake}
                  >
                    Yeniden Çöz
                  </ModernButton>
                )}
              </Box>
            </GlassCard>
          </StaggerItem>
        </StaggerContainer>
      </Container>
    </Box>
  );
};

export default ModernExamResults;
