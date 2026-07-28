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
  const [hata, setHata] = useState<string | null>(null);
  // Sınıfa öğrenci ekleme (blocker #6): bu ekranda hiç ekleme yolu yoktu.
  const [siniflar, setSiniflar] = useState<{ sinif_id: string; sinif_adi: string }[]>([]);
  const [seciliSinif, setSeciliSinif] = useState('');
  const [yeniEposta, setYeniEposta] = useState('');
  const [ekleniyor, setEkleniyor] = useState(false);
  const [bilgi, setBilgi] = useState<string | null>(null);

  useEffect(() => {
    fetchStudents();
    fetchSiniflar();
  }, []);

  const fetchSiniflar = async () => {
    try {
      const response = await apiClient.get('/api/v1/teacher/classes');
      const liste = response?.data ?? [];
      setSiniflar(liste);
      if (liste.length > 0) setSeciliSinif(liste[0].sinif_id);
    } catch (error) {
      console.error('Sınıflar yüklenemedi:', error);
      setSiniflar([]);
    }
  };

  const ogrenciEkle = async () => {
    const eposta = yeniEposta.trim();
    if (!seciliSinif || !eposta) return;
    setEkleniyor(true);
    setHata(null);
    setBilgi(null);
    try {
      const sonuc = await apiClient.post(
        `/api/v1/teacher/classes/${seciliSinif}/students`,
        { email: eposta },
      );
      const eklenen = sonuc?.data ?? {};
      setBilgi(`${eklenen.ad ?? ''} ${eklenen.soyad ?? ''}`.trim() + ' sınıfa eklendi.');
      setYeniEposta('');
      await fetchStudents();
    } catch (error) {
      // Sunucu "bu e-postayla kayıtlı öğrenci yok" / "yalnızca öğrenci
      // hesapları eklenebilir" ayrımını yapıyor; mesajı OLDUĞU GİBİ gösteriyoruz
      // ki öğretmen yazım hatasıyla gerçek reddi ayırt edebilsin.
      const mesaj =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Öğrenci eklenemedi.';
      setHata(mesaj);
    } finally {
      setEkleniyor(false);
    }
  };

  const fetchStudents = async () => {
    try {
      setLoading(true);
      setHata(null);
      const response = await apiClient.get('/api/v1/teacher/students');
      setStudents(response?.data?.students || []);
    } catch (error) {
      // 29 Tem 2026: burada 5 UYDURMA öğrenci vardı ("Ahmet Yılmaz", "Ayşe
      // Demir"…). Sonuç: uç bozuk olduğunda öğretmen sahte bir sınıf listesi
      // görüyor, eksiklik hiç fark edilmiyordu. Ekran gerçekte olmayan bir
      // şeyi göstermez; hata hata olarak söylenir.
      console.error('Öğrenciler yüklenemedi:', error);
      setStudents([]);
      setHata('Öğrenci listesi yüklenemedi. Bağlantını kontrol edip tekrar dene.');
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

        {/* Sınıfa öğrenci ekle — blocker #6: bu yol hiç yoktu */}
        <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
          <Box
            component="form"
            onSubmit={(e: React.FormEvent) => {
              e.preventDefault();
              void ogrenciEkle();
            }}
            sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}
          >
            <TextField
              select
              label="Sınıf"
              value={seciliSinif}
              onChange={(e) => setSeciliSinif(e.target.value)}
              SelectProps={{ native: true }}
              sx={{ minWidth: 160 }}
              InputLabelProps={{ shrink: true }}
            >
              {siniflar.length === 0 && <option value="">Önce sınıf oluştur</option>}
              {siniflar.map((s) => (
                <option key={s.sinif_id} value={s.sinif_id}>
                  {s.sinif_adi}
                </option>
              ))}
            </TextField>
            <TextField
              label="Öğrenci e-postası"
              type="email"
              placeholder="ogrenci@okul.tr"
              value={yeniEposta}
              onChange={(e) => setYeniEposta(e.target.value)}
              sx={{ flex: 1, minWidth: 240 }}
              InputLabelProps={{ shrink: true }}
            />
            <ModernButton
              type="submit"
              disabled={ekleniyor || !seciliSinif || !yeniEposta.trim()}
            >
              {ekleniyor ? 'Ekleniyor…' : 'Sınıfa ekle'}
            </ModernButton>
          </Box>
        </GlassCard>

        {bilgi && (
          <Box role="status" sx={{ mb: 2, color: 'success.main' }}>
            {bilgi}
          </Box>
        )}

        {/* Yükleme hatası — sessizce sahte liste göstermek yerine söylenir */}
        {hata && (
          <Box
            role="alert"
            sx={{
              mb: 3,
              p: 2,
              borderRadius: 2,
              border: '1px solid rgba(217,119,6,0.35)',
              background: 'rgba(217,119,6,0.08)',
              color: modernColors.text?.primary ?? 'inherit',
            }}
          >
            {hata}
          </Box>
        )}

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
