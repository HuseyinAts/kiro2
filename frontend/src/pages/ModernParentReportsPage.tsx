/**
 * Modern Parent Reports Page - Glassmorphism Design
 * Veli raporları ve analiz
 */

import {
  Assessment,
  TrendingUp,
  Timer,
  EmojiEvents,
  Psychology,
  Star,
  Download,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import apiClient from '../services/apiClient';
import modernColors from '../theme/modern-colors';
import { useAuthStore } from '@/store/authStore';

interface ChildPerformance {
  ogrenci_id: string
  ad_soyad: string
  sinif: string
  ortalama: number
  tamamlanan_sinav: number
  toplam_sinav: number
  haftalik_calisma_saat: number
  guc_alanlar: string[]
  gelistirilmesi_gerekenler: string[]
}

interface WeeklyReport {
  hafta: string
  sinav_sayisi: number
  ortalama: number
  calisma_saati: number
  en_basarili_ders: string
  gelismesi_gereken_ders: string
}

export function ModernParentReportsPage() {
  const { user: _user } = useAuthStore();
  const [children, setChildren] = useState<ChildPerformance[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<string>('');
  const [weeklyReports, setWeeklyReports] = useState<WeeklyReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [_activeTab, _setActiveTab] = useState(0);

  useEffect(() => {
    fetchChildren();
  }, []);

  useEffect(() => {
    if (selectedChildId) {
      fetchWeeklyReports(selectedChildId);
    }
  }, [selectedChildId]);

  const fetchChildren = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/parent/children-performance');
      const childrenData = response?.data?.children || [];
      setChildren(childrenData);
      if (childrenData.length > 0) {
        setSelectedChildId(childrenData[0].ogrenci_id);
      }
    } catch (error) {
      console.error('Çocuk performansları yüklenemedi:', error);
      // Mock data
      setChildren([
        {
          ogrenci_id: '1',
          ad_soyad: 'Ahmet Yılmaz',
          sinif: '12-A',
          ortalama: 85.5,
          tamamlanan_sinav: 15,
          toplam_sinav: 20,
          haftalik_calisma_saat: 12.5,
          guc_alanlar: ['Matematik', 'Fizik', 'Kimya'],
          gelistirilmesi_gerekenler: ['Tarih', 'Coğrafya'],
        },
      ]);
      if (children.length > 0) {
        setSelectedChildId('1');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchWeeklyReports = async (childId: string) => {
    try {
      const response = await apiClient.get(`/api/v1/parent/children/${childId}/weekly-performance`);
      setWeeklyReports(response?.data?.reports || []);
    } catch (error) {
      console.error('Haftalık raporlar yüklenemedi:', error);
      // Mock data
      setWeeklyReports([
        {
          hafta: 'Bu Hafta',
          sinav_sayisi: 3,
          ortalama: 87,
          calisma_saati: 14,
          en_basarili_ders: 'Matematik',
          gelismesi_gereken_ders: 'Tarih',
        },
        {
          hafta: 'Geçen Hafta',
          sinav_sayisi: 2,
          ortalama: 84,
          calisma_saati: 11,
          en_basarili_ders: 'Fizik',
          gelismesi_gereken_ders: 'Coğrafya',
        },
        {
          hafta: '2 Hafta Önce',
          sinav_sayisi: 4,
          ortalama: 86,
          calisma_saati: 13,
          en_basarili_ders: 'Kimya',
          gelismesi_gereken_ders: 'Biyoloji',
        },
        {
          hafta: '3 Hafta Önce',
          sinav_sayisi: 3,
          ortalama: 82,
          calisma_saati: 10,
          en_basarili_ders: 'Matematik',
          gelismesi_gereken_ders: 'Edebiyat',
        },
      ]);
    }
  };

  const getPerformanceGradient = (score: number): string => {
    if (score >= 85) {return modernColors.gradients.success;}
    if (score >= 70) {return modernColors.gradients.warning;}
    if (score >= 50) {return modernColors.gradients.ocean;}
    return modernColors.gradients.error;
  };

  const getPerformanceLabel = (score: number): string => {
    if (score >= 85) {return 'Mükemmel';}
    if (score >= 70) {return 'İyi';}
    if (score >= 50) {return 'Orta';}
    return 'Gelişmeli';
  };

  const selectedChild = children.find((c) => c.ogrenci_id === selectedChildId);

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.mesh,
        }}
      >
        <ModernLoader message="Raporlar yükleniyor..." size="large" />
      </Box>
    );
  }

  if (!selectedChild) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.mesh,
        }}
      >
        <Container maxWidth="sm">
          <GlassCard glassIntensity="medium" elevated>
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                Çocuk bulunamadı
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Performans raporlarını görüntülemek için önce çocuk seçiniz
              </Typography>
            </Box>
          </GlassCard>
        </Container>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.mesh,
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Box
                sx={{
                  width: 56,
                  height: 56,
                  borderRadius: 3,
                  background: modernColors.gradients.sunset,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Assessment sx={{ fontSize: 32, color: 'white' }} />
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 900,
                    background: modernColors.gradients.sunset,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  Performans Raporları
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Detaylı performans analizi ve gelişim takibi
                </Typography>
              </Box>
              {children.length > 1 && (
                <FormControl sx={{ minWidth: 200 }}>
                  <InputLabel>Çocuk Seç</InputLabel>
                  <Select
                    value={selectedChildId}
                    label="Çocuk Seç"
                    onChange={(e) => setSelectedChildId(e.target.value)}
                  >
                    {children.map((child) => (
                      <MenuItem key={child.ogrenci_id} value={child.ogrenci_id}>
                        {child.ad_soyad}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            </Box>
          </Box>
        </motion.div>

        {/* Child Summary */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard
            glassIntensity="medium"
            elevated
            gradient={getPerformanceGradient(selectedChild.ortalama)}
            sx={{ mb: 3 }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {selectedChild.ad_soyad}
                </Typography>
                <Chip label={selectedChild.sinif} />
              </Box>
              <ModernButton variant="gradient" gradient={modernColors.gradients.primary} icon={<Download />}>
                Raporu İndir
              </ModernButton>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.success}>
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {selectedChild.ortalama}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Genel Ortalama
                  </Typography>
                  <Chip
                    label={getPerformanceLabel(selectedChild.ortalama)}
                    size="small"
                    sx={{ mt: 1, fontWeight: 600 }}
                  />
                </GlassCard>
              </Grid>
              <Grid item xs={6} sm={3}>
                <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.primary}>
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {selectedChild.tamamlanan_sinav}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Tamamlanan Sınav
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(selectedChild.tamamlanan_sinav / selectedChild.toplam_sinav) * 100}
                    sx={{ mt: 1, height: 6, borderRadius: 3 }}
                  />
                </GlassCard>
              </Grid>
              <Grid item xs={6} sm={3}>
                <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.warning}>
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {selectedChild.haftalik_calisma_saat}h
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Haftalık Çalışma
                  </Typography>
                </GlassCard>
              </Grid>
              <Grid item xs={6} sm={3}>
                <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.ocean}>
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {Math.round((selectedChild.tamamlanan_sinav / selectedChild.toplam_sinav) * 100)}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    İlerleme
                  </Typography>
                </GlassCard>
              </Grid>
            </Grid>
          </GlassCard>
        </motion.div>

        {/* Strengths & Weaknesses */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6}>
              <GlassCard
                glassIntensity="medium"
                elevated
                gradient={modernColors.gradients.success}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: modernColors.gradients.success,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <EmojiEvents sx={{ color: 'white' }} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Güçlü Alanlar
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {selectedChild.guc_alanlar.map((alan, index) => (
                    <Chip
                      key={index}
                      label={alan}
                      icon={<Star />}
                      sx={{
                        background: modernColors.gradients.success,
                        color: 'white',
                        fontWeight: 600,
                      }}
                    />
                  ))}
                </Box>
              </GlassCard>
            </Grid>
            <Grid item xs={12} md={6}>
              <GlassCard
                glassIntensity="medium"
                elevated
                gradient={modernColors.gradients.warning}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: modernColors.gradients.warning,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Psychology sx={{ color: 'white' }} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Geliştirilmesi Gerekenler
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {selectedChild.gelistirilmesi_gerekenler.map((alan, index) => (
                    <Chip
                      key={index}
                      label={alan}
                      icon={<TrendingUp />}
                      sx={{
                        background: modernColors.gradients.warning,
                        color: 'white',
                        fontWeight: 600,
                      }}
                    />
                  ))}
                </Box>
              </GlassCard>
            </Grid>
          </Grid>
        </motion.div>

        {/* Weekly Reports */}
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            mb: 2,
            background: modernColors.gradients.sunset,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Haftalık Detay Raporları
        </Typography>

        <Grid container spacing={3}>
          {weeklyReports.map((report, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <GlassCard
                  glassIntensity="medium"
                  elevated
                  hoverable
                  gradient={getPerformanceGradient(report.ortalama)}
                >
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                    {report.hafta}
                  </Typography>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: modernColors.glass.white.medium,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Assessment fontSize="small" color="action" />
                        <Typography variant="caption" color="text.secondary">
                          Sınav Sayısı
                        </Typography>
                      </Box>
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        {report.sinav_sayisi}
                      </Typography>
                    </Box>

                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: `linear-gradient(135deg, ${getPerformanceGradient(report.ortalama)})`,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <TrendingUp fontSize="small" sx={{ color: 'white' }} />
                        <Typography variant="caption" sx={{ color: 'white' }}>
                          Ortalama
                        </Typography>
                      </Box>
                      <Typography variant="h5" sx={{ fontWeight: 900, color: 'white' }}>
                        {report.ortalama}%
                      </Typography>
                    </Box>

                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: modernColors.glass.white.medium,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Timer fontSize="small" color="action" />
                        <Typography variant="caption" color="text.secondary">
                          Çalışma
                        </Typography>
                      </Box>
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        {report.calisma_saati}h
                      </Typography>
                    </Box>

                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: modernColors.glass.white.medium,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Star fontSize="small" sx={{ color: 'success.main' }} />
                        <Typography variant="caption" color="text.secondary">
                          En Başarılı
                        </Typography>
                      </Box>
                      <Chip
                        label={report.en_basarili_ders}
                        size="small"
                        sx={{
                          background: modernColors.gradients.success,
                          color: 'white',
                          fontWeight: 600,
                        }}
                      />
                    </Box>
                  </Box>
                </GlassCard>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}

export default ModernParentReportsPage;
