/**
 * Modern 404 Page - Glassmorphism Design
 * Sayfa bulunamadı
 */

import {
  SearchOff,
  Home,
  ArrowBack,
  School,
  MenuBook,
  Quiz,
  Help,
} from '@mui/icons-material';
import { Container, Typography, Box, Grid } from '@mui/material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import modernColors from '../theme/modern-colors';
import { UserRole } from '../types';
import { useAuthStore } from '@/store/authStore';

export function Modern404Page() {
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

  // Suggested pages based on role
  const getSuggestedPages = () => {
    if (!user) {
      return [
        { label: 'Giriş Yap', path: '/login', icon: <Home /> },
        { label: 'Kayıt Ol', path: '/register', icon: <School /> },
      ];
    }

    const commonPages = [
      { label: 'Ana Sayfa', path: getDefaultDashboard(user.rol), icon: <Home /> },
      { label: 'Profil', path: '/profile', icon: <School /> },
    ];

    if (user.rol === 'ogrenci') {
      return [
        ...commonPages,
        { label: 'Sınav Başlat', path: '/exam/start', icon: <Quiz /> },
        { label: 'Öğrenme Yolu', path: '/learning-path', icon: <MenuBook /> },
      ];
    }

    return commonPages;
  };

  const suggestedPages = getSuggestedPages();

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
                  <SearchOff sx={{ fontSize: 80, color: 'white' }} />
                </Box>
              </motion.div>

              {/* Error Code */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <Typography
                  variant="h1"
                  sx={{
                    fontWeight: 900,
                    fontSize: { xs: '5rem', md: '8rem' },
                    background: modernColors.gradients.error,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    mb: 2,
                  }}
                >
                  404
                </Typography>
              </motion.div>

              {/* Title */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
              >
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
                  Sayfa Bulunamadı
                </Typography>
              </motion.div>

              {/* Description */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                  Aradığınız sayfa mevcut değil veya taşınmış olabilir.
                  <br />
                  Ana sayfaya dönebilir veya aşağıdaki önerilen sayfalara göz atabilirsiniz.
                </Typography>
              </motion.div>

              {/* Action Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
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

            {/* Suggested Pages */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.7 }}
            >
              <Box sx={{ mb: 3 }}>
                <Typography
                  variant="h6"
                  sx={{ fontWeight: 700, mb: 2, textAlign: 'center' }}
                >
                  Önerilen Sayfalar
                </Typography>

                <Grid container spacing={2}>
                  {suggestedPages.map((page, index) => (
                    <Grid item xs={12} sm={6} key={page.path}>
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: 0.8 + index * 0.1 }}
                      >
                        <GlassCard
                          glassIntensity="light"
                          hoverable
                          role="button"
                          aria-label={`${page.label} sayfasına git`}
                          tabIndex={0}
                          onClick={() => navigate(page.path)}
                          onKeyDown={(e: React.KeyboardEvent) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              navigate(page.path);
                            }
                          }}
                          sx={{
                            cursor: 'pointer',
                            '&:focus': {
                              outline: '2px solid rgba(59, 130, 246, 0.5)',
                              outlineOffset: '2px',
                            },
                          }}
                        >
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 2,
                              py: 1,
                            }}
                          >
                            <Box
                              sx={{
                                width: 40,
                                height: 40,
                                borderRadius: 2,
                                background: modernColors.gradients.primary,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                              }}
                            >
                              {page.icon}
                            </Box>
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              {page.label}
                            </Typography>
                          </Box>
                        </GlassCard>
                      </motion.div>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </motion.div>

            {/* Help Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.9 }}
            >
              <GlassCard glassIntensity="light" gradient={modernColors.gradients.ocean}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    textAlign: 'left',
                  }}
                >
                  <Help sx={{ fontSize: 32, color: 'primary.main' }} />
                  <Box>
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

export default Modern404Page;
