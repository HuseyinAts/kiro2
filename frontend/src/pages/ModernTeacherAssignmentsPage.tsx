/**
 * Modern Teacher Assignments Page - Glassmorphism Design
 * Öğretmen ödev yönetimi
 */

import {
  Assignment,
  Add,
  Edit,
  Delete,
  Schedule,
  MoreVert,
  Visibility,
  AttachFile,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Menu,
  MenuItem as MenuItemComponent,
  Fab,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import apiClient from '../services/apiClient';
import modernColors from '../theme/modern-colors';
import { useAuthStore } from '@/store/authStore';

interface AssignmentItem {
  id: string
  baslik: string
  aciklama: string
  sinif: string
  teslim_tarihi: string
  olusturma_tarihi: string
  durum: 'aktif' | 'tamamlandi' | 'iptal'
  teslim_eden: number
  toplam_ogrenci: number
  ek_dosya?: string
}

export function ModernTeacherAssignmentsPage() {
  const { user: _user } = useAuthStore();
  const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<AssignmentItem | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [newAssignment, setNewAssignment] = useState({
    baslik: '',
    aciklama: '',
    sinif: '',
    teslim_tarihi: '',
  });

  useEffect(() => {
    fetchAssignments();
  }, []);

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/teacher/assignments');
      setAssignments(response.data.assignments || []);
    } catch (error) {
      console.error('Ödevler yüklenemedi:', error);
      // Mock data
      setAssignments([
        {
          id: '1',
          baslik: 'Matematik Ödev 1 - Türev Uygulamaları',
          aciklama: 'Sayfa 124-130 arası tüm soruları çözünüz',
          sinif: '12-A',
          teslim_tarihi: '2025-11-25T23:59:00',
          olusturma_tarihi: '2025-11-15T10:00:00',
          durum: 'aktif',
          teslim_eden: 35,
          toplam_ogrenci: 45,
        },
        {
          id: '2',
          baslik: 'Fizik Problemleri - Elektrik',
          aciklama: 'Elektrik devre çözümlemeleri',
          sinif: '12-B',
          teslim_tarihi: '2025-11-22T23:59:00',
          olusturma_tarihi: '2025-11-12T14:30:00',
          durum: 'aktif',
          teslim_eden: 28,
          toplam_ogrenci: 40,
          ek_dosya: 'elektrik_problemleri.pdf',
        },
        {
          id: '3',
          baslik: 'Kimya Deney Raporu',
          aciklama: 'Asit-baz titrasyonu deney raporu hazırlayınız',
          sinif: '11-A',
          teslim_tarihi: '2025-11-20T23:59:00',
          olusturma_tarihi: '2025-11-01T10:00:00',
          durum: 'tamamlandi',
          teslim_eden: 38,
          toplam_ogrenci: 38,
        },
        {
          id: '4',
          baslik: 'Biyoloji Proje Ödevi',
          aciklama: 'Genetik mühendisliği üzerine araştırma',
          sinif: '12-A',
          teslim_tarihi: '2025-11-28T23:59:00',
          olusturma_tarihi: '2025-11-10T09:00:00',
          durum: 'aktif',
          teslim_eden: 12,
          toplam_ogrenci: 45,
        },
        {
          id: '5',
          baslik: 'Matematik Ödev 2 - İntegral',
          aciklama: 'Belirsiz ve belirli integral soruları',
          sinif: '12-B',
          teslim_tarihi: '2025-11-18T23:59:00',
          olusturma_tarihi: '2025-11-05T11:00:00',
          durum: 'tamamlandi',
          teslim_eden: 40,
          toplam_ogrenci: 40,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAssignment = async () => {
    if (!newAssignment.baslik || !newAssignment.sinif || !newAssignment.teslim_tarihi) {
      alert('Lütfen tüm zorunlu alanları doldurun');
      return;
    }

    try {
      await apiClient.post('/api/v1/teacher/assignments', newAssignment);
      setCreateDialogOpen(false);
      fetchAssignments();
      setNewAssignment({ baslik: '', aciklama: '', sinif: '', teslim_tarihi: '' });
    } catch (error) {
      console.error('Ödev oluşturulamadı:', error);
      alert('Ödev oluşturulurken bir hata oluştu');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, assignment: AssignmentItem) => {
    setAnchorEl(event.currentTarget);
    setSelectedAssignment(assignment);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleEditAssignment = () => {
    alert(`Ödevi düzenle: ${selectedAssignment?.baslik}`);
    handleMenuClose();
  };

  const handleDeleteAssignment = async () => {
    if (selectedAssignment && window.confirm('Bu ödevi silmek istediğinizden emin misiniz?')) {
      try {
        await apiClient.delete(`/api/v1/teacher/assignments/${selectedAssignment.id}`);
        fetchAssignments();
      } catch (error) {
        console.error('Ödev silinemedi:', error);
      }
    }
    handleMenuClose();
  };

  const handleViewSubmissions = () => {
    alert(`Teslimler: ${selectedAssignment?.baslik}`);
    handleMenuClose();
  };

  const getStatusGradient = (durum: string): string => {
    switch (durum) {
      case 'aktif':
        return modernColors.gradients.success;
      case 'tamamlandi':
        return modernColors.gradients.ocean;
      case 'iptal':
        return modernColors.gradients.error;
      default:
        return modernColors.gradients.primary;
    }
  };

  const getStatusLabel = (durum: string): string => {
    switch (durum) {
      case 'aktif':
        return 'Aktif';
      case 'tamamlandi':
        return 'Tamamlandı';
      case 'iptal':
        return 'İptal';
      default:
        return durum;
    }
  };

  const getSubmissionPercentage = (teslim: number, toplam: number): number => {
    return Math.round((teslim / toplam) * 100);
  };

  const getSubmissionGradient = (percentage: number): string => {
    if (percentage >= 80) {return modernColors.gradients.success;}
    if (percentage >= 50) {return modernColors.gradients.warning;}
    return modernColors.gradients.error;
  };

  const getDaysRemaining = (dueDate: string): number => {
    const now = new Date();
    const due = new Date(dueDate);
    const diff = due.getTime() - now.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  };

  const getDaysRemainingText = (dueDate: string): string => {
    const days = getDaysRemaining(dueDate);
    if (days < 0) {return `${Math.abs(days)} gün geçti`;}
    if (days === 0) {return 'Bugün son gün';}
    if (days === 1) {return 'Yarın son gün';}
    return `${days} gün kaldı`;
  };

  const getDaysRemainingColor = (dueDate: string): string => {
    const days = getDaysRemaining(dueDate);
    if (days < 0) {return modernColors.gradients.error;}
    if (days <= 2) {return modernColors.gradients.warning;}
    return modernColors.gradients.success;
  };

  const activeAssignments = assignments.filter((a) => a.durum === 'aktif');
  const completedAssignments = assignments.filter((a) => a.durum === 'tamamlandi');
  const totalSubmissions = assignments.reduce((sum, a) => sum + a.teslim_eden, 0);
  const totalStudents = assignments.reduce((sum, a) => sum + a.toplam_ogrenci, 0);
  const avgSubmissionRate = totalStudents > 0 ? Math.round((totalSubmissions / totalStudents) * 100) : 0;

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
        <ModernLoader message="Ödevler yükleniyor..." size="large" />
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
                <Assignment sx={{ fontSize: 32, color: 'white' }} />
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
                  Ödev Yönetimi
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Ödevleri takip edin ve teslim durumunu izleyin
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>

        {/* Stats Summary */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.primary}>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {assignments.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Toplam Ödev
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.success}>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {activeAssignments.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Aktif Ödev
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.ocean}>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {completedAssignments.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Tamamlanan
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.warning}>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {avgSubmissionRate}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Ortalama Teslim
                </Typography>
              </GlassCard>
            </Grid>
          </Grid>
        </motion.div>

        {/* Assignment Cards */}
        <AnimatePresence mode="wait">
          {assignments.length > 0 ? (
            <Grid container spacing={3}>
              {assignments.map((assignment, index) => {
                const submissionPercentage = getSubmissionPercentage(
                  assignment.teslim_eden,
                  assignment.toplam_ogrenci,
                );

                return (
                  <Grid item xs={12} sm={6} md={4} key={assignment.id}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                    >
                      <GlassCard
                        glassIntensity="medium"
                        elevated
                        hoverable
                        gradient={getStatusGradient(assignment.durum)}
                      >
                        {/* Assignment Header */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                          <Chip
                            label={assignment.sinif}
                            sx={{
                              background: modernColors.gradients.primary,
                              color: 'white',
                              fontWeight: 700,
                            }}
                          />
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Chip label={getStatusLabel(assignment.durum)} size="small" />
                            <IconButton
                              size="small"
                              onClick={(e) => handleMenuOpen(e, assignment)}
                            >
                              <MoreVert />
                            </IconButton>
                          </Box>
                        </Box>

                        {/* Assignment Info */}
                        <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                          {assignment.baslik}
                        </Typography>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            mb: 2,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                          }}
                        >
                          {assignment.aciklama}
                        </Typography>

                        {/* Due Date */}
                        {assignment.durum === 'aktif' && (
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 1,
                              mb: 2,
                              p: 1.5,
                              borderRadius: 2,
                              background: `linear-gradient(135deg, ${getDaysRemainingColor(assignment.teslim_tarihi)})`,
                            }}
                          >
                            <Schedule fontSize="small" sx={{ color: 'white' }} />
                            <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>
                              {getDaysRemainingText(assignment.teslim_tarihi)}
                            </Typography>
                          </Box>
                        )}

                        {/* Submission Progress */}
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
                              Teslim Durumu
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {assignment.teslim_eden}/{assignment.toplam_ogrenci}
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={submissionPercentage}
                            sx={{
                              height: 8,
                              borderRadius: 4,
                              backgroundColor: modernColors.glass.black.light,
                              '& .MuiLinearProgress-bar': {
                                borderRadius: 4,
                                background: getSubmissionGradient(submissionPercentage),
                              },
                            }}
                          />
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: 'block', mt: 0.5 }}
                          >
                            {submissionPercentage}% teslim edildi
                          </Typography>
                        </Box>

                        {/* Attachment */}
                        {assignment.ek_dosya && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                            <AttachFile fontSize="small" color="action" />
                            <Typography variant="caption" color="text.secondary">
                              {assignment.ek_dosya}
                            </Typography>
                          </Box>
                        )}

                        {/* Actions */}
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <ModernButton
                            variant="glass"
                            icon={<Visibility />}
                            size="small"
                            fullWidth
                            onClick={handleViewSubmissions}
                          >
                            Teslimler
                          </ModernButton>
                          <ModernButton
                            variant="glass"
                            icon={<Edit />}
                            size="small"
                            fullWidth
                            onClick={handleEditAssignment}
                          >
                            Düzenle
                          </ModernButton>
                        </Box>
                      </GlassCard>
                    </motion.div>
                  </Grid>
                );
              })}
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
                    <Assignment sx={{ fontSize: 64, color: 'white' }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                    Henüz ödev bulunmuyor
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                    İlk ödevi oluşturmak için aşağıdaki butona tıklayın
                  </Typography>
                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.forest}
                    icon={<Add />}
                    onClick={() => setCreateDialogOpen(true)}
                    glow
                  >
                    Ödev Oluştur
                  </ModernButton>
                </Box>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* FAB for creating assignment */}
        {assignments.length > 0 && (
          <Fab
            color="primary"
            aria-label="add assignment"
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

        {/* Context Menu */}
        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItemComponent onClick={handleEditAssignment}>
            <Edit fontSize="small" sx={{ mr: 1 }} />
            Düzenle
          </MenuItemComponent>
          <MenuItemComponent onClick={handleViewSubmissions}>
            <Visibility fontSize="small" sx={{ mr: 1 }} />
            Teslimler
          </MenuItemComponent>
          <MenuItemComponent onClick={handleDeleteAssignment} sx={{ color: 'error.main' }}>
            <Delete fontSize="small" sx={{ mr: 1 }} />
            Sil
          </MenuItemComponent>
        </Menu>

        {/* Create Assignment Dialog */}
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
              Yeni Ödev Oluştur
            </Typography>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="Ödev Başlığı"
                value={newAssignment.baslik}
                onChange={(e) => setNewAssignment({ ...newAssignment, baslik: e.target.value })}
                placeholder="örn: Matematik Ödev 3"
              />

              <TextField
                fullWidth
                label="Açıklama"
                multiline
                rows={3}
                value={newAssignment.aciklama}
                onChange={(e) => setNewAssignment({ ...newAssignment, aciklama: e.target.value })}
                placeholder="Ödev detaylarını açıklayın"
              />

              <FormControl fullWidth>
                <InputLabel>Sınıf</InputLabel>
                <Select
                  value={newAssignment.sinif}
                  label="Sınıf"
                  onChange={(e) => setNewAssignment({ ...newAssignment, sinif: e.target.value })}
                >
                  <MenuItem value="9-A">9-A</MenuItem>
                  <MenuItem value="10-A">10-A</MenuItem>
                  <MenuItem value="11-A">11-A</MenuItem>
                  <MenuItem value="12-A">12-A</MenuItem>
                  <MenuItem value="12-B">12-B</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                type="datetime-local"
                label="Teslim Tarihi"
                value={newAssignment.teslim_tarihi}
                onChange={(e) =>
                  setNewAssignment({ ...newAssignment, teslim_tarihi: e.target.value })
                }
                InputLabelProps={{ shrink: true }}
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
              onClick={handleCreateAssignment}
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

export default ModernTeacherAssignmentsPage;
