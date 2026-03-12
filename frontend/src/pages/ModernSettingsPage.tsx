/**
 * Modern Settings Page - Glassmorphism Design
 * Uygulama ayarları ve tercihleri
 */

import {
  Settings,
  Notifications,
  Security,
  Palette,
  Language,
  Storage,
  Backup,
  Download,
  Delete,
  Info,
  Public,
  Speed,
  Cloud,
  AnimationOutlined,
  Accessibility as AccessibilityIcon,
  FormatSize as FontSizeIcon,
  FormatLineSpacing as LineSpacingIcon,
  Contrast as ContrastIcon,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Chip,
  Slider,
} from '@mui/material';
import { motion } from 'framer-motion';
import { useState } from 'react';

import { RoleBasedComponent } from '../components/Common/RoleBasedComponent';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { useSettingsStore } from '../store/settingsStore';
import modernColors from '../theme/modern-colors';
import { useAuthStore } from '@/store/authStore';

export function ModernSettingsPage() {
  const { user: _user } = useAuthStore();
  const reduceMotion = useReducedMotion();
  const toggleReduceMotion = useSettingsStore((s) => s.toggleReduceMotion);
  const fontSize = useSettingsStore((s) => s.accessibility.fontSize);
  const setFontSize = useSettingsStore((s) => s.setFontSize);
  const lineHeight = useSettingsStore((s) => s.accessibility.lineHeight);
  const setLineHeight = useSettingsStore((s) => s.setLineHeight);
  const highContrast = useSettingsStore((s) => s.accessibility.highContrast);
  const toggleHighContrast = useSettingsStore((s) => s.toggleHighContrast);

  const [settings, setSettings] = useState({
    // Genel Ayarlar
    darkMode: false,
    language: 'tr',
    autoSave: true,

    // Bildirim Ayarları
    emailNotifications: true,
    pushNotifications: true,
    soundNotifications: false,
    weeklyReports: true,
    performanceAlerts: true,

    // Gizlilik Ayarları
    profileVisibility: 'private',
    shareProgress: false,
    analyticsOptIn: true,

    // Performans Ayarları
    autoSync: true,
    offlineMode: false,
    dataCompression: true,
  });

  const handleSettingChange =
    (setting: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
      setSettings((prev) => ({
        ...prev,
        [setting]: event.target.checked,
      }));
    };

  const handleExportData = async () => {
    try {
      const response = await fetch('/api/v1/user/export-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `kiro_verilerim_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      alert('Verileriniz başarıyla dışa aktarıldı');
    } catch (error: any) {
      console.error('Veri dışa aktarma hatası:', error);
      alert('Veri dışa aktarılırken hata oluştu: ' + error.message);
    }
  };

  const handleClearCache = async () => {
    try {
      localStorage.removeItem('api_cache');
      sessionStorage.clear();

      const response = await fetch('/api/v1/user/clear-cache', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      alert('Önbellek başarıyla temizlendi');
    } catch (error: any) {
      console.error('Önbellek temizleme hatası:', error);
      alert('Tarayıcı önbelleği temizlendi');
    }
  };

  const handleDeleteAccount = async () => {
    if (
      !window.confirm(
        'Hesabınızı silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.',
      )
    ) {
      return;
    }

    if (
      !window.confirm(
        'SON UYARI: Tüm verileriniz kalıcı olarak silinecektir. Devam etmek istiyor musunuz?',
      )
    ) {
      return;
    }

    try {
      const response = await fetch('/api/v1/user/delete-account', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult = await response.json();

      if (!apiResult.success) {
        throw new Error(apiResult.message || 'Hesap silinemedi');
      }

      localStorage.clear();
      sessionStorage.clear();

      alert('Hesabınız başarıyla silindi. Giriş sayfasına yönlendiriliyorsunuz.');

      window.location.href = '/login';
    } catch (error: any) {
      console.error('Hesap silme hatası:', error);
      alert('Hesap silinirken hata oluştu: ' + error.message);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

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
                  background: modernColors.gradients.ocean,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Settings sx={{ fontSize: 32, color: 'white' }} />
              </Box>
              <Box>
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 900,
                    background: modernColors.gradients.ocean,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  Ayarlar
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Uygulama ayarlarınızı ve tercihlerinizi yönetin
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>

        <motion.div variants={containerVariants} initial="hidden" animate="visible">
          <Grid container spacing={3}>
            {/* Genel Ayarlar */}
            <Grid item xs={12} md={6}>
              <motion.div variants={itemVariants}>
                <GlassCard
                  glassIntensity="medium"
                  elevated
                  gradient={modernColors.gradients.primary}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <Settings />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Genel Ayarlar
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                          <Palette fontSize="small" color="action" />
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              Koyu Tema
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Gözlerinizi korumak için koyu tema
                            </Typography>
                          </Box>
                        </Box>
                        <Switch
                          checked={settings.darkMode}
                          onChange={handleSettingChange('darkMode')}
                          disabled
                        />
                      </Box>
                      <Chip
                        label="Yakında"
                        size="small"
                        color="warning"
                        sx={{ mt: 1, ml: 4 }}
                      />
                    </Box>

                    <Divider />

                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Language fontSize="small" color="action" />
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Dil
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Uygulama dili
                          </Typography>
                        </Box>
                      </Box>
                      <Chip label="Türkçe" size="small" color="primary" />
                    </Box>

                    <Divider />

                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Backup fontSize="small" color="action" />
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Otomatik Kaydetme
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Çalışmalarınızı otomatik kaydet
                          </Typography>
                        </Box>
                      </Box>
                      <Switch
                        checked={settings.autoSave}
                        onChange={handleSettingChange('autoSave')}
                      />
                    </Box>

                    <Divider />

                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <AnimationOutlined fontSize="small" color="action" />
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Animasyonları Azalt
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Sayfa geçişlerini ve efektleri kapat
                          </Typography>
                        </Box>
                      </Box>
                      <Switch
                        checked={reduceMotion}
                        onChange={toggleReduceMotion}
                      />
                    </Box>
                  </Box>
                </GlassCard>
              </motion.div>
            </Grid>

            {/* Bildirim Ayarları */}
            <Grid item xs={12} md={6}>
              <motion.div variants={itemVariants}>
                <GlassCard
                  glassIntensity="medium"
                  elevated
                  gradient={modernColors.gradients.sunset}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <Notifications />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Bildirim Ayarları
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.emailNotifications}
                          onChange={handleSettingChange('emailNotifications')}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            E-posta Bildirimleri
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Önemli güncellemeler için e-posta
                          </Typography>
                        </Box>
                      }
                    />

                    <Divider />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.pushNotifications}
                          onChange={handleSettingChange('pushNotifications')}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Push Bildirimleri
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Tarayıcı bildirimleri
                          </Typography>
                        </Box>
                      }
                    />

                    <Divider />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.soundNotifications}
                          onChange={handleSettingChange('soundNotifications')}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Ses Bildirimleri
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Bildirimler için ses çal
                          </Typography>
                        </Box>
                      }
                    />

                    <Divider />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.weeklyReports}
                          onChange={handleSettingChange('weeklyReports')}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Haftalık Raporlar
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            İlerleme raporlarını e-posta ile al
                          </Typography>
                        </Box>
                      }
                    />
                  </Box>
                </GlassCard>
              </motion.div>
            </Grid>

            {/* Gizlilik ve Güvenlik */}
            <Grid item xs={12} md={6}>
              <motion.div variants={itemVariants}>
                <GlassCard
                  glassIntensity="medium"
                  elevated
                  gradient={modernColors.gradients.forest}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <Security />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Gizlilik ve Güvenlik
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Public fontSize="small" color="action" />
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Profil Görünürlüğü
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Diğer kullanıcılara görünürlük
                          </Typography>
                        </Box>
                      </Box>
                      <Chip label="Özel" size="small" color="success" />
                    </Box>

                    <Divider />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.shareProgress}
                          onChange={handleSettingChange('shareProgress')}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            İlerleme Paylaşımı
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            İlerlemenizi diğerleriyle paylaş
                          </Typography>
                        </Box>
                      }
                    />

                    <Divider />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.analyticsOptIn}
                          onChange={handleSettingChange('analyticsOptIn')}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Analitik Verileri
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Anonim veri paylaşımı
                          </Typography>
                        </Box>
                      }
                    />
                  </Box>
                </GlassCard>
              </motion.div>
            </Grid>

            {/* Performans Ayarları */}
            <Grid item xs={12} md={6}>
              <motion.div variants={itemVariants}>
                <GlassCard
                  glassIntensity="medium"
                  elevated
                  gradient={modernColors.gradients.warning}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <Speed />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Performans Ayarları
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.autoSync}
                          onChange={handleSettingChange('autoSync')}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Otomatik Senkronizasyon
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Verileri otomatik senkronize et
                          </Typography>
                        </Box>
                      }
                    />

                    <Divider />

                    <Box>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={settings.offlineMode}
                            onChange={handleSettingChange('offlineMode')}
                            disabled
                          />
                        }
                        label={
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              Çevrimdışı Mod
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              İnternet olmadan çalış
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip
                        label="Yakında"
                        size="small"
                        color="warning"
                        sx={{ ml: 5 }}
                      />
                    </Box>

                    <Divider />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.dataCompression}
                          onChange={handleSettingChange('dataCompression')}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Veri Sıkıştırma
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Daha az veri kullanımı
                          </Typography>
                        </Box>
                      }
                    />
                  </Box>
                </GlassCard>
              </motion.div>
            </Grid>

            {/* Erişilebilirlik Ayarları */}
            <Grid item xs={12} md={6}>
              <motion.div variants={itemVariants}>
                <GlassCard
                  glassIntensity="medium"
                  elevated
                  gradient={modernColors.gradients.success}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <AccessibilityIcon />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Erişilebilirlik
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                    {/* Yazı Boyutu */}
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                        <FontSizeIcon fontSize="small" color="action" />
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Yazı Boyutu
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {fontSize}px
                          </Typography>
                        </Box>
                      </Box>
                      <Box sx={{ px: 1 }}>
                        <Slider
                          value={fontSize}
                          onChange={(_e, val) => setFontSize(val as number)}
                          min={12}
                          max={24}
                          step={1}
                          marks={[
                            { value: 12, label: '12' },
                            { value: 16, label: '16' },
                            { value: 20, label: '20' },
                            { value: 24, label: '24' },
                          ]}
                          size="small"
                        />
                      </Box>
                    </Box>

                    <Divider />

                    {/* Satır Aralığı */}
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                        <LineSpacingIcon fontSize="small" color="action" />
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Satır Aralığı
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {lineHeight.toFixed(1)}x
                          </Typography>
                        </Box>
                      </Box>
                      <Box sx={{ px: 1 }}>
                        <Slider
                          value={lineHeight}
                          onChange={(_e, val) => setLineHeight(val as number)}
                          min={1.0}
                          max={2.0}
                          step={0.1}
                          marks={[
                            { value: 1.0, label: '1.0' },
                            { value: 1.5, label: '1.5' },
                            { value: 2.0, label: '2.0' },
                          ]}
                          size="small"
                        />
                      </Box>
                    </Box>

                    <Divider />

                    {/* Yüksek Kontrast */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <ContrastIcon fontSize="small" color="action" />
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Yüksek Kontrast
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Metin ve arka plan kontrastını artır
                          </Typography>
                        </Box>
                      </Box>
                      <Switch
                        checked={highContrast}
                        onChange={toggleHighContrast}
                      />
                    </Box>
                  </Box>
                </GlassCard>
              </motion.div>
            </Grid>

            {/* Veri Yönetimi */}
            <Grid item xs={12}>
              <motion.div variants={itemVariants}>
                <GlassCard
                  glassIntensity="medium"
                  elevated
                  gradient={modernColors.gradients.ocean}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <Cloud />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Veri Yönetimi
                    </Typography>
                  </Box>

                  <Alert severity="info" sx={{ mb: 3 }}>
                    <Typography variant="body2">
                      Verilerinizi yönetmek ve hesabınızı kontrol etmek için aşağıdaki
                      seçenekleri kullanabilirsiniz.
                    </Typography>
                  </Alert>

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <ModernButton
                        variant="gradient"
                        gradient={modernColors.gradients.primary}
                        icon={<Download />}
                        onClick={handleExportData}
                        fullWidth
                        glow
                      >
                        Verileri Dışa Aktar
                      </ModernButton>
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                      <ModernButton
                        variant="gradient"
                        gradient={modernColors.gradients.ocean}
                        icon={<Storage />}
                        onClick={handleClearCache}
                        fullWidth
                        glow
                      >
                        Önbelleği Temizle
                      </ModernButton>
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                      <ModernButton
                        variant="glass"
                        icon={<Backup />}
                        disabled
                        fullWidth
                      >
                        Yedek Oluştur
                      </ModernButton>
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                      <ModernButton
                        variant="gradient"
                        gradient={modernColors.gradients.error}
                        icon={<Delete />}
                        onClick={handleDeleteAccount}
                        fullWidth
                      >
                        Hesabı Sil
                      </ModernButton>
                    </Grid>
                  </Grid>
                </GlassCard>
              </motion.div>
            </Grid>

            {/* Admin Ayarları */}
            <RoleBasedComponent allowedRoles={['admin']}>
              <Grid item xs={12}>
                <motion.div variants={itemVariants}>
                  <GlassCard
                    glassIntensity="medium"
                    elevated
                    gradient={modernColors.gradients.fire}
                  >
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                      Admin Ayarları
                    </Typography>

                    <Alert severity="warning" sx={{ mb: 3 }}>
                      Bu ayarlar sadece sistem yöneticileri tarafından görülebilir ve
                      değiştirilebilir.
                    </Alert>

                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6} md={3}>
                        <ModernButton variant="glass" fullWidth disabled>
                          Sistem Bakımı
                        </ModernButton>
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <ModernButton variant="glass" fullWidth disabled>
                          Log Görüntüle
                        </ModernButton>
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <ModernButton variant="glass" fullWidth disabled>
                          Sistem İstatistikleri
                        </ModernButton>
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <ModernButton variant="glass" fullWidth disabled>
                          Güvenlik Ayarları
                        </ModernButton>
                      </Grid>
                    </Grid>
                  </GlassCard>
                </motion.div>
              </Grid>
            </RoleBasedComponent>

            {/* Uygulama Bilgileri */}
            <Grid item xs={12}>
              <motion.div variants={itemVariants}>
                <GlassCard glassIntensity="light" elevated>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <Info />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Uygulama Bilgileri
                    </Typography>
                  </Box>

                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Typography variant="body2">
                          <strong>Sürüm:</strong> 1.0.0
                        </Typography>
                        <Typography variant="body2">
                          <strong>Son Güncelleme:</strong> 15 Ocak 2024
                        </Typography>
                        <Typography variant="body2">
                          <strong>Geliştirici:</strong> EğitimEylemci Ekibi
                        </Typography>
                      </Box>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Typography variant="body2">
                          <strong>Destek:</strong> destek@egitimeylemci.com
                        </Typography>
                        <Typography variant="body2">
                          Gizlilik Politikası | Kullanım Şartları
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          © 2024 EğitimEylemci. Tüm hakları saklıdır.
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </GlassCard>
              </motion.div>
            </Grid>
          </Grid>
        </motion.div>
      </Container>
    </Box>
  );
}

export default ModernSettingsPage;
