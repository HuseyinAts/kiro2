/**
 * Modern Parent Dashboard
 * Beautiful dashboard for parents to track children's progress
 */

import {
  TrendingUp,
  School,
  EmojiEvents,
  Notifications,
  Assessment,
  CalendarToday,
  ArrowForward,
  LocalFireDepartment,
  CheckCircle,
} from '@mui/icons-material';
import {
  Container,
  Grid,
  Typography,
  Box,
  Avatar,
  Chip,
  LinearProgress,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  useState  } from 'react';
import { useNavigate } from 'react-router-dom';

import { StaggerContainer, StaggerItem } from '@/components/Animations/PageTransition';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { useAuthStore } from '@/store/authStore';
import modernColors from '@/theme/modern-colors';

export const ModernParentDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [selectedChild, setSelectedChild] = useState(0);

  // Mock data - gerçek API'den gelecek
  const children = [
    {
      id: 1,
      name: 'Ahmet Yılmaz',
      grade: '12-A',
      avatar: 'AY',
      overallScore: 85,
      attendance: 96,
      rank: 12,
      streak: 7,
      subjects: [
        { name: 'Matematik', score: 88, gradient: modernColors.gradients.primary },
        { name: 'Fizik', score: 82, gradient: modernColors.gradients.forest },
        { name: 'Kimya', score: 85, gradient: modernColors.gradients.fire },
        { name: 'Biyoloji', score: 87, gradient: modernColors.gradients.success },
      ],
    },
    {
      id: 2,
      name: 'Ayşe Yılmaz',
      grade: '9-B',
      avatar: 'AY',
      overallScore: 92,
      attendance: 98,
      rank: 5,
      streak: 14,
      subjects: [
        { name: 'Matematik', score: 95, gradient: modernColors.gradients.primary },
        { name: 'Türkçe', score: 90, gradient: modernColors.gradients.sunset },
        { name: 'İngilizce', score: 92, gradient: modernColors.gradients.ocean },
        { name: 'Tarih', score: 91, gradient: modernColors.gradients.forest },
      ],
    },
  ];

  const currentChild = children[selectedChild];

  const recentActivities = [
    {
      id: 1,
      child: 'Ahmet',
      activity: 'Matematik sınavını tamamladı',
      score: 88,
      date: '2 saat önce',
      type: 'exam',
      status: 'success',
    },
    {
      id: 2,
      child: 'Ayşe',
      activity: 'Türkçe ödevini yükledi',
      score: 95,
      date: '1 gün önce',
      type: 'assignment',
      status: 'success',
    },
    {
      id: 3,
      child: 'Ahmet',
      activity: 'Fizik dersine devam etti',
      date: '1 gün önce',
      type: 'attendance',
      status: 'info',
    },
  ];

  const upcomingEvents = [
    { id: 1, child: 'Ahmet', event: 'Kimya Sınavı', date: 'Yarın, 10:00', type: 'exam' },
    { id: 2, child: 'Ayşe', event: 'İngilizce Sözlü', date: '2 gün sonra', type: 'presentation' },
    { id: 3, child: 'Ahmet', event: 'Matematik Ödevi', date: '3 gün sonra', type: 'assignment' },
  ];

  const teacherMessages = [
    {
      id: 1,
      teacher: 'Mehmet Öğretmen',
      subject: 'Matematik',
      message: 'Ahmet son sınavda çok başarılıydı, tebrikler!',
      date: '1 gün önce',
      unread: true,
    },
    {
      id: 2,
      teacher: 'Ayşe Öğretmen',
      subject: 'Türkçe',
      message: 'Ayşe\'nin okuma alışkanlığı gelişiyor.',
      date: '2 gün önce',
      unread: false,
    },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.lightPurple,
        pb: 4,
      }}
    >
      {/* Header Section */}
      <Box
        sx={{
          background: modernColors.gradients.sunset,
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
                    background: modernColors.gradients.primary,
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
                  Hoş geldiniz, {user?.ad}! 👨‍👩‍👧‍👦
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    color: 'rgba(255,255,255,0.9)',
                    mt: 0.5,
                  }}
                >
                  Çocuklarınızın eğitim yolculuğunu takip edin
                </Typography>
              </Box>
            </Box>

            {/* Notification Badge */}
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Box
                role="status"
                aria-label={`${teacherMessages.filter(m => m.unread).length} yeni mesaj`}
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
                <Notifications sx={{ fontSize: 32, color: 'white' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 800, color: 'white' }}>
                    {teacherMessages.filter(m => m.unread).length}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Yeni Mesaj
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
          {/* Children Selector */}
          <StaggerItem>
            <GlassCard title="Çocuklarım" gradient={modernColors.gradients.primary} elevated>
              <Grid container spacing={2}>
                {children.map((child, index) => (
                  <Grid item xs={12} md={6} key={child.id}>
                    <motion.div
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Box
                        role="button"
                        aria-label={`${child.name} seç, ${child.grade} sınıfı`}
                        aria-pressed={selectedChild === index}
                        tabIndex={0}
                        onClick={() => setSelectedChild(index)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setSelectedChild(index);
                          }
                        }}
                        sx={{
                          p: 3,
                          borderRadius: '16px',
                          background:
                            selectedChild === index
                              ? modernColors.gradients.sunset
                              : modernColors.glass.white.light,
                          border: `2px solid ${
                            selectedChild === index
                              ? 'transparent'
                              : modernColors.glass.border
                          }`,
                          cursor: 'pointer',
                          transition: 'all 0.3s',
                          boxShadow:
                            selectedChild === index ? modernColors.shadow.glow : 'none',
                          '&:focus': {
                            outline: '2px solid rgba(249, 115, 22, 0.5)',
                            outlineOffset: '2px',
                          },
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Avatar
                            sx={{
                              width: 56,
                              height: 56,
                              background: modernColors.gradients.primary,
                              fontWeight: 700,
                            }}
                          >
                            {child.avatar}
                          </Avatar>
                          <Box sx={{ flex: 1 }}>
                            <Typography
                              variant="h6"
                              fontWeight={700}
                              sx={{
                                color:
                                  selectedChild === index ? 'white' : 'text.primary',
                              }}
                            >
                              {child.name}
                            </Typography>
                            <Typography
                              variant="body2"
                              sx={{
                                color:
                                  selectedChild === index
                                    ? 'rgba(255,255,255,0.9)'
                                    : 'text.secondary',
                              }}
                            >
                              {child.grade} • Sıralama: #{child.rank}
                            </Typography>
                          </Box>
                          <Box sx={{ textAlign: 'center' }}>
                            <Typography
                              variant="h5"
                              fontWeight={800}
                              sx={{
                                color:
                                  selectedChild === index ? 'white' : 'text.primary',
                              }}
                            >
                              {child.overallScore}
                            </Typography>
                            <Typography
                              variant="caption"
                              sx={{
                                color:
                                  selectedChild === index
                                    ? 'rgba(255,255,255,0.9)'
                                    : 'text.secondary',
                              }}
                            >
                              Ortalama
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    </motion.div>
                  </Grid>
                ))}
              </Grid>
            </GlassCard>
          </StaggerItem>

          {/* Stats Cards */}
          <Grid container spacing={3} sx={{ mt: 2 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<TrendingUp sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.success}
                  hoverable
                >
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    %{currentChild.overallScore}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Genel Başarı
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
                    %{currentChild.attendance}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Devam Oranı
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
                    #{currentChild.rank}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sınıf Sıralaması
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<LocalFireDepartment sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.fire}
                  hoverable
                >
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {currentChild.streak}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Günlük Seri
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* Subject Progress */}
          <Grid container spacing={3} sx={{ mt: 2 }}>
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard
                  title="Ders Performansı"
                  subtitle={`${currentChild.name}'in ders bazlı başarısı`}
                  gradient={modernColors.gradients.primary}
                  elevated
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {currentChild.subjects.map((subject, index) => (
                      <Box key={index}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" fontWeight={600}>
                            {subject.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            %{subject.score}
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={subject.score}
                          sx={{
                            height: 8,
                            borderRadius: 8,
                            backgroundColor: modernColors.glass.black.light,
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 8,
                              background: subject.gradient,
                            },
                          }}
                        />
                      </Box>
                    ))}
                  </Box>
                </GlassCard>
              </StaggerItem>
            </Grid>

            {/* Recent Activities */}
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard
                  title="Son Aktiviteler"
                  subtitle="Çocuklarınızın son hareketleri"
                  gradient={modernColors.gradients.ocean}
                  elevated
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {recentActivities.map((activity) => (
                      <Box
                        key={activity.id}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 2,
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
                        <Box
                          sx={{
                            width: 40,
                            height: 40,
                            borderRadius: '8px',
                            background:
                              activity.status === 'success'
                                ? modernColors.gradients.success
                                : modernColors.gradients.ocean,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                          }}
                        >
                          {activity.type === 'exam' ? (
                            <Assessment />
                          ) : activity.type === 'assignment' ? (
                            <CheckCircle />
                          ) : (
                            <School />
                          )}
                        </Box>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body2" fontWeight={600}>
                            {activity.child}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {activity.activity}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" display="block">
                            {activity.date}
                          </Typography>
                        </Box>
                        {activity.score && (
                          <Chip
                            label={`%${activity.score}`}
                            size="small"
                            sx={{
                              background: modernColors.gradients.success,
                              color: 'white',
                              fontWeight: 700,
                            }}
                          />
                        )}
                      </Box>
                    ))}
                  </Box>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* Bottom Section */}
          <Grid container spacing={3} sx={{ mt: 2 }}>
            {/* Upcoming Events */}
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard
                  title="Yaklaşan Etkinlikler"
                  subtitle="Önemli tarihler"
                  gradient={modernColors.gradients.warning}
                  elevated
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {upcomingEvents.map((event) => (
                      <Box
                        key={event.id}
                        sx={{
                          p: 2,
                          background: modernColors.glass.white.light,
                          borderRadius: '12px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 2,
                        }}
                      >
                        <CalendarToday sx={{ color: 'warning.main' }} />
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body2" fontWeight={600}>
                            {event.event}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {event.child} • {event.date}
                          </Typography>
                        </Box>
                        <Chip label={event.type} size="small" />
                      </Box>
                    ))}
                  </Box>
                </GlassCard>
              </StaggerItem>
            </Grid>

            {/* Teacher Messages */}
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard
                  title="Öğretmen Mesajları"
                  subtitle="Size gelen bildirimler"
                  gradient={modernColors.gradients.fire}
                  elevated
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {teacherMessages.map((msg) => (
                      <Box
                        key={msg.id}
                        sx={{
                          p: 2,
                          background: msg.unread
                            ? modernColors.glass.primary.light
                            : modernColors.glass.white.light,
                          borderRadius: '12px',
                          borderLeft: msg.unread
                            ? `4px solid ${modernColors.primary[500]}`
                            : 'none',
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" fontWeight={700}>
                            {msg.teacher}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {msg.date}
                          </Typography>
                        </Box>
                        <Chip label={msg.subject} size="small" sx={{ mb: 1 }} />
                        <Typography variant="body2" color="text.secondary">
                          {msg.message}
                        </Typography>
                      </Box>
                    ))}
                  </Box>

                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.fire}
                    fullWidth
                    endIcon={<ArrowForward />}
                    sx={{ mt: 2 }}
                    onClick={() => navigate('/parent/notifications')}
                  >
                    Tüm Mesajlar
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

export default ModernParentDashboard;
