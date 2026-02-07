/**
 * Modern Profile Page - Glassmorphism Design
 * Kullanıcı profili ve bildirim ayarları
 */

import {
  Person,
  Edit,
  Save,
  Cancel,
  PhotoCamera,
  Security,
  Notifications,
  CheckCircle,
  Email,
  Phone,
  School,
  CalendarToday,
  AccessTime,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  Grid,
  TextField,
  Avatar,
  Alert,
  Divider,
  Switch,
  FormControlLabel,
  Chip,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import modernColors from '../theme/modern-colors';
import { User, UserRole } from '../types';
import { useAuthStore } from '@/store/authStore';

export function ModernProfilePage() {
  const { user, updateProfile } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState<Partial<User>>({
    ad: '',
    soyad: '',
    email: '',
    telefon: '',
    okul_id: '',
  });

  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    pushNotifications: true,
    weeklyReports: true,
    performanceAlerts: true,
  });

  useEffect(() => {
    if (user) {
      setFormData({
        ad: user.ad,
        soyad: user.soyad,
        email: user.email,
        telefon: user.telefon || '',
        okul_id: user.okul_id || '',
      });
    }
  }, [user]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    if (error) {setError(null);}
  };

  const handlePreferenceChange =
    (preference: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
      setPreferences((prev) => ({
        ...prev,
        [preference]: e.target.checked,
      }));
    };

  const handleSave = async () => {
    if (!formData.ad || !formData.soyad || !formData.email) {
      setError('Ad, soyad ve e-posta alanları zorunludur');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await updateProfile(formData);
      setSuccess('Profil başarıyla güncellendi');
      setIsEditing(false);
    } catch (error: any) {
      setError(error.message || 'Profil güncellenirken hata oluştu');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    if (user) {
      setFormData({
        ad: user.ad,
        soyad: user.soyad,
        email: user.email,
        telefon: user.telefon || '',
        okul_id: user.okul_id || '',
      });
    }
    setIsEditing(false);
    setError(null);
  };

  const getRoleDisplayName = (role: UserRole): string => {
    switch (role) {
      case 'ogrenci':
        return 'Öğrenci';
      case 'ogretmen':
        return 'Öğretmen';
      case 'veli':
        return 'Veli';
      case 'admin':
        return 'Admin';
      default:
        return 'Kullanıcı';
    }
  };

  const getRoleGradient = (role: UserRole): string => {
    switch (role) {
      case 'ogrenci':
        return modernColors.gradients.primary;
      case 'ogretmen':
        return modernColors.gradients.forest;
      case 'veli':
        return modernColors.gradients.sunset;
      case 'admin':
        return modernColors.gradients.fire;
      default:
        return modernColors.gradients.primary;
    }
  };

  const getInitials = (ad?: string, soyad?: string): string => {
    if (!ad || !soyad) {return 'U';}
    return `${ad.charAt(0)}${soyad.charAt(0)}`.toUpperCase();
  };

  if (!user) {
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
        <ModernLoader message="Profil yükleniyor..." size="large" />
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
                  background: getRoleGradient(user.rol),
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
                    background: getRoleGradient(user.rol),
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  Profil Ayarları
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Kişisel bilgilerinizi ve hesap ayarlarınızı yönetin
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            </motion.div>
          )}

          {success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <Alert severity="success" sx={{ mb: 3 }}>
                {success}
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        <Grid container spacing={3}>
          {/* Profile Avatar & Summary */}
          <Grid item xs={12} md={4}>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <GlassCard
                glassIntensity="medium"
                elevated
                gradient={getRoleGradient(user.rol)}
              >
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                    Profil Fotoğrafı
                  </Typography>

                  <Avatar
                    sx={{
                      width: 120,
                      height: 120,
                      mx: 'auto',
                      mb: 2,
                      background: getRoleGradient(user.rol),
                      fontSize: '2.5rem',
                      fontWeight: 800,
                    }}
                  >
                    {getInitials(user.ad, user.soyad)}
                  </Avatar>

                  <ModernButton
                    variant="glass"
                    icon={<PhotoCamera />}
                    size="small"
                    disabled
                    sx={{ mb: 1 }}
                  >
                    Fotoğraf Yükle
                  </ModernButton>
                  <Typography variant="caption" display="block" color="text.secondary">
                    Yakında eklenecek
                  </Typography>
                </Box>

                <Divider sx={{ my: 3 }} />

                <Box>
                  <Typography
                    variant="subtitle2"
                    sx={{ fontWeight: 700, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}
                  >
                    <CheckCircle fontSize="small" />
                    Hesap Bilgileri
                  </Typography>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CalendarToday fontSize="small" color="action" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Üyelik Tarihi
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {new Date(user.olusturma_tarihi).toLocaleDateString('tr-TR')}
                        </Typography>
                      </Box>
                    </Box>

                    {user.son_giris && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <AccessTime fontSize="small" color="action" />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Son Giriş
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {new Date(user.son_giris).toLocaleDateString('tr-TR')}
                          </Typography>
                        </Box>
                      </Box>
                    )}

                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Hesap Durumu
                      </Typography>
                      <Box sx={{ mt: 0.5 }}>
                        <Chip
                          label={user.aktif ? 'Aktif' : 'Pasif'}
                          size="small"
                          color={user.aktif ? 'success' : 'error'}
                          icon={<CheckCircle />}
                        />
                      </Box>
                    </Box>

                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Rol
                      </Typography>
                      <Box sx={{ mt: 0.5 }}>
                        <Chip
                          label={getRoleDisplayName(user.rol)}
                          size="small"
                          sx={{
                            background: getRoleGradient(user.rol),
                            color: 'white',
                            fontWeight: 600,
                          }}
                        />
                      </Box>
                    </Box>
                  </Box>
                </Box>
              </GlassCard>
            </motion.div>
          </Grid>

          {/* Personal Information Form */}
          <Grid item xs={12} md={8}>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <GlassCard glassIntensity="medium" elevated>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 3,
                  }}
                >
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Kişisel Bilgiler
                  </Typography>
                  {!isEditing ? (
                    <ModernButton
                      variant="gradient"
                      gradient={modernColors.gradients.primary}
                      icon={<Edit />}
                      onClick={() => setIsEditing(true)}
                    >
                      Düzenle
                    </ModernButton>
                  ) : (
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <ModernButton
                        variant="gradient"
                        gradient={modernColors.gradients.success}
                        icon={<Save />}
                        onClick={handleSave}
                        loading={isLoading}
                        glow
                      >
                        Kaydet
                      </ModernButton>
                      <ModernButton
                        variant="glass"
                        icon={<Cancel />}
                        onClick={handleCancel}
                        disabled={isLoading}
                      >
                        İptal
                      </ModernButton>
                    </Box>
                  )}
                </Box>

                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Ad"
                      name="ad"
                      value={formData.ad}
                      onChange={handleInputChange}
                      disabled={!isEditing || isLoading}
                      required
                      InputProps={{
                        startAdornment: <Person sx={{ mr: 1, color: 'action.active' }} />,
                      }}
                    />
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Soyad"
                      name="soyad"
                      value={formData.soyad}
                      onChange={handleInputChange}
                      disabled={!isEditing || isLoading}
                      required
                      InputProps={{
                        startAdornment: <Person sx={{ mr: 1, color: 'action.active' }} />,
                      }}
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="E-posta"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      disabled={!isEditing || isLoading}
                      required
                      InputProps={{
                        startAdornment: <Email sx={{ mr: 1, color: 'action.active' }} />,
                      }}
                    />
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Telefon"
                      name="telefon"
                      value={formData.telefon}
                      onChange={handleInputChange}
                      disabled={!isEditing || isLoading}
                      InputProps={{
                        startAdornment: <Phone sx={{ mr: 1, color: 'action.active' }} />,
                      }}
                    />
                  </Grid>

                  {(user.rol === 'ogrenci' || user.rol === 'ogretmen') && (
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Okul Kodu"
                        name="okul_id"
                        value={formData.okul_id}
                        onChange={handleInputChange}
                        disabled={!isEditing || isLoading}
                        InputProps={{
                          startAdornment: <School sx={{ mr: 1, color: 'action.active' }} />,
                        }}
                      />
                    </Grid>
                  )}
                </Grid>
              </GlassCard>
            </motion.div>
          </Grid>

          {/* Notification Settings */}
          <Grid item xs={12} md={6}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <GlassCard
                glassIntensity="medium"
                elevated
                gradient={modernColors.gradients.ocean}
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
                        checked={preferences.emailNotifications}
                        onChange={handlePreferenceChange('emailNotifications')}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          E-posta Bildirimleri
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Önemli güncellemeler için e-posta alın
                        </Typography>
                      </Box>
                    }
                  />

                  <Divider />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.pushNotifications}
                        onChange={handlePreferenceChange('pushNotifications')}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Push Bildirimleri
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Tarayıcı bildirimleri alın
                        </Typography>
                      </Box>
                    }
                  />

                  <Divider />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.weeklyReports}
                        onChange={handlePreferenceChange('weeklyReports')}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Haftalık Raporlar
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          İlerleme raporlarını e-posta ile alın
                        </Typography>
                      </Box>
                    }
                  />

                  <Divider />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.performanceAlerts}
                        onChange={handlePreferenceChange('performanceAlerts')}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Performans Uyarıları
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Başarı hedefleriniz için hatırlatıcılar
                        </Typography>
                      </Box>
                    }
                  />
                </Box>
              </GlassCard>
            </motion.div>
          </Grid>

          {/* Security Settings */}
          <Grid item xs={12} md={6}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <GlassCard
                glassIntensity="medium"
                elevated
                gradient={modernColors.gradients.fire}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                  <Security />
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Güvenlik
                  </Typography>
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <ModernButton
                      variant="glass"
                      fullWidth
                      disabled
                      sx={{ justifyContent: 'flex-start', py: 2 }}
                    >
                      <Box sx={{ textAlign: 'left', width: '100%' }}>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Şifre Değiştir
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Yakında eklenecek
                        </Typography>
                      </Box>
                    </ModernButton>
                  </Grid>

                  <Grid item xs={12}>
                    <ModernButton
                      variant="glass"
                      fullWidth
                      disabled
                      sx={{ justifyContent: 'flex-start', py: 2 }}
                    >
                      <Box sx={{ textAlign: 'left', width: '100%' }}>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          İki Faktörlü Doğrulama
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Yakında eklenecek
                        </Typography>
                      </Box>
                    </ModernButton>
                  </Grid>

                  <Grid item xs={12}>
                    <Alert severity="info" sx={{ mt: 1 }}>
                      <Typography variant="caption">
                        Güvenlik özelliklerimizi geliştiriyoruz
                      </Typography>
                    </Alert>
                  </Grid>
                </Grid>
              </GlassCard>
            </motion.div>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default ModernProfilePage;
