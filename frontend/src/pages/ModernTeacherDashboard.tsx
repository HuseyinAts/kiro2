/**
 * Modern Teacher Dashboard
 * Professional dashboard for teachers with modern design
 */

import {
  People,
  Class,
  Assessment,
  Assignment,
  TrendingUp,
  CheckCircle,
  Schedule,
  BarChart,
  Add,
  ArrowForward,
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

export const ModernTeacherDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  // Mock data
  const stats = {
    totalStudents: 156,
    activeClasses: 4,
    pendingAssignments: 12,
    completedExams: 28,
    averageClassScore: 82.5,
    attendanceRate: 94.2,
  };

  const quickActions = [
    {
      title: 'Yeni Sınav Oluştur',
      icon: <Add sx={{ fontSize: 32 }} />,
      gradient: modernColors.gradients.primary,
      path: '/teacher/exams',
    },
    {
      title: 'Ödev Ver',
      icon: <Assignment sx={{ fontSize: 32 }} />,
      gradient: modernColors.gradients.sunset,
      path: '/teacher/assignments',
    },
    {
      title: 'Sınıflarım',
      icon: <Class sx={{ fontSize: 32 }} />,
      gradient: modernColors.gradients.forest,
      path: '/teacher/classes',
    },
    {
      title: 'Raporlar',
      icon: <BarChart sx={{ fontSize: 32 }} />,
      gradient: modernColors.gradients.ocean,
      path: '/teacher/reports',
    },
  ];

  const recentClasses = [
    { id: 1, name: '12-A Matematik', students: 32, avgScore: 85, gradient: modernColors.gradients.primary },
    { id: 2, name: '11-B Matematik', students: 28, avgScore: 78, gradient: modernColors.gradients.forest },
    { id: 3, name: '10-C Matematik', students: 30, avgScore: 82, gradient: modernColors.gradients.ocean },
  ];

  const pendingTasks = [
    { id: 1, title: '12-A Türev Sınavı Değerlendirmesi', type: 'exam', count: 32, deadline: 'Bugün' },
    { id: 2, title: '11-B Limit Ödevi Kontrolü', type: 'assignment', count: 28, deadline: 'Yarın' },
    { id: 3, title: '10-C İntegral Quiz', type: 'quiz', count: 30, deadline: '2 gün' },
  ];

  const upcomingLessons = [
    { id: 1, class: '12-A', topic: 'Türev Uygulamaları', time: '09:00', room: 'A-204' },
    { id: 2, class: '11-B', topic: 'Limit Problemleri', time: '11:00', room: 'A-205' },
    { id: 3, class: '10-C', topic: 'İntegral Giriş', time: '14:00', room: 'B-101' },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.lightGreen,
        pb: 4,
      }}
    >
      {/* Header Section */}
      <Box
        sx={{
          background: modernColors.gradients.forest,
          pt: 4,
          pb: 8,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Animated Background */}
        <motion.div
          style={{
            position: 'absolute',
            width: '500px',
            height: '500px',
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
                    background: modernColors.gradients.sunset,
                    fontWeight: 800,
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
                  Merhaba, {user?.ad} Öğretmen! 👨‍🏫
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    color: 'rgba(255,255,255,0.9)',
                    mt: 0.5,
                  }}
                >
                  Bugün {stats.activeClasses} sınıfınız var, {stats.pendingAssignments} bekleyen görev
                </Typography>
              </Box>
            </Box>

            {/* Today's Schedule Badge */}
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Box
                role="status"
                aria-label={`Bugün ${upcomingLessons.length} ders var`}
                sx={{
                  background: 'rgba(255,255,255,0.2)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: '16px',
                  p: 2,
                  minWidth: 150,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Schedule sx={{ color: 'white' }} />
                  <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>
                    Bugün
                  </Typography>
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 800, color: 'white' }}>
                  {upcomingLessons.length}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                  Ders var
                </Typography>
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
                  icon={<People sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.primary}
                  hoverable
                >
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {stats.totalStudents}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Toplam Öğrenci
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<Class sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.forest}
                  hoverable
                >
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {stats.activeClasses}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Aktif Sınıf
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
                    %{stats.averageClassScore}
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
                  icon={<CheckCircle sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.ocean}
                  hoverable
                >
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    %{stats.attendanceRate}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Devam Oranı
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* Quick Actions */}
          <StaggerItem>
            <GlassCard
              title="Hızlı İşlemler"
              subtitle="Sık kullandığın özellikler"
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
                            outline: '2px solid rgba(52, 211, 153, 0.5)',
                            outlineOffset: '2px',
                          },
                        }}
                      >
                        <Box sx={{ color: 'white', mb: 1 }}>{action.icon}</Box>
                        <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>
                          {action.title}
                        </Typography>
                      </Box>
                    </motion.div>
                  </Grid>
                ))}
              </Grid>
            </GlassCard>
          </StaggerItem>

          {/* Main Content Grid */}
          <Grid container spacing={3} sx={{ mt: 2 }}>
            {/* Classes */}
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard
                  title="Sınıflarım"
                  subtitle="Aktif sınıfların ve başarı oranları"
                  gradient={modernColors.gradients.forest}
                  elevated
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {recentClasses.map((cls) => (
                      <Box
                        key={cls.id}
                        sx={{
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
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body1" fontWeight={700}>
                            {cls.name}
                          </Typography>
                          <Chip
                            label={`${cls.students} öğrenci`}
                            size="small"
                            sx={{
                              background: cls.gradient,
                              color: 'white',
                              fontWeight: 600,
                            }}
                          />
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Box sx={{ flex: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={cls.avgScore}
                              sx={{
                                height: 8,
                                borderRadius: 8,
                                backgroundColor: modernColors.glass.black.light,
                                '& .MuiLinearProgress-bar': {
                                  borderRadius: 8,
                                  background: cls.gradient,
                                },
                              }}
                            />
                          </Box>
                          <Typography variant="body2" fontWeight={600}>
                            %{cls.avgScore}
                          </Typography>
                        </Box>
                      </Box>
                    ))}
                  </Box>

                  <ModernButton
                    variant="glass"
                    fullWidth
                    endIcon={<ArrowForward />}
                    onClick={() => navigate('/teacher/classes')}
                    sx={{ mt: 2 }}
                  >
                    Tüm Sınıflar
                  </ModernButton>
                </GlassCard>
              </StaggerItem>
            </Grid>

            {/* Pending Tasks */}
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard
                  title="Bekleyen Görevler"
                  subtitle="Değerlendirmen gereken işler"
                  gradient={modernColors.gradients.warning}
                  elevated
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {pendingTasks.map((task) => (
                      <Box
                        key={task.id}
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
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
                          <Box
                            sx={{
                              width: 40,
                              height: 40,
                              borderRadius: '8px',
                              background: modernColors.gradients.warning,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: 'white',
                            }}
                          >
                            {task.type === 'exam' ? <Assessment /> : <Assignment />}
                          </Box>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="body2" fontWeight={600}>
                              {task.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {task.count} kişi • {task.deadline}
                            </Typography>
                          </Box>
                        </Box>
                        <Chip
                          label="Bekliyor"
                          size="small"
                          sx={{
                            background: modernColors.gradients.warning,
                            color: 'white',
                            fontWeight: 600,
                          }}
                        />
                      </Box>
                    ))}
                  </Box>

                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.warning}
                    fullWidth
                    endIcon={<ArrowForward />}
                    sx={{ mt: 2 }}
                  >
                    Tüm Görevler
                  </ModernButton>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* Today's Schedule */}
          <StaggerItem sx={{ mt: 3 }}>
            <GlassCard
              title="Bugünün Programı"
              subtitle="Planlı dersleriniz"
              gradient={modernColors.gradients.ocean}
              elevated
            >
              <Grid container spacing={2}>
                {upcomingLessons.map((lesson) => (
                  <Grid item xs={12} md={4} key={lesson.id}>
                    <Box
                      sx={{
                        p: 2,
                        background: modernColors.glass.white.light,
                        borderRadius: '12px',
                        border: `2px solid ${modernColors.glass.border}`,
                        transition: 'all 0.2s',
                        '&:hover': {
                          background: modernColors.glass.white.medium,
                          borderColor: modernColors.primary[300],
                          transform: 'translateY(-4px)',
                        },
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Chip
                          label={lesson.time}
                          size="small"
                          icon={<Schedule />}
                          sx={{
                            background: modernColors.gradients.ocean,
                            color: 'white',
                            fontWeight: 600,
                          }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {lesson.room}
                        </Typography>
                      </Box>
                      <Typography variant="body1" fontWeight={700} sx={{ mb: 0.5 }}>
                        {lesson.class}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {lesson.topic}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </GlassCard>
          </StaggerItem>
        </StaggerContainer>
      </Container>
    </Box>
  );
};

export default ModernTeacherDashboard;
