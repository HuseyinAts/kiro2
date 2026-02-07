/**
 * Modern Login Page - Glassmorphism Design
 * Beautiful, professional login experience
 */

import {
  School,
  ArrowForward,
  Person,
  SchoolOutlined,
  SupervisorAccount,
  AdminPanelSettings,
} from '@mui/icons-material';
import {
  Container,
  TextField,
  Typography,
  Box,
  Alert,
  Divider,
  Grid,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';

import { LoginRequest, UserRole } from '../types';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { useAuthStore } from '@/store/authStore';
import modernColors from '@/theme/modern-colors';

export const ModernLoginPage: React.FC = () => {
  const [formData, setFormData] = useState<LoginRequest>({
    email: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { login, isAuthenticated, user } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      const from = location.state?.from?.pathname || getDefaultDashboard(user.rol);
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, user, navigate, location]);

  const getDefaultDashboard = (role: UserRole): string => {
    const dashboards = {
      ogrenci: '/dashboard',
      ogretmen: '/teacher/dashboard',
      veli: '/parent/dashboard',
      admin: '/admin/dashboard',
    };
    return dashboards[role] || '/dashboard';
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (error) {setError(null);}
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.email || !formData.password) {
      setError('Lütfen tüm alanları doldurun');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const success = await login(formData);
      if (!success) {
        setError('E-posta veya şifre hatalı');
      }
    } catch (error: any) {
      setError(error.message || 'Giriş sırasında bir hata oluştu');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (role: UserRole) => {
    const demoCredentials = {
      ogrenci: { email: 'ogrenci@demo.com', password: 'demo123' },
      ogretmen: { email: 'ogretmen@demo.com', password: 'demo123' },
      veli: { email: 'veli@demo.com', password: 'demo123' },
      admin: { email: 'admin@demo.com', password: 'demo123' },
    };

    setFormData(demoCredentials[role]);
    setIsLoading(true);

    try {
      await login(demoCredentials[role]);
    } catch (error: any) {
      setError(error.message || 'Demo giriş başarısız');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: modernColors.gradients.primary,
        position: 'relative',
        overflow: 'hidden',
        p: 2,
      }}
    >
      {/* Animated Background Shapes */}
      <motion.div
        style={{
          position: 'absolute',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.1)',
          top: '-200px',
          right: '-200px',
          filter: 'blur(80px)',
        }}
        animate={{
          scale: [1, 1.2, 1],
          rotate: [0, 90, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      <motion.div
        style={{
          position: 'absolute',
          width: '400px',
          height: '400px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.08)',
          bottom: '-150px',
          left: '-150px',
          filter: 'blur(60px)',
        }}
        animate={{
          scale: [1, 1.3, 1],
          rotate: [0, -90, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      <Container maxWidth="sm" sx={{ position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Logo and Brand */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <motion.div
              animate={{
                rotate: [0, 360],
                scale: [1, 1.1, 1],
              }}
              transition={{
                rotate: { duration: 20, repeat: Infinity, ease: 'linear' },
                scale: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
              }}
            >
              <School
                sx={{
                  fontSize: 72,
                  color: 'white',
                  filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.2))',
                  mb: 2,
                }}
              />
            </motion.div>

            <Typography
              variant="h2"
              sx={{
                fontWeight: 800,
                color: 'white',
                textShadow: '0 2px 20px rgba(0,0,0,0.2)',
                mb: 1,
              }}
            >
              KIRO2
            </Typography>

            <Typography
              variant="h6"
              sx={{
                color: 'rgba(255, 255, 255, 0.95)',
                fontWeight: 500,
                textShadow: '0 1px 10px rgba(0,0,0,0.1)',
              }}
            >
              Eğitimde Yapay Zeka Devrimi
            </Typography>
          </Box>

          {/* Login Form - Glass Card */}
          <GlassCard glassIntensity="medium" elevated>
            <Typography
              variant="h5"
              align="center"
              sx={{
                fontWeight: 700,
                mb: 3,
                background: modernColors.gradients.primary,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Giriş Yap
            </Typography>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Alert
                  severity="error"
                  sx={{
                    mb: 3,
                    borderRadius: '12px',
                    backdropFilter: 'blur(10px)',
                  }}
                >
                  {error}
                </Alert>
              </motion.div>
            )}

            <Box component="form" onSubmit={handleSubmit}>
              {/* Email Field */}
              <TextField
                fullWidth
                id="email"
                name="email"
                label="E-posta Adresi"
                type="email"
                autoComplete="email"
                value={formData.email}
                onChange={handleInputChange}
                disabled={isLoading}
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: '12px',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 1)',
                    },
                    '&.Mui-focused': {
                      backgroundColor: 'rgba(255, 255, 255, 1)',
                    },
                  },
                }}
              />

              {/* Password Field */}
              <TextField
                fullWidth
                id="password"
                name="password"
                label="Şifre"
                type="password"
                autoComplete="current-password"
                value={formData.password}
                onChange={handleInputChange}
                disabled={isLoading}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: '12px',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 1)',
                    },
                    '&.Mui-focused': {
                      backgroundColor: 'rgba(255, 255, 255, 1)',
                    },
                  },
                }}
              />

              {/* Login Button */}
              <ModernButton
                type="submit"
                variant="gradient"
                gradient={modernColors.gradients.sunset}
                fullWidth
                size="large"
                loading={isLoading}
                endIcon={<ArrowForward />}
                glow
              >
                Giriş Yap
              </ModernButton>

              {/* Forgot Password */}
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Link
                  to="/forgot-password"
                  style={{ textDecoration: 'none' }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      color: modernColors.primary[700],
                      fontWeight: 600,
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    Şifremi Unuttum
                  </Typography>
                </Link>
              </Box>
            </Box>

            {/* Divider */}
            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary" fontWeight={500}>
                VEYA
              </Typography>
            </Divider>

            {/* Demo Login Buttons */}
            <Typography
              variant="body2"
              align="center"
              color="text.secondary"
              sx={{ mb: 2, fontWeight: 600 }}
            >
              Demo Hesapları ile Dene:
            </Typography>

            <Grid container spacing={1.5}>
              {[
                { role: 'ogrenci' as UserRole, label: 'Öğrenci', icon: <Person />, gradient: modernColors.gradients.ocean },
                { role: 'ogretmen' as UserRole, label: 'Öğretmen', icon: <SchoolOutlined />, gradient: modernColors.gradients.forest },
                { role: 'veli' as UserRole, label: 'Veli', icon: <SupervisorAccount />, gradient: modernColors.gradients.aurora },
                { role: 'admin' as UserRole, label: 'Admin', icon: <AdminPanelSettings />, gradient: modernColors.gradients.fire },
              ].map((demo) => (
                <Grid item xs={6} key={demo.role}>
                  <ModernButton
                    variant="glass"
                    fullWidth
                    size="small"
                    onClick={() => handleDemoLogin(demo.role)}
                    disabled={isLoading}
                    startIcon={demo.icon}
                  >
                    {demo.label}
                  </ModernButton>
                </Grid>
              ))}
            </Grid>

            {/* Register Link */}
            <Box sx={{ textAlign: 'center', mt: 3, pt: 3, borderTop: `1px solid ${modernColors.divider.light}` }}>
              <Typography variant="body2" color="text.secondary">
                Hesabınız yok mu?{' '}
                <Link to="/register" style={{ textDecoration: 'none' }}>
                  <Typography
                    component="span"
                    variant="body2"
                    sx={{
                      background: modernColors.gradients.primary,
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      fontWeight: 700,
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    Kayıt Ol
                  </Typography>
                </Link>
              </Typography>
            </Box>
          </GlassCard>

          {/* Footer */}
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              textAlign: 'center',
              mt: 3,
              color: 'rgba(255, 255, 255, 0.8)',
              textShadow: '0 1px 4px rgba(0,0,0,0.2)',
            }}
          >
            © 2025 KIRO2 - Tüm hakları saklıdır
          </Typography>
        </motion.div>
      </Container>
    </Box>
  );
};

export default ModernLoginPage;
