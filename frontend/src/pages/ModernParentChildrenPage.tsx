/**
 * Modern Parent Children Page - Glassmorphism Design
 * Veli çocuk yönetimi ve takip
 */

import {
  ChildCare,
  School,
  Assessment,
  CalendarToday,
  Timer,
  BarChart,
  Psychology,
  Email,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  Avatar,
  Tabs,
  Tab,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import modernColors from '../theme/modern-colors';
import { ChildInfo, WeeklyReport } from '../types';
import { useAuthStore } from '@/store/authStore';

export function ModernParentChildrenPage() {
  const { user: _user } = useAuthStore();
  const [children, setChildren] = useState<ChildInfo[]>([]);
  const [selectedChildIndex, setSelectedChildIndex] = useState(0);
  const [weeklyReports, setWeeklyReports] = useState<WeeklyReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [_error, _setError] = useState<string | null>(null);

  useEffect(() => {
    loadChildren();
  }, []);

  useEffect(() => {
    if (children.length > 0 && children[selectedChildIndex]) {
      loadWeeklyReports(children[selectedChildIndex].ogrenci_id);
    }
  }, [selectedChildIndex, children]);

  const loadChildren = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/parent/children', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult = await response.json();
      const childrenData = Array.isArray(apiResult) ? apiResult : apiResult.data || [];
      setChildren(childrenData);
    } catch (error: any) {
      console.error('Parent Children API hatası:', error);
      // Mock data for demo
      setChildren([
        {
          ogrenci_id: '1',
          ad_soyad: 'Ahmet Yılmaz',
          sinif: '12-A',
          okul: 'Atatürk Lisesi',
          haftalik_ilerleme: 85,
          son_aktivite: '2025-11-21T10:30:00',
        },
        {
          ogrenci_id: '2',
          ad_soyad: 'Ayşe Yılmaz',
          sinif: '10-B',
          okul: 'Atatürk Lisesi',
          haftalik_ilerleme: 92,
          son_aktivite: '2025-11-21T09:15:00',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadWeeklyReports = async (childId: string) => {
    try {
      const response = await fetch(`/api/v1/parent/children/${childId}/weekly-report`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult = await response.json();
      const reportsData = Array.isArray(apiResult) ? apiResult : apiResult.data || [];
      setWeeklyReports(reportsData);
    } catch (error: any) {
      console.error('Weekly Reports API hatası:', error);
      // Mock data
      setWeeklyReports([
        {
          hafta: '2025-W47',
          calisma_suresi: 345,
          tamamlanan_dersler: 12,
          sinav_puanlari: [85, 90, 88],
          ortalama_puan: 87.7,
        },
        {
          hafta: '2025-W46',
          calisma_suresi: 320,
          tamamlanan_dersler: 11,
          sinav_puanlari: [82, 88, 85],
          ortalama_puan: 85.0,
        },
        {
          hafta: '2025-W45',
          calisma_suresi: 290,
          tamamlanan_dersler: 10,
          sinav_puanlari: [78, 84, 80],
          ortalama_puan: 80.7,
        },
      ]);
    }
  };

  const getProgressGradient = (progress: number): string => {
    if (progress >= 80) {return modernColors.gradients.success;}
    if (progress >= 60) {return modernColors.gradients.warning;}
    return modernColors.gradients.error;
  };

  const formatDuration = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}s ${mins}dk`;
  };

  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map((n) => n.charAt(0))
      .join('')
      .toUpperCase();
  };

  const getPerformanceLabel = (score: number): string => {
    if (score >= 85) {return 'Mükemmel';}
    if (score >= 70) {return 'İyi';}
    if (score >= 50) {return 'Orta';}
    return 'Gelişmeli';
  };

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
        <ModernLoader message="Çocuk bilgileri yükleniyor..." size="large" />
      </Box>
    );
  }

  if (children.length === 0) {
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
              <Box
                sx={{
                  width: 120,
                  height: 120,
                  borderRadius: '50%',
                  background: modernColors.gradients.sunset,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 3,
                }}
              >
                <ChildCare sx={{ fontSize: 64, color: 'white' }} />
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                Henüz kayıtlı çocuğunuz bulunmuyor
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Çocuğunuzun hesabını sisteme eklemek için okul yönetimiyle iletişime geçin
              </Typography>
            </Box>
          </GlassCard>
        </Container>
      </Box>
    );
  }

  const selectedChild = children[selectedChildIndex];

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
                <ChildCare sx={{ fontSize: 32, color: 'white' }} />
              </Box>
              <Box>
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
                  Çocuklarım
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Çocuklarınızın eğitim ilerlemesini detaylı takip edin
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>

        {/* Child Tabs */}
        {children.length > 1 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
              <Tabs
                value={selectedChildIndex}
                onChange={(_, newValue) => setSelectedChildIndex(newValue)}
                variant="scrollable"
                scrollButtons="auto"
              >
                {children.map((child, _index) => (
                  <Tab
                    key={child.ogrenci_id}
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar
                          sx={{
                            width: 32,
                            height: 32,
                            background: getProgressGradient(child.haftalik_ilerleme),
                            fontSize: '0.875rem',
                          }}
                        >
                          {getInitials(child.ad_soyad)}
                        </Avatar>
                        <Box sx={{ textAlign: 'left' }}>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {child.ad_soyad}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {child.sinif}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                ))}
              </Tabs>
            </GlassCard>
          </motion.div>
        )}

        {/* Selected Child Info */}
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedChildIndex}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {/* Child Info Card */}
            <GlassCard
              glassIntensity="medium"
              elevated
              gradient={getProgressGradient(selectedChild.haftalik_ilerleme)}
              sx={{ mb: 3 }}
            >
              <Grid container spacing={3} alignItems="center">
                <Grid item xs={12} md={8}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar
                      sx={{
                        width: 80,
                        height: 80,
                        background: getProgressGradient(selectedChild.haftalik_ilerleme),
                        fontSize: '2rem',
                        fontWeight: 800,
                      }}
                    >
                      {getInitials(selectedChild.ad_soyad)}
                    </Avatar>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                        {selectedChild.ad_soyad}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <School fontSize="small" color="action" />
                          <Typography variant="body2">{selectedChild.sinif}</Typography>
                        </Box>
                        <Chip label={selectedChild.okul} size="small" />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <CalendarToday fontSize="small" color="action" />
                        <Typography variant="caption" color="text.secondary">
                          Son aktivite:{' '}
                          {new Date(selectedChild.son_aktivite).toLocaleString('tr-TR')}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box
                    sx={{
                      textAlign: 'center',
                      p: 3,
                      borderRadius: 3,
                      background: `linear-gradient(135deg, ${getProgressGradient(selectedChild.haftalik_ilerleme)})`,
                    }}
                  >
                    <Typography
                      variant="h2"
                      sx={{ fontWeight: 900, color: 'white', mb: 1 }}
                    >
                      {selectedChild.haftalik_ilerleme}%
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>
                      Haftalık İlerleme
                    </Typography>
                    <Chip
                      label={getPerformanceLabel(selectedChild.haftalik_ilerleme)}
                      sx={{
                        mt: 2,
                        background: 'rgba(255, 255, 255, 0.3)',
                        color: 'white',
                        fontWeight: 700,
                      }}
                    />
                  </Box>
                </Grid>
              </Grid>

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', gap: 1, mt: 3, flexWrap: 'wrap' }}>
                <ModernButton variant="glass" icon={<BarChart />} size="small">
                  Detaylı Rapor
                </ModernButton>
                <ModernButton variant="glass" icon={<Assessment />} size="small">
                  Sınav Sonuçları
                </ModernButton>
                <ModernButton variant="glass" icon={<Psychology />} size="small">
                  Öğrenme Yolu
                </ModernButton>
                <ModernButton variant="glass" icon={<Email />} size="small">
                  Öğretmenle İletişim
                </ModernButton>
              </Box>
            </GlassCard>

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
              Haftalık İlerleme Raporları
            </Typography>

            <Grid container spacing={3}>
              {weeklyReports.map((report, index) => (
                <Grid item xs={12} sm={6} md={4} key={report.hafta}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <GlassCard
                      glassIntensity="medium"
                      elevated
                      hoverable
                      gradient={getProgressGradient(report.ortalama_puan)}
                    >
                      {/* Week Label */}
                      <Box sx={{ mb: 3 }}>
                        <Chip
                          label={
                            index === 0
                              ? 'Bu Hafta'
                              : index === 1
                              ? 'Geçen Hafta'
                              : `${index + 1} Hafta Önce`
                          }
                          sx={{
                            background: getProgressGradient(report.ortalama_puan),
                            color: 'white',
                            fontWeight: 700,
                          }}
                        />
                      </Box>

                      {/* Stats */}
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1.5,
                            p: 1.5,
                            borderRadius: 2,
                            background: modernColors.glass.white.medium,
                          }}
                        >
                          <Box
                            sx={{
                              width: 40,
                              height: 40,
                              borderRadius: 2,
                              background: modernColors.gradients.primary,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            <Timer sx={{ color: 'white' }} />
                          </Box>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Çalışma Süresi
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 700 }}>
                              {formatDuration(report.calisma_suresi)}
                            </Typography>
                          </Box>
                        </Box>

                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1.5,
                            p: 1.5,
                            borderRadius: 2,
                            background: modernColors.glass.white.medium,
                          }}
                        >
                          <Box
                            sx={{
                              width: 40,
                              height: 40,
                              borderRadius: 2,
                              background: modernColors.gradients.success,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            <School sx={{ color: 'white' }} />
                          </Box>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Tamamlanan Ders
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 700 }}>
                              {report.tamamlanan_dersler} ders
                            </Typography>
                          </Box>
                        </Box>

                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1.5,
                            p: 1.5,
                            borderRadius: 2,
                            background: modernColors.glass.white.medium,
                          }}
                        >
                          <Box
                            sx={{
                              width: 40,
                              height: 40,
                              borderRadius: 2,
                              background: modernColors.gradients.warning,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            <Assessment sx={{ color: 'white' }} />
                          </Box>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Sınav Sayısı
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 700 }}>
                              {report.sinav_puanlari.length} sınav
                            </Typography>
                          </Box>
                        </Box>
                      </Box>

                      {/* Average Score */}
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          background: `linear-gradient(135deg, ${getProgressGradient(report.ortalama_puan)})`,
                          textAlign: 'center',
                        }}
                      >
                        <Typography variant="caption" sx={{ color: 'white' }}>
                          Ortalama Puan
                        </Typography>
                        <Typography
                          variant="h4"
                          sx={{ fontWeight: 900, color: 'white', my: 1 }}
                        >
                          {report.ortalama_puan.toFixed(1)}
                        </Typography>
                        <Chip
                          label={getPerformanceLabel(report.ortalama_puan)}
                          size="small"
                          sx={{
                            background: 'rgba(255, 255, 255, 0.3)',
                            color: 'white',
                            fontWeight: 600,
                          }}
                        />
                      </Box>
                    </GlassCard>
                  </motion.div>
                </Grid>
              ))}
            </Grid>
          </motion.div>
        </AnimatePresence>
      </Container>
    </Box>
  );
}

export default ModernParentChildrenPage;
