/**
 * Modern Student Dashboard
 * Beautiful, functional dashboard with glassmorphism and modern design
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
  CheckCircle,
} from '@mui/icons-material';
import {
  Container,
  Grid,
  Typography,
  Box,
  LinearProgress,
  Avatar,
  Chip,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import { useNavigate } from 'react-router-dom';

import { StaggerContainer, StaggerItem } from '@/components/Animations/PageTransition';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { useAuthStore } from '@/store/authStore';
import modernColors from '@/theme/modern-colors';

export const ModernStudentDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  // Mock data - gerçek API'den gelecek
  const stats = {
    totalStudyTime: 1250, // minutes
    completedLessons: 45,
    averageScore: 78.5,
    currentStreak: 7,
    rank: 234,
    totalStudents: 10000,
  };

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

  const recentActivities = [
    { id: 1, title: 'Matematik - Türev', score: 85, date: '2 saat önce', type: 'exam' },
    { id: 2, title: 'Fizik - Newton Kanunları', score: 92, date: '1 gün önce', type: 'lesson' },
    { id: 3, title: 'Kimya - Periyodik Tablo', score: 78, date: '2 gün önce', type: 'exam' },
  ];

  const subjects = [
    { name: 'Matematik', progress: 75, color: modernColors.subject.matematik.main },
    { name: 'Fizik', progress: 60, color: modernColors.subject.fizik.main },
    { name: 'Kimya', progress: 85, color: modernColors.subject.kimya.main },
    { name: 'Biyoloji', progress: 70, color: modernColors.subject.biyoloji.main },
  ];

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
                  Hoş geldin, {user?.ad}! 👋
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    color: 'rgba(255,255,255,0.9)',
                    mt: 0.5,
                  }}
                >
                  Bugün harika şeyler öğrenmeye hazır mısın?
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
                aria-label={`${stats.currentStreak} günlük çalışma serisi`}
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
                    {stats.currentStreak}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Günlük Seri
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
                    {stats.completedLessons}
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
                    {stats.averageScore}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ortalama Başarı
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
                    #{stats.rank}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sıralama
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
                    {Math.floor(stats.totalStudyTime / 60)}sa
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Toplam Çalışma
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* Quick Actions */}
          <StaggerItem>
            <GlassCard
              title="Hızlı Erişim"
              subtitle="Sık kullandığın özelliklere hızlıca git"
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

          {/* Progress Section */}
          <Grid container spacing={3} sx={{ mt: 2 }}>
            {/* Subject Progress */}
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard
                  title="Ders İlerlemen"
                  subtitle="Her ders için ilerleme durumun"
                  gradient={modernColors.gradients.forest}
                  elevated
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {subjects.map((subject, index) => (
                      <Box key={index}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" fontWeight={600}>
                            {subject.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            %{subject.progress}
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={subject.progress}
                          sx={{
                            height: 8,
                            borderRadius: 8,
                            backgroundColor: modernColors.glass.black.light,
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 8,
                              background: `linear-gradient(90deg, ${subject.color} 0%, ${subject.color}dd 100%)`,
                            },
                          }}
                        />
                      </Box>
                    ))}
                  </Box>
                </GlassCard>
              </StaggerItem>
            </Grid>

            {/* Recent Activity */}
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard
                  title="Son Aktiviteler"
                  subtitle="Son yaptığın çalışmalar"
                  gradient={modernColors.gradients.sunset}
                  elevated
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {recentActivities.map((activity) => (
                      <Box
                        key={activity.id}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          p: 2,
                          background: modernColors.glass.white.light,
                          borderRadius: '12px',
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
                            {activity.type === 'exam' ? <Assessment /> : <CheckCircle />}
                          </Box>
                          <Box>
                            <Typography variant="body2" fontWeight={600}>
                              {activity.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {activity.date}
                            </Typography>
                          </Box>
                        </Box>
                        <Chip
                          label={`%${activity.score}`}
                          size="small"
                          sx={{
                            background: modernColors.gradients.success,
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
                    Tümünü Gör
                  </ModernButton>
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
