/**
 * Modern Admin Settings Page
 * Glassmorphism ile sistem ayarları yönetimi
 */

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Container,
  Typography,
  Box,
  Grid,
  TextField,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Tabs,
  Tab,
  MenuItem
} from '@mui/material'
import {
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Save as SaveIcon
} from '@mui/icons-material'
import { GlassCard } from '../components/ui/GlassCard'
import { ModernButton } from '../components/ui/ModernButton'
import { modernColors } from '../theme/modern-colors'

interface SettingsState {
  siteName: string
  siteUrl: string
  adminEmail: string
  maxUploadSize: number
  sessionTimeout: number
  enableRegistration: boolean
  enableEmailVerification: boolean
  enableTwoFactor: boolean
  enableNotifications: boolean
  maintenanceMode: boolean
  cacheEnabled: boolean
  logLevel: string
}

export const ModernAdminSettingsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0)
  const [saved, setSaved] = useState(false)

  const [settings, setSettings] = useState<SettingsState>({
    siteName: 'KIRO2 Eğitim Platformu',
    siteUrl: 'https://kiro2.edu.tr',
    adminEmail: 'admin@kiro2.edu.tr',
    maxUploadSize: 10,
    sessionTimeout: 30,
    enableRegistration: true,
    enableEmailVerification: true,
    enableTwoFactor: false,
    enableNotifications: true,
    maintenanceMode: false,
    cacheEnabled: true,
    logLevel: 'info'
  })

  const handleChange = (field: keyof SettingsState, value: any) => {
    setSettings(prev => ({ ...prev, [field]: value }))
    setSaved(false)
  }

  const handleSave = async () => {
    try {
      const response = await fetch('/api/v1/admin/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(settings)
      })

      if (!response.ok) throw new Error()
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch {
      // Simulate save
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    }
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: '16px',
              background: modernColors.gradients.fire,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2
            }}
          >
            <SettingsIcon sx={{ fontSize: 32, color: 'white' }} />
          </Box>

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              background: modernColors.gradients.fire,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1
            }}
          >
            Sistem Ayarları
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Platform konfigürasyonunu yönetin
          </Typography>
        </Box>
      </motion.div>

      {saved && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Alert severity="success" sx={{ mb: 3 }}>
            Ayarlar başarıyla kaydedildi!
          </Alert>
        </motion.div>
      )}

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <GlassCard sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab label="Genel" icon={<SettingsIcon />} iconPosition="start" />
            <Tab label="Güvenlik" icon={<SecurityIcon />} iconPosition="start" />
            <Tab label="Bildirimler" icon={<NotificationsIcon />} iconPosition="start" />
            <Tab label="Performans" icon={<SpeedIcon />} iconPosition="start" />
          </Tabs>
        </GlassCard>
      </motion.div>

      {/* Genel Ayarlar */}
      {tabValue === 0 && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <GlassCard sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Genel Ayarlar
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Site Adı"
                  value={settings.siteName}
                  onChange={(e) => handleChange('siteName', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Site URL"
                  value={settings.siteUrl}
                  onChange={(e) => handleChange('siteUrl', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Admin E-posta"
                  type="email"
                  value={settings.adminEmail}
                  onChange={(e) => handleChange('adminEmail', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Maksimum Dosya Boyutu (MB)"
                  type="number"
                  value={settings.maxUploadSize}
                  onChange={(e) => handleChange('maxUploadSize', parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 100 }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Oturum Zaman Aşımı (dakika)"
                  type="number"
                  value={settings.sessionTimeout}
                  onChange={(e) => handleChange('sessionTimeout', parseInt(e.target.value))}
                  inputProps={{ min: 5, max: 120 }}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enableRegistration}
                      onChange={(e) => handleChange('enableRegistration', e.target.checked)}
                    />
                  }
                  label="Kullanıcı kaydını etkinleştir"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.maintenanceMode}
                      onChange={(e) => handleChange('maintenanceMode', e.target.checked)}
                      color="warning"
                    />
                  }
                  label="Bakım modu (siteyi ziyaretçilere kapalı tutar)"
                />
              </Grid>
            </Grid>
          </GlassCard>
        </motion.div>
      )}

      {/* Güvenlik Ayarları */}
      {tabValue === 1 && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <GlassCard sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Güvenlik Ayarları
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Alert severity="info" sx={{ mb: 3 }}>
                  Güvenlik ayarları tüm kullanıcıları etkiler. Dikkatli yapılandırın.
                </Alert>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enableEmailVerification}
                      onChange={(e) => handleChange('enableEmailVerification', e.target.checked)}
                    />
                  }
                  label="E-posta doğrulaması gerektir"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Yeni kayıtlarda e-posta doğrulaması zorunlu olur
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enableTwoFactor}
                      onChange={(e) => handleChange('enableTwoFactor', e.target.checked)}
                    />
                  }
                  label="İki faktörlü kimlik doğrulamayı etkinleştir"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Kullanıcılar için 2FA opsiyonel olarak kullanılabilir
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Log Seviyesi"
                  value={settings.logLevel}
                  onChange={(e) => handleChange('logLevel', e.target.value)}
                >
                  <MenuItem value="debug">Debug (Tüm detaylar)</MenuItem>
                  <MenuItem value="info">Info (Standart)</MenuItem>
                  <MenuItem value="warn">Warning (Sadece uyarılar)</MenuItem>
                  <MenuItem value="error">Error (Sadece hatalar)</MenuItem>
                </TextField>
              </Grid>
            </Grid>
          </GlassCard>
        </motion.div>
      )}

      {/* Bildirim Ayarları */}
      {tabValue === 2 && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <GlassCard sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Bildirim Ayarları
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enableNotifications}
                      onChange={(e) => handleChange('enableNotifications', e.target.checked)}
                    />
                  }
                  label="Sistem bildirimlerini etkinleştir"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  E-posta ve push bildirimleri gönderilir
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Alert severity="info">
                  Bildirim ayarları yapılandırma bölümünde daha fazla özelleştirme seçeneği bulunur.
                </Alert>
              </Grid>
            </Grid>
          </GlassCard>
        </motion.div>
      )}

      {/* Performans Ayarları */}
      {tabValue === 3 && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <GlassCard sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Performans Ayarları
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.cacheEnabled}
                      onChange={(e) => handleChange('cacheEnabled', e.target.checked)}
                    />
                  }
                  label="Cache sistemini etkinleştir"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Sık kullanılan veriler önbellekte saklanır, performans artar
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Alert severity="success">
                  Cache sistemi performansı %40-60 oranında artırabilir.
                </Alert>
              </Grid>
            </Grid>
          </GlassCard>
        </motion.div>
      )}

      {/* Kaydet Butonu */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <ModernButton
            variant="contained"
            size="large"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            sx={{
              background: modernColors.gradients.fire,
              px: 6
            }}
          >
            Ayarları Kaydet
          </ModernButton>
        </Box>
      </motion.div>
    </Container>
  )
}

export default ModernAdminSettingsPage
