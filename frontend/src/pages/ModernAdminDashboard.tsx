/**
 * Modern Admin Dashboard
 * Glassmorphism tasarım ile platform yönetimi ve izleme
 */

import {
  Dashboard,
  People,
  Assessment,
  Computer,
  TrendingUp,
  CheckCircle,
  School,
  Groups,
  ChildCare,
  AdminPanelSettings,
  Refresh,
} from '@mui/icons-material';
import {
  Box,
  Container,
  Typography,
  Grid,
  Avatar,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { StaggerContainer, StaggerItem } from '@/components/Animations/PageTransition';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { ModernLoader } from '@/components/ui/ModernLoader';
import { useAuthStore } from '@/store/authStore';
import modernColors from '@/theme/modern-colors';

interface AdminDashboardData {
  sistem_istatistikleri: {
    toplam_kullanici: number
    aktif_kullanici: number
    toplam_sinav: number
    sistem_yuklemesi: number
  }
  kullanici_istatistikleri: {
    ogrenci_sayisi: number
    ogretmen_sayisi: number
    veli_sayisi: number
    yeni_kayitlar: number
  }
  performans_metrikleri: {
    ortalama_yanit_suresi: number
    sistem_kullanilabilirlik: number
    hata_orani: number
    kullanici_memnuniyeti: number
  }
  son_aktiviteler: Array<{
    aktivite_id: string
    eylem: string
    kullanici: string
    detay?: string
    tarih: string
  }>
}

export const ModernAdminDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { user } = useAuthStore();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Mock data for development
      setTimeout(() => {
        setDashboardData({
          sistem_istatistikleri: {
            toplam_kullanici: 1250,
            aktif_kullanici: 980,
            toplam_sinav: 3456,
            sistem_yuklemesi: 42.5,
          },
          kullanici_istatistikleri: {
            ogrenci_sayisi: 980,
            ogretmen_sayisi: 45,
            veli_sayisi: 225,
            yeni_kayitlar: 85,
          },
          performans_metrikleri: {
            ortalama_yanit_suresi: 156,
            sistem_kullanilabilirlik: 99.8,
            hata_orani: 0.2,
            kullanici_memnuniyeti: 4.7,
          },
          son_aktiviteler: [
            {
              aktivite_id: '1',
              eylem: 'Yeni sınav oluşturuldu',
              kullanici: 'Mehmet Öğretmen',
              detay: 'TYT Matematik',
              tarih: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
            },
            {
              aktivite_id: '2',
              eylem: 'Kullanıcı kaydoldu',
              kullanici: 'Ayşe Öğrenci',
              detay: '12-A',
              tarih: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
            },
            {
              aktivite_id: '3',
              eylem: 'Sınav tamamlandı',
              kullanici: 'Ali Öğrenci',
              detay: '%87 başarı',
              tarih: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
            },
          ],
        });
        setLoading(false);
      }, 1000);
    } catch (error: any) {
      console.error('Admin Dashboard API hatası:', error);
      setError(`Dashboard verileri yüklenemedi: ${error.message}`);
      setLoading(false);
    }
  };

  const getSystemHealthColor = (value: number): string => {
    if (value >= 95) {return modernColors.gradients.success;}
    if (value >= 80) {return modernColors.gradients.warning;}
    return modernColors.gradients.error;
  };

  const getLoadColor = (value: number): string => {
    if (value < 50) {return modernColors.gradients.success;}
    if (value < 75) {return modernColors.gradients.warning;}
    return modernColors.gradients.error;
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.fire,
        }}
      >
        <ModernLoader message="Admin verileri yükleniyor..." size="large" />
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
          background: modernColors.gradients.fire,
          p: 2,
        }}
      >
        <Container maxWidth="sm">
          <GlassCard glassIntensity="medium" elevated>
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
            <ModernButton
              variant="gradient"
              gradient={modernColors.gradients.fire}
              onClick={loadDashboardData}
              icon={<Refresh />}
            >
              Tekrar Dene
            </ModernButton>
          </GlassCard>
        </Container>
      </Box>
    );
  }

  if (!dashboardData) {return null;}

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.lightPurple,
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

      <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1 }}>
        <StaggerContainer>
          {/* Header */}
          <StaggerItem>
            <Box sx={{ mb: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Avatar
                  sx={{
                    width: 64,
                    height: 64,
                    background: modernColors.gradients.fire,
                    boxShadow: modernColors.shadow.modern,
                  }}
                >
                  <AdminPanelSettings sx={{ fontSize: 32 }} />
                </Avatar>
                <Box>
                  <Typography variant="h3" fontWeight={800}>
                    Admin Dashboard
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Hoş geldiniz, {user?.ad} {user?.soyad} - Sistem yönetimi ve izleme
                  </Typography>
                </Box>
              </Box>
            </Box>
          </StaggerItem>

          {/* System Stats */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<People sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.primary}
                  hoverable
                >
                  <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {dashboardData.sistem_istatistikleri.toplam_kullanici}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Toplam Kullanıcı
                  </Typography>
                  <Chip
                    label={`${dashboardData.sistem_istatistikleri.aktif_kullanici} aktif`}
                    size="small"
                    sx={{
                      mt: 1,
                      background: modernColors.gradients.success,
                      color: 'white',
                      fontWeight: 700,
                    }}
                  />
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<Assessment sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.success}
                  hoverable
                >
                  <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {dashboardData.sistem_istatistikleri.toplam_sinav.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Toplam Sınav
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<Computer sx={{ fontSize: 28 }} />}
                  gradient={getLoadColor(dashboardData.sistem_istatistikleri.sistem_yuklemesi)}
                  hoverable
                >
                  <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {dashboardData.sistem_istatistikleri.sistem_yuklemesi.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sistem Yükü
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={dashboardData.sistem_istatistikleri.sistem_yuklemesi}
                    sx={{
                      mt: 1,
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: modernColors.glass.black.light,
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 3,
                        background: getLoadColor(dashboardData.sistem_istatistikleri.sistem_yuklemesi),
                      },
                    }}
                  />
                </GlassCard>
              </StaggerItem>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <StaggerItem>
                <GlassCard
                  icon={<TrendingUp sx={{ fontSize: 28 }} />}
                  gradient={modernColors.gradients.ocean}
                  hoverable
                >
                  <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                    +{dashboardData.kullanici_istatistikleri.yeni_kayitlar}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Yeni Kayıtlar
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Bu hafta
                  </Typography>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* User Distribution */}
          <StaggerItem>
            <GlassCard title="Kullanıcı Dağılımı" gradient={modernColors.gradients.primary} elevated>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Box
                    sx={{
                      p: 3,
                      background: modernColors.glass.white.light,
                      borderRadius: '12px',
                      textAlign: 'center',
                    }}
                  >
                    <School sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                    <Typography variant="h4" fontWeight={800}>
                      {dashboardData.kullanici_istatistikleri.ogrenci_sayisi}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Öğrenci
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={6} sm={3}>
                  <Box
                    sx={{
                      p: 3,
                      background: modernColors.glass.white.light,
                      borderRadius: '12px',
                      textAlign: 'center',
                    }}
                  >
                    <Groups sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                    <Typography variant="h4" fontWeight={800}>
                      {dashboardData.kullanici_istatistikleri.ogretmen_sayisi}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Öğretmen
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={6} sm={3}>
                  <Box
                    sx={{
                      p: 3,
                      background: modernColors.glass.white.light,
                      borderRadius: '12px',
                      textAlign: 'center',
                    }}
                  >
                    <ChildCare sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                    <Typography variant="h4" fontWeight={800}>
                      {dashboardData.kullanici_istatistikleri.veli_sayisi}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Veli
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={6} sm={3}>
                  <Box
                    sx={{
                      p: 3,
                      background: modernColors.glass.white.light,
                      borderRadius: '12px',
                      textAlign: 'center',
                    }}
                  >
                    <TrendingUp sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                    <Typography variant="h4" fontWeight={800}>
                      {dashboardData.kullanici_istatistikleri.yeni_kayitlar}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Yeni Kayıt
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </GlassCard>
          </StaggerItem>

          <Grid container spacing={3} sx={{ mt: 2 }}>
            {/* Performance Metrics */}
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard title="Performans Metrikleri" gradient={modernColors.gradients.ocean} elevated>
                  {/* Response Time */}
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Ortalama Yanıt Süresi</Typography>
                      <Typography variant="body2" fontWeight={700}>
                        {dashboardData.performans_metrikleri.ortalama_yanit_suresi}ms
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={Math.max(0, 100 - dashboardData.performans_metrikleri.ortalama_yanit_suresi / 5)}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: modernColors.glass.black.light,
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 4,
                          background:
                            dashboardData.performans_metrikleri.ortalama_yanit_suresi < 200
                              ? modernColors.gradients.success
                              : modernColors.gradients.warning,
                        },
                      }}
                    />
                  </Box>

                  {/* System Uptime */}
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Sistem Kullanılabilirlik</Typography>
                      <Typography variant="body2" fontWeight={700}>
                        {dashboardData.performans_metrikleri.sistem_kullanilabilirlik}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={dashboardData.performans_metrikleri.sistem_kullanilabilirlik}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: modernColors.glass.black.light,
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 4,
                          background: getSystemHealthColor(
                            dashboardData.performans_metrikleri.sistem_kullanilabilirlik,
                          ),
                        },
                      }}
                    />
                  </Box>

                  {/* Error Rate */}
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Hata Oranı</Typography>
                      <Typography variant="body2" fontWeight={700}>
                        {dashboardData.performans_metrikleri.hata_orani}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={dashboardData.performans_metrikleri.hata_orani * 10}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: modernColors.glass.black.light,
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 4,
                          background:
                            dashboardData.performans_metrikleri.hata_orani < 1
                              ? modernColors.gradients.success
                              : modernColors.gradients.error,
                        },
                      }}
                    />
                  </Box>

                  {/* User Satisfaction */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Kullanıcı Memnuniyeti</Typography>
                      <Typography variant="body2" fontWeight={700}>
                        {dashboardData.performans_metrikleri.kullanici_memnuniyeti}/5.0
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(dashboardData.performans_metrikleri.kullanici_memnuniyeti / 5) * 100}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: modernColors.glass.black.light,
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 4,
                          background: modernColors.gradients.success,
                        },
                      }}
                    />
                  </Box>
                </GlassCard>
              </StaggerItem>
            </Grid>

            {/* Recent Activities */}
            <Grid item xs={12} md={6}>
              <StaggerItem>
                <GlassCard title="Son Aktiviteler" gradient={modernColors.gradients.fire} elevated>
                  <List>
                    {dashboardData.son_aktiviteler.map((aktivite) => (
                      <ListItem
                        key={aktivite.aktivite_id}
                        sx={{
                          background: modernColors.glass.white.light,
                          borderRadius: '8px',
                          mb: 1,
                        }}
                      >
                        <ListItemIcon>
                          <Avatar sx={{ background: modernColors.gradients.primary }}>
                            {aktivite.eylem.includes('sınav') ? (
                              <Assessment />
                            ) : aktivite.eylem.includes('kaydoldu') ? (
                              <People />
                            ) : (
                              <CheckCircle />
                            )}
                          </Avatar>
                        </ListItemIcon>
                        <ListItemText
                          primary={aktivite.eylem}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {aktivite.kullanici}
                              </Typography>
                              {aktivite.detay && (
                                <Chip
                                  label={aktivite.detay}
                                  size="small"
                                  sx={{
                                    mt: 0.5,
                                    background: modernColors.gradients.success,
                                    color: 'white',
                                  }}
                                />
                              )}
                              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                                {new Date(aktivite.tarih).toLocaleString('tr-TR')}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </GlassCard>
              </StaggerItem>
            </Grid>
          </Grid>

          {/* Actions */}
          <StaggerItem>
            <GlassCard elevated sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                <ModernButton variant="gradient" gradient={modernColors.gradients.primary} icon={<People />}>
                  Kullanıcı Yönetimi
                </ModernButton>
                <ModernButton variant="gradient" gradient={modernColors.gradients.ocean} icon={<Assessment />}>
                  Sınav Yönetimi
                </ModernButton>
                <ModernButton variant="gradient" gradient={modernColors.gradients.forest} icon={<Dashboard />}>
                  İstatistikler
                </ModernButton>
                <ModernButton variant="glass" icon={<Refresh />} onClick={loadDashboardData}>
                  Yenile
                </ModernButton>
              </Box>
            </GlassCard>
          </StaggerItem>
        </StaggerContainer>
      </Container>
    </Box>
  );
};

export default ModernAdminDashboard;
