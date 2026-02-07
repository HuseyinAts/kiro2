/**
 * Modern Teacher Students Page - Glassmorphism Design
 * Öğretmen öğrenci yönetimi
 */

import {
  Search,
  Person,
  Email,
  Phone,
  TrendingUp,
  Assignment,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  TextField,
  InputAdornment,
  Chip,
  Avatar,
  Grid,
  LinearProgress,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import apiClient from '../services/apiClient';
import modernColors from '../theme/modern-colors';

interface Student {
  id: string
  ad: string
  soyad: string
  email: string
  telefon?: string
  sinif: string
  ortalama: number
  tamamlanan_sinav: number
  toplam_sinav: number
  son_giris?: string
}

export function ModernTeacherStudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/teacher/students');
      setStudents(response.data.students || []);
    } catch (error) {
      console.error('Öğrenciler yüklenemedi:', error);
      // Mock data for demo
      setStudents([
        {
          id: '1',
          ad: 'Ahmet',
          soyad: 'Yılmaz',
          email: 'ahmet.yilmaz@example.com',
          telefon: '0555 123 4567',
          sinif: '12-A',
          ortalama: 85.5,
          tamamlanan_sinav: 15,
          toplam_sinav: 20,
          son_giris: '2025-10-19T10:30:00',
        },
        {
          id: '2',
          ad: 'Ayşe',
          soyad: 'Demir',
          email: 'ayse.demir@example.com',
          sinif: '12-A',
          ortalama: 92.3,
          tamamlanan_sinav: 18,
          toplam_sinav: 20,
          son_giris: '2025-10-19T09:15:00',
        },
        {
          id: '3',
          ad: 'Mehmet',
          soyad: 'Kaya',
          email: 'mehmet.kaya@example.com',
          telefon: '0555 987 6543',
          sinif: '12-B',
          ortalama: 78.9,
          tamamlanan_sinav: 12,
          toplam_sinav: 20,
          son_giris: '2025-10-18T16:45:00',
        },
        {
          id: '4',
          ad: 'Fatma',
          soyad: 'Şahin',
          email: 'fatma.sahin@example.com',
          sinif: '11-A',
          ortalama: 88.7,
          tamamlanan_sinav: 16,
          toplam_sinav: 20,
        },
        {
          id: '5',
          ad: 'Ali',
          soyad: 'Öztürk',
          email: 'ali.ozturk@example.com',
          telefon: '0555 456 7890',
          sinif: '11-B',
          ortalama: 72.4,
          tamamlanan_sinav: 10,
          toplam_sinav: 20,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredStudents = students.filter(
    (student) =>
      `${student.ad} ${student.soyad}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
      student.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      student.sinif.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const getInitials = (ad: string, soyad: string): string => {
    return `${ad.charAt(0)}${soyad.charAt(0)}`.toUpperCase();
  };

  const getPerformanceGradient = (ortalama: number): string => {
    if (ortalama >= 85) {return modernColors.gradients.success;}
    if (ortalama >= 70) {return modernColors.gradients.primary;}
    if (ortalama >= 50) {return modernColors.gradients.warning;}
    return modernColors.gradients.error;
  };

  const getProgressPercentage = (tamamlanan: number, toplam: number): number => {
    return Math.round((tamamlanan / toplam) * 100);
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
        <ModernLoader message="Öğrenciler yükleniyor..." size="large" />
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
                  background: modernColors.gradients.forest,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Person sx={{ fontSize: 32, color: 'white' }} />
              </Box>
              <Box>
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 900,
                    background: modernColors.gradients.forest,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  Öğrencilerim
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Öğrenci performansını takip edin ve raporları görüntüleyin
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
            <TextField
              fullWidth
              placeholder="Öğrenci adı, e-posta veya sınıf ara..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </GlassCard>
        </motion.div>

        {/* Stats Summary */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.primary}>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {filteredStudents.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Toplam Öğrenci
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.success}>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {(
                    filteredStudents.reduce((sum, s) => sum + s.ortalama, 0) /
                    filteredStudents.length
                  ).toFixed(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Ortalama Başarı
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.warning}>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {Math.round(
                    (filteredStudents.reduce((sum, s) => sum + s.tamamlanan_sinav, 0) /
                      filteredStudents.reduce((sum, s) => sum + s.toplam_sinav, 0)) *
                      100,
                  )}
                  %
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sınav Tamamlama
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.ocean}>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {new Set(filteredStudents.map((s) => s.sinif)).size}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Farklı Sınıf
                </Typography>
              </GlassCard>
            </Grid>
          </Grid>
        </motion.div>

        {/* Student Cards */}
        <AnimatePresence mode="wait">
          {filteredStudents.length > 0 ? (
            <Grid container spacing={3}>
              {filteredStudents.map((student, index) => (
                <Grid item xs={12} sm={6} md={4} key={student.id}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <GlassCard
                      glassIntensity="medium"
                      elevated
                      hoverable
                      gradient={getPerformanceGradient(student.ortalama)}
                    >
                      {/* Student Header */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                        <Avatar
                          sx={{
                            width: 56,
                            height: 56,
                            background: getPerformanceGradient(student.ortalama),
                            fontSize: '1.5rem',
                            fontWeight: 800,
                          }}
                        >
                          {getInitials(student.ad, student.soyad)}
                        </Avatar>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" sx={{ fontWeight: 700 }}>
                            {student.ad} {student.soyad}
                          </Typography>
                          <Chip label={student.sinif} size="small" />
                        </Box>
                      </Box>

                      {/* Contact Info */}
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Email fontSize="small" color="action" />
                          <Typography variant="body2" sx={{ fontSize: 11 }}>
                            {student.email}
                          </Typography>
                        </Box>

                        {student.telefon && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Phone fontSize="small" color="action" />
                            <Typography variant="body2">{student.telefon}</Typography>
                          </Box>
                        )}
                      </Box>

                      {/* Performance */}
                      <Box sx={{ mb: 2 }}>
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            mb: 1,
                          }}
                        >
                          <Typography variant="body2" color="text.secondary">
                            Ortalama Başarı
                          </Typography>
                          <Typography variant="h6" sx={{ fontWeight: 700 }}>
                            {student.ortalama.toFixed(1)}
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={student.ortalama}
                          sx={{
                            height: 8,
                            borderRadius: 4,
                            backgroundColor: modernColors.glass.black.light,
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 4,
                              background: getPerformanceGradient(student.ortalama),
                            },
                          }}
                        />
                      </Box>

                      {/* Exam Progress */}
                      <Box sx={{ mb: 3 }}>
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            mb: 1,
                          }}
                        >
                          <Typography variant="body2" color="text.secondary">
                            Sınav İlerlemesi
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {student.tamamlanan_sinav}/{student.toplam_sinav}
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={getProgressPercentage(
                            student.tamamlanan_sinav,
                            student.toplam_sinav,
                          )}
                          sx={{
                            height: 8,
                            borderRadius: 4,
                            backgroundColor: modernColors.glass.black.light,
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 4,
                              background: modernColors.gradients.primary,
                            },
                          }}
                        />
                      </Box>

                      {/* Actions */}
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <ModernButton variant="glass" icon={<TrendingUp />} size="small" fullWidth>
                          Rapor
                        </ModernButton>
                        <ModernButton variant="glass" icon={<Assignment />} size="small" fullWidth>
                          Detay
                        </ModernButton>
                      </Box>
                    </GlassCard>
                  </motion.div>
                </Grid>
              ))}
            </Grid>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <GlassCard glassIntensity="medium" elevated>
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <Box
                    sx={{
                      width: 120,
                      height: 120,
                      borderRadius: '50%',
                      background: modernColors.gradients.ocean,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mx: 'auto',
                      mb: 3,
                    }}
                  >
                    <Person sx={{ fontSize: 64, color: 'white' }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                    Öğrenci bulunamadı
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Arama kriterlerinize uygun öğrenci bulunmamaktadır
                  </Typography>
                </Box>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>
      </Container>
    </Box>
  );
}

export default ModernTeacherStudentsPage;
