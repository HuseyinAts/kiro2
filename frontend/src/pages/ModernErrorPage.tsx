/**
 * Modern Error Page - Glassmorphism Design
 * Genel hata sayfası
 */

import { ErrorOutline, Home, Refresh, BugReport, ArrowBack } from '@mui/icons-material';
import { Container, Typography, Box, Chip, Alert } from '@mui/material';
import { motion } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import modernColors from '../theme/modern-colors';
import { UserRole } from '../types';
import { useAuthStore } from '@/store/authStore';

interface ErrorPageProps {
  errorCode?: string
  errorMessage?: string
  errorDetails?: string
}

export function ModernErrorPage({
  errorCode = '500',
  errorMessage = 'Bir Hata Oluştu',
  errorDetails,
}: ErrorPageProps) {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  // Get error info from location state if available
  const state = location.state as any;
  const finalErrorCode = state?.errorCode || errorCode;
  const finalErrorMessage = state?.errorMessage || errorMessage;
  const finalErrorDetails = state?.errorDetails || errorDetails;

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

  const handleRefresh = () => {
    window.location.reload();
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleReportBug = () => {
    // In production, this could open a bug report form or redirect to support
    const subject = `Hata Raporu - ${finalErrorCode}`;
    const body = `
Hata Kodu: ${finalErrorCode}
Hata Mesajı: ${finalErrorMessage}
Sayfa: ${window.location.href}
Zaman: ${new Date().toISOString()}

Detaylar:
${finalErrorDetails || 'Detay yok'}
    `;
    window.open(
      `mailto:destek@egitimeylemci.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`,
    );
  };

  const getErrorGradient = (code: string) => {
    if (code.startsWith('4')) {return modernColors.gradients.warning;}
    if (code.startsWith('5')) {return modernColors.gradients.error;}
    return modernColors.gradients.sunset;
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
                    background: getErrorGradient(finalErrorCode),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 3,
                  }}
                >
                  <ErrorOutline sx={{ fontSize: 80, color: 'white' }} />
                </Box>
              </motion.div>

              {/* Error Code Badge */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <Chip
                  label={`Hata Kodu: ${finalErrorCode}`}
                  color="error"
                  sx={{
                    mb: 2,
                    fontWeight: 700,
                    fontSize: 16,
                    height: 36,
                  }}
                />
              </motion.div>

              {/* Error Message */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
              >
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
                  {finalErrorMessage}
                </Typography>
              </motion.div>

              {/* Description */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                  Üzgünüz, bir şeyler ters gitti. Lütfen sayfayı yenilemeyi deneyin veya ana
                  sayfaya dönün.
                </Typography>
              </motion.div>

              {/* Error Details */}
              {finalErrorDetails && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.6 }}
                >
                  <Alert severity="error" sx={{ mb: 4, textAlign: 'left' }}>
                    <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                      Hata Detayları:
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: 12 }}>
                      {finalErrorDetails}
                    </Typography>
                  </Alert>
                </motion.div>
              )}

              {/* Action Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.7 }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    gap: 2,
                    justifyContent: 'center',
                    flexWrap: 'wrap',
                    mb: 3,
                  }}
                >
                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.primary}
                    icon={<Home />}
                    onClick={handleGoHome}
                    glow
                  >
                    Ana Sayfa
                  </ModernButton>

                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.success}
                    icon={<Refresh />}
                    onClick={handleRefresh}
                  >
                    Yenile
                  </ModernButton>

                  <ModernButton variant="glass" icon={<ArrowBack />} onClick={handleGoBack}>
                    Geri Dön
                  </ModernButton>
                </Box>
              </motion.div>
            </Box>

            {/* Troubleshooting Tips */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.8 }}
            >
              <GlassCard
                glassIntensity="light"
                gradient={modernColors.gradients.ocean}
                sx={{ mb: 3 }}
              >
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                  Ne yapabilirim?
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
                  <li>Sayfayı yenilemeyi deneyin</li>
                  <li>İnternet bağlantınızı kontrol edin</li>
                  <li>Tarayıcı önbelleğinizi temizleyin</li>
                  <li>
                    Sorun devam ederse, destek ekibimizle iletişime geçin veya hata raporu gönderin
                  </li>
                </Box>
              </GlassCard>
            </motion.div>

            {/* Bug Report Button */}
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
                    justifyContent: 'space-between',
                    gap: 2,
                    flexWrap: 'wrap',
                  }}
                >
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                      Bu hatayı bildirin
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Destek ekibimize otomatik hata raporu gönderin
                    </Typography>
                  </Box>
                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.warning}
                    icon={<BugReport />}
                    onClick={handleReportBug}
                    size="small"
                  >
                    Hata Bildir
                  </ModernButton>
                </Box>
              </GlassCard>
            </motion.div>
          </GlassCard>
        </motion.div>
      </Container>
    </Box>
  );
}

export default ModernErrorPage;
