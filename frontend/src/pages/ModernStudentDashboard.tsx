/**
 * Modern Student Dashboard
 * Beautiful, functional dashboard with glassmorphism and modern design
 * REFACTORED: Real API data instead of mock data
 */

import {
  TrendingUp,
  School,
  Assessment,
  EmojiEvents,
  Timeline,
  Chat,
  MenuBook,
  ArrowForward,
  LocalFireDepartment,
  HourglassEmpty,
} from '@mui/icons-material';
import {
  Container,
  Grid,
  Typography,
  Box,
  Avatar,
  Chip,
  CircularProgress,
  Skeleton,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import { useNavigate } from 'react-router-dom';

import { StaggerContainer, StaggerItem } from '@/components/Animations/PageTransition';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { useAuthStore } from '@/store/authStore';
import modernColors from '@/theme/modern-colors';

// Types matching backend DashboardIstatistikleri
interface DashboardStats {
  tamamlanan_dersler: number;
  toplam_dersler: number;
  tamamlanan_sinavlar: number;
  ortalama_puan: number;
  toplam_calisma_suresi: number;
  haftalik_ilerleme: number;
  gunluk_seri: number;
  toplam_puan: number;
  seviye: number;
  deneyim: number;
}

interface RecentExam {
  sinav_id: string;
  sinav_adi: string;
  sinav_tipi: string;
  tarih: string;
  puan: number;
  dogru_sayisi: number;
  yanlis_sayisi: number;
  bos_sayisi: number;
  sure: number;
}

const DEFAULT_STATS: DashboardStats = {
  tamamlanan_dersler: 0,
  toplam_dersler: 0,
  tamamlanan_sinavlar: 0,
  ortalama_puan: 0,
  toplam_calisma_suresi: 0,
  haftalik_ilerleme: 0,
  gunluk_seri: 0,
  toplam_puan: 0,
  seviye: 1,
  deneyim: 0,
};

export const ModernStudentDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [stats, setStats] = React.useState<DashboardStats>(DEFAULT_STATS);
  const [recentExams, setRecentExams] = React.useState<RecentExam[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        const [statsRes, examsRes] = await Promise.all([
          fetch('/api/v1/student-dashboard/istatistikler', { credentials: 'include' }),
          fetch('/api/v1/student-dashboard/sinav-gecmisi?limit=3', { credentials: 'include' }),
        ]);

        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setStats(statsData);
        }

        if (examsRes.ok) {
          const examsData = await examsRes.json();
          setRecentExams(Array.isArray(examsData) ? examsData : []);
        }
      } catch {
        // Silently handle - dashboard shows defaults for new students
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const quickActions = [
    {
      title: 'Sınava Başla',
      icon: <Assessment sx={{ fontSize: 32 }} />,
      gradient: modernColors.gradients.primary,
      path: '/exam/start',
    },
    {
      title: 'AI Sohbet',
      icon: <Chat sx={{ fontSize: 32 }} />,
      gradient: modernColors.gradients.ocean,
      path: '/chat',
    },
    {
      title: 'Öğrenme Yolu',
      icon: <Timeline sx={{ fontSize: 32 }} />,
      gradient: modernColors.gradients.forest,
      path: '/learning-path',
    },
    {
      title: 'Sınav Geçmişi',
      icon: <MenuBook sx={{ fontSize: 32 }} />,
      gradient: modernColors.gradients.sunset,
      path: '/exam/history',
    },
  ];

  // Format relative time from ISO date string
  const formatRelativeTime = (dateStr: string): string => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 60) return `${minutes} dk önce`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} saat önce`;
    const days = Math.floor(hours / 24);
    return `${days} gün önce`;
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.lightBlue,
        pb: 4,
      }}
    >
      {/* Header Section */}
      <Box
        sx={{
          background: modernColors.gradients.primary,
          pt: 4,
          pb: 8,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Animated Background Shapes */}
        <motion.div
          style={{
            position: 'absolute',
            width: '400px',
            height: '400px',
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.1)',
            top: '-150px',
            right: '-100px',
            filter: 'blur(60px)',
          }}
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: 'linear',
          }}
        />

        <Container maxWidth="xl">
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 10 }}
              >
                <Avatar
                  sx={{
                    width: 80,
                    height: 80,
                    border: '4px solid rgba(255,255,255,0.3)',
                    boxShadow: modernColors.shadow.modern,
                  }}
                >
                  {user?.ad?.[0]}{user?.soyad?.[0]}
                </Avatar>
              </motion.div>

              <Box>
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 800,
                    color: 'white',
                    textShadow: '0 2px 10px rgba(0,0,0,0.2)',
                  }}
                >
                  Hos geldin, {user?.ad}!
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    color: 'rgba(255,255,255,0.9)',
                    mt: 0.5,
                  }}
                >
                  {stats.tamamlanan_sinavlar > 0
                    ? `${stats.tamamlanan_sinavlar} sinav tamamladin, ortalama %${stats.ortalama_puan.toFixed(0)}`
                    : 'Bugün harika seyler ogrenmeye hazir misin?'}
                </Typography>
              </Box>
            </Box>

            {/* Streak Badge */}
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Box
                role="status"
                aria-label={`${stats.gunluk_seri} gunluk calisma serisi`}
                sx={{
                  background: 'rgba(255,255,255,0.2)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: '16px',
                  p: 2,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <LocalFireDepartment sx={{ fontSize: 32, color: '#FF6B35' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 800, color: 'white' }}>
                    {loading ? <Skeleton width={30} /> : stats.gunluk_seri}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Gunluk Seri
                  </Typography>
                </Box>
              </Box>
            </motion.div>
          </Box>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxWidth="xl" sx={{ mt: -4, position: 'relative', zIndex: 1 }}>
        <StaggerContainer>
          {/* Stats Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<School sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.primary}
                  hoverable
                >
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {loading ? <Skeleton width={40} /> : stats.tamamlanan_dersler}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Tamamlanan Ders
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<TrendingUp sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.success}
                  hoverable
                >
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {loading ? <Skeleton width={40} /> : `${stats.ortalama_puan.toFixed(0)}%`}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ortalama Basari
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<EmojiEvents sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.warning}
                  hoverable
                >
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {loading ? <Skeleton width={40} /> : stats.tamamlanan_sinavlar}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Tamamlanan Sinav
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<Timeline sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.ocean}
                  hoverable
                >
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {loading ? <Skeleton width={40} /> : `${Math.floor(stats.toplam_calisma_suresi / 60)}sa`}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Toplam Calisma
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* Quick Actions */}
          <StaggerItem>
            <GlassCard
              title="Hizli Erisim"
              subtitle="Sik kullandigin ozelliklere hizlica git"
              gradient={modernColors.gradients.primary}
              elevated
            >
              <Grid container spacing={2}>
                {quickActions.map((action, index) => (
                  <Grid item xs={6} md={3} key={index}>
                    <motion.div
                      whileHover={{ scale: 1.05, y: -5 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <Box
                        role="button"
                        aria-label={action.title}
                        tabIndex={0}
                        onClick={() => navigate(action.path)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            navigate(action.path);
                          }
                        }}
                        sx={{
                          background: action.gradient,
                          borderRadius: '16px',
                          p: 3,
                          textAlign: 'center',
                          cursor: 'pointer',
                          boxShadow: modernColors.shadow.md,
                          transition: 'all 0.3s',
                          '&:hover': {
                            boxShadow: modernColors.shadow.lg,
                          },
                          '&:focus': {
                            outline: '2px solid rgba(59, 130, 246, 0.5)',
                            outlineOffset: '2px',
                          },
                        }}
                      >
                        <Box sx={{ color: 'white', mb: 1 }}>{action.icon}</Box>
                        <Typography
                          variant="body2"
                          sx={{ color: 'white', fontWeight: 600 }}
                        >
                          {action.title}
                        </Typography>
                      </Box>
                    </motion.div>
                  </Grid>
                ))}
              </Grid>
            </GlassCard>
          </StaggerItem>

          {/* Recent Activity */}
          <Grid container spacing={3} sx={{ mt: 2 }}>
            <Grid item xs={12}>
              <StaggerItem>
                <GlassCard
                  title="Son Sinavlar"
                  subtitle="Son yaptigin sinavlar"
                  gradient={modernColors.gradients.sunset}
                  elevated
                >
                  {loading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                      <CircularProgress />
                    </Box>
                  ) : recentExams.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <HourglassEmpty sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                      <Typography variant="body1" color="text.secondary">
                        Henuz sinav yapmadiniz
                      </Typography>
                      <ModernButton
                        variant="glass"
                        onClick={() => navigate('/exam/start')}
                        sx={{ mt: 2 }}
                      >
                        Ilk Sinavina Basla
                      </ModernButton>
                    </Box>
                  ) : (
                    <>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {recentExams.map((exam) => (
                          <Box
                            key={exam.sinav_id}
                            onClick={() => navigate(`/exam/${exam.sinav_id}/results`)}
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              p: 2,
                              background: modernColors.glass.white.light,
                              borderRadius: '12px',
                              cursor: 'pointer',
                              transition: 'all 0.2s',
                              '&:hover': {
                                background: modernColors.glass.white.medium,
                                transform: 'translateX(4px)',
                              },
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                              <Box
                                sx={{
                                  width: 40,
                                  height: 40,
                                  borderRadius: '8px',
                                  background: modernColors.gradients.primary,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  color: 'white',
                                }}
                              >
                                <Assessment />
                              </Box>
                              <Box>
                                <Typography variant="body2" fontWeight={600}>
                                  {exam.sinav_adi || `${exam.sinav_tipi} Sinavi`}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {formatRelativeTime(exam.tarih)} | D:{exam.dogru_sayisi} Y:{exam.yanlis_sayisi} B:{exam.bos_sayisi}
                                </Typography>
                              </Box>
                            </Box>
                            <Chip
                              label={`%${exam.puan.toFixed(0)}`}
                              size="small"
                              sx={{
                                background: exam.puan >= 70 ? modernColors.gradients.success : modernColors.gradients.warning,
                                color: 'white',
                                fontWeight: 700,
                              }}
                            />
                          </Box>
                        ))}
                      </Box>

                      <ModernButton
                        variant="glass"
                        fullWidth
                        endIcon={<ArrowForward />}
                        onClick={() => navigate('/exam/history')}
                        sx={{ mt: 2 }}
                      >
                        Tumunu Gor
                      </ModernButton>
                    </>
                  )}
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>
        </StaggerContainer>
      </Container>
    </Box>
  );
};

export default ModernStudentDashboard;
