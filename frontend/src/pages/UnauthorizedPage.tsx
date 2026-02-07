/**
 * Unauthorized Page - Modern Tasarım
 * Glassmorphism ile yetkilendirme hatası
 */

import {
  Lock,
  Home,
  ArrowBack,
  Shield,
  Person,
  Email,
  AdminPanelSettings,
  ContactSupport,
} from '@mui/icons-material';
import { Container, Typography, Box, Chip, Grid } from '@mui/material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import modernColors from '../theme/modern-colors';
import { UserRole } from '../types';
import { useAuthStore } from '@/store/authStore';

function getRoleDisplayName(role: UserRole): string {
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
}

function getRoleIcon(role?: UserRole) {
  switch (role) {
    case 'ogrenci':
      return <Person />;
    case 'ogretmen':
      return <Shield />;
    case 'veli':
      return <Shield />;
    case 'admin':
      return <AdminPanelSettings />;
    default:
      return <Person />;
  }
}

export function UnauthorizedPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const getDefaultDashboard = (role?: UserRole): string => {
    switch (role) {
      case 'ogrenci':
        return '/dashboard';
      case 'ogretmen':
        return '/teacher/dashboard';
      case 'veli':
        return '/parent/dashboard';
      case 'admin':
        return '/admin/dashboard';
      default:
        return '/login';
    }
  };

  const handleGoHome = () => {
    const defaultPath = getDefaultDashboard(user?.rol);
    navigate(defaultPath);
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: modernColors.gradients.mesh,
        py: 4,
      }}
    >
      <Container maxWidth="md">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <GlassCard glassIntensity="medium" elevated>
            {/* Main Content */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              {/* Animated Icon */}
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <Box
                  sx={{
                    width: 140,
                    height: 140,
                    borderRadius: '50%',
                    background: modernColors.gradients.error,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 3,
                  }}
                >
                  <Lock sx={{ fontSize: 80, color: 'white' }} />
                </Box>
              </motion.div>

              {/* Error Code */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <Chip
                  label="403 - Forbidden"
                  color="error"
                  sx={{
                    mb: 2,
                    fontWeight: 700,
                    fontSize: 16,
                    height: 36,
                  }}
                />
              </motion.div>

              {/* Title */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
              >
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
                  Erişim Engellendi
                </Typography>
              </motion.div>

              {/* Description */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                  Bu sayfaya erişim yetkiniz bulunmamaktadır.
                  <br />
                  Eğer bu sayfaya erişmeniz gerektiğini düşünüyorsanız, sistem yöneticinizle
                  iletişime geçin.
                </Typography>
              </motion.div>

              {/* User Info Card */}
              {user && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.6 }}
                >
                  <GlassCard
                    glassIntensity="light"
                    gradient={modernColors.gradients.ocean}
                    sx={{ mb: 4 }}
                  >
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 2 }}>
                      Mevcut Kullanıcı Bilgileri
                    </Typography>

                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={4}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Person fontSize="small" color="action" />
                          <Box sx={{ textAlign: 'left' }}>
                            <Typography variant="caption" color="text.secondary">
                              İsim
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {user.ad} {user.soyad}
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>

                      <Grid item xs={12} sm={4}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getRoleIcon(user.rol)}
                          <Box sx={{ textAlign: 'left' }}>
                            <Typography variant="caption" color="text.secondary">
                              Rol
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {getRoleDisplayName(user.rol)}
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>

                      <Grid item xs={12} sm={4}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Email fontSize="small" color="action" />
                          <Box sx={{ textAlign: 'left' }}>
                            <Typography variant="caption" color="text.secondary">
                              E-posta
                            </Typography>
                            <Typography
                              variant="body2"
                              sx={{
                                fontWeight: 600,
                                fontSize: '0.75rem',
                                wordBreak: 'break-all',
                              }}
                            >
                              {user.email}
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                    </Grid>
                  </GlassCard>
                </motion.div>
              )}

              {/* Action Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.7 }}
              >
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mb: 4 }}>
                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.primary}
                    icon={<Home />}
                    onClick={handleGoHome}
                    glow
                  >
                    Ana Sayfaya Dön
                  </ModernButton>

                  <ModernButton
                    variant="glass"
                    icon={<ArrowBack />}
                    onClick={handleGoBack}
                  >
                    Geri Dön
                  </ModernButton>
                </Box>
              </motion.div>
            </Box>

            {/* Information Box */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.8 }}
            >
              <GlassCard
                glassIntensity="light"
                gradient={modernColors.gradients.warning}
                sx={{ mb: 3 }}
              >
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                  Neden bu sayfayı göremiyorum?
                </Typography>
                <Box
                  component="ul"
                  sx={{
                    pl: 2,
                    m: 0,
                    '& li': {
                      mb: 1,
                      color: 'text.secondary',
                    },
                  }}
                >
                  <li>Bu sayfa sadece belirli kullanıcı rolleri için erişilebilir</li>
                  <li>Hesabınızın yetkileri bu içeriği görüntülemek için yeterli olmayabilir</li>
                  <li>Oturum süreniz dolmuş olabilir - tekrar giriş yapmayı deneyin</li>
                  <li>
                    Yetki değişikliği gerekiyorsa, sistem yöneticinizle iletişime geçin
                  </li>
                </Box>
              </GlassCard>
            </motion.div>

            {/* Help Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.9 }}
            >
              <GlassCard glassIntensity="light">
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                  }}
                >
                  <ContactSupport sx={{ fontSize: 32, color: 'primary.main' }} />
                  <Box sx={{ textAlign: 'left' }}>
                    <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                      Yardıma mı ihtiyacınız var?
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Destek için: <strong>destek@egitimeylemci.com</strong>
                    </Typography>
                  </Box>
                </Box>
              </GlassCard>
            </motion.div>
          </GlassCard>
        </motion.div>
      </Container>
    </Box>
  );
}

export default UnauthorizedPage;
