/**
 * Modern Button Component
 * Enhanced button with loading states, accessibility, and touch optimization
 */

import {
  Button as MuiButton,
  ButtonProps as MuiButtonProps,
  CircularProgress,
  Box,
  useTheme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import * as React from 'react';
import {  memo, forwardRef  } from 'react';

export interface ModernButtonProps extends Omit<MuiButtonProps, 'variant' | 'color'> {
  children: React.ReactNode
  variant?: 'text' | 'outlined' | 'contained' | 'gradient'
  size?: 'small' | 'medium' | 'large'
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info'
  loading?: boolean
  touchOptimized?: boolean
  sx?: MuiButtonProps['sx']
  'data-testid'?: string
}

export const ModernButton = memo(forwardRef<HTMLButtonElement, ModernButtonProps>(({
  children,
  variant = 'contained',
  size = 'medium',
  color = 'primary',
  loading = false,
  disabled = false,
  fullWidth = false,
  startIcon,
  endIcon,
  onClick,
  type = 'button',
  className,
  'aria-label': ariaLabel,
  'data-testid': testId,
  touchOptimized = true,
  ...props
}, ref) => {
  const theme = useTheme();

  // Size configurations for touch optimization
  const sizeConfig = {
    small: {
      height: touchOptimized ? 40 : 32,
      px: 2,
      fontSize: '0.875rem',
    },
    medium: {
      height: touchOptimized ? 48 : 36,
      px: 3,
      fontSize: '0.875rem',
    },
    large: {
      height: touchOptimized ? 56 : 42,
      px: 4,
      fontSize: '1rem',
    },
  };

  const config = sizeConfig[size];

  // Gradient variant styles
  const gradientStyles = {
    primary: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.primary.light} 90%)`,
    secondary: `linear-gradient(45deg, ${theme.palette.secondary.main} 30%, ${theme.palette.secondary.light} 90%)`,
    success: `linear-gradient(45deg, ${theme.palette.success.main} 30%, ${theme.palette.success.light} 90%)`,
    error: `linear-gradient(45deg, ${theme.palette.error.main} 30%, ${theme.palette.error.light} 90%)`,
    warning: `linear-gradient(45deg, ${theme.palette.warning.main} 30%, ${theme.palette.warning.light} 90%)`,
    info: `linear-gradient(45deg, ${theme.palette.info.main} 30%, ${theme.palette.info.light} 90%)`,
  };

  const buttonVariant = variant === 'gradient' ? 'contained' : variant;

  const isDisabled = disabled || loading;

  return (
    <MuiButton
      ref={ref}
      variant={buttonVariant}
      size={size}
      color={variant === 'gradient' ? undefined : color}
      disabled={isDisabled}
      fullWidth={fullWidth}
      startIcon={loading ? null : startIcon}
      endIcon={loading ? null : endIcon}
      onClick={onClick}
      type={type}
      className={className}
      aria-label={ariaLabel}
      data-testid={testId}
      sx={{
        height: config.height,
        px: config.px,
        fontSize: config.fontSize,
        fontWeight: 600,
        textTransform: 'none',
        borderRadius: 2,
        boxShadow: variant === 'contained' || variant === 'gradient' ?
          `0 2px 8px ${alpha(theme.palette[color].main, 0.3)}` : 'none',

        // Gradient styles
        ...(variant === 'gradient' && {
          background: gradientStyles[color],
          color: theme.palette.getContrastText(theme.palette[color].main),
          border: 'none',
          '&:hover': {
            background: gradientStyles[color],
            boxShadow: `0 4px 12px ${alpha(theme.palette[color].main, 0.4)}`,
            transform: 'translateY(-1px)',
          },
        }),

        // Touch optimization
        ...(touchOptimized && {
          minHeight: 44, // iOS minimum touch target
          minWidth: 44,
          '@media (hover: hover)': {
            '&:hover': {
              transform: 'translateY(-1px)',
              boxShadow: variant === 'contained' || variant === 'gradient' ?
                `0 4px 12px ${alpha(theme.palette[color].main, 0.4)}` : 'none',
            },
          },
        }),

        // Focus styles for accessibility
        '&:focus-visible': {
          outline: `2px solid ${theme.palette[color].main}`,
          outlineOffset: 2,
        },

        // Loading state
        ...(loading && {
          color: 'transparent',
        }),

        // Smooth transitions
        transition: 'all 0.2s ease-in-out',
      }}
      {...props}
    >
      {loading && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CircularProgress
            size={20}
            sx={{
              color: variant === 'contained' || variant === 'gradient' ?
                'currentColor' : theme.palette[color].main,
            }}
          />
        </Box>
      )}

      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          opacity: loading ? 0 : 1,
          transition: 'opacity 0.2s ease-in-out',
        }}
      >
        {startIcon}
        {children}
        {endIcon}
      </Box>
    </MuiButton>
  );
}));

ModernButton.displayName = 'ModernButton';

export default ModernButton;