/**
 * Modern Register Page
 * Beautiful registration page with glassmorphism and role-based visuals
 */

import {
  School,
  PersonAdd,
  Visibility,
  VisibilityOff,
  CheckCircle,
  Cancel,
  Person,
  Groups,
  ChildCare,
  AdminPanelSettings,
  Email,
  Lock,
  Phone,
  Business,
} from '@mui/icons-material';
import {
  Container,
  Grid,
  Typography,
  Box,
  TextField,
  Alert,
  LinearProgress,
  IconButton,
  InputAdornment,
  Link,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import {  useState  } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';

import { RegisterRequest, UserRole } from '../types';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { useAuthStore } from '@/store/authStore';
import modernColors from '@/theme/modern-colors';

export const ModernRegisterPage: React.FC = () => {
  const [formData, setFormData] = useState<RegisterRequest>({
    email: '',
    password: '',
    ad: '',
    soyad: '',
    rol: 'ogrenci',
    telefon: '',
    okul_id: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const { register } = useAuthStore();
  const navigate = useNavigate();

  // Password strength calculation
  const getPasswordStrength = (password: string): number => {
    let strength = 0;
    if (password.length >= 6) {strength += 25;}
    if (password.length >= 10) {strength += 25;}
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) {strength += 25;}
    if (/\d/.test(password)) {strength += 15;}
    if (/[^a-zA-Z\d]/.test(password)) {strength += 10;}
    return Math.min(strength, 100);
  };

  const passwordStrength = getPasswordStrength(formData.password);

  const getPasswordStrengthColor = (strength: number): string => {
    if (strength < 30) {return modernColors.gradients.error;}
    if (strength < 60) {return modernColors.gradients.warning;}
    return modernColors.gradients.success;
  };

  const getPasswordStrengthLabel = (strength: number): string => {
    if (strength < 30) {return 'Zayıf';}
    if (strength < 60) {return 'Orta';}
    return 'Güçlü';
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (error) {setError(null);}
    if (fieldErrors[name]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  const handleRoleSelect = (role: UserRole) => {
    setFormData((prev) => ({ ...prev, rol: role }));
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!formData.ad) {errors.ad = 'Ad gerekli';}
    if (!formData.soyad) {errors.soyad = 'Soyad gerekli';}

    if (!formData.email) {
      errors.email = 'E-posta adresi gerekli';
    } else if (!emailRegex.test(formData.email)) {
      errors.email = 'Geçerli bir e-posta adresi girin';
    }

    if (!formData.password) {
      errors.password = 'Şifre gerekli';
    } else if (formData.password.length < 6) {
      errors.password = 'Şifre en az 6 karakter olmalıdır';
    }

    if (!confirmPassword) {
      errors.confirmPassword = 'Şifre tekrarı gerekli';
    } else if (formData.password !== confirmPassword) {
      errors.confirmPassword = 'Şifreler eşleşmiyor';
    }

    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      setError('Lütfen formdaki hataları düzeltin.');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {return;}

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const success = await register(formData);

      if (success) {
        setSuccess('Kayıt başarılı! Giriş sayfasına yönlendiriliyorsunuz...');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      }
    } catch (error: any) {
      setError(error.message || 'Kayıt sırasında bir hata oluştu');
    } finally {
      setIsLoading(false);
    }
  };

  const roles = [
    {
      value: 'ogrenci' as UserRole,
      label: 'Öğrenci',
      icon: <Person sx={{ fontSize: 32 }} />,
      description: 'Sınavlara hazırlan, öğren',
      gradient: modernColors.gradients.primary,
    },
    {
      value: 'ogretmen' as UserRole,
      label: 'Öğretmen',
      icon: <Groups sx={{ fontSize: 32 }} />,
      description: 'Öğrencileri yönet, içerik oluştur',
      gradient: modernColors.gradients.forest,
    },
    {
      value: 'veli' as UserRole,
      label: 'Veli',
      icon: <ChildCare sx={{ fontSize: 32 }} />,
      description: 'Çocuklarını takip et',
      gradient: modernColors.gradients.sunset,
    },
    {
      value: 'admin' as UserRole,
      label: 'Admin',
      icon: <AdminPanelSettings sx={{ fontSize: 32 }} />,
      description: 'Sistem yönetimi',
      gradient: modernColors.gradients.fire,
    },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.primary,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
        py: 4,
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
          right: '-150px',
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
          background: 'rgba(255, 255, 255, 0.05)',
          bottom: '-100px',
          left: '-100px',
          filter: 'blur(60px)',
        }}
        animate={{
          scale: [1, 1.1, 1],
          rotate: [0, -90, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
              style={{ display: 'inline-block' }}
            >
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: '20px',
                  background: 'rgba(255, 255, 255, 0.2)',
                  backdropFilter: 'blur(10px)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto',
                  boxShadow: modernColors.shadow.modern,
                }}
              >
                <School sx={{ fontSize: 48, color: 'white' }} />
              </Box>
            </motion.div>

            <Typography
              variant="h3"
              sx={{
                fontWeight: 800,
                color: 'white',
                mt: 2,
                textShadow: '0 2px 10px rgba(0,0,0,0.2)',
              }}
            >
              KIRO2&apos;ye Hoş Geldiniz
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: 'rgba(255,255,255,0.9)',
                mt: 1,
              }}
            >
              Eğitim yolculuğunuza başlayın
            </Typography>
          </Box>

          {/* Registration Form */}
          <GlassCard glassIntensity="medium" elevated>
            <Box component="form" onSubmit={handleSubmit} noValidate>
              <AnimatePresence mode="wait">
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

              {/* Role Selection */}
              <Typography variant="h6" fontWeight={700} gutterBottom>
                Rolünüzü Seçin
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                {roles.map((role, index) => (
                  <Grid item xs={6} sm={3} key={role.value}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <Box
                        role="button"
                        aria-label={`${role.label} rolü seç - ${role.description}`}
                        aria-pressed={formData.rol === role.value}
                        tabIndex={0}
                        onClick={() => handleRoleSelect(role.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleRoleSelect(role.value);
                          }
                        }}
                        sx={{
                          p: 2,
                          borderRadius: '16px',
                          background:
                            formData.rol === role.value
                              ? role.gradient
                              : modernColors.glass.white.light,
                          border: `2px solid ${
                            formData.rol === role.value
                              ? 'transparent'
                              : modernColors.glass.border
                          }`,
                          cursor: 'pointer',
                          transition: 'all 0.3s',
                          textAlign: 'center',
                          boxShadow:
                            formData.rol === role.value
                              ? modernColors.shadow.glow
                              : 'none',
                          '&:focus': {
                            outline: '2px solid rgba(59, 130, 246, 0.5)',
                            outlineOffset: '2px',
                          },
                        }}
                      >
                        <Box
                          sx={{
                            color:
                              formData.rol === role.value ? 'white' : 'text.primary',
                          }}
                        >
                          {role.icon}
                        </Box>
                        <Typography
                          variant="body2"
                          fontWeight={700}
                          sx={{
                            mt: 1,
                            color:
                              formData.rol === role.value ? 'white' : 'text.primary',
                          }}
                        >
                          {role.label}
                        </Typography>
                        <Typography
                          variant="caption"
                          sx={{
                            color:
                              formData.rol === role.value
                                ? 'rgba(255,255,255,0.9)'
                                : 'text.secondary',
                            display: 'block',
                            mt: 0.5,
                          }}
                        >
                          {role.description}
                        </Typography>
                      </Box>
                    </motion.div>
                  </Grid>
                ))}
              </Grid>

              {/* Personal Information */}
              <Typography variant="h6" fontWeight={700} gutterBottom sx={{ mt: 3 }}>
                Kişisel Bilgiler
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    required
                    fullWidth
                    name="ad"
                    label="Ad"
                    value={formData.ad}
                    onChange={handleInputChange}
                    disabled={isLoading}
                    autoComplete="given-name"
                    error={!!fieldErrors.ad}
                    helperText={fieldErrors.ad}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Person />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(10px)',
                      },
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    required
                    fullWidth
                    name="soyad"
                    label="Soyad"
                    value={formData.soyad}
                    onChange={handleInputChange}
                    disabled={isLoading}
                    autoComplete="family-name"
                    error={!!fieldErrors.soyad}
                    helperText={fieldErrors.soyad}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Person />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(10px)',
                      },
                    }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    required
                    fullWidth
                    name="email"
                    label="E-posta Adresi"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    disabled={isLoading}
                    autoComplete="email"
                    error={!!fieldErrors.email}
                    helperText={fieldErrors.email}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Email />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(10px)',
                      },
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    required
                    fullWidth
                    name="password"
                    label="Şifre"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={handleInputChange}
                    disabled={isLoading}
                    autoComplete="new-password"
                    error={!!fieldErrors.password}
                    helperText={fieldErrors.password}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Lock />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPassword(!showPassword)}
                            edge="end"
                          >
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(10px)',
                      },
                    }}
                  />
                  {formData.password && (
                    <Box sx={{ mt: 1 }}>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          mb: 0.5,
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          Şifre Gücü:
                        </Typography>
                        <Typography variant="caption" fontWeight={600}>
                          {getPasswordStrengthLabel(passwordStrength)}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={passwordStrength}
                        aria-label={`Şifre gücü: ${getPasswordStrengthLabel(passwordStrength)}`}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: modernColors.glass.black.light,
                          '& .MuiLinearProgress-bar': {
                            borderRadius: 3,
                            background: getPasswordStrengthColor(passwordStrength),
                          },
                        }}
                      />
                    </Box>
                  )}
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    required
                    fullWidth
                    name="confirmPassword"
                    label="Şifre Tekrar"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (fieldErrors.confirmPassword) {
                        setFieldErrors((prev) => {
                          const next = { ...prev };
                          delete next.confirmPassword;
                          return next;
                        });
                      }
                    }}
                    disabled={isLoading}
                    autoComplete="new-password"
                    error={!!fieldErrors.confirmPassword}
                    helperText={fieldErrors.confirmPassword}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Lock />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() =>
                              setShowConfirmPassword(!showConfirmPassword)
                            }
                            edge="end"
                          >
                            {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(10px)',
                      },
                    }}
                  />
                  {confirmPassword && (
                    <Box role="status" aria-live="polite" sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                      {formData.password === confirmPassword ? (
                        <>
                          <CheckCircle sx={{ fontSize: 18, color: 'success.main' }} />
                          <Typography variant="caption" color="success.main">
                            Şifreler eşleşiyor
                          </Typography>
                        </>
                      ) : (
                        <>
                          <Cancel sx={{ fontSize: 18, color: 'error.main' }} />
                          <Typography variant="caption" color="error.main">
                            Şifreler eşleşmiyor
                          </Typography>
                        </>
                      )}
                    </Box>
                  )}
                </Grid>
              </Grid>

              {/* Additional Information */}
              <Typography variant="h6" fontWeight={700} gutterBottom sx={{ mt: 3 }}>
                Ek Bilgiler (Opsiyonel)
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    name="telefon"
                    label="Telefon"
                    value={formData.telefon}
                    onChange={handleInputChange}
                    disabled={isLoading}
                    autoComplete="tel"
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Phone />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(10px)',
                      },
                    }}
                  />
                </Grid>

                {(formData.rol === 'ogrenci' || formData.rol === 'ogretmen') && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      name="okul_id"
                      label="Okul Kodu"
                      value={formData.okul_id}
                      onChange={handleInputChange}
                      disabled={isLoading}
                      autoComplete="off"
                      helperText="Okulunuzun verdiği özel kod"
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <Business />
                          </InputAdornment>
                        ),
                      }}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          backdropFilter: 'blur(10px)',
                        },
                      }}
                    />
                  </Grid>
                )}
              </Grid>

              {/* Submit Button */}
              <ModernButton
                type="submit"
                fullWidth
                variant="gradient"
                gradient={
                  roles.find((r) => r.value === formData.rol)?.gradient ||
                  modernColors.gradients.primary
                }
                glow
                loading={isLoading}
                icon={<PersonAdd />}
                sx={{ mt: 4 }}
              >
                Kayıt Ol
              </ModernButton>

              {/* Login Link */}
              <Box sx={{ textAlign: 'center', mt: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Zaten hesabınız var mı?{' '}
                  <Link
                    component={RouterLink}
                    to="/login"
                    sx={{
                      fontWeight: 700,
                      textDecoration: 'none',
                      background: modernColors.gradients.primary,
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    Giriş Yap
                  </Link>
                </Typography>
              </Box>
            </Box>
          </GlassCard>
        </motion.div>
      </Container>
    </Box>
  );
};

export default ModernRegisterPage;
