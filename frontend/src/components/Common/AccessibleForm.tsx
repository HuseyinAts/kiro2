/**
 * WCAG 2.1 Level AA Uyumlu Form Bileşeni
 * Erişilebilir form yapısı ve doğrulama
 */

import {
  Visibility,
  VisibilityOff,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import {
  Box,
  TextField,
  Button,
  Typography,
  FormControl,
  FormLabel,
  FormHelperText,
  InputAdornment,
  IconButton,
  Alert,
  Paper,
  useTheme,
} from '@mui/material';
import * as React from 'react';
import {  useState, useRef, useCallback, useEffect  } from 'react';

import { useAccessibilitySettings } from '../../hooks/useAccessibilitySettings';
import { useScreenReader } from '../../hooks/useScreenReader';

export interface FormField {
  id: string;
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'tel' | 'url' | 'number' | 'textarea';
  required?: boolean;
  placeholder?: string;
  helperText?: string;
  validation?: {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    email?: boolean;
    custom?: (value: string) => string | null;
  };
  autoComplete?: string;
  ariaDescribedBy?: string;
}

interface FormError {
  field: string;
  message: string;
}

interface AccessibleFormProps {
  fields: FormField[];
  onSubmit: (data: Record<string, string>) => void | Promise<void>;
  title?: string;
  description?: string;
  submitLabel?: string;
  resetLabel?: string;
  loading?: boolean;
  disabled?: boolean;
  showRequiredIndicator?: boolean;
  validateOnBlur?: boolean;
  validateOnChange?: boolean;
  className?: string;
}

const AccessibleForm: React.FC<AccessibleFormProps> = ({
  fields,
  onSubmit,
  title,
  description,
  submitLabel = 'Gönder',
  resetLabel = 'Sıfırla',
  loading: _loading = false,
  disabled = false,
  showRequiredIndicator = true,
  validateOnBlur = true,
  validateOnChange = false,
  className,
}) => {
  const theme = useTheme();
  const { settings } = useAccessibilitySettings();
  const { announce, announceFormError, announceSuccess } = useScreenReader();

  const formRef = useRef<HTMLFormElement>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<FormError[]>([]);
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitAttempted, setSubmitAttempted] = useState(false);

  // Form ID'leri
  const formId = `accessible-form-${Math.random().toString(36).substr(2, 9)}`;
  const titleId = `${formId}-title`;
  const descriptionId = `${formId}-description`;
  const errorsId = `${formId}-errors`;

  // Doğrulama fonksiyonu
  const validateField = useCallback((field: FormField, value: string): string | null => {
    if (!field.validation) {return null;}

    const { required, minLength, maxLength, pattern, email, custom } = field.validation;

    // Zorunlu alan kontrolü
    if (required && !value.trim()) {
      return `${field.label} alanı zorunludur`;
    }

    // Değer yoksa diğer kontrolleri yapma
    if (!value.trim()) {return null;}

    // Minimum uzunluk
    if (minLength && value.length < minLength) {
      return `${field.label} en az ${minLength} karakter olmalıdır`;
    }

    // Maksimum uzunluk
    if (maxLength && value.length > maxLength) {
      return `${field.label} en fazla ${maxLength} karakter olmalıdır`;
    }

    // E-posta kontrolü
    if (email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) {
        return 'Geçerli bir e-posta adresi giriniz';
      }
    }

    // Pattern kontrolü
    if (pattern && !pattern.test(value)) {
      return `${field.label} geçerli formatta değil`;
    }

    // Özel doğrulama
    if (custom) {
      return custom(value);
    }

    return null;
  }, []);

  // Tüm alanları doğrula
  const validateForm = useCallback((): FormError[] => {
    const newErrors: FormError[] = [];

    fields.forEach(field => {
      const value = formData[field.name] || '';
      const error = validateField(field, value);
      if (error) {
        newErrors.push({ field: field.name, message: error });
      }
    });

    return newErrors;
  }, [fields, formData, validateField]);

  // Alan değeri değişikliği
  const handleFieldChange = useCallback((fieldName: string, value: string) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));

    // Değişiklik sırasında doğrulama
    if (validateOnChange || (submitAttempted && touched[fieldName])) {
      const field = fields.find(f => f.name === fieldName);
      if (field) {
        const error = validateField(field, value);
        setErrors(prev => {
          const filtered = prev.filter(e => e.field !== fieldName);
          return error ? [...filtered, { field: fieldName, message: error }] : filtered;
        });
      }
    }
  }, [validateOnChange, submitAttempted, touched, fields, validateField]);

  // Alan odak kaybı
  const handleFieldBlur = useCallback((fieldName: string) => {
    setTouched(prev => ({ ...prev, [fieldName]: true }));

    // Odak kaybında doğrulama
    if (validateOnBlur) {
      const field = fields.find(f => f.name === fieldName);
      if (field) {
        const value = formData[fieldName] || '';
        const error = validateField(field, value);

        setErrors(prev => {
          const filtered = prev.filter(e => e.field !== fieldName);
          const newErrors = error ? [...filtered, { field: fieldName, message: error }] : filtered;

          // Hata varsa duyur
          if (error) {
            announceFormError(field.label, error);
          }

          return newErrors;
        });
      }
    }
  }, [validateOnBlur, formData, fields, validateField, announceFormError]);

  // Şifre görünürlük toggle
  const togglePasswordVisibility = useCallback((fieldName: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [fieldName]: !prev[fieldName],
    }));

    const isVisible = !showPasswords[fieldName];
    announce(
      isVisible ? 'Şifre gösteriliyor' : 'Şifre gizleniyor',
      'polite',
    );
  }, [showPasswords, announce]);

  // Form gönderimi
  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitAttempted(true);

    // Tüm alanları doğrula
    const formErrors = validateForm();
    setErrors(formErrors);

    if (formErrors.length > 0) {
      // İlk hataya odaklan
      const firstErrorField = formErrors[0].field;
      const firstErrorElement = formRef.current?.querySelector(`[name="${firstErrorField}"]`) as HTMLElement;
      if (firstErrorElement) {
        firstErrorElement.focus();
      }

      announce(
        `Form ${formErrors.length} hata içeriyor. İlk hata: ${formErrors[0].message}`,
        'assertive',
      );
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(formData);
      announceSuccess('Form başarıyla gönderildi');
    } catch {
      announce('Form gönderilirken hata oluştu', 'assertive');
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validateForm, onSubmit, announce, announceSuccess]);

  // Form sıfırlama
  const handleReset = useCallback(() => {
    setFormData({});
    setErrors([]);
    setTouched({});
    setSubmitAttempted(false);
    announce('Form sıfırlandı', 'polite');
  }, [announce]);

  // Alan hatası alma
  const getFieldError = useCallback((fieldName: string): string | null => {
    const error = errors.find(e => e.field === fieldName);
    return error ? error.message : null;
  }, [errors]);

  // Alan durumu
  const getFieldProps = useCallback((field: FormField) => {
    const error = getFieldError(field.name);
    const value = formData[field.name] || '';
    const hasError = !!error && (touched[field.name] || submitAttempted);

    return {
      id: field.id,
      name: field.name,
      value,
      error: hasError,
      helperText: hasError ? error : field.helperText,
      required: field.required,
      disabled: disabled || isSubmitting,
      onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
        handleFieldChange(field.name, e.target.value),
      onBlur: () => handleFieldBlur(field.name),
      'aria-describedby': [
        field.ariaDescribedBy,
        field.helperText ? `${field.id}-helper` : undefined,
        hasError ? `${field.id}-error` : undefined,
      ].filter(Boolean).join(' ') || undefined,
      'aria-invalid': hasError,
      autoComplete: field.autoComplete,
    };
  }, [formData, touched, submitAttempted, disabled, isSubmitting, getFieldError, handleFieldChange, handleFieldBlur]);

  // Klavye kısayolları
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl + Enter: Form gönder
      if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        handleSubmit(event as any);
      }

      // Escape: Form sıfırla (onay ile)
      if (event.key === 'Escape') {
        if (Object.keys(formData).some(key => formData[key])) {
          if (confirm('Formu sıfırlamak istediğinizden emin misiniz?')) {
            handleReset();
          }
        }
      }
    };

    if (formRef.current) {
      formRef.current.addEventListener('keydown', handleKeyDown);
      return () => formRef.current?.removeEventListener('keydown', handleKeyDown);
    }
  }, [formData, handleSubmit, handleReset]);

  return (
    <Paper
      component="form"
      ref={formRef}
      onSubmit={handleSubmit}
      noValidate
      className={className}
      sx={{
        p: 3,
        maxWidth: 600,
        mx: 'auto',
        '& .wcag-aa-target-size': {
          minHeight: 44,
          minWidth: 44,
        },
      }}
      role="form"
      aria-labelledby={title ? titleId : undefined}
      aria-describedby={description ? descriptionId : undefined}
    >
      {/* Başlık */}
      {title && (
        <Typography
          id={titleId}
          variant="h4"
          component="h1"
          gutterBottom
          sx={{ mb: 2 }}
        >
          {title}
        </Typography>
      )}

      {/* Açıklama */}
      {description && (
        <Typography
          id={descriptionId}
          variant="body1"
          color="textSecondary"
          sx={{ mb: 3 }}
        >
          {description}
        </Typography>
      )}

      {/* Zorunlu alan göstergesi */}
      {showRequiredIndicator && fields.some(f => f.required) && (
        <Typography
          variant="body2"
          color="textSecondary"
          sx={{ mb: 2 }}
        >
          <span style={{ color: theme.palette.error.main }}>*</span> işaretli alanlar zorunludur
        </Typography>
      )}

      {/* Hata özeti */}
      {errors.length > 0 && submitAttempted && (
        <Alert
          severity="error"
          icon={<ErrorIcon />}
          sx={{ mb: 3 }}
          role="alert"
          aria-labelledby={errorsId}
        >
          <Typography id={errorsId} variant="h6" gutterBottom>
            Form Hataları ({errors.length})
          </Typography>
          <Box component="ul" sx={{ m: 0, pl: 2 }}>
            {errors.map((error, index) => {
              const field = fields.find(f => f.name === error.field);
              return (
                <Typography
                  key={index}
                  component="li"
                  variant="body2"
                  sx={{ mb: 0.5 }}
                >
                  <Button
                    variant="text"
                    size="small"
                    onClick={() => {
                      const element = document.getElementById(field?.id || '');
                      element?.focus();
                    }}
                    sx={{
                      textAlign: 'left',
                      justifyContent: 'flex-start',
                      textTransform: 'none',
                      p: 0,
                      minWidth: 'auto',
                    }}
                  >
                    {field?.label}: {error.message}
                  </Button>
                </Typography>
              );
            })}
          </Box>
        </Alert>
      )}

      {/* Form Alanları */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {fields.map((field) => {
          const fieldProps = getFieldProps(field);
          const isPassword = field.type === 'password';
          const showPassword = showPasswords[field.name];

          return (
            <FormControl key={field.id} fullWidth error={fieldProps.error}>
              <FormLabel
                htmlFor={field.id}
                required={field.required}
                sx={{ mb: 1, fontWeight: 'medium' }}
              >
                {field.label}
                {field.required && showRequiredIndicator && (
                  <span style={{ color: theme.palette.error.main, marginLeft: 4 }}>*</span>
                )}
              </FormLabel>

              <TextField
                {...fieldProps}
                type={isPassword ? (showPassword ? 'text' : 'password') : field.type}
                placeholder={field.placeholder}
                multiline={field.type === 'textarea'}
                rows={field.type === 'textarea' ? 4 : undefined}
                InputProps={{
                  ...(isPassword && {
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => togglePasswordVisibility(field.name)}
                          edge="end"
                          aria-label={showPassword ? 'Şifreyi gizle' : 'Şifreyi göster'}
                          className="wcag-aa-target-size"
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }),
                  className: 'wcag-aa-target-size',
                }}
                sx={{
                  '& .MuiInputBase-root': {
                    minHeight: 44,
                  },
                  '& .MuiInputBase-input': {
                    fontSize: settings.fontSize === 'large' ? '1.2rem' : '1rem',
                  },
                }}
              />

              {/* Yardım metni */}
              {field.helperText && !fieldProps.error && (
                <FormHelperText id={`${field.id}-helper`}>
                  <InfoIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                  {field.helperText}
                </FormHelperText>
              )}

              {/* Hata mesajı */}
              {fieldProps.error && fieldProps.helperText && (
                <FormHelperText id={`${field.id}-error`} error>
                  <ErrorIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                  {fieldProps.helperText}
                </FormHelperText>
              )}
            </FormControl>
          );
        })}
      </Box>

      {/* Form Butonları */}
      <Box sx={{
        display: 'flex',
        gap: 2,
        justifyContent: 'flex-end',
        mt: 4,
        flexWrap: 'wrap',
      }}>
        <Button
          type="button"
          variant="outlined"
          onClick={handleReset}
          disabled={disabled || isSubmitting || Object.keys(formData).length === 0}
          className="wcag-aa-target-size"
        >
          {resetLabel}
        </Button>

        <Button
          type="submit"
          variant="contained"
          disabled={disabled || isSubmitting}
          className="wcag-aa-target-size"
          sx={{ minWidth: 120 }}
        >
          {isSubmitting ? 'Gönderiliyor...' : submitLabel}
        </Button>
      </Box>

      {/* Klavye kısayolları yardımı */}
      {settings.keyboardNavigation && (
        <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="caption" color="textSecondary">
            <strong>Klavye Kısayolları:</strong> Ctrl+Enter: Gönder | Esc: Sıfırla |
            Tab: Sonraki alan | Shift+Tab: Önceki alan
          </Typography>
        </Box>
      )}

      {/* Başarı durumu */}
      {!errors.length && submitAttempted && !isSubmitting && (
        <Alert severity="success" sx={{ mt: 2 }}>
          <SuccessIcon sx={{ mr: 1 }} />
          Form başarıyla doğrulandı
        </Alert>
      )}
    </Paper>
  );
};

export default AccessibleForm;