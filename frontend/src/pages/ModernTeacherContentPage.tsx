/**
 * Modern Teacher Content Page - Glassmorphism Design
 * Öğretmen içerik yönetimi
 */

import {
  Folder,
  Add,
  VideoLibrary,
  Description,
  Slideshow,
  Quiz,
  Search,
  Edit,
  Delete,
  Visibility,
  Download,
  MoreVert,
  CloudUpload,
  CalendarToday,
  Subject,
} from '@mui/icons-material';
import {
  Typography,
  Box,
  Grid,
  Chip,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Menu,
  MenuItem as MenuItemComponent,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { DashboardScaffold } from '../components/Layout/DashboardScaffold';
import apiClient from '../services/apiClient';
import modernColors from '../theme/modern-colors';
import { useAuthStore } from '@/store/authStore';

interface Content {
  id: string
  baslik: string
  aciklama: string
  tip: 'video' | 'dokuman' | 'sunum' | 'quiz' | 'diger'
  konu: string
  sinif: string
  tarih: string
  boyut: string
  goruntulenme: number
}

export function ModernTeacherContentPage() {
  const { user: _user } = useAuthStore();
  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterSubject, setFilterSubject] = useState<string>('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [newContent, setNewContent] = useState({
    baslik: '',
    aciklama: '',
    tip: 'dokuman' as 'video' | 'dokuman' | 'sunum' | 'quiz' | 'diger',
    konu: '',
    sinif: '',
  });

  useEffect(() => {
    fetchContents();
  }, []);

  const fetchContents = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/teacher/contents');
      setContents(response?.data?.contents || []);
    } catch (error) {
      console.error('İçerikler yüklenemedi:', error);
      // Mock data
      setContents([
        {
          id: '1',
          baslik: 'Türev Konusu Ders Notları',
          aciklama: 'Detaylı türev konusu anlatım notları',
          tip: 'dokuman',
          konu: 'Matematik',
          sinif: '12-A',
          tarih: '2025-11-15T10:00:00',
          boyut: '2.4 MB',
          goruntulenme: 145,
        },
        {
          id: '2',
          baslik: 'Fizik - Elektrik Video Dersi',
          aciklama: 'Elektrik devre analizi video anlatım',
          tip: 'video',
          konu: 'Fizik',
          sinif: '12-B',
          tarih: '2025-11-14T14:30:00',
          boyut: '124 MB',
          goruntulenme: 89,
        },
        {
          id: '3',
          baslik: 'Kimya Asit-Baz Sunumu',
          aciklama: 'Asit-baz dengesi sunum',
          tip: 'sunum',
          konu: 'Kimya',
          sinif: '11-A',
          tarih: '2025-11-12T09:15:00',
          boyut: '8.6 MB',
          goruntulenme: 67,
        },
        {
          id: '4',
          baslik: 'Matematik İntegral Quiz',
          aciklama: 'İntegral konusu test soruları',
          tip: 'quiz',
          konu: 'Matematik',
          sinif: '12-A',
          tarih: '2025-11-10T11:00:00',
          boyut: '1.2 MB',
          goruntulenme: 198,
        },
        {
          id: '5',
          baslik: 'Biyoloji Genetik Ders Notları',
          aciklama: 'Genetik mühendisliği özet notlar',
          tip: 'dokuman',
          konu: 'Biyoloji',
          sinif: '12-A',
          tarih: '2025-11-08T16:45:00',
          boyut: '3.1 MB',
          goruntulenme: 112,
        },
        {
          id: '6',
          baslik: 'Fizik Optik Video Dersi',
          aciklama: 'Işık ve optik olaylar video',
          tip: 'video',
          konu: 'Fizik',
          sinif: '11-B',
          tarih: '2025-11-05T13:20:00',
          boyut: '156 MB',
          goruntulenme: 78,
        },
        {
          id: '7',
          baslik: 'Matematik Geometri Sunumu',
          aciklama: 'Analitik geometri sunum',
          tip: 'sunum',
          konu: 'Matematik',
          sinif: '12-B',
          tarih: '2025-11-03T10:30:00',
          boyut: '12.4 MB',
          goruntulenme: 134,
        },
        {
          id: '8',
          baslik: 'Kimya Organik Kimya Quiz',
          aciklama: 'Organik bileşikler test',
          tip: 'quiz',
          konu: 'Kimya',
          sinif: '12-A',
          tarih: '2025-11-01T15:00:00',
          boyut: '856 KB',
          goruntulenme: 167,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateContent = async () => {
    if (!newContent.baslik || !newContent.konu || !newContent.sinif) {
      alert('Lütfen tüm zorunlu alanları doldurun');
      return;
    }

    try {
      await apiClient.post('/api/v1/teacher/contents', newContent);
      setCreateDialogOpen(false);
      fetchContents();
      setNewContent({
        baslik: '',
        aciklama: '',
        tip: 'dokuman',
        konu: '',
        sinif: '',
      });
    } catch (error) {
      console.error('İçerik oluşturulamadı:', error);
      alert('İçerik oluşturulurken bir hata oluştu');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, content: Content) => {
    setAnchorEl(event.currentTarget);
    setSelectedContent(content);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleEditContent = () => {
    alert(`İçeriği düzenle: ${selectedContent?.baslik}`);
    handleMenuClose();
  };

  const handleDeleteContent = async () => {
    if (selectedContent && window.confirm('Bu içeriği silmek istediğinizden emin misiniz?')) {
      try {
        await apiClient.delete(`/api/v1/teacher/contents/${selectedContent.id}`);
        fetchContents();
      } catch (error) {
        console.error('İçerik silinemedi:', error);
      }
    }
    handleMenuClose();
  };

  const handleDownloadContent = () => {
    alert(`İndir: ${selectedContent?.baslik}`);
    handleMenuClose();
  };

  const getTypeGradient = (tip: string): string => {
    switch (tip) {
      case 'video':
        return modernColors.gradients.sunset;
      case 'dokuman':
        return modernColors.gradients.primary;
      case 'sunum':
        return modernColors.gradients.ocean;
      case 'quiz':
        return modernColors.gradients.success;
      default:
        return modernColors.gradients.forest;
    }
  };

  const getTypeIcon = (tip: string) => {
    switch (tip) {
      case 'video':
        return <VideoLibrary sx={{ fontSize: 32 }} />;
      case 'dokuman':
        return <Description sx={{ fontSize: 32 }} />;
      case 'sunum':
        return <Slideshow sx={{ fontSize: 32 }} />;
      case 'quiz':
        return <Quiz sx={{ fontSize: 32 }} />;
      default:
        return <Folder sx={{ fontSize: 32 }} />;
    }
  };

  const getTypeLabel = (tip: string): string => {
    switch (tip) {
      case 'video':
        return 'Video';
      case 'dokuman':
        return 'Doküman';
      case 'sunum':
        return 'Sunum';
      case 'quiz':
        return 'Quiz';
      default:
        return 'Diğer';
    }
  };

  const filteredContents = contents.filter((content) => {
    const matchesSearch =
      content.baslik.toLowerCase().includes(searchTerm.toLowerCase()) ||
      content.aciklama.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || content.tip === filterType;
    const matchesSubject = filterSubject === 'all' || content.konu === filterSubject;
    return matchesSearch && matchesType && matchesSubject;
  });

  const getContentCountByType = (tip: string) => {
    return contents.filter((c) => c.tip === tip).length;
  };

  const uniqueSubjects = Array.from(new Set(contents.map((c) => c.konu)));

  return (
    <DashboardScaffold
      loading={loading}
      loadingMessage="İçerikler yükleniyor..."
      icon={<Folder />}
      iconGradient={modernColors.gradients.forest}
      title="İçerik Yönetimi"
      titleGradient={modernColors.gradients.forest}
      subtitle="Eğitim içeriklerinizi yönetin ve paylaşın"
      maxWidth="lg"
    >
        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  placeholder="İçerik ara..."
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
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>İçerik Tipi</InputLabel>
                  <Select
                    value={filterType}
                    label="İçerik Tipi"
                    onChange={(e) => setFilterType(e.target.value)}
                  >
                    <MenuItem value="all">Tümü</MenuItem>
                    <MenuItem value="video">Video</MenuItem>
                    <MenuItem value="dokuman">Doküman</MenuItem>
                    <MenuItem value="sunum">Sunum</MenuItem>
                    <MenuItem value="quiz">Quiz</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Konu</InputLabel>
                  <Select
                    value={filterSubject}
                    label="Konu"
                    onChange={(e) => setFilterSubject(e.target.value)}
                  >
                    <MenuItem value="all">Tümü</MenuItem>
                    {uniqueSubjects.map((subject) => (
                      <MenuItem key={subject} value={subject}>
                        {subject}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </GlassCard>
        </motion.div>

        {/* Stats Summary */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.sunset}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getContentCountByType('video')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Video
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.primary}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getContentCountByType('dokuman')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Doküman
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.ocean}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getContentCountByType('sunum')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Sunum
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={3}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.success}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getContentCountByType('quiz')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Quiz
                </Typography>
              </GlassCard>
            </Grid>
          </Grid>
        </motion.div>

        {/* Content Cards */}
        <AnimatePresence mode="wait">
          {filteredContents.length > 0 ? (
            <Grid container spacing={3}>
              {filteredContents.map((content, index) => (
                <Grid item xs={12} sm={6} md={4} key={content.id}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <GlassCard
                      glassIntensity="medium"
                      elevated
                      hoverable
                      gradient={getTypeGradient(content.tip)}
                    >
                      {/* Content Header */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                        <Box
                          sx={{
                            width: 56,
                            height: 56,
                            borderRadius: 2,
                            background: getTypeGradient(content.tip),
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                          }}
                        >
                          {getTypeIcon(content.tip)}
                        </Box>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, alignItems: 'flex-end' }}>
                          <Chip
                            label={getTypeLabel(content.tip)}
                            size="small"
                            sx={{
                              background: getTypeGradient(content.tip),
                              color: 'white',
                              fontWeight: 600,
                            }}
                          />
                          <IconButton size="small" onClick={(e) => handleMenuOpen(e, content)}>
                            <MoreVert />
                          </IconButton>
                        </Box>
                      </Box>

                      {/* Content Info */}
                      <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                        {content.baslik}
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
                        {content.aciklama}
                      </Typography>

                      {/* Content Metadata */}
                      <Box
                        sx={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 1,
                          mb: 2,
                          p: 1.5,
                          borderRadius: 2,
                          background: modernColors.glass.white.medium,
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Subject fontSize="small" color="action" />
                            <Typography variant="caption">{content.konu}</Typography>
                          </Box>
                          <Chip label={content.sinif} size="small" />
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <CalendarToday fontSize="small" color="action" />
                            <Typography variant="caption" color="text.secondary">
                              {new Date(content.tarih).toLocaleDateString('tr-TR')}
                            </Typography>
                          </Box>
                          <Typography variant="caption" color="text.secondary">
                            {content.boyut}
                          </Typography>
                        </Box>
                      </Box>

                      {/* View Count */}
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 1,
                          mb: 2,
                          p: 1,
                          borderRadius: 2,
                          background: `linear-gradient(135deg, ${getTypeGradient(content.tip)})`,
                        }}
                      >
                        <Visibility sx={{ color: 'white', fontSize: 18 }} />
                        <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>
                          {content.goruntulenme} görüntülenme
                        </Typography>
                      </Box>

                      {/* Actions */}
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <ModernButton
                          variant="glass"
                          icon={<Visibility />}
                          size="small"
                          fullWidth
                        >
                          Görüntüle
                        </ModernButton>
                        <ModernButton
                          variant="glass"
                          icon={<Download />}
                          size="small"
                          fullWidth
                          onClick={handleDownloadContent}
                        >
                          İndir
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
                    <Folder sx={{ fontSize: 64, color: 'white' }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                    İçerik bulunamadı
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                    Arama kriterlerinize uygun içerik bulunmamaktadır
                  </Typography>
                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.forest}
                    icon={<Add />}
                    onClick={() => setCreateDialogOpen(true)}
                    glow
                  >
                    İçerik Ekle
                  </ModernButton>
                </Box>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* FAB for creating content */}
        {filteredContents.length > 0 && (
          <Fab
            color="primary"
            aria-label="add content"
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
          <MenuItemComponent onClick={handleEditContent}>
            <Edit fontSize="small" sx={{ mr: 1 }} />
            Düzenle
          </MenuItemComponent>
          <MenuItemComponent onClick={handleDownloadContent}>
            <Download fontSize="small" sx={{ mr: 1 }} />
            İndir
          </MenuItemComponent>
          <MenuItemComponent onClick={handleDeleteContent} sx={{ color: 'error.main' }}>
            <Delete fontSize="small" sx={{ mr: 1 }} />
            Sil
          </MenuItemComponent>
        </Menu>

        {/* Create Content Dialog */}
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
              Yeni İçerik Ekle
            </Typography>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="İçerik Başlığı"
                value={newContent.baslik}
                onChange={(e) => setNewContent({ ...newContent, baslik: e.target.value })}
                placeholder="örn: Matematik Ders Notları"
              />

              <TextField
                fullWidth
                label="Açıklama"
                multiline
                rows={3}
                value={newContent.aciklama}
                onChange={(e) => setNewContent({ ...newContent, aciklama: e.target.value })}
                placeholder="İçerik açıklaması"
              />

              <FormControl fullWidth>
                <InputLabel>İçerik Tipi</InputLabel>
                <Select
                  value={newContent.tip}
                  label="İçerik Tipi"
                  onChange={(e) =>
                    setNewContent({ ...newContent, tip: e.target.value as any })
                  }
                >
                  <MenuItem value="dokuman">Doküman</MenuItem>
                  <MenuItem value="video">Video</MenuItem>
                  <MenuItem value="sunum">Sunum</MenuItem>
                  <MenuItem value="quiz">Quiz</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Konu"
                value={newContent.konu}
                onChange={(e) => setNewContent({ ...newContent, konu: e.target.value })}
                placeholder="örn: Matematik"
              />

              <FormControl fullWidth>
                <InputLabel>Sınıf</InputLabel>
                <Select
                  value={newContent.sinif}
                  label="Sınıf"
                  onChange={(e) => setNewContent({ ...newContent, sinif: e.target.value })}
                >
                  <MenuItem value="9-A">9-A</MenuItem>
                  <MenuItem value="10-A">10-A</MenuItem>
                  <MenuItem value="11-A">11-A</MenuItem>
                  <MenuItem value="11-B">11-B</MenuItem>
                  <MenuItem value="12-A">12-A</MenuItem>
                  <MenuItem value="12-B">12-B</MenuItem>
                </Select>
              </FormControl>

              <Box
                sx={{
                  p: 3,
                  border: '2px dashed rgba(0, 0, 0, 0.2)',
                  borderRadius: 2,
                  textAlign: 'center',
                  cursor: 'pointer',
                  '&:hover': {
                    borderColor: 'primary.main',
                    background: modernColors.glass.white.light,
                  },
                }}
              >
                <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Dosya yüklemek için tıklayın
                </Typography>
              </Box>
            </Box>
          </DialogContent>
          <DialogActions>
            <ModernButton variant="glass" onClick={() => setCreateDialogOpen(false)}>
              İptal
            </ModernButton>
            <ModernButton
              variant="gradient"
              gradient={modernColors.gradients.success}
              onClick={handleCreateContent}
              glow
            >
              Ekle
            </ModernButton>
          </DialogActions>
        </Dialog>
    </DashboardScaffold>
  );
}

export default ModernTeacherContentPage;
