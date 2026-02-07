/**
 * Modern Teacher Classes Page - Glassmorphism Design
 * Öğretmen sınıf yönetimi
 */

import {
  Class,
  People,
  Add,
  Edit,
  Assessment,
  TrendingUp,
  School,
  MenuBook,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  Alert,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import modernColors from '../theme/modern-colors';
import { ClassInfo } from '../types';
import { useAuthStore } from '@/store/authStore';

export function ModernTeacherClassesPage() {
  const [classes, setClasses] = useState<ClassInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newClass, setNewClass] = useState({
    sinif_adi: '',
    seviye: '',
    ders: '',
  });

  const { user: _user } = useAuthStore();

  useEffect(() => {
    loadClasses();
  }, []);

  const loadClasses = async () => {
    try {
      setLoading(true);

      const response = await fetch('/api/v1/teacher/classes', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult = await response.json();

      if (!apiResult.success && !Array.isArray(apiResult)) {
        throw new Error(apiResult.message || 'Sınıf listesi alınamadı');
      }

      const classesData = Array.isArray(apiResult) ? apiResult : apiResult.data || [];
      setClasses(classesData);
    } catch (error: any) {
      console.error('Teacher Classes API hatası:', error);
      setError(`Sınıf listesi yüklenemedi: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClass = async () => {
    if (!newClass.sinif_adi || !newClass.seviye || !newClass.ders) {
      alert('Lütfen tüm alanları doldurun');
      return;
    }

    try {
      const response = await fetch('/api/v1/teacher/classes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(newClass),
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult = await response.json();

      if (!apiResult.success) {
        throw new Error(apiResult.message || 'Sınıf oluşturulamadı');
      }

      const createdClass = apiResult.data;

      setClasses((prev) => [...prev, createdClass]);
      setCreateDialogOpen(false);
      setNewClass({ sinif_adi: '', seviye: '', ders: '' });
    } catch (error: any) {
      console.error('Create Class API hatası:', error);
      alert(`Sınıf oluşturulamadı: ${error.message}`);
    }
  };

  const getSuccessGradient = (basari: number): string => {
    if (basari >= 80) {return modernColors.gradients.success;}
    if (basari >= 60) {return modernColors.gradients.warning;}
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
          background: modernColors.gradients.mesh,
        }}
      >
        <ModernLoader message="Sınıflar yükleniyor..." size="large" />
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
          background: modernColors.gradients.mesh,
          p: 2,
        }}
      >
        <Container maxWidth="sm">
          <GlassCard glassIntensity="medium" elevated>
            <Alert severity="error">{error}</Alert>
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <ModernButton
                variant="gradient"
                gradient={modernColors.gradients.primary}
                onClick={loadClasses}
              >
                Tekrar Dene
              </ModernButton>
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
                  background: modernColors.gradients.forest,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Class sx={{ fontSize: 32, color: 'white' }} />
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
                  Sınıflarım
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Sınıflarınızı yönetin ve öğrenci performansını takip edin
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>

        {/* Class Cards */}
        <AnimatePresence mode="wait">
          {classes.length > 0 ? (
            <Grid container spacing={3}>
              {classes.map((sinif, index) => (
                <Grid item xs={12} sm={6} md={4} key={sinif.sinif_id}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <GlassCard
                      glassIntensity="medium"
                      elevated
                      hoverable
                      gradient={getSuccessGradient(sinif.ortalama_basari)}
                      sx={{ height: '100%' }}
                    >
                      {/* Class Header */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                        <Box
                          sx={{
                            width: 48,
                            height: 48,
                            borderRadius: 2,
                            background: modernColors.gradients.primary,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <School sx={{ color: 'white' }} />
                        </Box>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" sx={{ fontWeight: 700 }}>
                            {sinif.sinif_adi}
                          </Typography>
                          <Chip label={sinif.seviye || 'Seviye belirtilmemiş'} size="small" />
                        </Box>
                      </Box>

                      {/* Stats */}
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <People fontSize="small" color="action" />
                          <Typography variant="body2">
                            <strong>{sinif.ogrenci_sayisi}</strong> öğrenci
                          </Typography>
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <TrendingUp fontSize="small" color="action" />
                          <Typography variant="body2">Ortalama Başarı:</Typography>
                          <Chip
                            label={`${sinif.ortalama_basari.toFixed(1)}%`}
                            size="small"
                            sx={{
                              background: getSuccessGradient(sinif.ortalama_basari),
                              color: 'white',
                              fontWeight: 600,
                            }}
                          />
                        </Box>

                        {sinif.ders && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <MenuBook fontSize="small" color="action" />
                            <Typography variant="body2">
                              <strong>{sinif.ders}</strong>
                            </Typography>
                          </Box>
                        )}
                      </Box>

                      {/* Actions */}
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <ModernButton variant="glass" icon={<People />} size="small" fullWidth>
                          Öğrenciler
                        </ModernButton>
                        <ModernButton variant="glass" icon={<Assessment />} size="small" fullWidth>
                          Sınavlar
                        </ModernButton>
                        <ModernButton variant="glass" icon={<Edit />} size="small" fullWidth>
                          Düzenle
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
                      background: modernColors.gradients.forest,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mx: 'auto',
                      mb: 3,
                    }}
                  >
                    <Class sx={{ fontSize: 64, color: 'white' }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                    Henüz sınıfınız bulunmuyor
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                    İlk sınıfınızı oluşturmak için aşağıdaki butona tıklayın
                  </Typography>
                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.forest}
                    icon={<Add />}
                    onClick={() => setCreateDialogOpen(true)}
                    glow
                  >
                    Sınıf Oluştur
                  </ModernButton>
                </Box>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* FAB for creating class */}
        {classes.length > 0 && (
          <Fab
            color="primary"
            aria-label="add class"
            sx={{
              position: 'fixed',
              bottom: 24,
              right: 24,
              background: modernColors.gradients.forest,
              '&:hover': {
                background: modernColors.gradients.forest,
              },
            }}
            onClick={() => setCreateDialogOpen(true)}
          >
            <Add />
          </Fab>
        )}

        {/* Create Class Dialog */}
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
              Yeni Sınıf Oluştur
            </Typography>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="Sınıf Adı"
                value={newClass.sinif_adi}
                onChange={(e) =>
                  setNewClass((prev) => ({ ...prev, sinif_adi: e.target.value }))
                }
                placeholder="örn: 12-A Matematik"
              />

              <FormControl fullWidth>
                <InputLabel>Seviye</InputLabel>
                <Select
                  value={newClass.seviye}
                  label="Seviye"
                  onChange={(e) => setNewClass((prev) => ({ ...prev, seviye: e.target.value }))}
                >
                  <MenuItem value="9">9. Sınıf</MenuItem>
                  <MenuItem value="10">10. Sınıf</MenuItem>
                  <MenuItem value="11">11. Sınıf</MenuItem>
                  <MenuItem value="12">12. Sınıf</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>Ders</InputLabel>
                <Select
                  value={newClass.ders}
                  label="Ders"
                  onChange={(e) => setNewClass((prev) => ({ ...prev, ders: e.target.value }))}
                >
                  <MenuItem value="matematik">Matematik</MenuItem>
                  <MenuItem value="fizik">Fizik</MenuItem>
                  <MenuItem value="kimya">Kimya</MenuItem>
                  <MenuItem value="biyoloji">Biyoloji</MenuItem>
                  <MenuItem value="turkce">Türkçe</MenuItem>
                  <MenuItem value="tarih">Tarih</MenuItem>
                  <MenuItem value="cografya">Coğrafya</MenuItem>
                  <MenuItem value="felsefe">Felsefe</MenuItem>
                  <MenuItem value="ingilizce">İngilizce</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </DialogContent>
          <DialogActions>
            <ModernButton variant="glass" onClick={() => setCreateDialogOpen(false)}>
              İptal
            </ModernButton>
            <ModernButton
              variant="gradient"
              gradient={modernColors.gradients.success}
              onClick={handleCreateClass}
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

export default ModernTeacherClassesPage;
