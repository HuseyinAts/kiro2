/**
 * Modern Admin Content Page - Glassmorphism Design
 * Admin içerik moderasyonu
 */

import {
  Folder,
  CheckCircle,
  Cancel,
  Visibility,
  HourglassEmpty,
  VideoLibrary,
  Description,
  Quiz,
  Person,
  CalendarToday,
  Search,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Chip,
  Tabs,
  Tab,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import apiClient from '../services/apiClient';
import modernColors from '../theme/modern-colors';

interface Content {
  id: string
  baslik: string
  aciklama: string
  tip: 'soru' | 'video' | 'dokuman' | 'quiz'
  kullanici: string
  kullanici_id: string
  tarih: string
  durum: 'beklemede' | 'onaylandi' | 'reddedildi'
  neden?: string
}

export function ModernAdminContentPage() {
  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('beklemede');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [_rejectReason, setRejectReason] = useState('');

  useEffect(() => {
    fetchContents();
  }, []);

  const fetchContents = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/admin/content');
      setContents(response.data.contents || []);
    } catch (error) {
      console.error('İçerikler yüklenemedi:', error);
      // Mock data
      setContents([
        {
          id: '1',
          baslik: 'Matematik TYT Soru Seti - Türev',
          aciklama: '50 adet türev sorusu içeren kapsamlı soru seti',
          tip: 'soru',
          kullanici: 'Ahmet Öğretmen',
          kullanici_id: '101',
          tarih: '2025-11-21T10:30:00',
          durum: 'beklemede',
        },
        {
          id: '2',
          baslik: 'Fizik Video Dersi - Elektrik',
          aciklama: 'Elektrik konusu detaylı video anlatım',
          tip: 'video',
          kullanici: 'Ayşe Öğretmen',
          kullanici_id: '102',
          tarih: '2025-11-20T14:20:00',
          durum: 'beklemede',
        },
        {
          id: '3',
          baslik: 'Kimya Ders Notu - Asit Baz',
          aciklama: 'Asit-baz dengesi özet notları',
          tip: 'dokuman',
          kullanici: 'Mehmet Öğretmen',
          kullanici_id: '103',
          tarih: '2025-11-19T09:15:00',
          durum: 'onaylandi',
        },
        {
          id: '4',
          baslik: 'Biyoloji Quiz - Genetik',
          aciklama: 'Genetik konusu test soruları',
          tip: 'quiz',
          kullanici: 'Fatma Öğretmen',
          kullanici_id: '104',
          tarih: '2025-11-18T16:45:00',
          durum: 'beklemede',
        },
        {
          id: '5',
          baslik: 'Edebiyat Ders Notları',
          aciklama: 'Divan edebiyatı özet',
          tip: 'dokuman',
          kullanici: 'Ali Öğretmen',
          kullanici_id: '105',
          tarih: '2025-11-17T11:00:00',
          durum: 'reddedildi',
          neden: 'İçerik standartlara uygun değil',
        },
        {
          id: '6',
          baslik: 'Tarih Video Dersi - Osmanlı',
          aciklama: 'Osmanlı tarihi anlatımı',
          tip: 'video',
          kullanici: 'Zeynep Öğretmen',
          kullanici_id: '106',
          tarih: '2025-11-16T13:30:00',
          durum: 'onaylandi',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (contentId: string) => {
    try {
      await apiClient.patch(`/api/v1/admin/content/${contentId}/approve`);
      setContents((prev) =>
        prev.map((c) => (c.id === contentId ? { ...c, durum: 'onaylandi' as const } : c)),
      );
    } catch (error) {
      console.error('İçerik onaylanamadı:', error);
    }
  };

  const handleReject = async (contentId: string, reason: string) => {
    try {
      await apiClient.patch(`/api/v1/admin/content/${contentId}/reject`, { neden: reason });
      setContents((prev) =>
        prev.map((c) =>
          c.id === contentId ? { ...c, durum: 'reddedildi' as const, neden: reason } : c,
        ),
      );
      setRejectReason('');
    } catch (error) {
      console.error('İçerik reddedilemedi:', error);
    }
  };

  const handleView = (content: Content) => {
    setSelectedContent(content);
    setViewDialogOpen(true);
  };

  const getTypeGradient = (tip: string): string => {
    switch (tip) {
      case 'soru':
        return modernColors.gradients.primary;
      case 'video':
        return modernColors.gradients.sunset;
      case 'dokuman':
        return modernColors.gradients.ocean;
      case 'quiz':
        return modernColors.gradients.success;
      default:
        return modernColors.gradients.fire;
    }
  };

  const getTypeIcon = (tip: string) => {
    switch (tip) {
      case 'soru':
        return <Quiz sx={{ fontSize: 32 }} />;
      case 'video':
        return <VideoLibrary sx={{ fontSize: 32 }} />;
      case 'dokuman':
        return <Description sx={{ fontSize: 32 }} />;
      case 'quiz':
        return <Quiz sx={{ fontSize: 32 }} />;
      default:
        return <Folder sx={{ fontSize: 32 }} />;
    }
  };

  const getTypeLabel = (tip: string): string => {
    switch (tip) {
      case 'soru':
        return 'Soru';
      case 'video':
        return 'Video';
      case 'dokuman':
        return 'Doküman';
      case 'quiz':
        return 'Quiz';
      default:
        return tip;
    }
  };

  const getStatusGradient = (durum: string): string => {
    switch (durum) {
      case 'beklemede':
        return modernColors.gradients.warning;
      case 'onaylandi':
        return modernColors.gradients.success;
      case 'reddedildi':
        return modernColors.gradients.error;
      default:
        return modernColors.gradients.ocean;
    }
  };

  const getStatusLabel = (durum: string): string => {
    switch (durum) {
      case 'beklemede':
        return 'Beklemede';
      case 'onaylandi':
        return 'Onaylandı';
      case 'reddedildi':
        return 'Reddedildi';
      default:
        return durum;
    }
  };

  const filteredContents = contents.filter((content) => {
    const matchesTab = activeTab === 'all' || content.durum === activeTab;
    const matchesSearch =
      content.baslik.toLowerCase().includes(searchTerm.toLowerCase()) ||
      content.kullanici.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || content.tip === filterType;
    return matchesTab && matchesSearch && matchesType;
  });

  const getContentCountByStatus = (durum: string) => {
    return contents.filter((c) => c.durum === durum).length;
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
        <ModernLoader message="İçerikler yükleniyor..." size="large" />
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
                  background: modernColors.gradients.fire,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Folder sx={{ fontSize: 32, color: 'white' }} />
              </Box>
              <Box>
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 900,
                    background: modernColors.gradients.fire,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  İçerik Moderasyonu
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Platform içeriklerini yönetin ve onaylayın
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
            <Tabs
              value={activeTab}
              onChange={(_, newValue) => setActiveTab(newValue)}
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Folder fontSize="small" />
                    Tümü ({contents.length})
                  </Box>
                }
                value="all"
              />
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <HourglassEmpty fontSize="small" />
                    Beklemede ({getContentCountByStatus('beklemede')})
                  </Box>
                }
                value="beklemede"
              />
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircle fontSize="small" />
                    Onaylı ({getContentCountByStatus('onaylandi')})
                  </Box>
                }
                value="onaylandi"
              />
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Cancel fontSize="small" />
                    Reddedildi ({getContentCountByStatus('reddedildi')})
                  </Box>
                }
                value="reddedildi"
              />
            </Tabs>
          </GlassCard>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  placeholder="İçerik veya yükleyen ara..."
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
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>İçerik Tipi</InputLabel>
                  <Select
                    value={filterType}
                    label="İçerik Tipi"
                    onChange={(e) => setFilterType(e.target.value)}
                  >
                    <MenuItem value="all">Tümü</MenuItem>
                    <MenuItem value="soru">Soru</MenuItem>
                    <MenuItem value="video">Video</MenuItem>
                    <MenuItem value="dokuman">Doküman</MenuItem>
                    <MenuItem value="quiz">Quiz</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </GlassCard>
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
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <GlassCard
                      glassIntensity="medium"
                      elevated
                      hoverable
                      gradient={getStatusGradient(content.durum)}
                    >
                      {/* Header */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                        <Box
                          sx={{
                            width: 48,
                            height: 48,
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
                          <Chip
                            label={getStatusLabel(content.durum)}
                            size="small"
                            sx={{
                              background: getStatusGradient(content.durum),
                              color: 'white',
                              fontWeight: 600,
                            }}
                          />
                        </Box>
                      </Box>

                      {/* Content */}
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

                      {/* Meta */}
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
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Person fontSize="small" color="action" />
                          <Typography variant="caption">{content.kullanici}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <CalendarToday fontSize="small" color="action" />
                          <Typography variant="caption">
                            {new Date(content.tarih).toLocaleDateString('tr-TR')}
                          </Typography>
                        </Box>
                      </Box>

                      {/* Reject Reason */}
                      {content.durum === 'reddedildi' && content.neden && (
                        <Box
                          sx={{
                            p: 1.5,
                            borderRadius: 2,
                            background: modernColors.gradients.error,
                            mb: 2,
                          }}
                        >
                          <Typography variant="caption" sx={{ color: 'white', fontWeight: 600 }}>
                            Red Nedeni: {content.neden}
                          </Typography>
                        </Box>
                      )}

                      {/* Actions */}
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <ModernButton
                          variant="glass"
                          icon={<Visibility />}
                          size="small"
                          fullWidth
                          onClick={() => handleView(content)}
                        >
                          Görüntüle
                        </ModernButton>
                        {content.durum === 'beklemede' && (
                          <>
                            <ModernButton
                              variant="gradient"
                              gradient={modernColors.gradients.success}
                              icon={<CheckCircle />}
                              size="small"
                              fullWidth
                              onClick={() => handleApprove(content.id)}
                            >
                              Onayla
                            </ModernButton>
                            <ModernButton
                              variant="gradient"
                              gradient={modernColors.gradients.error}
                              icon={<Cancel />}
                              size="small"
                              fullWidth
                              onClick={() => {
                                const reason = prompt('Red nedeni:');
                                if (reason) {handleReject(content.id, reason);}
                              }}
                            >
                              Reddet
                            </ModernButton>
                          </>
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
                      background: modernColors.gradients.fire,
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
                  <Typography variant="body1" color="text.secondary">
                    Seçilen kriterlere uygun içerik bulunmamaktadır
                  </Typography>
                </Box>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* View Dialog */}
        <Dialog
          open={viewDialogOpen}
          onClose={() => setViewDialogOpen(false)}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: {
              background: modernColors.glass.white.light,
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            },
          }}
        >
          {selectedContent && (
            <>
              <DialogTitle>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: getTypeGradient(selectedContent.tip),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    {getTypeIcon(selectedContent.tip)}
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    {selectedContent.baslik}
                  </Typography>
                </Box>
              </DialogTitle>
              <DialogContent>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Typography variant="body1">{selectedContent.aciklama}</Typography>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Yükleyen: {selectedContent.kullanici}
                    </Typography>
                    <br />
                    <Typography variant="caption" color="text.secondary">
                      Tarih: {new Date(selectedContent.tarih).toLocaleString('tr-TR')}
                    </Typography>
                  </Box>
                </Box>
              </DialogContent>
              <DialogActions>
                <ModernButton variant="glass" onClick={() => setViewDialogOpen(false)}>
                  Kapat
                </ModernButton>
              </DialogActions>
            </>
          )}
        </Dialog>
      </Container>
    </Box>
  );
}

export default ModernAdminContentPage;
