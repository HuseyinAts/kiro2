/**
 * Modern Login Form Component
 * Enhanced login form with modern design and accessibility
 */

import {
  Email as EmailIcon,
  Lock as LockIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  School as SchoolIcon,
} from '@mui/icons-material';
import {
  Box,
  TextField,
  Typography,
  Alert,
  Paper,
  Fade,
  InputAdornment,
  IconButton,
  useTheme,
} from '@mui/material';
import * as React from 'react';
import {  useState, useCallback, memo  } from 'react';

import { useResponsive } from '../../utils/responsive';
import { ModernButton } from '../ui/modern-button';

interface LoginFormData {
  email: string
  password: string
}

interface ModernLoginFormProps {
  onSubmit: (data: LoginFormData) => Promise<void>
  loading?: boolean
  error?: string | null
  className?: string
}

export const ModernLoginForm: React.FC<ModernLoginFormProps> = memo(({
  onSubmit,
  loading = false,
  error = null,
  className,
}) => {
  const theme = useTheme();
  const { isMobile } = useResponsive();

  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Partial<LoginFormData>>({});

  const handleInputChange = useCallback((field: keyof LoginFormData) => (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));

    // Clear field error when user starts typing
    if (fieldErrors[field]) {
      setFieldErrors(prev => ({ ...prev, [field]: undefined }));
    }
  }, [fieldErrors]);

  const togglePasswordVisibility = useCallback(() => {
    setShowPassword(prev => !prev);
  }, []);

  const validateForm = useCallback((): boolean => {
    const errors: Partial<LoginFormData> = {};

    // Email validation
    if (!formData.email) {
      errors.email = 'E-posta adresi gerekli';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Geçerli bir e-posta adresi girin';
    }

    // Password validation
    if (!formData.password) {
      errors.password = 'Şifre gerekli';
    } else if (formData.password.length < 6) {
      errors.password = 'Şifre en az 6 karakter olmalı';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData]);

  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(formData);
    } catch (error) {
      // Error handling is done by parent component
      console.error('Login error:', error);
    }
  }, [formData, validateForm, onSubmit]);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(135deg, ${theme.palette.primary.main}10 0%, ${theme.palette.secondary.main}10 100%)`,
        p: 2,
      }}
      className={className}
    >
      <Fade in timeout={600}>
        <Paper
          elevation={0}
          sx={{
            width: '100%',
            maxWidth: 400,
            p: { xs: 3, sm: 4 },
            borderRadius: 3,
            boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
            backgroundColor: 'background.paper',
            border: `1px solid ${theme.palette.divider}`,
          }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 64,
                height: 64,
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.light})`,
                color: 'white',
                mb: 2,
                boxShadow: `0 8px 32px ${theme.palette.primary.main}40`,
              }}
            >
              <SchoolIcon sx={{ fontSize: 32 }} />
            </Box>

            <Typography
              variant="h4"
              component="h1"
              sx={{
                fontWeight: 700,
                mb: 1,
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                color: 'transparent',
              }}
            >
              KIRO2 Platform
            </Typography>

            <Typography variant="body2" color="text.secondary">
              Türkiye Üniversite Sınavları Hazırlık Platformu
            </Typography>
          </Box>

          {/* Error Alert */}
          {error && (
            <Fade in>
              <Alert
                severity="error"
                sx={{
                  mb: 3,
                  borderRadius: 2,
                  '& .MuiAlert-message': {
                    width: '100%',
                  },
                }}
              >
                {error}
              </Alert>
            </Fade>
          )}

          {/* Login Form */}
          <Box component="form" onSubmit={handleSubmit} noValidate>
            <TextField
              fullWidth
              label="E-posta Adresi"
              type="email"
              value={formData.email}
              onChange={handleInputChange('email')}
              error={!!fieldErrors.email}
              helperText={fieldErrors.email}
              disabled={loading}
              margin="normal"
              required
              autoComplete="email"
              autoFocus={!isMobile} // Don't auto-focus on mobile to prevent keyboard popup
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <EmailIcon color="action" />
                  </InputAdornment>
                ),
                sx: {
                  borderRadius: 2,
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: theme.palette.divider,
                  },
                },
              }}
              sx={{
                '& .MuiFormLabel-root': {
                  fontSize: '0.875rem',
                },
                '& .MuiInputBase-root': {
                  minHeight: 56, // Touch-friendly height
                },
              }}
            />

            <TextField
              fullWidth
              label="Şifre"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleInputChange('password')}
              error={!!fieldErrors.password}
              helperText={fieldErrors.password}
              disabled={loading}
              margin="normal"
              required
              autoComplete="current-password"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="şifreyi göster/gizle"
                      onClick={togglePasswordVisibility}
                      edge="end"
                      disabled={loading}
                      size="small"
                    >
                      {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
                sx: {
                  borderRadius: 2,
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: theme.palette.divider,
                  },
                },
              }}
              sx={{
                '& .MuiFormLabel-root': {
                  fontSize: '0.875rem',
                },
                '& .MuiInputBase-root': {
                  minHeight: 56, // Touch-friendly height
                },
              }}
            />

            <ModernButton
              type="submit"
              fullWidth
              variant="gradient"
              color="primary"
              size="large"
              loading={loading}
              disabled={!formData.email || !formData.password}
              touchOptimized
              sx={{ mt: 3, mb: 2 }}
              aria-label="giriş yap"
            >
              Giriş Yap
            </ModernButton>
          </Box>

          {/* Footer */}
          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Hesabınız yok mu?{' '}
              <Typography
                component="span"
                color="primary"
                sx={{
                  fontWeight: 600,
                  cursor: 'pointer',
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                }}
              >
                Kayıt Ol
              </Typography>
            </Typography>
          </Box>
        </Paper>
      </Fade>
    </Box>
  );
});

ModernLoginForm.displayName = 'ModernLoginForm';

export default ModernLoginForm;