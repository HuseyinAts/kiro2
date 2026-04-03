/**
 * Modern Teacher Exams Page - Glassmorphism Design
 * Öğretmen sınav yönetimi
 */

import {
  Add,
  Edit,
  Delete,
  Visibility,
  MoreVert,
  Assignment,
  People,
  Timer,
  CheckCircle,
  Quiz,
  PlayArrow,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Menu,
  MenuItem as MenuItemComponent,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import apiClient from '../services/apiClient';
import modernColors from '../theme/modern-colors';

interface Exam {
  id: string
  baslik: string
  aciklama: string
  sinav_tipi: 'TYT' | 'AYT' | 'YDT'
  soru_sayisi: number
  sure_dakika: number
  durum: 'taslak' | 'aktif' | 'tamamlandi'
  olusturma_tarihi: string
  baslangic_tarihi?: string
  bitis_tarihi?: string
  katilimci_sayisi: number
}

export function ModernTeacherExamsPage() {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedExam, setSelectedExam] = useState<Exam | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const [formData, setFormData] = useState({
    baslik: '',
    aciklama: '',
    sinav_tipi: 'TYT' as 'TYT' | 'AYT' | 'YDT',
    soru_sayisi: 120,
    sure_dakika: 165,
  });

  useEffect(() => {
    fetchExams();
  }, []);

  const fetchExams = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/teacher/exams');
      setExams(response?.data?.exams || []);
    } catch (error) {
      console.error('Sınavlar yüklenemedi:', error);
      // Mock data
      setExams([
        {
          id: '1',
          baslik: 'TYT Deneme Sınavı 1',
          aciklama: 'İlk dönem TYT deneme sınavı',
          sinav_tipi: 'TYT',
          soru_sayisi: 120,
          sure_dakika: 165,
          durum: 'aktif',
          olusturma_tarihi: '2025-10-15T10:00:00',
          baslangic_tarihi: '2025-10-20T09:00:00',
          bitis_tarihi: '2025-10-20T12:00:00',
          katilimci_sayisi: 45,
        },
        {
          id: '2',
          baslik: 'AYT Matematik Sınavı',
          aciklama: 'Matematik konuları deneme sınavı',
          sinav_tipi: 'AYT',
          soru_sayisi: 40,
          sure_dakika: 90,
          durum: 'taslak',
          olusturma_tarihi: '2025-10-18T14:30:00',
          katilimci_sayisi: 0,
        },
        {
          id: '3',
          baslik: 'TYT Deneme Sınavı 2',
          aciklama: 'İkinci dönem TYT deneme sınavı',
          sinav_tipi: 'TYT',
          soru_sayisi: 120,
          sure_dakika: 165,
          durum: 'tamamlandi',
          olusturma_tarihi: '2025-10-01T10:00:00',
          baslangic_tarihi: '2025-10-05T09:00:00',
          bitis_tarihi: '2025-10-05T12:00:00',
          katilimci_sayisi: 42,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExam = async () => {
    try {
      await apiClient.post('/api/v1/teacher/exams', formData);
      setCreateDialogOpen(false);
      fetchExams();
      setFormData({
        baslik: '',
        aciklama: '',
        sinav_tipi: 'TYT',
        soru_sayisi: 120,
        sure_dakika: 165,
      });
    } catch (error) {
      console.error('Sınav oluşturulamadı:', error);
      alert('Sınav oluşturulurken bir hata oluştu');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, exam: Exam) => {
    setAnchorEl(event.currentTarget);
    setSelectedExam(exam);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleEditExam = () => {
    alert(`Sınavı düzenle: ${selectedExam?.baslik}`);
    handleMenuClose();
  };

  const handleDeleteExam = async () => {
    if (selectedExam && window.confirm('Bu sınavı silmek istediğinizden emin misiniz?')) {
      try {
        await apiClient.delete(`/api/v1/teacher/exams/${selectedExam.id}`);
        fetchExams();
      } catch (error) {
        console.error('Sınav silinemedi:', error);
      }
    }
    handleMenuClose();
  };

  const handleViewResults = () => {
    alert(`Sonuçları görüntüle: ${selectedExam?.baslik}`);
    handleMenuClose();
  };

  const getStatusGradient = (durum: string): string => {
    switch (durum) {
      case 'aktif':
        return modernColors.gradients.success;
      case 'taslak':
        return modernColors.gradients.warning;
      case 'tamamlandi':
        return modernColors.gradients.ocean;
      default:
        return modernColors.gradients.primary;
    }
  };

  const getStatusLabel = (durum: string): string => {
    switch (durum) {
      case 'aktif':
        return 'Aktif';
      case 'taslak':
        return 'Taslak';
      case 'tamamlandi':
        return 'Tamamlandı';
      default:
        return durum;
    }
  };

  const getExamTypeGradient = (tip: string): string => {
    switch (tip) {
      case 'TYT':
        return modernColors.gradients.primary;
      case 'AYT':
        return modernColors.gradients.sunset;
      case 'YDT':
        return modernColors.gradients.ocean;
      default:
        return modernColors.gradients.primary;
    }
  };

  const activeExams = exams.filter((e) => e.durum === 'aktif').length;
  const draftExams = exams.filter((e) => e.durum === 'taslak').length;
  // Note: completedExams is calculated but not currently displayed in UI
  // const completedExams = exams.filter((e) => e.durum === 'tamamlandi').length
  const totalParticipants = exams.reduce((sum, e) => sum + e.katilimci_sayisi, 0);

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
        <ModernLoader message="Sınavlar yükleniyor..." size="large" />
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
      <Container maxWidth="xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 4,
              flexWrap: 'wrap',
              gap: 2,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
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
                <Quiz sx={{ fontSize: 32, color: 'white' }} />
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
                  Sınav Yönetimi
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Sınavlarınızı oluşturun, düzenleyin ve sonuçları analiz edin
                </Typography>
              </Box>
            </Box>
            <ModernButton
              variant="gradient"
              gradient={modernColors.gradients.forest}
              icon={<Add />}
              onClick={() => setCreateDialogOpen(true)}
              glow
            >
              Yeni Sınav Oluştur
            </ModernButton>
          </Box>
        </motion.div>

        {/* Statistics */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Grid container spacing={2} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <GlassCard
                glassIntensity="medium"
                elevated
                hoverable
                gradient={modernColors.gradients.primary}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Assignment sx={{ fontSize: 32, color: 'primary.main' }} />
                  <Box>
                    <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                      {exams.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Toplam Sınav
                    </Typography>
                  </Box>
                </Box>
              </GlassCard>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <GlassCard
                glassIntensity="medium"
                elevated
                hoverable
                gradient={modernColors.gradients.success}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <CheckCircle sx={{ fontSize: 32, color: 'success.main' }} />
                  <Box>
                    <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                      {activeExams}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Aktif Sınavlar
                    </Typography>
                  </Box>
                </Box>
              </GlassCard>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <GlassCard
                glassIntensity="medium"
                elevated
                hoverable
                gradient={modernColors.gradients.warning}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Edit sx={{ fontSize: 32, color: 'warning.main' }} />
                  <Box>
                    <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                      {draftExams}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Taslak
                    </Typography>
                  </Box>
                </Box>
              </GlassCard>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <GlassCard
                glassIntensity="medium"
                elevated
                hoverable
                gradient={modernColors.gradients.ocean}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <People sx={{ fontSize: 32, color: 'info.main' }} />
                  <Box>
                    <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                      {totalParticipants}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Toplam Katılımcı
                    </Typography>
                  </Box>
                </Box>
              </GlassCard>
            </Grid>
          </Grid>
        </motion.div>

        {/* Exam Cards */}
        <AnimatePresence mode="wait">
          {exams.length > 0 ? (
            <Grid container spacing={3}>
              {exams.map((exam, index) => (
                <Grid item xs={12} sm={6} md={4} key={exam.id}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <GlassCard
                      glassIntensity="medium"
                      elevated
                      hoverable
                      gradient={getStatusGradient(exam.durum)}
                      sx={{ height: '100%' }}
                    >
                      {/* Header */}
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'start',
                          mb: 2,
                        }}
                      >
                        <Chip
                          label={exam.sinav_tipi}
                          sx={{
                            background: getExamTypeGradient(exam.sinav_tipi),
                            color: 'white',
                            fontWeight: 700,
                          }}
                          size="small"
                        />
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Chip
                            label={getStatusLabel(exam.durum)}
                            size="small"
                            sx={{
                              background: getStatusGradient(exam.durum),
                              color: 'white',
                              fontWeight: 600,
                            }}
                          />
                          <IconButton size="small" onClick={(e) => handleMenuOpen(e, exam)}>
                            <MoreVert />
                          </IconButton>
                        </Box>
                      </Box>

                      {/* Title & Description */}
                      <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                        {exam.baslik}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        {exam.aciklama}
                      </Typography>

                      {/* Stats */}
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Assignment fontSize="small" color="action" />
                          <Typography variant="body2">
                            <strong>{exam.soru_sayisi}</strong> Soru
                          </Typography>
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Timer fontSize="small" color="action" />
                          <Typography variant="body2">
                            <strong>{exam.sure_dakika}</strong> Dakika
                          </Typography>
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <People fontSize="small" color="action" />
                          <Typography variant="body2">
                            <strong>{exam.katilimci_sayisi}</strong> Katılımcı
                          </Typography>
                        </Box>
                      </Box>

                      {/* Date */}
                      {exam.baslangic_tarihi && (
                        <Box sx={{ mb: 3 }}>
                          <Typography variant="caption" color="text.secondary">
                            Başlangıç: {new Date(exam.baslangic_tarihi).toLocaleString('tr-TR')}
                          </Typography>
                        </Box>
                      )}

                      {/* Actions */}
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <ModernButton variant="glass" icon={<Visibility />} size="small" fullWidth>
                          Görüntüle
                        </ModernButton>
                        {exam.durum === 'tamamlandi' && (
                          <ModernButton
                            variant="gradient"
                            gradient={modernColors.gradients.primary}
                            icon={<PlayArrow />}
                            size="small"
                            fullWidth
                          >
                            Sonuçlar
                          </ModernButton>
                        )}
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
                      background: modernColors.gradients.forest,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mx: 'auto',
                      mb: 3,
                    }}
                  >
                    <Quiz sx={{ fontSize: 64, color: 'white' }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                    Henüz sınav oluşturmadınız
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                    İlk sınavınızı oluşturmak için butona tıklayın
                  </Typography>
                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.forest}
                    icon={<Add />}
                    onClick={() => setCreateDialogOpen(true)}
                    glow
                  >
                    Sınav Oluştur
                  </ModernButton>
                </Box>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Context Menu */}
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItemComponent onClick={handleEditExam}>
            <Edit fontSize="small" sx={{ mr: 1 }} />
            Düzenle
          </MenuItemComponent>
          <MenuItemComponent onClick={handleViewResults}>
            <Visibility fontSize="small" sx={{ mr: 1 }} />
            Sonuçları Görüntüle
          </MenuItemComponent>
          <MenuItemComponent onClick={handleDeleteExam} sx={{ color: 'error.main' }}>
            <Delete fontSize="small" sx={{ mr: 1 }} />
            Sil
          </MenuItemComponent>
        </Menu>

        {/* Create Exam Dialog */}
        <Dialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          maxWidth="sm"
          fullWidth
          PaperProps={{
            sx: {
              background: modernColors.glass.white.light,
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            },
          }}
        >
          <DialogTitle>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Yeni Sınav Oluştur
            </Typography>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="Sınav Başlığı"
                value={formData.baslik}
                onChange={(e) => setFormData({ ...formData, baslik: e.target.value })}
              />
              <TextField
                fullWidth
                label="Açıklama"
                multiline
                rows={3}
                value={formData.aciklama}
                onChange={(e) => setFormData({ ...formData, aciklama: e.target.value })}
              />
              <FormControl fullWidth>
                <InputLabel>Sınav Tipi</InputLabel>
                <Select
                  value={formData.sinav_tipi}
                  label="Sınav Tipi"
                  onChange={(e) => setFormData({ ...formData, sinav_tipi: e.target.value as any })}
                >
                  <MenuItem value="TYT">TYT</MenuItem>
                  <MenuItem value="AYT">AYT</MenuItem>
                  <MenuItem value="YDT">YDT</MenuItem>
                </Select>
              </FormControl>
              <TextField
                fullWidth
                type="number"
                label="Soru Sayısı"
                value={formData.soru_sayisi}
                onChange={(e) =>
                  setFormData({ ...formData, soru_sayisi: parseInt(e.target.value) })
                }
              />
              <TextField
                fullWidth
                type="number"
                label="Süre (Dakika)"
                value={formData.sure_dakika}
                onChange={(e) =>
                  setFormData({ ...formData, sure_dakika: parseInt(e.target.value) })
                }
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <ModernButton variant="glass" onClick={() => setCreateDialogOpen(false)}>
              İptal
            </ModernButton>
            <ModernButton
              variant="gradient"
              gradient={modernColors.gradients.success}
              onClick={handleCreateExam}
              glow
            >
              Oluştur
            </ModernButton>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
}

export default ModernTeacherExamsPage;
