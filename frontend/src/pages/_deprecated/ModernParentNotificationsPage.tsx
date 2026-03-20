/**
 * Modern Parent Notifications Page - Glassmorphism Design
 * Veli bildirim merkezi
 */

import {
  Notifications,
  CheckCircle,
  Assignment,
  Message,
  EmojiEvents,
  School,
  MarkEmailRead,
  Delete,
  Star,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Chip,
  IconButton,
  Badge,
  Tabs,
  Tab,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import apiClient from '../services/apiClient';
import modernColors from '../theme/modern-colors';
import { useAuthStore } from '@/store/authStore';

interface Notification {
  id: string
  tip: 'sinav' | 'odev' | 'mesaj' | 'rozet' | 'duyuru'
  baslik: string
  mesaj: string
  tarih: string
  okundu: boolean
  oncelik: 'dusuk' | 'normal' | 'yuksek'
}

export function ModernParentNotificationsPage() {
  const { user: _user } = useAuthStore();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/parent/notifications');
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error('Bildirimler yüklenemedi:', error);
      // Mock data
      setNotifications([
        {
          id: '1',
          tip: 'sinav',
          baslik: 'TYT Deneme Sınavı Tamamlandı',
          mesaj: 'Çocuğunuz Ahmet TYT deneme sınavını başarıyla tamamladı. Genel başarı oranı: %85',
          tarih: '2025-11-21T10:30:00',
          okundu: false,
          oncelik: 'yuksek',
        },
        {
          id: '2',
          tip: 'odev',
          baslik: 'Matematik Ödevi Teslim Edildi',
          mesaj: 'Türev konusu ödev teslim edildi ve değerlendirme süreci başladı',
          tarih: '2025-11-20T14:20:00',
          okundu: true,
          oncelik: 'normal',
        },
        {
          id: '3',
          tip: 'mesaj',
          baslik: 'Matematik Öğretmeninden Mesaj',
          mesaj: 'Sayın Veli, çocuğunuz matematik dersinde çok başarılı. Tebrik ederim.',
          tarih: '2025-11-19T09:15:00',
          okundu: false,
          oncelik: 'yuksek',
        },
        {
          id: '4',
          tip: 'rozet',
          baslik: 'Yeni Rozet Kazanıldı',
          mesaj: '7 gün üst üste çalışma rozeti kazanıldı. Harika bir performans!',
          tarih: '2025-11-18T20:00:00',
          okundu: true,
          oncelik: 'normal',
        },
        {
          id: '5',
          tip: 'duyuru',
          baslik: 'Haftalık Performans Raporu Hazır',
          mesaj: 'Bu haftanın performans raporu görüntülenebilir',
          tarih: '2025-11-17T08:00:00',
          okundu: true,
          oncelik: 'dusuk',
        },
        {
          id: '6',
          tip: 'sinav',
          baslik: 'AYT Matematik Sınavı Yaklaşıyor',
          mesaj: 'Yarın saat 14:00\'te AYT Matematik sınavı başlayacak',
          tarih: '2025-11-16T16:45:00',
          okundu: false,
          oncelik: 'yuksek',
        },
        {
          id: '7',
          tip: 'mesaj',
          baslik: 'Fizik Öğretmeninden Mesaj',
          mesaj: 'Laboratuvar çalışması için ek materyal gerekiyor',
          tarih: '2025-11-15T11:30:00',
          okundu: true,
          oncelik: 'normal',
        },
        {
          id: '8',
          tip: 'rozet',
          baslik: '50 Soru Çözme Rozeti',
          mesaj: 'Bu hafta 50 soru çözme hedefini başardı',
          tarih: '2025-11-14T19:20:00',
          okundu: true,
          oncelik: 'dusuk',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getTypeGradient = (tip: string): string => {
    switch (tip) {
      case 'sinav':
        return modernColors.gradients.success;
      case 'odev':
        return modernColors.gradients.primary;
      case 'mesaj':
        return modernColors.gradients.ocean;
      case 'rozet':
        return modernColors.gradients.fire;
      case 'duyuru':
        return modernColors.gradients.warning;
      default:
        return modernColors.gradients.sunset;
    }
  };

  const getTypeIcon = (tip: string) => {
    switch (tip) {
      case 'sinav':
        return <CheckCircle sx={{ fontSize: 32 }} />;
      case 'odev':
        return <Assignment sx={{ fontSize: 32 }} />;
      case 'mesaj':
        return <Message sx={{ fontSize: 32 }} />;
      case 'rozet':
        return <EmojiEvents sx={{ fontSize: 32 }} />;
      case 'duyuru':
        return <School sx={{ fontSize: 32 }} />;
      default:
        return <Notifications sx={{ fontSize: 32 }} />;
    }
  };

  const getTypeLabel = (tip: string): string => {
    switch (tip) {
      case 'sinav':
        return 'Sınav';
      case 'odev':
        return 'Ödev';
      case 'mesaj':
        return 'Mesaj';
      case 'rozet':
        return 'Rozet';
      case 'duyuru':
        return 'Duyuru';
      default:
        return tip;
    }
  };

  const getPriorityColor = (oncelik: string): string => {
    switch (oncelik) {
      case 'yuksek':
        return modernColors.gradients.error;
      case 'normal':
        return modernColors.gradients.primary;
      case 'dusuk':
        return modernColors.gradients.ocean;
      default:
        return modernColors.gradients.sunset;
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      await apiClient.patch(`/api/v1/parent/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, okundu: true } : n)),
      );
    } catch (error) {
      console.error('Bildirim işaretlenemedi:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await apiClient.patch('/api/v1/parent/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, okundu: true })));
    } catch (error) {
      console.error('Tüm bildirimler işaretlenemedi:', error);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.delete(`/api/v1/parent/notifications/${id}`);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch (error) {
      console.error('Bildirim silinemedi:', error);
    }
  };

  const filteredNotifications =
    filterType === 'all'
      ? notifications
      : filterType === 'unread'
      ? notifications.filter((n) => !n.okundu)
      : notifications.filter((n) => n.tip === filterType);

  const unreadCount = notifications.filter((n) => !n.okundu).length;

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
        <ModernLoader message="Bildirimler yükleniyor..." size="large" />
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
      <Container maxWidth="md">
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
                <Badge badgeContent={unreadCount} color="error">
                  <Notifications sx={{ fontSize: 32, color: 'white' }} />
                </Badge>
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
                  Bildirimler
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Çocuğunuzun aktiviteleri hakkında güncel bildirimler
                </Typography>
              </Box>
              {unreadCount > 0 && (
                <ModernButton
                  variant="gradient"
                  gradient={modernColors.gradients.success}
                  icon={<MarkEmailRead />}
                  onClick={handleMarkAllAsRead}
                  size="small"
                >
                  Tümünü Okundu İşaretle
                </ModernButton>
              )}
            </Box>
          </Box>
        </motion.div>

        {/* Filter Tabs */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
            <Tabs
              value={filterType}
              onChange={(_, newValue) => setFilterType(newValue)}
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Notifications fontSize="small" />
                    Tümü ({notifications.length})
                  </Box>
                }
                value="all"
              />
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Badge badgeContent={unreadCount} color="error">
                      <Star fontSize="small" />
                    </Badge>
                    Okunmamış
                  </Box>
                }
                value="unread"
              />
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircle fontSize="small" />
                    Sınav
                  </Box>
                }
                value="sinav"
              />
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Assignment fontSize="small" />
                    Ödev
                  </Box>
                }
                value="odev"
              />
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Message fontSize="small" />
                    Mesaj
                  </Box>
                }
                value="mesaj"
              />
            </Tabs>
          </GlassCard>
        </motion.div>

        {/* Notifications */}
        <AnimatePresence mode="wait">
          {filteredNotifications.length > 0 ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {filteredNotifications.map((notification, index) => (
                <motion.div
                  key={notification.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                >
                  <GlassCard
                    glassIntensity={notification.okundu ? 'light' : 'medium'}
                    elevated
                    hoverable
                    gradient={notification.okundu ? undefined : getPriorityColor(notification.oncelik)}
                    sx={{
                      borderLeft: notification.okundu
                        ? 'none'
                        : `4px solid ${getPriorityColor(notification.oncelik)}`,
                    }}
                  >
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      {/* Icon */}
                      <Box
                        sx={{
                          width: 56,
                          height: 56,
                          borderRadius: 2,
                          background: getTypeGradient(notification.tip),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          flexShrink: 0,
                        }}
                      >
                        {getTypeIcon(notification.tip)}
                      </Box>

                      {/* Content */}
                      <Box sx={{ flex: 1 }}>
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'start',
                            mb: 1,
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                            <Typography
                              variant="h6"
                              sx={{
                                fontWeight: notification.okundu ? 500 : 700,
                              }}
                            >
                              {notification.baslik}
                            </Typography>
                            <Chip
                              label={getTypeLabel(notification.tip)}
                              size="small"
                              sx={{
                                background: getTypeGradient(notification.tip),
                                color: 'white',
                                fontWeight: 600,
                              }}
                            />
                            {!notification.okundu && (
                              <Chip
                                label="Yeni"
                                size="small"
                                color="error"
                                sx={{ fontWeight: 700 }}
                              />
                            )}
                          </Box>
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            {!notification.okundu && (
                              <IconButton
                                size="small"
                                onClick={() => handleMarkAsRead(notification.id)}
                                title="Okundu işaretle"
                              >
                                <MarkEmailRead fontSize="small" />
                              </IconButton>
                            )}
                            <IconButton
                              size="small"
                              onClick={() => handleDelete(notification.id)}
                              title="Sil"
                            >
                              <Delete fontSize="small" />
                            </IconButton>
                          </Box>
                        </Box>

                        <Typography variant="body2" color="text.primary" sx={{ mb: 1 }}>
                          {notification.mesaj}
                        </Typography>

                        <Typography variant="caption" color="text.secondary">
                          {new Date(notification.tarih).toLocaleString('tr-TR', {
                            day: 'numeric',
                            month: 'long',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </Typography>
                      </Box>
                    </Box>
                  </GlassCard>
                </motion.div>
              ))}
            </Box>
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
                      background: modernColors.gradients.sunset,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mx: 'auto',
                      mb: 3,
                    }}
                  >
                    <Notifications sx={{ fontSize: 64, color: 'white' }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                    Bildirim bulunamadı
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    {filterType === 'all'
                      ? 'Henüz bildiriminiz bulunmuyor'
                      : 'Bu kategoride bildirim bulunmuyor'}
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

export default ModernParentNotificationsPage;
